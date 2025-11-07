#!/bin/bash

# LoreGuard Quick Start Script
# One-command setup for Ubuntu development environment

set -e  # Exit on any error

echo "🚀 LoreGuard Quick Start"
echo "========================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on Ubuntu
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    echo -e "${RED}❌ This script is designed for Ubuntu Linux${NC}"
    echo "Please run on Ubuntu 22.04 LTS or later"
    exit 1
fi

echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1 is available${NC}"
        return 0
    fi
}

# Check Docker
if ! check_command docker; then
    echo -e "${YELLOW}📦 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker Compose...${NC}"
    sudo apt update
    sudo apt install -y docker-compose-plugin
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
fi

# Check Node.js
if ! check_command node; then
    echo -e "${YELLOW}📦 Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    echo -e "${GREEN}✅ Node.js installed${NC}"
fi

# Check Python
if ! check_command python3; then
    echo -e "${YELLOW}📦 Installing Python...${NC}"
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip
    echo -e "${GREEN}✅ Python installed${NC}"
fi

echo ""
echo -e "${BLUE}⚙️  Setting up LoreGuard environment...${NC}"

# Create .env file if it doesn't exist
if [[ ! -f .env ]]; then
    echo -e "${YELLOW}📝 Creating environment configuration...${NC}"
    cp .env.template .env
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    MINIO_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    JWT_SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    # Update .env with generated passwords (using | as delimiter to avoid conflicts)
    sed -i "s|secure_password_here|$POSTGRES_PASSWORD|" .env
    sed -i "s|redis_password_here|$REDIS_PASSWORD|" .env
    sed -i "s|minio_password_here|$MINIO_SECRET_KEY|" .env
    sed -i "s|your_jwt_secret_key_here|$JWT_SECRET_KEY|" .env
    
    echo -e "${GREEN}✅ Environment configuration created${NC}"
else
    echo -e "${GREEN}✅ Environment configuration exists${NC}"
fi

echo ""
echo -e "${BLUE}🐳 Starting infrastructure services...${NC}"

# Start infrastructure services first
docker compose -f docker-compose.dev.yml up -d postgres redis minio

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL"
until docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U loreguard &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

# Wait for Redis
echo -n "Waiting for Redis"
until docker compose -f docker-compose.dev.yml exec -T redis redis-cli ping &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

# Wait for MinIO
echo -n "Waiting for MinIO"
MINIO_HOST=${LOREGUARD_HOST_IP:-localhost}
until curl -s http://${MINIO_HOST}:9000/minio/health/ready &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

echo ""
echo -e "${BLUE}🗄️  Initializing databases...${NC}"

# Initialize databases
./scripts/dev/init-databases.sh

echo ""
echo -e "${BLUE}🔧 Setting up backend API...${NC}"

# Setup backend
cd apps/svc-api

if [[ ! -d venv ]]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt

echo -e "${YELLOW}🚀 Starting backend API...${NC}"
nohup python -m app.main > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../../logs/backend.pid

# Wait for backend to start
echo -n "Waiting for backend API"
API_HOST=${LOREGUARD_HOST_IP:-localhost}
until curl -s http://${API_HOST}:8000/health &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

cd ../..

echo ""
echo -e "${BLUE}🎨 Setting up frontend...${NC}"

# Setup frontend
cd apps/web

if [[ ! -d node_modules ]]; then
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm install
fi

echo -e "${YELLOW}🚀 Starting frontend development server...${NC}"
nohup npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../../logs/frontend.pid

# Wait for frontend to start
echo -n "Waiting for frontend"
WEB_HOST=${LOREGUARD_HOST_IP:-localhost}
until curl -s http://${WEB_HOST}:6060 &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

cd ../..

echo ""
echo -e "${BLUE}📊 Loading sample data...${NC}"

# Load sample data
./scripts/dev/load-sample-data.sh

echo ""
echo -e "${BLUE}🔍 Running health checks...${NC}"

# Run health checks
./scripts/dev/health-check.sh

echo ""
echo -e "${GREEN}🎉 LoreGuard is ready!${NC}"
echo ""
echo -e "${BLUE}📱 Access URLs:${NC}"
HOST_IP=${LOREGUARD_HOST_IP:-localhost}
echo -e "   Frontend:     ${YELLOW}http://${HOST_IP}:6060${NC}"
echo -e "   Backend API:  ${YELLOW}http://${HOST_IP}:8000${NC}"
echo -e "   API Docs:     ${YELLOW}http://${HOST_IP}:8000/docs${NC}"
echo -e "   MinIO Console:${YELLOW}http://${HOST_IP}:9001${NC}"
echo ""
echo -e "${BLUE}🔐 Default Login:${NC}"
echo -e "   Email:    ${YELLOW}admin@loreguard.local${NC}"
echo -e "   Password: ${YELLOW}admin${NC}"
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo -e "   Stop services:    ${YELLOW}./scripts/dev/stop-services.sh${NC}"
echo -e "   View logs:        ${YELLOW}./scripts/dev/view-logs.sh${NC}"
echo -e "   Health check:     ${YELLOW}./scripts/dev/health-check.sh${NC}"
echo -e "   Reset everything: ${YELLOW}./scripts/dev/reset-environment.sh${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

