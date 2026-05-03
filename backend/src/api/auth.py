"""
Authentication routes for user registration, login, and token management
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from ..models import db, User
from ..config import config
from ..utils.logger import logger

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request body:
    {
        "name": "John Doe",
        "email": "user@example.com",
        "password": "securepassword123"
    }
    
    Returns: JWT token on success
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not name or not email or not password:
            return jsonify({'error': 'Name, email and password required'}), 400
        
        if len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if '@' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(name=name, email=email, plan='free')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token (valid for 30 days, identity must be a string)
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        # Generate refresh token (valid for 90 days)
        refresh_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=90),
            fresh=False
        )
        
        logger.info(f'New user registered: {name} ({email})')
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 30 * 24 * 60 * 60  # 30 days in seconds
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Registration error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and return JWT token
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword123"
    }
    
    Returns: JWT token on success
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            logger.warning(f'Failed login attempt for: {email}')
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Generate token (valid for 30 days, identity must be a string)
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        # Generate refresh token (valid for 90 days)
        refresh_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=90),
            fresh=False
        )
        
        logger.info(f'User logged in: {user.name} ({email})')
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 30 * 24 * 60 * 60  # 30 days in seconds
        }), 200
        
    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user info
    
    Returns: Current user details
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'Error fetching user: {str(e)}')
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify token is valid and return current user info.
    Used by frontend to validate stored tokens on page load.
    
    Returns: User details if token is valid
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'error': 'Invalid user or inactive account',
                'user': None
            }), 401
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'message': 'Token is valid'
        }), 200
        
    except Exception as e:
        logger.error(f'Token verification error: {str(e)}')
        return jsonify({
            'error': 'Token verification failed',
            'user': None
        }), 401


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token
    
    Request body:
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    
    Returns: New access token
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('refresh_token'):
            return jsonify({'error': 'Refresh token required'}), 400
        
        refresh_token_str = data.get('refresh_token')
        
        # Decode and validate refresh token manually (without jwt_required decorator)
        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(refresh_token_str)
            user_id = int(decoded['sub'])
        except Exception as e:
            logger.warning(f'Invalid refresh token: {str(e)}')
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Generate new access token (valid for 30 days)
        new_access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        # Generate new refresh token (valid for 90 days)
        new_refresh_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=90),
            fresh=False
        )
        
        logger.info(f'Token refreshed for user: {user.name}')
        return jsonify({
            'message': 'Refresh successful',
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'expires_in': 30 * 24 * 60 * 60
        }), 200
    except Exception as e:
        logger.error(f'Refresh error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/bootstrap-admin', methods=['POST'])
def bootstrap_admin():
    """Create or promote an admin user using a protected bootstrap secret."""
    if not config.ADMIN_BOOTSTRAP_SECRET:
        return jsonify({'error': 'Admin bootstrap secret is not configured'}), 403

    data = request.get_json() or {}
    provided_secret = data.get('bootstrap_secret') or request.headers.get('X-Bootstrap-Secret')
    if not provided_secret or provided_secret != config.ADMIN_BOOTSTRAP_SECRET:
        logger.warning('Unauthorized admin bootstrap attempt')
        return jsonify({'error': 'Unauthorized'}), 403

    email = data.get('email', config.ADMIN_EMAIL).strip().lower()
    password = data.get('password', config.ADMIN_PASSWORD)
    name = data.get('name', config.ADMIN_NAME) or 'Admin User'

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        user.is_active = True
        if not user.check_password(password):
            user.set_password(password)
            logger.info('Admin bootstrap updated existing user password')
        db.session.commit()
        message = f"Promoted existing user '{user.email}' to admin."
    else:
        user = User(name=name, email=email, plan='enterprise', is_admin=True, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        message = f"Created admin user '{user.email}'."

    logger.info(message)
    return jsonify({
        'message': message,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_active': user.is_active
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    
    Request body:
    {
        "current_password": "oldpassword123",
        "new_password": "newpassword456"
    }
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Both passwords required'}), 400
        
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f'Password changed for user: {user.email}')
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Password change error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (frontend removes token)
    """
    user_id = int(get_jwt_identity())
    logger.info(f'User logged out: {user_id}')
    
    return jsonify({'message': 'Logged out successfully'}), 200
