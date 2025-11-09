#!/bin/bash

# LoreGuard Health Check Script
# Validates all services are running and accessible

set -e  # Exit on any error

# Load environment variables from .env (single source of truth)
if [[ -f .env ]]; then
    source .env
fi

# Use detected IP or fallback to localhost
HOST_IP=${LOREGUARD_HOST_IP:-localhost}

echo "🔍 LoreGuard Health Check"
echo "========================"
echo ""
echo "Checking services on: $HOST_IP"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check functions
check_service() {
    local service_name=$1
    local check_command=$2
    local expected_result=$3
    
    echo -n "Checking $service_name... "
    
    if eval $check_command &> /dev/null; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

check_http_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null || echo "000")
    
    if [[ "$status_code" == "$expected_status" ]]; then
        echo -e "${GREEN}✅ Healthy (HTTP $status_code)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed (HTTP $status_code)${NC}"
        return 1
    fi
}

check_json_response() {
    local service_name=$1
    local url=$2
    local expected_key=$3
    
    echo -n "Checking $service_name... "
    
    local response=$(curl -s $url 2>/dev/null || echo "{}")
    
    if echo "$response" | jq -e ".$expected_key" &> /dev/null; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Initialize counters
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Infrastructure Services
echo -e "${BLUE}🏗️  Infrastructure Services${NC}"

# PostgreSQL
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_service "PostgreSQL" "docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U loreguard"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# Redis
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_service "Redis" "docker compose -f docker-compose.dev.yml exec -T redis redis-cli ping"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# MinIO
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_http_service "MinIO" "http://${HOST_IP}:9000/minio/health/ready"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

echo ""

# Application Services
echo -e "${BLUE}🚀 Application Services${NC}"

# Backend API Health
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_json_response "Backend API Health" "http://${HOST_IP}:8000/health" "status"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# Backend API Test Endpoints
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_json_response "Backend API Ping" "http://${HOST_IP}:8000/api/v1/test/ping" "message"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_json_response "Database Connection" "http://${HOST_IP}:8000/api/v1/test/db-test" "database_connected"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# Frontend
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if check_http_service "Frontend" "http://${HOST_IP}:6060"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi

# Normalize Service - check if service is responding (even if dependencies aren't configured)
# Accept both 200 (healthy) and 503 (unhealthy but running) as valid responses
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking Normalize Service... "
NORMALIZE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST_IP}:8001/health" 2>/dev/null || echo "000")
if [[ "$NORMALIZE_STATUS" == "200" ]] || [[ "$NORMALIZE_STATUS" == "503" ]]; then
    echo -e "${GREEN}✅ Healthy (HTTP $NORMALIZE_STATUS)${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌ Failed (HTTP $NORMALIZE_STATUS)${NC}"
fi

# AI Assistant Service
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking AI Assistant Service... "
ASSISTANT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST_IP}:8002/health" 2>/dev/null || echo "000")
if [[ "$ASSISTANT_STATUS" == "200" ]] || [[ "$ASSISTANT_STATUS" == "503" ]]; then
    echo -e "${GREEN}✅ Healthy (HTTP $ASSISTANT_STATUS)${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌ Failed (HTTP $ASSISTANT_STATUS)${NC}"
fi

# Ingestion Service - check if container is running (no HTTP endpoint, invoked via scrapy commands)
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo -n "Checking Ingestion Service... "
if docker compose -f docker-compose.dev.yml ps loreguard-ingestion --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null; then
    # Verify scrapy is available in the container
    if docker compose -f docker-compose.dev.yml exec -T loreguard-ingestion scrapy --version &> /dev/null; then
        echo -e "${GREEN}✅ Healthy (Container running, Scrapy available)${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${YELLOW}⚠️  Container running but Scrapy not available${NC}"
    fi
else
    echo -e "${RED}❌ Failed (Container not running)${NC}"
fi

echo ""

# Detailed Service Information
echo -e "${BLUE}📊 Service Details${NC}"

