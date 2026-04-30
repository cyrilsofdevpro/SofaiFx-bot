# 🚀 MT5 Execution Layer - Implementation Complete

## System Overview

The MT5 Execution Layer is a complete automated trading system that:

1. **Connects to MetaTrader 5** running on your local machine or VPS
2. **Fetches trading signals** from the SofAi FX backend API
3. **Validates signals** against safety rules and market conditions
4. **Calculates position sizes** based on risk management rules
5. **Executes trades** automatically with proper stop loss and take profit
6. **Monitors positions** in real-time
7. **Logs all activity** for analytics and auditing

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SofAi FX Backend (Cloud)                  │
│                   (Render / Any Cloud Host)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Flask API                                           │   │
│  │  - Signal Generation                                │   │
│  │  - User Management                                  │   │
│  │  - Dashboard                                        │   │
│  │  - Execution Endpoints (NEW)                        │   │
│  │  - Trade API (NEW)                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ▲ API Calls                         │
└──────────────────────────┼──────────────────────────────────┘
                          │
                          │ HTTP REST
                          │
┌──────────────────────────┼──────────────────────────────────┐
│                          ▼                                   │
│                Execution Service (Local/VPS)                │
│            (Python + MetaTrader5 Connection)                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Signal Listener                                     │   │
│  │  - Polls API for signals                             │   │
│  │  - Queues signals for processing                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Trade Validator                                     │   │
│  │  - Bot enabled check                                 │   │
│  │  - Duplicate position check                          │   │
│  │  - Spread validation                                 │   │
│  │  - Risk constraints                                  │   │
│  │  - Margin validation                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Position Sizer                                      │   │
│  │  - Calculate lot size based on risk                  │   │
│  │  - Validate margin requirements                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Order Executor                                      │   │
│  │  - Place orders on MT5                               │   │
│  │  - Handle slippage                                   │   │
│  │  - Retry logic                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Trade Manager                                       │   │
│  │  - Track open positions                              │   │
│  │  - Monitor P&L                                       │   │
│  │  - Close positions                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Execution Logger                                    │   │
│  │  - Log all events                                    │   │
│  │  - Track analytics                                   │   │
│  │  - Generate reports                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MT5 Connection                                      │   │
│  │  - Connect to terminal                               │   │
│  │  - Execute trades                                    │   │
│  │  - Get account/position info                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
└──────────────────────────┼──────────────────────────────────┘
                          │
                          │ MetaTrader 5 Protocol
                          │
                ┌─────────┴─────────┐
                │                   │
        ┌───────▼────────┐  ┌───────▼────────┐
        │  MT5 Terminal  │  │ Broker Gateway │
        │  (Local/VPS)   │  │   (ICMarkets)  │
        └────────────────┘  └────────────────┘
                │
                │ Real Trades / Market Data
                │
        ┌───────▼────────────────┐
        │  Forex Market           │
        │  (Real Trading)         │
        └────────────────────────┘
```

### Execution Flow

```
1. Signal Generation
   └─> Backend generates trading signal (RSI, MA, S/R)
   
2. Signal Emission
   └─> Signal sent to database and queue
   
3. Signal Listening
   └─> Execution service polls API every 30s
   └─> Retrieves new signals from API
   
4. Validation
   └─> Bot enabled check
   └─> Duplicate position check
   └─> Spread validation
   └─> Risk validation
   └─> Margin check
   
5. Position Sizing
   └─> Calculate lot size = (Balance * Risk%) / (SL_Pips * Pip_Value)
   └─> Validate margin requirements
   
6. Order Execution
   └─> Send order to MT5 terminal
   └─> MT5 executes on broker
   └─> Broker routes to forex market
   
7. Trade Tracking
   └─> Create trade record in database
   └─> Monitor position in real-time
   └─> Track P&L
   
8. Position Management
   └─> Monitor for TP/SL hit
   └─> Optional: Trailing stop
   └─> Optional: Close on signal reversal
   
9. Trade Closing
   └─> Position closes at TP/SL or manually
   └─> Calculate final P&L
   └─> Store trade history
   
10. Analytics & Logging
    └─> Log all events to database
    └─> Calculate statistics
    └─> Generate reports
