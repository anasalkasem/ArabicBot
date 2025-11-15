import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger('indicator_tracker')

class IndicatorPerformanceTracker:
    def __init__(self, data_file='indicator_performance.json', max_signals_per_indicator=50):
        self.data_file = data_file
        self.max_signals_per_indicator = max_signals_per_indicator
        
        self.signals = defaultdict(lambda: defaultdict(lambda: deque(maxlen=max_signals_per_indicator)))
        self.pending_resolutions = []
        
        self.default_weights = {
            'rsi': 0.25,
            'stochastic': 0.25,
            'bollinger_bands': 0.25,
            'macd': 0.25
        }
        
        self.load_from_file()
        logger.info("📊 Indicator Performance Tracker initialized")
    
    def track_signal(self, symbol: str, indicator: str, timeframe: str, 
                    signal_value: bool, price_at_signal: float, 
                    metadata: Optional[Dict] = None):
        timestamp = time.time()
        
        key = f"{indicator}_{timeframe}"
        
        signal_record = {
            'timestamp': timestamp,
            'signal': signal_value,
            'price': price_at_signal,
            'metadata': metadata or {},
            'outcome_1h': None,
            'outcome_resolved': False
        }
        
        self.signals[symbol][key].append(signal_record)
        
        logger.debug(f"📝 Tracked {indicator} signal for {symbol}: {signal_value}")
    
    def resolve_outcome(self, symbol: str, indicator: str, timeframe: str, 
                       timestamp: float, price_after_1h: float):
        key = f"{indicator}_{timeframe}"
        
        if symbol not in self.signals or key not in self.signals[symbol]:
            return
        
        for signal in self.signals[symbol][key]:
            if abs(signal['timestamp'] - timestamp) < 60:
                price_change_pct = ((price_after_1h - signal['price']) / signal['price']) * 100
                signal['outcome_1h'] = price_change_pct
                signal['outcome_resolved'] = True
                
                logger.debug(f"✅ Resolved {indicator} outcome for {symbol}: {price_change_pct:+.2f}%")
                break
    
    def get_success_rate(self, symbol: str, indicator: str, timeframe: str, 
                        min_profit_threshold: float = 1.0) -> float:
        key = f"{indicator}_{timeframe}"
        
        if symbol not in self.signals or key not in self.signals[symbol]:
            return 0.5
        
        signals = self.signals[symbol][key]
        resolved_signals = [s for s in signals if s['outcome_resolved'] and s['signal']]
        
        if len(resolved_signals) < 5:
            return 0.5
        
        successful = sum(1 for s in resolved_signals if s['outcome_1h'] >= min_profit_threshold)
        
        success_rate = successful / len(resolved_signals) if resolved_signals else 0.5
        
        ema_weight = 0.3
        recent_signals = list(resolved_signals)[-10:]
        if recent_signals:
            recent_success = sum(1 for s in recent_signals if s['outcome_1h'] >= min_profit_threshold)
            recent_rate = recent_success / len(recent_signals)
            success_rate = (ema_weight * recent_rate) + ((1 - ema_weight) * success_rate)
        
        return success_rate
    
    def get_indicator_weights(self, symbol: str, timeframe: str = '15m') -> Dict[str, float]:
        indicators = ['rsi', 'stochastic', 'bollinger_bands', 'macd']
        
        success_rates = {}
        for indicator in indicators:
            success_rates[indicator] = self.get_success_rate(symbol, indicator, timeframe)
        
        total_score = sum(success_rates.values())
        
        if total_score == 0 or all(rate == 0.5 for rate in success_rates.values()):
            logger.info(f"⚖️ Using default weights for {symbol} (insufficient data)")
            return self.default_weights.copy()
        
        weights = {}
        for indicator in indicators:
            raw_weight = success_rates[indicator] / total_score
            
            clamped_weight = max(0.10, min(0.40, raw_weight))
            weights[indicator] = clamped_weight
        
        weight_sum = sum(weights.values())
        normalized_weights = {k: v / weight_sum for k, v in weights.items()}
        
        logger.info(f"⚖️ Dynamic weights for {symbol}:")
        for indicator, weight in normalized_weights.items():
            rate = success_rates[indicator]
            logger.info(f"   {indicator}: {weight:.1%} (success: {rate:.1%})")
        
        return normalized_weights
    
    def get_buy_confidence(self, symbol: str, indicator_signals: Dict[str, bool], 
                          timeframe: str = '15m') -> float:
        weights = self.get_indicator_weights(symbol, timeframe)
        
        confidence = 0.0
        for indicator, is_bullish in indicator_signals.items():
            if is_bullish and indicator in weights:
                confidence += weights[indicator]
        
        logger.info(f"🎯 Buy confidence for {symbol}: {confidence:.1%}")
        
        return confidence
    
    def get_statistics(self, symbol: str, timeframe: str = '15m') -> Dict:
        indicators = ['rsi', 'stochastic', 'bollinger_bands', 'macd']
        
        stats = {
            'symbol': symbol,
            'timeframe': timeframe,
            'indicators': {}
        }
        
        for indicator in indicators:
            key = f"{indicator}_{timeframe}"
            signals = self.signals[symbol].get(key, deque())
            resolved = [s for s in signals if s['outcome_resolved']]
            
            if resolved:
                avg_outcome = sum(s['outcome_1h'] for s in resolved) / len(resolved)
                success_rate = self.get_success_rate(symbol, indicator, timeframe)
            else:
                avg_outcome = 0.0
                success_rate = 0.5
            
            stats['indicators'][indicator] = {
                'total_signals': len(signals),
                'resolved_signals': len(resolved),
                'success_rate': success_rate,
                'avg_outcome': avg_outcome
            }
        
        return stats
    
    def save_to_file(self, pending_resolutions_list=None):
        try:
            data = {
                'signals': {},
                'pending_resolutions': pending_resolutions_list or [],
                'last_save': datetime.now().isoformat()
            }
            
            for symbol, indicators in self.signals.items():
                data['signals'][symbol] = {}
                for key, signal_deque in indicators.items():
                    data['signals'][symbol][key] = list(signal_deque)
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"💾 Saved indicator performance data to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving indicator performance: {e}")
    
    def load_from_file(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            for symbol, indicators in data.get('signals', {}).items():
                for key, signals_list in indicators.items():
                    self.signals[symbol][key] = deque(signals_list, maxlen=self.max_signals_per_indicator)
            
            self.pending_resolutions = data.get('pending_resolutions', [])
            
            logger.info(f"📂 Loaded indicator performance data from {self.data_file}")
            if self.pending_resolutions:
                logger.info(f"📂 Loaded {len(self.pending_resolutions)} pending resolutions")
        except FileNotFoundError:
            logger.info(f"📂 No existing data file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading indicator performance: {e}")
