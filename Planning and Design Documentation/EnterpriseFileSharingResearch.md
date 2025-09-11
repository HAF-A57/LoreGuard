## Enterprise File Sharing Research: Nextcloud vs ownCloud

### Executive Summary
For LoreGuard's Signal document distribution to the DoD wargaming community, we need an enterprise file sharing solution that provides security, scalability, and compliance features. Based on research, **Nextcloud Enterprise** emerges as the recommended solution, with **ownCloud** as a viable alternative for specific use cases.

### Technology Comparison

#### Nextcloud Enterprise (Recommended)
**Strengths:**
- **Open Source Core**: AGPLv3 license with enterprise add-ons
- **Enterprise Security**: End-to-end encryption, FIPS compliance, LDAP/SAML integration
- **Scalability**: Supports thousands of users and millions of files
- **Compliance**: GDPR, HIPAA, SOX compliance features
- **Active Development**: Regular updates and security patches
- **Rich Ecosystem**: 200+ apps and integrations
- **Self-Hosted**: Complete on-premises control
- **Mobile/Desktop**: Native clients for all platforms

**Enterprise Features:**
- **Branded Client Apps**: Custom branded mobile/desktop clients
- **Advanced Security**: File access control, watermarking, DLP
- **Compliance**: Audit logging, retention policies, legal hold
- **Scalability**: Clustering, load balancing, high availability
- **Support**: Professional support and SLA guarantees

**Architecture:**
```yaml
# Nextcloud Enterprise deployment for LoreGuard
version: '3.8'
services:
  nextcloud-app:
    image: nextcloud:28-apache
    restart: always
    ports:
      - "8080:80"
    volumes:
      - ./nextcloud-data:/var/www/html
      - ./signal-documents:/var/www/html/data/shared-documents
    environment:
      - POSTGRES_DB=nextcloud
      - POSTGRES_USER=nextcloud
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
      - POSTGRES_HOST=nextcloud-db
      - NEXTCLOUD_ADMIN_USER=admin
      - NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD}
      - NEXTCLOUD_TRUSTED_DOMAINS=loreguard.af.mil
    depends_on:
      - nextcloud-db
      - nextcloud-redis

  nextcloud-db:
    image: postgres:15
    restart: always
    volumes:
      - ./nextcloud-db:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=nextcloud
      - POSTGRES_USER=nextcloud
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD}

  nextcloud-redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}

  nextcloud-collabora:
    image: collabora/code:latest
    restart: always
    environment:
      - domain=loreguard.af.mil
      - username=admin
      - password=${COLLABORA_PASSWORD}
    cap_add:
      - MKNOD
```

