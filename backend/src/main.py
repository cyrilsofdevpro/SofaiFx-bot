"""
Entry point for Hugging Face Spaces deployment
Runs Flask app on port 7860 (required by HF Spaces)
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Override Flask port for HF Spaces
os.environ['FLASK_PORT'] = os.getenv('FLASK_PORT', '7860')

from src.api.flask_app import app
from src.utils.logger import logger
from src.scheduler import scheduler

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 7860))
    
    logger.info(f'🚀 Starting SofAi FX API server on port {port}...')
    logger.info('📍 Bound to 0.0.0.0 - accessible from Hugging Face Spaces')
    
    try:
        # Run on port 7860 for HF Spaces
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        logger.info('Shutting down...')
    finally:
        scheduler.stop()
        logger.info('Server stopped')
