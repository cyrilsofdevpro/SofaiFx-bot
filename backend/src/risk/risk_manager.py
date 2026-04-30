import numpy as np
import pandas as pd
from ..utils.logger import logger

class RiskManager:
    """
    Risk Management System for Forex Trading
    
    Features:
    - Auto lot size calculation
    - Risk per trade (1-2% of account)
    - Stop Loss & Take Profit based on ATR (volatility)
    - Position sizing based on risk/reward ratio
    """
    
    def __init__(self, account_balance=10000, risk_per_trade=0.02, reward_ratio=2.0):
        """
        Initialize Risk Manager
        
        Args:
            account_balance: Trading account size (default $10,000)
            risk_per_trade: Risk per trade as % of account (default 2%)
            reward_ratio: Reward/Risk ratio (default 2:1)
        """
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade  # 0.02 = 2%
        self.reward_ratio = reward_ratio  # 2:1 means TP = 2 * SL
        
        logger.info(f'RiskManager initialized: Balance=${account_balance}, Risk={risk_per_trade*100}%, R/R={reward_ratio}:1')
    
    def calculate_atr(self, df, period=14):
        """
        Calculate Average True Range (ATR) - volatility measure
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period (default 14)
        
        Returns:
            float: Current ATR value
        """
        if df is None or len(df) < period:
            return None
        
        # Calculate True Range
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(period).mean()
        
        return atr.iloc[-1]
    
    def calculate_position_size(self, symbol, entry_price, stop_loss_price, pair_details=None):
        """
        Calculate position size in lots based on risk per trade
        
        Args:
            symbol: Currency pair (e.g., EURUSD)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            pair_details: Optional dict with pip_size, lot_size info
        
        Returns:
            dict: {'lots': lot_size, 'units': units, 'risk_amount': risk_amt}
        """
        # Risk amount in dollars
        risk_amount = self.account_balance * self.risk_per_trade
        
        # Calculate pip value (standard lot = 100,000 units)
        # For most pairs: 1 pip = $10 per standard lot
        
        # Default values (can be customized per pair)
        if pair_details is None:
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            standard_lot_units = 100000
        else:
            pip_size = pair_details.get('pip_size', 0.0001)
            standard_lot_units = pair_details.get('lot_size', 100000)
        
        # Calculate pips of risk
        risk_pips = abs(entry_price - stop_loss_price) / pip_size
        
        if risk_pips == 0:
            logger.warning('Risk in pips is zero, cannot calculate position size')
            return {'lots': 0, 'units': 0, 'risk_amount': 0, 'risk_pips': 0}
        
        # Value per pip per standard lot (approximately $10 for most pairs)
        value_per_pip_per_lot = standard_lot_units * pip_size
        
        # Calculate number of lots
        # risk_amount = number_of_lots * value_per_pip_per_lot * risk_pips
        lots = risk_amount / (value_per_pip_per_lot * risk_pips)
        
        # Round to standard lot sizes (0.01, 0.1, 1.0 etc)
        lots = round(lots, 2)
        
        units = lots * standard_lot_units
        
        return {
            'lots': lots,
            'units': int(units),
            'risk_amount': risk_amount,
            'risk_pips': risk_pips,
            'pip_size': pip_size
        }
    
    def calculate_sl_tp(self, df, symbol, signal_direction, entry_price, atr=None):
        """
        Calculate Stop Loss and Take Profit based on ATR (volatility)
        
        Args:
            df: DataFrame with OHLC data
            symbol: Currency pair
            signal_direction: 'BUY' or 'SELL'
            entry_price: Entry price
            atr: Optional pre-calculated ATR
        
        Returns:
            dict: {'stop_loss': SL, 'take_profit': TP, 'atr': atr_value}
        """
        # Calculate ATR if not provided
        if atr is None:
            atr = self.calculate_atr(df, period=14)
        
        if atr is None or atr == 0:
            logger.warning(f'Cannot calculate ATR for {symbol}')
            return None
        
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        
        # ATR in pips
        atr_pips = atr / pip_size
        
        # SL at 1.5 x ATR
        # TP at 3.0 x ATR (2:1 reward/risk)
        sl_distance = atr_pips * 1.5
        tp_distance = atr_pips * 3.0
        
        if signal_direction.upper() == 'BUY':
            stop_loss = entry_price - (sl_distance * pip_size)
            take_profit = entry_price + (tp_distance * pip_size)
        else:  # SELL
            stop_loss = entry_price + (sl_distance * pip_size)
            take_profit = entry_price - (tp_distance * pip_size)
        
        return {
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'atr': atr,
            'atr_pips': atr_pips,
            'sl_pips': sl_distance,
            'tp_pips': tp_distance
        }
    
    def calculate_risk_reward(self, entry_price, stop_loss, take_profit):
        """
        Calculate Risk/Reward ratio for a trade
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            dict: {'risk_pips': risk, 'reward_pips': reward, 'ratio': ratio}
        """
        risk_pips = abs(entry_price - stop_loss)
        reward_pips = abs(take_profit - entry_price)
        
        if risk_pips == 0:
            return None
        
        ratio = reward_pips / risk_pips
        
        return {
            'risk_pips': risk_pips,
            'reward_pips': reward_pips,
            'ratio': ratio
        }
    
    def calculate_max_drawdown(self, loss_sequence):
        """
        Calculate maximum drawdown from a sequence of trades
        
        Args:
            loss_sequence: List of P&L values
        
        Returns:
            float: Maximum drawdown percentage
        """
        if not loss_sequence or len(loss_sequence) == 0:
            return 0
        
        cumulative = np.cumsum(loss_sequence)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        return min(drawdown) if len(drawdown) > 0 else 0

# Singleton instance
risk_manager = RiskManager(account_balance=10000, risk_per_trade=0.02, reward_ratio=2.0)
