"""
Backtest Scheduler Module
Handles background scheduling of backtesting jobs using APScheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Callable
import json
import os

logger = logging.getLogger('SofAi-FX.Backtesting')


class BacktestScheduler:
    """Manages background backtesting jobs"""
    
    def __init__(self, results_dir: str = 'backtest_results'):
        """Initialize backtesting scheduler
        
        Args:
            results_dir: Directory to store backtest results
        """
        self.scheduler = BackgroundScheduler()
        self.jobs = {}  # Track jobs by job_id
        self.results_dir = results_dir
        
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            logger.info(f"Created backtest results directory: {self.results_dir}")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Backtest scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⛔ Backtest scheduler stopped")
    
    def schedule_backtest(
        self,
        job_id: str,
        backtest_func: Callable,
        pairs: List[str],
        schedule_expression: str = '0 2 * * *',  # Daily at 2 AM
        params: Optional[Dict] = None
    ) -> bool:
        """Schedule a backtest job
        
        Args:
            job_id: Unique job identifier
            backtest_func: Function to run backtest (should accept pairs and params)
            pairs: List of currency pairs to backtest
            schedule_expression: Cron expression for scheduling
            params: Additional parameters for backtest function
        
        Returns:
            True if job was scheduled successfully
        """
        try:
            def job_wrapper():
                logger.info(f"🔄 [BACKTEST] Starting scheduled backtest job: {job_id}")
                results = {
                    'job_id': job_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'pairs': pairs,
                    'status': 'running',
                    'results': {},
                    'errors': []
                }
                
                try:
                    for pair in pairs:
                        try:
                            logger.info(f"   Backtesting {pair}...")
                            
                            # Run backtest with provided parameters
                            result = backtest_func(pair, params or {})
                            
                            if result and 'success' in result:
                                if result['success']:
                                    results['results'][pair] = result
                                    logger.info(f"   ✅ {pair}: Backtest complete")
                                else:
                                    error_msg = result.get('error', 'Unknown error')
                                    results['errors'].append({
                                        'pair': pair,
                                        'error': error_msg
                                    })
                                    logger.error(f"   ❌ {pair}: {error_msg}")
                            else:
                                results['errors'].append({
                                    'pair': pair,
                                    'error': 'Invalid result format'
                                })
                                
                        except Exception as e:
                            error_msg = str(e)
                            results['errors'].append({
                                'pair': pair,
                                'error': error_msg
                            })
                            logger.error(f"   ❌ {pair}: {error_msg}")
                    
                    results['status'] = 'completed'
                    
                except Exception as e:
                    results['status'] = 'failed'
                    results['errors'].append({
                        'job': 'general',
                        'error': str(e)
                    })
                    logger.error(f"❌ [BACKTEST] Job {job_id} failed: {e}")
                
                # Save results to file
                self._save_results(job_id, results)
                
                logger.info(f"📊 [BACKTEST] Job {job_id} completed: "
                           f"{len(results['results'])} pairs, "
                           f"{len(results['errors'])} errors")
                
                return results
            
            # Remove existing job if it exists
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed existing job: {job_id}")
            
            # Parse cron expression and schedule job
            trigger = CronTrigger.from_crontab(schedule_expression)
            job = self.scheduler.add_job(
                job_wrapper,
                trigger=trigger,
                id=job_id,
                name=f"Backtest: {job_id}",
                max_instances=1,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                'pairs': pairs,
                'schedule': schedule_expression,
                'params': params,
                'job': job,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ [SCHEDULER] Scheduled backtest job '{job_id}' "
                       f"({schedule_expression}) for pairs: {', '.join(pairs)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule backtest job '{job_id}': {e}")
            return False
    
    def schedule_quick_backtest(
        self,
        pair: str,
        backtest_func: Callable,
        delay_seconds: int = 5
    ) -> bool:
        """Schedule a quick backtest to run after a delay
        
        Args:
            pair: Currency pair to backtest
            backtest_func: Function to run backtest
            delay_seconds: Delay before running (default 5 seconds)
        
        Returns:
            True if scheduled successfully
        """
        job_id = f"quick_backtest_{pair}_{datetime.utcnow().timestamp()}"
        
        try:
            def quick_job_wrapper():
                logger.info(f"⚡ [QUICK BACKTEST] Starting for {pair}")
                try:
                    result = backtest_func(pair, {})
                    logger.info(f"✅ Quick backtest complete for {pair}")
                    return result
                except Exception as e:
                    logger.error(f"❌ Quick backtest failed for {pair}: {e}")
                    return {'success': False, 'error': str(e)}
            
            job = self.scheduler.add_job(
                quick_job_wrapper,
                'date',
                run_date=datetime.utcnow() + timedelta(seconds=delay_seconds),
                id=job_id,
                name=f"Quick backtest: {pair}"
            )
            
            self.jobs[job_id] = {
                'pair': pair,
                'job': job,
                'type': 'quick'
            }
            
            logger.info(f"✅ Scheduled quick backtest for {pair} in {delay_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule quick backtest for {pair}: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if job was removed successfully
        """
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"✅ Removed backtest job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to remove job {job_id}: {e}")
            return False
    
    def get_job_info(self, job_id: str) -> Optional[Dict]:
        """Get information about a scheduled job
        
        Args:
            job_id: Job identifier
        
        Returns:
            Dictionary with job information or None if not found
        """
        if job_id not in self.jobs:
            return None
        
        job_info = self.jobs[job_id].copy()
        job_obj = job_info.pop('job', None)
        
        if job_obj:
            try:
                job_info['next_run'] = str(job_obj.next_run_time) if job_obj.next_run_time else None
                job_info['enabled'] = job_obj.enabled if hasattr(job_obj, 'enabled') else True
            except:
                pass
        
        return job_info
    
    def get_all_jobs(self) -> List[Dict]:
        """Get information about all scheduled jobs
        
        Returns:
            List of job information dictionaries
        """
        jobs_info = []
        for job_id in self.jobs:
            job_info = self.get_job_info(job_id)
            if job_info:
                jobs_info.append(job_info)
        return jobs_info
    
    def get_results(self, job_id: str) -> Optional[Dict]:
        """Get results from a completed backtest job
        
        Args:
            job_id: Job identifier
        
        Returns:
            Dictionary with backtest results or None if not found
        """
        results_file = os.path.join(self.results_dir, f"{job_id}.json")
        
        if not os.path.exists(results_file):
            return None
        
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load results for {job_id}: {e}")
            return None
    
    def _save_results(self, job_id: str, results: Dict):
        """Save backtest results to file
        
        Args:
            job_id: Job identifier
            results: Results dictionary
        """
        results_file = os.path.join(self.results_dir, f"{job_id}.json")
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"💾 Saved backtest results: {results_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save results for {job_id}: {e}")


# Global instance
backtest_scheduler = BacktestScheduler()
