#!/bin/bash
# Setup ingestion service virtual environment with dependencies

set -e

LOREGUARD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INGESTION_DIR="$LOREGUARD_ROOT/apps/svc-ingestion"

cd "$INGESTION_DIR"

echo "Setting up ingestion service virtual environment..."

# Check if venv exists and has pip
if [ -f "venv/bin/python" ]; then
    if venv/bin/python -m pip --version >/dev/null 2>&1; then
        echo "✓ Virtual environment exists with pip"
        INSTALL_DEPS=true
    else
        echo "⚠ Virtual environment exists but pip not available"
        echo "Removing old venv..."
        rm -rf venv
        INSTALL_DEPS=false
    fi
else
    INSTALL_DEPS=false
fi

# Create venv if needed
if [ "$INSTALL_DEPS" = false ]; then
    echo "Creating virtual environment..."
    
    # Try to create venv with ensurepip
    if python3 -m venv venv 2>/dev/null; then
        echo "✓ Virtual environment created"
    else
        echo "❌ Failed to create virtual environment"
        echo "Please install python3-venv:"
        echo "  sudo apt install python3-venv"
        exit 1
    fi
    
    # Bootstrap pip if needed
    if ! venv/bin/python -m pip --version >/dev/null 2>&1; then
        echo "Bootstrapping pip..."
        venv/bin/python -m ensurepip --upgrade || {
            echo "❌ Failed to bootstrap pip"
            echo "Please install python3-pip:"
            echo "  sudo apt install python3-pip"
            exit 1
        }
    fi
    
    # Upgrade pip
    echo "Upgrading pip..."
    venv/bin/pip install --upgrade pip -q
fi

# Install dependencies
echo "Installing dependencies..."
venv/bin/pip install -q -r requirements.txt

# Verify scrapy installation
if venv/bin/python -m scrapy --version >/dev/null 2>&1; then
    echo "✓ Scrapy installed successfully"
    venv/bin/python -m scrapy --version | head -1
else
    echo "❌ Scrapy installation verification failed"
    exit 1
fi

echo ""
echo "✓ Ingestion service virtual environment ready!"

