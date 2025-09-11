## Evidence Storage Format Research: WARC vs HTML Snapshot vs Text Extract

### Executive Summary
For LoreGuard's clarification pipeline, we need to store evidence from web searches used to evaluate document credibility and context. This includes author reputation checks, organization verification, and cross-reference validation. Based on research, **WARC format with selective HTML snapshots** emerges as the recommended approach for comprehensive evidence preservation.

### Storage Format Comparison

#### WARC (Web ARChive) Format (Recommended)
**Strengths:**
- **Industry Standard**: ISO 28500 standard for web archiving
- **Complete Preservation**: Captures HTTP headers, response metadata, timestamps
- **Legal Compliance**: Maintains chain of custody for evidence
- **Compression**: Built-in gzip compression reduces storage requirements
- **Metadata Rich**: Stores request/response pairs with full context
- **Tool Support**: Extensive ecosystem of tools and libraries
- **Long-term Viability**: Designed for archival purposes

**Structure:**
```
WARC/1.1
WARC-Type: response
WARC-Target-URI: https://example.com/author-profile
WARC-Date: 2024-01-15T10:30:00Z
WARC-Record-ID: <urn:uuid:12345678-1234-5678-9012-123456789abc>
WARC-IP-Address: 192.0.2.1
WARC-Payload-Digest: sha1:B2LTWWPUOYAH7UIPQ7ZUPQ64BODY
Content-Type: application/http; msgtype=response
Content-Length: 1024

HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 512
Date: Mon, 15 Jan 2024 10:30:00 GMT

<!DOCTYPE html>
<html>
<head><title>Dr. John Smith - Research Profile</title></head>
<body>...</body>
</html>
```

**Use Cases:**
- Author reputation verification searches
- Organization credibility checks  
- Cross-reference validation
- Citation verification
- Publication venue assessment

#### HTML Snapshot (Selective Use)
**Strengths:**
- **Human Readable**: Easy to review and debug
- **Lightweight**: Smaller than full WARC records
- **Fast Processing**: Quick to parse and analyze
- **Visual Preservation**: Maintains page layout and styling

**Weaknesses:**
- **Incomplete**: Missing HTTP headers and metadata
- **No Request Context**: Lost information about how page was accessed
- **Limited Forensic Value**: Insufficient for legal evidence
- **Link Rot**: External resources may not be preserved

**Use Cases:**
- Quick reference snapshots
- Visual evidence for human reviewers
- Lightweight caching for frequently accessed pages

#### Text Extract Only (Minimal)
**Strengths:**
- **Minimal Storage**: Smallest footprint
- **Fast Search**: Easy to index and search
- **Privacy Friendly**: Removes tracking pixels and scripts

**Weaknesses:**
- **Context Loss**: Missing visual layout and structure
- **Incomplete Evidence**: Insufficient for credibility assessment
- **No Metadata**: Lost timing and source information
- **Limited Forensic Value**: Poor audit trail

**Use Cases:**
- Content analysis only
- Search indexing
- Privacy-sensitive scenarios

### Recommended Architecture: Hybrid WARC Approach

#### Tier 1: Full WARC Records (Critical Evidence)
```python
# WARC creation for critical evidence
import warcio
from warcio.warcwriter import WARCWriter
import requests
import hashlib
from datetime import datetime

class EvidenceArchiver:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        
    def archive_evidence(self, url: str, purpose: str, artifact_id: str) -> str:
        """Archive web evidence in WARC format"""
        
        # Make request with proper headers
        headers = {
            'User-Agent': 'LoreGuard-Evidence-Collector/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        # Generate WARC filename
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        warc_filename = f"evidence-{artifact_id}-{timestamp}.warc.gz"
        warc_path = os.path.join(self.storage_path, warc_filename)
        
        with open(warc_path, 'wb') as output:
            writer = WARCWriter(output, gzip=True)
            
            # Create request record
            request_data = f"GET {url} HTTP/1.1\r\n"
            for key, value in headers.items():
                request_data += f"{key}: {value}\r\n"
            request_data += "\r\n"
            
            request_record = writer.create_warc_record(
                uri=url,
                record_type='request',
                payload=BytesIO(request_data.encode()),
                warc_headers_dict={
                    'WARC-Date': datetime.utcnow().isoformat() + 'Z',
                    'Content-Type': 'application/http; msgtype=request',
                    'LoreGuard-Purpose': purpose,
                    'LoreGuard-Artifact-ID': artifact_id
                }
            )
            writer.write_record(request_record)
            
            # Create response record
            response_data = f"HTTP/1.1 {response.status_code} {response.reason}\r\n"
            for key, value in response.headers.items():
                response_data += f"{key}: {value}\r\n"
            response_data += "\r\n"
            response_data += response.text
            
            response_record = writer.create_warc_record(
                uri=url,
                record_type='response',
                payload=BytesIO(response_data.encode()),
                warc_headers_dict={
                    'WARC-Date': datetime.utcnow().isoformat() + 'Z',
                    'Content-Type': 'application/http; msgtype=response',
                    'WARC-IP-Address': self._resolve_ip(url),
                    'WARC-Payload-Digest': f"sha1:{hashlib.sha1(response.content).hexdigest()}",
                    'LoreGuard-Purpose': purpose,
                    'LoreGuard-Artifact-ID': artifact_id
                }
            )
            writer.write_record(response_record)
        
        return warc_path
```

