# 🚀 MT5 Execution Layer - Complete Implementation Guide

## Overview

The MT5 Execution Layer adds **automated trade execution** to the SofAi FX Bot. It connects to MetaTrader 5, receives trading signals from the backend API, validates them, and executes trades with strict risk management.

---

## 📁 Project Structure

```
backend/
├── execution/                    # Main execution layer
│   ├── __init__.py
│   ├── service.py               # Main execution service (orchestrator)
│   ├── config.py                # Configuration template
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── SETUP_GUIDE.md
│   │
│   ├── engines/                 # Core execution engines
│   │   ├── __init__.py
│   │   ├── validator.py         # Pre-execution validation
│   │   ├── position_sizer.py    # Risk-based lot calculation
│   │   ├── executor.py          # Order placement & management
│   │   ├── signal_listener.py   # Signal polling from API
│   │   ├── trade_manager.py     # Trade lifecycle management
│   │   └── logger.py            # Event & trade logging
│   │
│   └── mt5/                     # MT5 Terminal Connection
│       ├── __init__.py
│       └── connection.py        # MT5 connection manager
│
├── src/
│   ├── models.py                # Updated with Trade & ExecutionLog
│   ├── api/
│   │   ├── execution.py         # Execution API endpoints
│   │   ├── flask_app.py         # Flask app with execution_bp registered
│   │   ├── auth.py
│   │   └── admin.py
│   └── ...
│
├── run_execution_service.py     # Main entry point (Python)
├── run_execution_service.bat    # Windows batch runner
├── run_execution_service.sh     # Linux/Mac bash runner
├── test_execution_components.py # Component tests
├── EXECUTION_QUICKSTART.md      # Quick start guide
├── requirements.txt             # Updated with MetaTrader5
└── .env.example                 # Configuration template
```

---

## ✅ Installation Checklist

- [x] **Database Models**: Trade, ExecutionLog, UserPreference models added to src/models.py
- [x] **MT5 Connection**: Connection manager with authentication
- [x] **Execution Engines**: All 7 engines implemented
  - [x] Signal Listener (polls API for signals)
  - [x] Trade Validator (pre-execution checks)
  - [x] Position Sizer (risk-based lot calculation)
  - [x] Order Executor (places orders on MT5)
  - [x] Trade Manager (tracks trade lifecycle)
  - [x] Execution Logger (logs all events)
  - [x] MT5 Connection (manages terminal connection)
- [x] **Execution Service**: Main orchestrator combining all engines
- [x] **API Endpoints**: RESTful endpoints for trade management
- [x] **Configuration**: .env template and config system
- [x] **Runner Scripts**: Python, Windows batch, Linux/Mac bash
- [x] **Documentation**: Setup guide and quick start
- [x] **Testing**: Component test script
- [x] **Requirements**: MetaTrader5 package added

---

## 🔧 Key Components Explained

### 1. **Signal Listener** (`engines/signal_listener.py`)
- Polls the API for new trading signals at configurable intervals (default: 30s)
- Maintains a queue of signals to process
- Validates signal format before queuing
- Provides statistics and monitoring

```python
listener = SignalListener(
    api_base_url="http://localhost:5000",
    user_id=1,
    polling_interval=30
)
signals = listener.fetch_latest_signals()
```

### 2. **Trade Validator** (`engines/validator.py`)
- Performs 8 comprehensive pre-execution checks:
  1. Bot enabled (kill switch)
  2. Signal format validation
  3. Symbol validity
  4. Spread within threshold
  5. No duplicate position on same pair
  6. Max open positions not exceeded
  7. Daily loss limit not breached
  8. Sufficient margin available

```python
validator = TradeValidator()
is_valid, reason = validator.validate_signal(
    signal, symbol_info, open_positions,
    account_info, today_pnl, bot_enabled=True
)
```

