#!/bin/bash
# Manual E2E Test - Step by step with visible output

set -e

API_URL="http://localhost:8000"

echo "========================================="
echo "LoreGuard Manual E2E Test"
echo "========================================="
echo ""

# Step 1: Check health
echo "Step 1: Checking services..."
curl -s $API_URL/health | jq -r '.status' && echo "✓ API healthy" || echo "✗ API failed"
curl -s http://localhost:8001/health | jq -r '.status' 2>/dev/null && echo "✓ Normalize healthy" || echo "✗ Normalize not responding (may not be critical for initial crawl)"
echo ""

# Step 2: Check rubric
echo "Step 2: Checking active rubric..."
RUBRIC_VERSION=$(curl -s $API_URL/api/v1/rubrics/active | jq -r '.version' 2>/dev/null)
if [ "$RUBRIC_VERSION" != "null" ] && [ ! -z "$RUBRIC_VERSION" ]; then
    echo "✓ Active rubric: $RUBRIC_VERSION"
else
    echo "✗ No active rubric found"
    exit 1
fi
echo ""

# Step 3: Check LLM provider
echo "Step 3: Checking LLM provider..."
PROVIDER_NAME=$(curl -s $API_URL/api/v1/llm-providers/default/active | jq -r '.name' 2>/dev/null)
if [ "$PROVIDER_NAME" != "null" ] && [ ! -z "$PROVIDER_NAME" ]; then
    echo "✓ Active provider: $PROVIDER_NAME"
else
    echo "✗ No active LLM provider found"
    exit 1
fi
echo ""

# Step 4: Create test source
echo "Step 4: Creating test source..."
SOURCE_RESPONSE=$(curl -s -X POST $API_URL/api/v1/sources/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manual E2E Test - Books to Scrape",
    "type": "web",
    "config": {
      "start_urls": ["http://books.toscrape.com/"],
      "crawl_scope": {
        "max_depth": 1,
        "max_artifacts": 5,
        "max_crawl_time_minutes": 5
      },
      "filtering": {
        "allowed_domains": ["books.toscrape.com"]
      },
      "politeness": {
        "download_delay": 0.5,
        "concurrent_requests_per_domain": 1
      }
    },
    "status": "active"
  }')

SOURCE_ID=$(echo $SOURCE_RESPONSE | jq -r '.id' 2>/dev/null)
if [ "$SOURCE_ID" != "null" ] && [ ! -z "$SOURCE_ID" ]; then
    echo "✓ Source created: $SOURCE_ID"
else
    echo "✗ Failed to create source"
    echo "Response: $SOURCE_RESPONSE"
    exit 1
fi
echo ""

# Step 5: Trigger crawl
echo "Step 5: Triggering crawl..."
CRAWL_RESPONSE=$(curl -s -X POST $API_URL/api/v1/sources/$SOURCE_ID/trigger)
JOB_ID=$(echo $CRAWL_RESPONSE | jq -r '.job_id' 2>/dev/null)
if [ "$JOB_ID" != "null" ] && [ ! -z "$JOB_ID" ]; then
    echo "✓ Crawl triggered: $JOB_ID"
    echo "Response: $(echo $CRAWL_RESPONSE | jq -c '.')"
else
    echo "✗ Failed to trigger crawl"
    echo "Response: $CRAWL_RESPONSE"
    exit 1
fi
echo ""

# Step 6: Wait for job to start
echo "Step 6: Waiting for crawl to start (5 seconds)..."
sleep 5

JOB_STATUS=$(curl -s $API_URL/api/v1/jobs/$JOB_ID | jq -r '.status' 2>/dev/null)
echo "Job status: $JOB_STATUS"
echo ""

# Step 7: Check for artifacts (wait up to 30 seconds)
echo "Step 7: Waiting for artifacts (checking every 5 seconds for 30 seconds)..."
for i in {1..6}; do
    ARTIFACT_COUNT=$(curl -s "$API_URL/api/v1/artifacts/?limit=100" | jq -r '.total' 2>/dev/null)
    if [ "$ARTIFACT_COUNT" != "null" ] && [ "$ARTIFACT_COUNT" -gt 0 ]; then
        echo "✓ Found $ARTIFACT_COUNT artifacts!"
        break
    fi
    echo "  Attempt $i/6: $ARTIFACT_COUNT artifacts found, waiting..."
    sleep 5
