# 🚀 MT5 Execution Layer - Setup & Configuration Guide

## Overview

This guide covers the complete setup process for the MT5 Execution Layer - the automated trading system that connects to MetaTrader 5 and executes trades based on signals from the SofAi FX backend.

---

## 🎯 Prerequisites

### System Requirements
- **MetaTrader 5 Terminal**: Installed and running on your local machine or VPS
- **Python 3.8+**: For the execution service
- **Internet Connection**: For API communication and MT5 connection

### Required Accounts
1. **MetaTrader 5 Account**: Demo or live (we recommend starting with demo)
   - Account number
   - Password
   - Server name (e.g., "ICMarkets-Demo")

2. **SofAi FX Backend Access**:
   - Backend API running (e.g., http://localhost:5000)
   - User account with JWT authentication

---

## 📦 Installation

### Step 1: Install MetaTrader5 Python Package

```bash
pip install MetaTrader5
```

Verify installation:
```bash
python -c "import MetaTrader5; print(MetaTrader5.__version__)"
```

### Step 2: Ensure MT5 Terminal is Running

The execution service requires MetaTrader 5 terminal to be **running at all times**:

1. **Open MetaTrader 5 Desktop Terminal**
2. **Login** with your account credentials
3. **Verify Connection**: 
   - Terminal should show "Connected" status
   - You should see account equity and balance

### Step 3: Install Additional Dependencies

The execution service requires these additional packages:
```bash
pip install requests Flask-SQLAlchemy
```

---

## ⚙️ Configuration

### Configuration File

Create a file `backend/execution/config.py`:

```python
"""
MT5 Execution Service Configuration
"""

# ===== MT5 CREDENTIALS =====
MT5_ACCOUNT = 1234567  # Your MT5 account number
MT5_PASSWORD = "your_password"  # Your MT5 password
MT5_SERVER = "ICMarkets-Demo"  # Server name (change for live trading)

# ===== API CONFIGURATION =====
API_BASE_URL = "http://localhost:5000"  # Backend API URL
USER_ID = 1  # Your user ID in the SofAi system

# ===== EXECUTION SETTINGS =====
POLLING_INTERVAL = 30  # Check for signals every N seconds
MAX_OPEN_POSITIONS = 5  # Maximum simultaneous positions
RISK_PER_TRADE = 1.0  # Risk percentage per trade (1-2% recommended)
MAX_DAILY_LOSS = 5.0  # Maximum daily loss percentage before stopping
MIN_SPREAD_THRESHOLD = 3.0  # Maximum acceptable spread in pips

# ===== LOGGING =====
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_DIR = "backend/execution/logs"

# ===== SAFETY =====
BOT_ENABLED = True  # Master kill switch (can be toggled via API)
CLOSE_POSITIONS_ON_STOP = False  # Close positions when service stops
```

### Update with Your Details

Edit the config file and replace:
- `MT5_ACCOUNT`: Your actual MT5 account number
- `MT5_PASSWORD`: Your actual MT5 password
- `MT5_SERVER`: Your broker's server name
- `API_BASE_URL`: Your backend API URL
- `USER_ID`: Your user ID

---

## 🚀 Running the Service

### Method 1: Direct Python Execution

```bash
cd backend
python -m execution.service
```

### Method 2: With Configuration

Create a startup script `start_execution.py`:

```python
#!/usr/bin/env python3
"""
Start the MT5 Execution Service
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import configuration
from execution.config import (
    MT5_ACCOUNT, MT5_PASSWORD, MT5_SERVER,
    API_BASE_URL, USER_ID, POLLING_INTERVAL
)

# Import and run service
from execution.service import ExecutionService

def main():
    """Start the execution service"""
    service = ExecutionService(
        mt5_account=MT5_ACCOUNT,
        mt5_password=MT5_PASSWORD,
        mt5_server=MT5_SERVER,
        api_base_url=API_BASE_URL,
        user_id=USER_ID,
        polling_interval=POLLING_INTERVAL
    )
    
    try:
        service.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        service.stop()

if __name__ == '__main__':
    main()
```

Run it:
```bash
python start_execution.py
```

---

## 🧪 Testing the Service

### Test 1: Verify MT5 Connection

```python
from execution.mt5.connection import get_mt5_connection

# Connect
mt5 = get_mt5_connection(
    account=1234567,
    password="password",
    server="ICMarkets-Demo"
)

if mt5:
    print("✓ MT5 connected successfully")
    info = mt5.get_account_info()
    print(f"Account: {info['login']}")
    print(f"Balance: ${info['balance']}")
    mt5.disconnect()
else:
    print("✗ Failed to connect to MT5")
```

### Test 2: Verify API Connection

```python
from execution.engines.signal_listener import create_signal_listener

listener = create_signal_listener(
    api_base_url="http://localhost:5000",
    user_id=1,
    polling_interval=10
)

# Test one poll
signals = listener.fetch_latest_signals()
print(f"Fetched {len(signals)} signals")
```

### Test 3: Test Position Sizing

```python
from execution.engines.position_sizer import PositionSizer

sizer = PositionSizer(account_balance=10000, leverage=100)

lot_size = sizer.calculate_lot_size(
    symbol="EURUSD",
    entry_price=1.0850,
    stop_loss_price=1.0800,
    risk_percent=1.0
)

print(f"Calculated lot size: {lot_size:.2f}")
```

---

## 📊 Monitoring & Logs

### Log Files

Logs are saved to `backend/execution/logs/`:
- `execution_service.log` - Main service logs
- `execution.log` - Detailed execution events
- `trades.json` - Trade records
- `errors.json` - Error logs

### View Real-time Logs

```bash
# Watch logs (Linux/Mac)
tail -f backend/execution/logs/execution_service.log

# Watch logs (Windows PowerShell)
Get-Content backend/execution/logs/execution_service.log -Wait
```

### API Endpoints for Monitoring

All endpoints require JWT authentication:

```bash
# Get open trades
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/api/execution/trades?status=OPEN

# Get trade statistics
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/api/execution/trades/statistics?days=7

# Get execution logs
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/api/execution/logs

# Get current execution status
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/api/execution/status

# Get daily report
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/api/execution/daily-report
```

---

## 🛡️ Safety Features

### Kill Switch

The service has a kill switch that can be toggled to stop execution:

```bash
# Get current kill switch status
curl -H "Authorization: Bearer {token}" \
  http://localhost:5000/api/execution/kill-switch

# Disable bot
curl -X POST -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' \
  http://localhost:5000/api/execution/kill-switch
```

### Risk Controls

The service enforces:
1. **Max Open Positions**: Prevents over-exposure
2. **Daily Loss Limit**: Stops trading if daily loss exceeds threshold
3. **Spread Filter**: Rejects trades if spread is too wide
4. **Margin Check**: Ensures sufficient margin for each trade
5. **Risk Per Trade**: Limits risk to configured percentage

---

## 🐛 Troubleshooting

### Issue: "MT5 initialization failed"

**Cause**: MT5 terminal not running or not installed

**Solution**:
1. Open MetaTrader 5 desktop terminal
2. Verify you're logged in
3. Check that terminal shows "Connected" status
4. Restart the execution service

### Issue: "Login failed"

**Cause**: Incorrect credentials or server name

**Solution**:
1. Verify account number in MT5 terminal
2. Check password is correct
3. Verify server name (visible in MT5 terminal title bar)
4. Try logging in to MT5 terminal directly to confirm

### Issue: "Failed to fetch signals"

**Cause**: Backend API not running or URL incorrect

**Solution**:
1. Verify backend API is running: `python backend/main.py`
2. Check API_BASE_URL in configuration
3. Verify network connectivity
4. Check firewall settings

### Issue: "Insufficient margin"

**Cause**: Account balance too low for position size

**Solution**:
1. Increase account balance (demo account)
2. Reduce RISK_PER_TRADE setting
3. Wait for positions to close

### Issue: "Symbol not found"

**Cause**: Currency pair not available on broker

**Solution**:
1. Check symbol is available in MT5 Market Watch
2. Use correct symbol format (e.g., EURUSD not EUR/USD)
3. Verify broker supports the pair

---

## 📈 Performance Optimization

### Tips for Better Performance

1. **Reduce Polling Interval**: Faster signal processing (trade-off: more CPU/bandwidth)
   ```python
   POLLING_INTERVAL = 10  # Check every 10 seconds instead of 30
   ```

2. **Optimize Position Sizing**: Use appropriate risk percentages
   ```python
   RISK_PER_TRADE = 1.0  # Start conservative, adjust based on results
   ```

3. **Use VPS for 24/7 Trading**: Run service on VPS for consistent operation
   - Reliable uptime
   - Fast network connection
   - No local computer shutdown concerns

4. **Monitor Resource Usage**: Check CPU and memory
   ```bash
   # Windows
   tasklist /fi "name:python*"
   
   # Linux
   ps aux | grep python
   ```

---

## 📋 Deployment Checklist

- [ ] MetaTrader 5 installed and running
- [ ] MT5 account created (demo or live)
- [ ] MetaTrader5 Python package installed
- [ ] Backend API running and accessible
- [ ] Configuration file created with correct credentials
- [ ] Execution service starts without errors
- [ ] Can connect to MT5 successfully
- [ ] Can fetch signals from API
- [ ] Kill switch works
- [ ] Kill switch disabled (ready for trading)
- [ ] Logs are being written
- [ ] API endpoints responding correctly
- [ ] Monitoring dashboard working

---

## 🔒 Security Best Practices

1. **Never commit credentials to Git**:
   ```bash
   echo "backend/execution/config.py" >> .gitignore
   ```

2. **Use environment variables** for sensitive data:
   ```python
   import os
   MT5_ACCOUNT = int(os.getenv('MT5_ACCOUNT', 0))
   MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
   ```

3. **Restrict access** to execution service logs
   ```bash
   chmod 700 backend/execution/logs
   ```

4. **Use HTTPS** for API communication in production
   ```python
   API_BASE_URL = "https://api.sofai.com"  # Use HTTPS in production
   ```

5. **Rotate MT5 password** regularly

---

## 📞 Support & Documentation

- **Logs**: Check `backend/execution/logs/` for detailed logs
- **API Docs**: See `/api/execution/` endpoints documentation
- **Database**: View trades in `sofai_fx.db` via SQLite browser
- **MT5 Documentation**: https://www.mql5.com/en/docs/integration/python_metatrader5

---

## 🎓 Next Steps

1. **[Deploy to VPS](./DEPLOYMENT_VPS.md)**: Run 24/7 trading
2. **[Advanced Configuration](./ADVANCED_CONFIG.md)**: Multi-user, custom strategies
3. **[Performance Tuning](./PERFORMANCE_TUNING.md)**: Optimize for your setup
4. **[Monitoring Dashboard](./MONITORING.md)**: Real-time trading dashboard

---

**Last Updated**: April 26, 2026
