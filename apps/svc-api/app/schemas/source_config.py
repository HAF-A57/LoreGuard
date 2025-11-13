"""
Source Configuration Schemas

Comprehensive configuration schemas for different source types.
Defines all user-configurable parameters for web scraping, RSS feeds, and APIs.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class ScheduleType(str, Enum):
    """Schedule type options"""
    MANUAL = "manual"
    INTERVAL = "interval"
    CRON = "cron"
    RSS_POLL = "rss-poll"


class AuthType(str, Enum):
    """Authentication type options"""
    NONE = "none"
    FORM = "form"
    BASIC = "basic"
    BEARER = "bearer"
    APIKEY = "apikey"
    OAUTH2 = "oauth2"


class RetryBackoffStrategy(str, Enum):
    """Retry backoff strategy"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class PaginationType(str, Enum):
    """API pagination type"""
    NONE = "none"
    OFFSET = "offset"
    CURSOR = "cursor"
    PAGE = "page"


class CrawlScopeConfig(BaseModel):
    """Crawl scope and limits configuration"""
    max_depth: int = Field(default=3, ge=0, le=10, description="Maximum link depth to crawl")
    max_artifacts: int = Field(default=100, ge=0, description="Maximum artifacts per crawl (0=unlimited)")
    max_pages_per_domain: int = Field(default=1000, ge=0, description="Maximum pages per domain per job")
    max_crawl_time_minutes: int = Field(default=60, ge=1, description="Maximum crawl time in minutes")


class PolitenessConfig(BaseModel):
    """Request rate and politeness configuration"""
    download_delay: float = Field(default=2.0, ge=0.0, le=60.0, description="Base delay between requests (seconds)")
    randomize_download_delay: float = Field(default=0.5, ge=0.0, le=1.0, description="Randomization factor (0-1)")
    concurrent_requests: int = Field(default=16, ge=1, le=100, description="Total concurrent requests")
    concurrent_requests_per_domain: int = Field(default=2, ge=1, le=20, description="Concurrent requests per domain")
    autothrottle_enabled: bool = Field(default=True, description="Enable adaptive rate limiting")
    autothrottle_start_delay: float = Field(default=1.0, ge=0.1, description="Initial throttle delay")
    autothrottle_max_delay: float = Field(default=10.0, ge=1.0, description="Maximum throttle delay")
    autothrottle_target_concurrency: float = Field(default=2.0, ge=0.1, description="Target concurrency")


class FilteringConfig(BaseModel):
    """URL filtering and pattern matching"""
    allowed_domains: List[str] = Field(default_factory=list, description="Whitelist of domains to crawl")
    denied_domains: List[str] = Field(default_factory=list, description="Blacklist of domains to exclude")
    allowed_url_patterns: List[str] = Field(default_factory=list, description="Regex patterns for URLs to include")
    denied_url_patterns: List[str] = Field(
        default_factory=lambda: ["/admin/.*", "/login/.*", "/cart/.*"],
        description="Regex patterns for URLs to exclude"
    )
    allowed_file_types: List[str] = Field(
        default_factory=lambda: ["text/html", "application/pdf", "application/json"],
        description="Allowed MIME types or extensions"
    )
    max_file_size_mb: int = Field(default=50, ge=1, le=1000, description="Maximum file size in MB")


class JavaScriptConfig(BaseModel):
    """JavaScript rendering configuration"""
    javascript_required: bool = Field(default=False, description="Enable Playwright for JavaScript sites")
    javascript_wait_time: int = Field(default=2000, ge=0, le=10000, description="Wait time for JS rendering (ms)")
    wait_for_selectors: List[str] = Field(default_factory=list, description="CSS selectors to wait for")


class AuthenticationConfig(BaseModel):
    """Authentication configuration"""
    authentication_required: bool = Field(default=False, description="Site requires authentication")
    auth_type: AuthType = Field(default=AuthType.NONE, description="Authentication method")
    login_url: Optional[str] = Field(None, description="Login page URL")
    username: Optional[str] = Field(None, description="Username/email (encrypted)")
    password: Optional[str] = Field(None, description="Password (encrypted)")
    api_key: Optional[str] = Field(None, description="API key (encrypted)")
    api_key_header: Optional[str] = Field(None, description="Header name for API key")
    bearer_token: Optional[str] = Field(None, description="Bearer token (encrypted)")
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers")
    user_agent: Optional[str] = Field(None, description="Custom User-Agent string")
    rotate_user_agent: bool = Field(default=False, description="Rotate User-Agent strings")


