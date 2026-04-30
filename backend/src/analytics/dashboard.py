"""
Performance Dashboard - Show real, transparent system performance
- Win rate, total trades, PnL, max drawdown
- Equity curve & daily/weekly PnL charts
- Filter by pair and date range
- Data from trade history + backtesting results

Author: SofAi FX Bot - Analytics Division
Version: 1.0.0
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from ..utils.logger import logger

class PerformanceDashboard:
    """Generates performance analytics and dashboards"""
    
    def __init__(self, db_session=None):
        """Initialize dashboard"""
        self.db = db_session
        logger.info("[DASH] Performance Dashboard initialized")
    
    def get_overall_metrics(self) -> Dict:
        """Get overall system performance metrics"""
        try:
            # Fetch all closed trades from database
            trades = self._fetch_all_trades()
            
            if not trades:
                return self._empty_metrics()
            
            df = pd.DataFrame(trades)
            
            # Calculate metrics
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = df['pnl'].sum()
            avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = abs(df[df['pnl'] < 0]['pnl'].mean()) if losing_trades > 0 else 0
            
            metrics = {
                'total_trades': int(total_trades),
                'winning_trades': int(winning_trades),
                'losing_trades': int(losing_trades),
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
                'accuracy': win_rate,
                'best_trade': round(df['pnl'].max(), 2),
                'worst_trade': round(df['pnl'].min(), 2),
            }
            
            logger.info(f"[DASH] Overall metrics: {win_rate:.1f}% win rate")
            return metrics
        
        except Exception as e:
            logger.error(f"[DASH] Error fetching metrics: {e}")
            return self._empty_metrics()
    
    def get_pair_performance(self, pair: str = None) -> List[Dict]:
        """Get performance metrics by pair"""
        try:
            trades = self._fetch_all_trades(pair=pair)
            
            if not trades:
                return []
            
            df = pd.DataFrame(trades)
            
            # Group by pair if not filtered
            if pair is None:
                pairs = df['pair'].unique()
            else:
                pairs = [pair]
            
            results = []
            for p in pairs:
                pair_trades = df[df['pair'] == p]
                
                if pair_trades.empty:
                    continue
                
                total = len(pair_trades)
                wins = len(pair_trades[pair_trades['pnl'] > 0])
                
                result = {
                    'pair': p,
                    'total_trades': int(total),
                    'wins': int(wins),
                    'losses': int(total - wins),
                    'win_rate': round((wins / total * 100), 2),
                    'total_pnl': round(pair_trades['pnl'].sum(), 2),
                    'avg_pnl': round(pair_trades['pnl'].mean(), 2),
                    'best_trade': round(pair_trades['pnl'].max(), 2),
                    'worst_trade': round(pair_trades['pnl'].min(), 2),
                }
                results.append(result)
            
            return sorted(results, key=lambda x: x['win_rate'], reverse=True)
        
        except Exception as e:
            logger.error(f"[DASH] Pair performance error: {e}")
            return []
    
    def get_equity_curve(self, pair: str = None, days: int = 90) -> List[Dict]:
        """Get equity curve over time"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            trades = self._fetch_all_trades(pair=pair, since=start_date)
            
            if not trades:
                return []
            
            df = pd.DataFrame(trades)
            df['exit_date'] = pd.to_datetime(df['exit_date'])
            df = df.sort_values('exit_date')
            
            # Calculate cumulative PnL
            df['cumulative_pnl'] = df['pnl'].cumsum()
            
            # Daily equity
            equity_curve = []
            running_total = 0
            for idx, trade in df.iterrows():
                running_total += trade['pnl']
                equity_curve.append({
                    'date': trade['exit_date'].isoformat(),
                    'equity': running_total,
                    'pair': trade['pair']
                })
            
            return equity_curve
        
        except Exception as e:
            logger.error(f"[DASH] Equity curve error: {e}")
            return []
    
    def get_daily_pnl(self, pair: str = None, days: int = 30) -> List[Dict]:
        """Get daily PnL breakdown"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            trades = self._fetch_all_trades(pair=pair, since=start_date)
            
            if not trades:
                return []
            
            df = pd.DataFrame(trades)
            df['exit_date'] = pd.to_datetime(df['exit_date'])
            df['day'] = df['exit_date'].dt.date
            
            # Group by day
            daily = df.groupby('day').agg({
                'pnl': 'sum',
                'pair': 'count'
            }).reset_index()
            
            daily.columns = ['date', 'pnl', 'trades']
            
            return [
                {
                    'date': str(row['date']),
                    'pnl': round(row['pnl'], 2),
                    'trades': int(row['trades']),
                    'avg_pnl': round(row['pnl'] / row['trades'], 2)
                }
                for _, row in daily.iterrows()
            ]
        
        except Exception as e:
            logger.error(f"[DASH] Daily PnL error: {e}")
            return []
    
    def get_confidence_analysis(self, pair: str = None) -> Dict:
        """Analyze accuracy by signal confidence"""
        try:
            trades = self._fetch_all_trades(pair=pair)
            
            if not trades:
                return {}
            
            df = pd.DataFrame(trades)
            
            # Bucket by confidence level
            df['confidence_bucket'] = pd.cut(df['confidence'], 
                                             bins=[0, 60, 75, 90, 100],
                                             labels=['Low (0-60)', 'Medium (60-75)', 'High (75-90)', 'VeryHigh (90+)'])
            
            results = {}
            for bucket in df['confidence_bucket'].unique():
                bucket_trades = df[df['confidence_bucket'] == bucket]
                
                if bucket_trades.empty:
                    continue
                
                wins = len(bucket_trades[bucket_trades['pnl'] > 0])
                total = len(bucket_trades)
                
                results[str(bucket)] = {
                    'trades': int(total),
                    'wins': int(wins),
                    'win_rate': round((wins / total * 100), 2),
                    'avg_pnl': round(bucket_trades['pnl'].mean(), 2),
                }
            
            return results
        
        except Exception as e:
            logger.error(f"[DASH] Confidence analysis error: {e}")
            return {}
    
    def get_drawdown_analysis(self, pair: str = None) -> Dict:
        """Calculate maximum drawdown metrics"""
        try:
            trades = self._fetch_all_trades(pair=pair)
            
            if not trades:
                return {}
            
            df = pd.DataFrame(trades)
            cumulative = df['pnl'].cumsum()
            
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max * 100
            
            return {
                'current_drawdown': round(drawdown.iloc[-1], 2),
                'max_drawdown': round(drawdown.min(), 2),
                'avg_drawdown': round(drawdown[drawdown < 0].mean(), 2),
            }
        
        except Exception as e:
            logger.error(f"[DASH] Drawdown analysis error: {e}")
            return {}
    
    def _fetch_all_trades(self, pair: str = None, since: datetime = None) -> List[Dict]:
        """Fetch trades from database"""
        # This would connect to actual database
        # For now, return empty to avoid DB dependency
        return []
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
        }
