import logging
import logging.handlers
from datetime import datetime
import os

# ============================================
# Configure Logging System
# ============================================

# Create logger
logger = logging.getLogger('SofAi-FX')
logger.setLevel(logging.DEBUG)

# Create logs directory
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# ============================================
# Console Handler (Console Output)
# ============================================
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# ============================================
# File Handler (Rotating Logs)
# ============================================
log_filename = os.path.join(log_dir, 'sofai_fx.log')
file_handler = logging.handlers.RotatingFileHandler(
    log_filename,
    maxBytes=10485760,  # 10 MB
    backupCount=5  # Keep 5 backup files
)
file_handler.setLevel(logging.DEBUG)

# ============================================
# Error File Handler (Errors Only)
# ============================================
error_log_filename = os.path.join(log_dir, 'sofai_fx_errors.log')
error_handler = logging.handlers.RotatingFileHandler(
    error_log_filename,
    maxBytes=10485760,  # 10 MB
    backupCount=3
)
error_handler.setLevel(logging.ERROR)

# ============================================
# Formatter
# ============================================
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler.setFormatter(console_formatter)
file_handler.setFormatter(detailed_formatter)
error_handler.setFormatter(detailed_formatter)

# ============================================
# Add Handlers to Logger
# ============================================
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_handler)

# ============================================
# Module-Specific Loggers
# ============================================
def get_logger(module_name: str):
    """Get a logger for a specific module
    
    Args:
        module_name: Name of the module
    
    Returns:
        Logger instance for the module
    """
    return logging.getLogger(f'SofAi-FX.{module_name}')


# Initialize module loggers
signal_logger = get_logger('Signals')
backtest_logger = get_logger('Backtesting')
execution_logger = get_logger('Execution')
optimization_logger = get_logger('Optimization')
api_logger = get_logger('API')
database_logger = get_logger('Database')
mt5_logger = get_logger('MT5')

# ============================================
# Logging Events Helper
# ============================================
def log_event(event_type: str, details: dict, module: str = 'General'):
    """Log a structured event
    
    Args:
        event_type: Type of event (e.g., 'SIGNAL_GENERATED', 'TRADE_EXECUTED')
        details: Dictionary with event details
        module: Module name
    """
    module_logger = get_logger(module)
    message = f"[{event_type}] " + " | ".join(f"{k}={v}" for k, v in details.items())
    module_logger.info(message)


if __name__ == '__main__':
    logger.info('Logger initialized')
    logger.debug('Debug logging enabled')
    signal_logger.info('Signal logger ready')
    backtest_logger.info('Backtest logger ready')
