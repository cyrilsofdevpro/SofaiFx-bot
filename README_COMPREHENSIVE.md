# 🤖 SofAi FX - AI-Powered Forex Trading Bot

**Advanced AI-driven forex trading system with Hugging Face sentiment analysis, backtesting, and optimization.**

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the System](#running-the-system)
7. [API Endpoints](#api-endpoints)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Development](#development)
11. [Contributing](#contributing)

---

## 🎯 Overview

**SofAi FX** is a sophisticated forex trading system that combines multiple AI and technical analysis approaches to generate trading signals. The system includes:

- **🧠 AI Sentiment Analysis** - Hugging Face transformer models for market sentiment
- **📊 Technical Analysis** - RSI, Moving Averages, Pattern Recognition
- **🔄 Backtesting Engine** - Historical performance analysis with equity curve tracking
- **⚡ Auto-Optimization** - Automatic signal weight adjustment based on performance
- **🎯 Stress Testing** - System reliability and load testing
- **🔐 Multi-User Support** - Isolated trading accounts per user
- **📈 Real-Time Dashboard** - Live performance metrics and analytics

---

## ✨ Features

### 🔤 Sentiment Analysis (Phase 5)
- **Hugging Face Integration** - `cardiffnlp/twitter-roberta-base-sentiment-latest` model
- **Market Context Understanding** - Analyzes news, social media, and market data
- **Confidence Scoring** - Reliability metrics for each signal
- **50% Signal Weight** - Largest weight in the 4-layer signal architecture

### 📈 Backtesting Engine
- **Historical Simulation** - Run backtests on synthetic OHLC data
- **Trade Analysis** - Detailed metrics on every backtest
- **Equity Curve Tracking** - Track account balance through time
- **Multiple Metrics** - Win rate, PnL, Sharpe ratio, Max Drawdown
- **Scheduled Jobs** - Background backtesting on a cron schedule

### 🎲 Auto-Optimization
- **Dynamic Weighting** - Automatically adjust signal weights
- **Simple & Advanced Methods** - Multiple optimization algorithms
- **Pair-Specific Tuning** - Customize weights per currency pair
- **Performance-Based** - Optimize based on actual trade results

### 🧪 Stress Testing
- **Concurrent Load Testing** - Simulate multiple users
- **Performance Metrics** - Throughput (req/sec), response times (p50/p95/p99)
- **Reliability Analysis** - Error rates and success rates
- **System Health** - Validate system under load

### 🚀 Trade Execution
- **Retry Logic** - 3 attempts with 2-second delays
- **Slippage Checking** - Monitor execution quality
- **Risk Management** - Position sizing and stop-loss calculation
- **MT5 Integration** - Demo and real trading support

### 📊 Analytics Dashboard
- **Real-Time Metrics** - Overall system performance
- **Pair Performance** - Individual pair analysis
- **Equity Curves** - Historical balance tracking
- **Confidence Analysis** - Signal accuracy metrics
- **Drawdown Analysis** - Risk metrics and recovery patterns

---

## 🏗️ Architecture

### 4-Layer Signal Architecture

```
┌─────────────────────────────────────────────┐
│       Signal Decision (BUY/SELL/HOLD)       │
└─────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────┐
│    Intelligence Layer (50/25/15/10%)        │
│  ├─ Sentiment (HF):     50%                 │
│  ├─ Technical (RSI/MA): 25%                 │
│  ├─ Patterns:           15%                 │
│  └─ News:               10%                 │
└─────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────┐
│          Data Layer (Multiple APIs)          │
│  ├─ Twelve Data (OHLC)                      │
│  ├─ Alpha Vantage (Forex)                   │
│  ├─ NewsAPI (Market News)                   │
│  └─ Economic Calendar                       │
└─────────────────────────────────────────────┘
```

### System Components

```
backend/
├── src/
│   ├── signals/              # Signal generation
│   │   ├── signal_generator.py
│   │   ├── huggingface_service.py    # HF sentiment
│   │   └── phase_router.py
│   ├── backtesting/         # Backtesting engine
│   │   ├── backtester.py
│   │   └── backtest_scheduler.py     # Background jobs
│   ├── analytics/           # Dashboard & metrics
│   │   └── dashboard.py
│   ├── optimization/        # Auto-optimization
│   │   └── auto_optimizer.py
│   ├── execution/           # Trade execution
│   │   └── reliability.py
│   ├── testing/             # Stress testing
│   │   └── stress_test.py
│   ├── api/                 # Flask API
│   │   ├── flask_app.py
│   │   ├── routes/          # 32 endpoints
│   │   └── routes_integration.py
│   ├── data/                # Data providers
│   ├── scheduler/           # APScheduler integration
│   └── utils/               # Logging & helpers
├── main.py                  # CLI entry point
└── requirements.txt         # Dependencies
```

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- pip or Poetry
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/cyrilsofdevpro/SofaiFx-bot.git
cd SofaiFx-bot
```

### Step 2: Create Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Or using Poetry
poetry install
poetry shell
```

### Step 3: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy example configuration
cp backend/.env.example backend/.env

# Edit .env with your API keys
nano backend/.env
```

---

## ⚙️ Configuration

### Required Environment Variables

```env
# ============================================
# Data API Keys - Market Data
# ============================================
TWELVE_DATA_API_KEY=your_api_key_here
ALPHA_VANTAGE_KEY=your_api_key_here
NEWS_API_KEY=your_api_key_here

# ============================================
# AI/ML Integration - Hugging Face
# ============================================
HF_API_KEY=your_huggingface_api_key_here

# ============================================
# Database Configuration
# ============================================
DATABASE_URL=sqlite:///sofai_fx.db
# Or PostgreSQL: postgresql://user:password@localhost:5432/sofai_fx

# ============================================
# Trading Platform Integration
# ============================================
MT5_API_URL=http://localhost:5005
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# ============================================
# Flask Application Configuration
# ============================================
FLASK_ENV=development
FLASK_DEBUG=False
FLASK_PORT=5000
SECRET_KEY=your_secret_key_here

# ============================================
# Trading Settings
# ============================================
CURRENCY_PAIRS=EURUSD,GBPUSD,USDJPY
BACKTEST_INITIAL_BALANCE=10000
BACKTEST_COMMISSION=0.001
OPTIMIZATION_ENABLED=True

# ============================================
# Logging
# ============================================
LOG_LEVEL=INFO
```

### Signal Weights Configuration

Default weights (in backend/.env):

```env
SIGNAL_SENTIMENT_WEIGHT=0.50      # Hugging Face
SIGNAL_TECHNICAL_WEIGHT=0.25      # RSI/MA
SIGNAL_PATTERN_WEIGHT=0.15        # Chart patterns
SIGNAL_NEWS_WEIGHT=0.10           # News sentiment
```

---

## 🚀 Running the System

### Option 1: Flask API Server (Recommended)

```bash
cd backend
export FLASK_APP=src/api/flask_app.py
flask run --port 5000
```

Server starts at: `http://localhost:5000`

### Option 2: CLI Bot (Continuous Analysis)

```bash
cd backend
python main.py
```

Runs continuous pair analysis with scheduled jobs.

### Option 3: Using Docker

```bash
docker build -t sofai-fx .
docker run -p 5000:5000 --env-file .env sofai-fx
```

---

## 📡 API Endpoints

All endpoints return JSON responses with consistent error handling.

### Health & Status

```bash
GET /health
# Response: { "status": "healthy", "timestamp": "2024-01-01T12:00:00" }
```

### Signals API

```bash
# Get current signals
GET /api/signals

# Get signals for specific pair
GET /api/signals?pair=EURUSD

# Analyze and generate signal
POST /api/signals/analyze
# Payload: { "pair": "EURUSD" }
```

### Backtesting API

```bash
# Quick backtest
POST /api/backtesting/quick
# Payload: { "pair": "EURUSD" }

# Run full backtest
POST /api/backtesting/run
# Payload: { "pair": "EURUSD", "start_date": "2023-01-01", "end_date": "2024-01-01" }

# Get backtest history
GET /api/backtesting/history

# Get precomputed results
GET /api/dashboard/backtest/results?pair=EURUSD&range=90d
```

### Dashboard API

```bash
# Overall metrics
GET /api/dashboard/overview

# Per-pair analysis
GET /api/dashboard/pair-performance

# Equity curve
GET /api/dashboard/equity-curve

# System health
GET /api/dashboard/health

# Backtest results
GET /api/dashboard/backtest/results
```

### Optimization API

```bash
# Current signal weights
GET /api/optimization/current-weights

# Update weights
POST /api/optimization/update-weights
# Payload: { "sentiment": 0.50, "technical": 0.25, ... }

# Run optimization
POST /api/optimization/run-optimization

# Get statistics
GET /api/optimization/stats
```

### Execution API

```bash
# Execute trade
POST /api/execution/execute
# Payload: { "pair": "EURUSD", "action": "BUY", "volume": 0.1 }

# Execution history
GET /api/execution/history

# Execution statistics
GET /api/execution/stats
```

### Stress Testing API

```bash
# Run stress test
POST /api/stress-test/run
# Payload: { "concurrent_users": 10, "requests_per_user": 50 }

# Test history
GET /api/stress-test/history

# Test templates
GET /api/stress-test/test-templates
```

---

## 🧪 Testing

### Run API Endpoint Validation

```bash
python validate_endpoints.py
```

This script tests all major endpoints and reports status.

### Run Full Integration Tests

```bash
# Install pytest
pip install pytest

# Run all tests
python -m pytest test_phase5_integration.py -v

# Run specific test
python -m pytest test_phase5_integration.py::test_backtester_simple -v
```

### Manual Testing with cURL

```bash
# Test health
curl http://localhost:5000/health

# Test dashboard
curl http://localhost:5000/api/dashboard/overview

# Test backtest
curl -X POST http://localhost:5000/api/backtesting/quick \
  -H "Content-Type: application/json" \
  -d '{"pair": "EURUSD"}'
```

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'huggingface_hub'"

```bash
pip install huggingface_hub
```

### Issue: "Database locked"

The SQLite database is locked. Stop other processes using the database:

```bash
# Kill Flask process
pkill -f flask

# Or delete old database
rm backend/sofai_fx.db
```

### Issue: API returns 500 errors

Check logs in `logs/` directory:

```bash
tail -f logs/sofai_fx.log
tail -f logs/sofai_fx_errors.log
```

### Issue: "HF_API_KEY not set"

Ensure the API key is in your `.env` file:

```bash
cat backend/.env | grep HF_API_KEY
```

### Issue: Backtesting returns empty results

Check that pairs are configured:

```bash
echo $CURRENCY_PAIRS
# Should output: EURUSD,GBPUSD,USDJPY,...
```

---

## 👨‍💻 Development

### Project Structure

```
SofaiFx-bot/
├── backend/              # Flask API & core logic
│   ├── src/             # Source code
│   ├── main.py          # CLI entry point
│   └── requirements.txt  # Dependencies
├── frontend/            # Web dashboard (optional)
├── tests/              # Test suite
├── docs/               # Documentation
├── .env.example        # Environment template
├── .gitignore          # Git exclusions
└── README.md           # This file
```

### Adding New Features

1. Create module in appropriate subdirectory
2. Add logging using `get_logger('ModuleName')`
3. Create tests in `tests/` directory
4. Add API route in `backend/src/api/routes/`
5. Document in comments and README
6. Run validation tests

### Code Style

- Follow PEP 8
- Use type hints
- Include docstrings
- Log important events
- Handle exceptions gracefully

---

## 📊 Key Modules

### Hugging Face Integration (`backend/src/signals/huggingface_service.py`)

Sentiment analysis using transformer models:

```python
from backend.src.signals.huggingface_service import HuggingFaceService

hf = HuggingFaceService(api_key="your_key")
sentiment = hf.analyze_market_sentiment("EURUSD")
# Returns: { "sentiment": 0.25, "label": "bullish", "confidence": 0.95 }
```

### Backtesting (`backend/src/backtesting/backtester.py`)

Run historical simulations:

```python
from backend.src.backtesting.backtester import BacktestingEngine

backtester = BacktestingEngine()
results = backtester.backtest_pair("EURUSD")
# Returns: equity_curve, trades, metrics, win_rate, pnl
```

### Optimization (`backend/src/optimization/auto_optimizer.py`)

Automatic weight optimization:

```python
from backend.src.optimization.auto_optimizer import AutoOptimizationEngine

optimizer = AutoOptimizationEngine()
optimizer.record_trade(pair="EURUSD", is_profitable=True)
optimizer.optimize_weights()  # Runs every 50 trades
```

### Stress Testing (`backend/src/testing/stress_test.py`)

System reliability testing:

```python
from backend.src.testing.stress_test import StressTestEngine

stress = StressTestEngine()
report = stress.run_stress_test(concurrent_users=10, requests_per_user=50)
# Returns: throughput, response_times, error_rate, success_rate
```

---

## 📝 Logging

The system logs all important events:

```
logs/
├── sofai_fx.log          # All events
├── sofai_fx_errors.log   # Error-only log
└── 2024-01-01_analysis.log  # Daily logs
```

Log levels:
- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages

View logs:

```bash
# All events
tail -f logs/sofai_fx.log

# Errors only
tail -f logs/sofai_fx_errors.log

# With grep
grep "ERROR" logs/sofai_fx.log
grep "SIGNAL_GENERATED" logs/sofai_fx.log
```

---

## 🔐 Security

### Best Practices

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Use strong secrets** - Generate with: `python -c "import secrets; print(secrets.token_urlsafe())"`
3. **Rotate API keys regularly** - Update in `.env` and restart
4. **Use HTTPS in production** - Deploy with SSL certificates
5. **Validate all inputs** - API endpoints validate request data
6. **Rate limiting** - Configured at 1 req/sec per API

### Credential Management

MT5 credentials are encrypted:

```python
from backend.src.services.credential_manager import MT5CredentialManager

manager = MT5CredentialManager(encryptor)
manager.save_credentials(user_id, login, password, server)
```

---

## 🚢 Deployment

### Local Development

```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
flask run
```

### Production (Ubuntu/Linux)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.src.api.flask_app:app

# Use systemd service (see deployment docs)
```

### Production (Heroku)

```bash
# Create Procfile
echo "web: gunicorn backend.src.api.flask_app:app" > Procfile

# Deploy
git push heroku main
```

---

## 📚 Additional Resources

- **Hugging Face Docs**: https://huggingface.co/docs
- **Flask Documentation**: https://flask.palletsprojects.com/
- **APScheduler**: https://apscheduler.readthedocs.io/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **pytest**: https://docs.pytest.org/

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test: `python validate_endpoints.py`
4. Commit: `git commit -m "Add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Create Pull Request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 💬 Support

For issues, questions, or suggestions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs in `logs/` directory
3. Create an issue on GitHub
4. Contact the development team

---

## 🎉 Changelog

### Version 1.0.0 (Current)

- ✅ Hugging Face sentiment integration
- ✅ 5 feature modules (Backtesting, Dashboard, Optimization, Stress Testing, Execution)
- ✅ 32 API endpoints
- ✅ Background scheduling with APScheduler
- ✅ Comprehensive logging system
- ✅ 100% test pass rate (21/21 tests)
- ✅ Production-ready configuration

---

**Happy Trading! 🚀**

Last Updated: January 2024
