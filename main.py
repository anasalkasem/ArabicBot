import json
import time
import os
import threading
import asyncio
from datetime import datetime
from flask import Flask, jsonify, render_template
from binance_client import BinanceClientManager
from binance_derivatives_client import BinanceDerivativesClient
from technical_indicators import TechnicalIndicators
from trading_strategy import TradingStrategy
from risk_manager import RiskManager
from telegram_notifier import TelegramNotifier
from statistics_tracker import StatisticsTracker
from market_regime import MarketRegime
from sentiment_analyzer import SentimentAnalyzer
from custom_momentum import CustomMomentumIndex
from indicator_performance_tracker import IndicatorPerformanceTracker
from strategy_coordinator import StrategyCoordinator
from logger_setup import setup_logger
from db_manager import DatabaseManager
from telegram_bot import TelegramBotController
from swarm_intelligence import SwarmManager
from causal_inference import CausalInferenceEngine

logger = setup_logger('main_bot')

try:
    from ai_market_analyzer import AIMarketAnalyzer
    AI_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ AI features disabled - openai package not installed")
    AIMarketAnalyzer = None
    AI_AVAILABLE = False
app = Flask(__name__)

# قائمة السجلات للعرض في الواجهة
recent_logs = []
MAX_LOGS = 50

bot_instance = None
telegram_bot_instance = None
trading_enabled = True
bot_stats = {
    'status': 'initializing',
    'iterations': 0,
    'start_time': None,
    'last_check': None
}

