## Vector Database Research Findings

### Executive Summary
For LoreGuard's semantic search capabilities at 100M+ document scale, we need a vector database that can handle high-throughput ingestion, fast retrieval, and hybrid search (vector + BM25). Based on research, **pgvector with PostgreSQL** emerges as the recommended starting point, with **Weaviate** as a scaling option for specialized vector workloads.

### Technology Comparison

#### pgvector (PostgreSQL Extension)
**Strengths:**
- Single database for both metadata and vectors (operational simplicity)
- Mature PostgreSQL ecosystem with proven reliability
- ACID compliance and transactional consistency
- Excellent tooling, monitoring, and operational knowledge
- Cost-effective (no additional licensing)
- Supports HNSW and IVFFlat indexes for fast approximate search
- Native SQL integration for complex queries
- Strong security and compliance features
- Backup/recovery using standard PostgreSQL tools

**Weaknesses:**
- Vector performance may lag behind specialized solutions at extreme scale
- Memory requirements can be high for large vector indexes
- Limited to PostgreSQL's query optimization for vector operations
- May require careful tuning for optimal performance

**Performance at Scale:**
- Supports up to 2,000 dimensions per vector
- HNSW index provides sub-linear search time
- Tested with 100M+ vectors in production environments
- Query performance: 10-50ms for k-NN searches on properly indexed data

#### Weaviate
**Strengths:**
- Purpose-built for vector search with excellent performance
- Built-in hybrid search (vector + BM25 + filters)
- GraphQL API with powerful querying capabilities
- Automatic vectorization with multiple embedding models
- Horizontal scaling and sharding capabilities
- Rich filtering and where clauses
- Multi-tenancy support
- Active development and strong community

**Weaknesses:**
- Additional infrastructure component to manage
- Eventual consistency model (not ACID)
- Requires learning new query language and operations
- Less mature ecosystem compared to PostgreSQL
- Higher operational complexity
- Potential vendor lock-in with proprietary features

**Performance at Scale:**
- Optimized for 100M+ vector operations
- Sub-10ms query times for vector similarity
- Automatic sharding across nodes
- Memory-efficient vector storage

#### Milvus
**Strengths:**
- Highest performance for pure vector operations
- Advanced indexing algorithms (FAISS, Annoy, HNSW)
- Excellent for ML/AI workloads
- Cloud-native architecture with Kubernetes support
- Strong performance benchmarks
- Supports multiple vector types and distances

**Weaknesses:**
- Complex deployment and operations
- Limited hybrid search capabilities
- Steep learning curve
- Requires significant operational expertise
- Less integration with traditional business logic
- Higher infrastructure costs

**Performance at Scale:**
- Designed for billion-scale vector operations
- Single-digit millisecond query performance
- Horizontal scaling across multiple nodes
- Advanced memory management

### Recommended Architecture: Phased Approach

#### Phase 1: pgvector Foundation (0-10M documents)
```sql
-- Vector table design
CREATE TABLE artifact_vectors (
    artifact_id UUID PRIMARY KEY,
    content_vector vector(1536),  -- OpenAI embedding size
    chunk_vectors vector(1536)[],  -- Array of chunk embeddings
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for fast similarity search
CREATE INDEX artifact_vectors_content_idx 
ON artifact_vectors USING hnsw (content_vector vector_cosine_ops);

-- Hybrid search query
SELECT a.id, a.title, a.score,
       v.content_vector <=> %s::vector AS similarity_score
FROM artifacts a
JOIN artifact_vectors v ON a.id = v.artifact_id
WHERE a.metadata @> %s  -- JSON filter
ORDER BY v.content_vector <=> %s::vector
LIMIT 20;
```

#### Phase 2: Hybrid Architecture (10M-100M documents)
```python
# Dual storage approach
class HybridVectorStore:
    def __init__(self):
        self.pg_client = PostgreSQLClient()  # Metadata + small vectors
        self.weaviate_client = WeaviateClient()  # Large vector operations
    
    async def search(self, query_vector, filters, limit=20):
        # Use PostgreSQL for metadata filtering
        filtered_ids = await self.pg_client.filter_by_metadata(filters)
        
        # Use Weaviate for vector similarity on filtered set
        results = await self.weaviate_client.vector_search(
            query_vector, 
            where_filter={'id': {'in': filtered_ids}},
            limit=limit
        )
        
        # Enrich with PostgreSQL metadata
        return await self.pg_client.enrich_results(results)
```

#### Phase 3: Specialized Vector Store (100M+ documents)
```yaml
# Weaviate cluster configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: weaviate-config
data:
  weaviate.yaml: |
    origin: http://weaviate:8080
    persistence:
      dataPath: /var/lib/weaviate
    query_defaults:
      limit: 20
    authorization:
      admin_list:
        enabled: true
    cluster:
      hostname: weaviate
      gossip_bind_port: 7100
      data_bind_port: 7101
```

### Hybrid Search Implementation

