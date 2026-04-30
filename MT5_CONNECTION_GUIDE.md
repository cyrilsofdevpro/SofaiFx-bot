# MT5 Account Connection via SofAi Dashboard

## 🎯 Overview

This feature allows users to securely connect their MetaTrader 5 accounts through the SofAi dashboard. The connection is handled **server-side** with encrypted credential storage.

### Key Concept
```
User enters MT5 credentials → Backend connects to MT5 → Live trading enabled
NOT: User logs into MT5 in browser
```

---

## 🏗️ Architecture

### User Flow
1. User logs into SofAi dashboard (separate from MT5)
2. User navigates to "MT5 Account Connection" section
3. User enters:
   - MT5 Login ID
   - MT5 Password
   - MT5 Server (dropdown selection)
4. Clicks "Connect Account"
5. Backend validates and connects
6. Dashboard shows:
   - 🟢 Connected with account details
   - Or 🔴 Failed with error message

### Security Model
```
├── Frontend (Browser)
│   └── User enters credentials
│       └── Sends to backend (HTTPS)
│
├── Backend (Python/Flask)
│   ├── Receives credentials
│   ├── Encrypts credentials (Fernet)
│   ├── Stores encrypted in database
│   ├── Connects to MT5
│   └── Never returns plaintext credentials
│
└── MT5 Terminal (Server-side)
    └── Only backend connects (per-user session)
```

---

## 📁 Files Created/Modified

### Backend Files

1. **[backend/src/models.py](backend/src/models.py)** - MODIFIED
   - Added MT5 connection fields to User model:
     - `mt5_login` (encrypted)
     - `mt5_password` (encrypted)
     - `mt5_server`
     - `mt5_connected` (boolean)
     - `mt5_connection_time`
     - `mt5_account_number`

2. **[backend/src/services/credential_manager.py](backend/src/services/credential_manager.py)** - NEW
   - `CredentialEncryptor` class (Fernet encryption)
   - `MT5CredentialManager` class (store/retrieve/clear credentials)
   - Symmetric encryption with master key

3. **[backend/src/services/mt5_connection.py](backend/src/services/mt5_connection.py)** - NEW
   - `MT5ConnectionManager` class (per-user MT5 sessions)
   - Methods:
     - `connect_user()` - Connect to MT5
     - `disconnect_user()` - Disconnect from MT5
     - `is_user_connected()` - Check connection
     - `get_user_session_info()` - Get session details
     - `validate_credentials()` - Validate without storing

4. **[backend/src/config.py](backend/src/config.py)** - MODIFIED
   - Added `ENCRYPTION_MASTER_KEY` config variable

5. **[backend/src/api/flask_app.py](backend/src/api/flask_app.py)** - MODIFIED
   - Imported new services
   - Initialized credential managers
   - Added 4 new API endpoints:
     - `POST /api/mt5/connect` - Connect account
     - `POST /api/mt5/disconnect` - Disconnect account
     - `GET /api/mt5/connection-status` - Check status
     - `GET /api/mt5/servers` - List available servers

### Frontend Files

1. **[frontend/index.html](frontend/index.html)** - MODIFIED
   - Added MT5 Connection form section with:
     - Login ID input
     - Password input
     - Server dropdown
     - Connect/Disconnect buttons
     - Status indicator
     - Account info display

2. **[frontend/assets/js/mt5-connection.js](frontend/assets/js/mt5-connection.js)** - NEW
   - `MT5ConnectionManager` object
   - Methods:
     - `connect()` - Initiate connection
     - `disconnect()` - Disconnect account
     - `checkConnectionStatus()` - Verify connection
     - `displayAccountInfo()` - Show account details
     - `updateUI()` - Update form state

3. **[frontend/assets/css/mt5-connection.css](frontend/assets/css/mt5-connection.css)** - NEW
   - Styling for connection form
   - Status indicator styles
   - Account info cards
   - Notifications
   - Responsive design

---

## 🚀 Quick Start

### Step 1: Environment Setup

Add to `.env` file:
```env
ENCRYPTION_MASTER_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-here-change-in-production
```

### Step 2: Database Migration

The User model now has new columns. Run:
```bash
cd backend
# If using migrations (if set up):
flask db upgrade

# Or manually:
# The database will auto-create columns on next run
python -m src.api.flask_app
```

