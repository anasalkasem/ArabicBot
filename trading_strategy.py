from logger_setup import setup_logger
import numpy as np

logger = setup_logger('trading_strategy')

class TradingStrategy:
    def __init__(self, config):
        self.config = config
        self.base_rsi_oversold = config['indicators']['rsi_oversold']
        self.rsi_oversold = self.base_rsi_oversold
        self.rsi_overbought = config['indicators']['rsi_overbought']
        self.base_stoch_oversold = config['indicators']['stochastic_oversold']
        self.stoch_oversold = self.base_stoch_oversold
        self.stoch_overbought = config['indicators']['stochastic_overbought']
        self.base_bb_tolerance = 1 + (config['indicators']['bb_tolerance'] / 100)
        self.bb_tolerance = self.base_bb_tolerance
        self.multi_tf_enabled = config.get('multi_timeframe', {}).get('enabled', False)
        self.require_trend_alignment = config.get('multi_timeframe', {}).get('require_trend_alignment', True)
        
        self.regime_enabled = config.get('market_regime', {}).get('enabled', False)
        self.regime_config = config.get('market_regime', {})
        self.current_regime = 'sideways'
        self.current_regime_reason = 'Not yet detected'
        
        self.weaver_enabled = config.get('dynamic_strategy_weaver', {}).get('enabled', False)
        self.min_confidence = config.get('dynamic_strategy_weaver', {}).get('min_confidence_threshold', 0.50)
    
    def get_individual_indicator_signals(self, indicators, prev_indicators=None):
        """
        استخراج إشارات كل مؤشر على حدة (لتتبع الأداء)
        Returns: dict مع boolean لكل مؤشر
        """
        try:
            if not indicators or np.isnan(indicators.get('rsi', np.nan)):
                return {}
            
            signals = {}
            
            signals['rsi'] = indicators['rsi'] < self.rsi_oversold
            
            signals['stochastic'] = indicators.get('stoch_k', 100) < self.stoch_oversold
            
            signals['bollinger_bands'] = indicators['close'] <= (indicators.get('bb_lower', 0) * self.bb_tolerance)
            
            if prev_indicators and not np.isnan(prev_indicators.get('macd_hist', np.nan)):
                macd_bullish = (
                    prev_indicators.get('macd_hist', 0) < 0 and 
                    indicators.get('macd_hist', 0) > 0
                )
                signals['macd'] = macd_bullish
            else:
                signals['macd'] = indicators.get('macd_hist', 0) > 0
            
            return signals
        except Exception as e:
            logger.error(f"Error extracting individual signals: {e}")
            return {}
    
    def check_trend_alignment(self, medium_trend, long_trend):
        if not self.multi_tf_enabled or not self.require_trend_alignment:
            return True, "Multi-timeframe disabled"
        
        if medium_trend is None or long_trend is None:
            return True, "Multi-timeframe data unavailable, proceeding"
        
        if medium_trend == 'bullish' and long_trend == 'bullish':
            return True, f"✅ Trend aligned: 1h={medium_trend}, 4h={long_trend}"
        elif medium_trend == 'bullish' and long_trend == 'neutral':
            return True, f"⚠️ Partial alignment: 1h={medium_trend}, 4h={long_trend}"
        elif medium_trend == 'neutral' and long_trend in ['bullish', 'neutral']:
            return True, f"⚠️ Neutral trend acceptable: 1h={medium_trend}, 4h={long_trend}"
        elif medium_trend == 'bearish' and long_trend == 'neutral':
            return True, f"⚠️ Acceptable: 1h={medium_trend}, 4h={long_trend} (only one bearish)"
        elif medium_trend == 'neutral' and long_trend == 'bearish':
            return True, f"⚠️ Acceptable: 1h={medium_trend}, 4h={long_trend} (only one bearish)"
        elif medium_trend == 'bearish' and long_trend == 'bearish':
            return False, f"❌ Both bearish: 1h={medium_trend}, 4h={long_trend}"
        else:
            return False, f"❌ Trend not aligned: 1h={medium_trend}, 4h={long_trend}"
    
    def adapt_to_regime(self, regime, reason):
        """
        تكييف الاستراتيجية بناءً على حالة السوق
        """
        self.current_regime = regime
        self.current_regime_reason = reason
        
        if not self.regime_enabled:
            return
        
        if regime == 'bull':
            bull_config = self.regime_config.get('bull_strategy', {})
            self.rsi_oversold = self.base_rsi_oversold + bull_config.get('rsi_oversold_adjustment', 5)
            self.stoch_oversold = self.base_stoch_oversold + bull_config.get('stoch_oversold_adjustment', 5)
            bb_adjustment = bull_config.get('bb_tolerance_adjustment', 0.5)
            self.bb_tolerance = self.base_bb_tolerance + (bb_adjustment / 100)
            logger.info(f"🐂 Adapted to BULL market: RSI<{self.rsi_oversold}, Stoch<{self.stoch_oversold}, BB tolerance={((self.bb_tolerance-1)*100):.1f}%")
        
        elif regime == 'bear':
            bear_config = self.regime_config.get('bear_strategy', {})
            self.rsi_oversold = self.base_rsi_oversold + bear_config.get('rsi_oversold_adjustment', -15)
            self.stoch_oversold = self.base_stoch_oversold + bear_config.get('stoch_oversold_adjustment', -20)
            bb_adjustment = bear_config.get('bb_tolerance_adjustment', -0.5)
            self.bb_tolerance = self.base_bb_tolerance + (bb_adjustment / 100)
            logger.warning(f"🐻 BEAR market detected - Very conservative: RSI<{self.rsi_oversold}, Stoch<{self.stoch_oversold}, BB tolerance={((self.bb_tolerance-1)*100):.1f}%")
        
        else:
            self.rsi_oversold = self.base_rsi_oversold
            self.stoch_oversold = self.base_stoch_oversold
            self.bb_tolerance = self.base_bb_tolerance
            logger.info(f"↔️ Adapted to SIDEWAYS market: Using standard strategy")
    
    def check_buy_signal(self, indicators, prev_indicators=None, medium_trend=None, long_trend=None, market_regime=None, momentum_index=None, performance_tracker=None, symbol=None):
        try:
            if not indicators or np.isnan(indicators['rsi']):
                return False, [], {}
            
            signals = []
            
            indicator_signals_map = self.get_individual_indicator_signals(indicators, prev_indicators)
            
            buy_confidence = 0.0
            if self.weaver_enabled and performance_tracker and symbol:
                try:
                    buy_confidence = performance_tracker.get_buy_confidence(
                        symbol=symbol,
                        indicator_signals=indicator_signals_map,
                        timeframe=self.config['trading']['candle_interval']
                    )
                    
                    if buy_confidence < self.min_confidence:
                        logger.debug(f"🧠 Dynamic Weaver: Low confidence ({buy_confidence:.2%} < {self.min_confidence:.2%}) - rejecting buy")
                        return False, [f"Low AI confidence: {buy_confidence:.2%} < {self.min_confidence:.2%}"], indicator_signals_map
                    
                    signals.append(f"🧠 AI Confidence: {buy_confidence:.2%}")
                except Exception as e:
                    logger.warning(f"Error calculating buy confidence: {e}")
                    buy_confidence = 0.0
            
            if market_regime and self.regime_enabled and market_regime == 'bear':
                bear_config = self.regime_config.get('bear_strategy', {})
                if not bear_config.get('allow_new_trades', True):
                    logger.debug(f"🐻 Buy rejected: Bear market - trading disabled")
                    return False, [f"Bear market: {self.current_regime_reason}"], indicator_signals_map
            
            strong_momentum_threshold = self.config.get('custom_momentum', {}).get('strong_momentum_threshold', 35)
            has_strong_momentum = momentum_index is not None and momentum_index < strong_momentum_threshold
            
            if self.multi_tf_enabled:
                trend_ok, trend_msg = self.check_trend_alignment(medium_trend, long_trend)
                if not trend_ok:
                    if has_strong_momentum:
                        logger.info(f"🚀 STRONG MOMENTUM OVERRIDE: Ignoring bearish trends (momentum={momentum_index:.1f} < {strong_momentum_threshold})")
                        signals.append(f"⚡ Strong Momentum Override: {momentum_index:.1f} < {strong_momentum_threshold}")
                    else:
                        logger.debug(f"Buy signal rejected: {trend_msg}")
                        return False, [], indicator_signals_map
                else:
                    signals.append(trend_msg)
            
            rsi_condition = indicators['rsi'] < self.rsi_oversold
            if rsi_condition:
                signals.append(f"RSI={indicators['rsi']:.2f} < {self.rsi_oversold}")
            
            stoch_condition = indicators['stoch_k'] < self.stoch_oversold
            if stoch_condition:
                signals.append(f"Stochastic K={indicators['stoch_k']:.2f} < {self.stoch_oversold}")
            
            bb_condition = indicators['close'] <= (indicators['bb_lower'] * self.bb_tolerance)
            if bb_condition:
                price_diff_pct = ((indicators['close'] - indicators['bb_lower']) / indicators['bb_lower']) * 100
                signals.append(f"Price={indicators['close']:.2f} near BB lower={indicators['bb_lower']:.2f} ({price_diff_pct:+.2f}%)")
            
            ema_bullish = indicators['ema_short'] > indicators['ema_long']
            if ema_bullish:
                signals.append(f"EMA bullish: {indicators['ema_short']:.2f} > {indicators['ema_long']:.2f}")
            
            buy_signal = rsi_condition and stoch_condition and bb_condition
            
            if self.multi_tf_enabled:
                buy_signal = buy_signal and self.check_trend_alignment(medium_trend, long_trend)[0]
            
            if buy_signal:
                logger.info(f"✅ BUY SIGNAL DETECTED: {', '.join(signals)}")
            
            return buy_signal, signals, indicator_signals_map
            
        except Exception as e:
            logger.error(f"Error checking buy signal: {e}")
            return False, [], {}
    
    def check_sell_signal(self, indicators, entry_price=None, prev_indicators=None, market_regime=None, position=None):
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
                
                take_profit_percent = self.config['risk_management']['take_profit_percent']
                if position and 'take_profit_percent' in position:
                    take_profit_percent = position['take_profit_percent']
                
                if profit_percent >= take_profit_percent:
                    signals.append(f"Profit={profit_percent:.2f}% >= Target={take_profit_percent:.1f}%")
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
    
    def should_stop_loss(self, current_price, entry_price, position=None):
        try:
            if not entry_price or entry_price == 0:
                return False
            
            loss_percent = ((current_price - entry_price) / entry_price) * 100
            
            stop_loss_percent = self.config['risk_management']['stop_loss_percent']
            if position and 'stop_loss_percent' in position:
                stop_loss_percent = position['stop_loss_percent']
            
            stop_loss_threshold = -stop_loss_percent
            
            if loss_percent <= stop_loss_threshold:
                logger.warning(f"⛔ STOP LOSS TRIGGERED: Loss={loss_percent:.2f}% <= {stop_loss_threshold}%")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking stop loss: {e}")
            return False
