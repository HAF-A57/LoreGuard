# Web Scraping Configuration Parameters Research

**Date**: 2025-01-XX  
**Purpose**: Comprehensive research on configurable parameters for web scraping/crawling systems like LoreGuard  
**Target**: Define all user-configurable parameters for source management

---

## Executive Summary

This document outlines the comprehensive set of configurable parameters that should be available when configuring web sources for artifact retrieval in LoreGuard. These parameters balance thoroughness, performance, politeness, and compliance with ethical web scraping standards.

---

## 🎯 Recommended Test Sources for LoreGuard

### For Initial Testing & Development

#### 1. **Dedicated Practice Platforms** (Ideal for MVP Testing)
- **Books to Scrape** (`http://books.toscrape.com/`)
  - ✅ Static HTML content
  - ✅ Simple pagination
  - ✅ Well-structured data
  - ✅ Robots.txt compliant
  - ✅ Safe for testing
  
- **Quotes to Scrape** (`http://quotes.toscrape.com/`)
  - ✅ Multiple pagination types
  - ✅ Login functionality for testing auth
  - ✅ JavaScript-rendered content option
  - ✅ Safe testing environment

#### 2. **Real-World Defense/Military Sources** (Production-Ready)
- **NATO News** (`https://www.nato.int/cps/en/natohq/news.htm`)
  - ✅ Public RSS feeds available
  - ✅ Well-structured content
  - ✅ Professional organization
  - ✅ Robots.txt compliant
  
- **U.S. Department of Defense News** (`https://www.defense.gov/News/`)
  - ✅ RSS feeds available
  - ✅ Press releases and reports
  - ✅ PDF documents available
  - ✅ Public domain content

- **Defense News** (`https://www.defensenews.com/`)
  - ✅ News articles and analysis
  - ✅ Multiple content types
  - ✅ RSS feeds available

- **Jane's Defense** (if RSS/API available)
  - ✅ Professional defense analysis
  - ✅ Structured content

---

## 📋 Comprehensive Configuration Parameters

### Category 1: Crawl Scope & Limits

#### 1.1 Crawl Depth
- **Parameter**: `max_depth`
- **Type**: Integer (0-10 recommended)
- **Default**: 3
- **Description**: Maximum number of link levels to follow from start URLs
- **Best Practices**:
  - Depth 0: Only seed URLs
  - Depth 1-2: Seed + immediate links
  - Depth 3-5: Moderate exploration
  - Depth 6+: Deep crawling (use with caution)
- **Use Cases**:
  - News sites: Depth 2-3 (article listings → articles)
  - Documentation: Depth 4-6 (tables of contents → sections)
  - Forums: Depth 2-3 (thread listings → posts)

#### 1.2 Maximum Artifacts per Crawl
- **Parameter**: `max_artifacts`
- **Type**: Integer (0 = unlimited)
- **Default**: 100
- **Description**: Maximum number of artifacts to retrieve in a single crawl job
- **Best Practices**:
  - MVP testing: 10-50 artifacts
  - Production: 100-1000 per job
  - Large sources: Set per-run limits, use scheduling
- **Implementation**: Stop crawling when limit reached

#### 1.3 Maximum Pages per Domain
- **Parameter**: `max_pages_per_domain`
- **Type**: Integer
- **Default**: 1000
- **Description**: Maximum pages to crawl per domain per job
- **Use Case**: Prevent runaway crawls on large sites

#### 1.4 Time Budget
- **Parameter**: `max_crawl_time_minutes`
- **Type**: Integer (minutes)
- **Default**: 60
- **Description**: Maximum time allowed for crawl job
- **Best Practice**: Set reasonable limits to prevent infinite crawls

---

### Category 2: Request Rate & Politeness

#### 2.1 Download Delay
- **Parameter**: `download_delay`
- **Type**: Float (seconds)
- **Default**: 2.0
- **Description**: Base delay between requests
- **Best Practices**:
  - Conservative: 3-5 seconds
  - Moderate: 1-2 seconds
  - Aggressive: 0.5-1 second (use with caution)
- **Impact**: Lower delay = faster crawling, higher risk of blocking

#### 2.2 Randomize Download Delay
- **Parameter**: `randomize_download_delay`
- **Type**: Float (multiplier)
- **Default**: 0.5
- **Description**: Randomization factor (0.5 = delay varies 50% above/below base)
- **Best Practice**: 0.3-0.7 for human-like behavior

