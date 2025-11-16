from abc import ABC, abstractmethod
from logger_setup import setup_logger

logger = setup_logger('base_strategy')

class BaseStrategy(ABC):
    def __init__(self, config, market_regime=None):
        self.config = config
        self.market_regime = market_regime
    
    @abstractmethod
    def check_entry_signal(self, symbol, indicators, market_regime, trends=None):
        pass
    
    @abstractmethod
    def check_exit_signal(self, symbol, position, current_price, indicators):
        pass
    
    @abstractmethod
    def get_position_type(self):
        pass
    
    def get_stop_loss_percent(self, market_regime):
        if not market_regime:
            return self.config['risk_management']['stop_loss_percent']
        
        regime_config = self.config['market_regime'].get(f'{market_regime.lower()}_strategy', {})
        base_stop_loss = self.config['risk_management']['stop_loss_percent']
        multiplier = regime_config.get('stop_loss_multiplier', 1.0)
        
        return base_stop_loss * multiplier
    
    def get_take_profit_percent(self, market_regime):
        if not market_regime:
            return self.config['risk_management']['take_profit_percent']
        
        regime_config = self.config['market_regime'].get(f'{market_regime.lower()}_strategy', {})
        base_take_profit = self.config['risk_management']['take_profit_percent']
        multiplier = regime_config.get('take_profit_multiplier', 1.0)
        
        return base_take_profit * multiplier
    
    def log_signal(self, signal_type, symbol, reason, indicators=None):
        emoji = "✅" if signal_type == "ENTRY" else "❌"
        logger.info(f"{emoji} {signal_type} SIGNAL for {symbol}: {reason}")
        
        if indicators:
            logger.info(f"   Indicators: {indicators}")
