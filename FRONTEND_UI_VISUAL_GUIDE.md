# Frontend UI Visual Guide

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  SofAi FX Bot          👤 User Name        🔄 Refresh | 🚪 Logout   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Stats: Total: 10  │  BUY: 6  │  SELL: 2  │  AVG: 78%              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ⚡ Quick Analysis                                                    │
│ [EURUSD____] [Analyze] [Analyze All] [Clear Signals]              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 📊 Live Forex Charts                                                 │
│ [EUR/USD] [GBP/USD] [USD/JPY] ... [Timeframe: 1hour ▼]             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    📈 Candlestick Chart                         │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  Price: $1.0850  │  24h: +0.5%  │  High: $1.0890  │  Low: $1.0800  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 🔔 Latest Signals                        ℹ️ Info                     │
│                                                                      │
│ • EURUSD BUY @ 1.0850 (85%)             Status: Running             │
│   RSI 35%, MA 35%, SR 30%                Last: 2 min ago             │
│   ...                                    Monitored: 5 pairs          │
│                                                                      │
│ • GBPUSD SELL @ 1.3200 (72%)            [Load Config]               │
│   ...                                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 📋 Signal History (Table)                                            │
│ Pair | Signal | Price | Conf | AI | Filter | Agreement | Time      │
│ EURUSD | BUY  | 1.085 | 85%  | 80 | 2/3 | 3/3 | 2m ago              │
│ GBPUSD | SELL | 1.32  | 72%  | 70 | 2/3 | 3/3 | 5m ago              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 💡 PAIR RECOMMENDATIONS          [🔄 Refresh]  ← NEW FEATURE       │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 📈 EURUSD   │  │ 📉 GBPUSD   │  │ 😴 USDJPY   │              │
│  │ trending up │  │ trending dn │  │ low vol     │              │
│  │             │  │             │  │             │              │
│  │ Total:2 BUY │  │ Total:1 SELL│  │ Total:1 HLD │              │
│  │ Conf:80%    │  │ Conf:78%    │  │ Conf:65%    │              │
│  │ ████████░░ │  │ ███████░░░ │  │ ██████░░░░ │              │
│  │             │  │             │  │             │              │
│  │[Analyze][Mnt]  │[Analyze][Mnt]  │[Analyze][Mnt]  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│  Based on your signal history (24 hours)                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ SETTINGS & PREFERENCES          ← NEW FEATURE                   │
│                                                                      │
│ 📌 Monitored Pairs (Select pairs to monitor)                        │
│    [✓] EURUSD  [✓] GBPUSD  [ ] USDJPY  [ ] AUDUSD                 │
│    [ ] USDCAD  [ ] EURGBP  [ ] EURJPY  [ ] NZDUSD                 │
│                                                                      │
│ 🤖 Auto-Analysis                                                     │
│    Enable: [ON ⚪────]                                               │
│    Interval: [Every 1 hour ▼]  [Test]                              │
│                                                                      │
│ 📊 Confidence Thresholds                                            │
│    Min Confidence: [────●─] 75%                                     │
│    High Alerts: [OFF ⚪────]                                         │
│    Alert Level: [─────●──] 80%                                      │
│                                                                      │
│                    [💾 Save] [🔄 Reset]                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 🤖 AUTO-ANALYSIS SCHEDULER          ← NEW FEATURE                  │
│                                                                      │
│ ● Running              Uptime: 01:23:45                             │
│                                                                      │
│ 📋 Job Details                                                       │
│ Pairs: EURUSD, GBPUSD                                               │
│ Interval: 1 hour                                                    │
│ Next Run: 13:30:00                                                  │
│ Status: ✓ Enabled                                                   │
│                                                                      │
│          [▶ Start] [⏹ Stop] [⏸ Pause] [🔄 Refresh]                 │
│                                                                      │
│ Monitored: 2 │ Next Run: 13:30 │ Interval: 1h │ Last: Never       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 🤖 SofAi FX Trading Bot v1.0 | AI-Powered Forex Analysis           │
│ ⚠️ Disclaimer: Trading signals for educational purposes only        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Pair Recommendations Cards

### Card States

#### Normal State
```
┌────────────────────────────────┐
│ 📈 EURUSD                      │
│ 2 BUY signals - trending up!   │
├────────────────────────────────┤
│ Total: 2│BUY:2│SELL:0│HLD:0  │
├────────────────────────────────┤
│ Avg Confidence: 80%            │
│ ████████░░ (visual bar)        │
├────────────────────────────────┤
│ [Analyze] [Monitor]            │
└────────────────────────────────┘
```

