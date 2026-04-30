#!/usr/bin/env python3
"""
Quick verification script - run this to get a complete system check
Run from backend directory: python verify_setup.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*70)
print("🔍 SOFAI FX - SYSTEM VERIFICATION")
print("="*70)

# Check 1: Flask app can be imported
print("\n[1/5] Checking Flask app...")
try:
    from src.api.flask_app import app, db, logger
    print("  ✅ Flask app imports successfully")
except Exception as e:
    print(f"  ❌ Flask import failed: {e}")
    sys.exit(1)

# Check 2: Database configuration
print("\n[2/5] Checking database configuration...")
try:
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"  Database URI: {db_uri}")
        db_path = db_uri.replace('sqlite:///', '').replace('sqlite:////', '')
        db_path = db_path.replace('/', '\\')  # Convert back for Windows display
        print(f"  Database path: {db_path}")
        
        # Check if database file exists
        db_file_exists = os.path.exists(db_path)
        if db_file_exists:
            size = os.path.getsize(db_path)
            print(f"  ✅ Database file exists ({size} bytes)")
        else:
            print(f"  ⚠️  Database file does NOT exist (will be created on first save)")
except Exception as e:
    print(f"  ❌ Database check failed: {e}")
    sys.exit(1)

# Check 3: Models and database tables
print("\n[3/5] Checking database models...")
try:
    from src.models import User, Signal, init_db
    with app.app_context():
        inspector = __import__('sqlalchemy').inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'users' in tables:
            print("  ✅ Users table exists")
        else:
            print("  ⚠️  Users table missing (will be created)")
        
        if 'signals' in tables:
            print("  ✅ Signals table exists")
        else:
            print("  ⚠️  Signals table missing (will be created)")
        
        # Count data
        user_count = User.query.count()
        signal_count = Signal.query.count()
        print(f"  Users in database: {user_count}")
        print(f"  Signals in database: {signal_count}")
        
except Exception as e:
    print(f"  ❌ Models check failed: {e}")
    sys.exit(1)

# Check 4: Signal generation
print("\n[4/5] Checking signal generation...")
try:
    from src.signals.signal_generator import SignalGenerator
    import pandas as pd
    import numpy as np
    
    gen = SignalGenerator()
    print("  ✅ SignalGenerator initialized")
    
    # Create dummy data
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    dummy_data = pd.DataFrame({
        'Open': np.random.uniform(1.08, 1.10, 100),
        'High': np.random.uniform(1.09, 1.11, 100),
        'Low': np.random.uniform(1.07, 1.09, 100),
        'Close': np.random.uniform(1.08, 1.10, 100),
        'Volume': np.random.uniform(1000, 5000, 100)
    }, index=dates)
    
    # Try to generate a signal
    signal = gen.generate_signal(dummy_data, 'EURUSD')
    if signal:
        print(f"  ✅ Signal generation works (returned: {signal.signal.value})")
    else:
        print(f"  ⚠️  Signal generation returned None (strategies didn't agree)")
        
except Exception as e:
    print(f"  ❌ Signal generation check failed: {e}")
    import traceback
    traceback.print_exc()

# Check 5: API endpoints
print("\n[5/5] Checking API endpoints...")
try:
    from src.api.flask_app import health, get_signals, analyze_pair
    print("  ✅ API endpoints imported successfully")
except Exception as e:
    print(f"  ❌ API endpoints failed: {e}")

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE")
print("="*70)
print("\n📋 Next Steps:")
print("  1. Check if database file exists: " + db_path)
print("  2. Run: python debug_database.py")
print("  3. Run: python test_signal_flow.py")
print("  4. Start Flask: python -m src.api.flask_app")
print("  5. Test analyzing a pair in dashboard")
print("\n" + "="*70 + "\n")
