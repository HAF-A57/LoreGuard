# LoreGuard Final Technology Roadmap

## Executive Summary

After comprehensive research across **18 key technology areas**, we have identified the complete technology stack for LoreGuard's development. This document provides the definitive technology roadmap for the development team to build a system that harvests global facts and perspectives from the Information Space, including all architectural decisions, implementation strategies, and deployment configurations.

## Complete Technology Stack (FINAL)

### ✅ **FULLY RESOLVED: All Core Technologies**

| Component | Final Recommendation | Key Features |
|-----------|---------------------|--------------|
| **Web Crawling** | Scrapy + Playwright hybrid | Anti-bot evasion, politeness controls, distributed crawling |
| **Document Processing** | unstructured.io + GROBID + Tesseract | Multi-tier processing, 20+ formats, academic specialization |
| **Object Storage** | MinIO (on-premises S3-compatible) | Full on-premises, encryption, lifecycle management |
| **Vector Database** | pgvector → Weaviate (scaling) | Start simple, scale to specialized vector operations |
| **Workflow Orchestration** | Temporal + Celery hybrid | Durable workflows + simple task processing |
| **UI Framework** | shadcn/ui + TanStack Table | Modern, accessible, virtualized tables for 100K+ rows |
| **Data Virtualization** | TanStack Virtual + React Query | 60fps scrolling, infinite loading, real-time updates |
| **LLM Validation** | Pydantic v2 + Zod (frontend) | Type-safe validation, error recovery, monitoring |
| **Evidence Storage** | WARC format + structured extraction | Legal compliance, comprehensive archival |
| **Language Detection** | polyglot | 165+ languages, offline, high accuracy |
| **Translation (Traditional)** | LibreTranslate | On-premises, 30+ languages, API compatible |
| **Translation (LLM)** | NLLB + Tower + Ollama | 200+ languages, context-aware, ensemble approach |
| **Multilingual OCR** | Tesseract + language packs | 100+ languages, script-specific optimization |
| **Calibration** | Stratified sampling + active learning | Inter-rater reliability, drift detection |
| **Signal Distribution** | Nextcloud Enterprise | DoD compliance, RBAC, automated workflows |
| **Backup Platform** | SharePoint (existing DoD) | Folder organization, metadata columns |

## Architecture Overview

### Phase 1: Foundation Architecture (0-10M Documents)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Crawlers  │    │   Document      │    │   PostgreSQL    │
│   (Scrapy)      │───▶│   Processing    │───▶│   + pgvector    │
│   + Playwright  │    │   (unstructured)│    │   + MinIO       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Temporal      │    │   LLM           │    │   Signal        │
│   Workflows     │    │   Evaluation    │    │   Distribution  │
│   + WARC        │    │   + Translation │    │   (Nextcloud)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Phase 2: Enterprise Scale (10M-100M Documents)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Distributed   │    │   Multi-Tier    │    │   Hybrid Vector │
│   Crawling      │───▶│   Processing    │───▶│   + Weaviate    │
│   (Redis Queue) │    │   + Translation │    │   Scaling       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Auto-Scaling  │    │   Ensemble      │    │   Multi-Platform│
│   Workers       │    │   Evaluation    │    │   Distribution  │
│   + Monitoring  │    │   + Calibration │    │   + Analytics   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Service Architecture (Microservices)

