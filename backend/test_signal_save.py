#!/usr/bin/env python3
"""
Test signal saving directly to find the error
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import db, Signal, User, init_db
from src.api.flask_app import app

print("\n" + "="*80)
print("🧪 TESTING SIGNAL SAVING FOR USER 3")
print("="*80)

with app.app_context():
    try:
        # Try to create and save a signal
        print("\n[TEST] Creating Signal object...")
        new_signal = Signal(
            user_id=3,
            symbol='EURUSD',
            signal_type='BUY',
            price=1.08500,
            confidence=0.85,
            reason='Test signal',
            rsi_signal=None,
            ma_signal=None,
            sr_signal=None,
            ai_prediction={},
            filter_results={}
        )
        
        print("✅ Signal object created")
        print(f"   - User ID: {new_signal.user_id}")
        print(f"   - Symbol: {new_signal.symbol}")
        print(f"   - Type: {new_signal.signal_type}")
        
        print("\n[TEST] Adding to session...")
        db.session.add(new_signal)
        print("✅ Added to session")
        
        print("\n[TEST] Flushing to get ID...")
        db.session.flush()
        signal_id = new_signal.id
        print(f"✅ Signal ID: {signal_id}")
        
        print("\n[TEST] Committing to database...")
        db.session.commit()
        print("✅ Committed successfully!")
        
        # Verify it was saved
        print("\n[VERIFY] Checking if signal was saved...")
        retrieved = Signal.query.filter_by(id=signal_id).first()
        if retrieved:
            print(f"✅ SIGNAL FOUND IN DATABASE!")
            print(f"   - ID: {retrieved.id}")
            print(f"   - User ID: {retrieved.user_id}")
            print(f"   - Symbol: {retrieved.symbol}")
            print(f"   - Type: {retrieved.signal_type}")
        else:
            print(f"❌ Signal not found after commit!")
            
    except Exception as e:
        print(f"\n❌ ERROR DURING SAVE: {e}")
        print(f"\nFull error details:")
        import traceback
        traceback.print_exc()
        
        print("\n[INFO] Attempting rollback...")
        try:
            db.session.rollback()
            print("✅ Rollback successful")
        except:
            print("❌ Rollback failed")

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80 + "\n")
