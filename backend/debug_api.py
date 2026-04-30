#!/usr/bin/env python3
"""
Debug test: Check what API actually returns
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

# Login as israel
print("Logging in as israel@gmail.com...")
response = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'israel@gmail.com',
    'password': 'israel123'
}, timeout=5)

if response.status_code != 200:
    print(f"Login failed: {response.status_code}")
    print(response.text)
    exit(1)

token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("✅ Logged in\n")

# Get signals
print("Fetching signals from API...")
response = requests.get(f'{BASE_URL}/api/signals', headers=headers, timeout=5)

print(f"Status: {response.status_code}")
print(f"Response:")
print(json.dumps(response.json(), indent=2))