done
echo ""

# Step 8: Get first artifact
echo "Step 8: Getting first artifact details..."
FIRST_ARTIFACT=$(curl -s "$API_URL/api/v1/artifacts/?limit=1" | jq -r '.items[0]')
ARTIFACT_ID=$(echo $FIRST_ARTIFACT | jq -r '.id' 2>/dev/null)
NORMALIZED_REF=$(echo $FIRST_ARTIFACT | jq -r '.normalized_ref' 2>/dev/null)

if [ "$ARTIFACT_ID" != "null" ] && [ ! -z "$ARTIFACT_ID" ]; then
    echo "✓ Artifact ID: $ARTIFACT_ID"
    echo "  Normalized ref: $NORMALIZED_REF"
    echo "  URI: $(echo $FIRST_ARTIFACT | jq -r '.uri')"
else
    echo "✗ No artifacts found yet"
    echo "Check job status: curl $API_URL/api/v1/jobs/$JOB_ID"
    exit 1
fi
echo ""

# Step 9: Check if normalized (may take time)
echo "Step 9: Checking if artifact is normalized (waiting up to 20 seconds)..."
for i in {1..4}; do
    CURRENT_ARTIFACT=$(curl -s "$API_URL/api/v1/artifacts/$ARTIFACT_ID")
    NORMALIZED_REF=$(echo $CURRENT_ARTIFACT | jq -r '.normalized_ref' 2>/dev/null)
    if [ "$NORMALIZED_REF" != "null" ] && [ ! -z "$NORMALIZED_REF" ] && [ "$NORMALIZED_REF" != "" ]; then
        echo "✓ Artifact normalized: $NORMALIZED_REF"
        break
    fi
    echo "  Attempt $i/4: Not normalized yet, waiting..."
    sleep 5
done
echo ""

# Step 10: Check for evaluation
echo "Step 10: Checking for evaluation..."
EVAL_COUNT=$(curl -s "$API_URL/api/v1/evaluations/?artifact_id=$ARTIFACT_ID" | jq -r '.total' 2>/dev/null)
if [ "$EVAL_COUNT" != "null" ] && [ "$EVAL_COUNT" -gt 0 ]; then
    echo "✓ Found $EVAL_COUNT evaluation(s)!"
    EVALUATION=$(curl -s "$API_URL/api/v1/evaluations/?artifact_id=$ARTIFACT_ID" | jq -r '.items[0]')
    echo "  Label: $(echo $EVALUATION | jq -r '.label')"
    echo "  Confidence: $(echo $EVALUATION | jq -r '.confidence')"
else
    echo "⚠ No evaluation found yet (auto-trigger may not have fired)"
    echo "  Triggering manually..."
    EVAL_RESPONSE=$(curl -s -X POST $API_URL/api/v1/artifacts/$ARTIFACT_ID/evaluate)
    EVAL_LABEL=$(echo $EVAL_RESPONSE | jq -r '.label' 2>/dev/null)
    if [ "$EVAL_LABEL" != "null" ] && [ ! -z "$EVAL_LABEL" ]; then
        echo "✓ Manual evaluation completed: $EVAL_LABEL"
        echo "  Confidence: $(echo $EVAL_RESPONSE | jq -r '.confidence')"
        echo "  Total score: $(echo $EVAL_RESPONSE | jq -r '.total_score')"
    else
        echo "✗ Evaluation failed"
        echo "Response: $EVAL_RESPONSE"
    fi
fi
echo ""

echo "========================================="
echo "E2E Test Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  Source ID: $SOURCE_ID"
echo "  Job ID: $JOB_ID"
echo "  Artifact ID: $ARTIFACT_ID"
echo ""
echo "View in frontend:"
echo "  http://localhost:6060 (navigate to Artifacts page)"

