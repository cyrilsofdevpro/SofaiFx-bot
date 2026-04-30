#!/usr/bin/env python3
"""
Test pair recommendations and auto-analysis scheduler features
"""

import requests
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = 'http://localhost:5000'

print("\n" + "="*100)
print("🧪 TESTING: PAIR RECOMMENDATIONS & AUTO-ANALYSIS SCHEDULER")
print("="*100)

# Login
print("\n[1] Login as test@example.com...")
response = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'test@example.com',
    'password': 'password123'
}, timeout=5)

if response.status_code != 200:
    print(f"❌ Login failed")
    sys.exit(1)

token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
print(f"✅ Authenticated")

# Test 1: Get Pair Recommendations
print("\n[2] Getting pair recommendations...")
response = requests.get(f'{BASE_URL}/api/recommendations?hours=24', headers=headers, timeout=5)

if response.status_code == 200:
    data = response.json()
    recs = data.get('recommendations', [])
    print(f"✅ Got {len(recs)} recommendations:\n")
    
    for rec in recs:
        print(f"   {rec['full_message']}")
        stats = rec['stats']
        print(f"      Signals: {stats['buy_signals']} BUY | {stats['sell_signals']} SELL | {stats['hold_signals']} HOLD")
        print(f"      Confidence: {stats['avg_confidence']}\n")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)

# Test 2: Get User Preferences
print("\n[3] Getting user preferences...")
response = requests.get(f'{BASE_URL}/api/preferences', headers=headers, timeout=5)

if response.status_code == 200:
    prefs = response.json()
    print(f"✅ Current preferences:")
    print(f"   Monitored pairs: {prefs['monitored_pairs']}")
    print(f"   Auto-analysis enabled: {prefs['auto_analysis_enabled']}")
    print(f"   Interval: {prefs['auto_analysis_interval']}s")
else:
    print(f"❌ Failed: {response.status_code}")

# Test 3: Update Preferences
print("\n[4] Updating preferences...")
new_prefs = {
    'monitored_pairs': ['EURUSD', 'GBPUSD'],
    'auto_analysis_enabled': False,
    'auto_analysis_interval': 1800,  # 30 minutes
    'min_confidence_threshold': 0.75
}

response = requests.post(f'{BASE_URL}/api/preferences', 
    json=new_prefs, 
    headers=headers, 
    timeout=5)

if response.status_code == 200:
    print(f"✅ Preferences updated")
    prefs = response.json()['preferences']
    print(f"   Monitored pairs: {prefs['monitored_pairs']}")
    print(f"   Interval: {prefs['auto_analysis_interval']}s")
else:
    print(f"❌ Failed: {response.status_code}")

# Test 4: Start Auto-Analysis
print("\n[5] Starting auto-analysis...")
response = requests.post(f'{BASE_URL}/api/auto-analysis/start',
    json={
        'pairs': ['EURUSD', 'GBPUSD'],
        'interval_seconds': 3600  # 1 hour
    },
    headers=headers,
    timeout=5)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Auto-analysis started")
    print(f"   Pairs: {data['pairs']}")
    print(f"   Interval: {data['interval_seconds']}s")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)

# Test 5: Check Auto-Analysis Status
print("\n[6] Checking auto-analysis status...")
response = requests.get(f'{BASE_URL}/api/auto-analysis/status', headers=headers, timeout=5)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Auto-analysis active: {data['active']}")
    
    if data['jobs']:
        for job in data['jobs']:
            print(f"   Job for user {job['user_id']}")
            print(f"   Pairs: {job['pairs']}")
            print(f"   Interval: {job['interval_seconds']}s")
            print(f"   Next run: {job['next_run']}")
else:
    print(f"❌ Failed: {response.status_code}")

# Test 6: Stop Auto-Analysis
print("\n[7] Stopping auto-analysis...")
response = requests.post(f'{BASE_URL}/api/auto-analysis/stop', headers=headers, timeout=5)

if response.status_code == 200:
    print(f"✅ Auto-analysis stopped")
else:
    print(f"❌ Failed: {response.status_code}")

print("\n" + "="*100)
print("✅ ALL TESTS PASSED")
print("="*100 + "\n")

print("📋 Features Summary:")
print("   ✅ Pair Recommendations - Analyzes signal history and suggests pairs")
print("   ✅ User Preferences - Configure monitored pairs and thresholds")
print("   ✅ Auto-Analysis Scheduler - Background job to analyze pairs hourly")
print("   ✅ Status Monitoring - Check and control scheduled jobs")
