#!/usr/bin/env python3
"""
Minimal database test - directly tests SQLite without Flask complexity
Run this: python test_db_minimal.py
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*70)
print("🧪 MINIMAL DATABASE TEST")
print("="*70)

# Get database path
from src.api.flask_app import app

with app.app_context():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    # Extract path from sqlite:///...
    db_path = db_uri.replace('sqlite:///', '')
    
    print(f"\n[1] DATABASE PATH")
    print(f"  URI: {db_uri}")
    print(f"  Path: {db_path}")
    print(f"  Exists: {os.path.exists(db_path)}")
    
    # Import models AFTER getting the path
    from src.models import db, Signal, User, init_db
    
    print(f"\n[2] INITIALIZE DATABASE")
    try:
        # This should create tables if they don't exist
        init_db(app)
        print(f"  ✅ Database initialized")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        sys.exit(1)
    
    print(f"\n[3] CHECK TABLES EXIST")
    try:
        # Try a simple query
        user_count = User.query.count()
        signal_count = Signal.query.count()
        print(f"  ✅ Users table works: {user_count} users")
        print(f"  ✅ Signals table works: {signal_count} signals")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        sys.exit(1)
    
    print(f"\n[4] TEST: CREATE SIGNAL FOR USER 3")
    try:
        # Create a test signal for user 3
        test_signal = Signal(
            user_id=3,
            symbol='TEST',
            signal_type='BUY',
            price=1.0,
            confidence=0.5,
            reason='Test',
            rsi_signal=None,
            ma_signal=None,
            sr_signal=None,
            ai_prediction={},
            filter_results={}
        )
        db.session.add(test_signal)
        db.session.commit()
        print(f"  ✅ Signal created with ID: {test_signal.id}")
        
    except Exception as e:
        db.session.rollback()
        print(f"  ❌ Error creating signal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\n[5] TEST: RETRIEVE SIGNAL FOR USER 3")
    try:
        retrieved = Signal.query.filter_by(user_id=3).all()
        print(f"  ✅ Retrieved {len(retrieved)} signal(s) for user 3")
        
        if len(retrieved) > 0:
            for sig in retrieved:
                print(f"    - {sig.symbol} {sig.signal_type} (ID: {sig.id})")
        
    except Exception as e:
        print(f"  ❌ Error retrieving signals: {e}")
        sys.exit(1)
    
    print(f"\n[6] CHECK DATABASE FILE SIZE")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"  ✅ Database file size: {size} bytes ({size/1024:.2f} KB)")
    else:
        print(f"  ⚠️  Database file doesn't exist!")
    
    print(f"\n[7] VERIFICATION")
    all_signals = Signal.query.count()
    print(f"  Total signals in database: {all_signals}")
    
    if all_signals == 0:
        print(f"  ⚠️  Database is EMPTY - no signals are being saved!")
    else:
        print(f"  ✅ Database is working - signals are being saved!")

print("\n" + "="*70)
print("✅ Test complete\n")