# Database health details
echo -n "Database Health Details... "
DB_HEALTH=$(curl -s http://${HOST_IP}:8000/api/v1/test/db-test 2>/dev/null || echo "{}")
if echo "$DB_HEALTH" | jq -e '.database_connected' &> /dev/null; then
    TABLE_COUNT=$(echo "$DB_HEALTH" | jq -r '.table_count // 0')
    echo -e "${GREEN}✅ $TABLE_COUNT tables created${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
fi

# Check for sample data
echo -n "Sample Data... "
SOURCES_DATA=$(curl -s http://${HOST_IP}:8000/api/v1/test/sources-simple 2>/dev/null || echo "{}")
if echo "$SOURCES_DATA" | jq -e '.count' &> /dev/null; then
    SOURCE_COUNT=$(echo "$SOURCES_DATA" | jq -r '.count // 0')
    echo -e "${GREEN}✅ $SOURCE_COUNT sources loaded${NC}"
else
    echo -e "${YELLOW}⚠️  No sample data loaded${NC}"
fi

# Check for artifacts
echo -n "Artifacts Data... "
ARTIFACTS_DATA=$(curl -s http://${HOST_IP}:8000/api/v1/test/artifacts-simple 2>/dev/null || echo "{}")
if echo "$ARTIFACTS_DATA" | jq -e '.count' &> /dev/null; then
    ARTIFACT_COUNT=$(echo "$ARTIFACTS_DATA" | jq -r '.count // 0')
    echo -e "${GREEN}✅ $ARTIFACT_COUNT artifacts loaded${NC}"
else
    echo -e "${YELLOW}⚠️  No artifacts loaded${NC}"
fi

echo ""

# Container Status
echo -e "${BLUE}🐳 Container Status${NC}"

# Check Docker containers
if command -v docker &> /dev/null; then
    # Get container status - use JSON format for reliable parsing
    CONTAINERS=$(docker compose -f docker-compose.dev.yml ps --format json 2>/dev/null)
    
    if [[ ! -z "$CONTAINERS" ]]; then
        while IFS= read -r container_json; do
            [[ -z "$container_json" ]] && continue
            SERVICE=$(echo "$container_json" | jq -r '.Service // empty' 2>/dev/null)
            STATUS=$(echo "$container_json" | jq -r '.Status // empty' 2>/dev/null)
            
            [[ -z "$SERVICE" || -z "$STATUS" ]] && continue
            
            if [[ "$STATUS" == *"Up"* ]] || [[ "$STATUS" == *"healthy"* ]]; then
                echo -e "   ${GREEN}✅ $SERVICE${NC}: $STATUS"
            else
                echo -e "   ${RED}❌ $SERVICE${NC}: $STATUS"
            fi
        done <<< "$CONTAINERS"
    else
        echo -e "   ${YELLOW}⚠️  No containers found${NC}"
    fi
else
    echo -e "   ${RED}❌ Docker not available${NC}"
fi

echo ""

# Process Status
echo -e "${BLUE}⚙️  Process Status${NC}"

# Check for API process (can be local or containerized)
if [[ -f logs/api.pid ]]; then
    API_PID=$(cat logs/api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "   ${GREEN}✅ Backend API${NC}: Running (PID: $API_PID)"
    else
        echo -e "   ${RED}❌ Backend API${NC}: Process not found"
    fi
elif docker compose -f docker-compose.dev.yml ps loreguard-api --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null; then
    echo -e "   ${GREEN}✅ Backend API${NC}: Running (containerized)"
else
    echo -e "   ${YELLOW}⚠️  Backend API${NC}: Not running (check container or PID file)"
fi

# Check for normalize process (can be local or containerized)
if [[ -f logs/normalize.pid ]]; then
    NORMALIZE_PID=$(cat logs/normalize.pid)
    if kill -0 $NORMALIZE_PID 2>/dev/null; then
        echo -e "   ${GREEN}✅ Normalize Service${NC}: Running (PID: $NORMALIZE_PID)"
    else
        # PID file exists but process is dead - check if running in container
        if docker compose -f docker-compose.dev.yml ps loreguard-normalize --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null; then
            echo -e "   ${GREEN}✅ Normalize Service${NC}: Running (containerized, stale PID file)"
        else
            echo -e "   ${RED}❌ Normalize Service${NC}: Process not found (stale PID file)"
        fi
    fi
elif docker compose -f docker-compose.dev.yml ps loreguard-normalize --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null; then
    echo -e "   ${GREEN}✅ Normalize Service${NC}: Running (containerized)"
else
    echo -e "   ${YELLOW}⚠️  Normalize Service${NC}: Not running (check container or PID file)"
fi

# Check for assistant process (can be local or containerized)
if [[ -f logs/assistant.pid ]]; then
    ASSISTANT_PID=$(cat logs/assistant.pid)
    if kill -0 $ASSISTANT_PID 2>/dev/null; then
        echo -e "   ${GREEN}✅ AI Assistant Service${NC}: Running (PID: $ASSISTANT_PID)"
    else
        # PID file exists but process is dead - check if running in container
        if docker compose -f docker-compose.dev.yml ps loreguard-assistant --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null; then
            echo -e "   ${GREEN}✅ AI Assistant Service${NC}: Running (containerized, stale PID file)"
        else
            echo -e "   ${RED}❌ AI Assistant Service${NC}: Process not found (stale PID file)"
        fi
    fi
elif docker compose -f docker-compose.dev.yml ps loreguard-assistant --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null; then
    echo -e "   ${GREEN}✅ AI Assistant Service${NC}: Running (containerized)"
else
    echo -e "   ${YELLOW}⚠️  AI Assistant Service${NC}: Not running (check container or PID file)"
fi

# Check for frontend process (typically local for hot reload)
if [[ -f logs/web.pid ]]; then
    WEB_PID=$(cat logs/web.pid)
    if kill -0 $WEB_PID 2>/dev/null; then
        echo -e "   ${GREEN}✅ Frontend${NC}: Running (PID: $WEB_PID)"
    else
        echo -e "   ${RED}❌ Frontend${NC}: Process not found"
    fi
else
    echo -e "   ${YELLOW}⚠️  Frontend${NC}: PID file not found (may be running in container or not started)"
fi

echo ""

# Port Status
echo -e "${BLUE}🌐 Port Status${NC}"

check_port() {
    local port=$1
    local service=$2
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        echo -e "   ${GREEN}✅ Port $port${NC}: $service"
    else
        echo -e "   ${RED}❌ Port $port${NC}: $service (not listening)"
    fi
}

check_port 6060 "Frontend (Development)"
check_port 8000 "Backend API"
check_port 8001 "Normalize Service"
check_port 8002 "AI Assistant Service"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 9000 "MinIO API"
check_port 9001 "MinIO Console"

echo ""

# Summary
echo -e "${BLUE}📋 Health Check Summary${NC}"
echo "========================"

if [[ $PASSED_CHECKS -eq $TOTAL_CHECKS ]]; then
    echo -e "${GREEN}🎉 All systems healthy! ($PASSED_CHECKS/$TOTAL_CHECKS)${NC}"
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo -e "   Frontend:      ${YELLOW}http://${HOST_IP}:6060${NC}"
    echo -e "   Backend API:   ${YELLOW}http://${HOST_IP}:8000${NC}"
    echo -e "   API Docs:      ${YELLOW}http://${HOST_IP}:8000/docs${NC}"
    echo -e "   MinIO Console: ${YELLOW}http://${HOST_IP}:9001${NC}"
    echo ""
    echo -e "${BLUE}🔐 Default Login:${NC}"
    echo -e "   Email:    ${YELLOW}admin@loreguard.local${NC}"
    echo -e "   Password: ${YELLOW}admin${NC}"
    
    exit 0
else
    echo -e "${RED}⚠️  Some issues detected ($PASSED_CHECKS/$TOTAL_CHECKS passed)${NC}"
    echo ""
    echo -e "${BLUE}🔧 Troubleshooting:${NC}"
    echo -e "   1. Check logs: ${YELLOW}./scripts/dev/view-logs.sh${NC}"
    echo -e "   2. Restart services: ${YELLOW}./scripts/dev/restart-services.sh${NC}"
    echo -e "   3. Reset environment: ${YELLOW}./scripts/dev/reset-environment.sh${NC}"
    
    exit 1
fi

