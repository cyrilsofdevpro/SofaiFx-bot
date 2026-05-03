"""
Stress Testing API Routes
Endpoints for system load testing and reliability validation
"""
from flask import Blueprint, request, jsonify
import logging
import threading
from src.testing.stress_test import StressTestEngine

logger = logging.getLogger(__name__)
stress_bp = Blueprint('stress_testing', __name__, url_prefix='/api/stress-test')

# Initialize stress tester
stress_tester = StressTestEngine()


@stress_bp.route('/run', methods=['POST'])
def run_stress_test():
    """
    Run a stress test with specified parameters
    
    Request body:
    {
        "name": "Load Test 1",
        "num_users": 50,
        "requests_per_user": 20,
        "duration_seconds": 300,
        "test_type": "concurrent"
    }
    
    Returns (async):
    {
        "status": "started",
        "test_id": "test_abc123",
        "message": "Stress test started, check results endpoint for completion"
    }
    
    Or (if sync mode):
    {
        "status": "success",
        "data": {
            "total_requests": 1000,
            "successful": 950,
            "failed": 50,
            "error_rate": 5.0,
            "throughput_req_sec": 18.5,
            "response_times": {
                "p50": 45,
                "p95": 120,
                "p99": 250
            },
            "verdict": "PASS"
        }
    }
    """
    try:
        data = request.get_json()
        
        config = {
            'name': data.get('name', 'Stress Test'),
            'num_users': int(data.get('num_users', 10)),
            'requests_per_user': int(data.get('requests_per_user', 10)),
            'duration_seconds': int(data.get('duration_seconds', 60)),
            'test_type': data.get('test_type', 'concurrent')
        }
        
        logger.info(f"[STRESS] Starting test: {config['name']}")
        logger.info(f"[STRESS] Config: {config['num_users']} users, {config['requests_per_user']} req/user")
        
        # Run stress test (async via threading)
        test_id = stress_tester.generate_test_id()
        
        def run_test_async():
            try:
                results = stress_tester.run_stress_test(config)
                stress_tester.store_results(test_id, results)
                logger.info(f"[STRESS] Test {test_id} completed: {results['verdict']}")
            except Exception as e:
                logger.error(f"[STRESS] Test {test_id} failed: {str(e)}")
                stress_tester.store_results(test_id, {'status': 'error', 'message': str(e)})
        
        # Start test in background thread
        thread = threading.Thread(target=run_test_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'test_id': test_id,
            'message': 'Stress test started, check results endpoint for completion'
        }), 202
        
    except ValueError as e:
        logger.error(f"[STRESS] Parameter error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid parameters: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[STRESS] Error starting test: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@stress_bp.route('/results/<test_id>', methods=['GET'])
def get_test_results(test_id):
    """
    Get results of a specific stress test
    
    Returns:
    {
        "status": "complete" or "running" or "not_found",
        "data": {
            "total_requests": 1000,
            "successful": 950,
            "failed": 50,
            "error_rate": 5.0,
            "throughput_req_sec": 18.5,
            "response_times": {
                "p50": 45,
                "p95": 120,
                "p99": 250,
                "min": 10,
                "max": 500,
                "mean": 75
            },
            "verdict": "PASS",
            "duration_seconds": 54.2
        }
    }
    """
    try:
        logger.info(f"[STRESS] Fetching results for test: {test_id}")
        
        results = stress_tester.get_results(test_id)
        
        if results is None:
            return jsonify({
                'status': 'not_found',
                'message': f'Test {test_id} not found'
            }), 404
        
        status = 'complete' if results.get('status') == 'completed' else 'running'
        
        return jsonify({
            'status': status,
            'data': results
        }), 200
        
    except Exception as e:
        logger.error(f"[STRESS] Results fetch error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@stress_bp.route('/quick', methods=['POST'])
def quick_stress_test():
    """
    Run a quick stress test with sensible defaults
    (10 users, 10 requests each, 60 second duration)
    
    Returns:
    {
        "status": "started",
        "test_id": "test_abc123",
        "message": "Quick stress test started"
    }
    """
    try:
        logger.info("[STRESS] Quick stress test initiated")
        
        config = {
            'name': 'Quick Stress Test',
            'num_users': 10,
            'requests_per_user': 10,
            'duration_seconds': 60,
            'test_type': 'concurrent'
        }
        
        test_id = stress_tester.generate_test_id()
        
        def run_quick_test():
            try:
                results = stress_tester.run_stress_test(config)
                stress_tester.store_results(test_id, results)
                logger.info(f"[STRESS] Quick test {test_id} completed")
            except Exception as e:
                logger.error(f"[STRESS] Quick test failed: {str(e)}")
                stress_tester.store_results(test_id, {'status': 'error', 'message': str(e)})
        
        thread = threading.Thread(target=run_quick_test)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'test_id': test_id,
            'message': 'Quick stress test started'
        }), 202
        
    except Exception as e:
        logger.error(f"[STRESS] Quick test error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@stress_bp.route('/test-templates', methods=['GET'])
def get_test_templates():
    """
    Get predefined stress test templates
    
    Returns:
    {
        "status": "success",
        "data": [
            {
                "name": "Light Load",
                "description": "10 users, 10 requests each",
                "config": {...}
            },
            {
                "name": "Normal Load",
                "description": "50 users, 20 requests each",
                "config": {...}
            },
            {
                "name": "Heavy Load",
                "description": "100 users, 50 requests each",
                "config": {...}
            },
            {
                "name": "Extreme Load",
                "description": "500 users, 100 requests each",
                "config": {...}
            }
        ]
    }
    """
    try:
        logger.info("[STRESS] Fetching test templates")
        
        templates = [
            {
                'name': 'Light Load',
                'description': '10 users, 10 requests each',
                'config': {
                    'num_users': 10,
                    'requests_per_user': 10,
                    'duration_seconds': 60
                }
            },
            {
                'name': 'Normal Load',
                'description': '50 users, 20 requests each',
                'config': {
                    'num_users': 50,
                    'requests_per_user': 20,
                    'duration_seconds': 120
                }
            },
            {
                'name': 'Heavy Load',
                'description': '100 users, 50 requests each',
                'config': {
                    'num_users': 100,
                    'requests_per_user': 50,
                    'duration_seconds': 180
                }
            },
            {
                'name': 'Extreme Load',
                'description': '500 users, 100 requests each',
                'config': {
                    'num_users': 500,
                    'requests_per_user': 100,
                    'duration_seconds': 300
                }
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': templates
        }), 200
        
    except Exception as e:
        logger.error(f"[STRESS] Templates error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@stress_bp.route('/history', methods=['GET'])
def get_stress_history():
    """
    Get history of recent stress tests
    
    Query params:
    - limit: Max results (default: 20)
    
    Returns:
    {
        "status": "success",
        "data": [
            {
                "test_id": "test_abc123",
                "name": "Load Test 1",
                "timestamp": "2024-01-15 14:30:00",
                "verdict": "PASS",
                "throughput": 18.5,
                "error_rate": 5.0
            },
            ...
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 20))
        
        logger.info(f"[STRESS] Fetching test history: limit={limit}")
        
        history = stress_tester.get_history(limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': history
        }), 200
        
    except Exception as e:
        logger.error(f"[STRESS] History error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
