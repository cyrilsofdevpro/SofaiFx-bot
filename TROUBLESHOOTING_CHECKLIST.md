# Quick Troubleshooting Checklist

## Before Testing
- [ ] Delete old `sofai_fx.db` file (if exists) to start fresh
- [ ] Restart Flask API server
- [ ] Clear browser cache (Ctrl+Shift+Delete)
- [ ] Open browser DevTools (F12) to see console

## Testing Steps

### 1. Server Startup ✓
- [ ] Flask server starts without errors
- [ ] See log: `Database path: C:\...\sofai_fx.db`
- [ ] See log: `JWT Secret Key configured...`
- [ ] No import errors or exceptions

### 2. Authentication ✓
- [ ] Register new account (or login)
- [ ] See message: "Registration/Login successful"
- [ ] Token appears in browser storage
- [ ] Dashboard loads after login

### 3. Database Check ✓
- [ ] Go to `http://localhost:5000/api/diagnostics`
- [ ] See `"status": "ok"`
- [ ] See `"exists": true` for database
- [ ] `total_users` shows 1 or more

### 4. Signal Generation ✓
- [ ] Enter currency pair (EURUSD)
- [ ] Click "Analyze" button
- [ ] See modal appear with trading details
- [ ] Modal shows: Entry, Stop Loss, Take Profit
- [ ] Modal shows: Position Size, Risk/Reward, ATR
- [ ] No errors in browser console

### 5. Signal Saving ✓
- [ ] Check Flask logs for: `✅ Signal saved to database...`
- [ ] Check database size increased
- [ ] Try `/api/diagnostics` again
- [ ] `total_signals` should be 1 or higher

### 6. Signal Display ✓
- [ ] Check "Latest Signals" section on dashboard
- [ ] Signal should be visible (not showing 0)
- [ ] Shows: Symbol, Signal Type, Confidence %
- [ ] Shows: Timestamp of when analyzed
- [ ] Multiple signals appear in chronological order

### 7. Data Persistence ✓
- [ ] Refresh page (F5)
- [ ] Signals should still be visible
- [ ] Data persists even after reload
- [ ] Count matches `/api/diagnostics` output

## Common Issues & Fixes

### Issue: Database file doesn't exist
**Fix**: 
- Check file location: `c:\Users\Cyril Sofdev\Desktop\SofAi-Fx\sofai_fx.db`
- Try analyzing a pair - file should be created
- Check file permissions (must be writable)

### Issue: Signals show 0 even after analyzing
**Fix**:
- Check Flask logs for error messages
- Verify JWT token is valid (check browser storage)
- Try logging out and back in
- Delete database file and restart server

### Issue: Modal doesn't appear after clicking Analyze
**Fix**:
- Check browser console for errors
- Make sure API is responding (check Network tab)
- Try different currency pair
- Check server logs for API errors

### Issue: "No signals yet" message persists
**Fix**:
- Check if signal is being saved (look at logs)
- Check `/api/diagnostics` endpoint
- Verify user_id in token matches saved signals
- Check database file permissions

### Issue: API returns 401 Unauthorized
**Fix**:
- Check if logged in (look for `auth_token` in storage)
- Try logging out and back in
- Clear session storage and refresh
- Check JWT_SECRET_KEY matches in config

## Debug Commands

### Check Database File
```bash
ls -la c:\Users\Cyril Sofdev\Desktop\SofAi-Fx\sofai_fx.db
```

### Check Database Contents (from backend directory)
```bash
cd backend
python -c "
from src.models import Signal, User, init_db
from src.api.flask_app import app
init_db(app)
with app.app_context():
    print('Total Users:', User.query.count())
    print('Total Signals:', Signal.query.count())
    for s in Signal.query.all():
        print(f'  - User {s.user_id}: {s.symbol} {s.signal_type}')
"
```

### Check Server Logs
Look for these patterns:
- `✅ Signal generated for...` - Signal was created
- `✅ Saving signal for user_id=...` - About to save
- `✅ Signal saved to database...` - Successfully saved
- `✅ Retrieved X signals for user_id=...` - Successful retrieval
- `❌ Error...` - Any errors (red flags!)

### Browser Console Logs
Press F12 → Console tab
Look for:
- `🔄 Analyzing: /api/analyze` - Request sent
- `📨 Response status: 200` - Success
- `✓ Loaded X signals` - Signals retrieved
- Any red error messages

## Success Indicators ✅

All these should be true:
1. ✅ Database file exists at workspace root
2. ✅ `/api/diagnostics` shows signals
3. ✅ Modal appears when analyzing
4. ✅ "Latest Signals" section shows signals (not 0)
5. ✅ Signals persist after page refresh
6. ✅ Multiple signals appear in list
7. ✅ No errors in Flask logs
8. ✅ No errors in browser console
9. ✅ Different users see different signals
10. ✅ Timestamps are accurate

## Contact Points
If you need to check something:
- **Database State**: `GET /api/diagnostics`
- **Signals API**: `GET /api/signals?limit=50` (needs auth)
- **Analyze Signal**: `POST /api/analyze` (needs auth)
- **Health Check**: `GET /health`

---
**Note**: Some indicators like "Latest Signal showing 0" should be gone after this fix!