#### Hover State
```
┌────────────────────────────────┐  ↑ Lifts up 4px
│ 📈 EURUSD                      │  ⬆ Shadow expands
│ 2 BUY signals - trending up!   │
├────────────────────────────────┤
│ Total: 2│BUY:2│SELL:0│HLD:0  │
├────────────────────────────────┤
│ Avg Confidence: 80%            │
│ ████████░░                     │
├────────────────────────────────┤
│ [Analyze] [Monitor]            │
└────────────────────────────────┘
```

### Trend Types

```
📈 TRENDING UP
   Description: More BUY signals
   Color: Green
   Background: rgba(34, 197, 94, 0.1)

📉 TRENDING DOWN  
   Description: More SELL signals
   Color: Red
   Background: rgba(239, 68, 68, 0.1)

➡️ CONSOLIDATING
   Description: Mix of BUY and SELL
   Color: Yellow
   Background: rgba(234, 179, 8, 0.1)

😴 LOW VOLATILITY
   Description: Mostly HOLD signals
   Color: Blue
   Background: rgba(59, 130, 246, 0.1)
```

---

## Feature 2: Settings Form

### Section: Monitored Pairs

```
┌─────────────────────────────────────────────────────┐
│ 📌 Monitored Pairs                                  │
│ Select which pairs to monitor for analysis          │
│                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ ☑ EURUSD │ │ ☑ GBPUSD │ │ ☐ USDJPY │            │
│ └──────────┘ └──────────┘ └──────────┘            │
│                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ ☐ AUDUSD │ │ ☐ USDCAD │ │ ☐ EURGBP │            │
│ └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────┘
```

### Section: Auto-Analysis

```
┌─────────────────────────────────────────────────────┐
│ 🤖 Auto-Analysis                                    │
│                                                     │
│ Enable Auto-Analysis                                │
│ [      ⚪ OFF      ] [      ● ON       ]            │
│        ← Toggle Switch (animated)                  │
│                                                     │
│ Analysis Interval                                   │
│ [Every 1 hour ▼]  [Test]                           │
│                                                     │
│ Options:                                            │
│ • Every 15 minutes                                  │
│ • Every 30 minutes                                  │
│ • Every 1 hour (selected)                          │
│ • Every 2 hours                                     │
│ • Every 4 hours                                     │
│ • Every 24 hours                                    │
└─────────────────────────────────────────────────────┘
```

### Section: Confidence Thresholds

```
┌─────────────────────────────────────────────────────┐
│ 📊 Confidence Thresholds                            │
│                                                     │
│ Minimum Confidence:               75%               │
│ [════════●═════════════════════════] 50% --------- 99% │
│     ↑ Green thumb, glows on hover                  │
│                                                     │
│ High Confidence Alerts                              │
│ [      ⚪ OFF      ] [      ● ON       ]            │
│                                                     │
│ Alert when confidence exceeds:    80%               │
│ [════════════●────────────════════] 50% --------- 99% │
└─────────────────────────────────────────────────────┘
```

### Buttons

```
┌──────────────────────────────────────────────────────┐
│ [💾 Save Settings ]  [🔄 Reset]                    │
│  Green gradient      Slate gray                      │
│  Hover: Scale up     Hover: Scale up                │
│  Click: Spin icon    Click: Reload page             │
└──────────────────────────────────────────────────────┘
```

---

## Feature 3: Scheduler Controls

### Status Card

```
┌────────────────────────────────────┐
│ ● Running              Uptime:     │
│ (green pulsing dot)    01:23:45    │
│                                    │
│ 📋 Job Details                     │
│ ├─ Pairs: EURUSD, GBPUSD          │
│ ├─ Interval: 1 hour               │
│ ├─ Next Run: 13:30:00             │
│ └─ Status: ✓ Enabled              │
└────────────────────────────────────┘
```

### Control Buttons

```
┌─────────────────────────────────────────────────────┐
│ [▶ Start]  [⏹ Stop]  [⏸ Pause]  [🔄 Refresh]      │
│  Green      Red       Yellow       Slate            │
│  Active     Active    Disabled*    Always Active    │
│  *Feature in development                           │
└─────────────────────────────────────────────────────┘
```

### Quick Stats

```
┌────────────┬───────────┬──────────┬──────────┐
│ Pairs      │ Next Run  │ Interval │ Last Run │
│ Monitored  │ Time      │ Duration │ Timestamp│
├────────────┼───────────┼──────────┼──────────┤
│     2      │ 13:30:00  │   1h     │  Never   │
│ (blue)     │ (yellow)  │ (green)  │(purple)  │
└────────────┴───────────┴──────────┴──────────┘
```

