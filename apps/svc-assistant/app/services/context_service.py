"""
Context Retrieval Service

Retrieves user's LoreGuard environment context including rubrics, artifacts,
sources, jobs, evaluations, and model providers.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Import models from svc-api using container path
# Use importlib to avoid importing main.py
import importlib.util

# Try container path first, then local dev path
possible_paths = [
    Path('/app/svc-api-app'),  # Container path
    Path(__file__).resolve().parent.parent.parent.parent / 'svc-api' / 'app',  # Local dev
]

models_path = None
for path in possible_paths:
    models_dir = path / 'models'
    if models_dir.exists():
        models_path = path
        if str(models_path) not in sys.path:
            sys.path.insert(0, str(models_path))
        break

if models_path:
    # Import Base from assistant's database module first (this sets up db.database.Base)
    from app.core.database import Base as AssistantBase
    
    # Ensure db.database.Base is set (database.py should have done this, but double-check)
    import sys
    if 'db.database' in sys.modules:
        sys.modules['db.database'].Base = AssistantBase
    
    # Import models directly - db.database.Base is already set up
    # Use normal imports now that Base is configured
    from models.rubric import Rubric
    from models.artifact import Artifact, DocumentMetadata
    from models.source import Source
    from models.job import Job
    from models.evaluation import Evaluation
    from models.llm_provider import LLMProvider
    from models.prompt_template import PromptTemplate
    from models.library import LibraryItem
else:
    raise ImportError("Could not find svc-api models directory")

logger = logging.getLogger(__name__)


class ContextRetrievalService:
    """Service for retrieving user's LoreGuard environment context"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_full_context(self, user_id: str, include_details: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive context about user's LoreGuard environment
        
        Args:
            user_id: User identifier
            include_details: Include detailed information (can be large)
            
        Returns:
            Dictionary with all relevant context
        """
        context = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "rubrics": self.get_rubrics_context(include_details),
            "artifacts": self.get_artifacts_context(include_details),
            "sources": self.get_sources_context(include_details),
            "jobs": self.get_jobs_context(),
            "evaluations": self.get_evaluations_context(),
            "llm_providers": self.get_llm_providers_context(),
            "prompt_templates": self.get_prompt_templates_context(),
            "library": self.get_library_context()
        }
        
        return context
    
    def get_rubrics_context(self, include_details: bool = True) -> Dict[str, Any]:
        """Get information about user's rubrics"""
        try:
            # Get active rubric
            active_rubric = self.db.query(Rubric).filter(Rubric.is_active == True).first()
            
            # Get all rubrics
            all_rubrics = self.db.query(Rubric).all()
            
            context = {
                "count": len(all_rubrics),
                "active_rubric": None,
                "all_versions": [r.version for r in all_rubrics]
            }
            
            if active_rubric:
                context["active_rubric"] = {
                    "version": active_rubric.version,
                    "categories": list(active_rubric.categories.keys()) if active_rubric.categories else [],
                    "thresholds": active_rubric.thresholds,
                    "created_at": active_rubric.created_at.isoformat() if active_rubric.created_at else None
                }
                
                if include_details:
                    context["active_rubric"]["full_categories"] = active_rubric.categories
                    context["active_rubric"]["prompts"] = active_rubric.prompts
            
            if include_details:
                context["all_rubrics"] = [
                    {
                        "id": r.id,
                        "version": r.version,
                        "is_active": r.is_active,
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in all_rubrics
                ]
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving rubrics context: {e}")
            return {"count": 0, "error": str(e)}
    
    def get_artifacts_context(self, include_details: bool = True) -> Dict[str, Any]:
        """Get information about artifacts"""
        try:
            total_count = self.db.query(Artifact).count()
            
            # Get recent artifacts
            recent_artifacts = self.db.query(Artifact).order_by(Artifact.created_at.desc()).limit(10).all()
            
            # Get artifacts by label (from evaluations)
            signal_count = self.db.query(Evaluation).filter(Evaluation.label == "Signal").count()
            review_count = self.db.query(Evaluation).filter(Evaluation.label == "Review").count()
            noise_count = self.db.query(Evaluation).filter(Evaluation.label == "Noise").count()
            
            context = {
                "total_count": total_count,
                "signal_count": signal_count,
                "review_count": review_count,
                "noise_count": noise_count,
                "recent_count": len(recent_artifacts)
            }
            
            if include_details:
                context["recent_artifacts"] = [
                    {
                        "id": a.id,
                        "uri": a.uri,
                        "source_id": a.source_id,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                        "metadata": {
                            "title": a.document_metadata.title if a.document_metadata else None,
                            "organization": a.document_metadata.organization if a.document_metadata else None
                        }
                    }
                    for a in recent_artifacts[:5]  # Limit to 5 for context
                ]
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving artifacts context: {e}")
            return {"total_count": 0, "error": str(e)}
    
    def get_sources_context(self, include_details: bool = True) -> Dict[str, Any]:
        """Get information about sources"""
        try:
            all_sources = self.db.query(Source).all()
            active_sources = [s for s in all_sources if s.status == "active"]
            
            context = {
                "total_count": len(all_sources),
                "active_count": len(active_sources)
            }
            
            if include_details:
                context["sources"] = [
                    {
                        "id": s.id,
                        "name": s.name,
                        "type": s.type,
                        "status": s.status,
                        "last_run": s.last_run.isoformat() if s.last_run else None
                    }
                    for s in all_sources
                ]
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving sources context: {e}")
            return {"total_count": 0, "error": str(e)}
    
    def get_jobs_context(self) -> Dict[str, Any]:
        """Get information about recent jobs"""
        try:
            # Get jobs from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_jobs = self.db.query(Job).filter(Job.created_at >= week_ago).all()
            
            running_jobs = [j for j in recent_jobs if j.status == "running"]
            failed_jobs = [j for j in recent_jobs if j.status == "failed"]
            completed_jobs = [j for j in recent_jobs if j.status == "completed"]
            
            context = {
                "total_recent": len(recent_jobs),
                "running": len(running_jobs),
                "failed": len(failed_jobs),
                "completed": len(completed_jobs),
                "recent_jobs": [
                    {
                        "id": j.id,
                        "type": j.type,
                        "status": j.status,
                        "created_at": j.created_at.isoformat() if j.created_at else None
                    }
                    for j in recent_jobs[:10]
                ]
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving jobs context: {e}")
            return {"total_recent": 0, "error": str(e)}
    
    def get_evaluations_context(self) -> Dict[str, Any]:
        """Get recent evaluation statistics"""
        try:
            # Get evaluations from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_evals = self.db.query(Evaluation).filter(Evaluation.created_at >= week_ago).all()
            
            context = {
                "total_recent": len(recent_evals),
                "by_label": {
                    "Signal": len([e for e in recent_evals if e.label == "Signal"]),
                    "Review": len([e for e in recent_evals if e.label == "Review"]),
                    "Noise": len([e for e in recent_evals if e.label == "Noise"])
                }
            }
            
            # Average confidence
            confidences = [float(e.confidence) for e in recent_evals if e.confidence]
            if confidences:
                context["avg_confidence"] = sum(confidences) / len(confidences)
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving evaluations context: {e}")
            return {"total_recent": 0, "error": str(e)}
    
    def get_llm_providers_context(self) -> Dict[str, Any]:
        """Get configured LLM providers"""
        try:
            providers = self.db.query(LLMProvider).all()
            active_providers = [p for p in providers if p.status == "active"]
            default_provider = next((p for p in providers if p.is_default), None)
            
            context = {
                "total_count": len(providers),
                "active_count": len(active_providers),
                "default_provider": {
                    "id": default_provider.id,
                    "name": default_provider.name,
                    "provider": default_provider.provider,
                    "model": default_provider.model
                } if default_provider else None,
                "providers": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "provider": p.provider,
                        "model": p.model,
                        "status": p.status,
                        "is_default": p.is_default
                    }
                    for p in providers
                ]
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving LLM providers context: {e}")
            return {"total_count": 0, "error": str(e)}
    
    def get_prompt_templates_context(self) -> Dict[str, Any]:
        """Get configured prompt templates"""
        try:
            templates = self.db.query(PromptTemplate).filter(PromptTemplate.is_active == True).all()
            
            context = {
                "total_count": len(templates),
                "by_type": {
                    "metadata": len([t for t in templates if t.type == "metadata"]),
                    "evaluation": len([t for t in templates if t.type == "evaluation"]),
                    "clarification": len([t for t in templates if t.type == "clarification"])
                },
                "templates": [
                    {
                        "id": t.id,
                        "reference_id": t.reference_id,
                        "name": t.name,
                        "type": t.type,
                        "version": t.version,
                        "is_default": t.is_default
                    }
                    for t in templates
                ]
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving prompt templates context: {e}")
            return {"total_count": 0, "error": str(e)}
    
    def get_library_context(self) -> Dict[str, Any]:
        """Get library (Signal artifacts) information"""
        try:
            # Get Signal artifacts from evaluations
            signal_evals = self.db.query(Evaluation).filter(Evaluation.label == "Signal").all()
            
            # Get unique artifact IDs
            signal_artifact_ids = list(set([e.artifact_id for e in signal_evals]))
            
            context = {
                "signal_count": len(signal_artifact_ids),
                "recent_signals": []
            }
            
            # Get recent Signal artifacts
            if signal_artifact_ids:
                recent_signals = self.db.query(Artifact).filter(
                    Artifact.id.in_(signal_artifact_ids[:10])
                ).limit(5).all()
                
                context["recent_signals"] = [
                    {
                        "id": a.id,
                        "uri": a.uri,
                        "metadata": {
                            "title": a.document_metadata.title if a.document_metadata else None,
                            "organization": a.document_metadata.organization if a.document_metadata else None
                        }
                    }
                    for a in recent_signals
                ]
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving library context: {e}")
            return {"signal_count": 0, "error": str(e)}
    
    def get_context_summary(self, user_id: str) -> str:
        """
        Get a text summary of user's context for LLM
        
        Returns a formatted string suitable for including in LLM system prompt
        """
        context = self.get_full_context(user_id, include_details=False)
        
        summary_parts = [
            "# User's LoreGuard Environment",
            ""
        ]
        
        # Rubrics
        if context["rubrics"]["count"] > 0:
            summary_parts.append(f"## Rubrics ({context['rubrics']['count']} total)")
            if context["rubrics"]["active_rubric"]:
                active = context["rubrics"]["active_rubric"]
                summary_parts.append(f"- Active: {active['version']}")
                summary_parts.append(f"- Categories: {', '.join(active['categories'])}")
                summary_parts.append(f"- Thresholds: Signal≥{active['thresholds'].get('signal_min')}, Review≥{active['thresholds'].get('review_min')}")
            summary_parts.append("")
        
        # Artifacts
        summary_parts.append(f"## Artifacts ({context['artifacts']['total_count']} total)")
        summary_parts.append(f"- Signal: {context['artifacts']['signal_count']}")
        summary_parts.append(f"- Review: {context['artifacts']['review_count']}")
        summary_parts.append(f"- Noise: {context['artifacts']['noise_count']}")
        summary_parts.append("")
        
        # Sources
        summary_parts.append(f"## Sources ({context['sources']['total_count']} total)")
        summary_parts.append(f"- Active: {context['sources']['active_count']}")
        summary_parts.append("")
        
        # Jobs
        summary_parts.append(f"## Jobs (last 7 days)")
        summary_parts.append(f"- Running: {context['jobs']['running']}")
        summary_parts.append(f"- Failed: {context['jobs']['failed']}")
        summary_parts.append(f"- Completed: {context['jobs']['completed']}")
        summary_parts.append("")
        
        # LLM Providers
        if context["llm_providers"]["default_provider"]:
            default = context["llm_providers"]["default_provider"]
            summary_parts.append(f"## LLM Configuration")
            summary_parts.append(f"- Default Provider: {default['name']} ({default['provider']} - {default['model']})")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def search_artifacts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search artifacts by title, organization, or content
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching artifacts
        """
        try:
            # Simple text search on metadata
            results = self.db.query(Artifact).join(
                DocumentMetadata, Artifact.id == DocumentMetadata.artifact_id, isouter=True
            ).filter(
                DocumentMetadata.title.ilike(f"%{query}%") |
                DocumentMetadata.organization.ilike(f"%{query}%")
            ).limit(limit).all()
            
            return [
                {
                    "id": a.id,
                    "uri": a.uri,
                    "title": a.document_metadata.title if a.document_metadata else None,
                    "organization": a.document_metadata.organization if a.document_metadata else None,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching artifacts: {e}")
            return []
    
    def get_artifact_details(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific artifact"""
        try:
            artifact = self.db.query(Artifact).filter(Artifact.id == artifact_id).first()
            
            if not artifact:
                return None
            
            # Get latest evaluation
            latest_eval = self.db.query(Evaluation).filter(
                Evaluation.artifact_id == artifact_id
            ).order_by(Evaluation.created_at.desc()).first()
            
            details = {
                "id": artifact.id,
                "uri": artifact.uri,
                "source_id": artifact.source_id,
                "mime_type": artifact.mime_type,
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                "metadata": None,
                "evaluation": None
            }
            
            if artifact.document_metadata:
                details["metadata"] = {
                    "title": artifact.document_metadata.title,
                    "authors": artifact.document_metadata.authors,
                    "organization": artifact.document_metadata.organization,
                    "pub_date": artifact.document_metadata.pub_date.isoformat() if artifact.document_metadata.pub_date else None,
                    "topics": artifact.document_metadata.topics,
                    "language": artifact.document_metadata.language
                }
            
            if latest_eval:
                details["evaluation"] = {
                    "label": latest_eval.label,
                    "confidence": float(latest_eval.confidence) if latest_eval.confidence else None,
                    "rubric_version": latest_eval.rubric_version,
                    "created_at": latest_eval.created_at.isoformat() if latest_eval.created_at else None
                }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting artifact details: {e}")
            return None

