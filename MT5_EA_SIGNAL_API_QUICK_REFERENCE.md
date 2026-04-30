# MT5 EA Trading Signal API - Quick Reference

## 🚀 Quick Start

### 1. Get Your API Key

1. Open your SofAi FX dashboard: `http://localhost:5000` or deployed URL
2. Login with your credentials
3. Go to **Settings** → **API Key**
4. Copy your API key (looks like: `qWe...kRsT`)

### 2. Test the Endpoint Locally

```bash
# Replace YOUR_API_KEY with your actual key
curl "http://localhost:5000/signal?apikey=YOUR_API_KEY&symbol=EURUSD&format=json"
```

### 3. Deploy to Production

See [MT5_EA_SIGNAL_API_DEPLOYMENT.md](MT5_EA_SIGNAL_API_DEPLOYMENT.md) for full instructions.

---

## 📡 API Endpoint

```
GET /signal
```

### Query Parameters

```
?apikey=USER_KEY&symbol=EURUSD&timeframe=M5&format=json
```

| Parameter | Required | Example | Notes |
|-----------|----------|---------|-------|
| `apikey` | ✅ | `qWe2Rt...kRsT` | From dashboard |
| `symbol` | ✅ | `EURUSD` | Must be 6 chars |
| `timeframe` | ❌ | `M5` | Default: M5 |
| `format` | ❌ | `json` | `json` or `text` |

---

## 💻 Usage Examples

### Example 1: JSON Response

```bash
curl "https://yourdomain.com/signal?apikey=abc123&symbol=EURUSD&format=json"
```

**Response:**
```json
{
  "signal": "BUY",
  "confidence": 0.78,
  "timestamp": "2024-04-28T14:30:45.123456",
  "data_points": 100,
  "data_source": "TwelveData"
}
```

### Example 2: Text Response (for MT5 EA)

```bash
curl "https://yourdomain.com/signal?apikey=abc123&symbol=EURUSD&format=text"
```

**Response:**
```
BUY
```

### Example 3: Different Symbol

```bash
curl "https://yourdomain.com/signal?apikey=abc123&symbol=GBPUSD&timeframe=H1&format=json"
```

### Example 4: Python Request

```python
import requests

# Configuration
API_URL = "https://yourdomain.com/signal"
API_KEY = "your_api_key_here"
SYMBOL = "EURUSD"

# Make request
response = requests.get(
    f"{API_URL}?apikey={API_KEY}&symbol={SYMBOL}&format=json"
)

if response.status_code == 200:
    data = response.json()
    print(f"Signal: {data['signal']}")
    print(f"Confidence: {data['confidence']}")
else:
    print(f"Error: {response.status_code}")
```

### Example 5: JavaScript/Node.js

```javascript
// Configuration
const API_URL = "https://yourdomain.com/signal";
const API_KEY = "your_api_key_here";
const SYMBOL = "EURUSD";

// Make request
const url = `${API_URL}?apikey=${API_KEY}&symbol=${SYMBOL}&format=json`;

fetch(url)
  .then(response => response.json())
  .then(data => {
    console.log("Signal:", data.signal);
    console.log("Confidence:", data.confidence);
  })
  .catch(error => console.error("Error:", error));
```

---

## 🎯 Response Signals

### BUY Signal
- **Meaning:** Strong buy signal detected
- **When:** Multiple indicators confirm uptrend
- **Action:** Consider opening long position

### SELL Signal
- **Meaning:** Strong sell signal detected
- **When:** Multiple indicators confirm downtrend
- **Action:** Consider opening short position

### HOLD Signal
- **Meaning:** No clear signal or conflicting indicators
- **When:** Indicators are mixed or neutral
- **Action:** Wait for clearer signal

---

## ❌ Error Handling

### 401 - Invalid API Key

```bash
curl "https://yourdomain.com/signal?apikey=WRONG_KEY&symbol=EURUSD"
```

**Response:**
```json
{
  "error": "Invalid API key"
}
```

**Solution:** Check your API key in dashboard.

### 400 - Bad Request

```bash
curl "https://yourdomain.com/signal?apikey=abc123&symbol=EUR"
```

**Response:**
```json
{
  "error": "Invalid symbol format. Expected 6 characters (e.g., EURUSD), got EUR"
}
```

**Solution:** Use proper 6-character format (EURUSD, GBPUSD, etc.).

### 429 - Rate Limited

```json
{
  "error": "API_RATE_LIMIT",
  "message": "API rate limit reached. Please try again later."
}
```

**Solution:** Wait before making another request. Free tier limited.

### 500 - Server Error

```json
{
  "error": "Failed to generate signal for EURUSD",
  "message": "Internal server error"
}
```

**Solution:** Check if:
- API is running
- Database is accessible
- Data source APIs are working
- Check logs for details

---

## 🔐 Security Notes

### API Key Protection

1. **Never share** your API key publicly
2. **Never** put it in frontend code (only server-side)
3. **Rotate** API key regularly in dashboard
4. **Use HTTPS** always (never HTTP)
5. **Rate limit** your requests

### Best Practices

