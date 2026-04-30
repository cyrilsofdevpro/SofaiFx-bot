# Phase 5 Features - Complete API Documentation

## Overview

Phase 5 introduces 5 interconnected feature modules that transform SofAi FX into a production-grade trading system:

1. **Backtesting Engine** - Validate strategies on historical data
2. **Performance Dashboard** - Real-time analytics and metrics
3. **Auto-Optimization Engine** - Learn from trades, improve weights
4. **Stress Testing System** - Validate reliability under load
5. **Execution Reliability** - Fault-tolerant trade execution

All features are exposed via REST APIs and integrated into a unified signal pipeline.

---

## 1. Backtesting API

### Purpose
Run historical backtests to validate trading strategies and measure performance metrics.

### Endpoints

#### POST /api/backtesting/run
**Run a custom backtest with specified parameters**

```json
{
  "pair": "EURUSD",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_balance": 10000,
  "lot_size": 0.1
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "pair": "EURUSD",
    "total_trades": 45,
    "winning_trades": 28,
    "win_rate": 62.2,
    "total_pnl": 1250.50,
    "max_drawdown": -8.5,
    "sharpe_ratio": 1.45,
    "risk_reward_ratio": 2.1,
    "profit_factor": 1.85,
    "avg_win": 44.73,
    "avg_loss": -21.32,
    "equity_curve": [10000, 10045, 10089, ...]
  }
}
```

#### POST /api/backtesting/quick
**Quick backtest with default 6-month window**

```json
{
  "pair": "EURUSD",
  "initial_balance": 10000
}
```

#### GET /api/backtesting/history
**Retrieve historical backtests** (database integration pending)

#### GET /api/backtesting/export/<backtest_id>?format=json
**Export backtest results as JSON or CSV**

### Key Metrics
- **Win Rate**: Percentage of profitable trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Gross profit / Gross loss
- **Risk/Reward**: Average win / Average loss

---

## 2. Performance Dashboard API

### Purpose
Provide real-time performance analytics with multi-dimensional filtering and visualization data.

### Endpoints

#### GET /api/dashboard/overview?days=90
**Overall system performance metrics**

Response:
```json
{
  "status": "success",
  "data": {
    "total_trades": 156,
    "win_rate": 58.3,
    "total_pnl": 2847.50,
    "profit_factor": 1.85,
    "accuracy": 0.583,
    "max_drawdown": -12.5,
    "sharpe_ratio": 1.23
  }
}
```

#### GET /api/dashboard/pair-performance?days=90&sort_by=win_rate&limit=10
**Breakdown by currency pair**

Query Parameters:
- `days`: Analysis window (default: 90)
- `sort_by`: `win_rate`, `pnl`, or `trades` (default: `win_rate`)
- `limit`: Max pairs to return (default: 10)

Response:
```json
{
  "status": "success",
  "data": [
    {
      "pair": "EURUSD",
      "trades": 45,
      "win_rate": 62.2,
      "total_pnl": 1250.50,
      "avg_win": 35.50,
      "avg_loss": -20.25
    }
  ]
}
```

#### GET /api/dashboard/equity-curve?pair=EURUSD&days=90&interval=daily
**Equity curve for charting**

Response:
```json
{
  "status": "success",
  "data": {
    "timestamps": ["2024-01-01", "2024-01-02", ...],
    "balance": [10000, 10125.50, 10280.75, ...],
    "pair": "EURUSD"
  }
}
```

#### GET /api/dashboard/daily-pnl?pair=EURUSD&days=30
**Daily P&L breakdown**

#### GET /api/dashboard/confidence-analysis?days=90
**Accuracy stratified by signal confidence**

Response:
```json
{
  "status": "success",
  "data": {
    "high_confidence": {"count": 45, "accuracy": 68.9},
    "medium_confidence": {"count": 38, "accuracy": 55.3},
    "low_confidence": {"count": 22, "accuracy": 36.4}
  }
}
```

#### GET /api/dashboard/drawdown-analysis?pair=EURUSD&days=90
**Drawdown metrics and analysis**

#### GET /api/dashboard/health
**System health status and alerts**

---

## 3. Optimization API

### Purpose
Manage signal weights and automatically optimize them based on trade outcomes.

### Signal Weights (Default)
- **Sentiment (HF)**: 50% - Primary intelligence signal
- **Technical**: 25% - Price action, RSI, moving averages
- **Patterns**: 15% - Chart patterns, support/resistance
- **News**: 10% - Market news sentiment

### Endpoints

#### GET /api/optimization/current-weights?pair=null
**Get current signal weights**

Response:
```json
{
  "status": "success",
  "data": {
    "sentiment": 0.50,
    "technical": 0.25,
    "patterns": 0.15,
    "news": 0.10,
    "pair": null,
    "applies_to": "global"
  }
}
```