**Integration with LoreGuard:**
```python
import requests
from typing import Dict, List
import os

class NextcloudSignalDistributor:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    async def publish_signal_document(self, artifact_id: str, content: bytes, 
                                    metadata: dict) -> dict:
        """Publish Signal document to Nextcloud"""
        
        # Create organized folder structure
        folder_path = self._generate_folder_path(metadata)
        await self._ensure_folder_exists(folder_path)
        
        # Generate filename with metadata
        filename = self._generate_filename(artifact_id, metadata)
        file_path = f"{folder_path}/{filename}"
        
        # Upload file
        upload_url = f"{self.base_url}/remote.php/dav/files/{self.auth[0]}/{file_path}"
        
        response = self.session.put(
            upload_url,
            data=content,
            headers={
                'Content-Type': 'application/pdf',
                'X-OC-Mtime': str(int(metadata.get('date', datetime.utcnow()).timestamp()))
            }
        )
        
        if response.status_code in [201, 204]:
            # Set file metadata and tags
            await self._set_file_metadata(file_path, metadata)
            await self._apply_file_tags(file_path, metadata)
            
            # Create share link for distribution
            share_link = await self._create_share_link(file_path, metadata)
            
            return {
                'file_path': file_path,
                'share_link': share_link,
                'upload_status': 'success',
                'nextcloud_file_id': response.headers.get('OC-FileId')
            }
        else:
            raise DistributionError(f"Failed to upload to Nextcloud: {response.status_code}")
    
    def _generate_folder_path(self, metadata: dict) -> str:
        """Generate organized folder structure"""
        
        # Organize by: Year/Month/Source/Topic
        date = metadata.get('date', datetime.utcnow())
        year = date.strftime('%Y')
        month = date.strftime('%m')
        source = metadata.get('source_category', 'unknown')
        topic = metadata.get('primary_topic', 'general')
        
        return f"LoreGuard-Signals/{year}/{month}/{source}/{topic}"
    
    async def _set_file_metadata(self, file_path: str, metadata: dict):
        """Set file metadata properties"""
        
        # Nextcloud custom properties
        properties = {
            'loreguard:artifact_id': metadata.get('artifact_id'),
            'loreguard:confidence_score': str(metadata.get('confidence', 0)),
            'loreguard:evaluation_date': metadata.get('evaluation_date', ''),
            'loreguard:topics': ';'.join(metadata.get('topics', [])),
            'loreguard:classification': metadata.get('classification', 'UNCLASSIFIED'),
            'loreguard:author': metadata.get('author', ''),
            'loreguard:source_url': metadata.get('source_url', '')
        }
        
        # Set properties via WebDAV PROPPATCH
        proppatch_url = f"{self.base_url}/remote.php/dav/files/{self.auth[0]}/{file_path}"
        
        proppatch_body = '<?xml version="1.0"?><d:propertyupdate xmlns:d="DAV:" xmlns:lg="http://loreguard.af.mil/ns">'
        proppatch_body += '<d:set><d:prop>'
        
        for prop_name, prop_value in properties.items():
            namespace, name = prop_name.split(':')
            proppatch_body += f'<lg:{name}>{prop_value}</lg:{name}>'
        
        proppatch_body += '</d:prop></d:set></d:propertyupdate>'
        
        response = self.session.request(
            'PROPPATCH',
            proppatch_url,
            data=proppatch_body,
            headers={'Content-Type': 'application/xml'}
        )
        
        if response.status_code not in [200, 207]:
            logger.warning(f"Failed to set metadata for {file_path}: {response.status_code}")
```

#### ownCloud Enterprise
**Strengths:**
- **Enterprise Focus**: Built specifically for enterprise deployments
- **Mature**: Longer track record in enterprise environments
- **Performance**: Optimized for large file handling
- **Support**: Strong enterprise support and consulting
- **Security**: Advanced security features and certifications
- **Integration**: Good integration with enterprise systems

**Weaknesses:**
- **Licensing**: Commercial licensing required for enterprise features
- **Community**: Smaller community compared to Nextcloud
- **Development Pace**: Slower feature development
- **Cost**: Higher total cost of ownership

**Use Cases:**
- Organizations requiring commercial support guarantees
- Environments with strict enterprise software requirements
- Large-scale deployments with dedicated support needs

### Security and Compliance Features

#### DoD Security Requirements
```python
class DoDComplianceManager:
    def __init__(self, nextcloud_client):
        self.client = nextcloud_client
        
        # DoD-specific security configurations
        self.security_policies = {
            'password_policy': {
                'min_length': 14,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special': True,
                'max_age_days': 60
            },
            'session_policy': {
                'timeout_minutes': 30,
                'concurrent_sessions': 3,
                'force_logout_inactive': True
            },
            'file_policies': {
                'encryption_required': True,
                'watermarking': True,
                'download_logging': True,
                'external_sharing': False
            }
        }
    
    async def configure_dod_compliance(self):
        """Configure Nextcloud for DoD compliance"""
        
        # Enable server-side encryption
        await self._enable_server_side_encryption()
        
        # Configure password policies
        await self._configure_password_policies()
        
        # Set up audit logging
        await self._configure_audit_logging()
        
        # Configure file access controls
        await self._configure_file_access_controls()
        
        # Enable watermarking for classified documents
        await self._configure_watermarking()
    
    async def _enable_server_side_encryption(self):
        """Enable server-side encryption with master key"""
        
        # Enable encryption app
        response = await self.client.enable_app('encryption')
        
        # Set encryption configuration
        encryption_config = {
            'encryption.key_manager.class': 'OCA\\Encryption\\KeyManager',
            'encryption.master_key_enabled': 'yes',
            'encryption.recovery_key_enabled': 'yes'
        }
        
        for key, value in encryption_config.items():
            await self.client.set_system_config(key, value)
    
    async def _configure_audit_logging(self):
        """Configure comprehensive audit logging"""
        
        audit_config = {
            'admin_audit.log_file': '/var/log/nextcloud/audit.log',
            'admin_audit.log_level': '1',  # Log everything
            'admin_audit.log_file_sharing': 'yes',
            'admin_audit.log_user_management': 'yes',
            'admin_audit.log_group_management': 'yes'
        }
        
        for key, value in audit_config.items():
            await self.client.set_system_config(key, value)
```

