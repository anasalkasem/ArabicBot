# Binance Trading Bot

## Overview
This project is an automated cryptocurrency trading bot for the Binance platform. It utilizes an advanced technical analysis strategy to monitor prices automatically and execute buy and sell orders based on signals from multiple technical indicators. The bot aims to adapt to market conditions dynamically and provide comprehensive performance tracking, offering a robust solution for automated trading with an ambitious vision for market potential and continuous improvement.

## User Preferences
- The user prefers to be communicated with using clear, concise language, avoiding jargon where possible.
- The user appreciates detailed explanations when new features or significant changes are introduced, especially regarding the underlying logic.
- The user prefers an iterative development approach, with regular updates on progress and opportunities for feedback.
- The user wants to be asked before major architectural changes or significant modifications to the trading strategy are implemented.
- The user prefers to have control over configuration settings via a centralized file (`config.json`).
- The user values a strong focus on risk management and prefers conservative strategies unless explicitly stated otherwise.
- The user prefers the bot to be optimized for smaller accounts initially, with scalability in mind.

## System Architecture
The bot is structured into several modular Python files, each responsible for a specific aspect of the trading operation:

- **UI/UX Decisions**:
    - Arabic RTL interface with an iPhone 16 design aesthetic.
    - Professional dashboard for real-time analytics, displaying key metrics, open positions, market regime, custom momentum index breakdown, and performance statistics.
    - Dynamic visual indicators for market regime and live/testnet mode.
    - Interactive buttons for dashboard actions (refresh, show/hide logs, export).
    - Responsive design for mobile and tablet devices.

- **Technical Implementations**:
    - **Custom Momentum Index**: A composite index (0-100) based on Technical Analysis (RSI, Stochastic, MACD - 40%), Sentiment Analysis (CoinGecko, VADER NLP - 30%), Volume Analysis (24-hour average comparison - 20%), and Relative Strength (asset vs. BTC - 10%). Generates buy signals below 40 and sell signals above 80.
    - **Market Regime Adaptation**: Automatically identifies market states (Bull/Bear/Sideways) and dynamically adjusts trading parameters (e.g., RSI thresholds, Bollinger Band tolerance, Stop-Loss/Take-Profit multipliers).
    - **Advanced Technical Analysis**: Employs RSI, Stochastic, Bollinger Bands, MACD, EMA (50, 200), and ADX (14) for trend and momentum analysis.
    - **Multi-Timeframe Analysis**: Confirms trends across 5m, 1h, and 4h timeframes.
    - **Dynamic Trailing Stop-Loss**: Automatically protects profits by moving the stop-loss point.
    - **Smart Risk Management**: Adaptive Stop-Loss and Take-Profit based on market conditions, position sizing (5% of balance per trade), and maximum open positions (3).
    - **Dynamic Strategy Weaver**: An adaptive AI system that learns from indicator performance to optimize trading signals. Features:
        - **Signal Tracking**: Logs all indicator readings (RSI, MACD, Stochastic, BB) every 5 seconds for comprehensive data collection
        - **State-Change Gating**: Queues outcome resolution only when indicators flip from bearish → bullish, preventing queue explosion (0-30 entries/hour vs 720/hour)
        - **1-Hour Outcome Resolution**: Automatically evaluates signal quality by comparing price movement 1 hour after each bullish signal
        - **Retry Logic**: Handles API failures gracefully with automatic retry instead of data loss
        - **Dynamic Weighting**: Calculates indicator weights (10-40% range) based on EMA success rates per symbol
        - **Persistent Storage**: Survives bot restarts via JSON persistence (indicator_performance_data.json)
        - **API Endpoint**: /strategy-weights exposes real-time weights and success rates for dashboard integration
        - **Production-Ready**: Queue management, error resilience, and Railway deployment compatible

- **Feature Specifications**:
    - **Trading Strategy**:
        - **Buy Signals**: RSI < 50, Stochastic < 65, price within 1.5% of lower Bollinger Band, and multi-timeframe confirmation (allows one bearish timeframe).
        - **Sell Signals**: RSI > 70, profit >= 5%, MACD bearish crossover, or Trailing Stop activation (at 3% profit, protecting 2% from peak).
    - **Configurability**: All settings are easily adjustable via `config.json`, including trading pairs, testnet mode, risk management parameters, multi-timeframe settings, indicator parameters, and trading frequency.
    - **Logging & Statistics**: Comprehensive logging, performance tracking (Win Rate, Average Profit, Best/Worst Trade), and daily/per-pair statistics stored in `trading_stats.json`.
    - **Testnet Mode**: Allows strategy testing without financial risk.

- **System Design Choices**:
    - Python 3.12 environment.
    - Modular design for easy maintenance and extension.
    - **PostgreSQL Database**: Replaces JSON files for persistent storage with:
        - `trades` table: Complete trade history with entry/exit prices, P/L, and metadata
        - `positions` table: Current open positions with real-time tracking
        - `indicator_signals` & `indicator_outcomes` tables: Strategy Weaver data for ML learning
        - `daily_stats` & `pair_stats` tables: Performance analytics per day and per symbol
        - `market_regime_history` table: Historical market state transitions
    - Hybrid storage: Database-first with JSON fallback for reliability
    - Robust error handling with graceful degradation.

