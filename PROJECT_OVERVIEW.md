# 📊 SofAi FX Bot - Project Overview

## What You've Built

A complete **AI-powered forex trading system** that analyzes market data and generates intelligent trading signals.

## 🎯 Core Features

✅ **Market Data Integration**
- Live forex data from Alpha Vantage API
- Support for multiple currency pairs (EURUSD, GBPUSD, USDJPY, etc.)
- Configurable update intervals

✅ **Trading Strategies**
- RSI (Relative Strength Index) - Overbought/Oversold detection
- Moving Average Crossover - Trend identification
- Multi-strategy voting for robust signals
- Confidence scoring (0-100%)

✅ **Signal Generation**
- Automated BUY/SELL/HOLD signals
- Combined analysis from multiple strategies
- Detailed reasoning for each signal

✅ **Multi-Channel Notifications**
- 📱 Telegram bot alerts
- 📧 Email notifications
- 🌐 Web dashboard in real-time

✅ **Professional Dashboard**
- Real-time signal display
- Signal history and statistics
- Interactive charts (Chart.js)
- Responsive design (Tailwind CSS)
- Manual analysis capability

✅ **REST API Backend**
- Flask API for signal analysis
- JSON responses for integration
- CORS enabled for frontend communication

## 📁 Project Structure

```
SofAi-Fx/
├── 📄 README.md                 ← Project overview
├── 📄 SETUP_GUIDE.md            ← Step-by-step installation
├── 📄 PROJECT_OVERVIEW.md       ← This file
├── 🔧 .gitignore                ← Git configuration
│
├── backend/
│   ├── 🐍 main.py               ← Bot entry point
│   ├── 📋 requirements.txt       ← Python dependencies
│   ├── 📝 .env.example           ← Configuration template
│   ├── 🚀 run_api.bat/.sh        ← Start Flask API
│   │
│   └── src/
│       ├── ⚙️ config.py          ← Load environment settings
│       │
│       ├── 📊 data/
│       │   └── alpha_vantage.py  ← Fetch market data
│       │
│       ├── 🧠 strategies/
│       │   ├── base_strategy.py  ← Strategy base class
│       │   ├── rsi_strategy.py   ← RSI indicator
│       │   └── moving_average.py ← MA crossover
│       │
│       ├── 📈 signals/
│       │   └── signal_generator.py ← Combine strategies
│       │
│       ├── 🔔 notifications/
│       │   ├── telegram_notifier.py ← Telegram alerts
│       │   └── email_notifier.py    ← Email alerts
│       │
│       ├── 🌐 api/
│       │   └── flask_app.py      ← REST API server
│       │
│       └── 🛠️ utils/
│           └── logger.py         ← Logging utility
│
└── frontend/
    ├── 📄 index.html             ← Main dashboard
    └── 📁 assets/
        ├── js/
        │   └── dashboard.js      ← Frontend logic
        └── css/
            └── style.css         ← Custom Tailwind styles
```

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.8+ |
| Framework | Flask (REST API) |
| Data Analysis | pandas, numpy |
| Market Data | Alpha Vantage API |
| Telegram | python-telegram-bot |
| Email | SMTP (Gmail) |
| Frontend | HTML5 + Tailwind CSS |
| Charts | Chart.js |
| Server | Gunicorn (optional) |

## 🚀 Quick Start (3 Steps)

### 1️⃣ Configure
```bash
cd backend
copy .env.example .env
# Edit .env with your API keys
```

### 2️⃣ Install & Run
```bash
pip install -r requirements.txt
python -m src.api.flask_app
```

### 3️⃣ Open Dashboard
Open `frontend/index.html` in your browser

## 📊 How It Works

```
Market Data (Alpha Vantage)
         ↓
    [Data Engine]
         ↓
    [Strategies]
    ├─ RSI Strategy
    ├─ MA Strategy
         ↓
[Signal Generator]
    (Multi-strategy voting)
         ↓
   [Notifications]
   ├─ Telegram
   ├─ Email
   └─ Dashboard
```

## 🎯 Signal Logic

### RSI Strategy (Momentum)
```
RSI > 70  → SELL (Overbought)
RSI < 30  → BUY (Oversold)
30-70     → HOLD (Neutral)
```

### Moving Average Strategy (Trend)
```
SMA > LMA (Price > Both) → BUY (Uptrend)
SMA < LMA (Price < Both) → SELL (Downtrend)
Crossover                → Strong signal
```

