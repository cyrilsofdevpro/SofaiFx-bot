"""
MT5 Execution Layer - Automated trading execution via MetaTrader 5
"""

from .mt5.connection import MT5Connection, get_mt5_connection
from .engines.position_sizer import PositionSizer
from .engines.validator import TradeValidator
from .engines.executor import OrderExecutor, create_order_executor
from .engines.signal_listener import SignalListener, create_signal_listener
from .engines.logger import ExecutionLogger, get_execution_logger

__all__ = [
    'MT5Connection',
    'get_mt5_connection',
    'PositionSizer',
    'TradeValidator',
    'OrderExecutor',
    'create_order_executor',
    'SignalListener',
    'create_signal_listener',
    'ExecutionLogger',
    'get_execution_logger',
]
