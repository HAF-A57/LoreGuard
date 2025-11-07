#!/bin/bash

# LoreGuard Service Startup Script
# Starts all application services in background and verifies they're running
# Usage: ./start-services.sh [web-only]
#   web-only: Only start the frontend service (backend services are containerized)

set -e

# Check if web-only mode
WEB_ONLY=false
if [ "$1" = "web-only" ]; then
    WEB_ONLY=true
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment
if [[ -f .env.detected ]]; then
    source .env.detected
fi

LOREGUARD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$LOREGUARD_ROOT"

echo -e "${BLUE}🚀 Starting LoreGuard Application Services${NC}"
echo ""

# Check dependencies
echo -e "${BLUE}📋 Checking dependencies...${NC}"

# Check Python venv - verify ensurepip is available or test venv creation
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)

if ! python3 -c "import ensurepip" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  python3-venv package not installed${NC}"
    echo -e "${YELLOW}   Attempting to create venv without pip (will install pip manually)...${NC}"
    
    # Test if we can create venv without pip
    TEMP_TEST=$(mktemp -d)
    if python3 -m venv --without-pip "$TEMP_TEST" 2>/dev/null; then
        rm -rf "$TEMP_TEST"
        VENV_WITHOUT_PIP=true
        echo -e "${GREEN}✓ Can create venv without pip${NC}"
    else
        rm -rf "$TEMP_TEST" 2>/dev/null
        echo -e "${RED}❌ Cannot create virtual environment${NC}"
        echo -e "${YELLOW}   Install with: sudo apt install python${PYTHON_VERSION}-venv${NC}"
        echo -e "${YELLOW}   Then run: make quick-start${NC}"
        exit 1
    fi
else
    VENV_WITHOUT_PIP=false
fi

# Check Node.js
if ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}❌ npm not found${NC}"
    echo -e "${YELLOW}   Install Node.js first${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies OK${NC}"
echo ""

# Create PID directory
mkdir -p logs
PID_DIR="$LOREGUARD_ROOT/logs"

# Function to check if service is running
check_service() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    local host=${LOREGUARD_HOST_IP:-localhost}
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://${host}:$port/health >/dev/null 2>&1 || \
           curl -s -f http://127.0.0.1:$port/health >/dev/null 2>&1 || \
           curl -s -f http://${host}:$port >/dev/null 2>&1 || \
           curl -s -f http://127.0.0.1:$port >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

