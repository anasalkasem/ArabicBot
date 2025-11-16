"""
مثال توضيحي لكيفية استخدام نظام Futures Trading

هذا الملف للتوضيح فقط - الاستخدام الفعلي سيكون في main.py
"""

import json
from binance_derivatives_client import BinanceDerivativesClient
from strategies.long_strategy import LongStrategy
from strategies.short_strategy import ShortStrategy

def example_futures_trading_flow():
    config = json.load(open('config.json'))
    futures_config = config.get('futures', {})
    
    if not futures_config.get('enabled', False):
        print("❌ Futures trading is disabled in config.json")
        print("✅ Set futures.enabled = true to activate")
        return
    
    print("🚀 Initializing Futures Trading System...")
    
    futures_client = BinanceDerivativesClient(testnet=futures_config.get('testnet', True))
    
    long_strategy = LongStrategy(config)
    short_strategy = ShortStrategy(config)
    
    print("\n📊 Example 1: Checking Market Regime and Selecting Strategy")
    market_regime = "BEAR"
    
    if market_regime == "BULL":
        print("🐂 Bull Market → Using LONG ONLY strategy")
        active_strategy = long_strategy
    elif market_regime == "BEAR":
        print("🐻 Bear Market → Using SHORT ONLY strategy")
        active_strategy = short_strategy
    elif market_regime == "SIDEWAYS":
        print("↔️ Sideways Market → Using BOTH strategies (context-dependent)")
        active_strategy = None
    
    print("\n📊 Example 2: Opening a LONG Position")
    if futures_client.client:
        symbol = "BTCUSDT"
        leverage = futures_config.get('default_leverage', 2)
        quantity = 0.001
        
        print(f"Setting leverage to {leverage}x for {symbol}...")
        futures_client.set_leverage(symbol, leverage)
        
        print(f"Opening LONG position: {quantity} {symbol}")
        order = futures_client.open_long_position(symbol, quantity, leverage)
        
        if order:
            entry_price = float(order['avgPrice'])
            liquidation_price = futures_client.calculate_liquidation_price(
                entry_price, leverage, 'LONG'
            )
            print(f"✅ Long position opened at ${entry_price:,.2f}")
            print(f"🛡️ Liquidation price: ${liquidation_price:,.2f}")
    else:
        print("⚠️ Demo mode - no real trading")
    
    print("\n📊 Example 3: Opening a SHORT Position (in Bear Market)")
    if market_regime == "BEAR" and futures_client.client:
        symbol = "ETHUSDT"
        leverage = 2
        quantity = 0.01
        
        futures_client.set_leverage(symbol, leverage)
        
        print(f"Opening SHORT position: {quantity} {symbol}")
        order = futures_client.open_short_position(symbol, quantity, leverage)
        
        if order:
            entry_price = float(order['avgPrice'])
            liquidation_price = futures_client.calculate_liquidation_price(
                entry_price, leverage, 'SHORT'
            )
            print(f"✅ Short position opened at ${entry_price:,.2f}")
            print(f"🛡️ Liquidation price: ${liquidation_price:,.2f}")
    else:
        print("⚠️ Demo mode or market regime not suitable for SHORT")
    
    print("\n📊 Example 4: Checking Position Status")
    if futures_client.client:
        positions = futures_client.get_all_positions()
        print(f"Open positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['position_side']} {pos['symbol']}: {pos['position_amt']} @ ${pos['entry_price']:,.2f}")
            print(f"    Unrealized P/L: ${pos['unrealized_profit']:,.2f}")
            print(f"    Liquidation: ${pos['liquidation_price']:,.2f}")
    
    print("\n📊 Example 5: Checking Entry Signal (Long Strategy)")
    indicators = {
        'rsi': 45,
        'stochastic': 30,
        'bb_lower': 95000,
        'current_price': 95100,
        'bb_upper': 96000
    }
    
    should_enter, reason = long_strategy.check_entry_signal(
        'BTCUSDT', indicators, 'SIDEWAYS'
    )
    
    if should_enter:
        print(f"✅ LONG entry signal detected: {reason}")
    else:
        print(f"❌ No LONG entry: {reason}")
    
    print("\n📊 Example 6: Checking Entry Signal (Short Strategy)")
    bear_indicators = {
        'rsi': 78,
        'stochastic': 85,
        'bb_upper': 3200,
        'current_price': 3195,
        'bb_lower': 3100
    }
    
    should_enter, reason = short_strategy.check_entry_signal(
        'ETHUSDT', bear_indicators, 'BEAR'
    )
    
    if should_enter:
        print(f"✅ SHORT entry signal detected: {reason}")
    else:
        print(f"❌ No SHORT entry: {reason}")
    
    print("\n📊 Example 7: Risk Management - Position Sizing")
    balance = 1000
    position_size_percent = futures_config['risk_management']['position_size_percent']
    position_value = balance * (position_size_percent / 100)
    leverage = futures_config.get('default_leverage', 2)
    
    print(f"Account balance: ${balance:,.2f}")
    print(f"Position size: {position_size_percent}% = ${position_value:,.2f}")
    print(f"With {leverage}x leverage: ${position_value * leverage:,.2f} contract value")
    print(f"Actual risk: ${position_value:,.2f} (your money at risk)")
    
    print("\n🎯 Summary:")
    print("✅ Futures client initialized")
    print("✅ Long & Short strategies loaded")
    print("✅ Market regime detection ready")
    print("✅ Risk management configured")
    print("\n📝 Next steps:")
    print("1. Get Futures API keys from Binance")
    print("2. Test on Testnet first (set testnet: true)")
    print("3. Run for 1 week on testnet")
    print("4. Switch to live trading (set testnet: false)")
    print("\n⚠️ Remember: Start with small amounts and low leverage (2x)!")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Futures Trading Integration Example")
    print("="*70)
    example_futures_trading_flow()
    print("="*70)
