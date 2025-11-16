# Binance Trading Bot

## Overview
This project is an automated cryptocurrency trading bot for the Binance platform, supporting both Spot and Futures trading (Long & Short). It uses an advanced technical analysis strategy, leveraging multiple indicators to monitor prices and execute trades. The bot dynamically adapts to market conditions, offers comprehensive performance tracking, and includes features like leverage support and liquidation protection to provide a robust solution for automated trading. The project aims to provide a reliable and adaptable tool for cryptocurrency trading, focusing on automation, risk management, and market responsiveness.

## User Preferences
- The user prefers to be communicated with using clear, concise language, avoiding jargon where possible.
- The user appreciates detailed explanations when new features or significant changes are introduced, especially regarding the underlying logic.
- The user prefers an iterative development approach, with regular updates on progress and opportunities for feedback.
- The user wants to be asked before major architectural changes or significant modifications to the trading strategy are implemented.
- The user prefers to have control over configuration settings via a centralized file (`config.json`).
- The user values a strong focus on risk management and prefers conservative strategies unless explicitly stated otherwise.
- The user prefers the bot to be optimized for smaller accounts initially, with scalability in mind.

## System Architecture
The bot features a modular Python architecture designed for maintainability and extensibility.

- **UI/UX Decisions**:
    - Arabic RTL interface with an iPhone 16 design aesthetic.
    - Professional dashboard for real-time analytics, displaying key metrics, open positions, market regime, custom momentum index breakdown, and performance statistics.
    - Dynamic visual indicators for market regime and live/testnet mode.
    - Interactive buttons for dashboard actions (refresh, show/hide logs, export).
    - Responsive design for mobile and tablet devices.

- **Technical Implementations**:
    - **Custom Momentum Index**: A composite index (0-100) based on Technical Analysis (RSI, Stochastic, MACD - 40%), Sentiment Analysis (CoinGecko, VADER NLP - 30%), Volume Analysis (24-hour average comparison - 20%), and Relative Strength (asset vs. BTC - 10%). Generates buy signals below 40 and sell signals above 80.
    - **Market Regime Adaptation**: Automatically identifies market states (Bull/Bear/Sideways) and dynamically adjusts trading parameters.
    - **Advanced Technical Analysis**: Employs RSI, Stochastic, Bollinger Bands, MACD, EMA (50, 200), and ADX (14) for trend and momentum analysis across multiple timeframes (5m, 1h, 4h).
    - **Dynamic Trailing Stop-Loss**: Automatically protects profits by moving the stop-loss point.
    - **Smart Risk Management**: Adaptive Stop-Loss and Take-Profit based on market conditions, position sizing (5% of balance per trade), and maximum open positions (3).
    - **Dynamic Strategy Weaver**: An adaptive AI system that learns from indicator performance to optimize trading signals through signal tracking, 1-hour outcome resolution, retry logic, dynamic weighting, and persistent storage.

- **Feature Specifications**:
    - **Trading Strategy**:
        - **Buy Signals**: RSI < 50, Stochastic < 65, price within 1.5% of lower Bollinger Band, and multi-timeframe confirmation (allows one bearish timeframe).
        - **Sell Signals**: RSI > 70, profit >= 5%, MACD bearish crossover, or Trailing Stop activation (at 3% profit, protecting 2% from peak).
    - **Configurability**: All settings are adjustable via `config.json`, including trading pairs, testnet mode, risk management, multi-timeframe settings, indicator parameters, and trading frequency.
    - **Logging & Statistics**: Comprehensive logging, performance tracking (Win Rate, Average Profit, Best/Worst Trade), and daily/per-pair statistics.
    - **Testnet Mode**: Allows strategy testing without financial risk.
    - **Futures Trading**: Full support for Long and Short positions with leverage management and liquidation price tracking.

- **System Design Choices**:
    - Python 3.12 environment.
    - Modular design for easy maintenance and extension.
    - **PostgreSQL Database**: Used for persistent storage, replacing JSON files. Includes tables for trades, positions, indicator signals/outcomes, daily/pair statistics, and market regime history.
    - Hybrid storage: Database-first with JSON fallback for reliability.
    - Robust error handling with graceful degradation.

## External Dependencies
- **Binance API**: For real-time market data and trade execution (mainnet and testnet).
- **Telegram API**: For instant notifications on trades and critical events, and a full control panel with interactive commands.
- **CoinGecko API**: Utilized for sentiment analysis data in the Custom Momentum Index.
- **VADER Sentiment Analysis**: A lexicon and rule-based sentiment analysis tool.
- **OpenAI GPT-4**: Integrated for AI Market Analyzer, Telegram AI Commands (`/analyze`, `/audit`), and an AI Chat Assistant.
- **Python Libraries**: `numpy`, `pandas`, `pandas-ta`, `python-binance`, `python-telegram-bot`, `requests`.