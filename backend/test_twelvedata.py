#!/usr/bin/env python3
"""Test real-time price from TwelveData API"""

from src.data.twelvedata import TwelveDataClient

client = TwelveDataClient()

# Get real-time quote
print("=" * 60)
print("EUR/USD REAL-TIME QUOTE")
print("=" * 60)

quote = client.get_quote('EUR/USD')
if quote:
    print(f"\n✅ Quote Data Retrieved Successfully!")
    print(f"Last Price:  {quote.get('last', 'N/A')}")
    print(f"Bid:         {quote.get('bid', 'N/A')}")
    print(f"Ask:         {quote.get('ask', 'N/A')}")
    print(f"Volume:      {quote.get('volume', 'N/A')}")
    print(f"Timestamp:   {quote.get('timestamp', 'N/A')}")
else:
    print("\n❌ Failed to get quote data")

# Get time series data
print("\n" + "=" * 60)
print("EUR/USD RECENT 1-MINUTE CANDLES")
print("=" * 60)

df = client.get_time_series('EUR/USD', interval='1min', outputsize=10)
if not df.empty:
    print(f"\n✅ Retrieved {len(df)} candles from TwelveData")
    print("\nRecent candles:")
    print(df[['datetime', 'open', 'high', 'low', 'close']].tail(10).to_string())
    print(f"\nLatest Close Price: {df['close'].iloc[-1]}")
    print(f"Latest Candle Time: {df['datetime'].iloc[-1]}")
else:
    print("\n❌ No time series data received")
