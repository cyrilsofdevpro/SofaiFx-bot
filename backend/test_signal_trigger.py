#!/usr/bin/env python
"""Test script to generate a signal and watch execution service process it"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000'

print("=" * 70)
print("TEST: Generate EURUSD Signal and Watch Execution")
print("=" * 70)

# Step 1: Login
print("\n[1/3] Logging in...")
login_resp = requests.post(
    f'{BASE_URL}/auth/login',
    json={'email': 'testuser@example.com', 'password': 'password123'},
    timeout=10
)

if login_resp.status_code != 200:
    print(f"ERROR: Login failed - {login_resp.json()}")
    exit(1)

token = login_resp.json()['access_token']
print(f"✓ Logged in successfully")

# Step 2: Generate signal
print("\n[2/3] Generating EURUSD signal...")
signal_resp = requests.post(
    f'{BASE_URL}/api/analyze',
    json={'symbol': 'EURUSD', 'notify': True},
    headers={'Authorization': f'Bearer {token}'},
    timeout=45
)

if signal_resp.status_code != 200:
    print(f"ERROR: Signal generation failed - {signal_resp.json()}")
    exit(1)

signal_data = signal_resp.json()
print(f"✓ Signal generated!")
print(f"  Type: {signal_data['signal']['signal_type']}")
print(f"  Price: {signal_data['signal']['price']}")
print(f"  Confidence: {signal_data['signal']['confidence']:.2%}")

# Step 3: Wait for execution
print("\n[3/3] Waiting for execution service to process signal...")
print("(The execution service polls every 30 seconds)")
print("Waiting 35 seconds...", end="", flush=True)
for i in range(35):
    print(".", end="", flush=True)
    time.sleep(1)
print("\n✓ Done waiting")

# Step 4: Check if signal was processed
print("\nChecking signals in database...")
signals_resp = requests.get(
    f'{BASE_URL}/api/signals',
    headers={'Authorization': f'Bearer {token}'},
    timeout=10
)

if signals_resp.status_code == 200:
    signals = signals_resp.json()['signals']
    print(f"✓ Found {len(signals)} signal(s) in database")
    if signals:
        sig = signals[0]
        print(f"  Latest: {sig['signal_type']} @ {sig['price']} (confidence: {sig['confidence']:.2%})")
else:
    print(f"ERROR: Could not fetch signals - {signals_resp.json()}")

print("\n" + "=" * 70)
print("Signal generation test completed!")
print("Check the execution service terminal for trade execution logs")
print("=" * 70)
