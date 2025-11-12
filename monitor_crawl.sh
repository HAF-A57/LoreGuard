#!/bin/bash
# Monitor crawl job processing pipeline

echo "=== Monitoring LoreGuard Crawl Pipeline ==="
echo ""

# Function to check artifact counts
check_artifacts() {
    echo "[$(date +'%H:%M:%S')] Artifact Status:"
    docker exec loreguard-postgres psql -U loreguard -d loreguard -t -c "
        SELECT 
            COUNT(*) as total,
            COUNT(normalized_ref) as normalized,
            COUNT((SELECT COUNT(*) FROM evaluations WHERE evaluations.artifact_id = artifacts.id)) as evaluated
        FROM artifacts;
    " | xargs
    echo ""
}

# Function to check job statuses
check_jobs() {
    echo "[$(date +'%H:%M:%S')] Job Status:"
    docker exec loreguard-postgres psql -U loreguard -d loreguard -t -c "
        SELECT type, status, COUNT(*) 
        FROM jobs 
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY type, status
        ORDER BY type, status;
    "
    echo ""
}

# Monitor logs in real-time
echo "Starting log monitoring (Ctrl+C to stop)..."
echo ""

# Tail logs from all services
docker logs -f --tail 0 loreguard-ingestion loreguard-normalize loreguard-api 2>&1 | \
    grep --line-buffered -i "artifact\|normalize\|evaluate\|error\|fail\|trigger" | \
    while IFS= read -r line; do
        echo "[LOG] $line"
        
        # Check status every 10 artifacts processed
        if echo "$line" | grep -q "Successfully processed artifact\|Triggered normalization"; then
            sleep 1
            check_artifacts
        fi
    done

