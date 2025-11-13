#!/bin/bash
# Monitor database connections during pipeline execution

echo "=== Database Connection Monitor ==="
echo "Timestamp: $(date)"
echo ""

# Get connection count
CONN_COUNT=$(docker exec loreguard-postgres psql -U loreguard -d loreguard -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'loreguard';" 2>/dev/null | tr -d ' ')

# Get max connections
MAX_CONN=$(docker exec loreguard-postgres psql -U loreguard -d loreguard -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' ')

# Calculate percentage
PERCENT=$((CONN_COUNT * 100 / MAX_CONN))

echo "Current Connections: $CONN_COUNT / $MAX_CONN ($PERCENT%)"
echo ""

# Connection breakdown by state
echo "Connections by State:"
docker exec loreguard-postgres psql -U loreguard -d loreguard -c "SELECT state, count(*) as count FROM pg_stat_activity WHERE datname = 'loreguard' GROUP BY state ORDER BY count DESC;" 2>/dev/null

echo ""
echo "Connections by Application:"
docker exec loreguard-postgres psql -U loreguard -d loreguard -c "SELECT application_name, count(*) as count FROM pg_stat_activity WHERE datname = 'loreguard' GROUP BY application_name ORDER BY count DESC;" 2>/dev/null

echo ""
echo "---"

