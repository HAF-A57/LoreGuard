"""
LoreGuard Ingestion Service - Scrapy Settings

This module configures Scrapy for large-scale, respectful web crawling
with anti-bot evasion and performance optimization.
"""

import os
from pathlib import Path

# Scrapy settings for loreguard-ingestion project
BOT_NAME = 'loreguard-ingestion'

SPIDER_MODULES = ['app.spiders']
NEWSPIDER_MODULE = 'app.spiders'

# =============================================================================
# ROBOTSTXT AND POLITENESS
# =============================================================================

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure delays for requests (in seconds)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
DOWNLOAD_DELAY = 2.0  # Default delay between requests
RANDOMIZE_DOWNLOAD_DELAY = 0.5  # Randomize delay (0.5 * to 1.5 * DOWNLOAD_DELAY)

# Enable AutoThrottle for adaptive delays
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False  # Enable to see throttling stats

# =============================================================================
# CONCURRENCY AND PERFORMANCE
# =============================================================================

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Configure timeouts
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# =============================================================================
# USER AGENT AND HEADERS
# =============================================================================

# Default user agent (will be overridden by middleware)
USER_AGENT = 'LoreGuard-Bot/1.0 (+https://github.com/HAF-A57/LoreGuard)'

# Default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    # 'app.middlewares.SourceConfigMiddleware': 100,
    # 'app.middlewares.DuplicateFilterMiddleware': 200,
    # 'app.middlewares.ContentValidationMiddleware': 300,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    # Built-in middlewares
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    
    # Custom middlewares (disabled for testing)
    # 'app.middlewares.RotatingUserAgentMiddleware': 400,
    # 'app.middlewares.ProxyRotationMiddleware': 410,
    # 'app.middlewares.AntiDetectionMiddleware': 420,
    # 'app.middlewares.CustomRetryMiddleware': 550,
    # 'app.middlewares.ResponseValidationMiddleware': 560,
}

# =============================================================================
# PLAYWRIGHT CONFIGURATION
# =============================================================================

# Playwright settings
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'headless': True,
    'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000
PLAYWRIGHT_DEFAULT_TIMEOUT = 30000

# =============================================================================
# ITEM PIPELINES
# =============================================================================

# Configure item pipelines
ITEM_PIPELINES = {
    # 'app.pipelines.ValidationPipeline': 100,
    # 'app.pipelines.DeduplicationPipeline': 200,
    # 'app.pipelines.ContentHashPipeline': 300,
    # 'app.pipelines.MetadataExtractionPipeline': 400,
    # 'app.pipelines.DatabaseStoragePipeline': 500,
    # 'app.pipelines.ObjectStoragePipeline': 600,
    # 'app.pipelines.MonitoringPipeline': 700,
}

# =============================================================================
# CACHING
# =============================================================================

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 403, 404, 408, 429]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# =============================================================================
# LOGGING
# =============================================================================

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(levelname)s: %(message)s'
LOG_FILE = os.getenv('LOG_FILE', 'logs/scrapy.log')

# Disable some verbose logs
LOG_ENABLED = True
LOGSTATS_INTERVAL = 60

# =============================================================================
# EXTENSIONS
# =============================================================================

# Enable or disable extensions
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    # 'app.extensions.PrometheusStatsExtension': 100,
    # 'app.extensions.HealthCheckExtension': 200,
}

# =============================================================================
# CUSTOM SETTINGS
# =============================================================================

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://loreguard:password@localhost:5432/loreguard')

# Redis configuration (for job queues and caching)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# MinIO/S3 configuration
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'http://localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'loreguard')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'password')
MINIO_BUCKET_ARTIFACTS = 'artifacts'
MINIO_BUCKET_EVIDENCE = 'evidence'

# Content processing settings
MAX_CONTENT_SIZE = 50 * 1024 * 1024  # 50MB max file size
SUPPORTED_CONTENT_TYPES = [
    'text/html',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'application/rtf',
    'application/xml',
    'text/xml',
]

# Source-specific settings
SOURCE_SPECIFIC_DELAYS = {
    'high_priority': 1.0,
    'medium_priority': 2.0,
    'low_priority': 5.0,
}

# Anti-detection settings
ROTATING_PROXY_LIST_PATH = os.getenv('PROXY_LIST_PATH', 'config/proxies.txt')
USER_AGENT_LIST_PATH = os.getenv('USER_AGENT_LIST_PATH', 'config/user_agents.txt')

# Monitoring and metrics
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '9090'))
HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8080'))

# Job processing
MAX_CONCURRENT_JOBS = int(os.getenv('MAX_CONCURRENT_JOBS', '5'))
JOB_TIMEOUT = int(os.getenv('JOB_TIMEOUT', '3600'))  # 1 hour

# Content validation
MIN_CONTENT_LENGTH = 100  # Minimum content length to consider valid
MAX_REDIRECT_HOPS = 5

# =============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# =============================================================================

# Development settings
if os.getenv('ENVIRONMENT') == 'development':
    LOG_LEVEL = 'DEBUG'
    HTTPCACHE_ENABLED = False
    DOWNLOAD_DELAY = 1.0
    CONCURRENT_REQUESTS = 8
    CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Production settings
elif os.getenv('ENVIRONMENT') == 'production':
    LOG_LEVEL = 'INFO'
    HTTPCACHE_ENABLED = True
    DOWNLOAD_DELAY = 3.0
    CONCURRENT_REQUESTS = 32
    CONCURRENT_REQUESTS_PER_DOMAIN = 4
    
    # Enable more aggressive anti-detection in production
    PLAYWRIGHT_LAUNCH_OPTIONS.update({
        'args': PLAYWRIGHT_LAUNCH_OPTIONS['args'] + [
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--disable-plugins-discovery',
            '--disable-default-apps',
        ]
    })

# =============================================================================
# TELEMETRY AND MONITORING
# =============================================================================

# Custom stats (disabled for testing)
# STATS_CLASS = 'app.stats.CustomStatsCollector'

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# DNS settings
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# =============================================================================
# SECURITY
# =============================================================================

# Disable cookies by default (can be enabled per spider)
COOKIES_ENABLED = False

# Media pipeline settings (for downloading files)
MEDIA_ALLOW_REDIRECTS = True
FILES_STORE = os.getenv('FILES_STORE', 'downloads')
FILES_EXPIRES = 90  # Days

# =============================================================================
# CUSTOM COMMANDS
# =============================================================================

# Custom Scrapy commands location (disabled for now)
# COMMANDS_MODULE = 'app.commands'

