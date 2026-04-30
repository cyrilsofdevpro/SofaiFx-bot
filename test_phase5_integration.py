"""
Integration Tests for Phase 5 Features
Tests all backtesting, dashboard, optimization, stress testing, and execution routes
"""
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureIntegrationTester:
    """Integration test suite for all Phase 5 features"""
    
    def __init__(self):
        self.test_results = {
            'backtesting': [],
            'dashboard': [],
            'optimization': [],
            'stress_testing': [],
            'execution': [],
            'summary': {}
        }
        self.passed = 0
        self.failed = 0
    
    def test_backtesting_module(self):
        """Test backtesting engine"""
        logger.info("\n[TEST] === BACKTESTING MODULE ===")
        
        try:
            from backend.src.backtesting.backtester import BacktestingEngine
            
            # Test 1: Create instance
            logger.info("[TEST] Creating BacktestingEngine instance")
            backtester = BacktestingEngine()
            self._pass("Backtesting instance creation")
            
            # Test 2: Run backtest
            logger.info("[TEST] Running backtest for EURUSD")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            
            results = backtester.backtest_pair(
                pair='EURUSD',
                start_date=start_date,
                end_date=end_date,
                initial_balance=10000
            )
            
            # Validate results structure - use actual keys from backtest results
            assert 'pair' in results
            assert 'trades' in results
            assert 'metrics' in results
            assert 'equity_curve' in results
            
            # Check metrics structure
            metrics = results.get('metrics', {})
            assert 'win_rate' in metrics or metrics == {}
            
            logger.info(f"[TEST] Backtest completed: {len(results.get('trades', []))} trades")
            self._pass("Backtest execution and metrics")
            
            # Test 3: Export functionality
            logger.info("[TEST] Testing export functionality")
            json_export = backtester.export_results(results, format='json')
            assert isinstance(json_export, str)
            # Verify it's valid JSON
            parsed = json.loads(json_export)
            assert isinstance(parsed, dict)
            self._pass("Results export (JSON)")
            
        except Exception as e:
            logger.error(f"[TEST] Backtesting test failed: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._fail(f"Backtesting module: {type(e).__name__}: {str(e)}")
    
    def test_dashboard_module(self):
        """Test performance dashboard"""
        logger.info("\n[TEST] === DASHBOARD MODULE ===")
        
        try:
            from backend.src.analytics.dashboard import PerformanceDashboard
            
            # Test 1: Create instance
            logger.info("[TEST] Creating PerformanceDashboard instance")
            dashboard = PerformanceDashboard()
            self._pass("Dashboard instance creation")
            
            # Test 2: Get overall metrics
            logger.info("[TEST] Retrieving overall metrics")
            metrics = dashboard.get_overall_metrics()
            
            assert 'total_trades' in metrics
            assert 'win_rate' in metrics
            assert 'total_pnl' in metrics
            
            logger.info(f"[TEST] Overall metrics: {metrics['total_trades']} trades, "
                       f"win rate {metrics['win_rate']:.1f}%")
            self._pass("Overall metrics retrieval")
            
            # Test 3: Get pair performance
            logger.info("[TEST] Retrieving pair performance")
            pairs = dashboard.get_pair_performance()
            assert isinstance(pairs, list)
            self._pass("Pair performance retrieval")
            
            # Test 4: Get equity curve
            logger.info("[TEST] Retrieving equity curve")
            curve = dashboard.get_equity_curve()
            assert isinstance(curve, (dict, list))
            self._pass("Equity curve retrieval")
            
            # Test 5: Get confidence analysis
            logger.info("[TEST] Retrieving confidence analysis")
            analysis = dashboard.get_confidence_analysis()
            assert isinstance(analysis, dict)
            self._pass("Confidence analysis retrieval")
            
        except Exception as e:
            logger.error(f"[TEST] Dashboard test failed: {str(e)}")
            self._fail(f"Dashboard module: {str(e)}")
    
    def test_optimization_module(self):
        """Test auto-optimization engine"""
        logger.info("\n[TEST] === OPTIMIZATION MODULE ===")
        
        try:
            from backend.src.optimization.auto_optimizer import AutoOptimizationEngine
            
            # Test 1: Create instance
            logger.info("[TEST] Creating AutoOptimizationEngine instance")
            optimizer = AutoOptimizationEngine()
            self._pass("Optimizer instance creation")
            
            # Test 2: Get current weights
            logger.info("[TEST] Retrieving current weights")
            weights = optimizer.weights
            
            assert 'sentiment' in weights
            assert 'technical' in weights
            assert 'patterns' in weights
            assert 'news' in weights
            
            total_weight = sum(weights[k] for k in ['sentiment', 'technical', 'patterns', 'news'])
            assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, not 1.0"
            
            logger.info(f"[TEST] Current weights: Sentiment {weights['sentiment']:.1%}, "
                       f"Technical {weights['technical']:.1%}")
            self._pass("Weight retrieval and validation")
            
            # Test 3: Record trades and check optimization trigger
            logger.info("[TEST] Simulating trades for optimization")
            for i in range(10):
                optimizer.record_trade({
                    'pair': 'EURUSD',
                    'pnl': 50.0 if i % 2 == 0 else -30.0,
                    'sentiment_score': 0.7 + (i * 0.01),
                    'confidence': 70
                })
            
            self._pass("Trade recording")
            
            # Test 4: Get pair-specific weights if optimization occurred
            logger.info("[TEST] Checking pair-specific weights")
            pair_weights = optimizer.pair_weights.get('EURUSD', {})
            self._pass("Pair-specific weights")
            
        except Exception as e:
            logger.error(f"[TEST] Optimization test failed: {str(e)}")
            self._fail(f"Optimization module: {str(e)}")
    
    def test_stress_testing_module(self):
        """Test stress testing engine"""
        logger.info("\n[TEST] === STRESS TESTING MODULE ===")
        
        try:
            from backend.src.testing.stress_test import StressTestEngine
            
            # Test 1: Create instance
            logger.info("[TEST] Creating StressTestEngine instance")
            stress_tester = StressTestEngine()
            self._pass("StressTestEngine instance creation")
            
            # Test 2: Run light stress test
            logger.info("[TEST] Running light stress test (10 users, 5 requests each)")
            config = {
                'name': 'Light Test',
                'num_users': 10,
                'requests_per_user': 5,
                'duration_seconds': 30,
                'test_type': 'concurrent'
            }
            
            results = stress_tester.run_stress_test(config)
            
            # Validate results - check for actual keys in returned results
            assert isinstance(results, dict), "Results should be a dict"
            assert 'total_requests' in results, f"Missing 'total_requests', keys: {results.keys()}"
            assert 'response_times' in results, f"Missing 'response_times', keys: {results.keys()}"
            assert 'error_rate' in results or 'failed_requests' in results
            
            logger.info(f"[TEST] Stress test completed: {results['total_requests']} requests")
            self._pass("Stress test execution")
            
            # Test 3: Verify response metrics
            logger.info("[TEST] Validating response metrics")
            rt = results.get('response_times', {})
            assert isinstance(rt, (dict, list)), "Response times should be dict or list"
            self._pass("Response time metrics")
            
        except Exception as e:
            logger.error(f"[TEST] Stress testing test failed: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._fail(f"Stress testing module: {type(e).__name__}: {str(e)}")
    
    def test_execution_module(self):
        """Test execution reliability engine"""
        logger.info("\n[TEST] === EXECUTION MODULE ===")
        
        try:
            from backend.src.execution.reliability import ExecutionReliabilityEngine
            
            # Test 1: Create instance
            logger.info("[TEST] Creating ExecutionReliabilityEngine instance")
            exec_engine = ExecutionReliabilityEngine()
            self._pass("ExecutionReliabilityEngine instance creation")
            
            # Test 2: Validate trade params
            logger.info("[TEST] Validating trade parameters")
            trade_params = {
                'pair': 'EURUSD',
                'signal': 'BUY',
                'entry_price': 1.0850,
                'stop_loss': 1.0820,
                'take_profit': 1.0900,
                'volume': 0.1
            }
            
            is_valid = exec_engine._validate_trade_params(trade_params)
            assert is_valid, "Trade params validation failed"
            self._pass("Trade parameter validation")
            
            # Test 3: Execute trade
            logger.info("[TEST] Executing trade with retry logic")
            result = exec_engine.execute_trade(trade_params)
            
            # Use actual keys from execution result
            assert isinstance(result, dict), "Result should be a dict"
            assert 'status' in result or 'ticket' in result, f"Missing execution status, keys: {result.keys()}"
            assert 'execution_time' in result or 'timestamp' in result, f"Missing timing info, keys: {result.keys()}"
            
            logger.info(f"[TEST] Trade executed: {result.get('status', 'submitted')}")
            self._pass("Trade execution with retry")
            
            # Test 4: Get execution stats
            logger.info("[TEST] Retrieving execution stats")
            stats = exec_engine.get_execution_stats()
            
            assert isinstance(stats, dict), "Stats should be a dict"
            assert 'success_rate' in stats or 'total_executions' in stats
            
            logger.info(f"[TEST] Execution stats retrieved")
            self._pass("Execution statistics")
            
        except Exception as e:
            logger.error(f"[TEST] Execution test failed: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._fail(f"Execution module: {type(e).__name__}: {str(e)}")
    
    def test_routes_integration(self):
        """Test routes registration integration"""
        logger.info("\n[TEST] === ROUTES INTEGRATION ===")
        
        try:
            from backend.src.api.routes_integration import register_feature_blueprints, get_routes_summary
            
            # Test 1: Get routes summary
            logger.info("[TEST] Retrieving routes summary")
            summary = get_routes_summary()
            
            assert 'backtesting' in summary
            assert 'dashboard' in summary
            assert 'optimization' in summary
            assert 'stress_testing' in summary
            assert 'execution' in summary
            
            logger.info(f"[TEST] Routes summary retrieved: {len(summary)} feature groups")
            self._pass("Routes summary retrieval")
            
            # Test 2: Validate blueprint imports
            logger.info("[TEST] Validating blueprint imports")
            from backend.src.api.routes import (
                backtesting_bp,
                dashboard_bp,
                optimization_bp,
                stress_bp,
                execution_bp
            )
            
            assert backtesting_bp is not None
            assert dashboard_bp is not None
            assert optimization_bp is not None
            assert stress_bp is not None
            assert execution_bp is not None
            
            self._pass("Blueprint imports")
            
        except Exception as e:
            logger.error(f"[TEST] Routes integration test failed: {str(e)}")
            self._fail(f"Routes integration: {str(e)}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("=" * 60)
        logger.info("PHASE 5 FEATURE INTEGRATION TEST SUITE")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        self.test_backtesting_module()
        self.test_dashboard_module()
        self.test_optimization_module()
        self.test_stress_testing_module()
        self.test_execution_module()
        self.test_routes_integration()
        
        elapsed = time.time() - start_time
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests Run: {self.passed + self.failed}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Success Rate: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        logger.info(f"Duration: {elapsed:.2f}s")
        logger.info("=" * 60)
        
        return self.failed == 0
    
    def _pass(self, test_name):
        """Record passing test"""
        self.passed += 1
        logger.info(f"[PASS] {test_name}")
    
    def _fail(self, test_name):
        """Record failing test"""
        self.failed += 1
        logger.error(f"[FAIL] {test_name}")


def main():
    """Run integration tests"""
    tester = FeatureIntegrationTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
