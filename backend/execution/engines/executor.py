"""
Order Execution Engine - Places and manages orders on MT5

This module handles:
- Order placement (BUY/SELL)
- Slippage management
- Order status tracking
- Error handling and retry logic
"""

import MetaTrader5 as mt5
import logging
from typing import Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


def normalize_symbol(symbol: str) -> str:
    """Ensure symbol has .m suffix for MT5."""
    if not symbol.endswith('.m'):
        return symbol + '.m'
    return symbol


class OrderType(Enum):
    """Order types"""
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP


class OrderTimeType(Enum):
    """Order time types"""
    GTC = mt5.ORDER_TIME_GTC  # Good Till Cancelled
    DAY = mt5.ORDER_TIME_DAY  # Good for today


class OrderExecutor:
    """
    Executes orders on MetaTrader 5.
    """
    
    # Default deviation for market orders (in points)
    DEFAULT_DEVIATION = 100
    
    # Magic number for tracking orders
    MAGIC_NUMBER = 20260426
    
    def __init__(self, mt5_connection):
        """
        Initialize order executor.
        
        Args:
            mt5_connection: Connected MT5Connection instance
        """
        self.mt5 = mt5_connection
        self.last_order_id = None
        self.retry_count = 3
        self.retry_delay = 1.0
    
    def place_market_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        comment: str = "",
        deviation: int = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Place a market order (BUY/SELL).
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            order_type: 'BUY' or 'SELL'
            volume: Lot size
            entry_price: Entry price (for reference)
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Order comment
            deviation: Price deviation in points (default: 100)
        
        Returns:
            tuple: (success: bool, order_details: dict or None)
        """
        try:
            if not self.mt5.is_connected:
                return False, {"error": "Not connected to MT5"}
            
            # Prepare order details
            deviation = deviation or self.DEFAULT_DEVIATION
            
            # Normalize symbol to ensure .m suffix for MT5
            symbol = normalize_symbol(symbol)
            
            order_type_enum = OrderType.BUY if order_type.upper() == 'BUY' else OrderType.SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_enum.value,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": deviation,
                "magic": self.MAGIC_NUMBER,
                "comment": comment or f"{order_type} {symbol} {volume:.2f}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            
            logger.info(f"Placing {order_type} order for {symbol}:")
            logger.info(f"  Volume: {volume:.2f} lots")
            logger.info(f"  SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            logger.info(f"  Deviation: {deviation} points")
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order failed: {result.comment if result else 'Unknown error'}"
                logger.error(error_msg)
                return False, {
                    "error": error_msg,
                    "retcode": result.retcode if result else None,
                    "symbol": symbol,
                    "type": order_type
                }
            
            # Order succeeded
            order_info = {
                'order_id': result.order,
                'symbol': symbol,
                'type': order_type,
                'volume': volume,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'status': 'FILLED',
                'timestamp': datetime.now().isoformat(),
                'deal_id': result.deal,
                'price': result.price,
                'bid': result.bid,
                'ask': result.ask
            }
            
            logger.info(f"[OK] Order placed successfully!")
            logger.info(f"  Order ID: {result.order}")
            logger.info(f"  Deal ID: {result.deal}")
            logger.info(f"  Price: {result.price:.5f}")
            
            self.last_order_id = result.order
            return True, order_info
            
        except Exception as e:
            logger.error(f"Exception during order placement: {e}", exc_info=True)
            return False, {"error": str(e), "symbol": symbol, "type": order_type}
    
    def modify_order(
        self,
        order_id: int,
        symbol: str,
        new_stop_loss: float = None,
        new_take_profit: float = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Modify an existing order (SL/TP).
        
        Args:
            order_id: Order ID to modify
            symbol: Trading symbol
            new_stop_loss: New stop loss price
            new_take_profit: New take profit price
        
        Returns:
            tuple: (success: bool, result: dict or None)
        """
        try:
            if not self.mt5.is_connected:
                return False, {"error": "Not connected to MT5"}
            
            # Get current position
            position = self.mt5.get_position_by_symbol(symbol)
            if not position:
                return False, {"error": f"No open position for {symbol}"}
            
            # Normalize symbol to ensure .m suffix for MT5
            symbol = normalize_symbol(symbol)
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "sl": new_stop_loss,
                "tp": new_take_profit,
                "magic": self.MAGIC_NUMBER,
                "comment": "SL/TP modified"
            }
            
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Modification failed: {result.comment if result else 'Unknown error'}"
                logger.error(error_msg)
                return False, {"error": error_msg}
            
            logger.info(f"[OK] Order modified successfully: {symbol}")
            return True, {"order_id": order_id, "new_sl": new_stop_loss, "new_tp": new_take_profit}
            
        except Exception as e:
            logger.error(f"Exception during order modification: {e}", exc_info=True)
            return False, {"error": str(e)}
    
    def close_position(
        self,
        symbol: str,
        volume: float = None,
        comment: str = "Manual close"
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Close an open position.
        
        Args:
            symbol: Trading symbol
            volume: Volume to close (None = close all)
            comment: Close reason
        
        Returns:
            tuple: (success: bool, result: dict or None)
        """
        try:
            if not self.mt5.is_connected:
                return False, {"error": "Not connected to MT5"}
            
            # Get position
            position = self.mt5.get_position_by_symbol(symbol)
            if not position:
                return False, {"error": f"No open position for {symbol}"}
            
            # Determine close volume
            close_volume = volume or position['volume']
            
            # Normalize symbol to ensure .m suffix for MT5
            symbol = normalize_symbol(symbol)
            
            # Determine order type (opposite of open)
            close_type = OrderType.SELL if position['type'] == 'BUY' else OrderType.BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": close_volume,
                "type": close_type.value,
                "deviation": self.DEFAULT_DEVIATION,
                "magic": self.MAGIC_NUMBER,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            
            logger.info(f"Closing position: {symbol} {close_volume:.2f}")
            
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Close failed: {result.comment if result else 'Unknown error'}"
                logger.error(error_msg)
                return False, {"error": error_msg}
            
            logger.info(f"[OK] Position closed successfully: {symbol}")
            logger.info(f"  Deal: {result.deal} | Price: {result.price:.5f}")
            
            return True, {
                "symbol": symbol,
                "closed_volume": close_volume,
                "close_price": result.price,
                "deal_id": result.deal
            }
            
        except Exception as e:
            logger.error(f"Exception during position close: {e}", exc_info=True)
            return False, {"error": str(e)}
    
    def get_order_status(self, order_id: int) -> Optional[Dict]:
        """
        Get status of an order.
        
        Args:
            order_id: Order ID
        
        Returns:
            dict: Order information or None
        """
        try:
            if not self.mt5.is_connected:
                return None
            
            orders = mt5.history_orders_get(ticket=order_id)
            if not orders or len(orders) == 0:
                logger.warning(f"Order {order_id} not found in history")
                return None
            
            order = orders[0]
            return {
                'ticket': order.ticket,
                'symbol': order.symbol,
                'price_open': order.price_open,
                'state': order.state,
                'time_setup': order.time_setup,
                'time_done': order.time_done,
                'comment': order.comment
            }
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None


def create_order_executor(mt5_connection) -> OrderExecutor:
    """
    Factory function to create order executor.
    
    Args:
        mt5_connection: Connected MT5Connection instance
    
    Returns:
        OrderExecutor: Order executor instance
    """
    return OrderExecutor(mt5_connection)
