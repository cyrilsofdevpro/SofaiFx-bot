# 🎯 Quick Start: Multi-Pair Chart Feature

## What Was Added

A fully functional **Live Forex Charts** section on the dashboard with:
- 5 currency pair tabs (EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD)
- Dynamic chart switching (no page reloads)
- 6 timeframe options (1min to 1day)
- Real OHLC candlestick charts using TradingView
- Live price data + metrics (high, low, 24h change)

## Files Modified

### Frontend
1. **[frontend/index.html](frontend/index.html)**
   - Added TradingView Lightweight Charts CDN
   - Added chart container and tabs section
   - Added timeframe dropdown and info cards

2. **[frontend/assets/css/style.css](frontend/assets/css/style.css)**
   - Added `.pair-tab` styling with gradients
   - Added `.active-tab` state with green gradient
   - Added chart container animations

3. **[frontend/assets/js/dashboard.js](frontend/assets/js/dashboard.js)**
   - Added `initTradingChart()` - Initialize chart
   - Added `changePair(pair)` - Switch currency pairs
   - Added `changeTimeframe(timeframe)` - Change timeframes
   - Added `updateChartData()` - Fetch OHLC from backend
   - Added `generateMockChartData()` - Fallback demo data
   - Added window resize handler for responsive charts

### Backend
1. **[backend/src/api/flask_app.py](backend/src/api/flask_app.py)**
   - Added `GET /api/chart-data` endpoint
   - Fetches OHLC from TwelveData (primary) or Alpha Vantage (fallback)
   - Returns JSON with candlestick data for chart

## How to Use

### Basic Usage
1. Open the dashboard (frontend loads)
2. Chart initializes with EUR/USD on 1-hour timeframe
3. Click any pair tab to switch instantly:
   - EUR/USD → Green gradient highlight
   - Chart updates with new OHLC data
4. Change timeframe dropdown for different intervals
5. View live metrics: Price, Change %, High, Low

### For Developers

**Add a new currency pair:**

1. Add tab in `index.html`:
```html
<button class="pair-tab" data-pair="NZDUSD" onclick="changePair('NZDUSD')">
    <i class="fas fa-chart-line"></i> NZD/USD
</button>
```

2. Add base price in `dashboard.js`:
```javascript
const basePrice = {
    'EURUSD': 1.1680,
    'NZDUSD': 0.6150,  // Add this
    // ...
}[pair] || 1.1680;
```

**Customize colors:**

In `dashboard.js` `initTradingChart()`:
```javascript
upColor: '#10b981',      // Green for buy
downColor: '#ef4444',    // Red for sell
```

**Change chart height:**

In `index.html`:
```html
<div id="trading-chart" style="height: 500px; width: 100%;"></div>
<!-- Change height: 400px to desired height -->
```

## Features

✅ **Multi-Pair Support** - 5 pairs pre-configured, easily extensible
✅ **No Page Reloads** - Instant chart switching
✅ **Real Data** - TwelveData API (1-min real-time) + Alpha Vantage fallback
✅ **Responsive** - Works on desktop, tablet, mobile
✅ **Auto-Refresh** - Updates chart every 60 seconds
✅ **Error Handling** - Falls back to mock data on API failure
✅ **Professional Charts** - TradingView Lightweight Charts library
✅ **Live Metrics** - Current price, change %, high, low

## API Endpoint

**GET** `/api/chart-data`

Query parameters:
```
symbol=EURUSD        (6-char currency pair)
timeframe=60         (minutes: 1, 5, 15, 60, 240, 1440)
```

Response:
```json
{
  "symbol": "EURUSD",
  "timeframe": "60",
  "ohlc": [
    {
      "time": 1682241600000,
      "open": 1.16801,
      "high": 1.16852,
      "low": 1.16750,
      "close": 1.16827
    },
    // 50 candles total
  ],
  "count": 50
}
```

## Testing

1. **Start Backend**:
```bash
cd backend
python main.py
```

2. **Open Dashboard**:
```
http://localhost:5000
# or
file:///path/to/frontend/index.html
```

3. **Test Interactions**:
   - Click EUR/USD tab → Chart updates
   - Click GBP/USD tab → Different data displayed
   - Change timeframe → Chart re-renders
   - Resize window → Chart scales

4. **Check Data**:
   - Open DevTools Network tab
   - Click a pair tab
   - See `/api/chart-data` request
   - Verify 50 candles in response

## Troubleshooting

**Issue**: Chart not showing
- **Solution**: Check DevTools console for errors, verify backend is running

**Issue**: Tabs not switching
- **Solution**: Verify `changePair()` function is defined, check browser console

**Issue**: Mock data instead of real data
- **Solution**: Confirm backend `/api/chart-data` is responding, check API keys

**Issue**: Chart freezes on resize
- **Solution**: Clear cache (Ctrl+Shift+Delete), refresh page (Ctrl+F5)

## Documentation

Full documentation with architecture, customization guide, and troubleshooting:
👉 [CHART_FEATURE.md](CHART_FEATURE.md)

## Next Steps

1. ✅ Start Flask backend
2. ✅ Test chart switching in browser
3. ✅ Verify real data is loading
4. ⏳ Add more pairs if needed
5. ⏳ Customize colors/sizing to match brand
6. ⏳ Consider adding technical indicators (future enhancement)

---

**Status**: ✅ **COMPLETE** - Multi-pair charts fully functional and tested!
