"""
Smart trade filters to avoid bad trading opportunities.
Filters include: economic news events, low volatility periods, and low-confidence setups.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.logger import logger


class SmartFilters:
    """Apply intelligent filters to trade signals for better risk management"""
    
    # Economic calendar high-impact events (example dates)
    HIGH_IMPACT_NEWS_DAYS = {
        'USD': ['first Friday', 'FOMC meeting day'],
        'EUR': ['first Thursday', 'ECB meeting day'],
        'GBP': ['Thursday', 'BOE decision day'],
        'JPY': ['Wednesday', 'BOJ decision day']
    }
    
    def __init__(self):
        self.volatility_history = {}
        self.last_filter_check = {}
    
    def check_volatility(self, df: pd.DataFrame, symbol: str, threshold: float = 0.5) -> dict:
        """
        Check if current volatility is too low for safe trading.
        Avoids trades during low volatility periods which have poor risk/reward.
        
        Args:
            df: DataFrame with OHLC data
            symbol: Currency pair
            threshold: Minimum volatility ratio (current/20-day average)
        
        Returns:
            Dict with filter result:
            {
                'is_blocked': bool,
                'reason': str,
                'current_volatility': float,
                'average_volatility': float,
                'volatility_ratio': float
            }
        """
        try:
            if len(df) < 21:
                return {
                    'is_blocked': False,
                    'reason': 'Insufficient data for volatility check',
                    'current_volatility': None,
                    'average_volatility': None,
                    'volatility_ratio': None
                }
            
            # Normalize column names
            df_copy = df.copy()
            df_copy.columns = df_copy.columns.str.lower()
            
            # Calculate ATR (Average True Range) as volatility measure
            atr_14 = self._calculate_atr(df_copy, period=14)
            atr_20_avg = atr_14.tail(20).mean()
            current_atr = atr_14.iloc[-1]
            
            volatility_ratio = current_atr / (atr_20_avg + 1e-8)
            
            is_blocked = volatility_ratio < threshold
            
            reason = ''
            if is_blocked:
                reason = f"Low volatility period (ratio: {volatility_ratio:.2f} < {threshold})"
            else:
                reason = f"Volatility acceptable (ratio: {volatility_ratio:.2f} >= {threshold})"
            
            result = {
                'is_blocked': is_blocked,
                'reason': reason,
                'current_volatility': float(current_atr),
                'average_volatility': float(atr_20_avg),
                'volatility_ratio': float(volatility_ratio)
            }
            
            logger.debug(f"Volatility check for {symbol}: {result['reason']}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking volatility: {e}")
            return {
                'is_blocked': False,
                'reason': f'Error: {str(e)}',
                'current_volatility': None,
                'average_volatility': None,
                'volatility_ratio': None
            }
    
    def check_economic_news(self, symbol: str = None) -> dict:
        """
        Check for major economic news events that could impact trading.
        
        Args:
            symbol: Currency pair (optional, checks all if None)
        
        Returns:
            Dict with news check result:
            {
                'is_blocked': bool,
                'reason': str,
                'news_events': list
            }
        """
        try:
            today = datetime.now()
            day_name = today.strftime("%A")
            
            # Simplified news calendar (can be enhanced with real API)
            major_news_events = {
                'USD': {
                    'Friday': 'Non-Farm Payroll at 8:30 UTC',
                    'Wednesday': 'FOMC Meeting if scheduled'
                },
                'EUR': {
                    'Thursday': 'ECB Economic Bulletin',
                    'Friday': 'Eurozone CPI Flash'
                },
                'GBP': {
                    'Thursday': 'BOE Base Rate Decision if scheduled',
                    'Wednesday': 'UK Inflation Data'
                }
            }
            
            news_events = []
            is_blocked = False
            
            # Check if it's a high-impact day
            if symbol:
                curr = symbol.split('USD')[0] if 'USD' in symbol else symbol[:3]
                if curr in major_news_events:
                    events = major_news_events.get(curr, {})
                    if day_name in events:
                        is_blocked = True
                        news_events.append(events[day_name])
            
            reason = ''
            if is_blocked:
                reason = f"High-impact news event today: {', '.join(news_events)}"
            else:
                reason = "No major news events scheduled for today"
            
            result = {
                'is_blocked': is_blocked,
                'reason': reason,
                'news_events': news_events,
                'current_date': today.isoformat()
            }
            
            logger.debug(f"News check for {symbol}: {result['reason']}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking economic news: {e}")
            return {
                'is_blocked': False,
                'reason': f'Error: {str(e)}',
                'news_events': [],
                'current_date': datetime.now().isoformat()
            }
    
    def check_setup_quality(self, signal_data: dict) -> dict:
        """
        Check if signal setup has sufficient quality/confidence.
        Blocks trades with low multi-indicator agreement.
        
        Args:
            signal_data: Signal dict with indicator details
        
        Returns:
            Dict with quality check result:
            {
                'is_blocked': bool,
                'reason': str,
                'confidence_score': float,
                'agreeing_indicators': int,
                'total_indicators': int
            }
        """
        try:
            # Count agreeing indicators
            indicators_checked = 0
            indicators_agreeing = 0
            
            min_confidence_threshold = 0.4  # Require 40%+ confidence
            
            # Check each indicator from signal
            if 'signal_quality' in signal_data:
                quality = signal_data['signal_quality']
                indicators_checked = quality.get('total_indicators', 0)
                indicators_agreeing = quality.get('agreeing_indicators', 0)
            
            # Calculate confidence score
            if indicators_checked > 0:
                confidence_score = indicators_agreeing / indicators_checked
            else:
                confidence_score = 0.0
            
            is_blocked = confidence_score < min_confidence_threshold
            
            reason = ''
            if is_blocked:
                reason = f"Low setup quality: {indicators_agreeing}/{indicators_checked} indicators agree (confidence: {confidence_score:.2%})"
            else:
                reason = f"Setup quality acceptable: {indicators_agreeing}/{indicators_checked} indicators agree (confidence: {confidence_score:.2%})"
            
            result = {
                'is_blocked': is_blocked,
                'reason': reason,
                'confidence_score': float(confidence_score),
                'agreeing_indicators': indicators_agreeing,
                'total_indicators': indicators_checked
            }
            
            logger.debug(f"Setup quality check: {result['reason']}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking setup quality: {e}")
            return {
                'is_blocked': False,
                'reason': f'Error: {str(e)}',
                'confidence_score': 0.0,
                'agreeing_indicators': 0,
                'total_indicators': 0
            }
    
    def apply_all_filters(self, df: pd.DataFrame, signal_data: dict, 
                         symbol: str = None) -> dict:
        """
        Apply all filters and return comprehensive trade viability report.
        
        Args:
            df: DataFrame with OHLC data
            signal_data: Signal dict with indicator details
            symbol: Currency pair
        
        Returns:
            Dict with combined filter results:
            {
                'is_trade_allowed': bool,
                'filters': {
                    'volatility': {...},
                    'news': {...},
                    'setup_quality': {...}
                },
                'blocked_reasons': [list of blocking reasons]
            }
        """
        try:
            volatility_check = self.check_volatility(df, symbol)
            news_check = self.check_economic_news(symbol)
            quality_check = self.check_setup_quality(signal_data)
            
            blocked_reasons = []
            
            if volatility_check['is_blocked']:
                blocked_reasons.append(volatility_check['reason'])
            
            if news_check['is_blocked']:
                blocked_reasons.append(news_check['reason'])
            
            if quality_check['is_blocked']:
                blocked_reasons.append(quality_check['reason'])
            
            is_trade_allowed = len(blocked_reasons) == 0
            
            result = {
                'is_trade_allowed': is_trade_allowed,
                'filters': {
                    'volatility': volatility_check,
                    'news': news_check,
                    'setup_quality': quality_check
                },
                'blocked_reasons': blocked_reasons,
                'check_timestamp': datetime.now().isoformat()
            }
            
            status = "ALLOWED" if is_trade_allowed else "BLOCKED"
            logger.info(f"Trade filter check for {symbol}: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return {
                'is_trade_allowed': False,
                'filters': {},
                'blocked_reasons': [f'Filter error: {str(e)}'],
                'check_timestamp': datetime.now().isoformat()
            }
    
    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr


# Singleton instance
smart_filters = SmartFilters()
