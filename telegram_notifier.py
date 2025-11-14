import requests
import os
from logger_setup import setup_logger
from datetime import datetime

logger = setup_logger('telegram_notifier')

class TelegramNotifier:
    def __init__(self, config):
        self.enabled = config.get('telegram', {}).get('enabled', False)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        if self.enabled and (not self.bot_token or not self.chat_id):
            logger.warning("⚠️ Telegram enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment")
            logger.info("💡 Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to Replit Secrets")
            self.enabled = False
        elif self.enabled:
            logger.info("✅ Telegram notifications enabled")
    
    def send_message(self, message):
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.debug("✅ Telegram message sent")
                return True
            else:
                logger.error(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def notify_buy(self, symbol, price, quantity, signals):
        """إشعار عند فتح صفقة شراء"""
        signals_text = "\n".join([f"  • {s}" for s in signals[:3]])
        message = (
            f"🟢 <b>صفقة شراء جديدة!</b>\n\n"
            f"💱 العملة: <b>{symbol}</b>\n"
            f"💵 السعر: <b>${price:.2f}</b>\n"
            f"📊 الكمية: <b>{quantity:.4f}</b>\n"
            f"💰 القيمة: <b>${price * quantity:.2f}</b>\n\n"
            f"📈 الإشارات:\n{signals_text}\n\n"
            f"🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message)
    
    def notify_sell(self, symbol, price, quantity, entry_price, reason):
        """إشعار عند إغلاق صفقة"""
        profit_pct = ((price - entry_price) / entry_price) * 100
        profit_usd = (price - entry_price) * quantity
        
        if profit_pct >= 0:
            emoji = "🟢"
            status = "ربح"
        else:
            emoji = "🔴"
            status = "خسارة"
        
        reason_ar = {
            'TAKE_PROFIT': 'جني أرباح',
            'STOP_LOSS': 'إيقاف خسارة',
            'TRAILING_STOP': 'إيقاف متحرك',
            'RSI_OVERBOUGHT': 'RSI تشبع شرائي',
            'MACD_BEARISH_CROSS': 'MACD تقاطع هبوطي'
        }.get(reason, reason)
        
        message = (
            f"{emoji} <b>إغلاق صفقة - {status}!</b>\n\n"
            f"💱 العملة: <b>{symbol}</b>\n"
            f"📉 سعر الدخول: <b>${entry_price:.2f}</b>\n"
            f"📈 سعر الخروج: <b>${price:.2f}</b>\n"
            f"📊 الكمية: <b>{quantity:.4f}</b>\n\n"
            f"💰 الربح/الخسارة: <b>{profit_pct:+.2f}%</b> (<b>${profit_usd:+.2f}</b>)\n"
            f"🎯 السبب: <b>{reason_ar}</b>\n\n"
            f"🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message)
    
    def notify_daily_summary(self, stats):
        """إشعار بملخص يومي"""
        win_rate = (stats['wins'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
        
        message = (
            f"📊 <b>الملخص اليومي</b>\n\n"
            f"📈 إجمالي الصفقات: <b>{stats['total_trades']}</b>\n"
            f"🟢 صفقات رابحة: <b>{stats['wins']}</b>\n"
            f"🔴 صفقات خاسرة: <b>{stats['losses']}</b>\n"
            f"🎯 نسبة النجاح: <b>{win_rate:.1f}%</b>\n\n"
            f"💰 إجمالي الربح/الخسارة: <b>${stats['total_profit']:+.2f}</b>\n"
            f"📊 أفضل صفقة: <b>+${stats['best_trade']:.2f}</b>\n"
            f"📉 أسوأ صفقة: <b>${stats['worst_trade']:.2f}</b>\n\n"
            f"🕐 التاريخ: {datetime.now().strftime('%Y-%m-%d')}"
        )
        self.send_message(message)
    
    def notify_error(self, error_message):
        """إشعار عند حدوث خطأ"""
        message = (
            f"⚠️ <b>تنبيه خطأ</b>\n\n"
            f"❌ {error_message}\n\n"
            f"🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message)
    
    def notify_startup(self, pairs, mode):
        """إشعار عند بدء تشغيل البوت"""
        pairs_text = ", ".join(pairs)
        mode_ar = "تجريبي (Testnet)" if mode else "حقيقي (Live)"
        
        message = (
            f"🤖 <b>البوت بدأ العمل!</b>\n\n"
            f"🔧 الوضع: <b>{mode_ar}</b>\n"
            f"💱 الأزواج: <b>{pairs_text}</b>\n"
            f"📊 الفترة: كل 5 ثواني\n\n"
            f"🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.send_message(message)
