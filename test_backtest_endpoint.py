#!/usr/bin/env python
"""Quick test for backtest results endpoint - all pairs"""
from flask import Flask
from backend.src.api.routes.dashboard_routes import get_backtest_results

app = Flask(__name__)

# Test with all pairs, 180 days
with app.test_request_context('/api/dashboard/backtest/results?range=180d'):
    result = get_backtest_results()
    print('Status:', result[1])
    import json
    data = json.loads(result[0].data)
    print(f'Pairs returned: {len(data.get("data", []))}')
    print()
    for r in data.get('data', []):
        print(f"  {r['pair']}: {r['total_trades']} trades, {r['win_rate']:.1f}% win, ${r['pnl']:.2f} PnL")
        print(f"    Max Drawdown: {r['max_drawdown']:.1f}%")
        print(f"    Equity curve: {len(r.get('equity_curve', []))} points")
        print(f"    Date range: {r['date_range']}")
        print()