# Start API service (skip if web-only mode)
if [ "$WEB_ONLY" = "false" ]; then
    echo -e "${BLUE}📡 Starting API service (port 8000)...${NC}"
    cd "$LOREGUARD_ROOT/apps/svc-api"

    # Remove broken venv if it exists but doesn't work
    if [ -d venv ] && [ ! -f venv/bin/python ]; then
        echo "Removing broken virtual environment..."
        rm -rf venv
    fi

    # Check if venv exists and is valid
    if [ ! -d venv ] || [ ! -f venv/bin/python ]; then
        echo "Creating virtual environment..."
        if [ "$VENV_WITHOUT_PIP" = "true" ]; then
            python3 -m venv --without-pip venv || {
                echo -e "${RED}❌ Failed to create virtual environment${NC}"
                echo -e "${YELLOW}   Install with: sudo apt install python${PYTHON_VERSION}-venv${NC}"
                exit 1
            }
            # Install pip manually
            echo "Installing pip in virtual environment..."
            source venv/bin/activate
            curl -sS https://bootstrap.pypa.io/get-pip.py | python3 2>&1 | grep -v "already installed" || {
                echo -e "${YELLOW}⚠️  Using alternative pip installation method...${NC}"
                python3 -m ensurepip --upgrade --default-pip 2>/dev/null || {
                    echo -e "${RED}❌ Cannot install pip. Please install python${PYTHON_VERSION}-venv${NC}"
                    echo -e "${YELLOW}   Run: sudo apt install python${PYTHON_VERSION}-venv${NC}"
                    exit 1
                }
            }
            deactivate
        else
            python3 -m venv venv || {
                echo -e "${RED}❌ Failed to create virtual environment${NC}"
                echo -e "${YELLOW}   Install with: sudo apt install python${PYTHON_VERSION}-venv${NC}"
                exit 1
            }
        fi
    fi

    source venv/bin/activate
    pip install --upgrade pip -q >/dev/null 2>&1 || true
    pip install -r requirements.txt -q >/dev/null 2>&1 || {
        echo -e "${RED}❌ Failed to install API dependencies${NC}"
        exit 1
    }

    # Export environment variables (load both .env.detected and .env)
    # Use 'source' with set -a to properly handle all variable formats
    if [ -f "$LOREGUARD_ROOT/.env.detected" ]; then
        set -a
        source "$LOREGUARD_ROOT/.env.detected" 2>/dev/null || true
        set +a
    fi
    if [ -f "$LOREGUARD_ROOT/.env" ]; then
        set -a
        source "$LOREGUARD_ROOT/.env" 2>/dev/null || true
        set +a
    fi

    # Function to check if port is in use
    check_port() {
        local port=$1
        if command -v lsof >/dev/null 2>&1; then
            lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
        elif command -v ss >/dev/null 2>&1; then
            ss -tln | grep -q ":$port "
        elif command -v netstat >/dev/null 2>&1; then
            netstat -tln | grep -q ":$port "
        else
            # Fallback: try to connect
            timeout 1 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null
        fi
    }

    if check_port 8000; then
        echo -e "${YELLOW}⚠️  Port 8000 already in use, skipping API start${NC}"
        API_PID=""
    else
        # Use uvicorn directly with reload for auto-restart on code changes
        nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$PID_DIR/api.log" 2>&1 &
        API_PID=$!
        echo $API_PID > "$PID_DIR/api.pid"
        echo -e "${GREEN}✓ API service started (PID: $API_PID) with auto-reload enabled${NC}"
    fi

    # Wait for API
    sleep 3
    if check_service 8000 "API"; then
        echo -e "${GREEN}✓ API service is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  API service may still be starting...${NC}"
    fi
else
    echo -e "${BLUE}⏭️  Skipping API service (containerized)${NC}"
fi

# Start Normalize service (skip if web-only mode)
if [ "$WEB_ONLY" = "false" ]; then
    echo -e "${BLUE}📄 Starting Normalize service (port 8001)...${NC}"
    cd "$LOREGUARD_ROOT/apps/svc-normalize"

# Remove broken venv if it exists but doesn't work
if [ -d venv ] && [ ! -f venv/bin/python ]; then
    echo "Removing broken virtual environment..."
    rm -rf venv
fi

# Check if venv exists and is valid
if [ ! -d venv ] || [ ! -f venv/bin/python ]; then
    echo "Creating virtual environment..."
    if [ "$VENV_WITHOUT_PIP" = "true" ]; then
        python3 -m venv --without-pip venv || {
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            echo -e "${YELLOW}   Install with: sudo apt install python${PYTHON_VERSION}-venv${NC}"
            exit 1
        }
        # Install pip manually
        echo "Installing pip in virtual environment..."
        source venv/bin/activate
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3 2>&1 | grep -v "already installed" || {
            echo -e "${YELLOW}⚠️  Using alternative pip installation method...${NC}"
            python3 -m ensurepip --upgrade --default-pip 2>/dev/null || {
                echo -e "${RED}❌ Cannot install pip. Please install python${PYTHON_VERSION}-venv${NC}"
                echo -e "${YELLOW}   Run: sudo apt install python${PYTHON_VERSION}-venv${NC}"
                exit 1
            }
        }
        deactivate
    else
        python3 -m venv venv || {
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            echo -e "${YELLOW}   Install with: sudo apt install python${PYTHON_VERSION}-venv${NC}"
            exit 1
        }
    fi
fi

source venv/bin/activate
pip install --upgrade pip -q >/dev/null 2>&1 || true
pip install -r requirements.txt -q >/dev/null 2>&1 || {
    echo -e "${RED}❌ Failed to install Normalize dependencies${NC}"
    exit 1
}

