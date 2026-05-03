"""
Pair recommendations engine - analyzes signal history and recommends pairs
"""

from datetime import datetime, timedelta
from src.models import Signal
import json


class PairRecommendationEngine:
    """Generates AI recommendations for which pairs to analyze"""
    
    def __init__(self):
        self.pair_trends = {}
    
    def get_pair_stats(self, user_id: int, hours_lookback: int = 24) -> dict:
        """
        Analyze recent signals for a user and return pair statistics
        
        Args:
            user_id: User ID to analyze
            hours_lookback: How many hours back to look (default 24)
        
        Returns:
            Dictionary with pair statistics and recommendations
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)
        
        # Get recent signals
        recent_signals = Signal.query.filter(
            Signal.user_id == user_id,
            Signal.created_at >= cutoff_time
        ).all()
        
        # Aggregate by pair
        pair_data = {}
        for signal in recent_signals:
            if signal.symbol not in pair_data:
                pair_data[signal.symbol] = {
                    'total': 0,
                    'buy': 0,
                    'sell': 0,
                    'hold': 0,
                    'avg_confidence': 0,
                    'confidences': []
                }
            
            pair_data[signal.symbol]['total'] += 1
            pair_data[signal.symbol]['confidences'].append(signal.confidence)
            
            if signal.signal_type == 'BUY':
                pair_data[signal.symbol]['buy'] += 1
            elif signal.signal_type == 'SELL':
                pair_data[signal.symbol]['sell'] += 1
            else:  # HOLD
                pair_data[signal.symbol]['hold'] += 1
        
        # Calculate stats and recommendations
        recommendations = []
        
        for symbol, data in pair_data.items():
            if data['total'] == 0:
                continue
            
            # Calculate average confidence
            avg_conf = sum(data['confidences']) / len(data['confidences'])
            data['avg_confidence'] = round(avg_conf, 2)
            
            # Determine trend
            if data['buy'] > data['sell'] and data['buy'] > data['hold']:
                trend = "trending_up"
                emoji = "📈"
                description = f"{data['buy']} BUY signals recently - trending up!"
            elif data['sell'] > data['buy'] and data['sell'] > data['hold']:
                trend = "trending_down"
                emoji = "📉"
                description = f"{data['sell']} SELL signals recently - trending down!"
            elif data['buy'] > 0 and data['sell'] > 0:
                trend = "consolidating"
                emoji = "➡️"
                description = f"Mix of signals - consolidating"
            else:
                trend = "low_volatility"
                emoji = "😴"
                description = f"Mostly HOLD - low volatility"
            
            recommendation = {
                'symbol': symbol,
                'trend': trend,
                'emoji': emoji,
                'description': description,
                'full_message': f"{emoji} {symbol}: {description}",
                'stats': {
                    'total_signals': data['total'],
                    'buy_signals': data['buy'],
                    'sell_signals': data['sell'],
                    'hold_signals': data['hold'],
                    'avg_confidence': f"{data['avg_confidence']:.0%}",
                    'hours_lookback': hours_lookback
                }
            }
            
            recommendations.append(recommendation)
        
        # Sort by number of signals (most active first)
        recommendations.sort(key=lambda x: x['stats']['total_signals'], reverse=True)
        
        return {
            'recommendations': recommendations,
            'total_pairs_analyzed': len(recommendations),
            'period_hours': hours_lookback,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_top_recommendations(self, user_id: int, top_n: int = 5) -> list:
        """Get top N pair recommendations"""
        stats = self.get_pair_stats(user_id)
        return stats['recommendations'][:top_n]
    
    def format_recommendations_text(self, recommendations: list) -> str:
        """Format recommendations as friendly text"""
        if not recommendations:
            return "No signals generated yet. Start analyzing pairs!"
        
        text = "📊 **Pair Recommendations**\n\n"
        for rec in recommendations:
            text += f"{rec['full_message']}\n"
            stats = rec['stats']
            text += f"   • {stats['buy_signals']} BUY | {stats['sell_signals']} SELL | {stats['hold_signals']} HOLD\n"
            text += f"   • Avg Confidence: {stats['avg_confidence']}\n\n"
        
        return text


# Singleton instance
recommendation_engine = PairRecommendationEngine()