### Core Services
```yaml
# Complete service architecture
services:
  # Frontend
  loreguard-web:
    build: ./apps/web
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://loreguard-api:8000
    depends_on: [loreguard-api]

  # Main API Gateway
  loreguard-api:
    build: ./apps/svc-api
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/loreguard
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=http://minio:9000
    depends_on: [postgres, redis, minio]

  # Document ingestion
  loreguard-ingestion:
    build: ./apps/svc-ingestion
    environment:
      - SCRAPY_SETTINGS=loreguard.settings.production
      - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    volumes:
      - ./crawler-data:/app/data

  # Document processing
  loreguard-normalize:
    build: ./apps/svc-normalize
    environment:
      - UNSTRUCTURED_API_KEY=${UNSTRUCTURED_API_KEY}
      - GROBID_URL=http://grobid:8070
      - TESSERACT_CONFIG_PATH=/app/tesseract-configs
    volumes:
      - ./tesseract-models:/usr/share/tesseract-tessdata

  # Translation services
  loreguard-translate:
    build: ./apps/svc-translate
    environment:
      - LIBRETRANSLATE_URL=http://libretranslate:5000
      - NLLB_URL=http://nllb-server:5001
      - OLLAMA_URL=http://ollama:11434
    depends_on: [libretranslate, nllb-server, ollama]

  # LLM evaluation
  loreguard-evaluate:
    build: ./apps/svc-evaluate
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - PYDANTIC_VALIDATION=strict
    volumes:
      - ./rubrics:/app/rubrics

  # Evidence collection
  loreguard-clarify:
    build: ./apps/svc-clarify
    environment:
      - WARC_STORAGE_PATH=/app/evidence
      - EVIDENCE_RETENTION_DAYS=1095
    volumes:
      - ./evidence-storage:/app/evidence

  # Workflow orchestration
  temporal-server:
    image: temporalio/auto-setup:1.22
    ports: ["7233:7233", "8233:8233"]
    environment:
      - DB=postgresql
      - POSTGRES_SEEDS=postgres
    depends_on: [postgres]

  # Storage services
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=loreguard
      - POSTGRES_USER=loreguard
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d

  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    environment:
      - MINIO_ROOT_USER=loreguard
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    volumes:
      - ./minio-data:/data
    command: server /data --console-address ":9001"

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --requirepass ${REDIS_PASSWORD}

  # Translation models
  libretranslate:
    image: libretranslate/libretranslate:latest
    ports: ["5000:5000"]
    environment:
      - LT_LOAD_ONLY=en,zh,ru,ar,es,fr,de,ja,ko,fa,ur,hi
    volumes:
      - ./libretranslate-models:/app/db

  nllb-server:
    build: ./translation-services/nllb
    ports: ["5001:5001"]
    environment:
      - MODEL_SIZE=1.3B
      - TORCH_DEVICE=cuda
    volumes:
      - ./nllb-models:/app/models

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ./ollama-models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

  # Document sharing
  nextcloud:
    image: nextcloud:28-apache
    ports: ["8080:80"]
    environment:
      - POSTGRES_DB=nextcloud
      - POSTGRES_USER=nextcloud
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
      - POSTGRES_HOST=nextcloud-db
    volumes:
      - ./nextcloud-data:/var/www/html
      - ./signal-documents:/var/www/html/data/shared
    depends_on: [nextcloud-db]

  nextcloud-db:
    image: postgres:15
    environment:
      - POSTGRES_DB=nextcloud
      - POSTGRES_USER=nextcloud
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
    volumes:
      - ./nextcloud-db:/var/lib/postgresql/data
```

## Implementation Phases

### Phase 1: Core Foundation (Months 1-2)
**Deliverables:**
- [ ] Scrapy + Playwright crawler with sample sources
- [ ] unstructured.io + Tesseract document processing
- [ ] PostgreSQL + pgvector semantic search
- [ ] Temporal workflow orchestration
- [ ] MinIO object storage with lifecycle policies
- [ ] Basic React frontend with shadcn/ui

**Success Criteria:**
- Process 1,000 documents/day
- 90%+ document processing success rate
- <2 hour source-to-processed pipeline
- Basic three-pane UI functional

### Phase 2: Evaluation Pipeline (Months 2-3)
**Deliverables:**
- [ ] OpenAI LLM evaluation with Pydantic validation
- [ ] Configurable rubric system with UI editor
- [ ] WARC evidence collection and archival
- [ ] polyglot language detection
- [ ] LibreTranslate integration for basic translation

**Success Criteria:**
- 95%+ evaluation completion rate
- <30 minute evaluation pipeline per document
- Structured evaluation outputs with confidence scores
- Evidence archival for audit trails

### Phase 3: Advanced Features (Months 3-4)
**Deliverables:**
- [ ] NLLB + Tower LLM translation models
- [ ] TanStack virtualization for 100K+ row tables
- [ ] Human calibration interface with active learning
- [ ] Nextcloud Signal document distribution
- [ ] Advanced monitoring and alerting

**Success Criteria:**
- Handle 10,000+ artifacts in UI smoothly
- Multi-language document processing
- Human annotation workflow operational
- Automated Signal distribution to DoD community

### Phase 4: Enterprise Scale (Months 4-6)
**Deliverables:**
- [ ] Weaviate vector database scaling
- [ ] Distributed crawler deployment
- [ ] Advanced analytics and reporting
- [ ] MAGE integration via shared APIs
- [ ] Performance optimization and tuning

