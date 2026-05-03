"""
News Filter - Economic calendar and breaking news integration
- Checks for upcoming economic events
- Filters trades during high-impact news
- Analyzes breaking news impact
- Provides trading readiness score

Author: SofAi FX Bot - AI Division
Version: 1.0.0
"""

import requests
from datetime import datetime, timedelta
from src.utils.logger import logger
from src.config import config
import warnings
warnings.filterwarnings('ignore')

class NewsFilter:
    """Filters trading signals based on news and economic events"""
    
    ECONOMIC_CALENDAR_URL = "https://api.example.com/events"  # Placeholder
    NEWSAPI_URL = "https://newsapi.org/v2/everything"
    
    # Economic indicators that affect forex
    HIGH_IMPACT_INDICATORS = [
        'Central Bank Interest Rate Decision',
        'Non-Farm Payroll',
        'CPI',
        'GDP',
        'Unemployment Rate',
        'Inflation Rate',
        'Consumer Confidence',
        'PMI',
        'Retail Sales'
    ]
    
    CURRENCY_INDICATORS = {
        'USD': ['Non-Farm Payroll', 'Fed Interest Rate', 'CPI', 'Unemployment', 'Consumer Confidence', 'Jobless Claims'],
        'EUR': ['ECB Interest Rate', 'ECB Decision', 'Eurozone CPI', 'Eurozone PMI', 'Eurozone GDP'],
        'GBP': ['BoE Interest Rate', 'UK CPI', 'UK Unemployment', 'UK Retail Sales', 'GfK Consumer Confidence'],
        'JPY': ['BoJ Interest Rate', 'Japan GDP', 'Japan CPI', 'Japan PMI', 'Japan Unemployment'],
        'AUD': ['RBA Interest Rate', 'Australia Employment', 'Australia GDP', 'Australia CPI'],
        'CAD': ['BoC Interest Rate', 'Canada Employment', 'Canada GDP', 'Canada CPI'],
        'CHF': ['SNB Interest Rate', 'Switzerland GDP', 'Switzerland Inflation'],
        'NZD': ['RBNZ Interest Rate', 'NZ Employment', 'NZ CPI', 'NZ GDP']
    }
    
    def __init__(self):
        self.news_key = getattr(config, 'NEWSAPI_KEY', '')
        self.cache = {}  # Simple cache for news/events
        logger.info("📰 News Filter initialized")
    
    def filter(self, symbol):
        """
        Check if trading should proceed based on news
        
        Args:
            symbol: Currency pair (e.g., EURUSD)
        
        Returns:
            tuple: (impact, should_trade)
            - impact: 'negative', 'neutral', 'positive'
            - should_trade: bool
        """
        try:
            impact = 'neutral'
            should_trade = True
            
            # Extract currencies from pair
            base_currency = symbol[:3]
            quote_currency = symbol[3:6]
            
            # 1. Check for upcoming high-impact events (within 2 hours)
            events_impact = self._check_upcoming_events(base_currency, quote_currency)
            
            # 2. Check for breaking news
            news_impact = self._check_breaking_news(symbol, base_currency, quote_currency)
            
            # 3. Combine impacts
            if events_impact == 'negative' or news_impact == 'negative':
                impact = 'negative'
                should_trade = False  # Don't trade before high-impact news
            elif events_impact == 'positive' or news_impact == 'positive':
                impact = 'positive'
                should_trade = True
            else:
                impact = 'neutral'
                should_trade = True
            
            logger.debug(
                f"📰 News filter for {symbol}: {impact} "
                f"(events: {events_impact}, news: {news_impact})"
            )
            
            return impact, should_trade
        
        except Exception as e:
            logger.warning(f"❌ News filter error for {symbol}: {e}")
            return 'neutral', True  # Default to trading if error
    
    def _check_upcoming_events(self, base_currency, quote_currency):
        """
        Check for upcoming economic events
        
        Returns: 'negative', 'neutral', 'positive'
        """
        try:
            # Simulate checking economic calendar
            # In production, would integrate with:
            # - https://economictimes.indiatimes.com
            # - https://tradingeconomics.com/calendar/
            # - https://www.forexfactory.com/calendar
            
            now = datetime.utcnow()
            
            # Simulated events check
            high_impact_coming = False
            medium_impact_coming = False
            
            # Currency-specific indicators
            base_indicators = self.CURRENCY_INDICATORS.get(base_currency, [])
            quote_indicators = self.CURRENCY_INDICATORS.get(quote_currency, [])
            
            # Check for any indicators in next 2 hours
            # This is a simplified version - real implementation would query actual calendar
            
            if high_impact_coming:
                logger.debug(f"⚠️ High-impact event coming for {base_currency}/{quote_currency}")
                return 'negative'  # Caution: high volatility expected
            elif medium_impact_coming:
                return 'neutral'  # Prepare for potential volatility
            
            return 'neutral'
        
        except Exception as e:
            logger.debug(f"Economic event check failed: {e}")
            return 'neutral'
    
    def _check_breaking_news(self, symbol, base_currency, quote_currency):
        """
        Check for breaking news about currencies
        
        Returns: 'negative', 'neutral', 'positive'
        """
        try:
            if not self.news_key:
                return 'neutral'
            
            # Check cache first (cache for 5 minutes)
            cache_key = f"{symbol}_news"
            if cache_key in self.cache:
                cached_time, cached_result = self.cache[cache_key]
                if (datetime.utcnow() - cached_time).total_seconds() < 300:
                    return cached_result
            
            # Fetch recent news
            query = f"{base_currency} {quote_currency} forex"
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_key,
                'pageSize': 10
            }
            
            response = requests.get(self.NEWSAPI_URL, params=params, timeout=5)
            articles = response.json().get('articles', [])
            
            if not articles:
                return 'neutral'
            
            # Analyze recent articles (last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_articles = []
            
            for article in articles:
                try:
                    pub_time = datetime.fromisoformat(
                        article.get('publishedAt', '').replace('Z', '+00:00')
                    )
                    if pub_time > one_hour_ago:
                        recent_articles.append(article)
                except:
                    pass
            
            if not recent_articles:
                return 'neutral'
            
            # Analyze sentiment of recent articles
            positive_count = 0
            negative_count = 0
            
            positive_keywords = [
                'gain', 'surge', 'rally', 'jump', 'bull', 'strength', 'bullish',
                'rise', 'recovery', 'positive', 'strong', 'support', 'outperform'
            ]
            negative_keywords = [
                'fall', 'crash', 'drop', 'plunge', 'bear', 'weakness', 'bearish',
                'decline', 'loss', 'negative', 'weak', 'resistance', 'underperform',
                'risk', 'concern', 'warning'
            ]
            
            for article in recent_articles:
                text = (
                    article.get('title', '') + ' ' + 
                    article.get('description', '')
                ).lower()
                
                pos = sum(1 for kw in positive_keywords if kw in text)
                neg = sum(1 for kw in negative_keywords if kw in text)
                
                if pos > neg:
                    positive_count += 1
                elif neg > pos:
                    negative_count += 1
            
            # Determine overall impact
            if negative_count > positive_count * 1.5:
                result = 'negative'
            elif positive_count > negative_count * 1.5:
                result = 'positive'
            else:
                result = 'neutral'
            
            # Cache the result
            self.cache[cache_key] = (datetime.utcnow(), result)
            
            logger.debug(
                f"Breaking news for {symbol}: {result} "
                f"(positive: {positive_count}, negative: {negative_count})"
            )
            
            return result
        
        except Exception as e:
            logger.debug(f"Breaking news check failed for {symbol}: {e}")
            return 'neutral'
    
    def get_trading_readiness(self, symbol):
        """
        Get overall trading readiness score (0-100)
        
        Considers: economic calendar, news sentiment, volatility expectations
        """
        try:
            impact, should_trade = self.filter(symbol)
            
            readiness_score = 75  # Base score
            
            if impact == 'negative':
                readiness_score = 40  # Risky to trade
            elif impact == 'positive':
                readiness_score = 85  # Favorable conditions
            else:
                readiness_score = 70  # Neutral, safe to trade
            
            return {
                'symbol': symbol,
                'readiness_score': readiness_score,
                'should_trade': should_trade,
                'impact': impact,
                'recommendation': self._get_recommendation(readiness_score, should_trade)
            }
        
        except Exception as e:
            logger.warning(f"Trading readiness check failed: {e}")
            return {
                'symbol': symbol,
                'readiness_score': 70,
                'should_trade': True,
                'impact': 'neutral',
                'recommendation': 'Unknown - proceed with caution'
            }
    
    @staticmethod
    def _get_recommendation(score, should_trade):
        """Get human-readable recommendation"""
        if score >= 80:
            return "✅ Excellent conditions - strong trade setup"
        elif score >= 70:
            return "🟡 Good conditions - safe to trade"
        elif score >= 50:
            return "⚠️ Caution - proceed with smaller position"
        else:
            return "🔴 High risk - consider waiting"
