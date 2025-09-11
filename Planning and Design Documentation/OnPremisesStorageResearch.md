## On-Premises Storage and DoD Document Sharing Research

### Executive Summary
Based on the requirement for fully on-premises deployment with no cloud dependencies, LoreGuard needs local storage solutions for artifact management and DoD-compatible platforms for sharing Signal documents across the wargaming community.

## On-Premises Object Storage Solutions

### MinIO (Recommended Primary)
**Strengths:**
- **S3-Compatible**: Drop-in replacement for AWS S3 APIs
- **High Performance**: Multi-part uploads, erasure coding, bit-rot protection
- **Enterprise Features**: Encryption, versioning, lifecycle policies, IAM
- **Kubernetes Native**: Easy container orchestration and scaling
- **Open Source**: Apache v2 license with commercial support available
- **Multi-Tenant**: Support for multiple organizations/projects
- **Monitoring**: Built-in metrics and Prometheus integration

**Deployment Options:**
- **Standalone**: Single-node deployment for development/testing
- **Distributed**: Multi-node cluster for production high-availability
- **Federated**: Multiple MinIO clusters for geographic distribution

**Configuration Example:**
```yaml
# MinIO cluster for LoreGuard
apiVersion: v1
kind: Service
metadata:
  name: minio-cluster
spec:
  ports:
  - port: 9000
    name: minio
  - port: 9001
    name: console
  selector:
    app: minio
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: minio
spec:
  serviceName: minio-cluster
  replicas: 4
  template:
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        args:
        - server
        - http://minio-{0...3}.minio-cluster.default.svc.cluster.local/data
        - --console-address
        - ":9001"
        env:
        - name: MINIO_ROOT_USER
          value: "loreguard-admin"
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Ti
```

### Alternative: Network File System (NFS/CIFS)
**Use Case**: Simple file-based storage without object API requirements

**Strengths:**
- **Simple**: Standard filesystem operations
- **Mature**: Well-understood by system administrators
- **Cross-Platform**: Works across Windows/Linux environments
- **Low Overhead**: Minimal resource requirements

**Weaknesses:**
- **Limited Scalability**: Single points of failure
- **No Object Metadata**: Limited metadata capabilities
- **Performance**: Slower than object storage for large files
- **Versioning**: Requires additional tooling

## DoD Document Sharing Platform Research

### SharePoint Scalability Analysis

#### Document Library Limits
- **Items per library**: 30 million (Microsoft official limit)
- **Practical limits**: 5,000-10,000 items per view for good performance
- **File size**: 250GB per file maximum
- **Storage**: 25TB per site collection

#### Performance Considerations
- **Indexing delays**: Large libraries may have search indexing delays
- **View thresholds**: Views over 5,000 items trigger throttling
- **Concurrent users**: Performance degrades with high concurrent access
- **Network bandwidth**: Large document transfers impact performance

#### Recommendations for LoreGuard
- **Folder structure**: Organize by date/source to stay under view thresholds
- **Metadata columns**: Use metadata instead of folders for better performance
- **Content types**: Define specific content types for different document categories
- **Retention policies**: Implement automated archival for old documents

### SIPR-Compatible Document Management

#### Potential Platforms
1. **Microsoft SharePoint (SIPR)**
   - Available in classified environments
   - Familiar interface for DoD users
   - Integration with existing DoD infrastructure
   - Scalability concerns for thousands of documents

2. **Alfresco Enterprise**
   - Open-source with enterprise features
   - Document versioning and workflow
   - LDAP/Active Directory integration
   - Can be deployed in air-gapped environments

3. **IBM FileNet**
   - Enterprise content management
   - Workflow and business process management
   - High scalability and performance
   - Expensive licensing costs

4. **Nextcloud/ownCloud Enterprise**
   - Self-hosted file sharing platform
   - End-to-end encryption
   - Fine-grained access controls
   - Mobile and desktop clients

### Recommended Architecture: Hybrid Approach

