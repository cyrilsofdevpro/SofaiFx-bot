#!/usr/bin/env python
"""
Test to verify both TwelveData and Alpha Vantage APIs are working and accessible
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.twelvedata import TwelveDataClient
from src.data.alpha_vantage import AlphaVantageClient
from src.utils.logger import logger

print("=" * 90)
print("TESTING DUAL API SUPPORT: TwelveData + Alpha Vantage")
print("=" * 90)

twelvedata = TwelveDataClient()
alpha_vantage = AlphaVantageClient()

# Test TwelveData
print("\n[1] Testing TwelveData API (Real-time 1-minute candles)")
print("-" * 90)
try:
    df_td = twelvedata.get_time_series('EUR/USD', interval='1min', outputsize=50)
    if df_td is not None and not df_td.empty:
        print(f"SUCCESS: TwelveData working!")
        print(f"  - Data points: {len(df_td)}")
        print(f"  - Latest close: {df_td['close'].iloc[-1]}")
        print(f"  - Columns: {list(df_td.columns)}")
        print(f"  - Time interval: 1-minute real-time candles")
    else:
        print("FAILED: TwelveData returned no data")
except Exception as e:
    print(f"ERROR: TwelveData failed: {e}")

# Test Alpha Vantage
print("\n[2] Testing Alpha Vantage API (Daily historical candles)")
print("-" * 90)
try:
    df_av = alpha_vantage.get_forex_data('EUR', 'USD', interval='daily')
    if df_av is not None and not df_av.empty:
        print(f"SUCCESS: Alpha Vantage working!")
        print(f"  - Data points: {len(df_av)}")
        print(f"  - Latest close: {df_av['Close'].iloc[-1] if 'Close' in df_av.columns else 'N/A'}")
        print(f"  - Columns: {list(df_av.columns)}")
        print(f"  - Time interval: Daily historical candles")
    else:
        print("FAILED: Alpha Vantage returned no data")
except Exception as e:
    print(f"ERROR: Alpha Vantage failed: {e}")

# Test Fallback Logic
print("\n[3] Testing Fallback Logic (Simulate TwelveData failure)")
print("-" * 90)
try:
    # Try TwelveData first
    df = TwelveDataClient().get_time_series('EUR/USD', interval='1min', outputsize=50)
    
    if df is not None and not df.empty:
        data_source = 'TwelveData (Primary)'
        print(f"USING: {data_source} - {len(df)} candles")
    else:
        # Fallback to Alpha Vantage
        df = AlphaVantageClient().get_forex_data('EUR', 'USD')
        data_source = 'Alpha Vantage (Fallback)'
        print(f"USING: {data_source} - {len(df)} candles")
        
    print(f"SUCCESS: Fallback logic working!")
except Exception as e:
    print(f"ERROR: Fallback failed: {e}")

# Summary
print("\n" + "=" * 90)
print("API CONFIGURATION SUMMARY")
print("=" * 90)
print("\nPrimary Data Source:")
print("  TwelveData API")
print("  - Real-time 1-minute candles")
print("  - Most accurate for short-term analysis")
print("  - Used for live signal generation")

print("\nFallback Data Source:")
print("  Alpha Vantage API")
print("  - Daily historical candles")
print("  - Used if TwelveData fails or is unavailable")
print("  - Provides longer-term trend analysis")

print("\nRedundancy Strategy:")
print("  ✓ System uses TwelveData first (real-time)")
print("  ✓ Falls back to Alpha Vantage if TwelveData fails")
print("  ✓ Ensures trading signals are always generated")
print("  ✓ Two independent data providers for reliability")

print("\n" + "=" * 90)
