from .base_strategy import BaseStrategy
from logger_setup import setup_logger

logger = setup_logger('long_strategy')

class LongStrategy(BaseStrategy):
    def __init__(self, config, market_regime=None):
        super().__init__(config, market_regime)
        self.position_type = "LONG"
    
    def get_position_type(self):
        return self.position_type
    
    def check_entry_signal(self, symbol, indicators, market_regime, trends=None):
        rsi = indicators.get('rsi')
        stoch = indicators.get('stochastic')
        bb_lower = indicators.get('bb_lower')
        current_price = indicators.get('current_price')
        
        if None in [rsi, stoch, bb_lower, current_price]:
            return False, "Missing indicators"
        
        adjusted_rsi = self.config['indicators']['rsi_oversold']
        adjusted_stoch = self.config['indicators']['stochastic_oversold']
        bb_tolerance = self.config['indicators']['bb_tolerance']
        
        if market_regime:
            regime_config = self.config['market_regime'].get(f'{market_regime.lower()}_strategy', {})
            adjusted_rsi += regime_config.get('rsi_oversold_adjustment', 0)
            adjusted_stoch += regime_config.get('stoch_oversold_adjustment', 0)
            bb_tolerance += regime_config.get('bb_tolerance_adjustment', 0)
        
        if rsi >= adjusted_rsi:
            return False, f"RSI too high ({rsi:.1f} >= {adjusted_rsi})"
        
        if stoch >= adjusted_stoch:
            return False, f"Stochastic too high ({stoch:.1f} >= {adjusted_stoch})"
        
        bb_distance = ((current_price - bb_lower) / bb_lower) * 100
        if bb_distance > bb_tolerance:
            return False, f"Price too far from BB lower ({bb_distance:.2f}% > {bb_tolerance}%)"
        
        if trends:
            bearish_count = sum(1 for trend in trends.values() if trend == 'bearish')
            if bearish_count >= 2:
                return False, f"Too many bearish trends ({bearish_count}/3)"
        
        self.log_signal("ENTRY", symbol, f"LONG signal - RSI:{rsi:.1f}, Stoch:{stoch:.1f}, BB Distance:{bb_distance:.2f}%")
        return True, "All LONG entry conditions met"
    
    def check_exit_signal(self, symbol, position, current_price, indicators):
        entry_price = position.get('entry_price')
        if not entry_price:
            return False, None, "No entry price"
        
        profit_percent = ((current_price - entry_price) / entry_price) * 100
        
        market_regime = position.get('market_regime', 'sideways')
        take_profit_percent = self.get_take_profit_percent(market_regime)
        
        if profit_percent >= take_profit_percent:
            self.log_signal("EXIT", symbol, f"Take Profit reached ({profit_percent:.2f}% >= {take_profit_percent}%)")
            return True, "TAKE_PROFIT", profit_percent
        
        rsi = indicators.get('rsi')
        if rsi and rsi > 70:
            self.log_signal("EXIT", symbol, f"RSI overbought ({rsi:.1f} > 70)")
            return True, "RSI_OVERBOUGHT", profit_percent
        
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd and macd_signal and macd < macd_signal:
            prev_macd = indicators.get('prev_macd')
            prev_signal = indicators.get('prev_macd_signal')
            if prev_macd and prev_signal and prev_macd > prev_signal:
                self.log_signal("EXIT", symbol, "MACD bearish crossover")
                return True, "MACD_BEARISH_CROSS", profit_percent
        
        trailing = position.get('trailing_stop', {})
        if trailing.get('enabled') and trailing.get('current_stop_percent'):
            stop_price = entry_price * (1 - trailing['current_stop_percent'] / 100)
            if current_price <= stop_price:
                self.log_signal("EXIT", symbol, f"Trailing stop triggered at {trailing['current_stop_percent']:.1f}%")
                return True, "TRAILING_STOP", profit_percent
        
        return False, None, "No exit signal"
