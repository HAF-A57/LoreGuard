"""
LoreGuard Ingestion Service - Scrapy Items

Defines the data structures for scraped content and metadata.
"""

import scrapy
from scrapy import Field
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags, strip_html5_whitespace
import re
from datetime import datetime
from typing import Optional, List, Dict, Any


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Remove HTML tags and extra whitespace
    text = remove_tags(text)
    text = strip_html5_whitespace(text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return ""
    
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc


def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date string to ISO format."""
    if not date_str:
        return None
    
    # This is a simplified version - in production, you'd want more robust date parsing
    try:
        from dateutil import parser
        parsed_date = parser.parse(date_str)
        return parsed_date.isoformat()
    except:
        return None


class ArtifactItem(scrapy.Item):
    """
    Primary item representing a discovered document/artifact.
    Maps to the Artifact model in the database.
    """
    
    # Core identification
    uri = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    source_id = Field(
        output_processor=TakeFirst()
    )
    
    content_hash = Field(
        output_processor=TakeFirst()
    )
    
    mime_type = Field(
        output_processor=TakeFirst()
    )
    
    # Content
    raw_content = Field()  # Binary content
    
    text_content = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Technical metadata
    content_length = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    response_status = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    response_headers = Field()
    
    # Timestamps
    discovered_at = Field(
        output_processor=TakeFirst()
    )
    
    fetched_at = Field(
        output_processor=TakeFirst()
    )
    
    # Processing metadata
    spider_name = Field(
        output_processor=TakeFirst()
    )
    
    crawl_job_id = Field(
        output_processor=TakeFirst()
    )


class DocumentMetadataItem(scrapy.Item):
    """
    Document metadata extracted from artifacts.
    Maps to the DocumentMetadata model in the database.
    """
    
    # Reference to parent artifact
    artifact_uri = Field(
        output_processor=TakeFirst()
    )
    
    # Document metadata
    title = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    authors = Field(
        input_processor=MapCompose(clean_text),
        output_processor=lambda x: [author.strip() for author in x if author.strip()]
    )
    
    organization = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    publication_date = Field(
        input_processor=MapCompose(normalize_date),
        output_processor=TakeFirst()
    )
    
    topics = Field(
        input_processor=MapCompose(clean_text),
        output_processor=lambda x: [topic.strip() for topic in x if topic.strip()]
    )
    
    geo_location = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    language = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )
    
    # Additional metadata
    description = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    keywords = Field(
        input_processor=MapCompose(clean_text),
        output_processor=lambda x: [kw.strip() for kw in x if kw.strip()]
    )
    
    document_type = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )


class SourceConfigItem(scrapy.Item):
    """
    Source configuration item for managing crawl sources.
    """
    
    # Source identification
    source_id = Field(
        output_processor=TakeFirst()
    )
    
    name = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    base_url = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    source_type = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )
    
    # Crawl configuration
    crawl_frequency = Field(
        output_processor=TakeFirst()
    )
    
    max_depth = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    allowed_domains = Field(
        output_processor=lambda x: [domain.strip() for domain in x if domain.strip()]
    )
    
    start_urls = Field(
        output_processor=lambda x: [url.strip() for url in x if url.strip()]
    )
    
    # Source-specific settings
    custom_headers = Field()
    
    authentication_required = Field(
        input_processor=MapCompose(bool),
        output_processor=TakeFirst()
    )
    
    javascript_required = Field(
        input_processor=MapCompose(bool),
        output_processor=TakeFirst()
    )
    
    # Content filtering
    include_patterns = Field(
        output_processor=lambda x: [pattern.strip() for pattern in x if pattern.strip()]
    )
    
    exclude_patterns = Field(
        output_processor=lambda x: [pattern.strip() for pattern in x if pattern.strip()]
    )
    
    # Politeness settings
    download_delay = Field(
        input_processor=MapCompose(float),
        output_processor=TakeFirst()
    )
    
    concurrent_requests = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    # Status and monitoring
    status = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )
    
    last_crawl_at = Field(
        input_processor=MapCompose(normalize_date),
        output_processor=TakeFirst()
    )
    
    success_rate = Field(
        input_processor=MapCompose(float),
        output_processor=TakeFirst()
    )
    
    error_count = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )


class CrawlJobItem(scrapy.Item):
    """
    Crawl job tracking item for monitoring and reporting.
    """
    
    # Job identification
    job_id = Field(
        output_processor=TakeFirst()
    )
    
    source_id = Field(
        output_processor=TakeFirst()
    )
    
    spider_name = Field(
        output_processor=TakeFirst()
    )
    
    # Job configuration
    job_type = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )
    
    priority = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    # Job status
    status = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )
    
    started_at = Field(
        output_processor=TakeFirst()
    )
    
    completed_at = Field(
        output_processor=TakeFirst()
    )
    
    # Job statistics
    items_scraped = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    items_dropped = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    requests_made = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    response_received = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    # Error tracking
    errors = Field()
    
    warnings = Field()
    
    # Performance metrics
    avg_response_time = Field(
        input_processor=MapCompose(float),
        output_processor=TakeFirst()
    )
    
    total_bytes_downloaded = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )


class LinkItem(scrapy.Item):
    """
    Discovered link item for tracking and following.
    """
    
    # Link information
    url = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    source_url = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    
    link_text = Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # Link classification
    link_type = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )
    
    priority = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    # Discovery metadata
    discovered_at = Field(
        output_processor=TakeFirst()
    )
    
    depth = Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst()
    )
    
    # Processing status
    processed = Field(
        input_processor=MapCompose(bool),
        output_processor=TakeFirst()
    )
    
    processing_status = Field(
        input_processor=MapCompose(str.lower, str.strip),
        output_processor=TakeFirst()
    )


# Item loaders for more complex processing
from itemloaders import ItemLoader

class ArtifactItemLoader(ItemLoader):
    """Custom item loader for ArtifactItem with additional processing."""
    
    default_item_class = ArtifactItem
    
    # Custom processors can be added here
    title_in = MapCompose(clean_text, lambda x: x[:500])  # Limit title length
    

class DocumentMetadataItemLoader(ItemLoader):
    """Custom item loader for DocumentMetadataItem."""
    
    default_item_class = DocumentMetadataItem
    
    # Custom processing for authors
    authors_in = MapCompose(
        clean_text,
        lambda x: [author.strip() for author in re.split(r'[,;]', x) if author.strip()]
    )
    
    # Custom processing for topics/keywords
    topics_in = MapCompose(
        clean_text,
        lambda x: [topic.strip() for topic in re.split(r'[,;]', x) if topic.strip()]
    )
    
    keywords_in = MapCompose(
        clean_text,
        lambda x: [kw.strip() for kw in re.split(r'[,;]', x) if kw.strip()]
    )