### 3. **Position Sizer** (`engines/position_sizer.py`)
- Calculates lot size based on risk management formula
- Formula: `lot_size = (balance * risk%) / (SL_pips * pip_value)`
- Prevents overleveraging
- Supports configurable rounding strategies

```python
sizer = PositionSizer(account_balance=10000, leverage=100)
lot_size = sizer.calculate_lot_size(
    symbol="EURUSD",
    entry_price=1.0850,
    stop_loss_price=1.0800,
    risk_percent=1.0  # 1% risk per trade
)
```

### 4. **Order Executor** (`engines/executor.py`)
- Places market orders on MT5
- Modifies SL/TP on existing positions
- Closes positions (full or partial)
- Handles order failures and retry logic

```python
executor = OrderExecutor(mt5_connection)
success, order_info = executor.place_market_order(
    symbol="EURUSD",
    order_type="BUY",
    volume=0.1,
    entry_price=1.0850,
    stop_loss=1.0800,
    take_profit=1.0900
)
```

### 5. **Trade Manager** (`engines/trade_manager.py`)
- Creates trade records in database
- Tracks trade lifecycle (PENDING → OPEN → CLOSED)
- Updates P&L when trades close
- Provides trade history and statistics

### 6. **Execution Logger** (`engines/logger.py`)
- Logs all execution events to JSON files
- Tracks trade data for analytics
- Records errors and failures
- Provides performance analytics

### 7. **MT5 Connection** (`mt5/connection.py`)
- Manages connection to MT5 terminal
- Authenticates with account credentials
- Retrieves account and symbol information
- Monitors connection status

```python
mt5 = get_mt5_connection(
    account=1234567,
    password="password",
    server="ICMarkets-Demo"
)
```

---

## 🎯 Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Signal Generated                            │
│                    (by analysis engines)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Signal Listener Fetches from API                        │
│          (every 30 seconds by default)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Signal Validation & Format Check                        │
│    (symbol, type, price, confidence required)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          8-Point Pre-Execution Validation                        │
│    (bot enabled, spread, positions, margin, daily loss, etc)    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
         ┌──────▼──────┐   ┌──────▼──────┐
         │   VALID     │   │  INVALID    │
         └──────┬──────┘   └─────────────┘
                │                │
                │                └──> LOG REJECTION
                │                     (continue listening)
                ▼
┌─────────────────────────────────────────────────────────────────┐
│          Position Size Calculation                               │
│    Based on account balance, risk %, and SL distance            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Order Execution on MT5                                  │
│    Place BUY/SELL with SL and TP                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
         ┌──────▼──────┐   ┌──────▼──────┐
         │  SUCCESS    │   │   FAILED    │
         └──────┬──────┘   └─────────────┘
                │                │
                │                └──> RETRY (up to 3x)
                │                     or LOG ERROR
                ▼
┌─────────────────────────────────────────────────────────────────┐
│          Create Trade Record in Database                         │
│    (entry price, SL, TP, lot size, timestamp)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Monitor Position                                        │
│    Track P&L, check for SL/TP hits, or manual closes           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
         ┌──────▼──────┐   ┌──────▼──────┐
         │  SL HIT     │   │  TP HIT     │
         │ or MANUAL   │   │ or SIGNAL   │
         │  CLOSE      │   │  REVERSAL   │
         └──────┬──────┘   └──────┬──────┘
                │                 │
                └────────┬────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Close Trade on MT5                                      │
│    Execute opposite order to close position                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Update Trade Record                                     │
│    (exit price, P&L, close reason, timestamp)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Log Event & Update Statistics                           │
│    (success/failure, P&L, daily total)                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Safety Features

### 1. **Kill Switch**
```python
BOT_ENABLED = False  # Disables all trading without stopping service
```

### 2. **Max Daily Loss**
```python
MAX_DAILY_LOSS = 5.0  # % of account balance
# If today's P&L is -5%, no more trades until next day
```

