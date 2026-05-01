import os
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

class Config:
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    # Twelve Data API
    TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY', '')
    
    # Hugging Face API
    HF_API_KEY = os.getenv('HF_API_KEY', '')
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Email Settings
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
    
    # Trading Settings
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 3600))
    CURRENCY_PAIRS = os.getenv('CURRENCY_PAIRS', 'EURUSD,GBPUSD,USDJPY,AUDUSD,NZDUSD,EURJPY,GBPJPY,EURAUD,EURCAD,EURCHF,GBPAUD,GBPCAD,GBPCHF,AUDJPY,AUDCAD,AUDNZD,NZDJPY,CADJPY,CHFJPY').split(',')
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', 14))
    RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', 70))
    RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', 30))
    
    # Flask
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    # Parse FLASK_DEBUG: only set to True if explicitly set to true/1/yes
    # Default to False if not set or set to anything else
    _debug_env = os.getenv('FLASK_DEBUG', '').strip().lower()
    FLASK_DEBUG = _debug_env in ('true', '1', 'yes') if _debug_env else False
    
    # JWT Authentication
    # CRITICAL: This secret key MUST be consistent. Change only in production with valid .env file
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'sofai-fx-secret-key-change-in-production')
    
    # Credential Encryption
    # Master key for encrypting/decrypting user credentials (especially MT5 passwords)
    ENCRYPTION_MASTER_KEY = os.getenv('ENCRYPTION_MASTER_KEY', 'sofai-fx-encryption-master-key-change-in-production')
    ENCRYPTION_KEY = ENCRYPTION_MASTER_KEY  # Alias for backward compatibility

config = Config()
