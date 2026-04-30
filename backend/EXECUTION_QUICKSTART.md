# 🚀 MT5 Execution Layer - Quick Start Guide

## Prerequisites

1. **MetaTrader 5 Terminal** installed and running
2. **Demo Account** created (via MT5 terminal)
3. **Python 3.8+** installed
4. **Backend API** running on your machine (http://localhost:5000)

---

## Installation

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs MetaTrader5 and all required packages.

### Step 2: Configure Environment

Create a `.env` file in the `backend/` directory:

```
MT5_ACCOUNT=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo
API_BASE_URL=http://localhost:5000
USER_ID=1
POLLING_INTERVAL=30
RISK_PER_TRADE=1.0
BOT_ENABLED=True
```

**How to find MT5 account info:**
1. Open MetaTrader 5
2. Go to **File → Account Information**
3. Copy your account number (login)
4. Use your login password

---

## Running the Execution Service

### Option 1: Direct Python (Recommended for Testing)

```bash
cd backend
python run_execution_service.py
```

### Option 2: Windows Batch Script

```bash
cd backend
run_execution_service.bat
```

### Option 3: Linux/Mac Script

```bash
cd backend
chmod +x run_execution_service.sh
./run_execution_service.sh
```

---

## What Happens on Startup

The service will:

1. ✓ Validate environment variables
2. ✓ Check Python dependencies
3. ✓ Verify MT5 terminal is running
4. ✓ Connect to MT5 with your credentials
5. ✓ Start listening for signals from the API
6. ✓ Begin monitoring for trading opportunities

---

## Expected Output

```
======================================================================
🚀 MT5 EXECUTION SERVICE STARTUP
======================================================================

[1/4] Validating environment...
✓ Environment validation passed

[2/4] Checking dependencies...
✓ MetaTrader5 package found
✓ requests package found
✓ All dependencies found

[3/4] Checking MT5 terminal...
✓ MT5 terminal is running and accessible

[4/4] Starting execution service...
======================================================================
✓ MT5 EXECUTION SERVICE RUNNING
======================================================================
Account: 1234567
Balance: $10,000.00 USD
Equity: $10,000.00 USD
Leverage: 100:1
Mode: demo
======================================================================
```

---

## Testing Signals

### Using curl to send a test signal:

```bash
curl -X POST http://localhost:5000/api/signals \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "price": 1.0850,
    "confidence": 0.85,
    "sl": 1.0820,
    "tp": 1.0900
  }'
```

The execution service will:
- Validate the signal
- Calculate position size based on risk
- Place the order on MT5
- Log all activities

---

## Monitoring

### Real-time Logs

The service logs everything to:
- **Console**: Real-time status messages
- **File**: `backend/execution/logs/execution.log`

### Trade Statistics

Access via API:

```bash
curl -X GET http://localhost:5000/api/execution/statistics
```

### Open Positions

```bash
curl -X GET http://localhost:5000/api/execution/positions
```

---

## Safety Features

### Kill Switch

Disable all trading without stopping the service:

```bash
# In .env file
BOT_ENABLED=False
```

Or via API:

```bash
curl -X POST http://localhost:5000/api/execution/bot/disable
```

### Risk Management

The service enforces:
- **Max Daily Loss**: Stops trading after 5% daily loss (configurable)
- **Max Positions**: Limits concurrent open positions to 5 (configurable)
- **Spread Filter**: Rejects trades if spread exceeds 3 pips
- **Position Sizing**: Automatically calculates lot size based on risk

---

## Troubleshooting

### Error: "MT5 terminal is not running!"

**Solution**: 
1. Open MetaTrader 5
2. Ensure you're logged into your account
3. Keep the MT5 window open while running the service

### Error: "Failed to connect to API"

**Solution**:
1. Make sure the backend API is running: `python backend/main.py`
2. Check that `API_BASE_URL` in `.env` is correct
3. Verify network connectivity

### Error: "Order failed: Insufficient margin"

**Solution**:
1. Check your account balance in MT5
2. Reduce `RISK_PER_TRADE` in `.env` (try 0.5%)
3. Reduce `MAX_OPEN_POSITIONS` to free up margin

### Error: "MT5 initialization failed"

**Solution**:
1. Reinstall MetaTrader5 package: `pip install --upgrade MetaTrader5`
2. Restart MT5 terminal
3. Try again

---

## Advanced Configuration

### Adjust Risk Per Trade

Edit `.env`:

```
RISK_PER_TRADE=1.5  # 1.5% per trade (more aggressive)
```

### Adjust Polling Interval

```
POLLING_INTERVAL=10  # Check for signals every 10 seconds (vs default 30)
```

### Adjust Max Daily Loss

```
MAX_DAILY_LOSS=3.0  # Stop trading after 3% daily loss (more conservative)
```

---

## Production Deployment

For 24/7 automated trading:

1. **Run on VPS or Local Machine**: The service must run continuously
2. **Use Process Manager**: Use `systemd`, `supervisor`, or `PM2`
3. **Enable Logging**: Configure log rotation to prevent disk overflow
4. **Monitor Health**: Set up alerts for service crashes
5. **Backup Configuration**: Keep `.env` file backed up

### Example: Using supervisor on Linux

Create `/etc/supervisor/conf.d/sofai-execution.conf`:

```ini
[program:sofai-execution]
command=/usr/bin/python3 /home/user/SofAi-Fx/backend/run_execution_service.py
directory=/home/user/SofAi-Fx/backend
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sofai-execution.log
```

Then:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sofai-execution
```

---

## Next Steps

1. ✅ Configure `.env` with your MT5 credentials
2. ✅ Start the execution service
3. ✅ Monitor logs to verify it's running
4. ✅ Test with a manual signal from the dashboard
5. ✅ Enable automated signal generation
6. ✅ Let it run and trade! 🚀

---

## Support

For issues or questions:
- Check `backend/execution/logs/execution.log` for error details
- Review the specification document for architecture details
- Test connections manually using provided test scripts
