#!/usr/bin/env python3
"""
Test script to simulate the signal flow
Run this from the backend directory: python test_signal_flow.py
"""

import sys
import os
import json

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import db, Signal, User, init_db
from src.api.flask_app import app
from src.utils.logger import logger

def test_signal_flow():
    """Test the complete signal flow"""
    print("\n" + "="*60)
    print("🧪 SIGNAL FLOW TEST")
    print("="*60)
    
    with app.app_context():
        # Step 1: Check database file
        print("\n[STEP 1] Check Database File")
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_exists = os.path.exists(db_path)
        print(f"  Database path: {db_path}")
        print(f"  Database exists: {db_exists}")
        if not db_exists:
            print("  ⚠️ Database file will be created on first signal save")
        
        # Step 2: Check users
        print("\n[STEP 2] Check Users")
        users = User.query.all()
        print(f"  Total users: {len(users)}")
        if len(users) == 0:
            print("  ⚠️ No users found - creating test user...")
            test_user = User(name='Test User', email='test@example.com', plan='free')
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            print(f"  ✅ Created test user: ID={test_user.id}")
            user_id = test_user.id
        else:
            user_id = users[0].id
            print(f"  Using existing user: ID={user_id}, Email={users[0].email}")
        
        # Step 3: Create test signal
        print("\n[STEP 3] Create Test Signal")
        print(f"  Creating signal for user_id={user_id}...")
        test_signal = Signal(
            user_id=user_id,
            symbol='EURUSD',
            signal_type='BUY',
            price=1.0950,
            confidence=0.75,
            reason='Test signal - strategies aligned',
            rsi_signal={'signal': 'BUY', 'value': 35},
            ma_signal={'signal': 'BUY', 'value': 1.0940},
            sr_signal={'signal': 'SELL', 'value': 1.0960},
            ai_prediction={'confidence': 0.70, 'direction': 'BUY'},
            filter_results={'is_trade_allowed': True}
        )
        db.session.add(test_signal)
        db.session.commit()
        print(f"  ✅ Signal saved with ID: {test_signal.id}")
        
        # Step 4: Retrieve signals
        print("\n[STEP 4] Retrieve Signals")
        print(f"  Querying signals for user_id={user_id}...")
        retrieved_signals = Signal.query.filter_by(user_id=user_id).all()
        print(f"  ✅ Retrieved {len(retrieved_signals)} signal(s)")
        for sig in retrieved_signals:
            print(f"    - {sig.symbol} {sig.signal_type} @ {sig.created_at}")
        
        # Step 5: Check total database state
        print("\n[STEP 5] Database State Summary")
        total_users = User.query.count()
        total_signals = Signal.query.count()
        print(f"  Total users in database: {total_users}")
        print(f"  Total signals in database: {total_signals}")
        
        # Group signals by user
        signals_by_user = {}
        for sig in Signal.query.all():
            if sig.user_id not in signals_by_user:
                signals_by_user[sig.user_id] = 0
            signals_by_user[sig.user_id] += 1
        
        for uid, count in signals_by_user.items():
            print(f"    User {uid}: {count} signal(s)")
        
        print("\n" + "="*60)
        print("✅ Signal flow test complete!")
        print("="*60 + "\n")

if __name__ == '__main__':
    try:
        test_signal_flow()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
