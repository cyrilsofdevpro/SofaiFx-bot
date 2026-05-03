"""
P&L (Profit & Loss) Tracking and Analytics Service
Calculates performance metrics for user trading

Author: SofAi FX Bot
Version: 1.0.0
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_
from src.models import Trade, db
from src.utils.logger import logger


class PnLTracker:
    """Track and calculate P&L metrics"""
    
    def __init__(self):
        logger.info("[PnL] P&L Tracker initialized")
    
    def get_summary(self, user_id):
        """
        Get overall P&L summary
        
        Returns:
            dict: Total P&L, Win rate, Trades count, etc.
        """
        try:
            # Get all trades for user
            trades = Trade.query.filter_by(user_id=user_id, status='CLOSED').all()
            
            if not trades:
                return self._empty_summary()
            
            total_pnl = sum(t.pnl for t in trades if t.pnl is not None)
            total_pnl_percent = sum(t.pnl_percent for t in trades if t.pnl_percent is not None)
            
            winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl and t.pnl < 0]
            
            win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
            
            avg_win = (sum(t.pnl for t in winning_trades) / len(winning_trades)) if winning_trades else 0
            avg_loss = (sum(t.pnl for t in losing_trades) / len(losing_trades)) if losing_trades else 0
            
            profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades and sum(t.pnl for t in losing_trades) != 0 else 0
            
            return {
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate_percent': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percent': round(total_pnl_percent, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'largest_win': round(max([t.pnl for t in winning_trades], default=0), 2),
                'largest_loss': round(min([t.pnl for t in losing_trades], default=0), 2),
                'profit_factor': round(profit_factor, 2),
                'avg_win_percent': round(sum(t.pnl_percent for t in winning_trades) / len(winning_trades), 2) if winning_trades else 0,
                'avg_loss_percent': round(sum(t.pnl_percent for t in losing_trades) / len(losing_trades), 2) if losing_trades else 0
            }
        
        except Exception as e:
            logger.error(f"❌ P&L summary error for user {user_id}: {e}")
            return self._empty_summary()
    
    def get_by_period(self, user_id, period_days=30):
        """
        Get P&L for specific period
        
        Args:
            user_id: User ID
            period_days: Number of days to look back
        
        Returns:
            dict: P&L metrics for period
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            trades = Trade.query.filter(
                and_(
                    Trade.user_id == user_id,
                    Trade.status == 'CLOSED',
                    Trade.exit_time >= cutoff_date
                )
            ).all()
            
            if not trades:
                return self._empty_summary()
            
            total_pnl = sum(t.pnl for t in trades if t.pnl is not None)
            total_pnl_percent = sum(t.pnl_percent for t in trades if t.pnl_percent is not None)
            
            winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl and t.pnl < 0]
            
            win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
            
            return {
                'period_days': period_days,
                'total_trades': len(trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate_percent': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percent': round(total_pnl_percent, 2),
                'avg_daily_pnl': round(total_pnl / period_days, 2),
                'cutoff_date': cutoff_date.isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ P&L period error for user {user_id}: {e}")
            return self._empty_summary()
    
    def get_by_symbol(self, user_id):
        """
        Get P&L breakdown by symbol
        
        Returns:
            dict: P&L for each symbol
        """
        try:
            trades = Trade.query.filter_by(user_id=user_id, status='CLOSED').all()
            
            symbols_pnl = {}
            for trade in trades:
                if trade.symbol not in symbols_pnl:
                    symbols_pnl[trade.symbol] = {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_pnl': 0,
                        'win_rate': 0
                    }
                
                symbols_pnl[trade.symbol]['total_trades'] += 1
                if trade.pnl and trade.pnl > 0:
                    symbols_pnl[trade.symbol]['winning_trades'] += 1
                elif trade.pnl and trade.pnl < 0:
                    symbols_pnl[trade.symbol]['losing_trades'] += 1
                
                symbols_pnl[trade.symbol]['total_pnl'] += trade.pnl if trade.pnl else 0
            
            # Calculate win rates
            for symbol in symbols_pnl:
                total = symbols_pnl[symbol]['total_trades']
                wins = symbols_pnl[symbol]['winning_trades']
                symbols_pnl[symbol]['win_rate'] = round((wins / total * 100) if total > 0 else 0, 2)
                symbols_pnl[symbol]['total_pnl'] = round(symbols_pnl[symbol]['total_pnl'], 2)
            
            return symbols_pnl
        
        except Exception as e:
            logger.error(f"❌ P&L by symbol error for user {user_id}: {e}")
            return {}
    
    def get_monthly_breakdown(self, user_id, months=12):
        """
        Get monthly P&L breakdown
        
        Returns:
            list: Monthly P&L data
        """
        try:
            monthly_data = []
            
            for i in range(months):
                month_start = datetime.utcnow().replace(day=1) - timedelta(days=i*30)
                month_start = month_start.replace(day=1)
                month_end = month_start + timedelta(days=32)
                month_end = month_end.replace(day=1) - timedelta(days=1)
                
                trades = Trade.query.filter(
                    and_(
                        Trade.user_id == user_id,
                        Trade.status == 'CLOSED',
                        Trade.exit_time >= month_start,
                        Trade.exit_time <= month_end
                    )
                ).all()
                
                if trades:
                    total_pnl = sum(t.pnl for t in trades if t.pnl is not None)
                    winning = len([t for t in trades if t.pnl and t.pnl > 0])
                    
                    monthly_data.append({
                        'month': month_start.strftime('%Y-%m'),
                        'trades': len(trades),
                        'winning': winning,
                        'total_pnl': round(total_pnl, 2)
                    })
            
            return monthly_data
        
        except Exception as e:
            logger.error(f"❌ Monthly breakdown error for user {user_id}: {e}")
            return []
    
    def get_recent_trades(self, user_id, limit=10):
        """
        Get recent closed trades
        
        Returns:
            list: Recent trades
        """
        try:
            trades = Trade.query.filter_by(
                user_id=user_id,
                status='CLOSED'
            ).order_by(Trade.exit_time.desc()).limit(limit).all()
            
            return [t.to_dict() for t in trades]
        
        except Exception as e:
            logger.error(f"❌ Recent trades error for user {user_id}: {e}")
            return []
    
    def get_open_trades(self, user_id):
        """
        Get currently open trades
        
        Returns:
            list: Open trades with current status
        """
        try:
            trades = Trade.query.filter_by(
                user_id=user_id,
                status='OPEN'
            ).order_by(Trade.entry_time.desc()).all()
            
            return [t.to_dict() for t in trades]
        
        except Exception as e:
            logger.error(f"❌ Open trades error for user {user_id}: {e}")
            return []
    
    @staticmethod
    def _empty_summary():
        """Return empty summary structure"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate_percent': 0.0,
            'total_pnl': 0.0,
            'total_pnl_percent': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'profit_factor': 0.0,
            'avg_win_percent': 0.0,
            'avg_loss_percent': 0.0
        }
