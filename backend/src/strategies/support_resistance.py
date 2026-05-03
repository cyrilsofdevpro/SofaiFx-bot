import pandas as pd
import numpy as np
from src.strategies.base_strategy import BaseStrategy, TradeSignal, Signal
from src.utils.logger import logger

class SupportResistanceStrategy(BaseStrategy):
    """
    Support & Resistance Level identification strategy
    
    Identifies key support (low resistance) and resistance (high resistance) levels
    - BUY when price bounces off support
    - SELL when price bounces off resistance
    """
    
    def __init__(self, lookback_period=50):
        super().__init__('SR_Strategy')
        self.lookback_period = lookback_period
    
    def find_support_resistance(self, df):
        """
        Identify support and resistance levels using local extrema
        
        Returns:
            tuple: (support_level, resistance_level, support_distance, resistance_distance)
        """
        if df is None or len(df) < self.lookback_period:
            return None, None, None, None
        
        recent_data = df.tail(self.lookback_period)
        
        # Find local minima (support) and maxima (resistance)
        lows = recent_data['Low']
        highs = recent_data['High']
        closes = recent_data['Close']
        
        # Support: multiple local lows
        support_level = lows.min()
        
        # Resistance: multiple local highs
        resistance_level = highs.max()
        
        # Current price
        current_price = closes.iloc[-1]
        
        # Distance from support/resistance
        support_distance = current_price - support_level
        resistance_distance = resistance_level - current_price
        
        return support_level, resistance_level, support_distance, resistance_distance
    
    def is_near_level(self, current_price, level, threshold_pct=0.5):
        """Check if price is near a support/resistance level within threshold %"""
        if level is None:
            return False
        distance_pct = abs(current_price - level) / level * 100
        return distance_pct < threshold_pct
    
    def analyze(self, df, symbol='UNKNOWN'):
        """
        Analyze using Support & Resistance levels
        
        Returns:
            TradeSignal based on price proximity to S/R levels
        """
        if df is None or df.empty or len(df) < self.lookback_period:
            return TradeSignal(symbol, Signal.HOLD, None, confidence=0.3, reason='Insufficient data for S/R')
        
        support, resistance, sup_dist, res_dist = self.find_support_resistance(df)
        latest_price = self.get_latest_price(df)
        
        if support is None or resistance is None:
            return TradeSignal(symbol, Signal.HOLD, latest_price, confidence=0.3, reason='Cannot identify S/R levels')
        
        # Calculate price position between support and resistance
        sr_range = resistance - support
        if sr_range == 0:
            ratio = 0.5
        else:
            ratio = (latest_price - support) / sr_range  # 0 = at support, 1 = at resistance
        
        # Determine signal based on position
        if ratio < 0.2:  # Near support
            signal_type = Signal.BUY
            confidence = min(0.2 - ratio, 0.6)  # Higher confidence if closer
            reason = f'Price near Support ({support:.4f}), {sup_dist:.6f} away'
        elif ratio > 0.8:  # Near resistance
            signal_type = Signal.SELL
            confidence = min(ratio - 0.8, 0.6)  # Higher confidence if closer
            reason = f'Price near Resistance ({resistance:.4f}), {res_dist:.6f} away'
        else:
            signal_type = Signal.HOLD
            confidence = 0.3
            reason = f'Price between Support ({support:.4f}) and Resistance ({resistance:.4f})'
        
        signal = TradeSignal(
            symbol=symbol,
            signal=signal_type,
            price=latest_price,
            confidence=confidence,
            reason=reason
        )
        
        self.log_signal(signal)
        return signal