#### 2.3 Concurrent Requests
- **Parameter**: `concurrent_requests`
- **Type**: Integer
- **Default**: 16
- **Description**: Total concurrent requests across all domains
- **Best Practices**:
  - Conservative: 8-16
  - Moderate: 16-32
  - Aggressive: 32-64 (may trigger rate limits)

#### 2.4 Concurrent Requests per Domain
- **Parameter**: `concurrent_requests_per_domain`
- **Type**: Integer
- **Default**: 2
- **Description**: Concurrent requests to single domain
- **Best Practices**:
  - Most sites: 1-2
  - Large sites: 2-4
  - High-capacity sites: 4-8

#### 2.5 AutoThrottle Settings
- **Parameter**: `autothrottle_enabled`
- **Type**: Boolean
- **Default**: True
- **Description**: Enable adaptive rate limiting based on server response times
- **Sub-parameters**:
  - `autothrottle_start_delay`: Initial delay (default: 1.0s)
  - `autothrottle_max_delay`: Maximum delay (default: 10.0s)
  - `autothrottle_target_concurrency`: Target concurrent requests (default: 2.0)

---

### Category 3: URL Filtering & Patterns

#### 3.1 Allowed Domains
- **Parameter**: `allowed_domains`
- **Type**: List of strings
- **Default**: Empty (all domains allowed)
- **Description**: Whitelist of domains to crawl
- **Example**: `["nato.int", "defense.gov"]`
- **Best Practice**: Always set for production sources

#### 3.2 Denied Domains
- **Parameter**: `denied_domains`
- **Type**: List of strings
- **Default**: Empty
- **Description**: Blacklist of domains to exclude
- **Example**: `["ads.example.com", "tracking.example.com"]`

#### 3.3 Allowed URL Patterns
- **Parameter**: `allowed_url_patterns`
- **Type**: List of regex patterns
- **Default**: Empty (all URLs allowed)
- **Description**: Regex patterns for URLs to include
- **Example**: `[r"/news/.*", r"/reports/.*"]`
- **Use Case**: Limit crawling to specific sections

#### 3.4 Denied URL Patterns
- **Parameter**: `denied_url_patterns`
- **Type**: List of regex patterns
- **Default**: Common exclusions (e.g., `/admin/`, `/login/`)
- **Description**: Regex patterns for URLs to exclude
- **Common Patterns**:
  - `/admin/.*` - Admin panels
  - `/login/.*` - Login pages
  - `/cart/.*` - Shopping carts
  - `.*\.(jpg|png|gif|css|js)$` - Static assets

#### 3.5 File Type Filters
- **Parameter**: `allowed_file_types`
- **Type**: List of MIME types or extensions
- **Default**: `["text/html", "application/pdf", "application/json"]`
- **Description**: File types to download and process
- **Options**: HTML, PDF, DOCX, JSON, XML, RSS, etc.

#### 3.6 Maximum File Size
- **Parameter**: `max_file_size_mb`
- **Type**: Integer (MB)
- **Default**: 50
- **Description**: Maximum file size to download
- **Best Practice**: Skip large files that may not be relevant

---

### Category 4: JavaScript & Dynamic Content

#### 4.1 JavaScript Rendering Required
- **Parameter**: `javascript_required`
- **Type**: Boolean
- **Default**: False
- **Description**: Enable Playwright/Selenium for JavaScript-heavy sites
- **Use Cases**:
  - Single-page applications (SPAs)
  - Content loaded via AJAX
  - Infinite scroll pages
- **Performance Impact**: Slower but necessary for modern sites

#### 4.2 JavaScript Wait Time
- **Parameter**: `javascript_wait_time`
- **Type**: Integer (milliseconds)
- **Default**: 2000
- **Description**: Time to wait for JavaScript to render
- **Best Practice**: 1-3 seconds depending on site complexity

#### 4.3 Wait for Selectors
- **Parameter**: `wait_for_selectors`
- **Type**: List of CSS selectors
- **Default**: Empty
- **Description**: Wait for specific elements before scraping
- **Example**: `["article.content", ".post-body"]`
- **Use Case**: Ensure content is loaded before extraction

---

### Category 5: Authentication & Sessions

#### 5.1 Authentication Required
- **Parameter**: `authentication_required`
- **Type**: Boolean
- **Default**: False
- **Description**: Site requires login
- **Sub-parameters**:
  - `auth_type`: "form", "basic", "bearer", "oauth"
  - `login_url`: URL for login page
  - `username`: Username/email (encrypted storage)
  - `password`: Password (encrypted storage)
  - `session_cookies`: Cookie storage for session persistence

