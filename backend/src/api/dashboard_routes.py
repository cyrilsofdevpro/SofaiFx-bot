"""
Dashboard and API Key Management Endpoints for Phase 5
User System: Multiple API keys, P&L tracking, Performance dashboard

Author: SofAi FX Bot
Version: 1.0.0
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from ..models import db, User, APIKey, Trade
from ..services.pnl_tracker import PnLTracker
from ..utils.logger import logger
import secrets

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

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
            logger.warning(f"Auth error: {e}")
            return jsonify({'error': 'Authentication required'}), 401
    return decorated


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@dashboard_bp.route('/summary', methods=['GET'])
@token_required
def get_dashboard_summary(user_id):
    """Get overall dashboard summary"""
    try:
        user = User.query.get(user_id)
        
        # Get P&L summary
        pnl_summary = pnl_tracker.get_summary(user_id)
        
        # Get 30-day P&L
        pnl_30d = pnl_tracker.get_by_period(user_id, 30)
        
        # Count open trades
        open_trades = Trade.query.filter_by(user_id=user_id, status='OPEN').count()
        
        # Get API keys count
        api_keys_count = APIKey.query.filter_by(user_id=user_id, is_active=True).count()
        
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
            'api': {
                'active_keys': api_keys_count
            },
            'mt5': {
                'connected': user.mt5_connected,
                'account': user.mt5_account_number
            }
        }
        
        logger.info(f"✅ Dashboard summary for user {user_id}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"❌ Dashboard summary error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/pnl/summary', methods=['GET'])
@token_required
def get_pnl_summary(user_id):
    """Get detailed P&L summary"""
    try:
        summary = pnl_tracker.get_summary(user_id)
        
        return jsonify({
            'data': summary,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ P&L summary error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/pnl/by-period', methods=['GET'])
@token_required
def get_pnl_by_period(user_id):
    """Get P&L for specific period"""
    try:
        days = request.args.get('days', 30, type=int)
        period_pnl = pnl_tracker.get_by_period(user_id, days)
        
        return jsonify({
            'data': period_pnl,
            'period_days': days,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ P&L period error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/pnl/by-symbol', methods=['GET'])
@token_required
def get_pnl_by_symbol(user_id):
    """Get P&L breakdown by symbol"""
    try:
        symbols_pnl = pnl_tracker.get_by_symbol(user_id)
        
        return jsonify({
            'data': symbols_pnl,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ P&L by symbol error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/pnl/monthly', methods=['GET'])
@token_required
def get_pnl_monthly(user_id):
    """Get monthly P&L breakdown"""
    try:
        months = request.args.get('months', 12, type=int)
        monthly = pnl_tracker.get_monthly_breakdown(user_id, months)
        
        return jsonify({
            'data': monthly,
            'months': months,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Monthly P&L error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/trades/recent', methods=['GET'])
@token_required
def get_recent_trades(user_id):
    """Get recent closed trades"""
    try:
        limit = request.args.get('limit', 10, type=int)
        trades = pnl_tracker.get_recent_trades(user_id, limit)
        
        return jsonify({
            'data': trades,
            'limit': limit,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Recent trades error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/trades/open', methods=['GET'])
@token_required
def get_open_trades(user_id):
    """Get currently open trades"""
    try:
        trades = pnl_tracker.get_open_trades(user_id)
        
        return jsonify({
            'data': trades,
            'count': len(trades),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"❌ Open trades error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================================

@dashboard_bp.route('/apikeys', methods=['GET'])
@token_required
def list_api_keys(user_id):
    """List all API keys for user"""
    try:
        api_keys = APIKey.query.filter_by(user_id=user_id).all()
        
        keys_data = [key.to_dict(include_key=False) for key in api_keys]
        
        logger.info(f"✅ Listed {len(keys_data)} API keys for user {user_id}")
        return jsonify({
            'data': keys_data,
            'count': len(keys_data)
        }), 200
    
    except Exception as e:
        logger.error(f"❌ API keys list error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/apikeys', methods=['POST'])
@token_required
def create_api_key(user_id):
    """Create new API key"""
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'API key name required'}), 400
        
        # Optional fields
        description = data.get('description', '')
        scope = data.get('scope', 'signal')  # signal, trade, full
        expires_days = data.get('expires_days')  # Optional expiration
        rate_limit = data.get('rate_limit', 100)
        
        # Validate scope
        if scope not in ['signal', 'trade', 'full']:
            return jsonify({'error': 'Invalid scope'}), 400
        
        # Create API key
        api_key = APIKey(
            user_id=user_id,
            key=secrets.token_urlsafe(48),
            name=name,
            description=description,
            scope=scope,
            rate_limit=rate_limit,
            expires_at=(datetime.utcnow() + timedelta(days=expires_days)) if expires_days else None
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        logger.info(f"✅ Created API key '{name}' for user {user_id}")
        return jsonify({
            'data': api_key.to_dict(include_key=True),
            'message': 'API key created successfully. Store it safely!'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ API key creation error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/apikeys/<int:key_id>', methods=['GET'])
@token_required
def get_api_key(user_id, key_id):
    """Get specific API key details"""
    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        return jsonify({
            'data': api_key.to_dict(include_key=False)
        }), 200
    
    except Exception as e:
        logger.error(f"❌ API key fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/apikeys/<int:key_id>', methods=['PUT'])
@token_required
def update_api_key(user_id, key_id):
    """Update API key details"""
    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        data = request.get_json() or {}
        
        # Update fields
        if 'name' in data:
            api_key.name = data['name'].strip()
        if 'description' in data:
            api_key.description = data['description']
        if 'is_active' in data:
            api_key.is_active = bool(data['is_active'])
        if 'rate_limit' in data:
            api_key.rate_limit = int(data['rate_limit'])
        
        db.session.commit()
        
        logger.info(f"✅ Updated API key {key_id} for user {user_id}")
        return jsonify({
            'data': api_key.to_dict(include_key=False),
            'message': 'API key updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ API key update error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/apikeys/<int:key_id>', methods=['DELETE'])
@token_required
def delete_api_key(user_id, key_id):
    """Delete API key"""
    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        db.session.delete(api_key)
        db.session.commit()
        
        logger.info(f"✅ Deleted API key {key_id} for user {user_id}")
        return jsonify({
            'message': 'API key deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ API key deletion error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/apikeys/<int:key_id>/regenerate', methods=['POST'])
@token_required
def regenerate_api_key(user_id, key_id):
    """Regenerate API key"""
    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Generate new key
        old_key = api_key.key
        api_key.key = secrets.token_urlsafe(48)
        api_key.usage_count = 0
        
        db.session.commit()
        
        logger.info(f"✅ Regenerated API key {key_id} for user {user_id}")
        return jsonify({
            'data': api_key.to_dict(include_key=True),
            'message': 'API key regenerated. Old key is now inactive.'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ API key regeneration error: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/apikeys/<int:key_id>/usage', methods=['GET'])
@token_required
def get_api_key_usage(user_id, key_id):
    """Get API key usage statistics"""
    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        return jsonify({
            'data': {
                'key_id': key_id,
                'name': api_key.name,
                'usage_count': api_key.usage_count,
                'rate_limit': api_key.rate_limit,
                'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
                'usage_percent': round((api_key.usage_count / api_key.rate_limit * 100), 2) if api_key.rate_limit else 0
            }
        }), 200
    
    except Exception as e:
        logger.error(f"❌ API key usage error: {e}")
        return jsonify({'error': str(e)}), 500
