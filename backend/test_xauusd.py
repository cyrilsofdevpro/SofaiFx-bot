import requests
import json

try:
    payload = {'symbol': 'XAUUSD', 'notify': False}
    response = requests.post('http://127.0.0.1:5000/api/analyze', json=payload, timeout=30)
    data = response.json()
    
    print("Status:", response.status_code)
    print("Response:", json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
