"""
MT5 Account Service - Cross-Platform Implementation

This module handles:
- Live account data retrieval from MT5 terminal (Windows)
- Stub implementation for Linux/Render environments
- Account info formatting for API responses
- Connection status checking
- Account balance/equity/margin tracking

Platform Detection:
- Windows: Uses actual MetaTrader5 package
- Linux/Render: Returns stub data with clear messaging

Trade Execution Architecture:
- Backend (Render): Signal generation only
- Windows VPS/PC: Trade execution via MT5 terminal
- Communication: REST API or messaging layer
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Detect platform - Linux/Render vs Windows
_IS_LINUX = os.name == 'posix' or os.getenv('RENDER') == 'true'

# Conditional import - only on Windows
if _IS_LINUX:
    # Linux/Render: Stub implementation
    mt5 = None
    logger.warning("MT5AccountService: Running on Linux - using stub implementation")
else:
    # Windows: Import actual MT5
    try:
        import MetaTrader5 as mt5
    except ImportError:
        mt5 = None
        logger.warning("MT5AccountService: MetaTrader5 not available")

logger = logging.getLogger(__name__)


class MT5AccountService:
    """
    Service for retrieving and managing MT5 account information.
    
    Provides methods to fetch live broker account data including:
    - Balance and equity
    - Margin information
    - Leverage and currency
    - Connection status
    """
    
    @staticmethod
    def get_account_info() -> Dict[str, Any]:
        """
        Get account information from MT5 terminal.
        
        On Linux/Render: Returns stub data explaining MT5 not available
        On Windows: Returns live data from MT5 terminal
        
        Returns:
            dict: Account information or connection error info
            
        Example:
            {
                "connected": True,
                "balance": 10000.50,
                "equity": 10500.75,
                "margin": 2000.00,
                "free_margin": 8500.75,
                "margin_level": 525.0,
                "leverage": 100,
                "currency": "USD",
                "login": 123456,
                "server": "ICMarkets-Demo",
                "trade_mode": "demo",
                "timestamp": "2024-04-26T10:30:45.123456"
            }
        """
        # Linux/Render stub
        if _IS_LINUX or mt5 is None:
            logger.warning("MT5AccountService: Running on Linux/Render - MT5 not available")
            return {
                "connected": False,
                "platform": "linux" if _IS_LINUX else "windows_no_mt5",
                "message": "MT5 not available on Linux/Render. Deploy Windows VPS for trade execution.",
                "error": "MT5_NOT_AVAILABLE",
                "docs": "See MT5_SETUP_REQUIRED.md for deployment instructions",
                "balance": 0,
                "equity": 0,
                "margin": 0,
                "free_margin": 0,
                "margin_level": 0,
                "leverage": 0,
                "currency": "USD",
                "login": 0,
                "server": "N/A",
                "trade_mode": "disabled",
                "account_type": "stub",
                "execution_mode": "signals_only",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Windows: Use actual MT5
        try:
            # Check if MT5 is initialized
            if mt5.version() is None:
                logger.warning("MT5 not initialized")
                return {
                    "connected": False,
                    "message": "MT5 not initialized",
                    "error": "MT5_NOT_INITIALIZED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get account info from MT5
            account = mt5.account_info()
            
            if account is None:
                logger.warning("Failed to retrieve account info from MT5")
                return {
                    "connected": False,
                    "message": "Failed to connect to MT5 terminal",
                    "error": "ACCOUNT_INFO_FAILED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Determine trade mode (1 = demo, 2 = live, 0 = contest)
            trade_mode = "demo" if account.trade_mode == 1 else "live" if account.trade_mode == 2 else "contest"
            
            # Build response
            response = {
                "connected": True,
                "balance": round(float(account.balance), 2),
                "equity": round(float(account.equity), 2),
                "margin": round(float(account.margin), 2),
                "free_margin": round(float(account.margin_free), 2),
                "margin_level": round(float(account.margin_level), 2),
                "leverage": int(account.leverage),
                "currency": str(account.currency),
                "login": int(account.login),
                "server": str(account.server),
                "trade_mode": trade_mode,
                "profit_loss": round(float(account.profit), 2),
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Account data retrieved successfully"
            }
            
            logger.info(f"✓ Account info retrieved for login {account.login}")
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving account info: {e}", exc_info=True)
            return {
                "connected": False,
                "message": f"Error retrieving account info: {str(e)}",
                "error": "ACCOUNT_RETRIEVE_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_account_summary() -> Dict[str, Any]:
        """
        Get account summary for dashboard display.
        
        Returns:
            dict: Account summary with key metrics
        """
        account_info = MT5AccountService.get_account_info()
        
        if not account_info.get("connected"):
            return {
                "status": "disconnected",
                "message": account_info.get("message", "Not connected"),
                "timestamp": account_info.get("timestamp")
            }
        
        # Calculate additional metrics
        used_margin = account_info["margin"]
        free_margin = account_info["free_margin"]
        total_margin = used_margin + free_margin
        margin_percentage = (used_margin / total_margin * 100) if total_margin > 0 else 0
        
        # Calculate profit/loss percentage
        balance = account_info["balance"]
        profit_loss_pct = (account_info["profit_loss"] / balance * 100) if balance > 0 else 0
        
        return {
            "status": "connected",
            "account_number": account_info["login"],
            "server": account_info["server"],
            "account_type": account_info["trade_mode"].upper(),
            "balance": account_info["balance"],
            "equity": account_info["equity"],
            "profit_loss": account_info["profit_loss"],
            "profit_loss_pct": round(profit_loss_pct, 2),
            "margin": account_info["margin"],
            "free_margin": account_info["free_margin"],
            "margin_level": account_info["margin_level"],
            "margin_percentage": round(margin_percentage, 2),
            "leverage": account_info["leverage"],
            "currency": account_info["currency"],
            "timestamp": account_info["timestamp"]
        }
    
    @staticmethod
    def check_connection_status() -> Dict[str, Any]:
        """
        Check if MT5 terminal is connected.
        
        Returns:
            dict: Connection status information
        """
        # Linux/Render stub
        if _IS_LINUX or mt5 is None:
            return {
                "connected": False,
                "platform": "linux" if _IS_LINUX else "windows_no_mt5",
                "message": "MT5 not available on Linux/Render",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            if mt5.version() is None:
                return {
                    "connected": False,
                    "message": "MT5 terminal not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Try to get version info to verify connection
            version_info = mt5.version()
            
            return {
                "connected": True,
                "message": "MT5 terminal connected",
                "build": version_info[1] if version_info else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return {
                "connected": False,
                "message": f"Connection check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_positions_summary() -> Dict[str, Any]:
        """
        Get summary of open positions.
        
        Returns:
            dict: Summary of open positions
        """
        # Linux/Render stub
        if _IS_LINUX or mt5 is None:
            return {
                "connected": False,
                "platform": "linux" if _IS_LINUX else "windows_no_mt5",
                "message": "MT5 positions unavailable on Linux/Render",
                "positions": [],
                "total_positions": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            if mt5.version() is None:
                return {
                    "connected": False,
                    "positions": [],
                    "total_positions": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            positions = mt5.positions_get()
            
            if positions is None:
                return {
                    "connected": True,
                    "positions": [],
                    "total_positions": 0,
                    "message": "No open positions",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            positions_list = []
            total_profit = 0.0
            
            for pos in positions:
                positions_list.append({
                    "ticket": int(pos.ticket),
                    "symbol": str(pos.symbol),
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": float(pos.volume),
                    "price_open": float(pos.price_open),
                    "sl": float(pos.sl) if pos.sl > 0 else None,
                    "tp": float(pos.tp) if pos.tp > 0 else None,
                    "profit": round(float(pos.profit), 2),
                    "comment": str(pos.comment) if pos.comment else None,
                    "time_open": datetime.fromtimestamp(pos.time).isoformat()
                })
                total_profit += float(pos.profit)
            
            return {
                "connected": True,
                "positions": positions_list,
                "total_positions": len(positions_list),
                "total_profit": round(total_profit, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}", exc_info=True)
            return {
                "connected": False,
                "positions": [],
                "total_positions": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_account_health() -> Dict[str, Any]:
        """
        Get account health metrics and warnings.
        
        Returns:
            dict: Health status with warnings/alerts
        """
        account_info = MT5AccountService.get_account_info()
        
        if not account_info.get("connected"):
            return {
                "status": "disconnected",
                "health_score": 0,
                "warnings": ["MT5 terminal not connected"],
                "timestamp": account_info.get("timestamp")
            }
        
        warnings = []
        health_score = 100
        
        # Check margin level
        margin_level = account_info["margin_level"]
        if margin_level < 100:
            warnings.append(f"CRITICAL: Margin level {margin_level}% - Account will be closed!")
            health_score -= 50
        elif margin_level < 300:
            warnings.append(f"WARNING: Low margin level {margin_level}% - Risk of liquidation")
            health_score -= 30
        elif margin_level < 1000:
            warnings.append(f"CAUTION: Margin level {margin_level}% - Moderate risk")
            health_score -= 10
        
        # Check free margin
        free_margin = account_info["free_margin"]
        if free_margin < 0:
            warnings.append("CRITICAL: Negative free margin")
            health_score -= 30
        
        # Check account type
        is_demo = account_info["trade_mode"] == "demo"
        if is_demo:
            warnings.append("Demo account - not trading with real money")
        
        return {
            "status": "connected",
            "health_score": max(0, health_score),
            "margin_level": account_info["margin_level"],
            "free_margin": account_info["free_margin"],
            "account_type": account_info["trade_mode"],
            "warnings": warnings,
            "is_demo": is_demo,
            "timestamp": account_info["timestamp"]
        }
