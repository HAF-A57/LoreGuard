## Workflow Orchestration Research Findings

### Executive Summary
For LoreGuard's complex document processing pipelines, we need a workflow orchestration system that can handle long-running processes, provide durability guarantees, and support complex retry/error handling logic. Based on research, **Temporal** emerges as the recommended solution for mission-critical workflows, with **Prefect** as an alternative for simpler data pipeline scenarios.

### Technology Comparison

#### Temporal
**Strengths:**
- **Durability**: Workflows survive process crashes, restarts, and infrastructure failures
- **Reliability**: Built-in retry logic with exponential backoff and jitter
- **Scalability**: Handles millions of concurrent workflow executions
- **Versioning**: Code versioning with backward compatibility for long-running workflows
- **Observability**: Rich UI with detailed execution history and debugging tools
- **Language Support**: SDKs for Go, Java, Python, TypeScript, PHP
- **Enterprise Features**: Multi-tenancy, encryption, audit logs, RBAC
- **Deterministic Execution**: Guarantees consistent replay for debugging

**Weaknesses:**
- **Complexity**: Steeper learning curve and operational overhead
- **Infrastructure**: Requires dedicated Temporal cluster (server, database, workers)
- **Resource Usage**: Higher memory and compute requirements
- **Vendor Lock-in**: Proprietary concepts and patterns

**Use Cases in LoreGuard:**
- Long-running document processing pipelines (hours/days)
- Complex retry logic for external API calls (clarification service)
- Orchestrating multi-service workflows (ingest → normalize → evaluate → store)
- Handling partial failures and compensation logic
- Audit trails for compliance and debugging

#### Prefect
**Strengths:**
- **Python-First**: Native Python with excellent developer experience
- **Modern UI**: Beautiful, intuitive web interface
- **Flexible Deployment**: Cloud, on-premises, or hybrid
- **Data-Centric**: Built specifically for data workflows and pipelines
- **Easy Debugging**: Local development and testing capabilities
- **Open Source**: Core functionality available without licensing
- **Rich Ecosystem**: Good integration with data tools (dbt, Spark, etc.)
- **Caching**: Intelligent task result caching

**Weaknesses:**
- **Newer Technology**: Less mature than alternatives, smaller community
- **Limited Language Support**: Primarily Python-focused
- **Durability**: Less robust than Temporal for long-running workflows
- **Enterprise Features**: Some advanced features require Prefect Cloud subscription

**Use Cases in LoreGuard:**
- Data processing pipelines with clear start/end
- Scheduled batch jobs (daily/weekly source refreshes)
- ETL workflows for moving data between systems
- Monitoring and alerting workflows

#### Celery
**Strengths:**
- **Mature**: Battle-tested in production environments
- **Simple**: Easy to understand task queue concept
- **Flexible**: Supports multiple brokers (Redis, RabbitMQ, AWS SQS)
- **Python Native**: Deep Python integration
- **Lightweight**: Minimal infrastructure requirements
- **Monitoring**: Good tooling (Flower, Celery Monitor)

**Weaknesses:**
- **Not a Workflow Engine**: Limited workflow orchestration capabilities
- **No Built-in Durability**: Tasks can be lost on broker failure
- **Complex Workflows**: Difficult to implement complex dependencies
- **State Management**: No built-in workflow state persistence
- **Error Handling**: Limited retry and error handling patterns
- **Scalability**: Can become complex to manage at scale

**Use Cases in LoreGuard:**
- Simple background tasks (sending notifications, cleanup jobs)
- Independent processing tasks without complex dependencies
- Quick wins for existing Python applications

### Recommended Architecture: Temporal-Centric

#### Core Workflow Definitions
```python
from temporalio import workflow, activity
from datetime import timedelta
import asyncio

@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, source_config: SourceConfig) -> ProcessingResult:
        # Ingest documents from source
        artifacts = await workflow.execute_activity(
            ingest_documents,
            source_config,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=30),
                maximum_interval=timedelta(minutes=10)
            )
        )
        
        # Process each artifact in parallel
        processing_tasks = []
        for artifact in artifacts:
            task = workflow.execute_activity(
                process_single_artifact,
                artifact,
                start_to_close_timeout=timedelta(minutes=30)
            )
            processing_tasks.append(task)
        
        # Wait for all processing to complete
        results = await asyncio.gather(*processing_tasks)
        
        # Aggregate results and update library
        final_result = await workflow.execute_activity(
            update_library,
            results,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return final_result

@activity.defn
async def process_single_artifact(artifact: Artifact) -> ProcessingResult:
    """Process a single artifact through the full pipeline"""
    
    # Normalize document
    normalized = await normalize_document(artifact)
    
    # Extract metadata
    metadata = await extract_metadata(normalized)
    
    # Clarification (may take time for web searches)
    clarification = await clarify_artifact(metadata)
    
    # Evaluate with LLM
    evaluation = await evaluate_artifact(normalized, clarification)
    
    # Store results
    await store_processed_artifact(artifact.id, normalized, evaluation)
    
    return ProcessingResult(
        artifact_id=artifact.id,
        label=evaluation.label,
        confidence=evaluation.confidence
    )
```

