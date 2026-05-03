"""
Dashboard API Routes
Endpoints for performance analytics and metrics visualization
"""
from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
from src.analytics.dashboard import PerformanceDashboard

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# Initialize dashboard
dashboard = PerformanceDashboard()


@dashboard_bp.route('/backtest/results', methods=['GET'])
def get_backtest_results():
    """
    Get precomputed backtest results for dashboard display
    
    Query params:
    - pair: Currency pair (e.g., EURUSD, GBPJPY) - optional, returns all if not specified
    - range: Date range (e.g., 30d, 90d, 180d, 1y) - default: 90d
    
    Returns:
    {
        "status": "success",
        "data": [
            {
                "pair": "EURUSD",
                "timeframe": "D1",
                "date_range": "2025-08-01 to 2026-04-30",
                "total_trades": 45,
                "win_rate": 62.2,
                "pnl": 1250.50,
                "max_drawdown": -8.5,
                "equity_curve": [10000, 10045, 10089, ...],
                "trades": [...]
            },
            ...
        ]
    }
    """
    try:
        pair = request.args.get('pair', '').upper()
        range_param = request.args.get('range', '90d')
        
        logger.info(f"[DASH] Backtest results: pair={pair}, range={range_param}")
        
        # Parse date range
        days = _parse_range_to_days(range_param)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get backtest results from database or compute
        results = _get_backtest_results(pair=pair, start_date=start_date, end_date=end_date)
        
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Backtest results error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def _parse_range_to_days(range_str: str) -> int:
    """Convert range string to days"""
    range_str = range_str.lower().strip()
    if range_str.endswith('d'):
        return int(range_str[:-1])
    elif range_str.endswith('w'):
        return int(range_str[:-1]) * 7
    elif range_str.endswith('m'):
        return int(range_str[:-1]) * 30
    elif range_str.endswith('y'):
        return int(range_str[:-1]) * 365
    elif range_str.isdigit():
        return int(range_str)
    return 90  # default


