"""
Position Sizing Engine - Calculates lot size based on risk management rules

This module provides:
- Risk-based lot size calculation
- Maximum position sizing validation
- Margin requirement calculations
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Calculates position size (lot size) based on risk parameters.
    
    The calculation follows the formula:
    lot_size = (account_balance * risk_percent) / (stop_loss_pips * pip_value)
    """
    
    # Pip values for common symbols (base currency)
    PIP_VALUES = {
        'EURUSD': 0.0001,
        'GBPUSD': 0.0001,
        'USDJPY': 0.01,
        'EURJPY': 0.01,
        'GBPJPY': 0.01,
        'AUDJPY': 0.01,
        'CADJPY': 0.01,
        'CHFJPY': 0.01,
        'NZDJPY': 0.01,
        'AUDUSD': 0.0001,
        'NZDUSD': 0.0001,
        'EURCAD': 0.0001,
        'EURAUD': 0.0001,
        'EURCHF': 0.0001,
        'GBPAUD': 0.0001,
        'GBPCAD': 0.0001,
        'GBPCHF': 0.0001,
        'AUDCAD': 0.0001,
        'AUDNZD': 0.0001,
        'USDCAD': 0.0001,
    }
    
    # Contract size (standard lot = 100,000 units)
    STANDARD_LOT_SIZE = 100000
    
    def __init__(self, account_balance: float, leverage: int = 100):
        """
        Initialize position sizer.
        
        Args:
            account_balance: Current account balance in USD
            leverage: Account leverage (default: 100)
        """
        self.account_balance = account_balance
        self.leverage = leverage
        self.max_margin_percent = 5.0  # Never use more than 5% of margin per trade
    
    def calculate_lot_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        risk_percent: float = 1.0,
        round_to: str = 'nearest'
    ) -> float:
        """
        Calculate lot size for a trade based on risk.
        
        Formula:
        - SL distance in pips = abs(entry - SL) / pip_value
        - Risk in USD = account_balance * risk_percent / 100
        - Lot size = Risk in USD / (SL_pips * pip_value * contract_size)
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            risk_percent: Risk percentage (1-2% recommended)
            round_to: Rounding strategy ('nearest', 'down', 'up')
        
        Returns:
            float: Calculated lot size
        
        Raises:
            ValueError: If parameters are invalid
        """
        try:
            # Validate inputs
            if risk_percent <= 0 or risk_percent > 5:
                logger.warning(f"Risk percent {risk_percent} out of bounds, clamping to 0.1-2%")
                risk_percent = max(0.1, min(2.0, risk_percent))
            
            if entry_price <= 0 or stop_loss_price <= 0:
                raise ValueError(f"Invalid prices: entry={entry_price}, SL={stop_loss_price}")
            
            if entry_price == stop_loss_price:
                raise ValueError("Entry price cannot equal stop loss price")
            
            # Get pip value
            pip_value = self.PIP_VALUES.get(symbol)
            if pip_value is None:
                logger.warning(f"Unknown symbol {symbol}, assuming pip_value=0.0001")
                pip_value = 0.0001
            
            # Calculate SL distance in pips
            sl_distance = abs(entry_price - stop_loss_price) / pip_value
            
            if sl_distance == 0:
                raise ValueError("Stop loss distance is zero")
            
            # Calculate risk amount in USD
            risk_amount = (self.account_balance * risk_percent) / 100
            
            # Calculate lot size
            # lot_size = risk_amount / (sl_distance_pips * pip_value * contract_size)
            # But we simplify: pip_value * contract_size = 10 for standard lots
            lot_size = risk_amount / (sl_distance * 10)
            
            # Round based on strategy
            if round_to == 'down':
                # Round down to nearest 0.01 lot (minimize risk)
                lot_size = int(lot_size * 100) / 100
            elif round_to == 'up':
                # Round up to nearest 0.01 lot (maximize potential)
                lot_size = (int(lot_size * 100) + 1) / 100
            else:  # nearest
                # Round to nearest 0.01 lot
                lot_size = round(lot_size, 2)
            
            # Ensure minimum lot size
            min_lot = 0.01
            if lot_size < min_lot:
                logger.warning(f"Calculated lot size {lot_size} below minimum, using {min_lot}")
                lot_size = min_lot
            
            # Ensure doesn't exceed max lot (safety check)
            max_lot = 100.0  # Arbitrary maximum
            if lot_size > max_lot:
                logger.warning(f"Calculated lot size {lot_size} exceeds maximum, using {max_lot}")
                lot_size = max_lot
            
            logger.info(
                f"Position sizing for {symbol}:\n"
                f"  Account balance: ${self.account_balance:.2f}\n"
                f"  Risk: {risk_percent}%\n"
                f"  Entry: {entry_price:.5f} | SL: {stop_loss_price:.5f}\n"
                f"  SL distance: {sl_distance:.2f} pips\n"
                f"  Lot size: {lot_size:.2f}"
            )
            
            return lot_size
            
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}", exc_info=True)
            raise
    
    def calculate_margin_required(
        self,
        symbol: str,
        lot_size: float,
        entry_price: float
    ) -> float:
        """
        Calculate margin required for a position.
        
        Formula:
        margin_required = lot_size * contract_size * entry_price / leverage
        
        Args:
            symbol: Trading symbol
            lot_size: Lot size
            entry_price: Entry price
        
        Returns:
            float: Margin required in USD
        """
        try:
            margin = (lot_size * self.STANDARD_LOT_SIZE * entry_price) / self.leverage
            return margin
        except Exception as e:
            logger.error(f"Error calculating margin: {e}")
            return 0.0
    
    def validate_margin(
        self,
        symbol: str,
        lot_size: float,
        entry_price: float,
        free_margin: float
    ) -> bool:
        """
        Validate if position can be opened with current margin.
        
        Args:
            symbol: Trading symbol
            lot_size: Lot size
            entry_price: Entry price
            free_margin: Free margin available
        
        Returns:
            bool: True if margin is sufficient, False otherwise
        """
        try:
            margin_required = self.calculate_margin_required(symbol, lot_size, entry_price)
            margin_percent = (margin_required / free_margin * 100) if free_margin > 0 else 0
            
            # Allow max 5% margin usage per trade
            if margin_percent > self.max_margin_percent:
                logger.warning(
                    f"Position would use {margin_percent:.2f}% margin (max {self.max_margin_percent}%)"
                )
                return False
            
            if margin_required > free_margin:
                logger.warning(f"Insufficient margin: required ${margin_required:.2f}, available ${free_margin:.2f}")
                return False
            
            logger.info(f"Margin validation passed: {margin_percent:.2f}% of free margin")
            return True
            
        except Exception as e:
            logger.error(f"Error validating margin: {e}")
            return False
    
    def suggest_lot_size_range(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        risk_percent_min: float = 0.5,
        risk_percent_max: float = 2.0
    ) -> Dict[str, float]:
        """
        Suggest a range of lot sizes based on different risk levels.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_percent_min: Minimum risk percentage
            risk_percent_max: Maximum risk percentage
        
        Returns:
            dict: Dict with 'conservative', 'moderate', 'aggressive' lot sizes
        """
        try:
            conservative = self.calculate_lot_size(symbol, entry_price, stop_loss_price, risk_percent_min)
            moderate = self.calculate_lot_size(symbol, entry_price, stop_loss_price, (risk_percent_min + risk_percent_max) / 2)
            aggressive = self.calculate_lot_size(symbol, entry_price, stop_loss_price, risk_percent_max)
            
            return {
                'conservative': conservative,
                'moderate': moderate,
                'aggressive': aggressive
            }
        except Exception as e:
            logger.error(f"Error suggesting lot size range: {e}")
            return {'conservative': 0.01, 'moderate': 0.01, 'aggressive': 0.01}
