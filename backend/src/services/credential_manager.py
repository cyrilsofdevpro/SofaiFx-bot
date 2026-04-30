"""
Credential Encryption Service - Handles secure storage of MT5 credentials

Uses Fernet (symmetric encryption) from cryptography library
Each instance of the service uses a master key from config
"""

from cryptography.fernet import Fernet
import hashlib
import base64
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CredentialEncryptor:
    """
    Securely encrypt and decrypt user credentials.
    
    Uses Fernet (symmetric encryption) with a master key derived from config.
    """
    
    def __init__(self, master_key: str):
        """
        Initialize encryptor with master key.
        
        Args:
            master_key: Master encryption key (should be stored in config/environment)
        """
        self.master_key = master_key
        self._cipher_suite = None
        self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize Fernet cipher with master key"""
        try:
            # Derive a proper key from the master key using SHA256
            # This ensures the key is the right length (32 bytes) for Fernet
            key_material = hashlib.sha256(self.master_key.encode()).digest()
            # Encode to base64 for Fernet
            key = base64.urlsafe_b64encode(key_material)
            self._cipher_suite = Fernet(key)
            logger.info("✓ Cipher suite initialized")
        except Exception as e:
            logger.error(f"Failed to initialize cipher: {e}")
            raise
    
    def encrypt_credentials(self, login: str, password: str) -> Tuple[str, str]:
        """
        Encrypt MT5 login and password.
        
        Args:
            login: MT5 login ID
            password: MT5 password
            
        Returns:
            Tuple of (encrypted_login, encrypted_password)
        """
        try:
            encrypted_login = self._cipher_suite.encrypt(login.encode()).decode()
            encrypted_password = self._cipher_suite.encrypt(password.encode()).decode()
            logger.debug(f"Credentials encrypted for login {login[:4]}***")
            return encrypted_login, encrypted_password
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise
    
    def decrypt_credentials(self, encrypted_login: str, encrypted_password: str) -> Tuple[str, str]:
        """
        Decrypt MT5 login and password.
        
        Args:
            encrypted_login: Encrypted login ID
            encrypted_password: Encrypted password
            
        Returns:
            Tuple of (login, password)
        """
        try:
            login = self._cipher_suite.decrypt(encrypted_login.encode()).decode()
            password = self._cipher_suite.decrypt(encrypted_password.encode()).decode()
            logger.debug(f"Credentials decrypted for login {login[:4]}***")
            return login, password
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise
    
    def encrypt_login(self, login: str) -> str:
        """
        Encrypt only login ID.
        
        Args:
            login: MT5 login ID
            
        Returns:
            Encrypted login
        """
        try:
            encrypted = self._cipher_suite.encrypt(login.encode()).decode()
            return encrypted
        except Exception as e:
            logger.error(f"Failed to encrypt login: {e}")
            raise
    
    def decrypt_login(self, encrypted_login: str) -> str:
        """
        Decrypt only login ID.
        
        Args:
            encrypted_login: Encrypted login ID
            
        Returns:
            Decrypted login
        """
        try:
            login = self._cipher_suite.decrypt(encrypted_login.encode()).decode()
            return login
        except Exception as e:
            logger.error(f"Failed to decrypt login: {e}")
            raise


class MT5CredentialManager:
    """
    Manager for MT5 credentials storage and retrieval.
    Handles encryption/decryption with credential encryptor.
    """
    
    def __init__(self, encryptor: CredentialEncryptor):
        """
        Initialize credential manager.
        
        Args:
            encryptor: CredentialEncryptor instance
        """
        self.encryptor = encryptor
    
    def store_credentials(self, user, login: str, password: str, server: str, account_number: Optional[str] = None):
        """
        Store encrypted MT5 credentials for user.
        
        Args:
            user: User model instance
            login: MT5 login ID
            password: MT5 password
            server: MT5 server name
            account_number: MT5 account number (optional, for reference)
        """
        try:
            encrypted_login, encrypted_password = self.encryptor.encrypt_credentials(login, password)
            
            user.mt5_login = encrypted_login
            user.mt5_password = encrypted_password
            user.mt5_server = server
            user.mt5_account_number = account_number or login  # Use login as default if not provided
            
            logger.info(f"✓ Credentials stored for user {user.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            raise
    
    def retrieve_credentials(self, user) -> Tuple[str, str, str]:
        """
        Retrieve decrypted MT5 credentials for user.
        
        Args:
            user: User model instance
            
        Returns:
            Tuple of (login, password, server)
        """
        try:
            if not user.mt5_login or not user.mt5_password:
                raise ValueError("Credentials not configured for this user")
            
            login, password = self.encryptor.decrypt_credentials(user.mt5_login, user.mt5_password)
            server = user.mt5_server
            
            logger.debug(f"✓ Credentials retrieved for user {user.id}")
            return login, password, server
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            raise
    
    def clear_credentials(self, user):
        """
        Clear stored MT5 credentials for user.
        
        Args:
            user: User model instance
        """
        try:
            user.mt5_login = None
            user.mt5_password = None
            user.mt5_server = None
            user.mt5_account_number = None
            user.mt5_connected = False
            user.mt5_connection_time = None
            
            logger.info(f"✓ Credentials cleared for user {user.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear credentials: {e}")
            raise
    
    def has_credentials(self, user) -> bool:
        """
        Check if user has stored MT5 credentials.
        
        Args:
            user: User model instance
            
        Returns:
            True if credentials are stored
        """
        return bool(user.mt5_login and user.mt5_password and user.mt5_server)
    
    def get_decrypted_credentials(self, user) -> Tuple[str, str]:
        """
        Get decrypted MT5 login and password for user.
        
        Args:
            user: User model instance
            
        Returns:
            Tuple of (login, password)
        """
        try:
            if not user.mt5_login or not user.mt5_password:
                raise ValueError("Credentials not configured for this user")
            
            login, password = self.encryptor.decrypt_credentials(user.mt5_login, user.mt5_password)
            logger.debug(f"✓ Credentials decrypted for user {user.id}")
            return login, password
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise
