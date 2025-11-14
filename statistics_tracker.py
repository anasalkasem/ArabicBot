import json
import os
from datetime import datetime
from logger_setup import setup_logger

logger = setup_logger('statistics_tracker')

class StatisticsTracker:
    def __init__(self, stats_file='trading_stats.json'):
        self.stats_file = stats_file
        self.stats = self.load_stats()
    
    def load_stats(self):
        """تحميل الإحصائيات من الملف"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
        
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit_usd': 0.0,
            'total_profit_percent': 0.0,
            'best_trade': {'symbol': '', 'profit_pct': 0.0, 'profit_usd': 0.0},
            'worst_trade': {'symbol': '', 'profit_pct': 0.0, 'profit_usd': 0.0},
            'trades_history': [],
            'daily_stats': {},
            'symbol_stats': {}
        }
    
    def save_stats(self):
        """حفظ الإحصائيات"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def record_trade(self, symbol, entry_price, exit_price, quantity, reason):
        """تسجيل صفقة جديدة"""
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        profit_usd = (exit_price - entry_price) * quantity
        
        trade = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'profit_pct': profit_pct,
            'profit_usd': profit_usd,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        self.stats['total_trades'] += 1
        
        if profit_pct >= 0:
            self.stats['winning_trades'] += 1
        else:
            self.stats['losing_trades'] += 1
        
        self.stats['total_profit_usd'] += profit_usd
        self.stats['total_profit_percent'] += profit_pct
        
        if profit_pct > self.stats['best_trade']['profit_pct']:
            self.stats['best_trade'] = {
                'symbol': symbol,
                'profit_pct': profit_pct,
                'profit_usd': profit_usd
            }
        
        if profit_pct < self.stats['worst_trade']['profit_pct']:
            self.stats['worst_trade'] = {
                'symbol': symbol,
                'profit_pct': profit_pct,
                'profit_usd': profit_usd
            }
        
        self.stats['trades_history'].append(trade)
        if len(self.stats['trades_history']) > 100:
            self.stats['trades_history'] = self.stats['trades_history'][-100:]
        
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.stats['daily_stats']:
            self.stats['daily_stats'][today] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'profit_usd': 0.0
            }
        
        self.stats['daily_stats'][today]['trades'] += 1
        if profit_pct >= 0:
            self.stats['daily_stats'][today]['wins'] += 1
        else:
            self.stats['daily_stats'][today]['losses'] += 1
        self.stats['daily_stats'][today]['profit_usd'] += profit_usd
        
        if symbol not in self.stats['symbol_stats']:
            self.stats['symbol_stats'][symbol] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'profit_usd': 0.0
            }
        
        self.stats['symbol_stats'][symbol]['trades'] += 1
        if profit_pct >= 0:
            self.stats['symbol_stats'][symbol]['wins'] += 1
        else:
            self.stats['symbol_stats'][symbol]['losses'] += 1
        self.stats['symbol_stats'][symbol]['profit_usd'] += profit_usd
        
        self.save_stats()
        logger.info(f"📊 Trade recorded: {symbol} {profit_pct:+.2f}% (${profit_usd:+.2f})")
    
    def get_stats(self):
        """الحصول على الإحصائيات"""
        return self.stats
    
    def get_win_rate(self):
        """حساب نسبة النجاح"""
        if self.stats['total_trades'] == 0:
            return 0.0
        return (self.stats['winning_trades'] / self.stats['total_trades']) * 100
    
    def get_average_profit(self):
        """متوسط الربح لكل صفقة"""
        if self.stats['total_trades'] == 0:
            return 0.0
        return self.stats['total_profit_usd'] / self.stats['total_trades']
    
    def get_today_stats(self):
        """إحصائيات اليوم"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.stats['daily_stats']:
            return self.stats['daily_stats'][today]
        return {'trades': 0, 'wins': 0, 'losses': 0, 'profit_usd': 0.0}
    
    def get_recent_trades(self, limit=10):
        """آخر الصفقات"""
        return self.stats['trades_history'][-limit:]
