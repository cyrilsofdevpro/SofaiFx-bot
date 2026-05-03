import requests
import pandas as pd
from datetime import datetime, timedelta
from src.config import config
from src.utils.logger import logger
from src.data_cache import data_cache

# Custom exceptions
class APIRateLimitError(Exception):
    """Raised when API rate limit is hit"""
    pass

class AlphaVantageClient:
    BASE_URL = 'https://www.alphavantage.co/query'
    
    def __init__(self, api_key=None):
        self.api_key = api_key or config.ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            logger.warning('Alpha Vantage API key not set!')
    
    def get_forex_data(self, from_symbol, to_symbol, interval='daily'):
        """
        Fetch forex data from Alpha Vantage (with caching)
        
        Args:
            from_symbol: e.g., 'EUR'
            to_symbol: e.g., 'USD'
            interval: 'daily' (free tier)
        
        Returns:
            pd.DataFrame with OHLC data
        """
        # Check cache first
        cached_data = data_cache.get(from_symbol, to_symbol)
        if cached_data is not None:
            try:
                df = pd.DataFrame(cached_data['data'])
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                for col in ['Open', 'High', 'Low', 'Close']:
                    df[col] = pd.to_numeric(df[col])
                logger.info(f'Using cached data for {from_symbol}/{to_symbol}')
                return df
            except Exception as e:
                logger.error(f'Error loading cached data: {e}')
        
        try:
            # Use FX_DAILY for free tier (intraday endpoints are premium)
            params = {
                'function': 'FX_DAILY',
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'apikey': self.api_key,
                'outputsize': 'full'  # Get up to 500 data points
            }
            
            logger.info(f'Fetching forex data for {from_symbol}/{to_symbol} (daily)...')
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f'API Error: {data["Error Message"]}')
                return None
            
            if 'Information' in data:
                logger.error(f'API Info: {data["Information"]}')
                return None
            
            if 'Note' in data:
                error_msg = data["Note"]
                logger.error(f'API Rate Limit Hit: {error_msg}')
                raise APIRateLimitError(error_msg)
            
            # Extract time series data
            time_series_key = [k for k in data.keys() if 'Time Series' in k]
            if not time_series_key:
                logger.error(f'No time series data found. Available keys: {list(data.keys())}')
                return None
            
            time_series = data[time_series_key[0]]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Rename columns
            df.columns = ['Open', 'High', 'Low', 'Close']
            df = df.astype(float)
            
            # Cache the data
            df_reset = df.reset_index().rename(columns={'index': 'Date'})
            df_reset['Date'] = df_reset['Date'].astype(str)  # Convert Timestamp to string for JSON serialization
            cache_data = {
                'data': df_reset.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
            data_cache.set(from_symbol, to_symbol, cache_data)
            
            logger.info(f'Successfully fetched {len(df)} data points for {from_symbol}/{to_symbol}')
            return df
        
        except requests.exceptions.RequestException as e:
            logger.error(f'Request error: {e}')
            return None
        except Exception as e:
            logger.error(f'Error fetching forex data: {e}')
            return None
    
    def get_intraday_data(self, symbol, interval='60min'):
        """Get intraday data for a forex pair (e.g., EURUSD)"""
        if '/' in symbol:
            from_sym, to_sym = symbol.split('/')
        else:
            # Assume format like EURUSD
            from_sym = symbol[:3]
            to_sym = symbol[3:]
        
        return self.get_forex_data(from_sym, to_sym, interval)
    
    def get_daily_data(self, from_symbol, to_symbol):
        """Get daily forex data"""
        return self.get_forex_data(from_symbol, to_symbol, 'daily')
    
    def get_forex_data_live(self, from_symbol, to_symbol, interval='daily'):
        """
        Fetch fresh forex data from Alpha Vantage API (bypass cache)
        
        Args:
            from_symbol: e.g., 'EUR'
            to_symbol: e.g., 'USD'
            interval: 'daily' (free tier)
        
        Returns:
            pd.DataFrame with OHLC data or None
        """
        try:
            # Use FX_DAILY for free tier (intraday endpoints are premium)
            params = {
                'function': 'FX_DAILY',
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'apikey': self.api_key,
                'outputsize': 'full'  # Get up to 500 data points
            }
            
            logger.info(f'Fetching LIVE forex data for {from_symbol}/{to_symbol} (daily)...')
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f'API Error: {data["Error Message"]}')
                return None
            
            if 'Information' in data:
                logger.error(f'API Info: {data["Information"]}')
                return None
            
            if 'Note' in data:
                error_msg = data["Note"]
                logger.error(f'API Rate Limit Hit: {error_msg}')
                raise APIRateLimitError(error_msg)
            
            # Extract time series data
            time_series_key = [k for k in data.keys() if 'Time Series' in k]
            if not time_series_key:
                logger.error(f'No time series data found. Available keys: {list(data.keys())}')
                return None
            
            time_series = data[time_series_key[0]]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Rename columns
            df.columns = ['Open', 'High', 'Low', 'Close']
            df = df.astype(float)
            
            # Cache the fresh data
            df_reset = df.reset_index().rename(columns={'index': 'Date'})
            df_reset['Date'] = df_reset['Date'].astype(str)  # Convert Timestamp to string for JSON serialization
            cache_data = {
                'data': df_reset.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
            data_cache.set(from_symbol, to_symbol, cache_data)
            
            logger.info(f'Successfully fetched LIVE {len(df)} data points for {from_symbol}/{to_symbol}')
            return df
        
        except requests.exceptions.RequestException as e:
            logger.error(f'Request error: {e}')
            return None
        except Exception as e:
            logger.error(f'Error fetching live forex data: {e}')
            return None

    def get_intraday_data(self, symbol, interval='60min'):
        """Get intraday data for a forex pair (e.g., EURUSD)"""
        if '/' in symbol:
            from_sym, to_sym = symbol.split('/')
        else:
            # Assume format like EURUSD
            from_sym = symbol[:3]
            to_sym = symbol[3:]
        
        return self.get_forex_data(from_sym, to_sym, interval)

# Singleton instance
alpha_vantage = AlphaVantageClient()
