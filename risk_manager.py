from logger_setup import setup_logger
import json
import os
from futures_risk_manager import FuturesRiskMixin

logger = setup_logger('risk_manager')

class RiskManager(FuturesRiskMixin):
    def __init__(self, config, binance_client, trading_strategy=None, db_manager=None, futures_client=None):
        self.config = config
        self.binance_client = binance_client
        self.futures_client = futures_client
        self.trading_strategy = trading_strategy
        self.db = db_manager
        self.positions_file = 'positions.json'
        self.positions = self.load_positions()
        self.futures_enabled = config.get('futures', {}).get('enabled', False)
    
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
                        entry_price = float(pos['entry_price'])
                        
                        stop_loss_price = None
                        if pos.get('stop_loss_percent'):
                            stop_loss_price = float(entry_price * (1 - float(pos['stop_loss_percent']) / 100))
                        
                        take_profit_price = None
                        if pos.get('take_profit_percent'):
                            take_profit_price = float(entry_price * (1 + float(pos['take_profit_percent']) / 100))
                        
                        trailing = pos.get('trailing_stop', {})
                        trailing_stop_price = None
                        if trailing.get('current_stop_percent'):
                            trailing_stop_price = float(entry_price * (1 - float(trailing['current_stop_percent']) / 100))
                        
                        highest_price = None
                        if trailing.get('highest_price'):
                            highest_price = float(trailing.get('highest_price'))
                        
                        position_type = pos.get('position_type', 'SPOT')
                        leverage = int(pos.get('leverage', 1))
                        liquidation_price = float(pos.get('liquidation_price')) if pos.get('liquidation_price') else None
                        unrealized_pnl = float(pos.get('unrealized_pnl')) if pos.get('unrealized_pnl') else None
                        funding_rate = float(pos.get('funding_rate')) if pos.get('funding_rate') else None
                        
                        self.db.save_position(
                            symbol=symbol,
                            entry_price=entry_price,
                            quantity=float(pos['quantity']),
                            entry_time=datetime.fromisoformat(pos['entry_time']) if isinstance(pos['entry_time'], str) else pos['entry_time'],
                            stop_loss=stop_loss_price,
                            take_profit=take_profit_price,
                            trailing_stop_price=trailing_stop_price,
                            highest_price=highest_price,
                            market_regime=pos.get('market_regime'),
                            buy_signals=pos.get('signals'),
                            position_type=position_type,
                            leverage=leverage,
                            liquidation_price=liquidation_price,
                            unrealized_pnl=unrealized_pnl,
                            funding_rate=funding_rate
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
            
            min_order_value = self.config['risk_management'].get('min_order_value_usdt', 11.0)
            if position_value < min_order_value:
                logger.warning(f"⚠️ Position value ${position_value:.2f} is below minimum ${min_order_value:.2f} - skipping trade")
                return 0
            
            if current_price and current_price > 0:
                quantity = position_value / current_price
                
                symbol_info = self.binance_client.get_symbol_info(symbol)
                if symbol_info:
                    for filter in symbol_info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            
                            # Calculate precision from step_size
                            step_size_str = f"{step_size:.10f}".rstrip('0')
                            if '.' in step_size_str:
                                precision = len(step_size_str.split('.')[1])
                            else:
                                precision = 0
                            
                            # Round to step_size and apply precision
                            quantity = round(quantity / step_size) * step_size
                            quantity = round(quantity, precision)
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
    
    def sync_positions_with_binance(self):
        """
        مزامنة الصفقات مع حساب Binance الحقيقي
        - يتحقق من الأرصدة الفعلية في Binance
        - يغلق أي "صفقات شبح" (موجودة في الذاكرة لكن غير موجودة في Binance)
        - يحدث قاعدة البيانات تلقائياً
        """
        try:
            from datetime import datetime
            
            # جلب الأرصدة الحقيقية من Binance
            binance_balances = self.binance_client.get_account_balance()
            
            # معالجة أفضل لحالات الفشل
            if not binance_balances:
                # في حالة Demo Mode أو HTTP 451، لا نستطيع المزامنة
                # نسجل تحذير واحد فقط في بداية البوت (لتجنب الضوضاء)
                if not hasattr(self, '_sync_warning_logged'):
                    logger.warning("⚠️ Real-Time Account Sync disabled - Cannot connect to Binance")
                    logger.warning("   Positions will rely on database/file tracking only")
                    logger.warning("   This is normal on Replit due to geo-restrictions")
                    self._sync_warning_logged = True
                return
            
            logger.debug("🔄 Starting Real-Time Account Sync...")
            
            open_positions = self.get_open_positions()
            if not open_positions:
                logger.debug("✅ Sync OK - No open positions to verify")
                return
            
            ghost_positions = []
            
            for symbol, position in open_positions.items():
                # الحصول على baseAsset الصحيح من معلومات الرمز
                symbol_info = self.binance_client.get_symbol_info(symbol)
                
                if symbol_info:
                    # استخدام baseAsset الرسمي من Binance
                    base_asset = symbol_info.get('baseAsset')
                else:
                    # Fallback: محاولة استخراج يدوي (لكن مع تحذير)
                    logger.warning(f"Cannot get symbol info for {symbol}, using fallback parsing")
                    # إزالة العملات المقتبسة المعروفة
                    for quote in ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB']:
                        if symbol.endswith(quote):
                            base_asset = symbol[:-len(quote)]
                            break
                    else:
                        logger.error(f"Cannot parse base asset from {symbol} - skipping sync check")
                        continue
                
                # التحقق من وجود العملة في حساب Binance
                if base_asset in binance_balances:
                    balance_qty = binance_balances[base_asset]['total']
                    position_qty = position['quantity']
                    
                    # التسامح مع فروق صغيرة (0.5%)
                    tolerance = position_qty * 0.005
                    
                    if balance_qty < (position_qty - tolerance):
                        # الرصيد في Binance أقل بكثير من المتوقع = صفقة شبح
                        logger.warning(f"👻 Ghost Position Detected: {symbol}")
                        logger.warning(f"   Expected: {position_qty:.8f} {base_asset}")
                        logger.warning(f"   Actual in Binance: {balance_qty:.8f} {base_asset}")
                        logger.warning(f"   → Position was likely sold manually")
                        ghost_positions.append(symbol)
                else:
                    # العملة غير موجودة في الحساب على الإطلاق = صفقة شبح
                    logger.warning(f"👻 Ghost Position Detected: {symbol}")
                    logger.warning(f"   Asset {base_asset} not found in Binance account")
                    logger.warning(f"   → Position was likely sold manually")
                    ghost_positions.append(symbol)
            
            # إغلاق الصفقات الشبح
            if ghost_positions:
                logger.info(f"🧹 Cleaning {len(ghost_positions)} ghost position(s)...")
                
                for symbol in ghost_positions:
                    position = self.positions[symbol]
                    
                    # حساب P/L تقريبي (نفترض سعر الخروج = آخر سعر معروف)
                    current_price = self.binance_client.get_symbol_price(symbol)
                    if not current_price:
                        current_price = position['entry_price']  # fallback
                    
                    profit_loss_percent = ((current_price - position['entry_price']) / position['entry_price']) * 100
                    profit_loss_usd = (current_price - position['entry_price']) * position['quantity']
                    
                    # إغلاق الصفقة في قاعدة البيانات أولاً (الأهم)
                    if self.db:
                        try:
                            self.db.close_trade(
                                symbol=symbol,
                                exit_price=current_price,
                                exit_time=datetime.now(),
                                profit_loss=profit_loss_usd,
                                profit_loss_percent=profit_loss_percent,
                                sell_reason='MANUAL_SELL_DETECTED'
                            )
                            self.db.delete_position(symbol)
                            logger.info(f"✅ Ghost position {symbol} closed in database")
                        except Exception as e:
                            logger.error(f"Error closing ghost position {symbol} in DB: {e}")
                    
                    # ثم تحديث الذاكرة المحلية
                    self.positions[symbol]['status'] = 'closed'
                    self.positions[symbol]['exit_price'] = current_price
                    self.positions[symbol]['exit_time'] = datetime.now().isoformat()
                    self.positions[symbol]['sell_reason'] = 'MANUAL_SELL_DETECTED'
                    self.positions[symbol]['profit_loss_percent'] = profit_loss_percent
                    self.positions[symbol]['profit_loss_usd'] = profit_loss_usd
                    
                    logger.info(f"✅ Closed ghost position: {symbol} | P/L: {profit_loss_percent:+.2f}% (${profit_loss_usd:+.2f})")
                
                # حفظ التغييرات في الملف (backup)
                self.save_positions()
                logger.info("✅ Real-Time Sync Complete - All positions now match Binance account")
            else:
                logger.debug("✅ Sync OK - All positions match Binance account")
                
        except Exception as e:
            logger.error(f"❌ Error during position sync: {e}")
            import traceback
            logger.debug(traceback.format_exc())

import pandas as pd
