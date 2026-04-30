# MT5 Account Data Integration - Implementation Guide

## 🎯 Overview

This implementation adds **live MetaTrader 5 account data** to the SofAi-Fx dashboard, displaying:

- 💳 **Balance & Equity**
- 📊 **Margin Information** (Used, Free, Level)
- ⚙️ **Leverage & Account Type** (Demo/Live)
- 🟢/🔴 **Connection Status**
- ⚠️ **Health Warnings & Alerts**
- 🔄 **Real-time Updates** (Every 5 seconds)

---

## 📁 Files Created/Modified

### Backend
1. **`backend/src/services/mt5_account.py`** - NEW
   - `MT5AccountService` class with 5 methods:
     - `get_account_info()` - Live account data
     - `get_account_summary()` - Dashboard metrics
     - `check_connection_status()` - Connection check
     - `get_positions_summary()` - Open positions
     - `get_account_health()` - Health metrics & warnings

2. **`backend/src/api/flask_app.py`** - MODIFIED
   - Added import: `from ..services.mt5_account import MT5AccountService`
   - Added 5 new API endpoints:
     - `GET /api/mt5/account` - Live account data
     - `GET /api/mt5/summary` - Account summary
     - `GET /api/mt5/status` - Connection status (no auth required)
     - `GET /api/mt5/positions` - Open positions
     - `GET /api/mt5/health` - Health status

### Frontend
1. **`frontend/assets/js/mt5-account.js`** - NEW
   - `MT5AccountManager` object with:
     - Auto-refresh every 5 seconds
     - Error handling
     - Real-time display updates
     - Health status parsing

2. **`frontend/index.html`** - MODIFIED
   - Added MT5 Account Overview section with:
     - Connection status indicator
     - Balance, Equity, Margin cards
     - Margin Level with visual bar
     - Leverage, Account Type, Account #, Server info
     - Health warnings/alerts
     - Auto-refresh button
   - Added script import: `<script src="assets/js/mt5-account.js" defer></script>`

---

## 🚀 Quick Start

### 1. **Verify Backend Installation**

```bash
# Check that MT5 is installed
cd backend
python -c "import MetaTrader5; print('✅ MetaTrader5 installed')"

# Check that the service can be imported
python -c "from src.services.mt5_account import MT5AccountService; print('✅ Service loaded')"
```

### 2. **Start the Backend API**

```bash
cd backend
python run_api.bat  # or: python -m src.api.flask_app
```

Expected output:
```
Database path: ...
Database URI: sqlite:///...
JWT Secret Key configured: ...
Starting SofAi FX API server...
Running on http://0.0.0.0:5000
```

### 3. **Open the Frontend**

```bash
# In another terminal
cd frontend
python serve.py  # Serves on http://localhost:8080
```

Then open: **http://localhost:8080** in your browser

### 4. **Connect Your MT5 Account**

The system will:
1. **Automatically detect** if MT5 terminal is running
2. **Fetch account info** if connected
3. **Display live data** in the dashboard
4. **Refresh every 5 seconds** automatically

---

## 📊 API Endpoints

### Get Account Info
```
GET /api/mt5/account
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "success": true,
  "data": {
    "connected": true,
    "balance": 10000.50,
    "equity": 10500.75,
    "margin": 2000.00,
    "free_margin": 8500.75,
    "margin_level": 525.0,
    "leverage": 100,
    "currency": "USD",
    "login": 123456,
    "server": "ICMarkets-Demo",
    "trade_mode": "demo",
    "profit_loss": 500.25,
    "timestamp": "2024-04-26T10:30:45.123456"
  }
}
```

### Get Account Summary (Dashboard)
```
GET /api/mt5/summary
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "success": true,
  "data": {
    "status": "connected",
    "account_number": 123456,
    "balance": 10000.50,
    "equity": 10500.75,
    "profit_loss": 500.25,
    "profit_loss_pct": 5.0,
    "margin": 2000.00,
    "free_margin": 8500.75,
    "margin_level": 525.0,
    "margin_percentage": 19.05,
    "leverage": 100,
    "currency": "USD"
  }
}
```

