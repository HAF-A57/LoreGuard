"""
LoreGuard Ingestion Service - Scrapy Pipelines

Pipelines for processing, validating, and storing scraped content.
"""

import hashlib
import json
import logging
import mimetypes
import os
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
import langdetect

from app.items import ArtifactItem, DocumentMetadataItem, CrawlJobItem


logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Pipeline to validate scraped items before processing.
    """
    
    def __init__(self, min_content_length: int = 100):
        self.min_content_length = min_content_length
        self.processed_count = 0
        self.dropped_count = 0
    
    @classmethod
    def from_crawler(cls, crawler):
        min_length = crawler.settings.getint('MIN_CONTENT_LENGTH', 100)
        return cls(min_length)
    
    def process_item(self, item, spider):
        """Validate item before further processing."""
        
        if isinstance(item, ArtifactItem):
            return self._validate_artifact(item, spider)
        elif isinstance(item, DocumentMetadataItem):
            return self._validate_metadata(item, spider)
        else:
            return item
    
    def _validate_artifact(self, item: ArtifactItem, spider) -> ArtifactItem:
        """Validate artifact item."""
        
        # Check required fields
        if not item.get('uri'):
            raise DropItem(f"Missing URI in artifact: {item}")
        
        if not item.get('raw_content') and not item.get('text_content'):
            raise DropItem(f"No content in artifact: {item['uri']}")
        
        # Check content length
        content = item.get('text_content', '') or item.get('raw_content', b'')
        content_length = len(content)
        
        if content_length < self.min_content_length:
            raise DropItem(f"Content too short ({content_length} chars): {item['uri']}")
        
        # Validate URI format
        try:
            parsed = urlparse(item['uri'])
            if not parsed.scheme or not parsed.netloc:
                raise DropItem(f"Invalid URI format: {item['uri']}")
        except Exception as e:
            raise DropItem(f"URI parsing error: {item['uri']} - {e}")
        
        self.processed_count += 1
        logger.debug(f"Validated artifact: {item['uri']}")
        
        return item
    
    def _validate_metadata(self, item: DocumentMetadataItem, spider) -> DocumentMetadataItem:
        """Validate metadata item."""
        
        if not item.get('artifact_uri'):
            raise DropItem(f"Missing artifact_uri in metadata: {item}")
        
        # At least one metadata field should be present
        metadata_fields = ['title', 'authors', 'organization', 'publication_date', 'topics']
        if not any(item.get(field) for field in metadata_fields):
            raise DropItem(f"No meaningful metadata extracted: {item['artifact_uri']}")
        
        return item
    
    def close_spider(self, spider):
        """Log validation statistics."""
        logger.info(f"Validation complete - Processed: {self.processed_count}, Dropped: {self.dropped_count}")


class DeduplicationPipeline:
    """
    Pipeline to detect and handle duplicate content.
    """
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.duplicate_count = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        redis_url = crawler.settings.get('REDIS_URL')
        if not redis_url:
            raise ValueError("REDIS_URL not configured")
        
        return cls(redis_url)
    
    def process_item(self, item, spider):
        """Check for duplicate content."""
        
        if isinstance(item, ArtifactItem):
            return self._check_duplicate_artifact(item, spider)
        
        return item
    
    def _check_duplicate_artifact(self, item: ArtifactItem, spider) -> ArtifactItem:
        """Check if artifact content is duplicate."""
        
        # Generate content hash if not present
        if not item.get('content_hash'):
            content = item.get('raw_content', b'') or item.get('text_content', '').encode('utf-8')
            content_hash = hashlib.sha256(content).hexdigest()
            item['content_hash'] = content_hash
        
        # Check Redis for existing hash
        redis_key = f"content_hash:{item['content_hash']}"
        
        if self.redis_client.exists(redis_key):
            existing_uri = self.redis_client.get(redis_key).decode('utf-8')
            self.duplicate_count += 1
            logger.debug(f"Duplicate content detected: {item['uri']} (original: {existing_uri})")
            raise DropItem(f"Duplicate content: {item['uri']}")
        
        # Store hash with URI (expire after 30 days)
        self.redis_client.setex(redis_key, 2592000, item['uri'])
        
        return item
    
    def close_spider(self, spider):
        """Log deduplication statistics."""
        logger.info(f"Deduplication complete - Duplicates found: {self.duplicate_count}")


class ContentHashPipeline:
    """
    Pipeline to generate content hashes for artifacts.
    """
    
    def process_item(self, item, spider):
        """Generate content hash for artifacts."""
        
        if isinstance(item, ArtifactItem) and not item.get('content_hash'):
            # Get content as bytes for hashing
            content = item.get('raw_content')
            if content and isinstance(content, bytes):
                # Already bytes
                pass
            elif item.get('text_content'):
                # Convert text to bytes
                content = item.get('text_content', '').encode('utf-8')
            else:
                # Fallback to empty bytes
                content = b''
            
            content_hash = hashlib.sha256(content).hexdigest()
            item['content_hash'] = content_hash
            
            logger.debug(f"Generated content hash for {item['uri']}: {content_hash[:8]}...")
        
        return item


class MetadataExtractionPipeline:
    """
    Pipeline to extract and enhance metadata from artifacts.
    """
    
    def process_item(self, item, spider):
        """Extract additional metadata from artifacts."""
        
        if isinstance(item, ArtifactItem):
            return self._extract_artifact_metadata(item, spider)
        
        return item
    
    def _extract_artifact_metadata(self, item: ArtifactItem, spider) -> ArtifactItem:
        """Extract metadata from artifact content."""
        
        # Note: Language detection removed - ArtifactItem doesn't have language field
        # Language detection happens during normalization phase
        
        # Determine MIME type
        if not item.get('mime_type'):
            uri = item['uri']
            mime_type, _ = mimetypes.guess_type(uri)
            if not mime_type and item.get('raw_content'):
                # Try to detect from content
                import magic
                try:
                    mime_type = magic.from_buffer(item['raw_content'][:1024], mime=True)
                except:
                    mime_type = 'application/octet-stream'
            
            item['mime_type'] = mime_type or 'text/html'
        
        # Set timestamps
        if not item.get('fetched_at'):
            item['fetched_at'] = datetime.utcnow().isoformat()
        
        if not item.get('discovered_at'):
            item['discovered_at'] = datetime.utcnow().isoformat()
        
        # Note: domain can be extracted from URI when needed, no need to store separately
        # as ArtifactItem doesn't have a domain field
        
        return item


class DatabaseStoragePipeline:
    """
    Pipeline to store items in the PostgreSQL database.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.Session = None
        self.stored_count = 0
        self.error_count = 0
        # Ensure models can be imported by adding svc-api/app to path
        import sys
        import pathlib
        # Get the apps directory (parent of svc-ingestion)
        apps_dir = pathlib.Path(__file__).resolve().parent.parent.parent
        svc_api_app_path = apps_dir / 'svc-api' / 'app'
        if str(svc_api_app_path) not in sys.path:
            sys.path.insert(0, str(svc_api_app_path))
        
    @classmethod
    def from_crawler(cls, crawler):
        database_url = crawler.settings.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not configured")
        
        return cls(database_url)
    
    def open_spider(self, spider):
        """Initialize database connection."""
        try:
            self.engine = create_engine(self.database_url)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close_spider(self, spider):
        """Close database connection and log statistics."""
        if self.engine:
            self.engine.dispose()
        
        logger.info(f"Database storage complete - Stored: {self.stored_count}, Errors: {self.error_count}")
    
    def process_item(self, item, spider):
        """Store item in database."""
        
        try:
            if isinstance(item, ArtifactItem):
                self._store_artifact(item, spider)
            elif isinstance(item, DocumentMetadataItem):
                self._store_metadata(item, spider)
            elif isinstance(item, CrawlJobItem):
                self._store_job(item, spider)
            
            self.stored_count += 1
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Database storage error for {item}: {e}")
            # Don't drop the item, let other pipelines process it
        
        return item
    
    def _store_artifact(self, item: ArtifactItem, spider):
        """Store artifact in database."""
        session = self.Session()
        
        try:
            # Import models from svc-api service
            # Add svc-api/app directory to path to access models
            import sys
            import pathlib
            # Get the apps directory (parent of svc-ingestion)
            apps_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            svc_api_app_path = apps_dir / 'svc-api' / 'app'
            if str(svc_api_app_path) not in sys.path:
                sys.path.insert(0, str(svc_api_app_path))
            from models.artifact import Artifact, DocumentMetadata
            from db.database import Base  # Ensure Base is imported for models
            
            # Check if artifact already exists
            existing = session.query(Artifact).filter_by(content_hash=item['content_hash']).first()
            if existing:
                logger.debug(f"Artifact already exists: {item['uri']}")
                return
            
            # Create new artifact
            artifact = Artifact(
                source_id=item.get('source_id'),
                uri=item['uri'],
                content_hash=item['content_hash'],
                mime_type=item.get('mime_type'),
                created_at=datetime.fromisoformat(item['fetched_at']) if item.get('fetched_at') else datetime.utcnow()
            )
            
            session.add(artifact)
            session.commit()
            
            # Note: We don't store artifact_id back in item as ArtifactItem doesn't have that field
            # The artifact.id is already persisted in the database
            
            logger.debug(f"Stored artifact: {item['uri']} (ID: {artifact.id})")
            
            # Note: Normalization is triggered by ObjectStoragePipeline after content is stored
            # This ensures content is available in MinIO before normalization attempts to fetch it
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _trigger_normalization(self, artifact_id: str, spider):
        """Trigger normalization service for newly stored artifact"""
        try:
            # Try to use Celery task queue first (preferred method)
            use_queue = spider.settings.get('USE_TASK_QUEUE', True)
            
            if use_queue:
                try:
                    import sys
                    import pathlib
                    # Try multiple paths - shared module is mounted at /app/apps/shared
                    # First try the mounted path (for container)
                    if '/app/apps' not in sys.path:
                        sys.path.insert(0, '/app/apps')
                    # Also try calculated project root as fallback
                    project_root = pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent
                    if str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))
                    
                    from apps.shared.tasks.normalize_tasks import normalize_artifact
                    
                    # Enqueue normalization task (fire-and-forget)
                    task = normalize_artifact.delay(str(artifact_id))
                    logger.info(f"Enqueued normalization task for artifact {artifact_id} (task_id: {task.id})")
                    return
                except ImportError as e:
                    logger.warning(f"Celery not available, falling back to HTTP: {e}")
                except Exception as e:
                    logger.warning(f"Failed to enqueue normalization task, falling back to HTTP: {e}")
            
            # Fallback to HTTP if queue not available
            import httpx
            normalize_url = spider.settings.get('NORMALIZE_SERVICE_URL')
            
            if not normalize_url:
                logger.warning("NORMALIZE_SERVICE_URL not configured, skipping normalization trigger")
                return
            
            try:
                # Use httpx in sync mode for Scrapy pipeline
                # Ensure artifact_id is a string for JSON serialization
                artifact_id_str = str(artifact_id)
                
                # Increased timeout to 60 seconds to allow normalization to complete
                # Normalization can take time for large documents or LLM processing
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        f"{normalize_url}/api/v1/documents/process",
                        json={"artifact_id": artifact_id_str},
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        logger.info(f"Triggered normalization for artifact {artifact_id}")
                    else:
                        logger.warning(
                            f"Normalization trigger returned {response.status_code} "
                            f"for artifact {artifact_id}: {response.text}"
                        )
            except httpx.TimeoutException:
                logger.warning(f"Timeout triggering normalization for artifact {artifact_id} (60s timeout exceeded)")
            except httpx.RequestError as e:
                logger.warning(f"Failed to trigger normalization for artifact {artifact_id}: {e}")
                
        except ImportError:
            logger.warning("httpx not available, cannot trigger normalization")
        except Exception as e:
            # Don't fail the pipeline if normalization trigger fails
            logger.warning(f"Error triggering normalization for artifact {artifact_id}: {e}")
    
    def _trigger_normalization_after_storage(self, content_hash: str, spider):
        """Trigger normalization service after content is stored in MinIO"""
        try:
            # Get artifact ID from database using content_hash
            import sys
            import pathlib
            apps_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            svc_api_app_path = apps_dir / 'svc-api' / 'app'
            if str(svc_api_app_path) not in sys.path:
                sys.path.insert(0, str(svc_api_app_path))
            
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.artifact import Artifact
            
            database_url = spider.settings.get('DATABASE_URL')
            if not database_url:
                logger.warning("DATABASE_URL not configured, cannot find artifact for normalization")
                return
            
            engine = create_engine(database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                artifact = session.query(Artifact).filter(Artifact.content_hash == content_hash).first()
                if artifact:
                    # Use the trigger method from DatabaseStoragePipeline
                    # Create a temporary instance to access the method
                    temp_pipeline = DatabaseStoragePipeline(database_url)
                    temp_pipeline._trigger_normalization(artifact.id, spider)
                else:
                    logger.warning(f"Artifact not found for content_hash {content_hash[:8]}...")
            finally:
                session.close()
                
        except Exception as e:
            # Don't fail the pipeline if normalization trigger fails
            logger.warning(f"Error triggering normalization after storage: {e}")
    
    def _store_metadata(self, item: DocumentMetadataItem, spider):
        """Store document metadata in database."""
        session = self.Session()
        
        try:
            # Import models from svc-api service
            import sys
            import pathlib
            # Get the apps directory (parent of svc-ingestion)
            apps_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            svc_api_app_path = apps_dir / 'svc-api' / 'app'
            if str(svc_api_app_path) not in sys.path:
                sys.path.insert(0, str(svc_api_app_path))
            from models.artifact import Artifact, DocumentMetadata
            
            # Find the associated artifact
            artifact = session.query(Artifact).filter_by(uri=item['artifact_uri']).first()
            if not artifact:
                logger.warning(f"No artifact found for metadata: {item['artifact_uri']}")
                return
            
            # Create metadata record
            metadata = DocumentMetadata(
                artifact_id=artifact.id,
                title=item.get('title'),
                authors=json.dumps(item.get('authors', [])) if item.get('authors') else None,
                organization=item.get('organization'),
                pub_date=datetime.fromisoformat(item['publication_date']) if item.get('publication_date') else None,
                topics=json.dumps(item.get('topics', [])) if item.get('topics') else None,
                geo_location=item.get('geo_location'),
                language=item.get('language')
            )
            
            session.add(metadata)
            session.commit()
            
            logger.debug(f"Stored metadata for artifact: {artifact.id}")
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _store_job(self, item: CrawlJobItem, spider):
        """Store crawl job information in database."""
        # Implementation would store job tracking information
        pass


class ObjectStoragePipeline:
    """
    Pipeline to store raw content in MinIO/S3 object storage.
    """
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, database_url: str = None):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.database_url = database_url
        self.s3_client = None
        self.stored_count = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        endpoint = crawler.settings.get('MINIO_ENDPOINT')
        access_key = crawler.settings.get('MINIO_ACCESS_KEY')
        secret_key = crawler.settings.get('MINIO_SECRET_KEY')
        bucket = crawler.settings.get('MINIO_BUCKET_ARTIFACTS', 'artifacts')
        database_url = crawler.settings.get('DATABASE_URL')
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError("MinIO configuration incomplete")
        
        return cls(endpoint, access_key, secret_key, bucket, database_url)
    
    def open_spider(self, spider):
        """Initialize S3/MinIO client."""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            
            # Ensure bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket)
            except ClientError:
                self.s3_client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            
            logger.info("Object storage connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to object storage: {e}")
            raise
    
    def process_item(self, item, spider):
        """Store raw content in object storage."""
        
        # Log that we received an item
        if isinstance(item, ArtifactItem):
            logger.info(f"ObjectStorage received ArtifactItem: {item.get('uri', 'no uri')[:60]}")
            has_raw = item.get('raw_content') is not None
            logger.info(f"  Has raw_content: {has_raw}")
            
            if has_raw:
                raw_content = item.get('raw_content')
                logger.info(f"  raw_content type: {type(raw_content)}, size: {len(raw_content) if raw_content else 0}")
            
            if has_raw:
                try:
                    self._store_content(item, spider)
                    self.stored_count += 1
                except Exception as e:
                    logger.error(f"Object storage error for {item['uri']}: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            else:
                logger.warning(f"  Skipping - no raw_content in item")
        
        return item
    
    def _store_content(self, item: ArtifactItem, spider):
        """Store artifact content in object storage."""
        
        content_hash = item['content_hash']
        key = f"artifacts/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.bin"
        
        # Check if object already exists
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            logger.debug(f"Content already stored: {content_hash}")
            # Note: Don't set storage_key on item - ArtifactItem doesn't support that field
            # The key can be reconstructed from content_hash when needed
            # Still trigger normalization even if content already exists
            # This includes retry logic to handle transient failures
            self._trigger_normalization_after_storage(content_hash, spider, retry_count=0, max_retries=3)
            return
        except ClientError:
            pass  # Object doesn't exist, continue with upload
        
        # Upload content
        metadata = {
            'uri': item['uri'],
            'mime-type': item.get('mime_type', 'application/octet-stream'),
            'fetched-at': item.get('fetched_at', ''),
            'spider': item.get('spider_name', ''),
        }
        
        # Ensure raw_content is bytes, not a list
        raw_content = item['raw_content']
        if isinstance(raw_content, list):
            # If it's a list, join the bytes
            raw_content = b''.join(raw_content) if raw_content else b''
        elif not isinstance(raw_content, (bytes, bytearray)):
            # If it's a string or other type, encode it
            raw_content = str(raw_content).encode('utf-8')
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=raw_content,
            ContentType=item.get('mime_type', 'application/octet-stream'),
            Metadata=metadata
        )
        
        # Note: storage_key is not stored in item as ArtifactItem doesn't have that field
        # The key can be reconstructed from content_hash when needed
        logger.debug(f"Stored content: {content_hash} -> {key}")
        
        # Trigger normalization service AFTER content is stored in MinIO
        # Get artifact ID from database using content_hash
        # This includes retry logic to handle transient failures
        self._trigger_normalization_after_storage(content_hash, spider, retry_count=0, max_retries=3)
    
    def _trigger_normalization_after_storage(self, content_hash: str, spider, retry_count: int = 0, max_retries: int = 3):
        """
        Trigger normalization service after content is stored in MinIO.
        
        Includes retry logic with exponential backoff to handle transient failures
        like database connection issues or timing problems.
        
        Args:
            content_hash: SHA-256 hash of the artifact content
            spider: Scrapy spider instance
            retry_count: Current retry attempt (for recursive retries)
            max_retries: Maximum number of retry attempts
        """
        try:
            # Get artifact ID from database using content_hash
            import sys
            import pathlib
            import time
            apps_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            svc_api_app_path = apps_dir / 'svc-api' / 'app'
            if str(svc_api_app_path) not in sys.path:
                sys.path.insert(0, str(svc_api_app_path))
            
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from models.artifact import Artifact
            
            database_url = self.database_url or spider.settings.get('DATABASE_URL')
            if not database_url:
                logger.error(f"[NORMALIZATION_TRIGGER] DATABASE_URL not configured, cannot find artifact for normalization (content_hash: {content_hash[:8]}...)")
                return
            
            engine = create_engine(database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Query with a small delay to ensure database commit has completed
                # This helps with timing issues where artifact was just created
                if retry_count > 0:
                    delay = min(2 ** retry_count, 10)  # Exponential backoff: 2s, 4s, 8s, max 10s
                    logger.info(f"[NORMALIZATION_TRIGGER] Retry attempt {retry_count}/{max_retries} - waiting {delay}s before querying database")
                    time.sleep(delay)
                
                artifact = session.query(Artifact).filter(Artifact.content_hash == content_hash).first()
                if artifact:
                    # Use the trigger method from DatabaseStoragePipeline
                    # Create a temporary instance to access the method
                    temp_pipeline = DatabaseStoragePipeline(database_url)
                    temp_pipeline._trigger_normalization(artifact.id, spider)
                    logger.info(f"[NORMALIZATION_TRIGGER] Successfully triggered normalization for artifact {artifact.id} (content_hash: {content_hash[:8]}...)")
                else:
                    # Artifact not found - this could be a timing issue, retry if we haven't exceeded max_retries
                    if retry_count < max_retries:
                        logger.warning(f"[NORMALIZATION_TRIGGER] Artifact not found for content_hash {content_hash[:8]}... (attempt {retry_count + 1}/{max_retries}) - will retry")
                        session.close()
                        return self._trigger_normalization_after_storage(content_hash, spider, retry_count + 1, max_retries)
                    else:
                        logger.error(f"[NORMALIZATION_TRIGGER] Artifact not found for content_hash {content_hash[:8]}... after {max_retries} attempts - giving up")
            finally:
                session.close()
                
        except Exception as e:
            # Log error with full traceback for debugging
            import traceback
            error_traceback = traceback.format_exc()
            
            # Retry on certain exceptions (database connection errors, etc.)
            retryable_exceptions = (
                'OperationalError',
                'InterfaceError',
                'ConnectionError',
                'TimeoutError',
            )
            
            is_retryable = any(exc_type in str(type(e).__name__) for exc_type in retryable_exceptions)
            
            if is_retryable and retry_count < max_retries:
                logger.warning(
                    f"[NORMALIZATION_TRIGGER] Retryable error triggering normalization after storage "
                    f"(content_hash: {content_hash[:8]}..., attempt {retry_count + 1}/{max_retries}): {e}"
                )
                logger.debug(f"[NORMALIZATION_TRIGGER] Traceback: {error_traceback}")
                # Retry with exponential backoff
                return self._trigger_normalization_after_storage(content_hash, spider, retry_count + 1, max_retries)
            else:
                # Non-retryable error or max retries exceeded
                logger.error(
                    f"[NORMALIZATION_TRIGGER] Error triggering normalization after storage "
                    f"(content_hash: {content_hash[:8]}...): {e}"
                )
                logger.error(f"[NORMALIZATION_TRIGGER] Full traceback: {error_traceback}")
                # Don't fail the pipeline if normalization trigger fails, but log as error
                # This ensures artifacts are still stored even if normalization trigger fails
    
    def close_spider(self, spider):
        """Log storage statistics."""
        logger.info(f"Object storage complete - Stored: {self.stored_count} files")


class MonitoringPipeline:
    """
    Pipeline for collecting metrics and monitoring.
    """
    
    def __init__(self):
        self.processed_items = 0
        self.processing_times = []
        self.start_time = datetime.utcnow()
        
    def process_item(self, item, spider):
        """Track item processing metrics."""
        
        self.processed_items += 1
        
        # Track processing time if available
        if hasattr(item, 'processing_start_time'):
            processing_time = datetime.utcnow() - item.processing_start_time
            self.processing_times.append(processing_time.total_seconds())
        
        # Update spider stats
        spider.crawler.stats.inc_value('items_processed')
        spider.crawler.stats.inc_value(f'items_processed/{item.__class__.__name__}')
        
        # Log progress every 100 items
        if self.processed_items % 100 == 0:
            logger.info(f"Processed {self.processed_items} items")
        
        return item
    
    def close_spider(self, spider):
        """Log final processing statistics."""
        
        duration = datetime.utcnow() - self.start_time
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        logger.info(f"Processing complete:")
        logger.info(f"  Total items: {self.processed_items}")
        logger.info(f"  Duration: {duration.total_seconds():.2f}s")
        logger.info(f"  Items/second: {self.processed_items / duration.total_seconds():.2f}")
        logger.info(f"  Avg processing time: {avg_processing_time:.3f}s")
        
        # Update final stats
        spider.crawler.stats.set_value('total_items_processed', self.processed_items)
        spider.crawler.stats.set_value('processing_duration', duration.total_seconds())
        spider.crawler.stats.set_value('items_per_second', self.processed_items / duration.total_seconds())


class ErrorHandlingPipeline:
    """
    Pipeline for handling and logging errors.
    """
    
    def __init__(self):
        self.error_count = 0
        self.errors_by_type = {}
        
    def process_item(self, item, spider):
        """Process item with error handling."""
        try:
            # Validate item has required fields
            self._validate_required_fields(item)
            return item
            
        except Exception as e:
            self.error_count += 1
            error_type = e.__class__.__name__
            self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
            
            logger.error(f"Pipeline error processing {item}: {e}")
            
            # Update spider stats
            spider.crawler.stats.inc_value('pipeline_errors')
            spider.crawler.stats.inc_value(f'pipeline_errors/{error_type}')
            
            # Re-raise to drop the item
            raise DropItem(f"Pipeline error: {e}")
    
    def _validate_required_fields(self, item):
        """Validate that item has required fields."""
        if isinstance(item, ArtifactItem):
            required_fields = ['uri', 'content_hash']
            for field in required_fields:
                if not item.get(field):
                    raise ValueError(f"Missing required field: {field}")
    
    def close_spider(self, spider):
        """Log error statistics."""
        logger.info(f"Error handling complete - Total errors: {self.error_count}")
        for error_type, count in self.errors_by_type.items():
            logger.info(f"  {error_type}: {count}")

