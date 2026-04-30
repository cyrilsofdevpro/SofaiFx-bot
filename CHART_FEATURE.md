# 📊 Multi-Pair Trading Chart Tabs Feature

## Overview

The dashboard now includes an interactive **Live Forex Charts** section with multi-pair support and dynamic chart switching. Users can easily browse different currency pairs and timeframes without page reloads.

## ✨ Features

### 1. **Currency Pair Tabs**
- **5 Pre-configured Pairs**:
  - EUR/USD
  - GBP/USD
  - USD/JPY
  - AUD/USD
  - USD/CAD
- **One-Click Switching**: Click any tab to instantly switch charts
- **Active Tab Indicator**: Green gradient highlight shows current pair
- **Smooth Transitions**: No page reloads, instant chart updates

### 2. **Dynamic Timeframe Selection**
Dropdown menu with 6 timeframe options:
- **1min** - Real-time minute candles
- **5min** - 5-minute intervals
- **15min** - Quarter-hour intervals
- **1hour** - Hourly candles (default)
- **4hour** - 4-hour candles
- **1day** - Daily candles

### 3. **Candlestick Charts**
- **TradingView Lightweight Charts**: Professional-grade charting library
- **Real OHLC Data**: 
  - Primary: TwelveData API (1-minute data)
  - Fallback: Alpha Vantage (daily data)
- **50+ Candles**: Historical data display
- **Responsive Design**: Auto-resizes on window resize

### 4. **Chart Information Panel**
Real-time metrics displayed below chart:
- **Current Price**: Latest close price
- **24h Change**: Price change percentage
- **High**: Period high price
- **Low**: Period low price

## 🏗️ Architecture

### Frontend Components

#### **HTML Structure** ([index.html](frontend/index.html))
```html
<!-- Trading Charts Section -->
<div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
    <!-- Pair Tabs -->
    <div class="flex flex-wrap gap-2 mb-4 pb-4 border-b border-slate-700">
        <button class="pair-tab active-tab" data-pair="EURUSD" onclick="changePair('EURUSD')">
            EUR/USD
        </button>
        <!-- More tabs... -->
    </div>
    
    <!-- Timeframe Selector -->
    <select id="timeframe-select" onchange="changeTimeframe(this.value)">
        <option value="1">1min</option>
        <option value="60" selected>1hour</option>
        <!-- More options... -->
    </select>
    
    <!-- Chart Container -->
    <div id="trading-chart" style="height: 400px; width: 100%;"></div>
    
    <!-- Chart Info Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div id="chart-current-price">--</div>
        <!-- More info cards... -->
    </div>
</div>
```

#### **CSS Styling** ([style.css](frontend/assets/css/style.css))
```css
/* Pair Tab Styles */
.pair-tab {
    background-color: #475569;
    color: #d1d5db;
    border: 1px solid #374151;
    transition: all 0.3s ease;
}

.pair-tab.active-tab {
    background: linear-gradient(135deg, #10b981, #3b82f6);
    color: #ffffff;
    border-color: #059669;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}
```

#### **JavaScript Functions** ([dashboard.js](frontend/assets/js/dashboard.js))

**Key Functions**:

```javascript
// Initialize chart on page load
function initTradingChart()
```
- Creates TradingView Lightweight chart instance
- Sets up candlestick series
- Loads initial data
- Auto-fits content

```javascript
// Switch to different pair
function changePair(pair)
```
- Updates active tab styling
- Fetches new data for pair
- Re-renders chart

```javascript
// Change timeframe
function changeTimeframe(timeframe)
```
- Updates current timeframe
- Refreshes chart data

```javascript
// Fetch OHLC data
async function updateChartData()
```
- Calls `/api/chart-data` endpoint
- Formats data for TradingView
- Updates chart and info cards
- Handles API failures with mock data fallback

```javascript
// Generate mock data
function generateMockChartData(pair, timeframe)
```
- Creates realistic test data
- Used when API fails or for demo mode
- Maintains consistent base prices per pair

### Backend Endpoint

#### **New Flask Route** ([flask_app.py](backend/src/api/flask_app.py))

```python
@app.route('/api/chart-data', methods=['GET'])
def get_chart_data():
    """Get OHLC data for charting
    
    Query params:
    - symbol: Currency pair (e.g., EURUSD)
    - timeframe: Timeframe in minutes (1, 5, 15, 60, 240, 1440)
    """
```

**Logic Flow**:
1. Validates symbol format (6 characters)
2. Maps timeframe to API interval
3. Attempts to fetch from TwelveData API
4. Falls back to Alpha Vantage if needed
5. Formats OHLC data for chart
6. Returns JSON with candlestick data

**Response Format**:
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
    ...
  ],
  "count": 50
}
```

## 🔄 Data Flow

```
User clicks tab (EUR/USD)
    ↓
changePair('EURUSD') triggered
    ↓
updateChartData() called
    ↓
Fetch /api/chart-data?symbol=EURUSD&timeframe=60
    ↓
Backend queries TwelveData API (real-time 1-min data)
    ↓
If TwelveData fails → Alpha Vantage fallback (daily data)
    ↓
Format 50 OHLC candles
    ↓
Return JSON response
    ↓
Parse data in updateChartData()
    ↓
Map to TradingView format
    ↓
candleStickSeries.setData(chartBars)
    ↓
Chart displays with new candles
    ↓
