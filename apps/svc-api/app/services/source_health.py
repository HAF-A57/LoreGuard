"""
Source Health Service

Calculates health metrics for sources based on:
- Last run recency
- Job success rate
- Error frequency
- Artifact freshness
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, String

from models.source import Source
from models.job import Job
from models.artifact import Artifact

logger = logging.getLogger(__name__)


class SourceHealthService:
    """Service for calculating source health metrics"""
    
    # Health thresholds
    HEALTH_EXCELLENT = 0.9  # 90%+
    HEALTH_GOOD = 0.7      # 70-89%
    HEALTH_WARNING = 0.5   # 50-69%
    HEALTH_POOR = 0.0      # <50%
    
    # Time thresholds (in hours)
    RECENT_RUN_HOURS = 24      # Recent if run within 24 hours
    STALE_RUN_HOURS = 168      # Stale if not run in 7 days
    VERY_STALE_RUN_HOURS = 720  # Very stale if not run in 30 days
    
    def __init__(self):
        """Initialize source health service"""
        pass
    
    def calculate_health(
        self,
        source: Source,
        db: Session
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive health metrics for a source.
        
        Args:
            source: Source model instance
            db: Database session
            
        Returns:
            Dictionary with health score, status, and detailed metrics
        """
        
        metrics = {
            'last_run_score': 0.0,
            'success_rate_score': 0.0,
            'error_rate_score': 1.0,  # Start at 1.0, deduct for errors
            'artifact_freshness_score': 0.0,
            'overall_score': 0.0
        }
        
        details = {
            'last_run': source.last_run.isoformat() if source.last_run else None,
            'last_run_age_hours': None,
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'success_rate': 0.0,
            'recent_errors': 0,
            'total_artifacts': 0,
            'recent_artifacts': 0,
            'artifact_freshness_hours': None
        }
        
        # Calculate last run score
        if source.last_run:
            age_hours = (datetime.now(timezone.utc) - source.last_run).total_seconds() / 3600
            details['last_run_age_hours'] = age_hours
            
            if age_hours <= self.RECENT_RUN_HOURS:
                metrics['last_run_score'] = 1.0
            elif age_hours <= self.STALE_RUN_HOURS:
                # Linear decay from 1.0 to 0.5 over 7 days
                metrics['last_run_score'] = 1.0 - ((age_hours - self.RECENT_RUN_HOURS) / 
                                                   (self.STALE_RUN_HOURS - self.RECENT_RUN_HOURS) * 0.5)
            elif age_hours <= self.VERY_STALE_RUN_HOURS:
                # Linear decay from 0.5 to 0.0 over 30 days
                metrics['last_run_score'] = 0.5 - ((age_hours - self.STALE_RUN_HOURS) / 
                                                   (self.VERY_STALE_RUN_HOURS - self.STALE_RUN_HOURS) * 0.5)
            else:
                metrics['last_run_score'] = 0.0
        else:
            # Never run
            metrics['last_run_score'] = 0.0
        
        # Calculate job success rate (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Query jobs for this source - need to filter by JSON payload
        # PostgreSQL JSONB operator: payload->>'source_id'
        jobs_query = db.query(Job).filter(
            and_(
                Job.type == 'ingest',
                Job.created_at >= thirty_days_ago,
                cast(Job.payload['source_id'], String) == str(source.id)
            )
        )
        
        total_jobs = jobs_query.count()
        successful_jobs = jobs_query.filter(Job.status == 'completed').count()
        failed_jobs = jobs_query.filter(Job.status == 'failed').count()
        
        details['total_jobs'] = total_jobs
        details['successful_jobs'] = successful_jobs
        details['failed_jobs'] = failed_jobs
        
        if total_jobs > 0:
            success_rate = successful_jobs / total_jobs
            details['success_rate'] = success_rate
            metrics['success_rate_score'] = success_rate
        else:
            # No jobs yet - neutral score
            metrics['success_rate_score'] = 0.5
        
        # Calculate error rate (recent errors in last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_errors = db.query(Job).filter(
            and_(
                Job.type == 'ingest',
                Job.status == 'failed',
                Job.created_at >= seven_days_ago,
                cast(Job.payload['source_id'], String) == str(source.id)
            )
        ).count()
        
        details['recent_errors'] = recent_errors
        
        # Error rate score: deduct 0.1 per error, minimum 0.0
        metrics['error_rate_score'] = max(0.0, 1.0 - (recent_errors * 0.1))
        
        # Calculate artifact freshness
        artifact_count = db.query(func.count(Artifact.id)).filter(
            Artifact.source_id == source.id
        ).scalar()
        
        details['total_artifacts'] = artifact_count
        
        if artifact_count > 0:
            # Get most recent artifact
            recent_artifact = db.query(Artifact).filter(
                Artifact.source_id == source.id
            ).order_by(Artifact.created_at.desc()).first()
            
            if recent_artifact and recent_artifact.created_at:
                artifact_age_hours = (datetime.now(timezone.utc) - recent_artifact.created_at).total_seconds() / 3600
                details['artifact_freshness_hours'] = artifact_age_hours
                
                # Count artifacts from last 24 hours
                recent_artifacts = db.query(func.count(Artifact.id)).filter(
                    and_(
                        Artifact.source_id == source.id,
                        Artifact.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
                    )
                ).scalar()
                
                details['recent_artifacts'] = recent_artifacts
                
                # Freshness score based on age of most recent artifact
                if artifact_age_hours <= 24:
                    metrics['artifact_freshness_score'] = 1.0
                elif artifact_age_hours <= 168:  # 7 days
                    metrics['artifact_freshness_score'] = 0.7
                elif artifact_age_hours <= 720:  # 30 days
                    metrics['artifact_freshness_score'] = 0.4
                else:
                    metrics['artifact_freshness_score'] = 0.1
            else:
                metrics['artifact_freshness_score'] = 0.0
        else:
            # No artifacts yet
            metrics['artifact_freshness_score'] = 0.3
        
        # Calculate overall health score (weighted average)
        # Weights: last_run (30%), success_rate (30%), error_rate (20%), freshness (20%)
        metrics['overall_score'] = (
            metrics['last_run_score'] * 0.3 +
            metrics['success_rate_score'] * 0.3 +
            metrics['error_rate_score'] * 0.2 +
            metrics['artifact_freshness_score'] * 0.2
        )
        
        # Determine health status
        if metrics['overall_score'] >= self.HEALTH_EXCELLENT:
            status = 'excellent'
        elif metrics['overall_score'] >= self.HEALTH_GOOD:
            status = 'good'
        elif metrics['overall_score'] >= self.HEALTH_WARNING:
            status = 'warning'
        else:
            status = 'poor'
        
        return {
            'source_id': source.id,
            'source_name': source.name,
            'health_score': round(metrics['overall_score'], 2),
            'health_status': status,
            'metrics': {
                'last_run_score': round(metrics['last_run_score'], 2),
                'success_rate_score': round(metrics['success_rate_score'], 2),
                'error_rate_score': round(metrics['error_rate_score'], 2),
                'artifact_freshness_score': round(metrics['artifact_freshness_score'], 2)
            },
            'details': details,
            'calculated_at': datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_health_batch(
        self,
        sources: list[Source],
        db: Session
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate health for multiple sources efficiently.
        
        Args:
            sources: List of Source model instances
            db: Database session
            
        Returns:
            Dictionary mapping source_id to health data
        """
        results = {}
        
        for source in sources:
            try:
                health = self.calculate_health(source, db)
                results[source.id] = health
            except Exception as e:
                logger.error(f"Error calculating health for source {source.id}: {e}")
                results[source.id] = {
                    'source_id': source.id,
                    'health_score': 0.0,
                    'health_status': 'error',
                    'error': str(e)
                }
        
        return results

