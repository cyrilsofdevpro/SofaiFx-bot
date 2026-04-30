"""
Hugging Face AI Service - Sentiment & Text Analysis
- Uses HF Inference API for advanced sentiment analysis
- Caches results to avoid rate limits
- Fallback to local analysis if API fails

Author: SofAi FX Bot - AI Division
Version: 2.0.0
"""

import hashlib
import time
from ..utils.logger import logger
from ..config import config

class HuggingFaceService:
    """Hugging Face API integration for market sentiment analysis"""
    
    HF_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    def __init__(self):
        self.api_key = getattr(config, 'HF_API_KEY', '') or os.getenv('HF_API_KEY', '')
        
        if not self.api_key:
            logger.warning("[HF] No HuggingFace API key found in environment or config")
        
        self.cache = {}
        self.cache_ttl = 300
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        # Initialize HF client
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=self.api_key) if self.api_key else None
            if self.client:
                logger.info("[HF] HuggingFace Service initialized")
            else:
                logger.warning("[HF] HuggingFace Client not initialized (no API key)")
        except Exception as e:
            logger.warning(f"[HF] Client init failed: {e}")
            self.client = None
        
        logger.info(f"[HF] HuggingFace Service initialized")
    
    def analyze_market_sentiment(self, symbol, market_data=None):
        """
        Analyze market sentiment using Hugging Face
        
        Args:
            symbol: Currency pair (EURUSD, etc.)
            market_data: Optional dict with market context
        
        Returns:
            float: -1.0 (bearish) to +1.0 (bullish)
        """
        # Check cache first
        cache_key = self._get_cache_key(symbol)
        if cache_key in self.cache:
            cached_time, cached_result = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                logger.debug(f"[HF] Cache hit for {symbol}")
                return cached_result
        
        try:
            # Build sentiment text from market data
            text = self._build_sentiment_text(symbol, market_data)
            
            # Get sentiment from HF
            sentiment_score = self._get_hf_sentiment(text)
            
            # Cache result
            self.cache[cache_key] = (time.time(), sentiment_score)
            
            logger.info(f"[HF] Sentiment for {symbol}: {sentiment_score:.2f}")
            return sentiment_score
        
        except Exception as e:
            logger.warning(f"[HF] Error for {symbol}: {e}")
            # Fallback to technical sentiment
            return self._technical_fallback(symbol, market_data)
    
    def _build_sentiment_text(self, symbol, market_data):
        """Build text for sentiment analysis"""
        base_currency = symbol[:3]
        quote_currency = symbol[3:]
        
        text = f"FX Market: {base_currency}/{quote_currency} "
        
        if market_data:
            # Add price direction
            if 'price' in market_data and 'ma50' in market_data:
                if market_data['price'] > market_data.get('ma50', market_data['price']):
                    text += "showing bullish momentum. "
                else:
                    text += "facing downward pressure. "
            
            # Add RSI context
            if 'rsi' in market_data:
                rsi = market_data['rsi']
                if rsi > 70:
                    text += f"RSI overbought at {rsi:.0f}. "
                elif rsi < 30:
                    text += f"RSI oversold at {rsi:.0f}. "
                else:
                    text += f"RSI neutral at {rsi:.0f}. "
            
            # Add trend info
            if 'trend' in market_data:
                text += f"Current trend: {market_data['trend']}. "
        
        text += "Market outlook remains cautious amid global economic uncertainty."
        
        return text
    
    def _get_hf_sentiment(self, text):
        """
        Get sentiment from Hugging Face API
        
        Returns:
            float: -1.0 to +1.0
        """
        if not self.client:
            return 0.0
        
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        text = text[:512]
        
        try:
            result = self.client.text_classification(text, model=self.HF_MODEL)
            
            # Parse result - use weighted sentiment score
            positive_score = 0.0
            negative_score = 0.0
            
            for item in result:
                label = item.label.lower()
                score = item.score
                
                if "positive" in label:
                    positive_score = score
                elif "negative" in label:
                    negative_score = score
            
            # Calculate weighted sentiment (-1 to 1)
            # When neutral is top, use positive - negative difference
            sentiment = positive_score - negative_score
            
            # Boost if positive is significant (> 20%)
            if positive_score > 0.2 and positive_score > negative_score:
                return positive_score
            elif negative_score > 0.2 and negative_score > positive_score:
                return -negative_score
            else:
                return sentiment
        
        except Exception as e:
            logger.warning(f"[HF] Request error: {e}")
            return 0.0
        finally:
            self.last_request_time = time.time()
    
    def _parse_hf_result(self, result):
        """Parse Hugging Face API response to -1 to 1 score"""
        try:
            if not result or not isinstance(result, list):
                return 0.0
            
            data = result[0]
            if not data or not isinstance(data, list):
                return 0.0
            
            # Find highest scoring label
            max_score = 0.0
            max_label = "neutral"
            
            for item in data:
                label = item.get('label', '').lower()
                score = item.get('score', 0.0)
                
                if score > max_score:
                    max_score = score
                    max_label = label
            
            # Convert to -1 to 1 scale
            if "positive" in max_label or "bullish" in max_label:
                return max_score  # 0 to 1
            elif "negative" in max_label or "bearish" in max_label:
                return -max_score  # -1 to 0
            else:
                return 0.0
        
        except Exception as e:
            logger.warning(f"[HF] Parse error: {e}")
            return 0.0
    
    def _technical_fallback(self, symbol, market_data):
        """Fallback to technical-based sentiment"""
        if not market_data:
            return 0.0
        
        score = 0.0
        count = 0
        
        # Price vs MA
        if 'price' in market_data and 'ma50' in market_data:
            if market_data['price'] > market_data['ma50']:
                score += 0.3
            else:
                score -= 0.3
            count += 1
        
        # RSI
        if 'rsi' in market_data:
            rsi = market_data['rsi']
            if rsi > 60:
                score += 0.2
            elif rsi < 40:
                score -= 0.2
            count += 1
        
        return score / count if count > 0 else 0.0
    
    def _get_cache_key(self, symbol):
        """Generate cache key for symbol"""
        return hashlib.md5(symbol.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear sentiment cache"""
        self.cache.clear()
        logger.info("[HF] Cache cleared")