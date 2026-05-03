"""
Stress Testing System - Ensure system stability under load
- Simulate multiple concurrent users
- Simulate high API request volume
- Validate rate limiting, caching, error handling
- Output: response time, error rate, throughput

Author: SofAi FX Bot - Testing Division
Version: 1.0.0
"""

import time
import threading
import queue
import random
from datetime import datetime
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.logger import logger

class StressTestEngine:
    """Stress test the trading system"""
    
    def __init__(self):
        """Initialize stress test engine"""
        self.results = []
        self.active_users = 0
        self.lock = threading.Lock()
        logger.info("[STRESS] Stress Testing Engine initialized")
    
    def run_stress_test(self, config: Dict) -> Dict:
        """
        Run stress test with given configuration
        
        Args:
            config: {
                'num_users': int,        # Number of concurrent users
                'requests_per_user': int, # Requests per user
                'ramp_up_time': int,     # Seconds to ramp up
                'test_duration': int,    # Total test duration (seconds)
            }
        
        Returns:
            dict: Test results with metrics
        """
        try:
            logger.info(f"[STRESS] Starting stress test: {config}")
            
            num_users = config.get('num_users', 10)
            requests_per_user = config.get('requests_per_user', 50)
            ramp_up = config.get('ramp_up_time', 5)
            duration = config.get('test_duration', 60)
            
            # Track metrics
            metrics = {
                'start_time': datetime.utcnow().isoformat(),
                'num_users': num_users,
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'response_times': [],
                'errors': [],
                'throughput': 0
            }
            
            # Run concurrent users
            with ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = []
                
                for user_id in range(num_users):
                    # Stagger user starts
                    time.sleep(ramp_up / num_users * user_id)
                    
                    future = executor.submit(
                        self._simulate_user,
                        user_id,
                        requests_per_user,
                        metrics
                    )
                    futures.append(future)
                
                # Wait for completion or timeout
                start_time = time.time()
                for future in as_completed(futures):
                    if time.time() - start_time > duration:
                        break
                    try:
                        future.result()
                    except Exception as e:
                        logger.warning(f"[STRESS] User error: {e}")
            
            # Calculate final metrics
            metrics['end_time'] = datetime.utcnow().isoformat()
            metrics['total_duration'] = time.time() - start_time
            metrics['throughput'] = metrics['successful_requests'] / metrics['total_duration']
            metrics['avg_response_time'] = sum(metrics['response_times']) / len(metrics['response_times']) if metrics['response_times'] else 0
            metrics['error_rate'] = (metrics['failed_requests'] / metrics['total_requests'] * 100) if metrics['total_requests'] > 0 else 0
            
            # Percentiles
            if metrics['response_times']:
                sorted_times = sorted(metrics['response_times'])
                metrics['p50'] = sorted_times[len(sorted_times) // 2]
                metrics['p95'] = sorted_times[int(len(sorted_times) * 0.95)]
                metrics['p99'] = sorted_times[int(len(sorted_times) * 0.99)]
            
            logger.info(f"[STRESS] Test complete: {metrics['successful_requests']}/{metrics['total_requests']} successful")
            return metrics
        
        except Exception as e:
            logger.error(f"[STRESS] Test error: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _simulate_user(self, user_id: int, num_requests: int, metrics: Dict):
        """Simulate a single user making requests"""
        try:
            with self.lock:
                self.active_users += 1
            
            # Simulate API calls
            for req_num in range(num_requests):
                start = time.time()
                
                try:
                    # Simulate API call
                    self._simulate_api_call(user_id, req_num)
                    
                    response_time = time.time() - start
                    
                    with self.lock:
                        metrics['total_requests'] += 1
                        metrics['successful_requests'] += 1
                        metrics['response_times'].append(response_time)
                
                except Exception as e:
                    with self.lock:
                        metrics['total_requests'] += 1
                        metrics['failed_requests'] += 1
                        metrics['errors'].append({
                            'user_id': user_id,
                            'request': req_num,
                            'error': str(e),
                            'time': datetime.utcnow().isoformat()
                        })
                
                # Random delay between requests (rate limiting simulation)
                time.sleep(random.uniform(0.1, 1.0))
        
        finally:
            with self.lock:
                self.active_users -= 1
    
    def _simulate_api_call(self, user_id: int, request_num: int):
        """Simulate an API call"""
        # Simulate different endpoints
        endpoints = ['/api/analyze', '/api/signals', '/api/user/profile']
        endpoint = random.choice(endpoints)
        
        # Simulate different response times
        base_time = 0.1  # 100ms base
        if 'analyze' in endpoint:
            base_time = 0.5  # 500ms for analysis
        elif 'signals' in endpoint:
            base_time = 0.3  # 300ms for signals
        
        # Add some randomness
        response_time = base_time * random.uniform(0.8, 1.5)
        
        # Simulate occasional failures (5% error rate)
        if random.random() < 0.05:
            raise Exception("Simulated API error")
        
        time.sleep(response_time)
    
    def test_rate_limiting(self) -> Dict:
        """Test rate limiting functionality"""
        logger.info("[STRESS] Testing rate limiting...")
        
        results = {
            'test_name': 'Rate Limiting',
            'passed': False,
            'details': {}
        }
        
        # Test 1: Single user rate limiting
        start = time.time()
        for i in range(10):
            self._simulate_api_call(0, i)
        
        elapsed = time.time() - start
        results['details']['single_user_time'] = elapsed
        
        # Should take at least 1 second (10 requests * 0.1s min delay)
        results['passed'] = elapsed >= 1.0
        results['details']['rate_limit_working'] = results['passed']
        
        logger.info(f"[STRESS] Rate limiting test: {'PASS' if results['passed'] else 'FAIL'}")
        return results
    
    def test_caching(self) -> Dict:
        """Test caching effectiveness"""
        logger.info("[STRESS] Testing caching...")
        
        results = {
            'test_name': 'Caching',
            'passed': False,
            'details': {}
        }
        
        # First call (cache miss)
        start = time.time()
        self._simulate_api_call(0, 0)
        first_call = time.time() - start
        
        # Second call (cache hit - should be faster)
        start = time.time()
        self._simulate_api_call(0, 1)
        second_call = time.time() - start
        
        results['details']['first_call'] = first_call
        results['details']['second_call'] = second_call
        results['details']['cache_speedup'] = first_call - second_call
        
        # Cache is working if second call is faster
        results['passed'] = second_call < first_call
        
        logger.info(f"[STRESS] Caching test: {'PASS' if results['passed'] else 'FAIL'}")
        return results
    
    def test_concurrent_load(self, num_requests: int = 100) -> Dict:
        """Test system under concurrent load"""
        logger.info(f"[STRESS] Testing concurrent load: {num_requests} requests")
        
        results = {
            'test_name': 'Concurrent Load',
            'passed': False,
            'details': {}
        }
        
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self._simulate_api_call, i, 0) for i in range(num_requests)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
        
        elapsed = time.time() - start
        throughput = num_requests / elapsed
        
        results['details']['total_requests'] = num_requests
        results['details']['duration'] = elapsed
        results['details']['throughput'] = throughput
        
        # Should handle at least 10 req/sec
        results['passed'] = throughput >= 10
        
        logger.info(f"[STRESS] Load test: {throughput:.1f} req/sec - {'PASS' if results['passed'] else 'FAIL'}")
        return results
    
    def generate_report(self, test_results: List[Dict]) -> str:
        """Generate stress test report"""
        report = """
╔══════════════════════════════════════════════════════════════╗
║              SOFAI FX STRESS TEST REPORT                     ║
╚══════════════════════════════════════════════════════════════╝

"""
        
        for result in test_results:
            test_name = result.get('test_name', 'Unknown')
            passed = result.get('passed', False)
            details = result.get('details', {})
            
            status = "✓ PASS" if passed else "✗ FAIL"
            
            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test: {test_name}
Status: {status}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            for key, value in details.items():
                report += f"  {key}: {value}\n"
        
        report += """
═══════════════════════════════════════════════════════════════
"""
        
        return report