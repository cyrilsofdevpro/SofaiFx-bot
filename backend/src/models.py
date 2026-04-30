"""
User model and database initialization for SofAi FX authentication system
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import secrets

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  # User's full name
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(20), default='free', nullable=False)  # free, premium, enterprise
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # Admin access flag
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # MT5 Connection Credentials (encrypted)
    mt5_login = db.Column(db.String(255), nullable=True)  # Encrypted MT5 login ID
    mt5_password = db.Column(db.String(255), nullable=True)  # Encrypted MT5 password
    mt5_server = db.Column(db.String(100), nullable=True)  # MT5 server name
    mt5_connected = db.Column(db.Boolean, default=False, nullable=False)  # Connection status
    mt5_connection_time = db.Column(db.DateTime, nullable=True)  # When connection was established
    mt5_account_number = db.Column(db.String(20), nullable=True)  # MT5 account number (for reference)
    
    # API Key for programmatic access
    api_key = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(48))
    api_key_created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    api_key_last_used = db.Column(db.DateTime, nullable=True)  # When the API key was last used
    
    # Token usage tracking (for plan limits)
    tokens_used_today = db.Column(db.Integer, default=0)  # Tokens used today
    tokens_reset_at = db.Column(db.DateTime, default=datetime.utcnow)  # Last token reset time
    
    # Relationships
    signals = db.relationship('Signal', back_populates='user', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', back_populates='user', lazy=True, cascade='all, delete-orphan')
    execution_logs = db.relationship('ExecutionLog', back_populates='user', lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', back_populates='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.name} ({self.email})>'
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        try:
            return bcrypt.check_password_hash(self.password, password)
        except Exception:
            return False
    
    def regenerate_api_key(self):
        """Generate a new API key"""
        self.api_key = secrets.token_urlsafe(48)
        self.api_key_created_at = datetime.utcnow()
        self.api_key_last_used = None
        return self.api_key
    
    def get_token_limit(self):
        """Get token limit based on plan"""
        limits = {
            'free': 15,
            'premium': 1000,
            'enterprise': -1  # Unlimited
        }
        return limits.get(self.plan, 15)
    
    def can_use_token(self):
        """Check if user can use more tokens today"""
        # Enterprise plan has unlimited
        if self.plan == 'enterprise':
            return True
        
        limit = self.get_token_limit()
        
        # Reset daily count if it's a new day
        if self.tokens_reset_at:
            now = datetime.utcnow()
            if self.tokens_reset_at.date() < now.date():
                self.tokens_used_today = 0
                self.tokens_reset_at = now
                db.session.commit()
        
        return self.tokens_used_today < limit
    
    def consume_token(self):
        """Consume one token if allowed, return False if limit reached"""
        # Enterprise plan has unlimited
        if self.plan == 'enterprise':
            return True
        
        if not self.can_use_token():
            return False
        
        # Reset daily count if it's a new day
        if self.tokens_reset_at:
            now = datetime.utcnow()
            if self.tokens_reset_at.date() < now.date():
                self.tokens_used_today = 0
                self.tokens_reset_at = now
        
        self.tokens_used_today += 1
        db.session.commit()
        return True
    
    def get_tokens_remaining(self):
        """Get remaining tokens for today"""
        if self.plan == 'enterprise':
            return -1  # Unlimited
        
        limit = self.get_token_limit()
        
        # Reset daily count if it's a new day
        if self.tokens_reset_at:
            now = datetime.utcnow()
            if self.tokens_reset_at.date() < now.date():
                self.tokens_used_today = 0
                self.tokens_reset_at = now
                db.session.commit()
        
        return max(0, limit - self.tokens_used_today)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'plan': self.plan,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'mt5_connected': self.mt5_connected,
            'mt5_account_number': self.mt5_account_number,
            'mt5_connection_time': self.mt5_connection_time.isoformat() if self.mt5_connection_time else None,
            'api_key': self.api_key,
            'api_key_created_at': self.api_key_created_at.isoformat(),
            'api_key_last_used': self.api_key_last_used.isoformat() if self.api_key_last_used else None,
            'tokens_used_today': self.tokens_used_today,
            'tokens_limit': self.get_token_limit(),
            'tokens_remaining': self.get_tokens_remaining()
        }


class Signal(db.Model):
    """Signal model for storing trading signals per user"""
    __tablename__ = 'signals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False)
    signal_type = db.Column(db.String(20), nullable=False)  # BUY, SELL, HOLD
    price = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    rsi_signal = db.Column(db.JSON, nullable=True)
    ma_signal = db.Column(db.JSON, nullable=True)
    sr_signal = db.Column(db.JSON, nullable=True)
    ai_prediction = db.Column(db.JSON, nullable=True)
    filter_results = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship back-reference
    user = db.relationship('User', back_populates='signals')
    
    def __repr__(self):
        return f'<Signal {self.symbol} {self.signal_type} by User {self.user_id}>'
    
    def to_dict(self):
        """Convert signal to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'signal': self.signal_type,
            'price': self.price,
            'confidence': self.confidence,
            'reason': self.reason,
            'timestamp': self.created_at.isoformat(),
            'rsi_signal': self.rsi_signal,
            'ma_signal': self.ma_signal,
            'sr_signal': self.sr_signal,
            'ai_prediction': self.ai_prediction or {},
            'filter_results': self.filter_results or {}
        }


