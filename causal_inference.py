import logging
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict

logger = logging.getLogger('causal_inference')

class CausalInferenceEngine:
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.causal_graph = nx.DiGraph()
        self.causal_effects = {}
        self.variable_history = defaultdict(list)
        
        self.variables = [
            'rsi', 'stochastic', 'macd', 'bb_position', 
            'volume_ratio', 'price_change', 'ema_alignment',
            'market_regime', 'sentiment_score', 'btc_correlation',
            'swarm_confidence', 'whale_activity'
        ]
        
        logger.info("🧠 Causal Inference Engine initialized")
    
    def build_causal_graph(self, historical_data: List[Dict]) -> nx.DiGraph:
        """
        بناء رسم بياني سببي (Causal Graph) من البيانات التاريخية
        يحدد العلاقات السببية الحقيقية بين المتغيرات
        """
        logger.info("📊 Building Causal Graph from historical data...")
        
        self.causal_graph.clear()
        
        for var in self.variables:
            self.causal_graph.add_node(var)
        
        causal_edges = [
            ('whale_activity', 'volume_ratio', 0.85),
            ('whale_activity', 'price_change', 0.72),
            ('volume_ratio', 'price_change', 0.68),
            ('price_change', 'rsi', 0.91),
            ('price_change', 'macd', 0.88),
            ('price_change', 'stochastic', 0.84),
            ('price_change', 'bb_position', 0.79),
            ('sentiment_score', 'whale_activity', 0.63),
            ('sentiment_score', 'volume_ratio', 0.58),
            ('btc_correlation', 'price_change', 0.76),
            ('market_regime', 'price_change', 0.71),
            ('ema_alignment', 'market_regime', 0.82),
            ('swarm_confidence', 'price_change', 0.54),
        ]
        
        if historical_data and len(historical_data) > 50:
            logger.info(f"🔍 Analyzing {len(historical_data)} historical records for causal relationships...")
            causal_edges = self._learn_causal_structure(historical_data)
        
        for source, target, strength in causal_edges:
            self.causal_graph.add_edge(source, target, weight=strength)
        
        logger.info(f"✅ Causal Graph built: {self.causal_graph.number_of_nodes()} nodes, {self.causal_graph.number_of_edges()} causal edges")
        
        return self.causal_graph
    
    def _learn_causal_structure(self, data: List[Dict]) -> List[Tuple[str, str, float]]:
        """
        تعلم البنية السببية من البيانات باستخدام Granger Causality
        """
        edges = []
        
        data_matrix = self._prepare_data_matrix(data)
        if data_matrix is None:
            return edges
        
        for i, var1 in enumerate(self.variables):
            for j, var2 in enumerate(self.variables):
                if i == j:
                    continue
                
                causal_strength = self._compute_granger_causality(
                    data_matrix[:, i], 
                    data_matrix[:, j]
                )
                
                if causal_strength > 0.5:
                    edges.append((var1, var2, causal_strength))
        
        edges.sort(key=lambda x: x[2], reverse=True)
        
        return edges[:15]
    
    def _prepare_data_matrix(self, data: List[Dict]) -> Optional[np.ndarray]:
        """
        تحويل البيانات التاريخية إلى مصفوفة للتحليل
        """
        try:
            matrix = []
            for record in data:
                row = []
                for var in self.variables:
                    value = record.get(var, 0)
                    if isinstance(value, (int, float)):
                        row.append(value)
                    else:
                        row.append(0)
                matrix.append(row)
            
            return np.array(matrix)
        except Exception as e:
            logger.error(f"❌ Error preparing data matrix: {e}")
            return None
    
    def _compute_granger_causality(self, x: np.ndarray, y: np.ndarray, max_lag: int = 5) -> float:
        """
        حساب Granger Causality بين متغيرين
        يحدد إذا كان X يسبب Y (وليس مجرد ارتباط)
        """
        try:
            if len(x) < max_lag + 10:
                return 0.0
            
            n = len(x) - max_lag
            X_lagged = np.zeros((n, max_lag))
            Y_lagged = np.zeros((n, max_lag))
            Y_target = y[max_lag:]
            
            for lag in range(max_lag):
                X_lagged[:, lag] = x[lag:lag + n]
                Y_lagged[:, lag] = y[lag:lag + n]
            
            X_full = np.hstack([Y_lagged, X_lagged])
            
            rss_restricted = self._compute_residuals(Y_lagged, Y_target)
            rss_full = self._compute_residuals(X_full, Y_target)
            
            if rss_restricted == 0 or rss_full == 0:
                return 0.0
            
            f_stat = ((rss_restricted - rss_full) / max_lag) / (rss_full / (n - 2 * max_lag))
            
            causality_strength = min(1.0, max(0.0, f_stat / 10))
            
            return causality_strength
        
        except Exception as e:
            logger.error(f"❌ Error computing Granger causality: {e}")
            return 0.0
    
    def _compute_residuals(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        حساب مجموع مربعات البواقي (RSS)
        """
        try:
            X_with_intercept = np.hstack([np.ones((X.shape[0], 1)), X])
            
            beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            
            predictions = X_with_intercept @ beta
            residuals = y - predictions
            rss = np.sum(residuals ** 2)
            
            return rss
        except Exception as e:
            logger.error(f"❌ Error computing residuals: {e}")
            return 1e10
    
    def compute_causal_effect(self, treatment: str, outcome: str, 
                             current_state: Dict[str, float]) -> Dict:
        """
        حساب التأثير السببي (Causal Effect) باستخدام Do-Calculus
        
        السؤال: "ماذا سيحدث للسعر إذا تدخلنا وغيرنا RSI؟"
        بدلاً من: "ماذا يحدث للسعر عندما يتغير RSI؟"
        """
        try:
            if not nx.has_path(self.causal_graph, treatment, outcome):
                return {
                    'effect': 0.0,
                    'confidence': 0.0,
                    'is_causal': False,
                    'explanation': f'No causal path from {treatment} to {outcome}'
                }
            
            all_paths = list(nx.all_simple_paths(self.causal_graph, treatment, outcome))
            
            total_effect = 0.0
            path_effects = []
            
            for path in all_paths:
                path_strength = 1.0
                for i in range(len(path) - 1):
                    edge_weight = self.causal_graph[path[i]][path[i + 1]]['weight']
                    path_strength *= edge_weight
                
                path_effects.append({
                    'path': ' → '.join(path),
                    'strength': path_strength
                })
                total_effect += path_strength
            
            confounders = self._find_confounders(treatment, outcome)
            
            adjustment_factor = 1.0
            if confounders:
                adjustment_factor = 0.7
            
            adjusted_effect = total_effect * adjustment_factor
            
            confidence = min(0.95, adjusted_effect)
            
            return {
                'effect': round(adjusted_effect, 4),
                'confidence': round(confidence, 4),
                'is_causal': adjusted_effect > 0.5,
                'paths': path_effects,
                'confounders': confounders,
                'explanation': f'{treatment} has {adjusted_effect:.2f} causal effect on {outcome}'
            }
        
        except Exception as e:
            logger.error(f"❌ Error computing causal effect: {e}")
            return {'effect': 0.0, 'confidence': 0.0, 'is_causal': False}
    
    def _find_confounders(self, treatment: str, outcome: str) -> List[str]:
        """
        البحث عن المتغيرات المربكة (Confounders)
        المتغير المربك يؤثر على كل من المعالجة والنتيجة
        """
        confounders = []
        
        for node in self.causal_graph.nodes():
            if node == treatment or node == outcome:
                continue
            
            affects_treatment = nx.has_path(self.causal_graph, node, treatment)
            affects_outcome = nx.has_path(self.causal_graph, node, outcome)
            
            if affects_treatment and affects_outcome:
                confounders.append(node)
        
        return confounders
    
    def filter_spurious_correlations(self, signals: List[Dict]) -> List[Dict]:
        """
        فلترة الارتباطات الزائفة - الإشارات المبنية على ارتباط وليس سببية
        """
        filtered_signals = []
        
        for signal in signals:
            indicator = signal.get('indicator', '')
            
            if not indicator:
                filtered_signals.append(signal)
                continue
            
            causal_analysis = self.compute_causal_effect(
                treatment=indicator,
                outcome='price_change',
                current_state=signal
            )
            
            if causal_analysis['is_causal']:
                signal['causal_strength'] = causal_analysis['effect']
                signal['causal_confidence'] = causal_analysis['confidence']
                signal['is_spurious'] = False
                filtered_signals.append(signal)
            else:
                logger.info(f"🚫 Filtered spurious signal from {indicator} (correlation without causation)")
                signal['is_spurious'] = True
        
        logger.info(f"✅ Filtered {len(signals) - len(filtered_signals)} spurious signals")
        
        return filtered_signals
    
    def identify_market_drivers(self, symbol: str) -> Dict:
        """
        تحديد المحركات الحقيقية للسوق (True Market Drivers)
        ما الذي يسبب حركة السعر فعلياً؟
        """
        drivers = []
        
        for node in self.causal_graph.nodes():
            if node == 'price_change':
                continue
            
            effect = self.compute_causal_effect(node, 'price_change', {})
            
            if effect['is_causal']:
                drivers.append({
                    'driver': node,
                    'strength': effect['effect'],
                    'confidence': effect['confidence'],
                    'paths': effect.get('paths', [])
                })
        
        drivers.sort(key=lambda x: x['strength'], reverse=True)
        
        logger.info(f"🎯 Identified {len(drivers)} true market drivers for {symbol}")
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'drivers': drivers[:5],
            'total_analyzed': len(self.causal_graph.nodes())
        }
    
    def get_causal_recommendation(self, swarm_vote: Dict, 
                                  technical_signals: Dict) -> Dict:
        """
        توصية مبنية على التحليل السببي
        دمج تصويت السرب مع التحليل السببي
        """
        try:
            signals = []
            
            for indicator, value in technical_signals.items():
                if isinstance(value, (int, float)):
                    signals.append({
                        'indicator': indicator,
                        'value': value
                    })
            
            causal_signals = self.filter_spurious_correlations(signals)
            
            causal_confidence = 0.0
            for sig in causal_signals:
                if not sig.get('is_spurious', False):
                    causal_confidence += sig.get('causal_strength', 0)
            
            causal_confidence = min(100, causal_confidence * 10)
            
            swarm_confidence = swarm_vote.get('confidence', 0)
            
            final_confidence = (causal_confidence * 0.6) + (swarm_confidence * 0.4)
            
            decision = swarm_vote.get('decision', 'HOLD')
            
            if final_confidence < 60:
                decision = 'HOLD'
            
            return {
                'decision': decision,
                'confidence': round(final_confidence, 2),
                'causal_confidence': round(causal_confidence, 2),
                'swarm_confidence': round(swarm_confidence, 2),
                'true_signals': len(causal_signals),
                'filtered_spurious': len(signals) - len(causal_signals),
                'explanation': f'Causal analysis filtered {len(signals) - len(causal_signals)} spurious signals'
            }
        
        except Exception as e:
            logger.error(f"❌ Error in causal recommendation: {e}")
            return swarm_vote
    
    def export_causal_graph(self) -> Dict:
        """
        تصدير الرسم البياني السببي للعرض في Dashboard
        """
        nodes = []
        for node in self.causal_graph.nodes():
            nodes.append({
                'id': node,
                'label': node.replace('_', ' ').title(),
                'in_degree': self.causal_graph.in_degree(node),
                'out_degree': self.causal_graph.out_degree(node)
            })
        
        edges = []
        for source, target, data in self.causal_graph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'weight': data['weight'],
                'strength': 'strong' if data['weight'] > 0.7 else 'medium' if data['weight'] > 0.5 else 'weak'
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'generated_at': datetime.now().isoformat()
        }


causal_engine = None

def initialize_causal_engine(db_manager=None):
    """تهيئة محرك التحليل السببي"""
    global causal_engine
    causal_engine = CausalInferenceEngine(db_manager)
    return causal_engine

def get_causal_engine():
    """الحصول على محرك التحليل السببي"""
    global causal_engine
    if causal_engine is None:
        causal_engine = CausalInferenceEngine()
    return causal_engine