```

---

## 📁 File Structure

```
backend/
├── execution/                          # NEW: Execution layer
│   ├── __init__.py
│   ├── config.py                      # Configuration template
│   ├── service.py                     # Main execution service
│   ├── SETUP_GUIDE.md                # Setup instructions
│   ├── mt5/
│   │   ├── __init__.py
│   │   └── connection.py              # MT5 terminal connection
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── position_sizer.py         # Lot size calculation
│   │   ├── validator.py               # Signal validation
│   │   ├── executor.py                # Order execution
│   │   ├── signal_listener.py         # API signal polling
│   │   ├── trade_manager.py           # Trade lifecycle
│   │   └── logger.py                  # Event logging
│   └── logs/                          # Execution logs
│       ├── execution_service.log
│       ├── execution.log
│       ├── trades.json
│       └── errors.json
│
├── src/
│   ├── models.py                      # UPDATED: Added Trade, ExecutionLog
│   ├── api/
│   │   ├── flask_app.py              # UPDATED: Added execution endpoints
│   │   ├── execution.py               # NEW: Execution API blueprint
│   │   ├── auth.py
│   │   └── admin.py
│   └── ...
│
└── run_execution_service.py            # NEW: Easy runner script
```

---

## 🔧 Key Modules

### 1. MT5 Connection (`mt5/connection.py`)

```python
from execution.mt5.connection import get_mt5_connection

# Connect to MT5
mt5 = get_mt5_connection(account=123456, password="pass", server="ICMarkets-Demo")

# Get account info
account = mt5.get_account_info()
print(f"Balance: ${account['balance']}")

# Get symbol info
symbol = mt5.get_symbol_info("EURUSD")
print(f"Bid: {symbol['bid']}, Ask: {symbol['ask']}")

# Get open positions
positions = mt5.get_open_positions()
```

### 2. Position Sizer (`engines/position_sizer.py`)

```python
from execution.engines.position_sizer import PositionSizer

sizer = PositionSizer(account_balance=10000, leverage=100)

lot_size = sizer.calculate_lot_size(
    symbol="EURUSD",
    entry_price=1.0850,
    stop_loss_price=1.0800,
    risk_percent=1.0
)
# Returns: 1.5 lots
```

### 3. Trade Validator (`engines/validator.py`)

```python
from execution.engines.validator import TradeValidator

validator = TradeValidator(max_open_positions=5, max_daily_loss_percent=5.0)

is_valid, reason = validator.validate_signal(
    signal={'symbol': 'EURUSD', 'signal_type': 'BUY', ...},
    symbol_info=symbol_info,
    open_positions=open_positions,
    account_info=account_info,
    today_pnl=today_pnl,
    bot_enabled=True
)
```

### 4. Order Executor (`engines/executor.py`)

```python
from execution.engines.executor import create_order_executor

executor = create_order_executor(mt5)

success, order = executor.place_market_order(
    symbol="EURUSD",
    order_type="BUY",
    volume=1.5,
    entry_price=1.0850,
    stop_loss=1.0800,
    take_profit=1.0900,
    comment="Automated trade"
)
```

### 5. Signal Listener (`engines/signal_listener.py`)

```python
from execution.engines.signal_listener import create_signal_listener

listener = create_signal_listener(
    api_base_url="http://localhost:5000",
    user_id=1,
    polling_interval=30
)

# Poll signals in a thread
listener.poll_signals(callback=on_signal_received)

# Get next signal
signal = listener.get_next_signal()
```

### 6. Execution Logger (`engines/logger.py`)

```python
from execution.engines.logger import get_execution_logger

logger = get_execution_logger()

# Log event
logger.log_event(
    event_type="ORDER_PLACED",
    status="SUCCESS",
    message="Order placed successfully",
    symbol="EURUSD",
    details={...}
)

