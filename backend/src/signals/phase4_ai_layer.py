"""
Phase 4: AI Layer - Advanced Signal Generation with ML & Sentiment
- Market sentiment scoring (Alpha Vantage + NewsAPI)
- Pattern recognition (ML-based chart pattern detection)
- News filter (economic calendar + breaking news)
- Enhanced confidence scoring
- 300-400ms response time

Author: SofAi FX Bot - AI Division
Version: 4.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.logger import logger
from src.config import config
import warnings
warnings.filterwarnings('ignore')

class Phase4AILayer:
    """Advanced AI-powered signal generation with sentiment + patterns + news"""
    
    VERSION = "4.0.0"
    PHASE = 4
    
    def __init__(self):
        """Initialize Phase 4 with all AI modules"""
        from src.signals.sentiment_analyzer import SentimentAnalyzer
        from src.signals.pattern_recognizer import PatternRecognizer
        from src.signals.news_filter import NewsFilter
        
        self.sentiment = SentimentAnalyzer()
        self.patterns = PatternRecognizer()
        self.news_filter = NewsFilter()
        
        logger.info("🤖 Phase 4: AI Layer initialized (Sentiment + Patterns + News)")
    
    def get_signal(self, df, symbol):
        """
        Generate AI-powered signal using:
        1. Technical analysis (Phase 1 base)
        2. Sentiment scoring
        3. Pattern recognition
        4. News filtering
        
        Args:
            df: OHLC DataFrame
            symbol: Currency pair (EURUSD, etc)
        
        Returns:
            dict: {signal, confidence, price, sentiment_score, patterns, news_impact, full_analysis}
        """
        try:
            if df is None or df.empty or len(df) < 100:
                logger.warning(f"❌ Phase 4: Insufficient data for {symbol}")
                return self._hold_signal("Insufficient data")
            
            start_time = datetime.utcnow()
            
            # ============ STEP 1: Technical Base (from Phase 1) ============
            tech_signal, tech_confidence = self._get_technical_signal(df, symbol)
            
            # Build market data for sentiment analysis
            market_data = {
                'price': float(df['Close'].iloc[-1]),
                'ma50': float(df['Close'].tail(50).mean()),
                'rsi': self._calculate_rsi(df['Close'], 14),
                'trend': tech_signal
            }
            
            # ============ STEP 2: Sentiment Analysis (with Hugging Face) ============
            sentiment_score = self.sentiment.analyze(symbol, market_data)
            sentiment_boost = self._sentiment_to_confidence_boost(sentiment_score)
            
            # ============ STEP 3: Pattern Recognition ============
            patterns = self.patterns.detect(df, symbol)
            pattern_confidence = self._patterns_to_confidence(patterns)
            
            # ============ STEP 4: News Filtering ============
            news_impact, should_trade = self.news_filter.filter(symbol)
            
            # ============ STEP 5: Combine All Signals ============
            final_signal, final_confidence = self._combine_ai_signals(
                tech_signal, tech_confidence,
                sentiment_score, sentiment_boost,
                patterns, pattern_confidence,
                news_impact, should_trade
            )
            
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            price = float(df['Close'].iloc[-1])
            
            result = {
                'signal': final_signal,
                'confidence': round(final_confidence, 2),
                'price': round(price, 5),
                'phase': 4,
                'response_time_ms': round(elapsed_ms, 1),
                'timestamp': datetime.utcnow().isoformat(),
                
                # AI Layer Specifics
                'sentiment': {
                    'score': round(sentiment_score, 2),  # -1.0 to +1.0
                    'interpretation': self._sentiment_text(sentiment_score),
                    'boost': round(sentiment_boost, 2)
                },
                'patterns': {
                    'detected': patterns,
                    'confidence_impact': round(pattern_confidence, 2),
                    'count': len(patterns)
                },
                'news': {
                    'impact': news_impact,  # 'negative', 'neutral', 'positive'
                    'should_trade': should_trade,
                    'reason': self._news_reason(news_impact)
                },
                'technical': {
                    'signal': tech_signal,
                    'confidence': round(tech_confidence, 2)
                },
                'analysis': {
                    'reason': self._generate_ai_reason(
                        tech_signal, sentiment_score, patterns, news_impact
                    ),
                    'recommendations': self._generate_recommendations(
                        final_signal, final_confidence, sentiment_score, patterns, news_impact
                    )
                }
            }
            
            logger.info(
                f"✅ Phase 4 AI: {symbol} → {final_signal} "
                f"(confidence: {final_confidence}, sentiment: {sentiment_score:.2f}, "
                f"patterns: {len(patterns)}, {elapsed_ms:.1f}ms)"
            )
            return result
        
        except Exception as e:
            logger.error(f"❌ Phase 4 Error: {symbol} - {str(e)}", exc_info=True)
            return self._error_signal(str(e))
    
    def _get_technical_signal(self, df, symbol):
        """
        Get base technical signal using Phase 1 lite engine logic
        """
        try:
            price = float(df['Close'].iloc[-1])
            ma50 = float(df['Close'].tail(50).mean())
            ma200 = float(df['Close'].tail(200).mean()) if len(df) >= 200 else ma50
            
            # Price relative to MAs
            above_ma50 = price > ma50
            above_ma200 = price > ma200
            
            # RSI
            rsi = self._calculate_rsi(df['Close'], 14)
            rsi_strong_buy = rsi < 30
            rsi_strong_sell = rsi > 70
            rsi_neutral = 40 <= rsi <= 60
            
            # Determine signal
            if above_ma50 and above_ma200 and not rsi_strong_sell:
                signal = "BUY"
                confidence = 0.7 if rsi_neutral else 0.6
            elif not above_ma50 and not above_ma200 and not rsi_strong_buy:
                signal = "SELL"
                confidence = 0.7 if rsi_neutral else 0.6
            else:
                signal = "HOLD"
                confidence = 0.5
            
            return signal, confidence
        
        except Exception as e:
            logger.warning(f"Technical signal failed: {e}")
            return "HOLD", 0.5
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate RSI indicator"""
        try:
            deltas = prices.diff()
            seed = deltas[:period+1]
            
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            
            rsi_values = [100 - (100 / (1 + rs)) if rs else 50]
            
            for i in range(period, len(deltas)):
                delta = deltas.iloc[i]
                if delta > 0:
                    up = (up * (period - 1) + delta) / period
                    down = (down * (period - 1)) / period
                else:
                    up = (up * (period - 1)) / period
                    down = (down * (period - 1) - delta) / period
                
                rs = up / down if down != 0 else 0
                rsi_values.append(100 - (100 / (1 + rs)))
            
            return float(rsi_values[-1])
        
        except Exception as e:
            logger.warning(f"RSI calculation failed: {e}")
            return 50.0
    
    @staticmethod
    def _sentiment_to_confidence_boost(sentiment_score):
        """
        Convert sentiment score (-1 to +1) to confidence boost
        
        Score:  -1.0 = -0.25 confidence (very bearish)
                 0.0 = +0.00 confidence (neutral)
                +1.0 = +0.25 confidence (very bullish)
        """
        return sentiment_score * 0.25
    
    @staticmethod
    def _patterns_to_confidence(patterns):
        """
        Convert detected patterns to confidence impact
        
        More confirmed patterns = higher confidence
        """
        if not patterns:
            return 0.0
        
        # Each pattern adds +0.1 to confidence (max +0.3 for 3+ patterns)
        pattern_count = min(len(patterns), 3)
        return pattern_count * 0.1
    
    @staticmethod
    def _sentiment_text(score):
        """Convert sentiment score to text"""
        if score >= 0.5:
            return "Very Bullish"
        elif score >= 0.2:
            return "Bullish"
        elif score >= -0.2:
            return "Neutral"
        elif score >= -0.5:
            return "Bearish"
        else:
            return "Very Bearish"
    
    @staticmethod
    def _news_reason(impact):
        """Get reason for news impact"""
        reasons = {
            'negative': 'Negative news detected - exercise caution',
            'neutral': 'No significant news events',
            'positive': 'Positive news supports trading'
        }
        return reasons.get(impact, 'Unknown news status')
    
    def _combine_ai_signals(self, tech_signal, tech_conf, 
                          sentiment_score, sentiment_boost,
                          patterns, pattern_conf,
                          news_impact, should_trade):
        """
        Combine all AI signals into final recommendation
        
        Formula: final_confidence = tech_conf + sentiment_boost + pattern_conf
        adjusted by news_impact
        """
        
        # If news says don't trade, override to HOLD
        if not should_trade:
            return "HOLD", 0.3
        
        # Base confidence from technical
        base_confidence = tech_conf
        
        # Add sentiment boost/penalty
        base_confidence += sentiment_boost
        
        # Add pattern recognition confidence
        base_confidence += pattern_conf
        
        # News impact modifier
        if news_impact == 'negative':
            base_confidence *= 0.7  # Reduce confidence by 30%
        elif news_impact == 'positive':
            base_confidence *= 1.2  # Boost confidence by 20%
        
        # Clamp to 0-1 range
        final_confidence = max(0.0, min(1.0, base_confidence))
        
        # If tech signal is weak, only return if confidence is very high
        if tech_signal == "HOLD":
            if final_confidence > 0.75:
                # Upgrade HOLD to BUY/SELL if we have strong sentiment + patterns
                final_signal = "BUY" if sentiment_score > 0 else "SELL"
            else:
                final_signal = "HOLD"
        else:
            final_signal = tech_signal
        
        return final_signal, final_confidence
    
    def _generate_ai_reason(self, tech_signal, sentiment_score, patterns, news_impact):
        """Generate human-readable explanation"""
        parts = []
        
        if tech_signal == "BUY":
            parts.append("✓ Technical setup is bullish")
        elif tech_signal == "SELL":
            parts.append("✓ Technical setup is bearish")
        else:
            parts.append("○ Technical setup is neutral")
        
        if sentiment_score > 0.3:
            parts.append(f"✓ Sentiment is bullish ({sentiment_score:.2f})")
        elif sentiment_score < -0.3:
            parts.append(f"✗ Sentiment is bearish ({sentiment_score:.2f})")
        else:
            parts.append(f"○ Sentiment is neutral ({sentiment_score:.2f})")
        
        if patterns:
            parts.append(f"✓ {len(patterns)} bullish pattern(s) detected")
        
        if news_impact == 'negative':
            parts.append("⚠ Negative news - caution advised")
        elif news_impact == 'positive':
            parts.append("✓ Positive news supports trade")
        
        return " | ".join(parts)
    
    def _generate_recommendations(self, signal, confidence, sentiment, patterns, news_impact):
        """Generate trading recommendations"""
        recommendations = []
        
        if confidence > 0.85:
            recommendations.append("🟢 HIGH CONFIDENCE - Strong trade setup")
        elif confidence > 0.65:
            recommendations.append("🟡 MEDIUM CONFIDENCE - Good setup, monitor closely")
        else:
            recommendations.append("🔴 LOW CONFIDENCE - Wait for better entry")
        
        if sentiment > 0.6:
            recommendations.append("📈 Market sentiment strongly bullish - favorable for longs")
        elif sentiment < -0.6:
            recommendations.append("📉 Market sentiment strongly bearish - favorable for shorts")
        
        if len(patterns) >= 2:
            recommendations.append(f"🎯 Multiple patterns aligned ({len(patterns)}) - increased reliability")
        
        if news_impact == 'negative' and signal == "BUY":
            recommendations.append("⚠️ Consider waiting - negative news could reverse the move")
        
        return recommendations
    
    @staticmethod
    def _hold_signal(reason):
        """Return HOLD signal"""
        return {
            'signal': 'HOLD',
            'confidence': 0.3,
            'phase': 4,
            'sentiment': {'score': 0.0, 'interpretation': 'Neutral', 'boost': 0.0},
            'patterns': {'detected': [], 'confidence_impact': 0.0, 'count': 0},
            'news': {'impact': 'neutral', 'should_trade': False, 'reason': reason},
            'analysis': {'reason': reason, 'recommendations': ['Wait for better setup']}
        }
    
    @staticmethod
    def _error_signal(error_msg):
        """Return error signal"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'phase': 4,
            'error': error_msg,
            'sentiment': {'score': 0.0, 'interpretation': 'Unknown', 'boost': 0.0},
            'patterns': {'detected': [], 'confidence_impact': 0.0, 'count': 0},
            'news': {'impact': 'neutral', 'should_trade': False, 'reason': f'Error: {error_msg}'}
        }
