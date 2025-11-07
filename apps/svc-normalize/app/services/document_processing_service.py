"""
Document Processing Service

Orchestrates document parsing, metadata extraction, and storage.
Handles the complete normalization workflow for artifacts.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.document_parser import DocumentParserService
from app.services.metadata_extractor import MetadataExtractorService

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing documents from artifacts"""
    
    def __init__(self):
        """Initialize document processing service"""
        self.parser_service = DocumentParserService()
        self.metadata_service = MetadataExtractorService()
        
        # Initialize S3/MinIO client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION
        )
        
        # Setup database connection (for accessing svc-api models)
        self._setup_database_access()
    
    def _setup_database_access(self):
        """Setup database access for svc-api models"""
        # Add svc-api/app to Python path to import models
        # Path: document_processing_service.py -> services -> app -> svc-normalize -> apps (4 levels up to apps dir)
        apps_dir = Path(__file__).resolve().parent.parent.parent.parent
        svc_api_app_path = apps_dir / 'svc-api' / 'app'
        if str(svc_api_app_path) not in sys.path:
            sys.path.insert(0, str(svc_api_app_path))
        
        # Create database engine
        self.engine = create_engine(settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
    
    async def process_artifact(
        self,
        artifact_id: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an artifact: fetch content, parse, extract metadata, store normalized content
        
        Args:
            artifact_id: Artifact ID from database
            processing_options: Optional processing configuration
            
        Returns:
            Dictionary with processing results
            
        Raises:
            ValueError: If artifact not found or invalid
            RuntimeError: If processing fails
        """
        session = self.Session()
        
        try:
            # Import models (available via sys.path modification)
            from models.artifact import Artifact, DocumentMetadata
            
            # Load artifact
            artifact = session.query(Artifact).filter(Artifact.id == artifact_id).first()
            
            if not artifact:
                raise ValueError(f"Artifact {artifact_id} not found")
            
            logger.info(f"Processing artifact {artifact_id} (URI: {artifact.uri})")
            
            # Fetch content from MinIO
            content_hash = artifact.content_hash
            content_key = self._get_content_key(content_hash)
            
            try:
                response = self.s3_client.get_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=content_key
                )
                file_content = response['Body'].read()
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise ValueError(f"Content not found in storage for artifact {artifact_id}")
                raise RuntimeError(f"Failed to fetch content from storage: {e}") from e
            
            # Extract filename from URI
            filename = artifact.uri.split('/')[-1] or f"artifact_{artifact_id}"
            
            # Set processing options
            options = processing_options or {}
            options.setdefault('extract_metadata', True)
            options.setdefault('extract_text', True)
            options.setdefault('extract_tables', True)
            options.setdefault('enable_ocr', True)
            options.setdefault('detect_language', True)
            
            # Parse document
            parse_result = await self.parser_service.parse_document(
                file_content=file_content,
                filename=filename,
                mime_type=artifact.mime_type,
                processing_options=options
            )
            
            text_content = parse_result.get('text_content', '')
            
            if not text_content:
                raise RuntimeError(f"No text content extracted from artifact {artifact_id}")
            
            # Extract metadata
            metadata = await self.metadata_service.extract_metadata(
                text_content=text_content,
                file_metadata=parse_result.get('file_metadata', {}),
                processing_options=options
            )
            
            # Store normalized content to MinIO
            normalized_key = self._get_normalized_key(content_hash)
            
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=normalized_key,
                Body=text_content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'artifact_id': artifact_id,
                    'processed_at': datetime.utcnow().isoformat(),
                    'mime_type': artifact.mime_type or 'unknown'
                }
            )
            
            # Update artifact with normalized reference
            artifact.normalized_ref = normalized_key
            session.commit()
            
            # Store/update metadata
            existing_metadata = session.query(DocumentMetadata).filter(
                DocumentMetadata.artifact_id == artifact_id
            ).first()
            
            if existing_metadata:
                # Update existing metadata
                existing_metadata.title = metadata.title
                existing_metadata.authors = json.dumps(metadata.authors) if metadata.authors else None
                existing_metadata.organization = metadata.organization
                existing_metadata.pub_date = metadata.publication_date
                existing_metadata.topics = json.dumps(metadata.topics) if metadata.topics else None
                existing_metadata.geo_location = metadata.geographic_scope[0] if metadata.geographic_scope else None
                existing_metadata.language = metadata.language.value if metadata.language else None
            else:
                # Create new metadata record
                db_metadata = DocumentMetadata(
                    artifact_id=artifact_id,
                    title=metadata.title,
                    authors=json.dumps(metadata.authors) if metadata.authors else None,
                    organization=metadata.organization,
                    pub_date=metadata.publication_date,
                    topics=json.dumps(metadata.topics) if metadata.topics else None,
                    geo_location=metadata.geographic_scope[0] if metadata.geographic_scope else None,
                    language=metadata.language.value if metadata.language else None
                )
                session.add(db_metadata)
            
            session.commit()
            
            logger.info(
                f"Successfully processed artifact {artifact_id}: "
                f"extracted {len(text_content)} characters, "
                f"normalized_ref={normalized_key}"
            )
            
            # Trigger evaluation automatically after normalization
            self._trigger_evaluation(artifact_id)
            
            return {
                "artifact_id": artifact_id,
                "normalized_ref": normalized_key,
                "text_length": len(text_content),
                "metadata": {
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "organization": metadata.organization,
                    "language": metadata.language.value if metadata.language else None,
                    "page_count": metadata.page_count,
                    "word_count": metadata.word_count
                },
                "processing_summary": {
                    "pages_processed": parse_result.get('page_count', 0),
                    "tables_extracted": len(parse_result.get('tables', [])),
                    "language_detected": parse_result.get('detected_language')
                }
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing artifact {artifact_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def _get_content_key(self, content_hash: str) -> str:
        """Get MinIO key for artifact content"""
        return f"artifacts/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.bin"
    
    def _get_normalized_key(self, content_hash: str) -> str:
        """Get MinIO key for normalized content"""
        return f"normalized/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.txt"
    
    def _trigger_evaluation(self, artifact_id: str):
        """Trigger evaluation service for newly normalized artifact"""
        try:
            import httpx
            api_url = settings.API_SERVICE_URL
            
            if not api_url:
                logger.warning("API_SERVICE_URL not configured, skipping evaluation trigger")
                return
            
            # Make async HTTP call (fire and forget for MVP)
            # In production, use Celery or message queue
            try:
                # Use httpx in sync mode
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        f"{api_url}/api/v1/artifacts/{artifact_id}/evaluate",
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        logger.info(f"Triggered evaluation for artifact {artifact_id}")
                    else:
                        logger.warning(
                            f"Evaluation trigger returned {response.status_code} "
                            f"for artifact {artifact_id}: {response.text}"
                        )
            except httpx.TimeoutException:
                logger.warning(f"Timeout triggering evaluation for artifact {artifact_id}")
            except httpx.RequestError as e:
                logger.warning(f"Failed to trigger evaluation for artifact {artifact_id}: {e}")
                
        except ImportError:
            logger.warning("httpx not available, cannot trigger evaluation")
        except Exception as e:
            # Don't fail the processing if evaluation trigger fails
            logger.warning(f"Error triggering evaluation for artifact {artifact_id}: {e}")

