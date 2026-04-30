# MT5 EA Trading Signal API - Deployment Guide

## 🎯 Overview

Your SofAi FX backend now has a dedicated **MT5 Expert Advisor (EA) Signal Endpoint** that provides real-time trading signals for MetaTrader 5.

### Endpoint Specification
```
GET /signal?apikey=USER_KEY&symbol=EURUSD&timeframe=M5&format=json
```

---

## 📋 API Documentation

### Endpoint Details

**URL:** `https://yourdomain.com/signal`

**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| `apikey` | string | ✅ Yes | `abc123xyz...` | User's API key from dashboard |
| `symbol` | string | ✅ Yes | `EURUSD` | Currency pair (6 characters) |
| `timeframe` | string | ❌ No | `M5` | Timeframe (M5, M15, H1, H4, D1) |
| `format` | string | ❌ No | `json` | Response format: `json` or `text` |

### Response Format

**JSON Response (Default):**
```json
{
  "signal": "BUY",
  "confidence": 0.78,
  "timestamp": "2024-04-28T14:30:45.123456",
  "data_points": 100,
  "data_source": "TwelveData"
}
```

**Text Response (for EA):**
```
BUY
```

### Signal Values
- **BUY** - Strong buy signal
- **SELL** - Strong sell signal  
- **HOLD** - No clear signal or conflicting indicators

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | ✅ Signal generated successfully | Normal operation |
| 400 | ❌ Missing or invalid parameters | Missing symbol |
| 401 | ❌ Invalid API key | Expired/wrong key |
| 429 | ⚠️ API rate limit exceeded | Too many requests |
| 500 | ❌ Server error | Data fetch failed |

---

## 🚀 Deployment Options

### Option 1: Render.com (Recommended for beginners)

**Pros:** Free tier available, easy setup, HTTPS included, no credit card required initially

**Steps:**

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub or email
   - Create new account

2. **Connect GitHub Repository**
   - Link your GitHub account to Render
   - Grant access to your SofAi-Fx repo

3. **Create Web Service**
   - Click "Create +" → "Web Service"
   - Select your GitHub repository
   - Choose branch: `main` or `master`

4. **Configure Service**
   - **Name:** `sofai-fx-api`
   - **Runtime:** `Python 3.9`
   - **Build Command:** 
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command:**
     ```bash
     cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT src.api.flask_app:app
     ```

5. **Environment Variables**
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `False`
   - `JWT_SECRET_KEY`: Generate a secure key
   - `ALPHA_VANTAGE_API_KEY`: Your API key
   - `TWELVE_DATA_API_KEY`: Your API key
   - Other config as needed

6. **Deploy**
   - Click "Create Web Service"
   - Render builds and deploys automatically
   - Your URL: `https://sofai-fx-api.onrender.com`

### Option 2: Railway.app

**Pros:** Simple deployment, $5 credit monthly, GitHub integration

**Steps:**