class BinanceTradingBot:
    def __init__(self, config_file='config.json'):
        logger.info("=" * 80)
        logger.info("🤖 Binance Trading Bot Starting...")
        logger.info("=" * 80)
        
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.testnet = self.config.get('testnet', True)
        self.trading_pairs = self.config['trading_pairs']
        self.check_interval = self.config['trading']['check_interval_seconds']
        
        self.futures_enabled = self.config.get('futures', {}).get('enabled', False)
        
        logger.info(f"Mode: {'TESTNET' if self.testnet else 'LIVE TRADING'}")
        logger.info(f"Trading Pairs: {', '.join(self.trading_pairs)}")
        
        if self.futures_enabled:
            logger.info("🔥 FUTURES TRADING ENABLED")
        else:
            logger.info("💰 SPOT TRADING ONLY")
        
        try:
            self.db = DatabaseManager()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.db = None
        
        self.binance_client = BinanceClientManager(testnet=self.testnet)
        
        if self.futures_enabled:
            futures_testnet = self.config.get('futures', {}).get('testnet', True)
            try:
                self.futures_client = BinanceDerivativesClient(testnet=futures_testnet)
                logger.info(f"✅ Futures Client initialized ({'TESTNET' if futures_testnet else 'LIVE'})")
            except Exception as e:
                logger.error(f"❌ Futures Client initialization failed: {e}")
                self.futures_client = None
                self.futures_enabled = False
        else:
            self.futures_client = None
        
        self.technical_indicators = TechnicalIndicators(self.config)
        self.trading_strategy = TradingStrategy(self.config)
        
        if self.futures_enabled and self.futures_client:
            self.strategy_coordinator = StrategyCoordinator(self.config)
            logger.info("✅ Strategy Coordinator initialized")
        else:
            self.strategy_coordinator = None
        
        self.risk_manager = RiskManager(
            self.config, 
            self.binance_client, 
            self.trading_strategy, 
            db_manager=self.db,
            futures_client=self.futures_client
        )
        self.telegram = TelegramNotifier(self.config)
        self.stats = StatisticsTracker(db_manager=self.db)
        self.market_regime = MarketRegime(self.config)
        self.sentiment_analyzer = SentimentAnalyzer(self.config)
        self.custom_momentum = CustomMomentumIndex(self.config, self.sentiment_analyzer)
        self.performance_tracker = IndicatorPerformanceTracker(db_manager=self.db)
        
        if AI_AVAILABLE:
            self.ai_analyzer = AIMarketAnalyzer()
        else:
            self.ai_analyzer = None
        
        self.prev_indicators = {}
        self.prev_indicator_signals = {}
        self.symbol_momentum_cache = {}
        self.multi_tf_enabled = self.config.get('multi_timeframe', {}).get('enabled', False)
        self.regime_enabled = self.config.get('market_regime', {}).get('enabled', False)
        self.momentum_enabled = self.config.get('custom_momentum', {}).get('enabled', False)
        self.weaver_enabled = True
        self.pending_resolutions = self.performance_tracker.pending_resolutions
        
        if self.multi_tf_enabled:
            logger.info("✨ Multi-Timeframe Analysis: ENABLED")
        
        if self.regime_enabled:
            logger.info("✨ Market Regime Adaptation: ENABLED")
        
        if self.momentum_enabled:
            logger.info("✨ Custom Momentum Index: ENABLED")
        
        if self.weaver_enabled:
            logger.info("✨ Dynamic Strategy Weaver: ENABLED (MVP mode)")
            if self.config.get('dynamic_strategy_weaver', {}).get('enabled', False):
                min_confidence = self.config['dynamic_strategy_weaver']['min_confidence_threshold']
                logger.info(f"   🎯 Min confidence threshold: {min_confidence:.2%}")
                logger.info(f"   📊 Learning period: {self.config['dynamic_strategy_weaver']['learning_period_days']} days")
        
        self.swarm_enabled = self.config.get('swarm_intelligence', {}).get('enabled', False)
        if self.swarm_enabled:
            try:
                num_workers = self.config['swarm_intelligence']['num_workers']
                self.swarm = SwarmManager(num_workers=num_workers)
                logger.info(f"🐝 Swarm Intelligence: ENABLED ({num_workers} worker bots)")
                logger.info(f"   📊 Decision mode: Collective Voting")
                logger.info(f"   💡 Paper trading: Active")
            except Exception as e:
                logger.error(f"❌ Swarm initialization failed: {e}")
                self.swarm_enabled = False
                self.swarm = None
        else:
            self.swarm = None
        
        self.causal_enabled = self.config.get('causal_inference', {}).get('enabled', True)
        if self.causal_enabled:
            try:
                self.causal_engine = CausalInferenceEngine(db_manager=self.db)
                logger.info("🧠 Causal Inference Engine: ENABLED")
                logger.info("   📊 Analysis type: Structural Causal Models")
                logger.info("   🎯 Filtering: Spurious Correlations")
                logger.info("   💡 Method: Do-Calculus & Granger Causality")
            except Exception as e:
                logger.error(f"❌ Causal Inference initialization failed: {e}")
                self.causal_enabled = False
                self.causal_engine = None
        else:
            self.causal_engine = None
        
        trailing_enabled = self.config.get('risk_management', {}).get('trailing_stop_loss', {}).get('enabled', False)
        if trailing_enabled:
            logger.info("✨ Trailing Stop-Loss: ENABLED")
        
        if self.ai_analyzer and self.ai_analyzer.enabled:
            logger.info("🤖 AI Market Analyzer: ENABLED (GPT-4)")
            logger.info("   Features: Market Analysis, Strategy Audit, Telegram Chat")
        elif AI_AVAILABLE and self.ai_analyzer:
            logger.info("⚠️ AI Market Analyzer: DISABLED (No OpenAI API key)")
        else:
            logger.info("⚠️ AI Market Analyzer: UNAVAILABLE (Install openai package)")
        
        logger.info("✅ Bot initialized successfully")
        logger.info("=" * 80)
    
    def display_account_info(self):
        logger.info("\n💼 Account Balance:")
        balances = self.binance_client.get_account_balance()
        if balances:
            for asset, balance in balances.items():
                if balance['total'] > 0:
                    logger.info(f"  {asset}: {balance['total']:.8f} (Free: {balance['free']:.8f})")
        else:
            logger.warning("  Running in DEMO mode - no real balance available")
        logger.info("")
    
    def analyze_symbol(self, symbol, timeframe=None):
        try:
            if timeframe is None:
                timeframe = self.config['trading']['candle_interval']
            
            klines = self.binance_client.get_historical_klines(symbol, timeframe, limit=100)
            
            if not klines:
                return None
            
            df = self.technical_indicators.calculate_all_indicators(klines)
            if df is None or df.empty:
                return None
            
            indicators = self.technical_indicators.get_latest_values(df)
            trend = self.technical_indicators.analyze_trend(df)
            
            return indicators, trend
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} on {timeframe}: {e}")
            return None
    
    def get_24h_data(self, symbol):
        """
        الحصول على بيانات 24 ساعة (volume avg, open price)
        Returns: (volume_avg, open_24h)
        """
        try:
            klines = self.binance_client.get_historical_klines(symbol, '1h', limit=24)
            if not klines or len(klines) < 2:
                return None, None
            
            volumes = [float(candle[5]) for candle in klines]
            volume_avg = sum(volumes) / len(volumes)
            
            open_24h = float(klines[0][1])
            
            return volume_avg, open_24h
        except Exception as e:
            logger.error(f"Error getting 24h data for {symbol}: {e}")
            return None, None
    
    def calculate_btc_change_24h(self):
        """حساب تغير سعر BTC خلال 24 ساعة"""
        try:
            klines = self.binance_client.get_historical_klines('BTCUSDT', '1h', limit=24)
            if not klines or len(klines) < 2:
                return None
            
            open_price = float(klines[0][1])
            close_price = float(klines[-1][4])
            
            change_percent = ((close_price - open_price) / open_price) * 100
            return change_percent
        except Exception as e:
            logger.error(f"Error calculating BTC 24h change: {e}")
            return None
    
    def analyze_multi_timeframe(self, symbol):
        try:
            short_tf = self.config['multi_timeframe']['short_timeframe']
            medium_tf = self.config['multi_timeframe']['medium_timeframe']
            long_tf = self.config['multi_timeframe']['long_timeframe']
            
            short_result = self.analyze_symbol(symbol, short_tf)
            medium_result = self.analyze_symbol(symbol, medium_tf)
            long_result = self.analyze_symbol(symbol, long_tf)
            
            if not short_result:
                return None
            
            short_indicators, short_trend = short_result
            medium_trend = medium_result[1] if medium_result else 'neutral'
            long_trend = long_result[1] if long_result else 'neutral'
            
            prev_indicators = self.prev_indicators.get(symbol)
            self.prev_indicators[symbol] = short_indicators
            
            return short_indicators, prev_indicators, medium_trend, long_trend
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis for {symbol}: {e}")
            return None
    
    def process_symbol(self, symbol):
        try:
            if self.multi_tf_enabled:
                result = self.analyze_multi_timeframe(symbol)
                if not result:
                    return
                indicators, prev_indicators, medium_trend, long_trend = result
                short_trend = 'neutral'
            else:
                result = self.analyze_symbol(symbol)
                if not result:
                    return
                indicators, trend = result
                prev_indicators = self.prev_indicators.get(symbol)
                self.prev_indicators[symbol] = indicators
                short_trend = trend if trend else 'neutral'
                medium_trend = None
                long_trend = None
            
            if not indicators:
                return
            
            current_price = indicators['close']
            
            market_regime = 'sideways'
            regime_reason = 'Not detected'
            if self.regime_enabled:
                timeframe = self.config['trading']['candle_interval']
                klines = self.binance_client.get_historical_klines(symbol, timeframe, limit=100)
                market_regime, regime_reason = self.market_regime.detect_regime(indicators, klines)
                self.trading_strategy.adapt_to_regime(market_regime, regime_reason)
            
            swarm_vote = self.get_swarm_decision(symbol, indicators)
            
            position = self.risk_manager.get_position(symbol)
            
            if position and position.get('status') == 'open':
                entry_price = position['entry_price']
                position_type = position.get('position_type', 'SPOT')
                
                if self.futures_enabled and position_type in ['LONG', 'SHORT']:
                    self.risk_manager.update_futures_trailing_stop(symbol, current_price)
                    
                    should_exit, exit_reason, profit_pct = self.strategy_coordinator.check_exit_signal(
                        symbol, position, current_price, indicators
                    )
                    
                    if should_exit:
                        logger.info(f"💵 Closing {position_type} {symbol} at ${current_price:.2f} ({exit_reason})")
                        closed_position = self.risk_manager.close_futures_position(symbol, current_price, exit_reason)
                        if closed_position:
                            self.stats.record_trade(symbol, entry_price, current_price, position['quantity'], exit_reason)
                            self.telegram.notify_sell(symbol, current_price, position['quantity'], entry_price, exit_reason)
                else:
                    self.risk_manager.update_trailing_stop(symbol, current_price)
                    
                    if self.risk_manager.check_trailing_stop(symbol, current_price):
                        logger.warning(f"🛑 TRAILING STOP triggered for {symbol}")
                        order = self.binance_client.create_market_order(
                            symbol=symbol,
                            side='SELL',
                            quantity=position['quantity']
                        )
                        if order:
                            self.risk_manager.close_position(symbol, current_price, "TRAILING_STOP")
                            self.stats.record_trade(symbol, entry_price, current_price, position['quantity'], "TRAILING_STOP")
                            self.telegram.notify_sell(symbol, current_price, position['quantity'], entry_price, "TRAILING_STOP")
                        return
                    
                    if self.trading_strategy.should_stop_loss(current_price, entry_price, position):
                        logger.warning(f"🛑 STOP LOSS triggered for {symbol}")
                        order = self.binance_client.create_market_order(
                            symbol=symbol,
                            side='SELL',
                            quantity=position['quantity']
                        )
                        if order:
                            self.risk_manager.close_position(symbol, current_price, "STOP_LOSS")
                            self.stats.record_trade(symbol, entry_price, current_price, position['quantity'], "STOP_LOSS")
                            self.telegram.notify_sell(symbol, current_price, position['quantity'], entry_price, "STOP_LOSS")
                        return
                    
                    sell_signal, signals, reason = self.trading_strategy.check_sell_signal(
                        indicators, entry_price, prev_indicators, market_regime, position
                    )
                    
                    if sell_signal:
                        logger.info(f"💵 Selling {symbol} at ${current_price:.2f}")
                        order = self.binance_client.create_market_order(
                            symbol=symbol,
                            side='SELL',
                            quantity=position['quantity']
                        )
                        if order:
                            self.risk_manager.close_position(symbol, current_price, reason)
                            self.stats.record_trade(symbol, entry_price, current_price, position['quantity'], reason)
                            self.telegram.notify_sell(symbol, current_price, position['quantity'], entry_price, reason)
            
            else:
                logger.info(f"   📊 RSI: {indicators['rsi']:.1f} | Stoch: {indicators['stoch_k']:.1f} | "
                          f"Price: ${current_price:.2f} | BB Lower: ${indicators['bb_lower']:.2f}")
                logger.info(f"   📈 Trends: 5m={short_trend}, 1h={medium_trend}, 4h={long_trend}")
                if self.regime_enabled:
                    regime_emoji = {'bull': '🐂', 'bear': '🐻', 'sideways': '↔️'}
                    logger.info(f"   {regime_emoji.get(market_regime, '📊')} Market Regime: {market_regime.upper()}")
                
                momentum_index = None
                momentum_components = None
                if self.momentum_enabled:
                    try:
                        volume_24h_avg, symbol_open_24h = self.get_24h_data(symbol)
                        btc_change_24h = self.calculate_btc_change_24h()
                        
                        momentum_index, momentum_components = self.custom_momentum.compute(
                            symbol, indicators, volume_24h_avg=volume_24h_avg, btc_change_24h=btc_change_24h, symbol_open_24h=symbol_open_24h
                        )
                        
                        if momentum_index is not None:
                            self.symbol_momentum_cache[symbol] = momentum_index
                            logger.info(f"   🎯 Custom Momentum Index for {symbol}: {momentum_index:.1f}/100 ✓")
                        else:
                            logger.warning(f"   ⚠️ Failed to compute Custom Momentum for {symbol} - skipping momentum check")
                            if symbol in self.symbol_momentum_cache:
                                del self.symbol_momentum_cache[symbol]
                    except Exception as e:
                        logger.error(f"   ❌ Error computing Custom Momentum for {symbol}: {e}")
                        momentum_index = None
                        if symbol in self.symbol_momentum_cache:
                            del self.symbol_momentum_cache[symbol]
                
                buy_signal, signals, indicator_signals = self.trading_strategy.check_buy_signal(
                    indicators, prev_indicators, medium_trend, long_trend, market_regime, momentum_index,
                    performance_tracker=self.performance_tracker, symbol=symbol
                )
                
                if self.weaver_enabled and self.config.get('dynamic_strategy_weaver', {}).get('enabled', False):
                    try:
                        weights = self.performance_tracker.get_indicator_weights(symbol, self.config['trading']['candle_interval'])
                        logger.debug(f"   🧠 Dynamic Weights for {symbol}: RSI={weights['rsi']:.2%}, Stoch={weights['stochastic']:.2%}, BB={weights['bollinger_bands']:.2%}, MACD={weights['macd']:.2%}")
                    except Exception as e:
                        logger.debug(f"Error displaying weights: {e}")
                
                if self.weaver_enabled and indicator_signals:
                    try:
                        if self.multi_tf_enabled:
                            timeframe = self.config['multi_timeframe']['short_timeframe']
                        else:
                            timeframe = self.config['trading']['candle_interval']
                        
                        signal_timestamp = time.time()
                        prev_signals = self.prev_indicator_signals.get(symbol, {})
                        
                        for indicator_name, is_bullish in indicator_signals.items():
                            self.performance_tracker.track_signal(
                                symbol, indicator_name, timeframe,
                                is_bullish, current_price
                            )
                            
                            prev_bullish = prev_signals.get(indicator_name, False)
                            
                            if is_bullish and not prev_bullish:
                                self.pending_resolutions.append({
                                    'symbol': symbol,
                                    'indicator': indicator_name,
                                    'timeframe': timeframe,
                                    'timestamp': signal_timestamp,
                                    'price': current_price,
                                    'was_bullish': is_bullish
                                })
                                logger.debug(f"📍 {indicator_name} flipped bullish for {symbol} @ ${current_price:.2f}")
                        
                        self.prev_indicator_signals[symbol] = indicator_signals.copy()
                    except Exception as e:
                        logger.error(f"Error tracking indicators: {e}")
                
                if self.momentum_enabled:
                    cached_momentum = self.symbol_momentum_cache.get(symbol)
                    if cached_momentum is not None and momentum_index is not None and abs(cached_momentum - momentum_index) < 0.01:
                        if not self.custom_momentum.should_buy(momentum_index):
                            buy_signal = False
                            logger.info(f"   ⏭️ Custom Momentum for {symbol}: No buy (index={momentum_index:.1f}, need <{self.custom_momentum.buy_threshold})")
                        else:
                            logger.info(f"   ✅ Custom Momentum for {symbol}: BUY signal (index={momentum_index:.1f} < {self.custom_momentum.buy_threshold})")
                    elif momentum_index is None:
                        logger.warning(f"   ⚠️ Custom Momentum check skipped for {symbol} - momentum_index is None")
                    else:
                        logger.error(f"   ❌ CRITICAL: Momentum data mismatch for {symbol}! Expected cached={cached_momentum}, got computed={momentum_index}")
                        buy_signal = False
                
                if buy_signal and self.risk_manager.can_open_position(symbol):
                    if self.futures_enabled and self.strategy_coordinator:
                        allowed_strategies = self.strategy_coordinator.get_allowed_strategies(market_regime)
                        position_opened = False
                        
                        if 'LONG' in allowed_strategies:
                            should_long, long_reason = self.strategy_coordinator.long_strategy.check_entry_signal(
                                symbol, indicators, market_regime, {
                                    'short_trend': short_trend,
                                    'medium_trend': medium_trend,
                                    'long_trend': long_trend
                                }
                            )
                            
                            if should_long:
                                quantity = self.risk_manager.calculate_futures_position_size(symbol, current_price)
                                if quantity > 0:
                                    success = self.risk_manager.open_futures_position(
                                        symbol=symbol,
                                        entry_price=current_price,
                                        quantity=quantity,
                                        position_type='LONG',
                                        signals=signals,
                                        market_regime=market_regime
                                    )
                                    if success:
                                        position_opened = True
                                        self.telegram.notify_buy(symbol, current_price, quantity, signals)
                        
                        if not position_opened and 'SHORT' in allowed_strategies:
                            should_short, short_reason = self.strategy_coordinator.short_strategy.check_entry_signal(
                                symbol, indicators, market_regime, {
                                    'short_trend': short_trend,
                                    'medium_trend': medium_trend,
                                    'long_trend': long_trend
                                }
                            )
                            
                            if should_short:
                                quantity = self.risk_manager.calculate_futures_position_size(symbol, current_price)
                                if quantity > 0:
                                    success = self.risk_manager.open_futures_position(
                                        symbol=symbol,
                                        entry_price=current_price,
                                        quantity=quantity,
                                        position_type='SHORT',
                                        signals=signals,
                                        market_regime=market_regime
                                    )
                                    if success:
                                        position_opened = True
                                        self.telegram.notify_buy(symbol, current_price, quantity, signals)
                    else:
                        quantity = self.risk_manager.calculate_position_size(symbol, current_price)
                        
                        if quantity > 0:
                            logger.info(f"💸 Buying {symbol} at ${current_price:.2f}")
                            order = self.binance_client.create_market_order(
                                symbol=symbol,
                                side='BUY',
                                quantity=quantity
                            )
                            if order:
                                self.risk_manager.open_position(symbol, current_price, quantity, signals)
                                self.telegram.notify_buy(symbol, current_price, quantity, signals)
                elif not buy_signal:
                    reasons = []
                    rsi_threshold = self.trading_strategy.rsi_oversold
                    stoch_threshold = self.trading_strategy.stoch_oversold
                    bb_tolerance_pct = ((self.trading_strategy.bb_tolerance - 1) * 100)
                    
                    if indicators['rsi'] >= rsi_threshold:
                        reasons.append(f"RSI={indicators['rsi']:.1f} (need <{rsi_threshold})")
                    if indicators['stoch_k'] >= stoch_threshold:
                        reasons.append(f"Stoch={indicators['stoch_k']:.1f} (need <{stoch_threshold})")
                    
                    bb_tolerance_price = indicators['bb_lower'] * self.trading_strategy.bb_tolerance
                    if current_price > bb_tolerance_price:
                        price_diff_pct = ((current_price - indicators['bb_lower']) / indicators['bb_lower']) * 100
                        reasons.append(f"Price {price_diff_pct:.2f}% above BB (tolerance: {bb_tolerance_pct:.1f}%)")
                    
                    if medium_trend == 'bearish' and long_trend == 'bearish':
                        reasons.append(f"Both trends bearish")
                    
                    if reasons:
                        logger.info(f"   ⏭️ No buy: {', '.join(reasons)}")
        
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    def resolve_pending_outcomes(self):
        """حل نتائج الإشارات بعد ساعة واحدة"""
        if not self.weaver_enabled or not self.pending_resolutions:
            return
        
        current_time = time.time()
        resolved_indices = []
        failed_count = 0
        
        for idx, pending in enumerate(self.pending_resolutions):
            time_elapsed = current_time - pending['timestamp']
            
            if time_elapsed >= 3600:
                try:
                    current_price = self.binance_client.get_symbol_price(pending['symbol'])
                    
                    if current_price:
                        self.performance_tracker.resolve_outcome(
                            pending['symbol'],
                            pending['indicator'],
                            pending['timeframe'],
                            pending['timestamp'],
                            current_price,
                            pending['price']
                        )
                        
                        price_change = ((current_price - pending['price']) / pending['price']) * 100
                        logger.info(f"✅ Resolved {pending['indicator']} for {pending['symbol']}: "
                                  f"{price_change:+.2f}% after 1h")
                        
                        resolved_indices.append(idx)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.debug(f"Cannot resolve {pending['symbol']} yet (retrying later): {str(e)[:50]}")
                    failed_count += 1
                    
                    if time_elapsed > 7200:
                        logger.warning(f"⚠️ Dropping stale pending for {pending['symbol']} (>2h old)")
                        resolved_indices.append(idx)
        
        for idx in reversed(resolved_indices):
            self.pending_resolutions.pop(idx)
        
        if resolved_indices or failed_count:
            logger.info(f"📊 Resolved: {len(resolved_indices)}, Retrying: {failed_count}, "
                      f"Total pending: {len(self.pending_resolutions)}")
    
    def get_swarm_decision(self, symbol, indicators):
        """الحصول على قرار السرب عبر التصويت الجماعي"""
        if not self.swarm_enabled or not self.swarm:
            return None
        
        try:
            macd_data = indicators['macd']
            if isinstance(macd_data, dict):
                macd_dict = macd_data
            else:
                macd_dict = {'macd': float(macd_data), 'signal': 0, 'histogram': 0}
            
            market_data = {
                'price': float(indicators['close']),
                'rsi': float(indicators['rsi']),
                'macd': macd_dict,
                'stoch_k': float(indicators.get('stoch_k', 50)),
                'bb_lower': float(indicators['bb_lower']),
                'bb_upper': float(indicators['bb_upper']),
                'ema_9': float(indicators.get('ema_9', indicators['close'])),
                'ema_21': float(indicators.get('ema_21', indicators['close'])),
                'ema_50': float(indicators.get('ema_50', indicators['close'])),
                'ema_200': float(indicators.get('ema_200', indicators['close'])),
                'sma_20': float(indicators.get('sma_20', indicators['close'])),
                'volume_ratio': float(indicators.get('volume_ratio', 1.0)),
                'price_change_pct': float(indicators.get('price_change', 0)),
                'adx': float(indicators.get('adx', 25)),
                'atr': float(indicators.get('atr', 0)),
                'atr_avg': float(indicators.get('atr_avg', 1)),
                'bb_width': float(indicators.get('bb_width', 0)),
                'high_20': float(indicators.get('high_20', indicators['close'])),
                'low_20': float(indicators.get('low_20', indicators['close'])),
                'rate_of_change': float(indicators.get('rate_of_change', 0))
            }
            
            vote = self.swarm.conduct_vote(symbol, market_data)
            
            if self.db:
                self.db.save_swarm_vote(vote)
            
            if self.swarm_enabled and self.config.get('swarm_intelligence', {}).get('paper_trading_enabled', True):
                current_price = indicators['close']
                self.swarm.run_paper_trading_cycle(symbol, market_data)
            
            if self.causal_enabled and self.causal_engine:
                technical_signals = {
                    'rsi': indicators['rsi'],
                    'stochastic': indicators['stoch_k'],
                    'macd': macd_dict.get('macd', 0),
                    'bb_position': (indicators['close'] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower']),
                    'volume_ratio': market_data['volume_ratio'],
                    'price_change': market_data['price_change_pct'],
                    'ema_alignment': 1 if indicators['close'] > indicators.get('ema_50', 0) else 0
                }
                
                causal_vote = self.causal_engine.get_causal_recommendation(vote, technical_signals)
                
                logger.info(f"   🧠 Causal Analysis: {causal_vote['decision']} "
                          f"(Confidence: {causal_vote['confidence']:.1f}%, "
                          f"Filtered: {causal_vote.get('filtered_spurious', 0)} spurious signals)")
                
                return causal_vote
            
            return vote
            
        except Exception as e:
            logger.error(f"Swarm decision error: {e}")
            return None
    
    def display_status(self):
        open_positions = self.risk_manager.get_open_positions()
        
        if open_positions:
            logger.info("\n📊 Open Positions:")
            for symbol, position in open_positions.items():
                current_price = self.binance_client.get_symbol_price(symbol)
                if current_price:
                    profit_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
                    logger.info(f"  {symbol}: Entry ${position['entry_price']:.2f} | "
                              f"Current ${current_price:.2f} | P/L: {profit_pct:+.2f}%")
        else:
            logger.info("\n📊 No open positions")
    
    def run(self):
        global bot_stats
        logger.info("\n🚀 Bot is now running...")
        logger.info(f"Checking markets every {self.check_interval} seconds\n")
        
        bot_stats['status'] = 'running'
        bot_stats['start_time'] = datetime.now().isoformat()
        
        self.telegram.notify_startup(self.trading_pairs, self.testnet)
        
        self.display_account_info()
        
        iteration = 0
        try:
            while True:
                iteration += 1
                bot_stats['iterations'] = iteration
                bot_stats['last_check'] = datetime.now().isoformat()
                
                global trading_enabled
                if not trading_enabled:
                    bot_stats['status'] = 'paused'
                    logger.warning("⏸️  التداول متوقف - في وضع الانتظار")
                    time.sleep(5)
                    continue
                
                bot_stats['status'] = 'running'
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                # Real-Time Account Sync - تحقق من حساب Binance قبل أي شيء
                self.risk_manager.sync_positions_with_binance()
                
                if self.weaver_enabled:
                    self.resolve_pending_outcomes()
                
                for symbol in self.trading_pairs:
                    logger.info(f"\n🔍 Analyzing {symbol}...")
                    self.process_symbol(symbol)
                
                self.display_status()
                
                
                logger.info(f"\n⏸️  Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Bot stopped by user")
            bot_stats['status'] = 'stopped'
            self.display_status()
            logger.info("\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"\n❌ Fatal error: {e}")
            bot_stats['status'] = 'error'
            raise

@app.route('/')
def index():
    """عرض الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check للـ deployment"""
    return jsonify({
        'status': 'healthy',
        'bot_status': bot_stats['status'],
        'iterations': bot_stats['iterations'],
        'uptime': f"Started at {bot_stats['start_time']}" if bot_stats['start_time'] else 'Not started',
        'last_check': bot_stats['last_check']
    })

@app.route('/status')
def get_status():
    """إرجاع حالة البوت والصفقات"""
    if bot_instance:
        positions_raw = bot_instance.risk_manager.get_open_positions()
        
        positions_enriched = {}
        for symbol, pos in positions_raw.items():
            current_price = bot_instance.binance_client.get_symbol_price(symbol)
            entry_price = pos.get('entry_price', 0)
            position_type = pos.get('position_type', 'SPOT')
            leverage = pos.get('leverage', 1)
            
            current_profit = 0
            if current_price and entry_price:
                if position_type in ['LONG', 'BUY', 'SPOT']:
                    current_profit = ((current_price - entry_price) / entry_price) * 100
                elif position_type in ['SHORT', 'SELL']:
                    current_profit = ((entry_price - current_price) / entry_price) * 100
                
                if position_type in ['LONG', 'SHORT']:
                    current_profit = current_profit * leverage
            
            stop_loss_price = None
            take_profit_price = None
            if entry_price:
                if pos.get('stop_loss_percent'):
                    if position_type in ['LONG', 'BUY', 'SPOT']:
                        stop_loss_price = entry_price * (1 - pos['stop_loss_percent'] / 100)
                    else:
                        stop_loss_price = entry_price * (1 + pos['stop_loss_percent'] / 100)
                        
                if pos.get('take_profit_percent'):
                    if position_type in ['LONG', 'BUY', 'SPOT']:
                        take_profit_price = entry_price * (1 + pos['take_profit_percent'] / 100)
                    else:
                        take_profit_price = entry_price * (1 - pos['take_profit_percent'] / 100)
            
            positions_enriched[symbol] = {
                **pos,
                'symbol': symbol,
                'current_price': current_price,
                'current_profit': round(current_profit, 2),
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'position_type': position_type,
                'leverage': leverage,
                'liquidation_price': pos.get('liquidation_price'),
                'unrealized_pnl': pos.get('unrealized_pnl', 0)
            }
        
        market_regime = bot_instance.trading_strategy.current_regime if bot_instance.regime_enabled else 'sideways'
        regime_reason = bot_instance.trading_strategy.current_regime_reason if bot_instance.regime_enabled else 'N/A'
        
        momentum_data = {}
        if bot_instance.momentum_enabled:
            try:
                for symbol in bot_instance.trading_pairs:
                    result = bot_instance.analyze_symbol(symbol)
                    if result:
                        indicators, _ = result
                        momentum_index, components = bot_instance.custom_momentum.compute(
                            symbol, indicators, volume_24h_avg=None, btc_change_24h=None
                        )
                        if momentum_index is not None:
                            momentum_data[symbol] = {
                                'index': round(momentum_index, 1),
                                'components': components
                            }
            except Exception as e:
                logger.error(f"Error calculating momentum for status: {e}")
        
        return jsonify({
            'bot_status': bot_stats['status'],
            'iterations': bot_stats['iterations'],
            'start_time': bot_stats['start_time'],
            'last_check': bot_stats['last_check'],
            'open_positions': len(positions_enriched),
            'positions': positions_enriched,
            'testnet': bot_instance.testnet,
            'trading_enabled': trading_enabled,
            'market_regime': market_regime,
            'regime_reason': regime_reason,
            'regime_enabled': bot_instance.regime_enabled,
            'momentum_enabled': bot_instance.momentum_enabled,
            'momentum_data': momentum_data
        })
    return jsonify({'status': 'initializing', 'testnet': True, 'trading_enabled': True, 'market_regime': 'unknown', 'regime_enabled': False, 'momentum_enabled': False})

@app.route('/logs')
def get_logs():
    """إرجاع آخر السجلات"""
    try:
        logs = []
        if os.path.exists('bot.log'):
            with open('bot.log', 'r', encoding='utf-8') as f:
                # قراءة آخر 50 سطر
                all_lines = f.readlines()
                logs = [line.strip() for line in all_lines[-50:] if line.strip()]
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'logs': [], 'error': str(e)})

