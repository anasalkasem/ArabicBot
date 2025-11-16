-- Migration: Add Futures Trading Support
-- Date: 2025-11-16
-- Description: Adds columns for Long/Short positions, leverage, liquidation price, and unrealized P&L

-- Add new columns to positions table
ALTER TABLE positions 
ADD COLUMN IF NOT EXISTS position_type VARCHAR(10) DEFAULT 'SPOT',
ADD COLUMN IF NOT EXISTS leverage INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS liquidation_price DECIMAL(20, 8),
ADD COLUMN IF NOT EXISTS unrealized_pnl DECIMAL(20, 8),
ADD COLUMN IF NOT EXISTS funding_rate DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS is_futures BOOLEAN DEFAULT FALSE;

-- Add new columns to trades table
ALTER TABLE trades
ADD COLUMN IF NOT EXISTS position_type VARCHAR(10) DEFAULT 'SPOT',
ADD COLUMN IF NOT EXISTS leverage INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS liquidation_price DECIMAL(20, 8),
ADD COLUMN IF NOT EXISTS funding_paid DECIMAL(20, 8),
ADD COLUMN IF NOT EXISTS is_futures BOOLEAN DEFAULT FALSE;

-- Create index for position_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_positions_type ON positions(position_type);
CREATE INDEX IF NOT EXISTS idx_trades_type ON trades(position_type);
CREATE INDEX IF NOT EXISTS idx_positions_futures ON positions(is_futures);
CREATE INDEX IF NOT EXISTS idx_trades_futures ON trades(is_futures);

-- Update existing records to have default values
UPDATE positions SET position_type = 'SPOT', leverage = 1, is_futures = FALSE WHERE position_type IS NULL;
UPDATE trades SET position_type = 'SPOT', leverage = 1, is_futures = FALSE WHERE position_type IS NULL;
