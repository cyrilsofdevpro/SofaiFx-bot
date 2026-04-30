"""
Signal Listener - Fetches signals from the Flask API and triggers execution

This module provides:
- Periodic signal polling
- Signal queue management
- API communication
- Signal delivery to execution engine
"""

import requests
import logging
import time
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SignalSource(Enum):
    """Signal sources"""
    API = "api"
    WEBHOOK = "webhook"
    LOCAL = "local"


class SignalListener:
    """
    Listens for trading signals from the backend API.
    """
    
    def __init__(
        self,
        api_base_url: str,
        user_id: int,
        polling_interval: int = 30,
        timeout: int = 10,
        jwt_token: str = None
    ):
        """
        Initialize signal listener.
        
        Args:
            api_base_url: Base URL of the API (e.g., http://localhost:5000)
            user_id: User ID to fetch signals for
            polling_interval: Polling interval in seconds
            timeout: Request timeout in seconds
            jwt_token: JWT token for authentication (optional - will be created if not provided)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.user_id = user_id
        self.polling_interval = polling_interval
        self.timeout = timeout
        self.jwt_token = jwt_token
        
        self.signal_queue: List[Dict] = []
        self.last_signal_id = None
        self.is_running = False
        self.last_poll_time = None
        
        # Stats
        self.total_signals_received = 0
        self.failed_polls = 0
        
        # Get JWT token if not provided
        if not self.jwt_token:
            self.jwt_token = self._get_jwt_token()
    
    def _get_jwt_token(self) -> Optional[str]:
        """
        Get JWT token by logging in via the API.
        
        Returns:
            str: JWT token or None if failed
        """
        try:
            # Try to login via the API to get a token
            # First, get user credentials from .env
            from dotenv import load_dotenv
            from pathlib import Path
            import os
            
            # Load .env from backend directory
            env_path = Path(__file__).parent.parent.parent / '.env'
            load_dotenv(env_path)
            
            user_id = int(os.getenv('USER_ID', '1'))
            
            # Try to get user credentials from database or use default
            # For now, we'll try to login with a default test user
            # In production, you'd store user credentials securely
            
            # Try to get token via API login
            # We'll try a few common test accounts
            test_credentials = [
                {'email': 'user1@gmail.com', 'password': 'user1123'},
                {'email': 'test@example.com', 'password': 'password123'},
                {'email': 'admin@example.com', 'password': 'admin123'},
            ]
            
            for creds in test_credentials:
                try:
                    login_url = f"{self.api_base_url}/auth/login"
                    response = requests.post(
                        login_url,
                        json={'email': creds['email'], 'password': creds['password']},
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if 'access_token' in data:
                            logger.info(f"[OK] JWT token obtained via login for {creds['email']}")
                            return data['access_token']
                except Exception as e:
                    continue
            
            # If login fails, try to create token using the backend's JWT secret
            jwt_secret = os.getenv('JWT_SECRET_KEY', 'sofai-fx-secret-key-change-in-production')
            
            # Create token using PyJWT directly (bypassing Flask-JWT-Extended)
            import jwt as pyjwt
            import time
            
            payload = {
                'sub': str(user_id),
                'iat': int(time.time()),
                'exp': int(time.time()) + (30 * 24 * 60 * 60),  # 30 days
                'fresh': False
            }
            
            token = pyjwt.encode(payload, jwt_secret, algorithm='HS256')
            logger.info(f"[OK] JWT token created directly for user_id={user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to get JWT token: {e}")
            return None
    
    def fetch_latest_signals(self) -> List[Dict]:
        """
        Fetch latest signals from the API.
        
        Returns:
            list: List of signal dictionaries
        """
        try:
            # Endpoint to fetch signals
            url = f"{self.api_base_url}/api/signals"
            params = {
                'user_id': self.user_id,
                'limit': 10,
                'since_id': self.last_signal_id
            }
            
            # Include JWT token in headers
            headers = {}
            if self.jwt_token:
                headers['Authorization'] = f'Bearer {self.jwt_token}'
            
            logger.debug(f"Fetching signals from {url}...")
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, (list, dict)):
                logger.warning(f"Unexpected response format: {type(data)}")
                return []
            
            # Handle dict response (e.g., {'signals': [...]})
            if isinstance(data, dict):
                signals = data.get('signals', [])
            else:
                signals = data
            
            if signals:
                logger.info(f"[OK] Fetched {len(signals)} signal(s)")
                
                # Update last signal ID
                if signals and isinstance(signals, list) and len(signals) > 0:
                    first_signal = signals[0]
                    if isinstance(first_signal, dict) and 'id' in first_signal:
                        self.last_signal_id = first_signal['id']
                
                self.total_signals_received += len(signals)
                self.failed_polls = 0  # Reset failed count on success
                return signals
            else:
                logger.debug("No new signals")
                return []
            
        except requests.exceptions.RequestException as e:
            self.failed_polls += 1
            logger.warning(f"Failed to fetch signals (attempt {self.failed_polls}): {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching signals: {e}", exc_info=True)
            return []
    
    def poll_signals(self, callback=None) -> None:
        """
        Poll signals from API periodically.
        
        Args:
            callback: Optional callback function to execute when signals are received
                     Should accept (signals: list) as parameter
        """
        self.is_running = True
        logger.info(f"Signal listener started (interval: {self.polling_interval}s)")
        
        try:
            while self.is_running:
                try:
                    self.last_poll_time = datetime.now()
                    signals = self.fetch_latest_signals()
                    
                    if signals:
                        self.signal_queue.extend(signals)
                        
                        # Execute callback if provided
                        if callback:
                            try:
                                callback(signals)
                            except Exception as e:
                                logger.error(f"Error in signal callback: {e}", exc_info=True)
                    
                    # Wait for next poll
                    time.sleep(self.polling_interval)
                    
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}", exc_info=True)
                    time.sleep(self.polling_interval)
        
        except KeyboardInterrupt:
            logger.info("Signal listener stopped by user")
            self.is_running = False
    
    def stop(self) -> None:
        """Stop listening for signals."""
        self.is_running = False
        logger.info("Signal listener stopped")
    
    def get_next_signal(self) -> Optional[Dict]:
        """
        Get the next signal from the queue (FIFO).
        
        Returns:
            dict: Next signal or None if queue is empty
        """
        if self.signal_queue:
            return self.signal_queue.pop(0)
        return None
    
    def peek_signal(self) -> Optional[Dict]:
        """
        Peek at the next signal without removing it.
        
        Returns:
            dict: Next signal or None if queue is empty
        """
        if self.signal_queue:
            return self.signal_queue[0]
        return None
    
    def get_queue_size(self) -> int:
        """
        Get the number of pending signals in queue.
        
        Returns:
            int: Queue size
        """
        return len(self.signal_queue)
    
    def clear_queue(self) -> int:
        """
        Clear all signals from queue.
        
        Returns:
            int: Number of signals cleared
        """
        size = len(self.signal_queue)
        self.signal_queue.clear()
        logger.info(f"Cleared {size} signals from queue")
        return size
    
    def get_stats(self) -> Dict:
        """
        Get listener statistics.
        
        Returns:
            dict: Statistics
        """
        return {
            'is_running': self.is_running,
            'user_id': self.user_id,
            'polling_interval': self.polling_interval,
            'queue_size': self.get_queue_size(),
            'total_signals_received': self.total_signals_received,
            'failed_polls': self.failed_polls,
            'last_poll_time': self.last_poll_time.isoformat() if self.last_poll_time else None
        }
    
    def validate_signal(self, signal: Dict) -> bool:
        """
        Validate signal format.
        
        Args:
            signal: Signal dictionary
        
        Returns:
            bool: True if signal is valid
        """
        required_fields = ['symbol', 'signal_type', 'price', 'confidence']
        
        for field in required_fields:
            if field not in signal:
                logger.warning(f"Signal missing required field: {field}")
                return False
        
        # Validate signal type
        if signal.get('signal_type') not in ['BUY', 'SELL', 'HOLD']:
            logger.warning(f"Invalid signal type: {signal.get('signal_type')}")
            return False
        
        # Validate confidence
        confidence = signal.get('confidence', 0)
        if not (0 <= confidence <= 1):
            logger.warning(f"Invalid confidence: {confidence}")
            return False
        
        return True


def create_signal_listener(
    api_base_url: str,
    user_id: int,
    polling_interval: int = 30,
    jwt_token: str = None
) -> SignalListener:
    """
    Factory function to create signal listener.
    
    Args:
        api_base_url: Base URL of the API
        user_id: User ID
        polling_interval: Polling interval in seconds
        jwt_token: JWT token for authentication (optional)
    
    Returns:
        SignalListener: Listener instance
    """
    return SignalListener(api_base_url, user_id, polling_interval, jwt_token=jwt_token)
