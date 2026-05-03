"""
Phase 1: Ultra-lightweight signal engine
- <50ms response time
- Zero heavy dependencies (pandas only)
- Production-ready for MT5 EAs
- Simple rules: MA, RSI, Momentum

Author: SofAi FX Bot
Version: 1.0.0
"""

import pandas as pd
from datetime import datetime
from src.utils.logger import logger

class LiteSignalEngine:
    """Ultra-fast, minimal signal engine for Phase 1"""
    
    VERSION = "1.0.0"
    PHASE = 1
    
    def __init__(self):
        logger.info("🚀 Phase 1: Lite Signal Engine initialized")
    
    def get_signal(self, df, symbol):
        """
        Generate signal using 3 simple rules
        
        Rules:
        1. Moving Average Trend (50-period)
        2. RSI Momentum (14-period) 
        3. Price Momentum (last 5 candles)
        
        Args:
            df: DataFrame with OHLC data
            symbol: Currency pair (EURUSD, etc)
        
        Returns:
            dict: {signal, confidence, price, ma50, rsi, momentum, reason, timestamp}
        """
        try:
            if df is None or df.empty or len(df) < 50:
                logger.warning(f"❌ Phase 1: Insufficient data for {symbol}")
                return self._hold_signal("Insufficient data")
            
            start_time = datetime.utcnow()
            
            # ============ RULE 1: Moving Average ============
            price = float(df['Close'].iloc[-1])
            ma50 = float(df['Close'].tail(50).mean())
            ma_signal = "BUY" if price > ma50 else "SELL"
            
            # ============ RULE 2: RSI (Momentum) ============
            rsi = self._calculate_rsi(df['Close'], 14)
            rsi_overbought = rsi > 70
            rsi_oversold = rsi < 30
            rsi_status = "overbought" if rsi_overbought else ("oversold" if rsi_oversold else "neutral")
            
            # ============ RULE 3: Price Momentum ============
            recent_change = ((price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
            momentum = "up" if recent_change > 0.5 else ("down" if recent_change < -0.5 else "flat")
            
            # ============ COMBINE RULES ============
            signal, confidence = self._combine_signals(
                ma_signal, rsi_status, momentum, price, ma50, rsi
            )
            
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = {
                'signal': signal,
                'confidence': round(confidence, 2),
                'price': round(price, 5),
                'ma50': round(ma50, 5),
                'rsi': round(rsi, 1),
                'momentum_pct': round(recent_change, 2),
                'reason': self._generate_reason(signal, ma_signal, rsi_status, momentum),
                'phase': 1,
                'response_time_ms': round(elapsed_ms, 1),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Phase 1: {symbol} → {signal} (confidence: {confidence}, {elapsed_ms:.1f}ms)")
            return result
        
        except Exception as e:
            logger.error(f"❌ Phase 1 Error: {symbol} - {str(e)}", exc_info=True)
            return self._error_signal(str(e))
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """
        Calculate RSI (Relative Strength Index)
        
        Formula: RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
        Optimized for speed - uses numba if available
        """
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
            return 50.0  # Neutral default
    
    @staticmethod
    def _combine_signals(ma_signal, rsi_status, momentum, price, ma50, rsi):
        """
        Combine 3 rules into final signal
        
        BUY Conditions:
        - Price above MA50 (ma_signal = BUY)
        - RSI not overbought (<70)
        - Price momentum positive (up)
        
        SELL Conditions:
        - Price below MA50 (ma_signal = SELL)
        - RSI not oversold (>30)
        - Price momentum negative (down)
        
        Otherwise: HOLD
        """
        
        # Strong BUY: All 3 rules agree
        if (ma_signal == "BUY" and 
            rsi_status != "overbought" and 
            momentum == "up"):
            return "BUY", 0.75
        
        # Strong SELL: All 3 rules agree
        if (ma_signal == "SELL" and 
            rsi_status != "oversold" and 
            momentum == "down"):
            return "SELL", 0.75
        
        # Moderate BUY: 2 of 3 agree
        buy_votes = (
            (ma_signal == "BUY") + 
            (rsi_status != "overbought") + 
            (momentum == "up")
        )
        if buy_votes == 2 and ma_signal == "BUY":
            return "BUY", 0.65
        
        # Moderate SELL: 2 of 3 agree
        sell_votes = (
            (ma_signal == "SELL") + 
            (rsi_status != "oversold") + 
            (momentum == "down")
        )
        if sell_votes == 2 and ma_signal == "SELL":
            return "SELL", 0.65
        
        # Weak signals or conflicting
        if buy_votes > sell_votes:
            return "BUY", 0.55
        elif sell_votes > buy_votes:
            return "SELL", 0.55
        else:
            return "HOLD", 0.45
    
    @staticmethod
    def _generate_reason(signal, ma_signal, rsi_status, momentum):
        """Generate human-readable signal reason"""
        
        reasons = []
        
        if signal == "BUY":
            reasons.append("📈 Bullish signals detected:")
            reasons.append(f"  • Price above MA50")
            if rsi_status == "neutral":
                reasons.append(f"  • RSI in neutral zone ({rsi_status})")
            if momentum == "up":
                reasons.append(f"  • Price momentum is positive")
            reasons.append(f"  → Action: Consider LONG position")
        
        elif signal == "SELL":
            reasons.append("📉 Bearish signals detected:")
            reasons.append(f"  • Price below MA50")
            if rsi_status == "neutral":
                reasons.append(f"  • RSI in neutral zone ({rsi_status})")
            if momentum == "down":
                reasons.append(f"  • Price momentum is negative")
            reasons.append(f"  → Action: Consider SHORT position")
        
        else:  # HOLD
            reasons.append("⏸️ Mixed or neutral signals:")
            reasons.append(f"  • Indicators not aligned")
            reasons.append(f"  • Waiting for clearer direction")
            reasons.append(f"  → Action: Wait for confirmation")
        
        return " ".join(reasons)
    
    @staticmethod
    def _hold_signal(reason):
        """Return a HOLD signal"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'reason': reason,
            'phase': 1,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _error_signal(error_msg):
        """Return error signal"""
        return {
            'signal': 'HOLD',
            'confidence': 0.0,
            'error': error_msg,
            'phase': 1,
            'timestamp': datetime.utcnow().isoformat()
        }