### Step 3: Start Services

```bash
# Terminal 1: Start Backend
cd backend
python run_api.bat
# or: python -m src.api.flask_app

# Terminal 2: Start Frontend
cd frontend
python serve.py
```

### Step 4: Connect MT5 Account

1. Open dashboard: http://localhost:8080
2. Login with your SofAi account
3. Scroll to "MT5 Account Connection" section
4. Enter your MT5 credentials:
   - Login ID: (e.g., 123456)
   - Password: (your MT5 password)
   - Server: (select from dropdown)
5. Click "Connect Account"
6. Wait for connection...
7. If successful: 🟢 Connected (account details shown)
8. If failed: 🔴 Failed (error message shown)

---

## 📊 API Endpoints

### Connect MT5 Account
```
POST /api/mt5/connect
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

Request body:
{
  "login": "123456",
  "password": "password",
  "server": "JustMarkets-Demo"
}

Response (Success):
{
  "success": true,
  "message": "MT5 account connected successfully",
  "account": {
    "login": 123456,
    "balance": 10000.50,
    "equity": 10500.75,
    "margin": 2000.00,
    "free_margin": 8500.75,
    "margin_level": 525.0,
    "currency": "USD",
    "leverage": 100,
    "trade_mode": "demo"
  }
}

Response (Failure):
{
  "success": false,
  "error": "MT5 login failed",
  "details": "Invalid credentials or server. Invalid login or password"
}
```

### Disconnect MT5 Account
```
POST /api/mt5/disconnect
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "success": true,
  "message": "MT5 account disconnected"
}
```

### Check Connection Status
```
GET /api/mt5/connection-status
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "success": true,
  "user_id": 1,
  "connected": true,
  "mt5_connected_db": true,
  "account_number": "123456",
  "connection_time": "2024-04-26T10:30:45.123456",
  "session_info": {
    "connected_since": "2024-04-26T10:30:45.123456",
    "login_id": "123456",
    "server": "JustMarkets-Demo"
  }
}
```

### Get Available Servers
```
GET /api/mt5/servers

Response:
{
  "success": true,
  "servers": [
    {"name": "JustMarkets-Demo", "type": "Demo"},
    {"name": "JustMarkets-Real", "type": "Live"},
    {"name": "ICMarkets-Demo", "type": "Demo"},
    {"name": "ICMarkets-Real", "type": "Live"},
    ...
  ]
}
```

---

## 🔐 Security Details

### Encryption
- **Method**: Fernet (symmetric encryption from cryptography library)
- **Key Derivation**: PBKDF2 with SHA256
- **Iterations**: 100,000
- **Master Key**: From `ENCRYPTION_MASTER_KEY` config

### Storage
```
User table:
├── mt5_login: "gAAAAABkU7s8nKj..." (encrypted)
├── mt5_password: "gAAAAABkU7s8mFx..." (encrypted)
├── mt5_server: "JustMarkets-Demo" (plaintext, OK)
├── mt5_connected: true/false
├── mt5_connection_time: timestamp
└── mt5_account_number: "123456" (plaintext, safe)
```

### What's NOT Stored
- ❌ Plaintext passwords (never stored)
- ❌ Plaintext login IDs (encrypted)
- ❌ Credentials in logs
- ❌ Credentials in responses

### Backend Behavior
```
Session Storage:
_user_mt5_sessions = {
    user_id: {
        'login': '123456',
        'server': 'JustMarkets-Demo',
        'connected_at': datetime,
        'account_number': 123456
    }
}

Per-User Isolation:
- Each user gets ONE MT5 connection
- Global MT5Lock prevents race conditions
- Credentials only in memory during active session
```

---

## 🧪 Testing

### Test Script: [test_mt5_connection.py](test_mt5_connection.py)

```bash
python test_mt5_connection.py
```

This tests:
1. ✅ Backend connectivity
2. ✅ User authentication
3. ✅ Credential encryption/decryption
4. ✅ MT5 connection success/failure
5. ✅ Credential storage
6. ✅ Connection status check
7. ✅ Disconnection
8. ✅ Error handling

### Manual Testing

#### Test 1: Valid Credentials
```
1. Use real MT5 account credentials
2. Select correct server
3. Verify: 🟢 Connected shown
4. Verify: Account details displayed
```