#### Tier 2: Structured Evidence Extraction
```python
# Extract structured evidence from WARC records
from bs4 import BeautifulSoup
import json

class EvidenceExtractor:
    def __init__(self):
        self.extractors = {
            'author_reputation': self._extract_author_info,
            'organization_info': self._extract_org_info,
            'citation_verification': self._extract_citation_info,
            'publication_venue': self._extract_venue_info
        }
    
    def extract_evidence(self, warc_path: str, purpose: str) -> dict:
        """Extract structured evidence from WARC file"""
        
        evidence = {
            'warc_file': warc_path,
            'extraction_time': datetime.utcnow().isoformat(),
            'purpose': purpose,
            'findings': {}
        }
        
        with open(warc_path, 'rb') as stream:
            for record in warcio.ArchiveIterator(stream):
                if record.rec_type == 'response':
                    url = record.rec_headers.get_header('WARC-Target-URI')
                    content = record.content_stream().read().decode('utf-8', errors='ignore')
                    
                    # Extract HTTP response
                    if '\r\n\r\n' in content:
                        _, html_content = content.split('\r\n\r\n', 1)
                        
                        # Apply appropriate extractor
                        if purpose in self.extractors:
                            findings = self.extractors[purpose](html_content, url)
                            evidence['findings'].update(findings)
        
        return evidence
    
    def _extract_author_info(self, html_content: str, url: str) -> dict:
        """Extract author reputation information"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        findings = {
            'author_name': self._find_author_name(soup),
            'affiliations': self._find_affiliations(soup),
            'expertise_areas': self._find_expertise(soup),
            'publications_count': self._find_publication_count(soup),
            'h_index': self._find_h_index(soup),
            'verification_source': url
        }
        
        return {'author_reputation': findings}
    
    def _extract_org_info(self, html_content: str, url: str) -> dict:
        """Extract organization credibility information"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        findings = {
            'organization_name': self._find_org_name(soup),
            'organization_type': self._classify_org_type(soup, url),
            'credibility_indicators': self._find_credibility_indicators(soup),
            'verification_source': url
        }
        
        return {'organization_info': findings}
```

#### Tier 3: Evidence Storage and Retrieval
```python
# Evidence storage service
class EvidenceStorageService:
    def __init__(self, minio_client, postgres_client):
        self.minio = minio_client
        self.db = postgres_client
        
    async def store_evidence(self, artifact_id: str, evidence_type: str, 
                           warc_path: str, extracted_data: dict) -> str:
        """Store evidence with metadata indexing"""
        
        # Upload WARC file to MinIO
        warc_key = f"evidence/{artifact_id}/{evidence_type}/{os.path.basename(warc_path)}"
        
        with open(warc_path, 'rb') as warc_file:
            self.minio.put_object(
                bucket_name='loreguard-evidence',
                object_name=warc_key,
                data=warc_file,
                length=os.path.getsize(warc_path),
                content_type='application/warc',
                metadata={
                    'artifact-id': artifact_id,
                    'evidence-type': evidence_type,
                    'created-at': datetime.utcnow().isoformat()
                }
            )
        
        # Store structured evidence in PostgreSQL
        evidence_record = {
            'id': str(uuid.uuid4()),
            'artifact_id': artifact_id,
            'evidence_type': evidence_type,
            'warc_path': warc_key,
            'extracted_data': json.dumps(extracted_data),
            'created_at': datetime.utcnow(),
            'urls_archived': [
                record.get('verification_source') 
                for record in extracted_data.values() 
                if isinstance(record, dict) and 'verification_source' in record
            ]
        }
        
        await self.db.execute("""
            INSERT INTO evidence_records 
            (id, artifact_id, evidence_type, warc_path, extracted_data, created_at, urls_archived)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, *evidence_record.values())
        
        return evidence_record['id']
    
    async def retrieve_evidence(self, artifact_id: str, evidence_type: str = None) -> list:
        """Retrieve evidence for an artifact"""
        
        query = "SELECT * FROM evidence_records WHERE artifact_id = $1"
        params = [artifact_id]
        
        if evidence_type:
            query += " AND evidence_type = $2"
            params.append(evidence_type)
        
        records = await self.db.fetch(query, *params)
        
        # Enrich with WARC access URLs
        for record in records:
            record['warc_url'] = self.minio.presigned_get_object(
                'loreguard-evidence',
                record['warc_path'],
                expires=timedelta(hours=1)
            )
        
        return records
```

