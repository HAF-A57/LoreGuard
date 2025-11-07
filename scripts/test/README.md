# LoreGuard End-to-End Test Script

## Overview

The `e2e_test.py` script tests the complete LoreGuard workflow from source creation through artifact evaluation. It simulates a user workflow through the API endpoints.

## Prerequisites

Before running the test, ensure:

1. **All services are running**:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - MinIO (port 9000)
   - API Service (port 8000)
   - Normalize Service (port 8001)

2. **Database is initialized**:
   ```bash
   # Run database initialization
   scripts/dev/init-databases.sh
   ```

3. **Active rubric exists**:
   - The default rubric (v0.1) should be created automatically
   - Verify: `curl http://localhost:8000/api/v1/rubrics/active`

4. **LLM provider is configured**:
   - Provider must be configured via Settings page or API
   - Provider must be active and set as default
   - Verify: `curl http://localhost:8000/api/v1/llm-providers/default/active`

5. **MinIO bucket exists**:
   - Bucket name: `loreguard-artifacts`
   - Can be created via MinIO web UI or client

## Usage

### Basic Usage (Full Test)

```bash
python scripts/test/e2e_test.py
```

This will:
1. Create a test source (Books to Scrape)
2. Trigger a crawl
3. Monitor the crawl job
4. Wait for artifacts to be normalized
5. Trigger LLM evaluations
6. Display results

### Use Existing Source

If you already have artifacts from a previous crawl:

```bash
python scripts/test/e2e_test.py --source-id <source-uuid> --skip-ingestion
```

### Custom API URL

If services are running on a different host:

```bash
python scripts/test/e2e_test.py --api-url http://192.168.1.100:8000
```

Or set environment variable:

```bash
export LOREGUARD_API_URL=http://192.168.1.100:8000
python scripts/test/e2e_test.py
```

## Test Flow

1. **Health Check** - Verifies API service is running
2. **Rubric Check** - Verifies active rubric exists
3. **Provider Check** - Verifies active LLM provider exists
4. **Source Creation** - Creates test source (if not using existing)
5. **Crawl Trigger** - Starts ingestion job
6. **Job Monitoring** - Monitors crawl job until completion (timeout: 10 minutes)
7. **Artifact Retrieval** - Gets artifacts from source (limit: 5)
8. **Normalization Wait** - Waits for artifacts to be normalized (timeout: 5 minutes)
9. **Evaluation Trigger** - Triggers LLM evaluation for each normalized artifact
10. **Results Display** - Shows Signal/Review/Noise breakdown with scores

## Expected Output

The script provides color-coded output:

- ✅ **Green**: Success messages
- ❌ **Red**: Error messages
- ⚠️ **Yellow**: Warnings
- ℹ️ **Cyan**: Informational messages
- 🔔 **Bold Green**: Signal artifacts
- 📋 **Bold Yellow**: Review artifacts
- 🔇 **Bold Red**: Noise artifacts

## Expected Duration

- **Source Creation**: < 1 second
- **Crawl Job**: 30-120 seconds (depends on source)
- **Normalization**: 10-60 seconds per artifact
- **Evaluation**: 10-30 seconds per artifact
- **Total**: ~5-10 minutes for 5 artifacts

## Troubleshooting

### API Connection Issues

If you see connection errors:
1. Verify services are running: `scripts/dev/health-check.sh`
2. Check API URL matches your configuration
3. Ensure firewall allows connections

### No Active Rubric

If you see "No active rubric found":
1. Check database initialization ran successfully
2. Verify: `curl http://localhost:8000/api/v1/rubrics/active`
3. If missing, restart API service to trigger `init_db()`

### No Active LLM Provider

If you see "No active LLM provider found":
1. Configure a provider via Settings page or API
2. Set provider status to "active"
3. Set provider as default
4. Verify: `curl http://localhost:8000/api/v1/llm-providers/default/active`

### Job Timeout

If crawl job times out:
1. Check ingestion service logs
2. Verify Scrapy spiders are working
3. Check network connectivity to source
4. Increase timeout: modify `timeout` parameter in `monitor_job()` call

### Normalization Timeout

If normalization times out:
1. Check normalize service is running
2. Verify MinIO is accessible
3. Check normalize service logs
4. Increase timeout: modify `timeout` parameter in `wait_for_normalization()` call

## Exit Codes

- `0`: Test completed successfully
- `1`: Test failed at some step

## Example Output

```
================================================================================
                        LOREGUARD END-TO-END TEST
================================================================================

[Step 1] Checking API Health
✓ API service is healthy: {'status': 'healthy', 'service': 'loreguard-api'}

[Step 2] Verifying Active Rubric
✓ Found active rubric: v0.1

[Step 3] Verifying Active LLM Provider
✓ Found active LLM provider: GPT-4 (openai)

[Step 4] Creating Test Source
✓ Created test source: E2E Test Source - Books to Scrape (ID: abc-123...)

[Step 5] Triggering Source Crawl
✓ Triggered crawl job: def-456...
ℹ Spider: generic_web
ℹ Process ID: 12345

[Step 6] Monitoring Crawl Job
ℹ Monitoring job def-456... (timeout: 600s)
ℹ Job status: running
ℹ Progress: 45% (9/20 items)
✓ Job completed successfully!
ℹ Duration: 45.2s

[Step 7] Retrieving Artifacts
✓ Found 5 artifacts (retrieved 5)

[Step 8] Waiting for Artifact Normalization
ℹ Waiting for normalization (timeout: 300s)
✓ Artifact abc12345... normalized
✓ All 5 artifacts normalized!

[Step 9] Triggering LLM Evaluations
ℹ Evaluating artifact abc12345...
✓ Evaluation completed
...

[Step 10] Displaying Results
================================================================================
                        EVALUATION RESULTS
================================================================================

Summary:
  Total Evaluated: 5
  Signal: 2
  Review: 2
  Noise: 1

Detailed Results:

🔔 Signal
  Artifact: abc12345...
  Total Score: 4.25
  Confidence: 0.85
  Category Scores:
    - credibility: 4.5
    - relevance: 4.0
    ...
```

