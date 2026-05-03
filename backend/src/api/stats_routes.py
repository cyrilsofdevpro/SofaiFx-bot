"""
Stats API Endpoints
Provides /api/stats/summary endpoint that wraps dashboard data
for backward compatibility with frontend

Author: SofAi FX Bot
Version: 1.0.0
"""

from flask import Blueprint, jsonify
from functools import wraps
from src.models import User, Trade, Signal
from src.services.pnl_tracker import PnLTracker

# Create blueprint
stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

# P&L tracker instance
pnl_tracker = PnLTracker()


def token_required(f):
    """JWT token required decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'Invalid user'}), 401
            return f(user_id, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return decorated


# ============================================================================
# STATS ENDPOINTS
# ============================================================================

@stats_bp.route('/summary', methods=['GET'])
@token_required
def get_stats_summary(user_id):
    """Get stats summary - wraps dashboard summary for frontend compatibility"""
    try:
        user = User.query.get(user_id)
        
        # Get P&L summary
        pnl_summary = pnl_tracker.get_summary(user_id)
        
        # Get 30-day P&L
        pnl_30d = pnl_tracker.get_by_period(user_id, 30)
        
        # Count open trades
        open_trades = Trade.query.filter_by(user_id=user_id, status='OPEN').count()
        
        # Get recent trades
        recent_trades = Trade.query.filter_by(user_id=user_id).order_by(Trade.created_at.desc()).limit(10).all()
        
        response = {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'plan': user.plan,
                'last_active': user.last_active.isoformat() if user.last_active else None
            },
            'pnl': {
                'summary': pnl_summary,
                'last_30_days': pnl_30d
            },
            'trades': {
                'open': open_trades,
                'total': pnl_summary['total_trades']
            },
            'recent_trades': [{
                'id': t.id,
                'pair': t.pair,
                'type': t.type,
                'status': t.status,
                'profit': float(t.profit) if t.profit else 0,
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in recent_trades]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/signals-breakdown', methods=['GET'])
@token_required
def get_signals_breakdown(user_id):
    """Get user's signal breakdown - total, buy, sell counts"""
    try:
        user = User.query.get(user_id)
        
        # Get total signals
        total_signals = Signal.query.filter_by(user_id=user_id).count()
        
        # Get buy signals
        buy_signals = Signal.query.filter_by(user_id=user_id, signal_type='BUY').count()
        
        # Get sell signals
        sell_signals = Signal.query.filter_by(user_id=user_id, signal_type='SELL').count()
        
        # Get hold signals
        hold_signals = Signal.query.filter_by(user_id=user_id, signal_type='HOLD').count()
        
        response = {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            },
            'signals': {
                'total': total_signals,
                'buy': buy_signals,
                'sell': sell_signals,
                'hold': hold_signals
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500