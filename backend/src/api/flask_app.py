from flask import Flask, jsonify, request, send_file, send_from_directory
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from src.data.alpha_vantage import alpha_vantage, APIRateLimitError
from src.data.twelvedata import TwelveDataClient
# NOTE: Signal engines are lazy-loaded to avoid heavy imports at startup
from src.notifications.telegram_notifier import TelegramNotifier
from src.notifications.email_notifier import EmailNotifier
from src.risk.risk_manager import risk_manager
from src.config import config
from src.utils.logger import logger
from src.models import init_db, db, User, Signal, UserPreference
from src.mongo_auth import init_mongo_db, seed_admin
from src.auth import auth_bp
from src.admin import admin_bp
from src.execution import execution_bp
from src.recommendations import recommendation_engine
from src.scheduler import scheduler
from src.services.mt5_account import MT5AccountService
from src.services.credential_manager import CredentialEncryptor, MT5CredentialManager
from src.services.mt5_connection import MT5ConnectionManager
from datetime import datetime
import pandas as pd
import numpy as np
import json
import os

# Custom JSON provider for Flask 2.x to handle numpy types
class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, np.bool_):
            return bool(o)
        elif isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)

# Initialize Flask app with static files serving
# Get the absolute path to the frontend directory (go up 3 levels from backend/src/api)
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../frontend'))
app = Flask(__name__)
app.json = NumpyJSONProvider(app)

# ===== Database Configuration =====
# Use absolute path for database - ensures consistency regardless of working directory
db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
db_path = os.path.join(db_dir, 'sofai_fx.db')
# Convert to forward slashes for SQLite on Windows
db_path_normalized = db_path.replace('\\', '/')
# Proper SQLite URI format: sqlite:///absolute/path or sqlite:////unc/path
if db_path_normalized.startswith('/'):
    # Unix-style absolute path
    db_uri = f'sqlite:///{db_path_normalized}'
else:
    # Windows absolute path (e.g., C:/path/to/file)
    db_uri = f'sqlite:///{db_path_normalized}'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
logger.info(f'Database path: {db_path}')
logger.info(f'Database URI: {db_uri}')

# ===== JWT Configuration =====
# Use consistent secret key - CRITICAL: Must be same for token generation and validation
jwt_secret = config.JWT_SECRET_KEY or 'sofai-fx-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 60 * 60 * 24 * 30  # 30 days
logger.info(f'JWT Secret Key configured: {jwt_secret[:20]}...')

# Initialize extensions
init_db(app)
try:
    init_mongo_db(app)
    seed_admin()
    print("✅ Mongo initialized")
except Exception as e:
    print("❌ Mongo init failed:", e)

jwt = JWTManager(app)

# CORS Configuration - Allow all origins for mobile/testing
# In production, restrict to specific frontend domains
cors_config = {
    'origins': '*',  # Allow all origins for mobile WebView compatibility
    'supports_credentials': True,
    'allow_headers': ['Content-Type', 'Authorization'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'max_age': 3600
}
# Apply CORS to ALL routes (not just /api/* and /auth/*)
CORS(app, resources={r"/*": cors_config})
logger.info('✓ CORS enabled for all origins and all routes')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(execution_bp)

# Register dashboard blueprint (Phase 5)
from src.dashboard_routes import dashboard_bp
app.register_blueprint(dashboard_bp)

# Register stats blueprint (for frontend compatibility)
from src.stats_routes import stats_bp
app.register_blueprint(stats_bp)

# Register MT5 isolation blueprint (Multi-user system)
from src.mt5_isolation_routes import mt5_isolation_bp
app.register_blueprint(mt5_isolation_bp)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Missing authorization token'}), 401

# Initialize services
signal_generator = None  # Lazy-loaded to speed up startup
phase_router = None      # Lazy-loaded: routes to lite or full engine
telegram_notifier = TelegramNotifier()
email_notifier = EmailNotifier()
twelvedata = TwelveDataClient()

def get_signal_generator():
    """Lazy-load signal generator on first use"""
    global signal_generator
    if signal_generator is None:
        from src.signals.signal_generator import SignalGenerator
        signal_generator = SignalGenerator()
        logger.info("✓ SignalGenerator loaded")
    return signal_generator

def get_phase_router():
    """Lazy-load phase router on first use"""
    global phase_router
    if phase_router is None:
        from src.signals.phase_router import PhaseRouter
        phase_router = PhaseRouter()
        logger.info("✓ PhaseRouter loaded")
    return phase_router

# Initialize credential encryption and management
encryption_key = config.ENCRYPTION_MASTER_KEY
credential_encryptor = CredentialEncryptor(encryption_key)
credential_manager = MT5CredentialManager(credential_encryptor)

# Initialize and start scheduler
scheduler.start()

# In-memory storage for signals (in production, use a database)
signal_history = []
max_history = 100

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'SofAi FX Bot API'
    }), 200

@app.route('/api/diagnostics', methods=['GET'])
def diagnostics():
    """Diagnostic endpoint to verify database and system status"""
    try:
        # Check database file exists
        import os
        db_file_exists = os.path.exists(db_path)
        db_file_size = os.path.getsize(db_path) if db_file_exists else 0
        
        # Get total counts from database
        total_users = User.query.count()
        total_signals = Signal.query.count()

        # List all signals in database
        all_signals = Signal.query.all()
        signals_by_user = {}
        for sig in all_signals:
            if sig.user_id not in signals_by_user:
                signals_by_user[sig.user_id] = []
            signals_by_user[sig.user_id].append({
                'id': sig.id,
                'symbol': sig.symbol,
                'signal': sig.signal_type,
                'created_at': sig.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'ok',
            'database': {
                'path': db_path,
                'exists': db_file_exists,
                'size_bytes': db_file_size,
                'total_users': total_users,
                'total_signals': total_signals,
                'signals_by_user': signals_by_user
            }
        }), 200
    except Exception as e:
        logger.error(f'Diagnostics error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals', methods=['GET'])
