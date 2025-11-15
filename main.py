import json
import time
import os
import threading
import asyncio
from datetime import datetime
from flask import Flask, jsonify, render_template
from binance_client import BinanceClientManager
from technical_indicators import TechnicalIndicators
from trading_strategy import TradingStrategy
from risk_manager import RiskManager
from telegram_notifier import TelegramNotifier
from statistics_tracker import StatisticsTracker
from market_regime import MarketRegime
from sentiment_analyzer import SentimentAnalyzer
from custom_momentum import CustomMomentumIndex
from indicator_performance_tracker import IndicatorPerformanceTracker
from logger_setup import setup_logger
from db_manager import DatabaseManager
from telegram_bot import TelegramBotController
from ai_market_analyzer import AIMarketAnalyzer

logger = setup_logger('main_bot')
app = Flask(__name__)

# قائمة السجلات للعرض في الواجهة
recent_logs = []
MAX_LOGS = 50

bot_instance = None
telegram_bot_instance = None
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
        
        logger.info(f"Mode: {'TESTNET' if self.testnet else 'LIVE TRADING'}")
        logger.info(f"Trading Pairs: {', '.join(self.trading_pairs)}")
        
        try:
            self.db = DatabaseManager()
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.db = None
        
        self.binance_client = BinanceClientManager(testnet=self.testnet)
        self.technical_indicators = TechnicalIndicators(self.config)
        self.trading_strategy = TradingStrategy(self.config)
        self.risk_manager = RiskManager(self.config, self.binance_client, self.trading_strategy, db_manager=self.db)
        self.telegram = TelegramNotifier(self.config)
        self.stats = StatisticsTracker(db_manager=self.db)
        self.market_regime = MarketRegime(self.config)
        self.sentiment_analyzer = SentimentAnalyzer(self.config)
        self.custom_momentum = CustomMomentumIndex(self.config, self.sentiment_analyzer)
        self.performance_tracker = IndicatorPerformanceTracker(db_manager=self.db)
        self.ai_analyzer = AIMarketAnalyzer()
        
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
        
        trailing_enabled = self.config.get('risk_management', {}).get('trailing_stop_loss', {}).get('enabled', False)
        if trailing_enabled:
            logger.info("✨ Trailing Stop-Loss: ENABLED")
        
        if self.ai_analyzer.enabled:
            logger.info("🤖 AI Market Analyzer: ENABLED (GPT-4)")
            logger.info("   Features: Market Analysis, Strategy Audit, Telegram Chat")
        
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
            
            position = self.risk_manager.get_position(symbol)
            
            if position and position.get('status') == 'open':
                entry_price = position['entry_price']
                
                self.risk_manager.update_trailing_stop(symbol, current_price)
                
                if self.risk_manager.check_trailing_stop(symbol, current_price):
                    logger.warning(f"🛑 TRAILING STOP triggered for {symbol}")
                    order = self.binance_client.create_test_order(
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
                    order = self.binance_client.create_test_order(
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
                    order = self.binance_client.create_test_order(
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
                    quantity = self.risk_manager.calculate_position_size(symbol, current_price)
                    
                    if quantity > 0:
                        logger.info(f"💸 Buying {symbol} at ${current_price:.2f}")
                        order = self.binance_client.create_test_order(
                            symbol=symbol,
                            side='BUY',
                            quantity=quantity
                        )
                        if order:
                            self.risk_manager.open_position(symbol, current_price, quantity, signals)
                            self.telegram.notify_buy(symbol, current_price, quantity, signals)
                elif not buy_signal:
                    reasons = []
                    rsi_threshold = self.config['indicators']['rsi_oversold']
                    stoch_threshold = self.config['indicators']['stochastic_oversold']
                    if indicators['rsi'] >= rsi_threshold:
                        reasons.append(f"RSI={indicators['rsi']:.1f} (need <{rsi_threshold})")
                    if indicators['stoch_k'] >= stoch_threshold:
                        reasons.append(f"Stoch={indicators['stoch_k']:.1f} (need <{stoch_threshold})")
                    bb_tolerance = indicators['bb_lower'] * 1.005
                    if current_price > bb_tolerance:
                        price_diff_pct = ((current_price - indicators['bb_lower']) / indicators['bb_lower']) * 100
                        reasons.append(f"Price {price_diff_pct:.2f}% above BB (tolerance: 0.5%)")
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
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
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
        positions = bot_instance.risk_manager.get_open_positions()
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
            'open_positions': len(positions),
            'positions': positions,
            'testnet': bot_instance.testnet,
            'market_regime': market_regime,
            'regime_reason': regime_reason,
            'regime_enabled': bot_instance.regime_enabled,
            'momentum_enabled': bot_instance.momentum_enabled,
            'momentum_data': momentum_data
        })
    return jsonify({'status': 'initializing', 'testnet': True, 'market_regime': 'unknown', 'regime_enabled': False, 'momentum_enabled': False})

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
