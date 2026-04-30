#!/usr/bin/env python3
"""
MT5 Execution Service Runner

This script starts the automated trading execution service.

Usage:
    python run_execution_service.py
    
Requirements:
    - MetaTrader5 terminal running and logged in
    - Configuration set in backend/execution/config.py
    - Backend API running and accessible

"""

import sys
import os
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all requirements are met"""
    logger.info("Checking requirements...")
    
    # Check MetaTrader5 package
    try:
        import MetaTrader5
        logger.info("✓ MetaTrader5 package installed")
    except ImportError:
        logger.error("✗ MetaTrader5 package not installed")
        logger.error("  Install with: pip install MetaTrader5")
        return False
    
    # Check requests package
    try:
        import requests
        logger.info("✓ Requests package installed")
    except ImportError:
        logger.error("✗ Requests package not installed")
        logger.error("  Install with: pip install requests")
        return False
    
    # Check configuration file
    config_path = Path(__file__).parent / 'backend' / 'execution' / 'config.py'
    if not config_path.exists():
        logger.error(f"✗ Configuration file not found: {config_path}")
        logger.error("  Create configuration by copying config.py template")
        return False
    
    logger.info("✓ Configuration file found")
    
    return True


def load_configuration():
    """Load configuration"""
    try:
        from execution.config import (
            MT5_ACCOUNT, MT5_PASSWORD, MT5_SERVER,
            API_BASE_URL, USER_ID, POLLING_INTERVAL,
            BOT_ENABLED, ENVIRONMENT, print_config
        )
        
        # Print configuration
        print_config()
        
        return {
            'mt5_account': MT5_ACCOUNT,
            'mt5_password': MT5_PASSWORD,
            'mt5_server': MT5_SERVER,
            'api_base_url': API_BASE_URL,
            'user_id': USER_ID,
            'polling_interval': POLLING_INTERVAL,
            'bot_enabled': BOT_ENABLED,
            'environment': ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None


def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("MT5 EXECUTION SERVICE")
    logger.info("=" * 70)
    
    # Check requirements
    if not check_requirements():
        logger.error("Requirements not met. Please install missing dependencies.")
        sys.exit(1)
    
    # Load configuration
    config = load_configuration()
    if not config:
        logger.error("Failed to load configuration")
        sys.exit(1)
    
    # Check for demo/live mode
    if config['environment'].upper() == 'LIVE':
        logger.warning("=" * 70)
        logger.warning("WARNING: LIVE TRADING MODE ENABLED")
        logger.warning("This will execute REAL trades with REAL MONEY")
        logger.warning("=" * 70)
        response = input("Are you sure? Type 'YES' to continue: ")
        if response.upper() != 'YES':
            logger.info("Aborted")
            sys.exit(0)
    
    # Import and run service
    try:
        from execution.service import ExecutionService
        
        logger.info("\nStarting MT5 Execution Service...")
        logger.info("Press Ctrl+C to stop\n")
        
        service = ExecutionService(
            mt5_account=config['mt5_account'],
            mt5_password=config['mt5_password'],
            mt5_server=config['mt5_server'],
            api_base_url=config['api_base_url'],
            user_id=config['user_id'],
            polling_interval=config['polling_interval']
        )
        
        # Run service (blocking)
        service.run()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