### 3. **Max Open Positions**
```python
MAX_OPEN_POSITIONS = 5  # Never more than 5 concurrent trades
```

### 4. **Spread Filter**
```python
MIN_SPREAD_THRESHOLD = 3.0  # Pips
# Rejects trades if bid-ask spread > 3 pips
```

### 5. **Margin Requirements**
```python
# Validates free margin is sufficient before placing order
# Fails trade if margin < required for position
```

### 6. **Duplicate Position Check**
```python
# Prevents multiple trades on the same symbol
# Only one BUY/SELL per pair at a time
```

---

## 📊 Database Schema

### Trade Table
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    signal_id INTEGER,
    mt5_order_id INTEGER UNIQUE,
    symbol VARCHAR(20) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,  -- BUY/SELL
    entry_price FLOAT NOT NULL,
    entry_time DATETIME NOT NULL,
    stop_loss FLOAT NOT NULL,
    take_profit FLOAT NOT NULL,
    lot_size FLOAT NOT NULL,
    risk_percent FLOAT NOT NULL,
    exit_price FLOAT,
    exit_time DATETIME,
    pnl FLOAT,  -- Profit/Loss in USD
    pnl_percent FLOAT,  -- Profit/Loss as %
    status VARCHAR(20) NOT NULL,  -- OPEN/CLOSED/CANCELLED/PENDING
    close_reason VARCHAR(100),
    strategy_name VARCHAR(100),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### ExecutionLog Table
```sql
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY,
    trade_id INTEGER,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- SIGNAL_RECEIVED, ORDER_PLACED, etc
    event_status VARCHAR(20) NOT NULL,  -- SUCCESS/FAILED/PENDING
    message TEXT NOT NULL,
    symbol VARCHAR(20),
    order_details JSON,
    error_details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔌 API Endpoints

### Get Trade History
```bash
GET /api/execution/trades
Query params: status=OPEN|CLOSED, limit=50
Response: { trades: [...], count: N }
```

### Get Trade Details
```bash
GET /api/execution/trades/<trade_id>
Response: { trade: {...} }
```

### Get Trade Statistics
```bash
GET /api/execution/trades/statistics
Query params: days=7
Response: { 
    total_trades: N,
    winning_trades: N,
    losing_trades: N,
    win_rate: 0.XX,
    total_pnl: 1234.56,
    avg_pnl: 123.45
}
```

### Get Execution Logs
```bash
GET /api/execution/logs
Query params: event_type, status, limit=100
Response: { logs: [...], count: N }
```

### Get Bot Status
```bash
GET /api/execution/status
Response: {
    is_running: true,
    bot_enabled: true,
    total_signals: 100,
    total_trades: 25,
    today_pnl: 1234.56,
    open_positions: 3
}
```

### Disable Bot (Kill Switch)
```bash
POST /api/execution/bot/disable
Body: none
Response: { status: "disabled" }
```

### Enable Bot
```bash
POST /api/execution/bot/enable
Body: none
Response: { status: "enabled" }
```

---

## 🚀 Quick Start

### 1. Configure Environment
```bash
cd backend
cp .env.example .env

# Edit .env with your MT5 credentials
# MT5_ACCOUNT=your_account
# MT5_PASSWORD=your_password
# MT5_SERVER=ICMarkets-Demo
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Test Components
```bash
python test_execution_components.py
```

### 4. Start Execution Service
```bash
python run_execution_service.py
```

Or use provided scripts:
- Windows: `run_execution_service.bat`
- Linux/Mac: `./run_execution_service.sh`

---

