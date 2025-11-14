import os
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from logger_setup import setup_logger

logger = setup_logger('binance_client')

class BinanceClientManager:
    def __init__(self, testnet=True):
        self.testnet = testnet
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            api_key = os.environ.get('BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_API_SECRET')
            
            if not api_key or not api_secret:
                logger.warning("API keys not found in environment. Using demo mode.")
                logger.warning("Please add BINANCE_API_KEY and BINANCE_API_SECRET to Replit Secrets.")
                return
            
            if self.testnet:
                try:
                    self.client = Client(api_key, api_secret, testnet=True)
                    logger.info("✅ Connected to Binance Testnet successfully")
                except BinanceAPIException as e:
                    if "restricted location" in str(e).lower():
                        logger.warning("⚠️ Binance Testnet is geo-restricted from Replit servers.")
                        logger.warning("Switching to Binance Live API (read-only mode)...")
                        self.testnet = False
                        self.client = Client(api_key, api_secret)
                        logger.info("✅ Connected to Binance Live API successfully")
                    else:
                        raise
            else:
                self.client = Client(api_key, api_secret)
                logger.info("✅ Connected to Binance Live API successfully")
                
        except BinanceAPIException as e:
            if "restricted location" in str(e).lower():
                logger.error("❌ Binance API is geo-restricted from Replit servers.")
                logger.error("The bot will continue in DEMO mode (monitoring only).")
                logger.info("💡 To use real trading, run the bot on your local computer.")
                self.client = None
            else:
                logger.error(f"Binance API Error: {e}")
                self.client = None
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            logger.info("Continuing in DEMO mode...")
            self.client = None
    
    def get_account_balance(self):
        if not self.client:
            return {}
        
        try:
            account = self.client.get_account()
            balances = {}
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    balances[balance['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }
            return balances
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_symbol_price(self, symbol):
        try:
            if self.client:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return float(ticker['price'])
            else:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
                else:
                    logger.error(f"Error getting price for {symbol}: HTTP {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_historical_klines(self, symbol, interval, limit=100):
        try:
            if self.client:
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    limit=limit
                )
                return klines
            else:
                url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Error getting klines for {symbol}: HTTP {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error getting klines for {symbol}: {e}")
            return []
    
    def create_market_order(self, symbol, side, quantity):
        if not self.client:
            logger.warning(f"Cannot create order - client not initialized. Would {side} {quantity} {symbol}")
            return None
        
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Market order created: {side} {quantity} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            return None
    
    def create_test_order(self, symbol, side, quantity):
        if not self.client:
            logger.info(f"DEMO MODE: Would {side} {quantity} {symbol}")
            return {'demo': True, 'symbol': symbol, 'side': side, 'quantity': quantity}
        
        try:
            order = self.client.create_test_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Test order validated: {side} {quantity} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error creating test order: {e}")
            return None
    
    def get_symbol_info(self, symbol):
        if not self.client:
            return None
        
        try:
            info = self.client.get_symbol_info(symbol)
            return info
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
