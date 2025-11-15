from logger_setup import setup_logger
import numpy as np

logger = setup_logger('market_regime')

class MarketRegime:
    def __init__(self, config):
        self.config = config
        self.regime_config = config.get('market_regime', {})
        self.enabled = self.regime_config.get('enabled', True)
        
        self.bull_adx_threshold = self.regime_config.get('bull_adx_threshold', 25)
        self.sideways_adx_threshold = self.regime_config.get('sideways_adx_threshold', 20)
        self.trend_strength_periods = self.regime_config.get('trend_strength_periods', 10)
    
    def detect_regime(self, indicators, historical_data=None):
        """
        تحديد حالة السوق الحالية: Bull, Bear, أو Sideways
        """
        try:
            if not self.enabled:
                return 'sideways', "Market regime detection disabled"
            
            if not indicators or np.isnan(indicators.get('adx', np.nan)):
                return 'sideways', "Insufficient data"
            
            close = indicators['close']
            ema_50 = indicators.get('ema_short', np.nan)
            ema_200 = indicators.get('ema_long', np.nan)
            adx = indicators['adx']
            bb_upper = indicators['bb_upper']
            bb_lower = indicators['bb_lower']
            bb_middle = indicators['bb_middle']
            
            signals = []
            
            # 1. تحليل الاتجاه بناءً على EMA
            price_above_ema50 = close > ema_50
            price_above_ema200 = close > ema_200
            ema50_above_ema200 = ema_50 > ema_200
            
            # 2. قوة الاتجاه من ADX
            strong_trend = adx > self.bull_adx_threshold
            weak_trend = adx < self.sideways_adx_threshold
            
            # 3. موقع السعر في Bollinger Bands
            bb_range = bb_upper - bb_lower
            bb_position = (close - bb_lower) / bb_range if bb_range > 0 else 0.5
            
            # 4. حساب momentum من البيانات التاريخية
            momentum_bullish = False
            if historical_data and len(historical_data) >= self.trend_strength_periods:
                recent_prices = [candle[4] for candle in historical_data[-self.trend_strength_periods:]]
                price_change_pct = ((recent_prices[-1] - recent_prices[0]) / recent_prices[0]) * 100
                momentum_bullish = price_change_pct > 0
                signals.append(f"Momentum {self.trend_strength_periods} candles: {price_change_pct:+.2f}%")
            
            # تحديد حالة السوق
            regime = None
            confidence = 0
            
            # Bull Market: السعر فوق EMA + اتجاه قوي + momentum إيجابي
            if price_above_ema50 and price_above_ema200 and ema50_above_ema200:
                if strong_trend and momentum_bullish:
                    regime = 'bull'
                    confidence = 'high'
                    signals.append(f"🐂 Strong bull: Price above EMAs, ADX={adx:.1f}, Strong momentum")
                elif momentum_bullish:
                    regime = 'bull'
                    confidence = 'medium'
                    signals.append(f"🐂 Moderate bull: Price above EMAs, positive momentum")
            
            # Bear Market: السعر تحت EMA + اتجاه قوي + momentum سلبي
            elif not price_above_ema50 and not price_above_ema200 and not ema50_above_ema200:
                if strong_trend and not momentum_bullish:
                    regime = 'bear'
                    confidence = 'high'
                    signals.append(f"🐻 Strong bear: Price below EMAs, ADX={adx:.1f}, Negative momentum")
                elif not momentum_bullish:
                    regime = 'bear'
                    confidence = 'medium'
                    signals.append(f"🐻 Moderate bear: Price below EMAs, negative momentum")
            
            # Sideways Market: اتجاه ضعيف أو مختلط
            if regime is None or weak_trend:
                regime = 'sideways'
                confidence = 'high' if weak_trend else 'medium'
                signals.append(f"↔️ Sideways: ADX={adx:.1f}, Range-bound market")
            
            reason = ', '.join(signals)
            logger.info(f"Market regime detected: {regime.upper()} (confidence: {confidence}) - {reason}")
            
            return regime, reason
            
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return 'sideways', f"Error: {str(e)}"
    
    def get_regime_strategy(self, regime):
        """
        الحصول على الاستراتيجية المناسبة لحالة السوق
        """
        strategies = {
            'bull': {
                'name': 'Bull Strategy',
                'description': 'جريء - Buy the Dip',
                'buy_aggressiveness': 'high',
                'stop_loss_multiplier': 1.5,
                'take_profit_multiplier': 1.3,
                'allow_trading': True
            },
            'bear': {
                'name': 'Bear Strategy',
                'description': 'حذر جداً - حماية رأس المال',
                'buy_aggressiveness': 'very_low',
                'stop_loss_multiplier': 0.7,
                'take_profit_multiplier': 0.8,
                'allow_trading': False
            },
            'sideways': {
                'name': 'Sideways Strategy',
                'description': 'متوازن - استراتيجيتنا الحالية',
                'buy_aggressiveness': 'medium',
                'stop_loss_multiplier': 1.0,
                'take_profit_multiplier': 1.0,
                'allow_trading': True
            }
        }
        
        return strategies.get(regime, strategies['sideways'])
