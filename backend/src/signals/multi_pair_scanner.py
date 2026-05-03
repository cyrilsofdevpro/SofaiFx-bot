"""
Multi-Pair Signal Scanner
Scans multiple forex pairs and returns only the BEST opportunity

Features:
- Scans fixed watchlist: EURUSD, GBPUSD, USDJPY, XAUUSD, AUDUSD
- Scoring based on: Trend, RSI, Volatility, Session, Spread
- Returns only ONE best trade signal
- <1 second response time

Author: SofAi FX Bot
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from src.utils.logger import logger
from src.config import config
import requests
import warnings
warnings.filterwarnings('ignore')


class MultiPairScanner:
    """Scans multiple forex pairs and returns the best opportunity"""
    
    # Fixed watchlist
    WATCHLIST = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'AUDUSD']
    
    # Scoring weights
    WEIGHTS = {
        'trend': 0.30,      # MA alignment
        'rsi': 0.25,       # RSI conditions
        'volatility': 0.15, # ATR/volatility
        'session': 0.15,   # Market session
        'spread': 0.15     # Spread filter
    }
    
    # Market sessions (UTC)
    SESSIONS = {
        'sydney': (time(22, 0), time(7, 0)),
        'tokyo': (time(0, 0), time(9, 0)),
        'london': (time(7, 0), time(16, 0)),
        'newyork': (time(13, 0), time(22, 0))
    }
    
    # Max spread by pair (pips)
    MAX_SPREADS = {
        'EURUSD': 2.0,
        'GBPUSD': 3.0,
        'USDJPY': 2.0,
        'XAUUSD': 30.0,  # Gold is higher
        'AUDUSD': 3.0
    }
    
    def __init__(self):
        self.twelvedata_key = config.TWELVEDATA_API_KEY
        logger.info("🔍 Multi-Pair Scanner initialized")
    
    def scan_all(self, api_key=None):
        """
        Scan all pairs in watchlist and return best opportunity
        
        Args:
            api_key: Optional API key for rate limiting
        
        Returns:
            dict: Best opportunity or None
        """
        try:
            start_time = datetime.utcnow()
            logger.info(f"🔍 Starting multi-pair scan for {len(self.WATCHLIST)} pairs...")
            
            scores = []
            
            for symbol in self.WATCHLIST:
                try:
                    # Get data for this pair
                    df = self._get_pair_data(symbol)
                    
                    if df is None or df.empty or len(df) < 50:
                        logger.warning(f"  ⚠️ {symbol}: Insufficient data, skipping")
                        continue
                    
                    # Calculate score for this pair
                    score = self._calculate_score(df, symbol)
                    
                    if score:
                        scores.append(score)
                        logger.info(f"  📊 {symbol}: {score['signal']} (confidence: {score['confidence']:.2f})")
                    
                except Exception as e:
                    logger.warning(f"  ⚠️ {symbol}: Error - {str(e)}")
                    continue
            
            if not scores:
                logger.warning("❌ No valid opportunities found")
                return self._no_signal()
            
            # Sort by confidence and get best
            scores.sort(key=lambda x: x['confidence'], reverse=True)
            best = scores[0]
            
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"✅ Best opportunity: {best['symbol']} → {best['signal']} (confidence: {best['confidence']:.2f}, {elapsed_ms:.0f}ms)")
            
            return {
                'best_opportunity': {
                    'symbol': best['symbol'],
                    'signal': best['signal'],
                    'confidence': round(best['confidence'], 2),
                    'score_breakdown': best.get('breakdown', {}),
                    'timestamp': datetime.utcnow().isoformat(),
                    'scan_time_ms': round(elapsed_ms, 1)
                },
                'alternatives_scanned': len(scores) - 1
            }
        
        except Exception as e:
            logger.error(f"❌ Multi-pair scan error: {e}")
            return self._no_signal()
    
    def _get_pair_data(self, symbol):
        """Fetch OHLC data for a symbol"""
        try:
            from src.data.twelvedata import TwelveDataClient
            
            td = TwelveDataClient()
            
            # Parse symbol
            if len(symbol) == 6:
                from_sym = symbol[:3]
                to_sym = symbol[3:]
                td_symbol = f"{from_sym}/{to_sym}"
            else:
                td_symbol = symbol
            
            # Get 1-minute data for recent analysis
            df = td.get_time_series(td_symbol, interval='1min', outputsize=100)
            
            if df is not None and not df.empty:
                # Normalize columns
                if 'open' in df.columns:
                    df = df.rename(columns={
                        'open': 'Open', 'high': 'High', 
                        'low': 'Low', 'close': 'Close', 'volume': 'Volume'
                    })
            
            return df
        
        except Exception as e:
            logger.debug(f"Data fetch error for {symbol}: {e}")
            return None
    
    def _calculate_score(self, df, symbol):
        """Calculate overall score for a symbol"""
        try:
            breakdown = {}
            
            # 1. Trend Score (0-1)
            trend_score = self._score_trend(df)
            breakdown['trend'] = round(trend_score, 2)
            
            # 2. RSI Score (0-1)
            rsi_score = self._score_rsi(df)
            breakdown['rsi'] = round(rsi_score, 2)
            
            # 3. Volatility Score (0-1)
            volatility_score = self._score_volatility(df, symbol)
            breakdown['volatility'] = round(volatility_score, 2)
            
            # 4. Session Score (0-1)
            session_score = self._score_session()
            breakdown['session'] = round(session_score, 2)
            
            # 5. Spread Score (0-1)
            spread_score = self._score_spread(symbol)
            breakdown['spread'] = round(spread_score, 2)
            
            # Calculate weighted total
            total_score = (
                trend_score * self.WEIGHTS['trend'] +
                rsi_score * self.WEIGHTS['rsi'] +
                volatility_score * self.WEIGHTS['volatility'] +
                session_score * self.WEIGHTS['session'] +
                spread_score * self.WEIGHTS['spread']
            )
            
            # Determine signal direction
            signal = self._determine_signal(df, trend_score, rsi_score)
            
            return {
                'symbol': symbol,
                'signal': signal,
                'confidence': total_score,
                'breakdown': breakdown
            }
        
        except Exception as e:
            logger.debug(f"Score calculation error for {symbol}: {e}")
            return None
    
    def _score_trend(self, df):
        """Score based on MA alignment (trend strength)"""
        try:
            if len(df) < 50:
                return 0.5
            
            close = df['Close']
            
            # Calculate MAs
            ma20 = close.tail(20).mean()
            ma50 = close.tail(50).mean()
            ma200 = close.tail(200).mean() if len(df) >= 200 else ma50
            
            price = close.iloc[-1]
            
            # Score based on alignment
            score = 0.5  # Base
            
            # Price above all MAs = strong uptrend
            if price > ma20 > ma50 > ma200:
                score = 0.9
            # Price above 2 MAs = moderate uptrend
            elif price > ma20 and price > ma50:
                score = 0.7
            # Price below all MAs = strong downtrend
            elif price < ma20 < ma50 < ma200:
                score = 0.9  # Strong for SELL
            # Price below 2 MAs = moderate downtrend
            elif price < ma20 and price < ma50:
                score = 0.7
            # Mixed = weak/no trend
            else:
                score = 0.4
            
            return score
        
        except Exception as e:
            return 0.5
    
    def _score_rsi(self, df):
        """Score based on RSI conditions"""
        try:
            rsi = self._calculate_rsi(df['Close'], 14)
            
            # Strong buy signal: RSI < 30 (oversold)
            if rsi < 30:
                return 0.9
            # Moderate buy: RSI 30-40
            elif rsi < 40:
                return 0.7
            # Strong sell signal: RSI > 70 (overbought)
            elif rsi > 70:
                return 0.9
            # Moderate sell: RSI 60-70
            elif rsi > 60:
                return 0.7
            # Neutral: RSI 40-60
            else:
                return 0.5
        
        except Exception as e:
            return 0.5
    
    def _score_volatility(self, df, symbol):
        """Score based on volatility (ATR)"""
        try:
            if len(df) < 14:
                return 0.5
            
            # Calculate ATR
            high = df['High']
            low = df['Low']
            close = df['Close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.tail(14).mean()
            
            # Calculate ATR as percentage of price
            price = close.iloc[-1]
            atr_pct = (atr / price) * 100
            
            # Optimal volatility: 0.1% - 1.0% for forex
            if 0.1 <= atr_pct <= 0.5:
                return 0.8  # Good volatility
            elif 0.5 < atr_pct <= 1.0:
                return 0.6  # Moderate
            elif atr_pct < 0.1:
                return 0.4  # Too low
            else:
                return 0.3  # Too high (volatile)
        
        except Exception as e:
            return 0.5
    
    def _score_session(self):
        """Score based on market session"""
        try:
            now = datetime.utcnow().time()
            
            # Check which sessions are active
            active_sessions = []
            for session_name, (start, end) in self.SESSIONS.items():
                if start > end:
                    # Session spans midnight
                    if now >= start or now <= end:
                        active_sessions.append(session_name)
                else:
                    if start <= now <= end:
                        active_sessions.append(session_name)
            
            # Best sessions for trading
            if 'london' in active_sessions or 'newyork' in active_sessions:
                return 0.9  # Peak liquidity
            elif 'tokyo' in active_sessions:
                return 0.7  # Good liquidity
            elif 'sydney' in active_sessions:
                return 0.5  # Lower liquidity
            else:
                return 0.3  # Off hours
        
        except Exception as e:
            return 0.5
    
    def _score_spread(self, symbol):
        """Score based on spread (simulated)"""
        try:
            # In production, would fetch real spread from broker
            # For now, use conservative estimates
            
            typical_spreads = {
                'EURUSD': 1.2,
                'GBPUSD': 1.5,
                'USDJPY': 1.0,
                'XAUUSD': 20.0,
                'AUDUSD': 1.8
            }
            
            spread = typical_spreads.get(symbol, 2.0)
            max_spread = self.MAX_SPREADS.get(symbol, 3.0)
            
            if spread <= max_spread * 0.5:
                return 0.9
            elif spread <= max_spread:
                return 0.7
            else:
                return 0.3
        
        except Exception as e:
            return 0.5
    
    def _determine_signal(self, df, trend_score, rsi_score):
        """Determine BUY/SELL/HOLD based on scores"""
        try:
            close = df['Close']
            ma50 = close.tail(50).mean()
            price = close.iloc[-1]
            
            rsi = self._calculate_rsi(df['Close'], 14)
            
            # Strong BUY conditions
            if price > ma50 and rsi < 40:
                return 'BUY'
            # Strong SELL conditions
            elif price < ma50 and rsi > 60:
                return 'SELL'
            # Moderate conditions
            elif trend_score > 0.6 and rsi < 50:
                return 'BUY'
            elif trend_score > 0.6 and rsi > 50:
                return 'SELL'
            else:
                return 'HOLD'
        
        except Exception as e:
            return 'HOLD'
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate RSI"""
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
            return 50.0
    
    def _no_signal(self):
        """Return no signal response"""
        return {
            'best_opportunity': None,
            'message': 'No valid trade opportunities found',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_watchlist(self):
        """Get current watchlist"""
        return self.WATCHLIST.copy()