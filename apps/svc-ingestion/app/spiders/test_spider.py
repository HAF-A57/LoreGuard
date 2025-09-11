"""
LoreGuard Test Spider

Simple spider for testing the ingestion system functionality.
"""

from app.spiders.base import BaseLoreGuardSpider


class TestSpider(BaseLoreGuardSpider):
    """
    Simple test spider for validating the ingestion system.
    """
    
    name = 'test'
    allowed_domains = ['httpbin.org', 'example.com']
    start_urls = [
        'https://httpbin.org/html',
        'https://example.com',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': False,  # Disable for testing
        'HTTPCACHE_ENABLED': False,     # Disable caching for testing
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_depth = 1  # Limit depth for testing
        
    def should_follow_link(self, url: str, response) -> bool:
        """Override to be more restrictive for testing."""
        
        # Only follow links within allowed domains
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        return parsed.netloc in self.allowed_domains

