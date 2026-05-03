"""
Phase Router: Intelligently routes signal requests to phase-appropriate engine

Routes to:
- Phase 1 (Lite): Ultra-fast engine (<50ms) for high-frequency trading
- Phase 2+ (Full): Full strategy engine (150ms+) for comprehensive analysis

Author: SofAi FX Bot
Version: 1.0.0
"""

from src.signals.lite_engine import LiteSignalEngine
from src.signals.signal_generator import SignalGenerator
from src.signals.phase4_ai_layer import Phase4AILayer
from src.utils.logger import logger
from src.config import config

class PhaseRouter:
    """
    Intelligently routes signal requests based on:
    - ?lite parameter (explicit choice)
    - ?ai parameter (Phase 4 AI Layer)
    - SIGNAL_PHASE config (default behavior)
    - Performance requirements
    """
    
    def __init__(self):
        self.lite_engine = LiteSignalEngine()
        self.full_engine = SignalGenerator()
        self.ai_layer = Phase4AILayer()
        self.phase = getattr(config, 'SIGNAL_PHASE', 1)
        logger.info(f"📊 Phase Router initialized (default phase: {self.phase})")
    
    def get_signal(self, df, symbol, lite=None, ai=None):
        """
        Route to appropriate signal engine
        
        Args:
            df: OHLC DataFrame
            symbol: Currency pair (EURUSD, etc)
            lite: Force Phase 1 Lite (True=lite, False=full)
            ai: Force Phase 4 AI Layer (True=AI, False=other)
        
        Returns:
            dict: Signal with phase-appropriate data
        """
        
        # Explicit parameters take priority
        if ai:
            logger.debug(f"🤖 Routing {symbol} to Phase 4 (AI Layer)")
            return self.ai_layer.get_signal(df, symbol)
        
        if lite:
            logger.debug(f"🚀 Routing {symbol} to Phase 1 (Lite Engine)")
            return self.lite_engine.get_signal(df, symbol)
        
        # Otherwise use config default phase
        if self.phase == 1:
            logger.debug(f"🚀 Routing {symbol} to Phase 1 (Lite Engine)")
            return self.lite_engine.get_signal(df, symbol)
        elif self.phase >= 4:
            logger.debug(f"🤖 Routing {symbol} to Phase 4 (AI Layer)")
            return self.ai_layer.get_signal(df, symbol)
        else:
            logger.debug(f"🔬 Routing {symbol} to Phase {self.phase} (Full Engine)")
            return self.full_engine.generate_signal(df, symbol)
    

    def get_phases_info(self):
        """Get info about available phases"""
        
        return {
            1: {
                'name': 'Lite Engine',
                'description': 'Ultra-fast rule-based signals',
                'response_time_ms': 45,
                'memory_mb': 5,
                'features': ['MA50', 'RSI', 'Momentum'],
                'active': self.phase >= 1
            },
            2: {
                'name': 'Strategy Layer',
                'description': 'RSI + MA filters + Trend detection',
                'response_time_ms': 150,
                'memory_mb': 15,
                'features': ['RSI', 'MA', 'SupportResistance', 'Trend'],
                'active': self.phase >= 2
            },
            3: {
                'name': 'Risk Management',
                'description': 'Position sizing + Loss limits',
                'response_time_ms': 200,
                'memory_mb': 20,
                'features': ['RiskManager', 'LotSizing', 'StopLoss/TakeProfit'],
                'active': self.phase >= 3
            },
            4: {
                'name': 'AI Layer',
                'description': 'Sentiment + Pattern recognition + ML',
                'response_time_ms': 400,
                'memory_mb': 50,
                'features': ['Sentiment', 'PatternRecognition', 'ML', 'ConfidenceBoost'],
                'active': self.phase >= 4
            },
            5: {
                'name': 'User Dashboard',
                'description': 'P&L tracking + Analytics',
                'response_time_ms': 500,
                'memory_mb': 80,
                'features': ['Dashboard', 'P&L', 'Performance', 'History'],
                'active': self.phase >= 5
            }
        }
    
    def switch_phase(self, new_phase):
        """
        Switch to different phase
        
        Note: This updates runtime behavior but doesn't persist
        Use config.py for persistent changes
        """
        if 1 <= new_phase <= 5:
            self.phase = new_phase
            logger.info(f"🔄 Switched to Phase {new_phase}")
            return True
        else:
            logger.warning(f"Invalid phase: {new_phase}")
            return False
