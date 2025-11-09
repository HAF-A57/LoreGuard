# LoreGuard

**Automated Facts and Perspectives Harvesting for Military Wargaming**

LoreGuard is a companion system to the Multi-Agent Generative Engine (MAGE) designed to automatically discover, retrieve, evaluate, and curate open-source artifacts from thousands of global sources. The system captures diverse facts and perspectives from the Information Space to support Air Force wargaming operations.

## 🚀 Quick Start

### Prerequisites

- **Ubuntu 22.04 LTS** (recommended development environment)
- **Docker** and **Docker Compose** v2.0+
- **Node.js** 18+ and **npm** (for frontend development)
- **Python** 3.11+ (for local development, optional)
- **Git**
- **8GB RAM minimum** (16GB recommended)
- **50GB free disk space**

### One-Command Setup

```bash
# Clone and start LoreGuard
git clone https://github.com/HAF-A57/LoreGuard.git
cd LoreGuard
make quick-start
```

This single command will:
- ✅ Automatically detect your network IP address
- ✅ Configure environment variables
- ✅ Start all infrastructure containers (PostgreSQL, Redis, MinIO)
- ✅ Initialize database schema and create default admin user
- ✅ Build and start all backend services (API, Normalize, AI Assistant, Ingestion)
- ✅ Start frontend development server with hot reload

**Access Your Application:**
- **Frontend**: http://[YOUR_IP]:6060 (IP shown after startup)
- **API Docs**: http://[YOUR_IP]:8000/docs
- **Default Login**:
  - Email: `admin@loreguard.local`
  - Password: `admin`

**Note**: Backend services run in Docker containers for consistency, while the frontend runs locally for optimal hot-reload development experience.

## 📋 Alternative Setup Options

### Infrastructure Only

If you only need to start the infrastructure services (database, Redis, MinIO):

```bash
make quick-start-infra
```

This is useful if you want to run application services locally for development.

### Manual Service Management

For more control over individual services:

```bash
# Start infrastructure first
make quick-start-infra

# Then start individual services as needed
make start-api       # Backend API (port 8000)
make start-normalize # Normalize service (port 8001)
make start-assistant # AI Assistant (port 8002)
make start-web       # Frontend (port 6060)
```

### Verify Installation

After starting services, verify everything is working:

```bash
# Comprehensive health check
make health-check

# Expected output shows:
# ✅ All infrastructure services healthy
# ✅ All application services responding
# ✅ Container status and port availability
```

**Note**: The `make quick-start` command handles everything automatically. Manual setup is only needed for advanced development scenarios.

## 🏗️ Architecture Overview

### Current Implementation Status

| Component | Status | Description |
|-----------|--------|-------------|
| **Frontend** | ✅ **Complete** | React + Vite + Tailwind + shadcn/ui with professional branding |
| **Backend API** | ✅ **Complete** | FastAPI + SQLAlchemy + PostgreSQL with full CRUD operations |
| **Database** | ✅ **Complete** | PostgreSQL with 8 application tables + admin/audit tables |
| **Object Storage** | ✅ **Complete** | MinIO S3-compatible storage with health checks |
| **Authentication** | ✅ **Complete** | Admin user system with default credentials |
| **UI Components** | ✅ **Complete** | 8 pages + AI assistant with enhanced contrast |
| **Container Setup** | ✅ **Complete** | Docker Compose orchestration with volume management |
| **Sample Data** | ✅ **Complete** | 9 realistic sources with metadata |
| **Health Monitoring** | ✅ **Complete** | Comprehensive health check scripts |
| **Startup Scripts** | ✅ **Complete** | One-command setup with error handling |

### Next Phase: Evaluation Pipeline

Based on the [Final Technology Roadmap](./Planning/FinalTechnologyRoadmap.md), the next implementation phase focuses on:

- **LLM Evaluation Engine** - OpenAI integration with Pydantic validation
- **Configurable Rubric System** - UI editor for evaluation criteria
- **Document Processing Pipeline** - unstructured.io + Tesseract OCR
- **Evidence Collection** - WARC format archival system
- **Language Detection** - polyglot integration for multilingual support

## 🎯 Key Features

### ✅ **Currently Implemented**

