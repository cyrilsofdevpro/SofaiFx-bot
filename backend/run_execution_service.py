#!/usr/bin/env python
"""
MT5 Execution Service Runner

This script starts the automated trading execution service.

Usage:
    python run_execution_service.py
    
Requirements:
    1. MetaTrader 5 terminal must be running and logged in
    2. .env file must be configured with MT5 credentials
    3. Backend API must be running (e.g., http://localhost:5000)

Configuration (.env):
    MT5_ACCOUNT=1234567
    MT5_PASSWORD=your_password
    MT5_SERVER=ICMarkets-Demo
    API_BASE_URL=http://localhost:5000
    USER_ID=1
    BOT_ENABLED=True
    POLLING_INTERVAL=30
    RISK_PER_TRADE=1.0
"""

import os
import sys
import logging
import signal
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Get the script's directory for log paths
script_dir = Path(__file__).parent
log_dir = script_dir / 'execution' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'execution_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = ['MT5_ACCOUNT', 'MT5_PASSWORD', 'MT5_SERVER']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("=" * 70)
        logger.error("❌ CONFIGURATION ERROR")
        logger.error("=" * 70)
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("\nPlease configure .env file with:")
        logger.error("  MT5_ACCOUNT=your_account_number")
        logger.error("  MT5_PASSWORD=your_password")
        logger.error("  MT5_SERVER=ICMarkets-Demo (or your broker server)")
        logger.error("=" * 70)
        return False
    
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import MetaTrader5
        logger.info("[OK] MetaTrader5 package found")
    except ImportError:
        logger.error("[!] MetaTrader5 package not found!")
        logger.error("Install with: pip install MetaTrader5")
        return False
    
    try:
        import requests
        logger.info("[OK] requests package found")
    except ImportError:
        logger.error("[!] requests package not found!")
        logger.error("Install with: pip install requests")
        return False
    
    return True


def check_mt5_terminal():
    """Check if MT5 terminal is running."""
    try:
        import MetaTrader5 as mt5
        
        logger.info("\nChecking MetaTrader 5 terminal...")
        
        # Try to initialize (this will fail if terminal is not running)
        if mt5.initialize():
            logger.info("[OK] MT5 terminal is running and accessible")
            mt5.shutdown()
            return True
        else:
            logger.error("[!] MT5 terminal is not running!")
            logger.error("Please start MetaTrader 5 terminal and try again")
            return False
            
    except Exception as e:
        logger.error(f"[!] Error checking MT5 terminal: {e}")
        return False


def main():
    """Main entry point for the execution service."""
    try:
        logger.info("\n" + "=" * 70)
        logger.info("[>>] MT5 EXECUTION SERVICE STARTUP")
        logger.info("=" * 70)
        
        # Step 1: Validate environment
        logger.info("\n[1/4] Validating environment...")
        if not validate_environment():
            sys.exit(1)
        logger.info("[OK] Environment validation passed")
        
        # Step 2: Check dependencies
        logger.info("\n[2/4] Checking dependencies...")
        if not check_dependencies():
            sys.exit(1)
        logger.info("[OK] All dependencies found")
        
        # Step 3: Check MT5 terminal
        logger.info("\n[3/4] Checking MT5 terminal...")
        if not check_mt5_terminal():
            sys.exit(1)
        
        # Step 4: Start execution service
        logger.info("\n[4/4] Starting execution service...")
        
        from execution.service import ExecutionService
        
        # Get configuration from environment
        mt5_account = int(os.getenv('MT5_ACCOUNT'))
        mt5_password = os.getenv('MT5_PASSWORD')
        mt5_server = os.getenv('MT5_SERVER', 'ICMarkets-Demo')
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
        user_id = int(os.getenv('USER_ID', '1'))
        polling_interval = int(os.getenv('POLLING_INTERVAL', '30'))
        
        # Create and start service
        service = ExecutionService(
            mt5_account=mt5_account,
            mt5_password=mt5_password,
            mt5_server=mt5_server,
            api_base_url=api_base_url,
            user_id=user_id,
            polling_interval=polling_interval
        )
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\n\nReceived interrupt signal - shutting down gracefully...")
            service.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the service (blocking)
        service.run()
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure you're running from the backend directory")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
