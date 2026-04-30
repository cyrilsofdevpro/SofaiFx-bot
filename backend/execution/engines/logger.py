"""
Execution Logger - Logs all trade execution events and analytics

This module provides:
- Trade event logging
- Performance analytics
- Error logging
- Database integration
"""

import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """
    Logs all execution events and maintains analytics.
    """
    
    def __init__(self, logs_dir: str = "backend/execution/logs"):
        """
        Initialize execution logger.
        
        Args:
            logs_dir: Directory for log files
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging files
        self.execution_log_file = self.logs_dir / "execution.log"
        self.trades_log_file = self.logs_dir / "trades.json"
        self.analytics_log_file = self.logs_dir / "analytics.json"
        self.errors_log_file = self.logs_dir / "errors.json"
        
        logger.info(f"Execution logger initialized at {self.logs_dir}")
    
    def log_event(
        self,
        event_type: str,
        status: str,
        message: str,
        symbol: str = None,
        details: Dict = None,
        user_id: int = None
    ) -> None:
        """
        Log an execution event.
        
        Args:
            event_type: Event type (e.g., SIGNAL_RECEIVED, ORDER_PLACED, etc.)
            status: Event status (SUCCESS, FAILED, PENDING)
            message: Human-readable message
            symbol: Trading symbol
            details: Additional details as dictionary
            user_id: User ID
        """
        try:
            timestamp = datetime.now().isoformat()
            
            log_entry = {
                'timestamp': timestamp,
                'event_type': event_type,
                'status': status,
                'message': message,
                'symbol': symbol,
                'user_id': user_id,
                'details': details or {}
            }
            
            # Append to execution log file
            with open(self.execution_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Log to standard logger
            log_level = logging.ERROR if status == 'FAILED' else logging.INFO
            logger.log(
                log_level,
                f"[{event_type}] {status}: {message}"
                + (f" ({symbol})" if symbol else "")
            )
            
        except Exception as e:
            logger.error(f"Error logging event: {e}", exc_info=True)
    
    def log_trade(
        self,
        trade_data: Dict,
        user_id: int
    ) -> None:
        """
        Log a completed trade.
        
        Args:
            trade_data: Trade information dictionary
            user_id: User ID
        """
        try:
            trade_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'trade': trade_data
            }
            
            # Append to trades log
            with open(self.trades_log_file, 'a') as f:
                f.write(json.dumps(trade_entry) + '\n')
            
            logger.info(
                f"Trade logged: {trade_data.get('symbol')} "
                f"{trade_data.get('trade_type')} @ {trade_data.get('entry_price')}"
            )
            
        except Exception as e:
            logger.error(f"Error logging trade: {e}", exc_info=True)
    
    def log_error(
        self,
        error_message: str,
        error_type: str,
        context: Dict = None,
        user_id: int = None
    ) -> None:
        """
        Log an error.
        
        Args:
            error_message: Error message
            error_type: Type of error
            context: Additional context
            user_id: User ID
        """
        try:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'message': error_message,
                'context': context or {},
                'user_id': user_id
            }
            
            # Append to errors log
            with open(self.errors_log_file, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
            
            logger.error(f"[{error_type}] {error_message}")
            
        except Exception as e:
            logger.error(f"Error logging error: {e}", exc_info=True)
    
    def get_trade_summary(self, user_id: int = None, days: int = 1) -> Dict:
        """
        Get trading summary for a period.
        
        Args:
            user_id: Filter by user ID (None = all users)
            days: Number of days to look back
        
        Returns:
            dict: Summary statistics
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            trades = []
            if self.trades_log_file.exists():
                with open(self.trades_log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if user_id and entry.get('user_id') != user_id:
                                continue
                            
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time >= cutoff_time:
                                trades.append(entry['trade'])
                        except:
                            continue
            
            # Calculate statistics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
            breakeven_trades = [t for t in trades if t.get('pnl', 0) == 0]
            
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            total_pnl_percent = sum(t.get('pnl_percent', 0) for t in trades) / max(len(trades), 1)
            
            return {
                'period_days': days,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'breakeven_trades': len(breakeven_trades),
                'win_rate': (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': round(total_pnl, 2),
                'avg_pnl_percent': round(total_pnl_percent, 2),
                'largest_win': max((t.get('pnl', 0) for t in winning_trades), default=0),
                'largest_loss': min((t.get('pnl', 0) for t in losing_trades), default=0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating trade summary: {e}", exc_info=True)
            return {}
    
    def get_execution_events(
        self,
        user_id: int = None,
        event_type: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get execution events.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            limit: Maximum events to return
        
        Returns:
            list: List of execution events
        """
        try:
            events = []
            if self.execution_log_file.exists():
                with open(self.execution_log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if user_id and entry.get('user_id') != user_id:
                                continue
                            if event_type and entry.get('event_type') != event_type:
                                continue
                            events.append(entry)
                        except:
                            continue
            
            # Return most recent first
            return events[-limit:][::-1]
            
        except Exception as e:
            logger.error(f"Error getting execution events: {e}", exc_info=True)
            return []
    
    def get_errors(
        self,
        user_id: int = None,
        error_type: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get logged errors.
        
        Args:
            user_id: Filter by user ID
            error_type: Filter by error type
            limit: Maximum errors to return
        
        Returns:
            list: List of errors
        """
        try:
            errors = []
            if self.errors_log_file.exists():
                with open(self.errors_log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if user_id and entry.get('user_id') != user_id:
                                continue
                            if error_type and entry.get('error_type') != error_type:
                                continue
                            errors.append(entry)
                        except:
                            continue
            
            # Return most recent first
            return errors[-limit:][::-1]
            
        except Exception as e:
            logger.error(f"Error getting errors: {e}", exc_info=True)
            return []
    
    def export_daily_report(self, user_id: int = None, date: str = None) -> Dict:
        """
        Export a daily report.
        
        Args:
            user_id: User ID to filter
            date: Date string (YYYY-MM-DD), defaults to today
        
        Returns:
            dict: Daily report
        """
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            summary = self.get_trade_summary(user_id=user_id, days=1)
            events = self.get_execution_events(user_id=user_id, limit=1000)
            errors = self.get_errors(user_id=user_id, limit=1000)
            
            # Filter to today
            today_cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            events = [e for e in events if datetime.fromisoformat(e['timestamp']) >= today_cutoff]
            errors = [e for e in errors if datetime.fromisoformat(e['timestamp']) >= today_cutoff]
            
            return {
                'date': date,
                'user_id': user_id,
                'summary': summary,
                'events': events,
                'errors': errors,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting daily report: {e}", exc_info=True)
            return {}


# Global logger instance
_logger_instance = None


def get_execution_logger(logs_dir: str = "backend/execution/logs") -> ExecutionLogger:
    """
    Get or create global execution logger.
    
    Args:
        logs_dir: Directory for log files
    
    Returns:
        ExecutionLogger: Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ExecutionLogger(logs_dir)
    return _logger_instance
