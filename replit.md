# Binance Trading Bot

## Overview
بوت تداول آلي للعملات الرقمية على منصة Binance باستخدام استراتيجية تحليل فني متقدمة. البوت يقوم بمراقبة الأسعار تلقائياً وتنفيذ صفقات الشراء والبيع بناءً على إشارات من عدة مؤشرات فنية.

## Features
- **🎯 Market Regime Adaptation (جديد!)**: البوت يتكيف مع حالة السوق تلقائياً
  - تحديد ذكي لحالة السوق (Bull/Bear/Sideways)
  - تعديل ديناميكي للإعدادات حسب الظروف
  - استراتيجيات مخصصة لكل حالة سوق
- **التحليل الفني المتقدم**: استخدام RSI, Stochastic, Bollinger Bands, MACD, EMA, و ADX
- **Multi-Timeframe Analysis**: تحليل متعدد الأطر الزمنية (5m, 1h, 4h) لتأكيد الاتجاهات
- **Trailing Stop-Loss الديناميكي**: حماية تلقائية للأرباح مع تحريك نقطة الإيقاف
- **إدارة المخاطر الذكية**: Stop-Loss و Take-Profit يتكيفان مع حالة السوق تلقائياً
- **التنويع**: دعم التداول على أزواج عملات متعددة في نفس الوقت
- **إشعارات Telegram**: تنبيهات فورية للصفقات والأحداث المهمة
- **لوحة تحكم احترافية**: واجهة عربية RTL بتصميم iPhone 16
- **إحصائيات شاملة**: تتبع الأداء وحساب نسبة النجاح
- **وضع Testnet**: اختبار الاستراتيجيات بدون مخاطر مالية
- **قابل للتخصيص**: إعدادات سهلة التعديل عبر config.json

## Project Structure
```
.
├── main.py                    # البوت الرئيسي
├── binance_client.py          # إدارة الاتصال مع Binance API
├── technical_indicators.py    # حساب المؤشرات الفنية
├── trading_strategy.py        # منطق إشارات الشراء والبيع
├── risk_manager.py           # إدارة المخاطر والصفقات
├── logger_setup.py           # إعدادات التسجيل
├── config.json               # ملف الإعدادات
├── positions.json            # الصفقات المفتوحة (يتم إنشاؤه تلقائياً)
└── bot.log                   # ملف السجلات (يتم إنشاؤه تلقائياً)
```

## Configuration
جميع الإعدادات في ملف `config.json`:
- `trading_pairs`: أزواج العملات للتداول (مثل BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BNBUSDT)
- `testnet`: **false** للتداول الحقيقي (تم التعديل!)
- `risk_management`: إعدادات Stop-Loss, Take-Profit, Trailing Stop-Loss
- `multi_timeframe`: إعدادات التحليل متعدد الأطر الزمنية (5m, 1h, 4h)
- `indicators`: معلمات المؤشرات الفنية (RSI, MACD, EMA, ADX, إلخ)
- `trading`: إعدادات التداول (فترة الشموع، تكرار الفحص)

## Trading Strategy

### إشارات الشراء (جميع الشروط يجب أن تتحقق):
1. **RSI < 50**: السوق في منطقة التشبع البيعي (محسّن)
2. **Stochastic < 65**: تأكيد إضافي على التشبع البيعي (محسّن)
3. **السعر قريب من Bollinger Band السفلي**: السعر ضمن 1.5% من القاع (tolerance محسّن)
4. **Multi-Timeframe Confirmation**: يقبل bearish على إطار واحد فقط (ليس الاثنين)

### إشارات البيع (أي شرط يتحقق):
1. **RSI > 70**: السوق في منطقة التشبع الشرائي
2. **الربح >= 5%**: تحقق هدف الربح
3. **MACD تقاطع سلبي**: ضعف الزخم الصاعد
4. **Trailing Stop**: تفعيل تلقائي عند ربح 3%، يتحرك مع السعر

### إدارة المخاطر:
- **Stop-Loss**: خروج تلقائي عند خسارة 2%
- **Trailing Stop-Loss**: يبدأ عند ربح 3%، يحمي 2% من أعلى سعر
- **Position Sizing**: كل صفقة = 5% من الرصيد
- **Maximum Positions**: 3 صفقات مفتوحة كحد أقصى

### المؤشرات الفنية المستخدمة:
- **RSI (14)**: قياس قوة الزخم
- **Stochastic (14)**: تأكيد مناطق التشبع
- **Bollinger Bands (20, 2)**: تحديد نطاقات السعر
- **MACD (12, 26, 9)**: تحليل الاتجاه والزخم
- **EMA (50, 200)**: تحديد الاتجاه العام
- **ADX (14)**: قياس قوة الاتجاه

## Setup Instructions

### 1. إضافة المفاتيح السرية (Secrets)
في Replit Secrets (قائمة Tools → Secrets):
```
BINANCE_API_KEY = your_api_key_here
BINANCE_API_SECRET = your_api_secret_here
TELEGRAM_BOT_TOKEN = your_telegram_bot_token (اختياري)
TELEGRAM_CHAT_ID = your_telegram_chat_id (اختياري)
```

