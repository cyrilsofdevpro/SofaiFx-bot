"""
Trade Manager - Manages trade lifecycle and monitoring

This module handles:
- Trade tracking and updates
- Position monitoring
- Trade closing logic
- Analytics and reporting
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Trade status enum"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class TradeManager:
    """
    Manages trade lifecycle and monitoring.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize trade manager.
        
        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session
        self.open_trades: Dict[int, Dict] = {}  # symbol -> trade data
    
    def create_trade(
        self,
        user_id: int,
        symbol: str,
        trade_type: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        lot_size: float,
        risk_percent: float,
        signal_id: Optional[int] = None,
        strategy_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Create a new trade record.
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            trade_type: BUY or SELL
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            lot_size: Lot size
            risk_percent: Risk percentage
            signal_id: Associated signal ID
            strategy_name: Strategy name
            notes: Trade notes
        
        Returns:
            dict: Trade data
        """
        try:
            trade_data = {
                'user_id': user_id,
                'symbol': symbol,
                'trade_type': trade_type,
                'entry_price': entry_price,
                'entry_time': datetime.utcnow(),
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'lot_size': lot_size,
                'risk_percent': risk_percent,
                'signal_id': signal_id,
                'status': TradeStatus.PENDING.value,
                'strategy_name': strategy_name,
                'notes': notes,
                'pnl': None,
                'pnl_percent': None,
                'exit_price': None,
                'exit_time': None,
                'close_reason': None
            }
            
            logger.info(f"Created trade record: {symbol} {trade_type}")
            return trade_data
            
        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            raise
    
    def update_trade_status(
        self,
        trade_id: int,
        status: str,
        mt5_order_id: Optional[int] = None
    ) -> bool:
        """
        Update trade status.
        
        Args:
            trade_id: Trade ID
            status: New status
            mt5_order_id: MT5 order ID
        
        Returns:
            bool: Success status
        """
        try:
            if self.db_session:
                from src.models import Trade
                trade = self.db_session.query(Trade).get(trade_id)
                if trade:
                    trade.status = status
                    if mt5_order_id:
                        trade.mt5_order_id = mt5_order_id
                    trade.updated_at = datetime.utcnow()
                    self.db_session.commit()
                    logger.info(f"Updated trade {trade_id} status to {status}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating trade status: {e}")
            return False
    
    def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        close_reason: str = "Manual close"
    ) -> Tuple[bool, Dict]:
        """
        Close a trade.
        
        Args:
            trade_id: Trade ID
            exit_price: Exit price
            close_reason: Reason for closing
        
        Returns:
            tuple: (success, trade_data)
        """
        try:
            if self.db_session:
                from src.models import Trade
                trade = self.db_session.query(Trade).get(trade_id)
                
                if not trade:
                    logger.warning(f"Trade {trade_id} not found")
                    return False, {}
                
                # Calculate P&L
                if trade.trade_type == 'BUY':
                    pnl = (exit_price - trade.entry_price) * trade.lot_size * 100000
                else:  # SELL
                    pnl = (trade.entry_price - exit_price) * trade.lot_size * 100000
                
                pnl_percent = (pnl / (trade.entry_price * trade.lot_size * 100000)) * 100 if trade.entry_price > 0 else 0
                
                # Update trade
                trade.exit_price = exit_price
                trade.exit_time = datetime.utcnow()
                trade.pnl = pnl
                trade.pnl_percent = pnl_percent
                trade.close_reason = close_reason
                trade.status = TradeStatus.CLOSED.value
                trade.updated_at = datetime.utcnow()
                
                self.db_session.commit()
                
                logger.info(
                    f"Trade {trade_id} closed: "
                    f"P&L ${pnl:.2f} ({pnl_percent:.2f}%)"
                )
                
                return True, trade.to_dict()
            
            return False, {}
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            return False, {}
    
    def get_open_trades(self, user_id: int = None) -> List[Dict]:
        """
        Get all open trades.
        
        Args:
            user_id: Filter by user ID
        
        Returns:
            list: List of open trades
        """
        try:
            if self.db_session:
                from src.models import Trade
                query = self.db_session.query(Trade).filter_by(status=TradeStatus.OPEN.value)
                
                if user_id:
                    query = query.filter_by(user_id=user_id)
                
                trades = query.all()
                return [t.to_dict() for t in trades]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting open trades: {e}")
            return []
    
    def get_trade_history(
        self,
        user_id: int,
        limit: int = 100,
        status: str = None
    ) -> List[Dict]:
        """
        Get trade history.
        
        Args:
            user_id: User ID
            limit: Maximum trades to return
            status: Filter by status
        
        Returns:
            list: List of trades
        """
        try:
            if self.db_session:
                from src.models import Trade
                query = self.db_session.query(Trade).filter_by(user_id=user_id)
                
                if status:
                    query = query.filter_by(status=status)
                
                trades = query.order_by(Trade.created_at.desc()).limit(limit).all()
                return [t.to_dict() for t in trades]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    def get_trade_statistics(self, user_id: int, days: int = 7) -> Dict:
        """
        Calculate trade statistics.
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            dict: Statistics
        """
        try:
            if not self.db_session:
                return {}
            
            from src.models import Trade
            from datetime import timedelta
            
            # Get trades from the past N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            trades = self.db_session.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.created_at >= cutoff_date,
                Trade.status == TradeStatus.CLOSED.value
            ).all()
            
            if not trades:
                return {
                    'period_days': days,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_pnl_per_trade': 0.0
                }
            
            # Calculate stats
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            
            total_pnl = sum(t.pnl for t in trades)
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            
            largest_win = max((t.pnl for t in winning_trades), default=0)
            largest_loss = min((t.pnl for t in losing_trades), default=0)
            
            return {
                'period_days': days,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'breakeven_trades': total_trades - len(winning_trades) - len(losing_trades),
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl_per_trade': round(avg_pnl, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2),
                'profitability': round((total_pnl / abs(largest_loss) if largest_loss != 0 else 0), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def get_daily_pnl(self, user_id: int, date: str = None) -> float:
        """
        Get P&L for a specific day.
        
        Args:
            user_id: User ID
            date: Date string (YYYY-MM-DD), defaults to today
        
        Returns:
            float: Daily P&L
        """
        try:
            if not self.db_session:
                return 0.0
            
            from src.models import Trade
            from datetime import datetime as dt
            
            if not date:
                date = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Parse date
            start_date = dt.strptime(date, '%Y-%m-%d')
            end_date = start_date + timedelta(days=1)
            
            trades = self.db_session.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED.value,
                Trade.exit_time >= start_date,
                Trade.exit_time < end_date
            ).all()
            
            daily_pnl = sum(t.pnl for t in trades)
            return daily_pnl
            
        except Exception as e:
            logger.error(f"Error calculating daily P&L: {e}")
            return 0.0
