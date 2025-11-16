# 🔧 Main.py Integration Patch

## التعديلات المطلوبة على main.py

### 1. الإضافات في الـ Imports (أعلى الملف)

```python
# أضف هذه الـ imports بعد السطر 1
from binance_derivatives_client import BinanceDerivativesClient
from strategy_coordinator import StrategyCoordinator
```

---

### 2. تحديث `__init__` في `BinanceTradingBot` (السطر ~47)

```python
def __init__(self, config_file='config.json'):
    logger.info("=" * 80)
    logger.info("🤖 Binance Trading Bot Starting...")
    logger.info("=" * 80)
    
    # تحميل الإعدادات
    with open(config_file) as f:
        self.config = json.load(f)
    
    self.testnet = self.config.get('testnet', True)
    
    # ✅ NEW: تحقق من تفعيل Futures
    self.futures_enabled = self.config.get('futures', {}).get('enabled', False)
    
    # Spot Client (الأصلي)
    self.binance_client = BinanceClientManager(testnet=self.testnet)
    
    # ✅ NEW: Futures Client
    if self.futures_enabled:
        futures_testnet = self.config.get('futures', {}).get('testnet', True)
        self.futures_client = BinanceDerivativesClient(testnet=futures_testnet)
        logger.info("✅ Futures Trading ENABLED")
    else:
        self.futures_client = None
        logger.info("⚠️ Futures Trading DISABLED")
    
    # Database Manager
    try:
        self.db = DatabaseManager()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        self.db = None
    
    # Trading Strategy & Market Regime
    self.trading_strategy = TradingStrategy(self.config, self.binance_client)
    
    # ✅ NEW: Strategy Coordinator (لاختيار Long/Short)
    if self.futures_enabled:
        self.strategy_coordinator = StrategyCoordinator(self.config)
    else:
        self.strategy_coordinator = None
    
    # Risk Manager (مع دعم Futures)
    self.risk_manager = RiskManager(
        self.config, 
        self.binance_client, 
        self.trading_strategy, 
        self.db,
        futures_client=self.futures_client  # ✅ NEW: إضافة futures_client
    )
    
    # باقي الكود كما هو...
```

---

### 3. تحديث `process_symbol` لدعم Long/Short (السطر ~222)

#### الكود الأصلي (Spot فقط):
```python
def process_symbol(self, symbol):
    # ... existing code ...
    
    # تحقق من إشارة الشراء
    buy_signal, signal_info = self.trading_strategy.check_buy_signal(
        symbol, indicators, market_regime, trends
    )
    
    if buy_signal:
        # فتح صفقة شراء عادية
        # ... existing code ...
```

