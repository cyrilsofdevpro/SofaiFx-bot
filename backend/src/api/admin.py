"""
Admin Dashboard API routes for SofAi FX
Requires admin role for all endpoints
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta
from ..models import db, User, Signal
from ..utils.logger import logger
from ..config import config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ===== Admin Authorization Decorator =====
def require_admin(f):
    """Decorator to require admin role"""
    from functools import wraps
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            logger.warning(f'Unauthorized admin access attempt by user {user_id}')
            return jsonify({'error': 'Admin access required'}), 403
        
        # Update last active
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        return f(*args, **kwargs)
    
    return decorated_function


# ===== 1. OVERVIEW STATS =====
@admin_bp.route('/stats/overview', methods=['GET'])
@require_admin
def get_overview_stats():
    """Get main overview statistics"""
    try:
        # Current stats
        total_users = User.query.count()
        active_users_24h = User.query.filter(
            User.last_active >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        total_signals = Signal.query.count()
        
        # Signals today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        signals_today = Signal.query.filter(
            Signal.created_at >= today_start
        ).count()
        
        # Signal breakdown today
        buy_signals_today = Signal.query.filter(
            Signal.created_at >= today_start,
            Signal.signal_type == 'BUY'
        ).count()
        sell_signals_today = Signal.query.filter(
            Signal.created_at >= today_start,
            Signal.signal_type == 'SELL'
        ).count()
        
        # Average confidence today
        avg_confidence_today = db.session.query(
            func.avg(Signal.confidence)
        ).filter(
            Signal.created_at >= today_start
        ).scalar() or 0
        
        # API Status (mock - can integrate with real checks)
        api_status = {
            'twelvedata': 'operational',
            'alpha_vantage': 'operational',
            'telegram': 'operational',
            'email': 'operational'
        }
        
        # Scheduler status
        scheduler_status = 'running'  # Can be enhanced
        
        return jsonify({
            'overview': {
                'total_users': total_users,
                'active_users_24h': active_users_24h,
                'total_signals_all_time': total_signals,
                'signals_today': signals_today,
                'buy_signals_today': buy_signals_today,
                'sell_signals_today': sell_signals_today,
                'avg_confidence_today': round(float(avg_confidence_today) * 100, 2),
                'buy_sell_ratio': round(buy_signals_today / max(sell_signals_today, 1), 2)
            },
            'system_status': {
                'api_status': api_status,
                'scheduler': scheduler_status,
                'database': 'connected'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f'Error fetching overview stats: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 2. USER MANAGEMENT =====
@admin_bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get list of all users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        users_data = []
        for user in pagination.items:
            signal_count = Signal.query.filter_by(user_id=user.id).count()
            users_data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'plan': user.plan,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat(),
                'last_active': user.last_active.isoformat() if user.last_active else None,
                'signal_count': signal_count
            })
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
        }), 200
    except Exception as e:
        logger.error(f'Error fetching users: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@require_admin
def toggle_user_active(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        logger.info(f'Admin toggled user {user_id} active status to {user.is_active}')
        
        return jsonify({
            'message': 'User status updated',
            'user_id': user_id,
            'is_active': user.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error toggling user: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@require_admin
def toggle_user_admin(user_id):
    """Toggle user admin status"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Prevent self-demotion (can add additional checks here)
        # if current_user_id == user_id:
        #     return jsonify({'error': 'Cannot modify your own admin status'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_admin = not user.is_admin
        db.session.commit()
        
        logger.info(f'Admin toggled user {user_id} admin status to {user.is_admin}')
        
        return jsonify({
            'message': 'User admin status updated',
            'user_id': user_id,
            'is_admin': user.is_admin
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error toggling admin: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/change-plan', methods=['POST'])
@require_admin
def change_user_plan(user_id):
    """Change user subscription plan"""
    try:
        data = request.json
        new_plan = data.get('plan')
        
        if new_plan not in ['free', 'premium', 'enterprise']:
            return jsonify({'error': 'Invalid plan'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        old_plan = user.plan
        user.plan = new_plan
        db.session.commit()
        
        logger.info(f'Admin changed user {user_id} plan from {old_plan} to {new_plan}')
        
        return jsonify({
            'message': 'User plan updated',
            'user_id': user_id,
            'old_plan': old_plan,
            'new_plan': new_plan
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error changing plan: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/signals', methods=['GET'])
@require_admin
def get_user_signals(user_id):
    """Get all signals for a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        limit = request.args.get('limit', 20, type=int)
        signals = Signal.query.filter_by(user_id=user_id).order_by(
            Signal.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'user': user.to_dict(),
            'signals': [s.to_dict() for s in signals],
            'signal_count': len(signals)
        }), 200
    except Exception as e:
        logger.error(f'Error fetching user signals: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 3. SIGNALS ANALYTICS =====
@admin_bp.route('/signals/analytics', methods=['GET'])
@require_admin
def get_signal_analytics():
    """Get comprehensive signal analytics"""
    try:
        # Total counts
        total_signals = Signal.query.count()
        
        # Signal type breakdown
        buy_count = Signal.query.filter_by(signal_type='BUY').count()
        sell_count = Signal.query.filter_by(signal_type='SELL').count()
        hold_count = Signal.query.filter_by(signal_type='HOLD').count()
        
        # Average confidence by signal type
        avg_confidence_buy = db.session.query(
            func.avg(Signal.confidence)
        ).filter_by(signal_type='BUY').scalar() or 0
        
        avg_confidence_sell = db.session.query(
            func.avg(Signal.confidence)
        ).filter_by(signal_type='SELL').scalar() or 0
        
        # Most active pairs
        pair_stats = db.session.query(
            Signal.symbol,
            func.count(Signal.id).label('count'),
            func.avg(Signal.confidence).label('avg_confidence')
        ).group_by(Signal.symbol).order_by(
            func.count(Signal.id).desc()
        ).limit(20).all()
        
        pairs_data = []
        for symbol, count, avg_conf in pair_stats:
            pairs_data.append({
                'symbol': symbol,
                'signal_count': count,
                'avg_confidence': round(float(avg_conf) * 100, 2) if avg_conf else 0
            })
        
        # Timeline data (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_signals = db.session.query(
            func.date(Signal.created_at).label('date'),
            func.count(Signal.id).label('count')
        ).filter(Signal.created_at >= thirty_days_ago).group_by(
            func.date(Signal.created_at)
        ).order_by('date').all()
        
        timeline_data = []
        for date, count in daily_signals:
            timeline_data.append({
                'date': str(date),
                'signals': count
            })
        
        return jsonify({
            'summary': {
                'total_signals': total_signals,
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'hold_signals': hold_count,
                'buy_sell_ratio': round(buy_count / max(sell_count, 1), 2)
            },
            'confidence': {
                'avg_buy': round(float(avg_confidence_buy) * 100, 2),
                'avg_sell': round(float(avg_confidence_sell) * 100, 2)
            },
            'top_pairs': pairs_data,
            'timeline_30d': timeline_data
        }), 200
    except Exception as e:
        logger.error(f'Error fetching signal analytics: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 4. SYSTEM MONITORING =====
@admin_bp.route('/system/status', methods=['GET'])
@require_admin
def get_system_status():
    """Get system health status"""
    try:
        import os
        from pathlib import Path
        
        # Database status
        db_path = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')),
            'sofai_fx.db'
        )
        db_exists = os.path.exists(db_path)
        db_size = os.path.getsize(db_path) if db_exists else 0
        
        # Get error logs (if available)
        logs_dir = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')),
            'logs'
        )
        recent_errors = []
        if os.path.exists(logs_dir):
            log_files = sorted(Path(logs_dir).glob('*.log'), key=os.path.getmtime, reverse=True)
            for log_file in log_files[:3]:  # Last 3 logs
                recent_errors.append({
                    'file': log_file.name,
                    'size': os.path.getsize(log_file),
                    'modified': datetime.fromtimestamp(os.path.getmtime(log_file)).isoformat()
                })
        
        return jsonify({
            'system': {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'operational',
                'uptime': 'running'
            },
            'database': {
                'connected': True,
                'size_bytes': db_size,
                'size_mb': round(db_size / 1024 / 1024, 2),
                'users': User.query.count(),
                'signals': Signal.query.count()
            },
            'logs': recent_errors
        }), 200
    except Exception as e:
        logger.error(f'Error fetching system status: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 5. NOTIFICATIONS CONTROL =====
@admin_bp.route('/notifications/test', methods=['POST'])
@require_admin
def test_notification():
    """Send test notification"""
    try:
        data = request.json or {}
        channel = data.get('channel', 'telegram')  # telegram, email, or all
        
        message = f"🧪 Test notification from SofAi Admin Dashboard - {datetime.utcnow().isoformat()}"
        
        if channel in ['telegram', 'all']:
            # Import and send Telegram notification
            try:
                from ..notifications.telegram_notifier import telegram_notifier
                telegram_notifier.send_signal_alert(
                    symbol='TEST',
                    signal_type='TEST',
                    price=0.0,
                    confidence=1.0,
                    reason=message
                )
            except Exception as e:
                logger.error(f'Telegram test failed: {e}')
        
        if channel in ['email', 'all']:
            # Import and send Email notification
            try:
                from ..notifications.email_notifier import email_notifier
                admin_user = User.query.filter_by(is_admin=True).first()
                if admin_user:
                    email_notifier.send_signal_email(
                        to_email=admin_user.email,
                        symbol='TEST',
                        signal_type='TEST',
                        data={'message': message}
                    )
            except Exception as e:
                logger.error(f'Email test failed: {e}')
        
        logger.info(f'Admin sent test notification via {channel}')
        
        return jsonify({
            'message': 'Test notification sent',
            'channel': channel,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f'Error sending test notification: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/notifications/broadcast', methods=['POST'])
@require_admin
def broadcast_message():
    """Broadcast message to all users"""
    try:
        data = request.json
        message = data.get('message', '')
        title = data.get('title', 'SofAi Admin Broadcast')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Get all active users
        users = User.query.filter_by(is_active=True).all()
        sent_count = 0
        
        for user in users:
            try:
                # Send email to each user
                from ..notifications.email_notifier import email_notifier
                email_notifier.send_signal_email(
                    to_email=user.email,
                    symbol='BROADCAST',
                    signal_type='ANNOUNCEMENT',
                    data={'message': message, 'title': title}
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f'Failed to send broadcast to {user.email}: {e}')
        
        logger.info(f'Broadcast sent to {sent_count} users')
        
        return jsonify({
            'message': f'Broadcast sent to {sent_count} users',
            'total_users': len(users),
            'sent': sent_count
        }), 200
    except Exception as e:
        logger.error(f'Error broadcasting: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== MISC ADMIN ENDPOINTS =====
@admin_bp.route('/current-admin', methods=['GET'])
@require_admin
def get_current_admin():
    """Get current admin user info"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        return jsonify({
            'admin': user.to_dict()
        }), 200
    except Exception as e:
        logger.error(f'Error fetching current admin: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 6. BOT CONTROL PANEL =====
@admin_bp.route('/bot/status', methods=['GET'])
@require_admin
def get_bot_status():
    """Get trading bot status"""
    try:
        # Get bot configuration from environment or config
        bot_enabled = config.BOT_ENABLED if hasattr(config, 'BOT_ENABLED') else True
        risk_level = config.BOT_RISK_LEVEL if hasattr(config, 'BOT_RISK_LEVEL') else 'medium'
        max_trades_per_day = config.MAX_TRADES_PER_DAY if hasattr(config, 'MAX_TRADES_PER_DAY') else 10
        
        # Get trade stats for today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = db.session.query(func.count()).select_from(Signal).filter(
            Signal.created_at >= today_start,
            Signal.signal_type.in_(['BUY', 'SELL'])
        ).scalar() or 0
        
        return jsonify({
            'bot': {
                'enabled': bot_enabled,
                'risk_level': risk_level,
                'max_trades_per_day': max_trades_per_day,
                'trades_today': trades_today,
                'remaining_trades': max(0, max_trades_per_day - trades_today)
            }
        }), 200
    except Exception as e:
        logger.error(f'Error fetching bot status: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/bot/toggle', methods=['POST'])
@require_admin
def toggle_bot():
    """Toggle bot on/off"""
    try:
        data = request.json or {}
        enabled = data.get('enabled', True)
        
        # This would update config/environment
        # For now, just log it
        logger.info(f'Admin toggled bot to {enabled}')
        
        return jsonify({
            'message': 'Bot status toggled',
            'enabled': enabled,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f'Error toggling bot: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/bot/risk-level', methods=['POST'])
@require_admin
def set_risk_level():
    """Set global risk level"""
    try:
        data = request.json
        risk_level = data.get('risk_level')
        
        if risk_level not in ['low', 'medium', 'high']:
            return jsonify({'error': 'Invalid risk level'}), 400
        
        logger.info(f'Admin set risk level to {risk_level}')
        
        return jsonify({
            'message': 'Risk level updated',
            'risk_level': risk_level
        }), 200
    except Exception as e:
        logger.error(f'Error setting risk level: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 7. SUBSCRIPTION & PLANS =====
@admin_bp.route('/plans', methods=['GET'])
@require_admin
def get_plans():
    """Get all subscription plans"""
    try:
        plans = {
            'free': {
                'name': 'Free',
                'price': 0,
                'features': [
                    'Basic signals',
                    'Limited AI analysis',
                    'Email notifications',
                    'Basic charts'
                ],
                'token_limit': 15,
                'max_pairs': 5,
                'users': User.query.filter_by(plan='free').count()
            },
            'premium': {
                'name': 'Premium',
                'price': 29.99,
                'features': [
                    'Advanced signals',
                    'Full AI analysis',
                    'Telegram + Email',
                    'Advanced analytics',
                    'Custom alerts',
                    'Priority support'
                ],
                'token_limit': 1000,
                'max_pairs': 50,
                'users': User.query.filter_by(plan='premium').count()
            },
            'enterprise': {
                'name': 'Enterprise',
                'price': 99.99,
                'features': [
                    'Everything in Premium',
                    'API access',
                    'Custom strategies',
                    'Dedicated account manager',
                    'Unlimited pairs',
                    'Unlimited tokens'
                ],
                'token_limit': -1,
                'max_pairs': -1,
                'users': User.query.filter_by(plan='enterprise').count()
            }
        }
        
        return jsonify({'plans': plans}), 200
    except Exception as e:
        logger.error(f'Error fetching plans: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/upgrade', methods=['POST'])
@require_admin
def upgrade_user_trial(user_id):
    """Grant trial or upgrade access"""
    try:
        data = request.json
        trial_days = data.get('trial_days', 7)
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Set trial expiration
        user.trial_expires_at = datetime.utcnow() + timedelta(days=trial_days)
        db.session.commit()
        
        logger.info(f'Admin granted {trial_days} day trial to user {user_id}')
        
        return jsonify({
            'message': 'Trial access granted',
            'trial_expires_at': user.trial_expires_at.isoformat()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error granting trial: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 8. FEATURE TOGGLES =====
@admin_bp.route('/features', methods=['GET'])
@require_admin
def get_features():
    """Get all feature toggles"""
    try:
        features = {
            'auto_trading': {
                'name': 'Automated Trading',
                'enabled': True,
                'description': 'Allow users to enable automated bot trading'
            },
            'ai_predictions': {
                'name': 'AI Predictions',
                'enabled': True,
                'description': 'AI-powered signal predictions'
            },
            'signals': {
                'name': 'Signal Generation',
                'enabled': True,
                'description': 'Generate and display trading signals'
            },
            'charts': {
                'name': 'Advanced Charts',
                'enabled': True,
                'description': 'Display advanced trading charts'
            },
            'api_access': {
                'name': 'API Access',
                'enabled': True,
                'description': 'Allow API access for integrations'
            },
            'telegram_alerts': {
                'name': 'Telegram Alerts',
                'enabled': True,
                'description': 'Send alerts via Telegram'
            }
        }
        
        return jsonify({'features': features}), 200
    except Exception as e:
        logger.error(f'Error fetching features: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/features/<feature_id>/toggle', methods=['POST'])
@require_admin
def toggle_feature(feature_id):
    """Toggle feature on/off"""
    try:
        data = request.json or {}
        enabled = data.get('enabled', True)
        
        logger.info(f'Admin toggled feature {feature_id} to {enabled}')
        
        return jsonify({
            'message': f'Feature {feature_id} toggled',
            'enabled': enabled
        }), 200
    except Exception as e:
        logger.error(f'Error toggling feature: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 9. LEADERBOARD =====
@admin_bp.route('/leaderboard/users', methods=['GET'])
@require_admin
def get_user_leaderboard():
    """Get user leaderboard by signals"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # Get top users by signal count
        top_users = db.session.query(
            User.id,
            User.name,
            User.email,
            User.plan,
            func.count(Signal.id).label('signal_count')
        ).outerjoin(Signal).group_by(User.id).order_by(
            func.count(Signal.id).desc()
        ).limit(limit).all()
        
        leaderboard = []
        for rank, (user_id, name, email, plan, signal_count) in enumerate(top_users, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': user_id,
                'name': name,
                'email': email,
                'plan': plan,
                'signal_count': signal_count or 0
            })
        
        return jsonify({'leaderboard': leaderboard}), 200
    except Exception as e:
        logger.error(f'Error fetching leaderboard: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 10. SECURITY & LOGS =====
@admin_bp.route('/security/failed-logins', methods=['GET'])
@require_admin
def get_failed_logins():
    """Get failed login attempts"""
    try:
        # This would require a FailedLoginAttempt model to track
        # For now, returning mock data
        return jsonify({
            'failed_attempts': [
                {
                    'email': 'test@example.com',
                    'attempts': 5,
                    'last_attempt': datetime.utcnow().isoformat(),
                    'ip': '192.168.1.1'
                }
            ]
        }), 200
    except Exception as e:
        logger.error(f'Error fetching failed logins: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/security/lock-user', methods=['POST'])
@require_admin
def lock_user_account(user_id):
    """Lock user account due to suspicious activity"""
    try:
        data = request.json or {}
        reason = data.get('reason', 'Suspicious activity detected')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = False
        db.session.commit()
        
        logger.warning(f'Admin locked user {user_id}. Reason: {reason}')
        
        return jsonify({
            'message': 'User account locked',
            'user_id': user_id,
            'reason': reason
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error locking user: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 11. USER NOTES & METADATA =====
@admin_bp.route('/users/<int:user_id>/notes', methods=['GET', 'POST'])
@require_admin
def manage_user_notes(user_id):
    """Get or add admin notes on users"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if request.method == 'GET':
            notes = getattr(user, 'admin_notes', '')
            return jsonify({'user_id': user_id, 'notes': notes}), 200
        
        else:  # POST
            data = request.json
            notes = data.get('notes', '')
            user.admin_notes = notes
            db.session.commit()
            
            logger.info(f'Admin updated notes for user {user_id}')
            
            return jsonify({'message': 'Notes updated', 'user_id': user_id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error managing user notes: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ===== 12. DATA EXPORT =====
@admin_bp.route('/export/users-csv', methods=['GET'])
@require_admin
def export_users_csv():
    """Export users to CSV"""
    try:
        import csv
        from io import StringIO
        
        users = User.query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Email', 'Plan', 'Active', 'Admin', 'Created At', 'Last Active'])
        
        for user in users:
            writer.writerow([
                user.id,
                user.name,
                user.email,
                user.plan,
                user.is_active,
                user.is_admin,
                user.created_at.isoformat() if user.created_at else '',
                user.last_active.isoformat() if user.last_active else ''
            ])
        
        logger.info('Admin exported users to CSV')
        
        return output.getvalue(), 200, {
            'Content-Disposition': 'attachment; filename=sofai-users.csv',
            'Content-Type': 'text/csv'
        }
    except Exception as e:
        logger.error(f'Error exporting users: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