@jwt_required()
def get_signals():
    """Get recent signals for current user"""
    try:
        user_id = int(get_jwt_identity())
        limit = request.args.get('limit', 10, type=int)
        
        logger.info(f'🔍 [RETRIEVE START] user_id={user_id}, limit={limit}')
        
        # Get signals for current user only
        signals = Signal.query.filter_by(user_id=user_id).order_by(Signal.created_at.desc()).limit(limit).all()
        
        logger.info(f'✅ [RETRIEVE DONE] user_id={user_id}: Found {len(signals)} signals')
        
        if len(signals) == 0:
            # Debug: Check total signals in database
            total_signals = Signal.query.count()
            all_users = Signal.query.distinct(Signal.user_id).count()
            logger.warning(f'⚠️ No signals for user_id={user_id} (Total signals in DB: {total_signals}, Users with signals: {all_users})')
        
        return jsonify({
            'signals': [s.to_dict() for s in signals],
            'total': len(signals),
            'user_id': user_id
        }), 200
    except Exception as e:
        logger.error(f'❌ [ERROR] Failed to retrieve signals: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals/<symbol>', methods=['GET'])
@jwt_required()
def get_symbol_signals(symbol):
    """Get signals for a specific symbol for current user"""
    try:
        user_id = int(get_jwt_identity())
        symbol = symbol.upper()
        
        # Get signals for current user and symbol only
        symbol_signals = Signal.query.filter_by(user_id=user_id, symbol=symbol).all()
        
        return jsonify({
            'symbol': symbol,
            'signals': [s.to_dict() for s in symbol_signals],
            'total': len(symbol_signals),
            'user_id': user_id
        }), 200
    except Exception as e:
        logger.error(f'Error fetching symbol signals: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals/clear', methods=['DELETE'])
