================================================================================
           MT5 CREDENTIAL ISOLATION - QUICK START GUIDE (AFTER FIX)
================================================================================

🚀 FOR USERS
============

How to Use the Fixed MT5 Connection System:

STEP 1: Open Dashboard
  - Navigate to: http://localhost:8000/ (or your frontend URL)
  - Login with your account
  - Find "MT5 Account Connection" section

STEP 2: Enter Your MT5 Credentials
  Form Fields:
    MT5 Login ID:     Your MetaTrader 5 account number (e.g., 12345)
    MT5 Password:     Your MetaTrader 5 password
    MT5 Server:       Your broker's MT5 server (e.g., broker-demo.com)

STEP 3: Store & Connect
  Click: "Store & Connect" button
  
  What happens:
    1. Your credentials are encrypted using Fernet encryption
    2. Encrypted credentials stored in database with your user_id
    3. Connection established to your MT5 account
    4. Isolated session created for you only
    5. Status changes to "Connected" with your account number

STEP 4: Use Your Dashboard
  ✅ Your Signals (only yours)
    - See trading signals generated for your account
    - Other users' signals not visible
  
  ✅ Your Trades (only yours)
    - See trades executed on your account
    - Other users' trades not visible
  
  ✅ Your Positions (only yours)
    - See open positions in your account
    - Other users' positions not visible


KEY DIFFERENCES FROM OLD SYSTEM:
  ✅ Your credentials are encrypted (secure storage)
  ✅ Your credentials never sent in API requests after storage
  ✅ Your MT5 session is completely isolated
  ✅ You see only YOUR signals/trades/positions
  ✅ Other users cannot access your data


🔒 SECURITY
===========

Your Credentials Are:
  ✅ Encrypted in database (Fernet encryption)
  ✅ Only decrypted when you connect
  ✅ Never logged or exposed in API responses
  ✅ Inaccessible to other users
  ✅ Safe for multi-user environments

Your Data Is:
  ✅ Tagged with your user_id in database
  ✅ Filtered to show only your data
  ✅ Protected by authentication (JWT token)
  ✅ Isolated from other users' data

Your MT5 Session Is:
  ✅ Created only for you
  ✅ Stored separately in memory
  ✅ Not shared with other users
  ✅ Terminated when you disconnect


════════════════════════════════════════════════════════════════════════════════


🔧 FOR DEVELOPERS
=================

API Endpoints (Use These):

1. Store MT5 Credentials (Encrypted)
   ─────────────────────────────────
   POST /api/mt5/credentials/store
   
   Headers:
     Authorization: Bearer {jwt_token}
     Content-Type: application/json
   
   Body:
   {
     "mt5_login": "12345",
     "mt5_password": "yourpassword",
     "mt5_server": "broker-demo.com",
     "mt5_account_number": "ACC-001"  // optional
   }
   
   Response:
   {
     "success": true,
     "message": "Credentials stored",
     "user_id": 1
   }
   
   ✅ Credentials encrypted & stored in database
   ✅ Only this user can access them


2. Connect to MT5 (Isolated Session)
   ────────────────────────────────
   POST /api/mt5/connect
   
   Headers:
     Authorization: Bearer {jwt_token}
     Content-Type: application/json
   
   Body:
   {}  // Empty body - uses stored credentials
   
   Response:
   {
     "success": true,
     "message": "MT5 account connected successfully",
     "account": {
       "login": 12345,
       "balance": 50000.00,
       "equity": 51200.00,
       "margin": 1000.00,
       "free_margin": 9000.00,
       "currency": "USD",
       "leverage": 100,
       "trade_mode": "demo"
     }
   }
   
   ✅ Isolated session created for this user
   ✅ Only this user's account data returned


3. Disconnect MT5
   ─────────────
   POST /api/mt5/disconnect
   
   Headers:
     Authorization: Bearer {jwt_token}
   
   Response:
   {
     "success": true,
     "message": "MT5 account disconnected"
   }
   
   ✅ Session terminated for this user only


4. Get User's Signals (Isolated)
   ────────────────────────────
   GET /api/mt5/signals
   
   Headers:
     Authorization: Bearer {jwt_token}
   
   Response:
   {
     "success": true,
     "user_id": 1,
     "signal_count": 2,
     "signals": [
       {
         "id": 1,
         "symbol": "EURUSD",
         "signal": "BUY",
         "price": 1.0800,
         "confidence": 75.5,
         "created_at": "2026-04-28T10:30:00"
       }
     ]
   }
   
   ✅ Returns ONLY this user's signals
   ✅ User 1 cannot see User 2's signals