# Export environment variables (load both .env.detected and .env)
# Only export lines that match KEY=VALUE format (skip comments and invalid lines)
if [ -f "$LOREGUARD_ROOT/.env.detected" ]; then
    set -a
    source "$LOREGUARD_ROOT/.env.detected" 2>/dev/null || true
    set +a
fi
if [ -f "$LOREGUARD_ROOT/.env" ]; then
    set -a
    source "$LOREGUARD_ROOT/.env" 2>/dev/null || true
    set +a
fi

# Check if port is already in use
if check_port 8001; then
    echo -e "${YELLOW}⚠️  Port 8001 already in use, skipping Normalize start${NC}"
    NORMALIZE_PID=""
else
    # Use uvicorn directly with reload for auto-restart on code changes
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > "$PID_DIR/normalize.log" 2>&1 &
    NORMALIZE_PID=$!
    echo $NORMALIZE_PID > "$PID_DIR/normalize.pid"
    echo -e "${GREEN}✓ Normalize service started (PID: $NORMALIZE_PID) with auto-reload enabled${NC}"
fi

    # Wait for Normalize
    sleep 3
    if check_service 8001 "Normalize"; then
        echo -e "${GREEN}✓ Normalize service is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Normalize service may still be starting...${NC}"
    fi
else
    echo -e "${BLUE}⏭️  Skipping Normalize service (containerized)${NC}"
fi

# Start AI Assistant service (skip if web-only mode)
if [ "$WEB_ONLY" = "false" ]; then
    echo -e "${BLUE}🤖 Starting AI Assistant service (port 8002)...${NC}"
    cd "$LOREGUARD_ROOT/apps/svc-assistant"

# Remove broken venv if it exists but doesn't work
if [ -d venv ] && [ ! -f venv/bin/python ]; then
    echo "Removing broken virtual environment..."
    rm -rf venv
fi

# Check if venv exists and is valid
if [ ! -d venv ] || [ ! -f venv/bin/python ]; then
    echo "Creating virtual environment..."
    if [ "$VENV_WITHOUT_PIP" = true ]; then
        python3 -m venv --without-pip venv || {
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            exit 1
        }
        # Install pip manually
        echo "Installing pip in virtual environment..."
        source venv/bin/activate
        curl -sS https://bootstrap.pypa.io/get-pip.py | python3 2>&1 | grep -v "already installed" || {
            echo -e "${YELLOW}⚠️  Using alternative pip installation method...${NC}"
            python3 -m ensurepip --upgrade --default-pip 2>/dev/null || {
                echo -e "${RED}❌ Cannot install pip. Please install python${PYTHON_VERSION}-venv${NC}"
                echo -e "${YELLOW}   Run: sudo apt install python${PYTHON_VERSION}-venv${NC}"
                exit 1
            }
        }
        deactivate
    else
        python3 -m venv venv || {
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            echo -e "${YELLOW}   Install with: sudo apt install python${PYTHON_VERSION}-venv${NC}"
            exit 1
        }
    fi
fi

source venv/bin/activate
pip install --upgrade pip -q >/dev/null 2>&1 || true
pip install -r requirements.txt -q >/dev/null 2>&1 || {
    echo -e "${RED}❌ Failed to install Assistant dependencies${NC}"
    exit 1
}

# Export environment variables
if [ -f "$LOREGUARD_ROOT/.env.detected" ]; then
    set -a
    source "$LOREGUARD_ROOT/.env.detected" 2>/dev/null || true
    set +a
fi
if [ -f "$LOREGUARD_ROOT/.env" ]; then
    set -a
    source "$LOREGUARD_ROOT/.env" 2>/dev/null || true
    set +a
fi

# Check if port is already in use
if check_port 8002; then
    echo -e "${YELLOW}⚠️  Port 8002 already in use, skipping Assistant start${NC}"
    ASSISTANT_PID=""
