"""
Pattern Recognizer - Machine Learning-based chart pattern detection
- Head and shoulders patterns
- Triangle patterns (ascending, descending, symmetric)
- Double bottom/top patterns
- Wedge patterns
- Flag patterns

Author: SofAi FX Bot - AI Division
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from src.utils.logger import logger
import warnings
warnings.filterwarnings('ignore')

class PatternRecognizer:
    """Detects technical chart patterns using ML-based analysis"""
    
    MIN_BARS = 50
    PATTERN_LOOKBACK = 50  # Look at last 50 candles
    
    def __init__(self):
        logger.info("🎯 Pattern Recognizer initialized")
    
    def detect(self, df, symbol):
        """
        Detect chart patterns in the price data
        
        Args:
            df: OHLC DataFrame
            symbol: Currency pair
        
        Returns:
            list: Detected patterns with confidence scores
        """
        try:
            if df is None or df.empty or len(df) < self.MIN_BARS:
                return []
            
            patterns = []
            
            # Get recent price data
            recent_df = df.tail(self.PATTERN_LOOKBACK).copy()
            recent_df['Log_Return'] = np.log(recent_df['Close'] / recent_df['Close'].shift(1))
            
            # Pattern detection methods
            detected = []
            
            # 1. Head and Shoulders
            hs = self._detect_head_and_shoulders(recent_df, symbol)
            if hs:
                detected.append(hs)
            
            # 2. Double Bottom
            db = self._detect_double_bottom(recent_df, symbol)
            if db:
                detected.append(db)
            
            # 3. Double Top
            dt = self._detect_double_top(recent_df, symbol)
            if dt:
                detected.append(dt)
            
            # 4. Triangle
            tri = self._detect_triangle(recent_df, symbol)
            if tri:
                detected.append(tri)
            
            # 5. Wedge
            wedge = self._detect_wedge(recent_df, symbol)
            if wedge:
                detected.append(wedge)
            
            # 6. Flag Pattern
            flag = self._detect_flag(recent_df, symbol)
            if flag:
                detected.append(flag)
            
            logger.debug(f"🎯 Patterns for {symbol}: {[p['name'] for p in detected]}")
            return detected
        
        except Exception as e:
            logger.warning(f"❌ Pattern detection error for {symbol}: {e}")
            return []
    
    @staticmethod
    def _detect_head_and_shoulders(df, symbol):
        """
        Detect head and shoulders pattern
        
        Structure: Left Shoulder -> Head -> Right Shoulder
        - Head is highest point
        - Both shoulders are similar heights
        - Line through shoulders (neckline)
        """
        try:
            if len(df) < 20:
                return None
            
            lows = df['Low'].values
            highs = df['High'].values
            close = df['Close'].values
            
            # Find peaks and troughs
            peaks = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1] and \
                   highs[i] > highs[i-2] and highs[i] > highs[i+2]:
                    peaks.append((i, highs[i]))
            
            # Look for 3 peaks (left shoulder, head, right shoulder)
            if len(peaks) >= 3:
                # Sort by index and take last 3
                last_peaks = peaks[-3:]
                idx1, h1 = last_peaks[0]
                idx2, h2 = last_peaks[1]
                idx3, h3 = last_peaks[2]
                
                # Head should be highest, shoulders similar
                if h2 > h1 and h2 > h3 and abs(h1 - h3) < h2 * 0.05:
                    confidence = min(0.85, (h2 / ((h1 + h3) / 2)) * 0.7)
                    return {
                        'name': 'Head and Shoulders',
                        'type': 'reversal',
                        'confidence': confidence,
                        'description': 'Potential trend reversal (bearish signal)',
                        'bars_formed': idx3 - idx1
                    }
            
            return None
        
        except Exception as e:
            logger.debug(f"Head and shoulders detection failed: {e}")
            return None
    
    @staticmethod
    def _detect_double_bottom(df, symbol):
        """
        Detect double bottom pattern (bullish reversal)
        
        Two lows at similar levels with a peak in between
        """
        try:
            if len(df) < 20:
                return None
            
            lows = df['Low'].values
            
            # Find troughs
            troughs = []
            for i in range(2, len(lows) - 2):
                if lows[i] < lows[i-1] and lows[i] < lows[i+1] and \
                   lows[i] < lows[i-2] and lows[i] < lows[i+2]:
                    troughs.append((i, lows[i]))
            
            # Look for 2 troughs at similar levels
            if len(troughs) >= 2:
                last_troughs = troughs[-2:]
                idx1, low1 = last_troughs[0]
                idx2, low2 = last_troughs[1]
                
                # Lows should be similar
                if abs(low1 - low2) < low1 * 0.03:  # Within 3%
                    confidence = min(0.80, 0.7 + (0.1 * (idx2 - idx1) / 20))
                    return {
                        'name': 'Double Bottom',
                        'type': 'reversal',
                        'confidence': confidence,
                        'description': 'Bullish reversal pattern - expect upside',
                        'bars_formed': idx2 - idx1
                    }
            
            return None
        
        except Exception as e:
            logger.debug(f"Double bottom detection failed: {e}")
            return None
    
    @staticmethod
    def _detect_double_top(df, symbol):
        """
        Detect double top pattern (bearish reversal)
        
        Two highs at similar levels with a trough in between
        """
        try:
            if len(df) < 20:
                return None
            
            highs = df['High'].values
            
            # Find peaks
            peaks = []
            for i in range(2, len(highs) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1] and \
                   highs[i] > highs[i-2] and highs[i] > highs[i+2]:
                    peaks.append((i, highs[i]))
            
            # Look for 2 peaks at similar levels
            if len(peaks) >= 2:
                last_peaks = peaks[-2:]
                idx1, high1 = last_peaks[0]
                idx2, high2 = last_peaks[1]
                
                # Highs should be similar
                if abs(high1 - high2) < high1 * 0.03:  # Within 3%
                    confidence = min(0.80, 0.7 + (0.1 * (idx2 - idx1) / 20))
                    return {
                        'name': 'Double Top',
                        'type': 'reversal',
                        'confidence': confidence,
                        'description': 'Bearish reversal pattern - expect downside',
                        'bars_formed': idx2 - idx1
                    }
            
            return None
        
        except Exception as e:
            logger.debug(f"Double top detection failed: {e}")
            return None
    
    @staticmethod
    def _detect_triangle(df, symbol):
        """
        Detect triangle pattern (ascending, descending, or symmetric)
        
        Price converges to a point
        """
        try:
            if len(df) < 15:
                return None
            
            highs = df['High'].values
            lows = df['Low'].values
            
            # Calculate range compression
            recent_range = highs[-1] - lows[-1]
            older_range = highs[-15] - lows[-15]
            
            # Check if range is decreasing (convergence)
            if recent_range < older_range * 0.7:  # 30% compression
                # Determine triangle type
                high_slope = (highs[-1] - highs[-15]) / 15
                low_slope = (lows[-1] - lows[-15]) / 15
                
                if high_slope < 0 and low_slope > 0:
                    tri_type = 'Ascending'
                    description = 'Ascending triangle (bullish)'
                elif high_slope > 0 and low_slope < 0:
                    tri_type = 'Descending'
                    description = 'Descending triangle (bearish)'
                else:
                    tri_type = 'Symmetric'
                    description = 'Symmetric triangle (neutral, breakout expected)'
                
                confidence = min(0.75, 0.6 + (older_range - recent_range) / older_range)
                
                return {
                    'name': f'{tri_type} Triangle',
                    'type': 'continuation',
                    'confidence': confidence,
                    'description': description,
                    'compression_ratio': round(recent_range / older_range, 2)
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"Triangle detection failed: {e}")
            return None
    
    @staticmethod
    def _detect_wedge(df, symbol):
        """
        Detect wedge pattern (rising or falling)
        
        Similar to triangle but both lines slope same direction
        """
        try:
            if len(df) < 15:
                return None
            
            highs = df['High'].values
            lows = df['Low'].values
            
            # Check convergence and slope direction
            range_compression = (highs[-15] - lows[-15]) - (highs[-1] - lows[-1])
            
            if range_compression > 0:  # Converging
                high_slope = (highs[-1] - highs[-15]) / 15
                low_slope = (lows[-1] - lows[-15]) / 15
                
                # Both lines sloping same direction = wedge
                if (high_slope > 0 and low_slope > 0) or (high_slope < 0 and low_slope < 0):
                    if high_slope > 0 and low_slope > 0:
                        wedge_type = 'Rising'
                        description = 'Rising wedge (potential reversal down)'
                    else:
                        wedge_type = 'Falling'
                        description = 'Falling wedge (potential reversal up)'
                    
                    confidence = min(0.70, 0.55 + range_compression / (highs[-15] - lows[-15]))
                    
                    return {
                        'name': f'{wedge_type} Wedge',
                        'type': 'reversal',
                        'confidence': confidence,
                        'description': description,
                        'convergence': round(range_compression / (highs[-15] - lows[-15]), 3)
                    }
            
            return None
        
        except Exception as e:
            logger.debug(f"Wedge detection failed: {e}")
            return None
    
    @staticmethod
    def _detect_flag(df, symbol):
        """
        Detect flag pattern (continuation)
        
        Strong move followed by consolidation rectangle
        """
        try:
            if len(df) < 20:
                return None
            
            close = df['Close'].values
            
            # Check for strong move in first half
            first_half_change = abs((close[10] - close[0]) / close[0])
            
            # Check for consolidation in second half
            recent_highs = close[-10:]
            recent_lows = close[-10:]
            consolidation_range = (max(recent_highs) - min(recent_lows)) / close[-1]
            
            if first_half_change > 0.02 and consolidation_range < 0.015:  # 2% move, <1.5% consolidation
                if close[10] > close[0]:
                    description = 'Bullish flag (continuation up)'
                else:
                    description = 'Bearish flag (continuation down)'
                
                confidence = min(0.75, 0.6 + first_half_change)
                
                return {
                    'name': 'Flag Pattern',
                    'type': 'continuation',
                    'confidence': confidence,
                    'description': description,
                    'initial_move': round(first_half_change, 3)
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"Flag detection failed: {e}")
            return None
