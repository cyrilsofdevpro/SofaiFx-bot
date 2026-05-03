"""
Auto-Optimization Engine - Improve decision accuracy over time
- Store trade outcomes (win/loss + context)
- Periodically adjust signal weights
- Simple rule-based tuning
- Save optimized weights per pair

Author: SofAi FX Bot - Optimization Division
Version: 1.0.0
"""

import json
from datetime import datetime
from typing import Dict, List
import numpy as np
from src.utils.logger import logger

class AutoOptimizationEngine:
    """Automatically optimizes signal weights based on performance"""
    
    # Default weights
    DEFAULT_WEIGHTS = {
        'sentiment': 0.50,      # HF Sentiment (50%)
        'technical': 0.25,      # Technical analysis (25%)
        'patterns': 0.15,       # Pattern recognition (15%)
        'news': 0.10            # News filtering (10%)
    }
    
    def __init__(self):
        """Initialize optimization engine"""
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.pair_weights = {}  # Per-pair optimized weights
        self.trade_history = []
        logger.info("[OPT] Auto-Optimization Engine initialized")
    
    def record_trade(self, trade_data: Dict):
        """Record trade with outcome for optimization"""
        try:
            trade_record = {
                'pair': trade_data.get('pair'),
                'entry_date': trade_data.get('entry_date'),
                'exit_date': trade_data.get('exit_date'),
                'pnl': trade_data.get('pnl', 0),
                'win': trade_data.get('pnl', 0) > 0,
                'sentiment_score': trade_data.get('sentiment_score', 0),
                'technical_signal': trade_data.get('technical_signal'),
                'pattern_detected': trade_data.get('pattern_detected', False),
                'news_impact': trade_data.get('news_impact', 'neutral'),
                'confidence': trade_data.get('confidence', 50),
                'recorded_at': datetime.utcnow().isoformat()
            }
            
            self.trade_history.append(trade_record)
            logger.debug(f"[OPT] Trade recorded: {trade_record['pair']} ({'W' if trade_record['win'] else 'L'})")
            
            # Trigger optimization every 50 trades
            if len(self.trade_history) % 50 == 0:
                self.optimize_weights()
        
        except Exception as e:
            logger.error(f"[OPT] Error recording trade: {e}")
    
    def optimize_weights(self, method: str = 'simple'):
        """
        Optimize weights based on trade history
        
        Args:
            method: 'simple' (rule-based) or 'advanced' (Bayesian/RL)
        """
        try:
            if not self.trade_history or len(self.trade_history) < 20:
                logger.warning("[OPT] Not enough trades for optimization")
                return
            
            logger.info(f"[OPT] Running weight optimization ({method} method)")
            
            if method == 'simple':
                self._optimize_simple()
            elif method == 'advanced':
                self._optimize_advanced()
            
            # Also optimize per-pair weights
            self._optimize_pair_weights()
        
        except Exception as e:
            logger.error(f"[OPT] Optimization error: {e}", exc_info=True)
    
    def _optimize_simple(self):
        """Simple rule-based weight optimization"""
        try:
            # Calculate accuracy for each signal type
            winning_trades = [t for t in self.trade_history if t['win']]
            losing_trades = [t for t in self.trade_history if not t['win']]
            
            if not winning_trades or not losing_trades:
                return
            
            # Average accuracy by signal type
            accuracies = {
                'sentiment': self._calculate_accuracy_by_signal('sentiment_score', winning_trades, losing_trades),
                'technical': self._calculate_accuracy_by_signal('technical_signal', winning_trades, losing_trades),
                'patterns': self._calculate_accuracy_by_signal('pattern_detected', winning_trades, losing_trades),
                'news': self._calculate_accuracy_by_signal('news_impact', winning_trades, losing_trades),
            }
            
            # Normalize accuracies to weights
            total_accuracy = sum(accuracies.values())
            if total_accuracy > 0:
                new_weights = {k: v / total_accuracy for k, v in accuracies.items()}
                
                # Smooth adjustment (don't change too much at once)
                alpha = 0.2  # 20% adjustment rate
                self.weights = {
                    k: self.weights[k] * (1 - alpha) + new_weights[k] * alpha
                    for k in self.weights.keys()
                }
                
                logger.info(f"[OPT] Weights optimized: {self.weights}")
        
        except Exception as e:
            logger.error(f"[OPT] Simple optimization error: {e}")
    
    def _optimize_advanced(self):
        """Advanced optimization using Bayesian/RL approach"""
        try:
            # Simplified Bayesian approach: adjust based on win rate
            winning_trades = [t for t in self.trade_history if t['win']]
            total_trades = len(self.trade_history)
            
            if total_trades == 0:
                return
            
            win_rate = len(winning_trades) / total_trades
            
            # If win rate is good, make smaller adjustments
            # If win rate is poor, make larger adjustments
            adjustment_rate = 0.1 if win_rate > 0.6 else 0.3
            
            # Boost signal type that appears more in winning trades
            signal_scores = {}
            for signal_type in ['sentiment', 'technical', 'patterns', 'news']:
                signal_wins = sum(1 for t in winning_trades if self._has_strong_signal(t, signal_type))
                signal_total = sum(1 for t in self.trade_history if self._has_strong_signal(t, signal_type))
                
                if signal_total > 0:
                    signal_scores[signal_type] = signal_wins / signal_total
            
            # Adjust weights
            total_score = sum(signal_scores.values())
            if total_score > 0:
                for signal_type, score in signal_scores.items():
                    boost = (score / total_score) * adjustment_rate
                    self.weights[signal_type] = min(0.7, self.weights[signal_type] + boost)
                
                # Renormalize
                total_weight = sum(self.weights.values())
                self.weights = {k: v / total_weight for k, v in self.weights.items()}
                
                logger.info(f"[OPT] Advanced optimization complete: {self.weights}")
        
        except Exception as e:
            logger.error(f"[OPT] Advanced optimization error: {e}")
    
    def _optimize_pair_weights(self):
        """Optimize weights specifically for each pair"""
        try:
            pairs = set(t['pair'] for t in self.trade_history)
            
            for pair in pairs:
                pair_trades = [t for t in self.trade_history if t['pair'] == pair]
                
                if len(pair_trades) < 10:
                    continue
                
                # Calculate pair-specific accuracy
                winning = [t for t in pair_trades if t['win']]
                accuracy = len(winning) / len(pair_trades)
                
                # Create pair-specific weights if accuracy deviates from baseline
                if accuracy < 0.4:  # Poor performance
                    # Try different weight distribution
                    self.pair_weights[pair] = {
                        'sentiment': 0.60,   # Boost sentiment
                        'technical': 0.20,
                        'patterns': 0.15,
                        'news': 0.05         # Reduce news
                    }
                    logger.info(f"[OPT] Created optimized weights for {pair} (accuracy: {accuracy:.1%})")
        
        except Exception as e:
            logger.error(f"[OPT] Pair optimization error: {e}")
    
    def _calculate_accuracy_by_signal(self, signal_type: str, winning_trades: List[Dict], losing_trades: List[Dict]) -> float:
        """Calculate accuracy for a specific signal type"""
        try:
            # Count how many winning trades had strong signal
            # and losing trades had weak signal
            
            win_strength = sum(self._get_signal_strength(t, signal_type) for t in winning_trades) / len(winning_trades) if winning_trades else 0
            loss_strength = sum(self._get_signal_strength(t, signal_type) for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            # Accuracy is the difference
            accuracy = win_strength - loss_strength
            return max(0, accuracy)  # Ensure non-negative
        
        except Exception as e:
            logger.error(f"[OPT] Signal accuracy calc error: {e}")
            return 0.25
    
    def _get_signal_strength(self, trade: Dict, signal_type: str) -> float:
        """Get signal strength (0-1) for a trade"""
        if signal_type == 'sentiment':
            # Sentiment score -1 to 1, convert to 0-1
            return abs(trade.get('sentiment_score', 0)) / 1.0
        elif signal_type == 'technical':
            # Whether technical signal matched outcome
            return 1.0 if trade.get('technical_signal') else 0.5
        elif signal_type == 'patterns':
            # Whether pattern detected
            return 1.0 if trade.get('pattern_detected') else 0.3
        elif signal_type == 'news':
            # News impact strength
            news = trade.get('news_impact', 'neutral').lower()
            return {'positive': 0.8, 'negative': 0.2, 'neutral': 0.5}.get(news, 0.5)
        
        return 0.5
    
    def _has_strong_signal(self, trade: Dict, signal_type: str) -> bool:
        """Check if trade has strong signal for type"""
        return self._get_signal_strength(trade, signal_type) > 0.6
    
    def get_current_weights(self, pair: str = None) -> Dict:
        """Get current weights (pair-specific or global)"""
        if pair and pair in self.pair_weights:
            return self.pair_weights[pair]
        return self.weights
    
    def get_optimization_stats(self) -> Dict:
        """Get optimization statistics"""
        if not self.trade_history:
            return {}
        
        winning = sum(1 for t in self.trade_history if t['win'])
        total = len(self.trade_history)
        
        return {
            'trades_recorded': total,
            'winning_trades': winning,
            'win_rate': round((winning / total * 100), 2),
            'current_weights': self.weights,
            'pair_specific_weights': len(self.pair_weights),
            'last_optimization': self.trade_history[-1]['recorded_at'] if self.trade_history else None
        }
    
    def save_weights(self, filepath: str):
        """Save optimized weights to file"""
        try:
            data = {
                'global_weights': self.weights,
                'pair_weights': self.pair_weights,
                'saved_at': datetime.utcnow().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"[OPT] Weights saved to {filepath}")
        
        except Exception as e:
            logger.error(f"[OPT] Error saving weights: {e}")
    
    def load_weights(self, filepath: str):
        """Load optimized weights from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.weights = data.get('global_weights', self.DEFAULT_WEIGHTS)
            self.pair_weights = data.get('pair_weights', {})
            
            logger.info(f"[OPT] Weights loaded from {filepath}")
        
        except Exception as e:
            logger.error(f"[OPT] Error loading weights: {e}")
