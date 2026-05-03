#!/usr/bin/env python3
"""
Test deployed backend endpoints
"""
import urllib.request
import urllib.error
import json
import sys

def test_endpoint(url, method='GET', data=None, headers=None):
    """Test an endpoint and return status and response"""
    try:
        if headers is None:
            headers = {}

        if data and isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, body

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
        except:
            body = '<no body>'
        return e.code, body
    except Exception as e:
        return None, str(e)

def main():
    base_url = 'https://sofaifx-bot-v2.onrender.com'

    print("Testing deployed backend endpoints...\n")

    # Test health
    print("1. Testing /health endpoint:")
    status, body = test_endpoint(f"{base_url}/health")
    print(f"   Status: {status}")
    print(f"   Response: {body}\n")

    # Test login with admin credentials
    print("2. Testing /auth/login with admin credentials:")
    login_data = {
        'email': 'cyriladmin@gmail.com',
        'password': 'Admin1234'
    }
    status, body = test_endpoint(f"{base_url}/auth/login", 'POST', login_data)
    print(f"   Status: {status}")
    print(f"   Response: {body}\n")

    # Test bootstrap-admin (should fail without secret)
    print("3. Testing /auth/bootstrap-admin without secret:")
    bootstrap_data = {
        'email': 'cyriladmin@gmail.com',
        'password': 'Admin1234'
    }
    status, body = test_endpoint(f"{base_url}/auth/bootstrap-admin", 'POST', bootstrap_data)
    print(f"   Status: {status}")
    print(f"   Response: {body}\n")

if __name__ == '__main__':
    main()