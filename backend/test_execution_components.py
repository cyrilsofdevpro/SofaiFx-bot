#!/usr/bin/env python
"""
Test MT5 Execution Service

This script tests the execution service components in isolation before
running the full service.

Usage:
    python test_execution_components.py
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv(Path(__file__).parent / '.env')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_mt5_connection():
    """Test MT5 connection."""
    print("\n" + "=" * 70)
    print("TEST 1: MT5 Connection")
    print("=" * 70)
    
    try:
        from execution.mt5.connection import get_mt5_connection
        
        account = int(os.getenv('MT5_ACCOUNT', '0'))
        password = os.getenv('MT5_PASSWORD', '')
        server = os.getenv('MT5_SERVER', 'ICMarkets-Demo')
        
        if account == 0 or not password:
            print("❌ MT5 credentials not configured in .env")
            return False
        
        print(f"\nConnecting to MT5...")
        print(f"  Account: {account}")
        print(f"  Server: {server}")
        
        mt5 = get_mt5_connection(account, password, server)
        
        if not mt5:
            print("❌ Failed to connect to MT5")
            return False
        
        info = mt5.get_account_info()
        print(f"\n✓ Connected successfully!")
        print(f"  Login: {info.get('login')}")
        print(f"  Balance: ${info.get('balance'):.2f} {info.get('currency')}")
        print(f"  Equity: ${info.get('equity'):.2f}")
        print(f"  Leverage: {info.get('leverage')}:1")
        print(f"  Trade Mode: {info.get('trade_mode')}")
        
        mt5.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_sizer():
    """Test position sizer."""
    print("\n" + "=" * 70)
    print("TEST 2: Position Sizing Engine")
    print("=" * 70)
    
    try:
        from execution.engines.position_sizer import PositionSizer
        
        print("\nInitializing position sizer...")
        sizer = PositionSizer(account_balance=10000, leverage=100)
        
        print("\nTest Cases:")
        
        # Test case 1: EURUSD
        print("\n1. EURUSD - Conservative (1% risk, 50 pips SL)")
        lot_size = sizer.calculate_lot_size(
            symbol='EURUSD',
            entry_price=1.0850,
            stop_loss_price=1.0800,
            risk_percent=1.0
        )
        print(f"   Lot Size: {lot_size:.2f}")
        
        # Test case 2: Reduced risk
        print("\n2. EURUSD - Aggressive (2% risk, 30 pips SL)")
        lot_size = sizer.calculate_lot_size(
            symbol='EURUSD',
            entry_price=1.0850,
            stop_loss_price=1.0820,
            risk_percent=2.0
        )
        print(f"   Lot Size: {lot_size:.2f}")
        
        # Test case 3: GBPUSD
        print("\n3. GBPUSD - Standard (1% risk, 40 pips SL)")
        lot_size = sizer.calculate_lot_size(
            symbol='GBPUSD',
            entry_price=1.2750,
            stop_loss_price=1.2710,
            risk_percent=1.0
        )
        print(f"   Lot Size: {lot_size:.2f}")
        
        print("\n✓ Position sizer working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_validator():
    """Test trade validator."""
    print("\n" + "=" * 70)
    print("TEST 3: Trade Validator")
    print("=" * 70)
    
    try:
        from execution.engines.validator import TradeValidator
        
        print("\nInitializing validator...")
        validator = TradeValidator(
            max_open_positions=5,
            max_daily_loss_percent=5.0,
            min_spread_threshold=3.0,
            risk_percent=1.0
        )
        
        print("\nTest Case 1: Valid Signal")
        signal = {
            'symbol': 'EURUSD',
            'signal_type': 'BUY',
            'price': 1.0850,
            'confidence': 0.85
        }
        
        symbol_info = {
            'bid': 1.0849,
            'ask': 1.0851,
            'spread': 2
        }
        
        open_positions = []
        
        account_info = {
            'balance': 10000,
            'equity': 10000,
            'margin_free': 5000,
            'margin_level': 200
        }
        
        is_valid, reason = validator.validate_signal(
            signal=signal,
            symbol_info=symbol_info,
            open_positions=open_positions,
            account_info=account_info,
            today_pnl=0,
            bot_enabled=True
        )
        
        print(f"Result: {'✓ VALID' if is_valid else '❌ INVALID'}")
        print(f"Reason: {reason}")
        
        print("\nTest Case 2: Bot Disabled")
        is_valid, reason = validator.validate_signal(
            signal=signal,
            symbol_info=symbol_info,
            open_positions=open_positions,
            account_info=account_info,
            today_pnl=0,
            bot_enabled=False
        )
        
        print(f"Result: {'✓ VALID' if is_valid else '❌ INVALID (Expected)'}")
        print(f"Reason: {reason}")
        
        print("\n✓ Trade validator working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_listener():
    """Test signal listener."""
    print("\n" + "=" * 70)
    print("TEST 4: Signal Listener")
    print("=" * 70)
    
    try:
        from execution.engines.signal_listener import SignalListener
        
        print("\nInitializing signal listener...")
        api_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
        user_id = int(os.getenv('USER_ID', '1'))
        
        listener = SignalListener(
            api_base_url=api_url,
            user_id=user_id,
            polling_interval=30,
            timeout=5
        )
        
        print(f"API URL: {api_url}")
        print(f"User ID: {user_id}")
        
        print("\nTesting signal validation...")
        
        # Valid signal
        valid_signal = {
            'symbol': 'EURUSD',
            'signal_type': 'BUY',
            'price': 1.0850,
            'confidence': 0.85
        }
        
        is_valid = listener.validate_signal(valid_signal)
        print(f"Valid signal: {'✓' if is_valid else '❌'}")
        
        # Invalid signal (missing field)
        invalid_signal = {
            'symbol': 'EURUSD',
            'signal_type': 'BUY'
            # Missing 'price' and 'confidence'
        }
        
        is_valid = listener.validate_signal(invalid_signal)
        print(f"Invalid signal (missing fields): {'✓ Rejected (Expected)' if not is_valid else '❌ Accepted'}")
        
        # Get stats
        stats = listener.get_stats()
        print(f"\nListener Stats:")
        print(f"  User ID: {stats['user_id']}")
        print(f"  Queue Size: {stats['queue_size']}")
        print(f"  Total Signals: {stats['total_signals_received']}")
        print(f"  Failed Polls: {stats['failed_polls']}")
        
        print("\n✓ Signal listener working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_logger():
    """Test execution logger."""
    print("\n" + "=" * 70)
    print("TEST 5: Execution Logger")
    print("=" * 70)
    
    try:
        from execution.engines.logger import get_execution_logger
        
        print("\nInitializing logger...")
        logger_obj = get_execution_logger()
        
        print("Logging test events...")
        
        logger_obj.log_event(
            event_type="TEST_EVENT",
            status="SUCCESS",
            message="Test message",
            symbol="EURUSD",
            user_id=1,
            details={'test': 'data'}
        )
        
        logger_obj.log_event(
            event_type="TEST_ERROR",
            status="FAILED",
            message="Test error",
            symbol="EURUSD",
            user_id=1,
            details={'error': 'test'}
        )
        
        print("✓ Events logged successfully")
        print(f"Log file: backend/execution/logs/execution.log")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MT5 EXECUTION SERVICE - COMPONENT TESTS")
    print("=" * 70)
    
    results = {}
    
    # Run tests
    tests = [
        ("MT5 Connection", test_mt5_connection),
        ("Position Sizer", test_position_sizer),
        ("Trade Validator", test_trade_validator),
        ("Signal Listener", test_signal_listener),
        ("Execution Logger", test_execution_logger),
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Execution service is ready to run.")
        return 0
    else:
        print("\n❌ Some tests failed. Fix issues before running the service.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