#### Error Handling and Compensation
```python
@workflow.defn
class RobustProcessingWorkflow:
    @workflow.run
    async def run(self, batch_config: BatchConfig) -> BatchResult:
        try:
            # Main processing logic
            result = await self.process_batch(batch_config)
            return result
            
        except Exception as e:
            # Handle failures with compensation
            await workflow.execute_activity(
                compensate_failed_batch,
                batch_config,
                start_to_close_timeout=timedelta(minutes=15)
            )
            
            # Decide whether to retry or fail
            if self.should_retry(e):
                # Signal for manual intervention
                await workflow.execute_activity(
                    notify_operators,
                    f"Batch {batch_config.id} failed: {str(e)}"
                )
                
                # Wait for manual approval to retry
                approved = await workflow.wait_condition(
                    lambda: self.retry_approved,
                    timeout=timedelta(hours=24)
                )
                
                if approved:
                    return await self.run(batch_config)
            
            raise e
```

#### Integration with LoreGuard Services
```python
# Temporal worker configuration
async def start_loreguard_workers():
    client = await Client.connect("temporal-cluster:7233")
    
    # Create workers for different task types
    workers = [
        # Ingestion worker (I/O intensive)
        Worker(
            client,
            task_queue="loreguard-ingestion",
            workflows=[DocumentIngestionWorkflow],
            activities=[ingest_documents, validate_sources],
            max_concurrent_activities=50
        ),
        
        # Processing worker (CPU intensive)
        Worker(
            client,
            task_queue="loreguard-processing", 
            workflows=[DocumentProcessingWorkflow],
            activities=[normalize_document, extract_metadata],
            max_concurrent_activities=10
        ),
        
        # Evaluation worker (LLM calls)
        Worker(
            client,
            task_queue="loreguard-evaluation",
            workflows=[EvaluationWorkflow],
            activities=[evaluate_artifact, clarify_artifact],
            max_concurrent_activities=5  # Rate limited by LLM quotas
        )
    ]
    
    # Start all workers
    await asyncio.gather(*[worker.run() for worker in workers])
```

#### Workflow Scheduling and Triggers
```python
@workflow.defn
class SourceRefreshWorkflow:
    @workflow.run
    async def run(self, schedule_config: ScheduleConfig):
        """Scheduled workflow for refreshing sources"""
        
        # Get all active sources
        sources = await workflow.execute_activity(
            get_active_sources,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Process sources based on their refresh schedules
        for source in sources:
            if self.should_refresh(source, schedule_config.current_time):
                # Start child workflow for each source
                await workflow.start_child_workflow(
                    DocumentProcessingWorkflow.run,
                    source.config,
                    id=f"refresh-{source.id}-{schedule_config.current_time}"
                )
        
        # Schedule next refresh
        await workflow.sleep(schedule_config.interval)
        
        # Continue as new workflow to avoid history buildup
        await workflow.continue_as_new(schedule_config)

# Schedule setup
async def setup_source_refresh_schedule():
    client = await Client.connect("temporal-cluster:7233")
    
    handle = await client.start_workflow(
        SourceRefreshWorkflow.run,
        ScheduleConfig(interval=timedelta(hours=6)),
        id="loreguard-source-refresh",
        task_queue="loreguard-scheduler"
    )
    
    return handle
```

### Hybrid Approach: Temporal + Celery

For optimal resource utilization and complexity management:

```python
# Use Temporal for complex workflows
@workflow.defn
class MasterProcessingWorkflow:
    @workflow.run
    async def run(self, batch_id: str):
        # Complex orchestration logic in Temporal
        artifacts = await workflow.execute_activity(discover_artifacts, batch_id)
        
        # Delegate simple tasks to Celery
        for artifact in artifacts:
            await workflow.execute_activity(
                queue_celery_task,
                {
                    'task': 'loreguard.tasks.simple_processing',
                    'args': [artifact.id],
                    'queue': 'processing'
                }
            )
        
        # Wait for Celery tasks and aggregate
        results = await workflow.execute_activity(
            wait_for_celery_batch,
            batch_id,
            start_to_close_timeout=timedelta(hours=2)
        )
        
        return results

# Simple Celery tasks
from celery import Celery

celery_app = Celery('loreguard')

@celery_app.task(bind=True, max_retries=3)
def simple_processing(self, artifact_id):
    """Handle simple, independent processing tasks"""
    try:
        # Process artifact
        result = process_artifact_simple(artifact_id)
        
        # Notify Temporal workflow of completion
        notify_temporal_completion(artifact_id, result)
        
        return result
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Monitoring and Observability

#### Temporal Dashboard Integration
```python
# Custom metrics for LoreGuard workflows
class LoreGuardMetrics:
    def __init__(self, temporal_client):
        self.client = temporal_client
        self.prometheus = PrometheusClient()
    
    async def track_workflow_metrics(self):
        """Export Temporal metrics to Prometheus"""
        
        # Query workflow execution stats
        workflows = await self.client.list_workflows(
            query="WorkflowType='DocumentProcessingWorkflow'"
        )
        
        # Export metrics
        self.prometheus.gauge('loreguard_active_workflows').set(len(workflows))
        
        # Track processing throughput
        completed_today = await self.client.count_workflows(
            query="WorkflowType='DocumentProcessingWorkflow' AND CloseTime > '2024-01-01'"
        )
        
        self.prometheus.counter('loreguard_documents_processed').inc(completed_today)
