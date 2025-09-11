# LoreGuard

**Automated Facts and Perspectives Harvesting for Military Wargaming**

LoreGuard is a companion system to the Multi-Agent Generative Engine (MAGE) designed to automatically discover, retrieve, evaluate, and curate open-source artifacts from thousands of global sources. The system captures diverse facts and perspectives from the Information Space to support Air Force wargaming operations.

## 🚀 Quick Start

### Prerequisites

- **Ubuntu 22.04 LTS** (recommended development environment)
- **Docker** and **Docker Compose** v2.0+
- **Node.js** 18+ and **npm**
- **Python** 3.11+
- **Git**
- **8GB RAM minimum** (16GB recommended)
- **50GB free disk space**

### One-Command Setup

```bash
# Clone and start LoreGuard
git clone https://github.com/HAF-A57/LoreGuard.git
cd LoreGuard
./scripts/dev/quick-start.sh
```

This script will:
- ✅ Install all dependencies
- ✅ Set up environment variables
- ✅ Build and start all containers
- ✅ Initialize databases with sample data
- ✅ Create default admin user
- ✅ Start development servers

**Default Login:**
- **URL**: http://localhost:6060
- **Username**: admin@airforcewargaming.com  
- **Password**: LoreGuard2024!

**Note**: The application now uses "artifact" terminology throughout instead of "document" for better consistency.

## 📋 Manual Setup (Step by Step)

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/HAF-A57/LoreGuard.git
cd LoreGuard

# Copy environment template
cp .env.template .env

# Edit environment variables (optional)
nano .env
```

### 3. Start Infrastructure Services

```bash
# Start databases and core services
docker-compose -f docker-compose.dev.yml up -d postgres redis minio

# Wait for services to be ready
./scripts/dev/wait-for-services.sh

# Initialize databases
./scripts/dev/init-databases.sh
```

### 4. Start Application Services

```bash
# Start backend API
cd apps/svc-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main &

# Start frontend (new terminal)
cd apps/web
npm install
npm run dev &
```

### 5. Verify Installation

```bash
# Check all services are running
./scripts/dev/health-check.sh

# Expected output:
# ✅ PostgreSQL: Connected
# ✅ Redis: Connected  
# ✅ MinIO: Connected
# ✅ Backend API: Healthy
# ✅ Frontend: Running on http://localhost:6060
```

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
- **AI Assistant Integration**: Context-aware chatbot with LoreGuard knowledge
- **Authentication Flow**: Login system with loading screens
- **Responsive Design**: Mobile-friendly with dark/light mode
- **Professional UI**: Air Force Wargaming branding with official LoreGuard logo
- **Enhanced Accessibility**: Improved text contrast and visibility
- **Consistent Terminology**: Uses "artifact" terminology throughout for clarity

#### **Backend Services**
- **REST API**: FastAPI with OpenAPI documentation
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

### Container Management

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Stop all services  
docker-compose -f docker-compose.dev.yml down

# Rebuild containers
docker-compose -f docker-compose.dev.yml up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f [service-name]

# Reset everything (WARNING: destroys data)
./scripts/dev/reset-environment.sh
```

### Database Operations

```bash
# Initialize databases
./scripts/dev/init-databases.sh

# Load sample data
./scripts/dev/load-sample-data.sh

# Backup database
./scripts/dev/backup-database.sh

# Restore database
./scripts/dev/restore-database.sh [backup-file]

# Run migrations
cd apps/svc-api && alembic upgrade head
```

### Development Servers

```bash
# Start backend API (development mode)
cd apps/svc-api
source venv/bin/activate
python -m app.main

# Start frontend (development mode)
cd apps/web
npm run dev

# Start both with hot reload
./scripts/dev/start-dev-servers.sh
```

### Testing and Validation

```bash
# Run backend tests
cd apps/svc-api
python -m pytest tests/

# Run frontend tests
cd apps/web
npm test

# Run integration tests
./scripts/dev/run-integration-tests.sh

# Validate API endpoints
./scripts/dev/test-api-endpoints.sh
```

## 📁 Project Structure