#### Tier 1: Local Storage (All Artifacts)
```
┌─────────────────┐    ┌─────────────────┐
│   MinIO Cluster │    │   PostgreSQL    │
│   Raw Artifacts │    │   Metadata      │
│   Normalized    │    │   Evaluations   │
│   Evidence      │    │   Audit Logs    │
└─────────────────┘    └─────────────────┘
```

#### Tier 2: Signal Distribution
```
┌─────────────────┐    ┌─────────────────┐
│   SharePoint    │    │   Nextcloud     │
│   (Primary)     │    │   (Backup/Alt)  │
│   Signal Docs   │    │   Signal Docs   │
│   Metadata      │    │   Sync          │
└─────────────────┘    └─────────────────┘
```

### Implementation Strategy

#### Phase 1: MinIO Deployment
```python
# MinIO client integration
from minio import Minio
from minio.error import S3Error

class LoreGuardStorage:
    def __init__(self):
        self.client = Minio(
            "minio-cluster:9000",
            access_key="loreguard-service",
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=True  # Use TLS
        )
        
    def store_artifact(self, artifact_id, content, content_type):
        """Store raw artifact in MinIO"""
        bucket_name = "loreguard-raw"
        object_name = f"artifacts/{artifact_id[:2]}/{artifact_id}.{self.get_extension(content_type)}"
        
        try:
            # Store with metadata
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(content),
                length=len(content),
                content_type=content_type,
                metadata={
                    "artifact-id": artifact_id,
                    "ingestion-date": datetime.utcnow().isoformat(),
                    "content-hash": hashlib.sha256(content).hexdigest()
                }
            )
            return f"minio://{bucket_name}/{object_name}"
            
        except S3Error as e:
            logger.error(f"Failed to store artifact {artifact_id}: {e}")
            raise
```

#### Phase 2: Signal Distribution
```python
# SharePoint integration for Signal documents
import requests
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

class SignalDistributor:
    def __init__(self, sharepoint_url, username, password):
        self.ctx_auth = AuthenticationContext(sharepoint_url)
        self.ctx_auth.acquire_token_for_user(username, password)
        self.ctx = ClientContext(sharepoint_url, self.ctx_auth)
        
    def publish_signal_document(self, artifact_id, content, metadata):
        """Publish Signal document to SharePoint"""
        
        # Create folder structure by date and source
        folder_path = f"LoreGuard/{metadata['source']}/{metadata['date'][:7]}"  # YYYY-MM
        
        # Upload document with rich metadata
        target_folder = self.ctx.web.get_folder_by_server_relative_url(folder_path)
        
        file_info = {
            'Title': metadata['title'],
            'LoreGuardID': artifact_id,
            'Source': metadata['source'],
            'Author': metadata.get('author', ''),
            'ConfidenceScore': metadata['confidence'],
            'EvaluationDate': datetime.utcnow(),
            'Topics': ';'.join(metadata.get('topics', [])),
            'Classification': metadata.get('classification', 'UNCLASSIFIED')
        }
        
        uploaded_file = target_folder.upload_file(
            f"{artifact_id}.pdf",
            content
        ).execute_query()
        
        # Set metadata
        list_item = uploaded_file.listItemAllFields
        for key, value in file_info.items():
            list_item.set_property(key, value)
        list_item.update()
        self.ctx.execute_query()
        
        return uploaded_file.serverRelativeUrl
```

### Storage Lifecycle Management

#### Retention Policies
```yaml
# MinIO lifecycle configuration
lifecycle_config:
  rules:
    - id: "raw-artifacts-archive"
      status: "Enabled"
      filter:
        prefix: "artifacts/"
      transitions:
        - days: 90
          storage_class: "COLD"  # Move to cold storage after 90 days
        - days: 365
          storage_class: "ARCHIVE"  # Archive after 1 year
    
    - id: "evidence-cleanup"
      status: "Enabled" 
      filter:
        prefix: "evidence/"
      expiration:
        days: 1095  # Delete evidence after 3 years
```