#### **Frontend Application**
- **Three-Pane Layout**: Navigation + Content + AI Assistant
- **8 Complete Pages**: Dashboard, Artifacts, Sources, Library, Evaluations, Jobs, Analytics, Settings
- **AI Assistant Integration**: Real-time context-aware chatbot with chat history and tool calling
- **Authentication Flow**: Login system with loading screens
- **Responsive Design**: Mobile-friendly with dark/light mode
- **Professional UI**: Air Force Wargaming branding with official LoreGuard logo
- **Enhanced Accessibility**: Improved text contrast and visibility
- **Consistent Terminology**: Uses "artifact" terminology throughout for clarity

#### **Backend Services**
- **REST API**: FastAPI with OpenAPI documentation
- **Document Processing**: unstructured.io integration for text extraction
- **AI Assistant**: Context-aware chatbot with tool calling and chat history
- **Database Models**: Complete schema for all LoreGuard entities
- **Real CRUD Operations**: Tested with actual data persistence
- **Configuration Management**: Environment-based settings
- **Health Monitoring**: Service status and connectivity checks

#### **Infrastructure**
- **Containerized Deployment**: Docker Compose orchestration
- **Database Setup**: PostgreSQL with automated initialization
- **Object Storage**: MinIO with bucket configuration
- **Development Tools**: Hot reload, debugging, logging

### 🚧 **Next Phase Implementation**

#### **Document Processing Pipeline**
- **Web Crawling**: Scrapy + Playwright for source monitoring
- **Document Conversion**: unstructured.io + GROBID + Tesseract OCR
- **Metadata Extraction**: Title, authors, organization, publication date
- **Content Normalization**: Text extraction and structure preservation

#### **LLM Evaluation Engine**
- **OpenAI Integration**: GPT-4 for document evaluation
- **Pydantic Validation**: Structured JSON outputs with error handling
- **Configurable Rubrics**: Version-controlled evaluation criteria
- **Confidence Scoring**: Reliability metrics for automated decisions
- **Evidence Collection**: WARC archival for audit compliance

#### **Multilingual Support**
- **Language Detection**: polyglot for 165+ languages
- **Translation Pipeline**: LibreTranslate + NLLB ensemble
- **Multilingual OCR**: Tesseract with language-specific models
- **Cultural Context**: Perspective-aware evaluation for global sources

## 🛠️ Development Commands

All development commands are available through the Makefile. Run `make help` to see all available commands.

### Essential Commands

```bash
# Complete setup (infrastructure + all services)
make quick-start

# Infrastructure only (database, Redis, MinIO)
make quick-start-infra

# Check service health
make health-check

# Stop all application services
make stop-services

# View container logs
make logs              # Last 100 lines
make logs-follow       # Streaming (Ctrl+C to exit)
```

### Container Management

```bash
# Start all containers
make up

# Stop all containers  
make down

# Restart containers
make restart

# Rebuild service containers (after code changes)
make rebuild-services

# Clean up (interactive prompt)
make clean

# Force cleanup without prompt
make clean-force
```

### Database Operations

```bash
# Initialize database schema
make init-db

# Reset database (interactive, WARNING: destroys data)
make reset-db

# Force reset without prompt
make reset-db-force
```

### Local Development Services

For local development with hot reload:

```bash
# Start individual services locally
make start-api       # Backend API (port 8000)
make start-normalize # Normalize service (port 8001)
make start-assistant # AI Assistant (port 8002)
make start-web       # Frontend (port 6060)
```

**Note**: By default, backend services run in containers. Use these commands only if you need local development with hot reload.

### Development Tools

```bash
# Run tests
make test

# Format code (requires black and prettier)
make format

# Lint code (requires flake8 and eslint)
make lint

# Check environment configuration
make check-env

# Detect and configure IP address
make detect-ip
```

## 📁 Project Structure