5. Execute Trade (Isolated)
   ───────────────────────
   POST /api/mt5/execute
   
   Headers:
     Authorization: Bearer {jwt_token}
     Content-Type: application/json
   
   Body:
   {
     "symbol": "EURUSD",
     "order_type": "buy",
     "volume": 1.0,
     "stop_loss": 1.0750,
     "take_profit": 1.0900
   }
   
   Response:
   {
     "success": true,
     "order_id": 12345,
     "trade": {...}
   }
   
   ✅ Executed ONLY on this user's MT5 account
   ✅ Trade saved with user_id isolation


ENDPOINTS TO AVOID:
   ❌ POST /api/mt5/connect (old version - returns 410 Gone)
   ❌ POST /api/mt5/disconnect (old version - returns 410 Gone)
   ❌ GET /api/mt5/account (old version - returns 410 Gone)
   ❌ GET /api/mt5/health (old version - returns 410 Gone)
   
   These are deprecated - use the isolation endpoints instead


════════════════════════════════════════════════════════════════════════════════


📝 CODE EXAMPLES
================

JAVASCRIPT EXAMPLE:
─────────────────

// Step 1: Store credentials
const storeResponse = await fetch('http://localhost:5000/api/mt5/credentials/store', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mt5_login: '12345',
    mt5_password: 'password123',
    mt5_server: 'broker-demo.com'
  })
});

if (!storeResponse.ok) {
  console.error('Failed to store credentials');
  return;
}

// Step 2: Connect to MT5
const connectResponse = await fetch('http://localhost:5000/api/mt5/connect', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})  // Empty body
});

const data = await connectResponse.json();
if (data.success) {
  console.log('Connected to MT5:', data.account.login);
}

// Step 3: Get user's signals
const signalsResponse = await fetch('http://localhost:5000/api/mt5/signals', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const signals = await signalsResponse.json();
console.log('My signals:', signals.signals);


PYTHON EXAMPLE:
──────────────

import requests
import json

token = 'your_jwt_token_here'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Step 1: Store credentials
cred_data = {
    'mt5_login': '12345',
    'mt5_password': 'password123',
    'mt5_server': 'broker-demo.com'
}

response = requests.post(
    'http://localhost:5000/api/mt5/credentials/store',
    headers=headers,
    json=cred_data
)

if response.status_code == 200:
    print('Credentials stored')

# Step 2: Connect
response = requests.post(
    'http://localhost:5000/api/mt5/connect',
    headers=headers,
    json={}
)

data = response.json()
if data['success']:
    print(f"Connected to MT5: {data['account']['login']}")

# Step 3: Get signals
response = requests.get(
    'http://localhost:5000/api/mt5/signals',
    headers=headers
)

signals = response.json()
for signal in signals['signals']:
    print(f"{signal['symbol']} {signal['signal']}: {signal['confidence']}%")


════════════════════════════════════════════════════════════════════════════════


⚠️ COMMON ERRORS & SOLUTIONS
=============================

Error: "MT5 credentials not configured"
  Cause: Tried to connect without storing credentials first
  Solution: POST /api/mt5/credentials/store BEFORE /api/mt5/connect

Error: "Invalid credentials or server"
  Cause: Credentials don't match your MT5 account
  Solution: Verify login ID, password, and server name with your broker

Error: "410 Gone"
  Cause: Using old non-isolated endpoint
  Solution: Use the new /api/mt5/* endpoints from isolation routes

Error: "Not authenticated"
  Cause: Missing or invalid JWT token
  Solution: Login first to get valid JWT token

Error: "Unauthorized"
  Cause: Trying to access another user's data
  Solution: Your authenticated user_id must match the resource owner


════════════════════════════════════════════════════════════════════════════════


✅ VERIFICATION
===============

Verify Isolation is Working:

Open TWO browser tabs/windows:
  Tab 1: Login as User A
  Tab 2: Login as User B

User A:
  1. Enter MT5 login: 12345
  2. Enter MT5 password: pwd_A
  3. Enter server: broker1.com
  4. Click "Store & Connect"
  5. Dashboard shows: "Connected to Account 12345"
  6. Go to "My Signals" → See only User A's signals
  7. Go to "My Trades" → See only User A's trades

User B (in Tab 2):
  1. Enter MT5 login: 67890
  2. Enter MT5 password: pwd_B
  3. Enter server: broker2.com
  4. Click "Store & Connect"
  5. Dashboard shows: "Connected to Account 67890"  ← DIFFERENT account
  6. Go to "My Signals" → See only User B's signals (NOT User A's)
  7. Go to "My Trades" → See only User B's trades (NOT User A's)

✅ PASS: Each user has isolated credentials and data


════════════════════════════════════════════════════════════════════════════════


📞 SUPPORT
==========

For more information:
  - FIX_SUMMARY.md → Complete fix documentation
  - MT5_ISOLATION_FIX_COMPLETE.md → Technical details
  - MT5_BEFORE_AFTER_DIAGRAM.md → Visual comparison
  - backend/test_isolation_fix.py → Test examples


════════════════════════════════════════════════════════════════════════════════