class RetryConfig(BaseModel):
    """Retry and error handling configuration"""
    retry_times: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    retry_http_codes: List[int] = Field(
        default_factory=lambda: [500, 502, 503, 504, 408, 429],
        description="HTTP status codes that trigger retry"
    )
    retry_backoff_strategy: RetryBackoffStrategy = Field(
        default=RetryBackoffStrategy.EXPONENTIAL,
        description="Retry backoff strategy"
    )
    download_timeout: int = Field(default=30, ge=5, le=300, description="Request timeout in seconds")


class ComplianceConfig(BaseModel):
    """Compliance and blocker handling configuration"""
    # Robots.txt settings
    obey_robots_txt: bool = Field(default=True, description="Respect robots.txt directives (recommended)")
    robots_txt_user_agent: str = Field(default="*", description="User-Agent string for robots.txt check")
    robots_txt_warning_only: bool = Field(default=False, description="Warn but don't block when robots.txt disallows")
    
    # Blocker detection
    detect_blockers: bool = Field(default=True, description="Automatically detect common blockers (Cloudflare, CAPTCHA, etc.)")
    notify_on_blocker: bool = Field(default=True, description="Notify admin when blocker detected")
    
    # Blocker response strategies
    blocker_response_strategy: Literal["abort", "retry", "bypass", "notify"] = Field(
        default="notify",
        description="Default response when blocker detected: abort (stop), retry (retry with different approach), bypass (attempt bypass), notify (notify and wait)"
    )
    
    # Per-blocker-type handling
    handle_403: Literal["abort", "retry", "bypass", "notify"] = Field(
        default="retry",
        description="Response to 403 Forbidden errors"
    )
    handle_429: Literal["abort", "retry", "bypass", "notify"] = Field(
        default="retry",
        description="Response to 429 Rate Limited errors"
    )
    handle_cloudflare: Literal["abort", "bypass", "notify"] = Field(
        default="notify",
        description="Response to Cloudflare challenge pages"
    )
    handle_captcha: Literal["abort", "notify", "pause"] = Field(
        default="pause",
        description="Response to CAPTCHA challenges"
    )
    
    # Bypass options
    allow_proxy_bypass: bool = Field(
        default=False,
        description="Allow proxy rotation to bypass IP blocks (may violate ToS)"
    )
    allow_browser_bypass: bool = Field(
        default=False,
        description="Allow headless browser to bypass JavaScript challenges (may violate ToS)"
    )
    allow_user_agent_rotation: bool = Field(
        default=True,
        description="Allow User-Agent rotation to avoid detection"
    )


class RSSConfig(BaseModel):
    """RSS/Feed specific configuration"""
    feed_update_frequency_minutes: int = Field(default=60, ge=1, description="Feed check frequency in minutes")
    max_feed_items: int = Field(default=100, ge=1, description="Maximum items per feed check")
    feed_item_retention_days: int = Field(default=30, ge=1, description="Days to retain feed items")
    follow_feed_links: bool = Field(default=True, description="Crawl URLs from feed items")


class APIConfig(BaseModel):
    """API-specific configuration"""
    api_base_url: str = Field(default="", description="Base URL for API endpoints")
    api_auth_type: AuthType = Field(default=AuthType.NONE, description="API authentication method")
    api_endpoints: List[str] = Field(default_factory=list, description="API endpoints to call")
    api_request_method: Literal["GET", "POST"] = Field(default="GET", description="HTTP method")
    api_request_body: Dict[str, Any] = Field(default_factory=dict, description="Request body for POST")
    api_rate_limit_requests: int = Field(default=100, ge=1, description="Max requests per window")
    api_rate_limit_window_seconds: int = Field(default=60, ge=1, description="Rate limit time window")
    api_pagination_type: PaginationType = Field(default=PaginationType.NONE, description="Pagination method")
    pagination_param_name: Optional[str] = Field(None, description="Pagination parameter name")
    pagination_start_value: Optional[int] = Field(None, description="Starting pagination value")
    pagination_increment: Optional[int] = Field(None, description="Pagination increment")
    pagination_max_pages: Optional[int] = Field(None, ge=1, description="Maximum pages to fetch")


class ExtractionConfig(BaseModel):
    """Content extraction configuration"""
    content_selectors: Dict[str, str] = Field(default_factory=dict, description="CSS/XPath selectors for content")
    extract_images: bool = Field(default=False, description="Download and process images")
    extract_pdfs: bool = Field(default=True, description="Download and process PDF documents found during crawling")
    extract_documents: bool = Field(default=True, description="Download and process document files (PDF, DOCX, DOC, PPTX, XLSX, etc.)")
    allowed_document_types: List[str] = Field(
        default_factory=lambda: ['pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'],
        description="List of document types to extract (extensions without dot, e.g., 'pdf', 'docx')"
    )
    max_document_size_mb: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum document file size in MB (documents larger than this will be skipped)"
    )
    extract_metadata: bool = Field(default=True, description="Extract document metadata")
    min_content_length: int = Field(default=100, ge=0, description="Minimum content length (characters)")