```
LoreGuard/
├── apps/
│   ├── web/                    # React frontend application
│   │   ├── src/
│   │   │   ├── components/     # UI components (8 pages + AI assistant)
│   │   │   ├── App.jsx         # Main application component
│   │   │   └── App.css         # Aulendur design system styles
│   │   ├── package.json        # Frontend dependencies
│   │   └── vite.config.js      # Build configuration
│   │
│   └── svc-api/                # FastAPI backend service
│       ├── app/
│       │   ├── api/v1/         # REST API endpoints
│       │   ├── models/         # SQLAlchemy database models
│       │   ├── schemas/        # Pydantic request/response schemas
│       │   ├── db/             # Database configuration
│       │   ├── core/           # Configuration and settings
│       │   └── main.py         # FastAPI application entry point
│       ├── requirements.txt    # Python dependencies
│       └── .env               # Environment configuration
│
├── scripts/
│   └── dev/                    # Development automation scripts
│       ├── quick-start.sh      # One-command setup
│       ├── init-databases.sh   # Database initialization
│       ├── health-check.sh     # Service health validation
│       └── reset-environment.sh # Complete environment reset
│
├── Planning/                   # Comprehensive planning documentation
│   ├── FinalTechnologyRoadmap.md
│   ├── EvaluationPipelinePlan.md
│   └── [18 other planning documents]
│
├── docker-compose.dev.yml      # Development container orchestration
├── .env.template              # Environment variable template
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://loreguard:password@localhost:5432/loreguard
POSTGRES_PASSWORD=secure_password_here

# Redis Configuration  
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=redis_password_here

# MinIO Object Storage
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=loreguard
MINIO_SECRET_KEY=minio_password_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:6060

# Frontend Configuration
VITE_API_URL=http://localhost:8000

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here
ADMIN_EMAIL=admin@airforcewargaming.com
ADMIN_PASSWORD=LoreGuard2024!
```

### Service Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Frontend | 6060 | http://localhost:6060 | React development server (Vite) |
| Backend API | 8000 | http://localhost:8000 | FastAPI REST API |
| PostgreSQL | 5432 | localhost:5432 | Database server |
| Redis | 6379 | localhost:6379 | Cache and message broker |
| MinIO | 9000 | http://localhost:9000 | Object storage API |
| MinIO Console | 9001 | http://localhost:9001 | Storage management UI |

## 🐳 Container Services

### Core Infrastructure

```yaml
# PostgreSQL Database
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: loreguard
    POSTGRES_USER: loreguard
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./scripts/dev/init-db.sql:/docker-entrypoint-initdb.d/init.sql

# Redis Cache
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data

# MinIO Object Storage
minio:
  image: minio/minio:latest
  environment:
    MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
    MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
  volumes:
    - minio_data:/data
  command: server /data --console-address ":9001"
```

### Application Services

```yaml
# Backend API
loreguard-api:
  build: ./apps/svc-api
  environment:
    DATABASE_URL: postgresql://loreguard:${POSTGRES_PASSWORD}@postgres:5432/loreguard
    REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    MINIO_ENDPOINT: http://minio:9000
  depends_on:
    - postgres
    - redis
    - minio

# Frontend Web App
loreguard-web:
  build: ./apps/web
  environment:
    VITE_API_URL: http://localhost:8000
  depends_on:
    - loreguard-api
```

## 🚨 Troubleshooting

### Common Issues

#### **Port Already in Use**
```bash
# Find process using port
sudo lsof -i :6060
sudo lsof -i :8000

# Kill process
sudo kill -9 [PID]

# Or use different ports in .env
```

#### **Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check database logs
docker-compose -f docker-compose.dev.yml logs postgres

# Reinitialize database
./scripts/dev/init-databases.sh
```

#### **Frontend Build Errors**
```bash
# Clear node modules and reinstall
cd apps/web
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
npm run dev -- --force
```

#### **Backend Import Errors**
```bash
# Recreate virtual environment
cd apps/svc-api
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Health Check Commands

```bash
# Check all service health
./scripts/dev/health-check.sh

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/test/ping

# Test database connection
curl http://localhost:8000/api/v1/test/db-test

# Test frontend
curl http://localhost:6060
```

### Reset Environment

```bash
# Complete reset (WARNING: destroys all data)
./scripts/dev/reset-environment.sh

# Selective reset
docker-compose -f docker-compose.dev.yml down -v  # Remove volumes
docker system prune -f                            # Clean Docker
./scripts/dev/quick-start.sh                      # Restart fresh
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

- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

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

2. **Make Changes**
   - Follow existing code patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Changes**
   ```bash
   ./scripts/dev/run-tests.sh
   ./scripts/dev/health-check.sh
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
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

1. **Check Documentation**: Review planning docs and README sections
2. **Run Health Checks**: Use `./scripts/dev/health-check.sh` to diagnose issues
3. **Review Logs**: Check container logs for error details
4. **Search Issues**: Look for similar problems in project issues
5. **Ask Questions**: Create detailed issue reports with reproduction steps

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