```javascript
// ❌ WRONG - Don't expose key in frontend
const key = "abc123xyz..."; // Visible in browser
fetch(`/signal?apikey=${key}&symbol=EURUSD`);

// ✅ RIGHT - Call your backend instead
fetch("/api/get-signal?symbol=EURUSD"); // Backend calls external API
```

---

## 📊 Supported Symbols

All major forex pairs:

```
EURUSD  GBPUSD  USDJPY  USDCAD
AUDUSD  NZDUSD  EUROGBP EURCHF
EURJPY  AUDJPY  GBPJPY  CHFJPY
EURCAD  NZDJPY  GBPCAD  AUDBSD
```

---

## ⏱️ Timeframes

```
M1   M5   M15  M30  H1   H4   D1   W1   MN1
```

**Note:** Most commonly used: **M5, M15, H1**

---

## 📈 Response Time

- **Local:** <100ms
- **Cloud (Render):** 200-500ms
- **Guaranteed:** <1 second (SLA)

### Optimization Tips

If slow:
1. Use TwelveData (faster than Alpha Vantage)
2. Cache results for 1 minute
3. Check your internet connection
4. Verify API service is up

---

## 🧪 Testing Checklist

- [ ] Get API key from dashboard
- [ ] Test with curl locally
- [ ] Test with your language (Python, JS, etc.)
- [ ] Test with different symbols
- [ ] Test error cases (bad key, wrong symbol)
- [ ] Test after deployment
- [ ] Monitor response times
- [ ] Check API key usage logs

---

## 📞 Troubleshooting

### API Key not working?
1. Copy exactly from dashboard
2. No spaces or special characters
3. Not expired or regenerated
4. Check database connection

### Response too slow?
1. Check TwelveData is working
2. Reduce data points needed
3. Add caching layer
4. Check server resources

### Getting 500 error?
1. Check backend is running
2. Check logs for errors
3. Verify database exists
4. Test with health endpoint first

---

## 🔗 Useful Endpoints

### Health Check
```bash
curl "https://yourdomain.com/health"
```

### Minimal Health (no auth)
```bash
curl "https://yourdomain.com/api/health/minimal"
```

### Get User Info (requires JWT)
```bash
curl "https://yourdomain.com/api/user" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📱 MT5 EA Template

```mql5
//+------------------------------------------------------------------+
//| SofAi FX Signal - Simple EA                                     |
//+------------------------------------------------------------------+

#property strict

// Settings
input string API_URL = "https://yourdomain.com/signal";
input string API_KEY = "your_api_key_here";
input double LOT_SIZE = 0.1;

//+------------------------------------------------------------------+
//| Expert initialization function                                  |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("SofAi EA initialized");
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_signal = 0;
    
    // Check signal once per minute
    if (TimeCurrent() - last_signal < 60) return;
    
    string signal = GetSignal();
    
    if (signal == "BUY")
    {
        if (CountOpenPositions(OP_BUY) == 0)
        {
            OrderSend(Symbol(), OP_BUY, LOT_SIZE, Ask, 10, 0, 0);
        }
    }
    else if (signal == "SELL")
    {
        if (CountOpenPositions(OP_SELL) == 0)
        {
            OrderSend(Symbol(), OP_SELL, LOT_SIZE, Bid, 10, 0, 0);
        }
    }
    
    last_signal = TimeCurrent();
}

//+------------------------------------------------------------------+
string GetSignal()
{
    string symbol = Symbol();
    string url = API_URL + "?apikey=" + API_KEY + 
                 "&symbol=" + symbol + 
                 "&format=text";
    
    char result[];
    int res = WebRequest("GET", url, NULL, NULL, 500, result, NULL);
    
    if (res == -1) return "HOLD";
    
    string signal = CharArrayToString(result);
    return StringTrimRight(signal);
}

int CountOpenPositions(int type)
{
    int count = 0;
    for (int i = 0; i < OrdersTotal(); i++)
    {
        if (OrderSelect(i, SELECT_BY_POS) && 
            OrderSymbol() == Symbol() && 
            OrderType() == type)
        {
            count++;
        }
    }
    return count;
}

void OnDeinit(const int reason)
{
    Print("SofAi EA stopped");
}
```

---

## 📚 Documentation Links

- Full Deployment Guide: [MT5_EA_SIGNAL_API_DEPLOYMENT.md](MT5_EA_SIGNAL_API_DEPLOYMENT.md)
- Flask API Docs: https://flask.palletsprojects.com/
- MQL5 Docs: https://www.mql5.com/en/docs
- MetaTrader 5 WebRequest: https://www.mql5.com/en/docs/network_common_functions/webrequest

---

## 🎓 Learning Path

1. **Test locally** - Run backend, get key, test with curl
2. **Deploy to cloud** - Use Render.com or similar
3. **Create EA** - Use MQL5 template above
4. **Monitor** - Check logs and API usage
5. **Optimize** - Cache results, handle errors better
6. **Scale** - Add more symbols, features, etc.

---

Good luck! 🚀

Questions? Check logs:
```bash
tail -f logs/sofai.log  # Local
tail -f /var/log/syslog # Production
```
