#!/usr/bin/env python
"""Test the Flask API health endpoint"""

import requests
import json

try:
    response = requests.get('http://localhost:5000/health', timeout=5)
    print("API Health Check:")
    print(json.dumps(response.json(), indent=2))
    print(f"\nStatus Code: {response.status_code}")
    if response.status_code == 200:
        print("API is HEALTHY and responding!")
except Exception as e:
    print(f"ERROR: Could not connect to API: {e}")