else
    # Set PYTHONPATH to include svc-api for database access
    export PYTHONPATH="$LOREGUARD_ROOT/apps/svc-api:$PYTHONPATH"
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload > "$PID_DIR/assistant.log" 2>&1 &
    ASSISTANT_PID=$!
    echo $ASSISTANT_PID > "$PID_DIR/assistant.pid"
    echo -e "${GREEN}✓ AI Assistant service started (PID: $ASSISTANT_PID) with auto-reload enabled${NC}"
fi

    # Wait for Assistant
    sleep 3
    if check_service 8002 "Assistant"; then
        echo -e "${GREEN}✓ AI Assistant service is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  AI Assistant service may still be starting...${NC}"
    fi
else
    echo -e "${BLUE}⏭️  Skipping AI Assistant service (containerized)${NC}"
fi

# Start Web service (always start)
echo -e "${BLUE}🌐 Starting Frontend service (port 6060)...${NC}"
cd "$LOREGUARD_ROOT/apps/web"

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "Installing npm dependencies..."
    npm install || {
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    }
fi

# Export environment variables
# Use 'source' with set -a to properly handle all variable formats
if [ -f "$LOREGUARD_ROOT/.env.detected" ]; then
    set -a
    source "$LOREGUARD_ROOT/.env.detected" 2>/dev/null || true
    set +a
fi

# Check if port is already in use
if check_port 6060; then
    echo -e "${YELLOW}⚠️  Port 6060 already in use, skipping Frontend start${NC}"
    WEB_PID=""
else
    nohup npm run dev > "$PID_DIR/web.log" 2>&1 &
    WEB_PID=$!
    echo $WEB_PID > "$PID_DIR/web.pid"
    echo -e "${GREEN}✓ Frontend service started (PID: $WEB_PID)${NC}"
fi

# Wait for Web
sleep 5
if check_service 6060 "Frontend"; then
    echo -e "${GREEN}✓ Frontend service is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend service may still be starting...${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Services startup complete!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
if [ "$WEB_ONLY" = "false" ]; then
    [ -n "$API_PID" ] && echo -e "   API:       http://${LOREGUARD_HOST_IP:-localhost}:8000 (PID: $API_PID)" || echo -e "   API:       ${YELLOW}Not started (port in use)${NC}"
    [ -n "$NORMALIZE_PID" ] && echo -e "   Normalize: http://${LOREGUARD_HOST_IP:-localhost}:8001 (PID: $NORMALIZE_PID)" || echo -e "   Normalize: ${YELLOW}Not started (port in use)${NC}"
    [ -n "$ASSISTANT_PID" ] && echo -e "   Assistant: http://${LOREGUARD_HOST_IP:-localhost}:8002 (PID: $ASSISTANT_PID)" || echo -e "   Assistant: ${YELLOW}Not started (port in use)${NC}"
else
    echo -e "   API:       ${BLUE}Running in container${NC}"
    echo -e "   Normalize: ${BLUE}Running in container${NC}"
    echo -e "   Assistant: ${BLUE}Running in container${NC}"
fi
[ -n "$WEB_PID" ] && echo -e "   Frontend:  http://${LOREGUARD_HOST_IP:-localhost}:6060 (PID: $WEB_PID) ${GREEN}[Hot Reload Enabled]${NC}" || echo -e "   Frontend:  ${YELLOW}Not started (port in use)${NC}"
echo ""
if [ "$WEB_ONLY" = "false" ]; then
    echo -e "${BLUE}📝 Logs:${NC}"
    echo -e "   API:       tail -f logs/api.log"
    echo -e "   Normalize: tail -f logs/normalize.log"
    echo -e "   Assistant: tail -f logs/assistant.log"
    echo -e "   Frontend:  tail -f logs/web.log"
    echo ""
fi
echo -e "${BLUE}📝 Container Logs:${NC}"
echo -e "   docker compose -f docker-compose.dev.yml logs -f loreguard-api"
echo -e "   docker compose -f docker-compose.dev.yml logs -f loreguard-normalize"
echo -e "   docker compose -f docker-compose.dev.yml logs -f loreguard-assistant"
echo ""
echo -e "${YELLOW}💡 To stop services: make stop-services${NC}"

