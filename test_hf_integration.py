#!/usr/bin/env python3
"""
Test Hugging Face Sentiment Analysis Integration
Tests HF sentiment across multiple currency pairs and signal generation
"""

import sys
sys.path.insert(0, 'backend')

from src.signals.signal_generator import SignalGenerator
from src.signals.huggingface_service import HuggingFaceService

print('='*60)
print('🧠 HUGGING FACE SENTIMENT ANALYSIS TEST')
print('='*60)

# Test HF service directly
print('\n📍 Testing Hugging Face Service:')
hf = HuggingFaceService()
pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']

for pair in pairs:
    sentiment = hf.analyze_market_sentiment(pair)
    label = 'Bullish' if sentiment > 0.1 else 'Bearish' if sentiment < -0.1 else 'Neutral'
    print(f'  {pair}: {sentiment:>7.3f} ({label})')

# Test signal generation with HF integrated
print('\n\n📊 Testing Signal Generation (with HF @ 50% weight):')
sg = SignalGenerator()

for pair in pairs:
    try:
        signal = sg.generate_signal(pair)
        if signal:
            print(f'\n  {pair}:')
            print(f'    Signal: {signal.get("signal", "N/A")}')
            print(f'    Confidence: {signal.get("confidence", 0):.1%}')
            print(f'    HF Sentiment: {signal.get("hf_sentiment", "N/A")}')
        else:
            print(f'  {pair}: No signal generated')
    except Exception as e:
        print(f'  {pair}: Error - {str(e)[:50]}')

print('\n' + '='*60)
print('✅ Test Complete')
print('='*60)
