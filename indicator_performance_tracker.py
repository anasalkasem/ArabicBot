import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger('indicator_tracker')

class IndicatorPerformanceTracker:
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.pending_resolutions = []
        
        self.default_weights = {
            'rsi': 0.25,
            'stochastic': 0.25,
            'bollinger_bands': 0.25,
            'macd': 0.25
        }
        
        logger.info("📊 Indicator Performance Tracker initialized with database")
    
    def track_signal(self, symbol: str, indicator: str, timeframe: str, 
                    signal_value: bool, price_at_signal: float, 
                    metadata: Optional[Dict] = None):
        if not self.db:
            logger.warning("No database connection, skipping signal tracking")
            return
        
        try:
            self.db.save_indicator_signal(
                symbol=symbol,
                indicator_name=indicator,
                timeframe=timeframe,
                is_bullish=signal_value,
                price=price_at_signal,
                signal_time=datetime.now()
            )
            logger.debug(f"📝 Tracked {indicator} signal for {symbol}: {signal_value}")
        except Exception as e:
            logger.error(f"Error tracking signal: {e}")
    
    def resolve_outcome(self, symbol: str, indicator: str, timeframe: str, 
                       signal_time: datetime, price_after_1h: float, signal_price: float):
        if not self.db:
            logger.warning("No database connection, skipping outcome resolution")
            return
        
        try:
            price_change_pct = ((price_after_1h - signal_price) / signal_price) * 100
            was_successful = price_change_pct >= 1.0
            
            self.db.save_indicator_outcome(
                symbol=symbol,
                indicator_name=indicator,
                timeframe=timeframe,
                signal_price=signal_price,
                outcome_price=price_after_1h,
                price_change_percent=price_change_pct,
                was_successful=was_successful,
                signal_time=signal_time,
                outcome_time=datetime.now()
            )
            
            logger.debug(f"✅ Resolved {indicator} outcome for {symbol}: {price_change_pct:+.2f}%")
        except Exception as e:
            logger.error(f"Error resolving outcome: {e}")
    
    def get_success_rate(self, symbol: str, indicator: str, timeframe: str, 
                        min_profit_threshold: float = 1.0) -> float:
        if not self.db:
            return 0.5
        
        try:
            stats = self.db.get_indicator_statistics(
                symbol=symbol,
                indicator_name=indicator,
                days=30
            )
            
            if not stats or len(stats) == 0:
                return 0.5
            
            stat = stats[0]
            
            if stat['total_signals'] < 5:
                return 0.5
            
            success_rate = stat['successful_signals'] / stat['total_signals'] if stat['total_signals'] > 0 else 0.5
            
            return max(0.0, min(1.0, success_rate))
        except Exception as e:
            logger.error(f"Error getting success rate: {e}")
            return 0.5
    
    def get_indicator_weights(self, symbol: str, timeframe: str = '5m') -> Dict[str, float]:
        indicators = ['rsi', 'stochastic', 'bollinger_bands', 'macd']
        
        success_rates = {}
        for indicator in indicators:
            success_rates[indicator] = self.get_success_rate(symbol, indicator, timeframe)
        
        total_score = sum(success_rates.values())
        
        if total_score == 0 or all(rate == 0.5 for rate in success_rates.values()):
            return self.default_weights.copy()
        
        weights = {}
        for indicator in indicators:
            raw_weight = success_rates[indicator] / total_score
            clamped_weight = max(0.10, min(0.40, raw_weight))
            weights[indicator] = clamped_weight
        
        weight_sum = sum(weights.values())
        normalized_weights = {k: v / weight_sum for k, v in weights.items()}
        
        return normalized_weights
    
    def get_buy_confidence(self, symbol: str, indicator_signals: Dict[str, bool], 
                          timeframe: str = '5m') -> float:
        weights = self.get_indicator_weights(symbol, timeframe)
        
        confidence = 0.0
        for indicator, is_bullish in indicator_signals.items():
            if is_bullish and indicator in weights:
                confidence += weights[indicator]
        
        return confidence
    
    def get_statistics(self, symbol: str, timeframe: str = '5m') -> Dict:
        if not self.db:
            return {'symbol': symbol, 'timeframe': timeframe, 'indicators': {}}
        
        try:
            indicators = ['rsi', 'stochastic', 'bollinger_bands', 'macd']
            
            stats = {
                'symbol': symbol,
                'timeframe': timeframe,
                'indicators': {}
            }
            
            db_stats = self.db.get_indicator_statistics(symbol=symbol, days=30)
            
            for indicator in indicators:
                indicator_stat = next((s for s in db_stats if s['indicator_name'] == indicator), None)
                
                if indicator_stat:
                    stats['indicators'][indicator] = {
                        'total_signals': indicator_stat['total_signals'],
                        'resolved_signals': indicator_stat['successful_signals'] + (indicator_stat['total_signals'] - indicator_stat['successful_signals']),
                        'success_rate': indicator_stat['successful_signals'] / indicator_stat['total_signals'] if indicator_stat['total_signals'] > 0 else 0.5,
                        'avg_outcome': float(indicator_stat['avg_price_change']) if indicator_stat['avg_price_change'] else 0.0
                    }
                else:
                    stats['indicators'][indicator] = {
                        'total_signals': 0,
                        'resolved_signals': 0,
                        'success_rate': 0.5,
                        'avg_outcome': 0.0
                    }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'symbol': symbol, 'timeframe': timeframe, 'indicators': {}}
