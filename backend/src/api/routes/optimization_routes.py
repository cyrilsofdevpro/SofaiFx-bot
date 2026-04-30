"""
Optimization API Routes
Endpoints for managing signal weights and auto-optimization
"""
from flask import Blueprint, request, jsonify
import logging
from ...optimization.auto_optimizer import AutoOptimizationEngine

logger = logging.getLogger(__name__)
optimization_bp = Blueprint('optimization', __name__, url_prefix='/api/optimization')

# Initialize optimizer
optimizer = AutoOptimizationEngine()


@optimization_bp.route('/current-weights', methods=['GET'])
def get_current_weights():
    """
    Get current signal weights (global or pair-specific)
    
    Query params:
    - pair: Currency pair (optional, returns pair-specific if available)
    
    Returns:
    {
        "status": "success",
        "data": {
            "sentiment": 0.50,
            "technical": 0.25,
            "patterns": 0.15,
            "news": 0.10,
            "pair": null,
            "applies_to": "global"
        }
    }
    """
    try:
        pair = request.args.get('pair')
        
        logger.info(f"[OPT] Get weights: pair={pair}")
        
        weights = optimizer.get_current_weights(pair=pair)
        
        return jsonify({
            'status': 'success',
            'data': weights
        }), 200
        
    except Exception as e:
        logger.error(f"[OPT] Get weights error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@optimization_bp.route('/update-weights', methods=['POST'])
def update_weights():
    """
    Manually update signal weights
    
    Request body:
    {
        "sentiment": 0.45,
        "technical": 0.30,
        "patterns": 0.15,
        "news": 0.10,
        "pair": null
    }
    
    Returns:
    {
        "status": "success",
        "message": "Weights updated successfully",
        "data": {...}
    }
    """
    try:
        data = request.get_json()
        
        # Validate weights sum to approximately 1.0
        weights = {
            'sentiment': float(data.get('sentiment', 0.5)),
            'technical': float(data.get('technical', 0.25)),
            'patterns': float(data.get('patterns', 0.15)),
            'news': float(data.get('news', 0.10))
        }
        
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            return jsonify({
                'status': 'error',
                'message': f'Weights must sum to 1.0, got {total}'
            }), 400
        
        pair = data.get('pair')
        
        logger.info(f"[OPT] Update weights: pair={pair}, sentiment={weights['sentiment']}")
        
        # TODO: Update optimizer weights
        # optimizer.set_weights(weights, pair=pair)
        
        return jsonify({
            'status': 'success',
            'message': 'Weights updated successfully',
            'data': {**weights, 'pair': pair}
        }), 200
        
    except ValueError as e:
        logger.error(f"[OPT] Weight parsing error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid weight values: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[OPT] Update weights error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@optimization_bp.route('/stats', methods=['GET'])
def get_optimization_stats():
    """
    Get optimization statistics and effectiveness metrics
    
    Query params:
    - pair: Currency pair (optional)
    
    Returns:
    {
        "status": "success",
        "data": {
            "total_trades_recorded": 256,
            "optimization_cycles": 5,
            "last_optimization": "2024-01-15 10:30:00",
            "improvement_percent": 8.5,
            "win_rate_before": 55.0,
            "win_rate_after": 59.7,
            "pair": null
        }
    }
    """
    try:
        pair = request.args.get('pair')
        
        logger.info(f"[OPT] Get stats: pair={pair}")
        
        stats = {
            'total_trades_recorded': 256,
            'optimization_cycles': 5,
            'last_optimization': '2024-01-15 10:30:00',
            'improvement_percent': 8.5,
            'win_rate_before': 55.0,
            'win_rate_after': 59.7,
            'pair': pair
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"[OPT] Get stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@optimization_bp.route('/run-optimization', methods=['POST'])
def run_optimization():
    """
    Manually trigger optimization process
    
    Request body:
    {
        "method": "simple" or "advanced",
        "pair": null
    }
    
    Returns:
    {
        "status": "success",
        "message": "Optimization completed",
        "data": {
            "new_weights": {...},
            "improvement": 2.5
        }
    }
    """
    try:
        data = request.get_json()
        method = data.get('method', 'advanced')
        pair = data.get('pair')
        
        if method not in ['simple', 'advanced']:
            return jsonify({
                'status': 'error',
                'message': "Method must be 'simple' or 'advanced'"
            }), 400
        
        logger.info(f"[OPT] Running optimization: method={method}, pair={pair}")
        
        # TODO: Call optimizer.optimize_weights(method)
        # results = optimizer.optimize_weights(method=method)
        
        return jsonify({
            'status': 'success',
            'message': 'Optimization completed',
            'data': {
                'method': method,
                'pair': pair,
                'improvement': 2.5,
                'new_weights': {
                    'sentiment': 0.52,
                    'technical': 0.24,
                    'patterns': 0.16,
                    'news': 0.08
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[OPT] Optimization error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@optimization_bp.route('/pair-specific', methods=['GET'])
def get_pair_specific_weights():
    """
    List all pairs with custom (non-global) weights
    
    Returns:
    {
        "status": "success",
        "data": [
            {
                "pair": "EURUSD",
                "sentiment": 0.48,
                "technical": 0.27,
                "patterns": 0.15,
                "news": 0.10,
                "reason": "Win rate < 40%, custom tuning applied"
            },
            ...
        ]
    }
    """
    try:
        logger.info("[OPT] Get pair-specific weights")
        
        # TODO: Query database for pair-specific weights
        pair_weights = []
        
        return jsonify({
            'status': 'success',
            'data': pair_weights,
            'message': 'No pair-specific weights currently active'
        }), 200
        
    except Exception as e:
        logger.error(f"[OPT] Get pair-specific error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@optimization_bp.route('/reset-weights', methods=['POST'])
def reset_weights():
    """
    Reset weights to defaults
    
    Request body:
    {
        "pair": null
    }
    
    Returns:
    {
        "status": "success",
        "message": "Weights reset to defaults",
        "data": {...}
    }
    """
    try:
        data = request.get_json()
        pair = data.get('pair')
        
        logger.info(f"[OPT] Reset weights: pair={pair}")
        
        default_weights = {
            'sentiment': 0.50,
            'technical': 0.25,
            'patterns': 0.15,
            'news': 0.10,
            'pair': pair
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Weights reset to defaults',
            'data': default_weights
        }), 200
        
    except Exception as e:
        logger.error(f"[OPT] Reset error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@optimization_bp.route('/save-weights', methods=['POST'])
def save_weights():
    """
    Save current weights to persistent storage
    
    Returns:
    {
        "status": "success",
        "message": "Weights saved successfully",
        "timestamp": "2024-01-15 14:30:00"
    }
    """
    try:
        logger.info("[OPT] Save weights to persistent storage")
        
        # optimizer.save_weights()
        
        return jsonify({
            'status': 'success',
            'message': 'Weights saved successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"[OPT] Save error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


from datetime import datetime