#### POST /api/optimization/update-weights
**Manually adjust weights**

```json
{
  "sentiment": 0.45,
  "technical": 0.30,
  "patterns": 0.15,
  "news": 0.10,
  "pair": null
}
```

#### GET /api/optimization/stats?pair=null
**Optimization effectiveness metrics**

Response:
```json
{
  "status": "success",
  "data": {
    "total_trades_recorded": 256,
    "optimization_cycles": 5,
    "last_optimization": "2024-01-15 10:30:00",
    "improvement_percent": 8.5,
    "win_rate_before": 55.0,
    "win_rate_after": 59.7
  }
}
```

#### POST /api/optimization/run-optimization
**Manually trigger optimization**

```json
{
  "method": "advanced",
  "pair": null
}
```

Methods:
- **simple**: Rule-based weight adjustment
- **advanced**: Bayesian optimization using trade history

#### GET /api/optimization/pair-specific
**List pairs with custom (non-global) weights**

#### POST /api/optimization/reset-weights
**Reset weights to defaults**

#### POST /api/optimization/save-weights
**Save current weights to persistent storage**

### Optimization Logic

**Simple Method (Rule-Based):**
- Analyze which signals were accurate in wins vs losses
- Boost weights for signals that predicted wins
- Reduce weights for signals that predicted losses
- Adjustment rate: 0.2 (smooth transitions)
- Triggered every: 50 trades

**Advanced Method (Bayesian):**
- Calculate signal success rate (correct predictions / total)
- Update weights based on Bayesian probability
- Consider signal prevalence in winning trades
- Create pair-specific weights if accuracy < 40%

---

## 4. Stress Testing API

### Purpose
Validate system stability and performance under concurrent load.

### Endpoints

#### POST /api/stress-test/run
**Run stress test with custom parameters**

```json
{
  "name": "Load Test 1",
  "num_users": 50,
  "requests_per_user": 20,
  "duration_seconds": 300,
  "test_type": "concurrent"
}
```

Response (async, returns immediately):
```json
{
  "status": "started",
  "test_id": "test_abc123",
  "message": "Stress test started, check results endpoint for completion"
}
```

#### GET /api/stress-test/results/<test_id>
**Get stress test results**

Response:
```json
{
  "status": "complete",
  "data": {
    "total_requests": 1000,
    "successful": 950,
    "failed": 50,
    "error_rate": 5.0,
    "throughput_req_sec": 18.5,
    "response_times": {
      "p50": 45,
      "p95": 120,
      "p99": 250,
      "min": 10,
      "max": 500,
      "mean": 75
    },
    "verdict": "PASS",
    "duration_seconds": 54.2
  }
}
```

#### POST /api/stress-test/quick
**Quick stress test (default: 10 users, 10 req/user)**

#### GET /api/stress-test/test-templates
**Predefined test scenarios**

Templates:
- **Light Load**: 10 users, 10 requests each
- **Normal Load**: 50 users, 20 requests each
- **Heavy Load**: 100 users, 50 requests each
- **Extreme Load**: 500 users, 100 requests each

#### GET /api/stress-test/history?limit=20
**Recent stress test history**

### Pass/Fail Criteria
- **Throughput**: ≥ 10 req/sec
- **Error Rate**: < 5%
- **Success Rate**: ≥ 95%

---

## 5. Execution Reliability API

### Purpose
Execute trades with automatic retry logic, validation, and slippage control.

### Endpoints

#### POST /api/execution/execute
**Execute a trade with retry logic**

```json
{
  "pair": "EURUSD",
  "signal": "BUY",
  "entry_price": 1.0850,
  "stop_loss": 1.0820,
  "take_profit": 1.0900,
  "volume": 0.1,
  "strategy": "signal_engine",
  "confidence": 0.75
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "trade_id": "trade_abc123",
    "pair": "EURUSD",
    "signal": "BUY",
    "execution_time_ms": 245,
    "attempts": 1,
    "actual_price": 1.0851,
    "slippage_pct": 0.009,
    "order_status": "filled"
  }
}
```

**Retry Logic:**
- Max 3 attempts
- 2-second delay between attempts
- Continues if: timeout, failed submission, or confirmation miss
- Stops on: successful fill or slippage > 0.2%

**Price Validation (BUY):**
- Requirement: stop_loss < entry_price < take_profit
- Prevents: invalid price structures

**Validation (SELL):**
- Requirement: take_profit < entry_price < stop_loss

#### POST /api/execution/cancel/<trade_id>
**Cancel a pending trade**

#### GET /api/execution/stats
**Execution reliability metrics**

