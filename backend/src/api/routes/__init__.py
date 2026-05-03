# API routes module
from src.api.routes.backtesting_routes import backtesting_bp
from src.api.routes.dashboard_routes import dashboard_bp
from src.api.routes.optimization_routes import optimization_bp
from src.api.routes.stress_testing_routes import stress_bp
from src.api.routes.execution_routes import execution_bp

__all__ = [
    'backtesting_bp',
    'dashboard_bp',
    'optimization_bp',
    'stress_bp',
    'execution_bp'
]
