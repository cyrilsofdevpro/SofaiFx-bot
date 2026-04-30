#!/usr/bin/env python3
"""
Test with known working user: test@example.com
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

# Try test@example.com
print("Testing login for test@example.com...")
response = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'test@example.com',
    'password': 'password123'
}, timeout=5)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Login successful")
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Get current signals
    print("\nGetting current signals...")
    response = requests.get(f'{BASE_URL}/api/signals', headers=headers, timeout=5)
    signals = response.json()['signals']
    print(f"Current signals: {len(signals)}")
    
    # Try analyzing EURCAD
    print("\nAnalyzing EURCAD...")
    response = requests.post(f'{BASE_URL}/api/analyze',
        json={'symbol': 'EURCAD', 'notify': False},
        headers=headers,
        timeout=30)
    
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Signal: {result.get('signal', {}).get('signal') if result.get('signal') else 'None'}")
    print(f"Saved to DB: {result.get('saved_to_db')}")
    
    # Check if appeared in signal list
    print("\nGetting updated signals...")
    response = requests.get(f'{BASE_URL}/api/signals', headers=headers, timeout=5)
    signals = response.json()['signals']
    print(f"Updated signals: {len(signals)}")
    
    if signals:
        print("\nLatest signal:")
        sig = signals[0]
        print(f"  {sig['symbol']} {sig['signal']} @ {sig['price']}")
else:
    print(f"❌ Login failed")
    print(response.text)
