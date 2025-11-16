from logger_setup import setup_logger
from strategies.long_strategy import LongStrategy
from strategies.short_strategy import ShortStrategy

logger = setup_logger('strategy_coordinator')

class StrategyCoordinator:
    def __init__(self, config):
        self.config = config
        self.futures_config = config.get('futures', {})
        self.futures_enabled = self.futures_config.get('enabled', False)
        
        self.long_strategy = LongStrategy(config)
        self.short_strategy = ShortStrategy(config) if self.futures_enabled else None
        
        self.regime_strategies = self.futures_config.get('market_regime_strategy', {})
    
    def get_allowed_strategies(self, market_regime):
        if not self.futures_enabled:
            return ['LONG']
        
        regime = market_regime.lower() if market_regime else 'sideways'
        strategy_mode = self.regime_strategies.get(f'{regime}_market', 'LONG_ONLY')
        
        if strategy_mode == 'LONG_ONLY':
            return ['LONG']
        elif strategy_mode == 'SHORT_ONLY':
            return ['SHORT']
        elif strategy_mode == 'BOTH':
            return ['LONG', 'SHORT']
        else:
            return ['LONG']
    
    def get_strategy_for_signal(self, market_regime, indicators):
        allowed = self.get_allowed_strategies(market_regime)
        
        if 'LONG' in allowed:
            should_long, reason = self.long_strategy.check_entry_signal(
                symbol='',
                indicators=indicators,
                market_regime=market_regime
            )
            if should_long:
                return 'LONG', self.long_strategy, reason
        
        if 'SHORT' in allowed and self.short_strategy:
            should_short, reason = self.short_strategy.check_entry_signal(
                symbol='',
                indicators=indicators,
                market_regime=market_regime
            )
            if should_short:
                return 'SHORT', self.short_strategy, reason
        
        return None, None, "No strategy signal"
    
    def check_exit_signal(self, symbol, position, current_price, indicators):
        position_type = position.get('position_type', 'SPOT')
        
        if position_type in ['LONG', 'BUY', 'SPOT']:
            return self.long_strategy.check_exit_signal(symbol, position, current_price, indicators)
        elif position_type in ['SHORT', 'SELL']:
            if self.short_strategy:
                return self.short_strategy.check_exit_signal(symbol, position, current_price, indicators)
        
        return False, None, "No strategy"
    
    def log_regime_strategy(self, market_regime):
        allowed = self.get_allowed_strategies(market_regime)
        
        regime_emoji = {
            'bull': '🐂',
            'bear': '🐻',
            'sideways': '↔️'
        }.get(market_regime.lower() if market_regime else 'sideways', '📊')
        
        logger.info(f"{regime_emoji} Market Regime: {market_regime.upper()} → Allowed strategies: {', '.join(allowed)}")
        
        if not self.futures_enabled and 'SHORT' in allowed:
            logger.warning("⚠️ SHORT strategy allowed but Futures trading is disabled in config!")
