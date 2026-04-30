# SofAi FX Frontend Features Guide

## Overview

The frontend has been enhanced with three powerful new features for managing trading signals and automating analysis:

1. **Pair Recommendations** - Visual cards showing the best pairs based on recent signals
2. **Settings & Preferences** - Configure monitored pairs, analysis intervals, and alerts
3. **Auto-Analysis Scheduler** - Start/stop/monitor background analysis jobs

---

## File Structure

```
frontend/
├── index.html                          # Main dashboard with new sections
├── assets/
│   ├── css/
│   │   ├── style.css                  # Original styles (150KB)
│   │   └── features.css               # NEW: Feature styles & animations
│   └── js/
│       ├── auth.js                    # Authentication (existing)
│       ├── dashboard.js               # Dashboard logic (existing)
│       ├── utils.js                   # NEW: Shared utilities
│       ├── recommendations.js         # NEW: Recommendations manager
│       ├── settings.js                # NEW: Settings manager
│       └── scheduler.js               # NEW: Scheduler manager
```

---

## Feature 1: Pair Recommendations

### Purpose
Automatically analyzes your signal history and recommends the most active/promising currency pairs.

### Location
Dashboard → "Pair Recommendations" section (below charts)

### How It Works

1. **Data Source**: Fetches from `GET /api/recommendations`
2. **Display**: Shows up to 4 pairs in a responsive grid
3. **Trends**: Identifies 4 trend types:
   - 📈 **Trending Up**: More BUY signals recently
   - 📉 **Trending Down**: More SELL signals recently
   - ➡️ **Consolidating**: Mix of BUY and SELL
   - 😴 **Low Volatility**: Mostly HOLD signals

### Card Information

```
┌─────────────────────────────┐
│ 📈 EURUSD                   │
│ 2 BUY signals - trending up │
├─────────────────────────────┤
│ Total: 2 | BUY: 2 | SELL: 0 │
│ HOLD: 0                      │
├─────────────────────────────┤
│ Avg Confidence: 80%         │
│ ████████░░                  │
├─────────────────────────────┤
│ [Analyze] [Monitor]         │
└─────────────────────────────┘
```

### User Actions

- **Analyze Button**: Run quick analysis on that pair
- **Monitor Button**: Add to your monitored pairs list
- **Refresh Button**: Manually refresh recommendations
- **Auto-Refresh**: Automatically updates every 5 minutes

### Example Response

```json
{
  "success": true,
  "recommendations": [
    {
      "symbol": "EURUSD",
      "trend": "trending_up",
      "emoji": "📈",
      "description": "2 BUY signals recently - trending up!",
      "full_message": "📈 EURUSD: 2 BUY signals recently - trending up!",
      "stats": {
        "total_signals": 2,
        "buy_signals": 2,
        "sell_signals": 0,
        "hold_signals": 0,
        "avg_confidence": "80%",
        "hours_lookback": 24
      }
    }
  ],
  "total_pairs": 4,
  "period_hours": 24,
  "timestamp": "2026-04-24T19:27:46.551427"
}
```

---

## Feature 2: Settings & Preferences

### Purpose
Manage which pairs you monitor, configure auto-analysis intervals, and set confidence thresholds.

### Location
Dashboard → "Settings & Preferences" section (middle area)

### Sections

#### 2.1 Monitored Pairs
```
Select which pairs to monitor for analysis
[✓] EURUSD  [✓] GBPUSD  [ ] USDJPY  [ ] AUDUSD
[ ] USDCAD  [ ] EURGBP  [ ] EURJPY  [ ] NZDUSD
```

**Actions:**
- Click checkbox to select/deselect
- Selected pairs are analyzed by auto-analysis job
- Maximum 8 major pairs available

#### 2.2 Auto-Analysis Configuration
```
Enable Auto-Analysis: [ON/OFF toggle]

Analysis Interval:
[Dropdown: Every 15 min / 30 min / 1 hour / 2 hour / 4 hour / 24 hour] [Test]

Current Interval: Every 1 hour
```

**Features:**
- Toggle to enable/disable automatic analysis
- Choose interval (15 min to 24 hours)
- Test button validates configuration

#### 2.3 Confidence Thresholds
```
Minimum Confidence: [====O==] 75%

High Confidence Alerts: [ON/OFF toggle]
Alert when confidence exceeds: [========O] 80%
```

**Features:**
- Minimum confidence slider (50%-99%)
- High confidence alert toggle
- Alert threshold slider
- Live percentage display

### Save Functionality

- **Save Settings** button posts all preferences to API
- **Reset** button reloads from database
- **Notifications**:
  - ✅ Green: Settings saved successfully
  - ❌ Red: Save failed
  - ℹ️ Blue: Info messages

### Stored Settings

```json
{
  "monitored_pairs": ["EURUSD", "GBPUSD"],
  "auto_analysis_enabled": true,
  "auto_analysis_interval": 3600,
  "min_confidence_threshold": 0.75,
  "alert_on_high_confidence": true,
  "alert_high_confidence_threshold": 0.8
}
```

---

## Feature 3: Auto-Analysis Scheduler

### Purpose
Automatically analyze your monitored pairs on a schedule without manual intervention.

### Location
Dashboard → "Auto-Analysis Scheduler" section (bottom area)

### Status Card

```
┌─────────────────────────────────┐
│ ● Running        Uptime: 01:23:45│
├─────────────────────────────────┤
│ Job Details                      │
│ Pairs: EURUSD, GBPUSD            │
│ Interval: 1h                      │
│ Next Run: 13:30:00                │
│ Status: ✓ Enabled                │
└─────────────────────────────────┘
```

