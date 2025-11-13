# Binance Trading Bot

## Overview
بوت تداول آلي للعملات الرقمية على منصة Binance باستخدام استراتيجية تحليل فني متقدمة. البوت يقوم بمراقبة الأسعار تلقائياً وتنفيذ صفقات الشراء والبيع بناءً على إشارات من عدة مؤشرات فنية.

## Features
- **التحليل الفني المتقدم**: استخدام RSI, Stochastic Oscillator, Bollinger Bands, و MACD
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
- `trading_pairs`: أزواج العملات للتداول (مثل BTCUSDT, ETHUSDT)
- `testnet`: true للوضع التجريبي، false للتداول الحقيقي
- `risk_management`: إعدادات Stop-Loss, Take-Profit, حجم الصفقات
- `indicators`: معلمات المؤشرات الفنية (فترات RSI, MACD, إلخ)
- `trading`: إعدادات التداول (فترة الشموع، تكرار الفحص)

## Trading Strategy

### إشارات الشراء (جميع الشروط يجب أن تتحقق):
1. **RSI < 30**: السوق في منطقة التشبع البيعي
2. **Stochastic < 20**: تأكيد إضافي على التشبع البيعي
3. **السعر يلامس Bollinger Band السفلي**: السعر عند أدنى مستوياته

### إشارات البيع (أي شرط يتحقق):
1. **RSI > 70**: السوق في منطقة التشبع الشرائي
2. **الربح >= 5%**: تحقق هدف الربح
3. **MACD تقاطع سلبي**: ضعف الزخم الصاعد

### إدارة المخاطر:
- **Stop-Loss**: خروج تلقائي عند خسارة 2%
- **Position Sizing**: كل صفقة = 5% من الرصيد
- **Maximum Positions**: 3 صفقات مفتوحة كحد أقصى

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
- ✅ All dependencies installed
- ✅ Binance API integration
- ✅ Technical indicators (RSI, Stochastic, Bollinger Bands, MACD)
- ✅ Trading strategy implementation
- ✅ Risk management system
- ✅ Logging system
- ✅ Testnet mode for safe testing

## Important Notes
- البوت حالياً في وضع **TESTNET** (تجريبي) - لا يتم استخدام أموال حقيقية
- للتحول إلى التداول الحقيقي: غيّر `"testnet": false` في config.json
- **تحذير**: التداول في العملات الرقمية يحمل مخاطر عالية
- اختبر الاستراتيجية جيداً على Testnet قبل استخدام أموال حقيقية

## Recent Changes
- 2025-11-13: Initial project setup with complete trading bot implementation
- Python 3.12 environment configured
- All core modules implemented (API client, indicators, strategy, risk manager)
- Configuration system with JSON file

## Next Steps
1. اختبار البوت على Binance Testnet
2. إضافة نظام Backtesting لاختبار الاستراتيجية على بيانات تاريخية
3. إضافة نظام إشعارات (Telegram أو Email)
4. تطوير لوحة تحكم متقدمة مع رسوم بيانية
