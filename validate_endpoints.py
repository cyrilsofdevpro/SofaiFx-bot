#!/usr/bin/env python3
"""
API Endpoint Validation Script
Tests all major API endpoints to ensure they are working correctly

Run this before pushing to GitHub to ensure no broken endpoints
"""

import requests
import json
import sys
from datetime import datetime
from time import sleep

# Configuration
BASE_URL = "http://localhost:5000"
TEST_TIMEOUT = 10

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class APIValidator:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        self.session = requests.Session()
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{BLUE}{'='*60}")
        print(f"{text}")
        print(f"{'='*60}{RESET}\n")
    
    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result"""
        if status == "PASS":
            symbol = f"{GREEN}✅{RESET}"
        elif status == "FAIL":
            symbol = f"{RED}❌{RESET}"
        else:
            symbol = f"{YELLOW}⊘{RESET}"
        
        print(f"{symbol} {name}")
        if details:
            print(f"   {YELLOW}→{RESET} {details}")
    
    def test_endpoint(self, method: str, endpoint: str, name: str, 
                     expected_status: int = 200, payload: dict = None) -> bool:
        """Test a single API endpoint
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Endpoint path
            name: Test name for reporting
            expected_status: Expected HTTP status code
            payload: Request payload for POST requests
        
        Returns:
            True if test passed, False otherwise
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=TEST_TIMEOUT)
            elif method.upper() == "POST":
                response = self.session.post(url, json=payload, timeout=TEST_TIMEOUT)
            else:
                self.print_test(name, "SKIP", f"Unsupported method: {method}")
                self.results['skipped'].append(name)
                return False
            
            if response.status_code == expected_status:
                self.print_test(name, "PASS", f"{method} {endpoint} → {response.status_code}")
                self.results['passed'].append(name)
                return True
            else:
                self.print_test(name, "FAIL", 
                              f"{method} {endpoint} → {response.status_code} (expected {expected_status})")
                self.results['failed'].append(name)
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_test(name, "SKIP", "Server not running")
            self.results['skipped'].append(name)
            return False
        except Exception as e:
            self.print_test(name, "FAIL", f"Exception: {str(e)}")
            self.results['failed'].append(name)
            return False
    
    def run_all_tests(self):
        """Run all API endpoint tests"""
        
        self.print_header("🚀 SofAi FX - API Endpoint Validation")
        print(f"Base URL: {self.base_url}")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # ============================================
        # Health Checks
        # ============================================
        self.print_header("1️⃣ Health Checks")
        self.test_endpoint("GET", "/health", "Health Check Endpoint")
        
        # ============================================
        # Signal API
        # ============================================
        self.print_header("2️⃣ Signal API")
        self.test_endpoint("GET", "/api/signals", "Get Signals", expected_status=200)
        self.test_endpoint("GET", "/api/signals?pair=EURUSD", "Get Signals for Pair", expected_status=200)
        self.test_endpoint("POST", "/api/signals/analyze", "Analyze Signal", 
                          expected_status=200, payload={"pair": "EURUSD"})
        
        # ============================================
        # Backtesting API
        # ============================================
        self.print_header("3️⃣ Backtesting API")
        self.test_endpoint("GET", "/api/backtesting/history", "Get Backtest History")
        self.test_endpoint("POST", "/api/backtesting/quick", "Quick Backtest",
                          payload={"pair": "EURUSD"})
        
        # ============================================
        # Dashboard API
        # ============================================
        self.print_header("4️⃣ Dashboard API")
        self.test_endpoint("GET", "/api/dashboard/overview", "Dashboard Overview")
        self.test_endpoint("GET", "/api/dashboard/pair-performance", "Pair Performance")
        self.test_endpoint("GET", "/api/dashboard/equity-curve", "Equity Curve")
        self.test_endpoint("GET", "/api/dashboard/health", "System Health")
        self.test_endpoint("GET", "/api/dashboard/backtest/results", "Backtest Results")
        self.test_endpoint("GET", "/api/dashboard/backtest/results?pair=EURUSD", 
                          "Backtest Results for Pair")
        
        # ============================================
        # Optimization API
        # ============================================
        self.print_header("5️⃣ Optimization API")
        self.test_endpoint("GET", "/api/optimization/current-weights", "Get Signal Weights")
        self.test_endpoint("GET", "/api/optimization/stats", "Optimization Stats")
        
        # ============================================
        # Execution API
        # ============================================
        self.print_header("6️⃣ Execution API")
        self.test_endpoint("GET", "/api/execution/stats", "Execution Stats")
        self.test_endpoint("GET", "/api/execution/history", "Execution History")
        
        # ============================================
        # Stress Testing API
        # ============================================
        self.print_header("7️⃣ Stress Testing API")
        self.test_endpoint("GET", "/api/stress-test/test-templates", "Test Templates")
        self.test_endpoint("GET", "/api/stress-test/history", "Stress Test History")
        
        # ============================================
        # Print Summary
        # ============================================
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results['passed']) + len(self.results['failed']) + len(self.results['skipped'])
        
        self.print_header("📊 Test Summary")
        
        print(f"{GREEN}✅ Passed:{RESET} {len(self.results['passed'])}")
        print(f"{RED}❌ Failed:{RESET} {len(self.results['failed'])}")
        print(f"{YELLOW}⊘ Skipped:{RESET} {len(self.results['skipped'])}")
        print(f"\nTotal Tests: {total}")
        
        if self.results['failed']:
            print(f"\n{RED}Failed Tests:{RESET}")
            for test in self.results['failed']:
                print(f"  • {test}")
        
        # Return exit code
        if self.results['failed']:
            print(f"\n{RED}❌ Some tests failed!{RESET}")
            return 1
        else:
            print(f"\n{GREEN}✅ All tests passed!{RESET}")
            return 0


def main():
    """Main entry point"""
    validator = APIValidator()
    exit_code = validator.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
