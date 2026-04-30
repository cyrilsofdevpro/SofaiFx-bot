"""
Trade Validator - Validates signals before execution

This module performs pre-execution checks:
- Bot enabled check
- Duplicate position check
- Spread validation
- Risk constraints validation
- Max open positions check
"""

import logging
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TradeValidator:
    """
    Validates trading signals before execution.
    """
    
    def __init__(self, max_open_positions: int = 5, max_daily_loss_percent: float = 5.0,
                 min_spread_threshold: float = 10.0, risk_percent: float = 1.0):
        """
        Initialize trade validator.
        
        Args:
            max_open_positions: Maximum number of open positions allowed
            max_daily_loss_percent: Maximum daily loss percentage before stopping
            min_spread_threshold: Maximum acceptable spread in pips
            risk_percent: Maximum risk per trade in percentage
        """
        self.max_open_positions = max_open_positions
        self.max_daily_loss_percent = max_daily_loss_percent
        self.min_spread_threshold = min_spread_threshold
        self.risk_percent = risk_percent
    
    def validate_signal(
        self,
        signal: Dict,
        symbol_info: Dict,
        open_positions: List[Dict],
        account_info: Dict,
        today_pnl: float,
        bot_enabled: bool = True,
        trades_today: Optional[List[Dict]] = None
    ) -> Tuple[bool, str]:
        """
        Perform comprehensive validation of a signal before execution.
        
        Args:
            signal: Signal data (symbol, type, price, etc.)
            symbol_info: Symbol information from MT5
            open_positions: List of currently open positions
            account_info: Account information from MT5
            today_pnl: Cumulative P&L for today
            bot_enabled: Whether bot is enabled (kill switch)
            trades_today: List of trades executed today
        
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        validation_results = []
        
        # 1. Check bot enabled (kill switch)
        if not bot_enabled:
            validation_results.append(("FAIL", "BOT_DISABLED", "Bot is disabled (kill switch)"))
        else:
            validation_results.append(("PASS", "BOT_ENABLED", "Bot is enabled"))
        
        # 2. Check required signal fields
        if not self._validate_signal_format(signal):
            validation_results.append(("FAIL", "INVALID_SIGNAL_FORMAT", "Signal missing required fields"))
        else:
            validation_results.append(("PASS", "SIGNAL_FORMAT_OK", "Signal format valid"))
        
        # 3. Check symbol exists and is valid
        if not symbol_info or not symbol_info.get('bid') or not symbol_info.get('ask'):
            validation_results.append(("FAIL", "INVALID_SYMBOL", f"Symbol {signal.get('symbol')} not found or invalid"))
        else:
            validation_results.append(("PASS", "SYMBOL_VALID", f"Symbol {signal.get('symbol')} valid"))
        
        # 4. Check spread
        spread_status, spread_msg = self._validate_spread(symbol_info)
        validation_results.append(("FAIL" if not spread_status else "PASS", "SPREAD_CHECK", spread_msg))
        
        # 5. Check for duplicate position
        dup_status, dup_msg = self._validate_duplicate_position(signal['symbol'], open_positions)
        validation_results.append(("FAIL" if not dup_status else "PASS", "DUPLICATE_CHECK", dup_msg))
        
        # 6. Check max open positions
        max_pos_status, max_pos_msg = self._validate_max_positions(len(open_positions))
        validation_results.append(("FAIL" if not max_pos_status else "PASS", "MAX_POSITIONS_CHECK", max_pos_msg))
        
        # 7. Check daily loss limit
        if trades_today is None:
            trades_today = []
        daily_loss_status, daily_loss_msg = self._validate_daily_loss(today_pnl, account_info)
        validation_results.append(("FAIL" if not daily_loss_status else "PASS", "DAILY_LOSS_CHECK", daily_loss_msg))
        
        # 8. Check margin availability
        margin_status, margin_msg = self._validate_margin(account_info)
        validation_results.append(("FAIL" if not margin_status else "PASS", "MARGIN_CHECK", margin_msg))
        
        # Log validation results
        logger.info("=" * 60)
        logger.info("TRADE VALIDATION RESULTS")
        logger.info("=" * 60)
        
        failed_checks = []
        for status, check_name, message in validation_results:
            log_level = logging.ERROR if status == "FAIL" else logging.INFO
            logger.log(log_level, f"[{status:4s}] {check_name:20s}: {message}")
            if status == "FAIL":
                failed_checks.append((check_name, message))
        
        logger.info("=" * 60)
        
        # Determine overall validity
        all_passed = all(status == "PASS" for status, _, _ in validation_results)
        
        if all_passed:
            reason = "All validation checks passed"
            return True, reason
        else:
            reason = " | ".join([f"{name}: {msg}" for name, msg in failed_checks])
            return False, reason
    
    def _validate_signal_format(self, signal: Dict) -> bool:
        """
        Check if signal has all required fields.
        
        Returns:
            bool: True if valid format
        """
        required_fields = ['symbol', 'signal_type', 'price', 'confidence']
        return all(field in signal for field in required_fields)
    
    def _validate_spread(self, symbol_info: Dict) -> Tuple[bool, str]:
        """
        Validate spread is within acceptable threshold.
        
        Args:
            symbol_info: Symbol information
        
        Returns:
            tuple: (is_valid, message)
        """
        try:
            spread = symbol_info.get('spread', float('inf'))
            if spread > self.min_spread_threshold:
                return False, f"Spread {spread:.1f}p exceeds threshold {self.min_spread_threshold}p"
            return True, f"Spread {spread:.1f}p acceptable"
        except Exception as e:
            logger.error(f"Error validating spread: {e}")
            return False, f"Spread validation error: {e}"
    
    def _validate_duplicate_position(self, symbol: str, open_positions: List[Dict]) -> Tuple[bool, str]:
        """
        Check if a position already exists for this symbol.
        
        Args:
            symbol: Trading symbol
            open_positions: List of open positions
        
        Returns:
            tuple: (is_valid, message)
        """
        for position in open_positions:
            if position['symbol'] == symbol:
                return False, f"Position already open for {symbol}"
        return True, f"No duplicate position for {symbol}"
    
    def _validate_max_positions(self, current_positions: int) -> Tuple[bool, str]:
        """
        Check if maximum open positions limit is reached.
        
        Args:
            current_positions: Current number of open positions
        
        Returns:
            tuple: (is_valid, message)
        """
        if current_positions >= self.max_open_positions:
            return False, f"Max positions ({self.max_open_positions}) reached, currently {current_positions}"
        return True, f"Position limit OK: {current_positions}/{self.max_open_positions}"
    
    def _validate_daily_loss(self, today_pnl: float, account_info: Dict) -> Tuple[bool, str]:
        """
        Check if daily loss limit is exceeded.
        
        Args:
            today_pnl: P&L for today
            account_info: Account information
        
        Returns:
            tuple: (is_valid, message)
        """
        try:
            balance = account_info.get('balance', 0)
            max_loss_usd = (balance * self.max_daily_loss_percent) / 100
            
            if today_pnl < -max_loss_usd:
                return False, f"Daily loss ${abs(today_pnl):.2f} exceeds limit ${max_loss_usd:.2f}"
            
            return True, f"Daily P&L: ${today_pnl:.2f} within limit ${max_loss_usd:.2f}"
        except Exception as e:
            logger.error(f"Error validating daily loss: {e}")
            return False, f"Daily loss validation error: {e}"
    
    def _validate_margin(self, account_info: Dict) -> Tuple[bool, str]:
        """
        Check if sufficient margin is available.
        
        Args:
            account_info: Account information
        
        Returns:
            tuple: (is_valid, message)
        """
        try:
            free_margin = account_info.get('free_margin', 0)
            margin_level = account_info.get('margin_level', 0)
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            
            # If margin_level is 0 or None, it means no positions are open
            # In this case, check if we have sufficient balance to open a position
            if margin_level == 0 or margin_level is None:
                # No open positions - check balance instead
                if balance >= 10:  # Minimum $10 balance
                    logger.info(f"Margin check: No open positions, using balance: ${balance:.2f}")
                    return True, f"Margin OK: ${balance:.2f} available (no open positions)"
                else:
                    return False, f"Insufficient balance: ${balance:.2f}"
            
            # Margin level should be > 100% for safe trading (avoid margin calls)
            if margin_level < 150:  # Warning at 150%
                logger.warning(f"Margin level low: {margin_level:.2f}%")
            
            # Reject if margin level below 100%
            if margin_level < 100:
                return False, f"Critical margin level: {margin_level:.2f}% (below 100%)"
            
            if free_margin <= 0:
                return False, f"No free margin available"
            
            return True, f"Margin OK: ${free_margin:.2f} free, Level: {margin_level:.2f}%"
        except Exception as e:
            logger.error(f"Error validating margin: {e}")
            return False, f"Margin validation error: {e}"
    
    def update_settings(self, **kwargs):
        """
        Update validator settings.
        
        Args:
            **kwargs: Settings to update (e.g., max_open_positions=10)
        """
        allowed_settings = {
            'max_open_positions',
            'max_daily_loss_percent',
            'min_spread_threshold',
            'risk_percent'
        }
        
        for key, value in kwargs.items():
            if key in allowed_settings:
                setattr(self, key, value)
                logger.info(f"Updated {key} to {value}")
            else:
                logger.warning(f"Unknown setting: {key}")