---

## Notifications System

### Success Notification
```
┌────────────────────────────────────┐
│ ✓ Settings saved successfully!     │
│ [auto-dismiss in 4s or click X]    │ ← Green bg
│                                    │
│ Appears: Bottom-right corner       │
│ Animation: Fade-in from bottom     │
│ Duration: 4 seconds               │
└────────────────────────────────────┘
```

### Error Notification
```
┌────────────────────────────────────┐
│ ✗ Failed to save settings          │
│ [auto-dismiss in 4s or click X]    │ ← Red bg
└────────────────────────────────────┘
```

### Info Notification
```
┌────────────────────────────────────┐
│ ℹ Pause feature coming soon        │
│ [auto-dismiss in 4s or click X]    │ ← Blue bg
└────────────────────────────────────┘
```

---

## Responsive Design

### Mobile (< 768px)

```
┌─────────────────────┐
│ SofAi FX Bot        │
│ 👤 User | 🚪 Logout│
└─────────────────────┘

Recommendations: 1 column
┌─────────────────────┐
│ 📈 EURUSD           │
│ trending up         │
│                     │
│ [Analyze] [Monitor] │
└─────────────────────┘

Settings: Stacked
┌─────────────────────┐
│ Pairs               │
│ [✓] [✓] [✓] [✓]    │
│ [✓] [✓] [✓] [✓]    │
│                     │
│ Toggle              │
│ [ON]                │
│                     │
│ [Save] [Reset]      │
└─────────────────────┘
```

### Tablet (768px - 1024px)

```
Recommendations: 2 columns
┌────────────┬────────────┐
│ 📈 EURUSD  │ 📉 GBPUSD  │
│ trending up│ trending dn│
│            │            │
│ [Btn][Btn] │ [Btn][Btn] │
└────────────┴────────────┘
```

### Desktop (> 1024px)

```
Recommendations: 4 columns
┌────────┬────────┬────────┬────────┐
│EURUSD  │GBPUSD  │USDJPY  │EURGBP │
│   ◡    │   ◡    │   ◡    │   ◡    │
└────────┴────────┴────────┴────────┘
```

---

## Animations

### Fade In (New Cards)
```
Step 1:  opacity: 0, transform: translateY(20px)
Step 2:  opacity: 0.5, transform: translateY(10px)
Step 3:  opacity: 1, transform: translateY(0)
Duration: 0.3s
```

### Hover Lift (Card Hover)
```
Original: transform: scale(1), shadow: small
Hover:    transform: translateY(-4px), shadow: large
Duration: 0.3s ease
```

### Pulse (Status Indicator)
```
Step 1: opacity: 1
Step 2: opacity: 0.5
Step 3: opacity: 1
Duration: 2s infinite
```

### Toggle Animation (Switch)
```
OFF → ON:  left: 3px → left: 27px
           bg: gray → bg: green
Duration:  0.4s smooth
```

---

## Color Scheme

### Primary Colors
```
Success:  #22c55e (Green)    - Actions, running, positive
Danger:   #ef4444 (Red)      - Errors, stop, negative
Warning:  #eab308 (Yellow)   - Alerts, caution
Info:     #3b82f6 (Blue)     - Information, secondary actions
```

### Background Colors
```
Primary:   #0f172a (Slate-900)
Secondary: #1e293b (Slate-800)
Tertiary:  #334155 (Slate-700)
Accent:    #475569 (Slate-600)
```

### Text Colors
```
Primary:   #ffffff (White)
Secondary: #e2e8f0 (Gray-200)
Muted:     #94a3b8 (Gray-400)
Subtle:    #64748b (Gray-500)
```

---

## Accessibility Features

- ✅ High contrast colors (WCAG AA)
- ✅ Keyboard navigable (Tab, Enter, Space)
- ✅ Focus visible (outline on interactive elements)
- ✅ Semantic HTML (button, input, label, form)
- ✅ ARIA labels on toggles
- ✅ Touch-friendly (48px+ tap targets)
- ✅ Screen reader compatible
- ✅ Readable font sizes (16px minimum)

---

## Performance Metrics

- Load Time: < 2 seconds
- Time to Interactive: < 3 seconds
- Recommendation Refresh: Every 5 minutes
- Scheduler Status Update: Every 5 seconds
- CSS Animations: GPU accelerated
- No layout thrashing
- Debounced API calls

---

This visual guide shows the complete UI/UX for all three new features! 🎨

