from logger_setup import setup_logger
import json
import os
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests

logger = setup_logger('sentiment_analyzer')

class SentimentAnalyzer:
    def __init__(self, config):
        self.config = config
        self.sentiment_config = config.get('custom_momentum', {}).get('sentiment', {})
        self.cache_file = 'sentiment_cache.json'
        self.cache_ttl_minutes = self.sentiment_config.get('cache_ttl_minutes', 15)
        
        self.vader = SentimentIntensityAnalyzer()
        self.cache = self.load_cache()
        
        self.reddit_enabled = False
        self.coingecko_enabled = True
        
        logger.info(f"✅ Sentiment Analyzer initialized (cache TTL: {self.cache_ttl_minutes} min)")
    
    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading sentiment cache: {e}")
                return {}
        return {}
    
    def save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sentiment cache: {e}")
    
    def is_cache_valid(self, symbol):
        if symbol not in self.cache:
            return False
        
        cached_time = datetime.fromisoformat(self.cache[symbol]['timestamp'])
        age_minutes = (datetime.now() - cached_time).total_seconds() / 60
        
        return age_minutes < self.cache_ttl_minutes
    
    def get_sentiment_score(self, symbol):
        """
        الحصول على sentiment score للعملة (0-100 scale)
        """
        try:
            if self.is_cache_valid(symbol):
                score = self.cache[symbol]['score']
                source = self.cache[symbol]['source']
                logger.debug(f"📦 Using cached sentiment for {symbol}: {score:.1f}/100 (source: {source})")
                return score, source
            
            coin_name = symbol.replace('USDT', '').lower()
            
            score, source = self.fetch_coingecko_sentiment(coin_name)
            
            if score is None:
                score, source = 50.0, 'default'
                logger.warning(f"⚠️ No sentiment data for {symbol}, using neutral (50/100)")
            
            self.cache[symbol] = {
                'score': score,
                'source': source,
                'timestamp': datetime.now().isoformat()
            }
            self.save_cache()
            
            logger.info(f"💭 Sentiment for {symbol}: {score:.1f}/100 (source: {source})")
            return score, source
            
        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")
            return 50.0, 'error_fallback'
    
    def fetch_coingecko_sentiment(self, coin_name):
        """
        الحصول على sentiment من CoinGecko community stats
        """
        try:
            coin_id_map = {
                'btc': 'bitcoin',
                'eth': 'ethereum',
                'sol': 'solana',
                'xrp': 'ripple',
                'bnb': 'binancecoin'
            }
            
            coin_id = coin_id_map.get(coin_name, coin_name)
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'false',
                'community_data': 'true',
                'developer_data': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"CoinGecko API returned {response.status_code}")
                return None, None
            
            data = response.json()
            community_data = data.get('community_data', {})
            
            twitter_followers = community_data.get('twitter_followers', 0)
            reddit_subscribers = community_data.get('reddit_subscribers', 0)
            sentiment_up = community_data.get('sentiment_votes_up_percentage', 50)
            sentiment_down = community_data.get('sentiment_votes_down_percentage', 50)
            
            if sentiment_up > 0 or sentiment_down > 0:
                net_sentiment = sentiment_up
            else:
                net_sentiment = 50.0
            
            social_score = min(100, (twitter_followers / 10000 + reddit_subscribers / 1000) * 10)
            
            final_score = (net_sentiment * 0.7) + (social_score * 0.3)
            final_score = max(0, min(100, final_score))
            
            logger.debug(f"CoinGecko sentiment for {coin_name}: sentiment={sentiment_up:.1f}%, social={social_score:.1f}, final={final_score:.1f}")
            
            return final_score, 'coingecko'
            
        except Exception as e:
            logger.error(f"Error fetching CoinGecko sentiment: {e}")
            return None, None
    
    def analyze_text_sentiment(self, text):
        """
        تحليل sentiment نص باستخدام VADER
        يعيد compound score من -1 إلى +1
        """
        try:
            scores = self.vader.polarity_scores(text)
            return scores['compound']
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {e}")
            return 0.0
    
    def normalize_sentiment_to_100(self, compound_score):
        """
        تحويل VADER compound score (-1 to +1) إلى scale 0-100
        """
        return ((compound_score + 1) / 2) * 100