#### Backup Strategy
```bash
#!/bin/bash
# MinIO backup script for LoreGuard

# Create snapshot of current data
mc mirror --overwrite loreguard-prod/loreguard-raw loreguard-backup/$(date +%Y%m%d)/raw/
mc mirror --overwrite loreguard-prod/loreguard-normalized loreguard-backup/$(date +%Y%m%d)/normalized/

# Compress and encrypt backups
tar -czf loreguard-backup-$(date +%Y%m%d).tar.gz loreguard-backup/$(date +%Y%m%d)/
gpg --cipher-algo AES256 --compress-algo 1 --symmetric loreguard-backup-$(date +%Y%m%d).tar.gz

# Store on separate physical media
cp loreguard-backup-$(date +%Y%m%d).tar.gz.gpg /mnt/backup-drive/
```

### Monitoring and Alerting

#### Storage Metrics
```python
# MinIO monitoring integration
import prometheus_client
from minio.error import S3Error

class StorageMonitor:
    def __init__(self):
        self.storage_used = prometheus_client.Gauge('loreguard_storage_used_bytes', 'Storage used by bucket', ['bucket'])
        self.storage_operations = prometheus_client.Counter('loreguard_storage_operations_total', 'Storage operations', ['operation', 'status'])
        
    def collect_metrics(self):
        """Collect storage metrics for monitoring"""
        try:
            # Get bucket statistics
            buckets = ['loreguard-raw', 'loreguard-normalized', 'loreguard-evidence']
            
            for bucket in buckets:
                objects = self.minio_client.list_objects(bucket, recursive=True)
                total_size = sum(obj.size for obj in objects)
                self.storage_used.labels(bucket=bucket).set(total_size)
                
        except S3Error as e:
            logger.error(f"Failed to collect storage metrics: {e}")
            self.storage_operations.labels(operation='metrics', status='error').inc()
```

### Security Considerations

#### Encryption at Rest
- **MinIO**: Server-side encryption with customer-provided keys (SSE-C)
- **Database**: PostgreSQL transparent data encryption (TDE)
- **Filesystem**: LUKS encryption for underlying storage

#### Access Controls
- **RBAC**: Role-based access control for different user types
- **API Keys**: Service-specific access keys with limited permissions
- **Network**: VPN/IPSEC for inter-service communication
- **Audit**: Comprehensive logging of all storage operations

### Cost Analysis (Annual, On-Premises)

#### Hardware Costs
- **MinIO Cluster**: $50K (4-node cluster with 100TB total)
- **Network Storage**: $30K (NFS/CIFS backup systems)
- **Backup Hardware**: $20K (tape/disk backup systems)
- **Total Hardware**: $100K

#### Software/Licensing
- **MinIO**: $0 (open-source) or $25K (enterprise support)
- **SharePoint**: Included in existing DoD Office 365 licensing
- **Monitoring**: $5K (Prometheus/Grafana setup)
- **Total Software**: $30K

#### Operational
- **Power/Cooling**: $15K annually
- **Maintenance**: $20K annually (hardware/software support)
- **Personnel**: $100K (0.5 FTE storage administrator)
- **Total Operational**: $135K annually

### Next Steps
1. **Proof of Concept**: Deploy MinIO cluster with sample data
2. **SharePoint Testing**: Evaluate performance with 10K+ documents
3. **Integration Development**: Build storage abstraction layer
4. **Security Review**: Validate encryption and access controls
5. **Disaster Recovery**: Implement and test backup/restore procedures

### Open Questions Resolved
- [x] **Primary Storage**: MinIO for S3-compatible object storage
- [x] **Signal Distribution**: SharePoint with folder organization strategy
- [x] **Backup Strategy**: Tiered backup with encryption
- [ ] **SIPR Deployment**: Investigate classified environment requirements
- [ ] **Alternative Sharing**: Evaluate Nextcloud/ownCloud for backup distribution
- [ ] **Performance Testing**: Validate SharePoint scalability with target document volume
