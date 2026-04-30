"""
Execution API - Endpoints for managing automated trade execution

Provides:
- Trade status and history
- Execution logs and analytics
- Kill switch control
- Position management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from src.models import db, Trade, ExecutionLog
from src.utils.logger import logger as api_logger

execution_bp = Blueprint('execution', __name__, url_prefix='/api/execution')


@execution_bp.route('/trades', methods=['GET'])
@jwt_required()
def get_trades():
    """
    Get user's trades (open or closed).
    
    Query params:
        status: 'OPEN', 'CLOSED', or None for all
        limit: Maximum trades to return (default: 50)
    
    Returns:
        list: Trade data
    """
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        query = Trade.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        trades = query.order_by(Trade.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'ok',
            'count': len(trades),
            'trades': [t.to_dict() for t in trades]
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting trades: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/trades/<int:trade_id>', methods=['GET'])
@jwt_required()
def get_trade(trade_id):
    """
    Get specific trade details.
    
    Returns:
        dict: Trade data
    """
    try:
        user_id = get_jwt_identity()
        trade = Trade.query.filter_by(id=trade_id, user_id=user_id).first()
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'trade': trade.to_dict()
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting trade: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/trades/statistics', methods=['GET'])
@jwt_required()
def get_trade_statistics():
    """
    Get trade statistics.
    
    Query params:
        days: Number of days to look back (default: 7)
    
    Returns:
        dict: Statistics
    """
    try:
        user_id = get_jwt_identity()
        days = int(request.args.get('days', 7))
        
        # Get closed trades from the past N days
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.status == 'CLOSED',
            Trade.exit_time >= cutoff_date
        ).all()
        
        if not trades:
            return jsonify({
                'status': 'ok',
                'statistics': {
                    'period_days': days,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_pnl_per_trade': 0.0
                }
            }), 200
        
        # Calculate statistics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in trades) if trades else 0
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        return jsonify({
            'status': 'ok',
            'statistics': {
                'period_days': days,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl_per_trade': round(avg_pnl, 2)
            }
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_execution_logs():
    """
    Get execution logs.
    
    Query params:
        event_type: Filter by event type
        limit: Maximum logs to return (default: 100)
    
    Returns:
        list: Execution logs
    """
    try:
        user_id = get_jwt_identity()
        event_type = request.args.get('event_type')
        limit = int(request.args.get('limit', 100))
        
        query = ExecutionLog.query.filter_by(user_id=user_id)
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        logs = query.order_by(ExecutionLog.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'ok',
            'count': len(logs),
            'logs': [l.to_dict() for l in logs]
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting logs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/status', methods=['GET'])
@jwt_required()
def get_execution_status():
    """
    Get current execution status.
    
    Returns:
        dict: Status information
    """
    try:
        user_id = get_jwt_identity()
        
        # Get open positions count
        open_trades = Trade.query.filter_by(user_id=user_id, status='OPEN').all()
        
        # Get today's P&L
        from datetime import date
        today = date.today()
        today_start = datetime(today.year, today.month, today.day)
        
        today_trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.status == 'CLOSED',
            Trade.exit_time >= today_start
        ).all()
        
        today_pnl = sum(t.pnl for t in today_trades) if today_trades else 0
        
        return jsonify({
            'status': 'ok',
            'execution_status': {
                'open_trades': len(open_trades),
                'open_trade_symbols': [t.symbol for t in open_trades],
                'today_trades_closed': len(today_trades),
                'today_pnl': round(today_pnl, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting execution status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/trades/<int:trade_id>/close', methods=['POST'])
@jwt_required()
def close_trade(trade_id):
    """
    Close an open trade manually.
    
    Body:
        exit_price: Exit price (required)
        reason: Close reason (optional)
    
    Returns:
        dict: Closed trade data
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'exit_price' not in data:
            return jsonify({'error': 'exit_price is required'}), 400
        
        exit_price = float(data['exit_price'])
        reason = data.get('reason', 'Manual close')
        
        trade = Trade.query.filter_by(id=trade_id, user_id=user_id).first()
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        if trade.status != 'OPEN':
            return jsonify({'error': f'Trade is {trade.status}, cannot close'}), 400
        
        # Calculate P&L
        if trade.trade_type == 'BUY':
            pnl = (exit_price - trade.entry_price) * trade.lot_size * 100000
        else:
            pnl = (trade.entry_price - exit_price) * trade.lot_size * 100000
        
        pnl_percent = (pnl / (trade.entry_price * trade.lot_size * 100000)) * 100 if trade.entry_price > 0 else 0
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.close_reason = reason
        trade.status = 'CLOSED'
        
        db.session.commit()
        
        api_logger.info(f"Trade {trade_id} closed manually: P&L ${pnl:.2f}")
        
        return jsonify({
            'status': 'ok',
            'trade': trade.to_dict()
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error closing trade: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/kill-switch', methods=['GET', 'POST'])
@jwt_required()
def kill_switch():
    """
    Get or set bot kill switch status.
    
    POST body:
        enabled: true/false
    
    Returns:
        dict: Kill switch status
    """
    try:
        user_id = get_jwt_identity()
        
        if request.method == 'POST':
            data = request.get_json()
            enabled = data.get('enabled', True)
            
            # Store kill switch status in user preferences
            from src.models import UserPreference
            pref = UserPreference.query.filter_by(user_id=user_id).first()
            
            if not pref:
                pref = UserPreference(user_id=user_id)
                db.session.add(pref)
            
            pref.execution_enabled = enabled
            db.session.commit()
            
            api_logger.info(f"Kill switch set to {enabled} for user {user_id}")
            
            return jsonify({
                'status': 'ok',
                'kill_switch': {'enabled': enabled}
            }), 200
        
        else:  # GET
            from src.models import UserPreference
            pref = UserPreference.query.filter_by(user_id=user_id).first()
            
            enabled = pref.execution_enabled if pref else False
            
            return jsonify({
                'status': 'ok',
                'kill_switch': {'enabled': enabled}
            }), 200
        
    except Exception as e:
        api_logger.error(f"Error managing kill switch: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/open-positions', methods=['GET'])
@jwt_required()
def get_open_positions():
    """
    Get all open trades (positions).
    
    Returns:
        list: Open trades
    """
    try:
        user_id = get_jwt_identity()
        
        open_trades = Trade.query.filter_by(user_id=user_id, status='OPEN').all()
        
        return jsonify({
            'status': 'ok',
            'count': len(open_trades),
            'positions': [t.to_dict() for t in open_trades]
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting open positions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/daily-report', methods=['GET'])
@jwt_required()
def get_daily_report():
    """
    Get daily trading report.
    
    Query params:
        date: Date string (YYYY-MM-DD), defaults to today
    
    Returns:
        dict: Daily report
    """
    try:
        user_id = get_jwt_identity()
        date_str = request.args.get('date')
        
        if not date_str:
            from datetime import date as date_obj
            date_str = date_obj.today().strftime('%Y-%m-%d')
        
        # Parse date
        from datetime import datetime as dt, timedelta
        start_date = dt.strptime(date_str, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1)
        
        # Get trades for the day
        trades = Trade.query.filter(
            Trade.user_id == user_id,
            Trade.exit_time >= start_date,
            Trade.exit_time < end_date
        ).all()
        
        # Get execution logs for the day
        logs = ExecutionLog.query.filter(
            ExecutionLog.user_id == user_id,
            ExecutionLog.created_at >= start_date,
            ExecutionLog.created_at < end_date
        ).all()
        
        # Calculate stats
        total_pnl = sum(t.pnl for t in trades) if trades else 0
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        
        return jsonify({
            'status': 'ok',
            'daily_report': {
                'date': date_str,
                'total_trades': len(trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': round(total_pnl, 2),
                'total_events': len(logs),
                'trades': [t.to_dict() for t in trades],
                'events': [l.to_dict() for l in logs]
            }
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting daily report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# In-memory execution service storage (for demo purposes)
_execution_services = {}


@execution_bp.route('/start', methods=['POST'])
@jwt_required()
def start_execution():
    """
    Start the trading bot for the user.
    
    Body:
        mt5_login: MT5 account login
        mt5_password: MT5 password
        mt5_server: MT5 server (optional)
    
    Returns:
        dict: Start result
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get MT5 credentials from user or request body
        from src.models import User
        user = User.query.get(user_id)
        
        mt5_login = data.get('mt5_login') or (user.mt5_login if user else None)
        mt5_password = data.get('mt5_password') or (user.mt5_password if user else None)
        mt5_server = data.get('mt5_server') or user.mt5_server if user else "ICMarkets-Demo"
        
        if not mt5_login or not mt5_password:
            return jsonify({'error': 'MT5 credentials not configured. Please connect your MT5 account first.'}), 400
        
        # Store execution state
        _execution_services[user_id] = {
            'running': True,
            'started_at': datetime.utcnow().isoformat(),
            'mt5_server': mt5_server
        }
        
        # Update user preferences
        from src.models import UserPreference
        pref = UserPreference.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = UserPreference(user_id=user_id)
            db.session.add(pref)
        pref.execution_enabled = True
        db.session.commit()
        
        api_logger.info(f"Trading bot started for user {user_id}")
        
        return jsonify({
            'status': 'ok',
            'message': 'Trading bot started successfully',
            'running': True,
            'started_at': _execution_services[user_id]['started_at']
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error starting execution: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_execution():
    """
    Stop the trading bot for the user.
    
    Returns:
        dict: Stop result
    """
    try:
        user_id = get_jwt_identity()
        
        # Update execution state
        if user_id in _execution_services:
            _execution_services[user_id]['running'] = False
        
        # Update user preferences
        from src.models import UserPreference
        pref = UserPreference.query.filter_by(user_id=user_id).first()
        if pref:
            pref.execution_enabled = False
            db.session.commit()
        
        api_logger.info(f"Trading bot stopped for user {user_id}")
        
        return jsonify({
            'status': 'ok',
            'message': 'Trading bot stopped successfully',
            'running': False
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error stopping execution: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@execution_bp.route('/running', methods=['GET'])
@jwt_required()
def get_execution_running():
    """
    Get whether the trading bot is running for the user.
    
    Returns:
        dict: Running status
    """
    try:
        user_id = get_jwt_identity()
        
        running = False
        started_at = None
        
        if user_id in _execution_services:
            running = _execution_services[user_id].get('running', False)
            started_at = _execution_services[user_id].get('started_at')
        
        # Also check user preferences
        from src.models import UserPreference
        pref = UserPreference.query.filter_by(user_id=user_id).first()
        if pref and pref.execution_enabled:
            running = True
        
        return jsonify({
            'status': 'ok',
            'running': running,
            'started_at': started_at
        }), 200
        
    except Exception as e:
        api_logger.error(f"Error getting execution status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
