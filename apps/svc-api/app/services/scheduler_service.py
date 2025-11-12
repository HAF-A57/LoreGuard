"""
Source Scheduler Service

Manages scheduled crawls for sources using cron expressions.
Checks schedules periodically and triggers crawls when due.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    logging.warning("croniter not available - scheduling will be disabled")

from db.database import SessionLocal
from models.source import Source
from services.crawl_service_subprocess import CrawlServiceSubprocess

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled source crawls"""
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize scheduler service
        
        Args:
            check_interval_seconds: How often to check schedules (default: 60s = 1 minute)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self.crawl_service = None
        
        if not CRONITER_AVAILABLE:
            logger.warning("croniter not available - scheduler will not function")
    
    def _get_crawl_service(self) -> Optional[CrawlServiceSubprocess]:
        """Get or create crawl service instance"""
        if not self.crawl_service:
            try:
                self.crawl_service = CrawlServiceSubprocess()
            except Exception as e:
                logger.error(f"Failed to initialize crawl service: {e}")
                return None
        return self.crawl_service
    
    def validate_cron_expression(self, cron_expr: str) -> bool:
        """
        Validate a cron expression
        
        Args:
            cron_expr: Cron expression string (e.g., "0 * * * *")
            
        Returns:
            True if valid, False otherwise
        """
        if not CRONITER_AVAILABLE:
            return False
        
        if not cron_expr or not cron_expr.strip():
            return False
        
        try:
            # Try to create a croniter instance - will raise if invalid
            croniter(cron_expr)
            return True
        except Exception:
            return False
    
    def get_next_run_time(self, cron_expr: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate next run time for a cron expression
        
        Args:
            cron_expr: Cron expression string
            base_time: Base time to calculate from (default: now)
            
        Returns:
            Next run time or None if invalid
        """
        if not CRONITER_AVAILABLE or not self.validate_cron_expression(cron_expr):
            return None
        
        if base_time is None:
            base_time = datetime.now(timezone.utc)
        
        try:
            cron = croniter(cron_expr, base_time)
            next_run = cron.get_next(datetime)
            return next_run
        except Exception as e:
            logger.error(f"Error calculating next run time for '{cron_expr}': {e}")
            return None
    
    def is_due(self, cron_expr: str, last_run: Optional[datetime] = None) -> bool:
        """
        Check if a schedule is due to run
        
        Args:
            cron_expr: Cron expression string
            last_run: Last run time (if None, assumes never run)
            
        Returns:
            True if schedule is due, False otherwise
        """
        if not CRONITER_AVAILABLE or not self.validate_cron_expression(cron_expr):
            return False
        
        now = datetime.now(timezone.utc)
        
        # If never run, check if schedule would have triggered before now
        if last_run is None:
            # Get the most recent time this schedule would have triggered
            try:
                cron = croniter(cron_expr, now)
                # Get previous occurrence
                prev_run = cron.get_prev(datetime)
                # If previous occurrence is recent (within check interval), it's due
                return (now - prev_run).total_seconds() <= self.check_interval * 2
            except Exception:
                return False
        
        # Calculate next run time from last run
        next_run = self.get_next_run_time(cron_expr, last_run)
        
        if next_run is None:
            return False
        
        # Check if next run time has passed (with small buffer for timing)
        return next_run <= now + timedelta(seconds=self.check_interval)
    
    async def check_and_trigger_schedules(self):
        """Check all active sources and trigger crawls for due schedules"""
        if not CRONITER_AVAILABLE:
            return
        
        db = SessionLocal()
        try:
            # Get all active sources with schedules
            sources = db.query(Source).filter(
                Source.status == 'active',
                Source.schedule.isnot(None),
                Source.schedule != ''
            ).all()
            
            logger.debug(f"Checking {len(sources)} scheduled sources")
            
            crawl_service = self._get_crawl_service()
            if not crawl_service:
                logger.warning("Crawl service not available, skipping schedule check")
                return
            
            triggered_count = 0
            
            for source in sources:
                try:
                    if self.is_due(source.schedule, source.last_run):
                        logger.info(f"Schedule due for source {source.id} ({source.name})")
                        
                        # Trigger crawl
                        try:
                            job = crawl_service.trigger_crawl(source=source, db=db)
                            
                            # Update source last_run timestamp
                            source.last_run = datetime.now(timezone.utc)
                            db.commit()
                            
                            logger.info(f"Triggered crawl for source {source.id}, job {job.id}")
                            triggered_count += 1
                        except Exception as e:
                            logger.error(f"Failed to trigger crawl for source {source.id}: {e}")
                            # Update source status to error if multiple failures
                            # (For now, just log the error)
                            
                except Exception as e:
                    logger.error(f"Error checking schedule for source {source.id}: {e}")
                    continue
            
            if triggered_count > 0:
                logger.info(f"Triggered {triggered_count} scheduled crawls")
                
        except Exception as e:
            logger.error(f"Error in schedule check: {e}", exc_info=True)
        finally:
            db.close()
    
    async def start_scheduler(self):
        """Start the scheduler background task"""
        if not CRONITER_AVAILABLE:
            logger.warning("Scheduler not started - croniter not available")
            return
        
        self.running = True
        logger.info(f"Starting source scheduler (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.check_and_trigger_schedules()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Stopping source scheduler")

