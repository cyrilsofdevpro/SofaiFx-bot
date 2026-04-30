#!/usr/bin/env python3
"""
Diagnose why signals aren't showing for User 3
"""

import sys
import os
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import db, Signal, User, init_db
from src.api.flask_app import app

API_URL = 'http://localhost:5000'
USER_EMAIL = 'israel@gmail.com'
USER_PASSWORD = 'israel123'

print("\n" + "="*80)
print("🔍 DIAGNOSING USER 3 SIGNAL ISSUE")
print("="*80)

# Step 1: Verify User 3 exists and get their ID
print("\n[STEP 1] Verify User 3 exists...")
with app.app_context():
    user_3 = User.query.filter_by(email=USER_EMAIL).first()
    if not user_3:
        print(f"❌ User not found with email {USER_EMAIL}")
        print("   Available users:")
        all_users = User.query.all()
        for u in all_users:
            print(f"      - ID: {u.id}, Name: {u.name}, Email: {u.email}")
        sys.exit(1)
    
    print(f"✅ Found user: ID={user_3.id}, Name={user_3.name}")

# Step 2: Login and get JWT token
print("\n[STEP 2] Login to get JWT token...")
try:
    response = requests.post(f'{API_URL}/auth/login', json={
        'email': USER_EMAIL,
        'password': USER_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   {response.text}")
        sys.exit(1)
    
    data = response.json()
    token = data['access_token']
    returned_user_id = data['user']['id']
    
    print(f"✅ Login successful")
    print(f"   Token: {token[:40]}...")
    print(f"   User ID from JWT: {returned_user_id}")
    
except Exception as e:
    print(f"❌ Login failed: {e}")
    sys.exit(1)

# Step 3: Test analyze endpoint
print("\n[STEP 3] Call /api/analyze endpoint...")
try:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(
        f'{API_URL}/api/analyze',
        json={'symbol': 'GBPUSD', 'notify': False},
        headers=headers,
        timeout=30
    )
    
    print(f"   Response status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        print(f"✅ Analyze succeeded")
        print(f"   Signal generated: {data.get('signal', {}).get('signal') if data.get('signal') else 'None'}")
        print(f"   Saved to DB: {data.get('saved_to_db')}")
    else:
        print(f"❌ Analyze failed")
        print(f"   Error: {data.get('error')}")
        
except Exception as e:
    print(f"❌ Analyze request failed: {e}")

# Step 4: Check database for signals
print(f"\n[STEP 4] Check database for signals...")
with app.app_context():
    # Query signals for User 3
    user_3_signals = Signal.query.filter_by(user_id=returned_user_id).all()
    
    print(f"   User {returned_user_id} signals in DB: {len(user_3_signals)}")
    
    if len(user_3_signals) > 0:
        print(f"   ✅ SIGNALS FOUND:")
        for sig in user_3_signals:
            print(f"      - {sig.symbol} {sig.signal_type} (ID: {sig.id}, Created: {sig.created_at})")
    else:
        print(f"   ❌ NO SIGNALS FOR THIS USER")
        
        # Show all signals
        all_signals = Signal.query.all()
        print(f"\n   Total signals in DB: {len(all_signals)}")
        for sig in all_signals:
            print(f"      - User {sig.user_id}: {sig.symbol} {sig.signal_type}")

# Step 5: Test signal retrieval API
print(f"\n[STEP 5] Test /api/signals endpoint...")
try:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(
        f'{API_URL}/api/signals?limit=50',
        headers=headers
    )
    
    print(f"   Response status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        total = data.get('total', 0)
        print(f"✅ API returned {total} signal(s)")
        
        if total > 0:
            for sig in data.get('signals', []):
                print(f"      - {sig.get('symbol')} {sig.get('signal')}")
        else:
            print(f"   ❌ API returned 0 signals")
    else:
        print(f"❌ API call failed")
        print(f"   {data}")
        
except Exception as e:
    print(f"❌ API request failed: {e}")

print("\n" + "="*80)
print("✅ DIAGNOSIS COMPLETE")
print("="*80 + "\n")
