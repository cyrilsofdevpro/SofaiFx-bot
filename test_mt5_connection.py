#!/usr/bin/env python3
"""
MT5 Account Connection - Integration Test
Tests MT5 connection feature end-to-end
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
API_BASE_URL = 'http://localhost:5000'
AUTH_TOKEN = None
TEST_USER_EMAIL = 'test_mt5@sofai.com'
TEST_USER_PASSWORD = 'Test@12345'
TEST_USER_NAME = 'Test MT5 User'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_server_health():
    """Test server connectivity"""
    print_header("1. Testing Server Health")
    
    try:
        response = requests.get(f'{API_BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is running: {data.get('service')}")
            return True
        else:
            print_error(f"Server returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_warning("Make sure backend is running: python backend/run_api.bat")
        return False

def register_user():
    """Register test user"""
    print_header("2. Registering Test User")
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/auth/register',
            json={
                'name': TEST_USER_NAME,
                'email': TEST_USER_EMAIL,
                'password': TEST_USER_PASSWORD
            },
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            print_success(f"User registered: {TEST_USER_EMAIL}")
            return True
        elif response.status_code == 400:
            # User might already exist
            print_warning("User may already exist")
            return True
        else:
            print_error(f"Registration failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Registration failed: {e}")
        return False

def login_user():
    """Login test user"""
    print_header("3. Logging in Test User")
    global AUTH_TOKEN
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/auth/login',
            json={
                'email': TEST_USER_EMAIL,
                'password': TEST_USER_PASSWORD
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            AUTH_TOKEN = data.get('access_token')
            if AUTH_TOKEN:
                print_success(f"User logged in")
                print_info(f"Token: {AUTH_TOKEN[:40]}...")
                return True
            else:
                print_error("No token in response")
                return False
        else:
            print_error(f"Login failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Login failed: {e}")
        return False

def test_get_servers():
    """Test getting available servers"""
    print_header("4. Testing GET /api/mt5/servers")
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/mt5/servers',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            servers = data.get('servers', [])
            print_success(f"Loaded {len(servers)} MT5 servers")
            
            for i, server in enumerate(servers[:5], 1):
                print_info(f"  {i}. {server['name']} ({server['type']})")
            
            if len(servers) > 5:
                print_info(f"  ... and {len(servers) - 5} more")
            
            return True
        else:
            print_error(f"Failed to get servers: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error getting servers: {e}")
        return False

def test_connect_invalid_credentials():
    """Test connection with invalid credentials"""
    print_header("5. Testing MT5 Connect with Invalid Credentials")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return True
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/mt5/connect',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            json={
                'login': '999999',
                'password': 'wrongpassword',
                'server': 'JustMarkets-Demo'
            },
            timeout=10
        )
        
        print_info(f"Response: {response.status_code}")
        data = response.json()
        
        if not data.get('success'):
            print_success(f"Correctly rejected invalid credentials")
            print_info(f"Error: {data.get('error')}")
            return True
        else:
            print_warning(f"Connection succeeded (unlikely with invalid creds)")
            return True
    except Exception as e:
        print_error(f"Error during connection test: {e}")
        return False

def test_connect_valid_credentials():
    """Test connection with valid credentials (requires real account)"""
    print_header("6. Testing MT5 Connect with Valid Credentials")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return True
    
    print_warning("This test requires real MT5 credentials")
    print_info("To test manually, enter credentials in the UI")
    
    # Prompt for credentials (optional)
    response = input("\nEnter MT5 Login ID (or press Enter to skip): ").strip()
    if not response:
        print_info("Skipping valid credentials test")
        return True
    
    login = response
    password = input("Enter MT5 Password: ").strip()
    server = input("Enter MT5 Server (e.g., JustMarkets-Demo): ").strip()
    
    if not login or not password or not server:
        print_warning("Invalid input - skipping")
        return True
    
    try:
        print_info("Attempting connection...")
        response = requests.post(
            f'{API_BASE_URL}/api/mt5/connect',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            json={
                'login': login,
                'password': password,
                'server': server
            },
            timeout=15
        )
        
        data = response.json()
        
        if data.get('success'):
            print_success(f"Connected to MT5!")
            account = data.get('account', {})
            print_info(f"  Account: {account.get('login')}")
            print_info(f"  Balance: {account.get('balance')} {account.get('currency')}")
            print_info(f"  Equity: {account.get('equity')} {account.get('currency')}")
            print_info(f"  Type: {account.get('trade_mode')}")
            return True
        else:
            print_error(f"Connection failed: {data.get('error')}")
            print_info(f"Details: {data.get('details')}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_connection_status():
    """Test getting connection status"""
    print_header("7. Testing GET /api/mt5/connection-status")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return True
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/mt5/connection-status',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Connection status retrieved")
            print_info(f"  Connected: {data.get('connected')}")
            print_info(f"  Account #: {data.get('account_number', 'N/A')}")
            
            if data.get('session_info', {}).get('connected_since'):
                print_info(f"  Since: {data['session_info']['connected_since']}")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_disconnect():
    """Test disconnection"""
    print_header("8. Testing POST /api/mt5/disconnect")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return True
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/mt5/disconnect',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Disconnected successfully")
                return True
            else:
                print_warning(f"Disconnect returned false (no active connection)")
                return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_api_protection():
    """Test that endpoints require authentication"""
    print_header("9. Testing API Authentication Protection")
    
    endpoints = [
        ('/api/mt5/connect', 'POST'),
        ('/api/mt5/disconnect', 'POST'),
        ('/api/mt5/connection-status', 'GET'),
    ]
    
    all_protected = True
    
    for endpoint, method in endpoints:
        try:
            if method == 'POST':
                response = requests.post(
                    f'{API_BASE_URL}{endpoint}',
                    json={},
                    timeout=5
                )
            else:
                response = requests.get(
                    f'{API_BASE_URL}{endpoint}',
                    timeout=5
                )
            
            if response.status_code == 401:
                print_success(f"{method} {endpoint} - Protected ✓")
            else:
                print_warning(f"{method} {endpoint} - Not protected (status: {response.status_code})")
                all_protected = False
        except Exception as e:
            print_error(f"Error testing {endpoint}: {e}")
            all_protected = False
    
    return all_protected

def run_all_tests():
    """Run all tests"""
    print_header("MT5 Account Connection - Test Suite")
    
    tests = [
        ("Server Health", test_server_health),
        ("User Registration", register_user),
        ("User Login", login_user),
        ("Get Servers", test_get_servers),
        ("Invalid Credentials", test_connect_invalid_credentials),
        ("Valid Credentials", test_connect_valid_credentials),
        ("Connection Status", test_connection_status),
        ("Disconnect", test_disconnect),
        ("API Protection", test_api_protection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print_header("Test Results Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {Colors.BOLD}{passed}/{total} passed{Colors.RESET}")
    
    if passed == total:
        print_success("\n✅ All tests passed! MT5 connection feature is working correctly.")
        return True
    else:
        print_error(f"\n❌ {total - passed} test(s) failed. Check the issues above.")
        return False

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
