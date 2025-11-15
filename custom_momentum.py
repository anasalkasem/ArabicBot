from logger_setup import setup_logger
import numpy as np

logger = setup_logger('custom_momentum')

class CustomMomentumIndex:
    def __init__(self, config, sentiment_analyzer=None):
        self.config = config
        self.momentum_config = config.get('custom_momentum', {})
        self.sentiment_analyzer = sentiment_analyzer
        
        self.enabled = self.momentum_config.get('enabled', False)
        
        self.weights = self.momentum_config.get('weights', {})
        self.technical_weight = self.weights.get('technical', 40)
        self.sentiment_weight = self.weights.get('sentiment', 30)
        self.volume_weight = self.weights.get('volume', 20)
        self.relative_strength_weight = self.weights.get('relative_strength', 10)
        
        total_weight = (self.technical_weight + self.sentiment_weight + 
                       self.volume_weight + self.relative_strength_weight)
        if abs(total_weight - 100) > 0.1:
            logger.warning(f"⚠️ Weights don't sum to 100: {total_weight}")
        
        self.buy_threshold = self.momentum_config.get('buy_threshold', 20)
        self.sell_threshold = self.momentum_config.get('sell_threshold', 80)
        
        logger.info(f"✅ Custom Momentum Index initialized")
        logger.info(f"   Weights: Tech={self.technical_weight}%, Sentiment={self.sentiment_weight}%, " + 
                   f"Volume={self.volume_weight}%, RelStrength={self.relative_strength_weight}%")
        logger.info(f"   Thresholds: Buy<{self.buy_threshold}, Sell>{self.sell_threshold}")
    
    def compute(self, symbol, indicators, volume_24h_avg=None, btc_change_24h=None, symbol_open_24h=None):
        """
        حساب Custom Momentum Index (0-100)
        
        Parameters:
        - symbol: العملة (مثل BTCUSDT)
        - indicators: dict من المؤشرات الفنية
        - volume_24h_avg: متوسط حجم التداول 24 ساعة
        - btc_change_24h: تغير BTC خلال 24h (%)
        - symbol_open_24h: سعر افتتاح العملة قبل 24 ساعة
        
        Returns:
        - momentum_index: درجة 0-100
        - components: dict بتفاصيل كل component
        """
        try:
            if not self.enabled:
                return None, None
            
            technical_score = self.calculate_technical_score(indicators)
            
            sentiment_score = 50.0
            sentiment_source = 'disabled'
            if self.sentiment_analyzer and self.sentiment_weight > 0:
                sentiment_score, sentiment_source = self.sentiment_analyzer.get_sentiment_score(symbol)
            
            volume_score = 50.0
            if volume_24h_avg is not None and self.volume_weight > 0:
                volume_score = self.calculate_volume_score(indicators, volume_24h_avg)
            
            relative_strength_score = 50.0
            if (btc_change_24h is not None and symbol_open_24h is not None and 
                self.relative_strength_weight > 0):
                relative_strength_score = self.calculate_relative_strength(symbol, indicators, btc_change_24h, symbol_open_24h)
            
            momentum_index = (
                (technical_score * self.technical_weight / 100) +
                (sentiment_score * self.sentiment_weight / 100) +
                (volume_score * self.volume_weight / 100) +
                (relative_strength_score * self.relative_strength_weight / 100)
            )
            
            components = {
                'technical': {'score': technical_score, 'weight': self.technical_weight},
                'sentiment': {'score': sentiment_score, 'weight': self.sentiment_weight, 'source': sentiment_source},
                'volume': {'score': volume_score, 'weight': self.volume_weight},
                'relative_strength': {'score': relative_strength_score, 'weight': self.relative_strength_weight}
            }
            
            logger.info(f"📊 Custom Momentum Index for {symbol}: {momentum_index:.1f}/100")
            logger.info(f"   🔧 Technical: {technical_score:.1f} ({self.technical_weight}%)")
            logger.info(f"   💭 Sentiment: {sentiment_score:.1f} ({self.sentiment_weight}%) - {sentiment_source}")
            logger.info(f"   📈 Volume: {volume_score:.1f} ({self.volume_weight}%)")
            logger.info(f"   ⚖️  Rel.Strength: {relative_strength_score:.1f} ({self.relative_strength_weight}%)")
            
            return momentum_index, components
            
        except Exception as e:
            logger.error(f"Error computing Custom Momentum Index: {e}")
            return None, None
    
    def calculate_technical_score(self, indicators):
        """
        حساب Technical Score (0-100) من RSI, MACD, Stochastic
        """
        try:
            rsi = indicators.get('rsi', 50)
            stoch_k = indicators.get('stoch_k', 50)
            macd_hist = indicators.get('macd_hist', 0)
            
            rsi_score = 100 - rsi
            
            stoch_score = 100 - stoch_k
            
            macd_normalized = self.normalize_macd(macd_hist)
            
            technical_score = (rsi_score + stoch_score + macd_normalized) / 3
            
            logger.debug(f"   Technical components: RSI={rsi_score:.1f}, Stoch={stoch_score:.1f}, MACD={macd_normalized:.1f}")
            
            return technical_score
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 50.0
    
    def normalize_macd(self, macd_hist):
        """
        تحويل MACD histogram إلى 0-100 scale
        MACD سالب = oversold (high score)
        MACD موجب = overbought (low score)
        """
        try:
            if np.isnan(macd_hist) or macd_hist == 0:
                return 50.0
            
            macd_clamped = max(-100, min(100, macd_hist * 100))
            
            score = 50 - (macd_clamped / 2)
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error normalizing MACD: {e}")
            return 50.0
    
    def calculate_volume_score(self, indicators, volume_24h_avg):
        """
        حساب Volume Score (0-100)
        حجم تداول عالي + سعر منخفض = فرصة شراء (high score)
        """
        try:
            if volume_24h_avg is None or volume_24h_avg == 0:
                return 50.0
            
            current_volume = indicators.get('volume', 0)
            
            if current_volume == 0:
                return 50.0
            
            volume_ratio = current_volume / volume_24h_avg
            
            if volume_ratio > 1.5:
                score = 75
            elif volume_ratio > 1.2:
                score = 65
            elif volume_ratio > 0.8:
                score = 50
            elif volume_ratio > 0.5:
                score = 35
            else:
                score = 20
            
            logger.debug(f"   Volume: current={current_volume:.0f}, avg_24h={volume_24h_avg:.0f}, ratio={volume_ratio:.2f}x, score={score}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating volume score: {e}")
            return 50.0
    
    def calculate_relative_strength(self, symbol, indicators, btc_change_24h, symbol_open_24h):
        """
        حساب Relative Strength Score (0-100)
        عملة ترتفع أكثر من BTC = قوة نسبية
        
        Parameters:
        - symbol: رمز العملة
        - indicators: المؤشرات الفنية
        - btc_change_24h: تغير BTC خلال 24 ساعة (%)
        - symbol_open_24h: سعر افتتاح العملة قبل 24 ساعة
        """
        try:
            if symbol == 'BTCUSDT' or btc_change_24h is None or symbol_open_24h is None:
                return 50.0
            
            current_price = indicators.get('close', 0)
            
            if symbol_open_24h == 0:
                return 50.0
            
            coin_change_24h = ((current_price - symbol_open_24h) / symbol_open_24h) * 100
            
            relative_performance = coin_change_24h - btc_change_24h
            
            score = 50 + (relative_performance * 5)
            score = max(0, min(100, score))
            
            logger.debug(f"   RelStrength: coin={coin_change_24h:+.2f}%, BTC={btc_change_24h:+.2f}%, diff={relative_performance:+.2f}%, score={score:.1f}")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating relative strength: {e}")
            return 50.0
    
    def should_buy(self, momentum_index):
        """
        هل يجب الشراء بناءً على Custom Momentum Index؟
        """
        if momentum_index is None:
            return False
        
        return momentum_index < self.buy_threshold
    
    def should_sell(self, momentum_index):
        """
        هل يجب البيع بناءً على Custom Momentum Index؟
        """
        if momentum_index is None:
            return False
        
        return momentum_index > self.sell_threshold