**Success Criteria:**
- 10,000+ documents processed/day
- <1 second search response times
- 99.5% system uptime
- Full MAGE integration operational

## Cost Summary (Updated with All Components)

### Development Costs (6 months)
- **Personnel**: $600K (5 engineers × 6 months)
- **Infrastructure**: $50K (development environments + GPU servers)
- **Software Licenses**: $30K (Nextcloud Enterprise, monitoring tools)
- **Translation Models**: $15K (GPU infrastructure for NLLB/Tower)
- **Total Development**: $695K

### Annual Operational Costs
- **Infrastructure**: $75K (on-premises servers, storage, networking)
- **Software Licenses**: $40K (Nextcloud Enterprise, support contracts)
- **LLM Costs**: $0 (on-premises models, no API fees)
- **Personnel**: $300K (2.5 FTE for operations and maintenance)
- **Power/Cooling**: $25K (additional power for GPU servers)
- **Total Annual Operations**: $440K

### Hardware Requirements Summary
- **Crawler Nodes**: 4 × (8 CPU, 32GB RAM) = $40K
- **Processing Nodes**: 4 × (16 CPU, 64GB RAM) = $60K
- **GPU Servers**: 2 × (8 CPU, 64GB RAM, RTX 4090) = $40K
- **Storage**: 200TB enterprise storage = $50K
- **Network**: 10Gb switches and cabling = $20K
- **Total Hardware**: $210K

## Risk Assessment (Final)

### Technical Risks (Mitigated)
| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|-------------------|
| Translation quality drift | Medium | Medium | Ensemble models + human calibration |
| Vector database performance | Low | Medium | Phased scaling with Weaviate option |
| Crawler detection/blocking | High | Low | Multi-proxy rotation + politeness controls |
| LLM evaluation inconsistency | Medium | High | Pydantic validation + confidence thresholds |

### Operational Risks (Addressed)
| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|-------------------|
| Storage capacity growth | High | Medium | Automated lifecycle policies + archival |
| Security compliance | Low | High | DoD-compliant deployment + audit trails |
| Performance degradation | Medium | Medium | Monitoring + auto-scaling + optimization |
| Knowledge transfer | Medium | Medium | Comprehensive documentation + training |

## Success Metrics (Comprehensive)

### Technical KPIs
- **Throughput**: 10,000+ documents processed/day
- **Accuracy**: 90%+ precision on Signal classification
- **Performance**: <1 second search response, 60fps table scrolling
- **Availability**: 99.5% uptime with <4 hour recovery
- **Multilingual**: 95%+ accuracy for top 20 languages
- **Evidence**: 100% WARC archival for audit compliance

### Business KPIs
- **Analyst Productivity**: 10x increase in documents reviewed
- **Time-to-Insight**: 90% reduction in research time
- **Source Coverage**: 100x increase in monitored sources
- **Quality**: 95%+ analyst satisfaction with Signal recommendations
- **Distribution**: <1 hour Signal-to-community sharing
- **Compliance**: 100% audit trail coverage

## Deployment Strategy (Complete)

### Development Environment
```bash
# Complete development setup
git clone https://github.com/af-wargaming/loreguard.git
cd loreguard

# Set up environment variables
cp .env.template .env
# Edit .env with local configuration

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Initialize databases
make init-databases

# Load sample data
make load-sample-data

# Start development servers
make dev-start
```

### Production Deployment
```bash
# Production deployment checklist
□ Hardware provisioned (210K budget allocated)
□ Network configured (10Gb internal, secure external)
□ Storage configured (MinIO cluster + PostgreSQL)
□ Security hardened (encryption, RBAC, audit logging)
□ Monitoring deployed (Prometheus + Grafana + alerts)
□ Backup systems configured (automated + tested)
□ Documentation complete (operations + user guides)
□ Staff trained (administrators + analysts)
□ Security review passed (DoD compliance verified)
□ Performance tested (10K documents/day validated)
```

## Integration Points with MAGE

### Shared Components
- **LLM Providers**: OpenAI-compatible API abstraction
- **Authentication**: SAML/LDAP integration with existing DoD identity
- **UI Patterns**: Three-pane layout, dark/light themes, consistent styling
- **Vector Search**: Shared semantic search capabilities
- **Document Library**: Common artifact access via REST APIs

