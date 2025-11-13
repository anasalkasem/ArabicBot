from logger_setup import setup_logger
import json
import os

logger = setup_logger('risk_manager')

class RiskManager:
    def __init__(self, config, binance_client):
        self.config = config
        self.binance_client = binance_client
        self.positions_file = 'positions.json'
        self.positions = self.load_positions()
    
    def load_positions(self):
        if os.path.exists(self.positions_file):
            try:
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading positions: {e}")
                return {}
        return {}
    
    def save_positions(self):
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving positions: {e}")
    
    def calculate_position_size(self, symbol, current_price):
        try:
            balances = self.binance_client.get_account_balance()
            
            if not balances or 'USDT' not in balances:
                logger.warning("No USDT balance found")
                return 0
            
            usdt_balance = balances['USDT']['free']
            position_size_percent = self.config['risk_management']['position_size_percent']
            position_value = usdt_balance * (position_size_percent / 100)
            
            if current_price and current_price > 0:
                quantity = position_value / current_price
                
                symbol_info = self.binance_client.get_symbol_info(symbol)
                if symbol_info:
                    for filter in symbol_info['filters']:
                        if filter['filterType'] == 'LOT_SIZE':
                            step_size = float(filter['stepSize'])
                            quantity = round(quantity / step_size) * step_size
                            break
                
                logger.info(f"Position size for {symbol}: {quantity:.8f} (${position_value:.2f})")
                return quantity
            
            return 0
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def can_open_position(self, symbol):
        max_positions = self.config['risk_management']['max_positions']
        current_positions = len([p for p in self.positions.values() if p.get('status') == 'open'])
        
        if current_positions >= max_positions:
            logger.warning(f"Cannot open position - max positions ({max_positions}) reached")
            return False
        
        if symbol in self.positions and self.positions[symbol].get('status') == 'open':
            logger.warning(f"Position already open for {symbol}")
            return False
        
        return True
    
    def open_position(self, symbol, entry_price, quantity, signals):
        self.positions[symbol] = {
            'status': 'open',
            'entry_price': entry_price,
            'quantity': quantity,
            'signals': signals,
            'entry_time': str(pd.Timestamp.now())
        }
        self.save_positions()
        logger.info(f"📈 Position opened: {symbol} @ ${entry_price:.2f}, Quantity: {quantity:.8f}")
    
    def close_position(self, symbol, exit_price, reason):
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return None
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        profit_percent = ((exit_price - entry_price) / entry_price) * 100
        profit_usd = (exit_price - entry_price) * quantity
        
        position['status'] = 'closed'
        position['exit_price'] = exit_price
        position['exit_time'] = str(pd.Timestamp.now())
        position['profit_percent'] = profit_percent
        position['profit_usd'] = profit_usd
        position['close_reason'] = reason
        
        self.save_positions()
        
        profit_emoji = "💰" if profit_usd > 0 else "📉"
        logger.info(f"{profit_emoji} Position closed: {symbol} @ ${exit_price:.2f}, "
                   f"Profit: {profit_percent:.2f}% (${profit_usd:.2f}), Reason: {reason}")
        
        return position
    
    def get_open_positions(self):
        return {k: v for k, v in self.positions.items() if v.get('status') == 'open'}
    
    def get_position(self, symbol):
        return self.positions.get(symbol)

import pandas as pd
