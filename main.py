import json
import time
import os
from datetime import datetime
from binance_client import BinanceClientManager
from technical_indicators import TechnicalIndicators
from trading_strategy import TradingStrategy
from risk_manager import RiskManager
from logger_setup import setup_logger

logger = setup_logger('main_bot')

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
        
        self.binance_client = BinanceClientManager(testnet=self.testnet)
        self.technical_indicators = TechnicalIndicators(self.config)
        self.trading_strategy = TradingStrategy(self.config)
        self.risk_manager = RiskManager(self.config, self.binance_client)
        
        self.prev_indicators = {}
        self.multi_tf_enabled = self.config.get('multi_timeframe', {}).get('enabled', False)
        
        if self.multi_tf_enabled:
            logger.info("✨ Multi-Timeframe Analysis: ENABLED")
        
        trailing_enabled = self.config.get('risk_management', {}).get('trailing_stop_loss', {}).get('enabled', False)
        if trailing_enabled:
            logger.info("✨ Trailing Stop-Loss: ENABLED")
        
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
            else:
                result = self.analyze_symbol(symbol)
                if not result:
                    return
                indicators, _ = result
                prev_indicators = self.prev_indicators.get(symbol)
                self.prev_indicators[symbol] = indicators
                medium_trend = None
                long_trend = None
            
            current_price = indicators['close']
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
                    return
                
                if self.trading_strategy.should_stop_loss(current_price, entry_price):
                    logger.warning(f"🛑 STOP LOSS triggered for {symbol}")
                    order = self.binance_client.create_test_order(
                        symbol=symbol,
                        side='SELL',
                        quantity=position['quantity']
                    )
                    if order:
                        self.risk_manager.close_position(symbol, current_price, "STOP_LOSS")
                    return
                
                sell_signal, signals, reason = self.trading_strategy.check_sell_signal(
                    indicators, entry_price, prev_indicators
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
            
            else:
                buy_signal, signals = self.trading_strategy.check_buy_signal(
                    indicators, prev_indicators, medium_trend, long_trend
                )
                
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
        
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
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
        logger.info("\n🚀 Bot is now running...")
        logger.info(f"Checking markets every {self.check_interval} seconds\n")
        
        self.display_account_info()
        
        iteration = 0
        try:
            while True:
                iteration += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"🔄 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                for symbol in self.trading_pairs:
                    logger.info(f"\n🔍 Analyzing {symbol}...")
                    self.process_symbol(symbol)
                
                self.display_status()
                
                logger.info(f"\n⏸️  Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Bot stopped by user")
            self.display_status()
            logger.info("\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"\n❌ Fatal error: {e}")
            raise

if __name__ == "__main__":
    bot = BinanceTradingBot()
    bot.run()