## External Dependencies
- **Binance API**: For real-time market data and trade execution (supports both mainnet and testnet).
- **Telegram API**: For instant notifications on trades and critical events.
- **Telegram Bot API**: Full control panel via Telegram with interactive commands and buttons (see `TELEGRAM_SETUP.md`).
- **CoinGecko API**: Utilized for sentiment analysis data in the Custom Momentum Index.
- **VADER Sentiment Analysis**: A lexicon and rule-based sentiment analysis tool (integrated via `sentiment_analyzer.py`).
- **Python Libraries**: `numpy`, `pandas`, `pandas-ta`, `python-binance`, `python-telegram-bot`, `requests`.

## Recent Updates (November 2025)
- **SELL ALL BUTTON (Nov 15, 2025)**: Added "Sell All" button to dashboard for quick liquidation of all open positions. Features: (1) Confirmation dialog before execution, (2) Batch processing with individual order validation, (3) Detailed success/failure reporting per symbol, (4) Proper order status checking (FILLED/REJECTED/PARTIALLY_FILLED), (5) Database sync after successful sells, (6) Real-time UI feedback with loading state, (7) Automatic dashboard refresh after completion. Endpoint: `/sell-all` (POST). Button located in open positions section with red danger styling.
- **DASHBOARD DATA ENRICHMENT (Nov 15, 2025)**: Enhanced `/status` endpoint to send enriched position data including: (1) Current price fetched from Binance, (2) Real-time profit/loss percentage calculation, (3) Actual Stop-Loss and Take-Profit prices (not percentages), (4) Symbol name properly included. This fixed dashboard display issues where symbol showed "undefined", profit was always 0.00%, and stop-loss/take-profit displayed as $0.00.
- **SELL ORDER VALIDATION FIX (Nov 15, 2025)**: Fixed critical bug where bot would mark positions as closed even if the sell order failed on Binance. Added order status validation in `binance_client.py` to verify orders are FILLED before closing positions. Now checks: (1) Order status = 'FILLED' before proceeding, (2) Logs warning for PARTIALLY_FILLED orders, (3) Rejects FAILED/REJECTED orders and keeps position open. This prevents "ghost position" bugs where trades disappear from dashboard but remain open on Binance exchange.
- **LOGGER DUPLICATION FIX (Nov 15, 2025)**: Fixed critical issue where every log message was appearing twice due to Python logger propagation. Added `logger.propagate = False` to `logger_setup.py` to prevent messages from being sent to parent logger. This fixed: (1) Duplicate log entries in both Replit and Railway, (2) Telegram 409 Conflict errors caused by apparent "dual execution", (3) Improved log readability and reduced confusion. All logs now appear exactly once with clean, consistent output.
- **CRITICAL DEPLOYMENT FIX (Nov 15, 2025)**: Fixed Railway deployment with 3 critical issues: (1) **Database Connection** - Modified `db_manager.py` to use `DATABASE_URL` from Railway (connection string) instead of separate PGHOST/PGPORT variables, (2) **Port Conflict** - Simplified `railway.json` to run `python main.py` only (removed Gunicorn to prevent Flask server conflict), (3) **Multiple Instances** - Enforced `numReplicas: 1` to prevent Telegram API conflicts (409 errors). Solution is production-ready and works on both Railway (DATABASE_URL) and Replit (fallback to separate credentials). See `DEPLOYMENT_STEPS_FINAL.md` for complete deployment guide.
- **Real-Time Account Sync (Nov 15, 2025)**: Added intelligent position synchronization with Binance account. The bot now automatically detects and closes "ghost positions" (trades sold manually on Binance but still showing as open in the bot). Features: (1) Runs every iteration, (2) Uses official symbol metadata via `get_symbol_info()` for accurate asset parsing, (3) Gracefully handles geo-restrictions with one-time warning, (4) Properly updates both database and in-memory positions, (5) Prevents data inconsistency and ensures accurate P/L tracking.
- **AI Integration - OpenAI GPT-4 (Nov 15, 2025)**: Added 3 powerful AI features: (1) AI Market Analyzer - intelligent market analysis with recommendations and risk assessment, (2) Telegram AI Commands - `/analyze` and `/audit` commands for instant AI insights, (3) AI Chat Assistant - 24/7 intelligent chatbot via Telegram. Uses GPT-4o-mini for fast, accurate analysis. See `AI_FEATURES.md` for complete documentation.
- **Telegram Control Panel**: Added comprehensive Telegram bot controller with 8 commands (`/start`, `/status`, `/stats`, `/balance`, `/positions`, `/regime`, `/logs`, `/help`) and interactive keyboard buttons for full bot management via mobile.
- **PostgreSQL Integration**: Migrated from JSON to PostgreSQL database for better performance, scalability, and complex analytics.
- **Dynamic Strategy Weaver - FULL ACTIVATION (Nov 15, 2025)**: The system now **actively uses** calculated indicator weights to make buy decisions! When confidence ≥50%, the bot buys immediately (bypassing static strategy). When confidence <50%, falls back to proven RSI+Stoch+BB strategy. This allows the bot to learn which indicators work best per symbol and adapt over time. See `DYNAMIC_STRATEGY_WEAVER.md` for full details.
- **CRITICAL FIX (Nov 15, 2025)**: Fixed severe logic error in Custom Momentum Index where the bot was mixing data between different trading pairs. Added `symbol_momentum_cache` for complete data isolation, triple-level validation, and enhanced logging with symbol names. See `LOGIC_ERROR_FIX.md` for details.
- **MOMENTUM OPTIMIZATION (Nov 15, 2025)**: Relaxed Custom Momentum buy threshold from 40 to 45, and added "Strong Momentum Override" feature that allows buying even during bearish trends when momentum index < 35. This makes the bot more dynamic and capable of catching bottom opportunities. See `MOMENTUM_OPTIMIZATION.md` for details.