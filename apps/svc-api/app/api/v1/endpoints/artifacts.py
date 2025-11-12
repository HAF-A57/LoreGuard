"""
Artifacts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from db.database import get_db, SessionLocal
from models.artifact import Artifact, DocumentMetadata, Clarification
from models.evaluation import Evaluation
from models.rubric import Rubric
from models.library import LibraryItem
from models.job import Job
from models.llm_provider import LLMProvider
from schemas.artifact import ArtifactResponse, ArtifactListResponse, ArtifactListItem
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper function to get MinIO/S3 client
def get_s3_client():
    """Get configured MinIO/S3 client"""
    return boto3.client(
        's3',
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        use_ssl=False
    )

# Helper function to get storage keys
def get_content_key(content_hash: str) -> str:
    """Get MinIO key for artifact raw content"""
    return f"artifacts/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.bin"

def get_normalized_key(content_hash: str) -> str:
    """Get MinIO key for normalized content"""
    return f"normalized/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.txt"

def cleanup_artifact_storage(artifact: Artifact) -> dict:
    """
    Clean up storage files for an artifact
    
    Returns:
        dict with cleanup results: {'raw_deleted': bool, 'normalized_deleted': bool, 'evidence_deleted': bool}
    """
    results = {
        'raw_deleted': False,
        'normalized_deleted': False,
        'evidence_deleted': False
    }
    
    # Safely get artifact properties
    try:
        content_hash = getattr(artifact, 'content_hash', None)
        normalized_ref = getattr(artifact, 'normalized_ref', None)
    except Exception as e:
        logger.error(f"Failed to get artifact properties: {e}", exc_info=True)
        return results
    
    try:
        s3_client = get_s3_client()
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}", exc_info=True)
        return results
    
    # Delete raw content
    if content_hash:
        raw_key = get_content_key(content_hash)
        try:
            s3_client.delete_object(Bucket=settings.MINIO_BUCKET_NAME, Key=raw_key)
            results['raw_deleted'] = True
            logger.info(f"Deleted raw content: {raw_key}")
        except ClientError as e:
            try:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown') if hasattr(e, 'response') and e.response else 'Unknown'
            except:
                error_code = 'Unknown'
            if error_code != 'NoSuchKey':
                logger.warning(f"Failed to delete raw content {raw_key}: {error_code} - {e}")
        except Exception as e:
            logger.warning(f"Unexpected error deleting raw content {raw_key}: {e}")
    
    # Delete normalized content
    if normalized_ref:
        try:
            s3_client.delete_object(Bucket=settings.MINIO_BUCKET_NAME, Key=normalized_ref)
            results['normalized_deleted'] = True
            logger.info(f"Deleted normalized content: {normalized_ref}")
        except ClientError as e:
            try:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown') if hasattr(e, 'response') and e.response else 'Unknown'
            except:
                error_code = 'Unknown'
            if error_code != 'NoSuchKey':
                logger.warning(f"Failed to delete normalized content {normalized_ref}: {error_code} - {e}")
        except Exception as e:
            logger.warning(f"Unexpected error deleting normalized content {normalized_ref}: {e}")
    
    # Delete evidence/clarification files if they exist
    # Use try-except to handle case where clarification relationship isn't loaded
    evidence_ref = None
    try:
        clarification = getattr(artifact, 'clarification', None)
        if clarification:
            evidence_ref = getattr(clarification, 'evidence_ref', None)
    except Exception as e:
        logger.debug(f"Could not access clarification for artifact {getattr(artifact, 'id', 'unknown')}: {e}")
    
    if evidence_ref:
        try:
            s3_client.delete_object(Bucket=settings.MINIO_BUCKET_NAME, Key=evidence_ref)
            results['evidence_deleted'] = True
            logger.info(f"Deleted evidence: {evidence_ref}")
        except ClientError as e:
            try:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown') if hasattr(e, 'response') and e.response else 'Unknown'
            except:
                error_code = 'Unknown'
            if error_code != 'NoSuchKey':
                logger.warning(f"Failed to delete evidence {evidence_ref}: {error_code} - {e}")
        except Exception as e:
            logger.warning(f"Unexpected error deleting evidence {evidence_ref}: {e}")
    
    return results

@router.get("/", response_model=ArtifactListResponse)
async def list_artifacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search in title, URI, or topics"),
    label: Optional[str] = Query(None, description="Filter by evaluation label: Signal, Review, Noise, or 'not_evaluated'"),
    source_id: Optional[uuid.UUID] = Query(None, description="Filter by source ID"),
    include_deleted_sources: bool = Query(True, description="Include artifacts from deleted sources (default: True)"),
    # Date range filters
    created_after: Optional[str] = Query(None, description="Filter artifacts created after this date (YYYY-MM-DD)"),
    created_before: Optional[str] = Query(None, description="Filter artifacts created before this date (YYYY-MM-DD)"),
    pub_date_after: Optional[str] = Query(None, description="Filter by publication date after (YYYY-MM-DD)"),
    pub_date_before: Optional[str] = Query(None, description="Filter by publication date before (YYYY-MM-DD)"),
    # Document type and content filters
    mime_type: Optional[str] = Query(None, description="Filter by MIME type (e.g., 'application/pdf', 'text/html')"),
    has_normalized: Optional[bool] = Query(None, description="Filter by whether artifact has normalized content"),
    # Metadata filters
    organization: Optional[str] = Query(None, description="Filter by organization (partial match)"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g., 'en', 'zh')"),
    topic: Optional[str] = Query(None, description="Filter by topic (searches in topics JSON array)"),
    geo_location: Optional[str] = Query(None, description="Filter by geographic location (partial match)"),
    author: Optional[str] = Query(None, description="Filter by author name (searches in authors JSON array)"),
    # Evaluation filters
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum evaluation confidence score"),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum evaluation confidence score"),
    # Sorting
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at, title, confidence, pub_date"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    """
    List artifacts with comprehensive filtering, search, and pagination.
    By default, includes all artifacts (including from deleted sources).
    Set include_deleted_sources=False to exclude artifacts from deleted sources.
    """
    from models.source import Source
    from datetime import datetime
    import json as json_module
    
    # Start with base query - use distinct to avoid duplicates from joins
    query = db.query(Artifact).distinct()
    
    # Join DocumentMetadata (outer join to include artifacts without metadata)
    query = query.join(DocumentMetadata, isouter=True)
    
    # Exclude artifacts from deleted sources only if explicitly requested
    # Use outerjoin to avoid filtering out artifacts if source doesn't exist
    if not include_deleted_sources:
        query = query.outerjoin(Source, Artifact.source_id == Source.id).filter(
            (Source.status != 'deleted') | (Source.id.is_(None))
        )
    
    # Apply text search filter
    if search:
        query = query.filter(
            (DocumentMetadata.title.ilike(f"%{search}%")) |
            (Artifact.uri.ilike(f"%{search}%")) |
            (DocumentMetadata.topics.ilike(f"%{search}%"))
        )
    
    # Source filter
    if source_id:
        query = query.filter(Artifact.source_id == str(source_id))
    
    # Evaluation label filter (including "not_evaluated")
    if label:
        if label.lower() == 'not_evaluated':
            # Artifacts without any evaluation
            subquery = db.query(Evaluation.artifact_id).subquery()
            query = query.filter(~Artifact.id.in_(subquery))
        else:
            # Artifacts with specific label
            subquery = db.query(Evaluation.artifact_id).filter(
                Evaluation.label == label
            ).subquery()
            query = query.filter(Artifact.id.in_(subquery))
    
    # Date range filters
    if created_after:
        try:
            date_obj = datetime.strptime(created_after, "%Y-%m-%d")
            query = query.filter(Artifact.created_at >= date_obj)
        except ValueError:
            pass  # Invalid date format, ignore
    
    if created_before:
        try:
            date_obj = datetime.strptime(created_before, "%Y-%m-%d")
            # Add one day to include the entire day
            from datetime import timedelta
            date_obj = date_obj + timedelta(days=1)
            query = query.filter(Artifact.created_at < date_obj)
        except ValueError:
            pass
    
    if pub_date_after:
        try:
            date_obj = datetime.strptime(pub_date_after, "%Y-%m-%d")
            query = query.filter(DocumentMetadata.pub_date >= date_obj)
        except ValueError:
            pass
    
    if pub_date_before:
        try:
            date_obj = datetime.strptime(pub_date_before, "%Y-%m-%d")
            from datetime import timedelta
            date_obj = date_obj + timedelta(days=1)
            query = query.filter(DocumentMetadata.pub_date < date_obj)
        except ValueError:
            pass
    
    # Document type filter
    if mime_type:
        query = query.filter(Artifact.mime_type == mime_type)
    
    # Normalized content filter
    if has_normalized is not None:
        if has_normalized:
            query = query.filter(Artifact.normalized_ref.isnot(None))
        else:
            query = query.filter(Artifact.normalized_ref.is_(None))
    
    # Organization filter
    if organization:
        query = query.filter(DocumentMetadata.organization.ilike(f"%{organization}%"))
    
    # Language filter
    if language:
        query = query.filter(DocumentMetadata.language == language)
    
    # Topic filter (searches in JSON array)
    if topic:
        query = query.filter(DocumentMetadata.topics.ilike(f"%{topic}%"))
    
    # Geographic location filter
    if geo_location:
        query = query.filter(DocumentMetadata.geo_location.ilike(f"%{geo_location}%"))
    
    # Author filter (searches in JSON array)
    if author:
        query = query.filter(DocumentMetadata.authors.ilike(f"%{author}%"))
    
    # Confidence range filters (requires join with Evaluation)
    if min_confidence is not None or max_confidence is not None:
        # Get latest evaluation per artifact
        from sqlalchemy import func
        latest_eval_subquery = (
            db.query(
                Evaluation.artifact_id,
                func.max(Evaluation.created_at).label('max_date')
            )
            .group_by(Evaluation.artifact_id)
            .subquery()
        )
        
        latest_eval_query = (
            db.query(Evaluation.artifact_id, Evaluation.confidence)
            .join(
                latest_eval_subquery,
                (Evaluation.artifact_id == latest_eval_subquery.c.artifact_id) &
                (Evaluation.created_at == latest_eval_subquery.c.max_date)
            )
        )
        
        if min_confidence is not None:
            latest_eval_query = latest_eval_query.filter(Evaluation.confidence >= min_confidence)
        if max_confidence is not None:
            latest_eval_query = latest_eval_query.filter(Evaluation.confidence <= max_confidence)
        
        artifact_ids_with_confidence = [str(row[0]) for row in latest_eval_query.all()]
        if artifact_ids_with_confidence:
            query = query.filter(Artifact.id.in_(artifact_ids_with_confidence))
        elif min_confidence is not None:
            # If min_confidence specified but no artifacts match, return empty
            query = query.filter(False)
    
    # Apply sorting
    sort_field = sort_by.lower() if sort_by else "created_at"
    sort_dir = sort_order.lower() if sort_order else "desc"
    
    if sort_field == "title":
        if sort_dir == "asc":
            query = query.order_by(DocumentMetadata.title.asc().nulls_last())
        else:
            query = query.order_by(DocumentMetadata.title.desc().nulls_last())
    elif sort_field == "pub_date":
        if sort_dir == "asc":
            query = query.order_by(DocumentMetadata.pub_date.asc().nulls_last())
        else:
            query = query.order_by(DocumentMetadata.pub_date.desc().nulls_last())
    elif sort_field == "confidence":
        # Sort by latest evaluation confidence
        from sqlalchemy import func
        latest_eval_subquery = (
            db.query(
                Evaluation.artifact_id,
                func.max(Evaluation.created_at).label('max_date')
            )
            .group_by(Evaluation.artifact_id)
            .subquery()
        )
        
        latest_eval_confidence = (
            db.query(Evaluation.artifact_id, Evaluation.confidence)
            .join(
                latest_eval_subquery,
                (Evaluation.artifact_id == latest_eval_subquery.c.artifact_id) &
                (Evaluation.created_at == latest_eval_subquery.c.max_date)
            )
            .subquery()
        )
        
        query = query.outerjoin(
            latest_eval_confidence,
            Artifact.id == latest_eval_confidence.c.artifact_id
        )
        
        if sort_dir == "asc":
            query = query.order_by(latest_eval_confidence.c.confidence.asc().nulls_last())
        else:
            query = query.order_by(latest_eval_confidence.c.confidence.desc().nulls_last())
    else:
        # Default: sort by created_at
        if sort_dir == "asc":
            query = query.order_by(Artifact.created_at.asc())
        else:
            query = query.order_by(Artifact.created_at.desc())
    
    # Get total count (before pagination)
    total = query.count()
    
    # Apply pagination
    artifacts = query.offset(skip).limit(limit).all()
    
    # Convert to response format with flattened metadata
    import json as json_module
    items = []
    for artifact in artifacts:
        # Get latest evaluation
        latest_eval = (
            db.query(Evaluation)
            .filter(Evaluation.artifact_id == artifact.id)
            .order_by(Evaluation.created_at.desc())
            .first()
        )
        
        # Get metadata
        metadata = artifact.document_metadata
        
        item = ArtifactListItem(
            id=uuid.UUID(artifact.id) if isinstance(artifact.id, str) else artifact.id,
            source_id=uuid.UUID(artifact.source_id) if isinstance(artifact.source_id, str) else artifact.source_id,
            uri=artifact.uri,
            mime_type=artifact.mime_type,
            created_at=artifact.created_at,
            title=metadata.title if metadata and metadata.title else None,
            authors=(
                json_module.loads(metadata.authors) if metadata and metadata.authors 
                else None
            ),
            organization=metadata.organization if metadata and metadata.organization else None,
            topics=(
                json_module.loads(metadata.topics) if metadata and metadata.topics 
                else None
            ),
            label=latest_eval.label if latest_eval else None,
            confidence=(
                float(latest_eval.confidence) 
                if latest_eval and latest_eval.confidence 
                else None
            )
        )
        items.append(item)
    
    return ArtifactListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )

# More specific routes must come before the generic {artifact_id} route
@router.get("/{artifact_id}/normalized-content")
async def get_normalized_content(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get normalized content for an artifact
    """
    artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    if not artifact.normalized_ref:
        raise HTTPException(
            status_code=404,
            detail="Artifact has not been normalized yet"
        )
    
    # Initialize MinIO/S3 client
    s3_client = get_s3_client()
    
    try:
        response = s3_client.get_object(
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=artifact.normalized_ref
        )
        content = response['Body'].read().decode('utf-8')
        
        return {
            "artifact_id": str(artifact_id),
            "normalized_ref": artifact.normalized_ref,
            "content": content,
            "content_length": len(content)
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(
                status_code=404,
                detail=f"Normalized content not found in storage: {artifact.normalized_ref}"
            )
        logger.error(f"Failed to fetch normalized content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch normalized content: {str(e)}"
        )

@router.get("/{artifact_id}/evaluation-readiness")
async def check_evaluation_readiness(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Check if an artifact is ready for evaluation
    
    Returns readiness status and reasons if not ready.
    Checks:
    - Artifact exists
    - Artifact has normalized content (normalized_ref exists)
    - Normalized content file exists in storage
    - Active LLM provider is configured
    - Active rubric is available
    """
    artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    readiness = {
        "ready": False,
        "artifact_id": str(artifact_id),
        "checks": {
            "has_normalized_ref": False,
            "normalized_content_exists": False,
            "llm_provider_available": False,
            "rubric_available": False
        },
        "reasons": []
    }
    
    # Check if artifact has normalized_ref
    if not artifact.normalized_ref:
        readiness["reasons"].append("Artifact has not been normalized yet")
        return readiness
    
    readiness["checks"]["has_normalized_ref"] = True
    
    # Check if normalized content exists in storage
    try:
        s3_client = get_s3_client()
        try:
            s3_client.head_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=artifact.normalized_ref
            )
            readiness["checks"]["normalized_content_exists"] = True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown') if hasattr(e, 'response') and e.response else 'Unknown'
            if error_code == 'NoSuchKey':
                readiness["reasons"].append("Normalized content file not found in storage")
            else:
                readiness["reasons"].append(f"Error checking storage: {error_code}")
            return readiness
    except Exception as e:
        logger.error(f"Error checking normalized content: {e}", exc_info=True)
        readiness["reasons"].append(f"Error checking storage: {str(e)}")
        return readiness
    
    # Check if active LLM provider exists
    provider = db.query(LLMProvider).filter(LLMProvider.status == "active").first()
    if not provider:
        readiness["reasons"].append("No active LLM provider configured. Please configure a provider in Settings.")
        return readiness
    
    readiness["checks"]["llm_provider_available"] = True
    
    # Check if active rubric exists
    rubric = db.query(Rubric).filter(Rubric.is_active == True).first()
    if not rubric:
        readiness["reasons"].append("No active rubric found. Please activate a rubric first.")
        return readiness
    
    readiness["checks"]["rubric_available"] = True
    
    # All checks passed
    readiness["ready"] = True
    readiness["rubric_version"] = rubric.version
    readiness["llm_provider_id"] = str(provider.id)
    readiness["llm_provider_name"] = provider.name
    
    return readiness

@router.get("/{artifact_id}/evaluations")
async def get_artifact_evaluations(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get all evaluations for an artifact with full details including rubric info
    """
    import json as json_module
    
    artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    evaluations = db.query(Evaluation).filter(
        Evaluation.artifact_id == str(artifact_id)
    ).order_by(Evaluation.created_at.desc()).all()
    
    # Enrich evaluations with rubric details
    enriched_evaluations = []
    for eval_obj in evaluations:
        rubric = db.query(Rubric).filter(Rubric.version == eval_obj.rubric_version).first()
        
        eval_data = {
            "id": str(eval_obj.id),
            "artifact_id": str(eval_obj.artifact_id),
            "rubric_version": eval_obj.rubric_version,
            "model_id": eval_obj.model_id,
            "scores": eval_obj.scores if isinstance(eval_obj.scores, dict) else {},
            "label": eval_obj.label,
            "confidence": float(eval_obj.confidence) if eval_obj.confidence else 0.0,
            "total_score": eval_obj.total_score,
            "prompt_ref": eval_obj.prompt_ref,
            "created_at": eval_obj.created_at.isoformat() if eval_obj.created_at else None,
            "rubric": {
                "version": rubric.version if rubric else None,
                "categories": rubric.categories if rubric else {},
                "thresholds": rubric.thresholds if rubric else {}
            } if rubric else None
        }
        enriched_evaluations.append(eval_data)
    
    return {
        "artifact_id": str(artifact_id),
        "evaluations": enriched_evaluations
    }

@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific artifact by ID
    """
    import json as json_module
    
    artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Build response manually to handle JSON string deserialization
    response_data = {
        "id": uuid.UUID(artifact.id) if isinstance(artifact.id, str) else artifact.id,
        "source_id": uuid.UUID(artifact.source_id) if isinstance(artifact.source_id, str) else artifact.source_id,
        "uri": artifact.uri,
        "content_hash": artifact.content_hash,
        "mime_type": artifact.mime_type,
        "version": artifact.version,
        "normalized_ref": artifact.normalized_ref,
        "created_at": artifact.created_at
    }
    
    # Add document metadata if exists
    if artifact.document_metadata:
        metadata = artifact.document_metadata
        response_data["document_metadata"] = {
            "id": uuid.UUID(metadata.id) if isinstance(metadata.id, str) else metadata.id,
            "artifact_id": uuid.UUID(metadata.artifact_id) if isinstance(metadata.artifact_id, str) else metadata.artifact_id,
            "title": metadata.title,
            "authors": json_module.loads(metadata.authors) if metadata.authors else [],
            "organization": metadata.organization,
            "pub_date": metadata.pub_date,
            "topics": json_module.loads(metadata.topics) if metadata.topics else [],
            "geo_location": metadata.geo_location,
            "language": metadata.language,
            "created_at": metadata.created_at
        }
    
    return response_data

# Background task function for running evaluation
async def run_evaluation_task(
    job_id: str,
    artifact_id: str,
    rubric_version: str,
    provider_id: Optional[str]
):
    """
    Background task to run artifact evaluation
    
    Args:
        job_id: Job ID for tracking
        artifact_id: Artifact ID to evaluate
        rubric_version: Rubric version to use
        provider_id: Optional LLM provider ID
    """
    db = SessionLocal()
    try:
        from services.llm_evaluation import LLMEvaluationService
        
        # Load job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for evaluation task")
            return
        
        # Update job status to running
        job.add_timeline_entry("running", "Starting evaluation")
        db.commit()
        
        try:
            # Perform evaluation
            evaluation_service = LLMEvaluationService(db=db)
            evaluation = await evaluation_service.evaluate_artifact(
                artifact_id=artifact_id,
                rubric_version=rubric_version,
                provider_id=provider_id,
                db=db
            )
            
            # Update job status to completed
            job.add_timeline_entry("completed", f"Evaluation completed: {evaluation.label}")
            job.payload = {
                **(job.payload or {}),
                "evaluation_id": str(evaluation.id),
                "label": evaluation.label,
                "confidence": float(evaluation.confidence) if evaluation.confidence else 0.0,
                "total_score": evaluation.total_score
            }
            db.commit()
            
            logger.info(f"Evaluation job {job_id} completed successfully for artifact {artifact_id}")
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Evaluation job {job_id} failed (ValueError): {error_msg}")
            job.add_timeline_entry("failed", f"Evaluation failed: {error_msg}")
            job.error = error_msg
            db.commit()
        except RuntimeError as e:
            error_msg = str(e)
            logger.error(f"Evaluation job {job_id} failed (RuntimeError): {error_msg}")
            job.add_timeline_entry("failed", f"Evaluation failed: {error_msg}")
            job.error = error_msg
            db.commit()
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Evaluation job {job_id} failed (Exception): {error_msg}", exc_info=True)
            job.add_timeline_entry("failed", error_msg)
            job.error = error_msg
            db.commit()
            
    except Exception as e:
        logger.error(f"Critical error in evaluation task for job {job_id}: {e}", exc_info=True)
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.add_timeline_entry("failed", f"Critical error: {str(e)}")
                job.error = str(e)
                db.commit()
        except:
            pass
    finally:
        db.close()

@router.post("/{artifact_id}/evaluate")
async def trigger_evaluation(
    artifact_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    rubric_version: Optional[str] = None,
    provider_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger evaluation for an artifact using configured LLM provider
    
    Creates a job and runs evaluation asynchronously.
    Returns immediately with job ID for status tracking.
    """
    artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Check if artifact already has an evaluation
    latest_eval = (
        db.query(Evaluation)
        .filter(Evaluation.artifact_id == str(artifact_id))
        .order_by(Evaluation.created_at.desc())
        .first()
    )
    
    # Check if there's already a running evaluation job for this artifact
    # Query all evaluate jobs and filter in Python (SQLAlchemy JSON querying can be tricky)
    evaluate_jobs = (
        db.query(Job)
        .filter(
            Job.type == "evaluate",
            Job.status.in_(["pending", "running"])
        )
        .all()
    )
    existing_job = None
    for job in evaluate_jobs:
        if job.payload and job.payload.get("artifact_id") == str(artifact_id):
            existing_job = job
            break
    
    if existing_job:
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation already in progress. Job ID: {existing_job.id}"
        )
    
    # Check readiness
    if not artifact.normalized_ref:
        raise HTTPException(
            status_code=400,
            detail="Artifact must be normalized before evaluation. Normalize the artifact first."
        )
    
    # Verify normalized content exists
    try:
        s3_client = get_s3_client()
        s3_client.head_object(
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=artifact.normalized_ref
        )
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown') if hasattr(e, 'response') and e.response else 'Unknown'
        if error_code == 'NoSuchKey':
            raise HTTPException(
                status_code=400,
                detail="Normalized content file not found in storage. Artifact may not have been processed correctly."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error checking normalized content: {error_code}"
        )
    
    # Check for active LLM provider
    llm_provider = None
    if provider_id:
        llm_provider = db.query(LLMProvider).filter(LLMProvider.id == str(provider_id)).first()
        if not llm_provider:
            raise HTTPException(status_code=404, detail=f"LLM provider {provider_id} not found")
        if llm_provider.status != "active":
            raise HTTPException(
                status_code=400,
                detail=f"LLM provider {llm_provider.name} is not active (status: {llm_provider.status})"
            )
    else:
        # Get default or first active provider
        llm_provider = db.query(LLMProvider).filter(LLMProvider.is_default == True, LLMProvider.status == "active").first()
        if not llm_provider:
            llm_provider = db.query(LLMProvider).filter(LLMProvider.status == "active").first()
        if not llm_provider:
            raise HTTPException(
                status_code=400,
                detail="No active LLM provider configured. Please configure a provider in Settings."
            )
    
    # Check for rubric
    rubric = None
    if rubric_version and rubric_version != "latest":
        rubric = db.query(Rubric).filter(Rubric.version == rubric_version).first()
        if not rubric:
            raise HTTPException(status_code=404, detail=f"Rubric version '{rubric_version}' not found")
    else:
        rubric = db.query(Rubric).filter(Rubric.is_active == True).first()
        if not rubric:
            raise HTTPException(
                status_code=400,
                detail="No active rubric found. Please activate a rubric first."
            )
    
    # Create job
    job = Job(
        type="evaluate",
        status="pending",
        payload={
            "artifact_id": str(artifact_id),
            "rubric_version": rubric.version,
            "provider_id": str(llm_provider.id),
            "provider_name": llm_provider.name
        }
    )
    job.add_timeline_entry("pending", f"Evaluation job created for artifact {artifact_id}")
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Add background task
    background_tasks.add_task(
        run_evaluation_task,
        job_id=str(job.id),
        artifact_id=str(artifact_id),
        rubric_version=rubric.version,
        provider_id=str(llm_provider.id) if provider_id else None
    )
    
    return {
        "message": "Evaluation job created",
        "job_id": str(job.id),
        "artifact_id": str(artifact_id),
        "status": "pending",
        "rubric_version": rubric.version,
        "provider_name": llm_provider.name
    }

# Schema for bulk delete request
class BulkDeleteRequest(BaseModel):
    artifact_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100)

