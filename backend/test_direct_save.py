#!/usr/bin/env python3
"""
Direct database test: Can we save signals directly?
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, Signal, User
from datetime import datetime

print("Testing direct signal save to database...\n")

with app.app_context():
    # Check if user 1 exists
    user = User.query.filter_by(id=1).first()
    if not user:
        print("❌ User 1 not found")
        exit(1)
    
    print(f"✅ Found user: {user.email}")
    
    # Try to create and save a signal
    try:
        print("\nCreating test signal...")
        
        test_signal = Signal(
            user_id=1,
            symbol='EURGBP',
            signal_type='SELL',
            price=0.8500,
            confidence=0.95,
            reason='Test signal from direct DB save',
            rsi_signal=None,
            ma_signal=None,
            sr_signal=None,
            ai_prediction={},
            filter_results={}
        )
        
        print(f"Signal created: {test_signal}")
        print(f"  Symbol: {test_signal.symbol}")
        print(f"  Type: {test_signal.signal_type}")
        print(f"  User ID: {test_signal.user_id}")
        
        print("\nAdding to session...")
        db.session.add(test_signal)
        
        print("Committing...")
        db.session.commit()
        
        print(f"✅ Signal saved! ID: {test_signal.id}")
        
        # Verify it was saved
        print("\nVerifying save...")
        saved = Signal.query.filter_by(id=test_signal.id).first()
        if saved:
            print(f"✅ Signal found in database!")
            print(f"  {saved.symbol} {saved.signal_type} by User {saved.user_id}")
        else:
            print("❌ Signal not found after commit!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

# Check total signals
with app.app_context():
    total = Signal.query.count()
    print(f"\n📊 Total signals in database: {total}")