#### 5.2 Custom Headers
- **Parameter**: `custom_headers`
- **Type**: Dictionary
- **Default**: Empty
- **Description**: Custom HTTP headers to send with requests
- **Example**: 
  ```json
  {
    "X-API-Key": "your-key",
    "Authorization": "Bearer token",
    "Accept": "application/json"
  }
  ```

#### 5.3 User-Agent
- **Parameter**: `user_agent`
- **Type**: String
- **Default**: "LoreGuard-Bot/1.0"
- **Description**: Custom User-Agent string
- **Best Practice**: Use realistic browser User-Agent strings

#### 5.4 User-Agent Rotation
- **Parameter**: `rotate_user_agent`
- **Type**: Boolean
- **Default**: False
- **Description**: Rotate User-Agent strings per request
- **Use Case**: Reduce detection risk

---

### Category 6: Retry & Error Handling

#### 6.1 Retry Times
- **Parameter**: `retry_times`
- **Type**: Integer
- **Default**: 3
- **Description**: Number of retry attempts for failed requests
- **Best Practice**: 2-5 retries with exponential backoff

#### 6.2 Retry HTTP Codes
- **Parameter**: `retry_http_codes`
- **Type**: List of integers
- **Default**: `[500, 502, 503, 504, 408, 429]`
- **Description**: HTTP status codes that trigger retry
- **Common Codes**:
  - 500: Internal Server Error
  - 502: Bad Gateway
  - 503: Service Unavailable
  - 504: Gateway Timeout
  - 408: Request Timeout
  - 429: Too Many Requests (rate limit)

#### 6.3 Retry Backoff Strategy
- **Parameter**: `retry_backoff_strategy`
- **Type**: String ("exponential", "linear", "fixed")
- **Default**: "exponential"
- **Description**: How to increase delay between retries
- **Options**:
  - Exponential: 1s, 2s, 4s, 8s...
  - Linear: 1s, 2s, 3s, 4s...
  - Fixed: 2s, 2s, 2s...

#### 6.4 Download Timeout
- **Parameter**: `download_timeout`
- **Type**: Integer (seconds)
- **Default**: 30
- **Description**: Maximum time to wait for response
- **Best Practice**: 30-60 seconds for normal sites, 120+ for slow sites

---

### Category 7: Proxy & IP Management

#### 7.1 Use Proxies
- **Parameter**: `use_proxies`
- **Type**: Boolean
- **Default**: False
- **Description**: Enable proxy rotation
- **Use Cases**:
  - Large-scale crawling
  - Geo-restricted content
  - Rate limit avoidance

#### 7.2 Proxy List
- **Parameter**: `proxy_list`
- **Type**: List of proxy URLs
- **Default**: Empty
- **Description**: Proxy servers to use
- **Format**: `["http://proxy1:port", "http://proxy2:port"]`

#### 7.3 Proxy Rotation Strategy
- **Parameter**: `proxy_rotation_strategy`
- **Type**: String ("round-robin", "random", "failover")
- **Default**: "round-robin"
- **Description**: How to select proxies

---

### Category 8: Robots.txt & Compliance

#### 8.1 Obey Robots.txt
- **Parameter**: `obey_robots_txt`
- **Type**: Boolean
- **Default**: True
- **Description**: Respect robots.txt directives
- **Best Practice**: Always True for ethical scraping

#### 8.2 Robots.txt User-Agent
- **Parameter**: `robots_txt_user_agent`
- **Type**: String
- **Default**: "*" (all bots)
- **Description**: User-Agent to use when checking robots.txt
- **Best Practice**: Use your bot's User-Agent or "*"

---

### Category 9: RSS/Feed Specific Parameters

#### 9.1 Feed Update Frequency
- **Parameter**: `feed_update_frequency_minutes`
- **Type**: Integer
- **Default**: 60
- **Description**: How often to check feed for updates
- **Best Practices**:
  - News feeds: 15-60 minutes
  - Blog feeds: 60-240 minutes
  - Static feeds: 360+ minutes

#### 9.2 Maximum Feed Items
- **Parameter**: `max_feed_items`
- **Type**: Integer
- **Default**: 100
- **Description**: Maximum items to retrieve per feed check
- **Use Case**: Prevent processing thousands of items