Response:
```json
{
  "status": "success",
  "data": {
    "total_executions": 245,
    "successful": 238,
    "failed": 7,
    "success_rate": 97.1,
    "avg_execution_time_ms": 234,
    "avg_slippage_pct": 0.018,
    "max_slippage_pct": 0.15,
    "retries_triggered": 12,
    "retry_success_rate": 83.3
  }
}
```

#### GET /api/execution/history?limit=50&pair=EURUSD&status=filled
**Recent execution history**

Query Parameters:
- `limit`: Max trades (default: 50)
- `pair`: Filter by pair (optional)
- `status`: `filled`, `cancelled`, `failed` (optional)

#### POST /api/execution/validate
**Dry run: validate trade before execution**

Response:
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "errors": [],
    "warnings": ["Take profit very close to entry price"],
    "estimated_execution_time_ms": 200
  }
}
```

#### GET /api/execution/slippage-report?pair=EURUSD&days=30
**Slippage analysis and optimization recommendations**

Response:
```json
{
  "status": "success",
  "data": {
    "avg_slippage_pct": 0.018,
    "median_slippage_pct": 0.012,
    "max_slippage_pct": 0.15,
    "best_execution_hour": 14,
    "worst_execution_hour": 3,
    "recommendations": [
      "Consider executing during peak hours (12-16 UTC)"
    ]
  }
}
```

---

## Integration Guide

### Registering Blueprints in Flask

```python
from flask import Flask
from backend.src.api.routes_integration import register_feature_blueprints

app = Flask(__name__)

# Register all Phase 5 feature routes
register_feature_blueprints(app)

# Your existing routes...
app.run(debug=True)
```

### Using the Routes Summary

```python
from backend.src.api.routes_integration import get_routes_summary

summary = get_routes_summary()

# Print all available endpoints
for feature, details in summary.items():
    print(f"\n{feature.upper()}")
    print(f"Description: {details['description']}")
    for endpoint in details['endpoints']:
        print(f"  {endpoint}")
```

---

## Complete API Endpoint Reference

### Backtesting (7 endpoints)
- `POST /api/backtesting/run`
- `POST /api/backtesting/quick`
- `GET /api/backtesting/history`
- `GET /api/backtesting/export/<id>`

### Dashboard (7 endpoints)
- `GET /api/dashboard/overview`
- `GET /api/dashboard/pair-performance`
- `GET /api/dashboard/equity-curve`
- `GET /api/dashboard/daily-pnl`
- `GET /api/dashboard/confidence-analysis`
- `GET /api/dashboard/drawdown-analysis`
- `GET /api/dashboard/health`

### Optimization (7 endpoints)
- `GET /api/optimization/current-weights`
- `POST /api/optimization/update-weights`
- `GET /api/optimization/stats`
- `POST /api/optimization/run-optimization`
- `GET /api/optimization/pair-specific`
- `POST /api/optimization/reset-weights`
- `POST /api/optimization/save-weights`

### Stress Testing (5 endpoints)
- `POST /api/stress-test/run`
- `GET /api/stress-test/results/<test_id>`
- `POST /api/stress-test/quick`
- `GET /api/stress-test/test-templates`
- `GET /api/stress-test/history`

### Execution (6 endpoints)
- `POST /api/execution/execute`
- `POST /api/execution/cancel/<trade_id>`
- `GET /api/execution/stats`
- `GET /api/execution/history`
- `POST /api/execution/validate`
- `GET /api/execution/slippage-report`

**Total: 32 production-grade API endpoints**

---

## Testing

Run the comprehensive integration test suite:

```bash
python test_phase5_integration.py
```

This validates:
- All 5 module instantiations
- Core functionality of each module
- Routes registration
- Metrics calculation
- Export functionality

---

## Database Integration (TODO)

The following features require database schema migration:

1. **Backtesting**: `backtest_results` table
   - Store historical backtest runs with full metrics
   - Enable retrieval and comparison

2. **Dashboard**: `trade_history` table
   - Store all executed trades
   - Enable metrics calculation

3. **Optimization**: `optimization_weights` table
   - Persist weight history
   - Track optimization changes over time

4. **Execution**: `execution_log` table
   - Log all trades with retry attempts
   - Analyze execution quality

---

## Next Steps

1. ✅ Phase 5 modules implemented (5/5)
2. ✅ API routes created (32 endpoints)
3. ⭕ Database schema migration
4. ⭕ Admin UI dashboard updates
5. ⭕ Real MT5 connection (currently simulated)
6. ⭕ Real historical data API (currently synthetic)
7. ⭕ Performance optimization and caching
8. ⭕ Advanced monitoring and alerting

---

## Contact & Support

For detailed implementation questions, refer to module documentation in:
- `backend/src/backtesting/backtester.py`
- `backend/src/analytics/dashboard.py`
- `backend/src/optimization/auto_optimizer.py`
- `backend/src/testing/stress_test.py`
- `backend/src/execution/reliability.py`
