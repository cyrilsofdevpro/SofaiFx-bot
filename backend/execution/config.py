"""
MT5 Execution Service - Configuration Template

Copy this file to config.py and update with your settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ===== MT5 ACCOUNT CREDENTIALS =====
# Get from your MT5 terminal
MT5_ACCOUNT = int(os.getenv('MT5_ACCOUNT', '1234567'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD', 'your_password')
MT5_SERVER = os.getenv('MT5_SERVER', 'ICMarkets-Demo')  # Change to 'ICMarkets' for live trading

# ===== BACKEND API CONFIGURATION =====
# URL of the SofAi FX backend API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
USER_ID = int(os.getenv('USER_ID', '1'))

# ===== EXECUTION SERVICE SETTINGS =====
# Signal polling interval in seconds (shorter = more responsive but more CPU/bandwidth)
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '30'))

# Maximum number of open positions allowed at once
MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '5'))

# Risk percentage per trade (recommended: 1-2% for safety)
# Formula: Position Size = (Account Balance * Risk%) / (SL Distance in Pips * Pip Value)
RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', '1.0'))

# Maximum daily loss percentage before stopping all trading (safety circuit breaker)
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '5.0'))

# Maximum acceptable spread in pips (wider spreads = higher slippage, trades rejected if exceeded)
MIN_SPREAD_THRESHOLD = float(os.getenv('MIN_SPREAD_THRESHOLD', '10.0'))

# ===== LOGGING CONFIGURATION =====
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR
LOG_DIR = os.getenv('LOG_DIR', 'backend/execution/logs')

# ===== SAFETY & CONTROL =====
# Master kill switch - set to False to disable all trading
BOT_ENABLED = os.getenv('BOT_ENABLED', 'True').lower() == 'true'

# Close all positions when service stops (recommended: False to preserve positions)
CLOSE_POSITIONS_ON_STOP = os.getenv('CLOSE_POSITIONS_ON_STOP', 'False').lower() == 'true'

# ===== ENVIRONMENT =====
# Set to 'DEMO' for testing, 'LIVE' for real trading
ENVIRONMENT = os.getenv('ENVIRONMENT', 'DEMO')

# ===== ADVANCED SETTINGS =====
# Connection timeout in seconds
CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', '10'))

# Order deviation in points (slippage tolerance for market orders)
ORDER_DEVIATION = int(os.getenv('ORDER_DEVIATION', '100'))

# Retry attempts for failed orders
ORDER_RETRY_COUNT = int(os.getenv('ORDER_RETRY_COUNT', '3'))


def print_config():
    """Print current configuration (for debugging)"""
    print("\n" + "=" * 70)
    print("MT5 EXECUTION SERVICE CONFIGURATION")
    print("=" * 70)
    print(f"Environment: {ENVIRONMENT}")
    print(f"MT5 Account: {MT5_ACCOUNT} (Server: {MT5_SERVER})")
    print(f"API URL: {API_BASE_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Polling Interval: {POLLING_INTERVAL}s")
    print(f"Max Positions: {MAX_OPEN_POSITIONS}")
    print(f"Risk Per Trade: {RISK_PER_TRADE}%")
    print(f"Max Daily Loss: {MAX_DAILY_LOSS}%")
    print(f"Max Spread: {MIN_SPREAD_THRESHOLD}p")
    print(f"Bot Enabled: {BOT_ENABLED}")
    print(f"Log Level: {LOG_LEVEL}")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    print_config()