#### ✅ الكود الجديد (Spot + Futures Long/Short):
```python
def process_symbol(self, symbol):
    try:
        # تحليل الرمز (كما هو)
        if self.multi_tf_enabled:
            trends, timeframes_data = self.analyze_multi_timeframe(symbol)
        else:
            trends = {}
            timeframes_data = []
        
        indicators = self.analyze_symbol(symbol)
        
        # ... existing code (market regime, custom momentum, etc) ...
        
        # ✅ NEW: اختيار الاستراتيجية حسب السوق
        if self.futures_enabled and self.strategy_coordinator:
            # استخدام Strategy Coordinator الجديد
            allowed_strategies = self.strategy_coordinator.get_allowed_strategies(market_regime)
            self.strategy_coordinator.log_regime_strategy(market_regime)
            
            # تحقق من إشارة Long
            if 'LONG' in allowed_strategies:
                should_enter, reason = self.strategy_coordinator.long_strategy.check_entry_signal(
                    symbol, indicators, market_regime, trends
                )
                
                if should_enter:
                    logger.info(f"✅ LONG signal for {symbol}: {reason}")
                    
                    # فتح صفقة Long
                    current_price = indicators.get('current_price')
                    if self.risk_manager.can_open_position(symbol):
                        quantity = self.risk_manager.calculate_futures_position_size(
                            symbol, current_price
                        )
                        
                        if quantity > 0:
                            success = self.risk_manager.open_futures_position(
                                symbol=symbol,
                                entry_price=current_price,
                                quantity=quantity,
                                position_type='LONG',
                                signals=indicators,
                                market_regime=market_regime
                            )
                            if success:
                                logger.info(f"🟢 LONG position opened for {symbol}")
            
            # تحقق من إشارة Short
            if 'SHORT' in allowed_strategies:
                should_enter, reason = self.strategy_coordinator.short_strategy.check_entry_signal(
                    symbol, indicators, market_regime, trends
                )
                
                if should_enter:
                    logger.info(f"✅ SHORT signal for {symbol}: {reason}")
                    
                    # فتح صفقة Short
                    current_price = indicators.get('current_price')
                    if self.risk_manager.can_open_position(symbol):
                        quantity = self.risk_manager.calculate_futures_position_size(
                            symbol, current_price
                        )
                        
                        if quantity > 0:
                            success = self.risk_manager.open_futures_position(
                                symbol=symbol,
                                entry_price=current_price,
                                quantity=quantity,
                                position_type='SHORT',
                                signals=indicators,
                                market_regime=market_regime
                            )
                            if success:
                                logger.info(f"🔴 SHORT position opened for {symbol}")
        
        else:
            # ✅ Spot Trading (الكود الأصلي - كما هو)
            buy_signal, signal_info = self.trading_strategy.check_buy_signal(
                symbol, indicators, market_regime, trends
            )
            
            if buy_signal:
                logger.info(f"✅ BUY signal for {symbol}")
                current_price = indicators.get('current_price')
                
                if self.risk_manager.can_open_position(symbol):
                    quantity = self.risk_manager.calculate_position_size(symbol, current_price)
                    
                    if quantity > 0:
                        order = self.binance_client.create_market_order(symbol, 'BUY', quantity)
                        
                        if order and order.get('status') == 'FILLED':
                            logger.info(f"💸 Buying {symbol} at ${current_price:.2f}")
                            self.risk_manager.open_position(symbol, current_price, quantity, indicators)
        
        # تحقق من إشارات البيع/الخروج
        open_positions = self.risk_manager.get_open_positions()
        
        for pos_symbol, position in open_positions.items():
            if pos_symbol == symbol and position.get('status') == 'open':
                current_price = indicators.get('current_price')
                position_type = position.get('position_type', 'SPOT')
                
                # ✅ NEW: استخدام Strategy Coordinator لفحص الخروج
                if self.futures_enabled and self.strategy_coordinator and position_type in ['LONG', 'SHORT']:
                    should_exit, exit_reason, profit_pct = self.strategy_coordinator.check_exit_signal(
                        symbol, position, current_price, indicators
                    )
                    
                    if should_exit:
                        logger.info(f"❌ EXIT signal for {position_type} {symbol}: {exit_reason}")
                        self.risk_manager.close_futures_position(symbol, current_price, exit_reason)
                    
                    else:
                        # تحديث Trailing Stop
                        self.risk_manager.update_futures_trailing_stop(symbol, current_price)
                
                else:
                    # ✅ Spot Trading Exit (الكود الأصلي)
                    should_sell, sell_reason = self.trading_strategy.check_sell_signal(
                        symbol, position, current_price, indicators
                    )
                    
                    if should_sell:
                        logger.info(f"💵 Selling {symbol} at ${current_price:.2f}")
                        order = self.binance_client.create_market_order(symbol, 'SELL', position['quantity'])
                        
                        if order and order.get('status') == 'FILLED':
                            self.risk_manager.close_position(symbol, current_price, sell_reason)
                    
                    else:
                        # تحديث Trailing Stop
                        self.risk_manager.update_trailing_stop(symbol, current_price)
    
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        import traceback
        logger.error(traceback.format_exc())
```

---

### 4. تحديث `/status` endpoint (لعرض معلومات Futures)

