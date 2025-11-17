"""
Gunicorn Configuration for Railway Deployment
"""
import os
import threading
import logging

logger = logging.getLogger(__name__)

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1
threads = 4
timeout = 0
worker_class = 'sync'

def post_fork(server, worker):
    """
    تُنفذ بعد fork الـ worker - هنا نبدأ الـ background threads
    """
    from main import run_bot, run_telegram_bot
    
    logger.info("🔄 Post-fork: Starting background services in worker...")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    telegram_enabled = os.getenv('TELEGRAM_BOT_TOKEN') is not None
    if telegram_enabled:
        logger.info("📱 Starting Telegram bot in worker...")
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
    else:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set - Telegram bot disabled")
    
    logger.info("✅ Background services started in worker")
