#!/usr/bin/env python3
"""
Quick diagnostic for user_id=3 (Israel)
Run this: python check_user_3.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import db, Signal, User, init_db
from src.api.flask_app import app

print("\n" + "="*70)
print("🔍 CHECKING USER ID 3 (ISRAEL)")
print("="*70)

with app.app_context():
    # Check database file
    print("\n[DATABASE FILE]")
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    print(f"  URI: {db_uri}")
    print(f"  Path: {db_path}")
    print(f"  Exists: {os.path.exists(db_path)}")
    
    # Check user 3
    print("\n[USER ID 3]")
    user = User.query.get(3)
    if user:
        print(f"  ✅ Found: {user.name} ({user.email})")
        print(f"  ID: {user.id}")
        print(f"  Plan: {user.plan}")
    else:
        print(f"  ❌ User ID 3 not found!")
    
    # Check ALL signals
    print("\n[ALL SIGNALS IN DATABASE]")
    all_signals = Signal.query.all()
    print(f"  Total signals: {len(all_signals)}")
    
    if len(all_signals) == 0:
        print("  ⚠️  NO SIGNALS IN DATABASE AT ALL!")
        print("     This means signals are NOT being saved")
    else:
        for sig in all_signals:
            print(f"    - User {sig.user_id}: {sig.symbol} {sig.signal_type} @ {sig.created_at}")
    
    # Check signals for user 3
    print("\n[SIGNALS FOR USER 3]")
    user_3_signals = Signal.query.filter_by(user_id=3).all()
    print(f"  Count: {len(user_3_signals)}")
    
    if len(user_3_signals) == 0:
        print("  ⚠️  User 3 has NO signals!")
        
        # Debug: show signals grouped by user
        print("\n[SIGNALS BY USER]")
        signals_by_user = {}
        for sig in all_signals:
            if sig.user_id not in signals_by_user:
                signals_by_user[sig.user_id] = 0
            signals_by_user[sig.user_id] += 1
        
        for uid, count in sorted(signals_by_user.items()):
            print(f"    User {uid}: {count} signal(s)")
    else:
        for sig in user_3_signals:
            print(f"    - {sig.symbol} {sig.signal_type} (confidence: {sig.confidence:.2f})")

print("\n" + "="*70)
print("✅ Diagnostic complete\n")