# Schema for artifact update
class ArtifactUpdate(BaseModel):
    uri: Optional[str] = None
    mime_type: Optional[str] = None

@router.put("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: uuid.UUID,
    artifact_update: ArtifactUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an artifact
    """
    artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Update fields
    update_data = artifact_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(artifact, field, value)
    
    db.commit()
    db.refresh(artifact)
    
    # Build response
    import json as json_module
    response_data = {
        "id": uuid.UUID(artifact.id) if isinstance(artifact.id, str) else artifact.id,
        "source_id": uuid.UUID(artifact.source_id) if isinstance(artifact.source_id, str) else artifact.source_id,
        "uri": artifact.uri,
        "content_hash": artifact.content_hash,
        "mime_type": artifact.mime_type,
        "version": artifact.version,
        "normalized_ref": artifact.normalized_ref,
        "created_at": artifact.created_at
    }
    
    # Add document metadata if exists
    if artifact.document_metadata:
        metadata = artifact.document_metadata
        response_data["document_metadata"] = {
            "id": uuid.UUID(metadata.id) if isinstance(metadata.id, str) else metadata.id,
            "artifact_id": uuid.UUID(metadata.artifact_id) if isinstance(metadata.artifact_id, str) else metadata.artifact_id,
            "title": metadata.title,
            "authors": json_module.loads(metadata.authors) if metadata.authors else [],
            "organization": metadata.organization,
            "pub_date": metadata.pub_date,
            "topics": json_module.loads(metadata.topics) if metadata.topics else [],
            "geo_location": metadata.geo_location,
            "language": metadata.language,
            "created_at": metadata.created_at
        }
    
    return response_data

@router.delete("/bulk")
async def bulk_delete_artifacts(
    request: BulkDeleteRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Delete multiple artifacts in bulk
    
    Maximum 100 artifacts per request.
    """
    if len(request.artifact_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 artifacts can be deleted at once")
    
    artifact_ids_str = [str(aid) for aid in request.artifact_ids]
    artifacts = db.query(Artifact).filter(Artifact.id.in_(artifact_ids_str)).all()
    
    if not artifacts:
        raise HTTPException(status_code=404, detail="No artifacts found")
    
    deleted_count = 0
    cleanup_results = []
    errors = []
    
    for artifact in artifacts:
        try:
            artifact_id_str = str(artifact.id)
            
            # Clean up storage
            cleanup_result = cleanup_artifact_storage(artifact)
            cleanup_results.append({
                "artifact_id": artifact_id_str,
                "cleanup": cleanup_result
            })
            
            # Delete related records explicitly (database FK constraints don't have CASCADE)
            db.query(Evaluation).filter(Evaluation.artifact_id == artifact_id_str).delete()
            db.query(LibraryItem).filter(LibraryItem.artifact_id == artifact_id_str).delete()
            db.query(Clarification).filter(Clarification.artifact_id == artifact_id_str).delete()
            db.query(DocumentMetadata).filter(DocumentMetadata.artifact_id == artifact_id_str).delete()
            
            # Delete artifact
            db.delete(artifact)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact.id}: {e}", exc_info=True)
            errors.append({
                "artifact_id": str(artifact.id),
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "message": f"Deleted {deleted_count} artifact(s)",
        "deleted_count": deleted_count,
        "requested_count": len(request.artifact_ids),
        "cleanup_results": cleanup_results,
        "errors": errors if errors else None
    }

@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an artifact and all related data
    
    This will:
    - Delete the artifact record (cascades to metadata, evaluations, library items)
    - Delete raw content from MinIO storage
    - Delete normalized content from MinIO storage
    - Delete evidence/clarification files if they exist
    """
    try:
        # Query artifact - try with eager loading first, fallback to regular query
        try:
            artifact = db.query(Artifact).options(
                joinedload(Artifact.clarification)
            ).filter(Artifact.id == str(artifact_id)).first()
        except Exception as e:
            logger.warning(f"Could not load artifact with joinedload, trying regular query: {e}")
            artifact = db.query(Artifact).filter(Artifact.id == str(artifact_id)).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Store artifact ID for logging
        artifact_id_str = str(artifact.id)
        
        # Clean up storage files (wrap in try-except to not fail deletion if storage cleanup fails)
        cleanup_results = {
            'raw_deleted': False,
            'normalized_deleted': False,
            'evidence_deleted': False
        }
        
        try:
            cleanup_results = cleanup_artifact_storage(artifact)
        except Exception as e:
            logger.error(f"Error during storage cleanup for artifact {artifact_id_str}: {e}", exc_info=True)
            # Continue with deletion even if cleanup fails
        
        # Delete related records explicitly (database FK constraints don't have CASCADE)
        # Delete in order: evaluations, library_items, clarifications, document_metadata, then artifact
        try:
            # Delete evaluations
            db.query(Evaluation).filter(Evaluation.artifact_id == artifact_id_str).delete()
            
            # Delete library items
            db.query(LibraryItem).filter(LibraryItem.artifact_id == artifact_id_str).delete()
            
            # Delete clarifications
            db.query(Clarification).filter(Clarification.artifact_id == artifact_id_str).delete()
            
            # Delete document metadata
            db.query(DocumentMetadata).filter(DocumentMetadata.artifact_id == artifact_id_str).delete()
            
            # Finally delete the artifact
            db.delete(artifact)
            db.commit()
        except Exception as e:
            logger.error(f"Error committing artifact deletion {artifact_id_str}: {e}", exc_info=True)
            db.rollback()
            raise
        
        return {
            "message": "Artifact deleted successfully",
            "artifact_id": artifact_id_str,
            "storage_cleanup": cleanup_results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting artifact {artifact_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete artifact: {str(e)}"
        )

