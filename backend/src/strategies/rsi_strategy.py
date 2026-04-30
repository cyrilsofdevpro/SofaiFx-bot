import pandas as pd
from .base_strategy import BaseStrategy, TradeSignal, Signal
from ..config import config
from ..utils.logger import logger

class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) based trading strategy
    
    RSI > 70: Overbought (potential SELL)
    RSI < 30: Oversold (potential BUY)
    """
    
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__('RSI_Strategy')
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate_rsi(self, df, period=None):
        """Calculate Relative Strength Index"""
        if period is None:
            period = self.period
        
        if df is None or len(df) < period:
            return None
        
        # Calculate price changes
        delta = df['Close'].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def analyze(self, df, symbol='UNKNOWN'):
        """
        Analyze using RSI indicator
        
        Returns:
            TradeSignal with BUY, SELL, or HOLD
        """
        if df is None or df.empty or len(df) < self.period:
            return TradeSignal(symbol, Signal.UNKNOWN, None, reason='Insufficient data')
        
        # Calculate RSI
        rsi = self.calculate_rsi(df)
        
        if rsi is None or rsi.isna().all():
            return TradeSignal(symbol, Signal.UNKNOWN, None, reason='Cannot calculate RSI')
        
        latest_rsi = rsi.iloc[-1]
        latest_price = self.get_latest_price(df)
        
        # Determine signal
        if latest_rsi > self.overbought:
            signal_type = Signal.SELL
            confidence = min((latest_rsi - self.overbought) / 30, 1.0)  # Max 1.0
            reason = f'RSI ({latest_rsi:.2f}) > Overbought ({self.overbought})'
        elif latest_rsi < self.oversold:
            signal_type = Signal.BUY
            confidence = min((self.oversold - latest_rsi) / 30, 1.0)  # Max 1.0
            reason = f'RSI ({latest_rsi:.2f}) < Oversold ({self.oversold})'
        else:
            signal_type = Signal.HOLD
            confidence = 0.5
            reason = f'RSI ({latest_rsi:.2f}) in neutral zone'
        
        signal = TradeSignal(
            symbol=symbol,
            signal=signal_type,
            price=latest_price,
            confidence=confidence,
            reason=reason
        )
        
        self.log_signal(signal)
        return signal
