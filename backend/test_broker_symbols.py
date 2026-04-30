#!/usr/bin/env python3
"""Test script to fetch and display all available broker symbols from MT5"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

import MetaTrader5 as mt5

def main():
    print("Initializing MT5...")
    
    # Initialize MT5
    if not mt5.initialize():
        error = mt5.last_error()
        print(f"MT5 initialization failed: {error}")
        return
    
    print("MT5 initialized successfully!")
    
    # Get all symbols
    print("\nFetching all symbols from broker...")
    symbols = mt5.symbols_get()
    
    if symbols is None:
        print("Failed to get symbols")
        mt5.shutdown()
        return
    
    print(f"\nTotal symbols available: {len(symbols)}")
    print("\n" + "=" * 60)
    print("ALL AVAILABLE BROKER SYMBOLS:")
    print("=" * 60)
    
    # Print all symbols
    for i, s in enumerate(symbols):
        print(f"{i+1:3}. {s.name}")
    
    print("\n" + "=" * 60)
    print("SYMBOLS CONTAINING 'EUR':")
    print("=" * 60)
    
    eur_symbols = [s.name for s in symbols if 'EUR' in s.name.upper()]
    for s in eur_symbols:
        print(f"  {s}")
    
    print("\n" + "=" * 60)
    print("SYMBOLS CONTAINING 'USD':")
    print("=" * 60)
    
    usd_symbols = [s.name for s in symbols if 'USD' in s.name.upper()]
    for s in usd_symbols:
        print(f"  {s}")
    
    mt5.shutdown()
    print("\nMT5 connection closed.")

if __name__ == '__main__':
    main()