### Control Buttons

```
[▶ Start] [⏹ Stop] [⏸ Pause] [🔄 Refresh]
```

**Buttons:**
- **Start**: Creates background job for monitored pairs
  - Uses interval from settings
  - Job runs automatically in backend
- **Stop**: Terminates the current job
  - Cancels all future runs
  - Status becomes red
- **Pause**: Pauses job (feature in development)
  - Will resume without recreating job
- **Refresh**: Manually update status display
  - Queries `/api/auto-analysis/status`

### Quick Statistics

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Pairs        │ Next Run     │ Interval     │ Last Run     │
│ Monitored: 2 │ 13:30:00     │ 1 hour       │ Never        │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Status Indicator

- **Green Pulsing Dot**: Auto-analysis running
- **Red Dot**: Auto-analysis stopped
- **Animated**: Real-time updates every 5 seconds

### Job Lifecycle

1. **Start**: User clicks "Start" button
2. **Created**: Backend creates APScheduler job
3. **Running**: Job executes analysis every N seconds
4. **Stop**: User clicks "Stop" or closes browser
5. **Terminated**: Backend removes job

### Example API Response

```json
{
  "success": true,
  "active": true,
  "jobs": [
    {
      "user_id": 1,
      "pairs": ["EURUSD", "GBPUSD"],
      "interval_seconds": 3600,
      "next_run": "2026-04-24T13:30:00",
      "enabled": true
    }
  ]
}
```

---

## How to Use

### First Time Setup

1. **Login** to your account
2. **Go to Settings & Preferences**
3. **Select Pairs** - Choose which pairs to monitor
4. **Configure Interval** - Choose analysis frequency
5. **Save** - Click "Save Settings"

### Start Auto-Analysis

1. **Go to Auto-Analysis Scheduler**
2. **Click [▶ Start]** button
3. **Confirm** - Status becomes green
4. **Wait** - Analysis runs automatically
5. **View Results** - Check "Latest Signals" for new signals

### View Recommendations

1. **Scroll to Pair Recommendations**
2. **See Cards** - Shows trending pairs
3. **Click Analyze** - Run analysis on specific pair
4. **Click Monitor** - Add pair to your list
5. **Refresh** - Get latest data

### Troubleshooting

**Recommendations not loading:**
- Check browser console for errors (F12)
- Verify token is valid
- Try refresh button
- Check Flask is running on port 5000

**Auto-analysis won't start:**
- Select at least one pair in settings
- Save settings first
- Check Flask for errors
- Verify network connection

**Settings won't save:**
- Check authentication token
- Verify all fields have valid values
- Try refresh button
- Check network tab in DevTools

---

## Styling & Customization

### Colors
- **Primary**: Green (#22c55e) - Success, active
- **Secondary**: Blue (#3b82f6) - Info, actions
- **Danger**: Red (#ef4444) - Errors, stop
- **Warning**: Yellow (#eab308) - Warnings, caution

### Animations
- **Cards**: Lift on hover with shadow
- **Buttons**: Scale up on hover
- **Notifications**: Fade in from bottom
- **Status**: Pulse animation when running
- **Toggles**: Smooth 0.4s animation

### Responsive
- **Mobile**: 1 column, full width
- **Tablet**: 2 columns, 80% width
- **Desktop**: 4 columns, centered

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/recommendations?hours=24` | Get pair recommendations |
| GET | `/api/preferences` | Load user preferences |
| POST | `/api/preferences` | Save preferences |
| POST | `/api/auto-analysis/start` | Start analysis job |
| POST | `/api/auto-analysis/stop` | Stop analysis job |
| GET | `/api/auto-analysis/status` | Get job status |

---

## JavaScript Objects

### recommendationsManager
```javascript
recommendationsManager.fetchRecommendations(hours=24)
recommendationsManager.refresh()
recommendationsManager.renderRecommendations()
```

### settingsManager
```javascript
settingsManager.loadPreferences()
settingsManager.savePreferences()
settingsManager.updatePairSelection()
settingsManager.toggleAutoAnalysis(enabled)
```

### schedulerManager
```javascript
schedulerManager.startAutoAnalysis()
schedulerManager.stopAutoAnalysis()
schedulerManager.getJobStatus()
schedulerManager.pauseAutoAnalysis()
schedulerManager.resumeAutoAnalysis()
```

### UIUtils (Shared Utilities)
```javascript
analyzeSymbol(symbol)
addToMonitored(symbol)
showNotification(message, type)
getConfidenceColor(confidence)
getSignalColor(signal)
isAuthenticated()
getCurrentUserId()
```

---

## Performance

- **Recommendations**: Auto-refresh every 5 minutes (configurable)
- **Settings**: Load once on page start
- **Scheduler**: Status refresh every 5 seconds while running
- **Optimized**: Uses debounce for API calls
- **Lazy Loading**: Features initialize 1 second after page load

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires ES6 support and Fetch API.

---

## Future Enhancements

- [ ] WebSocket real-time updates
- [ ] Historical charts for recommendations
- [ ] Custom notification sounds
- [ ] Dark/light theme toggle
- [ ] Export data to CSV
- [ ] Mobile app version
- [ ] Pause/resume implementation
- [ ] Custom analysis templates

---

## Support

For issues or questions:
1. Check browser console (F12)
2. Verify Flask is running
3. Check network tab for failed requests
4. Review browser devtools
5. Check README files in respective directories

