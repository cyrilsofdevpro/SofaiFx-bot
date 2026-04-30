#!/usr/bin/env python
"""Test multiple currency pairs"""
import requests
import json

pairs = ['EURAUD', 'GBPJPY', 'EURCHF', 'GBPCAD', 'GBPCHF', 'AUDCAD']

print('\n' + '=' * 70)
print('MULTI-PAIR ANALYSIS TEST')
print('=' * 70)

for pair in pairs:
    try:
        r = requests.post('http://127.0.0.1:5000/api/analyze', 
                         json={'symbol': pair, 'notify': False}, 
                         timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            s = data['signal']
            
            print(f'\n{pair:10} | Signal: {s["signal"]:6} | Confidence: {s["confidence"]:.2f} | Price: {s["price"]}')
            print(f'           | Reason: {s["reason"]}')
            
            # Show individual indicators
            if s.get('rsi_signal'):
                print(f'           | RSI: {s["rsi_signal"]["signal"]:6} - {s["rsi_signal"]["reason"][:40]}')
            if s.get('ma_signal'):
                print(f'           | MA:  {s["ma_signal"]["signal"]:6} - {s["ma_signal"]["reason"][:40]}')
        else:
            print(f'\n{pair:10} | Error: Status {r.status_code}')
            
    except Exception as e:
        print(f'\n{pair:10} | Error: {str(e)[:50]}')

print('\n' + '=' * 70)
print('ANALYSIS COMPLETE - All pairs using cached data!')
print('=' * 70)
