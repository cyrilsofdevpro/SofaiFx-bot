#!/usr/bin/env python3
"""
Quick test to verify signals are saving correctly
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, Signal

print("\n" + "="*80)
print("🧪 FINAL TEST - SIGNAL SAVE FOR USER 3")
print("="*80)

# Step 1: Login
print("\n[1] Logging in as Israel...")
response = requests.post('https://sofaifx-bot-v2.onrender.com/auth/login', json={
    'email': 'israel@gmail.com',
    'password': 'israel123'
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    sys.exit(1)

token = response.json()['access_token']
print(f"✅ Token: {token[:40]}...")

# Step 2: Analyze GBPUSD
print("\n[2] Analyzing GBPUSD...")
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
response = requests.post('https://sofaifx-bot-v2.onrender.com/api/analyze', 
    json={'symbol': 'GBPUSD', 'notify': False}, 
    headers=headers)

data = response.json()
signal_type = data.get('signal', {}).get('signal') if data.get('signal') else 'NONE'
saved = data.get('saved_to_db')

print(f"✅ Analysis complete")
print(f"   Signal: {signal_type}")
print(f"   Saved to DB: {saved}")

# Step 3: Verify in database
print("\n[3] Checking database...")
with app.app_context():
    signals = Signal.query.filter_by(user_id=3).all()
    print(f"✅ Total signals for User 3: {len(signals)}")
    for sig in signals:
        print(f"   - {sig.symbol} {sig.signal_type} (ID: {sig.id}, Created: {sig.created_at})")

# Step 4: Test API retrieval
print("\n[4] Testing API retrieval...")
response = requests.get('http://localhost:5000/api/signals?limit=50', headers=headers)
data = response.json()
print(f"✅ API returned: {data['total']} signal(s)")
for sig in data.get('signals', []):
    print(f"   - {sig['symbol']} {sig['signal']}")

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80 + "\n")
