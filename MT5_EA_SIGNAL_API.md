# 🚀 SofAi FX - MT5 EA Trading Signal API

## What's New

Your SofAi FX backend now includes a **production-ready MT5 Expert Advisor Signal Endpoint** that can be deployed to a real server!

---

## 📡 The Signal API Endpoint

```
GET /signal?apikey=USER_KEY&symbol=EURUSD&timeframe=M5&format=json
```

### What It Does

1. **Authenticates** your API key
2. **Fetches** real-time market data (TwelveData or Alpha Vantage)
3. **Analyzes** price action with technical indicators
4. **Generates** trading signals: **BUY**, **SELL**, or **HOLD**
5. **Returns** JSON or plain text response

### Example Response

```json
{
  "signal": "BUY",
  "confidence": 0.78,
  "timestamp": "2024-04-28T14:30:45.123456",
  "data_points": 100,
  "data_source": "TwelveData"
}
```

---

## 🎯 Quick Start (3 Steps)

### Step 1: Test Locally

```bash
# Start backend
cd backend
python src/api/flask_app.py

# In another terminal, get your API key from the dashboard
# Login to http://localhost:5000 → Settings → API Key

# Test the endpoint
curl "http://localhost:5000/signal?apikey=YOUR_KEY&symbol=EURUSD&format=json"
```

### Step 2: Choose Deployment Platform

| Platform | Cost | Setup Time | Best For |
|----------|------|-----------|----------|
| **Render.com** | Free/paid | 5 min | 🏆 Easiest |
| Railway.app | $5/mo | 5 min | Quick deploy |
| DigitalOcean | $5/mo | 30 min | Full control |
| AWS | Varies | 45 min | Enterprise |

**Recommendation:** Use **Render.com** for fastest deployment

### Step 3: Deploy (Render.com Example)

1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create Web Service from repo
4. Add start command:
   ```bash
   cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT src.api.flask_app:app
   ```
5. Add environment variables (API keys, secrets)
6. Deploy - done! 🎉

Your API is now live at:
```
https://sofai-fx-api.onrender.com/signal?apikey=YOUR_KEY&symbol=EURUSD
```

---

## 📖 Documentation

**Complete Guides:**

1. **[MT5_EA_SIGNAL_API_QUICK_REFERENCE.md](MT5_EA_SIGNAL_API_QUICK_REFERENCE.md)** ⭐
   - Quick examples with curl, Python, JavaScript
   - Error handling
   - Security best practices
   - MQL5 EA template

2. **[MT5_EA_SIGNAL_API_DEPLOYMENT.md](MT5_EA_SIGNAL_API_DEPLOYMENT.md)** 🚀
   - Complete deployment options
   - Production checklist
   - Performance requirements
   - Troubleshooting guide
   - Scaling strategies

---

## 💡 Key Features

✅ **Fast Response** - Returns signal in <1 second
✅ **Real-time Data** - Uses TwelveData for 1-minute candles
✅ **API Key Auth** - Secure with API keys
✅ **Multiple Formats** - JSON or plain text (for EAs)
✅ **Error Handling** - Proper HTTP status codes
✅ **Rate Limiting** - Handles API limits gracefully
✅ **Production Ready** - Secure, tested, documented
✅ **Cloud Ready** - Deployable anywhere

---

## 🔐 API Security

### Getting Your API Key

1. Open dashboard: `http://localhost:5000`
2. Login with your credentials
3. Go to **Settings** → **API Key**
4. Copy your key (example: `qWe2Rt...kRsT`)

### Using the API Key

```bash
# Include as query parameter
curl "https://yourdomain.com/signal?apikey=YOUR_KEY&symbol=EURUSD"

# Always use HTTPS (never HTTP)
# Never expose key in frontend code
```

### Rotating Your Key

If compromised:
1. Go to Settings → API Key
2. Click "Regenerate API Key"
3. Update your EA with new key

---

## 🤖 MT5 EA Integration

### Simple Example (MQL5)

```mql5
string GetSignal() {
    string url = "https://yourdomain.com/signal?apikey=" + API_KEY + 
                 "&symbol=EURUSD&format=text";
    char result[];
    WebRequest("GET", url, NULL, NULL, 500, result, NULL);
    return CharArrayToString(result); // Returns: BUY, SELL, or HOLD
}

void OnTick() {
    string signal = GetSignal();
    if (signal == "BUY") {
        // Place BUY order
    }
}
```

