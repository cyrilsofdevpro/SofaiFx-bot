#!/usr/bin/env python
import requests
import time

# Wait for API to start
print("⏳ Waiting for API to start...")
time.sleep(5)

try:
    print("📡 Testing /api/mt5/servers endpoint...")
    response = requests.get('http://localhost:5000/api/mt5/servers', timeout=5)
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ Connection refused - API not ready")
except Exception as e:
    print(f"❌ Error: {e}")
