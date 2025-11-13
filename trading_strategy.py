from logger_setup import setup_logger
import numpy as np

logger = setup_logger('trading_strategy')

class TradingStrategy:
    def __init__(self, config):
        self.config = config
        self.rsi_oversold = config['indicators']['rsi_oversold']
        self.rsi_overbought = config['indicators']['rsi_overbought']
        self.stoch_oversold = config['indicators']['stochastic_oversold']
        self.stoch_overbought = config['indicators']['stochastic_overbought']
        self.multi_tf_enabled = config.get('multi_timeframe', {}).get('enabled', False)
        self.require_trend_alignment = config.get('multi_timeframe', {}).get('require_trend_alignment', True)
    
    def check_trend_alignment(self, medium_trend, long_trend):
        if not self.multi_tf_enabled or not self.require_trend_alignment:
            return True, "Multi-timeframe disabled"
        
        if medium_trend == 'bullish' and long_trend == 'bullish':
            return True, f"✅ Trend aligned: 1h={medium_trend}, 4h={long_trend}"
        elif medium_trend == 'bullish' and long_trend == 'neutral':
            return True, f"⚠️ Partial alignment: 1h={medium_trend}, 4h={long_trend}"
        else:
            return False, f"❌ Trend not aligned: 1h={medium_trend}, 4h={long_trend}"
    
    def check_buy_signal(self, indicators, prev_indicators=None, medium_trend=None, long_trend=None):
        try:
            if not indicators or np.isnan(indicators['rsi']):
                return False, []
            
            signals = []
            
            if self.multi_tf_enabled:
                trend_ok, trend_msg = self.check_trend_alignment(medium_trend, long_trend)
                if not trend_ok:
                    logger.debug(f"Buy signal rejected: {trend_msg}")
                    return False, []
                signals.append(trend_msg)
            
            rsi_condition = indicators['rsi'] < self.rsi_oversold
            if rsi_condition:
                signals.append(f"RSI={indicators['rsi']:.2f} < {self.rsi_oversold}")
            
            stoch_condition = indicators['stoch_k'] < self.stoch_oversold
            if stoch_condition:
                signals.append(f"Stochastic K={indicators['stoch_k']:.2f} < {self.stoch_oversold}")
            
            bb_condition = indicators['close'] <= indicators['bb_lower']
            if bb_condition:
                signals.append(f"Price={indicators['close']:.2f} touching lower BB={indicators['bb_lower']:.2f}")
            
            ema_bullish = indicators['ema_short'] > indicators['ema_long']
            if ema_bullish:
                signals.append(f"EMA bullish: {indicators['ema_short']:.2f} > {indicators['ema_long']:.2f}")
            
            buy_signal = rsi_condition and stoch_condition and bb_condition
            
            if self.multi_tf_enabled:
                buy_signal = buy_signal and self.check_trend_alignment(medium_trend, long_trend)[0]
            
            if buy_signal:
                logger.info(f"✅ BUY SIGNAL DETECTED: {', '.join(signals)}")
            
            return buy_signal, signals
            
        except Exception as e:
            logger.error(f"Error checking buy signal: {e}")
            return False, []
    
    def check_sell_signal(self, indicators, entry_price=None, prev_indicators=None):
        try:
            if not indicators or np.isnan(indicators['rsi']):
                return False, [], None
            
            signals = []
            sell_reason = None
            
            rsi_condition = indicators['rsi'] > self.rsi_overbought
            if rsi_condition:
                signals.append(f"RSI={indicators['rsi']:.2f} > {self.rsi_overbought}")
                sell_reason = "RSI_OVERBOUGHT"
            
            if entry_price:
                profit_percent = ((indicators['close'] - entry_price) / entry_price) * 100
                take_profit_target = self.config['risk_management']['take_profit_percent']
                
                if profit_percent >= take_profit_target:
                    signals.append(f"Profit={profit_percent:.2f}% >= Target={take_profit_target}%")
                    sell_reason = "TAKE_PROFIT"
            
            if prev_indicators and not np.isnan(prev_indicators.get('macd_hist', np.nan)):
                macd_bearish_cross = (
                    prev_indicators['macd_hist'] > 0 and 
                    indicators['macd_hist'] < 0
                )
                if macd_bearish_cross:
                    signals.append("MACD bearish crossover detected")
                    if not sell_reason:
                        sell_reason = "MACD_BEARISH_CROSS"
            
            sell_signal = len(signals) > 0
            
            if sell_signal:
                logger.info(f"❌ SELL SIGNAL DETECTED ({sell_reason}): {', '.join(signals)}")
            
            return sell_signal, signals, sell_reason
            
        except Exception as e:
            logger.error(f"Error checking sell signal: {e}")
            return False, [], None
    
    def should_stop_loss(self, current_price, entry_price):
        try:
            if not entry_price or entry_price == 0:
                return False
            
            loss_percent = ((current_price - entry_price) / entry_price) * 100
            stop_loss_threshold = -self.config['risk_management']['stop_loss_percent']
            
            if loss_percent <= stop_loss_threshold:
                logger.warning(f"⛔ STOP LOSS TRIGGERED: Loss={loss_percent:.2f}% <= {stop_loss_threshold}%")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking stop loss: {e}")
            return False
