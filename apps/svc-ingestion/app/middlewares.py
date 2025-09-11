"""
LoreGuard Ingestion Service - Scrapy Middlewares

Custom middlewares for anti-bot detection, proxy rotation, content validation,
and source-specific processing.
"""

import random
import time
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import scrapy
from scrapy import signals
from scrapy.http import HtmlResponse, Request, Response
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from fake_useragent import UserAgent
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.items import SourceConfigItem


logger = logging.getLogger(__name__)


class RotatingUserAgentMiddleware:
    """
    Middleware to rotate User-Agent headers to avoid detection.
    """
    
    def __init__(self, user_agent_list: Optional[List[str]] = None):
        self.user_agent_list = user_agent_list or []
        self.ua = UserAgent()
        
    @classmethod
    def from_crawler(cls, crawler):
        # Try to load user agents from file
        user_agent_list = []
        user_agent_file = crawler.settings.get('USER_AGENT_LIST_PATH')
        
        if user_agent_file:
            try:
                with open(user_agent_file, 'r') as f:
                    user_agent_list = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                logger.warning(f"User agent file not found: {user_agent_file}")
        
        return cls(user_agent_list)
    
    def process_request(self, request: Request, spider) -> None:
        """Set a random User-Agent for each request."""
        if self.user_agent_list:
            ua = random.choice(self.user_agent_list)
        else:
            # Fallback to fake-useragent
            try:
                ua = self.ua.random
            except:
                ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        request.headers['User-Agent'] = ua
        return None


