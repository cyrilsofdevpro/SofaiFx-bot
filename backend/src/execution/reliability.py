"""
Execution Reliability Engine - Ensure trades execute safely and consistently
- Retry logic for failed trades
- Timeout handling
- Slippage check
- Trade confirmation from MT5
- Comprehensive logging

Author: SofAi FX Bot - Execution Division
Version: 1.0.0
"""

import time
import threading
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
from src.utils.logger import logger

class ExecutionStatus(Enum):
    """Trade execution status"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FILLED = "filled"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class ExecutionReliabilityEngine:
    """Ensures reliable trade execution with retry logic and error handling"""
    
    def __init__(self):
        """Initialize execution engine"""
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.timeout = 30  # seconds
        self.slippage_tolerance = 0.002  # 0.2% slippage tolerance
        self.active_trades = {}
        self.execution_history = []
        logger.info("[EXEC] Execution Reliability Engine initialized")
    
    def execute_trade(self, trade_params: Dict) -> Dict:
        """
        Execute a trade with retry logic and error handling
        
        Args:
            trade_params: {
                'pair': str,
                'signal': str (BUY/SELL),
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'volume': float,
                'user_id': int,
            }
        
        Returns:
            dict: Execution result with status and details
        """
        try:
            logger.info(f"[EXEC] Executing trade: {trade_params['pair']} {trade_params['signal']}")
            
            # Validate trade parameters
            validation = self._validate_trade_params(trade_params)
            if not validation['valid']:
                return self._failed_result(validation['error'])
            
            # Attempt execution with retries
            for attempt in range(self.max_retries + 1):
                result = self._attempt_execution(trade_params, attempt)
                
                if result['status'] in [ExecutionStatus.CONFIRMED.value, ExecutionStatus.FILLED.value]:
                    logger.info(f"[EXEC] Trade executed successfully: {trade_params['pair']}")
                    return result
                
                if result['status'] == ExecutionStatus.TIMEOUT.value:
                    logger.warning(f"[EXEC] Attempt {attempt + 1} timed out, retrying...")
                    time.sleep(self.retry_delay)
                    continue
                
                if result['status'] == ExecutionStatus.FAILED.value:
                    if attempt < self.max_retries:
                        logger.warning(f"[EXEC] Attempt {attempt + 1} failed, retrying...")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"[EXEC] All retry attempts exhausted")
                        return result
            
            # All retries exhausted
            return self._failed_result("Max retries exceeded")
        
        except Exception as e:
            logger.error(f"[EXEC] Execution error: {e}", exc_info=True)
            return self._failed_result(str(e))
    
    def _attempt_execution(self, trade_params: Dict, attempt: int) -> Dict:
        """Attempt to execute a single trade"""
        try:
            # Step 1: Submit trade to MT5
            submission = self._submit_to_mt5(trade_params)
            
            if not submission['success']:
                return {
                    'status': ExecutionStatus.FAILED.value,
                    'error': submission.get('error', 'Submission failed'),
                    'attempt': attempt + 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Step 2: Wait for confirmation
            confirmation = self._wait_for_confirmation(submission['ticket'])
            
            if confirmation['status'] == 'timeout':
                return {
                    'status': ExecutionStatus.TIMEOUT.value,
                    'ticket': submission['ticket'],
                    'attempt': attempt + 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Step 3: Verify slippage
            slippage_check = self._check_slippage(trade_params, confirmation)
            
            if not slippage_check['acceptable']:
                logger.warning(f"[EXEC] Slippage too high: {slippage_check['slippage']:.2%}")
                # Could cancel here or accept with warning
            
            # Step 4: Record execution
            execution_record = {
                'trade_id': submission['ticket'],
                'pair': trade_params['pair'],
                'signal': trade_params['signal'],
                'entry_price': confirmation.get('fill_price', trade_params['entry_price']),
                'status': confirmation['status'],
                'slippage': slippage_check.get('slippage', 0),
                'attempt': attempt + 1,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.execution_history.append(execution_record)
            
            return {
                'status': ExecutionStatus.FILLED.value if confirmation['status'] == 'filled' else ExecutionStatus.CONFIRMED.value,
                'ticket': submission['ticket'],
                'fill_price': confirmation.get('fill_price'),
                'execution_time': confirmation.get('execution_time', 0),
                'slippage': slippage_check.get('slippage', 0),
                'attempt': attempt + 1,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"[EXEC] Execution attempt error: {e}")
            return {
                'status': ExecutionStatus.FAILED.value,
                'error': str(e),
                'attempt': attempt + 1,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _submit_to_mt5(self, trade_params: Dict) -> Dict:
        """Submit trade to MT5 (simulated)"""
        # In production, this would call actual MT5 API
        # Simulating for now
        
        time.sleep(0.1)  # Simulate API call time
        
        # Simulate success (90% success rate)
        import random
        if random.random() < 0.9:
            return {
                'success': True,
                'ticket': f"TKT{int(time.time())}{random.randint(1000, 9999)}"
            }
        else:
            return {
                'success': False,
                'error': 'MT5 connection error'
            }
    
    def _wait_for_confirmation(self, ticket: str, timeout: int = None) -> Dict:
        """Wait for MT5 confirmation"""
        timeout = timeout or self.timeout
        
        # Simulate waiting for confirmation
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # In production, query MT5 for order status
            time.sleep(0.5)
            
            # Simulate confirmation (95% chance within timeout)
            import random
            if random.random() < 0.95:
                return {
                    'status': 'filled',
                    'fill_price': 1.0850 + random.uniform(-0.001, 0.001),
                    'execution_time': time.time() - start_time
                }
        
        return {'status': 'timeout'}
    
    def _check_slippage(self, trade_params: Dict, confirmation: Dict) -> Dict:
        """Check if slippage is within acceptable range"""
        try:
            entry_price = trade_params['entry_price']
            fill_price = confirmation.get('fill_price', entry_price)
            
            slippage = abs(fill_price - entry_price) / entry_price
            
            return {
                'slippage': slippage,
                'acceptable': slippage <= self.slippage_tolerance,
                'max_acceptable': self.slippage_tolerance
            }
        
        except Exception as e:
            logger.warning(f"[EXEC] Slippage check error: {e}")
            return {'slippage': 0, 'acceptable': True}
    
    def _validate_trade_params(self, trade_params: Dict) -> Dict:
        """Validate trade parameters before execution"""
        required_fields = ['pair', 'signal', 'entry_price', 'stop_loss', 'take_profit', 'volume']
        
        for field in required_fields:
            if field not in trade_params:
                return {'valid': False, 'error': f'Missing field: {field}'}
        
        # Validate signal
        if trade_params['signal'] not in ['BUY', 'SELL']:
            return {'valid': False, 'error': 'Invalid signal type'}
        
        # Validate prices
        if trade_params['entry_price'] <= 0 or trade_params['stop_loss'] <= 0 or trade_params['take_profit'] <= 0:
            return {'valid': False, 'error': 'Invalid price values'}
        
        # Validate volume
        if trade_params['volume'] <= 0 or trade_params['volume'] > 100:
            return {'valid': False, 'error': 'Invalid volume'}
        
        return {'valid': True}
    
    def _failed_result(self, error: str) -> Dict:
        """Create failed execution result"""
        return {
            'status': ExecutionStatus.FAILED.value,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0,
                'avg_slippage': 0,
                'avg_execution_time': 0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e['status'] in ['filled', 'confirmed'])
        total_slippage = sum(e.get('slippage', 0) for e in self.execution_history)
        total_time = sum(e.get('execution_time', 0) for e in self.execution_history)
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
            'avg_slippage': round((total_slippage / total * 100), 4) if total > 0 else 0,
            'avg_execution_time': round(total_time / total, 3) if total > 0 else 0,
            'failed_executions': total - successful
        }
    
    def cancel_trade(self, ticket: str) -> Dict:
        """Cancel a pending trade"""
        try:
            logger.info(f"[EXEC] Cancelling trade: {ticket}")
            
            # In production, call MT5 to cancel order
            # Simulating for now
            
            return {
                'success': True,
                'ticket': ticket,
                'cancelled_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"[EXEC] Cancel error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_active_trades(self) -> List[Dict]:
        """Get all active trades"""
        return list(self.active_trades.values())
    
    def close(self):
        """Cleanup resources"""
        logger.info("[EXEC] Execution engine shutting down")
        self.active_trades.clear()