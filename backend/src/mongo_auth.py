from datetime import datetime
import secrets
from pymongo import MongoClient, errors
import certifi
from flask_bcrypt import Bcrypt
from src.config import config
from src.models import db, User
from src.utils.logger import logger

bcrypt = Bcrypt()
_mongo_client = None
_mongo_db = None
_users_collection = None


def normalize_email(email: str) -> str:
    return email.strip().lower() if email else ''


def init_mongo_db(app=None):
    global _mongo_client, _mongo_db, _users_collection

    mongo_uri = config.MONGO_URI
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is not configured')

    if app is not None:
        bcrypt.init_app(app)

    _mongo_client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        tls=True,
        tlsCAFile=certifi.where()
    )
    _mongo_db = _mongo_client.get_default_database()
    if _mongo_db is None:
        _mongo_db = _mongo_client['sofaifx']

    _users_collection = _mongo_db['users']
    _users_collection.create_index('email', unique=True)
    _users_collection.create_index('api_key', unique=True, sparse=True)

    logger.info(f'✓ MongoDB initialized: {mongo_uri}')
    return _mongo_db


def get_users_collection():
    if _users_collection is None:
        raise RuntimeError('MongoDB has not been initialized. Call init_mongo_db() first.')
    return _users_collection


def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode('utf-8')


def check_password(hashed_password: str, password: str) -> bool:
    try:
        return bcrypt.check_password_hash(hashed_password, password)
    except Exception:
        return False


def get_mongo_user_by_email(email: str):
    email = normalize_email(email)
    return get_users_collection().find_one({'email': email})


def get_mongo_user_by_api_key(api_key: str):
    return get_users_collection().find_one({'api_key': api_key})


def create_mongo_user(name: str, email: str, password: str, plan: str = 'free', is_admin: bool = False, is_active: bool = True):
    email = normalize_email(email)
    user_doc = {
        'name': name.strip() if name else '',
        'email': email,
        'password': hash_password(password),
        'plan': plan,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'is_active': is_active,
        'is_admin': is_admin,
        'last_active': datetime.utcnow(),
        'api_key': secrets.token_urlsafe(48),
        'api_key_created_at': datetime.utcnow(),
        'api_key_last_used': None
    }
    try:
        get_users_collection().insert_one(user_doc)
    except errors.DuplicateKeyError:
        raise ValueError('Email already registered')
    return get_mongo_user_by_email(email)


def update_mongo_user(email: str, updates: dict):
    email = normalize_email(email)
    if not updates:
        return get_mongo_user_by_email(email)
    updates['updated_at'] = datetime.utcnow()
    get_users_collection().update_one({'email': email}, {'$set': updates}, upsert=False)
    return get_mongo_user_by_email(email)


def upsert_mongo_user(email: str, updates: dict):
    email = normalize_email(email)
    updates['updated_at'] = datetime.utcnow()
    get_users_collection().update_one({'email': email}, {'$set': updates}, upsert=True)
    return get_mongo_user_by_email(email)


def sync_mongo_user_to_sql(mongo_user):
    if not mongo_user:
        return None
    email = normalize_email(mongo_user.get('email'))
    if not email:
        return None

    user = User.query.filter_by(email=email).first()
    if user:
        user.name = mongo_user.get('name', user.name)
        user.plan = mongo_user.get('plan', user.plan)
        user.is_active = mongo_user.get('is_active', user.is_active)
        user.is_admin = mongo_user.get('is_admin', user.is_admin)
        user.last_active = mongo_user.get('last_active') or user.last_active or datetime.utcnow()
        if mongo_user.get('password') and user.password != mongo_user.get('password'):
            user.password = mongo_user.get('password')
        if mongo_user.get('api_key'):
            user.api_key = mongo_user.get('api_key')
            user.api_key_created_at = mongo_user.get('api_key_created_at') or user.api_key_created_at
            user.api_key_last_used = mongo_user.get('api_key_last_used') or user.api_key_last_used
        db.session.commit()
    else:
        user = User(
            name=mongo_user.get('name', ''),
            email=email,
            password=mongo_user.get('password'),
            plan=mongo_user.get('plan', 'free'),
            is_active=mongo_user.get('is_active', True),
            is_admin=mongo_user.get('is_admin', False),
            last_active=mongo_user.get('last_active', datetime.utcnow()),
            api_key=mongo_user.get('api_key'),
            api_key_created_at=mongo_user.get('api_key_created_at', datetime.utcnow()),
            api_key_last_used=mongo_user.get('api_key_last_used')
        )
        db.session.add(user)
        db.session.commit()
    return user


def sync_sql_user_to_mongo(sql_user):
    if not sql_user or not sql_user.email:
        return None
    email = normalize_email(sql_user.email)
    user_doc = {
        'name': sql_user.name,
        'email': email,
        'password': sql_user.password,
        'plan': sql_user.plan,
        'is_active': sql_user.is_active,
        'is_admin': sql_user.is_admin,
        'last_active': sql_user.last_active or datetime.utcnow(),
        'api_key': sql_user.api_key,
        'api_key_created_at': sql_user.api_key_created_at or datetime.utcnow(),
        'api_key_last_used': sql_user.api_key_last_used
    }
    get_users_collection().update_one({'email': email}, {'$set': user_doc}, upsert=True)
    return get_mongo_user_by_email(email)


def seed_admin():
    admin_email = normalize_email(config.ADMIN_EMAIL)
    admin_password = config.ADMIN_PASSWORD
    admin_name = config.ADMIN_NAME or 'Admin User'

    if not admin_email or not admin_password:
        raise RuntimeError('Admin email and password must be configured for seeding')

    mongo_user = get_mongo_user_by_email(admin_email)
    if mongo_user:
        update_mongo_user(admin_email, {
            'name': admin_name,
            'plan': 'enterprise',
            'is_admin': True,
            'is_active': True,
            'last_active': datetime.utcnow()
        })
        mongo_user = get_mongo_user_by_email(admin_email)
    else:
        mongo_user = create_mongo_user(
            name=admin_name,
            email=admin_email,
            password=admin_password,
            plan='enterprise',
            is_admin=True,
            is_active=True
        )

    sync_mongo_user_to_sql(mongo_user)
    logger.info(f'Admin seeded to MongoDB and local SQL: {admin_email}')
    return mongo_user
