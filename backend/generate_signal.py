import requests
import json

BASE_URL = 'http://localhost:5000'

print("=" * 60)
print("Generating fresh EURUSD signal...")
print("=" * 60)

# Login with user that has id=3
login_resp = requests.post(
    f'{BASE_URL}/auth/login', 
    json={'email': 'testuser@example.com', 'password': 'password123'}, 
    timeout=10
)
token = login_resp.json()['access_token']
print("Logged in successfully")

# Generate signal
signal_resp = requests.post(
    f'{BASE_URL}/api/analyze', 
    json={'symbol': 'EURUSD', 'notify': True}, 
    headers={'Authorization': f'Bearer {token}'}, 
    timeout=45
)
data = signal_resp.json()

signal_info = data.get('signal', {})
print(f"Signal generated: {signal_info.get('signal_type')} @ {signal_info.get('price')}")
print(f"Confidence: {signal_info.get('confidence'):.2%}")
print(f"Saved to DB: {data.get('saved_to_db')}")

print("\n" + "=" * 60)
print("Signal saved! Execution service will pick it up in ~30 seconds")
print("=" * 60)