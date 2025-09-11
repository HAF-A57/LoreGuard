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
            content = item.get('raw_content', b'') or item.get('text_content', '').encode('utf-8')
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
        
        # Detect language
        if item.get('text_content') and not item.get('language'):
            try:
                detected_lang = langdetect.detect(item['text_content'][:1000])
                item['language'] = detected_lang
                logger.debug(f"Detected language for {item['uri']}: {detected_lang}")
            except:
                item['language'] = 'unknown'
        
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
        
        # Extract domain information
        parsed_uri = urlparse(item['uri'])
        item['domain'] = parsed_uri.netloc
        
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
            # Import here to avoid circular imports
            from app.models import Artifact
            
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
            
            # Store the generated ID back in the item
            item['artifact_id'] = artifact.id
            
            logger.debug(f"Stored artifact: {item['uri']} (ID: {artifact.id})")
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _store_metadata(self, item: DocumentMetadataItem, spider):
        """Store document metadata in database."""
        session = self.Session()
        
        try:
            # Import here to avoid circular imports
            from app.models import DocumentMetadata, Artifact
            
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
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.s3_client = None
        self.stored_count = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        endpoint = crawler.settings.get('MINIO_ENDPOINT')
        access_key = crawler.settings.get('MINIO_ACCESS_KEY')
        secret_key = crawler.settings.get('MINIO_SECRET_KEY')
        bucket = crawler.settings.get('MINIO_BUCKET_ARTIFACTS', 'artifacts')
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError("MinIO configuration incomplete")
        
        return cls(endpoint, access_key, secret_key, bucket)
    
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
        
        if isinstance(item, ArtifactItem) and item.get('raw_content'):
            try:
                self._store_content(item, spider)
                self.stored_count += 1
            except Exception as e:
                logger.error(f"Object storage error for {item['uri']}: {e}")
        
        return item
    
    def _store_content(self, item: ArtifactItem, spider):
        """Store artifact content in object storage."""
        
        content_hash = item['content_hash']
        key = f"artifacts/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}.bin"
        
        # Check if object already exists
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            logger.debug(f"Content already stored: {content_hash}")
            item['storage_key'] = key
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
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=item['raw_content'],
            ContentType=item.get('mime_type', 'application/octet-stream'),
            Metadata=metadata
        )
        
        item['storage_key'] = key
        logger.debug(f"Stored content: {content_hash} -> {key}")
    
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

