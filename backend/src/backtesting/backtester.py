"""
Backtesting Engine - Validate strategy performance using historical data
- Fetch historical OHLC data (1-3 years)
- Simulate trades using signal logic
- Calculate metrics: win rate, PnL, drawdown, Sharpe ratio
- Support multi-pair backtesting
- Export results (JSON/CSV)

Author: SofAi FX Bot - Backtesting Division
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from src.utils.logger import logger
from src.config import config

class BacktestingEngine:
    """Validates trading strategy using historical data"""
    
    def __init__(self):
        """Initialize backtesting engine"""
        self.trades = []
        self.equity_curve = []
        self.metrics = {}
        logger.info("[BT] Backtesting Engine initialized")
    
    def backtest_pair(self, pair: str, start_date: str, end_date: str, initial_balance: float = 10000):
        """
        Run backtest on a single pair
        
        Args:
            pair: Currency pair (EURUSD, GBPUSD, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_balance: Starting balance ($)
        
        Returns:
            dict: Backtest results with metrics and trades
        """
        try:
            logger.info(f"[BT] Starting backtest: {pair} ({start_date} to {end_date})")
            
            # Fetch historical data
            df = self._fetch_historical_data(pair, start_date, end_date)
            if df is None or df.empty:
                logger.warning(f"[BT] No data for {pair}")
                return self._empty_result()
            
            # Simulate trading
            trades = self._simulate_trades(pair, df)
            
            # Calculate metrics
            metrics = self._calculate_metrics(trades, initial_balance)
            
            result = {
                'pair': pair,
                'start_date': start_date,
                'end_date': end_date,
                'initial_balance': initial_balance,
                'trades': trades,
                'metrics': metrics,
                'equity_curve': self._build_equity_curve(trades, initial_balance),
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"[BT] Backtest complete: {pair} - Win Rate: {metrics['win_rate']:.1f}%")
            return result
        
        except Exception as e:
            logger.error(f"[BT] Backtest error for {pair}: {e}", exc_info=True)
            return self._empty_result()
    
    def _fetch_historical_data(self, pair: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical OHLC data
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Date
        """
        try:
            # In production, fetch from Alpha Vantage or Twelve Data
            # For now, generate synthetic data for demo
            
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            dates = pd.date_range(start=start, end=end, freq='D')
            
            # Get base price for pair
            base_prices = {
                'EURUSD': 1.0850,
                'GBPUSD': 1.2650,
                'USDJPY': 150.50,
                'AUDUSD': 0.6750
            }
            base_price = base_prices.get(pair, 1.0)
            
            # Generate synthetic OHLC with random walk
            np.random.seed(42)
            returns = np.random.normal(0.0005, 0.01, len(dates))
            prices = base_price * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                'Date': dates,
                'Open': prices * (1 + np.random.uniform(-0.002, 0.002, len(prices))),
                'High': prices * (1 + np.random.uniform(0, 0.005, len(prices))),
                'Low': prices * (1 - np.random.uniform(0, 0.005, len(prices))),
                'Close': prices,
                'Volume': np.random.randint(1000000, 5000000, len(prices))
            })
            
            logger.debug(f"[BT] Fetched {len(df)} candles for {pair}")
            return df
        
        except Exception as e:
            logger.warning(f"[BT] Data fetch error: {e}")
            return None
    
    def _simulate_trades(self, pair: str, df: pd.DataFrame) -> List[Dict]:
        """Simulate trades based on signal logic"""
        trades = []
        position = None
        
        for idx, row in df.iterrows():
            price = row['Close']
            
            # Generate signal (simplified version)
            # In production, use actual signal logic from Phase4AILayer
            signal = self._generate_signal(df.iloc[:idx+1], pair)
            
            if signal['signal'] == 'BUY' and position is None:
                # Open trade
                position = {
                    'entry_price': price,
                    'entry_date': row['Date'],
                    'signal_confidence': signal['confidence'],
                    'type': 'BUY'
                }
            
            elif signal['signal'] == 'SELL' and position is not None:
                # Close trade
                exit_price = price
                pnl = (exit_price - position['entry_price']) * 100000  # 100k units
                
                trade = {
                    'pair': pair,
                    'entry_date': position['entry_date'],
                    'entry_price': position['entry_price'],
                    'exit_date': row['Date'],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': ((exit_price / position['entry_price']) - 1) * 100,
                    'confidence': position['signal_confidence'],
                    'duration_days': (row['Date'] - position['entry_date']).days,
                    'win': pnl > 0
                }
                trades.append(trade)
                position = None
        
        return trades
    
    def _generate_signal(self, df: pd.DataFrame, pair: str) -> Dict:
        """Generate simplified signal for backtesting"""
        if len(df) < 50:
            return {'signal': 'HOLD', 'confidence': 0}
        
        # Calculate simple indicators
        close = df['Close'].values
        ma50 = close[-50:].mean()
        ma200 = close[-200:].mean() if len(close) >= 200 else close.mean()
        
        rsi = self._calculate_rsi(close, 14)
        
        # Simple signal logic
        if close[-1] > ma50 and rsi > 50 and rsi < 70:
            return {'signal': 'BUY', 'confidence': 75}
        elif close[-1] < ma50 and rsi < 50 and rsi > 30:
            return {'signal': 'SELL', 'confidence': 75}
        else:
            return {'signal': 'HOLD', 'confidence': 50}
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = gains.mean()
        avg_loss = losses.mean()
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_metrics(self, trades: List[Dict], initial_balance: float) -> Dict:
        """Calculate backtest metrics"""
        if not trades:
            return self._empty_metrics()
        
        trades_df = pd.DataFrame(trades)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len(trades_df[trades_df['win'] == True])
        losing_trades = len(trades_df[trades_df['win'] == False])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # PnL metrics
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['win'] == True]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = abs(trades_df[trades_df['win'] == False]['pnl'].mean()) if losing_trades > 0 else 0
        
        # Risk/Reward
        risk_reward = (avg_win / avg_loss) if avg_loss > 0 else 0
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(trades_df)
        
        # Sharpe ratio
        sharpe = self._calculate_sharpe_ratio(trades_df)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'initial_balance': initial_balance,
            'final_balance': round(initial_balance + total_pnl, 2),
            'return_percent': round((total_pnl / initial_balance * 100), 2)
        }
    
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        if trades_df.empty:
            return 0.0
        
        cumulative_pnl = trades_df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max
        
        return abs(drawdown.min()) * 100
    
    def _calculate_sharpe_ratio(self, trades_df: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if trades_df.empty:
            return 0.0
        
        returns = trades_df['pnl_percent'].values
        excess_returns = returns.mean() - (risk_free_rate / 252)
        volatility = returns.std()
        
        if volatility == 0:
            return 0.0
        
        return excess_returns / volatility * np.sqrt(252)
    
    def _build_equity_curve(self, trades: List[Dict], initial_balance: float) -> List[Dict]:
        """Build equity curve from trades"""
        # Handle empty trades list
        if not trades:
            return [{'date': None, 'equity': initial_balance}]
        
        equity_curve = [{'date': trades[0]['entry_date'], 'equity': initial_balance}]
        
        cumulative_pnl = 0
        for trade in trades:
            cumulative_pnl += trade['pnl']
            equity_curve.append({
                'date': trade['exit_date'],
                'equity': initial_balance + cumulative_pnl
            })
        
        return equity_curve
    
    def _empty_result(self) -> Dict:
        """Return empty result"""
        return {
            'pair': 'N/A',
            'trades': [],
            'metrics': self._empty_metrics(),
            'equity_curve': [],
            'error': 'Backtest failed'
        }
    
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
            'risk_reward_ratio': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'return_percent': 0.0
        }
    
    def export_results(self, results: Dict, format: str = 'json') -> str:
        """Export backtest results to JSON or CSV"""
        try:
            if format == 'json':
                return json.dumps(results, indent=2, default=str)
            elif format == 'csv':
                trades_df = pd.DataFrame(results['trades'])
                return trades_df.to_csv(index=False)
            else:
                return json.dumps(results, default=str)
        except Exception as e:
            logger.error(f"[BT] Export error: {e}")
            return ""
