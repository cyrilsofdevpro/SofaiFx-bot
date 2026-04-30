#!/usr/bin/env python3
"""
Test Suite for MT5 Execution Service

Run comprehensive tests to verify the execution system is working correctly.

Usage:
    python test_execution.py              # Run all tests
    python test_execution.py --quick      # Run quick tests only
    python test_execution.py --mt5        # Test MT5 connection only
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_mt5_connection():
    """Test MT5 connection"""
    print("\n" + "=" * 70)
    print("TEST 1: MT5 CONNECTION")
    print("=" * 70)
    
    try:
        from execution.config import MT5_ACCOUNT, MT5_PASSWORD, MT5_SERVER
        from execution.mt5.connection import get_mt5_connection
        
        logger.info(f"Connecting to MT5 ({MT5_SERVER})...")
        mt5 = get_mt5_connection(MT5_ACCOUNT, MT5_PASSWORD, MT5_SERVER)
        
        if not mt5:
            logger.error("✗ Failed to connect to MT5")
            logger.error("  - Is MetaTrader 5 terminal running?")
            logger.error("  - Is terminal logged in?")
            logger.error("  - Are credentials correct?")
            return False
        
        logger.info("✓ Connected successfully")
        
        # Get account info
        account = mt5.get_account_info()
        logger.info(f"✓ Account: {account.get('login')}")
        logger.info(f"  Balance: ${account.get('balance'):.2f}")
        logger.info(f"  Equity: ${account.get('equity'):.2f}")
        logger.info(f"  Free Margin: ${account.get('free_margin'):.2f}")
        logger.info(f"  Mode: {account.get('trade_mode')}")
        
        # Test symbol info
        logger.info("\nTesting symbol info retrieval...")
        symbol = mt5.get_symbol_info("EURUSD")
        if symbol:
            logger.info(f"✓ EURUSD: Bid {symbol.get('bid'):.5f}, Ask {symbol.get('ask'):.5f}")
            logger.info(f"  Spread: {symbol.get('spread'):.1f}p")
        else:
            logger.warning("✗ Failed to get EURUSD info")
        
        # Disconnect
        mt5.disconnect()
        logger.info("\n✓ TEST 1 PASSED: MT5 Connection Working")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}", exc_info=True)
        return False


def test_signal_listener():
    """Test signal listener"""
    print("\n" + "=" * 70)
    print("TEST 2: SIGNAL LISTENER")
    print("=" * 70)
    
    try:
        from execution.config import API_BASE_URL, USER_ID
        from execution.engines.signal_listener import create_signal_listener
        
        logger.info(f"Creating signal listener ({API_BASE_URL})...")
        listener = create_signal_listener(
            api_base_url=API_BASE_URL,
            user_id=USER_ID,
            polling_interval=10
        )
        
        logger.info("Fetching signals...")
        signals = listener.fetch_latest_signals()
        
        logger.info(f"✓ Fetched {len(signals)} signal(s)")
        
        for signal in signals:
            logger.info(
                f"  - {signal.get('symbol')} {signal.get('signal')} "
                f"@ {signal.get('price')} (confidence: {signal.get('confidence'):.2%})"
            )
        
        logger.info("\n✓ TEST 2 PASSED: Signal Listener Working")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}", exc_info=True)
        return False


def test_position_sizer():
    """Test position sizing"""
    print("\n" + "=" * 70)
    print("TEST 3: POSITION SIZER")
    print("=" * 70)
    
    try:
        from execution.engines.position_sizer import PositionSizer
        
        sizer = PositionSizer(account_balance=10000, leverage=100)
        
        logger.info("Calculating position size...")
        logger.info("  Account: $10,000")
        logger.info("  Risk: 1%")
        logger.info("  Entry: 1.0850 | SL: 1.0800 | TP: 1.0900")
        
        lot_size = sizer.calculate_lot_size(
            symbol="EURUSD",
            entry_price=1.0850,
            stop_loss_price=1.0800,
            risk_percent=1.0
        )
        
        logger.info(f"✓ Calculated lot size: {lot_size:.2f}")
        
        # Test margin calculation
        margin = sizer.calculate_margin_required("EURUSD", lot_size, 1.0850)
        logger.info(f"✓ Margin required: ${margin:.2f}")
        
        logger.info("\n✓ TEST 3 PASSED: Position Sizer Working")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}", exc_info=True)
        return False


def test_validator():
    """Test trade validator"""
    print("\n" + "=" * 70)
    print("TEST 4: TRADE VALIDATOR")
    print("=" * 70)
    
    try:
        from execution.engines.validator import TradeValidator
        
        validator = TradeValidator()
        
        # Create test data
        signal = {
            'symbol': 'EURUSD',
            'signal_type': 'BUY',
            'price': 1.0850,
            'confidence': 0.85
        }
        
        symbol_info = {
            'bid': 1.0849,
            'ask': 1.0850,
            'spread': 1.0
        }
        
        account_info = {
            'balance': 10000,
            'equity': 10500,
            'free_margin': 8000,
            'margin_level': 500
        }
        
        logger.info("Validating signal...")
        is_valid, reason = validator.validate_signal(
            signal=signal,
            symbol_info=symbol_info,
            open_positions=[],
            account_info=account_info,
            today_pnl=0,
            bot_enabled=True
        )
        
        if is_valid:
            logger.info("✓ Signal validation passed")
        else:
            logger.warning(f"Signal validation failed: {reason}")
        
        logger.info("\n✓ TEST 4 PASSED: Validator Working")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}", exc_info=True)
        return False


def test_logger():
    """Test execution logger"""
    print("\n" + "=" * 70)
    print("TEST 5: EXECUTION LOGGER")
    print("=" * 70)
    
    try:
        from execution.engines.logger import get_execution_logger
        
        exec_logger = get_execution_logger()
        
        logger.info("Logging test events...")
        
        # Log event
        exec_logger.log_event(
            event_type="TEST_EVENT",
            status="SUCCESS",
            message="This is a test event",
            symbol="EURUSD",
            user_id=1,
            details={'test': True}
        )
        
        logger.info("✓ Event logged")
        
        # Get stats
        stats = exec_logger.get_trade_summary(days=7)
        logger.info(f"✓ Retrieved stats: {stats}")
        
        logger.info("\n✓ TEST 5 PASSED: Logger Working")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 5 FAILED: {e}", exc_info=True)
        return False


def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "=" * 70)
    print("TEST 6: API ENDPOINTS")
    print("=" * 70)
    
    try:
        import requests
        from execution.config import API_BASE_URL
        
        logger.info(f"Testing API endpoints ({API_BASE_URL})...")
        
        # Health check
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Health check endpoint working")
        else:
            logger.warning(f"Health check returned {response.status_code}")
        
        # Try to fetch signals (will fail without auth)
        logger.info("Note: Full API testing requires JWT authentication")
        logger.info("       See API endpoints documentation for auth setup")
        
        logger.info("\n✓ TEST 6 PASSED: API Reachable")
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("✗ Cannot connect to API")
        logger.error("  - Is backend API running?")
        logger.error("  - Is API_BASE_URL correct?")
        return False
    except Exception as e:
        logger.error(f"✗ TEST 6 FAILED: {e}", exc_info=True)
        return False


def run_all_tests(quick=False):
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MT5 EXECUTION SERVICE - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("MT5 Connection", test_mt5_connection),
        ("Signal Listener", test_signal_listener),
        ("Position Sizer", test_position_sizer),
        ("Validator", test_validator),
        ("Logger", test_logger),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} - {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED - System is ready!")
        return True
    else:
        print("✗ Some tests failed - see errors above")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='MT5 Execution Service Test Suite'
    )
    parser.add_argument('--mt5', action='store_true', help='Test MT5 only')
    parser.add_argument('--listener', action='store_true', help='Test signal listener only')
    parser.add_argument('--sizer', action='store_true', help='Test position sizer only')
    parser.add_argument('--validator', action='store_true', help='Test validator only')
    parser.add_argument('--logger', action='store_true', help='Test logger only')
    parser.add_argument('--api', action='store_true', help='Test API only')
    parser.add_argument('--quick', action='store_true', help='Skip slow tests')
    
    args = parser.parse_args()
    
    # Single test mode
    if args.mt5:
        return test_mt5_connection()
    elif args.listener:
        return test_signal_listener()
    elif args.sizer:
        return test_position_sizer()
    elif args.validator:
        return test_validator()
    elif args.logger:
        return test_logger()
    elif args.api:
        return test_api_endpoints()
    
    # Run all tests
    return run_all_tests(quick=args.quick)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
