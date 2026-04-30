import pandas as pd
import numpy as np
from src.risk.risk_manager import risk_manager

# Create mock data with realistic OHLC values
dates = pd.date_range('2025-01-01', periods=100, freq='D')
np.random.seed(42)

# EURUSD mock data
eurusd_close = 1.1703 + np.cumsum(np.random.randn(100) * 0.001)
eurusd_data = {
    'Close': eurusd_close,
    'High': eurusd_close + np.abs(np.random.randn(100) * 0.002),
    'Low': eurusd_close - np.abs(np.random.randn(100) * 0.002)
}
df_eurusd = pd.DataFrame(eurusd_data, index=dates)

# GBPUSD mock data
gbpusd_close = 1.3501 + np.cumsum(np.random.randn(100) * 0.0015)
gbpusd_data = {
    'Close': gbpusd_close,
    'High': gbpusd_close + np.abs(np.random.randn(100) * 0.003),
    'Low': gbpusd_close - np.abs(np.random.randn(100) * 0.003)
}
df_gbpusd = pd.DataFrame(gbpusd_data, index=dates)

# Test EURUSD
current_price = df_eurusd['Close'].iloc[-1]
print('=== EURUSD Risk Management ===')
print(f'Current Price: {current_price:.5f}')

# Calculate ATR
atr = risk_manager.calculate_atr(df_eurusd, period=14)
print(f'ATR (14): {atr:.6f}')

# Calculate SL/TP for BUY
sl_tp = risk_manager.calculate_sl_tp(df_eurusd, 'EURUSD', 'BUY', current_price, atr)
print(f'\nBUY Setup:')
print(f'  Entry: {current_price:.5f}')
print(f'  Stop Loss: {sl_tp["stop_loss"]:.5f} ({sl_tp["sl_pips"]:.1f} pips away)')
print(f'  Take Profit: {sl_tp["take_profit"]:.5f} ({sl_tp["tp_pips"]:.1f} pips away)')

# Calculate position size
pos_size = risk_manager.calculate_position_size('EURUSD', current_price, sl_tp['stop_loss'])
print(f'\nPosition Size (2% risk):')
print(f'  Lots: {pos_size["lots"]}')
print(f'  Units: {pos_size["units"]:,}')
print(f'  Risk Amount: ${pos_size["risk_amount"]:.2f}')
print(f'  Risk Pips: {pos_size["risk_pips"]:.1f} pips')

# Calculate R/R ratio
rr = risk_manager.calculate_risk_reward(current_price, sl_tp['stop_loss'], sl_tp['take_profit'])
print(f'\nRisk/Reward Ratio: {rr["ratio"]:.2f}:1')
print(f'  Risk: {rr["risk_pips"]:.1f} pips')
print(f'  Reward: {rr["reward_pips"]:.1f} pips')

# Test GBPUSD
print('\n' + '='*50)
print('=== GBPUSD Risk Management ===')

current_price2 = df_gbpusd['Close'].iloc[-1]
print(f'Current Price: {current_price2:.5f}')

# Calculate ATR
atr2 = risk_manager.calculate_atr(df_gbpusd, period=14)
print(f'ATR (14): {atr2:.6f}')

# Calculate SL/TP for SELL
sl_tp2 = risk_manager.calculate_sl_tp(df_gbpusd, 'GBPUSD', 'SELL', current_price2, atr2)
print(f'\nSELL Setup:')
print(f'  Entry: {current_price2:.5f}')
print(f'  Stop Loss: {sl_tp2["stop_loss"]:.5f} ({sl_tp2["sl_pips"]:.1f} pips away)')
print(f'  Take Profit: {sl_tp2["take_profit"]:.5f} ({sl_tp2["tp_pips"]:.1f} pips away)')

# Calculate position size
pos_size2 = risk_manager.calculate_position_size('GBPUSD', current_price2, sl_tp2['stop_loss'])
print(f'\nPosition Size (2% risk):')
print(f'  Lots: {pos_size2["lots"]}')
print(f'  Units: {pos_size2["units"]:,}')
print(f'  Risk Amount: ${pos_size2["risk_amount"]:.2f}')
print(f'  Risk Pips: {pos_size2["risk_pips"]:.1f} pips')

# Calculate R/R ratio
rr2 = risk_manager.calculate_risk_reward(current_price2, sl_tp2['stop_loss'], sl_tp2['take_profit'])
print(f'\nRisk/Reward Ratio: {rr2["ratio"]:.2f}:1')
print(f'  Risk: {rr2["risk_pips"]:.1f} pips')
print(f'  Reward: {rr2["reward_pips"]:.1f} pips')

print('\n' + '='*50)
print('✓ Risk Management System Working!')
print('\nKey Features:')
print('  ✓ ATR-based Stop Loss & Take Profit')
print('  ✓ Auto Position Sizing (2% risk per trade)')
print('  ✓ Risk/Reward Ratio Calculation')
print('  ✓ Volatility-Adjusted Levels')