#### BM25 + Vector Search
```python
async def hybrid_search(query_text, query_vector, alpha=0.7):
    """Combine BM25 text search with vector similarity"""
    
    # BM25 search using PostgreSQL full-text search
    bm25_results = await pg_client.execute("""
        SELECT artifact_id, ts_rank(search_vector, plainto_tsquery(%s)) as bm25_score
        FROM artifact_search
        WHERE search_vector @@ plainto_tsquery(%s)
        ORDER BY bm25_score DESC
        LIMIT 100
    """, [query_text, query_text])
    
    # Vector similarity search
    vector_results = await pg_client.execute("""
        SELECT artifact_id, (content_vector <=> %s::vector) as vector_score
        FROM artifact_vectors
        ORDER BY content_vector <=> %s::vector
        LIMIT 100
    """, [query_vector, query_vector])
    
    # Combine scores
    combined_scores = {}
    for result in bm25_results:
        combined_scores[result.artifact_id] = alpha * (1 - result.bm25_score)
    
    for result in vector_results:
        artifact_id = result.artifact_id
        vector_component = (1 - alpha) * (1 - result.vector_score)
        
        if artifact_id in combined_scores:
            combined_scores[artifact_id] += vector_component
        else:
            combined_scores[artifact_id] = vector_component
    
    # Return top results
    sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results[:20]
```

### Performance Optimization

#### Indexing Strategy
```python
# Multi-level indexing for different query patterns
class VectorIndexManager:
    def __init__(self):
        self.indexes = {
            'global': 'hnsw_global_idx',      # All vectors
            'recent': 'hnsw_recent_idx',      # Last 30 days
            'high_value': 'hnsw_signal_idx',  # Signal documents only
            'by_source': {}                   # Per-source indexes
        }
    
    async def optimize_for_query(self, query_context):
        """Select optimal index based on query context"""
        if query_context.get('time_range') == 'recent':
            return self.indexes['recent']
        elif query_context.get('label') == 'Signal':
            return self.indexes['high_value']
        else:
            return self.indexes['global']
```

#### Chunking Strategy
```python
def chunk_document_for_vectors(document, chunk_size=1000, overlap=200):
    """Create overlapping chunks for better retrieval"""
    
    chunks = []
    text = document.normalized_text
    
    # Split by sentences to avoid breaking mid-sentence
    sentences = sent_tokenize(text)
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size:
            if current_chunk:
                chunks.append({
                    'text': current_chunk,
                    'start_pos': len(''.join(chunks)) if chunks else 0,
                    'metadata': document.metadata
                })
            
            # Start new chunk with overlap
            if overlap and chunks:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk += " " + sentence
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            'text': current_chunk,
            'start_pos': len(''.join(chunks)),
            'metadata': document.metadata
        })
    
    return chunks
```

### Monitoring and Observability

#### Performance Metrics
```python
# Key metrics to track
VECTOR_DB_METRICS = {
    'query_latency_p95': 'Vector query 95th percentile latency',
    'index_memory_usage': 'Memory used by vector indexes',
    'ingestion_throughput': 'Vectors indexed per second',
    'search_accuracy': 'Relevance score for known queries',
    'cache_hit_rate': 'Vector cache effectiveness'
}

# Monitoring queries
async def monitor_vector_performance():
    # Query latency distribution
    latencies = await pg_client.execute("""
        SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY duration)
        FROM pg_stat_statements
        WHERE query LIKE '%vector%'
    """)
    
    # Index size and usage
    index_stats = await pg_client.execute("""
        SELECT schemaname, tablename, indexname, 
               pg_size_pretty(pg_relation_size(indexrelid)) as size,
               idx_scan, idx_tup_read
        FROM pg_stat_user_indexes
        WHERE indexname LIKE '%vector%'
    """)
    
    return {
        'p95_latency': latencies[0][0],
        'index_stats': index_stats
    }
```

### Cost Analysis

#### Storage Costs (per 1M documents)
- **pgvector**: ~50GB storage (vectors + metadata)
- **Weaviate**: ~30GB storage (optimized vector format)
- **Milvus**: ~25GB storage (compressed vectors)

#### Compute Costs (monthly, 1M queries)
- **pgvector**: $200-500 (existing PostgreSQL infrastructure)
- **Weaviate**: $500-1000 (dedicated cluster)
- **Milvus**: $800-1500 (specialized hardware requirements)

#### Operational Costs
- **pgvector**: Low (existing PostgreSQL expertise)
- **Weaviate**: Medium (new system to learn/manage)
- **Milvus**: High (specialized knowledge required)

### Migration Strategy

#### Phase 1 to Phase 2 Migration
```python
async def migrate_to_hybrid():
    """Migrate from pure pgvector to hybrid architecture"""
    
    # 1. Set up Weaviate cluster
    await setup_weaviate_cluster()
    
    # 2. Migrate vectors in batches
    async for batch in pg_client.get_vectors_batch(batch_size=10000):
        await weaviate_client.batch_insert(batch)
        
        # Verify migration
        sample_queries = await validate_migration_batch(batch)
        if not sample_queries.all_passed():
            await rollback_batch(batch)
            raise MigrationError("Vector migration validation failed")
    
    # 3. Switch traffic gradually
    await traffic_router.set_vector_traffic_split(
        pgvector=0.8, 
        weaviate=0.2
    )
```

### Next Steps
1. Implement pgvector proof-of-concept with sample document set
2. Benchmark query performance against requirements
3. Develop hybrid search algorithm and test relevance
4. Create monitoring dashboards for vector operations
5. Plan migration strategy for scaling phases

### Open Questions Resolved
- [x] Primary vector store: **pgvector for simplicity and reliability**
- [x] Scaling strategy: **Hybrid approach with Weaviate for specialized workloads**
- [x] Hybrid search: **BM25 + vector similarity with tunable weights**
- [x] Performance optimization: **Multi-level indexing and chunking strategy**
- [x] Monitoring approach: **PostgreSQL stats + custom vector metrics**
