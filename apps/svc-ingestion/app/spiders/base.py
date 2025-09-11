"""
LoreGuard Ingestion Service - Base Spider

Base spider class with common functionality for all LoreGuard spiders.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.url import canonicalize_url

from app.items import ArtifactItem, DocumentMetadataItem, ArtifactItemLoader, DocumentMetadataItemLoader


logger = logging.getLogger(__name__)


class BaseLoreGuardSpider(scrapy.Spider):
    """
    Base spider class for LoreGuard ingestion with common functionality.
    """
    
    # Default settings (can be overridden in subclasses)
    custom_settings = {
        'DOWNLOAD_DELAY': 2.0,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    }
    
    def __init__(self, source_id: str = None, max_depth: int = 3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.source_id = source_id or getattr(self, 'source_id', 'unknown')
        self.max_depth = max_depth
        self.crawl_job_id = kwargs.get('job_id', f"{self.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        
        # Statistics tracking
        self.stats = {
            'pages_crawled': 0,
            'documents_found': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }
        
        # Link extractor for finding new URLs
        self.link_extractor = LinkExtractor(
            allow_domains=getattr(self, 'allowed_domains', []),
            deny_extensions=['jpg', 'jpeg', 'png', 'gif', 'svg', 'ico', 'css', 'js'],
            canonicalize=True,
            unique=True
        )
        
        logger.info(f"Initialized spider {self.name} for source {self.source_id}")
    
    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests."""
        
        start_urls = getattr(self, 'start_urls', [])
        if not start_urls:
            logger.error(f"No start URLs configured for spider {self.name}")
            return
        
        for url in start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta={
                    'source_id': self.source_id,
                    'depth': 0,
                    'job_id': self.crawl_job_id
                },
                dont_filter=True  # Always process start URLs
            )
    
    def parse(self, response: Response) -> Generator:
        """
        Default parse method - extracts content and follows links.
        Override in subclasses for source-specific parsing.
        """
        
        self.stats['pages_crawled'] += 1
        current_depth = response.meta.get('depth', 0)
        
        logger.debug(f"Parsing {response.url} (depth: {current_depth})")
        
        # Extract content from current page
        yield from self.extract_content(response)
        
        # Follow links if not at max depth
        if current_depth < self.max_depth:
            yield from self.follow_links(response)
    
    def extract_content(self, response: Response) -> Generator:
        """Extract content from the current page."""
        
        # Skip non-HTML content for link extraction
        if not self.is_html_response(response):
            # But still process as potential document
            yield from self.process_document(response)
            return
        
        # Extract main content
        content_selectors = [
            'article',
            'main',
            '.content',
            '.post-content',
            '.entry-content',
            '#content',
            'body'
        ]
        
        text_content = ""
        for selector in content_selectors:
            content = response.css(selector).get()
            if content:
                text_content = response.css(selector + ' ::text').getall()
                text_content = ' '.join(text_content).strip()
                break
        
        if not text_content:
            # Fallback to body text
            text_content = ' '.join(response.css('body ::text').getall()).strip()
        
        # Only process if we have meaningful content
        if len(text_content) > 100:
            yield from self.process_document(response, text_content)
    
    def process_document(self, response: Response, text_content: str = None) -> Generator:
        """Process a document and extract metadata."""
        
        try:
            # Create artifact item
            artifact_loader = ArtifactItemLoader(response=response)
            
            artifact_loader.add_value('uri', response.url)
            artifact_loader.add_value('source_id', self.source_id)
            artifact_loader.add_value('spider_name', self.name)
            artifact_loader.add_value('crawl_job_id', self.crawl_job_id)
            artifact_loader.add_value('response_status', response.status)
            artifact_loader.add_value('content_length', len(response.body))
            artifact_loader.add_value('raw_content', response.body)
            
            if text_content:
                artifact_loader.add_value('text_content', text_content)
            
            # Detect MIME type
            content_type = response.headers.get('Content-Type', b'').decode('utf-8')
            if content_type:
                mime_type = content_type.split(';')[0].strip()
                artifact_loader.add_value('mime_type', mime_type)
            
            artifact_item = artifact_loader.load_item()
            
            # Extract metadata
            metadata_item = self.extract_metadata(response, text_content)
            
            self.stats['documents_found'] += 1
            
            yield artifact_item
            if metadata_item:
                yield metadata_item
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error processing document {response.url}: {e}")
    
    def extract_metadata(self, response: Response, text_content: str = None) -> Optional[DocumentMetadataItem]:
        """Extract metadata from the document."""
        
        try:
            metadata_loader = DocumentMetadataItemLoader(response=response)
            
            metadata_loader.add_value('artifact_uri', response.url)
            
            # Extract title
            title_selectors = [
                'title::text',
                'h1::text',
                '.title::text',
                '.post-title::text',
                'meta[property="og:title"]::attr(content)',
                'meta[name="title"]::attr(content)'
            ]
            
            title = self.extract_first_match(response, title_selectors)
            if title:
                metadata_loader.add_value('title', title)
            
            # Extract authors
            author_selectors = [
                'meta[name="author"]::attr(content)',
                '.author::text',
                '.byline::text',
                '.post-author::text',
                'meta[property="article:author"]::attr(content)'
            ]
            
            authors = self.extract_all_matches(response, author_selectors)
            if authors:
                metadata_loader.add_value('authors', authors)
            
            # Extract organization/publisher
            org_selectors = [
                'meta[property="og:site_name"]::attr(content)',
                'meta[name="publisher"]::attr(content)',
                '.publisher::text',
                '.site-name::text'
            ]
            
            organization = self.extract_first_match(response, org_selectors)
            if organization:
                metadata_loader.add_value('organization', organization)
            
            # Extract publication date
            date_selectors = [
                'meta[property="article:published_time"]::attr(content)',
                'meta[name="date"]::attr(content)',
                'meta[name="publish_date"]::attr(content)',
                '.publish-date::text',
                '.post-date::text',
                'time::attr(datetime)'
            ]
            
            pub_date = self.extract_first_match(response, date_selectors)
            if pub_date:
                metadata_loader.add_value('publication_date', pub_date)
            
            # Extract keywords/topics
            keyword_selectors = [
                'meta[name="keywords"]::attr(content)',
                'meta[property="article:tag"]::attr(content)',
                '.tags a::text',
                '.categories a::text'
            ]
            
            keywords = self.extract_all_matches(response, keyword_selectors)
            if keywords:
                metadata_loader.add_value('topics', keywords)
            
            # Extract description
            desc_selectors = [
                'meta[name="description"]::attr(content)',
                'meta[property="og:description"]::attr(content)',
                '.excerpt::text',
                '.summary::text'
            ]
            
            description = self.extract_first_match(response, desc_selectors)
            if description:
                metadata_loader.add_value('description', description)
            
            # Try to extract language
            lang_selectors = [
                'html::attr(lang)',
                'meta[http-equiv="content-language"]::attr(content)'
            ]
            
            language = self.extract_first_match(response, lang_selectors)
            if language:
                metadata_loader.add_value('language', language)
            
            metadata_item = metadata_loader.load_item()
            
            # Only return if we extracted meaningful metadata
            if any(metadata_item.get(field) for field in ['title', 'authors', 'organization', 'publication_date']):
                return metadata_item
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {response.url}: {e}")
        
        return None
    
    def follow_links(self, response: Response) -> Generator[Request, None, None]:
        """Follow links found on the current page."""
        
        current_depth = response.meta.get('depth', 0)
        
        # Extract links using the link extractor
        links = self.link_extractor.extract_links(response)
        
        for link in links:
            # Apply custom link filtering
            if self.should_follow_link(link.url, response):
                yield Request(
                    url=link.url,
                    callback=self.parse,
                    meta={
                        'source_id': self.source_id,
                        'depth': current_depth + 1,
                        'job_id': self.crawl_job_id,
                        'link_text': link.text
                    }
                )
    
    def should_follow_link(self, url: str, response: Response) -> bool:
        """Determine if a link should be followed."""
        
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Skip certain file types
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip social media and external links (can be overridden)
        skip_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']
        if any(domain in parsed.netloc.lower() for domain in skip_domains):
            return False
        
        return True
    
    def extract_first_match(self, response: Response, selectors: List[str]) -> Optional[str]:
        """Extract the first matching value from a list of selectors."""
        
        for selector in selectors:
            try:
                value = response.css(selector).get()
                if value and value.strip():
                    return value.strip()
            except Exception:
                continue
        
        return None
    
    def extract_all_matches(self, response: Response, selectors: List[str]) -> List[str]:
        """Extract all matching values from a list of selectors."""
        
        results = []
        
        for selector in selectors:
            try:
                values = response.css(selector).getall()
                for value in values:
                    if value and value.strip():
                        cleaned = value.strip()
                        if cleaned not in results:
                            results.append(cleaned)
            except Exception:
                continue
        
        return results
    
    def is_html_response(self, response: Response) -> bool:
        """Check if response is HTML content."""
        
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        return 'text/html' in content_type or 'application/xhtml' in content_type
    
    def closed(self, reason: str):
        """Called when spider closes."""
        
        end_time = datetime.utcnow()
        duration = end_time - self.stats['start_time']
        
        logger.info(f"Spider {self.name} closed: {reason}")
        logger.info(f"Statistics:")
        logger.info(f"  Duration: {duration.total_seconds():.2f}s")
        logger.info(f"  Pages crawled: {self.stats['pages_crawled']}")
        logger.info(f"  Documents found: {self.stats['documents_found']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        
        if self.stats['pages_crawled'] > 0:
            logger.info(f"  Documents/page ratio: {self.stats['documents_found'] / self.stats['pages_crawled']:.2f}")
    
    def handle_error(self, failure):
        """Handle request errors."""
        
        self.stats['errors'] += 1
        logger.error(f"Request failed: {failure.request.url} - {failure.value}")


class GenericWebSpider(BaseLoreGuardSpider):
    """
    Generic web spider for crawling standard websites.
    """
    
    name = 'generic_web'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Additional settings for generic web crawling
        self.custom_settings.update({
            'DOWNLOAD_DELAY': 2.0,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.5,
        })


class NewsSpider(BaseLoreGuardSpider):
    """
    Specialized spider for news websites.
    """
    
    name = 'news'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # News-specific settings
        self.custom_settings.update({
            'DOWNLOAD_DELAY': 1.5,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        })
    
    def should_follow_link(self, url: str, response: Response) -> bool:
        """News-specific link filtering."""
        
        if not super().should_follow_link(url, response):
            return False
        
        # Prioritize article URLs
        article_patterns = [
            r'/article/',
            r'/news/',
            r'/story/',
            r'/\d{4}/\d{2}/',  # Date patterns
            r'-\d{4}-\d{2}-\d{2}',  # Date in URL
        ]
        
        return any(re.search(pattern, url) for pattern in article_patterns)


class AcademicSpider(BaseLoreGuardSpider):
    """
    Specialized spider for academic and research websites.
    """
    
    name = 'academic'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Academic-specific settings
        self.custom_settings.update({
            'DOWNLOAD_DELAY': 3.0,  # Be more respectful to academic sites
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        })
    
    def should_follow_link(self, url: str, response: Response) -> bool:
        """Academic-specific link filtering."""
        
        if not super().should_follow_link(url, response):
            return False
        
        # Prioritize research content
        academic_patterns = [
            r'/paper/',
            r'/publication/',
            r'/research/',
            r'/journal/',
            r'/article/',
            r'\.pdf$',  # Allow PDFs for academic content
        ]
        
        return any(re.search(pattern, url) for pattern in academic_patterns)
    
    def should_follow_link(self, url: str, response: Response) -> bool:
        """Override to allow PDFs for academic content."""
        
        # Call parent method but allow PDFs
        if url.lower().endswith('.pdf'):
            return True
        
        return super().should_follow_link(url, response)