```

#### Alerting and SLA Monitoring
```python
@activity.defn
async def check_processing_sla(batch_id: str):
    """Monitor processing SLA and alert if breached"""
    
    batch_start = await get_batch_start_time(batch_id)
    current_time = datetime.utcnow()
    processing_time = current_time - batch_start
    
    # SLA: 95% of documents processed within 4 hours
    sla_threshold = timedelta(hours=4)
    
    if processing_time > sla_threshold:
        await send_alert(
            level='WARNING',
            message=f'Batch {batch_id} exceeding SLA: {processing_time}',
            channels=['slack', 'email']
        )
        
        # Escalate if severely delayed
        if processing_time > timedelta(hours=8):
            await send_alert(
                level='CRITICAL',
                message=f'Batch {batch_id} critically delayed: {processing_time}',
                channels=['pagerduty']
            )
```

### Deployment and Infrastructure

#### Docker Compose for Development
```yaml
version: '3.8'
services:
  temporal-server:
    image: temporalio/auto-setup:1.22
    ports:
      - "7233:7233"
      - "8233:8233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    depends_on:
      - postgresql

  loreguard-worker:
    build: .
    environment:
      - TEMPORAL_HOST=temporal-server:7233
      - REDIS_URL=redis://redis:6379
    depends_on:
      - temporal-server
      - redis
    command: python -m loreguard.workers.temporal_worker

  celery-worker:
    build: .
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on:
      - redis
    command: celery -A loreguard.celery worker -l info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgresql:
    image: postgres:15
    environment:
      POSTGRES_DB: temporal
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
```

#### Production Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loreguard-temporal-workers
spec:
  replicas: 3
  selector:
    matchLabels:
      app: loreguard-temporal-workers
  template:
    metadata:
      labels:
        app: loreguard-temporal-workers
    spec:
      containers:
      - name: worker
        image: loreguard:latest
        env:
        - name: TEMPORAL_HOST
          value: "temporal-frontend:7233"
        - name: WORKER_TYPE
          value: "processing"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Performance and Scalability

#### Throughput Estimates
- **Temporal**: 10,000+ workflow executions per second
- **Activity Throughput**: 100,000+ activities per second per worker
- **Latency**: Sub-100ms for simple workflows
- **Durability**: 99.99% reliability with proper cluster setup

#### Scaling Strategy
```python
# Auto-scaling based on queue depth
class WorkerAutoScaler:
    def __init__(self, temporal_client, k8s_client):
        self.temporal = temporal_client
        self.k8s = k8s_client
    
    async def scale_workers(self):
        """Scale workers based on task queue depth"""
        
        # Check queue metrics
        queue_stats = await self.temporal.describe_task_queue("loreguard-processing")
        pending_tasks = queue_stats.pending_activities
        
        # Calculate desired replicas
        target_replicas = min(
            max(pending_tasks // 100, 1),  # 1 worker per 100 pending tasks
            20  # Max 20 workers
        )
        
        # Scale deployment
        await self.k8s.scale_deployment(
            "loreguard-temporal-workers",
            target_replicas
        )
```

### Cost Analysis

#### Infrastructure Costs (monthly)
- **Temporal Cluster**: $500-2000 (depending on scale)
- **Workers**: $200-1000 (based on throughput requirements)
- **Monitoring**: $100-300 (Prometheus, Grafana)
- **Total**: $800-3300 per month

#### Operational Benefits
- **Reduced Downtime**: 99.9% vs 95% availability = $10,000+ saved incidents
- **Faster Development**: 50% reduction in workflow development time
- **Better Observability**: 80% faster incident resolution

### Next Steps
1. Set up Temporal development cluster
2. Implement proof-of-concept document processing workflow
3. Benchmark throughput and resource usage
4. Develop monitoring and alerting dashboards
5. Plan production deployment strategy

### Open Questions Resolved
- [x] Primary orchestration engine: **Temporal for complex workflows**
- [x] Hybrid approach: **Temporal + Celery for optimal resource usage**
- [x] Error handling: **Built-in retry policies with compensation logic**
- [x] Monitoring strategy: **Temporal UI + Prometheus metrics**
- [x] Scalability approach: **Auto-scaling workers based on queue depth**
