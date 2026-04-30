"""
Backtesting API Routes
Endpoints for running historical backtests and retrieving results
"""
from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from ...backtesting.backtester import BacktestingEngine

logger = logging.getLogger(__name__)
backtesting_bp = Blueprint('backtesting', __name__, url_prefix='/api/backtesting')

# Initialize backtesting engine
backtester = BacktestingEngine()


@backtesting_bp.route('/run', methods=['POST'])
def run_backtest():
    """
    Run a backtest on specified pair with date range
    
    Request body:
    {
        "pair": "EURUSD",
        "start_date": "2023-01-01",
        "end_date": "2024-01-01",
        "initial_balance": 10000,
        "lot_size": 0.1
    }
    
    Response: {
        "status": "success",
        "data": {
            "pair": "EURUSD",
            "total_trades": 45,
            "winning_trades": 28,
            "win_rate": 62.2,
            "total_pnl": 1250.50,
            "max_drawdown": -8.5,
            "sharpe_ratio": 1.45,
            ...
        },
        "equity_curve": [...]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pair', 'start_date', 'end_date', 'initial_balance']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {required_fields}'
            }), 400
        
        pair = data['pair'].upper()
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        initial_balance = float(data['initial_balance'])
        lot_size = float(data.get('lot_size', 0.1))
        
        logger.info(f"[BACKTEST] Running backtest: {pair} from {start_date} to {end_date}")
        
        # Run backtest
        results = backtester.backtest_pair(
            pair=pair,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            lot_size=lot_size
        )
        
        logger.info(f"[BACKTEST] Backtest complete for {pair}: {results['total_trades']} trades")
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
        
    except ValueError as e:
        logger.error(f"[BACKTEST] Date parsing error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid date format. Use YYYY-MM-DD: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[BACKTEST] Error running backtest: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@backtesting_bp.route('/quick', methods=['POST'])
def quick_backtest():
    """
    Quick backtest with sensible defaults (last 6 months)
    
    Request body:
    {
        "pair": "EURUSD",
        "initial_balance": 10000
    }
    """
    try:
        data = request.get_json()
        pair = data.get('pair', 'EURUSD').upper()
        initial_balance = float(data.get('initial_balance', 10000))
        
        # Default to last 6 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        logger.info(f"[BACKTEST] Quick backtest: {pair}, default 6-month window")
        
        results = backtester.backtest_pair(
            pair=pair,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance
        )
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"[BACKTEST] Quick backtest error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@backtesting_bp.route('/history', methods=['GET'])
def get_backtest_history():
    """
    Get list of recent backtests (stub - would query database)
    
    Returns: [
        {
            "id": 1,
            "pair": "EURUSD",
            "run_date": "2024-01-15",
            "total_trades": 45,
            "win_rate": 62.2,
            "total_pnl": 1250.50
        },
        ...
    ]
    """
    try:
        # TODO: Query database for backtest history
        # For now, return empty list
        logger.info("[BACKTEST] Fetching backtest history")
        
        return jsonify({
            'status': 'success',
            'data': [],
            'message': 'Backtest history database integration pending'
        }), 200
        
    except Exception as e:
        logger.error(f"[BACKTEST] History fetch error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@backtesting_bp.route('/export/<int:backtest_id>', methods=['GET'])
def export_backtest(backtest_id):
    """
    Export backtest results as CSV or JSON
    
    Query params:
    - format: 'csv' or 'json' (default: 'json')
    """
    try:
        fmt = request.args.get('format', 'json').lower()
        
        if fmt not in ['csv', 'json']:
            return jsonify({
                'status': 'error',
                'message': 'Format must be csv or json'
            }), 400
        
        # TODO: Fetch backtest from database and export
        logger.info(f"[BACKTEST] Export request: backtest_id={backtest_id}, format={fmt}")
        
        return jsonify({
            'status': 'error',
            'message': 'Backtest export database integration pending'
        }), 501
        
    except Exception as e:
        logger.error(f"[BACKTEST] Export error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
