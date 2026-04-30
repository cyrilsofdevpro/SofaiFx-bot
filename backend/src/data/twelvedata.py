"""
TwelveData API client for real-time market data and forex quotes.
Provides complementary market data to Alpha Vantage for enhanced AI decision-making.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from src.config import config
from src.utils.logger import logger
from src.data.data_cache import data_cache


class TwelveDataClient:
    """Client for TwelveData API - real-time market data provider"""
    
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self):
        self.api_key = config.TWELVEDATA_API_KEY
        if not self.api_key:
            logger.warning("TwelveData API key not configured in .env")
    
    def get_quote(self, symbol: str) -> dict:
        """
        Get real-time quote for a currency pair.
        
        Args:
            symbol: Currency pair (e.g., 'EUR/USD')
        
        Returns:
            Dict with quote data: {last, bid, ask, volume, timestamp, etc}
        """
        try:
            # TwelveData quote is real-time, minimal caching
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(
                f"{self.BASE_URL}/quote",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # TwelveData returns quote data directly with fields like 'close', 'open', etc.
            if isinstance(data, dict) and ('close' in data or 'last' in data):
                logger.info(f"Retrieved real-time quote for {symbol}")
                return data
            elif 'data' in data:
                quote_data = data['data']
                logger.info(f"Retrieved real-time quote for {symbol}")
                return quote_data
            else:
                logger.error(f"Invalid quote response for {symbol}: {data}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TwelveData API error fetching quote for {symbol}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_quote: {e}")
            return {}
    
    def get_time_series(self, symbol: str, interval: str = "1day", 
                       outputsize: int = 90) -> pd.DataFrame:
        """
        Get historical time series data for a currency pair.
        
        Args:
            symbol: Currency pair (e.g., 'EUR/USD')
            interval: Time interval ('1min', '5min', '15min', '30min', '1h', '1day', etc.)
            outputsize: Number of data points to retrieve (max 5000)
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(
                f"{self.BASE_URL}/time_series",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            # TwelveData returns data in 'values' key
            if 'values' in data:
                df = pd.DataFrame(data['values'])
                if not df.empty:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.sort_values('datetime')
                    
                    # Convert to float
                    for col in ['open', 'high', 'low', 'close']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    if 'volume' in df.columns:
                        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
                    
                    logger.info(f"Retrieved {len(df)} candles for {symbol} ({interval})")
                    return df
            elif 'data' in data:
                df = pd.DataFrame(data['data'])
                if not df.empty:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.sort_values('datetime')
                    
                    # Convert to float
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    logger.info(f"Retrieved {len(df)} candles for {symbol} ({interval})")
                    return df
            else:
                logger.error(f"Invalid time series response for {symbol}: {data}")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TwelveData API error fetching time series for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error in get_time_series: {e}")
            return pd.DataFrame()
    
    def get_market_status(self) -> dict:
        """
        Get market status and trading hours.
        
        Returns:
            Dict with market status information
        """
        try:
            params = {'apikey': self.api_key}
            response = requests.get(
                f"{self.BASE_URL}/market/status",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                logger.info("Retrieved market status")
                return data['data']
            else:
                logger.error(f"Invalid market status response: {data}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TwelveData API error fetching market status: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_market_status: {e}")
            return {}
    
    def get_top_gainers(self, country: str = "US") -> list:
        """
        Get top gainers in a market.
        
        Args:
            country: Country code (e.g., 'US', 'GB', 'EU')
        
        Returns:
            List of top gaining instruments
        """
        try:
            params = {
                'country': country,
                'apikey': self.api_key
            }
            response = requests.get(
                f"{self.BASE_URL}/stocks/top/gainers",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                logger.info(f"Retrieved top gainers for {country}")
                return data['data']
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return []


# Singleton instance
twelvedata_client = TwelveDataClient()