```python
@app.route('/status')
def get_status():
    """إرجاع حالة البوت والصفقات"""
    if bot_instance:
        try:
            open_positions = bot_instance.risk_manager.get_open_positions()
            positions_data = []
            
            for symbol, pos in open_positions.items():
                # الحصول على السعر الحالي
                current_price = bot_instance.binance_client.get_symbol_price(symbol)
                if not current_price:
                    current_price = pos.get('entry_price', 0)
                
                position_type = pos.get('position_type', 'SPOT')
                leverage = pos.get('leverage', 1)
                
                # ✅ حساب الربح/الخسارة حسب نوع الصفقة
                if position_type in ['LONG', 'BUY', 'SPOT']:
                    profit_percent = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                elif position_type in ['SHORT', 'SELL']:
                    profit_percent = ((pos['entry_price'] - current_price) / pos['entry_price']) * 100
                else:
                    profit_percent = 0.0
                
                # ضرب في leverage للـ Futures
                if position_type in ['LONG', 'SHORT']:
                    profit_percent = profit_percent * leverage
                
                # ✅ حساب Stop-Loss و Take-Profit الفعلي
                entry_price = pos['entry_price']
                stop_loss_percent = pos.get('stop_loss_percent', 0)
                take_profit_percent = pos.get('take_profit_percent', 0)
                
                if position_type in ['LONG', 'BUY', 'SPOT']:
                    stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
                    take_profit_price = entry_price * (1 + take_profit_percent / 100)
                else:
                    stop_loss_price = entry_price * (1 + stop_loss_percent / 100)
                    take_profit_price = entry_price * (1 - take_profit_percent / 100)
                
                positions_data.append({
                    'symbol': symbol,
                    'entry_price': pos['entry_price'],
                    'quantity': pos['quantity'],
                    'current_price': current_price,
                    'profit_percent': profit_percent,
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price,
                    'entry_time': pos.get('entry_time', ''),
                    'market_regime': pos.get('market_regime', 'unknown'),
                    # ✅ NEW: Futures metadata
                    'position_type': position_type,
                    'leverage': leverage,
                    'liquidation_price': pos.get('liquidation_price', None),
                    'unrealized_pnl': pos.get('unrealized_pnl', 0.0)
                })
            
            return jsonify({
                'running': True,
                'positions': positions_data,
                'bot_stats': bot_stats
            })
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'running': False, 'positions': []})
```

---

## ملخص التعديلات

| الملف | التعديل | الحالة |
|-------|---------|--------|
| main.py (imports) | إضافة Futures & Strategy imports | ⏳ مطلوب |
| main.py (__init__) | إنشاء futures_client & coordinator | ⏳ مطلوب |
| main.py (process_symbol) | دمج Long/Short strategy selection | ⏳ مطلوب |
| main.py (/status) | إضافة Futures metadata | ⏳ مطلوب |

---

## طريقة التطبيق

### Option 1: تطبيق يدوي (موصى به)
```bash
# 1. افتح main.py
# 2. نسخ/لصق التعديلات أعلاه في الأماكن المحددة
# 3. احفظ الملف
# 4. اختبر على Testnet
```

### Option 2: Backup & Replace
```bash
# 1. عمل نسخة احتياطية
cp main.py main.py.backup

# 2. تطبيق التعديلات بحذر
# 3. اختبر البوت
# 4. إذا فشل، استرجع النسخة الاحتياطية:
# mv main.py.backup main.py
```

---

## اختبار بعد التكامل

```bash
# 1. تفعيل Testnet في config.json
"futures": {
  "enabled": true,
  "testnet": true
}

# 2. شغّل البوت
python main.py

# 3. راقب السجلات:
# ✅ "Futures Trading ENABLED"
# ✅ "Market Regime: BEAR → Allowed strategies: SHORT"
# ✅ "SHORT signal for ETHUSDT"
# ✅ "🔴 SHORT position opened"
```

---

## ⚠️ تحذيرات مهمة

1. **اختبر على Testnet أولاً** - لا تفعّل على Live مباشرة!
2. **تحقق من API Keys** - Futures تحتاج API keys منفصلة
3. **راقب Liquidation Price** - لا تتجاهل تحذيرات Stop-Loss
4. **Leverage منخفض** - ابدأ بـ 2x فقط

---

**🎯 Good Luck!** 🚀
