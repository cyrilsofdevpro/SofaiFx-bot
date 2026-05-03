import pandas as pd
from src.base_strategy import BaseStrategy, TradeSignal, Signal
from src.utils.logger import logger

class MovingAverageStrategy(BaseStrategy):
    """
    Moving Average Crossover strategy
    
    BUY: When short MA crosses above long MA
    SELL: When short MA crosses below long MA
    """
    
    def __init__(self, short_period=20, long_period=50):
        super().__init__('MA_Strategy')
        self.short_period = short_period
        self.long_period = long_period
    
    def calculate_moving_averages(self, df):
        """Calculate simple moving averages"""
        if df is None or df.empty:
            return None, None
        
        if len(df) < self.long_period:
            return None, None
        
        short_ma = df['Close'].rolling(window=self.short_period).mean()
        long_ma = df['Close'].rolling(window=self.long_period).mean()
        
        return short_ma, long_ma
    
    def analyze(self, df, symbol='UNKNOWN'):
        """
        Analyze using Moving Average crossover
        
        Returns:
            TradeSignal with BUY, SELL, or HOLD
        """
        if df is None or df.empty or len(df) < self.long_period:
            return TradeSignal(symbol, Signal.UNKNOWN, None, reason='Insufficient data')
        
        short_ma, long_ma = self.calculate_moving_averages(df)
        
        if short_ma is None or long_ma is None:
            return TradeSignal(symbol, Signal.UNKNOWN, None, reason='Cannot calculate MAs')
        
        # Get latest values
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]
        prev_short_ma = short_ma.iloc[-2]
        prev_long_ma = long_ma.iloc[-2]
        latest_price = self.get_latest_price(df)
        
        # Detect crossover
        if latest_short_ma > latest_long_ma and prev_short_ma <= prev_long_ma:
            signal_type = Signal.BUY
            reason = f'Golden Cross: {latest_short_ma:.4f} > {latest_long_ma:.4f}'
            confidence = 0.7
        elif latest_short_ma < latest_long_ma and prev_short_ma >= prev_long_ma:
            signal_type = Signal.SELL
            reason = f'Death Cross: {latest_short_ma:.4f} < {latest_long_ma:.4f}'
            confidence = 0.7
        else:
            # Check if price is above/below MAs (trend following)
            if latest_price > latest_short_ma > latest_long_ma:
                signal_type = Signal.BUY
                reason = f'Bullish trend: Price > SMA > LMA'
                confidence = 0.5
            elif latest_price < latest_short_ma < latest_long_ma:
                signal_type = Signal.SELL
                reason = f'Bearish trend: Price < SMA < LMA'
                confidence = 0.5
            else:
                signal_type = Signal.HOLD
                reason = f'No clear MA signal'
                confidence = 0.3
        
        signal = TradeSignal(
            symbol=symbol,
            signal=signal_type,
            price=latest_price,
            confidence=confidence,
            reason=reason
        )
        
        self.log_signal(signal)
        return signal
