from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.moving_average import MovingAverageStrategy
from src.strategies.support_resistance import SupportResistanceStrategy
from src.strategies.base_strategy import Signal
from src.utils.logger import logger
from src.predictions.price_predictor import price_predictor
from src.filters.smart_filters import smart_filters
from datetime import datetime

class SignalGenerator:
    """
    Combines multiple strategies to generate robust trading signals
    - RSI (momentum indicator)
    - Moving Averages (trend indicator)
    - Support & Resistance (price levels)
    """
    
    # Strategy weights
    WEIGHTS = {
        'rsi': 0.35,           # Momentum - 35%
        'ma': 0.35,            # Trend - 35%
        'sr': 0.30             # Price levels - 30%
    }
    
    # Minimum agreement threshold
    MIN_AGREEMENT = 2  # At least 2 strategies must agree
    
    def __init__(self):
        self.rsi_strategy = RSIStrategy()
        self.ma_strategy = MovingAverageStrategy()
        self.sr_strategy = SupportResistanceStrategy()
        self.signal_history = []
    
    def generate_signal(self, df, symbol):
        """
        Generate signal by combining all three strategies with weighted voting
        Includes AI predictions and smart filters for enhanced decision-making
        
        Only generates strong signals when strategies agree
        Returns: CombinedSignal with all indicator details, predictions, and filter results
        """
        if df is None or df.empty:
            logger.warning(f'No data available for {symbol}')
            return None
        
        # Get signals from all three strategies
        rsi_signal = self.rsi_strategy.analyze(df, symbol)
        ma_signal = self.ma_strategy.analyze(df, symbol)
        sr_signal = self.sr_strategy.analyze(df, symbol)
        
        # Weighted voting mechanism
        buy_weight = 0.0
        sell_weight = 0.0
        total_weight = 0.0
        
        # RSI contribution (35%)
        if rsi_signal.signal == Signal.BUY:
            buy_weight += rsi_signal.confidence * self.WEIGHTS['rsi']
        elif rsi_signal.signal == Signal.SELL:
            sell_weight += rsi_signal.confidence * self.WEIGHTS['rsi']
        
        # Moving Average contribution (35%)
        if ma_signal.signal == Signal.BUY:
            buy_weight += ma_signal.confidence * self.WEIGHTS['ma']
        elif ma_signal.signal == Signal.SELL:
            sell_weight += ma_signal.confidence * self.WEIGHTS['ma']
        
        # Support & Resistance contribution (30%)
        if sr_signal.signal == Signal.BUY:
            buy_weight += sr_signal.confidence * self.WEIGHTS['sr']
        elif sr_signal.signal == Signal.SELL:
            sell_weight += sr_signal.confidence * self.WEIGHTS['sr']
        
        total_weight = buy_weight + sell_weight
        
        # Count agreement (how many indicators point in same direction)
        buy_votes = sum([
            1 for sig in [rsi_signal, ma_signal, sr_signal] 
            if sig.signal == Signal.BUY
        ])
        sell_votes = sum([
            1 for sig in [rsi_signal, ma_signal, sr_signal] 
            if sig.signal == Signal.SELL
        ])
        
        # Determine final signal based on weighted votes
        if buy_weight > sell_weight and buy_votes >= self.MIN_AGREEMENT:
            final_signal = Signal.BUY
            confidence = min(buy_weight, 1.0)
            reason = f'Strong bullish: RSI+MA+SR aligned ({buy_votes} indicators agree)'
        elif sell_weight > buy_weight and sell_votes >= self.MIN_AGREEMENT:
            final_signal = Signal.SELL
            confidence = min(sell_weight, 1.0)
            reason = f'Strong bearish: RSI+MA+SR aligned ({sell_votes} indicators agree)'
        elif total_weight > 0:
            # Partial agreement - weaker signal
            if buy_weight > sell_weight:
                final_signal = Signal.BUY
                confidence = min(buy_weight / 2, 0.65)  # Cap confidence for partial agreement
                reason = f'Moderate bullish: {buy_votes} indicators bullish'
            else:
                final_signal = Signal.SELL
                confidence = min(sell_weight / 2, 0.65)
                reason = f'Moderate bearish: {sell_votes} indicators bearish'
        else:
            final_signal = Signal.HOLD
            confidence = 0.3
            reason = 'Indicators mixed or neutral - waiting for clearer signals'
        
        current_price = rsi_signal.price if rsi_signal.price else df['Close'].iloc[-1]
        
        # Get AI prediction
        ai_prediction = self._get_ai_prediction(df, symbol)
        
        # Apply smart filters
        filter_results = smart_filters.apply_all_filters(df, {
            'signal': final_signal,
            'signal_quality': {
                'total_indicators': 3,
                'agreeing_indicators': max(buy_votes, sell_votes)
            }
        }, symbol)
        
        # Enhance confidence with AI prediction agreement
        final_confidence = self._blend_confidence(
            confidence, 
            ai_prediction.get('confidence', 0.5),
            final_signal,
            ai_prediction.get('direction')
        )
        
        # Calculate Stop Loss and Take Profit
        stop_loss, take_profit = self._calculate_sl_tp(current_price, final_signal)
        
        signal = CombinedSignal(
            symbol=symbol,
            signal=final_signal,
            price=current_price,
            confidence=final_confidence,
            reason=reason,
            rsi_signal=rsi_signal,
            ma_signal=ma_signal,
            sr_signal=sr_signal,
            ai_prediction=ai_prediction,
            filter_results=filter_results,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.signal_history.append(signal)
        
        trade_status = "ALLOWED" if filter_results.get('is_trade_allowed', True) else "BLOCKED"
        logger.info(f'[Combined] {signal.symbol}: {signal.signal.value} (Conf: {final_confidence:.2f}) [{trade_status}] - {signal.reason}')
        
        return signal
    
    def _calculate_sl_tp(self, price, signal):
        """
        Calculate Stop Loss and Take Profit based on signal direction.
        Uses 1:2 risk-reward ratio by default.
        """
        if signal == Signal.HOLD or price is None:
            return None, None
        
        # Risk-reward ratio
        rr_ratio = 2.0
        
        # Calculate SL/TP based on signal direction
        # For forex, we use pips. Typical SL/TP distance: 20-50 pips
        pip_distance = 0.0020  # 20 pips for EURUSD (0.0001 * 20)
        
        if signal == Signal.BUY:
            # Stop loss below entry
            stop_loss = price - pip_distance
            # Take profit above entry (1:2 ratio)
            take_profit = price + (pip_distance * rr_ratio)
        elif signal == Signal.SELL:
            # Stop loss above entry
            stop_loss = price + pip_distance
            # Take profit below entry (1:2 ratio)
            take_profit = price - (pip_distance * rr_ratio)
        else:
            return None, None
        
        return round(stop_loss, 5), round(take_profit, 5)
    
    def _get_ai_prediction(self, df, symbol):
        """Get AI-based price prediction"""
        try:
            # Try to load pre-trained model
            if not price_predictor.is_trained:
                price_predictor.load_models(symbol.replace('/', '_'))
            
            # Make prediction
            if price_predictor.is_trained:
                prediction = price_predictor.predict(df)
                logger.debug(f"AI Prediction for {symbol}: {prediction['direction']} ({prediction['confidence']:.2%})")
                return prediction
            else:
                # Train on current data if no model exists
                if len(df) >= 20:
                    logger.info(f"Training AI model for {symbol}")
                    price_predictor.train(df, symbol.replace('/', '_'))
                    prediction = price_predictor.predict(df)
                    return prediction
                else:
                    return {
                        'direction': 'NEUTRAL',
                        'confidence': 0.0,
                        'ensemble_probability': 0.5
                    }
        except Exception as e:
            logger.warning(f"AI prediction unavailable: {e}")
            return {
                'direction': 'NEUTRAL',
                'confidence': 0.0,
                'ensemble_probability': 0.5
            }
    
    def _blend_confidence(self, technical_confidence, ai_confidence, signal, ai_direction):
        """Blend technical and AI confidence scores"""
        try:
            signal_str = signal.value if hasattr(signal, 'value') else str(signal)
            
            # If AI agrees with technical signal, boost confidence
            if (signal_str == 'BUY' and ai_direction == 'UP') or \
               (signal_str == 'SELL' and ai_direction == 'DOWN'):
                # Increase confidence by blending
                blended = (technical_confidence * 0.6) + (ai_confidence * 0.4)
                blended = min(blended * 1.1, 1.0)  # Slight boost for agreement
            elif (signal_str == 'BUY' and ai_direction == 'DOWN') or \
                 (signal_str == 'SELL' and ai_direction == 'UP'):
                # Reduce confidence if AI disagrees
                blended = (technical_confidence * 0.6) + ((1 - ai_confidence) * 0.4)
                blended = max(blended * 0.8, 0.2)  # Reduce for disagreement
            else:
                # Neutral AI prediction - stick with technical
                blended = technical_confidence
            
            return min(max(blended, 0.0), 1.0)  # Clamp between 0 and 1
        except Exception as e:
            logger.debug(f"Error blending confidence: {e}")
            return technical_confidence


class CombinedSignal:
    """Result of combining all three strategy signals"""
    
    def __init__(self, symbol, signal, price, confidence, reason, rsi_signal=None, ma_signal=None, sr_signal=None,
                 ai_prediction=None, filter_results=None, stop_loss=None, take_profit=None):
        self.symbol = symbol
        self.signal = signal
        self.price = price
        self.confidence = confidence
        self.reason = reason
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timestamp = datetime.now()
        self.rsi_signal = rsi_signal
        self.ma_signal = ma_signal
        self.sr_signal = sr_signal
        self.ai_prediction = ai_prediction or {}
        self.filter_results = filter_results or {}
    
    def __repr__(self):
        return f"CombinedSignal({self.symbol}, {self.signal.value}, confidence={self.confidence:.2f})"
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'signal': self.signal.value,
            'price': self.price,
            'confidence': self.confidence,
            'reason': self.reason,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'timestamp': self.timestamp.isoformat(),
            'rsi_signal': self.rsi_signal.to_dict() if self.rsi_signal else None,
            'ma_signal': self.ma_signal.to_dict() if self.ma_signal else None,
            'sr_signal': self.sr_signal.to_dict() if self.sr_signal else None,
            'ai_prediction': self.ai_prediction if self.ai_prediction else {},
            'filter_results': self.filter_results if self.filter_results else {},
            'signal_quality': {
                'total_indicators': 3,
                'agreeing_indicators': self._count_agreeing_indicators(),
                'trade_allowed': self.filter_results.get('is_trade_allowed', True) if self.filter_results else True
            }
        }
    
    def _count_agreeing_indicators(self):
        """Count how many indicators agree with final signal"""
        if self.signal == Signal.HOLD:
            return 0
        
        agreeing = 0
        target_signal = self.signal
        
        for sig in [self.rsi_signal, self.ma_signal, self.sr_signal]:
            if sig and sig.signal == target_signal:
                agreeing += 1
        
        return agreeing