# Get stats
stats = logger.get_trade_summary(user_id=1, days=7)
```

---

## 📊 Database Schema

### Trade Table
```
trades:
- id (PK)
- user_id (FK users.id)
- signal_id (FK signals.id)
- mt5_order_id (unique)
- symbol (string)
- trade_type (BUY/SELL)
- entry_price (float)
- entry_time (datetime)
- stop_loss (float)
- take_profit (float)
- lot_size (float)
- risk_percent (float)
- exit_price (float)
- exit_time (datetime)
- pnl (float)
- pnl_percent (float)
- status (OPEN/CLOSED/CANCELLED)
- close_reason (string)
- strategy_name (string)
- notes (text)
```

### ExecutionLog Table
```
execution_logs:
- id (PK)
- trade_id (FK trades.id)
- user_id (FK users.id)
- event_type (string)
- event_status (SUCCESS/FAILED/PENDING)
- message (text)
- symbol (string)
- order_details (JSON)
- error_details (JSON)
- created_at (datetime)
```

---

## 🔒 Safety Features

### 1. Kill Switch
```bash
# Disable all trading
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -d '{"enabled": false}' \
  http://localhost:5000/api/execution/kill-switch
```

### 2. Max Open Positions
- Default: 5 positions
- Prevents over-exposure

### 3. Daily Loss Limit
- Default: 5% of account balance
- Stops trading if limit exceeded

### 4. Spread Filter
- Default: 3 pips maximum
- Rejects trades if spread too wide

### 5. Margin Validation
- Checks free margin before each trade
- Rejects if insufficient margin

### 6. Risk Per Trade
- Calculates lot size based on 1-2% risk
- Ensures consistent risk management

---

## 📈 API Endpoints

All endpoints require JWT authentication:

```
GET    /api/execution/trades              # Get user's trades
GET    /api/execution/trades/<id>         # Get specific trade
GET    /api/execution/trades/statistics   # Get trade stats
GET    /api/execution/open-positions      # Get open trades
GET    /api/execution/logs                # Get execution logs
GET    /api/execution/status              # Get service status
GET    /api/execution/daily-report        # Get daily report
POST   /api/execution/trades/<id>/close   # Close trade manually
GET    /api/execution/kill-switch         # Get kill switch status
POST   /api/execution/kill-switch         # Set kill switch status
```

---

## 🚀 Quick Start

### 1. Install MetaTrader5 Package
```bash
pip install MetaTrader5
```

### 2. Configure Service
```bash
# Edit configuration
cp backend/execution/config.py backend/execution/config.py
# Update with your MT5 credentials
```

### 3. Start Service
```bash
python run_execution_service.py
```

### 4. Monitor in Dashboard
- Open dashboard at http://localhost:3000
- View live trades, P&L, statistics

---

## 🧪 Testing

See `tests/` directory for comprehensive test suite:

- `test_mt5_connection.py` - Test MT5 connection
- `test_signal_listener.py` - Test signal polling
- `test_validator.py` - Test validation logic
- `test_executor.py` - Test order placement
- `test_integration.py` - End-to-end testing

---

## 🎯 Key Features Implemented

✅ **MT5 Integration**
- Terminal connection and authentication
- Account info retrieval
- Symbol data fetching
- Order placement and management

✅ **Signal Processing**
- API polling with callback
- Signal validation
- Queue management
- Error handling

✅ **Risk Management**
- Position sizing calculation
- Margin validation
- Spread filtering
- Daily loss limits

✅ **Trade Execution**
- Market order placement
- SL/TP setting
- Slippage handling
- Order retry logic

✅ **Trade Management**
- Open position tracking
- P&L calculation
- Manual position closing
- Trade history

✅ **Logging & Analytics**
- Event logging
- Trade statistics
- Daily reports
- Error tracking

✅ **Safety Features**
- Kill switch
- Max positions limit
- Daily loss circuit breaker
- Margin requirements
- Risk per trade limits

---

## 🔄 Continuous Improvement

The system is designed for easy extension:

1. **Add New Strategies**: Modify signal generation in backend
2. **Custom Risk Rules**: Update `TradeValidator`
3. **Advanced Position Sizing**: Extend `PositionSizer`
4. **Trailing Stops**: Add to `TradeManager`
5. **Copy Trading**: Implement signal redistribution

---

## 📞 Support

- **Documentation**: See SETUP_GUIDE.md
- **Logs**: Check backend/execution/logs/
- **API**: See Execution API endpoints
- **Database**: Query sofai_fx.db with SQLite

---

**Status**: ✅ Implementation Complete
**Version**: 1.0.0
**Last Updated**: April 26, 2026