### Combined Signal
- Both strategies agree = Higher confidence
- Single strategy signal = Moderate confidence
- Conflicting signals = HOLD or lower confidence

## 📈 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Server health check |
| GET | `/api/config` | Get bot configuration |
| GET | `/api/signals?limit=10` | Get recent signals |
| GET | `/api/signals/<symbol>` | Get signals for symbol |
| POST | `/api/analyze` | Analyze single pair |
| POST | `/api/analyze-all` | Analyze all pairs |

### Example API Call
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","notify":true}'
```

## 🔑 Required Configuration

Create `backend/.env`:
```env
# REQUIRED
ALPHA_VANTAGE_API_KEY=your_key_here

# OPTIONAL (Telegram)
TELEGRAM_BOT_TOKEN=bot_token
TELEGRAM_CHAT_ID=your_chat_id

# OPTIONAL (Email)
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=app_password

# TRADING
UPDATE_INTERVAL=3600
CURRENCY_PAIRS=EURUSD,GBPUSD,USDJPY
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30
```

## 💡 Understanding Signals

| Signal | Meaning | Indicator |
|--------|---------|-----------|
| 🟢 BUY | Bullish signal, consider buying | Green badge |
| 🔴 SELL | Bearish signal, consider selling | Red badge |
| 🟡 HOLD | No clear direction | Yellow badge |

Confidence: 0-100% (higher = more reliable)

## 🎨 Dashboard Features

- **Stats Cards**: Total signals, buy/sell counts, average confidence
- **Quick Analysis**: Search and analyze any forex pair
- **Signals Feed**: Latest signals with details
- **Signal Table**: Historical view with sorting
- **Charts**: Signal distribution and confidence analysis
- **Configuration**: View monitored pairs and settings
- **Real-time Updates**: Auto-refresh every 30 seconds

## 🔄 Execution Modes

### Mode 1: API Server (Flask)
```bash
python -m src.api.flask_app
# Runs on localhost:5000
# Access dashboard at frontend/index.html
# On-demand analysis via REST API
```

### Mode 2: Bot (Continuous)
```bash
python main.py
# Runs indefinitely
# Monitors all pairs on schedule
# Sends auto notifications
```

## 📝 Customization Points

1. **Add more strategies**: Create files in `src/strategies/`
2. **Change indicators**: Edit RSI period, MA windows in `.env`
3. **Add pairs**: Modify `CURRENCY_PAIRS` in `.env`
4. **Customize dashboard**: Edit `frontend/index.html` and `.css`
5. **Change notification channels**: Modify `notifications/` modules

## 🔐 Security Notes

- Keep `.env` file private (in `.gitignore`)
- Never commit API keys to Git
- Use app-specific passwords for Gmail
- Store Telegram bot tokens securely
- In production, use environment variables, not `.env`

## 📚 Learning Resources

- **Trading Concepts**: https://www.investopedia.com/
- **Alpha Vantage Docs**: https://www.alphavantage.co/documentation/
- **Flask Guide**: https://flask.palletsprojects.com/
- **Technical Analysis**: https://www.investopedia.com/terms/t/technicalanalysis.asp

## 🎯 Roadmap

**Phase 1** (Current) ✅
- RSI + MA strategies
- Telegram + Email notifications
- Web dashboard

**Phase 2** (Next)
- [ ] Database integration
- [ ] More indicators (MACD, Bollinger Bands)
- [ ] Backtesting engine

**Phase 3** (Advanced)
- [ ] Machine learning predictions
- [ ] Paper trading simulator
- [ ] User authentication
- [ ] Subscription system

## ⚠️ Important Disclaimer

🚨 **FOR EDUCATIONAL PURPOSES ONLY**

- This bot is not financial advice
- Trading forex has substantial risk of loss
- Never use real money without thorough testing
- Past performance ≠ future results
- Always do your own research (DYOR)
- Use appropriate risk management

## 🎉 You're All Set!

Your complete AI-powered forex trading bot is ready to use!

**Next Steps:**
1. Read SETUP_GUIDE.md for detailed instructions
2. Get API keys from Alpha Vantage, Telegram, Gmail
3. Configure .env file
4. Run the bot or API server
5. Start analyzing forex pairs!

---

**Project**: SofAi Forex Trading Bot v1.0  
**Built by**: SofDev (Cyril)  
**Platform**: Python + Flask + HTML/Tailwind  
**Purpose**: AI-driven forex analysis and signal generation

🚀 Happy Trading! 📈
