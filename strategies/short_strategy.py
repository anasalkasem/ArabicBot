from .base_strategy import BaseStrategy
from logger_setup import setup_logger

logger = setup_logger('short_strategy')

class ShortStrategy(BaseStrategy):
    def __init__(self, config, market_regime=None):
        super().__init__(config, market_regime)
        self.position_type = "SHORT"
        
        self.futures_config = config.get('futures', {})
        self.short_config = self.futures_config.get('short_strategy', {})
    
    def get_position_type(self):
        return self.position_type
    
    def check_entry_signal(self, symbol, indicators, market_regime, trends=None):
        if not self.short_config.get('enabled', True):
            return False, "Short strategy disabled"
        
        entry_conditions = self.short_config.get('entry_conditions', {})
        
        if entry_conditions.get('require_bear_market', True):
            if market_regime != 'bear':
                return False, f"Market regime is {market_regime}, need BEAR for short"
        
        rsi = indicators.get('rsi')
        stoch = indicators.get('stochastic')
        bb_upper = indicators.get('bb_upper')
        current_price = indicators.get('current_price')
        
        if None in [rsi, stoch, bb_upper, current_price]:
            return False, "Missing indicators"
        
        rsi_threshold = entry_conditions.get('rsi_threshold', 75)
        stoch_threshold = entry_conditions.get('stochastic_threshold', 80)
        bb_tolerance = entry_conditions.get('bb_upper_tolerance', 0.5)
        
        if rsi < rsi_threshold:
            return False, f"RSI too low ({rsi:.1f} < {rsi_threshold})"
        
        if stoch < stoch_threshold:
            return False, f"Stochastic too low ({stoch:.1f} < {stoch_threshold})"
        
        bb_distance = ((bb_upper - current_price) / bb_upper) * 100
        if bb_distance > bb_tolerance:
            return False, f"Price too far from BB upper ({bb_distance:.2f}% > {bb_tolerance}%)"
        
        if trends:
            bullish_count = sum(1 for trend in trends.values() if trend == 'bullish')
            if bullish_count >= 2:
                return False, f"Too many bullish trends ({bullish_count}/3)"
        
        self.log_signal("ENTRY", symbol, f"SHORT signal - RSI:{rsi:.1f}, Stoch:{stoch:.1f}, BB Distance:{bb_distance:.2f}%")
        return True, "All SHORT entry conditions met"
    
    def check_exit_signal(self, symbol, position, current_price, indicators):
        entry_price = position.get('entry_price')
        if not entry_price:
            return False, None, "No entry price"
        
        profit_percent = ((entry_price - current_price) / entry_price) * 100
        
        exit_conditions = self.short_config.get('exit_conditions', {})
        take_profit_percent = exit_conditions.get('take_profit_percent', 4.0)
        rsi_reversal = exit_conditions.get('rsi_reversal_threshold', 30)
        
        if profit_percent >= take_profit_percent:
            self.log_signal("EXIT", symbol, f"SHORT Take Profit reached ({profit_percent:.2f}% >= {take_profit_percent}%)")
            return True, "TAKE_PROFIT", profit_percent
        
        rsi = indicators.get('rsi')
        if rsi and rsi < rsi_reversal:
            self.log_signal("EXIT", symbol, f"RSI reversal signal ({rsi:.1f} < {rsi_reversal})")
            return True, "RSI_REVERSAL", profit_percent
        
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd and macd_signal and macd > macd_signal:
            prev_macd = indicators.get('prev_macd')
            prev_signal = indicators.get('prev_macd_signal')
            if prev_macd and prev_signal and prev_macd < prev_signal:
                self.log_signal("EXIT", symbol, "MACD bullish crossover (exit SHORT)")
                return True, "MACD_BULLISH_CROSS", profit_percent
        
        trailing = position.get('trailing_stop', {})
        if trailing.get('enabled') and trailing.get('current_stop_percent'):
            stop_price = entry_price * (1 + trailing['current_stop_percent'] / 100)
            if current_price >= stop_price:
                self.log_signal("EXIT", symbol, f"SHORT Trailing stop triggered at {trailing['current_stop_percent']:.1f}%")
                return True, "TRAILING_STOP", profit_percent
        
        return False, None, "No exit signal"