#### 9.3 Feed Item Retention
- **Parameter**: `feed_item_retention_days`
- **Type**: Integer
- **Default**: 30
- **Description**: How long to keep feed items before re-processing
- **Use Case**: Avoid re-processing old items

#### 9.4 Follow Feed Links
- **Parameter**: `follow_feed_links`
- **Type**: Boolean
- **Default**: True
- **Description**: Crawl URLs from feed items
- **Use Case**: Get full article content, not just summaries

---

### Category 10: API-Specific Parameters

#### 10.1 API Base URL
- **Parameter**: `api_base_url`
- **Type**: String (URL)
- **Default**: Empty
- **Description**: Base URL for API endpoints
- **Example**: `https://api.example.com/v1`

#### 10.2 API Authentication
- **Parameter**: `api_auth_type`
- **Type**: String ("none", "bearer", "basic", "apikey", "oauth2")
- **Default**: "none"
- **Description**: Authentication method for API
- **Sub-parameters**:
  - `api_key`: API key value (encrypted)
  - `api_key_header`: Header name (e.g., "X-API-Key")
  - `bearer_token`: Bearer token (encrypted)
  - `oauth2_client_id`: OAuth2 client ID
  - `oauth2_client_secret`: OAuth2 secret (encrypted)

#### 10.3 API Rate Limits
- **Parameter**: `api_rate_limit_requests`
- **Type**: Integer
- **Default**: 100
- **Description**: Max requests per time window
- **Sub-parameter**: `api_rate_limit_window_seconds`: Time window (default: 60)

#### 10.4 API Pagination
- **Parameter**: `api_pagination_type`
- **Type**: String ("none", "offset", "cursor", "page")
- **Default**: "none"
- **Description**: Pagination method
- **Sub-parameters**:
  - `pagination_param_name`: Parameter name (e.g., "page", "offset")
  - `pagination_start_value`: Starting value
  - `pagination_increment`: Value increment
  - `pagination_max_pages`: Maximum pages to fetch

#### 10.5 API Endpoints
- **Parameter**: `api_endpoints`
- **Type**: List of strings
- **Default**: Empty
- **Description**: API endpoints to call
- **Example**: `["/articles", "/reports", "/news"]`

#### 10.6 API Request Method
- **Parameter**: `api_request_method`
- **Type**: String ("GET", "POST")
- **Default**: "GET"
- **Description**: HTTP method for API calls

#### 10.7 API Request Body
- **Parameter**: `api_request_body`
- **Type**: Dictionary (JSON)
- **Default**: Empty
- **Description**: Request body for POST requests
- **Example**: `{"filter": {"status": "published"}, "limit": 100}`

---

### Category 11: Content Extraction & Processing

#### 11.1 Content Selectors
- **Parameter**: `content_selectors`
- **Type**: Dictionary of CSS/XPath selectors
- **Default**: Empty
- **Description**: Custom selectors for content extraction
- **Example**:
  ```json
  {
    "title": "h1.article-title",
    "content": "article.main-content",
    "author": ".author-name",
    "date": "time.publish-date"
  }
  ```

#### 11.2 Extract Images
- **Parameter**: `extract_images`
- **Type**: Boolean
- **Default**: False
- **Description**: Download and process images
- **Sub-parameter**: `max_image_size_mb`: Maximum image size

#### 11.3 Extract PDFs
- **Parameter**: `extract_pdfs`
- **Type**: Boolean
- **Default**: True
- **Description**: Download and process PDF documents

#### 11.4 Extract Metadata
- **Parameter**: `extract_metadata`
- **Type**: Boolean
- **Default**: True
- **Description**: Extract document metadata (title, author, date, etc.)

#### 11.5 Minimum Content Length
- **Parameter**: `min_content_length`
- **Type**: Integer (characters)
- **Default**: 100
- **Description**: Minimum content length to consider valid
- **Use Case**: Filter out navigation pages, empty pages

---

### Category 12: Scheduling & Automation

#### 12.1 Schedule Type
- **Parameter**: `schedule_type`
- **Type**: String ("manual", "interval", "cron", "rss-poll")
- **Default**: "manual"
- **Description**: How to trigger crawls
- **Options**:
  - Manual: User-triggered only
  - Interval: Every X minutes/hours
  - Cron: Cron expression (e.g., "0 */4 * * *")
  - RSS-poll: Check RSS feed periodically

#### 12.2 Schedule Value
- **Parameter**: `schedule_value`
- **Type**: String
- **Default**: Empty
- **Description**: Schedule configuration
- **Examples**:
  - Interval: "60m" (every 60 minutes)
  - Cron: "0 */4 * * *" (every 4 hours)
  - RSS-poll: "30m" (check every 30 minutes)

