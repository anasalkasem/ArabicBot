import os
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from logger_setup import setup_logger
import time

logger = setup_logger('binance_derivatives')

class BinanceDerivativesClient:
    def __init__(self, testnet=True):
        self.testnet = testnet
        self.client = None
        self.base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            api_key = os.environ.get('BINANCE_FUTURES_API_KEY') or os.environ.get('BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_FUTURES_API_SECRET') or os.environ.get('BINANCE_API_SECRET')
            
            if not api_key or not api_secret:
                logger.warning("⚠️ Futures API keys not found in environment. Using demo mode.")
                logger.warning("💡 Add BINANCE_FUTURES_API_KEY and BINANCE_FUTURES_API_SECRET to Replit Secrets.")
                return
            
            self.api_key = api_key
            self.api_secret = api_secret
            
            if self.testnet:
                try:
                    self.client = Client(api_key, api_secret, testnet=True)
                    logger.info("✅ Connected to Binance Futures Testnet successfully")
                except BinanceAPIException as e:
                    if "restricted location" in str(e).lower():
                        logger.warning("⚠️ Binance Futures Testnet is geo-restricted from Replit servers.")
                        logger.warning("Switching to Binance Futures Live API (read-only mode)...")
                        self.testnet = False
                        self.client = Client(api_key, api_secret)
                        self.base_url = "https://fapi.binance.com"
                        logger.info("✅ Connected to Binance Futures Live API successfully")
                    else:
                        raise
            else:
                self.client = Client(api_key, api_secret)
                logger.info("✅ Connected to Binance Futures Live API successfully")
                
        except BinanceAPIException as e:
            if "restricted location" in str(e).lower():
                logger.error("❌ Binance Futures API is geo-restricted from Replit servers.")
                logger.error("The bot will continue in DEMO mode (monitoring only).")
                logger.info("💡 To use real Futures trading, run the bot on your local computer or Railway.")
                self.client = None
            else:
                logger.error(f"Binance Futures API Error: {e}")
                self.client = None
        except Exception as e:
            logger.error(f"Error initializing Binance Futures client: {e}")
            logger.info("Continuing in DEMO mode...")
            self.client = None
    
    def set_leverage(self, symbol, leverage):
        if not self.client:
            logger.warning(f"Cannot set leverage - client not initialized. Would set {symbol} leverage to {leverage}x")
            return False
        
        try:
            result = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            logger.info(f"✅ Leverage set to {leverage}x for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error setting leverage for {symbol}: {e}")
            return False
    
    def set_margin_type(self, symbol, margin_type="ISOLATED"):
        if not self.client:
            logger.warning(f"Cannot set margin type - client not initialized.")
            return False
        
        try:
            result = self.client.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type
            )
            logger.info(f"✅ Margin type set to {margin_type} for {symbol}")
            return True
        except BinanceAPIException as e:
            if "No need to change margin type" in str(e):
                logger.debug(f"Margin type already {margin_type} for {symbol}")
                return True
            logger.error(f"Error setting margin type for {symbol}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting margin type for {symbol}: {e}")
            return False
    
    def get_futures_balance(self):
        if not self.client:
            return {}
        
        try:
            account = self.client.futures_account()
            balances = {}
            for asset in account['assets']:
                balance = float(asset['walletBalance'])
                if balance > 0:
                    balances[asset['asset']] = {
                        'wallet_balance': balance,
                        'unrealized_profit': float(asset['unrealizedProfit']),
                        'margin_balance': float(asset['marginBalance']),
                        'available_balance': float(asset['availableBalance'])
                    }
            return balances
        except Exception as e:
            logger.error(f"Error getting futures balance: {e}")
            return {}
    
    def get_futures_position(self, symbol):
        if not self.client:
            return None
        
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    return {
                        'symbol': pos['symbol'],
                        'position_amt': float(pos['positionAmt']),
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_profit': float(pos['unRealizedProfit']),
                        'liquidation_price': float(pos['liquidationPrice']),
                        'leverage': int(pos['leverage']),
                        'position_side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT'
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None
    
    def get_all_positions(self):
        if not self.client:
            return []
        
        try:
            positions = self.client.futures_position_information()
            open_positions = []
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    open_positions.append({
                        'symbol': pos['symbol'],
                        'position_amt': float(pos['positionAmt']),
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_profit': float(pos['unRealizedProfit']),
                        'liquidation_price': float(pos['liquidationPrice']),
                        'leverage': int(pos['leverage']),
                        'position_side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT'
                    })
            return open_positions
        except Exception as e:
            logger.error(f"Error getting all positions: {e}")
            return []
    
    def create_futures_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        if not self.client:
            logger.warning(f"Cannot create order - client not initialized. Would {side} {quantity} {symbol}")
            return None
        
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            
            if order_type in ['LIMIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']:
                if price:
                    params['price'] = price
                params['timeInForce'] = 'GTC'
            
            if order_type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET'] and stop_price:
                params['stopPrice'] = stop_price
            
            order = self.client.futures_create_order(**params)
            
            status = order.get('status', 'UNKNOWN')
            if status == 'FILLED':
                logger.info(f"✅ Futures order FILLED: {side} {quantity} {symbol}")
            elif status == 'PARTIALLY_FILLED':
                logger.warning(f"⚠️ Futures order PARTIALLY_FILLED: {side} {quantity} {symbol}")
            else:
                logger.info(f"📝 Futures order {status}: {side} {quantity} {symbol}")
            
            return order
        except Exception as e:
            logger.error(f"Error creating futures order: {e}")
            return None
    
    def open_long_position(self, symbol, quantity, leverage=2):
        if not self.set_leverage(symbol, leverage):
            return None
        
        return self.create_futures_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quantity=quantity
        )
    
    def open_short_position(self, symbol, quantity, leverage=2):
        if not self.set_leverage(symbol, leverage):
            return None
        
        return self.create_futures_order(
            symbol=symbol,
            side='SELL',
            order_type='MARKET',
            quantity=quantity
        )
    
    def close_long_position(self, symbol, quantity):
        return self.create_futures_order(
            symbol=symbol,
            side='SELL',
            order_type='MARKET',
            quantity=quantity
        )
    
    def close_short_position(self, symbol, quantity):
        return self.create_futures_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quantity=quantity
        )
    
    def set_stop_loss(self, symbol, side, quantity, stop_price):
        opposite_side = 'SELL' if side == 'LONG' else 'BUY'
        return self.create_futures_order(
            symbol=symbol,
            side=opposite_side,
            order_type='STOP_MARKET',
            quantity=quantity,
            stop_price=stop_price
        )
    
    def set_take_profit(self, symbol, side, quantity, take_profit_price):
        opposite_side = 'SELL' if side == 'LONG' else 'BUY'
        return self.create_futures_order(
            symbol=symbol,
            side=opposite_side,
            order_type='TAKE_PROFIT_MARKET',
            quantity=quantity,
            stop_price=take_profit_price
        )
    
    def get_funding_rate(self, symbol):
        if not self.client:
            return None
        
        try:
            funding_rate = self.client.futures_funding_rate(symbol=symbol, limit=1)
            if funding_rate:
                return {
                    'symbol': funding_rate[0]['symbol'],
                    'funding_rate': float(funding_rate[0]['fundingRate']),
                    'funding_time': funding_rate[0]['fundingTime']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting funding rate for {symbol}: {e}")
            return None
    
    def get_open_interest(self, symbol):
        if not self.client:
            return None
        
        try:
            open_interest = self.client.futures_open_interest(symbol=symbol)
            return {
                'symbol': open_interest['symbol'],
                'open_interest': float(open_interest['openInterest']),
                'time': open_interest['time']
            }
        except Exception as e:
            logger.error(f"Error getting open interest for {symbol}: {e}")
            return None
    
    def calculate_liquidation_price(self, entry_price, leverage, position_side, maintenance_margin_rate=0.004):
        if position_side == 'LONG':
            liquidation_price = entry_price * (1 - (1 / leverage) + maintenance_margin_rate)
        else:
            liquidation_price = entry_price * (1 + (1 / leverage) - maintenance_margin_rate)
        
        return liquidation_price
    
    def get_symbol_info(self, symbol):
        if not self.client:
            return None
        
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_mark_price(self, symbol):
        if not self.client:
            return None
        
        try:
            mark_price = self.client.futures_mark_price(symbol=symbol)
            return float(mark_price['markPrice'])
        except Exception as e:
            logger.error(f"Error getting mark price for {symbol}: {e}")
            return None
