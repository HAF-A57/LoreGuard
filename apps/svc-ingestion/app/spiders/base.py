"""
LoreGuard Ingestion Service - Base Spider

Base spider class with common functionality for all LoreGuard spiders.
"""

import logging
import re
import json
import html as html_module
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
        'CONCURRENT_REQUESTS': 8,  # Limit concurrent requests for better control
    }
    
    def __init__(self, source_id: str = None, max_depth: int = 3, max_artifacts: int = 0, start_urls: str = None, allowed_domains: str = None, job_id: str = None, config: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.source_id = source_id or getattr(self, 'source_id', 'unknown')
        self.max_depth = int(max_depth) if max_depth else 3
        self.max_artifacts = int(max_artifacts) if max_artifacts else 0  # 0 = unlimited
        self.crawl_job_id = job_id or kwargs.get('job_id', f"{self.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        
        # Parse start_urls from comma-separated string or use class attribute
        if start_urls:
            # Scrapy passes arguments as strings, split comma-separated values
            self.start_urls = [url.strip() for url in str(start_urls).split(',') if url.strip()]
        elif not hasattr(self, 'start_urls') or not self.start_urls:
            self.start_urls = []
        
        # Parse allowed_domains from comma-separated string
        if allowed_domains:
            parsed_domains = [domain.strip() for domain in str(allowed_domains).split(',') if domain.strip()]
            self.allowed_domains = parsed_domains if parsed_domains else getattr(self, 'allowed_domains', [])
        elif not hasattr(self, 'allowed_domains'):
            self.allowed_domains = []
        
        # Parse config from JSON string if provided, otherwise use dict or empty dict
        config_dict = {}
        if config:
            if isinstance(config, str):
                try:
                    config_dict = json.loads(config)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse config JSON: {config}")
                    config_dict = {}
            elif isinstance(config, dict):
                config_dict = config
        
        # Extract document extraction configuration from config dict
        extraction_config = config_dict.get('extraction', {}) if config_dict else {}
        self.extract_pdfs = extraction_config.get('extract_pdfs', True)
        self.extract_documents = extraction_config.get('extract_documents', True)
        self.allowed_document_types = extraction_config.get('allowed_document_types', ['pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'])
        self.max_document_size_mb = extraction_config.get('max_document_size_mb', 50)
        
        # Statistics tracking
        self.stats = {
            'pages_crawled': 0,
            'documents_found': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }
        
        # Link extractor for finding new URLs
        # Note: We don't deny PDF/document extensions here because we want to follow them
        # and let should_follow_link() decide based on extraction config
        self.link_extractor = LinkExtractor(
            allow_domains=self.allowed_domains,
            deny_extensions=['jpg', 'jpeg', 'png', 'gif', 'svg', 'ico', 'css', 'js', 'woff', 'woff2', 'ttf', 'eot'],
            canonicalize=True,
            unique=True
        )
        
        logger.info(f"Initialized spider {self.name} for source {self.source_id} with {len(self.start_urls)} start URLs")
        logger.info(f"  Max depth: {self.max_depth}, Max artifacts: {self.max_artifacts if self.max_artifacts > 0 else 'unlimited'}")
        logger.info(f"  Extract PDFs: {self.extract_pdfs}, Extract Documents: {self.extract_documents}, Max size: {self.max_document_size_mb}MB")
    
    def start_requests(self) -> Generator[Request, None, None]:
        """Generate initial requests."""
        
        start_urls = getattr(self, 'start_urls', [])
        if not start_urls:
            logger.error(f"No start URLs configured for spider {self.name} (source: {self.source_id})")
            return
        
        logger.info(f"Starting crawl with {len(start_urls)} start URLs for source {self.source_id}")
        
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
        
        # Check if this is a document response (PDF, DOCX, etc.) by Content-Type
        # This handles cases where URLs don't have file extensions but serve documents
        if self.is_document_response(response):
            # Process as document immediately
            yield from self.process_document(response)
            return
        
        # Skip non-HTML content for link extraction
        if not self.is_html_response(response):
            # But still process as potential document
            yield from self.process_document(response)
            return
        
        # Safety check: ensure response can be parsed as text
        try:
            # Test if we can use CSS selectors (will fail if content isn't text)
            _ = response.css('html').get()
        except Exception as e:
            logger.warning(f"Cannot parse response as HTML: {e}. Skipping content extraction for {response.url}")
            return
        
        # Extract document links from meta tags and HTML attributes BEFORE following regular links
        # This ensures we catch high-value document links that might be missed by link following
        yield from self.extract_document_links_from_page(response)
        
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
            try:
                content = response.css(selector).get()
                if content:
                    text_content = response.css(selector + ' ::text').getall()
                    text_content = ' '.join(text_content).strip()
                    break
            except Exception as e:
                logger.warning(f"Error extracting content with selector {selector}: {e}")
                continue
        
        if not text_content:
            # Fallback to body text
            text_content = ' '.join(response.css('body ::text').getall()).strip()
        
        # Only process if we have meaningful content
        if len(text_content) > 100:
            yield from self.process_document(response, text_content)
    
    def extract_document_links_from_page(self, response: Response) -> Generator:
        """Extract document download links from HTML page using multiple detection methods."""
        
        try:
            # Method 1: Extract from meta tags (common in academic repositories)
            meta_selectors = [
                'meta[name="citation_pdf_url"]::attr(content)',
                'meta[name="bepress_citation_pdf_url"]::attr(content)',
                'meta[property="og:url"][content*="pdf"]::attr(content)',
                'link[rel="alternate"][type="application/pdf"]::attr(href)',
            ]
            
            for selector in meta_selectors:
                try:
                    urls = response.css(selector).getall()
                    for url in urls:
                        if url:
                            # Clean and normalize URL
                            url = url.strip()
                            # Decode HTML entities (e.g., &amp; -> &)
                            url = html_module.unescape(url)
                            if not url.startswith('http'):
                                url = urljoin(response.url, url)
                            
                            if self.should_follow_link(url, response):
                                logger.info(f"Found document link from meta tag: {url}")
                                yield Request(
                                    url=url,
                                    callback=self.parse,
                                    meta={
                                        'source_id': self.source_id,
                                        'depth': response.meta.get('depth', 0) + 1,
                                        'job_id': self.crawl_job_id,
                                        'link_text': 'meta_tag_document_link',
                                        'dont_redirect': False,  # Allow redirects for document links
                                    },
                                    priority=10  # Higher priority for document links
                                )
                except Exception as e:
                    logger.debug(f"Error extracting meta tag links with selector {selector}: {e}")
                    continue
            
            # Method 2: Extract links with download attribute or PDF-related attributes
            download_link_selectors = [
                'a[download]::attr(href)',
                'a[type*="pdf"]::attr(href)',
                'a[type*="application/pdf"]::attr(href)',
                'a[aria-label*="download" i]::attr(href)',
                'a[aria-label*="pdf" i]::attr(href)',
                'a[data-download]::attr(href)',
                'a[data-file]::attr(href)',
            ]
            
            for selector in download_link_selectors:
                try:
                    urls = response.css(selector).getall()
                    for url in urls:
                        if url:
                            url = url.strip()
                            # Decode HTML entities
                            url = html_module.unescape(url)
                            if not url.startswith('http'):
                                url = urljoin(response.url, url)
                            
                            if self.should_follow_link(url, response):
                                logger.info(f"Found document link with download attribute: {url}")
                                yield Request(
                                    url=url,
                                    callback=self.parse,
                                    meta={
                                        'source_id': self.source_id,
                                        'depth': response.meta.get('depth', 0) + 1,
                                        'job_id': self.crawl_job_id,
                                        'link_text': 'download_attribute_link',
                                    },
                                    priority=10
                                )
                except Exception as e:
                    logger.debug(f"Error extracting download attribute links: {e}")
                    continue
            
            # Method 3: Extract links with download-related class names or IDs
            download_class_selectors = [
                'a.download::attr(href)',
                'a.pdf-download::attr(href)',
                'a.document-download::attr(href)',
                'a.file-download::attr(href)',
                'a#download::attr(href)',
                'a#pdf-download::attr(href)',
                'button.download a::attr(href)',
                'button.pdf-download a::attr(href)',
            ]
            
            for selector in download_class_selectors:
                try:
                    urls = response.css(selector).getall()
                    for url in urls:
                        if url:
                            url = url.strip()
                            # Decode HTML entities
                            url = html_module.unescape(url)
                            if not url.startswith('http'):
                                url = urljoin(response.url, url)
                            
                            if self.should_follow_link(url, response):
                                logger.info(f"Found document link with download class: {url}")
                                yield Request(
                                    url=url,
                                    callback=self.parse,
                                    meta={
                                        'source_id': self.source_id,
                                        'depth': response.meta.get('depth', 0) + 1,
                                        'job_id': self.crawl_job_id,
                                        'link_text': 'download_class_link',
                                    },
                                    priority=10
                                )
                except Exception as e:
                    logger.debug(f"Error extracting download class links: {e}")
                    continue
            
            # Method 4: Extract links based on anchor text patterns (download keywords)
            # This is more expensive, so we do it last
            if self.extract_pdfs or self.extract_documents:
                download_keywords = ['download', 'pdf', 'document', 'paper', 'report', 'full text', 'view pdf']
                all_links = response.css('a::attr(href)').getall()
                all_texts = response.css('a::text').getall()
                
                for link, text in zip(all_links, all_texts):
                    if link and text:
                        text_lower = text.lower().strip()
                        # Check if anchor text contains download keywords
                        if any(keyword in text_lower for keyword in download_keywords):
                            url = link.strip()
                            # Decode HTML entities
                            url = html_module.unescape(url)
                            if not url.startswith('http'):
                                url = urljoin(response.url, url)
                            
                            if self.should_follow_link(url, response):
                                logger.info(f"Found document link from anchor text '{text}': {url}")
                                yield Request(
                                    url=url,
                                    callback=self.parse,
                                    meta={
                                        'source_id': self.source_id,
                                        'depth': response.meta.get('depth', 0) + 1,
                                        'job_id': self.crawl_job_id,
                                        'link_text': text.strip(),
                                    },
                                    priority=8  # Slightly lower priority than explicit attributes
                                )
        
        except Exception as e:
            logger.warning(f"Error extracting document links from page {response.url}: {e}")
            # Don't fail the entire page if link extraction fails
    
    def process_document(self, response: Response, text_content: str = None) -> Generator:
        """Process a document and extract metadata."""
        
        # Check max_artifacts limit BEFORE incrementing to ensure we process exactly max_artifacts
        # This ensures the last document (the 100th) gets fully processed
        if self.max_artifacts > 0 and self.stats['documents_found'] >= self.max_artifacts:
            logger.info(f"Reached max_artifacts limit ({self.max_artifacts}). Closing spider.")
            # Use Scrapy's close spider mechanism
            from scrapy.exceptions import CloseSpider
            raise CloseSpider(f'max_artifacts_reached_{self.max_artifacts}')
        
        # Check file size limit for documents
        content_length = len(response.body)
        max_size_bytes = self.max_document_size_mb * 1024 * 1024
        
        # Only check size for actual documents (not HTML pages)
        if self.is_document_response(response) and content_length > max_size_bytes:
            size_mb = content_length / 1024 / 1024
            logger.warning(
                f"Skipping document {response.url}: "
                f"size {size_mb:.2f}MB exceeds limit {self.max_document_size_mb}MB"
            )
            return
        
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
        
        # Extract links using the link extractor (with error handling for non-text responses)
        try:
            links = self.link_extractor.extract_links(response)
        except (AttributeError, TypeError) as e:
            logger.warning(f"Cannot extract links from {response.url}: {e} (possibly binary content)")
            return
        
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
        
        url_lower = url.lower()
        
        # Check document extraction configuration
        if self.extract_documents:
            # Build list of document extensions to check
            document_extensions = [f'.{ext}' for ext in self.allowed_document_types]
            
            # Check if URL is a document type we want to extract (by extension)
            if any(url_lower.endswith(ext) for ext in document_extensions):
                # Special handling for PDFs
                if url_lower.endswith('.pdf'):
                    return self.extract_pdfs
                # Allow other document types if extract_documents is True
                return True
            
            # Check for common document download URL patterns (CGI scripts, download handlers, etc.)
            # These URLs may serve PDFs/documents even without file extensions
            # Based on comprehensive research of academic repositories and document serving patterns
            document_url_patterns = [
                # CGI scripts (common in academic repositories)
                r'viewcontent',      # Digital Commons, bepress (viewcontent.cgi)
                r'viewfile',         # Alternative view file handler
                r'getfile',          # Get file handler
                r'servefile',        # Serve file handler
                r'serve',            # Serve file handler
                
                # PHP/ASP handlers
                r'file\.php',        # PHP file handlers
                r'file\.asp',        # ASP file handlers
                r'file\.aspx',       # ASPX file handlers
                r'download\.php',    # PHP download handlers
                r'download\.asp',    # ASP download handlers
                r'download\.aspx',   # ASPX download handlers
                r'document\.php',    # PHP document handlers
                r'pdf\.php',         # PHP PDF handlers
                r'get\.php',         # PHP get handlers
                r'fetch\.php',       # PHP fetch handlers
                
                # API endpoints
                r'/api/download',    # API download endpoints
                r'/api/file',       # API file endpoints
                r'/api/document',   # API document endpoints
                r'/rest/api/document', # REST API document endpoints
                
                # Path patterns
                r'/download/',       # Download directory
                r'/file/',          # File directory
                r'/document/',      # Document directory
                r'/pdf/',           # PDF directory
                r'/documents/',     # Documents directory
                r'/files/',         # Files directory
                r'/publications/',  # Publications directory
                r'/papers/',        # Papers directory
                
                # DSpace patterns
                r'/bitstream/handle/', # DSpace bitstreams
                r'/xmlui/bitstream/handle/', # DSpace XML UI bitstreams
                
                # EPrints patterns
                r'/id/eprint/',    # EPrints document IDs
                r'/eprint/',       # EPrints documents
                
                # Query parameter patterns
                r'[?&]download=',  # Download query parameter
                r'[?&]file=',      # File query parameter
                r'[?&]document=',  # Document query parameter
                r'[?&]pdf=',       # PDF query parameter
                r'[?&]id=.*pdf',   # ID parameter with PDF in value
                
                # PDF with query parameters
                r'\.pdf\?',        # PDF with query parameters
                r'\.pdf&',         # PDF with query parameters (alternative)
            ]
            
            # Check if URL matches document download patterns
            if self.extract_pdfs and any(re.search(pattern, url_lower) for pattern in document_url_patterns):
                # Also check if the link text or surrounding context suggests it's a PDF/download
                # We'll follow it and let Content-Type detection handle it
                return True
        
        # Skip certain file types if document extraction is disabled
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
        if any(url_lower.endswith(ext) for ext in skip_extensions):
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
    
    def is_document_response(self, response: Response) -> bool:
        """Check if response is a document (PDF, DOCX, etc.) based on Content-Type header."""
        
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        
        # Check Content-Type header first
        document_mime_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # PPTX
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # XLSX
            'application/vnd.ms-powerpoint',
            'application/vnd.ms-excel',
            'application/rtf',
        ]
        
        if any(doc_type in content_type for doc_type in document_mime_types):
            return True
        
        # Fallback to URL extension check
        url_lower = response.url.lower()
        document_extensions = [f'.{ext}' for ext in self.allowed_document_types]
        return any(url_lower.endswith(ext) for ext in document_extensions)
    
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
        """Academic-specific link filtering - allows PDFs and prioritizes research content."""
        
        # Allow PDFs for academic content if extraction is enabled
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            # Check if PDF extraction is enabled (defaults to True if not set)
            extract_pdfs = getattr(self, 'extract_pdfs', True)
            if extract_pdfs:
                return True
        
        # Call parent method for other links
        if not super().should_follow_link(url, response):
            return False
        
        # Prioritize research content
        academic_patterns = [
            r'/paper/',
            r'/publication/',
            r'/research/',
            r'/journal/',
            r'/article/',
        ]
        
        return any(re.search(pattern, url) for pattern in academic_patterns)