#### 12.3 Crawl Hours
- **Parameter**: `crawl_hours`
- **Type**: List of hours (0-23)
- **Default**: Empty (all hours)
- **Description**: Only crawl during specified hours
- **Use Case**: Avoid peak traffic times
- **Example**: `[2, 3, 4, 5]` (2 AM - 6 AM)

---

### Category 13: Advanced Features

#### 13.1 Duplicate Detection
- **Parameter**: `enable_duplicate_detection`
- **Type**: Boolean
- **Default**: True
- **Description**: Skip duplicate content
- **Method**: Content hash comparison

#### 13.2 Content Caching
- **Parameter**: `enable_content_cache`
- **Type**: Boolean
- **Default**: True
- **Description**: Cache downloaded content
- **Sub-parameter**: `cache_expiration_hours`: Cache TTL (default: 24)

#### 13.3 Respect HTTP Cache Headers
- **Parameter**: `respect_cache_headers`
- **Type**: Boolean
- **Default**: True
- **Description**: Honor Cache-Control and ETag headers

#### 13.4 Follow Redirects
- **Parameter**: `follow_redirects`
- **Type**: Boolean
- **Default**: True
- **Description**: Follow HTTP redirects
- **Sub-parameter**: `max_redirects`: Maximum redirect hops (default: 5)

#### 13.5 Verify SSL Certificates
- **Parameter**: `verify_ssl`
- **Type**: Boolean
- **Default**: True
- **Description**: Verify SSL certificates
- **Use Case**: Set False only for testing/internal sites

---

## 🎯 Source Type-Specific Recommendations

### Web Crawling (`type: "web"`)
**Essential Parameters:**
- `max_depth`: 2-3
- `max_artifacts`: 100-500
- `download_delay`: 2.0
- `concurrent_requests_per_domain`: 2
- `allowed_domains`: Required
- `allowed_url_patterns`: Recommended
- `javascript_required`: Based on site type

**Optional Parameters:**
- `autothrottle_enabled`: True
- `obey_robots_txt`: True
- `custom_headers`: If needed
- `extract_pdfs`: True

### RSS Feed (`type: "rss"` or `type: "feed"`)
**Essential Parameters:**
- `feed_update_frequency_minutes`: 15-60
- `max_feed_items`: 50-200
- `follow_feed_links`: True (usually)
- `feed_item_retention_days`: 30

**Optional Parameters:**
- `allowed_domains`: If following links
- `download_delay`: Lower (0.5-1.0) since RSS is fast

### API (`type: "api"`)
**Essential Parameters:**
- `api_base_url`: Required
- `api_auth_type`: Based on API
- `api_endpoints`: Required
- `api_rate_limit_requests`: Check API docs
- `api_pagination_type`: Based on API

**Optional Parameters:**
- `api_request_method`: "GET" or "POST"
- `api_request_body`: For POST requests
- `custom_headers`: Often needed

### News Sites (`type: "news"`)
**Essential Parameters:**
- `max_depth`: 2-3
- `feed_update_frequency_minutes`: 15-30
- `max_artifacts`: 100-500 per crawl
- `allowed_url_patterns`: Focus on article pages
- `extract_metadata`: True

---

## 📊 Parameter Priority Levels

### **Critical (Must Have for MVP)**
1. `max_depth` - Control crawl scope
2. `max_artifacts` - Prevent runaway crawls
3. `download_delay` - Basic politeness
4. `allowed_domains` - Security and scope
5. `obey_robots_txt` - Legal compliance

### **High Priority (Strongly Recommended)**
6. `concurrent_requests_per_domain` - Performance
7. `allowed_url_patterns` - Content filtering
8. `max_file_size_mb` - Resource management
9. `retry_times` - Reliability
10. `download_timeout` - Error handling

### **Medium Priority (Nice to Have)**
11. `javascript_required` - Modern site support
12. `autothrottle_enabled` - Adaptive behavior
13. `custom_headers` - API integration
14. `schedule_type` - Automation
15. `extract_metadata` - Rich data

### **Low Priority (Advanced Features)**
16. `use_proxies` - Large-scale operations
17. `authentication_required` - Premium content
18. `content_selectors` - Custom extraction
19. `crawl_hours` - Traffic management
20. `api_pagination_type` - Complex APIs

---

