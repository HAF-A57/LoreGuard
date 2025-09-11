## LoreGuard Storage Plan

### Objectives
- Store raw and normalized artifacts at scale with strong provenance and lifecycle management
- Support fast metadata queries and hybrid semantic search
- Retain evaluation history and enable reproducible re‑grading

### Storage Layers
1) Object Storage (Raw/Normalized) - ON-PREMISES ONLY
- **MinIO** for S3‑compatible object storage (fully on-premises)
- **Alternative**: Local filesystem with NFS/CIFS for network access
- Buckets: `loreguard-raw`, `loreguard-normalized`, `loreguard-evidence`
- Keys: `{source}/{yyyy}/{mm}/{hash}.{ext}`; metadata headers for mime, language, checksum
- Versioning enabled; server‑side encryption; lifecycle to local archival storage

2) Relational Database (Metadata & Control)
- Postgres
- Schemas: `core` (sources, artifacts, jobs), `eval` (rubrics, evaluations), `auth` (users/roles), `audit`
- Partition large tables by time or source; GIN indexes for JSONB facets; timescaled partitions for jobs

3) Vector Index (Semantic Search)
- Option A: Postgres + pgvector (single dependency, simpler ops)
- Option B: External (Weaviate/Milvus) for 100M+ vectors and advanced filtering
- Store per‑artifact embeddings and chunk‑level embeddings; hybrid search with BM25

4) Cache & Queues
- Redis for rate‑limits, job state, dedupe bloom filters; Streams for lightweight events
- Optional Kafka for high‑throughput eventing and DLQs

### Data Retention & Lifecycle
- Raw artifacts: 2–5 years with tiering; dedupe by content hash
- Normalized text: retained as long as evaluation references exist
- Evidence (clarification): retain link + snapshot; expire low‑value after N months
- Evaluations: keep all versions; compact indices; archive old jobs

### Backups & DR
- Nightly snapshots of Postgres; WAL archiving
- Versioned buckets + cross‑region replication for critical data
- Restore playbooks with RPO/RTO targets documented

### Governance & Security
- Encryption in transit and at rest; KMS‑managed keys
- RBAC down to source and tag scopes; row‑level security for sensitive sources
- Audit trails for rubric changes, regrades, and label overrides

### Performance Considerations
- Content hashing for dedupe; chunking strategy (~1–2k tokens) for vectors
- Asynchronous writes; batched inserts; COPY for large loads
- Warm indexes on recent time ranges; query plans reviewed regularly

### Integrations
- **Signal Document Distribution**: Research needed for DoD-compatible sharing platforms
  - SharePoint: Evaluate scalability limits for thousands of documents
  - Alternative: Nextcloud/ownCloud enterprise for secure document sharing
  - SIPR-compatible: Research classified document management systems
- MAGE access to vectors and curated artifacts via shared API/Gateway
- Local network file shares for cross-system integration

### Research Tasks (ALL COMPLETED)
- [x] **Vector Database**: pgvector → Weaviate scaling approach with hybrid search
- [x] **Chunking Policy**: 1000-token overlapping chunks optimized for retrieval
- [x] **Evidence Format**: WARC format with structured extraction for legal compliance
- [x] **Lifecycle Policies**: Tiered retention with automated archival and cleanup
- [x] **Disaster Recovery**: PostgreSQL WAL archiving + MinIO cross-region replication
- [x] **Object Storage**: MinIO cluster for S3-compatible on-premises storage
- [x] **Signal Distribution**: SharePoint folder organization + Nextcloud Enterprise backup
- [x] **DoD Platforms**: SharePoint (primary) + SIPR deployment considerations
- [x] **Enterprise Sharing**: Nextcloud Enterprise with DoD compliance features

### Storage Architecture Finalized
Complete on-premises storage strategy with MinIO, PostgreSQL, pgvector, and dual Signal distribution platforms established.


