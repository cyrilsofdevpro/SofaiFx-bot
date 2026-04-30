"""
Execution Reliability API Routes
Endpoints for managing trade execution with fault tolerance
"""
from flask import Blueprint, request, jsonify
import logging
from ...execution.reliability import ExecutionReliabilityEngine

logger = logging.getLogger(__name__)
execution_bp = Blueprint('execution', __name__, url_prefix='/api/execution')

# Initialize execution engine
execution_engine = ExecutionReliabilityEngine()


@execution_bp.route('/execute', methods=['POST'])
def execute_trade():
    """
    Execute a trade with automatic retry logic and validation
    
    Request body:
    {
        "pair": "EURUSD",
        "signal": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0820,
        "take_profit": 1.0900,
        "volume": 0.1,
        "strategy": "signal_engine"
    }
    
    Returns:
    {
        "status": "success",
        "data": {
            "trade_id": "trade_abc123",
            "pair": "EURUSD",
            "signal": "BUY",
            "execution_time_ms": 245,
            "attempts": 1,
            "actual_price": 1.0851,
            "slippage_pct": 0.009,
            "order_status": "filled"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pair', 'signal', 'entry_price', 'stop_loss', 'take_profit', 'volume']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {required_fields}'
            }), 400
        
        # Validate signal
        signal = data['signal'].upper()
        if signal not in ['BUY', 'SELL', 'HOLD']:
            return jsonify({
                'status': 'error',
                'message': "Signal must be 'BUY', 'SELL', or 'HOLD'"
            }), 400
        
        # Validate price levels
        entry = float(data['entry_price'])
        stop = float(data['stop_loss'])
        tp = float(data['take_profit'])
        
        if signal == 'BUY':
            if not (stop < entry < tp):
                return jsonify({
                    'status': 'error',
                    'message': 'For BUY: stop_loss < entry_price < take_profit'
                }), 400
        elif signal == 'SELL':
            if not (tp < entry < stop):
                return jsonify({
                    'status': 'error',
                    'message': 'For SELL: take_profit < entry_price < stop_loss'
                }), 400
        
        trade_params = {
            'pair': data['pair'].upper(),
            'signal': signal,
            'entry_price': entry,
            'stop_loss': stop,
            'take_profit': tp,
            'volume': float(data['volume']),
            'strategy': data.get('strategy', 'signal_engine'),
            'confidence': float(data.get('confidence', 0.5))
        }
        
        logger.info(f"[EXEC] Execute trade: {trade_params['pair']} {signal}")
        
        # Execute trade with retry logic
        result = execution_engine.execute_trade(trade_params)
        
        logger.info(f"[EXEC] Trade {result.get('trade_id')} executed: {result.get('order_status')}")
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except ValueError as e:
        logger.error(f"[EXEC] Validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid parameters: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[EXEC] Execution error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@execution_bp.route('/cancel/<trade_id>', methods=['POST'])
def cancel_trade(trade_id):
    """
    Cancel a pending trade
    
    Returns:
    {
        "status": "success",
        "data": {
            "trade_id": "trade_abc123",
            "cancelled": true,
            "message": "Order cancelled successfully"
        }
    }
    """
    try:
        logger.info(f"[EXEC] Cancel trade: {trade_id}")
        
        result = execution_engine.cancel_trade(trade_id)
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"[EXEC] Cancel error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@execution_bp.route('/stats', methods=['GET'])
def get_execution_stats():
    """
    Get execution reliability statistics
    
    Returns:
    {
        "status": "success",
        "data": {
            "total_executions": 245,
            "successful": 238,
            "failed": 7,
            "success_rate": 97.1,
            "avg_execution_time_ms": 234,
            "avg_slippage_pct": 0.018,
            "max_slippage_pct": 0.15,
            "retries_triggered": 12,
            "retry_success_rate": 83.3
        }
    }
    """
    try:
        logger.info("[EXEC] Get execution stats")
        
        stats = execution_engine.get_execution_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"[EXEC] Stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@execution_bp.route('/history', methods=['GET'])
def get_execution_history():
    """
    Get recent execution history
    
    Query params:
    - limit: Max trades to return (default: 50)
    - pair: Filter by currency pair (optional)
    - status: Filter by status (filled/cancelled/failed) (optional)
    
    Returns:
    {
        "status": "success",
        "data": [
            {
                "trade_id": "trade_abc123",
                "pair": "EURUSD",
                "signal": "BUY",
                "entry_price": 1.0850,
                "actual_price": 1.0851,
                "order_status": "filled",
                "execution_time": "2024-01-15 14:30:00",
                "attempts": 1,
                "slippage_pct": 0.009
            },
            ...
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 50))
        pair = request.args.get('pair')
        status = request.args.get('status')
        
        logger.info(f"[EXEC] Get history: limit={limit}, pair={pair}, status={status}")
        
        history = execution_engine.get_execution_history(limit=limit, pair=pair, status=status)
        
        return jsonify({
            'status': 'success',
            'data': history
        }), 200
        
    except Exception as e:
        logger.error(f"[EXEC] History error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@execution_bp.route('/validate', methods=['POST'])
def validate_trade():
    """
    Validate trade parameters before execution (dry run)
    
    Request body: Same as /execute
    
    Returns:
    {
        "status": "success",
        "data": {
            "valid": true,
            "errors": [],
            "warnings": ["Take profit very close to entry price"],
            "estimated_execution_time_ms": 200
        }
    }
    """
    try:
        data = request.get_json()
        
        logger.info(f"[EXEC] Validate trade: {data.get('pair')}")
        
        # Basic validation
        errors = []
        warnings = []
        
        if not data.get('pair'):
            errors.append("Missing pair")
        if not data.get('signal'):
            errors.append("Missing signal")
        if not data.get('volume') or float(data.get('volume', 0)) <= 0:
            errors.append("Invalid volume")
        
        # Check price levels
        try:
            entry = float(data['entry_price'])
            stop = float(data['stop_loss'])
            tp = float(data['take_profit'])
            
            if abs(tp - entry) < abs(entry * 0.001):  # Less than 0.1% TP
                warnings.append("Take profit very close to entry price")
            
            if abs(stop - entry) < abs(entry * 0.0005):  # Less than 0.05% SL
                warnings.append("Stop loss very close to entry price")
                
        except (TypeError, ValueError):
            errors.append("Invalid price values")
        
        return jsonify({
            'status': 'success',
            'data': {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'estimated_execution_time_ms': 200
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[EXEC] Validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@execution_bp.route('/slippage-report', methods=['GET'])
def get_slippage_report():
    """
    Get slippage analysis and optimization recommendations
    
    Query params:
    - pair: Currency pair (optional)
    - days: Days to analyze (default: 30)
    
    Returns:
    {
        "status": "success",
        "data": {
            "avg_slippage_pct": 0.018,
            "median_slippage_pct": 0.012,
            "max_slippage_pct": 0.15,
            "best_execution_hour": 14,
            "worst_execution_hour": 3,
            "recommendations": [
                "Consider executing during peak hours (12-16 UTC)"
            ]
        }
    }
    """
    try:
        pair = request.args.get('pair')
        days = int(request.args.get('days', 30))
        
        logger.info(f"[EXEC] Get slippage report: pair={pair}, days={days}")
        
        report = execution_engine.get_slippage_report(pair=pair, days=days)
        
        return jsonify({
            'status': 'success',
            'data': report
        }), 200
        
    except Exception as e:
        logger.error(f"[EXEC] Slippage report error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
