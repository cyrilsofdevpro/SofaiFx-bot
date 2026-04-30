# 🚀 SofAi FX Bot - Complete Setup Guide

Welcome to your AI-powered forex trading system! This guide will walk you through everything step by step.

## 📋 Prerequisites

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Alpha Vantage API Key** (FREE) - [Get one here](https://www.alphavantage.co/api/)
- **Telegram** (Optional) - For signal alerts via Telegram
- **Gmail Account** (Optional) - For email alerts

## 🔧 Step 1: Get API Keys

### Alpha Vantage (Required)
1. Go to https://www.alphavantage.co/
2. Enter your email address
3. You'll get an API key instantly
4. Save it somewhere safe - you'll need it soon!

### Telegram Bot Token (Optional but Recommended)
1. Open Telegram and search for **@BotFather**
2. Send him `/newbot`
3. Follow the prompts to create your bot
4. You'll get a token that looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
5. Send your new bot a message (so it has your chat ID)
6. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Replace `<YOUR_TOKEN>` with your actual token
   - Look for `"id": <number>` in the response - that's your Chat ID

### Gmail SMTP (Optional)
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click "Security" in the left sidebar
3. Enable "2-Step Verification"
4. Go back to Security → App passwords
5. Generate an "App password" for Mail
6. Copy the 16-character password (this is your SENDER_PASSWORD)

## 📦 Step 2: Install & Configure

### Windows

```bash
# 1. Open Command Prompt and navigate to the project
cd Desktop\SofAi-Fx

# 2. Create virtual environment
python -m venv backend\venv

# 3. Activate it
backend\venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r backend\requirements.txt

# 5. Configure environment
copy backend\.env.example backend\.env
# Now open backend\.env and add your API keys
```

### macOS/Linux

```bash
# 1. Navigate to the project
cd ~/Desktop/SofAi-Fx

# 2. Create virtual environment
python3 -m venv backend/venv

# 3. Activate it
source backend/venv/bin/activate

# 4. Install dependencies
pip install -r backend/requirements.txt

# 5. Configure environment
cp backend/.env.example backend/.env
# Now open backend/.env and add your API keys
nano backend/.env
```

## 🔑 Step 3: Configure Your API Keys

Open `backend/.env` and fill in your details:

```env
# Required
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Optional (Telegram)
TELEGRAM_BOT_TOKEN=your_telegram_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Optional (Email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password_here

# Trading Settings (Adjust to your preferences)
UPDATE_INTERVAL=3600           # Check market every hour (seconds)
CURRENCY_PAIRS=EURUSD,GBPUSD,USDJPY   # Pairs to monitor
RSI_PERIOD=14                  # RSI calculation period
RSI_OVERBOUGHT=70             # When to sell
RSI_OVERSOLD=30               # When to buy

# Flask API
FLASK_PORT=5000
```

## 🚀 Step 4: Run the Bot

### Option A: Run the Flask API Server (Recommended for Dashboard)

**Windows:**
```bash
cd backend
run_api.bat
```

**macOS/Linux:**
```bash
cd backend
bash run_api.sh
```

The API will start on `http://localhost:5000`

### Option B: Run as Continuous Bot

**Windows:**
```bash
run_bot.bat
```

**macOS/Linux:**
```bash
bash run_bot.sh
```

This will continuously monitor markets and send notifications.

## 📊 Step 5: Open the Dashboard

Once the Flask API is running, open the dashboard:

1. **Option A**: Simple file open
   - Navigate to `frontend/index.html`
   - Double-click to open in your browser

2. **Option B**: Run a local web server
   ```bash
   # From the project root
   python -m http.server 8000 --directory frontend
   ```
   - Visit: http://localhost:8000

## 🧪 Step 6: Test Everything

### Test the API

```bash
# Health check
curl http://localhost:5000/health

# Get configuration
curl http://localhost:5000/api/config

# Analyze a pair
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","notify":true}'
```

### Test Telegram
1. Make sure your bot token and chat ID are configured
2. Run `/api/analyze` endpoint with `"notify": true`
3. Check your Telegram for the signal alert!

### Test Email
1. Make sure SMTP settings are configured
2. Verify your Gmail app password works
3. Run an analysis to trigger an email

## 📈 Step 7: Customize Your Strategies

Edit `backend/src/strategies/` to modify:

### RSI Strategy
File: `rsi_strategy.py`
```python
self.period = 14        # Change RSI period
self.overbought = 70    # Change overbought level
self.oversold = 30      # Change oversold level
```

### Moving Average Strategy
File: `moving_average.py`
```python
self.short_period = 20  # Short-term MA
self.long_period = 50   # Long-term MA
```

## 🎨 Customize Dashboard

The dashboard colors and layout are in:
- `frontend/index.html` - HTML structure
- `frontend/assets/css/style.css` - Custom styles
- `frontend/assets/js/dashboard.js` - JavaScript logic

## 📝 Understanding Signals

### What Each Signal Means

**BUY 📈**
- Market is oversold (RSI < 30) OR moving average shows uptrend
- Good time to consider buying
- Confidence: 0-100% based on strategy agreement

**SELL 📉**
- Market is overbought (RSI > 70) OR moving average shows downtrend
- Good time to consider selling
- Confidence: 0-100% based on strategy agreement

**HOLD ⏸️**
- No clear signal from strategies
- Market is neutral

### Confidence Score

- **80-100%**: Strong consensus between strategies - more reliable
- **60-80%**: Good signal, strategies mostly agree
- **40-60%**: Moderate signal, consider additional factors
- **Below 40%**: Weak signal, use with caution

## 🔍 Troubleshooting

### "API Rate Limit Exceeded"
- Alpha Vantage free tier: 5 requests per minute
- Solution: Increase `UPDATE_INTERVAL` in `.env`
- Or upgrade to paid plan

### "No Telegram notifications"
- Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in `.env`
- Make sure your bot received your message
- Check the logs in `backend/logs/`

### "Email not sending"
- Verify Gmail app password (16 characters, not your regular password)
- Enable "Less secure app access" if using regular Gmail
- Check SMTP settings are correct

### "API server won't start"
```bash
# Make sure you're in the backend directory
cd backend

# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Logs
Check detailed logs in: `backend/logs/sofai_fx_YYYYMMDD.log`

## 📊 Project Files Explained

```
SofAi-Fx/
├── backend/
│   ├── main.py              ← Main bot (continuous mode)
│   ├── requirements.txt      ← Python packages
│   ├── .env                  ← Your configuration (CREATE THIS)
│   └── src/
│       ├── config.py         ← Load settings from .env
│       ├── data/
│       │   └── alpha_vantage.py      ← Fetch market data
│       ├── strategies/
│       │   ├── base_strategy.py      ← Base strategy class
│       │   ├── rsi_strategy.py       ← RSI indicator
│       │   └── moving_average.py     ← MA crossover
│       ├── signals/
│       │   └── signal_generator.py   ← Combine strategies
│       ├── notifications/
│       │   ├── telegram_notifier.py  ← Telegram alerts
│       │   └── email_notifier.py     ← Email alerts
│       └── api/
│           └── flask_app.py          ← REST API server
│
└── frontend/
    ├── index.html           ← Main dashboard (open in browser!)
    └── assets/
        ├── js/
        │   └── dashboard.js  ← Dashboard logic
        └── css/
            └── style.css     ← Custom styles
```

## 🎯 What's Next?

### Short Term
- [ ] Get first signals working
- [ ] Test Telegram notifications
- [ ] Monitor live trading signals

### Medium Term
- [ ] Add more currency pairs
- [ ] Fine-tune RSI/MA parameters
- [ ] Backtest strategies

### Long Term
- [ ] Database for signal history
- [ ] Advanced strategies (MACD, Bollinger Bands)
- [ ] Backtesting engine
- [ ] Paper trading simulation
- [ ] ML-based predictions

## 💡 Tips & Best Practices

1. **Start with paper trading** - Never risk real money on a system you haven't tested
2. **Monitor signals** - Keep the dashboard open and review signals daily
3. **Adjust RSI/MA values** - Different pairs may need different settings
4. **Test before production** - Always backtest strategies first
5. **Risk management** - Use stop losses and position sizing
6. **Documentation** - Keep notes on signal performance

## 🚨 Important Disclaimer

⚠️ **Educational Purpose Only**

This bot is for **educational and research purposes only**. 
- Trading forex carries substantial risk of loss
- Past performance does not guarantee future results
- Always do your own research before trading
- Never risk money you can't afford to lose
- This bot is not a substitute for professional financial advice

## 📞 Support & Resources

- **Alpha Vantage Docs**: https://www.alphavantage.co/documentation/
- **Flask Docs**: https://flask.palletsprojects.com/
- **Telegram Bot Docs**: https://core.telegram.org/bots
- **Trading Indicators**: https://www.investopedia.com/

## 🎉 You're Ready!

You now have a complete AI-powered forex trading bot ready to generate signals!

**Next Step**: Create your `.env` file with your API keys and run the bot!

```bash
# Windows
run_bot.bat

# macOS/Linux
bash run_bot.sh
```

Happy trading! 🚀📈

---

**Built with ❤️ by SofDev**  
*AI-Powered Trading Solutions*
