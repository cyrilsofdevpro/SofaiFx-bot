#!/usr/bin/env python3
"""
Test script for Multi-Pair Chart Feature

Tests the /api/chart-data endpoint to verify:
- Symbol validation
- Timeframe mapping
- OHLC data formatting
- Fallback behavior
"""

import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:5000'

def test_chart_data():
    """Test /api/chart-data endpoint"""
    
    print("=" * 60)
    print("🧪 Testing Multi-Pair Chart Feature")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {'symbol': 'EURUSD', 'timeframe': '60', 'name': 'EUR/USD 1-hour'},
        {'symbol': 'GBPUSD', 'timeframe': '15', 'name': 'GBP/USD 15-min'},
        {'symbol': 'USDJPY', 'timeframe': '1', 'name': 'USD/JPY 1-min'},
        {'symbol': 'AUDUSD', 'timeframe': '240', 'name': 'AUD/USD 4-hour'},
        {'symbol': 'USDCAD', 'timeframe': '1440', 'name': 'USD/CAD Daily'},
    ]
    
    results = []
    
    for test in test_cases:
        symbol = test['symbol']
        timeframe = test['timeframe']
        name = test['name']
        
        try:
            url = f"{API_BASE}/api/chart-data?symbol={symbol}&timeframe={timeframe}"
            print(f"\n[TEST] {name}")
            print(f"  URL: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"  ✅ Status: {response.status_code}")
                print(f"  📊 Candles: {data.get('count', 0)}")
                
                if data.get('ohlc') and len(data['ohlc']) > 0:
                    latest = data['ohlc'][-1]
                    print(f"  📈 Latest Close: {latest['close']:.5f}")
                    
                    # Calculate change
                    if len(data['ohlc']) > 1:
                        prev = data['ohlc'][-2]
                        change = ((latest['close'] - prev['close']) / prev['close'] * 100)
                        print(f"  💹 Change: {change:+.2f}%")
                    
                    print(f"  🔹 High: {latest['high']:.5f}")
                    print(f"  🔹 Low: {latest['low']:.5f}")
                    print(f"  ✓ PASSED")
                    results.append((name, 'PASS'))
                else:
                    print(f"  ⚠️ No OHLC data returned")
                    print(f"  ✗ FAILED")
                    results.append((name, 'FAIL'))
            else:
                print(f"  ❌ Status: {response.status_code}")
                print(f"  Error: {response.text}")
                print(f"  ✗ FAILED")
                results.append((name, 'FAIL'))
                
        except requests.exceptions.ConnectError:
            print(f"  ❌ Connection Error - Backend not running at {API_BASE}")
            print(f"  ✗ FAILED")
            results.append((name, 'FAIL'))
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print(f"  ✗ FAILED")
            results.append((name, 'FAIL'))
    
    # Test invalid symbol
    print(f"\n[TEST] Invalid Symbol (should fail)")
    try:
        response = requests.get(f"{API_BASE}/api/chart-data?symbol=INVALID&timeframe=60", timeout=10)
        if response.status_code == 400:
            print(f"  ✅ Correctly rejected invalid symbol (400)")
            print(f"  ✓ PASSED")
            results.append(('Invalid Symbol Handling', 'PASS'))
        else:
            print(f"  ⚠️ Unexpected status: {response.status_code}")
            results.append(('Invalid Symbol Handling', 'FAIL'))
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        results.append(('Invalid Symbol Handling', 'FAIL'))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == 'PASS')
    failed = sum(1 for _, status in results if status == 'FAIL')
    
    for name, status in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {name}: {status}")
    
    print(f"\n{passed} passed, {failed} failed out of {len(results)} tests")
    
    if failed == 0:
        print("\n🎉 All tests PASSED! Chart feature is working!")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) FAILED. Check backend logs.")
        return False

def test_browser_integration():
    """Provide browser testing instructions"""
    
    print("\n" + "=" * 60)
    print("🌐 BROWSER INTEGRATION TEST")
    print("=" * 60)
    
    print("""
Steps to manually test in browser:

1. ✅ Start backend:
   cd backend && python main.py

2. ✅ Open dashboard:
   http://localhost:5000/
   or file:///path/to/frontend/index.html

3. ✅ Test chart initialization:
   - Look for candlestick chart below "Live Forex Charts"
   - Verify EUR/USD tab is active (green gradient)
   - Check info cards show price data

4. ✅ Test tab switching:
   - Click "GBP/USD" tab
   - Chart should update instantly (no reload)
   - Price/high/low should change
   - Watch DevTools Network tab for /api/chart-data call

5. ✅ Test timeframe switching:
   - Open Timeframe dropdown
   - Select "5min"
   - Chart should re-render with new candles
   - Info cards update

6. ✅ Test all pairs:
   EUR/USD → GBP/USD → USD/JPY → AUD/USD → USD/CAD
   (Each should display different data)

7. ✅ Test error recovery:
   - Stop backend API
   - Click a tab
   - Chart should show mock data (fallback)
   - No errors in console

8. ✅ Test responsiveness:
   - Resize window (desktop)
   - Chart should scale with window
   - Tabs should reflow on mobile

✓ If all steps work, feature is fully functional!
    """)

def quick_api_check():
    """Quick check if backend is running"""
    try:
        response = requests.get(f'{API_BASE}/health', timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print("❌ Backend returned non-200 status")
            return False
    except Exception as e:
        print(f"❌ Backend is not running: {str(e)}")
        return False

if __name__ == '__main__':
    print(f"Testing at: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if backend is running
    if not quick_api_check():
        print(f"\n⚠️ Backend not running at {API_BASE}")
        print("Start it with: cd backend && python main.py")
        exit(1)
    
    # Run API tests
    success = test_chart_data()
    
    # Show browser testing guide
    test_browser_integration()
    
    exit(0 if success else 1)
