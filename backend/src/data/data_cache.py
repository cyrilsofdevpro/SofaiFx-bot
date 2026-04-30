import json
import os
import time
from datetime import datetime, timedelta
from ..utils.logger import logger

class DataCache:
    """Simple file-based cache for forex data to avoid API rate limits"""
    
    def __init__(self, cache_dir=None, ttl_hours=24):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache')
        
        # Normalize to absolute path
        self.cache_dir = os.path.abspath(cache_dir)
        self.ttl = ttl_hours * 3600  # Convert to seconds
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f'DataCache initialized at {cache_dir}')
    
    def get_cache_key(self, from_sym, to_sym):
        """Generate cache key"""
        return f"{from_sym}_{to_sym}.json"
    
    def get_cache_path(self, from_sym, to_sym):
        """Get full cache file path"""
        return os.path.join(self.cache_dir, self.get_cache_key(from_sym, to_sym))
    
    def is_cache_valid(self, from_sym, to_sym):
        """Check if cache exists and is still valid"""
        path = self.get_cache_path(from_sym, to_sym)
        
        if not os.path.exists(path):
            return False
        
        # Check file age
        file_age = time.time() - os.path.getmtime(path)
        
        if file_age > self.ttl:
            logger.info(f'Cache expired for {from_sym}/{to_sym}')
            return False
        
        return True
    
    def get(self, from_sym, to_sym):
        """Retrieve data from cache"""
        if not self.is_cache_valid(from_sym, to_sym):
            return None
        
        try:
            path = self.get_cache_path(from_sym, to_sym)
            with open(path, 'r') as f:
                data = json.load(f)
                logger.info(f'Cache hit for {from_sym}/{to_sym}')
                return data
        except Exception as e:
            logger.error(f'Error reading cache: {e}')
            return None
    
    def set(self, from_sym, to_sym, data):
        """Store data in cache"""
        try:
            path = self.get_cache_path(from_sym, to_sym)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                logger.info(f'Cached data for {from_sym}/{to_sym}')
        except Exception as e:
            logger.error(f'Error writing cache: {e}')
    
    def clear_cache(self, from_sym=None, to_sym=None):
        """Clear cache for specific pair or all"""
        if from_sym and to_sym:
            path = self.get_cache_path(from_sym, to_sym)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f'Cleared cache for {from_sym}/{to_sym}')
        else:
            # Clear all cache files
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))
            logger.info('Cleared all cache')

# Singleton instance
data_cache = DataCache(ttl_hours=24)
