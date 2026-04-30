# API routes module
from .backtesting_routes import backtesting_bp
from .dashboard_routes import dashboard_bp
from .optimization_routes import optimization_bp
from .stress_testing_routes import stress_bp
from .execution_routes import execution_bp

__all__ = [
    'backtesting_bp',
    'dashboard_bp',
    'optimization_bp',
    'stress_bp',
    'execution_bp'
]
