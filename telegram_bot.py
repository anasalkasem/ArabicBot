import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotController:
    def __init__(self, bot_instance, db_manager, ai_analyzer=None):
        self.bot = bot_instance
        self.db = db_manager
        self.ai_analyzer = ai_analyzer
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("positions", self.positions_command))
        self.application.add_handler(CommandHandler("regime", self.regime_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("analyze", self.ai_analyze_command))
        self.application.add_handler(CommandHandler("audit", self.ai_audit_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.ai_chat_handler))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        logger.info("✅ Telegram bot handlers configured")
    
    def is_authorized(self, update: Update) -> bool:
        if not self.admin_chat_id:
            return True
        
        user_id = str(update.effective_chat.id)
        authorized = user_id == self.admin_chat_id
        
        if not authorized:
            logger.warning(f"⚠️ Unauthorized access attempt from {user_id}")
        
        return authorized
    
    def get_main_keyboard(self):
        keyboard = [
            [
                InlineKeyboardButton("📊 حالة البوت", callback_data='status'),
                InlineKeyboardButton("💰 الرصيد", callback_data='balance')
            ],
            [
                InlineKeyboardButton("📈 المراكز المفتوحة", callback_data='positions'),
                InlineKeyboardButton("📉 الإحصائيات", callback_data='stats')
            ],
            [
                InlineKeyboardButton("🎯 حالة السوق", callback_data='regime'),
                InlineKeyboardButton("📜 السجلات", callback_data='logs')
            ],
            [
                InlineKeyboardButton("🔄 تحديث", callback_data='refresh'),
                InlineKeyboardButton("❓ المساعدة", callback_data='help')
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        message = """
🤖 مرحباً بك في لوحة تحكم بوت Binance!

📊 معلومات البوت:
━━━━━━━━━━━━━━━━━━━━
🔹 الحالة: نشط وجاهز
🔹 الأزواج: 5 أزواج تداول
🔹 الوضع: تداول مباشر

استخدم الأزرار أدناه للتحكم بالبوت:
        """
        
        await update.message.reply_text(
            message,
            reply_markup=self.get_main_keyboard()
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        try:
            positions = self.bot.risk_manager.get_open_positions()
            regime = self.bot.trading_strategy.current_regime if self.bot.regime_enabled else 'sideways'
            
            regime_emoji = {
                'bull': '🐂',
                'bear': '🐻', 
                'sideways': '↔️'
            }
            
            message = f"""
📊 حالة البوت الحالية
━━━━━━━━━━━━━━━━━━━━

🟢 الحالة: نشط
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{regime_emoji.get(regime, '↔️')} حالة السوق: {regime.upper()}

📈 المراكز المفتوحة: {len(positions)}
💼 الحد الأقصى: {self.bot.config['risk_management']['max_positions']}

🎯 الميزات النشطة:
{'✅' if self.bot.regime_enabled else '❌'} Market Regime Adaptation
{'✅' if self.bot.momentum_enabled else '❌'} Custom Momentum Index  
{'✅' if self.bot.weaver_enabled else '❌'} Dynamic Strategy Weaver
{'✅' if self.bot.config['risk_management']['trailing_stop_loss']['enabled'] else '❌'} Trailing Stop-Loss
            """
            
            await update.message.reply_text(
                message,
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text(f"❌ خطأ في جلب الحالة: {str(e)}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        try:
            stats = self.bot.stats_tracker.get_statistics()
            
            total_trades = stats.get('total_trades', 0)
            winning_trades = stats.get('winning_trades', 0)
            losing_trades = stats.get('losing_trades', 0)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            message = f"""
📊 إحصائيات التداول
━━━━━━━━━━━━━━━━━━━━

📈 عدد الصفقات: {total_trades}
✅ صفقات رابحة: {winning_trades}
❌ صفقات خاسرة: {losing_trades}
🎯 نسبة النجاح: {win_rate:.1f}%

💰 الأرباح:
• المجموع: ${stats.get('total_profit_usd', 0):.2f}
• النسبة: {stats.get('total_profit_percent', 0):.2f}%

🏆 أفضل صفقة: {stats.get('best_trade', {}).get('profit_pct', 0):.2f}%
📉 أسوأ صفقة: {stats.get('worst_trade', {}).get('profit_pct', 0):.2f}%
            """
            
            await update.message.reply_text(
                message,
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text(f"❌ خطأ في جلب الإحصائيات: {str(e)}")
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        try:
            balances = self.bot.binance_client.get_account_balance()
            
            if not balances:
                await update.message.reply_text("⚠️ لا يمكن جلب الرصيد حالياً (وضع تجريبي أو خطأ)")
                return
            
            message = """
💰 رصيد الحساب
━━━━━━━━━━━━━━━━━━━━

"""
            
            for asset, balance in balances.items():
                if balance['free'] > 0 or balance['locked'] > 0:
                    total = balance['free'] + balance['locked']
                    message += f"""
🔹 {asset}:
   • متاح: {balance['free']:.8f}
   • محجوز: {balance['locked']:.8f}
   • المجموع: {total:.8f}
"""
            
            await update.message.reply_text(
                message,
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in balance_command: {e}")
            await update.message.reply_text(f"❌ خطأ في جلب الرصيد: {str(e)}")
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        try:
            positions = self.bot.risk_manager.get_open_positions()
            
            if not positions:
                await update.message.reply_text(
                    "📊 لا توجد مراكز مفتوحة حالياً",
                    reply_markup=self.get_main_keyboard()
                )
                return
            
            message = """
📈 المراكز المفتوحة
━━━━━━━━━━━━━━━━━━━━

"""
            
            for symbol, pos in positions.items():
                current_price = self.bot.binance_client.get_current_price(symbol)
                profit_pct = ((current_price - pos['entry_price']) / pos['entry_price'] * 100) if current_price else 0
                profit_emoji = "🟢" if profit_pct > 0 else "🔴"
                
                message += f"""
{profit_emoji} {symbol}
━━━━━━━━━━━━━━━━━━━━
• سعر الدخول: ${pos['entry_price']:.4f}
• السعر الحالي: ${current_price:.4f}
• الكمية: {pos['quantity']:.6f}
• الربح/الخسارة: {profit_pct:+.2f}%
• وقت الدخول: {pos['entry_time'][:16]}

"""
            
            await update.message.reply_text(
                message,
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in positions_command: {e}")
            await update.message.reply_text(f"❌ خطأ في جلب المراكز: {str(e)}")
    
    async def regime_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        try:
            if not self.bot.regime_enabled:
                await update.message.reply_text("⚠️ نظام Market Regime غير مفعّل")
                return
            
            regime = self.bot.trading_strategy.current_regime
            
            regime_info = {
                'bull': {
                    'emoji': '🐂',
                    'name': 'سوق صاعد',
                    'desc': 'جريء - Buy the Dip',
                    'color': '🟢'
                },
                'bear': {
                    'emoji': '🐻',
                    'name': 'سوق هابط',
                    'desc': 'حذر جداً - حماية رأس المال',
                    'color': '🔴'
                },
                'sideways': {
                    'emoji': '↔️',
                    'name': 'سوق جانبي',
                    'desc': 'متوازن - استراتيجية BB',
                    'color': '🟡'
                }
            }
            
            info = regime_info.get(regime, regime_info['sideways'])
            
            message = f"""
{info['color']} حالة السوق الحالية
━━━━━━━━━━━━━━━━━━━━

{info['emoji']} الحالة: {info['name']}
📋 الاستراتيجية: {info['desc']}

⚙️ التعديلات الحالية:
━━━━━━━━━━━━━━━━━━━━
{self.get_regime_adjustments(regime)}

💡 التوصية:
{self.get_regime_recommendation(regime)}
            """
            
            await update.message.reply_text(
                message,
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in regime_command: {e}")
            await update.message.reply_text(f"❌ خطأ في جلب حالة السوق: {str(e)}")
    
    def get_regime_adjustments(self, regime):
        config = self.bot.config['market_regime']
        strategy = config.get(f'{regime}_strategy', {})
        
        if regime == 'bull':
            return f"""
• RSI: +{strategy.get('rsi_oversold_adjustment', 0)}
• Stochastic: +{strategy.get('stoch_oversold_adjustment', 0)}
• Stop Loss: ×{strategy.get('stop_loss_multiplier', 1.0)}
• Take Profit: ×{strategy.get('take_profit_multiplier', 1.0)}
"""
        elif regime == 'bear':
            return f"""
• RSI: {strategy.get('rsi_oversold_adjustment', 0)}
• Stochastic: {strategy.get('stoch_oversold_adjustment', 0)}
• Stop Loss: ×{strategy.get('stop_loss_multiplier', 1.0)}
• Take Profit: ×{strategy.get('take_profit_multiplier', 1.0)}
"""
        else:
            return """
• إعدادات متوازنة قياسية
• استراتيجية Bollinger Bands
"""
    
    def get_regime_recommendation(self, regime):
        recommendations = {
            'bull': '✅ فرصة جيدة للشراء عند الانخفاضات',
            'bear': '⚠️ كن حذراً - تجنب المخاطرة الزائدة',
            'sideways': '💡 انتظر إشارات واضحة قبل الدخول'
        }
        return recommendations.get(regime, '💡 استمر في المراقبة')
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        try:
            log_file = 'bot.log'
            
            if not os.path.exists(log_file):
                await update.message.reply_text("⚠️ لا يوجد ملف سجلات")
                return
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_20 = lines[-20:] if len(lines) > 20 else lines
            
            message = """
📜 آخر 20 سطر من السجلات
━━━━━━━━━━━━━━━━━━━━

"""
            message += ''.join(last_20)
            
            if len(message) > 4096:
                message = message[-4096:]
            
            await update.message.reply_text(
                f"```\n{message}\n```",
                parse_mode='Markdown',
                reply_markup=self.get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in logs_command: {e}")
            await update.message.reply_text(f"❌ خطأ في جلب السجلات: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        message = """
❓ دليل المساعدة
━━━━━━━━━━━━━━━━━━━━

📋 الأوامر المتاحة:

/start - القائمة الرئيسية
/status - حالة البوت والمراكز
/stats - الإحصائيات والأداء
/balance - رصيد الحساب
/positions - المراكز المفتوحة
/regime - حالة السوق
/logs - آخر السجلات
/help - هذه الرسالة

💡 يمكنك أيضاً استخدام الأزرار التفاعلية!

🔔 الإشعارات التلقائية:
• فتح صفقة جديدة
• إغلاق صفقة (ربح/خسارة)
• تغير حالة السوق
• أخطاء مهمة

📊 البوت يعمل 24/7 ويراقب الأسواق تلقائياً!
        """
        
        await update.message.reply_text(
            message,
            reply_markup=self.get_main_keyboard()
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if not self.is_authorized(update):
            await query.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        handlers = {
            'status': self.status_button,
            'balance': self.balance_button,
            'positions': self.positions_button,
            'stats': self.stats_button,
            'regime': self.regime_button,
            'logs': self.logs_button,
            'help': self.help_button,
            'refresh': self.refresh_button
        }
        
        handler = handlers.get(query.data)
        if handler:
            await handler(query)
        else:
            await query.message.reply_text("❌ أمر غير معروف")
    
    async def status_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.status_command(temp_update, None)
    
    async def balance_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.balance_command(temp_update, None)
    
    async def positions_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.positions_command(temp_update, None)
    
    async def stats_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.stats_command(temp_update, None)
    
    async def regime_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.regime_command(temp_update, None)
    
    async def logs_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.logs_command(temp_update, None)
    
    async def help_button(self, query):
        temp_update = type('obj', (object,), {'message': query.message, 'effective_chat': query.message.chat})()
        await self.help_command(temp_update, None)
    
    async def refresh_button(self, query):
        await query.message.reply_text(
            "🔄 تم التحديث!\n\nاستخدم الأزرار أدناه:",
            reply_markup=self.get_main_keyboard()
        )
    
    async def send_notification(self, message: str):
        if not self.admin_chat_id:
            return
        
        try:
            await self.application.bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def ai_analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحليل السوق باستخدام AI"""
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        if not self.ai_analyzer or not self.ai_analyzer.enabled:
            await update.message.reply_text("⚠️ ميزة AI غير مفعّلة. تحتاج إلى OPENAI_API_KEY")
            return
        
        try:
            await update.message.reply_text("🤖 جاري تحليل السوق باستخدام الذكاء الاصطناعي...")
            
            symbol = context.args[0] if context.args else 'BTCUSDT'
            
            result = self.bot.analyze_symbol(symbol)
            if not result:
                await update.message.reply_text(f"❌ لا يمكن الحصول على بيانات {symbol}")
                return
            
            indicators, _trend = result
            
            market_regime = self.bot.trading_strategy.current_regime if self.bot.regime_enabled else 'sideways'
            momentum_index = self.bot.symbol_momentum_cache.get(symbol)
            recent_trades = self.bot.stats.get_recent_trades(5)
            
            analysis = self.ai_analyzer.analyze_market_conditions(
                symbol, indicators, market_regime, momentum_index, recent_trades
            )
            
            if not analysis:
                await update.message.reply_text("❌ فشل تحليل AI")
                return
            
            recommendation_emoji = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '🟡'
            }
            
            risk_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🔴'
            }
            
            message = f"""
🤖 تحليل AI لـ {symbol}
━━━━━━━━━━━━━━━━━━━━

📊 التحليل:
{analysis['analysis']}

{recommendation_emoji.get(analysis['recommendation'], '⚪')} التوصية: {analysis['recommendation']}
🎯 مستوى الثقة: {analysis['confidence']:.0%}
{risk_emoji.get(analysis['risk_level'], '⚪')} المخاطرة: {analysis['risk_level']}

💡 نقاط رئيسية:
{chr(10).join(f"• {insight}" for insight in analysis['key_insights'])}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in AI analyze command: {e}")
            await update.message.reply_text(f"❌ خطأ: {str(e)}")
    
    async def ai_audit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تدقيق الاستراتيجية باستخدام AI"""
        if not self.is_authorized(update):
            await update.message.reply_text("⛔ عذراً، غير مصرح لك باستخدام هذا البوت")
            return
        
        if not self.ai_analyzer or not self.ai_analyzer.enabled:
            await update.message.reply_text("⚠️ ميزة AI غير مفعّلة. تحتاج إلى OPENAI_API_KEY")
            return
        
        try:
            await update.message.reply_text("🔍 جاري تدقيق الاستراتيجية...")
            
            stats = self.bot.stats.get_stats()
            win_rate = self.bot.stats.get_win_rate()
            avg_profit = self.bot.stats.get_average_profit()
            recent_trades = self.bot.stats.get_recent_trades(10)
            
            full_stats = {
                'total_trades': stats['total_trades'],
                'winning_trades': stats['winning_trades'],
                'losing_trades': stats['losing_trades'],
                'win_rate': win_rate,
                'total_profit_usd': stats['total_profit_usd'],
                'average_profit': avg_profit,
                'best_trade': stats['best_trade'],
                'worst_trade': stats['worst_trade']
            }
            
            audit = self.ai_analyzer.audit_strategy_performance(full_stats, recent_trades)
            
            if not audit:
                await update.message.reply_text("❌ فشل التدقيق")
                return
            
            message = f"""
🔍 تدقيق الاستراتيجية - AI
━━━━━━━━━━━━━━━━━━━━

⭐ التقييم العام: {audit['overall_rating']}
📊 الدرجة: {audit['performance_score']}/10

💪 نقاط القوة:
{chr(10).join(f"• {s}" for s in audit['strengths'])}

⚠️ نقاط الضعف:
{chr(10).join(f"• {w}" for w in audit['weaknesses'])}

🎯 التوصيات:
{chr(10).join(f"{i+1}. {r}" for i, r in enumerate(audit['recommendations']))}

🛡️ تقييم المخاطر:
{audit['risk_assessment']}

📌 الخطوات التالية:
{audit['next_steps']}
            """
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in AI audit command: {e}")
            await update.message.reply_text(f"❌ خطأ: {str(e)}")
    
    async def ai_chat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """الدردشة مع AI Assistant"""
        if not self.is_authorized(update):
            return
        
        if not self.ai_analyzer or not self.ai_analyzer.enabled:
            return
        
        try:
            user_message = update.message.text
            
            if len(user_message) < 5 or len(user_message) > 500:
                return
            
            await update.message.reply_text("🤖 جاري التفكير...")
            
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            stats = self.bot.stats.get_stats()
            positions = self.bot.risk_manager.get_open_positions()
            regime = self.bot.trading_strategy.current_regime if self.bot.regime_enabled else 'sideways'
            
            context_info = f"""
أنت مساعد تداول ذكي لبوت Binance. المعلومات الحالية:
- إجمالي الصفقات: {stats['total_trades']}
- نسبة النجاح: {self.bot.stats.get_win_rate():.1f}%
- المراكز المفتوحة: {len(positions)}
- حالة السوق: {regime}
- الأزواج: {', '.join(self.bot.trading_pairs)}

أجب بإيجاز ووضوح بالعربية.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context_info},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content.strip()
            await update.message.reply_text(f"🤖 {ai_response}")
            
        except Exception as e:
            logger.error(f"Error in AI chat handler: {e}")
    
    def run(self):
        logger.info("🤖 Starting Telegram bot...")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start_polling_async())
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Stopping Telegram bot...")
        finally:
            loop.close()
    
    async def start_polling_async(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("✅ Telegram bot polling started")