```
LoreGuard/
├── apps/
│   ├── web/                    # React frontend application
│   │   ├── src/                # Source code
│   │   │   ├── components/     # UI components (8 pages + AI assistant)
│   │   │   └── ...
│   │   ├── package.json        # Frontend dependencies
│   │   └── vite.config.js      # Build configuration
│   │
│   ├── svc-api/                # FastAPI backend service
│   │   ├── app/                # Application code
│   │   │   ├── api/v1/         # REST API endpoints
│   │   │   ├── models/         # SQLAlchemy database models
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   └── ...
│   │   ├── Dockerfile          # Container definition
│   │   └── requirements.txt   # Python dependencies
│   │
│   ├── svc-normalize/          # Document processing service
│   ├── svc-assistant/          # AI Assistant service
│   └── svc-ingestion/          # Scrapy web crawler service
│
├── scripts/
│   ├── detect-ip.sh            # IP detection script
│   └── dev/                    # Development automation scripts
│       ├── init-databases.sh  # Database initialization
│       ├── health-check.sh     # Service health validation
│       ├── start-services.sh   # Service startup automation
│       └── ...
│
├── Planning/                   # Comprehensive planning documentation
│   ├── FinalTechnologyRoadmap.md
│   ├── EvaluationPipelinePlan.md
│   └── [other planning documents]
│
├── docker-compose.dev.yml      # Development container orchestration
├── Makefile                    # Development commands
├── .env.template              # Environment variable template
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

LoreGuard uses automatic IP detection via `make detect-ip`, which updates the `.env` file with your network IP. For manual configuration, you can create a `.env` file from `.env.template`.

**Key Configuration Options:**

```bash
# Database Configuration
POSTGRES_PASSWORD=secure_password_here

# Redis Configuration  
REDIS_PASSWORD=redis_password_here

# MinIO Object Storage
MINIO_ACCESS_KEY=loreguard
MINIO_SECRET_KEY=minio_password_here

# LLM Configuration (for AI Assistant)
OPENAI_API_KEY=your_openai_api_key
DEFAULT_LLM_MODEL=gpt-4
```

**Note**: Most configuration is handled automatically. The `make quick-start` command detects your IP and configures all services accordingly. Manual `.env` configuration is only needed for advanced scenarios.

### Service Ports

| Service | Port | URL | Purpose | Deployment |
|---------|------|-----|---------|------------|
| Frontend | 6060 | http://[YOUR_IP]:6060 | React development server (Vite) | Local (hot reload) |
| Backend API | 8000 | http://[YOUR_IP]:8000 | FastAPI REST API | Containerized |
| Normalize Service | 8001 | http://[YOUR_IP]:8001 | Document processing service | Containerized |
| AI Assistant | 8002 | http://[YOUR_IP]:8002 | Context-aware chatbot service | Containerized |
| Ingestion Service | - | - | Scrapy web crawler | Containerized (invoked via API) |
| PostgreSQL | 5432 | [YOUR_IP]:5432 | Database server | Containerized |
| Redis | 6379 | [YOUR_IP]:6379 | Cache and message broker | Containerized |
| MinIO API | 9000 | http://[YOUR_IP]:9000 | Object storage API | Containerized |
| MinIO Console | 9001 | http://[YOUR_IP]:9001 | Storage management UI | Containerized |

**Note**: Replace `[YOUR_IP]` with your detected IP address (shown after `make quick-start`).

## 🐳 Container Architecture

LoreGuard uses Docker Compose for orchestration. All backend services run in containers for consistency, while the frontend runs locally for optimal development experience.

### Infrastructure Services

- **PostgreSQL** (postgres:15) - Primary database
- **Redis** (redis:7-alpine) - Cache and message broker
- **MinIO** (minio/minio:latest) - S3-compatible object storage

### Application Services

- **loreguard-api** - FastAPI backend service (port 8000)
- **loreguard-normalize** - Document processing service (port 8001)
- **loreguard-assistant** - AI Assistant service (port 8002)
- **loreguard-ingestion** - Scrapy web crawler (invoked via API)

All services are defined in `docker-compose.dev.yml` and managed via Makefile commands.

## 🚨 Troubleshooting

### Quick Diagnostics

```bash
# Comprehensive health check
make health-check

# View container status
docker compose -f docker-compose.dev.yml ps

# View logs for specific service
make logs | grep [service-name]
```

### Common Issues

#### **Services Not Starting**

```bash
# Check if containers are running
docker compose -f docker-compose.dev.yml ps

# Check logs for errors
make logs

# Restart services
make restart

# If issues persist, rebuild containers
make rebuild-services
```

#### **Port Already in Use**

```bash
# Stop conflicting services
make stop-services

# Or find and kill process using port
sudo lsof -i :6060  # Frontend
sudo lsof -i :8000  # API
```

#### **Database Issues**

```bash
# Check database connection
make health-check

# Reinitialize database (WARNING: destroys data)
make reset-db-force

# Or just recreate schema
make init-db
```

#### **Frontend Build Errors**

```bash
# Clear and reinstall dependencies
cd apps/web
rm -rf node_modules package-lock.json
npm install
```

#### **Container Build Failures**

```bash
# Rebuild all services from scratch
make rebuild-services