### Data Flow Integration
```python
# MAGE integration service
class MAGEIntegrationService:
    def __init__(self):
        self.mage_api = MAGEAPIClient()
        self.loreguard_api = LoreGuardAPIClient()
    
    async def sync_signal_documents_to_mage(self):
        """Sync new Signal documents to MAGE library"""
        
        # Get new Signal documents from LoreGuard
        new_signals = await self.loreguard_api.get_signal_documents(
            since=datetime.utcnow() - timedelta(hours=24)
        )
        
        for signal in new_signals:
            # Prepare document for MAGE
            mage_document = {
                'title': signal['title'],
                'content': signal['content'],
                'metadata': signal['metadata'],
                'vectors': signal['vectors'],
                'loreguard_id': signal['id'],
                'confidence_score': signal['confidence'],
                'evaluation_summary': signal['evaluation_summary']
            }
            
            # Add to MAGE library
            await self.mage_api.add_library_document(mage_document)
```

## Quality Assurance Framework

### Testing Strategy
- **Unit Tests**: 90%+ code coverage across all services
- **Integration Tests**: End-to-end pipeline testing
- **Performance Tests**: Load testing with 100K+ documents
- **Security Tests**: Penetration testing and vulnerability assessment
- **User Acceptance**: Testing with actual wargaming analysts

### Monitoring and Observability
- **Metrics**: Prometheus + Grafana dashboards for all services
- **Logging**: Centralized logging with ELK stack
- **Tracing**: OpenTelemetry for distributed request tracing
- **Alerting**: PagerDuty integration for critical issues
- **Health Checks**: Automated health monitoring with auto-recovery

## Documentation Deliverables

### Technical Documentation
- [ ] **API Documentation**: OpenAPI specs for all services
- [ ] **Deployment Guide**: Step-by-step production deployment
- [ ] **Operations Manual**: System administration and maintenance
- [ ] **Security Guide**: Security configuration and compliance
- [ ] **Performance Tuning**: Optimization guidelines and benchmarks

### User Documentation
- [ ] **User Manual**: Complete user interface guide
- [ ] **Administrator Guide**: System configuration and management
- [ ] **Analyst Workflow**: Document evaluation and curation workflows
- [ ] **Integration Guide**: MAGE integration and data sharing
- [ ] **Troubleshooting**: Common issues and resolution procedures

## Conclusion

The LoreGuard technology stack is now fully defined with **18 critical technology areas researched and decided**. The architecture balances:

- **Reliability**: Proven, battle-tested technologies
- **Scalability**: Phased growth from prototype to enterprise scale
- **Security**: DoD-compliant, on-premises deployment
- **Performance**: Optimized for 100K+ document scale
- **Maintainability**: Open-source technologies with strong communities
- **Cost-Effectiveness**: $695K development, $440K annual operations

**Key Differentiators:**
- **Zero Cloud Dependencies**: Fully air-gapped capable
- **Multilingual Excellence**: 200+ language support with LLM translation
- **Evidence-Based**: WARC archival for complete audit trails
- **Human-Calibrated**: Continuous quality assurance with expert feedback
- **MAGE Integrated**: Seamless workflow with existing wargaming systems

The development team now has a **complete blueprint** for implementing LoreGuard, from initial development through enterprise deployment and ongoing operations. All major technology decisions have been researched, validated, and documented with implementation examples.

## Next Action Items

### Week 1: Project Kickoff
- [ ] Assemble 5-person development team
- [ ] Set up development infrastructure (Docker Compose)
- [ ] Create project repositories and CI/CD pipelines
- [ ] Begin Sprint 1 implementation (crawler + basic processing)

### Month 1: Core Pipeline
- [ ] Functional document ingestion and processing
- [ ] Basic LLM evaluation pipeline
- [ ] PostgreSQL + pgvector semantic search
- [ ] Temporal workflow orchestration

### Month 3: Full Pipeline
- [ ] Complete evaluation pipeline with calibration
- [ ] Multilingual processing with translation
- [ ] Evidence collection with WARC archival
- [ ] React frontend with virtualized tables

### Month 6: Enterprise Ready
- [ ] Nextcloud Signal distribution
- [ ] MAGE integration complete
- [ ] Performance optimized for target scale
- [ ] Security review and DoD compliance validation

**LoreGuard is ready for development. All research complete. Technology stack finalized for global facts and perspectives harvesting. Implementation roadmap established.**
