import json
import os
from datetime import datetime
from db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('migration')

def migrate_positions():
    if not os.path.exists('positions.json'):
        logger.info("No positions.json file found, skipping...")
        return
    
    try:
        with open('positions.json', 'r') as f:
            positions = json.load(f)
        
        if not positions:
            logger.info("No positions to migrate")
            return
        
        db = DatabaseManager()
        migrated = 0
        errors = []
        
        for symbol, pos in positions.items():
            try:
                db.save_position(
                    symbol=symbol,
                    entry_price=pos['entry_price'],
                    quantity=pos['quantity'],
                    entry_time=datetime.fromisoformat(pos['entry_time']),
                    stop_loss=pos.get('stop_loss'),
                    take_profit=pos.get('take_profit'),
                    trailing_stop_price=pos.get('trailing_stop_price'),
                    highest_price=pos.get('highest_price'),
                    market_regime=pos.get('market_regime'),
                    buy_signals=pos.get('buy_signals')
                )
                migrated += 1
                logger.info(f"✅ Migrated position: {symbol}")
            except Exception as e:
                logger.error(f"❌ Error migrating position {symbol}: {e}")
                errors.append(f"{symbol}: {e}")
        
        if errors:
            logger.warning(f"Migration completed with {len(errors)} errors. NOT backing up JSON file.")
            return
        
        logger.info(f"✅ Successfully migrated {migrated} positions without errors")
        db.close()
        
        os.rename('positions.json', 'positions.json.backup')
        logger.info("Backed up positions.json to positions.json.backup")
        
    except Exception as e:
        logger.error(f"Error migrating positions: {e}")

def migrate_stats():
    if not os.path.exists('trading_stats.json'):
        logger.info("No trading_stats.json file found, skipping...")
        return
    
    try:
        with open('trading_stats.json', 'r') as f:
            stats = json.load(f)
        
        if not stats or 'trades' not in stats:
            logger.info("No trades to migrate")
            return
        
        db = DatabaseManager()
        migrated = 0
        errors = []
        
        for trade in stats.get('trades', []):
            try:
                trade_id = db.save_trade(
                    symbol=trade['symbol'],
                    side='BUY',
                    entry_price=trade['entry_price'],
                    quantity=trade.get('quantity', 0),
                    entry_time=datetime.fromisoformat(trade['entry_time']),
                    stop_loss=trade.get('stop_loss'),
                    take_profit=trade.get('take_profit'),
                    market_regime=trade.get('market_regime'),
                    buy_signals=trade.get('buy_signals')
                )
                
                if trade.get('exit_price'):
                    db.close_trade(
                        symbol=trade['symbol'],
                        exit_price=trade['exit_price'],
                        exit_time=datetime.fromisoformat(trade['exit_time']),
                        profit_loss=trade.get('profit_loss', 0),
                        profit_loss_percent=trade.get('profit_loss_percent', 0),
                        sell_reason=trade.get('sell_reason', 'Unknown')
                    )
                
                migrated += 1
                logger.info(f"✅ Migrated trade: {trade['symbol']}")
            except Exception as e:
                logger.error(f"❌ Error migrating trade: {e}")
                errors.append(str(e))
        
        if errors:
            logger.warning(f"Migration completed with {len(errors)} errors. NOT backing up JSON file.")
            return
        
        logger.info(f"✅ Successfully migrated {migrated} trades without errors")
        db.close()
        
        os.rename('trading_stats.json', 'trading_stats.json.backup')
        logger.info("Backed up trading_stats.json to trading_stats.json.backup")
        
    except Exception as e:
        logger.error(f"Error migrating stats: {e}")

def migrate_indicator_performance():
    if not os.path.exists('indicator_performance_data.json'):
        logger.info("No indicator_performance_data.json file found, skipping...")
        return
    
    try:
        with open('indicator_performance_data.json', 'r') as f:
            data = json.load(f)
        
        if not data or 'signals' not in data:
            logger.info("No indicator data to migrate")
            return
        
        db = DatabaseManager()
        signal_count = 0
        outcome_count = 0
        errors = []
        
        for key, signals in data.get('signals', {}).items():
            try:
                parts = key.split('_')
                symbol = parts[0]
                indicator = parts[1]
                timeframe = parts[2] if len(parts) > 2 else '5m'
                
                for signal in signals:
                    db.save_indicator_signal(
                        symbol=symbol,
                        indicator_name=indicator,
                        timeframe=timeframe,
                        is_bullish=signal.get('is_bullish', True),
                        price=signal.get('price', 0),
                        signal_time=datetime.fromtimestamp(signal['timestamp'])
                    )
                    signal_count += 1
            except Exception as e:
                logger.error(f"Error migrating signal {key}: {e}")
                errors.append(str(e))
        
        for item in data.get('pending_resolutions', []):
            try:
                db.save_indicator_signal(
                    symbol=item['symbol'],
                    indicator_name=item['indicator'],
                    timeframe=item['timeframe'],
                    is_bullish=item.get('was_bullish', True),
                    price=item['price'],
                    signal_time=datetime.fromtimestamp(item['timestamp'])
                )
                signal_count += 1
            except Exception as e:
                logger.error(f"Error migrating pending resolution: {e}")
                errors.append(str(e))
        
        if errors:
            logger.warning(f"Migration completed with {len(errors)} errors. NOT backing up JSON file.")
            return
        
        logger.info(f"✅ Successfully migrated {signal_count} signals and {outcome_count} outcomes without errors")
        db.close()
        
        os.rename('indicator_performance_data.json', 'indicator_performance_data.json.backup')
        logger.info("Backed up indicator_performance_data.json")
        
    except Exception as e:
        logger.error(f"Error migrating indicator performance: {e}")

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("Starting database migration...")
    logger.info("=" * 80)
    
    migrate_positions()
    migrate_stats()
    migrate_indicator_performance()
    
    logger.info("=" * 80)
    logger.info("✅ Migration completed!")
    logger.info("=" * 80)
