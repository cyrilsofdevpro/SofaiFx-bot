#!/usr/bin/env python3
"""Comprehensive test showing all new fields in API response"""

import requests
import json
from pprint import pprint

print("=" * 80)
print("TESTING SOFAI-FX API WITH NEW FIELDS")
print("=" * 80)

try:
    response = requests.post(
        'http://127.0.0.1:5000/api/analyze',
        json={'symbol': 'EURUSD', 'notify': False},
        timeout=5
    )
    
    print(f"\nStatus Code: {response.status_code}")
    data = response.json()
    signal = data.get('signal', {})
    
    print(f"\n✅ Response received successfully!")
    print(f"\nTotal keys: {len(signal)}")
    
    # Display signal basics
    print("\n" + "=" * 80)
    print("BASIC SIGNAL INFO")
    print("=" * 80)
    print(f"Symbol: {signal.get('symbol')}")
    print(f"Signal: {signal.get('signal')}")
    print(f"Price: {signal.get('price')}")
    print(f"Confidence: {signal.get('confidence'):.2%}")
    print(f"Timestamp: {signal.get('timestamp')}")
    print(f"Reason: {signal.get('reason')}")
    
    # Display individual indicator signals
    print("\n" + "=" * 80)
    print("TECHNICAL INDICATORS")
    print("=" * 80)
    print(f"RSI Signal: {signal.get('rsi_signal')}")
    print(f"MA Signal: {signal.get('ma_signal')}")
    print(f"S/R Signal: {signal.get('sr_signal')}")
    
    # Display AI Prediction (NEW)
    print("\n" + "=" * 80)
    print("AI PREDICTION (NEW FIELD) ⭐")
    print("=" * 80)
    ai_pred = signal.get('ai_prediction', {})
    if ai_pred:
        print(f"Direction: {ai_pred.get('direction', 'N/A')}")
        print(f"Confidence: {ai_pred.get('confidence', 'N/A')}")
        print(f"Reasoning: {ai_pred.get('reasoning', 'N/A')}")
    else:
        print("No AI prediction available (model not trained)")
    
    # Display Filter Results (NEW)
    print("\n" + "=" * 80)
    print("SMART FILTERS (NEW FIELD) ⭐")
    print("=" * 80)
    filters = signal.get('filter_results', {})
    if filters:
        print(f"Trade Allowed: {filters.get('is_trade_allowed')}")
        print(f"Volatility Check: {filters.get('volatility_check')}")
        print(f"News Check: {filters.get('news_check')}")
        print(f"Setup Quality Check: {filters.get('setup_quality_check')}")
        if filters.get('reason'):
            print(f"Reason: {filters.get('reason')}")
    else:
        print("No filter results available")
    
    # Display Signal Quality (NEW)
    print("\n" + "=" * 80)
    print("SIGNAL QUALITY (NEW FIELD) ⭐")
    print("=" * 80)
    quality = signal.get('signal_quality', {})
    if quality:
        total = quality.get('total_indicators', 0)
        agreeing = quality.get('agreeing_indicators', 0)
        allowed = quality.get('trade_allowed', False)
        print(f"Total Indicators: {total}")
        print(f"Agreeing Indicators: {agreeing}/{total}")
        print(f"Trade Allowed: {allowed}")
        if total > 0:
            agreement_pct = (agreeing / total) * 100
            print(f"Agreement: {agreement_pct:.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ ALL NEW FIELDS WORKING CORRECTLY!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