#### Test 2: Invalid Credentials
```
1. Use wrong password
2. Verify: 🔴 Failed shown
3. Verify: Error message explains issue
4. Verify: Form remains accessible
```

#### Test 3: Disconnect
```
1. Connect successfully
2. Click "Disconnect"
3. Confirm action
4. Verify: 🔴 Not Connected shown
5. Verify: Form becomes visible again
```

#### Test 4: Persistence
```
1. Connect MT5 account
2. Close browser tab
3. Reopen dashboard
4. Verify: Connection status remembered
5. Verify: Form is hidden (still connected)
```

#### Test 5: Multiple Users
```
1. User A logs in, connects MT5 account A
2. User B logs in, connects MT5 account B
3. Verify: Each user sees only their own connection
4. Verify: No credential leakage between users
```

---

## ⚙️ Configuration

### Encryption Master Key
**Important**: Change in production!

In `.env`:
```env
ENCRYPTION_MASTER_KEY=your-very-long-random-key-here-minimum-32-chars
```

Generate secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### JWT Secret
```env
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
```

---

## 🚨 Troubleshooting

### "MT5 initialization failed"
**Cause**: MT5 terminal not running  
**Solution**: 
1. Open MetaTrader 5 terminal
2. Wait for it to fully load
3. Try connecting again

### "MT5 login failed - Invalid login or password"
**Cause**: Wrong credentials or server  
**Solution**:
1. Verify credentials in MT5 terminal
2. Check server name spelling
3. Ensure server is available in MT5

### "MT5 connection works but credentials not stored"
**Cause**: Database or encryption error  
**Solution**:
1. Check database logs
2. Verify ENCRYPTION_MASTER_KEY is set
3. Restart backend

### Credentials work in MT5 but not in form
**Cause**: Encoding issue  
**Solution**:
1. Ensure no leading/trailing spaces
2. Try copy-pasting credentials again
3. Check for special characters

### Connection disappears after refresh
**Cause**: Session lost (normal)  
**Solution**:
1. Connection is stored in DB
2. Dashboard shows status from DB
3. Reconnect if needed, or clear credentials

---

## 📈 User Experience Flow

### Happy Path
```
┌─────────────────┐
│ User opens form │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Enters creds    │
└────────┬────────┘
         │
         ▼
┌──────────────────┐     ┌───────────┐
│ Clicks Connect   │────▶│ 🟡 Loading│
└──────────────────┘     └───────────┘
         │                     │
         └─────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
    ┌──────────┐      ┌──────────┐
    │ 🟢 Success│     │ 🔴 Failed │
    │ Show Creds│     │ Show Error│
    └──────────┘     └──────────┘
         │                  │
         ▼                  ▼
    ┌──────────┐      ┌──────────┐
    │Hide Form │      │Show Form │
    │Show Disc │      │Try Again │
    └──────────┘     └──────────┘
```

### Features After Connection
- ✅ MT5 Account Overview displays live data
- ✅ Automated trading can be enabled
- ✅ Balance/Equity updates every 5 seconds
- ✅ One-click disconnect
- ✅ Auto-reconnect on page refresh

---

## 🎯 Next Steps

### Phase 1: Manual Trading (Future)
- One-click place/close trades
- Trade history display
- Position management

### Phase 2: Automated Trading (Future)
- AI-generated signals execute automatically
- Risk management rules enforced
- Daily P/L tracking

### Phase 3: Portfolio Management (Future)
- Multi-account support
- Account comparison
- Performance analytics

---

## 📞 Support

For issues:
1. Check browser console (F12)
2. Check server logs (`backend/logs/`)
3. Verify MT5 terminal is running
4. Confirm encryption key is set
5. Check database for corruption

---

## 🔑 Key Features

✅ **Secure**: Credentials encrypted with Fernet  
✅ **User-Isolated**: Each user has one connection  
✅ **Persistent**: Credentials stored in DB  
✅ **Thread-Safe**: MT5 global lock prevents races  
✅ **Error-Handled**: Graceful failure messages  
✅ **UI-Responsive**: Real-time status updates  
✅ **Production-Ready**: All security best practices  

---

**Version**: 1.0  
**Status**: ✅ Ready for Production  
**Last Updated**: 2024-04-26
