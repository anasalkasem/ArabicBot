import pandas as pd
import numpy as np
import pandas_ta as ta
from logger_setup import setup_logger

logger = setup_logger('technical_indicators')

class TechnicalIndicators:
    def __init__(self, config):
        self.config = config
    
    def prepare_dataframe(self, klines):
        try:
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df
        except Exception as e:
            logger.error(f"Error preparing dataframe: {e}")
            return None
    
    def calculate_rsi(self, df):
        try:
            rsi_period = self.config['indicators']['rsi_period']
            df['rsi'] = ta.rsi(df['close'], length=rsi_period)
            return df
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return df
    
    def calculate_stochastic(self, df):
        try:
            stoch_period = self.config['indicators']['stochastic_period']
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=stoch_period, d=3, smooth_k=3)
            df['stoch_k'] = stoch['STOCHk_14_3_3']
            df['stoch_d'] = stoch['STOCHd_14_3_3']
            return df
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {e}")
            return df
    
    def calculate_bollinger_bands(self, df):
        try:
            bb_period = self.config['indicators']['bb_period']
            bb_std = self.config['indicators']['bb_std']
            bbands = ta.bbands(df['close'], length=bb_period, std=bb_std)
            
            if bbands is None or bbands.empty:
                logger.warning("Bollinger Bands calculation returned empty result")
                return df
            
            cols = bbands.columns.tolist()
            bb_upper_col = next((col for col in cols if 'BBU' in col), None)
            bb_middle_col = next((col for col in cols if 'BBM' in col), None)
            bb_lower_col = next((col for col in cols if 'BBL' in col), None)
            
            if bb_upper_col and bb_middle_col and bb_lower_col:
                df['bb_upper'] = bbands[bb_upper_col]
                df['bb_middle'] = bbands[bb_middle_col]
                df['bb_lower'] = bbands[bb_lower_col]
            else:
                logger.error(f"BB columns not found. Available: {cols}")
            
            return df
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return df
    
    def calculate_macd(self, df):
        try:
            fast = self.config['indicators']['macd_fast']
            slow = self.config['indicators']['macd_slow']
            signal = self.config['indicators']['macd_signal']
            
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            df['macd'] = macd[f'MACD_{fast}_{slow}_{signal}']
            df['macd_signal'] = macd[f'MACDs_{fast}_{slow}_{signal}']
            df['macd_hist'] = macd[f'MACDh_{fast}_{slow}_{signal}']
            return df
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return df
    
    def calculate_ema(self, df):
        try:
            ema_short = self.config['indicators']['ema_short']
            ema_long = self.config['indicators']['ema_long']
            
            df['ema_short'] = ta.ema(df['close'], length=ema_short)
            df['ema_long'] = ta.ema(df['close'], length=ema_long)
            return df
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return df
    
    def calculate_adx(self, df):
        try:
            adx_period = self.config['indicators']['adx_period']
            adx_data = ta.adx(df['high'], df['low'], df['close'], length=adx_period)
            df['adx'] = adx_data[f'ADX_{adx_period}']
            df['dmp'] = adx_data[f'DMP_{adx_period}']
            df['dmn'] = adx_data[f'DMN_{adx_period}']
            return df
        except Exception as e:
            logger.error(f"Error calculating ADX: {e}")
            return df
    
    def calculate_all_indicators(self, klines):
        df = self.prepare_dataframe(klines)
        if df is None or df.empty:
            return None
        
        df = self.calculate_rsi(df)
        df = self.calculate_stochastic(df)
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_macd(df)
        df = self.calculate_ema(df)
        df = self.calculate_adx(df)
        
        return df
    
    def get_latest_values(self, df):
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        return {
            'timestamp': latest['close_time'],
            'close': latest['close'],
            'volume': latest['volume'],
            'rsi': latest['rsi'],
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'bb_upper': latest['bb_upper'],
            'bb_middle': latest['bb_middle'],
            'bb_lower': latest['bb_lower'],
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal'],
            'macd_hist': latest['macd_hist'],
            'ema_short': latest['ema_short'],
            'ema_long': latest['ema_long'],
            'adx': latest['adx'],
            'dmp': latest['dmp'],
            'dmn': latest['dmn']
        }
    
    def analyze_trend(self, df):
        if df is None or df.empty:
            return 'neutral'
        
        latest = df.iloc[-1]
        
        ema_bullish = latest['ema_short'] > latest['ema_long']
        price_above_ema = latest['close'] > latest['ema_long']
        adx_strong = latest['adx'] > self.config['indicators']['adx_threshold']
        
        if ema_bullish and price_above_ema and adx_strong:
            return 'bullish'
        elif not ema_bullish and not price_above_ema and adx_strong:
            return 'bearish'
        else:
            return 'neutral'