**Full template available in Quick Reference guide.**

---

## 📊 Supported Symbols

All major forex pairs:
```
EURUSD  GBPUSD  USDJPY  USDCAD  AUDUSD
NZDUSD  EUROGBP EURCHF  EURJPY  AUDJPY
GBPJPY  CHFJPY  EURCAD  NZDJPY  GBPCAD
```

---

## ❓ FAQ

**Q: Do I need to deploy to use the API?**
A: No! You can test locally first. But EAs need a public HTTPS endpoint.

**Q: How much does it cost?**
A: Free tier on Render.com (with limitations) or $5/month on DigitalOcean.

**Q: Is it production ready?**
A: Yes! It's fully implemented with error handling, logging, and security.

**Q: Can I modify the signal logic?**
A: Yes! See [backend/src/signals/signal_generator.py](backend/src/signals/signal_generator.py)

**Q: What data sources are used?**
A: TwelveData (preferred, real-time) or Alpha Vantage (fallback, daily).

**Q: How many requests can I make?**
A: Limited by your data API plan. Free tier: ~800/day (TwelveData) or 5/min (Alpha Vantage).

---

## ⚠️ Important Reminders

1. **HTTPS Required** - All public requests must use HTTPS
2. **API Key Security** - Never share or expose your API key
3. **Rate Limits** - Respect data source API rate limits
4. **Testing** - Always test in demo account first
5. **Monitoring** - Keep logs and error alerts enabled
6. **Backups** - Regular database backups for production

---

## 🚀 Next Steps

1. **Test Locally:**
   ```bash
   cd backend
   python src/api/flask_app.py
   # Then curl: http://localhost:5000/signal?apikey=YOUR_KEY&symbol=EURUSD&format=json
   ```

2. **Deploy to Cloud:**
   - Follow [MT5_EA_SIGNAL_API_DEPLOYMENT.md](MT5_EA_SIGNAL_API_DEPLOYMENT.md)
   - Choose Render.com for easiest setup

3. **Create Your EA:**
   - Use MQL5 template from [Quick Reference](MT5_EA_SIGNAL_API_QUICK_REFERENCE.md)
   - Test in MT5 strategy tester
   - Deploy to live account

4. **Monitor & Optimize:**
   - Check logs regularly
   - Monitor API usage
   - Optimize response times
   - Update signal logic as needed

---

## 📚 Files

- **This File:** Overview and quick start
- **[MT5_EA_SIGNAL_API_QUICK_REFERENCE.md](MT5_EA_SIGNAL_API_QUICK_REFERENCE.md)** - Quick examples and MQL5 templates
- **[MT5_EA_SIGNAL_API_DEPLOYMENT.md](MT5_EA_SIGNAL_API_DEPLOYMENT.md)** - Complete deployment guide
- **Implementation:** [backend/src/api/flask_app.py](backend/src/api/flask_app.py) - Search for `/signal` endpoint

---

## 🤝 Support

### Debugging

Check logs:
```bash
# Local
tail -f logs/sofai.log

# Production (Render)
# View in dashboard → Logs

# Production (DigitalOcean)
sudo tail -f /var/log/syslog | grep gunicorn
```

### Common Issues

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check API key, verify it's correct |
| 400 Bad Request | Verify symbol format (EURUSD) |
| 429 Rate Limited | Wait or upgrade data API plan |
| 500 Error | Check logs, ensure APIs are working |

---

## 🎓 Learning Resources

- [Render.com Deployment](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MQL5 WebRequest](https://www.mql5.com/en/docs/network_common_functions/webrequest)
- [TwelveData API](https://twelvedata.com/docs)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)

---

## ✅ Deployment Checklist

Before going live:

- [ ] Test locally with curl
- [ ] Get API key from dashboard
- [ ] Choose deployment platform
- [ ] Push code to GitHub
- [ ] Create web service
- [ ] Add environment variables
- [ ] Enable HTTPS
- [ ] Test live endpoint
- [ ] Update EA with live URL
- [ ] Test EA in demo account
- [ ] Monitor logs and alerts
- [ ] Ready for live trading! 🎉

---

**Happy trading! 📈**

If you have questions, check the documentation files or review the Flask app logs.

```
Quick Command Reference:
- Local test: curl "http://localhost:5000/signal?apikey=KEY&symbol=EURUSD&format=text"
- JSON format: &format=json (returns confidence score)
- Text format: &format=text (just BUY/SELL/HOLD, for EAs)
```
