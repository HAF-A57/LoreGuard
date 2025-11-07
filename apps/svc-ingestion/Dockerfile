# LoreGuard Ingestion Service Dockerfile
# Multi-stage build for optimized image size
# Note: This service uses Scrapy and Playwright for web crawling

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers in builder stage
RUN playwright install chromium
RUN playwright install-deps chromium

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies including Playwright system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Playwright browsers from builder
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy application code
COPY . .

# Create non-root user for security
# Copy Playwright browsers to user-accessible location
RUN useradd -m -u 1000 loreguard && \
    mkdir -p /home/loreguard/.cache/ms-playwright && \
    cp -r /root/.cache/ms-playwright/* /home/loreguard/.cache/ms-playwright/ 2>/dev/null || true && \
    chown -R loreguard:loreguard /app && \
    chown -R loreguard:loreguard /home/loreguard/.cache

# Switch to non-root user
USER loreguard

# Set Playwright browser path for non-root user
ENV PLAYWRIGHT_BROWSERS_PATH=/home/loreguard/.cache/ms-playwright

# Note: This service doesn't expose a port as it's invoked via scrapy commands
# It can be run as a worker or invoked on-demand by the API service

# Default command: Keep container running (scrapy commands are invoked via docker exec)
# The service is typically invoked via: docker exec loreguard-ingestion scrapy crawl <spider_name> -a <args>
CMD ["tail", "-f", "/dev/null"]

