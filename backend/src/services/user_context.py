"""
User Context Service - Extracts and validates user identity from requests

Handles both JWT-based and API key-based authentication
Ensures complete user isolation in all operations
"""

from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from ..models import User, db
from ..utils.logger import logger
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserContext:
    """
    Manages user context extraction and validation.
    
    Supports two authentication methods:
    1. JWT Token (from dashboard login)
    2. API Key (from EA/bot integration)
    """
    
    @staticmethod
    def get_current_user_id():
        """
        Extract current user ID from request.
        
        Tries JWT first, then API key.
        
        Returns:
            int: user_id if authenticated, None if not
        """
        try:
            verify_jwt_in_request(optional=True)
            jwt_user_id = get_jwt_identity()
            if jwt_user_id:
                logger.debug(f"User identified via JWT: {jwt_user_id}")
                return int(jwt_user_id)
        except Exception as e:
            logger.debug(f"JWT verification failed: {e}")
        
        api_key = request.args.get('apikey') or request.headers.get('X-API-Key')
        if api_key:
            user = User.query.filter_by(api_key=api_key).first()
            if user:
                logger.debug(f"User identified via API key: {user.id}")
                user.api_key_last_used = datetime.utcnow()
                db.session.commit()
                return user.id
        
        return None
    
    @staticmethod
    def get_current_user():
        """
        Get full User object for current request.
        
        Returns:
            User: User object if authenticated, None if not
        """
        user_id = UserContext.get_current_user_id()
        if user_id:
            return User.query.get(user_id)
        return None
    
    @staticmethod
    def require_auth(f):
        """
        Decorator to require authentication for an endpoint.
        
        Usage:
            @app.route('/protected')
            @UserContext.require_auth
            def protected():
                user_id = g.current_user_id
                ...
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = UserContext.get_current_user_id()
            if not user_id:
                logger.warning(f"Unauthorized access attempt to {request.endpoint}")
                return jsonify({
                    'error': 'UNAUTHORIZED',
                    'message': 'Valid authentication required'
                }), 401
            
            g.current_user_id = user_id
            g.current_user = User.query.get(user_id)
            
            return f(*args, **kwargs)
        
        return decorated
    
    @staticmethod
    def require_api_key(f):
        """
        Decorator to require API key authentication.
        
        Usage:
            @app.route('/signal')
            @UserContext.require_api_key
            def get_signal():
                user_id = g.current_user_id
                ...
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.args.get('apikey') or request.headers.get('X-API-Key')
            
            if not api_key:
                logger.warning(f"Missing API key for {request.endpoint}")
                return jsonify({
                    'error': 'MISSING_API_KEY',
                    'message': 'API key is required'
                }), 400
            
            user = User.query.filter_by(api_key=api_key).first()
            if not user:
                logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
                return jsonify({
                    'error': 'INVALID_API_KEY',
                    'message': 'Invalid or expired API key'
                }), 401
            
            user.api_key_last_used = datetime.utcnow()
            db.session.commit()
            
            g.current_user_id = user.id
            g.current_user = user
            
            return f(*args, **kwargs)
        
        return decorated


def get_user_context():
    """
    Get current user context from Flask's g object.
    
    Returns:
        dict: {'user_id': int, 'user': User or None}
    """
    return {
        'user_id': getattr(g, 'current_user_id', None),
        'user': getattr(g, 'current_user', None)
    }


def require_user_isolation(model_class, owner_field='user_id'):
    """
    Decorator factory to ensure users can only access their own data.
    
    Usage:
        @app.route('/signal/<int:signal_id>')
        @UserContext.require_user_isolation(Signal)
        def get_signal(signal_id):
            signal = g.resource
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = getattr(g, 'current_user_id', None)
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            resource_id = kwargs.get('id') or kwargs.get(f'{owner_field.replace("_id", "_id")}')
            
            if not resource_id:
                return jsonify({'error': 'Resource ID required'}), 400
            
            resource = model_class.query.filter_by(
                id=resource_id,
                **{owner_field: user_id}
            ).first()
            
            if not resource:
                return jsonify({
                    'error': 'NOT_FOUND',
                    'message': 'Resource not found or access denied'
                }), 404
            
            g.resource = resource
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


# Helper function for logging with user context
def log_with_user(level, message, user_id=None, extra=None):
    """
    Log message with user context.
    
    Args:
        level: Logging level (INFO, WARNING, ERROR, etc.)
        message: Log message
        user_id: Optional user ID to include
        extra: Optional extra data dict
    """
    user_context = f"[USER {user_id or 'UNKNOWN'}]"
    full_message = f"{user_context} {message}"
    
    if extra:
        full_message += f" | {extra}"
    
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(full_message)


# Export for use in other modules
__all__ = [
    'UserContext',
    'get_user_context',
    'require_user_isolation',
    'log_with_user'
]