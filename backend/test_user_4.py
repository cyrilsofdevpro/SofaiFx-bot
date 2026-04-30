#!/usr/bin/env python3
"""
Test if backend is running and user 4 can analyze
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.flask_app import app
from src.models import db, Signal

print("\n" + "="*70)
print("Testing User 4 (bro) - Signal Analyze")
print("="*70)

# Test login
print("\n[1] Testing login...")
try:
    response = requests.post('http://localhost:5000/auth/login', json={
        'email': 'bro@gmail.com',
        'password': 'bro123'
    }, timeout=5)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    token = response.json()['access_token']
    print(f"✅ Logged in successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test analyze
print("\n[2] Testing analyze endpoint...")
try:
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    response = requests.post('http://localhost:5000/api/analyze', 
        json={'symbol': 'EURUSD', 'notify': False}, 
        headers=headers, timeout=30)
    
    print(f"   Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        signal = result.get('signal')
        if signal:
            print(f"✅ Signal generated: {signal.get('signal')}")
        else:
            print(f"⚠️  No signal generated (strategies didn't agree)")
        
        print(f"   Saved to DB: {result.get('saved_to_db')}")
    else:
        print(f"❌ Analysis failed: {result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Check database
print("\n[3] Checking database...")
with app.app_context():
    signals = Signal.query.filter_by(user_id=4).all()
    print(f"✅ Signals for user 4: {len(signals)}")
    for sig in signals:
        print(f"   - {sig.symbol} {sig.signal_type}")

print("\n" + "="*70)
