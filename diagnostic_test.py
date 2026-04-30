#!/usr/bin/env python
"""Quick diagnostic test for Phase 5 modules"""
import sys
import json
from datetime import datetime, timedelta

print("\n=== QUICK MODULE DIAGNOSTIC ===\n")

# Test 1: Backtesting
try:
    from backend.src.backtesting.backtester import BacktestingEngine
    bt = BacktestingEngine()
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    results = bt.backtest_pair('EURUSD', start_date, end_date, 10000)
    print(f"✓ Backtesting: {results.keys()}")
    print(f"  - Result has 'total_trades': {'total_trades' in results}")
    print(f"  - Result has 'sharpe_ratio': {'sharpe_ratio' in results}")
    if 'sharpe_ratio' not in results:
        print(f"  - Available keys: {list(results.keys())}")
except Exception as e:
    print(f"✗ Backtesting Error: {e}")

# Test 2: Stress Test
try:
    from backend.src.testing.stress_test import StressTestEngine
    st = StressTestEngine()
    config = {'name': 'Quick', 'num_users': 3, 'requests_per_user': 2, 'duration_seconds': 10, 'test_type': 'concurrent'}
    results = st.run_stress_test(config)
    print(f"\n✓ Stress Test: {results.keys()}")
    print(f"  - Result has 'total_requests': {'total_requests' in results}")
    print(f"  - Result has 'response_times': {'response_times' in results}")
    if 'total_requests' not in results and 'requests_completed' in results:
        print(f"  - Note: Found 'requests_completed' instead of 'total_requests'")
except Exception as e:
    print(f"✗ Stress Test Error: {e}")

# Test 3: Execution
try:
    from backend.src.execution.reliability import ExecutionReliabilityEngine
    ex = ExecutionReliabilityEngine()
    trade_params = {
        'pair': 'EURUSD',
        'signal': 'BUY',
        'entry_price': 1.0850,
        'stop_loss': 1.0820,
        'take_profit': 1.0900,
        'volume': 0.1
    }
    result = ex.execute_trade(trade_params)
    print(f"\n✓ Execution: {result.keys()}")
    print(f"  - Result has 'trade_id': {'trade_id' in result}")
    print(f"  - Result has 'order_status': {'order_status' in result}")
    if 'trade_id' not in result:
        print(f"  - Available keys: {list(result.keys())}")
except Exception as e:
    print(f"✗ Execution Error: {e}")

print("\n=== END DIAGNOSTIC ===\n")
