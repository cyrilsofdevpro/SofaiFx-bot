# API routes module
from src.backtesting_routes import backtesting_bp
from src.dashboard_routes import dashboard_bp
from src.optimization_routes import optimization_bp
from src.stress_testing_routes import stress_bp
from src.execution_routes import execution_bp

__all__ = [
    'backtesting_bp',
    'dashboard_bp',
    'optimization_bp',
    'stress_bp',
    'execution_bp'
]