class ProxyRotationMiddleware:
    """
    Middleware to rotate proxy servers for requests.
    """
    
    def __init__(self, proxy_list: List[str]):
        self.proxy_list = proxy_list
        self.proxy_index = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        proxy_list = []
        proxy_file = crawler.settings.get('ROTATING_PROXY_LIST_PATH')
        
        if proxy_file:
            try:
                with open(proxy_file, 'r') as f:
                    proxy_list = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                logger.warning(f"Proxy file not found: {proxy_file}")
        
        if not proxy_list:
            raise NotConfigured("No proxy list provided")
        
        return cls(proxy_list)
    
    def process_request(self, request: Request, spider) -> None:
        """Set a rotating proxy for each request."""
        if self.proxy_list:
            proxy = self.proxy_list[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
            request.meta['proxy'] = proxy
        
        return None


class AntiDetectionMiddleware:
    """
    Middleware to add anti-detection measures.
    """
    
    def __init__(self):
        self.session_cookies = {}
        
    def process_request(self, request: Request, spider) -> None:
        """Add anti-detection headers and behaviors."""
        
        # Add realistic headers
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
        # Add random delay variation
        delay = random.uniform(0.5, 2.0)
        request.meta['download_delay'] = delay
        
        return None
    
    def process_response(self, request: Request, response: Response, spider) -> Response:
        """Process response for anti-detection."""
        
        # Store cookies for session persistence
        domain = urlparse(request.url).netloc
        if 'Set-Cookie' in response.headers:
            self.session_cookies[domain] = response.headers.getlist('Set-Cookie')
        
        return response


class SourceConfigMiddleware:
    """
    Middleware to apply source-specific configurations.
    """
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.source_configs = {}
        
    @classmethod
    def from_crawler(cls, crawler):
        database_url = crawler.settings.get('DATABASE_URL')
        if not database_url:
            raise NotConfigured("DATABASE_URL not configured")
        
        return cls(database_url)
    
    def process_request(self, request: Request, spider) -> None:
        """Apply source-specific configuration to requests."""
        
        # Get source configuration
        source_id = request.meta.get('source_id')
        if not source_id:
            return None
        
        config = self._get_source_config(source_id)
        if not config:
            return None
        
        # Apply source-specific settings
        if config.get('download_delay'):
            request.meta['download_delay'] = config['download_delay']
        
        if config.get('custom_headers'):
            request.headers.update(config['custom_headers'])
        
        # Apply JavaScript rendering if required
        if config.get('javascript_required'):
            request.meta['playwright'] = True
            request.meta['playwright_page_methods'] = [
                'wait_for_load_state',
                'wait_for_timeout:2000'  # Wait 2 seconds for dynamic content
            ]
        
        return None
    
    def _get_source_config(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source configuration from database."""
        if source_id in self.source_configs:
            return self.source_configs[source_id]
        
        try:
            session = self.Session()
            # This would query the actual Source model
            # For now, return a default config
            config = {
                'download_delay': 2.0,
                'javascript_required': False,
                'custom_headers': {}
            }
            self.source_configs[source_id] = config
            return config
        except Exception as e:
            logger.error(f"Error fetching source config for {source_id}: {e}")
            return None
        finally:
            session.close()


class DuplicateFilterMiddleware:
    """
    Middleware to filter duplicate requests and responses.
    """
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.seen_urls = set()
        
    @classmethod
    def from_crawler(cls, crawler):
        redis_url = crawler.settings.get('REDIS_URL')
        if not redis_url:
            raise NotConfigured("REDIS_URL not configured")
        
        return cls(redis_url)
    
    def process_request(self, request: Request, spider) -> Optional[Request]:
        """Filter duplicate requests."""
        
        url_hash = hash(request.url)
        redis_key = f"seen_urls:{spider.name}:{url_hash}"
        
        # Check if URL was already processed
        if self.redis_client.exists(redis_key):
            logger.debug(f"Duplicate URL filtered: {request.url}")
            raise IgnoreRequest(f"Duplicate URL: {request.url}")
        
        # Mark URL as seen (expire after 24 hours)
        self.redis_client.setex(redis_key, 86400, "1")
        
        return None


class ContentValidationMiddleware:
    """
    Middleware to validate content before processing.
    """
    
    def __init__(self, max_content_size: int, supported_content_types: List[str]):
        self.max_content_size = max_content_size
        self.supported_content_types = supported_content_types
        
    @classmethod
    def from_crawler(cls, crawler):
        max_size = crawler.settings.get('MAX_CONTENT_SIZE', 50 * 1024 * 1024)
        supported_types = crawler.settings.get('SUPPORTED_CONTENT_TYPES', [])
        
        return cls(max_size, supported_types)
    
    def process_spider_input(self, response: Response, spider):
        """Validate response content before spider processing."""
        
        # Check content size
        content_length = len(response.body)
        if content_length > self.max_content_size:
            logger.warning(f"Content too large ({content_length} bytes): {response.url}")
            return []
        
        # Check content type
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        if self.supported_content_types:
            if not any(ct in content_type for ct in self.supported_content_types):
                logger.debug(f"Unsupported content type ({content_type}): {response.url}")
                return []
        
        # Check minimum content length
        min_length = spider.settings.get('MIN_CONTENT_LENGTH', 100)
        if content_length < min_length:
            logger.debug(f"Content too short ({content_length} bytes): {response.url}")
            return []
        
        return None


class CustomRetryMiddleware(RetryMiddleware):
    """
    Enhanced retry middleware with exponential backoff and custom logic.
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 3)
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST', -1)
        
    def retry(self, request: Request, reason: str, spider) -> Optional[Request]:
        """Enhanced retry logic with exponential backoff."""
        
        retries = request.meta.get('retry_times', 0) + 1
        
        if retries <= self.max_retry_times:
            logger.debug(f"Retrying {request.url} (attempt {retries}/{self.max_retry_times}): {reason}")
            
            # Exponential backoff
            delay = (2 ** retries) + random.uniform(0, 1)
            
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.meta['download_delay'] = delay
            retryreq.priority = request.priority + self.priority_adjust
            
            return retryreq
        else:
            logger.error(f"Gave up retrying {request.url} (failed {retries} times): {reason}")
            return None


class ResponseValidationMiddleware:
    """
    Middleware to validate responses and handle errors.
    """
    
    def process_response(self, request: Request, response: Response, spider) -> Response:
        """Validate response and handle common issues."""
        
        # Check for blocked/captcha pages
        if self._is_blocked_response(response):
            logger.warning(f"Blocked response detected: {response.url}")
            # Could implement captcha solving or proxy switching here
            raise IgnoreRequest("Response appears to be blocked")
        
        # Check for empty or invalid responses
        if not response.body or len(response.body) < 10:
            logger.warning(f"Empty or invalid response: {response.url}")
            raise IgnoreRequest("Empty response")
        
        # Log successful responses
        if response.status == 200:
            logger.debug(f"Successfully processed: {response.url} ({len(response.body)} bytes)")
        
        return response
    
    def _is_blocked_response(self, response: Response) -> bool:
        """Detect if response indicates blocking or captcha."""
        
        # Check for common blocking indicators
        body_text = response.text.lower() if hasattr(response, 'text') else ""
        
        blocking_indicators = [
            'captcha',
            'blocked',
            'access denied',
            'rate limit',
            'too many requests',
            'cloudflare',
            'please verify you are human'
        ]
        
        return any(indicator in body_text for indicator in blocking_indicators)


class MonitoringMiddleware:
    """
    Middleware for collecting metrics and monitoring.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.response_count = 0
        self.error_count = 0
        
    @classmethod
    def from_crawler(cls, crawler):
        o = cls()
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o
    
    def process_request(self, request: Request, spider) -> None:
        """Track request metrics."""
        self.request_count += 1
        request.meta['request_start_time'] = time.time()
        return None
    
    def process_response(self, request: Request, response: Response, spider) -> Response:
        """Track response metrics."""
        self.response_count += 1
        
        # Calculate response time
        start_time = request.meta.get('request_start_time')
        if start_time:
            response_time = time.time() - start_time
            spider.crawler.stats.set_value(f'response_time/{response.status}', response_time)
        
        return response
    
    def process_exception(self, request: Request, exception: Exception, spider):
        """Track error metrics."""
        self.error_count += 1
        spider.crawler.stats.inc_value('errors/total')
        spider.crawler.stats.inc_value(f'errors/{exception.__class__.__name__}')
        return None
    
    def spider_opened(self, spider):
        """Initialize spider metrics."""
        logger.info(f"Spider {spider.name} opened")
        spider.crawler.stats.set_value('spider_start_time', self.start_time)
    
    def spider_closed(self, spider):
        """Log final spider metrics."""
        duration = time.time() - self.start_time
        logger.info(f"Spider {spider.name} closed after {duration:.2f}s")
        logger.info(f"Requests: {self.request_count}, Responses: {self.response_count}, Errors: {self.error_count}")
        
        spider.crawler.stats.set_value('spider_duration', duration)
        spider.crawler.stats.set_value('requests_total', self.request_count)
        spider.crawler.stats.set_value('responses_total', self.response_count)
        spider.crawler.stats.set_value('errors_total', self.error_count)

