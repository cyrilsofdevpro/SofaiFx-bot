#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from src.api.flask_app import app
import json

with app.test_client() as client:
    # Test with live=true (default) to fetch from TwelveData first
    resp = client.get('/api/chart-data?symbol=EURUSD&timeframe=60&live=true')
    print(f"Status Code: {resp.status_code}")
    data = resp.get_json()
    print(f"Symbol: {data.get('symbol')}")
    print(f"Data Points: {data.get('count')}")
    if data.get('ohlc'):
        first = data['ohlc'][0]
        last = data['ohlc'][-1]
        print(f"First Candle Time: {first['time']}")
        print(f"Last Candle: O={last['open']}, H={last['high']}, L={last['low']}, C={last['close']}")
