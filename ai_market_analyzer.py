import os
import json
from openai import OpenAI
from logger_setup import setup_logger
from datetime import datetime

logger = setup_logger('ai_market_analyzer')

class AIMarketAnalyzer:
    """
    محلل السوق الذكي - يستخدم GPT-4 لتحليل السوق وإعطاء توصيات
    """
    
    def __init__(self):
        self.client = None
        self.enabled = False
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                self.enabled = True
                logger.info("🤖 AI Market Analyzer initialized with OpenAI GPT-4")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            logger.warning("⚠️ OPENAI_API_KEY not found - AI Market Analyzer disabled")
    
    def analyze_market_conditions(self, symbol: str, indicators: dict, market_regime: str, 
                                  momentum_index: float = None, recent_trades: list = None) -> dict:
        """
        تحليل شامل لظروف السوق باستخدام AI
        
        Returns:
        {
            'analysis': 'نص التحليل',
            'recommendation': 'BUY' | 'SELL' | 'HOLD',
            'confidence': 0.0 - 1.0,
            'key_insights': ['insight1', 'insight2', ...],
            'risk_level': 'LOW' | 'MEDIUM' | 'HIGH'
        }
        """
        if not self.enabled:
            return None
        
        try:
            market_data = {
                'symbol': symbol,
                'price': indicators.get('close'),
                'rsi': indicators.get('rsi'),
                'stochastic': indicators.get('stoch_k'),
                'macd': indicators.get('macd'),
                'macd_signal': indicators.get('macd_signal'),
                'bollinger_upper': indicators.get('bb_upper'),
                'bollinger_lower': indicators.get('bb_lower'),
                'ema_short': indicators.get('ema_short'),
                'ema_long': indicators.get('ema_long'),
                'adx': indicators.get('adx'),
                'market_regime': market_regime,
                'momentum_index': momentum_index
            }
            
            trade_history = ""
            if recent_trades and len(recent_trades) > 0:
                trade_history = f"\n\nآخر {len(recent_trades)} صفقات:\n"
                for trade in recent_trades[:5]:
                    profit = trade.get('profit_percent', 0)
                    trade_history += f"- {trade['symbol']}: {'ربح' if profit > 0 else 'خسارة'} {profit:.2f}%\n"
            
            prompt = f"""أنت محلل مالي خبير متخصص في العملات الرقمية. قم بتحليل البيانات التالية وقدم توصية واضحة.

**بيانات السوق:**
- الرمز: {symbol}
- السعر الحالي: ${market_data['price']:.2f}
- RSI: {market_data['rsi']:.1f}
- Stochastic: {market_data['stochastic']:.1f}
- MACD: {market_data['macd']:.4f}
- MACD Signal: {market_data['macd_signal']:.4f}
- Bollinger Bands: Lower=${market_data['bollinger_lower']:.2f}, Upper=${market_data['bollinger_upper']:.2f}
- EMA Short: {market_data['ema_short']:.2f}, EMA Long: {market_data['ema_long']:.2f}
- ADX (قوة الترند): {market_data['adx']:.1f}
- حالة السوق: {market_data['market_regime'].upper()}
- مؤشر الزخم المخصص: {market_data['momentum_index']:.1f}/100 (كلما قل، كلما كان أفضل للشراء)
{trade_history}

**المطلوب:**
1. تحليل شامل للوضع الحالي (3-4 جمل)
2. التوصية: BUY أو SELL أو HOLD
3. مستوى الثقة: رقم من 0 إلى 1
4. 3-4 نقاط رئيسية (key insights)
5. مستوى المخاطرة: LOW أو MEDIUM أو HIGH

**مهم:** أجب بصيغة JSON فقط بهذا الشكل:
{{
    "analysis": "نص التحليل بالعربية",
    "recommendation": "BUY أو SELL أو HOLD",
    "confidence": 0.85,
    "key_insights": ["نقطة 1", "نقطة 2", "نقطة 3"],
    "risk_level": "MEDIUM"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "أنت محلل مالي خبير في العملات الرقمية. تجيب دائماً بصيغة JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            logger.info(f"🤖 AI Analysis for {symbol}: {result['recommendation']} (confidence: {result['confidence']:.0%})")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Raw response: {result_text}")
            return None
        except Exception as e:
            logger.error(f"Error in AI market analysis: {e}")
            return None
    
    def explain_buy_signal(self, symbol: str, signals: list, indicators: dict) -> str:
        """
        شرح إشارة الشراء بلغة بسيطة
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""أنت مساعد تداول ذكي. اشرح بلغة بسيطة وواضحة لماذا تم إصدار إشارة شراء لـ {symbol}.

**الإشارات التي تحققت:**
{chr(10).join(f'- {signal}' for signal in signals)}

**بيانات المؤشرات:**
- RSI: {indicators.get('rsi', 0):.1f}
- Stochastic: {indicators.get('stoch_k', 0):.1f}
- السعر: ${indicators.get('close', 0):.2f}
- Bollinger Lower: ${indicators.get('bb_lower', 0):.2f}

اشرح في 2-3 جمل فقط بالعربية، بلغة بسيطة يفهمها المبتدئ."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "أنت مساعد تداول يشرح الإشارات بلغة بسيطة للمبتدئين."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.debug(f"AI explanation for {symbol} buy signal generated")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating buy signal explanation: {e}")
            return None
    
    def audit_strategy_performance(self, stats: dict, recent_trades: list) -> dict:
        """
        مراجعة وتدقيق أداء الاستراتيجية وإعطاء توصيات للتحسين
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""أنت مستشار استراتيجيات تداول خبير. راجع أداء البوت وقدم توصيات للتحسين.

**الإحصائيات الإجمالية:**
- إجمالي الصفقات: {stats.get('total_trades', 0)}
- الصفقات الرابحة: {stats.get('winning_trades', 0)}
- الصفقات الخاسرة: {stats.get('losing_trades', 0)}
- نسبة النجاح: {stats.get('win_rate', 0):.1f}%
- إجمالي الربح: ${stats.get('total_profit_usd', 0):.2f}
- متوسط الربح: {stats.get('average_profit', 0):.2f}%
- أفضل صفقة: {stats.get('best_trade', 0):.2f}%
- أسوأ صفقة: {stats.get('worst_trade', 0):.2f}%

**آخر 5 صفقات:**
{chr(10).join(f"- {trade['symbol']}: {'ربح' if trade.get('profit_percent', 0) > 0 else 'خسارة'} {trade.get('profit_percent', 0):.2f}%" for trade in recent_trades[:5])}

**المطلوب:**
قدم تقييم شامل بصيغة JSON:
{{
    "overall_rating": "ممتاز / جيد / متوسط / ضعيف",
    "performance_score": 0.0-10.0,
    "strengths": ["نقطة قوة 1", "نقطة قوة 2"],
    "weaknesses": ["نقطة ضعف 1", "نقطة ضعف 2"],
    "recommendations": ["توصية 1", "توصية 2", "توصية 3"],
    "risk_assessment": "تقييم المخاطر",
    "next_steps": "الخطوات التالية المقترحة"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "أنت مستشار استراتيجيات تداول خبير. تجيب بصيغة JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            logger.info(f"🔍 Strategy audit completed: {result['overall_rating']} (score: {result['performance_score']}/10)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in strategy audit: {e}")
            return None
