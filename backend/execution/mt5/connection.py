"""
MT5 Connection Manager - Handles MetaTrader 5 terminal connection and initialization

This module manages:
- MT5 terminal connection
- Account authentication
- Connection status monitoring
- Account information retrieval
"""

import MetaTrader5 as mt5
from datetime import datetime
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MT5Connection:
    """
    Manages connection to MetaTrader 5 terminal
    
    Attributes:
        is_connected (bool): Connection status
        account_info (dict): Current account information
        server (str): MT5 server name
        account (int): MT5 account number
    """
    
    def __init__(self, account: int, password: str, server: str = "ICMarkets-Demo", 
                 terminal_path: Optional[str] = None):
        """
        Initialize MT5 connection (does not connect yet).
        
        Args:
            account: MT5 account number
            password: MT5 account password
            server: MT5 server name (default: ICMarkets-Demo for demo trading)
            terminal_path: Path to MT5 terminal executable (auto-detected if None)
        """
        self.account = account
        self.password = password
        self.server = server
        self.terminal_path = terminal_path
        self.is_connected = False
        self.account_info = {}
        
    def connect(self) -> bool:
        """
        Connect to MT5 terminal and authenticate.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Attempting to connect to MT5 server: {self.server}, Account: {self.account}")
            
            # Initialize MT5 - let it auto-detect the terminal
            if self.terminal_path:
                if not mt5.initialize(path=self.terminal_path):
                    error = mt5.last_error()
                    logger.error(f"MT5 initialization failed: {error}")
                    return False
            else:
                # Auto-detect terminal
                if not mt5.initialize():
                    error = mt5.last_error()
                    logger.error(f"MT5 initialization failed: {error}")
                    return False
            
            # Login to account
            if not mt5.login(self.account, password=self.password, server=self.server):
                error = mt5.last_error()
                logger.error(f"MT5 login failed: {error}")
                mt5.shutdown()
                return False
            
            # Verify connection
            self.account_info = self._get_account_info()
            if not self.account_info:
                logger.error("Failed to retrieve account information")
                mt5.shutdown()
                return False
            
            self.is_connected = True
            logger.info(f"[OK] MT5 connected successfully")
            logger.info(f"  Account: {self.account_info.get('login')}")
            logger.info(f"  Balance: {self.account_info.get('balance')} {self.account_info.get('currency')}")
            logger.info(f"  Equity: {self.account_info.get('equity')} {self.account_info.get('currency')}")
            logger.info(f"  Demo: {self.account_info.get('trade_mode') == 'demo'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Exception during MT5 connection: {e}", exc_info=True)
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from MT5 terminal.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.is_connected:
                mt5.shutdown()
                self.is_connected = False
                logger.info("[OK] MT5 disconnected")
            return True
        except Exception as e:
            logger.error(f"Error during MT5 disconnection: {e}")
            return False
    
    def _get_account_info(self) -> Dict[str, Any]:
        """
        Retrieve account information from MT5.
        
        Returns:
            dict: Account information
        """
        try:
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("Failed to get account info from MT5")
                return {}
            
            return {
                'login': account_info.login,
                'server': account_info.server,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'free_margin': account_info.margin_free,
                'margin_level': account_info.margin_level,
                'currency': account_info.currency,
                'trade_mode': 'demo' if account_info.trade_mode == 1 else 'real',
                'leverage': account_info.leverage,
                'max_orders': 200  # Default limit if not available
            }
        except Exception as e:
            logger.error(f"Error retrieving account info: {e}", exc_info=True)
            return {}
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get current account information.
        
        Returns:
            dict: Account information
        """
        if not self.is_connected:
            logger.warning("Not connected to MT5")
            return {}
        
        self.account_info = self._get_account_info()
        return self.account_info
    
    def check_connection(self) -> bool:
        """
        Verify if connection is still active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            if not self.is_connected:
                return False
            
            # Try to get account info to verify connection
            account_info = self._get_account_info()
            if account_info:
                self.account_info = account_info
                return True
            
            self.is_connected = False
            return False
            
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            self.is_connected = False
            return False
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get information about a trading symbol.
        
        Args:
            symbol: Symbol name (e.g., "EURUSD")
        
        Returns:
            dict: Symbol information
        """
        try:
            if not self.is_connected:
                logger.warning("Not connected to MT5")
                return {}
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.warning(f"Symbol {symbol} not found in MT5")
                return {}
            
            return {
                'symbol': symbol_info.name,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'spread': symbol_info.spread,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'volume': symbol_info.volume,
                'volume_high': getattr(symbol_info, 'volume_high', None),
                'volume_low': getattr(symbol_info, 'volume_low', None),
                'time': symbol_info.time,
                'min_volume': symbol_info.volume_min,
                'max_volume': symbol_info.volume_max,
                'min_lot': symbol_info.volume_min,
                'max_lot': symbol_info.volume_max
            }
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}", exc_info=True)
            return {}
    
    def get_open_positions(self) -> list:
        """
        Get all open positions.
        
        Returns:
            list: List of open positions
        """
        try:
            if not self.is_connected:
                logger.warning("Not connected to MT5")
                return []
            
            positions = mt5.positions_get()
            if positions is None:
                logger.warning("Failed to get positions from MT5")
                return []
            
            return [
                {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'pnl': pos.profit,
                    'pnl_percent': (pos.profit / (pos.volume * pos.price_open)) * 100 if pos.price_open != 0 else 0,
                    'open_time': datetime.fromtimestamp(pos.time).isoformat(),
                    'comment': pos.comment
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting open positions: {e}", exc_info=True)
            return []
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get open position for a specific symbol.
        
        Args:
            symbol: Symbol name
        
        Returns:
            dict: Position information or None if no open position
        """
        positions = self.get_open_positions()
        for pos in positions:
            if pos['symbol'] == symbol:
                return pos
        return None
    
    def get_history_orders(self, limit: int = 50) -> list:
        """
        Get order history.
        
        Args:
            limit: Maximum number of orders to retrieve
        
        Returns:
            list: List of historical orders
        """
        try:
            if not self.is_connected:
                logger.warning("Not connected to MT5")
                return []
            
            orders = mt5.history_orders_get(limit=limit)
            if orders is None:
                logger.warning("Failed to get order history from MT5")
                return []
            
            return [
                {
                    'ticket': order.ticket,
                    'symbol': order.symbol,
                    'type': 'BUY' if order.type == 0 else 'SELL',
                    'volume': order.volume_initial,
                    'price_open': order.price_open,
                    'price_close': order.price_current,
                    'sl': order.sl,
                    'tp': order.tp,
                    'open_time': datetime.fromtimestamp(order.time_setup).isoformat(),
                    'close_time': datetime.fromtimestamp(order.time_done).isoformat() if order.time_done else None,
                    'state': order.state
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting order history: {e}", exc_info=True)
            return []


def get_mt5_connection(account: int, password: str, server: str = "ICMarkets-Demo") -> Optional[MT5Connection]:
    """
    Factory function to create and connect to MT5.
    
    Args:
        account: MT5 account number
        password: MT5 account password
        server: MT5 server name
    
    Returns:
        MT5Connection: Connected instance or None if connection failed
    """
    conn = MT5Connection(account, password, server)
    if conn.connect():
        return conn
    return None


class SymbolMapper:
    """
    Auto-detects and maps broker symbols to normalized format.
    
    This class handles symbol resolution between AI-generated symbols
    (e.g., EURUSD.m) and actual broker symbols (e.g., EURUSD).
    """
    
    def __init__(self, mt5_connection):
        """
        Initialize symbol mapper.
        
        Args:
            mt5_connection: MT5Connection instance
        """
        self.mt5 = mt5_connection
        self._symbol_map = None
        self._last_refresh = None
    
    def _normalize_ai_symbol(self, symbol: str) -> str:
        """
        Normalize AI-generated symbol to base form.
        
        Args:
            symbol: Symbol from AI (e.g., 'EURUSD.m', 'EURUSD.pro')
        
        Returns:
            str: Normalized symbol (e.g., 'EURUSD')
        """
        if not symbol:
            return symbol
        
        # Convert to uppercase and remove common suffixes
        normalized = symbol.upper()
        normalized = normalized.replace('.M', '')
        normalized = normalized.replace('.PRO', '')
        normalized = normalized.replace('.', '')
        
        return normalized
    
    def fetch_all_symbols(self) -> Dict[str, str]:
        """
        Fetch all available symbols from broker and build lookup map.
        
        Returns:
            dict: Mapping of normalized symbols to broker symbols
        """
        try:
            if not self.mt5 or not self.mt5.is_connected:
                logger.warning("MT5 not connected - cannot fetch symbols")
                return {}
            
            # Get all symbols from broker
            symbols = mt5.symbols_get()
            if symbols is None:
                logger.warning("Failed to get symbols from MT5")
                return {}
            
            # Build mapping: normalized -> broker symbol
            symbol_map = {}
            for s in symbols:
                # Store both the full name and normalized version
                broker_symbol = s.name
                normalized = self._normalize_ai_symbol(broker_symbol)
                
                # Map normalized form to broker symbol
                if normalized not in symbol_map:
                    symbol_map[normalized] = broker_symbol
            
            logger.info(f"Fetched {len(symbol_map)} symbols from broker")
            
            # Log some examples for debugging
            sample_symbols = list(symbol_map.keys())[:10]
            logger.info(f"Sample broker symbols: {sample_symbols}")
            
            self._symbol_map = symbol_map
            self._last_refresh = datetime.now()
            
            return symbol_map
            
        except Exception as e:
            logger.error(f"Error fetching symbols from MT5: {e}", exc_info=True)
            return {}
    
    def get_symbol_map(self) -> Dict[str, str]:
        """
        Get the symbol map, fetching if necessary.
        
        Returns:
            dict: Symbol mapping
        """
        if self._symbol_map is None:
            self._symbol_map = self.fetch_all_symbols()
        return self._symbol_map
    
    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """
        Resolve AI symbol to actual broker symbol.
        
        Args:
            symbol: Symbol from AI system (e.g., 'EURUSD.m')
        
        Returns:
            str: Broker symbol or None if not found
        """
        if not symbol:
            return None
        
        # Get fresh symbol map
        symbol_map = self.get_symbol_map()
        
        if not symbol_map:
            logger.error("No symbol map available - cannot resolve symbol")
            return None
        
        # Normalize the input symbol
        normalized = self._normalize_ai_symbol(symbol)
        
        # Direct match
        if normalized in symbol_map:
            resolved = symbol_map[normalized]
            logger.info(f"Symbol resolved: {symbol} -> {resolved}")
            return resolved
        
        # Try partial match (e.g., EURUSD in EURUSD.m)
        for key, value in symbol_map.items():
            if normalized in key or key in normalized:
                logger.info(f"Symbol partially matched: {symbol} -> {value}")
                return value
        
        # No match found
        logger.error(f"Symbol not found in broker: {symbol} (normalized: {normalized})")
        logger.error(f"Available symbols sample: {list(symbol_map.keys())[:20]}")
        return None
    
    def is_symbol_available(self, symbol: str) -> bool:
        """
        Check if a symbol is available in the broker.
        
        Args:
            symbol: Symbol to check
        
        Returns:
            bool: True if symbol is available
        """
        resolved = self.resolve_symbol(symbol)
        return resolved is not None
    
    def refresh_symbol_map(self) -> None:
        """Refresh the symbol map from broker."""
        self._symbol_map = None
        self.get_symbol_map()
