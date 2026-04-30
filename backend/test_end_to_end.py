#!/usr/bin/env python3
"""
Complete test: User searches (analyzes) signals → They're saved and displayed
"""

import sys
import os
import requests
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, Signal, User

API_URL = 'http://localhost:5000'

print("\n" + "="*80)
print("🧪 END-TO-END TEST: ANALYZE → SAVE → DISPLAY")
print("="*80)

# Get all users
with app.app_context():
    users = User.query.all()
    print(f"\n[USERS] Found {len(users)} users:")
    for u in users:
        print(f"  - ID: {u.id}, Name: {u.name}, Email: {u.email}")

print("\n" + "="*80)

# Test for each user
for user in users:
    print(f"\n[TEST USER {user.id}] {user.name} ({user.email})")
    print("-" * 80)
    
    # Step 1: Login
    print(f"  [1] Logging in...")
    response = requests.post(f'{API_URL}/auth/login', json={
        'email': user.email,
        'password': 'password123' if user.id == 1 else (
            'cyril123' if user.id == 2 else (
                'israel123' if user.id == 3 else 'bro123'
            )
        )
    })
    
    if response.status_code != 200:
        print(f"      ❌ Login failed: {response.json()}")
        continue
    
    token = response.json()['access_token']
    print(f"      ✅ Logged in")
    
    # Step 2: Analyze a pair
    print(f"  [2] Analyzing EURUSD...")
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    response = requests.post(
        f'{API_URL}/api/analyze',
        json={'symbol': 'EURUSD', 'notify': False},
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"      ❌ Analysis failed: {response.json()}")
        continue
    
    data = response.json()
    signal_type = data.get('signal', {}).get('signal', 'NONE')
    saved = data.get('saved_to_db', False)
    
    print(f"      ✅ Analysis complete")
    print(f"         Signal: {signal_type}")
    print(f"         Saved to DB: {saved}")
    
    # Small delay to ensure database is written
    time.sleep(0.5)
    
    # Step 3: Check database directly
    print(f"  [3] Checking database...")
    with app.app_context():
        user_signals = Signal.query.filter_by(user_id=user.id, symbol='EURUSD').all()
        print(f"      ✅ Found {len(user_signals)} EURUSD signal(s) for user {user.id}")
    
    # Step 4: Test API retrieval
    print(f"  [4] Testing API retrieval...")
    response = requests.get(f'{API_URL}/api/signals?limit=50', headers=headers)
    
    if response.status_code != 200:
        print(f"      ❌ API call failed: {response.json()}")
        continue
    
    data = response.json()
    total = data.get('total', 0)
    print(f"      ✅ API returned {total} signal(s)")
    
    for sig in data.get('signals', [])[:3]:  # Show first 3
        print(f"         - {sig['symbol']} {sig['signal']} (Confidence: {sig['confidence']:.2%})")

print("\n" + "="*80)
print("✅ END-TO-END TEST COMPLETE")
print("="*80 + "\n")
