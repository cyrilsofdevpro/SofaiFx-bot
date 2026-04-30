#!/usr/bin/env python3
"""
MT5 EA Signal API - Test Script

This script tests the /signal endpoint locally to verify it works before deployment.

Usage:
    python test_signal_api.py

Requirements:
    - Backend running: python src/api/flask_app.py
    - Valid API key in database
"""

import requests
import sys
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:5000"
SIGNAL_ENDPOINT = f"{API_URL}/signal"

# Test symbols
TEST_SYMBOLS = [
    "EURUSD",
    "GBPUSD", 
    "USDJPY",
]

def get_api_key():
    """Get API key from user input"""
    print("\n" + "="*60)
    print("🔑 API Key Needed")
    print("="*60)
    print("\nTo get your API key:")
    print("1. Open http://localhost:5000")
    print("2. Login with your credentials")
    print("3. Go to Settings → API Key")
    print("4. Copy and paste below")
    print()
    
    api_key = input("Enter your API key: ").strip()
    
    if not api_key:
        print("❌ API key cannot be empty")
        sys.exit(1)
    
    return api_key


def test_health_check():
    """Test basic health endpoint"""
    print("\n" + "="*60)
    print("🏥 Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print(f"   Make sure it's running: python src/api/flask_app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signal_endpoint(api_key, symbol="EURUSD", format_type="json"):
    """Test the signal endpoint"""
    
    print(f"\n📡 Testing: GET /signal")
    print(f"   Symbol: {symbol}")
    print(f"   Format: {format_type}")
    print(f"   API Key: {api_key[:10]}...")
    
    url = f"{SIGNAL_ENDPOINT}?apikey={api_key}&symbol={symbol}&format={format_type}"
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            if format_type == "json":
                data = response.json()
                print(f"   ✅ Response received:")
                print(f"      Signal: {data.get('signal')}")
                print(f"      Confidence: {data.get('confidence')}")
                print(f"      Data Points: {data.get('data_points')}")
                print(f"      Data Source: {data.get('data_source')}")
                print(f"      Timestamp: {data.get('timestamp')}")
                return True
            else:
                signal = response.text.strip()
                print(f"   ✅ Response received: {signal}")
                return True
        
        elif response.status_code == 401:
            print(f"   ❌ 401 Unauthorized - Invalid API key")
            print(f"      Check your API key is correct")
            return False
        
        elif response.status_code == 400:
            print(f"   ❌ 400 Bad Request - Invalid parameters")
            error = response.json()
            print(f"      Error: {error.get('error')}")
            return False
        
        elif response.status_code == 429:
            print(f"   ⚠️ 429 Rate Limited - Too many requests")
            print(f"      Wait before retrying")
            return False
        
        else:
            print(f"   ❌ {response.status_code} Error")
            try:
                print(f"      {response.json()}")
            except:
                print(f"      {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timeout (>10 seconds)")
        print(f"      Backend might be slow or unreachable")
        return False
    
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection error")
        print(f"      Backend not running or URL incorrect")
        return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_invalid_key(api_key):
    """Test with invalid API key"""
    print("\n" + "="*60)
    print("🔒 Security Test - Invalid Key")
    print("="*60)
    
    invalid_key = "INVALID_KEY_123456789"
    
    print(f"\n📡 Testing with invalid key: {invalid_key[:20]}...")
    
    url = f"{SIGNAL_ENDPOINT}?apikey={invalid_key}&symbol=EURUSD&format=json"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected invalid key (401 Unauthorized)")
            return True
        else:
            print(f"❌ Should return 401, got {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invalid_symbol(api_key):
    """Test with invalid symbol"""
    print("\n" + "="*60)
    print("🔍 Validation Test - Invalid Symbol")
    print("="*60)
    
    print(f"\n📡 Testing with invalid symbol: EUR")
    
    url = f"{SIGNAL_ENDPOINT}?apikey={api_key}&symbol=EUR&format=json"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 400:
            print(f"✅ Correctly rejected invalid symbol (400 Bad Request)")
            print(f"   Error: {response.json().get('error')}")
            return True
        else:
            print(f"❌ Should return 400, got {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_text_format(api_key):
    """Test text response format"""
    print("\n" + "="*60)
    print("📄 Response Format Test - Text")
    print("="*60)
    
    print(f"\n📡 Testing text format (for MT5 EA)...")
    
    url = f"{SIGNAL_ENDPOINT}?apikey={api_key}&symbol=EURUSD&format=text"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            signal = response.text.strip()
            if signal in ["BUY", "SELL", "HOLD"]:
                print(f"✅ Text format working: {signal}")
                return True
            else:
                print(f"❌ Invalid signal response: {signal}")
                return False
        else:
            print(f"❌ {response.status_code} Error")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    
    print("\n" + "="*60)
    print("🧪 SofAi FX - Signal API Test Suite")
    print("="*60)
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   URL: {API_URL}")
    print("="*60)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Backend is not running!")
        print("   Start it with: python src/api/flask_app.py")
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    
    # Track results
    results = {
        "Health Check": True,  # Already passed
        "Signal Endpoint (JSON)": False,
        "Signal Endpoint (Text)": False,
        "Security (Invalid Key)": False,
        "Validation (Invalid Symbol)": False,
        "Multiple Symbols": False,
    }
    
    # Test 2: Signal endpoint with JSON
    results["Signal Endpoint (JSON)"] = test_signal_endpoint(api_key, "EURUSD", "json")
    
    # Test 3: Signal endpoint with text
    results["Signal Endpoint (Text)"] = test_text_format(api_key)
    
    # Test 4: Invalid API key
    results["Security (Invalid Key)"] = test_invalid_key(api_key)
    
    # Test 5: Invalid symbol
    results["Validation (Invalid Symbol)"] = test_invalid_symbol(api_key)
    
    # Test 6: Multiple symbols
    print("\n" + "="*60)
    print("🔄 Testing Multiple Symbols")
    print("="*60)
    
    all_symbols_ok = True
    for symbol in TEST_SYMBOLS[:2]:  # Test first 2
        if not test_signal_endpoint(api_key, symbol, "json"):
            all_symbols_ok = False
    
    results["Multiple Symbols"] = all_symbols_ok
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to deploy!")
        print("\nNext steps:")
        print("1. Read MT5_EA_SIGNAL_API.md for deployment options")
        print("2. Deploy to Render.com or your chosen platform")
        print("3. Create MT5 EA using the template in Quick Reference")
        print("4. Test in strategy tester before live trading")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. See errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