@app.route('/statistics')
def get_statistics():
    """إرجاع الإحصائيات الكاملة"""
    if bot_instance:
        stats = bot_instance.stats.get_stats()
        win_rate = bot_instance.stats.get_win_rate()
        avg_profit = bot_instance.stats.get_average_profit()
        today_stats = bot_instance.stats.get_today_stats()
        recent_trades = bot_instance.stats.get_recent_trades(10)
        
        return jsonify({
            'total_trades': stats['total_trades'],
            'winning_trades': stats['winning_trades'],
            'losing_trades': stats['losing_trades'],
            'win_rate': win_rate,
            'total_profit_usd': stats['total_profit_usd'],
            'average_profit': avg_profit,
            'best_trade': stats['best_trade'],
            'worst_trade': stats['worst_trade'],
            'today': today_stats,
            'recent_trades': recent_trades,
            'symbol_stats': stats['symbol_stats']
        })
    return jsonify({'error': 'Bot not initialized'})

@app.route('/strategy-weights')
def get_strategy_weights():
    """إرجاع أوزان الاستراتيجية الديناميكية لكل زوج تداول"""
    if bot_instance and bot_instance.weaver_enabled:
        try:
            timeframe = bot_instance.config['trading']['candle_interval']
            weaver_config = bot_instance.config.get('dynamic_strategy_weaver', {})
            weights_data = {}
            
            for symbol in bot_instance.trading_pairs:
                weights = bot_instance.performance_tracker.get_indicator_weights(symbol, timeframe)
                stats = bot_instance.performance_tracker.get_statistics(symbol, timeframe)
                
                total_signals = sum(s['total_signals'] for s in stats['indicators'].values())
                
                weights_data[symbol] = {
                    'weights': {k: round(v * 100, 1) for k, v in weights.items()},
                    'statistics': stats,
                    'total_learning_signals': total_signals,
                    'is_learning': total_signals < weaver_config.get('min_signals_for_learning', 10)
                }
            
            return jsonify({
                'enabled': weaver_config.get('enabled', False),
                'timeframe': timeframe,
                'min_confidence': weaver_config.get('min_confidence_threshold', 0.50),
                'learning_period_days': weaver_config.get('learning_period_days', 30),
                'symbols': weights_data
            })
        except Exception as e:
            logger.error(f"Error getting strategy weights: {e}")
            return jsonify({'error': str(e), 'enabled': False})
    return jsonify({'enabled': False, 'message': 'Dynamic Strategy Weaver not enabled'})

