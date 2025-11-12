#!/bin/bash
# Simplified E2E test using docker exec for scrapy
# This bypasses the API's crawl service and invokes scrapy directly

set -e

HOST_IP=${LOREGUARD_HOST_IP:-192.168.1.28}
API_URL="http://${HOST_IP}:8000"

echo "===== LoreGuard E2E Test (Docker-Native) ====="
echo ""
echo "API URL: $API_URL"
echo "Max Artifacts: 40"
echo ""

# Step 1: Create source
echo "[Step 1] Creating Brookings China source..."
SOURCE_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/sources/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Brookings China E2E Test (Docker)",
    "type": "web",
    "status": "active",
    "config": {
      "start_urls": ["https://www.brookings.edu/regions/asia-the-pacific/china"],
      "crawl_scope": {
        "max_depth": 2,
        "max_artifacts": 40,
        "max_pages_per_domain": 50,
        "max_crawl_time_minutes": 15
      },
      "filtering": {
        "allowed_domains": ["brookings.edu", "www.brookings.edu"],
        "allowed_file_types": ["text/html", "application/pdf"],
        "max_file_size_mb": 50
      },
      "politeness": {
        "download_delay": 2.0,
        "concurrent_requests_per_domain": 1,
        "autothrottle_enabled": true
      },
      "compliance": {
        "obey_robots_txt": true
      }
    }
  }')

SOURCE_ID=$(echo "$SOURCE_RESPONSE" | jq -r '.id')
echo "✓ Source created: $SOURCE_ID"
echo ""

# Step 2: Run scrapy in ingestion container
echo "[Step 2] Running scrapy crawl in ingestion container..."
echo "This will take approximately 5 minutes..."
echo ""

docker exec loreguard-ingestion scrapy crawl generic_web \
  -a source_id=$SOURCE_ID \
  -a max_depth=2 \
  -a max_artifacts=40 \
  -a start_urls="https://www.brookings.edu/regions/asia-the-pacific/china" \
  -a allowed_domains="brookings.edu,www.brookings.edu"

echo ""
echo "✓ Crawl completed!"
echo ""

# Step 3: Check artifacts
echo "[Step 3] Checking for artifacts..."
sleep 3
ARTIFACT_COUNT=$(curl -s "${API_URL}/api/v1/artifacts/?limit=1000" | jq '.items | length')
echo "✓ Found $ARTIFACT_COUNT artifacts"
echo ""

# Step 4: Get artifacts for this source
echo "[Step 4] Getting artifacts from source..."
SOURCE_ARTIFACTS=$(curl -s "${API_URL}/api/v1/artifacts/?limit=1000" | jq --arg sid "$SOURCE_ID" '[.items[] | select(.source_id == $sid)]')
SOURCE_ARTIFACT_COUNT=$(echo "$SOURCE_ARTIFACTS" | jq 'length')
echo "✓ Found $SOURCE_ARTIFACT_COUNT artifacts from this source"

# Save artifact IDs
echo "$SOURCE_ARTIFACTS" | jq -r '.[].id' > /tmp/artifact_ids.txt

echo ""
echo "[Step 5] Waiting for normalization..."
NORMALIZED_COUNT=0
MAX_WAIT=300  # 5 minutes
ELAPSED=0

while [ $NORMALIZED_COUNT -lt $SOURCE_ARTIFACT_COUNT ] && [ $ELAPSED -lt $MAX_WAIT ]; do
  NORMALIZED_COUNT=0
  
  while read artifact_id; do
    NORMALIZED_REF=$(curl -s "${API_URL}/api/v1/artifacts/${artifact_id}" | jq -r '.normalized_ref // empty')
    if [ ! -z "$NORMALIZED_REF" ]; then
      NORMALIZED_COUNT=$((NORMALIZED_COUNT + 1))
    fi
  done < /tmp/artifact_ids.txt
  
  echo "  Normalized: $NORMALIZED_COUNT/$SOURCE_ARTIFACT_COUNT"
  
  if [ $NORMALIZED_COUNT -lt $SOURCE_ARTIFACT_COUNT ]; then
    sleep 10
    ELAPSED=$((ELAPSED + 10))
  fi
done

echo "✓ $NORMALIZED_COUNT artifacts normalized"
echo ""

# Step 6: Evaluate artifacts
echo "[Step 6] Evaluating artifacts with LLM..."
EVAL_COUNT=0

while read artifact_id; do
  EVAL_COUNT=$((EVAL_COUNT + 1))
  echo "  [$EVAL_COUNT/$NORMALIZED_COUNT] Evaluating $artifact_id..."
  
  curl -s -X POST "${API_URL}/api/v1/artifacts/${artifact_id}/evaluate" > /dev/null 2>&1 || echo "    (evaluation failed)"
  
  sleep 2  # Rate limiting
done < /tmp/artifact_ids.txt

echo "✓ Evaluation complete"
echo ""

# Step 7: Get results
echo "[Step 7] Analyzing results..."
echo ""

python3 - <<EOF
import requests
import json

api_url = "$API_URL"
source_id = "$SOURCE_ID"

# Get all evaluations
response = requests.get(f"{api_url}/api/v1/evaluations/?limit=1000")
evals = response.json()['items']

# Get artifacts for this source
response = requests.get(f"{api_url}/api/v1/artifacts/?limit=1000")
all_artifacts = response.json()['items']
source_artifacts = [a for a in all_artifacts if a['source_id'] == source_id]
source_artifact_ids = {a['id'] for a in source_artifacts}

# Filter evaluations for this source
source_evals = [e for e in evals if e['artifact_id'] in source_artifact_ids]

if source_evals:
    signal = sum(1 for e in source_evals if e['label'] == 'Signal')
    review = sum(1 for e in source_evals if e['label'] == 'Review')
    noise = sum(1 for e in source_evals if e['label'] == 'Noise')
    
    avg_score = sum(float(e.get('total_score', 0)) for e in source_evals) / len(source_evals)
    avg_conf = sum(float(e.get('confidence', 0)) for e in source_evals) / len(source_evals)
    
    print(f"Total Evaluated: {len(source_evals)}")
    print(f"Signal: {signal} ({signal/len(source_evals)*100:.1f}%)")
    print(f"Review: {review} ({review/len(source_evals)*100:.1f}%)")
    print(f"Noise: {noise} ({noise/len(source_evals)*100:.1f}%)")
    print(f"Average Score: {avg_score:.2f}/5.0")
    print(f"Average Confidence: {avg_conf:.2f}")
else:
    print("No evaluations found")
EOF

echo ""
echo "===== E2E Test Complete ====="
echo "Source ID: $SOURCE_ID"
echo "View results at: http://${HOST_IP}:6060"