#### Access Control and Permissions
```python
class DocumentAccessController:
    def __init__(self, nextcloud_client):
        self.client = nextcloud_client
        
        # Define access roles for LoreGuard
        self.access_roles = {
            'signal_viewer': {
                'permissions': ['read', 'download'],
                'description': 'Can view and download Signal documents'
            },
            'signal_contributor': {
                'permissions': ['read', 'download', 'comment'],
                'description': 'Can view, download, and comment on Signal documents'
            },
            'signal_curator': {
                'permissions': ['read', 'download', 'comment', 'upload', 'delete'],
                'description': 'Can manage Signal document collection'
            },
            'loreguard_admin': {
                'permissions': ['all'],
                'description': 'Full administrative access'
            }
        }
    
    async def setup_signal_document_permissions(self, file_path: str, 
                                              classification: str,
                                              authorized_groups: List[str]) -> dict:
        """Set up role-based access for Signal documents"""
        
        # Create share for authorized groups
        share_configs = []
        
        for group in authorized_groups:
            share_config = {
                'path': file_path,
                'shareType': 1,  # Group share
                'shareWith': group,
                'permissions': self._get_permissions_for_classification(classification)
            }
            
            response = await self.client.create_share(share_config)
            share_configs.append({
                'group': group,
                'share_id': response.get('share_id'),
                'permissions': share_config['permissions']
            })
        
        # Set file tags for classification
        await self._apply_classification_tags(file_path, classification)
        
        return {
            'file_path': file_path,
            'classification': classification,
            'shares': share_configs,
            'access_configured': True
        }
    
    def _get_permissions_for_classification(self, classification: str) -> int:
        """Get permission mask based on document classification"""
        
        permission_masks = {
            'UNCLASSIFIED': 31,    # Read, update, create, delete, share
            'CUI': 19,             # Read, update, create, delete (no share)
            'CONFIDENTIAL': 17,    # Read, update, create (no delete, no share)
            'SECRET': 1,           # Read only
            'TOP_SECRET': 1        # Read only
        }
        
        return permission_masks.get(classification, 1)  # Default to read-only
```

### Scalability and Performance

#### Large-Scale Document Management
```python
class NextcloudPerformanceOptimizer:
    def __init__(self, nextcloud_client):
        self.client = nextcloud_client
        
    async def optimize_for_large_collections(self):
        """Optimize Nextcloud for handling thousands of documents"""
        
        # Database optimizations
        db_config = {
            'mysql.utf8mb4': 'true',
            'dbdriveroptions': {
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_bin'
            }
        }
        
        # Redis caching configuration
        cache_config = {
            'memcache.local': '\\OC\\Memcache\\APCu',
            'memcache.distributed': '\\OC\\Memcache\\Redis',
            'memcache.locking': '\\OC\\Memcache\\Redis',
            'redis': {
                'host': 'nextcloud-redis',
                'port': 6379,
                'password': os.getenv('REDIS_PASSWORD')
            }
        }
        
        # File handling optimizations
        file_config = {
            'filesystem_check_changes': 1,  # Check for external changes
            'filelocking.enabled': 'true',
            'preview_max_filesize_image': 50,  # MB
            'preview_max_scale_factor': 10,
            'enabledPreviewProviders': [
                'OC\\Preview\\PNG',
                'OC\\Preview\\JPEG',
                'OC\\Preview\\PDF',
                'OC\\Preview\\TXT'
            ]
        }
        
        # Apply configurations
        for config_dict in [db_config, cache_config, file_config]:
            await self._apply_system_config(config_dict)
    
    async def setup_signal_document_workflow(self):
        """Set up automated workflow for Signal document management"""
        
        # Create folder structure
        base_folders = [
            'LoreGuard-Signals/Current',
            'LoreGuard-Signals/Archive',
            'LoreGuard-Signals/High-Priority',
            'LoreGuard-Signals/Under-Review'
        ]
        
        for folder in base_folders:
            await self.client.create_folder(folder)
        
        # Set up automated workflows
        workflow_config = {
            'retention_policy': {
                'archive_after_days': 365,
                'delete_after_days': 1825  # 5 years
            },
            'notification_rules': {
                'new_signal_document': {
                    'notify_groups': ['wargaming-analysts', 'red-team', 'blue-team'],
                    'notification_method': 'email'
                },
                'high_priority_signal': {
                    'notify_groups': ['wargaming-directors'],
                    'notification_method': 'email+push'
                }
            }
        }
        
        return workflow_config
```