## 📝 Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MT5_ACCOUNT` | - | MT5 account number (required) |
| `MT5_PASSWORD` | - | MT5 password (required) |
| `MT5_SERVER` | ICMarkets-Demo | MT5 server name |
| `API_BASE_URL` | http://localhost:5000 | Backend API URL |
| `USER_ID` | 1 | User ID for signals |
| `POLLING_INTERVAL` | 30 | Signal polling interval (seconds) |
| `MAX_OPEN_POSITIONS` | 5 | Max concurrent positions |
| `RISK_PER_TRADE` | 1.0 | Risk per trade (%) |
| `MAX_DAILY_LOSS` | 5.0 | Max daily loss (%) |
| `MIN_SPREAD_THRESHOLD` | 3.0 | Max acceptable spread (pips) |
| `BOT_ENABLED` | True | Enable/disable trading |
| `ORDER_DEVIATION` | 100 | Slippage tolerance (points) |
| `ORDER_RETRY_COUNT` | 3 | Retries for failed orders |

---

## 🧪 Testing

### Component Tests
```bash
python test_execution_components.py
```

Tests:
- MT5 connection
- Position sizing
- Trade validation
- Signal listening
- Event logging

### Manual Testing
```bash
# Send test signal via curl
curl -X POST http://localhost:5000/api/signals \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "signal_type": "BUY",
    "price": 1.0850,
    "confidence": 0.85
  }'

# Check execution status
curl http://localhost:5000/api/execution/status

# Get recent trades
curl http://localhost:5000/api/execution/trades?limit=10
```

---

## 📈 Monitoring & Logging

### Log Files
- **Main Log**: `backend/execution/logs/execution.log`
- **Trades Log**: `backend/execution/logs/trades.json`
- **Analytics Log**: `backend/execution/logs/analytics.json`
- **Errors Log**: `backend/execution/logs/errors.json`

### Real-time Monitoring
```bash
# Watch execution logs live (Linux/Mac)
tail -f backend/execution/logs/execution.log

# Watch execution logs live (Windows PowerShell)
Get-Content -Path backend/execution/logs/execution.log -Wait
```

---

## 🐛 Troubleshooting

### MT5 Terminal Not Responding
**Problem**: "MT5 initialization failed" or "MT5 login failed"

**Solution**:
1. Ensure MT5 is running and minimized (not closed)
2. Verify credentials in .env are correct
3. Try logging in manually in MT5 first
4. Restart MT5 and try again

### Connection to API Failed
**Problem**: "Failed to fetch signals" repeatedly

**Solution**:
1. Check backend API is running: `python backend/main.py`
2. Verify `API_BASE_URL` in .env is correct
3. Check network connectivity
4. Verify firewall allows local connections

### Insufficient Margin
**Problem**: "Order failed: Insufficient margin"

**Solution**:
1. Check account balance in MT5
2. Reduce `RISK_PER_TRADE` in .env (try 0.5%)
3. Reduce `MAX_OPEN_POSITIONS`
4. Close some positions manually in MT5

### No Signals Being Processed
**Problem**: Service runs but no trades execute

**Solution**:
1. Check signal generation is working
2. Verify `USER_ID` in .env matches your user
3. Check `POLLING_INTERVAL` isn't too large
4. Review logs for validation failures

---

## 📚 Additional Resources

- [MetaTrader 5 Python API Docs](https://www.mql5.com/en/docs/python_metatrader5)
- [Risk Management Best Practices](https://www.investopedia.com/terms/r/riskmanagement.asp)
- [Position Sizing Formula](https://www.babypips.com/forexforbeginners/lesson1.html)
- [SofAi FX Signal Generation Docs](./SIGNAL_SYSTEM_COMPLETE.md)

---

## 🎉 Next Steps

1. ✅ Configure .env with MT5 credentials
2. ✅ Install Python dependencies
3. ✅ Run component tests
4. ✅ Start execution service
5. ✅ Monitor logs and trades
6. ✅ Adjust risk settings as needed
7. ✅ Enable automated signal generation
8. ✅ Let it trade 24/7! 🚀

---

**Created**: April 26, 2026  
**Status**: ✅ Production Ready  
**Last Updated**: April 26, 2026
