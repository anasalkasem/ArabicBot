"""
🐝 Bot Swarm Intelligence System
نظام سرب البوتات - ذكاء جماعي متقدم

يدير 50 بوت عامل، كل واحد بإستراتيجية مختلفة، يتداولون افتراضياً
ويصوتون جماعياً على القرارات الحقيقية بناءً على أدائهم.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('swarm_intelligence')


class StrategyType(Enum):
    """أنواع الاستراتيجيات المتاحة"""
    RSI_ONLY = "rsi_only"
    MACD_ONLY = "macd_only"
    STOCH_ONLY = "stochastic_only"
    BB_ONLY = "bollinger_bands_only"
    EMA_CROSS = "ema_crossover"
    VOLUME_SPIKE = "volume_spike"
    RSI_STOCH = "rsi_stochastic_combo"
    MACD_BB = "macd_bollinger_combo"
    TRIPLE_EMA = "triple_ema"
    MOMENTUM = "momentum_based"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout_strategy"
    TREND_FOLLOW = "trend_following"
    VOLATILITY = "volatility_based"
    MULTI_INDICATOR = "multi_indicator"


@dataclass
class WorkerBotConfig:
    """إعدادات البوت العامل"""
    bot_id: int
    strategy_type: StrategyType
    timeframe: str = "5m"
    
    rsi_period: int = 14
    rsi_buy_threshold: int = 30
    rsi_sell_threshold: int = 70
    
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    stoch_k: int = 14
    stoch_d: int = 3
    stoch_buy: int = 20
    stoch_sell: int = 80
    
    bb_period: int = 20
    bb_std: float = 2.0
    
    ema_fast: int = 9
    ema_medium: int = 21
    ema_slow: int = 50
    
    volume_threshold: float = 1.5
    initial_balance: float = 1000.0


@dataclass
class PaperTrade:
    """صفقة افتراضية"""
    trade_id: str
    bot_id: int
    symbol: str
    side: str
    entry_price: float
    quantity: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    profit_loss: float = 0.0
    profit_pct: float = 0.0
    status: str = "open"


@dataclass
class WorkerBotPerformance:
    """أداء البوت العامل"""
    bot_id: int
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    current_balance: float = 1000.0
    roi: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    last_24h_profit: float = 0.0
    last_7d_profit: float = 0.0
    vote_weight: float = 1.0


class WorkerBot:
    """
    🤖 بوت عامل - يطبق استراتيجية واحدة بسيطة
    """
    
    def __init__(self, config: WorkerBotConfig):
        self.config = config
        self.bot_id = config.bot_id
        self.strategy_type = config.strategy_type
        self.balance = config.initial_balance
        self.positions: Dict[str, PaperTrade] = {}
        self.closed_trades: List[PaperTrade] = []
        self.performance = WorkerBotPerformance(bot_id=config.bot_id)
        
        logger.info(f"🤖 Worker Bot #{self.bot_id} initialized with {self.strategy_type.value}")
    
    def analyze(self, symbol: str, market_data: Dict) -> Optional[str]:
        """
        تحليل السوق وإصدار قرار: BUY, SELL, أو None
        """
        try:
            if self.strategy_type == StrategyType.RSI_ONLY:
                return self._analyze_rsi_only(market_data)
            
            elif self.strategy_type == StrategyType.MACD_ONLY:
                return self._analyze_macd_only(market_data)
            
            elif self.strategy_type == StrategyType.STOCH_ONLY:
                return self._analyze_stoch_only(market_data)
            
            elif self.strategy_type == StrategyType.BB_ONLY:
                return self._analyze_bb_only(market_data)
            
            elif self.strategy_type == StrategyType.EMA_CROSS:
                return self._analyze_ema_cross(market_data)
            
            elif self.strategy_type == StrategyType.VOLUME_SPIKE:
                return self._analyze_volume_spike(market_data)
            
            elif self.strategy_type == StrategyType.RSI_STOCH:
                return self._analyze_rsi_stoch_combo(market_data)
            
            elif self.strategy_type == StrategyType.MACD_BB:
                return self._analyze_macd_bb_combo(market_data)
            
            elif self.strategy_type == StrategyType.TRIPLE_EMA:
                return self._analyze_triple_ema(market_data)
            
            elif self.strategy_type == StrategyType.MOMENTUM:
                return self._analyze_momentum(market_data)
            
            elif self.strategy_type == StrategyType.MEAN_REVERSION:
                return self._analyze_mean_reversion(market_data)
            
            elif self.strategy_type == StrategyType.BREAKOUT:
                return self._analyze_breakout(market_data)
            
            elif self.strategy_type == StrategyType.TREND_FOLLOW:
                return self._analyze_trend_following(market_data)
            
            elif self.strategy_type == StrategyType.VOLATILITY:
                return self._analyze_volatility(market_data)
            
            elif self.strategy_type == StrategyType.MULTI_INDICATOR:
                return self._analyze_multi_indicator(market_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Bot #{self.bot_id} analysis error: {e}")
            return None
    
    def _analyze_rsi_only(self, data: Dict) -> Optional[str]:
        """استراتيجية RSI فقط"""
        rsi = data.get('rsi', 50)
        
        if rsi < self.config.rsi_buy_threshold:
            return "BUY"
        elif rsi > self.config.rsi_sell_threshold:
            return "SELL"
        return None
    
    def _analyze_macd_only(self, data: Dict) -> Optional[str]:
        """استراتيجية MACD فقط"""
        macd = data.get('macd', {})
        macd_line = macd.get('macd', 0)
        signal_line = macd.get('signal', 0)
        
        if macd_line > signal_line and macd_line < 0:
            return "BUY"
        elif macd_line < signal_line and macd_line > 0:
            return "SELL"
        return None
    
    def _analyze_stoch_only(self, data: Dict) -> Optional[str]:
        """استراتيجية Stochastic فقط"""
        stoch_k = data.get('stoch_k', 50)
        
        if stoch_k < self.config.stoch_buy:
            return "BUY"
        elif stoch_k > self.config.stoch_sell:
            return "SELL"
        return None
    
    def _analyze_bb_only(self, data: Dict) -> Optional[str]:
        """استراتيجية Bollinger Bands فقط"""
        price = data.get('price', 0)
        bb_lower = data.get('bb_lower', 0)
        bb_upper = data.get('bb_upper', 0)
        
        if price <= bb_lower:
            return "BUY"
        elif price >= bb_upper:
            return "SELL"
        return None
    
    def _analyze_ema_cross(self, data: Dict) -> Optional[str]:
        """استراتيجية تقاطع EMA"""
        ema_fast = data.get('ema_9', 0)
        ema_slow = data.get('ema_21', 0)
        
        if ema_fast > ema_slow:
            return "BUY"
        elif ema_fast < ema_slow:
            return "SELL"
        return None
    
    def _analyze_volume_spike(self, data: Dict) -> Optional[str]:
        """استراتيجية قفزات الحجم"""
        volume_ratio = data.get('volume_ratio', 1.0)
        price_change = data.get('price_change_pct', 0)
        
        if volume_ratio > self.config.volume_threshold and price_change > 0:
            return "BUY"
        elif volume_ratio > self.config.volume_threshold and price_change < -2:
            return "SELL"
        return None
    
    def _analyze_rsi_stoch_combo(self, data: Dict) -> Optional[str]:
        """استراتيجية RSI + Stochastic"""
        rsi = data.get('rsi', 50)
        stoch_k = data.get('stoch_k', 50)
        
        if rsi < 35 and stoch_k < 25:
            return "BUY"
        elif rsi > 65 and stoch_k > 75:
            return "SELL"
        return None
    
    def _analyze_macd_bb_combo(self, data: Dict) -> Optional[str]:
        """استراتيجية MACD + Bollinger Bands"""
        macd = data.get('macd', {})
        price = data.get('price', 0)
        bb_lower = data.get('bb_lower', 0)
        
        macd_line = macd.get('macd', 0)
        signal_line = macd.get('signal', 0)
        
        if macd_line > signal_line and price <= bb_lower * 1.01:
            return "BUY"
        return None
    
    def _analyze_triple_ema(self, data: Dict) -> Optional[str]:
        """استراتيجية ثلاثة EMAs"""
        ema9 = data.get('ema_9', 0)
        ema21 = data.get('ema_21', 0)
        ema50 = data.get('ema_50', 0)
        
        if ema9 > ema21 > ema50:
            return "BUY"
        elif ema9 < ema21 < ema50:
            return "SELL"
        return None
    
    def _analyze_momentum(self, data: Dict) -> Optional[str]:
        """استراتيجية الزخم"""
        roc = data.get('rate_of_change', 0)
        rsi = data.get('rsi', 50)
        
        if roc > 2 and rsi > 45 and rsi < 70:
            return "BUY"
        elif roc < -2 and rsi < 55:
            return "SELL"
        return None
    
    def _analyze_mean_reversion(self, data: Dict) -> Optional[str]:
        """استراتيجية العودة للمتوسط"""
        price = data.get('price', 0)
        sma20 = data.get('sma_20', 0)
        
        deviation = ((price - sma20) / sma20) * 100
        
        if deviation < -3:
            return "BUY"
        elif deviation > 3:
            return "SELL"
        return None
    
    def _analyze_breakout(self, data: Dict) -> Optional[str]:
        """استراتيجية الاختراق"""
        price = data.get('price', 0)
        high_20 = data.get('high_20', 0)
        low_20 = data.get('low_20', 0)
        volume_ratio = data.get('volume_ratio', 1.0)
        
        if price > high_20 and volume_ratio > 1.3:
            return "BUY"
        elif price < low_20 and volume_ratio > 1.3:
            return "SELL"
        return None
    
    def _analyze_trend_following(self, data: Dict) -> Optional[str]:
        """استراتيجية متابعة الاتجاه"""
        adx = data.get('adx', 0)
        ema50 = data.get('ema_50', 0)
        ema200 = data.get('ema_200', 0)
        price = data.get('price', 0)
        
        if adx > 25 and ema50 > ema200 and price > ema50:
            return "BUY"
        elif adx > 25 and ema50 < ema200 and price < ema50:
            return "SELL"
        return None
    
    def _analyze_volatility(self, data: Dict) -> Optional[str]:
        """استراتيجية التذبذب"""
        atr = data.get('atr', 0)
        atr_avg = data.get('atr_avg', 1)
        bb_width = data.get('bb_width', 0)
        
        if atr < atr_avg * 0.7 and bb_width < 0.02:
            return "BUY"
        return None
    
    def _analyze_multi_indicator(self, data: Dict) -> Optional[str]:
        """استراتيجية متعددة المؤشرات"""
        signals = []
        
        signals.append(self._analyze_rsi_only(data))
        signals.append(self._analyze_macd_only(data))
        signals.append(self._analyze_stoch_only(data))
        
        buy_count = signals.count("BUY")
        sell_count = signals.count("SELL")
        
        if buy_count >= 2:
            return "BUY"
        elif sell_count >= 2:
            return "SELL"
        return None
    
    def execute_paper_trade(self, symbol: str, signal: str, price: float) -> Optional[PaperTrade]:
        """
        تنفيذ صفقة افتراضية
        """
        try:
            if signal == "BUY" and symbol not in self.positions:
                quantity = (self.balance * 0.95) / price
                
                trade = PaperTrade(
                    trade_id=f"bot{self.bot_id}_{symbol}_{datetime.now().timestamp()}",
                    bot_id=self.bot_id,
                    symbol=symbol,
                    side="BUY",
                    entry_price=price,
                    quantity=quantity,
                    entry_time=datetime.now()
                )
                
                self.positions[symbol] = trade
                self.balance -= (quantity * price)
                
                logger.debug(f"Bot #{self.bot_id} BUY {symbol} @ ${price:.2f}")
                return trade
                
            elif signal == "SELL" and symbol in self.positions:
                position = self.positions[symbol]
                exit_value = position.quantity * price
                profit = exit_value - (position.quantity * position.entry_price)
                profit_pct = (profit / (position.quantity * position.entry_price)) * 100
                
                position.exit_price = price
                position.exit_time = datetime.now()
                position.profit_loss = profit
                position.profit_pct = profit_pct
                position.status = "closed"
                
                self.balance += exit_value
                self.closed_trades.append(position)
                del self.positions[symbol]
                
                self._update_performance(position)
                
                logger.debug(f"Bot #{self.bot_id} SELL {symbol} @ ${price:.2f} | P/L: ${profit:.2f} ({profit_pct:.2f}%)")
                return position
                
        except Exception as e:
            logger.error(f"Bot #{self.bot_id} trade execution error: {e}")
        
        return None
    
    def _update_performance(self, trade: PaperTrade):
        """تحديث إحصائيات الأداء"""
        perf = self.performance
        perf.total_trades += 1
        
        if trade.profit_loss > 0:
            perf.winning_trades += 1
        else:
            perf.losing_trades += 1
        
        perf.total_profit += trade.profit_loss
        perf.win_rate = (perf.winning_trades / perf.total_trades) * 100 if perf.total_trades > 0 else 0
        perf.avg_profit = perf.total_profit / perf.total_trades if perf.total_trades > 0 else 0
        perf.current_balance = self.balance
        perf.roi = ((self.balance - self.config.initial_balance) / self.config.initial_balance) * 100
        
        recent_24h = [t for t in self.closed_trades if t.exit_time and t.exit_time > datetime.now() - timedelta(hours=24)]
        perf.last_24h_profit = sum(t.profit_loss for t in recent_24h)
        
        recent_7d = [t for t in self.closed_trades if t.exit_time and t.exit_time > datetime.now() - timedelta(days=7)]
        perf.last_7d_profit = sum(t.profit_loss for t in recent_7d)
    
    def get_vote_signal(self, symbol: str, market_data: Dict) -> Optional[str]:
        """
        الحصول على تصويت البوت (BUY/SELL/None)
        """
        return self.analyze(symbol, market_data)
    
    def update_vote_weight(self):
        """
        تحديث وزن التصويت بناءً على الأداء
        """
        perf = self.performance
        
        weight = 1.0
        
        if perf.last_24h_profit > 0:
            weight += min(perf.last_24h_profit / 100, 3.0)
        elif perf.last_24h_profit < 0:
            weight = max(0.1, weight + (perf.last_24h_profit / 100))
        
        if perf.win_rate > 60:
            weight *= 1.2
        elif perf.win_rate < 40:
            weight *= 0.8
        
        if perf.total_trades < 5:
            weight *= 0.5
        
        perf.vote_weight = max(0.1, min(weight, 5.0))
        
        return perf.vote_weight


@dataclass
class SwarmVote:
    """نتيجة تصويت السرب"""
    symbol: str
    timestamp: datetime
    total_bots: int
    buy_votes: int
    sell_votes: int
    hold_votes: int
    buy_weight: float
    sell_weight: float
    hold_weight: float
    final_decision: str
    confidence: float
    top_performers: List[int] = field(default_factory=list)


class SwarmManager:
    """
    🐝 مدير السرب - ينسق بين جميع البوتات العاملة
    """
    
    def __init__(self, num_workers: int = 50):
        self.num_workers = num_workers
        self.workers: List[WorkerBot] = []
        self.vote_history: List[SwarmVote] = []
        
        logger.info(f"🐝 Initializing Swarm with {num_workers} worker bots...")
        self._initialize_swarm()
    
    def _initialize_swarm(self):
        """إنشاء السرب من 50 بوت متنوع"""
        
        strategies = [
            StrategyType.RSI_ONLY,
            StrategyType.MACD_ONLY,
            StrategyType.STOCH_ONLY,
            StrategyType.BB_ONLY,
            StrategyType.EMA_CROSS,
            StrategyType.VOLUME_SPIKE,
            StrategyType.RSI_STOCH,
            StrategyType.MACD_BB,
            StrategyType.TRIPLE_EMA,
            StrategyType.MOMENTUM,
            StrategyType.MEAN_REVERSION,
            StrategyType.BREAKOUT,
            StrategyType.TREND_FOLLOW,
            StrategyType.VOLATILITY,
            StrategyType.MULTI_INDICATOR
        ]
        
        timeframes = ["5m", "15m", "1h", "4h"]
        
        for i in range(self.num_workers):
            strategy = strategies[i % len(strategies)]
            timeframe = timeframes[i % len(timeframes)]
            
            config = WorkerBotConfig(
                bot_id=i + 1,
                strategy_type=strategy,
                timeframe=timeframe,
                rsi_buy_threshold=20 + (i % 5) * 2,
                rsi_sell_threshold=70 + (i % 5) * 2,
                stoch_buy=15 + (i % 4) * 3,
                stoch_sell=75 + (i % 4) * 3,
                bb_std=1.5 + (i % 5) * 0.2,
                volume_threshold=1.2 + (i % 6) * 0.1
            )
            
            worker = WorkerBot(config)
            self.workers.append(worker)
        
        logger.info(f"✅ Swarm initialized with {len(self.workers)} workers")
    
    def conduct_vote(self, symbol: str, market_data: Dict) -> SwarmVote:
        """
        إجراء تصويت جماعي من جميع البوتات
        """
        buy_votes = 0
        sell_votes = 0
        hold_votes = 0
        
        buy_weight = 0.0
        sell_weight = 0.0
        hold_weight = 0.0
        
        for worker in self.workers:
            worker.update_vote_weight()
            
            signal = worker.get_vote_signal(symbol, market_data)
            weight = worker.performance.vote_weight
            
            if signal == "BUY":
                buy_votes += 1
                buy_weight += weight
            elif signal == "SELL":
                sell_votes += 1
                sell_weight += weight
            else:
                hold_votes += 1
                hold_weight += weight
        
        total_weight = buy_weight + sell_weight + hold_weight
        
        if total_weight == 0:
            final_decision = "HOLD"
            confidence = 0.0
        else:
            buy_pct = (buy_weight / total_weight) * 100
            sell_pct = (sell_weight / total_weight) * 100
            hold_pct = (hold_weight / total_weight) * 100
            
            max_pct = max(buy_pct, sell_pct, hold_pct)
            
            if max_pct == buy_pct:
                final_decision = "BUY"
                confidence = buy_pct
            elif max_pct == sell_pct:
                final_decision = "SELL"
                confidence = sell_pct
            else:
                final_decision = "HOLD"
                confidence = hold_pct
        
        top_performers = sorted(
            self.workers,
            key=lambda w: w.performance.last_24h_profit,
            reverse=True
        )[:5]
        
        vote = SwarmVote(
            symbol=symbol,
            timestamp=datetime.now(),
            total_bots=len(self.workers),
            buy_votes=buy_votes,
            sell_votes=sell_votes,
            hold_votes=hold_votes,
            buy_weight=buy_weight,
            sell_weight=sell_weight,
            hold_weight=hold_weight,
            final_decision=final_decision,
            confidence=confidence,
            top_performers=[b.bot_id for b in top_performers]
        )
        
        self.vote_history.append(vote)
        
        logger.info(f"🗳️  Swarm Vote for {symbol}: {final_decision} (confidence: {confidence:.1f}%)")
        logger.info(f"    BUY: {buy_votes} bots ({buy_weight:.1f} weight) | SELL: {sell_votes} bots ({sell_weight:.1f} weight) | HOLD: {hold_votes} bots")
        
        return vote
    
    def run_paper_trading_cycle(self, symbol: str, market_data: Dict):
        """
        دورة تداول افتراضي لجميع البوتات
        """
        price = market_data.get('price', 0)
        
        if price == 0:
            return
        
        for worker in self.workers:
            signal = worker.get_vote_signal(symbol, market_data)
            
            if signal:
                worker.execute_paper_trade(symbol, signal, price)
    
    def get_swarm_stats(self) -> Dict:
        """
        إحصائيات السرب الكاملة
        """
        total_profit = sum(w.performance.total_profit for w in self.workers)
        avg_balance = sum(w.balance for w in self.workers) / len(self.workers)
        
        profitable_bots = len([w for w in self.workers if w.performance.total_profit > 0])
        
        best_bot = max(self.workers, key=lambda w: w.performance.roi)
        worst_bot = min(self.workers, key=lambda w: w.performance.roi)
        
        top_10 = sorted(self.workers, key=lambda w: w.performance.last_24h_profit, reverse=True)[:10]
        
        return {
            'total_workers': len(self.workers),
            'total_profit': total_profit,
            'avg_balance': avg_balance,
            'profitable_bots': profitable_bots,
            'profitability_rate': (profitable_bots / len(self.workers)) * 100,
            'best_bot': {
                'id': best_bot.bot_id,
                'strategy': best_bot.strategy_type.value,
                'roi': best_bot.performance.roi,
                'profit': best_bot.performance.total_profit
            },
            'worst_bot': {
                'id': worst_bot.bot_id,
                'strategy': worst_bot.strategy_type.value,
                'roi': worst_bot.performance.roi,
                'profit': worst_bot.performance.total_profit
            },
            'top_10_performers': [
                {
                    'id': w.bot_id,
                    'strategy': w.strategy_type.value,
                    'profit_24h': w.performance.last_24h_profit,
                    'roi': w.performance.roi,
                    'win_rate': w.performance.win_rate,
                    'vote_weight': w.performance.vote_weight
                }
                for w in top_10
            ]
        }
    
    def get_worker_details(self, bot_id: int) -> Optional[Dict]:
        """
        الحصول على تفاصيل بوت معين
        """
        worker = next((w for w in self.workers if w.bot_id == bot_id), None)
        
        if not worker:
            return None
        
        return {
            'bot_id': worker.bot_id,
            'strategy': worker.strategy_type.value,
            'timeframe': worker.config.timeframe,
            'balance': worker.balance,
            'performance': {
                'total_trades': worker.performance.total_trades,
                'winning_trades': worker.performance.winning_trades,
                'win_rate': worker.performance.win_rate,
                'total_profit': worker.performance.total_profit,
                'roi': worker.performance.roi,
                'last_24h_profit': worker.performance.last_24h_profit,
                'vote_weight': worker.performance.vote_weight
            },
            'open_positions': len(worker.positions),
            'closed_trades': len(worker.closed_trades)
        }
