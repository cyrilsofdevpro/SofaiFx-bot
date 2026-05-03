"""
MongoDB User model for SofAi FX authentication system
Replaces SQLAlchemy models with MongoDB for persistent storage
"""

from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, ListField, ReferenceField
from flask_bcrypt import Bcrypt
from datetime import datetime
import secrets
import os

bcrypt = Bcrypt()

class User(Document):
    """User model for MongoDB"""
    meta = {'collection': 'users'}

    name = StringField(required=True, max_length=120)
    email = StringField(required=True, unique=True, max_length=120)
    password = StringField(required=True, max_length=255)
    plan = StringField(default='free', max_length=20)  # free, premium, enterprise
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)  # Admin access flag
    last_active = DateTimeField(default=datetime.utcnow)

    # MT5 Connection Credentials (encrypted)
    mt5_login = StringField(max_length=255)  # Encrypted MT5 login ID
    mt5_password = StringField(max_length=255)  # Encrypted MT5 password
    mt5_server = StringField(max_length=100)  # MT5 server name
    mt5_connected = BooleanField(default=False)  # Connection status
    mt5_connection_time = DateTimeField()  # When connection was established
    mt5_account_number = StringField(max_length=20)  # MT5 account number (for reference)

    # API Key for programmatic access
    api_key = StringField(unique=True, default=lambda: secrets.token_urlsafe(48), max_length=64)
    api_key_created_at = DateTimeField(default=datetime.utcnow)
    api_key_last_used = DateTimeField()  # When the API key was last used

    # Token usage tracking (for plan limits)
    tokens_used_today = IntField(default=0)  # Tokens used today
    tokens_reset_at = DateTimeField(default=datetime.utcnow)  # Last token reset time

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

        return self.tokens_used_today < limit

    def consume_token(self):
        """Consume a token (increment usage)"""
        if self.plan != 'enterprise':
            self.tokens_used_today += 1

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'plan': self.plan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'mt5_connected': self.mt5_connected,
            'mt5_account_number': self.mt5_account_number,
            'api_key': self.api_key,
            'api_key_created_at': self.api_key_created_at.isoformat() if self.api_key_created_at else None,
            'tokens_used_today': self.tokens_used_today,
            'tokens_limit': self.get_token_limit(),
            'tokens_remaining': -1 if self.plan == 'enterprise' else max(0, self.get_token_limit() - self.tokens_used_today)
        }


class Signal(Document):
    """Signal model for MongoDB"""
    meta = {'collection': 'signals'}

    user_id = StringField(required=True)  # Reference to user ID
    symbol = StringField(required=True, max_length=10)
    signal_type = StringField(required=True, max_length=20)  # buy, sell, hold
    confidence = IntField(min_value=0, max_value=100)
    price = StringField(max_length=20)
    timestamp = DateTimeField(default=datetime.utcnow)
    strategy = StringField(max_length=50)
    indicators = StringField()  # JSON string of indicators
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'price': self.price,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'strategy': self.strategy,
            'indicators': self.indicators,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Trade(Document):
    """Trade model for MongoDB"""
    meta = {'collection': 'trades'}

    user_id = StringField(required=True)
    symbol = StringField(required=True, max_length=10)
    side = StringField(required=True, max_length=10)  # buy, sell
    quantity = IntField(min_value=1)
    price = StringField(max_length=20)
    status = StringField(default='pending', max_length=20)  # pending, filled, cancelled
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ExecutionLog(Document):
    """Execution log model for MongoDB"""
    meta = {'collection': 'execution_logs'}

    user_id = StringField(required=True)
    action = StringField(required=True, max_length=50)
    symbol = StringField(max_length=10)
    details = StringField()
    status = StringField(default='success', max_length=20)
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'action': self.action,
            'symbol': self.symbol,
            'details': self.details,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class APIKey(Document):
    """API Key model for MongoDB"""
    meta = {'collection': 'api_keys'}

    user_id = StringField(required=True)
    key = StringField(required=True, unique=True, max_length=64)
    name = StringField(max_length=100)
    created_at = DateTimeField(default=datetime.utcnow)
    last_used = DateTimeField()
    is_active = BooleanField(default=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'key': self.key,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active
        }


def init_mongo_db(app):
    """Initialize MongoDB connection"""
    from mongoengine import connect
    import os

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/sofaifx')

    try:
        connect(host=mongo_uri)
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise e


def seed_admin():
    """Create admin user if it doesn't exist"""
    try:
        admin_email = os.getenv('ADMIN_EMAIL', 'cyriladmin@gmail.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin1234')
        admin_name = os.getenv('ADMIN_NAME', 'Cyril Admin')

        existing = User.objects(email=admin_email).first()

        if not existing:
            admin_user = User(
                name=admin_name,
                email=admin_email,
                plan='enterprise',
                is_admin=True,
                is_active=True
            )
            admin_user.set_password(admin_password)
            admin_user.save()
            print(f"✅ Admin user created: {admin_email}")
        else:
            print(f"✅ Admin user already exists: {admin_email}")

    except Exception as e:
        print(f"❌ Admin seeding failed: {e}")
        raise e