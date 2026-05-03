"""
Blueprint Registration Helper
Centralizes registration of all API blueprints for the Flask app
"""
import logging

logger = logging.getLogger(__name__)


def register_feature_blueprints(app):
    """
    Register all Phase 5 feature blueprints with Flask application
    
    Call this function in your main Flask app initialization:
    
    Example:
        from flask import Flask
        from backend.src.api.routes_integration import register_feature_blueprints
        
        app = Flask(__name__)
        register_feature_blueprints(app)
    
    Args:
        app: Flask application instance
    """
    try:
        from src.routes import (
            backtesting_bp,
            dashboard_bp,
            optimization_bp,
            stress_bp,
            execution_bp
        )
        
        # Register backtesting routes
        app.register_blueprint(backtesting_bp)
        logger.info("[ROUTES] Registered backtesting routes (/api/backtesting/*)")
        
        # Register dashboard routes
        app.register_blueprint(dashboard_bp)
        logger.info("[ROUTES] Registered dashboard routes (/api/dashboard/*)")
        
        # Register optimization routes
        app.register_blueprint(optimization_bp)
        logger.info("[ROUTES] Registered optimization routes (/api/optimization/*)")
        
        # Register stress testing routes
        app.register_blueprint(stress_bp)
        logger.info("[ROUTES] Registered stress testing routes (/api/stress-test/*)")
        
        # Register execution reliability routes
        app.register_blueprint(execution_bp)
        logger.info("[ROUTES] Registered execution routes (/api/execution/*)")
        
        logger.info("[ROUTES] All Phase 5 feature blueprints registered successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"[ROUTES] Failed to import blueprints: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[ROUTES] Error registering blueprints: {str(e)}")
        return False


def get_routes_summary():
    """
    Get a summary of all registered API routes
    
    Returns:
        dict: Organized summary of all available endpoints
    """
    return {
        'backtesting': {
            'endpoints': [
                'POST /api/backtesting/run',
                'POST /api/backtesting/quick',
                'GET /api/backtesting/history',
                'GET /api/backtesting/export/<id>'
            ],
            'description': 'Run historical backtests and retrieve results'
        },
        'dashboard': {
            'endpoints': [
                'GET /api/dashboard/overview',
                'GET /api/dashboard/pair-performance',
                'GET /api/dashboard/equity-curve',
                'GET /api/dashboard/daily-pnl',
                'GET /api/dashboard/confidence-analysis',
                'GET /api/dashboard/drawdown-analysis',
                'GET /api/dashboard/health'
            ],
            'description': 'Real-time performance analytics and metrics'
        },
        'optimization': {
            'endpoints': [
                'GET /api/optimization/current-weights',
                'POST /api/optimization/update-weights',
                'GET /api/optimization/stats',
                'POST /api/optimization/run-optimization',
                'GET /api/optimization/pair-specific',
                'POST /api/optimization/reset-weights',
                'POST /api/optimization/save-weights'
            ],
            'description': 'Signal weight management and auto-optimization'
        },
        'stress_testing': {
            'endpoints': [
                'POST /api/stress-test/run',
                'GET /api/stress-test/results/<test_id>',
                'POST /api/stress-test/quick',
                'GET /api/stress-test/test-templates',
                'GET /api/stress-test/history'
            ],
            'description': 'System load testing and reliability validation'
        },
        'execution': {
            'endpoints': [
                'POST /api/execution/execute',
                'POST /api/execution/cancel/<trade_id>',
                'GET /api/execution/stats',
                'GET /api/execution/history',
                'POST /api/execution/validate',
                'GET /api/execution/slippage-report'
            ],
            'description': 'Trade execution with fault tolerance'
        }
    }