1. Go to [railway.app](https://railway.app)
2. Sign up and connect GitHub
3. Create new project from your repo
4. Set start command:
   ```bash
   cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT src.api.flask_app:app
   ```
5. Add environment variables
6. Deploy instantly

### Option 3: DigitalOcean

**Pros:** Powerful, affordable ($5-12/month), full control, good docs

**Steps:**

1. Create Droplet (Ubuntu 22.04, $5/month)
2. SSH into server
3. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```
4. Clone repo and setup:
   ```bash
   cd /home/ubuntu
   git clone https://github.com/YOUR_USERNAME/SofAi-Fx.git
   cd SofAi-Fx/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Setup Nginx as reverse proxy
6. Use systemd to run service
7. Add SSL with Let's Encrypt (Certbot)

### Option 4: AWS EC2

**Pros:** Powerful, scalable, enterprise-grade

**Steps:**

1. Launch EC2 instance (t3.micro free tier eligible)
2. Configure security group (allow ports 80, 443)
3. SSH and setup similar to DigitalOcean
4. Use Elastic IP for fixed address
5. Setup RDS for database (or use local SQLite)
6. Add CloudFront CDN for caching

### Option 5: PythonAnywhere

**Pros:** Simplest deployment, Python-specific, free tier available

**Steps:**

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload your code
3. Configure web app with Flask
4. Set working directory to `backend/`
5. Point WSGI to `src.api.flask_app:app`
6. Enable HTTPS
7. Your URL: `https://yourusername.pythonanywhere.com`

---

## 🔐 Production Checklist

Before deploying to production:

- [ ] **HTTPS Enabled** - All requests must use HTTPS
- [ ] **Database** - Use proper database (PostgreSQL recommended, not SQLite for production)
- [ ] **Environment Variables** - All secrets in env vars, not in code
- [ ] **API Keys** - Store API keys securely (Alpha Vantage, TwelveData)
- [ ] **Rate Limiting** - Implement rate limiting per user
- [ ] **Monitoring** - Setup error tracking (Sentry)
- [ ] **Logging** - Centralized logging (Datadog, LogRocket)
- [ ] **Backups** - Regular database backups
- [ ] **SSL Certificate** - Valid SSL/TLS certificate
- [ ] **Health Checks** - Monitoring that service is up
- [ ] **Auto-Restart** - Service restarts on failure
- [ ] **Load Balancing** - For high traffic (future)

---

## 🧪 Testing the Endpoint

### Local Testing (Before Deployment)

1. **Start Flask server:**
   ```bash
   cd backend
   python src/api/flask_app.py
   ```

2. **Get an API key:**
   - Login to dashboard
   - Copy your API key from settings

3. **Test the endpoint:**
   ```bash
   curl "http://localhost:5000/signal?apikey=YOUR_KEY&symbol=EURUSD&timeframe=M5&format=json"
   ```

   **Expected response:**
   ```json
   {
     "signal": "BUY",
     "confidence": 0.78,
     "timestamp": "2024-04-28T14:30:45.123456",
     "data_points": 100,
     "data_source": "TwelveData"
   }
   ```

### Production Testing

1. **After deployment, test live endpoint:**
   ```bash
   curl "https://yourdomain.com/signal?apikey=YOUR_KEY&symbol=EURUSD&format=text"
   ```

2. **Should return just:** `BUY` (or SELL/HOLD)

3. **Test with invalid key:**
   ```bash
   curl "https://yourdomain.com/signal?apikey=WRONG_KEY&symbol=EURUSD"
   ```
   **Should return:** `401 Unauthorized`

---

## 🤖 MT5 EA Integration

### MQL5 Code Example

```mql5
//+------------------------------------------------------------------+
//| SofAi FX Signal Fetcher for MT5                                 |
//+------------------------------------------------------------------+

#include <Arrays\List.mqh>

// Configuration
string API_URL = "https://yourdomain.com/signal";
string API_KEY = "YOUR_API_KEY_HERE";
string SYMBOL = "EURUSD";
string TIMEFRAME = "M5";

//+------------------------------------------------------------------+
//| Function to fetch signal from API                               |
//+------------------------------------------------------------------+
string GetTradingSignal()
{
    // Build URL with parameters
    string url = API_URL + "?apikey=" + API_KEY + 
                 "&symbol=" + SYMBOL + 
                 "&timeframe=" + TIMEFRAME + 
                 "&format=text";
    
    // Create request
    char post_data[];
    char result[];
    string result_headers;
    
    // Make HTTP GET request
    int res = WebRequest("GET", url, "", NULL, 500, post_data, 0, result, result_headers);
    
    if (res == -1) {
        Print("WebRequest error code = ", GetLastError());
        return "HOLD";
    }
    
    // Convert response to string
    string signal = CharArrayToString(result);
    Print("Signal received: " + signal);
    
    return signal;
}

//+------------------------------------------------------------------+
//| OnTick function                                                 |
//+------------------------------------------------------------------+
void OnTick()
{
    // Get signal every 5 minutes
    static datetime last_check = 0;
    datetime current = TimeCurrent();
    
    if (current - last_check >= 300) // 5 minutes
    {
        string signal = GetTradingSignal();
        
        if (signal == "BUY")
        {
            // Place BUY order
            Print("BUY signal received!");
        }
        else if (signal == "SELL")
        {
            // Place SELL order
            Print("SELL signal received!");
        }
        else
        {
            Print("HOLD signal");
        }
        
        last_check = current;
    }
}
```

---

## 📊 Performance Requirements

Your API must meet these requirements:

| Metric | Target | Requirement |
|--------|--------|-------------|
| Response Time | < 1 second | ✅ Achievable with TwelveData |
| Availability | 99.5% uptime | ✅ Supported by services |
| Requests/sec | 100+ | ✅ Scalable |
| Concurrent Users | 1000+ | ✅ With load balancing |

---

## 🐛 Troubleshooting

### Issue: 401 Unauthorized

**Solution:** Check API key is correct
```bash
# Verify API key in database
curl "http://localhost:5000/api/user" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Issue: 429 Rate Limited

**Solution:** API rate limits exceeded
- Alpha Vantage: 5 calls/min free tier
- TwelveData: 800 calls/day free tier
- **Action:** Wait or upgrade API plan

### Issue: Slow Response (>5 seconds)

**Solution:** Data fetching is slow
- Use TwelveData (real-time) instead of Alpha Vantage
- Cache responses temporarily
- Reduce data points requested

### Issue: 500 Internal Server Error

**Solution:** Check logs
```bash
# On Render/Railway, check logs in dashboard
# On DigitalOcean:
tail -f /var/log/syslog | grep gunicorn
```

---

## 💰 Cost Breakdown

### Free/Low-Cost Options

| Service | Cost | Trade-offs |
|---------|------|-----------|
| Render.com | Free (limited) | Sleeps on inactivity |
| Railway.app | $5/month | Limited credits |
| PythonAnywhere | Free | Limited resources |
| DigitalOcean | $5/month | Need to setup |

### API Costs (Data)

| Service | Cost | Limit |
|---------|------|-------|
| Alpha Vantage | Free | 5 calls/min |
| TwelveData | Free | 800 calls/day |
| TwelveData Pro | $9/month | 100k calls/month |

---

## 📈 Scaling to Production

### Stage 1: MVP (Current)
- Single server
- SQLite database
- Basic monitoring
- **Cost:** ~$5/month

### Stage 2: Growing
- PostgreSQL database
- Redis caching
- Better monitoring (Sentry)
- **Cost:** ~$20-50/month

### Stage 3: Enterprise
- Load balancer
- Multiple servers
- CDN
- Database replication
- **Cost:** $100+/month

---

## 🔗 Deployment Summary

1. **Choose platform:** Render.com (easiest) or DigitalOcean (best control)
2. **Add environment variables** with your API keys
3. **Set start command** to run Flask with gunicorn
4. **Enable HTTPS** (usually automatic)
5. **Test endpoint** with curl or browser
6. **Monitor logs** for errors
7. **Setup alerts** for downtime

---

## 📚 Additional Resources

- [Flask Production Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Nginx Reverse Proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Let's Encrypt SSL](https://letsencrypt.org/)
- [Render.com Docs](https://render.com/docs)
- [Railway.app Docs](https://docs.railway.app/)

---

## ✅ Quick Start (Render.com)

1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create Web Service
4. Select repository
5. Add start command: `cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT src.api.flask_app:app`
6. Add environment variables
7. Deploy
8. Get your URL: `https://sofai-fx-api.onrender.com`
9. Test: `curl "https://sofai-fx-api.onrender.com/signal?apikey=KEY&symbol=EURUSD&format=text"`

**Total time: ~5 minutes** ⚡
