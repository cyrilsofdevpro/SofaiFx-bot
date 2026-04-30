#!/usr/bin/env python3
"""
Comprehensive test: Verify signal history works for multiple users
"""

import sys
import os
import requests
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, User, Signal

BASE_URL = 'http://localhost:5000'

# Test users
USERS = [
    {'email': 'user1@gmail.com', 'password': 'user1123', 'pairs': ['EURUSD', 'GBPUSD']},
    {'email': 'israel@gmail.com', 'password': 'israel123', 'pairs': ['EURUSD', 'USDJPY']},
    {'email': 'user3@gmail.com', 'password': 'user3123', 'pairs': ['EURUSD']},
    {'email': 'bro@gmail.com', 'password': 'bro123', 'pairs': ['EURUSD', 'GBPUSD', 'USDJPY']},
]

print("\n" + "="*80)
print("🔍 COMPREHENSIVE SIGNAL HISTORY TEST - MULTIPLE USERS")
print("="*80)

# Get initial database state
print("\n[INITIAL STATE]")
with app.app_context():
    total_signals = Signal.query.count()
    total_users = User.query.count()
    print(f"Database: {total_users} users, {total_signals} signals")

# Test each user
for idx, user_info in enumerate(USERS, 1):
    print(f"\n{'='*80}")
    print(f"USER {idx}: {user_info['email']}")
    print(f"{'='*80}")
    
    email = user_info['email']
    password = user_info['password']
    pairs = user_info['pairs']
    
    # Step 1: Login
    print(f"\n[Step 1] Login as {email}")
    try:
        response = requests.post(f'{BASE_URL}/auth/login', json={
            'email': email,
            'password': password
        }, timeout=5)
        
        if response.status_code != 200:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   {response.text}")
            continue
        
        token = response.json()['access_token']
        print(f"   ✅ Login successful")
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        continue
    
    # Step 2: Analyze pairs
    print(f"\n[Step 2] Analyze {len(pairs)} pairs")
    analyzed_count = 0
    
    for pair in pairs:
        try:
            response = requests.post(f'{BASE_URL}/api/analyze', 
                json={'symbol': pair, 'notify': False}, 
                headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                signal_type = result.get('signal', {}).get('signal', 'N/A')
                saved = result.get('saved_to_db', False)
                
                status = "✅" if signal_type != 'N/A' else "⏸️ "
                print(f"   {status} {pair}: {signal_type} (saved={saved})")
                analyzed_count += 1
            else:
                print(f"   ⚠️  {pair}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {pair}: {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    print(f"   → Analyzed: {analyzed_count}/{len(pairs)} pairs")
    
    # Step 3: Retrieve signals via API
    print(f"\n[Step 3] Retrieve signal history via API")
    try:
        response = requests.get(f'{BASE_URL}/api/signals', headers=headers, timeout=5)
        
        if response.status_code == 200:
            signals = response.json()
            print(f"   ✅ Retrieved {len(signals)} signals")
            
            if signals:
                print(f"\n   Signal History:")
                for sig in signals:
                    created = sig.get('created_at', 'N/A')
                    symbol = sig.get('symbol', 'N/A')
                    signal_type = sig.get('signal_type', 'N/A')
                    confidence = sig.get('confidence', 'N/A')
                    print(f"      • {symbol} {signal_type} (Confidence: {confidence}, Created: {created})")
            else:
                print(f"   ℹ️  No signals yet (user hasn't analyzed any pairs)")
        else:
            print(f"   ❌ Failed to retrieve signals: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 4: Check database directly
    print(f"\n[Step 4] Verify signals in database")
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            signals = Signal.query.filter_by(user_id=user.id).all()
            print(f"   ✅ Database shows {len(signals)} signals for this user")
            if signals:
                for sig in signals:
                    print(f"      • {sig.symbol} {sig.signal_type}")
        else:
            print(f"   ❌ User not found in database")

# Final summary
print(f"\n{'='*80}")
print("FINAL SUMMARY")
print(f"{'='*80}")

with app.app_context():
    total_signals = Signal.query.count()
    total_users = User.query.count()
    
    print(f"\nDatabase Summary:")
    print(f"  Total users: {total_users}")
    print(f"  Total signals: {total_signals}")
    
    print(f"\nSignals per user:")
    for user in User.query.all():
        count = Signal.query.filter_by(user_id=user.id).count()
        print(f"  {user.email}: {count} signals")

print(f"\n✅ TEST COMPLETED")
print(f"{'='*80}\n")
