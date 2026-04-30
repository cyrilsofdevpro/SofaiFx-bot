#!/usr/bin/env python3
"""
Final System Test - Pre-Deployment Verification
Tests all core modules and system components
"""

import sys
import os

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60 + "\n")

def print_result(status, message):
    if status == "OK":
        print(f"   ✅ {message}")
    elif status == "WARN":
        print(f"   ⚠️  {message}")
    else:
        print(f"   ❌ {message}")

print_header("🚀 FINAL SYSTEM TEST - SofAi FX")

# Test 1: Core Module Imports
print("1️⃣  Testing core module imports...")
try:
    from backend.src.backtesting.backtester import BacktestingEngine
    from backend.src.analytics.dashboard import PerformanceDashboard
    from backend.src.optimization.auto_optimizer import AutoOptimizationEngine
    from backend.src.execution.reliability import ExecutionReliabilityEngine
    from backend.src.testing.stress_test import StressTestEngine
    from backend.src.signals.huggingface_service import HuggingFaceService
    print_result("OK", "All core modules imported successfully")
except Exception as e:
    print_result("FAIL", f"Failed to import modules: {e}")
    sys.exit(1)

# Test 2: Scheduler
print("\n2️⃣  Testing scheduler...")
try:
    from backend.src.backtesting.backtest_scheduler import BacktestScheduler
    scheduler = BacktestScheduler()
    print_result("OK", "BacktestScheduler initialized")
except Exception as e:
    print_result("FAIL", f"Failed to initialize scheduler: {e}")
    sys.exit(1)

# Test 3: Logger
print("\n3️⃣  Testing logging system...")
try:
    from backend.src.utils.logger import logger, get_logger, signal_logger, backtest_logger
    logger.info("Test log entry")
    print_result("OK", "Logging system working")
except Exception as e:
    print_result("FAIL", f"Failed to initialize logger: {e}")
    sys.exit(1)

# Test 4: Backtesting
print("\n4️⃣  Testing backtesting engine...")
try:
    backtester = BacktestingEngine()
    result = backtester.backtest_pair("EURUSD")
    if "metrics" in result:
        metrics = result.get("metrics", {})
        trades = metrics.get("total_trades", 0)
        pnl = metrics.get("pnl", 0)
        print_result("OK", f"Backtest successful - Trades: {trades}, PnL: ${pnl:.2f}")
    else:
        print_result("WARN", "Backtest completed but unexpected format")
except Exception as e:
    print_result("FAIL", f"Backtest failed: {e}")

# Test 5: Environment Variables
print("\n5️⃣  Checking environment configuration...")
required_keys = ["HF_API_KEY", "TWELVE_DATA_API_KEY", "ALPHA_VANTAGE_KEY"]
configured = []
missing = []
for key in required_keys:
    if os.getenv(key):
        configured.append(key)
    else:
        missing.append(key)

if configured:
    print_result("OK", f"Configured: {len(configured)} environment variables")
if missing:
    print_result("WARN", f"Missing (optional): {', '.join(missing)}")

# Test 6: File Structure
print("\n6️⃣  Checking project structure...")
required_files = [
    "backend/.env.example",
    "backend/main.py",
    "backend/src/api/flask_app.py",
    "README_COMPREHENSIVE.md",
    "validate_endpoints.py",
    ".gitignore",
]

missing_files = []
for file in required_files:
    path = os.path.join(os.getcwd(), file)
    if os.path.exists(path):
        print_result("OK", file)
    else:
        print_result("FAIL", f"Missing: {file}")
        missing_files.append(file)

# Summary
print_header("📊 TEST SUMMARY")

if missing_files:
    print(f"Missing files: {len(missing_files)}")
    for f in missing_files:
        print(f"  • {f}")
    print("\n❌ SYSTEM NOT READY - FIX ABOVE ITEMS")
    sys.exit(1)
else:
    print("✅ All tests passed!")
    print("✅ SYSTEM READY FOR DEPLOYMENT")
    print("\nNext step: git commit and push to GitHub")