### Evidence Lifecycle Management

#### Retention Policies
```python
# Evidence retention and cleanup
class EvidenceRetentionManager:
    def __init__(self, storage_service):
        self.storage = storage_service
        
    async def apply_retention_policy(self):
        """Apply retention policies to evidence storage"""
        
        policies = [
            # Keep critical evidence (author verification) for 5 years
            {
                'evidence_type': 'author_reputation',
                'retention_days': 1825,
                'action': 'archive'
            },
            # Keep organization info for 3 years
            {
                'evidence_type': 'organization_info', 
                'retention_days': 1095,
                'action': 'archive'
            },
            # Keep citation verification for 2 years
            {
                'evidence_type': 'citation_verification',
                'retention_days': 730,
                'action': 'delete'
            },
            # Keep publication venue info for 1 year
            {
                'evidence_type': 'publication_venue',
                'retention_days': 365,
                'action': 'delete'
            }
        ]
        
        for policy in policies:
            cutoff_date = datetime.utcnow() - timedelta(days=policy['retention_days'])
            
            expired_records = await self.storage.db.fetch("""
                SELECT id, warc_path FROM evidence_records 
                WHERE evidence_type = $1 AND created_at < $2
            """, policy['evidence_type'], cutoff_date)
            
            for record in expired_records:
                if policy['action'] == 'archive':
                    await self._archive_evidence(record)
                elif policy['action'] == 'delete':
                    await self._delete_evidence(record)
    
    async def _archive_evidence(self, record):
        """Move evidence to cold storage"""
        
        # Move WARC file to archive bucket
        archive_key = record['warc_path'].replace('evidence/', 'evidence-archive/')
        
        # Copy to archive bucket
        self.storage.minio.copy_object(
            bucket_name='loreguard-evidence-archive',
            object_name=archive_key,
            object_source=f"loreguard-evidence/{record['warc_path']}"
        )
        
        # Update database record
        await self.storage.db.execute("""
            UPDATE evidence_records 
            SET warc_path = $1, archived = true 
            WHERE id = $2
        """, archive_key, record['id'])
        
        # Delete from active storage
        self.storage.minio.remove_object('loreguard-evidence', record['warc_path'])
```

### Performance Optimization

#### Efficient WARC Processing
```python
# Optimized WARC processing for large volumes
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedEvidenceProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def process_evidence_batch(self, evidence_requests: List[dict]) -> List[dict]:
        """Process multiple evidence requests concurrently"""
        
        # Group requests by type for efficiency
        grouped_requests = {}
        for request in evidence_requests:
            evidence_type = request['type']
            if evidence_type not in grouped_requests:
                grouped_requests[evidence_type] = []
            grouped_requests[evidence_type].append(request)
        
        # Process each group concurrently
        tasks = []
        for evidence_type, requests in grouped_requests.items():
            task = asyncio.create_task(
                self._process_evidence_group(evidence_type, requests)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_results = []
        for result_group in results:
            all_results.extend(result_group)
        
        return all_results
    
    async def _process_evidence_group(self, evidence_type: str, requests: List[dict]) -> List[dict]:
        """Process a group of evidence requests of the same type"""
        
        # Use thread pool for I/O intensive operations
        loop = asyncio.get_event_loop()
        
        tasks = []
        for request in requests:
            task = loop.run_in_executor(
                self.executor,
                self._process_single_evidence,
                request
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
```

### Monitoring and Observability

