#!/bin/bash

# LoreGuard Environment Reset Script
# WARNING: This will destroy all data and reset the environment

set -e  # Exit on any error

echo "🗑️  LoreGuard Environment Reset"
echo "==============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Warning prompt
echo -e "${RED}⚠️  WARNING: This will permanently delete all data!${NC}"
echo ""
echo "This script will:"
echo "  • Stop all running services"
echo "  • Remove all Docker containers and volumes"
echo "  • Delete all database data"
echo "  • Remove all logs and temporary files"
echo "  • Reset the environment to initial state"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo -e "${BLUE}Reset cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🛑 Stopping all services...${NC}"

# Stop any running processes
if [[ -f logs/backend.pid ]]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping backend API (PID: $BACKEND_PID)"
        kill $BACKEND_PID
    fi
    rm -f logs/backend.pid
fi

if [[ -f logs/frontend.pid ]]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID
    fi
    rm -f logs/frontend.pid
fi

# Stop Docker services
echo -e "${YELLOW}🐳 Stopping Docker containers...${NC}"
docker compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true

# Remove Docker volumes
echo -e "${YELLOW}🗄️  Removing Docker volumes...${NC}"
docker volume rm loreguard_postgres_data 2>/dev/null || true
docker volume rm loreguard_redis_data 2>/dev/null || true
docker volume rm loreguard_minio_data 2>/dev/null || true
docker volume rm loreguard_libretranslate_data 2>/dev/null || true
docker volume rm loreguard_nextcloud_data 2>/dev/null || true
docker volume rm loreguard_nextcloud_db_data 2>/dev/null || true
docker volume rm loreguard_pgadmin_data 2>/dev/null || true

# Remove Docker network
echo -e "${YELLOW}🌐 Removing Docker network...${NC}"
docker network rm loreguard-network 2>/dev/null || true

# Clean up Docker system
echo -e "${YELLOW}🧹 Cleaning Docker system...${NC}"
docker system prune -f

# Remove logs and temporary files
echo -e "${YELLOW}📝 Cleaning logs and temporary files...${NC}"
rm -rf logs/*.log
rm -rf logs/*.pid
mkdir -p logs

# Remove Python virtual environments
echo -e "${YELLOW}🐍 Removing Python virtual environments...${NC}"
rm -rf apps/svc-api/venv

# Remove Node.js node_modules (optional)
read -p "Remove Node.js dependencies? This will require reinstalling (y/N): " remove_node
if [[ "$remove_node" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📦 Removing Node.js dependencies...${NC}"
    rm -rf apps/web/node_modules
    rm -rf apps/web/package-lock.json
fi

# Remove .env file (optional)
if [[ -f .env ]]; then
    read -p "Remove .env file? You'll need to reconfigure (y/N): " remove_env
    if [[ "$remove_env" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⚙️  Removing environment configuration...${NC}"
        rm -f .env
    fi
fi

echo ""
echo -e "${GREEN}🎉 Environment reset completed!${NC}"
echo ""
echo -e "${BLUE}🚀 To start fresh:${NC}"
echo -e "   1. Run: ${YELLOW}./scripts/dev/quick-start.sh${NC}"
echo -e "   2. Or manually: ${YELLOW}cp .env.template .env${NC} and edit configuration"
echo -e "   3. Then: ${YELLOW}docker compose -f docker-compose.dev.yml up -d${NC}"
echo ""

