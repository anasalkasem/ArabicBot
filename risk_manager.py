from logger_setup import setup_logger
import json
import os

logger = setup_logger('risk_manager')

class RiskManager:
    def __init__(self, config, binance_client, trading_strategy=None, db_manager=None):
        self.config = config
        self.binance_client = binance_client
        self.trading_strategy = trading_strategy
        self.db = db_manager
        self.positions_file = 'positions.json'
        self.positions = self.load_positions()
    
    def load_positions(self):
        if self.db:
            try:
                return self.db.get_positions()
            except Exception as e:
                logger.error(f"Error loading positions from DB: {e}")
        
        if os.path.exists(self.positions_file):
            try:
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading positions from file: {e}")
                return {}
        return {}
    
    def save_positions(self):
        if self.db:
            for symbol, pos in self.positions.items():
                if pos.get('status') == 'open':
                    try:
                        from datetime import datetime
                        self.db.save_position(
                            symbol=symbol,
                            entry_price=pos['entry_price'],
                            quantity=pos['quantity'],
                            entry_time=datetime.fromisoformat(pos['entry_time']) if isinstance(pos['entry_time'], str) else pos['entry_time'],
                            stop_loss=pos.get('stop_loss_percent'),
                            take_profit=pos.get('take_profit_percent'),
                            trailing_stop_price=pos.get('trailing_stop', {}).get('current_stop_percent'),
                            highest_price=pos.get('trailing_stop', {}).get('highest_price'),
                            market_regime=pos.get('market_regime'),
                            buy_signals=pos.get('signals')
                        )
                    except Exception as e:
                        logger.error(f"Error saving position {symbol} to DB: {e}")
        
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving positions to file: {e}")
    
    def calculate_position_size(self, symbol, current_price):
        try:
            balances = self.binance_client.get_account_balance()
            
            if not balances or 'USDT' not in balances:
                logger.warning("No USDT balance found")
                return 0
            
            usdt_balance = balances['USDT']['free']
            position_size_percent = self.config['risk_management']['position_size_percent']
            position_value = usdt_balance * (position_size_percent / 100)
            
            if current_price and current_price > 0:
                quantity = position_value / current_price
                
                symbol_info = self.binance_client.get_symbol_info(symbol)
                if symbol_info:
                    for filter in symbol_info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            quantity = round(quantity / step_size) * step_size
                            break
                
                logger.info(f"Position size for {symbol}: {quantity:.8f} (${position_value:.2f})")
                return quantity
            
            return 0
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def can_open_position(self, symbol):
        max_positions = self.config['risk_management']['max_positions']
        current_positions = len([p for p in self.positions.values() if p.get('status') == 'open'])
        
        if current_positions >= max_positions:
            logger.warning(f"Cannot open position - max positions ({max_positions}) reached")
            return False
        
        if symbol in self.positions and self.positions[symbol].get('status') == 'open':
            logger.warning(f"Position already open for {symbol}")
            return False
        
        return True
    
    def open_position(self, symbol, entry_price, quantity, signals):
        market_regime = 'sideways'
        stop_loss_multiplier = 1.0
        take_profit_multiplier = 1.0
        
        if self.trading_strategy and hasattr(self.trading_strategy, 'current_regime'):
            market_regime = self.trading_strategy.current_regime
            regime_config = self.config.get('market_regime', {})
            regime_strategy = regime_config.get(f'{market_regime}_strategy', {})
            stop_loss_multiplier = regime_strategy.get('stop_loss_multiplier', 1.0)
            take_profit_multiplier = regime_strategy.get('take_profit_multiplier', 1.0)
        
        base_stop_loss = self.config['risk_management']['stop_loss_percent']
        base_take_profit = self.config['risk_management']['take_profit_percent']
        
        adjusted_stop_loss = base_stop_loss * stop_loss_multiplier
        adjusted_take_profit = base_take_profit * take_profit_multiplier
        
        trailing_config = self.config['risk_management'].get('trailing_stop_loss', {})
        initial_stop = -adjusted_stop_loss
        
        self.positions[symbol] = {
            'status': 'open',
            'entry_price': entry_price,
            'quantity': quantity,
            'signals': signals,
            'entry_time': str(pd.Timestamp.now()),
            'market_regime': market_regime,
            'stop_loss_percent': adjusted_stop_loss,
            'take_profit_percent': adjusted_take_profit,
            'trailing_stop': {
                'enabled': trailing_config.get('enabled', False),
                'current_stop_percent': initial_stop,
                'highest_price': entry_price,
                'activation_profit': trailing_config.get('activation_profit_percent', 3.0),
                'trail_percent': trailing_config.get('trail_percent', 2.0)
            }
        }
        self.save_positions()
        logger.info(f"📈 Position opened: {symbol} @ ${entry_price:.2f}, Quantity: {quantity:.8f}")
        logger.info(f"   Regime: {market_regime.upper()} | SL: {adjusted_stop_loss:.1f}% | TP: {adjusted_take_profit:.1f}%")
    
    def close_position(self, symbol, exit_price, reason):
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return None
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        profit_percent = ((exit_price - entry_price) / entry_price) * 100
        profit_usd = (exit_price - entry_price) * quantity
        
        position['status'] = 'closed'
        position['exit_price'] = exit_price
        position['exit_time'] = str(pd.Timestamp.now())
        position['profit_percent'] = profit_percent
        position['profit_usd'] = profit_usd
        position['close_reason'] = reason
        
        self.save_positions()
        
        profit_emoji = "💰" if profit_usd > 0 else "📉"
        logger.info(f"{profit_emoji} Position closed: {symbol} @ ${exit_price:.2f}, "
                   f"Profit: {profit_percent:.2f}% (${profit_usd:.2f}), Reason: {reason}")
        
        return position
    
    def update_trailing_stop(self, symbol, current_price):
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        if position.get('status') != 'open':
            return None
        
        trailing = position.get('trailing_stop', {})
        if not trailing.get('enabled', False):
            return None
        
        entry_price = position['entry_price']
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
                
                logger.info(f"🔄 Trailing stop updated for {symbol}: "
                          f"{old_stop:.2f}% → {new_stop:.2f}% (Price: ${current_price:.2f})")
                return new_stop
        
        return trailing['current_stop_percent']
    
    def check_trailing_stop(self, symbol, current_price):
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        trailing = position.get('trailing_stop', {})
        
        if not trailing.get('enabled', False):
            return False
        
        entry_price = position['entry_price']
        current_profit_percent = ((current_price - entry_price) / entry_price) * 100
        stop_percent = trailing.get('current_stop_percent', -2.0)
        
        if current_profit_percent <= stop_percent:
            logger.warning(f"🛑 TRAILING STOP triggered for {symbol}: "
                         f"Profit {current_profit_percent:.2f}% <= Stop {stop_percent:.2f}%")
            return True
        
        return False
    
    def get_open_positions(self):
        return {k: v for k, v in self.positions.items() if v.get('status') == 'open'}
    
    def get_position(self, symbol):
        return self.positions.get(symbol)

import pandas as pd
