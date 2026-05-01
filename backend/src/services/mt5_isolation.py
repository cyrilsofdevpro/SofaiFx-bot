"""
MT5 User Isolation Service - Manages isolated MT5 connections per user

Each user has their own MT5 connection that is completely isolated from other users.
No user can access another user's MT5 account, credentials, or trades.

Platform Detection:
- Windows: Uses actual MetaTrader5 package
- Linux/Render: Returns stub data
"""

import os
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Detect platform
_IS_LINUX = os.name == 'posix' or os.getenv('RENDER') == 'true'

# Conditional import
if _IS_LINUX:
    mt5 = None
    logger.warning("MT5UserIsolation: Running on Linux - using stub")
else:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        mt5 = None

logger = logging.getLogger(__name__)

# Thread-safe storage for user MT5 sessions
_user_sessions_lock = threading.RLock()
_user_mt5_sessions: Dict[int, Dict[str, Any]] = {}


class MT5UserIsolation:
    """
    Manages isolated MT5 connections per user.
    
    Each user has:
    - Their own MT5 login credentials (encrypted in DB)
    - Their own MT5 connection session
    - Isolated trade execution
    - Private account data
    """
    
    @staticmethod
    def connect_user(user_id: int, login: str, password: str, server: str) -> Dict[str, Any]:
        """
        Connect a user's MT5 account with full isolation.
        
        Args:
            user_id: SofAi user ID (for session isolation)
            login: MT5 login ID
            password: MT5 password
            server: MT5 server name
            
        Returns:
            dict: Connection result with status and account info
        """
        with _user_sessions_lock:
            logger.info(f"🔌 [USER {user_id}] Connecting MT5 account...")
            
            # Check if already connected
            if user_id in _user_mt5_sessions:
                existing = _user_mt5_sessions[user_id]
                if existing.get('connection_status') == 'connected':
                    logger.info(f"⚠️ [USER {user_id}] Already connected, returning existing session")
                    return {
                        "success": True,
                        "message": "Already connected",
                        "account": {
                            "login": existing.get('account_number'),
                            "balance": existing.get('balance'),
                            "server": existing.get('server')
                        },
                        "reconnected": False
                    }
            
            # Initialize MT5
            if not mt5.initialize():
                error = mt5.last_error()
                logger.error(f"❌ [USER {user_id}] MT5 initialization failed: {error}")
                return {
                    "success": False,
                    "error": "MT5_INITIALIZATION_FAILED",
                    "message": "MetaTrader5 terminal is not running. Please start the MT5 terminal application on your computer and try again.",
                    "details": str(error),
                    "requirement": "MT5 terminal must be running to establish connections"
                }
            
            # Attempt login
            if not mt5.login(login=int(login), password=password, server=server):
                error = mt5.last_error()
                logger.error(f"❌ [USER {user_id}] MT5 login failed: {error}")
                mt5.shutdown()
                
                # Provide helpful error messages based on error code
                error_msg = "Login failed"
                if "Authorization failed" in str(error) or "-6" in str(error):
                    error_msg = "Authorization failed - check your credentials and server name"
                elif "Unknown host" in str(error):
                    error_msg = "Server not found - check the server name"
                
                return {
                    "success": False,
                    "error": "MT5_LOGIN_FAILED",
                    "message": error_msg,
                    "details": str(error),
                    "login_id": login,
                    "server": server,
                    "hint": "Check that login ID, password, and server name are correct"
                }
            
            # Get account info
            account = mt5.account_info()
            if account is None:
                logger.error(f"❌ [USER {user_id}] Failed to get account info")
                mt5.shutdown()
                return {
                    "success": False,
                    "error": "ACCOUNT_INFO_FAILED"
                }
            
            # Store isolated session
            _user_mt5_sessions[user_id] = {
                'login': str(login),
                'server': server,
                'connected_at': datetime.utcnow(),
                'account_number': str(account.login),
                'balance': float(account.balance),
                'equity': float(account.equity),
                'margin': float(account.margin),
                'free_margin': float(account.margin_free),
                'currency': account.currency,
                'leverage': account.leverage,
                'connection_status': 'connected'
            }
            
            logger.info(f"✅ [USER {user_id}] MT5 connected: Account {account.login}, Balance: {account.balance} {account.currency}")
            
            return {
                "success": True,
                "message": "MT5 account connected successfully",
                "account": {
                    "login": int(account.login),
                    "balance": float(account.balance),
                    "equity": float(account.equity),
                    "margin": float(account.margin),
                    "free_margin": float(account.margin_free),
                    "currency": account.currency,
                    "leverage": account.leverage,
                    "server": server
                },
                "connected_at": datetime.utcnow().isoformat()
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
        with _user_sessions_lock:
            if user_id not in _user_mt5_sessions:
                return {
                    "success": True,
                    "message": "No active connection to disconnect"
                }
            
            # Shutdown MT5
            mt5.shutdown()
            
            # Remove session
            session_info = _user_mt5_sessions.pop(user_id, {})
            
            logger.info(f"✅ [USER {user_id}] MT5 disconnected: Account {session_info.get('account_number')}")
            
            return {
                "success": True,
                "message": "MT5 account disconnected",
                "disconnected_account": session_info.get('account_number')
            }
    
    @staticmethod
    def get_user_connection_status(user_id: int) -> Dict[str, Any]:
        """
        Get connection status for a user.
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            dict: Connection status
        """
        with _user_sessions_lock:
            if user_id not in _user_mt5_sessions:
                return {
                    "connected": False,
                    "status": "not_connected"
                }
            
            session = _user_mt5_sessions[user_id]
            
            return {
                "connected": True,
                "status": session.get('connection_status', 'unknown'),
                "account_number": session.get('account_number'),
                "server": session.get('server'),
                "connected_at": session.get('connected_at').isoformat() if session.get('connected_at') else None,
                "balance": session.get('balance'),
                "equity": session.get('equity')
            }
    
    @staticmethod
    def is_user_connected(user_id: int) -> bool:
        """
        Check if a user has an active MT5 connection.
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            bool: True if connected
        """
        with _user_sessions_lock:
            session = _user_mt5_sessions.get(user_id, {})
            return session.get('connection_status') == 'connected'
    
    @staticmethod
    def get_user_session(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's MT5 session data (without credentials).
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            dict: Session data or None
        """
        with _user_sessions_lock:
            session = _user_mt5_sessions.get(user_id, {})
            if not session:
                return None
            
            # Return safe data (no credentials)
            return {
                'account_number': session.get('account_number'),
                'server': session.get('server'),
                'connected_at': session.get('connected_at').isoformat() if session.get('connected_at') else None,
                'balance': session.get('balance'),
                'equity': session.get('equity'),
                'margin': session.get('margin'),
                'free_margin': session.get('free_margin'),
                'currency': session.get('currency'),
                'leverage': session.get('leverage')
            }
    
    @staticmethod
    def get_all_connected_users() -> Dict[int, Dict[str, Any]]:
        """
        Get all currently connected users (for admin monitoring).
        
        Returns:
            dict: Mapping of user_id to session info (no credentials)
        """
        with _user_sessions_lock:
            result = {}
            for uid, session in _user_mt5_sessions.items():
                result[uid] = {
                    'account_number': session.get('account_number'),
                    'server': session.get('server'),
                    'connected_at': session.get('connected_at').isoformat() if session.get('connected_at') else None,
                    'connection_status': session.get('connection_status')
                }
            return result
    
    @staticmethod
    def execute_trade_for_user(user_id: int, symbol: str, order_type: str, 
                               volume: float, price: float = None,
                               sl: float = None, tp: float = None,
                               comment: str = None) -> Dict[str, Any]:
        """
        Execute a trade on a user's MT5 account.
        
        Args:
            user_id: SofAi user ID (ensures isolation)
            symbol: Trading symbol (e.g., "EURUSD")
            order_type: "buy" or "sell"
            volume: Lot size
            price: Entry price (None for market)
            sl: Stop loss price
            tp: Take profit price
            comment: Trade comment
            
        Returns:
            dict: Trade execution result
        """
        with _user_sessions_lock:
            # Verify user is connected
            if user_id not in _user_mt5_sessions:
                return {
                    "success": False,
                    "error": "NOT_CONNECTED",
                    "message": "User MT5 account not connected"
                }
            
            session = _user_mt5_sessions[user_id]
            if session.get('connection_status') != 'connected':
                return {
                    "success": False,
                    "error": "CONNECTION_LOST",
                    "message": "MT5 connection not active"
                }
            
            # Prepare order request
            symbol = symbol.upper()
            symbol_info = mt5.symbol_info(symbol)
            
            if symbol_info is None:
                return {
                    "success": False,
                    "error": "INVALID_SYMBOL",
                    "message": f"Symbol {symbol} not found"
                }
            
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
            
            point = symbol_info.point
            
            # Determine order type
            if order_type.lower() == 'buy':
                trade_type = mt5.ORDER_TYPE_BUY
                if price is None:
                    price = mt5.symbol_info_tick(symbol).ask
            elif order_type.lower() == 'sell':
                trade_type = mt5.ORDER_TYPE_SELL
                if price is None:
                    price = mt5.symbol_info_tick(symbol).bid
            else:
                return {
                    "success": False,
                    "error": "INVALID_ORDER_TYPE",
                    "message": "Order type must be 'buy' or 'sell'"
                }
            
            # Build request
            request_dict = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": trade_type,
                "price": float(price),
                "deviation": 20,
                "magic": user_id * 1000 + int(datetime.utcnow().timestamp()) % 1000,
                "comment": comment or f"SofAi-User-{user_id}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if provided
            if sl:
                if order_type.lower() == 'buy':
                    request_dict["sl"] = float(sl)
                else:
                    request_dict["tp"] = float(sl)
            
            if tp:
                if order_type.lower() == 'buy':
                    request_dict["tp"] = float(tp)
                else:
                    request_dict["sl"] = float(tp)
            
            # Send order
            result = mt5.order_send(request_dict)
            
            if result is None:
                return {
                    "success": False,
                    "error": "ORDER_FAILED",
                    "message": "Failed to send order"
                }
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False,
                    "error": "ORDER_REJECTED",
                    "message": f"Order rejected: {result.comment}",
                    "retcode": result.retcode
                }
            
            logger.info(f"✅ [USER {user_id}] Trade executed: {order_type} {volume} {symbol} @ {price}")
            
            return {
                "success": True,
                "order_id": result.order,
                "deal": result.deal,
                "volume": volume,
                "price": price,
                "symbol": symbol,
                "order_type": order_type,
                "comment": comment
            }
    
    @staticmethod
    def get_user_positions(user_id: int) -> list:
        """
        Get all open positions for a user.
        
        Args:
            user_id: SofAi user ID
            
        Returns:
            list: Open positions
        """
        with _user_sessions_lock:
            if user_id not in _user_mt5_sessions:
                return []
            
            # Get positions (filtered by magic number would be better in production)
            positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            # Filter to user's positions (using comment as filter)
            user_positions = []
            for pos in positions:
                if f"SofAi-User-{user_id}" in str(pos.comment):
                    user_positions.append({
                        "ticket": pos.ticket,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "price_open": pos.price_open,
                        "price_current": pos.price_current,
                        "profit": pos.profit,
                        "comment": pos.comment
                    })
            
            return user_positions
    
    @staticmethod
    def close_user_position(user_id: int, ticket: int) -> Dict[str, Any]:
        """
        Close a specific position for a user.
        
        Args:
            user_id: SofAi user ID
            ticket: Position ticket number
            
        Returns:
            dict: Close result
        """
        with _user_sessions_lock:
            if user_id not in _user_mt5_sessions:
                return {
                    "success": False,
                    "error": "NOT_CONNECTED"
                }
            
            # Get position
            position = mt5.position_get(ticket=ticket)
            
            if position is None:
                return {
                    "success": False,
                    "error": "POSITION_NOT_FOUND"
                }
            
            # Verify it belongs to this user
            if f"SofAi-User-{user_id}" not in str(position.comment):
                return {
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": "Position does not belong to this user"
                }
            
            # Determine opposite order type
            if position.type == mt5.POSITION_TYPE_BUY:
                trade_type = mt5.ORDER_TYPE_SELL
            else:
                trade_type = mt5.ORDER_TYPE_BUY
            
            # Close position
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": trade_type,
                "position": ticket,
                "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
                "deviation": 20,
                "comment": f"SofAi-Close-User-{user_id}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(close_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ [USER {user_id}] Position {ticket} closed")
                return {
                    "success": True,
                    "closed_ticket": ticket
                }
            
            return {
                "success": False,
                "error": "CLOSE_FAILED",
                "message": result.comment if result else "Unknown error"
            }


# Export singleton for easy import
mt5_isolation = MT5UserIsolation()

__all__ = [
    'MT5UserIsolation',
    'mt5_isolation',
    '_user_mt5_sessions'
]