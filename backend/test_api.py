#!/usr/bin/env python3
"""Test API to see if new signal fields are present"""

import requests
import json
import time

# Give server time to fully start
time.sleep(1)

try:
    print("Testing API endpoint...")
    response = requests.post(
        'http://127.0.0.1:5000/api/analyze',
        json={'symbol': 'EURUSD', 'notify': False},
        timeout=5
    )
    
    print(f"Status code: {response.status_code}")
    data = response.json()
    
    signal = data.get('signal', {})
    
    print(f"\nTotal keys in signal: {len(signal)}")
    print("\nKeys present:")
    for key in sorted(signal.keys()):
        print(f"  • {key}")
    
    print("\n=== Critical Check ===")
    has_ai = 'ai_prediction' in signal
    has_filter = 'filter_results' in signal
    has_quality = 'signal_quality' in signal
    
    print(f"ai_prediction present: {has_ai}")
    print(f"filter_results present: {has_filter}")
    print(f"signal_quality present: {has_quality}")
    
    if not has_ai or not has_filter:
        print("\n❌ ISSUE CONFIRMED: New fields are MISSING from API response")
        print("\nFull response:")
        print(json.dumps(signal, indent=2))
    else:
        print("\n✅ SUCCESS: All new fields are present!")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
