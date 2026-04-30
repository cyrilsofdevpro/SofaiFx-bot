import requests
import json

pairs = ['GBPUSD', 'USDJPY']

for pair in pairs:
    try:
        payload = {'symbol': pair, 'notify': False}
        response = requests.post('http://127.0.0.1:5000/api/analyze', json=payload, timeout=20)
        data = response.json()
        
        if 'signal' in data and data['signal']:
            signal = data['signal']
            print(f"\n{signal['symbol']}:")
            print(f"  Signal: {signal['signal']}")
            print(f"  Confidence: {signal['confidence']}")
            print(f"  Price: {signal['price']}")
            print(f"  Reason: {signal['reason']}")
    except Exception as e:
        print(f"Error analyzing {pair}: {e}")