class SchedulingConfig(BaseModel):
    """Scheduling and automation configuration"""
    schedule_type: ScheduleType = Field(default=ScheduleType.MANUAL, description="Schedule type")
    schedule_value: Optional[str] = Field(None, description="Schedule configuration (cron or interval)")
    crawl_hours: List[int] = Field(default_factory=list, description="Hours of day to crawl (0-23)")


class ProxyConfig(BaseModel):
    """Proxy configuration"""
    use_proxies: bool = Field(default=False, description="Enable proxy rotation")
    proxy_list: List[str] = Field(default_factory=list, description="Proxy server URLs")
    proxy_rotation_strategy: Literal["round-robin", "random", "failover"] = Field(
        default="round-robin",
        description="Proxy selection strategy"
    )


class SourceConfig(BaseModel):
    """
    Comprehensive source configuration schema
    
    Combines all configuration categories into a single schema.
    Different source types will use different subsets of these parameters.
    """
    # Start URLs (required for web sources)
    start_urls: List[str] = Field(default_factory=list, description="Starting URLs for crawl")
    
    # Configuration categories
    crawl_scope: CrawlScopeConfig = Field(default_factory=CrawlScopeConfig, description="Crawl scope settings")
    politeness: PolitenessConfig = Field(default_factory=PolitenessConfig, description="Politeness settings")
    filtering: FilteringConfig = Field(default_factory=FilteringConfig, description="URL filtering")
    javascript: JavaScriptConfig = Field(default_factory=JavaScriptConfig, description="JavaScript settings")
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig, description="Auth settings")
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Retry settings")
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig, description="Compliance settings")
    rss: Optional[RSSConfig] = Field(None, description="RSS/Feed settings (for feed sources)")
    api: Optional[APIConfig] = Field(None, description="API settings (for API sources)")
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig, description="Extraction settings")
    scheduling: SchedulingConfig = Field(default_factory=SchedulingConfig, description="Scheduling settings")
    proxy: ProxyConfig = Field(default_factory=ProxyConfig, description="Proxy settings")
    
    @validator("start_urls")
    def validate_start_urls(cls, v, values):
        """Validate start URLs are provided for web sources"""
        # Note: This validation happens at the Source level, not here
        return v
    
    @validator("allowed_domains", always=True, pre=True)
    def validate_allowed_domains(cls, v, values):
        """Extract allowed_domains from filtering config if present"""
        if isinstance(values, dict) and "filtering" in values:
            return values["filtering"].get("allowed_domains", v)
        return v
    
    class Config:
        extra = "forbid"  # Don't allow extra fields


def get_default_config_for_type(source_type: str) -> Dict[str, Any]:
    """
    Get default configuration for a specific source type
    
    Args:
        source_type: Type of source (web, rss, api, etc.)
        
    Returns:
        Dictionary with default configuration values
    """
    base_config = SourceConfig().dict()
    
    if source_type in ["rss", "feed"]:
        base_config["rss"] = RSSConfig().dict()
        # RSS sources typically don't need deep crawling
        base_config["crawl_scope"]["max_depth"] = 1
        base_config["crawl_scope"]["max_artifacts"] = 100
        base_config["politeness"]["download_delay"] = 0.5  # RSS is fast
    
    elif source_type == "api":
        base_config["api"] = APIConfig().dict()
        # API sources don't crawl
        base_config["crawl_scope"]["max_depth"] = 0
        base_config["crawl_scope"]["max_artifacts"] = 1000  # APIs can return many items
    
    elif source_type in ["web", "news"]:
        # Web sources use standard defaults
        pass
    
    return base_config


def validate_config_for_type(source_type: str, config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration for a specific source type
    
    Args:
        source_type: Type of source
        config: Configuration dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Type-specific validations
    if source_type in ["web", "news"]:
        if not config.get("start_urls"):
            errors.append("start_urls is required for web sources")
        if not config.get("filtering", {}).get("allowed_domains"):
            errors.append("allowed_domains is recommended for web sources")
    
    elif source_type in ["rss", "feed"]:
        if not config.get("start_urls"):
            errors.append("start_urls (RSS feed URL) is required for RSS sources")
        if not config.get("rss"):
            errors.append("RSS configuration is required for RSS sources")
    
    elif source_type == "api":
        if not config.get("api", {}).get("api_base_url"):
            errors.append("api_base_url is required for API sources")
        if not config.get("api", {}).get("api_endpoints"):
            errors.append("api_endpoints is required for API sources")
    
    # General validations
    if config.get("crawl_scope", {}).get("max_depth", 0) > 10:
        errors.append("max_depth should not exceed 10")
    
    if config.get("politeness", {}).get("download_delay", 0) < 0:
        errors.append("download_delay must be non-negative")
    
    return errors