@jwt_required()
def clear_signals():
    """Delete all signals for current user"""
    try:
        user_id = int(get_jwt_identity())
        deleted_count = Signal.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        logger.info(f'Cleared {deleted_count} signals for user {user_id}')
        
        return jsonify({
            'message': 'Signals cleared successfully',
            'deleted': deleted_count,
            'user_id': user_id
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error clearing signals: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
@jwt_required()
def analyze_pair():
    """
    Analyze a currency pair and generate signal
    
    Request body:
    {
        "symbol": "EURUSD",
        "notify": true
    }
    """
    try:
        # Get user_id first
        user_id = int(get_jwt_identity())
        logger.info(f'📍 [ANALYZE START] User {user_id} analyzing pair...')
        
        # Check token limit for free users
        user = User.query.get(user_id)
        if user:
            if not user.can_use_token():
                remaining = user.get_tokens_remaining()
                return jsonify({
                    'error': 'TOKEN_LIMIT_REACHED',
                    'message': f'Daily token limit reached. You have used all {user.get_token_limit()} tokens for today. Upgrade to Premium for unlimited tokens.',
                    'tokens_remaining': remaining,
                    'tokens_limit': user.get_token_limit()
                }), 403
            
            # Consume a token
            user.consume_token()
            logger.info(f'🔢 Token consumed. Used: {user.tokens_used_today}/{user.get_token_limit()}')
        
        data = request.json
        symbol = data.get('symbol', '').upper()
        notify = data.get('notify', True)
        
        if not symbol or len(symbol) != 6:
            return jsonify({'error': 'Invalid symbol. Expected format: EURUSD'}), 400
        
        # Store original symbol for API calls (Alpha Vantage, TwelveData)
        original_symbol = symbol
        
        # Normalize symbol for internal use and MT5 (append .m suffix)
        if not symbol.endswith('.m'):
            symbol = symbol + '.m'
        
        # Parse symbol for API
        from_sym = original_symbol[:3]
        to_sym = original_symbol[3:]
        
        logger.info(f'🔍 Analyzing {symbol}...')
        
        # Fetch real-time data from TwelveData API (1-minute candles)
        try:
            # Format symbol for TwelveData: EUR/USD format
            td_symbol = f"{from_sym}/{to_sym}"
            logger.info(f'Fetching real OHLC data from TwelveData: {td_symbol}')
            
            # Get 1-minute candles for real-time analysis
            df = twelvedata.get_time_series(td_symbol, interval='1min', outputsize=100)
            
            if df is None or df.empty:
                logger.warning(f'TwelveData returned no data, falling back to Alpha Vantage...')
                df = alpha_vantage.get_forex_data(from_sym, to_sym)
                
        except APIRateLimitError as e:
            logger.error(f'API Rate limit hit for {symbol}')
            return jsonify({
                'error': 'API_RATE_LIMIT',
                'message': 'API rate limit reached.',
                'detail': str(e)
            }), 429
        except Exception as e:
            logger.warning(f'TwelveData fetch failed: {e}, trying Alpha Vantage...')
            try:
                df = alpha_vantage.get_forex_data(from_sym, to_sym)
            except APIRateLimitError as e:
                logger.error(f'API Rate limit hit for {symbol}')
                return jsonify({
                    'error': 'API_RATE_LIMIT',
                    'message': 'API rate limit reached.',
                    'detail': str(e)
                }), 429
        
        if df is None or df.empty:
            return jsonify({'error': 'Failed to fetch market data'}), 500
        
        # Track which API provided the data
        data_source = 'TwelveData (Real-time 1-min candles)' if len(df) > 10 else 'Alpha Vantage (Daily candles)'
        logger.info(f'Data source for {symbol}: {data_source} ({len(df)} candles)')
        
        # Normalize column names to capitalize OHLC (required by strategies)
        # TwelveData returns lowercase: open, high, low, close
        # Strategies expect: Open, High, Low, Close
        if 'open' in df.columns:
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
        elif 'Date' in df.columns:
            # Alpha Vantage data already has uppercase columns
            pass
        
        logger.info(f'Using {data_source} for signal analysis on {symbol}')
        
        # Generate signal
        signal = get_signal_generator().generate_signal(df, symbol)
        
        if signal is None:
            logger.warning(f'⚠️ No signal generated for {symbol} (strategies did not meet MIN_AGREEMENT threshold)')
            return jsonify({
                'success': False,
                'signal': None,
                'message': 'No clear signal found for this pair',
                'data_points': len(df),
                'data_source': data_source,
                'symbol': symbol
            }), 200
        
        logger.info(f'✅ [SIGNAL GENERATED] {symbol}: {signal.signal.value}, Confidence: {signal.confidence:.2f}')
        
        # Save to database with user_id
        saved_id = None
        try:
            if signal is None:
                logger.warning(f'⚠️ [SAVE SKIPPED] signal is None for {symbol}')
                saved_id = None
            else:
                logger.info(f'💾 [SAVING START] user_id={user_id}, symbol={symbol}, signal={signal.signal.value}')
                
                # Convert numpy types to Python native types for JSON serialization
                def convert_numpy_types(obj):
                    """Recursively convert numpy types to native Python types"""
                    import numpy as np
                    if isinstance(obj, dict):
                        return {k: convert_numpy_types(v) for k, v in obj.items()}
                    elif isinstance(obj, (list, tuple)):
                        return type(obj)(convert_numpy_types(item) for item in obj)
                    elif isinstance(obj, np.bool_):
                        return bool(obj)
                    elif isinstance(obj, (np.integer, np.floating)):
                        return obj.item()
                    return obj
                
                db_signal = Signal(
                    user_id=user_id,
                    symbol=symbol,
                    signal_type=signal.signal.value,
                    price=signal.price,
                    confidence=signal.confidence,
                    reason=signal.reason,
                    rsi_signal=convert_numpy_types(signal.rsi_signal.to_dict() if signal.rsi_signal else None),
                    ma_signal=convert_numpy_types(signal.ma_signal.to_dict() if signal.ma_signal else None),
                    sr_signal=convert_numpy_types(signal.sr_signal.to_dict() if signal.sr_signal else None),
                    ai_prediction=convert_numpy_types(signal.ai_prediction if signal.ai_prediction else {}),
                    filter_results=convert_numpy_types(signal.filter_results if signal.filter_results else {})
                )
                logger.info(f'   Created Signal object')
                
                db.session.add(db_signal)
                logger.info(f'   Added to session')
                
                db.session.commit()
                logger.info(f'   Committed to database')
                
                saved_id = db_signal.id
                logger.info(f'✅ [SAVED SUCCESS] Database ID: {saved_id}, user_id={user_id}, symbol={symbol}')
        except Exception as e:
            db.session.rollback()
            logger.error(f'❌ [SAVE ERROR] Failed to save signal: {e}', exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            # Continue - we can still return the signal even if save fails
        
        # Send notifications if enabled
        if notify and signal:
            if signal.signal.value != 'HOLD':
                telegram_notifier.send_signal(signal)
                email_notifier.send_signal(signal)
        
        # Calculate risk management data
        risk_data = None
        if signal:
            try:
                current_price = df['Close'].iloc[-1]
                atr = risk_manager.calculate_atr(df, period=14)
                
                # Calculate SL/TP based on signal direction
                signal_direction = signal.signal.value.lower()
                sl_tp = risk_manager.calculate_sl_tp(df, symbol, signal_direction, current_price, atr)
                
                if sl_tp is not None:
                    # Calculate position size
                    pos_size = risk_manager.calculate_position_size(symbol, current_price, sl_tp['stop_loss'])
                    
                    # Calculate R/R ratio
                    rr = risk_manager.calculate_risk_reward(current_price, sl_tp['stop_loss'], sl_tp['take_profit'])
                    
                    risk_data = {
                        'entry_price': round(current_price, 5),
                        'stop_loss': round(sl_tp['stop_loss'], 5),
                        'take_profit': round(sl_tp['take_profit'], 5),
                        'sl_pips': round(sl_tp['sl_pips'], 1),
                        'tp_pips': round(sl_tp['tp_pips'], 1),
                        'atr': round(atr, 6) if atr else 0,
                        'position_size': {
                            'lots': pos_size['lots'],
                            'units': pos_size['units'],
                            'risk_amount': round(pos_size['risk_amount'], 2),
                            'risk_pips': round(pos_size['risk_pips'], 1)
                        },
                        'risk_reward_ratio': round(rr['ratio'], 2) if rr else 2.0,
                        'account_balance': 10000,
                        'risk_per_trade_percent': 2.0
                    }
            except Exception as e:
                logger.warning(f'Could not calculate risk management for {symbol}: {e}')
                risk_data = None
        
        signal_dict = signal.to_dict() if signal else None
        
        response_data = {
            'success': True,
            'signal': signal_dict,
            'risk_management': risk_data,
            'data_points': len(df),
            'data_source': data_source,
            'symbol': symbol,
            'saved_to_db': saved_id is not None
        }
        
        logger.info(f'📤 [RESPONSE] user_id={user_id}, symbol={symbol}, signal_saved={saved_id is not None}, db_id={saved_id}')
        
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f'❌ [ERROR] Analyze endpoint failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-all', methods=['POST'])
@jwt_required()
def analyze_all_pairs():
    """Analyze all configured currency pairs for current user"""
    try:
        user_id = int(get_jwt_identity())
        
        # Check token limit for free users
        user = User.query.get(user_id)
        if user:
            if not user.can_use_token():
                remaining = user.get_tokens_remaining()
                return jsonify({
                    'error': 'TOKEN_LIMIT_REACHED',
                    'message': f'Daily token limit reached. You have used all {user.get_token_limit()} tokens for today. Upgrade to Premium for unlimited tokens.',
                    'tokens_remaining': remaining,
                    'tokens_limit': user.get_token_limit()
                }), 403
            
            # Consume a token for the batch
            user.consume_token()
            logger.info(f'🔢 Token consumed for batch analysis. Used: {user.tokens_used_today}/{user.get_token_limit()}')
        
        pairs = request.json.get('pairs', config.CURRENCY_PAIRS) if request.json else config.CURRENCY_PAIRS
        results = []
        
        for pair in pairs:
            if '/' in pair:
                from_sym, to_sym = pair.split('/')
            else:
                from_sym = pair[:3]
                to_sym = pair[3:]
            
            logger.info(f'Analyzing {pair}...')
            
            # Fetch real-time data from TwelveData API (1-minute candles)
            try:
                td_symbol = f"{from_sym}/{to_sym}"
                df = twelvedata.get_time_series(td_symbol, interval='1min', outputsize=100)
                
                if df is None or df.empty:
                    logger.warning(f'TwelveData returned no data for {pair}, skipping...')
                    continue
                    
            except Exception as e:
                logger.warning(f'TwelveData fetch failed for {pair}: {e}, trying Alpha Vantage...')
                try:
                    df = alpha_vantage.get_forex_data(from_sym, to_sym)
                    if df is None or df.empty:
                        continue
                except Exception as av_error:
                    logger.warning(f'Alpha Vantage also failed for {pair}: {av_error}')
                    continue
            
            if df is not None and not df.empty:
                signal = get_signal_generator().generate_signal(df, pair)
                
                if signal:
                    # ✅ Save signal to database with user_id
                    try:
                        db_signal = Signal(
                            user_id=user_id,
                            symbol=pair,
                            signal_type=signal.signal.value,
                            price=signal.price,
                            confidence=signal.confidence,
                            reason=signal.reason,
                            rsi_signal=signal.rsi_signal.to_dict() if signal.rsi_signal else None,
                            ma_signal=signal.ma_signal.to_dict() if signal.ma_signal else None,
                            sr_signal=signal.sr_signal.to_dict() if signal.sr_signal else None,
                            ai_prediction=signal.ai_prediction if signal.ai_prediction else {},
                            filter_results=signal.filter_results if signal.filter_results else {}
                        )
                        db.session.add(db_signal)
                        db.session.commit()
                        logger.info(f'Signal saved to database for user {user_id}: {pair}')
                    except Exception as db_error:
                        db.session.rollback()
                        logger.error(f'Error saving signal to database: {db_error}')
                    
                    results.append(signal.to_dict())
                    
                    # Send notifications for strong signals
                    if signal.signal.value != 'HOLD':
                        telegram_notifier.send_signal(signal)
        
        return jsonify({
            'success': True,
            'analyzed': len(results),
            'signals': results,
            'user_id': user_id
        }), 200
    
    except Exception as e:
        logger.error(f'Error analyzing pairs: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get bot configuration"""
    return jsonify({
        'currency_pairs': config.CURRENCY_PAIRS,
        'rsi_period': config.RSI_PERIOD,
        'rsi_overbought': config.RSI_OVERBOUGHT,
        'rsi_oversold': config.RSI_OVERSOLD,
        'update_interval': config.UPDATE_INTERVAL,
        'telegram_enabled': telegram_notifier.is_configured(),
        'email_enabled': email_notifier.is_configured()
    }), 200

@app.route('/api/chart-data', methods=['GET'])
def get_chart_data():
    """Get OHLC data for charting with TwelveData priority
    
    Query params:
    - symbol: Currency pair (e.g., EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, etc.)
    - timeframe: Timeframe in minutes (1, 5, 15, 60, 240, 1440)
    - live: Boolean to fetch live data first (default: true)
    """
    try:
        symbol = request.args.get('symbol', 'EURUSD').upper().strip()
        timeframe = request.args.get('timeframe', '60')
        live = request.args.get('live', 'true').lower() == 'true'
        
        # Validate symbol format (must be 6 characters like EURUSD)
        if len(symbol) != 6:
            return jsonify({'error': f'Invalid symbol format. Expected 6-char pair like EURUSD, got {symbol}'}), 400
        
        # Map timeframe minutes to TwelveData/Alpha Vantage intervals
        timeframe_map = {
            '1': '1min',
            '5': '5min',
            '15': '15min',
            '60': '1h',
            '240': '4h',
            '1440': '1day'
        }
        
        interval = timeframe_map.get(timeframe, '1h')
        ohlc_data = None
        data_source = None
        
        # Priority 1: Try TwelveData first (most reliable for forex)
        if live:
            symbol_formatted = f"{symbol[:3]}/{symbol[3:6]}"
            logger.info(f'[CHART] Fetching live data for {symbol_formatted} ({interval}) - Priority: TwelveData')
            
            try:
                ohlc_data = twelvedata.get_time_series(
                    symbol_formatted, 
                    interval=interval, 
                    outputsize=100
                )
                if ohlc_data is not None and not ohlc_data.empty:
                    data_source = 'TwelveData'
                    logger.info(f'[CHART] ✓ TwelveData SUCCESS: {len(ohlc_data)} candles for {symbol_formatted}')
            except Exception as e:
                logger.warning(f'[CHART] TwelveData failed: {e}')
            
            # Priority 2: Fallback to Alpha Vantage live fetch
            if ohlc_data is None or ohlc_data.empty:
                logger.warning(f'[CHART] TwelveData unavailable, trying Alpha Vantage live fetch for {symbol}')
                from_symbol = symbol[:3]
                to_symbol = symbol[3:6]
                
                try:
                    ohlc_data = alpha_vantage.get_forex_data_live(from_symbol, to_symbol, 'daily')
                    if ohlc_data is not None and not ohlc_data.empty:
                        data_source = 'Alpha Vantage (Live)'
                        logger.info(f'[CHART] ✓ Alpha Vantage LIVE SUCCESS: {len(ohlc_data)} candles for {symbol}')
                except Exception as e:
                    logger.warning(f'[CHART] Alpha Vantage live fetch failed: {e}')
        
        # Priority 3: Fallback to cached data
        if ohlc_data is None or ohlc_data.empty:
            logger.warning(f'[CHART] Live data unavailable for {symbol}, using cached data')
            from_symbol = symbol[:3]
            to_symbol = symbol[3:6]
            
            try:
                ohlc_data = alpha_vantage.get_daily_data(from_symbol, to_symbol)
                if ohlc_data is not None and not ohlc_data.empty:
                    data_source = 'Alpha Vantage (Cache)'
                    logger.info(f'[CHART] ✓ Cache HIT: {len(ohlc_data)} candles for {symbol}')
            except Exception as e:
                logger.warning(f'[CHART] Cache retrieval failed: {e}')
        
        if ohlc_data is None or ohlc_data.empty:
            return jsonify({
                'error': f'No data available for {symbol} from any source',
                'tried': ['TwelveData', 'Alpha Vantage (Live)', 'Alpha Vantage (Cache)']
            }), 404
        
        # Normalize column names to lowercase
        ohlc_data.columns = ohlc_data.columns.str.lower()
        
        # Handle different index formats (TwelveData uses 'datetime' column)
        if 'datetime' in ohlc_data.columns:
            ohlc_data.set_index('datetime', inplace=True)
        
        # Format data for chart
        chart_ohlc = []
        for idx, row in ohlc_data.iterrows():
            try:
                # Convert index to unix timestamp
                if isinstance(idx, str):
                    from datetime import datetime
                    try:
                        timestamp = datetime.strptime(idx, '%Y-%m-%d %H:%M:%S')
                        unix_time = int(timestamp.timestamp() * 1000)
                    except:
                        unix_time = int(pd.Timestamp(idx).timestamp() * 1000)
                else:
                    unix_time = int(pd.Timestamp(idx).timestamp() * 1000)
                
                chart_ohlc.append({
                    'time': unix_time,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close'])
                })
            except Exception as e:
                logger.warning(f'[CHART] Skipping row due to error: {e}')
                continue
        
        logger.info(f'[CHART] Successfully formatted {len(chart_ohlc)} candles for chart from {data_source}')
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'interval': interval,
            'ohlc': chart_ohlc,
            'count': len(chart_ohlc),
            'source': data_source
        }), 200
        
    except Exception as e:
        logger.error(f'[CHART] Unexpected error: {e}')
        return jsonify({'error': f'Chart data error: {str(e)}'}), 500

# ==================== RECOMMENDATIONS ENDPOINTS ====================

@app.route('/api/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get pair recommendations based on signal history"""
    try:
        user_id = int(get_jwt_identity())
        hours = request.args.get('hours', 24, type=int)
        
        logger.info(f'📊 [RECOMMENDATIONS] Getting for user {user_id} (last {hours} hours)')
        
        stats = recommendation_engine.get_pair_stats(user_id, hours_lookback=hours)
        
        return jsonify({
            'success': True,
            'recommendations': stats['recommendations'],
            'total_pairs': stats['total_pairs_analyzed'],
            'period_hours': stats['period_hours'],
            'timestamp': stats['timestamp']
        }), 200
        
    except Exception as e:
        logger.error(f'❌ [RECOMMENDATIONS] Error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user_info():
    """Get current user information including API key and token usage"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'plan': user.plan,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'api_key': user.api_key,
            'api_key_created_at': user.api_key_created_at.isoformat(),
            'api_key_last_used': user.api_key_last_used.isoformat() if user.api_key_last_used else None,
            'created_at': user.created_at.isoformat(),
            'last_active': user.last_active.isoformat() if user.last_active else None,
            'token_usage': {
                'tokens_used_today': user.tokens_used_today,
                'tokens_limit': user.get_token_limit(),
                'tokens_remaining': user.get_tokens_remaining(),
                'plan': user.plan
            }
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Error getting user info: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/api-key/regenerate', methods=['POST'])
@jwt_required()
def regenerate_api_key():
    """Generate a new API key for the user"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate new API key
        new_api_key = user.regenerate_api_key()
        db.session.commit()
        
        logger.info(f'✅ API key regenerated for user {user_id}')
        
        return jsonify({
            'success': True,
            'api_key': new_api_key,
            'api_key_created_at': user.api_key_created_at.isoformat(),
            'message': 'API key successfully regenerated'
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Error regenerating API key: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== USER PREFERENCES ENDPOINTS ====================

@app.route('/api/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get user preferences"""
    try:
        user_id = int(get_jwt_identity())
        
        prefs = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not prefs:
            # Create default preferences
            prefs = UserPreference(user_id=user_id)
            db.session.add(prefs)
            db.session.commit()
            logger.info(f'Created default preferences for user {user_id}')
        
        return jsonify(prefs.to_dict()), 200
        
    except Exception as e:
        logger.error(f'❌ Error getting preferences: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/preferences', methods=['POST'])
@jwt_required()
def update_preferences():
    """Update user preferences"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        
        prefs = UserPreference.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            db.session.add(prefs)
        
        # Update fields if provided
        if 'monitored_pairs' in data:
            prefs.monitored_pairs = data['monitored_pairs']
        if 'auto_analysis_enabled' in data:
            prefs.auto_analysis_enabled = data['auto_analysis_enabled']
        if 'auto_analysis_interval' in data:
            prefs.auto_analysis_interval = data['auto_analysis_interval']
        if 'min_confidence_threshold' in data:
            prefs.min_confidence_threshold = data['min_confidence_threshold']
        if 'alert_on_high_confidence' in data:
            prefs.alert_on_high_confidence = data['alert_on_high_confidence']
        if 'alert_high_confidence_threshold' in data:
            prefs.alert_high_confidence_threshold = data['alert_high_confidence_threshold']
        
        db.session.commit()
        
        logger.info(f'✅ Updated preferences for user {user_id}')
        
        return jsonify({
            'success': True,
            'preferences': prefs.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Error updating preferences: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== AUTO-ANALYSIS SCHEDULER ENDPOINTS ====================

@app.route('/api/auto-analysis/start', methods=['POST'])
@jwt_required()
def start_auto_analysis():
    """Start auto-analysis for user"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json or {}
        
        # Get user preferences
        prefs = UserPreference.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            db.session.add(prefs)
            db.session.commit()
        
        pairs = data.get('pairs', prefs.monitored_pairs)
        interval = data.get('interval_seconds', prefs.auto_analysis_interval)
        
        # Define analyze function to pass to scheduler
        def analyze_user_pair(uid, symbol):
            """Analyze a pair for a user"""
            try:
                # Get JWT token for internal request
                from src.api.auth import create_access_token
                token = create_access_token(identity=uid)
                
                # Make internal request
                from flask import current_app
                with current_app.test_client() as client:
                    response = client.post(
                        '/api/analyze',
                        json={'symbol': symbol, 'notify': False},
                        headers={'Authorization': f'Bearer {token}'}
                    )
                    return response.get_json()
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Add job to scheduler
        success = scheduler.add_auto_analysis_job(
            user_id,
            analyze_user_pair,
            pairs,
            interval
        )
        
        if success:
            # Update preferences
            prefs.auto_analysis_enabled = True
            prefs.auto_analysis_interval = interval
            prefs.monitored_pairs = pairs
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Auto-analysis started for {len(pairs)} pairs',
                'pairs': pairs,
                'interval_seconds': interval
            }), 200
        else:
            return jsonify({'error': 'Failed to start auto-analysis'}), 500
            
    except Exception as e:
        logger.error(f'❌ Error starting auto-analysis: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-analysis/stop', methods=['POST'])
@jwt_required()
def stop_auto_analysis():
    """Stop auto-analysis for user"""
    try:
        user_id = int(get_jwt_identity())
        
        success = scheduler.remove_auto_analysis_job(user_id)
        
        if success:
            # Update preferences
            prefs = UserPreference.query.filter_by(user_id=user_id).first()
            if prefs:
                prefs.auto_analysis_enabled = False
                db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Auto-analysis stopped'
            }), 200
        else:
            return jsonify({'success': False, 'message': 'No active auto-analysis job'}), 200
            
    except Exception as e:
        logger.error(f'❌ Error stopping auto-analysis: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-analysis/status', methods=['GET'])
@jwt_required()
def get_auto_analysis_status():
    """Get auto-analysis status for user"""
    try:
        user_id = int(get_jwt_identity())
        
        jobs = scheduler.get_user_jobs(user_id)
        
        return jsonify({
            'success': True,
            'active': len(jobs) > 0,
            'jobs': jobs
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Error getting auto-analysis status: {e}')
        return jsonify({'error': str(e)}), 500

# ==================== MT5 ACCOUNT ENDPOINTS - REMOVED ====================
# All old MT5 endpoints have been removed to prevent conflicts with isolated routes
# Use /api/mt5/* endpoints from mt5_isolation_bp blueprint for proper user isolation


# ==================== LIGHTWEIGHT OPTIMIZATION ENDPOINTS ====================
# These endpoints return minimal data to reduce bandwidth usage

@app.route('/api/signals/latest', methods=['GET'])
@jwt_required()
def get_latest_signals():
    """
    Get only the latest signals (lightweight version)
    Returns minimal fields: symbol, signal, confidence, timestamp
    
    Query params:
    - limit: Number of signals to return (default: 20)
    """
    try:
        user_id = int(get_jwt_identity())
        limit = min(request.args.get('limit', 20, type=int), 100)  # Max 100
        
        logger.info(f'🚀 [LIGHTWEIGHT] Getting latest {limit} signals for user {user_id}')
        
        signals = Signal.query.filter_by(user_id=user_id)\
            .order_by(Signal.created_at.desc())\
            .limit(limit)\
            .all()
        
        # Return minimal fields only
        lightweight_signals = []
        for s in signals:
            lightweight_signals.append({
                'id': s.id,
                'symbol': s.symbol,
                'signal': s.signal_type,
                'confidence': round(s.confidence, 3),
                'timestamp': s.created_at.isoformat(),
                'price': round(s.price, 5) if s.price else None
            })
        
        return jsonify({
            'signals': lightweight_signals,
            'count': len(lightweight_signals),
            'user_id': user_id
        }), 200
    except Exception as e:
        logger.error(f'❌ Error getting latest signals: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/summary', methods=['GET'])
@jwt_required()
def get_stats_summary():
    """
    Get lightweight statistics summary (no detailed breakdowns)
    Returns: total, buys, sells, avg_confidence
    
    Much more efficient than fetching all signals and calculating client-side
    """
    try:
        user_id = int(get_jwt_identity())
        
        logger.info(f'📊 [LIGHTWEIGHT] Getting stats summary for user {user_id}')
        
        # Get counts with single query
        total = Signal.query.filter_by(user_id=user_id).count()
        buys = Signal.query.filter_by(user_id=user_id, signal_type='BUY').count()
        sells = Signal.query.filter_by(user_id=user_id, signal_type='SELL').count()
        holds = Signal.query.filter_by(user_id=user_id, signal_type='HOLD').count()
        
        # Get average confidence
        avg_conf_result = db.session.query(db.func.avg(Signal.confidence))\
            .filter_by(user_id=user_id).scalar()
        avg_confidence = float(avg_conf_result) if avg_conf_result else 0.0
        
        # Get latest signal timestamp
        latest = Signal.query.filter_by(user_id=user_id)\
            .order_by(Signal.created_at.desc()).first()
        last_signal_time = latest.created_at.isoformat() if latest else None
        
        return jsonify({
            'total': total,
            'buys': buys,
            'sells': sells,
            'holds': holds,
            'avg_confidence': round(avg_confidence, 3),
            'last_signal': last_signal_time,
            'user_id': user_id
        }), 200
    except Exception as e:
        logger.error(f'❌ Error getting stats summary: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/health/minimal', methods=['GET'])
def health_minimal():
    """
    Minimal health check endpoint (no auth required)
    Returns: status only
    """
    return jsonify({'status': 'ok'}), 200


# ===== MT5 EA Signal Endpoint =====
@app.route('/signal', methods=['GET'])
def get_trading_signal():
    """
    MT5 EA Trading Signal Endpoint
    
    Query Parameters:
        - apikey: User's API key (required)
        - symbol: Currency pair (e.g., EURUSD) (required)
        - timeframe: Timeframe (M5, M15, H1, etc.) (optional, default: M5)
        - format: Response format - 'json' or 'text' (optional, default: json)
        - lite: Use Phase 1 lite engine (true/false) - optional, default: true
        - ai: Use Phase 4 AI Layer with sentiment + patterns (true/false) - optional
    
    Returns:
        JSON: {"signal": "BUY", "confidence": 0.78, "timestamp": "..."}
        OR
        TEXT: BUY
    
    Status Codes:
        200: Signal generated successfully
        400: Missing or invalid parameters
        401: Invalid API key
        500: Server error
    
    Example:
        GET /signal?apikey=YOUR_KEY&symbol=EURUSD&timeframe=M5&format=json
        GET /signal?apikey=YOUR_KEY&symbol=EURUSD&lite=true  (Phase 1: <50ms)
        GET /signal?apikey=YOUR_KEY&symbol=EURUSD&lite=false (Phase 2+: Full analysis)
        GET /signal?apikey=YOUR_KEY&symbol=EURUSD&ai=true    (Phase 4: AI + Sentiment + Patterns)
    """
    try:
        # Get query parameters
        api_key = request.args.get('apikey', '').strip()
        symbol = request.args.get('symbol', '').upper().strip()
        timeframe = request.args.get('timeframe', 'M5').upper().strip()
        response_format = request.args.get('format', 'json').lower()
        
        # NEW: Phase parameter - use lite engine by default for speed
        lite_param = request.args.get('lite', 'true').lower()
        use_lite = lite_param == 'true'
        
        # Validate required parameters
        if not api_key:
            logger.warning('❌ [SIGNAL] Missing API key')
            return jsonify({'error': 'Missing apikey parameter'}), 400
        
        if not symbol:
            logger.warning('❌ [SIGNAL] Missing symbol')
            return jsonify({'error': 'Missing symbol parameter'}), 400
        
        # Validate symbol format (should be 6 chars like EURUSD)
        if len(symbol) != 6:
            logger.warning(f'❌ [SIGNAL] Invalid symbol format: {symbol}')
            return jsonify({'error': f'Invalid symbol format. Expected 6 characters (e.g., EURUSD), got {symbol}'}), 400
        
        # Validate response format
        if response_format not in ['json', 'text']:
            response_format = 'json'
        
        # NEW: AI parameter - use Phase 4 AI Layer if requested
        ai_param = request.args.get('ai', 'false').lower()
        use_ai = ai_param == 'true'
        
        # Authenticate user by API key
        user = User.query.filter_by(api_key=api_key).first()
        
        if not user:
            logger.warning(f'❌ [SIGNAL] Invalid API key attempted')
            return jsonify({'error': 'Invalid API key'}), 401
        
        logger.info(f'✅ [SIGNAL] User {user.id} ({user.email}) requesting signal for {symbol} {timeframe} (lite={use_lite})')
        
        # Update last_used timestamp for the API key
        user.api_key_last_used = datetime.utcnow()
        db.session.commit()
        
        # Parse symbol
        from_sym = symbol[:3]
        to_sym = symbol[3:]
        
        # Fetch market data
        try:
            logger.info(f'📡 [SIGNAL] Fetching data for {symbol} on {timeframe}...')
            
            # Try TwelveData first (real-time)
            try:
                td_symbol = f"{from_sym}/{to_sym}"
                df = twelvedata.get_time_series(td_symbol, interval='1min', outputsize=100)
                data_source = 'TwelveData'
            except Exception as e:
                logger.warning(f'TwelveData failed, using Alpha Vantage: {e}')
                df = alpha_vantage.get_forex_data(from_sym, to_sym)
                data_source = 'AlphaVantage'
            
            if df is None or df.empty:
                logger.error(f'❌ [SIGNAL] Failed to fetch data for {symbol}')
                return jsonify({'error': f'Failed to fetch market data for {symbol}'}), 500
            
            # Normalize column names
            if 'open' in df.columns:
                df = df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
            
            # Generate signal using PhaseRouter (lite, full, or AI engine)
            router = get_phase_router()
            signal_result = router.get_signal(df, symbol, lite=use_lite, ai=use_ai)
            
            if signal_result is None:
                logger.info(f'⚠️ [SIGNAL] No clear signal for {symbol}')
                response_data = {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'message': 'No clear signal',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_points': len(df),
                    'data_source': data_source,
                    'phase': 1 if use_lite else 2
                }
            else:
                # Handle response from different engines
                if isinstance(signal_result, dict):
                    signal_value = signal_result.get('signal', 'HOLD')
                    confidence = signal_result.get('confidence', 0.0)
                    response_time = signal_result.get('response_time_ms', 0)
                    phase = signal_result.get('phase', 1)
                    
                    logger.info(f'✅ [SIGNAL] {symbol}: {signal_value} (confidence: {confidence}, {response_time}ms, phase={phase})')
                    
                    # Build base response
                    response_data = {
                        'signal': signal_value,
                        'confidence': confidence,
                        'timestamp': signal_result.get('timestamp', datetime.utcnow().isoformat()),
                        'data_points': len(df),
                        'data_source': data_source,
                        'phase': phase,
                        'response_time_ms': response_time
                    }
                    
                    # Add Phase 1 (Lite) specific fields
                    if phase == 1:
                        response_data.update({
                            'price': signal_result.get('price'),
                            'ma50': signal_result.get('ma50'),
                            'rsi': signal_result.get('rsi'),
                            'momentum_pct': signal_result.get('momentum_pct'),
                            'reason': signal_result.get('reason')
                        })
                    
                    # Add Phase 4 (AI Layer) specific fields
                    elif phase == 4:
                        response_data.update({
                            'price': signal_result.get('price'),
                            'sentiment': signal_result.get('sentiment'),
                            'patterns': signal_result.get('patterns'),
                            'news': signal_result.get('news'),
                            'technical': signal_result.get('technical'),
                            'analysis': signal_result.get('analysis')
                        })
                else:
                    # Full engine returns object
                    signal_value = signal_result.signal.value
                    confidence = signal_result.confidence
                    
                    logger.info(f'✅ [SIGNAL] {symbol}: {signal_value} (confidence: {confidence:.2f})')
                    
                    response_data = {
                        'signal': signal_value,
                        'confidence': round(confidence, 2),
                        'timestamp': datetime.utcnow().isoformat(),
                        'data_points': len(df),
                        'data_source': data_source,
                        'phase': 2,
                        'reason': signal_result.reason
                    }
            
            # Return response in requested format
            if response_format == 'text':
                return response_data['signal'], 200, {'Content-Type': 'text/plain'}
            else:
                return jsonify(response_data), 200
        
        except APIRateLimitError as e:
            logger.error(f'❌ [SIGNAL] API rate limit for {symbol}')
            return jsonify({
                'error': 'API_RATE_LIMIT',
                'message': 'API rate limit reached. Please try again later.',
                'signal': 'HOLD'
            }), 429
        
        except Exception as e:
            logger.error(f'❌ [SIGNAL] Error analyzing {symbol}: {e}', exc_info=True)
            return jsonify({
                'error': str(e),
                'message': f'Failed to generate signal for {symbol}'
            }), 500
    
    except Exception as e:
        logger.error(f'❌ [SIGNAL] Unexpected error: {e}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


# ===== Multi-Pair Scanner Endpoint =====
@app.route('/scan', methods=['GET'])
def scan_all_pairs():
    """
    Multi-Pair Signal Scanner Endpoint
    
    Scans multiple forex pairs and returns ONLY the BEST opportunity.
    
    Query Parameters:
        - apikey: User's API key (required)
        - format: Response format - 'json' or 'text' (optional, default: json)
    
    Returns:
        JSON: {"best_opportunity": {"symbol": "GBPUSD", "signal": "BUY", "confidence": 0.82}, ...}
        OR
        TEXT: GBPUSD BUY 0.82
    
    Watchlist:
        - EURUSD, GBPUSD, USDJPY, XAUUSD, AUDUSD
    
    Status Codes:
        200: Signal generated successfully
        400: Missing or invalid parameters
        401: Invalid API key
        500: Server error
    
    Example:
        GET /scan?apikey=YOUR_KEY
        GET /scan?apikey=YOUR_KEY&format=json
    """
    try:
        # Get query parameters
        api_key = request.args.get('apikey', '').strip()
        response_format = request.args.get('format', 'json').lower()
        
        # Validate API key
        if not api_key:
            logger.warning('❌ [SCAN] Missing API key')
            return jsonify({'error': 'Missing apikey parameter'}), 400
        
        # Authenticate user by API key
        user = User.query.filter_by(api_key=api_key).first()
        
        if not user:
            logger.warning(f'❌ [SCAN] Invalid API key attempted')
            return jsonify({'error': 'Invalid API key'}), 401
        
        logger.info(f'✅ [SCAN] User {user.id} ({user.email}) requesting multi-pair scan')
        
        # Update last_used timestamp
        user.api_key_last_used = datetime.utcnow()
        db.session.commit()
        
        # Initialize scanner and scan all pairs
        from src.signals.multi_pair_scanner import MultiPairScanner
        scanner = MultiPairScanner()
        
        result = scanner.scan_all(api_key)
        
        if response_format == 'text':
            if result.get('best_opportunity'):
                best = result['best_opportunity']
                return f"{best['symbol']} {best['signal']} {best['confidence']}", 200, {'Content-Type': 'text/plain'}
            else:
                return "NO SIGNAL", 200, {'Content-Type': 'text/plain'}
        else:
            return jsonify(result), 200
    
    except Exception as e:
        logger.error(f'❌ [SCAN] Error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def serve_index():
    """Serve the frontend index.html"""
    try:
        logger.info(f'📁 Serving index.html from {frontend_path}')
        index_file = os.path.join(frontend_path, 'index.html')
        if not os.path.exists(index_file):
            logger.error(f'❌ index.html not found at {index_file}')
            return jsonify({'error': 'index.html not found'}), 500
        return send_file(index_file)
    except Exception as e:
        logger.error(f'❌ Error serving index.html: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Serve static files from the frontend directory"""
    file_path = os.path.join(frontend_path, path)
    if os.path.isfile(file_path):
        return send_from_directory(frontend_path, path)
    # If not a file, return 404 to let Flask handle it
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    """Shutdown scheduler when app stops"""
    scheduler.stop()

if __name__ == '__main__':
    logger.info('Starting SofAi FX API server...')
    try:
        app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
    finally:
        scheduler.stop()