Update info cards (price, change, high, low)
```

## 📱 User Experience

### Desktop (4K)
- Full-width chart with tabs on one line
- Clear timeframe dropdown
- All info cards visible
- Responsive candlestick rendering

### Tablet/Mobile
- Stacked layout for tabs
- Chart height adapts to viewport
- Info cards in 2-column grid
- Touch-friendly button sizing

### Interactions
- **Tab Click**: Instant chart update (< 500ms)
- **Timeframe Change**: New data fetch and re-render
- **Window Resize**: Chart auto-scales
- **Mouse Hover**: Tab highlight on inactive tabs
- **Keyboard**: None (pure mouse/touch interface)

## 🔧 Configuration

### Supported Pairs (Extensible)
Edit `index.html` to add more pairs:

```html
<!-- Add new pair tab -->
<button class="pair-tab" data-pair="NZDUSD" onclick="changePair('NZDUSD')">
    NZD/USD
</button>
```

Update base prices in `generateMockChartData()`:
```javascript
const basePrice = {
    'EURUSD': 1.1680,
    'GBPUSD': 1.3463,
    'NZDUSD': 0.6150,  // Add new pair
    // ...
}[pair] || 1.1680;
```

### Chart Settings
Modify in `initTradingChart()`:

```javascript
tradingChart = LightweightCharts.createChart(container, {
    layout: {
        textColor: '#d1d5db',           // Candlestick label color
        background: { color: '#0f172a' } // Chart background
    },
    timeScale: {
        timeVisible: true,              // Show time labels
        secondsVisible: false           // Hide seconds
    }
});

window.candleStickSeries = tradingChart.addCandlestickSeries({
    upColor: '#10b981',        // Bullish candle (green)
    downColor: '#ef4444',      // Bearish candle (red)
    borderUpColor: '#10b981',
    borderDownColor: '#ef4444',
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444'
});
```

## 🚀 Performance Optimizations

1. **Single Chart Instance**: One chart object, no duplicates
2. **Data Caching**: TwelveData and Alpha Vantage caching
3. **Debounced Resize**: Window resize handled efficiently
4. **Lazy Loading**: Chart initialized on DOM ready
5. **Auto-Refresh**: Updates every 60 seconds (configurable)
6. **Fallback Data**: Mock data prevents blank charts on API failure

## 🛡️ Error Handling

| Error | Behavior |
|-------|----------|
| API timeout | Falls back to mock data, shows chart |
| Invalid symbol | Returns 400 error, chart stays same |
| No data available | Shows mock data, logs warning |
| Network error | Uses cached mock data, continues |
| Chart library error | Logs error, can retry with refresh |

## 📊 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Chart Library** | TradingView Lightweight Charts |
| **Frontend Framework** | Tailwind CSS + Vanilla JS |
| **Backend API** | Flask + Python |
| **Data Source** | TwelveData API + Alpha Vantage |
| **Styling** | Tailwind CSS (responsive grid) |

## 🔗 Related Files

```
frontend/
├── index.html              # Chart UI structure
├── assets/
│   ├── css/
│   │   └── style.css       # Tab and chart styling
│   └── js/
│       └── dashboard.js    # Chart functions (750+ lines added)

backend/
├── src/
│   └── api/
│       └── flask_app.py    # /api/chart-data endpoint
└── main.py                 # Entry point
```

## 📋 Checklist

- ✅ TradingView Lightweight Charts CDN added
- ✅ Chart container HTML created
- ✅ Pair tabs with onclick handlers
- ✅ Timeframe dropdown with change handler
- ✅ CSS styling for active/inactive tabs
- ✅ Chart initialization function
- ✅ Pair switching function
- ✅ Timeframe changing function
- ✅ Chart data fetching function
- ✅ Mock data generation function
- ✅ Window resize handler
- ✅ Info cards update logic
- ✅ Backend `/api/chart-data` endpoint
- ✅ TwelveData integration with fallback
- ✅ Error handling and recovery
- ✅ Auto-refresh every 60 seconds
- ✅ Responsive design (mobile-friendly)

## 🎯 Future Enhancements

- [ ] Add technical indicators (SMA, EMA, RSI, Bollinger Bands)
- [ ] Implement drawing tools (trend lines, support/resistance)
- [ ] Add trading signal overlays on chart
- [ ] Save favorite pairs and timeframes
- [ ] Chart export (PNG, SVG)
- [ ] Multi-chart layout (compare pairs side-by-side)
- [ ] Advanced order types on chart
- [ ] Volume bars
- [ ] Pattern recognition overlays

## 🐛 Troubleshooting

### Chart Not Loading
- Check browser console for errors
- Verify TradingView CDN is loaded
- Check backend `/api/chart-data` endpoint is working
- Try refreshing page

### Tabs Not Switching
- Ensure `changePair()` function is defined
- Check for JavaScript errors in console
- Verify tab `data-pair` attribute matches function parameter

### Wrong Data Displayed
- Confirm symbol format (6 chars: EURUSD)
- Check API responses in Network tab
- Verify timeframe mapping in backend

### Chart Lag on Tab Switch
- Check network latency (`/api/chart-data` response time)
- Reduce number of candles displayed
- Check for memory leaks in browser DevTools

## 📞 Support

For issues or feature requests, check:
1. Browser console (F12) for errors
2. Network tab for API response status
3. Backend logs for server-side errors
4. This documentation for configuration options
