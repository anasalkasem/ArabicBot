# Binance Trading Bot

## Overview
بوت تداول آلي للعملات الرقمية على منصة Binance باستخدام استراتيجية تحليل فني متقدمة. البوت يقوم بمراقبة الأسعار تلقائياً وتنفيذ صفقات الشراء والبيع بناءً على إشارات من عدة مؤشرات فنية.

## Features
- **التحليل الفني المتقدم**: استخدام RSI, Stochastic, Bollinger Bands, MACD, EMA, و ADX
- **Multi-Timeframe Analysis**: تحليل متعدد الأطر الزمنية (5m, 1h, 4h) لتأكيد الاتجاهات
- **Trailing Stop-Loss الديناميكي**: حماية تلقائية للأرباح مع تحريك نقطة الإيقاف
- **إدارة المخاطر الذكية**: Stop-Loss تلقائي (2%), Take-Profit (5%), وحجم صفقات محدد (5% من الرصيد)
- **التنويع**: دعم التداول على أزواج عملات متعددة في نفس الوقت
- **وضع Testnet**: اختبار الاستراتيجيات بدون مخاطر مالية
- **التسجيل الشامل**: تسجيل جميع العمليات والصفقات في ملفات log
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
- `trading_pairs`: أزواج العملات للتداول (مثل BTCUSDT, ETHUSDT, SOLUSDT)
- `testnet`: true للوضع التجريبي، false للتداول الحقيقي
- `risk_management`: إعدادات Stop-Loss, Take-Profit, Trailing Stop-Loss
- `multi_timeframe`: إعدادات التحليل متعدد الأطر الزمنية (5m, 1h, 4h)
- `indicators`: معلمات المؤشرات الفنية (RSI, MACD, EMA, ADX, إلخ)
- `trading`: إعدادات التداول (فترة الشموع، تكرار الفحص)

## Trading Strategy

### إشارات الشراء (جميع الشروط يجب أن تتحقق):
1. **RSI < 30**: السوق في منطقة التشبع البيعي
2. **Stochastic < 20**: تأكيد إضافي على التشبع البيعي
3. **السعر يلامس Bollinger Band السفلي**: السعر عند أدنى مستوياته
4. **Multi-Timeframe Confirmation**: الاتجاه على الأطر الزمنية الأعلى (1h, 4h) صاعد أو محايد

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

### 1. إضافة مفاتيح Binance API
في Replit Secrets (قائمة Tools → Secrets):
```
BINANCE_API_KEY = your_api_key_here
BINANCE_API_SECRET = your_api_secret_here
```

**مهم**: 
- للتجربة: استخدم [Binance Testnet](https://testnet.binance.vision/)
- للتداول الحقيقي: احصل على المفاتيح من [Binance API Management](https://www.binance.com/en/my/settings/api-management)

### 2. تشغيل البوت
اضغط على زر "Run" أو نفذ:
```bash
python main.py
```

## Current Status
- ✅ Python 3.12 environment setup
- ✅ All dependencies installed (numpy, pandas, pandas-ta, python-binance)
- ✅ Binance API integration
- ✅ Technical indicators (RSI, Stochastic, Bollinger Bands, MACD, EMA, ADX)
- ✅ Multi-Timeframe Analysis (5m, 1h, 4h)
- ✅ Trailing Stop-Loss system
- ✅ Trading strategy implementation
- ✅ Risk management system
- ✅ Logging system
- ✅ Testnet mode for safe testing
- ⏳ Demo mode active (waiting for API keys)

## Important Notes
- البوت حالياً في وضع **TESTNET** (تجريبي) - لا يتم استخدام أموال حقيقية
- للتحول إلى التداول الحقيقي: غيّر `"testnet": false` في config.json
- **تحذير**: التداول في العملات الرقمية يحمل مخاطر عالية
- اختبر الاستراتيجية جيداً على Testnet قبل استخدام أموال حقيقية

## Recent Changes
### 2025-11-13 (Latest Update)
- ✨ إضافة Multi-Timeframe Analysis لتحليل الاتجاهات على أطر زمنية متعددة
- ✨ إضافة Trailing Stop-Loss الديناميكي لحماية الأرباح
- ✨ إضافة مؤشرات فنية جديدة: EMA (50, 200) و ADX (14)
- ✨ تحسين منطق إشارات الشراء والبيع
- ✅ اختبار شامل للبوت مع جميع الميزات الجديدة
- ✅ مراجعة معمارية ناجحة (PASS rating)

### 2025-11-13 (Initial Setup)
- Initial project setup with complete trading bot implementation
- Python 3.12 environment configured
- All core modules implemented (API client, indicators, strategy, risk manager)
- Configuration system with JSON file

## Next Steps
1. **إضافة مفاتيح API**: للانتقال من Demo Mode إلى التداول الفعلي
2. **اختبار على Testnet**: تجربة البوت بأموال تجريبية قبل الأموال الحقيقية
3. **Backtesting System**: اختبار الاستراتيجية على بيانات تاريخية
4. **نظام الإشعارات**: إضافة Telegram أو Email للتنبيهات
5. **لوحة تحكم متقدمة**: واجهة رسومية مع مخططات بيانية
