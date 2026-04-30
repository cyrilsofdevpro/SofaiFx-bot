#!/usr/bin/env python
"""
Test script to verify the full signal analysis pipeline with REAL market data from TwelveData API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.twelvedata import TwelveDataClient
from src.signals.signal_generator import SignalGenerator
from src.utils.logger import logger
from datetime import datetime

print("=" * 90)
print("TESTING LIVE MARKET DATA PIPELINE WITH REAL TWELVEDATA API")
print("=" * 90)
print()

# Initialize services
twelvedata = TwelveDataClient()
signal_generator = SignalGenerator()

# Test 1: Verify we can fetch real data from TwelveData
print("TEST 1: Fetching real market data from TwelveData API")
print("-" * 90)

symbols = ['EUR/USD', 'GBP/USD']
real_data_status = {}

for symbol in symbols:
    print(f"\nFetching {symbol} (1-minute candles)...")
    df = twelvedata.get_time_series(symbol, interval='1min', outputsize=100)
    
    if df is not None and not df.empty and len(df) > 0:
        latest_close = df['close'].iloc[-1] if 'close' in df.columns else None
        real_data_status[symbol] = {
            'fetched': True,
            'candles': len(df),
            'latest_close': latest_close,
            'columns': list(df.columns)
        }
        print(f"  SUCCESS: Successfully fetched {len(df)} candles")
        print(f"  Latest close: {latest_close}")
        print(f"  Columns: {', '.join(df.columns)}")
    else:
        real_data_status[symbol] = {
            'fetched': False,
            'candles': 0,
            'latest_close': None,
            'columns': []
        }
        print(f"  FAILED: Failed to fetch data")

print("\n" + "=" * 90)
print("TEST 2: Generating signals with real market data")
print("=" * 90)

signals_data = []

for symbol in symbols:
    if real_data_status[symbol]['fetched']:
        print(f"\nGenerating signal for {symbol} with REAL data...")
        try:
            # Format symbol for signal generator (e.g., EUR/USD -> EURUSD)
            symbol_code = symbol.replace('/', '')
            
            # Fetch fresh data for signal generation
            df = twelvedata.get_time_series(symbol, interval='1min', outputsize=100)
            
            if df is not None and not df.empty:
                # Normalize column names to capitalize OHLC (required by strategies)
                # TwelveData returns lowercase: open, high, low, close
                # Strategies expect: Open, High, Low, Close
                if 'open' in df.columns:
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })
                
                # Generate signal
                signal = signal_generator.generate_signal(df, symbol_code)
                
                if signal:
                    signals_data.append(signal)
                    signal_dict = signal.to_dict()
                    
                    print(f"\nSUCCESS: Signal for {symbol}:")
                    print(f"  Signal: {signal_dict.get('signal', 'N/A')}")
                    print(f"  Confidence: {signal_dict.get('confidence', 0):.2%}")
                    print(f"  AI Prediction: {signal_dict.get('ai_prediction', {}).get('direction', 'N/A')}")
                    print(f"  AI Confidence: {signal_dict.get('ai_prediction', {}).get('confidence', 0):.2%}")
                    print(f"  Price: ${signal_dict.get('price', 'N/A')}")
                    print(f"  Timestamp: {signal_dict.get('timestamp', 'N/A')}")
                else:
                    print(f"  WARNING: Signal generation returned None")
            else:
                print(f"  WARNING: Failed to fetch fresh data for signal generation")
                
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\nSKIPPED: Skipping signal generation - could not fetch real data for {symbol}")

print("\n" + "=" * 90)
print("TEST 3: Results Summary")
print("=" * 90)

print("\nReal Data Fetch Results:")
for symbol, status in real_data_status.items():
    if status['fetched']:
        print(f"  SUCCESS: {symbol}: {status['candles']} candles fetched")
        print(f"    Latest close: {status['latest_close']}")
    else:
        print(f"  FAILED: {symbol}: Failed to fetch real data")

print(f"\nSignals Generated: {len(signals_data)}")
for signal in signals_data:
    try:
        sig_dict = signal.to_dict()
        ai_conf = sig_dict.get('ai_prediction', {}).get('confidence', 0)
        print(f"  SUCCESS: {sig_dict.get('symbol', 'N/A')}: AI Confidence {ai_conf:.2%}, Signal: {sig_dict.get('signal', 'N/A')}")
    except Exception as e:
        print(f"  WARNING: Error processing signal: {e}")

print("\n" + "=" * 90)

# Critical check: Are we using REAL data?
if real_data_status['EUR/USD']['fetched'] and real_data_status['GBP/USD']['fetched']:
    print("SUCCESS: System is now using REAL market data from TwelveData API!")
    print("         AI predictions are based on actual market patterns")
else:
    print("WARNING: Could not fetch real market data")
    print("         Check TwelveData API key and internet connection")

print("=" * 90)