### Check Connection Status
```
GET /api/mt5/status

Response:
{
  "success": true,
  "data": {
    "connected": true,
    "message": "MT5 terminal connected",
    "build": 3737,
    "timestamp": "2024-04-26T10:30:45.123456"
  }
}
```

### Get Positions
```
GET /api/mt5/positions
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "success": true,
  "data": {
    "connected": true,
    "positions": [
      {
        "ticket": 123456,
        "symbol": "EURUSD",
        "type": "BUY",
        "volume": 0.1,
        "price_open": 1.0850,
        "sl": 1.0800,
        "tp": 1.0900,
        "profit": 25.50,
        "time_open": "2024-04-26T09:30:00"
      }
    ],
    "total_positions": 1,
    "total_profit": 25.50
  }
}
```

### Get Account Health
```
GET /api/mt5/health
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "success": true,
  "data": {
    "status": "connected",
    "health_score": 100,
    "margin_level": 525.0,
    "free_margin": 8500.75,
    "account_type": "demo",
    "warnings": ["Demo account - not trading with real money"],
    "is_demo": true
  }
}
```

---

## 🧪 Testing the Integration

### 1. **Test Backend Endpoints**

```bash
# From any terminal with curl:

# Test connection status (no auth required)
curl http://localhost:5000/api/mt5/status

# Test with auth (replace YOUR_TOKEN)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/mt5/account

# Test health status
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/mt5/health
```

### 2. **Test Frontend Dashboard**

1. Login to the dashboard
2. Scroll down to **"MT5 Account Overview"** section
3. Verify:
   - ✅ Connection status shows 🟢 Connected or 🔴 Disconnected
   - ✅ Balance, Equity, Margin update correctly
   - ✅ Margin Level shows appropriate color (green/yellow/red)
   - ✅ Account type shows DEMO or LIVE
   - ✅ Data refreshes every 5 seconds (timestamp updates)
   - ✅ Warnings appear for low margin levels

### 3. **Test Auto-Refresh**

1. Check the timestamp in the MT5 section
2. Wait 5-10 seconds
3. Verify timestamp updates automatically
4. Click "Refresh" button - should update immediately

### 4. **Test Error Handling**

Simulate MT5 disconnection:
1. **Close MT5 Terminal** while dashboard is open
2. Verify:
   - ✅ Connection status changes to 🔴 Disconnected
   - ✅ All values show "--"
   - ✅ Warning shows "MT5 terminal not connected"
3. **Reopen MT5 Terminal**
4. Verify:
   - ✅ Dashboard reconnects automatically after ~5 seconds
   - ✅ Live data reappears

---

## ⚙️ Configuration

### Refresh Rate
In `frontend/assets/js/mt5-account.js`:
```javascript
refreshRate: 5000, // 5 seconds (change to 3000 for 3 seconds, etc.)
```

### Auto-Refresh Control
```javascript
// In browser console:
MT5AccountManager.stopAutoRefresh();  // Stop auto-refresh
MT5AccountManager.startAutoRefresh(); // Start auto-refresh
MT5AccountManager.refreshRate = 3000; // Change to 3 seconds
```

---

## 🚨 Troubleshooting

### MT5 shows "Not Connected"

**Cause**: MT5 terminal is not running or not initialized
```bash
# Solution:
1. Open MT5 terminal
2. Log in with your account
3. Wait for dashboard to auto-refresh (5 seconds)
4. Or click "Refresh" button manually
```

### API returns 401 Unauthorized

**Cause**: JWT token expired or invalid
```bash
# Solution:
1. Logout and login again
2. Check browser console for auth errors
3. Ensure token is being sent in Authorization header
```

### Margin Level shows "--"

