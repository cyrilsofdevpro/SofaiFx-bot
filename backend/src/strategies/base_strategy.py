from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from src.utils.logger import logger

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    UNKNOWN = "UNKNOWN"

class TradeSignal:
    def __init__(self, symbol, signal, price, timestamp=None, confidence=0.5, reason=""):
        self.symbol = symbol
        self.signal = signal  # Signal.BUY, Signal.SELL, Signal.HOLD
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.confidence = confidence  # 0-1, higher is more confident
        self.reason = reason
    
    def __repr__(self):
        return f"TradeSignal({self.symbol}, {self.signal.value}, {self.price}, confidence={self.confidence:.2f})"
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'signal': self.signal.value,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'reason': self.reason
        }

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name):
        self.name = name
        self.last_signal = None
    
    @abstractmethod
    def analyze(self, df):
        """
        Analyze market data and return trading signal
        
        Args:
            df: pandas DataFrame with OHLC data
        
        Returns:
            TradeSignal object
        """
        pass
    
    def get_latest_price(self, df):
        """Get the latest close price"""
        if df is None or df.empty:
            return None
        return df['Close'].iloc[-1]
    
    def log_signal(self, signal):
        """Log the generated signal"""
        if signal.signal != Signal.HOLD:
            logger.info(f'[{self.name}] {signal}')
        self.last_signal = signal