@app.route('/sell-all', methods=['POST'])
def sell_all_positions():
    """بيع جميع الصفقات المفتوحة"""
    if not bot_instance:
        return jsonify({'success': False, 'error': 'Bot not initialized'}), 400
    
    try:
        positions = bot_instance.risk_manager.get_open_positions()
        
        if not positions:
            return jsonify({'success': True, 'message': 'No open positions to sell', 'sold': 0})
        
        results = []
        sold_count = 0
        failed_count = 0
        
        for symbol, position in positions.items():
            try:
                current_price = bot_instance.binance_client.get_symbol_price(symbol)
                quantity = position.get('quantity', 0)
                entry_price = position.get('entry_price', 0)
                
                if current_price and quantity > 0:
                    profit_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price else 0
                    
                    logger.info(f"🔴 MANUAL SELL ALL: Selling {symbol} at {profit_pct:.2f}% profit")
                    
                    order = bot_instance.binance_client.create_market_order(symbol, 'SELL', quantity)
                    
                    if order is None:
                        results.append({
                            'symbol': symbol,
                            'success': False,
                            'error': 'Order creation failed or rejected by exchange'
                        })
                        failed_count += 1
                        logger.warning(f"⚠️ {symbol} sell order creation failed")
                    elif order.get('status') == 'FILLED':
                        bot_instance.risk_manager.close_position(
                            symbol, 
                            current_price, 
                            "MANUAL_SELL_ALL"
                        )
                        
                        profit_usd = (current_price - entry_price) * quantity if entry_price else 0
                        
                        bot_instance.stats.record_trade(
                            symbol, 
                            entry_price, 
                            current_price, 
                            quantity, 
                            "MANUAL_SELL_ALL"
                        )
                        
                        results.append({
                            'symbol': symbol,
                            'success': True,
                            'profit_pct': round(profit_pct, 2),
                            'profit_usd': round(profit_usd, 2),
                            'price': current_price
                        })
                        sold_count += 1
                        logger.info(f"✅ {symbol} sold successfully at ${current_price:.2f} ({profit_pct:+.2f}%)")
                    elif order.get('status') in ['PARTIALLY_FILLED', 'PENDING']:
                        results.append({
                            'symbol': symbol,
                            'success': False,
                            'error': f"Order partially filled or pending - Status: {order.get('status')}"
                        })
                        failed_count += 1
                        logger.warning(f"⚠️ {symbol} order status: {order.get('status')} - Check manually")
                    else:
                        results.append({
                            'symbol': symbol,
                            'success': False,
                            'error': f"Order status: {order.get('status', 'UNKNOWN')}"
                        })
                        failed_count += 1
                        logger.warning(f"⚠️ {symbol} sell order failed - Status: {order.get('status')}")
                        
            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                })
                failed_count += 1
                logger.error(f"❌ Error selling {symbol}: {e}")
        
        return jsonify({
            'success': True,
            'sold': sold_count,
            'failed': failed_count,
            'total': len(positions),
            'results': results,
            'message': f'Successfully sold {sold_count} out of {len(positions)} positions'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in sell-all endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/toggle-trading', methods=['POST'])
def toggle_trading():
    """تبديل حالة التداول (تشغيل/إيقاف)"""
    global trading_enabled
    
    try:
        trading_enabled = not trading_enabled
        
        if trading_enabled:
            logger.info("▶️ التداول تم تشغيله من لوحة التحكم")
            bot_stats['status'] = 'running'
            message = "تم بدء التداول بنجاح"
        else:
            logger.warning("⏸️ التداول تم إيقافه من لوحة التحكم")
            bot_stats['status'] = 'paused'
            message = "تم إيقاف التداول مؤقتاً"
        
        return jsonify({
            'success': True,
            'trading_enabled': trading_enabled,
            'status': bot_stats['status'],
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error toggling trading: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/create-demo-position', methods=['POST'])
def create_demo_position():
    """إنشاء صفقة تجريبية لعرض Futures UI"""
    if not bot_instance:
        return jsonify({'success': False, 'error': 'Bot not initialized'}), 500
    
    try:
        demo_positions = [
            {
                'symbol': 'BTCUSDT',
                'position_type': 'LONG',
                'entry_price': 94500.00,
                'quantity': 0.001,
                'leverage': 2,
                'liquidation_price': 47250.00
            },
            {
                'symbol': 'ETHUSDT',
                'position_type': 'SHORT',
                'entry_price': 3250.00,
                'quantity': 0.015,
                'leverage': 3,
                'liquidation_price': 4875.00
            }
        ]
        
        created_count = 0
        for pos_data in demo_positions:
            liquidation_price = pos_data['liquidation_price']
            entry_price = pos_data['entry_price']
            
            if pos_data['position_type'] == 'LONG':
                stop_loss_price = entry_price * 0.98
                take_profit_price = entry_price * 1.04
            else:
                stop_loss_price = entry_price * 1.02
                take_profit_price = entry_price * 0.96
            
            bot_instance.risk_manager.positions[pos_data['symbol']] = {
                'status': 'open',
                'entry_price': entry_price,
                'quantity': pos_data['quantity'],
                'signals': {'demo': True},
                'entry_time': str(datetime.now()),
                'market_regime': 'sideways',
                'position_type': pos_data['position_type'],
                'leverage': pos_data['leverage'],
                'liquidation_price': liquidation_price,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 4.0,
                'unrealized_pnl': 0.0,
                'funding_rate': None,
                'trailing_stop': {
                    'enabled': True,
                    'current_stop_percent': -2.0 if pos_data['position_type'] == 'LONG' else 2.0,
                    'highest_price': entry_price if pos_data['position_type'] == 'LONG' else None,
                    'lowest_price': entry_price if pos_data['position_type'] == 'SHORT' else None,
                    'activation_profit': 3.0,
                    'trail_percent': 2.0
                }
            }
            
            if bot_instance.db:
                try:
                    bot_instance.db.save_position(
                        symbol=pos_data['symbol'],
                        entry_price=entry_price,
                        quantity=pos_data['quantity'],
                        entry_time=datetime.now(),
                        stop_loss=stop_loss_price,
                        take_profit=take_profit_price,
                        trailing_stop_price=stop_loss_price,
                        highest_price=entry_price,
                        market_regime='sideways',
                        buy_signals={'demo': 'true'},
                        position_type=pos_data['position_type'],
                        leverage=pos_data['leverage'],
                        liquidation_price=liquidation_price
                    )
                except Exception as e:
                    logger.error(f"Error saving demo position to DB: {e}")
            
            bot_instance.risk_manager.save_positions()
            created_count += 1
            
            pos_emoji = "🟢" if pos_data['position_type'] == 'LONG' else "🔴"
            logger.info(f"{pos_emoji} Created DEMO {pos_data['position_type']} position: {pos_data['symbol']} @ ${entry_price:.2f} ({pos_data['leverage']}x)")
        
        return jsonify({
            'success': True,
            'created': created_count,
            'message': f'Created {created_count} demo Futures positions'
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating demo position: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/swarm-stats')
def get_swarm_stats():
    """إحصائيات السرب"""
    if bot_instance and bot_instance.swarm_enabled and bot_instance.swarm:
        try:
            raw_stats = bot_instance.swarm.get_swarm_stats()
            
            total_paper_trades = sum(w.performance.total_trades for w in bot_instance.swarm.workers)
            
            votes_today = 0
            latest_decision = None
            if bot_instance.swarm.vote_history:
                from datetime import datetime as dt
                votes_today = len([v for v in bot_instance.swarm.vote_history 
                                 if (dt.now() - v.timestamp).days == 0])
                latest_vote = bot_instance.swarm.vote_history[-1]
                latest_decision = latest_vote.final_decision
            
            stats = {
                'total_bots': raw_stats['total_workers'],
                'top_performer': {
                    'bot_id': raw_stats['best_bot']['id'],
                    'win_rate': raw_stats['best_bot'].get('roi', 0)
                },
                'average_accuracy': raw_stats.get('profitability_rate', 0),
                'total_paper_trades': total_paper_trades,
                'votes_today': votes_today,
                'latest_decision': latest_decision
            }
            
            return jsonify({
                'success': True,
                'enabled': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Swarm stats error: {e}")
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'enabled': False, 'message': 'Swarm not enabled'})

def run_bot():
    global bot_instance
    try:
        bot_instance = BinanceTradingBot()
        bot_instance.run()
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_stats['status'] = 'error'

def run_telegram_bot():
    global telegram_bot_instance, bot_instance
    
    time.sleep(10)
    
    while bot_instance is None:
        logger.info("⏳ Waiting for trading bot to initialize...")
        time.sleep(2)
    
    try:
        logger.info("🤖 Starting Telegram bot controller...")
        telegram_bot_instance = TelegramBotController(bot_instance, bot_instance.db, bot_instance.ai_analyzer)
        telegram_bot_instance.run()
    except Exception as e:
        logger.error(f"❌ Telegram bot error: {e}")
        if "TELEGRAM_BOT_TOKEN" in str(e):
            logger.warning("⚠️ Telegram bot token not configured - skipping Telegram bot")
        else:
            raise

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting web server on port {port}...")
    logger.info("🤖 Starting trading bot in background...")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    telegram_enabled = os.getenv('TELEGRAM_BOT_TOKEN') is not None
    if telegram_enabled:
        logger.info("📱 Starting Telegram bot in background...")
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
    else:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set - Telegram bot disabled")
    
    app.run(host='0.0.0.0', port=port, debug=False)