## 🔧 Implementation Recommendations

### Configuration Schema Structure

```json
{
  "crawl_scope": {
    "max_depth": 3,
    "max_artifacts": 100,
    "max_pages_per_domain": 1000,
    "max_crawl_time_minutes": 60
  },
  "politeness": {
    "download_delay": 2.0,
    "randomize_download_delay": 0.5,
    "concurrent_requests": 16,
    "concurrent_requests_per_domain": 2,
    "autothrottle_enabled": true
  },
  "filtering": {
    "allowed_domains": ["example.com"],
    "denied_domains": [],
    "allowed_url_patterns": ["/news/.*"],
    "denied_url_patterns": ["/admin/.*"],
    "allowed_file_types": ["text/html", "application/pdf"]
  },
  "javascript": {
    "javascript_required": false,
    "javascript_wait_time": 2000,
    "wait_for_selectors": []
  },
  "authentication": {
    "authentication_required": false,
    "auth_type": "form",
    "custom_headers": {}
  },
  "retry": {
    "retry_times": 3,
    "retry_http_codes": [500, 502, 503, 504, 408, 429],
    "retry_backoff_strategy": "exponential",
    "download_timeout": 30
  },
  "compliance": {
    "obey_robots_txt": true,
    "robots_txt_user_agent": "*"
  },
  "rss": {
    "feed_update_frequency_minutes": 60,
    "max_feed_items": 100,
    "feed_item_retention_days": 30,
    "follow_feed_links": true
  },
  "api": {
    "api_base_url": "",
    "api_auth_type": "none",
    "api_rate_limit_requests": 100,
    "api_rate_limit_window_seconds": 60,
    "api_pagination_type": "none",
    "api_endpoints": []
  },
  "extraction": {
    "content_selectors": {},
    "extract_images": false,
    "extract_pdfs": true,
    "extract_metadata": true,
    "min_content_length": 100
  },
  "scheduling": {
    "schedule_type": "manual",
    "schedule_value": "",
    "crawl_hours": []
  }
}
```

---

## 🧪 Recommended Test Sources for LoreGuard MVP

### Test Source 1: Books to Scrape (Simple Web Crawl)
- **URL**: `http://books.toscrape.com/`
- **Type**: `web`
- **Configuration**:
  ```json
  {
    "max_depth": 2,
    "max_artifacts": 20,
    "download_delay": 1.0,
    "allowed_domains": ["books.toscrape.com"],
    "allowed_url_patterns": ["/catalogue/.*"]
  }
  ```
- **Why**: Simple, safe, well-structured, ideal for initial testing

### Test Source 2: NATO News RSS Feed
- **URL**: `https://www.nato.int/cps/en/natohq/news.htm` (RSS available)
- **Type**: `rss`
- **Configuration**:
  ```json
  {
    "feed_update_frequency_minutes": 60,
    "max_feed_items": 50,
    "follow_feed_links": true,
    "allowed_domains": ["nato.int"]
  }
  ```
- **Why**: Real-world defense content, RSS available, professional source

### Test Source 3: Defense News RSS Feed
- **URL**: Check for RSS feed at `https://www.defensenews.com/`
- **Type**: `rss`
- **Configuration**: Similar to NATO
- **Why**: Defense-focused content, real-world data

---

## 📝 Notes & Best Practices

### Legal & Ethical Considerations
1. **Always obey robots.txt** - Set `obey_robots_txt: true` by default
2. **Respect rate limits** - Use conservative delays for public sites
3. **Check Terms of Service** - Some sites prohibit scraping
4. **Public data only** - Don't scrape private/authenticated content without permission
5. **Attribution** - Consider displaying source attribution

### Performance Optimization
1. **Start conservative** - Begin with low concurrency and high delays
2. **Monitor server response** - Adjust based on site response times
3. **Use AutoThrottle** - Let Scrapy adapt automatically
4. **Set reasonable limits** - Prevent runaway crawls

### Error Handling
1. **Implement retries** - Handle transient failures
2. **Log errors** - Track what fails and why
3. **Graceful degradation** - Continue crawling if some pages fail
4. **Rate limit detection** - Back off if rate limited

---

## 🎯 Next Steps

1. **Update Source Model** - Add comprehensive config schema
2. **Update Source Schema** - Add Pydantic validators
3. **Update Frontend** - Create source configuration UI
4. **Update Ingestion Service** - Apply config parameters
5. **Test with Recommended Sources** - Validate implementation

---

**End of Research Document**

