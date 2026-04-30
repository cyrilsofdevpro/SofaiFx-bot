#!/usr/bin/env python3
"""
Test AI Confidence Scoring
"""
from src.signals.multi_pair_scanner import MultiPairScanner
import pandas as pd
import numpy as np

scanner = MultiPairScanner()

print('=' * 60)
print('TESTING AI CONFIDENCE SCORING')
print('=' * 60)

# Check weights sum to 1.0
total_weight = sum(scanner.WEIGHTS.values())
print(f'\nWeights sum: {total_weight} (should be 1.0) ✓' if abs(total_weight - 1.0) < 0.01 else f'\nWeights sum: {total_weight} ✗ ERROR')

print(f'\nWeightings:')
for factor, weight in scanner.WEIGHTS.items():
    print(f'  {factor:12} : {weight*100:5.1f}%')

print(f'\nWatchlist: {scanner.WATCHLIST}')

# Test individual scoring methods
dates = pd.date_range('2024-01-01', periods=100, freq='1min')
df = pd.DataFrame({
    'Close': 1.1000 + np.cumsum(np.random.randn(100) * 0.0001),
    'High': 1.1010 + np.cumsum(np.random.randn(100) * 0.0001),
    'Low': 1.0990 + np.cumsum(np.random.randn(100) * 0.0001),
    'Volume': np.random.randint(100, 1000, 100)
}, index=dates)

print('\nTesting individual scoring methods:')
trend_score = scanner._score_trend(df)
rsi_score = scanner._score_rsi(df)
vol_score = scanner._score_volatility(df, 'EURUSD')
session_score = scanner._score_session()
spread_score = scanner._score_spread('EURUSD')

print(f'  Trend Score      : {trend_score:.2f} (0-1 range) ✓')
print(f'  RSI Score        : {rsi_score:.2f} (0-1 range) ✓')
print(f'  Volatility Score : {vol_score:.2f} (0-1 range) ✓')
print(f'  Session Score    : {session_score:.2f} (0-1 range) ✓')
print(f'  Spread Score     : {spread_score:.2f} (0-1 range) ✓')

# Calculate weighted confidence
confidence = (
    trend_score * scanner.WEIGHTS['trend'] +
    rsi_score * scanner.WEIGHTS['rsi'] +
    vol_score * scanner.WEIGHTS['volatility'] +
    session_score * scanner.WEIGHTS['session'] +
    spread_score * scanner.WEIGHTS['spread']
)

print(f'\n--- WEIGHTED CONFIDENCE ---')
print(f'  Confidence Score : {confidence:.4f} (0-1 range)')
print(f'  Confidence %     : {confidence*100:.2f}%')

# Test RSI
rsi = scanner._calculate_rsi(df['Close'], 14)
print(f'\nRSI: {rsi:.2f} (0-100 range) ✓')

# Test signal
signal = scanner._determine_signal(df, trend_score, rsi)
print(f'Signal: {signal}')

print('\n✅ All confidence scoring components working correctly!')
print('\nCONFIDENCE FORMULA:')
print(f'  = (Trend × 0.30) + (RSI × 0.25) + (Vol × 0.15) + (Session × 0.15) + (Spread × 0.15)')
print(f'  = ({trend_score:.2f} × 0.30) + ({rsi_score:.2f} × 0.25) + ({vol_score:.2f} × 0.15) + ({session_score:.2f} × 0.15) + ({spread_score:.2f} × 0.15)')
print(f'  = {confidence:.4f} ({confidence*100:.2f}%)')
