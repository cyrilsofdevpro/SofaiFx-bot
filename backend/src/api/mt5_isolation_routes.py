"""
Multi-User MT5 Isolation Endpoints
===================================

All endpoints enforce strict user isolation:
- Each user can only access their own MT5 credentials
- Each user can only see their own signals and trades
- Trade execution is isolated per user's MT5 account
- No cross-user data exposure
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..models import db, User, Signal, Trade, ExecutionLog
from ..services.user_context import UserContext, get_user_context, log_with_user
from ..services.mt5_isolation import MT5UserIsolation
from ..services.credential_manager import CredentialEncryptor, MT5CredentialManager
from ..config import config
from ..utils.logger import logger

# Create blueprint
mt5_isolation_bp = Blueprint('mt5_isolation', __name__, url_prefix='/api/mt5')

# Initialize encryption
encryptor = CredentialEncryptor(config.ENCRYPTION_KEY)
cred_manager = MT5CredentialManager(encryptor)


# ============================================================
# MT5 PUBLIC ENDPOINTS - NO AUTH REQUIRED
# ============================================================

@mt5_isolation_bp.route('/servers', methods=['GET'])
def get_mt5_servers():
    """
    Get list of common MT5 servers (public - no auth required).
    
    Used by frontend to populate server dropdown in connection form.
    
    Returns:
        dict: List of MT5 servers with names and types
    """
    try:
        servers = [
            {'name': 'JustMarkets-Demo', 'type': 'Demo'},
            {'name': 'JustMarkets-Real', 'type': 'Live'},
            {'name': 'ICMarkets-Demo', 'type': 'Demo'},
            {'name': 'ICMarkets-Real', 'type': 'Live'},
            {'name': 'Exness-Demo', 'type': 'Demo'},
            {'name': 'Exness-Real', 'type': 'Live'},
            {'name': 'Pepperstone-Demo', 'type': 'Demo'},
            {'name': 'Pepperstone-Real', 'type': 'Live'},
            {'name': 'XM-Demo', 'type': 'Demo'},
            {'name': 'XM-Real', 'type': 'Live'},
            {'name': 'FXPRIMUS-Demo', 'type': 'Demo'},
            {'name': 'FXPRIMUS-Real', 'type': 'Live'},
        ]
        
        return jsonify({
            'success': True,
            'servers': servers
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting servers: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to get server list',
            'message': str(e)
        }), 500


# ============================================================
# MT5 CREDENTIAL MANAGEMENT - USER ISOLATED
# ============================================================

@mt5_isolation_bp.route('/credentials/store', methods=['POST'])
@UserContext.require_auth
def store_mt5_credentials():
    """
    Store user's MT5 credentials (encrypted).
    
    Only the authenticated user can store their own credentials.
    
    Request JSON:
    {
        "mt5_login": "12345",
        "mt5_password": "password",
        "mt5_server": "broker-server.com"
    }
    """
    try:
        user_id = g.current_user_id
        user = g.current_user
        data = request.json
        
        if not all(k in data for k in ['mt5_login', 'mt5_password', 'mt5_server']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        log_with_user('info', f'Storing MT5 credentials for user', user_id)
        
        # Store encrypted credentials
        cred_manager.store_credentials(
            user=user,
            login=data['mt5_login'],
            password=data['mt5_password'],
            server=data['mt5_server'],
            account_number=data.get('mt5_account_number')
        )
        
        db.session.commit()
        
        log_with_user('info', f'MT5 credentials stored successfully', user_id)
        
        return jsonify({
            'success': True,
            'message': 'Credentials stored',
            'user_id': user_id
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Error storing credentials: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/connect', methods=['POST'])
@UserContext.require_auth
def connect_user_mt5():
    """
    Connect user's MT5 account (isolated connection per user).
    
    Uses the user's encrypted credentials from database.
    Creates isolated MT5 session for this user only.
    """
    try:
        user_id = g.current_user_id
        user = g.current_user
        
        # Refresh user object to get latest credentials
        db.session.refresh(user)
        
        if not user.mt5_login or not user.mt5_password or not user.mt5_server:
            log_with_user('warning', f'MT5 credentials missing', user_id,
                         f"Login: {bool(user.mt5_login)}, Password: {bool(user.mt5_password)}, Server: {bool(user.mt5_server)}")
            return jsonify({
                'error': 'MISSING_CREDENTIALS',
                'message': 'MT5 credentials not configured. Please store credentials first.'
            }), 400
        
        log_with_user('info', f'Attempting MT5 connection', user_id)
        
        # Decrypt credentials
        login, password = cred_manager.get_decrypted_credentials(user)
        
        # Connect with isolation
        result = MT5UserIsolation.connect_user(
            user_id=user_id,
            login=login,
            password=password,
            server=user.mt5_server
        )
        
        if result['success']:
            # Update connection status in database
            user.mt5_connected = True
            user.mt5_connection_time = datetime.utcnow()
            user.mt5_account_number = result['account']['login']
            db.session.commit()
            
            log_with_user('info', f'MT5 connection successful', user_id, 
                         f"Account: {result['account']['login']}")
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Connection error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/disconnect', methods=['POST'])
@UserContext.require_auth
def disconnect_user_mt5():
    """
    Disconnect user's MT5 account.
    
    Closes isolated MT5 session for this user.
    """
    try:
        user_id = g.current_user_id
        user = g.current_user
        
        log_with_user('info', f'Disconnecting MT5', user_id)
        
        result = MT5UserIsolation.disconnect_user(user_id)
        
        # Update database
        user.mt5_connected = False
        db.session.commit()
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Disconnect error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/status', methods=['GET'])
@UserContext.require_auth
def get_mt5_status():
    """
    Get MT5 connection status for current user.
    
    Returns only this user's connection status.
    """
    try:
        user_id = g.current_user_id
        
        status = MT5UserIsolation.get_user_connection_status(user_id)
        
        return jsonify({
            'user_id': user_id,
            'mt5_status': status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Status check error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/connection-status', methods=['GET'])
@UserContext.require_auth
def get_connection_status():
    """
    Get MT5 connection status (user-friendly format).
    
    Returns:
        dict: {success: bool, connected: bool}
    """
    try:
        user_id = g.current_user_id
        
        status_info = MT5UserIsolation.get_user_connection_status(user_id)
        
        # status_info is a dict like {"connected": bool, "status": "..."}
        is_connected = status_info.get('connected', False) if isinstance(status_info, dict) else False
        
        return jsonify({
            'success': True,
            'connected': is_connected,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Connection status error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'connected': False,
            'error': str(e)
        }), 500


# ============================================================
# ISOLATED SIGNAL GENERATION
# ============================================================

@mt5_isolation_bp.route('/signal', methods=['GET'])
@UserContext.require_api_key
def get_signal_isolated():
    """
    Generate trading signal for user (isolated execution).
    
    Query Parameters:
    - symbol: Currency pair (e.g., EURUSD)
    - apikey: User's API key
    
    Features:
    - Signal generated only for this user
    - Saved with user_id isolation
    - Uses only this user's risk parameters
    """
    try:
        user_id = g.current_user_id
        user = g.current_user
        symbol = request.args.get('symbol', 'EURUSD').upper()
        
        log_with_user('info', f'Generating signal for {symbol}', user_id)
        
        # Fetch market data
        from ..data.twelvedata import TwelveDataClient
        td = TwelveDataClient()
        
        if len(symbol) == 6:
            from_sym = symbol[:3]
            to_sym = symbol[3:]
            td_symbol = f"{from_sym}/{to_sym}"
        else:
            td_symbol = symbol
        
        df = td.get_time_series(td_symbol, interval='1min', outputsize=100)
        
        if df is None or df.empty:
            return jsonify({
                'error': 'NO_DATA',
                'message': f'Could not fetch data for {symbol}'
            }), 400
        
        # Generate signal
        from ..signals.phase4_ai_layer import Phase4AILayer
        ai_layer = Phase4AILayer()
        signal_result = ai_layer.get_signal(df, symbol)
        
        # ✅ CRITICAL: Save signal with user_id (USER ISOLATION)
        db_signal = Signal(
            user_id=user_id,  # <-- ISOLATION KEY
            symbol=symbol,
            signal_type=signal_result['signal'],
            price=signal_result.get('price', 0),
            confidence=signal_result.get('confidence', 0),
            reason=signal_result.get('analysis', {}).get('reason', ''),
            ai_prediction=signal_result.get('sentiment', {})
        )
        db.session.add(db_signal)
        db.session.commit()
        
        log_with_user('info', f'Signal saved: {signal_result["signal"]} (confidence: {signal_result["confidence"]})', user_id)
        
        return jsonify({
            'success': True,
            'signal': signal_result,
            'user_id': user_id,
            'saved_to_db': True
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Signal generation error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/signals', methods=['GET'])
@UserContext.require_auth
def get_user_signals():
    """
    Get all signals for current user (isolated).
    
    Returns ONLY this user's signals.
    Other users' signals are NOT accessible.
    """
    try:
        user_id = g.current_user_id
        limit = request.args.get('limit', 100, type=int)
        
        # ✅ CRITICAL: Filter by user_id (USER ISOLATION)
        signals = Signal.query.filter_by(user_id=user_id).order_by(Signal.created_at.desc()).limit(limit).all()
        
        log_with_user('info', f'Retrieved {len(signals)} signals', user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'signal_count': len(signals),
            'signals': [
                {
                    'id': s.id,
                    'symbol': s.symbol,
                    'signal': s.signal_type,
                    'price': s.price,
                    'confidence': s.confidence,
                    'created_at': s.created_at.isoformat()
                }
                for s in signals
            ]
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Error retrieving signals: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================
# ISOLATED TRADE EXECUTION
# ============================================================

@mt5_isolation_bp.route('/execute', methods=['POST'])
@UserContext.require_auth
def execute_trade_isolated():
    """
    Execute trade on user's MT5 account (isolated).
    
    Trade is executed ONLY on this user's MT5 account.
    No cross-user execution is possible.
    
    Request JSON:
    {
        "symbol": "EURUSD",
        "order_type": "buy",
        "volume": 1.0,
        "stop_loss": 1.0850,
        "take_profit": 1.1000
    }
    """
    try:
        user_id = g.current_user_id
        user = g.current_user
        data = request.json
        
        # Verify user is connected
        if not MT5UserIsolation.is_user_connected(user_id):
            return jsonify({
                'error': 'NOT_CONNECTED',
                'message': 'MT5 account not connected'
            }), 400
        
        log_with_user('info', f'Executing trade: {data.get("order_type")} {data.get("volume")} {data.get("symbol")}', user_id)
        
        # Execute with isolation
        result = MT5UserIsolation.execute_trade_for_user(
            user_id=user_id,  # <-- ISOLATION KEY
            symbol=data['symbol'],
            order_type=data['order_type'],
            volume=data['volume'],
            sl=data.get('stop_loss'),
            tp=data.get('take_profit'),
            comment=f"SofAi-User-{user_id}"
        )
        
        if result['success']:
            # Save trade to database with user_id
            trade = Trade(
                user_id=user_id,  # <-- ISOLATION KEY
                symbol=data['symbol'],
                order_type=data['order_type'],
                volume=data['volume'],
                entry_price=data.get('price', 0),
                stop_loss=data.get('stop_loss'),
                take_profit=data.get('take_profit'),
                status='open',
                order_id=result.get('order_id')
            )
            db.session.add(trade)
            db.session.commit()
            
            log_with_user('info', f'Trade executed and saved: {result.get("order_id")}', user_id)
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Trade execution error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/trades', methods=['GET'])
@UserContext.require_auth
def get_user_trades():
    """
    Get all trades for current user (isolated).
    
    Returns ONLY this user's trades.
    Other users' trades are NOT accessible.
    """
    try:
        user_id = g.current_user_id
        status = request.args.get('status')
        
        # ✅ CRITICAL: Filter by user_id (USER ISOLATION)
        query = Trade.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        trades = query.order_by(Trade.created_at.desc()).all()
        
        log_with_user('info', f'Retrieved {len(trades)} trades', user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'trade_count': len(trades),
            'trades': [
                {
                    'id': t.id,
                    'symbol': t.symbol,
                    'type': t.order_type,
                    'volume': t.volume,
                    'entry_price': t.entry_price,
                    'status': t.status,
                    'profit_loss': t.profit_loss,
                    'created_at': t.created_at.isoformat()
                }
                for t in trades
            ]
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Error retrieving trades: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@mt5_isolation_bp.route('/positions', methods=['GET'])
@UserContext.require_auth
def get_user_positions():
    """
    Get open positions for user's MT5 account (isolated).
    
    Returns ONLY this user's open positions on MT5.
    """
    try:
        user_id = g.current_user_id
        
        if not MT5UserIsolation.is_user_connected(user_id):
            return jsonify({
                'error': 'NOT_CONNECTED',
                'positions': []
            }), 200
        
        positions = MT5UserIsolation.get_user_positions(user_id)
        
        log_with_user('info', f'Retrieved {len(positions)} positions', user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'position_count': len(positions),
            'positions': positions
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Position retrieval error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================
# ACCOUNT INFO - ISOLATED
# ============================================================

@mt5_isolation_bp.route('/account', methods=['GET'])
@UserContext.require_auth
def get_user_account_info():
    """
    Get user's MT5 account information (isolated).
    
    Returns ONLY this user's account info.
    """
    try:
        user_id = g.current_user_id
        
        session = MT5UserIsolation.get_user_session(user_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'NO_CONNECTION',
                'message': 'MT5 account not connected. Please connect your MT5 account first.'
            }), 200  # Return 200 so frontend handles gracefully
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'account': session
        }), 200
    
    except Exception as e:
        logger.error(f'[USER {g.current_user_id}] Account info error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['mt5_isolation_bp']