**مهم**: 
- للتجربة: استخدم [Binance Testnet](https://testnet.binance.vision/)
- للتداول الحقيقي: احصل على المفاتيح من [Binance API Management](https://www.binance.com/en/my/settings/api-management)
- للإشعارات: أنشئ بوت Telegram عبر [@BotFather](https://t.me/BotFather)

### 2. تشغيل البوت
اضغط على زر "Run" أو نفذ:
```bash
python main.py
```

## Current Status
- ✅ Python 3.12 environment setup
- ✅ All dependencies installed (numpy, pandas, pandas-ta, python-binance, requests)
- ✅ Binance API integration
- ✅ Technical indicators (RSI, Stochastic, Bollinger Bands, MACD, EMA, ADX)
- ✅ Multi-Timeframe Analysis (5m, 1h, 4h)
- ✅ Trailing Stop-Loss system
- ✅ Trading strategy implementation
- ✅ Risk management system
- ✅ Logging system
- ✅ Telegram notifications system
- ✅ Performance statistics tracking
- ✅ Real-time dashboard with analytics
- ✅ Testnet mode for safe testing
- ⏳ Demo mode active (waiting for API keys)

## Important Notes
- البوت حالياً في وضع **TESTNET** (تجريبي) - لا يتم استخدام أموال حقيقية
- للتحول إلى التداول الحقيقي: غيّر `"testnet": false` في config.json
- **تحذير**: التداول في العملات الرقمية يحمل مخاطر عالية
- اختبر الاستراتيجية جيداً على Testnet قبل استخدام أموال حقيقية

## Recent Changes
### 2025-11-15 (Latest Update - Market Regime Adaptation System)
- ✨ **Major Feature**: Market Regime Adaptation - البوت يغير استراتيجيته حسب حالة السوق!
  - تحديد تلقائي لحالة السوق: Bull (صاعد) / Bear (هابط) / Sideways (جانبي)
  - استراتيجية Bull: جريئة - RSI<55, Stoch<70, BB tolerance 2%, TP 5.2%
  - استراتيجية Bear: حذرة - يوقف الصفقات الجديدة، SL 2.1%, TP 3.2%
  - استراتيجية Sideways: متوازنة - الإعدادات القياسية
  - تطبيق multipliers على Stop-Loss و Take-Profit لكل صفقة
  - عرض حالة السوق في Dashboard مع مؤشرات بصرية
- 📁 **New Files**: market_regime.py - نظام تحديد حالة السوق
- ⚙️ **Config**: إضافة market_regime settings في config.json
- 🎨 **UI**: Market Regime card في Dashboard مع ألوان ديناميكية

### 2025-11-15 (Previous Update - Bug Fix)
- 🐛 **Bug Fix**: Fixed BB tolerance not reading from config.json
  - BB tolerance was hard-coded to 0.5% in trading_strategy.py
  - Now correctly reads from config.json (currently set to 1.5%)
  - Also fixed mode display to show LIVE vs TESTNET dynamically
- 🎨 **UI Enhancement**: Mode badge now shows green for LIVE, orange for TESTNET

### 2025-11-14 (Previous Update - Telegram Notifications + Statistics Dashboard)
- 📲 **Telegram Integration**: إشعارات فورية عند البيع/الشراء/الأخطاء
  - استخدام TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID من environment variables
  - telegram_notifier.py module جديد لإدارة الإشعارات
- 📊 **Performance Statistics**: نظام تتبع شامل للإحصائيات
  - statistics_tracker.py يحفظ جميع الصفقات في trading_stats.json
  - حساب Win Rate, Average Profit, Best/Worst Trade
  - إحصائيات يومية وإحصائيات لكل زوج تداول
  - /statistics API endpoint للحصول على البيانات
- 🎨 **Enhanced Dashboard**: واجهة محسّنة مع عرض الإحصائيات
  - قسم إحصائيات جديد يعرض 4 مقاييس رئيسية
  - تحديث تلقائي للبيانات كل 5 ثوانٍ
  - عرض 5 أزواج تداول (BTC, ETH, SOL, XRP, BNB)
- 📦 **Dependencies**: إضافة requests>=2.31.0 لـ Telegram HTTP API
- ✅ **Testing**: اختبار شامل - البوت يعمل بدون أخطاء

### 2025-11-14 (Previous Update - Optimized for Small Accounts)
- 🎨 **واجهة محسّنة**: إضافة أزرار تفاعلية (تحديث، إظهار/إخفاء السجلات، تصدير)
- 📱 **Responsive Design**: تصميم متجاوب كامل للهواتف والأجهزة اللوحية
- 🚀 **جاهز للنشر على Railway**: إضافة ملفات requirements.txt, Procfile, railway.json
- 💱 **More Trading Pairs**: إضافة XRP و BNB (إجمالي 5 عملات)
- ⚡ **Faster Checks**: تحليل السوق كل 5 ثواني (بدل 60 ثانية)
- ⚙️ **Optimized Settings**: إعدادات محسّنة للحسابات الصغيرة ($50-$100)

### 2025-11-13 (Multi-Timeframe & Trailing Stop)
- ✨ إضافة Multi-Timeframe Analysis (5m, 1h, 4h)
- ✨ إضافة Trailing Stop-Loss الديناميكي
- ✨ إضافة مؤشرات فنية جديدة: EMA (50, 200) و ADX (14)
- ✅ اختبار شامل للبوت مع جميع الميزات
- ✅ مراجعة معمارية ناجحة

### 2025-11-13 (Initial Setup)
- Initial project setup with complete trading bot
- Python 3.12 environment configured
- Core modules: API client, indicators, strategy, risk manager

## Next Steps
1. **إضافة مفاتيح API**: للانتقال من Demo Mode إلى التداول الفعلي
2. **تفعيل Telegram**: إضافة TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID للحصول على إشعارات فورية
3. **النشر على Railway**: لتشغيل البوت 24/7 بدون قيود جغرافية
4. **Backtesting System**: اختبار الاستراتيجية على بيانات تاريخية
5. **رسوم بيانية متقدمة**: إضافة Chart.js لعرض الأداء بصرياً