class UserPreference(db.Model):
    """User preferences for pair monitoring and auto-analysis"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Monitoring preferences
    monitored_pairs = db.Column(db.JSON, default=lambda: ["EURUSD", "GBPUSD", "USDJPY"], nullable=False)  # List of pairs
    auto_analysis_enabled = db.Column(db.Boolean, default=False, nullable=False)
    auto_analysis_interval = db.Column(db.Integer, default=3600, nullable=False)  # seconds (default 1 hour)
    min_confidence_threshold = db.Column(db.Float, default=0.7, nullable=False)  # Min confidence for alerts
    
    # Alert preferences
    alert_on_high_confidence = db.Column(db.Boolean, default=True, nullable=False)
    alert_high_confidence_threshold = db.Column(db.Float, default=0.8, nullable=False)
    
    # Execution preferences
    execution_enabled = db.Column(db.Boolean, default=False, nullable=False)  # Enable MT5 execution
    risk_per_trade = db.Column(db.Float, default=1.0, nullable=False)  # Risk % per trade (1-2%)
    max_open_positions = db.Column(db.Integer, default=5, nullable=False)
    max_daily_loss = db.Column(db.Float, default=5.0, nullable=False)  # Max daily loss %
    min_spread_threshold = db.Column(db.Float, default=10.0, nullable=False)  # Max acceptable spread in pips
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPreference user_id={self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'monitored_pairs': self.monitored_pairs,
            'auto_analysis_enabled': self.auto_analysis_enabled,
            'auto_analysis_interval': self.auto_analysis_interval,
            'min_confidence_threshold': self.min_confidence_threshold,
            'alert_on_high_confidence': self.alert_on_high_confidence,
            'alert_high_confidence_threshold': self.alert_high_confidence_threshold,
            'execution_enabled': self.execution_enabled,
            'risk_per_trade': self.risk_per_trade,
            'max_open_positions': self.max_open_positions,
            'max_daily_loss': self.max_daily_loss,
            'min_spread_threshold': self.min_spread_threshold
        }


class Trade(db.Model):
    """Trade model for storing executed trades"""
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    signal_id = db.Column(db.Integer, db.ForeignKey('signals.id'), nullable=True)  # Original signal
    
    # Trade identifiers
    mt5_order_id = db.Column(db.Integer, nullable=True, unique=True)  # MT5 order/position ID
    symbol = db.Column(db.String(20), nullable=False, index=True)
    trade_type = db.Column(db.String(10), nullable=False)  # BUY, SELL
    
    # Entry details
    entry_price = db.Column(db.Float, nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Risk management
    stop_loss = db.Column(db.Float, nullable=False)
    take_profit = db.Column(db.Float, nullable=False)
    lot_size = db.Column(db.Float, nullable=False)
    risk_percent = db.Column(db.Float, nullable=False)
    
    # Exit details
    exit_price = db.Column(db.Float, nullable=True)
    exit_time = db.Column(db.DateTime, nullable=True)
    pnl = db.Column(db.Float, nullable=True)  # Profit/Loss
    pnl_percent = db.Column(db.Float, nullable=True)  # P/L %
    
    # Status
    status = db.Column(db.String(20), default='OPEN', nullable=False, index=True)  # OPEN, CLOSED, CANCELLED, PENDING
    close_reason = db.Column(db.String(100), nullable=True)  # TP hit, SL hit, Manual, Signal reversal, etc.
    
    # Metadata
    strategy_name = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back-reference
    user = db.relationship('User', back_populates='trades')
    
    def __repr__(self):
        return f'<Trade {self.symbol} {self.trade_type} User {self.user_id} ({self.status})>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'signal_id': self.signal_id,
            'mt5_order_id': self.mt5_order_id,
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'lot_size': self.lot_size,
            'risk_percent': self.risk_percent,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'status': self.status,
            'close_reason': self.close_reason,
            'strategy_name': self.strategy_name,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


class ExecutionLog(db.Model):
    """Execution log for tracking all trade execution events"""
    __tablename__ = 'execution_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Event details
    event_type = db.Column(db.String(50), nullable=False, index=True)  # SIGNAL_RECEIVED, VALIDATION_PASSED, ORDER_PLACED, ORDER_FILLED, ORDER_CANCELLED, etc.
    event_status = db.Column(db.String(20), nullable=False)  # SUCCESS, FAILED, PENDING
    message = db.Column(db.Text, nullable=False)
    
    # Data snapshot
    symbol = db.Column(db.String(20), nullable=True)
    order_details = db.Column(db.JSON, nullable=True)  # JSON of order params, response, etc.
    error_details = db.Column(db.JSON, nullable=True)  # Error info if applicable
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship back-references
    user = db.relationship('User', back_populates='execution_logs')
    
    def __repr__(self):
        return f'<ExecutionLog {self.event_type} {self.event_status} User {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_status': self.event_status,
            'message': self.message,
            'symbol': self.symbol,
            'order_details': self.order_details or {},
            'error_details': self.error_details or {},
            'created_at': self.created_at.isoformat()
        }


class APIKey(db.Model):
    """Multiple API Keys per user for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Key details
    key = db.Column(db.String(64), unique=True, nullable=False, index=True, default=lambda: secrets.token_urlsafe(48))
    name = db.Column(db.String(100), nullable=False)  # Friendly name (e.g., "EA Key", "Dashboard Key")
    description = db.Column(db.Text, nullable=True)
    
    # Status and permissions
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    scope = db.Column(db.String(100), default='signal', nullable=False)  # signal, trade, full
    
    # Usage tracking
    last_used = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    rate_limit = db.Column(db.Integer, default=100, nullable=False)  # Requests per hour
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    
    # Relationship
    user = db.relationship('User', back_populates='api_keys')
    
    def __repr__(self):
        return f'<APIKey {self.name} for User {self.user_id}>'
    
    def is_valid(self):
        """Check if API key is valid"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def to_dict(self, include_key=False):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'key': self.key if include_key else self.key[:8] + '...' + self.key[-8:],
            'is_active': self.is_active,
            'scope': self.scope,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'rate_limit': self.rate_limit,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_valid': self.is_valid()
        }


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    bcrypt.init_app(app)
    with app.app_context():
        db.create_all()
        return db
