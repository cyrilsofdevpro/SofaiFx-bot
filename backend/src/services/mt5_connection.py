"""
MT5 Connection Manager - Handles user MT5 account connections

Manages per-user MT5 sessions and connection lifecycle

Platform Detection:
- Windows: Uses actual MetaTrader5 package
- Linux/Render: Returns stub data
"""

import os
import logging
from typing import Optional, Dict, Any
from threading import Lock
from datetime import datetime

# Initialize logger FIRST
logger = logging.getLogger(__name__)

# Detect platform
_IS_LINUX = os.name == 'posix' or os.getenv('RENDER') == 'true'

# Conditional import
if _IS_LINUX:
    mt5 = None
    logger.warning("MT5ConnectionManager: Running on Linux - using stub")
else:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        mt5 = None

# Global lock for MT5 operations (MT5 is not thread-safe)
mt5_lock = Lock()

# Store active MT5 connections per user
_user_mt5_sessions = {}


class MT5ConnectionManager:
    """
    Manages MT5 connections per user.
    
    Each user can have one active MT5 connection.
    Connections are maintained server-side, not in the browser.
    """
    
    @staticmethod
    def connect_user(user_id: int, login: str, password: str, server: str) -> Dict[str, Any]:
        """
        Connect a user's MT5 account.
        
        Args:
            user_id: SofAi user ID
            login: MT5 login ID
            password: MT5 password
            server: MT5 server name
            
        Returns:
            dict: Connection result with status and account info
        """
        try:
            with mt5_lock:
                logger.info(f"🔌 [USER {user_id}] Attempting MT5 connection to {server}...")
                
                # Initialize MT5
                if not mt5.initialize():
                    error = mt5.last_error()
                    logger.error(f"❌ [USER {user_id}] MT5 initialization failed: {error}")
                    return {
                        "success": False,
                        "error": "MT5 initialization failed",
                        "details": str(error)
                    }
                
                # Attempt login
                if not mt5.login(login=int(login), password=password, server=server):
                    error = mt5.last_error()
                    logger.error(f"❌ [USER {user_id}] MT5 login failed for account {login}: {error}")
                    mt5.shutdown()
                    return {
                        "success": False,
                        "error": "MT5 login failed",
                        "details": f"Invalid credentials or server. {error}",
                        "login_id": login,
                        "server": server
                    }
                
                # Get account info to verify connection
                account = mt5.account_info()
                if account is None:
                    logger.error(f"❌ [USER {user_id}] Failed to get account info")
                    mt5.shutdown()
                    return {
                        "success": False,
                        "error": "Failed to retrieve account information"
                    }
                
                # Connection successful - store session
                _user_mt5_sessions[user_id] = {
                    'login': login,
                    'server': server,
                    'connected_at': datetime.utcnow(),
                    'account_number': account.login
                }
                
                logger.info(f"✅ [USER {user_id}] MT5 connected successfully")
                logger.info(f"   Account: {account.login}")
                logger.info(f"   Balance: {account.balance} {account.currency}")
                
                return {
                    "success": True,
                    "message": "MT5 account connected successfully",
                    "account": {
                        "login": int(account.login),
                        "balance": float(account.balance),
                        "equity": float(account.equity),
                        "margin": float(account.margin),
                        "free_margin": float(account.margin_free),
                        "margin_level": float(account.margin_level),
                        "currency": str(account.currency),
                        "leverage": int(account.leverage),
                        "trade_mode": "demo" if account.trade_mode == 1 else "live"
                    }
                }
        
        except Exception as e:
            logger.error(f"❌ [USER {user_id}] Unexpected error during connection: {e}", exc_info=True)
            try:
                mt5.shutdown()
            except:
                pass
            
            return {
                "success": False,
                "error": "Connection error",
                "details": str(e)
            }
    
    @staticmethod
    def disconnect_user(user_id: int) -> Dict[str, Any]:
        """
        Disconnect a user's MT5 account.
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            dict: Disconnection result
        """
        try:
            with mt5_lock:
                logger.info(f"🔌 [USER {user_id}] Disconnecting MT5...")
                
                if user_id not in _user_mt5_sessions:
                    logger.warning(f"⚠️ [USER {user_id}] No active session found")
                    return {
                        "success": True,
                        "message": "No active connection found"
                    }
                
                # Shutdown MT5 for this user
                mt5.shutdown()
                
                # Remove session
                session_info = _user_mt5_sessions.pop(user_id)
                logger.info(f"✅ [USER {user_id}] MT5 disconnected")
                
                return {
                    "success": True,
                    "message": "MT5 account disconnected",
                    "was_connected_since": session_info['connected_at'].isoformat()
                }
        
        except Exception as e:
            logger.error(f"❌ [USER {user_id}] Error during disconnection: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Disconnection failed",
                "details": str(e)
            }
    
    @staticmethod
    def is_user_connected(user_id: int) -> bool:
        """
        Check if user has active MT5 connection.
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            True if connected
        """
        if user_id not in _user_mt5_sessions:
            return False
        
        try:
            with mt5_lock:
                # Verify connection by getting account info
                account = mt5.account_info()
                return account is not None
        except:
            return False
    
    @staticmethod
    def get_user_session_info(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get stored session info for user.
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            Session info dict or None
        """
        return _user_mt5_sessions.get(user_id)
    
    @staticmethod
    def get_active_user_count() -> int:
        """Get number of users with active MT5 connections"""
        return len(_user_mt5_sessions)
    
    @staticmethod
    def get_all_active_users() -> list:
        """Get list of user IDs with active connections"""
        return list(_user_mt5_sessions.keys())
    
    @staticmethod
    def validate_credentials(login: str, password: str, server: str) -> bool:
        """
        Validate MT5 credentials without storing them.
        
        Args:
            login: MT5 login ID
            password: MT5 password
            server: MT5 server name
            
        Returns:
            True if credentials are valid
        """
        try:
            with mt5_lock:
                logger.info(f"🔍 Validating credentials for account {login}...")
                
                if not mt5.initialize():
                    logger.warning("MT5 init failed during validation")
                    return False
                
                if not mt5.login(login=int(login), password=password, server=server):
                    logger.warning(f"Login validation failed for {login}")
                    mt5.shutdown()
                    return False
                
                # Quick validation - just check if we can get account info
                account = mt5.account_info()
                mt5.shutdown()
                
                return account is not None
        
        except Exception as e:
            logger.warning(f"Validation error: {e}")
            try:
                mt5.shutdown()
            except:
                pass
            return False
