from logger_setup import setup_logger
import pandas as pd

logger = setup_logger('futures_risk')

class FuturesRiskMixin:
    def calculate_futures_position_size(self, symbol, current_price, leverage=2):
        try:
            if not self.futures_client:
                logger.warning("Futures client not initialized")
                return 0
            
            futures_config = self.config.get('futures', {})
            risk_config = futures_config.get('risk_management', {})
            
            balances = self.futures_client.get_futures_balance()
            
            if not balances or 'USDT' not in balances:
                logger.warning("No USDT balance found in Futures wallet")
                return 0
            
            usdt_balance = balances['USDT']['available_balance']
            position_size_percent = risk_config.get('position_size_percent', 2.0)
            position_value = usdt_balance * (position_size_percent / 100)
            
            min_order_value = 10.0
            if position_value < min_order_value:
                logger.warning(f"⚠️ Futures position value ${position_value:.2f} below minimum ${min_order_value:.2f}")
                return 0
            
            if current_price and current_price > 0:
                quantity = position_value / current_price
                
                symbol_info = self.futures_client.get_symbol_info(symbol)
                if symbol_info:
                    for filter in symbol_info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            
                            step_size_str = f"{step_size:.10f}".rstrip('0')
                            if '.' in step_size_str:
                                precision = len(step_size_str.split('.')[1])
                            else:
                                precision = 0
                            
                            quantity = round(quantity / step_size) * step_size
                            quantity = round(quantity, precision)
                            break
                
                contract_value = position_value * leverage
                logger.info(f"Futures position for {symbol}: {quantity:.8f} @ {leverage}x")
                logger.info(f"   Margin: ${position_value:.2f} | Contract: ${contract_value:.2f}")
                return quantity
            
            return 0
        except Exception as e:
            logger.error(f"Error calculating futures position size: {e}")
            return 0
    
    def calculate_liquidation_price(self, entry_price, leverage, position_type, maintenance_margin_rate=0.004):
        if position_type in ['LONG', 'BUY']:
            liquidation_price = entry_price * (1 - (1 / leverage) + maintenance_margin_rate)
        elif position_type in ['SHORT', 'SELL']:
            liquidation_price = entry_price * (1 + (1 / leverage) - maintenance_margin_rate)
        else:
            return None
        
        return liquidation_price
    
    def validate_liquidation_buffer(self, entry_price, stop_loss_price, liquidation_price, position_type):
        futures_config = self.config.get('futures', {})
        risk_config = futures_config.get('risk_management', {})
        buffer_percent = risk_config.get('liquidation_buffer_percent', 5.0)
        
        if position_type in ['LONG', 'BUY']:
            required_sl = liquidation_price * (1 + buffer_percent / 100)
            if stop_loss_price < required_sl:
                logger.error(f"❌ Stop-Loss too close to liquidation!")
                logger.error(f"   Liquidation: ${liquidation_price:.2f}")
                logger.error(f"   Required SL: ${required_sl:.2f} (with {buffer_percent}% buffer)")
                logger.error(f"   Your SL: ${stop_loss_price:.2f}")
                return False
        else:
            required_sl = liquidation_price * (1 - buffer_percent / 100)
            if stop_loss_price > required_sl:
                logger.error(f"❌ Stop-Loss too close to liquidation!")
                logger.error(f"   Liquidation: ${liquidation_price:.2f}")
                logger.error(f"   Required SL: ${required_sl:.2f} (with {buffer_percent}% buffer)")
                logger.error(f"   Your SL: ${stop_loss_price:.2f}")
                return False
        
        logger.info(f"✅ Stop-Loss safe from liquidation (buffer: {buffer_percent}%)")
        return True
    
    def open_futures_position(self, symbol, entry_price, quantity, position_type, signals, market_regime):
        if not self.futures_client:
            logger.error("Cannot open futures position - client not initialized")
            return False
        
        futures_config = self.config.get('futures', {})
        leverage = futures_config.get('default_leverage', 2)
        
        self.futures_client.set_leverage(symbol, leverage)
        self.futures_client.set_margin_type(symbol, futures_config.get('margin_type', 'ISOLATED'))
        
        risk_config = futures_config.get('risk_management', {})
        stop_loss_percent = risk_config.get('stop_loss_percent', 2.0)
        take_profit_percent = risk_config.get('take_profit_percent', 4.0)
        
        if position_type in ['LONG', 'BUY']:
            stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
            take_profit_price = entry_price * (1 + take_profit_percent / 100)
        else:
            stop_loss_price = entry_price * (1 + stop_loss_percent / 100)
            take_profit_price = entry_price * (1 - take_profit_percent / 100)
        
        liquidation_price = self.calculate_liquidation_price(entry_price, leverage, position_type)
        
        if not self.validate_liquidation_buffer(entry_price, stop_loss_price, liquidation_price, position_type):
            logger.error("❌ Position rejected - Stop-Loss too close to liquidation!")
            return False
        
        if position_type in ['LONG', 'BUY']:
            order = self.futures_client.open_long_position(symbol, quantity, leverage)
        else:
            order = self.futures_client.open_short_position(symbol, quantity, leverage)
        
        if not order:
            logger.error(f"Failed to open {position_type} position for {symbol}")
            return False
        
        actual_entry_price = float(order.get('avgPrice', entry_price))
        actual_quantity = float(order.get('executedQty', quantity))
        
        trailing_config = risk_config.get('trailing_stop_loss', {})
        initial_stop = -stop_loss_percent if position_type in ['LONG', 'BUY'] else stop_loss_percent
        
        self.positions[symbol] = {
            'status': 'open',
            'entry_price': actual_entry_price,
            'quantity': actual_quantity,
            'signals': signals,
            'entry_time': str(pd.Timestamp.now()),
            'market_regime': market_regime,
            'position_type': position_type,
            'leverage': leverage,
            'liquidation_price': liquidation_price,
            'stop_loss_percent': stop_loss_percent,
            'take_profit_percent': take_profit_percent,
            'unrealized_pnl': 0.0,
            'funding_rate': None,
            'trailing_stop': {
                'enabled': trailing_config.get('enabled', True),
                'current_stop_percent': initial_stop,
                'highest_price': actual_entry_price if position_type in ['LONG', 'BUY'] else None,
                'lowest_price': actual_entry_price if position_type in ['SHORT', 'SELL'] else None,
                'activation_profit': trailing_config.get('activation_profit_percent', 3.0),
                'trail_percent': trailing_config.get('trail_percent', 2.0)
            }
        }
        
        self.save_positions()
        
        pos_emoji = "🟢" if position_type in ['LONG', 'BUY'] else "🔴"
        logger.info(f"{pos_emoji} FUTURES {position_type} opened: {symbol} @ ${actual_entry_price:.2f}")
        logger.info(f"   Quantity: {actual_quantity:.8f} | Leverage: {leverage}x")
        logger.info(f"   SL: ${stop_loss_price:.2f} | TP: ${take_profit_price:.2f}")
        logger.info(f"   Liquidation: ${liquidation_price:.2f}")
        
        return True
    
    def close_futures_position(self, symbol, exit_price, reason):
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return None
        
        position = self.positions[symbol]
        position_type = position.get('position_type', 'LONG')
        quantity = position['quantity']
        
        if not self.futures_client:
            logger.error("Cannot close futures position - client not initialized")
            return None
        
        if position_type in ['LONG', 'BUY']:
            order = self.futures_client.close_long_position(symbol, quantity)
        else:
            order = self.futures_client.close_short_position(symbol, quantity)
        
        if not order or order.get('status') != 'FILLED':
            logger.error(f"Failed to close {position_type} position for {symbol}")
            return None
        
        entry_price = position['entry_price']
        leverage = position.get('leverage', 1)
        
        if position_type in ['LONG', 'BUY']:
            profit_percent = ((exit_price - entry_price) / entry_price) * 100
        else:
            profit_percent = ((entry_price - exit_price) / entry_price) * 100
        
        profit_percent_leveraged = profit_percent * leverage
        margin_used = entry_price * quantity
        profit_usd = (margin_used * profit_percent_leveraged) / 100
        
        position['status'] = 'closed'
        position['exit_price'] = exit_price
        position['exit_time'] = str(pd.Timestamp.now())
        position['profit_percent'] = profit_percent_leveraged
        position['profit_usd'] = profit_usd
        position['close_reason'] = reason
        
        self.save_positions()
        
        profit_emoji = "💰" if profit_usd > 0 else "📉"
        pos_emoji = "🟢" if position_type in ['LONG', 'BUY'] else "🔴"
        logger.info(f"{profit_emoji} FUTURES {pos_emoji} {position_type} closed: {symbol} @ ${exit_price:.2f}")
        logger.info(f"   Profit: {profit_percent_leveraged:+.2f}% (${profit_usd:+.2f}) | Leverage: {leverage}x")
        logger.info(f"   Reason: {reason}")
        
        return position
    
    def update_futures_trailing_stop(self, symbol, current_price):
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        if position.get('status') != 'open':
            return None
        
        position_type = position.get('position_type', 'LONG')
        trailing = position.get('trailing_stop', {})
        
        if not trailing.get('enabled', False):
            return None
        
        entry_price = position['entry_price']
        
        if position_type in ['LONG', 'BUY']:
            current_profit_percent = ((current_price - entry_price) / entry_price) * 100
            
            activation_profit = trailing['activation_profit']
            if current_profit_percent < activation_profit:
                return None
            
            highest_price = trailing.get('highest_price', entry_price)
            if current_price > highest_price:
                trailing['highest_price'] = current_price
                
                profit_from_entry = ((current_price - entry_price) / entry_price) * 100
                new_stop = profit_from_entry - trailing['trail_percent']
                
                if new_stop > trailing['current_stop_percent']:
                    old_stop = trailing['current_stop_percent']
                    trailing['current_stop_percent'] = new_stop
                    position['trailing_stop'] = trailing
                    self.save_positions()
                    
                    logger.info(f"🔄 LONG Trailing stop updated for {symbol}: {old_stop:.2f}% → {new_stop:.2f}%")
                    return new_stop
        else:
            current_profit_percent = ((entry_price - current_price) / entry_price) * 100
            
            activation_profit = trailing['activation_profit']
            if current_profit_percent < activation_profit:
                return None
            
            lowest_price = trailing.get('lowest_price', entry_price)
            if current_price < lowest_price:
                trailing['lowest_price'] = current_price
                
                profit_from_entry = ((entry_price - current_price) / entry_price) * 100
                new_stop = profit_from_entry - trailing['trail_percent']
                
                if new_stop > trailing['current_stop_percent']:
                    old_stop = trailing['current_stop_percent']
                    trailing['current_stop_percent'] = new_stop
                    position['trailing_stop'] = trailing
                    self.save_positions()
                    
                    logger.info(f"🔄 SHORT Trailing stop updated for {symbol}: {old_stop:.2f}% → {new_stop:.2f}%")
                    return new_stop
        
        return trailing['current_stop_percent']