### Integration with LoreGuard Pipeline

#### Automated Signal Distribution
```python
class AutomatedSignalDistribution:
    def __init__(self, nextcloud_client, loreguard_db):
        self.nextcloud = nextcloud_client
        self.db = loreguard_db
        
    async def distribute_new_signals(self):
        """Automatically distribute newly classified Signal documents"""
        
        # Get new Signal documents from LoreGuard
        new_signals = await self.db.fetch("""
            SELECT a.*, e.score, e.confidence, e.label
            FROM artifacts a
            JOIN evaluations e ON a.id = e.artifact_id
            WHERE e.label = 'Signal' 
              AND a.distributed_to_nextcloud = false
              AND e.created_at > NOW() - INTERVAL '1 day'
        """)
        
        distribution_results = []
        
        for signal in new_signals:
            try:
                # Get document content from MinIO
                content = await self._get_document_content(signal['content_path'])
                
                # Prepare metadata for distribution
                distribution_metadata = {
                    'artifact_id': signal['id'],
                    'title': signal['title'],
                    'author': signal['author'],
                    'source': signal['source'],
                    'confidence': signal['confidence'],
                    'score': signal['score'],
                    'topics': signal['topics'],
                    'classification': signal.get('classification', 'UNCLASSIFIED'),
                    'date': signal['created_at'],
                    'evaluation_date': signal['evaluation_date']
                }
                
                # Distribute to Nextcloud
                result = await self.nextcloud.publish_signal_document(
                    signal['id'], content, distribution_metadata
                )
                
                # Update database
                await self.db.execute("""
                    UPDATE artifacts 
                    SET distributed_to_nextcloud = true,
                        nextcloud_path = $1,
                        nextcloud_share_link = $2,
                        distribution_date = NOW()
                    WHERE id = $3
                """, result['file_path'], result['share_link'], signal['id'])
                
                distribution_results.append({
                    'artifact_id': signal['id'],
                    'status': 'success',
                    'nextcloud_path': result['file_path'],
                    'share_link': result['share_link']
                })
                
            except Exception as e:
                logger.error(f"Failed to distribute signal {signal['id']}: {e}")
                distribution_results.append({
                    'artifact_id': signal['id'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return distribution_results
```

### Alternative: ownCloud Enterprise

#### ownCloud Comparison
**Strengths:**
- **Enterprise Maturity**: Longer enterprise track record
- **Performance**: Optimized for large file operations
- **Support**: Comprehensive enterprise support
- **Compliance**: Strong compliance and audit features
- **Integration**: Excellent enterprise system integration

**Weaknesses:**
- **Cost**: Higher licensing costs than Nextcloud
- **Open Source**: Less open than Nextcloud (dual licensing)
- **Community**: Smaller community and ecosystem
- **Innovation**: Slower feature development

**When to Choose ownCloud:**
- Budget allows for commercial licensing
- Require guaranteed enterprise support SLAs
- Need specific enterprise integrations only available in ownCloud
- Prioritize stability over latest features