**Cause**: MT5 account_info() failed
```bash
# Solution:
1. Check MT5 terminal logs
2. Verify account has sufficient permissions
3. Try restarting MT5 terminal
```

### Dashboard not showing MT5 section

**Cause**: mt5-account.js not loaded
```bash
# Solution:
1. Check browser console (F12 → Console tab)
2. Look for "Initializing MT5 Account Manager"
3. Check if script tag is in HTML: <script src="assets/js/mt5-account.js"></script>
```

---

## 📈 Features Included

### ✅ Implemented
- Live balance & equity display
- Margin tracking with visual bar
- Margin level warnings (critical/warning/caution)
- Real-time auto-refresh (5 seconds)
- Connection status indicator
- Account type detection (Demo/Live)
- Health scoring & warnings
- Error handling & fallbacks

### 🚀 Future Enhancements
- WebSocket for real-time updates (currently polling)
- Historical equity chart
- Daily P/L tracking
- Position management UI
- Trade history display
- Drawdown percentage
- Win/loss ratio

---

## 🔐 Security Notes

1. **JWT Required**: Most endpoints require valid JWT token
2. **User Isolation**: Data is per-user (filtered by user_id from JWT)
3. **Status Endpoint**: Connection status doesn't require auth (health check)
4. **CORS Enabled**: Frontend can call API from different port

---

## 📝 Code Examples

### Using MT5AccountManager in JavaScript

```javascript
// Start monitoring
MT5AccountManager.init();

// Manually refresh
await MT5AccountManager.manualRefresh();

// Stop auto-refresh temporarily
MT5AccountManager.stopAutoRefresh();

// Resume auto-refresh
MT5AccountManager.startAutoRefresh();

// Change refresh rate to 3 seconds
MT5AccountManager.refreshRate = 3000;
MT5AccountManager.startAutoRefresh();

// Load health status
MT5AccountManager.loadHealthStatus();
```

### Using MT5AccountService in Python

```python
from src.services.mt5_account import MT5AccountService

# Get live account info
account = MT5AccountService.get_account_info()
print(f"Balance: {account['balance']}")
print(f"Equity: {account['equity']}")
print(f"Margin Level: {account['margin_level']}%")

# Get summary
summary = MT5AccountService.get_account_summary()
print(f"Account Type: {summary['account_type']}")

# Check connection
status = MT5AccountService.check_connection_status()
print(f"Connected: {status['connected']}")

# Get health
health = MT5AccountService.get_account_health()
print(f"Health Score: {health['health_score']}")
for warning in health['warnings']:
    print(f"⚠️ {warning}")
```

---

## 📊 What You Now Have

### Backend
- ✅ Complete MT5 account service
- ✅ 5 API endpoints for account data
- ✅ Error handling & connection checking
- ✅ Real-time data retrieval

### Frontend
- ✅ Beautiful MT5 Account Overview card
- ✅ Real-time display of account metrics
- ✅ Auto-refresh every 5 seconds
- ✅ Health warnings system
- ✅ Responsive grid layout
- ✅ Connection status indicator

### Integration
- ✅ Automatic initialization
- ✅ JWT authentication
- ✅ Error handling
- ✅ User-friendly display

---

## 🎉 Result

Your dashboard now shows:
- **Live Balance**: Updates every 5 seconds
- **Equity**: Real-time profit/loss tracking
- **Margin**: Visual representation of margin usage
- **Connection Status**: Instant connection feedback
- **Account Health**: Warnings for risky margin levels
- **Account Details**: Leverage, type, server info

This transforms SofAi into a **complete AI trading system + live broker dashboard**.

---

## 📞 Support

For issues:
1. Check browser console (F12)
2. Check server logs (`backend/logs/` directory)
3. Verify MT5 terminal is running
4. Ensure proper JWT token
5. Check API responses with curl

---

**Version**: 1.0  
**Last Updated**: 2024-04-26  
**Status**: ✅ Production Ready
