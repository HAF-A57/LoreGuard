## LoreGuard Technical Architecture

### Audience
Engineering and platform teams. This document specifies services, data contracts, and infrastructure choices to support large‑scale retrieval and LLM evaluation.

### Architectural Goals
- Horizontally scalable retrieval and processing of global facts and perspectives
- Strong provenance, auditability, and reproducibility for diverse viewpoints
- Configurable, versioned rubrics and prompts for perspective evaluation
- Efficient storage across raw, normalized, and vectorized views
- Interop with MAGE (LLM providers, UI shell, auth) for roleplay scenario support

### High‑Level System
- API Gateway / Web App
- Orchestrator (workflow engine)
- Ingestion (crawlers/fetchers for global perspectives)
- Normalization (convert/OCR, extract metadata and viewpoints)
- Clarification (targeted web checks, reputation lookups)
- Evaluation (LLM scoring of facts and perspectives, ensembles, thresholds)
- Storage (object store, relational DB, vector index)
- Scheduler and Queues
- Observability (logs, traces, metrics), Governance (audit, versions)

### Services
- `svc-loreguard-api` (FastAPI): REST + WebSockets; RBAC, jobs, CRUD for Sources/Artifacts/Rubrics
- `svc-ingestion`: crawl/scrape, sitemap/API/feeds, dedup, robots/politeness, rotating IPs
- `svc-normalize`: file conversion, MIME sniff, OCR (PDF/scan), text/structure extraction
- `svc-clarify`: author/org reputation checks, citations, cross‑site corroboration
- `svc-evaluate`: rubric application, LLM calls, calibration, versioned results
- `svc-scheduler`: schedules, retries, blackout windows
- `svc-worker`: general task workers (idempotent)

### Orchestration & Messaging
- Workflow engine: Temporal or Prefect for durable, versioned workflows
- Task queue: Redis Streams or RabbitMQ; optional Kafka for high‑throughput event streams
- Patterns: outbox for reliable events; idempotency keys per artifact hash

### Data Model (Core Entities)
- `Source(id, type, config, schedule, status, last_run, tags)`
- `Artifact(id, source_id, uri, content_hash, mime, created_at, version, normalized_ref)`
- `Metadata(artifact_id, title, authors, org, pub_date, topics, geo, language)`
- `Clarification(artifact_id, signals{author_reputation, org_type, citations,...}, evidence_ref)`
- `Evaluation(artifact_id, rubric_version, model_id, scores{...}, label, confidence, prompt_ref)`
- `Rubric(version, categories{weight, criteria}, thresholds, prompts)`
- `Job(id, type, status, timeline[], retries, error)`
- `LibraryItem(artifact_id, snapshot_id, tags)`

### Storage (ON-PREMISES ONLY)
- **Object store**: MinIO for S3‑compatible storage (fully on-premises deployment)
- **Relational DB**: PostgreSQL for metadata, jobs, rubrics, audit; use partitioning for scale
- **Vector index**: pgvector extension or external (Weaviate/Milvus) with HNSW/IVF; hybrid search via BM25 + vectors
- **Caches**: Redis for rate limits, job state, and feature flags
- **Signal Distribution**: Research DoD-compatible platforms for sharing curated documents

### LLM and Prompting
- Provider abstraction: OpenAI‑compatible API; per‑task model selection (clarify vs evaluate)
- Prompt versioning and templates; structured outputs via JSON schema
- Safety: prompt hardening, input sanitization, timeouts, budget caps

### Pipelines (Happy Path)
1. Ingest: discover → fetch → dedup (hash) → emit Artifact
2. Normalize: convert/OCR → extract text/structure → extract metadata
3. Clarify: targeted web queries → evidence store → signals map
4. Evaluate: rubric(version)+model → scores, label, confidence → store
5. Persist: write vectors, promote Signal to Library, notify
6. Refresh: re‑scan sources; fetch only changed; re‑evaluate net‑new

### Regrading
- Rubric changes emit a regrade job over prior artifacts; batch with backpressure
- Store both old and new results; compute deltas; update Library labels transactionally

### Security and Compliance
- RBAC, audit logs, signed rubric versions, artifact provenance
- Network egress controls, source allow/block lists, sandboxed renderers
- Encryption at rest/in transit; secrets in Vault; per‑service least privilege

### Observability
- Centralized logs (ELK or OpenSearch), tracing (OpenTelemetry), metrics (Prometheus/Grafana)
- SLOs per stage; dead‑letter queues; redrive tools

### Deployment
- Containers per service; compose for dev; Kubernetes for prod (HPA, VPA)
- Migrations via Alembic; vector index migrations scripted

### Interfaces (Examples)
- REST: `/sources`, `/artifacts`, `/evaluate`, `/rubrics`, `/jobs`
- Webhooks: job completed/failed; rubric published; source unhealthy
- Event topics: `artifact.created`, `artifact.normalized`, `artifact.evaluated`

### Research Tasks (ALL COMPLETED)
- [x] **Workflow Engine**: Temporal + Celery hybrid architecture finalized
- [x] **Crawler Stack**: Scrapy + Playwright hybrid with anti-bot evasion
- [x] **Document Processing**: unstructured.io + GROBID + Tesseract tiered pipeline
- [x] **Vector Database**: pgvector → Weaviate scaling strategy established
- [x] **JSON Schema Validation**: Pydantic v2 with OpenAI function calling integration
- [x] **Calibration Methodology**: Stratified sampling + active learning + inter-rater reliability
- [x] **On-Premises Storage**: MinIO cluster deployment with lifecycle policies
- [x] **Signal Distribution**: Nextcloud Enterprise + SharePoint backup approach
- [x] **UI Framework**: shadcn/ui + TanStack virtualization for large datasets
- [x] **Translation**: LibreTranslate + NLLB + Tower ensemble approach
- [x] **Evidence Archival**: WARC format with structured extraction pipeline

### Implementation Ready
Complete technology stack defined. All architectural decisions made. Ready for development phase.