#### Evidence Collection Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics for evidence collection
evidence_requests = Counter('loreguard_evidence_requests_total', 'Evidence requests', ['type', 'status'])
evidence_processing_time = Histogram('loreguard_evidence_processing_seconds', 'Processing time', ['type'])
evidence_storage_size = Gauge('loreguard_evidence_storage_bytes', 'Storage used', ['type'])

class MonitoredEvidenceService:
    def __init__(self, archiver, extractor, storage):
        self.archiver = archiver
        self.extractor = extractor
        self.storage = storage
    
    async def collect_evidence_with_monitoring(self, url: str, purpose: str, 
                                             artifact_id: str) -> dict:
        """Collect evidence with monitoring"""
        
        with evidence_processing_time.labels(type=purpose).time():
            try:
                # Archive evidence
                warc_path = await self.archiver.archive_evidence(url, purpose, artifact_id)
                
                # Extract structured data
                extracted_data = await self.extractor.extract_evidence(warc_path, purpose)
                
                # Store evidence
                evidence_id = await self.storage.store_evidence(
                    artifact_id, purpose, warc_path, extracted_data
                )
                
                # Update metrics
                evidence_requests.labels(type=purpose, status='success').inc()
                
                # Update storage metrics
                warc_size = os.path.getsize(warc_path)
                evidence_storage_size.labels(type=purpose).inc(warc_size)
                
                return {
                    'evidence_id': evidence_id,
                    'warc_path': warc_path,
                    'extracted_data': extracted_data
                }
                
            except Exception as e:
                evidence_requests.labels(type=purpose, status='error').inc()
                logger.error(f"Evidence collection failed: {e}")
                raise
```

### Integration with Clarification Pipeline

#### Evidence-Driven Clarification
```python
# Integration with LoreGuard's clarification service
class ClarificationService:
    def __init__(self, evidence_service):
        self.evidence = evidence_service
        
    async def clarify_artifact(self, artifact: Artifact) -> ClarificationSignals:
        """Generate clarification signals with evidence backing"""
        
        signals = ClarificationSignals(artifact_id=artifact.id)
        
        # Author reputation check
        if artifact.metadata.get('author'):
            author_evidence = await self._verify_author_reputation(
                artifact.metadata['author'], 
                artifact.id
            )
            signals.author_reputation = author_evidence['findings']['author_reputation']
            signals.evidence_refs.append(author_evidence['evidence_id'])
        
        # Organization verification
        if artifact.metadata.get('organization'):
            org_evidence = await self._verify_organization(
                artifact.metadata['organization'],
                artifact.id
            )
            signals.org_type = org_evidence['findings']['organization_info']
            signals.evidence_refs.append(org_evidence['evidence_id'])
        
        # Cross-reference validation
        if artifact.metadata.get('citations'):
            citation_evidence = await self._verify_citations(
                artifact.metadata['citations'],
                artifact.id
            )
            signals.citations = citation_evidence['findings']['citation_verification']
            signals.evidence_refs.append(citation_evidence['evidence_id'])
        
        return signals
    
    async def _verify_author_reputation(self, author_name: str, artifact_id: str) -> dict:
        """Verify author reputation with evidence collection"""
        
        # Search for author information
        search_urls = [
            f"https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors={author_name}",
            f"https://www.researchgate.net/search?q={author_name}",
            f"https://orcid.org/orcid-search/search?searchQuery={author_name}"
        ]
        
        evidence_results = []
        for url in search_urls:
            try:
                evidence = await self.evidence.collect_evidence_with_monitoring(
                    url, 'author_reputation', artifact_id
                )
                evidence_results.append(evidence)
            except Exception as e:
                logger.warning(f"Failed to collect evidence from {url}: {e}")
        
        # Aggregate evidence findings
        aggregated_findings = self._aggregate_author_evidence(evidence_results)
        
        return {
            'evidence_id': [r['evidence_id'] for r in evidence_results],
            'findings': aggregated_findings
        }
```

### Next Steps
1. **Implement WARC archiving** with warcio library
2. **Create evidence extraction** pipelines for different purposes
3. **Set up MinIO storage** for evidence archives
4. **Build retention policies** and cleanup processes
5. **Add monitoring and alerting** for evidence collection

### Open Questions Resolved
- [x] **Primary Format**: WARC for comprehensive evidence preservation
- [x] **Storage Strategy**: MinIO with PostgreSQL metadata indexing
- [x] **Extraction Approach**: Structured data extraction from WARC records
- [x] **Retention Policy**: Tiered retention based on evidence type
- [x] **Performance Strategy**: Concurrent processing with monitoring