def _get_backtest_results(pair: str, start_date: datetime, end_date: datetime):
    """
    Get backtest results - from database or compute on-the-fly
    TODO: Replace with actual database query
    """
    from src.backtesting.backtester import BacktestingEngine
    
    # Define pairs to analyze
    pairs_to_analyze = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
    if pair:
        pairs_to_analyze = [pair]
    
    results = []
    backtester = BacktestingEngine()
    
    for pair in pairs_to_analyze:
        try:
            # Run backtest for this pair
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            bt_result = backtester.backtest_pair(
                pair=pair,
                start_date=start_str,
                end_date=end_str,
                initial_balance=10000
            )
            
            # Extract metrics
            metrics = bt_result.get('metrics', {})
            trades = bt_result.get('trades', [])
            equity_curve = bt_result.get('equity_curve', [])
            
            result = {
                'pair': pair,
                'timeframe': 'D1',
                'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'total_trades': len(trades),
                'win_rate': metrics.get('win_rate', 0),
                'pnl': metrics.get('total_pnl', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'equity_curve': equity_curve,
                'trades': trades[:10] if trades else []  # Limit to 10 for display
            }
            
            results.append(result)
            logger.info(f"[DASH] Backtest for {pair}: {result['total_trades']} trades, {result['win_rate']:.1f}% win rate")
            
        except Exception as e:
            logger.warning(f"[DASH] Backtest failed for {pair}: {str(e)}")
            continue
    
    return results


@dashboard_bp.route('/overview', methods=['GET'])
def get_overview():
    """
    Get overall system performance metrics
    
    Query params:
    - days: Number of days to analyze (default: 90)
    
    Returns:
    {
        "status": "success",
        "data": {
            "total_trades": 156,
            "win_rate": 58.3,
            "total_pnl": 2847.50,
            "profit_factor": 1.85,
            "accuracy": 0.583,
            "max_drawdown": -12.5,
            "sharpe_ratio": 1.23
        }
    }
    """
    try:
        days = int(request.args.get('days', 90))
        logger.info(f"[DASH] Overview metrics: {days}-day window")
        
        metrics = dashboard.get_overall_metrics(days=days)
        
        return jsonify({
            'status': 'success',
            'data': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Overview error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/pair-performance', methods=['GET'])
def get_pair_performance():
    """
    Get performance breakdown by currency pair
    
    Query params:
    - days: Number of days (default: 90)
    - sort_by: 'win_rate', 'pnl', 'trades' (default: 'win_rate')
    - limit: Max pairs to return (default: 10)
    
    Returns:
    {
        "status": "success",
        "data": [
            {
                "pair": "EURUSD",
                "trades": 45,
                "win_rate": 62.2,
                "total_pnl": 1250.50,
                "avg_win": 35.50,
                "avg_loss": -20.25
            },
            ...
        ]
    }
    """
    try:
        days = int(request.args.get('days', 90))
        sort_by = request.args.get('sort_by', 'win_rate')
        limit = int(request.args.get('limit', 10))
        
        logger.info(f"[DASH] Pair performance: days={days}, sort={sort_by}, limit={limit}")
        
        pairs = dashboard.get_pair_performance(
            days=days,
            sort_by=sort_by,
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'data': pairs
        }), 200
        
    except ValueError as e:
        logger.error(f"[DASH] Parameter error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid parameters: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[DASH] Pair performance error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/equity-curve', methods=['GET'])
def get_equity_curve():
    """
    Get equity curve (balance over time) for charting
    
    Query params:
    - pair: Currency pair (required if analyzing single pair)
    - days: Number of days (default: 90)
    - interval: 'daily' or 'hourly' (default: 'daily')
    
    Returns:
    {
        "status": "success",
        "data": {
            "timestamps": ["2024-01-01", "2024-01-02", ...],
            "balance": [10000, 10125.50, 10280.75, ...],
            "pair": "EURUSD"
        }
    }
    """
    try:
        pair = request.args.get('pair')
        days = int(request.args.get('days', 90))
        interval = request.args.get('interval', 'daily')
        
        logger.info(f"[DASH] Equity curve: pair={pair}, days={days}, interval={interval}")
        
        curve = dashboard.get_equity_curve(
            pair=pair,
            days=days,
            interval=interval
        )
        
        return jsonify({
            'status': 'success',
            'data': curve
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Equity curve error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/daily-pnl', methods=['GET'])
def get_daily_pnl():
    """
    Get daily P&L breakdown
    
    Query params:
    - pair: Currency pair (optional)
    - days: Number of days (default: 30)
    
    Returns:
    {
        "status": "success",
        "data": {
            "dates": ["2024-01-01", "2024-01-02", ...],
            "pnl": [125.50, -50.25, 200.75, ...],
            "pair": "EURUSD"
        }
    }
    """
    try:
        pair = request.args.get('pair')
        days = int(request.args.get('days', 30))
        
        logger.info(f"[DASH] Daily PnL: pair={pair}, days={days}")
        
        pnl = dashboard.get_daily_pnl(pair=pair, days=days)
        
        return jsonify({
            'status': 'success',
            'data': pnl
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Daily PnL error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/confidence-analysis', methods=['GET'])
def get_confidence_analysis():
    """
    Analyze accuracy stratified by signal confidence levels
    
    Query params:
    - days: Number of days (default: 90)
    
    Returns:
    {
        "status": "success",
        "data": {
            "high_confidence": {"count": 45, "accuracy": 68.9},
            "medium_confidence": {"count": 38, "accuracy": 55.3},
            "low_confidence": {"count": 22, "accuracy": 36.4}
        }
    }
    """
    try:
        days = int(request.args.get('days', 90))
        
        logger.info(f"[DASH] Confidence analysis: {days}-day window")
        
        analysis = dashboard.get_confidence_analysis(days=days)
        
        return jsonify({
            'status': 'success',
            'data': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Confidence analysis error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/drawdown-analysis', methods=['GET'])
def get_drawdown_analysis():
    """
    Get drawdown metrics and analysis
    
    Query params:
    - pair: Currency pair (optional)
    - days: Number of days (default: 90)
    
    Returns:
    {
        "status": "success",
        "data": {
            "current_drawdown": -5.2,
            "max_drawdown": -15.8,
            "avg_drawdown": -4.5,
            "recovery_time_days": 12,
            "pair": "EURUSD"
        }
    }
    """
    try:
        pair = request.args.get('pair')
        days = int(request.args.get('days', 90))
        
        logger.info(f"[DASH] Drawdown analysis: pair={pair}, days={days}")
        
        drawdown = dashboard.get_drawdown_analysis(pair=pair, days=days)
        
        return jsonify({
            'status': 'success',
            'data': drawdown
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Drawdown analysis error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@dashboard_bp.route('/health', methods=['GET'])
def get_health_status():
    """
    Get system health status and alerts
    
    Returns:
    {
        "status": "success",
        "data": {
            "system_status": "healthy",
            "last_trade": "2024-01-15 14:30:00",
            "active_signals": 5,
            "api_status": "connected",
            "alerts": []
        }
    }
    """
    try:
        logger.info("[DASH] Health check")
        
        # TODO: Implement health check logic
        health = {
            'system_status': 'healthy',
            'last_trade': datetime.now().isoformat(),
            'active_signals': 5,
            'api_status': 'connected',
            'alerts': []
        }
        
        return jsonify({
            'status': 'success',
            'data': health
        }), 200
        
    except Exception as e:
        logger.error(f"[DASH] Health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
