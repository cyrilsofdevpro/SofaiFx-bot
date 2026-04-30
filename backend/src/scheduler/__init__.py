"""
Scheduler module - handles background auto-analysis jobs
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

logger = logging.getLogger('SofAi-FX')


class AnalysisScheduler:
    """Manages background scheduled analysis tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}  # Track jobs by user_id
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("[OK] Analysis scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⛔ Analysis scheduler stopped")
    
    def add_auto_analysis_job(self, user_id: int, analyze_func, pairs: list, 
                              interval_seconds: int = 3600):
        """
        Add a scheduled auto-analysis job for a user
        
        Args:
            user_id: User ID
            analyze_func: Function to call for analysis (should accept user_id, symbol)
            pairs: List of pairs to analyze
            interval_seconds: How often to run (default 1 hour)
        """
        job_id = f"auto_analysis_user_{user_id}"
        
        # Remove existing job if it exists
        if job_id in self.jobs:
            self.remove_auto_analysis_job(user_id)
        
        # Create wrapper function that will be called by scheduler
        def job_wrapper():
            logger.info(f"🤖 [AUTO-ANALYSIS] Starting scheduled analysis for user {user_id}")
            results = {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'pairs_analyzed': [],
                'signals_generated': 0,
                'errors': []
            }
            
            for symbol in pairs:
                try:
                    logger.info(f"   Analyzing {symbol} for user {user_id}...")
                    result = analyze_func(user_id, symbol)
                    
                    if result.get('success'):
                        results['pairs_analyzed'].append(symbol)
                        if result.get('signal'):
                            results['signals_generated'] += 1
                            logger.info(f"   ✅ {symbol}: {result['signal']['signal']}")
                    else:
                        results['errors'].append(f"{symbol}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    error_msg = f"{symbol}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(f"   ❌ Error analyzing {symbol}: {e}")
            
            logger.info(f"🤖 [AUTO-ANALYSIS] Completed for user {user_id}: "
                       f"{results['signals_generated']} signals, {len(results['errors'])} errors")
            return results
        
        # Add job to scheduler
        try:
            job = self.scheduler.add_job(
                job_wrapper,
                'interval',
                seconds=interval_seconds,
                id=job_id,
                name=f"Auto-analysis for user {user_id}",
                max_instances=1,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                'user_id': user_id,
                'job': job,
                'pairs': pairs,
                'interval': interval_seconds
            }
            
            logger.info(f"✅ [SCHEDULER] Added auto-analysis job for user {user_id} "
                       f"(interval: {interval_seconds}s, pairs: {', '.join(pairs)})")
            return True
            
        except Exception as e:
            logger.error(f"❌ [SCHEDULER] Failed to add job for user {user_id}: {e}")
            return False
    
    def remove_auto_analysis_job(self, user_id: int) -> bool:
        """Remove auto-analysis job for a user"""
        job_id = f"auto_analysis_user_{user_id}"
        
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"✅ [SCHEDULER] Removed auto-analysis job for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ [SCHEDULER] Failed to remove job for user {user_id}: {e}")
            return False
    
    def get_user_jobs(self, user_id: int) -> list:
        """Get all jobs for a user"""
        job_id = f"auto_analysis_user_{user_id}"
        if job_id in self.jobs:
            job_info = self.jobs[job_id]
            job = job_info['job']
            try:
                return [{
                    'user_id': user_id,
                    'pairs': job_info['pairs'],
                    'interval_seconds': job_info['interval'],
                    'next_run': str(job.next_run_time) if (job and hasattr(job, 'next_run_time') and job.next_run_time) else None,
                    'enabled': job.enabled if (job and hasattr(job, 'enabled')) else False
                }]
            except Exception as e:
                logger.error(f"Error serializing job info for user {user_id}: {e}")
                return [{
                    'user_id': user_id,
                    'pairs': job_info['pairs'],
                    'interval_seconds': job_info['interval'],
                    'next_run': None,
                    'enabled': True
                }]
        return []
    
    def pause_user_analysis(self, user_id: int) -> bool:
        """Pause auto-analysis for a user"""
        job_id = f"auto_analysis_user_{user_id}"
        try:
            if job_id in self.jobs:
                self.jobs[job_id]['job'].pause()
                logger.info(f"⏸️ [SCHEDULER] Paused auto-analysis for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to pause job for user {user_id}: {e}")
            return False
    
    def resume_user_analysis(self, user_id: int) -> bool:
        """Resume auto-analysis for a user"""
        job_id = f"auto_analysis_user_{user_id}"
        try:
            if job_id in self.jobs:
                self.jobs[job_id]['job'].resume()
                logger.info(f"▶️ [SCHEDULER] Resumed auto-analysis for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to resume job for user {user_id}: {e}")
            return False


# Singleton instance
scheduler = AnalysisScheduler()
