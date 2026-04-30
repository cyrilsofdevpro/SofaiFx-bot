"""
Sentiment Analyzer - Market sentiment scoring
- Hugging Face AI (primary)
- Alpha Vantage sentiment API (backup)
- NewsAPI integration
- Real-time market mood scoring (-1.0 to +1.0)

Author: SofAi FX Bot - AI Division
Version: 2.0.0
"""

import requests
from datetime import datetime, timedelta
from ..utils.logger import logger
from ..config import config
import json

class SentimentAnalyzer:
    """Analyzes market sentiment from multiple sources"""
    
    ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
    NEWSAPI_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self):
        self.alpha_key = config.ALPHA_VANTAGE_API_KEY
        self.news_key = getattr(config, 'NEWSAPI_KEY', '')
        
        # Initialize Hugging Face service
        try:
            from .huggingface_service import HuggingFaceService
            self.hf_service = HuggingFaceService()
            logger.info("📊 Sentiment Analyzer initialized (with HuggingFace)")
        except Exception as e:
            logger.warning(f"⚠️ HuggingFace not available: {e}")
            self.hf_service = None
    
    def analyze(self, symbol, market_data=None):
        """
        Get market sentiment for a currency pair
        
        Args:
            symbol: Currency pair (EURUSD, etc.)
            market_data: Optional dict with price, rsi, ma50, trend for context
        
        Returns:
            float: -1.0 (very bearish) to +1.0 (very bullish)
        """
        try:
            sentiments = []
            weights = []
            
            # 1. Hugging Face AI (primary - highest weight)
            if self.hf_service:
                hf_sentiment = self.hf_service.analyze_market_sentiment(symbol, market_data)
                sentiments.append(hf_sentiment)
                weights.append(0.5)  # 50% weight - most accurate
                logger.debug(f"🤗 HF sentiment for {symbol}: {hf_sentiment:.2f}")
            
            # 2. Alpha Vantage Sentiment (if available)
            av_sentiment = self._get_alphavantage_sentiment(symbol)
            if av_sentiment is not None:
                sentiments.append(av_sentiment)
                weights.append(0.3)  # 30% weight
            
            # 3. News Sentiment (if API key available)
            if self.news_key:
                news_sentiment = self._get_news_sentiment(symbol)
                if news_sentiment is not None:
                    sentiments.append(news_sentiment)
                    weights.append(0.2)  # 20% weight
            
            # 3. Technical Sentiment (if no external APIs)
            if not sentiments:
                tech_sentiment = self._get_technical_sentiment(symbol)
                sentiments.append(tech_sentiment)
                weights.append(1.0)
            
            # Weighted average
            if sentiments:
                total_weight = sum(weights)
                weighted_sum = sum(s * w for s, w in zip(sentiments, weights))
                final_sentiment = weighted_sum / total_weight
            else:
                final_sentiment = 0.0
            
            logger.debug(
                f"📊 Sentiment for {symbol}: {final_sentiment:.2f} "
                f"(sources: {len(sentiments)})"
            )
            return final_sentiment
        
        except Exception as e:
            logger.warning(f"❌ Sentiment analysis error for {symbol}: {e}")
            return 0.0  # Neutral default
    
    def _get_alphavantage_sentiment(self, symbol):
        """
        Get sentiment from Alpha Vantage News Sentiment API
        
        Returns: float (-1 to 1) or None if unavailable
        """
        try:
            if not self.alpha_key:
                return None
            
            # Extract base currency from pair (e.g., EUR from EURUSD)
            base_currency = symbol[:3]
            
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': base_currency,
                'apikey': self.alpha_key,
                'time_period': '24h'
            }
            
            response = requests.get(self.ALPHA_VANTAGE_URL, params=params, timeout=5)
            data = response.json()
            
            if 'feed' not in data or not data['feed']:
                logger.debug(f"No Alpha Vantage news for {symbol}")
                return None
            
            # Calculate average sentiment from articles
            sentiments = []
            for article in data['feed'][:10]:  # Last 10 articles
                if 'overall_sentiment_score' in article:
                    score = float(article['overall_sentiment_score'])
                    sentiments.append(score)
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                logger.debug(f"Alpha Vantage sentiment for {symbol}: {avg_sentiment:.2f}")
                return avg_sentiment
            
            return None
        
        except Exception as e:
            logger.debug(f"Alpha Vantage sentiment fetch failed for {symbol}: {e}")
            return None
    
    def _get_news_sentiment(self, symbol):
        """
        Get sentiment from NewsAPI
        
        Returns: float (-1 to 1) or None if unavailable
        """
        try:
            if not self.news_key:
                return None
            
            # Get news about the currency pair
            query = f"{symbol} forex trading"
            
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_key,
                'pageSize': 20
            }
            
            response = requests.get(self.NEWSAPI_URL, params=params, timeout=5)
            articles = response.json().get('articles', [])
            
            if not articles:
                logger.debug(f"No news articles for {symbol}")
                return None
            
            # Simple sentiment analysis on headlines
            positive_keywords = ['gain', 'surge', 'rally', 'up', 'bull', 'strength', 'bullish', 'rise']
            negative_keywords = ['fall', 'crash', 'drop', 'bear', 'weakness', 'bearish', 'decline']
            
            sentiment_scores = []
            for article in articles:
                headline = (article.get('title', '') + ' ' + article.get('description', '')).lower()
                
                positive_count = sum(1 for kw in positive_keywords if kw in headline)
                negative_count = sum(1 for kw in negative_keywords if kw in headline)
                
                if positive_count > negative_count:
                    sentiment_scores.append(0.5)
                elif negative_count > positive_count:
                    sentiment_scores.append(-0.5)
                else:
                    sentiment_scores.append(0.0)
            
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                logger.debug(f"News sentiment for {symbol}: {avg_sentiment:.2f}")
                return avg_sentiment
            
            return None
        
        except Exception as e:
            logger.debug(f"NewsAPI sentiment fetch failed for {symbol}: {e}")
            return None
    
    @staticmethod
    def _get_technical_sentiment(symbol):
        """
        Fallback: Simple technical sentiment
        
        Returns: float (-1 to 1)
        """
        try:
            # This is a placeholder - in real scenario would use existing market data
            # For now, return neutral
            logger.debug(f"Using technical sentiment fallback for {symbol}")
            return 0.0
        
        except Exception as e:
            logger.warning(f"Technical sentiment fallback failed: {e}")
            return 0.0