### Monitoring and Administration

#### Performance Monitoring
```python
class NextcloudMonitoringService:
    def __init__(self, nextcloud_client):
        self.client = nextcloud_client
        
    async def collect_performance_metrics(self) -> dict:
        """Collect Nextcloud performance and usage metrics"""
        
        # System information
        system_info = await self.client.get_system_info()
        
        # Storage usage
        storage_stats = await self.client.get_storage_stats()
        
        # User activity
        user_stats = await self.client.get_user_stats()
        
        # File sharing statistics
        sharing_stats = await self.client.get_sharing_stats()
        
        metrics = {
            'system': {
                'version': system_info.get('version'),
                'uptime': system_info.get('uptime'),
                'memory_usage': system_info.get('memory_usage'),
                'cpu_usage': system_info.get('cpu_usage')
            },
            'storage': {
                'total_space': storage_stats.get('total'),
                'used_space': storage_stats.get('used'),
                'free_space': storage_stats.get('free'),
                'file_count': storage_stats.get('num_files'),
                'user_count': storage_stats.get('num_users')
            },
            'activity': {
                'active_users_24h': user_stats.get('active_users_24h'),
                'total_shares': sharing_stats.get('total_shares'),
                'external_shares': sharing_stats.get('external_shares')
            },
            'loreguard_specific': await self._get_loreguard_metrics()
        }
        
        return metrics
    
    async def _get_loreguard_metrics(self) -> dict:
        """Get LoreGuard-specific metrics from Nextcloud"""
        
        # Count files in LoreGuard folders
        signal_folders = await self.client.list_folder_contents('LoreGuard-Signals')
        
        # Calculate distribution statistics
        total_signals = 0
        signals_by_month = {}
        signals_by_topic = {}
        
        for folder_item in signal_folders:
            if folder_item['type'] == 'file':
                total_signals += 1
                
                # Extract date from path for monthly stats
                path_parts = folder_item['path'].split('/')
                if len(path_parts) >= 3:
                    year_month = f"{path_parts[1]}-{path_parts[2]}"
                    signals_by_month[year_month] = signals_by_month.get(year_month, 0) + 1
                
                # Extract topic from metadata
                metadata = await self.client.get_file_metadata(folder_item['path'])
                topic = metadata.get('loreguard:topics', 'unknown').split(';')[0]
                signals_by_topic[topic] = signals_by_topic.get(topic, 0) + 1
        
        return {
            'total_signal_documents': total_signals,
            'signals_by_month': signals_by_month,
            'signals_by_topic': signals_by_topic,
            'last_updated': datetime.utcnow().isoformat()
        }
```

### Cost Analysis

#### Nextcloud Enterprise Costs (Annual)
- **Software Licensing**: $15K (100 users × $150/user/year)
- **Hardware**: $25K (dedicated servers for file storage and processing)
- **Support**: $10K (professional support contract)
- **Implementation**: $20K (initial setup and configuration)
- **Total Year 1**: $70K
- **Annual Ongoing**: $25K (licensing + support)

#### ownCloud Enterprise Costs (Annual)
- **Software Licensing**: $25K (100 users × $250/user/year)
- **Hardware**: $25K (same hardware requirements)
- **Support**: $15K (enterprise support contract)
- **Implementation**: $25K (professional services)
- **Total Year 1**: $90K
- **Annual Ongoing**: $40K (licensing + support)

### Next Steps
1. **Deploy Nextcloud pilot** with sample Signal documents
2. **Configure DoD compliance** settings and security policies
3. **Test integration** with LoreGuard artifact pipeline
4. **Performance testing** with target document volumes
5. **User acceptance testing** with wargaming analysts

### Open Questions Resolved
- [x] **Primary Platform**: Nextcloud Enterprise for open-source flexibility
- [x] **Security Configuration**: DoD compliance with encryption and audit logging
- [x] **Integration Strategy**: Automated distribution from LoreGuard pipeline
- [x] **Access Control**: Role-based permissions with classification handling
- [x] **Performance Optimization**: Caching and database tuning for scale