# Check Docker resources
docker system df
docker system prune  # Clean up unused resources
```

### Reset Everything

```bash
# Complete reset (WARNING: destroys all data)
make clean-force
make quick-start
```

## 📚 Documentation

### Planning Documents

Comprehensive planning documentation is available in the [`Planning/`](./Planning/) directory:

- **[Executive Summary](./Planning/LoreGuardExecutiveSummary.md)** - Strategic overview for leadership
- **[Technology Roadmap](./Planning/FinalTechnologyRoadmap.md)** - Complete implementation blueprint  
- **[Evaluation Pipeline](./Planning/EvaluationPipelinePlan.md)** - LLM evaluation methodology
- **[Architecture Design](./Planning/TechArchitecture.md)** - Technical architecture details
- **[UX Design](./Planning/CoreUXDesign.md)** - User experience specifications

### API Documentation

After starting services, access API documentation at:

- **Interactive API Docs**: http://[YOUR_IP]:8000/docs (Swagger UI)
- **Alternative API Docs**: http://[YOUR_IP]:8000/redoc (ReDoc)
- **OpenAPI Schema**: http://[YOUR_IP]:8000/openapi.json

Replace `[YOUR_IP]` with your detected IP address (shown after `make quick-start`).

### Development Guides

- **Frontend Development**: See [`apps/web/README.md`](./apps/web/README.md)
- **Backend Development**: See [`apps/svc-api/README.md`](./apps/svc-api/README.md)
- **Database Schema**: See [`apps/svc-api/app/models/`](./apps/svc-api/app/models/)

## 🤝 Contributing

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Start Development Environment**
   ```bash
   make quick-start
   ```

3. **Make Changes**
   - Follow existing code patterns
   - Backend services auto-reload in containers
   - Frontend has hot reload enabled

4. **Test Changes**
   ```bash
   make health-check    # Verify services
   make test            # Run tests
   make lint            # Check code quality
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Describe changes and testing performed
   - Reference any related issues
   - Request review from team members

### Code Standards

- **Python**: Follow PEP 8, use Black formatter
- **JavaScript/React**: Follow Airbnb style guide, use Prettier
- **Commits**: Use conventional commit messages (feat:, fix:, docs:, etc.)
- **Documentation**: Update README and inline docs for any changes

## 📞 Support

### Development Team

**Headquarters Air Force Wargaming (HAF/WG)**  
**Air Force Wargaming Institute (AFWI)**

### Getting Help

1. **Check Documentation**: Review this README and planning docs in `Planning/` directory
2. **Run Health Checks**: Use `make health-check` to diagnose issues
3. **Review Logs**: Use `make logs` or `make logs-follow` to check container logs
4. **Check Service Status**: Use `docker compose -f docker-compose.dev.yml ps`
5. **Search Issues**: Look for similar problems in project issues
6. **Ask Questions**: Create detailed issue reports with reproduction steps

### Reporting Issues

When reporting issues, please include:
- **Environment**: OS version, Docker version, hardware specs
- **Steps to Reproduce**: Exact commands and actions taken
- **Expected vs Actual**: What should happen vs what actually happens
- **Logs**: Relevant error messages and stack traces
- **Configuration**: Relevant environment variables and settings

---

## 🎯 Next Steps

### Phase 2: Evaluation Pipeline (Current Priority)

The next major development phase focuses on implementing the LLM evaluation engine:

1. **Document Processing Pipeline**
   - Web crawling with Scrapy + Playwright
   - Document conversion with unstructured.io
   - OCR processing with Tesseract
   - Metadata extraction and normalization

2. **LLM Evaluation Engine**
   - OpenAI API integration
   - Pydantic validation for structured outputs
   - Configurable rubric system with UI editor
   - Confidence scoring and quality metrics

3. **Evidence Collection System**
   - WARC format archival for audit compliance
   - Clarification signal gathering
   - Provenance tracking and chain of custody
   - Legal and regulatory compliance features

4. **Multilingual Processing**
   - Language detection with polyglot
   - Translation pipeline with LibreTranslate
   - Cultural context awareness
   - Global perspective capture

### Implementation Timeline

- **Week 1-2**: Document processing pipeline
- **Week 3-4**: LLM evaluation engine
- **Week 5-6**: Evidence collection system
- **Week 7-8**: Multilingual support and testing

This foundation provides a solid base for rapid development of LoreGuard's core capabilities! 🚀

