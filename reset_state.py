#!/usr/bin/env python3
"""
سكريبت تنظيف وإعادة ضبط حالة البوت
- يحذف جميع الصفقات الشبح
- يعيد تعيين الإحصائيات
- يضمن بداية نظيفة
"""
import json
import os
from datetime import datetime

def reset_bot_state():
    print("=" * 70)
    print("🧹 بدء عملية التنظيف الشامل")
    print("=" * 70)
    
    # 1. حذف ملفات الحالة المحلية
    files_to_clean = [
        'positions.json',
        'trading_stats.json',
        'market_regime_history.json',
        'indicator_performance_data.json'
    ]
    
    for file in files_to_clean:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ تم حذف: {file}")
        else:
            print(f"⏭️  غير موجود: {file}")
    
    # 2. إنشاء ملفات جديدة فارغة
    initial_data = {
        'positions.json': {},
        'trading_stats.json': {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit_usd': 0.0,
            'win_rate': 0.0,
            'best_trade': {'profit': 0, 'symbol': None},
            'worst_trade': {'profit': 0, 'symbol': None},
            'last_updated': datetime.now().isoformat()
        },
        'indicator_performance_data.json': {}
    }
    
    for file, data in initial_data.items():
        with open(file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ تم إنشاء: {file}")
    
    # 3. تنظيف قاعدة البيانات (إذا كانت متاحة)
    try:
        from db_manager import DatabaseManager
        db = DatabaseManager()
        
        if db.conn:
            # حذف جميع الصفقات المفتوحة
            db.cur.execute("DELETE FROM positions")
            db.conn.commit()
            print("✅ تم تنظيف جدول positions")
            
            # إعادة تعيين الإحصائيات
            db.cur.execute("DELETE FROM daily_stats")
            db.cur.execute("DELETE FROM pair_stats")
            db.conn.commit()
            print("✅ تم تنظيف جداول الإحصائيات")
            
            db.close()
        else:
            print("⚠️  قاعدة البيانات غير متاحة - تم التنظيف المحلي فقط")
            
    except Exception as e:
        print(f"⚠️  تحذير قاعدة البيانات: {e}")
    
    print()
    print("=" * 70)
    print("✅ اكتمل التنظيف - البوت جاهز للبدء من جديد")
    print("=" * 70)

if __name__ == '__main__':
    reset_state.py()
