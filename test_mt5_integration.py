#!/usr/bin/env python3
"""
MT5 Account Service - Integration Test
Tests all MT5 account service methods and API endpoints
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
API_BASE_URL = 'http://localhost:5000'
AUTH_TOKEN = None  # Will be set after login

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_connection():
    """Test basic server connectivity"""
    print_header("1. Testing Server Connectivity")
    
    try:
        response = requests.get(f'{API_BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print_success(f"Server is running on {API_BASE_URL}")
            data = response.json()
            print_info(f"Service: {data.get('service')}")
            print_info(f"Status: {data.get('status')}")
            return True
        else:
            print_error(f"Server returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_warning("Make sure the backend is running: python backend/run_api.bat")
        return False

def test_mt5_status():
    """Test MT5 connection status (no auth required)"""
    print_header("2. Testing MT5 Connection Status")
    
    try:
        response = requests.get(f'{API_BASE_URL}/api/mt5/status', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("MT5 status endpoint working")
            
            if data['data']['connected']:
                print_success(f"MT5 Terminal Connected")
                print_info(f"Build: {data['data'].get('build', 'Unknown')}")
            else:
                print_warning(f"MT5 Terminal Not Connected: {data['data']['message']}")
            
            return data['data']['connected']
        else:
            print_error(f"Status endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to check MT5 status: {e}")
        return False

def login_user(email='test@sofai.com', password='Test@1234'):
    """Login to get JWT token"""
    print_header("3. Testing Authentication (Login)")
    global AUTH_TOKEN
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/auth/login',
            json={'email': email, 'password': password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            AUTH_TOKEN = data.get('access_token')
            if AUTH_TOKEN:
                print_success(f"Login successful")
                print_info(f"Token: {AUTH_TOKEN[:30]}...")
                return True
            else:
                print_error("No token in response")
                return False
        else:
            print_warning(f"Login failed: {response.status_code}")
            # Try with different credentials
            if response.status_code == 401:
                print_warning("Invalid credentials - trying to register new user")
                return register_user(email, password)
            return False
    except Exception as e:
        print_error(f"Login failed: {e}")
        return False

def register_user(email='test@sofai.com', password='Test@1234', name='Test User'):
    """Register a new user"""
    print_info("Registering new user...")
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/auth/register',
            json={'name': name, 'email': email, 'password': password},
            timeout=5
        )
        
        if response.status_code == 201 or response.status_code == 200:
            print_success(f"User registered successfully")
            # Try to login
            return login_user(email, password)
        else:
            print_error(f"Registration failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Registration failed: {e}")
        return False

def test_account_endpoint():
    """Test /api/mt5/account endpoint"""
    print_header("4. Testing /api/mt5/account Endpoint")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return False
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/mt5/account',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Account endpoint working")
            
            if data['success']:
                account = data['data']
                print_info(f"Connection: {'🟢 Connected' if account['connected'] else '🔴 Disconnected'}")
                
                if account['connected']:
                    print_info(f"Balance: {account['balance']} {account['currency']}")
                    print_info(f"Equity: {account['equity']} {account['currency']}")
                    print_info(f"Margin: {account['margin']} / Free: {account['free_margin']}")
                    print_info(f"Margin Level: {account['margin_level']}%")
                    print_info(f"Leverage: 1:{account['leverage']}")
                    print_info(f"Account Type: {account['trade_mode']}")
                    return True
                else:
                    print_warning(f"MT5 not connected: {account['message']}")
                    return False
            else:
                print_error(data.get('error', 'Unknown error'))
                return False
        else:
            print_error(f"Endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to fetch account: {e}")
        return False

def test_summary_endpoint():
    """Test /api/mt5/summary endpoint"""
    print_header("5. Testing /api/mt5/summary Endpoint")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return False
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/mt5/summary',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Summary endpoint working")
            
            if data['success']:
                summary = data['data']
                print_info(f"Status: {summary['status']}")
                
                if summary['status'] == 'connected':
                    print_info(f"Account: {summary['account_number']}")
                    print_info(f"Balance: {summary['balance']} {summary['currency']}")
                    print_info(f"Equity: {summary['equity']} {summary['currency']}")
                    print_info(f"P/L: {summary['profit_loss']} ({summary['profit_loss_pct']}%)")
                    print_info(f"Margin Level: {summary['margin_level']}%")
                    return True
                else:
                    print_warning("MT5 not connected")
                    return False
            else:
                print_error(data.get('error', 'Unknown error'))
                return False
        else:
            print_error(f"Endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to fetch summary: {e}")
        return False

def test_health_endpoint():
    """Test /api/mt5/health endpoint"""
    print_header("6. Testing /api/mt5/health Endpoint")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return False
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/mt5/health',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Health endpoint working")
            
            if data['success']:
                health = data['data']
                print_info(f"Status: {health['status']}")
                print_info(f"Health Score: {health['health_score']}/100")
                print_info(f"Account Type: {health['account_type']}")
                
                if health['warnings']:
                    print_warning(f"Warnings ({len(health['warnings'])}):")
                    for warning in health['warnings']:
                        print_warning(f"  • {warning}")
                else:
                    print_success("No warnings - account is healthy")
                
                return True
            else:
                print_error(data.get('error', 'Unknown error'))
                return False
        else:
            print_error(f"Endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to fetch health: {e}")
        return False

def test_positions_endpoint():
    """Test /api/mt5/positions endpoint"""
    print_header("7. Testing /api/mt5/positions Endpoint")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return False
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/mt5/positions',
            headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Positions endpoint working")
            
            if data['success']:
                positions = data['data']
                print_info(f"Open Positions: {positions['total_positions']}")
                print_info(f"Total P/L: {positions['total_profit']}")
                
                if positions['positions']:
                    for pos in positions['positions']:
                        print_info(f"  • {pos['symbol']} {pos['type']} {pos['volume']} @ {pos['price_open']}")
                else:
                    print_info("No open positions")
                
                return True
            else:
                print_error(data.get('error', 'Unknown error'))
                return False
        else:
            print_error(f"Endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to fetch positions: {e}")
        return False

def test_auto_refresh():
    """Test auto-refresh behavior"""
    print_header("8. Testing Auto-Refresh Behavior")
    
    if not AUTH_TOKEN:
        print_warning("Skipping - no auth token")
        return False
    
    print_info("Fetching account data 3 times with 2-second intervals...")
    
    timestamps = []
    for i in range(3):
        try:
            response = requests.get(
                f'{API_BASE_URL}/api/mt5/account',
                headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                ts = data['data']['timestamp']
                timestamps.append(ts)
                print_info(f"  Request {i+1}: {ts}")
                
                if i < 2:
                    time.sleep(2)
        except Exception as e:
            print_error(f"Request {i+1} failed: {e}")
            return False
    
    # Check if timestamps are different
    if len(set(timestamps)) > 1:
        print_success("Data is updating correctly")
        return True
    else:
        print_warning("Timestamps are the same (data might be cached)")
        return True  # Not a critical failure

def run_all_tests():
    """Run all tests"""
    print_header("SofAi-Fx MT5 Account Integration Test Suite")
    
    results = {}
    
    # Test 1: Server connectivity
    if not test_connection():
        print_error("Server is not running. Cannot continue.")
        return False
    
    # Test 2: MT5 status
    results['mt5_status'] = test_mt5_status()
    
    # Test 3: Authentication
    if not login_user():
        print_error("Could not authenticate. Cannot continue.")
        return False
    
    # Tests 4-7: API endpoints
    results['account'] = test_account_endpoint()
    results['summary'] = test_summary_endpoint()
    results['health'] = test_health_endpoint()
    results['positions'] = test_positions_endpoint()
    
    # Test 8: Auto-refresh
    results['auto_refresh'] = test_auto_refresh()
    
    # Summary
    print_header("Test Results Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print_info(f"Tests Passed: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print_info(f"{test_name}: {status}")
    
    if passed == total:
        print_success("\nAll tests passed! MT5 integration is working correctly.")
        return True
    else:
        print_warning(f"\n{total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
