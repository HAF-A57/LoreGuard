## Crawler Framework Research Findings

### Executive Summary
For LoreGuard's ingestion service, we need a crawler framework that can handle thousands of global sources while respecting politeness policies and evading anti-bot detection. Based on research, **Scrapy with Playwright integration** emerges as the recommended approach.

### Framework Comparison

#### Scrapy
**Strengths:**
- Industry-standard framework with mature ecosystem
- Built-in politeness controls (delays, concurrent requests, AutoThrottle)
- Robust middleware system for rotating proxies, user agents, headers
- Excellent performance for large-scale crawling
- Strong community support and extensive documentation
- Built-in duplicate filtering and request/response middleware
- Supports both synchronous and asynchronous operations

**Weaknesses:**
- Limited JavaScript rendering capabilities without additional tools
- May struggle with heavily protected sites requiring browser-like behavior

#### Playwright
**Strengths:**
- Excellent JavaScript rendering and modern web app support
- Superior anti-bot evasion (real browser fingerprints, stealth mode)
- Can handle complex authentication flows and dynamic content
- Built-in screenshot and PDF generation capabilities
- Cross-browser support (Chrome, Firefox, Safari)

**Weaknesses:**
- Higher resource consumption (memory, CPU)
- Slower than pure HTTP clients
- More complex deployment and scaling

#### MechanicalSoup
**Strengths:**
- Simple API, easy to learn
- Good for basic form submission and simple scraping
- Lightweight

**Weaknesses:**
- Limited scalability features
- No built-in anti-bot evasion
- Lacks advanced features needed for enterprise crawling
- Not suitable for large-scale operations

### Recommended Architecture: Hybrid Approach

**Primary: Scrapy + scrapy-playwright**
- Use Scrapy as the main framework with scrapy-playwright middleware
- Playwright handles JavaScript-heavy sites and anti-bot challenges
- Scrapy handles bulk crawling, politeness, and pipeline management

**Key Components:**
```python
# Example middleware stack
DOWNLOADER_MIDDLEWARES = {
    'scrapy_playwright.PlaywrightMiddleware': 585,
    'rotating_proxies.RandomProxyMiddleware': 610,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.RandomUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
}
```

### Anti-Bot and Politeness Strategy

#### Politeness Controls
- **AutoThrottle Extension**: Automatically adjusts delays based on response times
- **Download Delay**: Minimum delay between requests (1-5 seconds)
- **Concurrent Requests**: Limit per domain (1-2 for politeness)
- **Robots.txt Compliance**: Built-in support with override capabilities

#### Anti-Bot Evasion
- **Rotating Proxies**: Use proxy pools with geographic distribution
- **User Agent Rotation**: Randomize browsers and versions
- **Header Randomization**: Vary Accept, Accept-Language, Accept-Encoding
- **Session Management**: Maintain cookies and session state
- **Request Timing**: Human-like delays with jitter

#### Implementation Libraries
- `scrapy-playwright`: JavaScript rendering integration
- `scrapy-rotating-proxies`: Proxy rotation middleware  
- `scrapy-user-agents`: User agent randomization
- `scrapy-splash`: Alternative JavaScript renderer
- `fake-useragent`: Generate realistic user agents

### Deployment Considerations

#### Scaling Strategy
- **Distributed Crawling**: Use Scrapy-Redis for distributed crawling
- **Queue Management**: Redis-based request queues
- **Load Balancing**: Multiple crawler instances behind load balancer
- **Resource Management**: Docker containers with CPU/memory limits

#### Monitoring and Observability
- **Scrapy Stats**: Built-in statistics collection
- **Custom Metrics**: Request success rates, response times, ban rates
- **Alerting**: Integration with Prometheus/Grafana
- **Log Aggregation**: Structured logging for debugging

### Integration with LoreGuard Pipeline

```python
# Example Scrapy spider for LoreGuard
class LoreGuardSpider(scrapy.Spider):
    name = 'loreguard'
    
    custom_settings = {
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
    }
    
    def start_requests(self):
        for source in self.get_sources():
            yield scrapy.Request(
                url=source.url,
                meta={'playwright': True, 'source_id': source.id},
                callback=self.parse_document
            )
    
    def parse_document(self, response):
        # Extract content and metadata
        # Emit to normalization pipeline
        pass
```

### Cost and Performance Analysis

#### Resource Requirements
- **Scrapy**: ~10-50MB RAM per concurrent request
- **Playwright**: ~100-200MB RAM per browser instance
- **Recommended**: 4-8 CPU cores, 16-32GB RAM per crawler node

#### Throughput Estimates
- **Scrapy alone**: 100-1000 pages/minute
- **With Playwright**: 10-50 pages/minute (for JS-heavy sites)
- **Mixed workload**: 50-200 pages/minute average

### Next Steps
1. Implement proof-of-concept with scrapy-playwright
2. Test against representative source sites
3. Benchmark performance and resource usage
4. Develop anti-bot detection monitoring
5. Create deployment scripts and monitoring dashboards
