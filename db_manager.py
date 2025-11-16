import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger('db_manager')

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
        self.apply_migrations()
    
    def connect(self):
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(database_url)
                logger.info("✅ Connected to PostgreSQL database (via DATABASE_URL)")
            else:
                self.connection = psycopg2.connect(
                    host=os.getenv('PGHOST'),
                    port=os.getenv('PGPORT'),
                    user=os.getenv('PGUSER'),
                    password=os.getenv('PGPASSWORD'),
                    database=os.getenv('PGDATABASE')
                )
                logger.info("✅ Connected to PostgreSQL database (via separate credentials)")
            self.connection.autocommit = False
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def create_tables(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        side VARCHAR(10) NOT NULL,
                        entry_price DECIMAL(20, 8) NOT NULL,
                        exit_price DECIMAL(20, 8),
                        quantity DECIMAL(20, 8) NOT NULL,
                        entry_time TIMESTAMP NOT NULL,
                        exit_time TIMESTAMP,
                        profit_loss DECIMAL(20, 8),
                        profit_loss_percent DECIMAL(10, 4),
                        stop_loss DECIMAL(20, 8),
                        take_profit DECIMAL(20, 8),
                        trailing_stop_price DECIMAL(20, 8),
                        highest_price DECIMAL(20, 8),
                        market_regime VARCHAR(20),
                        buy_signals TEXT,
                        sell_reason VARCHAR(100),
                        status VARCHAR(20) DEFAULT 'open',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
                    CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
                    CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS positions (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL UNIQUE,
                        entry_price DECIMAL(20, 8) NOT NULL,
                        quantity DECIMAL(20, 8) NOT NULL,
                        entry_time TIMESTAMP NOT NULL,
                        stop_loss DECIMAL(20, 8),
                        take_profit DECIMAL(20, 8),
                        trailing_stop_price DECIMAL(20, 8),
                        highest_price DECIMAL(20, 8),
                        market_regime VARCHAR(20),
                        buy_signals TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS indicator_signals (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        indicator_name VARCHAR(50) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        is_bullish BOOLEAN NOT NULL,
                        price DECIMAL(20, 8) NOT NULL,
                        signal_time TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_signals_symbol ON indicator_signals(symbol);
                    CREATE INDEX IF NOT EXISTS idx_signals_indicator ON indicator_signals(indicator_name);
                    CREATE INDEX IF NOT EXISTS idx_signals_time ON indicator_signals(signal_time);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS indicator_outcomes (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        indicator_name VARCHAR(50) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        signal_price DECIMAL(20, 8) NOT NULL,
                        outcome_price DECIMAL(20, 8) NOT NULL,
                        price_change_percent DECIMAL(10, 4) NOT NULL,
                        was_successful BOOLEAN NOT NULL,
                        signal_time TIMESTAMP NOT NULL,
                        outcome_time TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_outcomes_symbol ON indicator_outcomes(symbol);
                    CREATE INDEX IF NOT EXISTS idx_outcomes_indicator ON indicator_outcomes(indicator_name);
                    CREATE INDEX IF NOT EXISTS idx_outcomes_time ON indicator_outcomes(signal_time);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        id SERIAL PRIMARY KEY,
                        date DATE NOT NULL UNIQUE,
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_profit_loss DECIMAL(20, 8) DEFAULT 0,
                        win_rate DECIMAL(10, 4) DEFAULT 0,
                        average_profit DECIMAL(10, 4) DEFAULT 0,
                        best_trade DECIMAL(10, 4) DEFAULT 0,
                        worst_trade DECIMAL(10, 4) DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pair_stats (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        date DATE NOT NULL,
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_profit_loss DECIMAL(20, 8) DEFAULT 0,
                        win_rate DECIMAL(10, 4) DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, date)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_pair_stats_symbol ON pair_stats(symbol);
                    CREATE INDEX IF NOT EXISTS idx_pair_stats_date ON pair_stats(date);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_regime_history (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        regime VARCHAR(20) NOT NULL,
                        price DECIMAL(20, 8) NOT NULL,
                        recorded_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_regime_symbol ON market_regime_history(symbol);
                    CREATE INDEX IF NOT EXISTS idx_regime_time ON market_regime_history(recorded_at);
                """)
                
                self.connection.commit()
                logger.info("✅ Database tables created successfully")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Error creating tables: {e}")
            raise
    
    def apply_migrations(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE positions 
                    ADD COLUMN IF NOT EXISTS position_type VARCHAR(10) DEFAULT 'SPOT',
                    ADD COLUMN IF NOT EXISTS leverage INTEGER DEFAULT 1,
                    ADD COLUMN IF NOT EXISTS liquidation_price DECIMAL(20, 8),
                    ADD COLUMN IF NOT EXISTS unrealized_pnl DECIMAL(20, 8),
                    ADD COLUMN IF NOT EXISTS funding_rate DECIMAL(10, 8),
                    ADD COLUMN IF NOT EXISTS is_futures BOOLEAN DEFAULT FALSE;
                """)
                
                cursor.execute("""
                    ALTER TABLE trades
                    ADD COLUMN IF NOT EXISTS position_type VARCHAR(10) DEFAULT 'SPOT',
                    ADD COLUMN IF NOT EXISTS leverage INTEGER DEFAULT 1,
                    ADD COLUMN IF NOT EXISTS liquidation_price DECIMAL(20, 8),
                    ADD COLUMN IF NOT EXISTS funding_paid DECIMAL(20, 8),
                    ADD COLUMN IF NOT EXISTS is_futures BOOLEAN DEFAULT FALSE;
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_type ON positions(position_type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_type ON trades(position_type);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_futures ON positions(is_futures);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_futures ON trades(is_futures);")
                
                cursor.execute("UPDATE positions SET position_type = 'SPOT', leverage = 1, is_futures = FALSE WHERE position_type IS NULL;")
                cursor.execute("UPDATE trades SET position_type = 'SPOT', leverage = 1, is_futures = FALSE WHERE position_type IS NULL;")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS worker_bots (
                        bot_id INTEGER PRIMARY KEY,
                        strategy_type VARCHAR(50) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        balance DECIMAL(20, 8) DEFAULT 1000.0,
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_profit DECIMAL(20, 8) DEFAULT 0.0,
                        win_rate DECIMAL(10, 4) DEFAULT 0.0,
                        roi DECIMAL(10, 4) DEFAULT 0.0,
                        last_24h_profit DECIMAL(20, 8) DEFAULT 0.0,
                        last_7d_profit DECIMAL(20, 8) DEFAULT 0.0,
                        vote_weight DECIMAL(10, 4) DEFAULT 1.0,
                        config JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_worker_bots_strategy ON worker_bots(strategy_type);
                    CREATE INDEX IF NOT EXISTS idx_worker_bots_roi ON worker_bots(roi DESC);
                    CREATE INDEX IF NOT EXISTS idx_worker_bots_24h_profit ON worker_bots(last_24h_profit DESC);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS swarm_paper_trades (
                        id SERIAL PRIMARY KEY,
                        trade_id VARCHAR(100) UNIQUE NOT NULL,
                        bot_id INTEGER NOT NULL,
                        symbol VARCHAR(20) NOT NULL,
                        side VARCHAR(10) NOT NULL,
                        entry_price DECIMAL(20, 8) NOT NULL,
                        exit_price DECIMAL(20, 8),
                        quantity DECIMAL(20, 8) NOT NULL,
                        entry_time TIMESTAMP NOT NULL,
                        exit_time TIMESTAMP,
                        profit_loss DECIMAL(20, 8),
                        profit_pct DECIMAL(10, 4),
                        status VARCHAR(20) DEFAULT 'open',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_swarm_trades_bot ON swarm_paper_trades(bot_id);
                    CREATE INDEX IF NOT EXISTS idx_swarm_trades_symbol ON swarm_paper_trades(symbol);
                    CREATE INDEX IF NOT EXISTS idx_swarm_trades_status ON swarm_paper_trades(status);
                    CREATE INDEX IF NOT EXISTS idx_swarm_trades_entry_time ON swarm_paper_trades(entry_time);
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS swarm_votes (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        total_bots INTEGER NOT NULL,
                        buy_votes INTEGER DEFAULT 0,
                        sell_votes INTEGER DEFAULT 0,
                        hold_votes INTEGER DEFAULT 0,
                        buy_weight DECIMAL(10, 4) DEFAULT 0.0,
                        sell_weight DECIMAL(10, 4) DEFAULT 0.0,
                        hold_weight DECIMAL(10, 4) DEFAULT 0.0,
                        final_decision VARCHAR(10) NOT NULL,
                        confidence DECIMAL(10, 4) DEFAULT 0.0,
                        top_performers JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_swarm_votes_symbol ON swarm_votes(symbol);
                    CREATE INDEX IF NOT EXISTS idx_swarm_votes_timestamp ON swarm_votes(timestamp DESC);
                    CREATE INDEX IF NOT EXISTS idx_swarm_votes_decision ON swarm_votes(final_decision);
                """)
                
                self.connection.commit()
                logger.info("✅ Database migrations applied successfully (Futures + Swarm Intelligence support added)")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"⚠️ Error applying migrations: {e}")
            logger.info("Database will continue with existing schema")
    
    def save_position(self, symbol, entry_price, quantity, entry_time, stop_loss, take_profit, 
                     trailing_stop_price, highest_price, market_regime, buy_signals,
                     position_type='SPOT', leverage=1, liquidation_price=None, unrealized_pnl=None, funding_rate=None):
        try:
            with self.connection.cursor() as cursor:
                is_futures = position_type in ['LONG', 'SHORT']
                cursor.execute("""
                    INSERT INTO positions (symbol, entry_price, quantity, entry_time, stop_loss, 
                                         take_profit, trailing_stop_price, highest_price, 
                                         market_regime, buy_signals, position_type, leverage,
                                         liquidation_price, unrealized_pnl, funding_rate, is_futures, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (symbol) DO UPDATE SET
                        entry_price = EXCLUDED.entry_price,
                        quantity = EXCLUDED.quantity,
                        stop_loss = EXCLUDED.stop_loss,
                        take_profit = EXCLUDED.take_profit,
                        trailing_stop_price = EXCLUDED.trailing_stop_price,
                        highest_price = EXCLUDED.highest_price,
                        position_type = EXCLUDED.position_type,
                        leverage = EXCLUDED.leverage,
                        liquidation_price = EXCLUDED.liquidation_price,
                        unrealized_pnl = EXCLUDED.unrealized_pnl,
                        funding_rate = EXCLUDED.funding_rate,
                        is_futures = EXCLUDED.is_futures,
                        updated_at = CURRENT_TIMESTAMP
                """, (symbol, entry_price, quantity, entry_time, stop_loss, take_profit,
                     trailing_stop_price, highest_price, market_regime, 
                     json.dumps(buy_signals) if buy_signals else None,
                     position_type, leverage, liquidation_price, unrealized_pnl, funding_rate, is_futures))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving position: {e}")
            raise
    
    def get_positions(self):
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM positions")
                positions = cursor.fetchall()
                result = {}
                for pos in positions:
                    result[pos['symbol']] = {
                        'entry_price': float(pos['entry_price']),
                        'quantity': float(pos['quantity']),
                        'entry_time': pos['entry_time'].isoformat(),
                        'stop_loss': float(pos['stop_loss']) if pos['stop_loss'] else None,
                        'take_profit': float(pos['take_profit']) if pos['take_profit'] else None,
                        'trailing_stop_price': float(pos['trailing_stop_price']) if pos['trailing_stop_price'] else None,
                        'highest_price': float(pos['highest_price']) if pos['highest_price'] else None,
                        'market_regime': pos['market_regime'],
                        'buy_signals': json.loads(pos['buy_signals']) if pos['buy_signals'] else []
                    }
                return result
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    def delete_position(self, symbol):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM positions WHERE symbol = %s", (symbol,))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error deleting position: {e}")
            raise
    
    def update_position(self, symbol, **kwargs):
        try:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = %s")
                values.append(value)
            
            if not set_clauses:
                return
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(symbol)
            
            query = f"UPDATE positions SET {', '.join(set_clauses)} WHERE symbol = %s"
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, values)
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error updating position: {e}")
            raise
    
    def save_trade(self, symbol, side, entry_price, quantity, entry_time, stop_loss, take_profit,
                   market_regime=None, buy_signals=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trades (symbol, side, entry_price, quantity, entry_time, 
                                      stop_loss, take_profit, market_regime, buy_signals)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (symbol, side, entry_price, quantity, entry_time, stop_loss, take_profit,
                     market_regime, json.dumps(buy_signals) if buy_signals else None))
                trade_id = cursor.fetchone()[0]
                self.connection.commit()
                return trade_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving trade: {e}")
            raise
    
    def close_trade(self, symbol, exit_price, exit_time, profit_loss, profit_loss_percent, sell_reason):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE trades SET 
                        exit_price = %s,
                        exit_time = %s,
                        profit_loss = %s,
                        profit_loss_percent = %s,
                        sell_reason = %s,
                        status = 'closed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s AND status = 'open'
                """, (exit_price, exit_time, profit_loss, profit_loss_percent, sell_reason, symbol))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error closing trade: {e}")
            raise
    
    def save_indicator_signal(self, symbol, indicator_name, timeframe, is_bullish, price, signal_time):
        try:
            is_bullish_native = bool(is_bullish) if hasattr(is_bullish, 'item') else bool(is_bullish)
            price_native = float(price) if hasattr(price, 'item') else float(price)
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO indicator_signals (symbol, indicator_name, timeframe, is_bullish, price, signal_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (symbol, indicator_name, timeframe, is_bullish_native, price_native, signal_time))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving indicator signal: {e}")
    
    def save_indicator_outcome(self, symbol, indicator_name, timeframe, signal_price, outcome_price,
                              price_change_percent, was_successful, signal_time, outcome_time):
        try:
            signal_price_native = float(signal_price) if hasattr(signal_price, 'item') else float(signal_price)
            outcome_price_native = float(outcome_price) if hasattr(outcome_price, 'item') else float(outcome_price)
            price_change_native = float(price_change_percent) if hasattr(price_change_percent, 'item') else float(price_change_percent)
            was_successful_native = bool(was_successful) if hasattr(was_successful, 'item') else bool(was_successful)
            
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO indicator_outcomes (symbol, indicator_name, timeframe, signal_price,
                                                   outcome_price, price_change_percent, was_successful,
                                                   signal_time, outcome_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (symbol, indicator_name, timeframe, signal_price_native, outcome_price_native, 
                     price_change_native, was_successful_native, signal_time, outcome_time))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving indicator outcome: {e}")
    
    def get_indicator_statistics(self, symbol=None, indicator_name=None, days=30):
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        symbol,
                        indicator_name,
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN was_successful THEN 1 ELSE 0 END) as successful_signals,
                        AVG(price_change_percent) as avg_price_change,
                        AVG(CASE WHEN was_successful THEN price_change_percent END) as avg_win,
                        AVG(CASE WHEN NOT was_successful THEN price_change_percent END) as avg_loss
                    FROM indicator_outcomes
                    WHERE signal_time >= CURRENT_DATE - INTERVAL '%s days'
                """
                params = [days]
                
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol)
                
                if indicator_name:
                    query += " AND indicator_name = %s"
                    params.append(indicator_name)
                
                query += " GROUP BY symbol, indicator_name"
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting indicator statistics: {e}")
            return []
    
    def get_trading_statistics(self, days=None):
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(profit_loss) as total_profit_loss,
                        AVG(profit_loss_percent) as avg_profit_percent,
                        MAX(profit_loss_percent) as best_trade,
                        MIN(profit_loss_percent) as worst_trade
                    FROM trades
                    WHERE status = 'closed'
                """
                
                if days:
                    query += " AND exit_time >= CURRENT_DATE - INTERVAL '%s days'"
                    cursor.execute(query, [days])
                else:
                    cursor.execute(query)
                
                result = cursor.fetchone()
                
                if not result or result.get('total_trades') == 0 or result.get('total_trades') is None:
                    return {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_profit_loss': 0.0,
                        'avg_profit_percent': 0.0,
                        'best_trade': 0.0,
                        'worst_trade': 0.0
                    }
                
                return result
        except Exception as e:
            logger.error(f"Error getting trading statistics: {e}")
            return None
    
    def get_pair_statistics(self, symbol, days=None):
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(profit_loss) as total_profit_loss,
                        AVG(profit_loss_percent) as avg_profit_percent
                    FROM trades
                    WHERE symbol = %s AND status = 'closed'
                """
                params = [symbol]
                
                if days:
                    query += " AND exit_time >= CURRENT_DATE - INTERVAL '%s days'"
                    params.append(days)
                
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting pair statistics: {e}")
            return None
    
    def save_market_regime(self, symbol, regime, price, recorded_at):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO market_regime_history (symbol, regime, price, recorded_at)
                    VALUES (%s, %s, %s, %s)
                """, (symbol, regime, price, recorded_at))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving market regime: {e}")
    
    def save_worker_bot(self, bot_id, strategy_type, timeframe, balance, performance, config):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO worker_bots (bot_id, strategy_type, timeframe, balance,
                                           total_trades, winning_trades, losing_trades,
                                           total_profit, win_rate, roi, last_24h_profit,
                                           last_7d_profit, vote_weight, config, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (bot_id) DO UPDATE SET
                        balance = EXCLUDED.balance,
                        total_trades = EXCLUDED.total_trades,
                        winning_trades = EXCLUDED.winning_trades,
                        losing_trades = EXCLUDED.losing_trades,
                        total_profit = EXCLUDED.total_profit,
                        win_rate = EXCLUDED.win_rate,
                        roi = EXCLUDED.roi,
                        last_24h_profit = EXCLUDED.last_24h_profit,
                        last_7d_profit = EXCLUDED.last_7d_profit,
                        vote_weight = EXCLUDED.vote_weight,
                        updated_at = CURRENT_TIMESTAMP
                """, (bot_id, strategy_type, timeframe, balance,
                     performance.total_trades, performance.winning_trades, performance.losing_trades,
                     performance.total_profit, performance.win_rate, performance.roi,
                     performance.last_24h_profit, performance.last_7d_profit, performance.vote_weight,
                     json.dumps(config)))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving worker bot: {e}")
    
    def save_swarm_paper_trade(self, trade):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO swarm_paper_trades (trade_id, bot_id, symbol, side, entry_price,
                                                   exit_price, quantity, entry_time, exit_time,
                                                   profit_loss, profit_pct, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_id) DO UPDATE SET
                        exit_price = EXCLUDED.exit_price,
                        exit_time = EXCLUDED.exit_time,
                        profit_loss = EXCLUDED.profit_loss,
                        profit_pct = EXCLUDED.profit_pct,
                        status = EXCLUDED.status
                """, (trade.trade_id, trade.bot_id, trade.symbol, trade.side, trade.entry_price,
                     trade.exit_price, trade.quantity, trade.entry_time, trade.exit_time,
                     trade.profit_loss, trade.profit_pct, trade.status))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving swarm paper trade: {e}")
    
    def save_swarm_vote(self, vote):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO swarm_votes (symbol, timestamp, total_bots, buy_votes, sell_votes,
                                           hold_votes, buy_weight, sell_weight, hold_weight,
                                           final_decision, confidence, top_performers)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (vote.symbol, vote.timestamp, vote.total_bots, vote.buy_votes, vote.sell_votes,
                     vote.hold_votes, vote.buy_weight, vote.sell_weight, vote.hold_weight,
                     vote.final_decision, vote.confidence, json.dumps(vote.top_performers)))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving swarm vote: {e}")
    
    def get_swarm_stats(self):
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_bots,
                        SUM(total_profit) as total_profit,
                        AVG(balance) as avg_balance,
                        SUM(CASE WHEN total_profit > 0 THEN 1 ELSE 0 END) as profitable_bots,
                        MAX(roi) as best_roi,
                        MIN(roi) as worst_roi
                    FROM worker_bots
                """)
                stats = cursor.fetchone()
                
                cursor.execute("""
                    SELECT bot_id, strategy_type, roi, last_24h_profit, win_rate, vote_weight
                    FROM worker_bots
                    ORDER BY last_24h_profit DESC
                    LIMIT 10
                """)
                top_10 = cursor.fetchall()
                
                return {
                    'stats': dict(stats) if stats else {},
                    'top_10': [dict(row) for row in top_10]
                }
        except Exception as e:
            logger.error(f"Error getting swarm stats: {e}")
            return {'stats': {}, 'top_10': []}
    
    def get_recent_swarm_votes(self, limit=10):
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM swarm_votes
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting swarm votes: {e}")
            return []
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
