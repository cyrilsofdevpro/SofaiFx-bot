#!/usr/bin/env python
"""Test script for AI Predictions and Smart Filters"""

import requests
import json

print('\n' + '=' * 80)
print('TESTING AI PREDICTIONS & SMART FILTERS INTEGRATION')
print('=' * 80)

# Test pairs
pairs = ['EURUSD', 'GBPUSD', 'USDJPY']

for pair in pairs:
    print(f'\n\n--- {pair} Analysis ---')
    print('-' * 40)
    
    try:
        r = requests.post('http://127.0.0.1:5000/api/analyze', 
                         json={'symbol': pair, 'notify': False})
        
        if r.status_code != 200:
            print(f'ERROR: Status {r.status_code}')
            continue
        
        data = r.json()
        signal = data['signal']
        
        print(f'Signal: {signal["signal"]} (Conf: {signal["confidence"]:.1%})')
        print(f'Price: {signal["price"]}')
        print(f'Reason: {signal["reason"][:60]}...')
        
        # AI Prediction
        if 'ai_prediction' in signal and signal['ai_prediction']:
            ai = signal['ai_prediction']
            print(f'\nAI Prediction:')
            print(f'  Direction: {ai.get("direction", "N/A")}')
            print(f'  Confidence: {ai.get("confidence", 0):.1%}')
            print(f'  Ensemble Probability (UP): {ai.get("ensemble_probability", 0):.1%}')
        else:
            print(f'\nAI Prediction: Training in progress...')
        
        # Smart Filters
        if 'filter_results' in signal and signal['filter_results']:
            filt = signal['filter_results']
            print(f'\nSmart Filters:')
            print(f'  Trade Allowed: {"✓ YES" if filt.get("is_trade_allowed") else "✗ NO"}')
            
            if filt.get('blocked_reasons'):
                print(f'  Blocked Reasons:')
                for reason in filt['blocked_reasons']:
                    print(f'    - {reason}')
            
            filters = filt.get('filters', {})
            
            vol = filters.get('volatility', {})
            if vol:
                print(f'\n  Volatility Analysis:')
                print(f'    Current ATR: {vol.get("current_volatility", 0):.6f}')
                print(f'    Avg ATR (20d): {vol.get("average_volatility", 0):.6f}')
                print(f'    Ratio: {vol.get("volatility_ratio", 0):.2f}x')
            
            news = filters.get('news', {})
            if news:
                print(f'\n  Economic News:')
                print(f'    High Impact Today: {"✓ YES" if news.get("is_blocked") else "✗ NO"}')
                print(f'    Reason: {news.get("reason", "")}')
            
            quality = filters.get('setup_quality', {})
            if quality:
                print(f'\n  Setup Quality:')
                print(f'    Agreeing: {quality.get("agreeing_indicators", 0)}/{quality.get("total_indicators", 0)} indicators')
                print(f'    Confidence: {quality.get("confidence_score", 0):.1%}')
        
        # Signal Quality
        if 'signal_quality' in signal:
            sq = signal['signal_quality']
            print(f'\nSignal Quality Metrics:')
            print(f'  Total Indicators: {sq.get("total_indicators", 0)}')
            print(f'  Agreeing: {sq.get("agreeing_indicators", 0)}')
            print(f'  Trade Allowed: {"✓ YES" if sq.get("trade_allowed") else "✗ NO"}')
    
    except Exception as e:
        print(f'ERROR: {e}')

print('\n' + '=' * 80)
print('INTEGRATION TEST COMPLETE!')
print('=' * 80 + '\n')
