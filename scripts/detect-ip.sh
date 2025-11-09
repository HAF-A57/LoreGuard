#!/bin/bash
#
# LoreGuard IP Detection Script
# Detects the host machine's IP address for network access
# This script is automatically called before Docker Compose operations
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to validate IP address format
validate_ip() {
    local ip=$1
    # Check if it matches IPv4 pattern
    if [[ $ip =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        # Check each octet is <= 255
        IFS='.' read -ra ADDR <<< "$ip"
        for i in "${ADDR[@]}"; do
            if [[ $i -gt 255 ]]; then
                return 1
            fi
        done
        return 0
    fi
    return 1
}

# Function to detect IP address with improved reliability
detect_ip() {
    local detected_ip=""
    local method=""
    
    # Method 1: Get primary network interface IP (most reliable on Linux)
    # Uses the route to 8.8.8.8 to find the interface that would be used for internet traffic
    if command -v ip &> /dev/null; then
        detected_ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' | head -1 | tr -d '[:space:]')
        if [ ! -z "$detected_ip" ] && [ "$detected_ip" != "127.0.0.1" ] && validate_ip "$detected_ip"; then
            method="ip route (default gateway)"
            echo "$detected_ip"
            return 0
        fi
    fi
    
    # Method 2: Get IP from default route interface (hostname -I)
    if command -v hostname &> /dev/null; then
        detected_ip=$(hostname -I 2>/dev/null | awk '{print $1}' | tr -d '[:space:]')
        if [ ! -z "$detected_ip" ] && [ "$detected_ip" != "127.0.0.1" ] && validate_ip "$detected_ip"; then
            method="hostname -I"
            echo "$detected_ip"
            return 0
        fi
    fi
    
    # Method 3: Check active network interfaces directly
    if command -v ip &> /dev/null; then
        # Get list of all network interfaces
        for interface in $(ip -o link show | awk -F': ' '{print $2}' | grep -v lo); do
            if [ -f "/sys/class/net/$interface/operstate" ]; then
                if [ "$(cat /sys/class/net/$interface/operstate 2>/dev/null)" = "up" ]; then
                    detected_ip=$(ip addr show "$interface" 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | head -1 | tr -d '[:space:]')
                    if [ ! -z "$detected_ip" ] && [ "$detected_ip" != "127.0.0.1" ] && validate_ip "$detected_ip"; then
                        # Skip Docker and virtual interfaces
                        if [[ ! "$interface" =~ ^(docker|br-|veth|virbr) ]]; then
                            method="interface $interface"
                            echo "$detected_ip"
                            return 0
                        fi
                    fi
                fi
            fi
        done
    fi
    
    # Method 4: Check common network interfaces by name
    for interface in eth0 enp0s3 enp0s8 enp1s0 eth1 wlan0 wlp2s0; do
        if [ -f "/sys/class/net/$interface/operstate" ]; then
            if [ "$(cat /sys/class/net/$interface/operstate 2>/dev/null)" = "up" ]; then
                detected_ip=$(ip addr show "$interface" 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | head -1 | tr -d '[:space:]')
                if [ ! -z "$detected_ip" ] && [ "$detected_ip" != "127.0.0.1" ] && validate_ip "$detected_ip"; then
                    method="interface $interface"
                    echo "$detected_ip"
                    return 0
                fi
            fi
        fi
    done
    
    # Method 5: Use getent to resolve hostname (if hostname resolves to non-localhost IP)
    if command -v getent &> /dev/null; then
        local hostname=$(hostname 2>/dev/null)
        if [ ! -z "$hostname" ]; then
            detected_ip=$(getent ahostsv4 "$hostname" 2>/dev/null | awk '{print $1}' | grep -v '^127\.' | head -1 | tr -d '[:space:]')
            if [ ! -z "$detected_ip" ] && validate_ip "$detected_ip"; then
                method="hostname resolution"
                echo "$detected_ip"
                return 0
            fi
        fi
    fi
    
    # Method 6: Fallback - use ifconfig if available
    if command -v ifconfig &> /dev/null; then
        detected_ip=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1 | tr -d '[:space:]')
        if [ ! -z "$detected_ip" ] && validate_ip "$detected_ip"; then
            method="ifconfig"
            echo "$detected_ip"
            return 0
        fi
    fi
    
    # If all else fails, return localhost
    echo "127.0.0.1"
    return 1
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}Detecting host IP address for LoreGuard...${NC}"
echo -e "${BLUE}Note: This script detects IP dynamically for THIS machine.${NC}"
echo -e "${BLUE}      Generated files are gitignored and machine-specific.${NC}"
echo ""

# IMPORTANT: Always detect IP fresh - never read from old .env.detected files
# Only respect LOREGUARD_HOST_IP if explicitly set by user (not from files)
# This ensures each developer gets their own machine's IP
if [ ! -z "$LOREGUARD_HOST_IP" ] && validate_ip "$LOREGUARD_HOST_IP" && [ "$LOREGUARD_HOST_IP" != "127.0.0.1" ]; then
    # User explicitly set it (e.g., export LOREGUARD_HOST_IP=...)
    # This allows manual override for special cases
    DETECTED_IP="$LOREGUARD_HOST_IP"
    echo -e "${GREEN}Using explicitly provided IP address: $DETECTED_IP${NC}"
    echo -e "${YELLOW}   (IP was set via environment variable - skipping auto-detection)${NC}"
else
    # Always detect IP fresh - ignore any existing .env.detected files
    echo -e "${BLUE}Detecting IP address for this machine...${NC}"
    DETECTED_IP=$(detect_ip)
    
    if [ "$DETECTED_IP" = "127.0.0.1" ]; then
        echo -e "${YELLOW}⚠️  Warning: Could not detect network IP, using 127.0.0.1 (localhost only)${NC}"
        echo -e "${YELLOW}   If you need network access, manually set LOREGUARD_HOST_IP environment variable${NC}"
        echo -e "${YELLOW}   Example: export LOREGUARD_HOST_IP=192.168.1.100${NC}"
    else
        echo -e "${GREEN}✓ Detected IP address for this machine: $DETECTED_IP${NC}"
    fi
fi

# Validate the IP before proceeding
if ! validate_ip "$DETECTED_IP"; then
    echo -e "${RED}❌ Error: Invalid IP address format: $DETECTED_IP${NC}"
    exit 1
fi

# Note: We use a single .env file as the source of truth (industry best practice)
# The .env file will be updated below with the detected IP

# Write to .env file (Docker Compose reads this automatically)
# Preserve existing .env content if it exists, only update/add LOREGUARD_HOST_IP related vars
ENV_FILE=".env"
ENV_TEMPLATE=".env.template"

if [ -f "$ENV_FILE" ]; then
    # Backup existing .env
    cp "$ENV_FILE" "$ENV_FILE.bak" 2>/dev/null || true
    
    # Remove old LOREGUARD_HOST_IP entries if they exist
    # Filter out IP-related variables and keep everything else
    awk '
      /^LOREGUARD_HOST_IP=/ { next }
      /^LOREGUARD_API_URL=/ { next }
      /^LOREGUARD_NORMALIZE_URL=/ { next }
      /^LOREGUARD_FRONTEND_URL=/ { next }
      /^LOREGUARD_MINIO_URL=/ { next }
      /^LOREGUARD_MINIO_CONSOLE_URL=/ { next }
      /^LOREGUARD_POSTGRES_HOST=/ { next }
      /^LOREGUARD_REDIS_HOST=/ { next }
      /^BACKEND_CORS_ORIGINS=/ { next }
      { print }
    ' "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || cp "$ENV_FILE" "$ENV_FILE.tmp"
    
    # Add new IP detection entries
    cat >> "$ENV_FILE.tmp" <<EOF

# Auto-detected host IP address (DO NOT EDIT - Generated by scripts/detect-ip.sh)
# NOTE: This is machine-specific and will differ for each developer
# Run 'make detect-ip' to update with your machine's current IP
LOREGUARD_HOST_IP=$DETECTED_IP
LOREGUARD_API_URL=http://$DETECTED_IP:8000
LOREGUARD_NORMALIZE_URL=http://$DETECTED_IP:8001
LOREGUARD_FRONTEND_URL=http://$DETECTED_IP:6060
LOREGUARD_MINIO_URL=http://$DETECTED_IP:9000
LOREGUARD_MINIO_CONSOLE_URL=http://$DETECTED_IP:9001
LOREGUARD_POSTGRES_HOST=$DETECTED_IP
LOREGUARD_REDIS_HOST=$DETECTED_IP

# CORS Configuration - Includes detected IP for network access
# Allows frontend access from both network IP and localhost
BACKEND_CORS_ORIGINS=http://$DETECTED_IP:6060,http://$DETECTED_IP:5173,http://$DETECTED_IP:3000,http://localhost:6060,http://localhost:5173,http://localhost:3000
EOF
    
    mv "$ENV_FILE.tmp" "$ENV_FILE"
    echo -e "${GREEN}✓ Updated $ENV_FILE with detected IP${NC}"
else
    # .env doesn't exist - create it from template if available
    if [ -f "$ENV_TEMPLATE" ]; then
        echo -e "${BLUE}📝 Creating .env from .env.template...${NC}"
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        
        # Now update it with detected IP (same as above)
        awk '
          /^LOREGUARD_HOST_IP=/ { next }
          /^LOREGUARD_API_URL=/ { next }
          /^LOREGUARD_NORMALIZE_URL=/ { next }
          /^LOREGUARD_FRONTEND_URL=/ { next }
          /^LOREGUARD_MINIO_URL=/ { next }
          /^LOREGUARD_MINIO_CONSOLE_URL=/ { next }
          /^LOREGUARD_POSTGRES_HOST=/ { next }
          /^LOREGUARD_REDIS_HOST=/ { next }
          /^BACKEND_CORS_ORIGINS=/ { next }
          { print }
        ' "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || cp "$ENV_FILE" "$ENV_FILE.tmp"
        
        # Add IP detection entries
        cat >> "$ENV_FILE.tmp" <<EOF

# Auto-detected host IP address (DO NOT EDIT - Generated by scripts/detect-ip.sh)
# NOTE: This is machine-specific and will differ for each developer
# Run 'make detect-ip' to update with your machine's current IP
LOREGUARD_HOST_IP=$DETECTED_IP
LOREGUARD_API_URL=http://$DETECTED_IP:8000
LOREGUARD_NORMALIZE_URL=http://$DETECTED_IP:8001
LOREGUARD_FRONTEND_URL=http://$DETECTED_IP:6060
LOREGUARD_MINIO_URL=http://$DETECTED_IP:9000
LOREGUARD_MINIO_CONSOLE_URL=http://$DETECTED_IP:9001
LOREGUARD_POSTGRES_HOST=$DETECTED_IP
LOREGUARD_REDIS_HOST=$DETECTED_IP

# CORS Configuration - Includes detected IP for network access
# Allows frontend access from both network IP and localhost
BACKEND_CORS_ORIGINS=http://$DETECTED_IP:6060,http://$DETECTED_IP:5173,http://$DETECTED_IP:3000,http://localhost:6060,http://localhost:5173,http://localhost:3000
EOF
        
        mv "$ENV_FILE.tmp" "$ENV_FILE"
        echo -e "${GREEN}✓ Created $ENV_FILE from template with detected IP${NC}"
        echo -e "${YELLOW}⚠️  Note: You may want to update passwords and API keys in .env${NC}"
    else
        # No template either - create minimal .env with just IP detection
        echo -e "${YELLOW}⚠️  Warning: .env.template not found. Creating minimal .env file.${NC}"
        echo -e "${YELLOW}   Consider copying .env.template to .env and running detect-ip again.${NC}"
        cat > "$ENV_FILE" <<EOF
# LoreGuard Environment Configuration
# Auto-detected host IP address (DO NOT EDIT - Generated by scripts/detect-ip.sh)
# NOTE: This is machine-specific and will differ for each developer
# Run 'make detect-ip' to update with your machine's current IP
# 
# WARNING: This is a minimal .env file. For full configuration, copy .env.template to .env
LOREGUARD_HOST_IP=$DETECTED_IP
LOREGUARD_API_URL=http://$DETECTED_IP:8000
LOREGUARD_NORMALIZE_URL=http://$DETECTED_IP:8001
LOREGUARD_FRONTEND_URL=http://$DETECTED_IP:6060
LOREGUARD_MINIO_URL=http://$DETECTED_IP:9000
LOREGUARD_MINIO_CONSOLE_URL=http://$DETECTED_IP:9001
LOREGUARD_POSTGRES_HOST=$DETECTED_IP
LOREGUARD_REDIS_HOST=$DETECTED_IP

# CORS Configuration - Includes detected IP for network access
# Allows frontend access from both network IP and localhost
BACKEND_CORS_ORIGINS=http://$DETECTED_IP:6060,http://$DETECTED_IP:5173,http://$DETECTED_IP:3000,http://localhost:6060,http://localhost:5173,http://localhost:3000
EOF
        echo -e "${GREEN}✓ Created minimal $ENV_FILE with detected IP${NC}"
    fi
fi

# Write to apps/web/.env.local (for Vite - VITE_ prefix required)
FRONTEND_ENV_FILE="apps/web/.env.local"
mkdir -p "$(dirname "$FRONTEND_ENV_FILE")"

cat > "$FRONTEND_ENV_FILE" <<EOF
# LoreGuard Frontend Environment Variables
# Auto-generated by scripts/detect-ip.sh
# This file is git-ignored and safe for local development
# DO NOT EDIT MANUALLY - This file is auto-generated and machine-specific
# Each developer's machine will have different IP addresses
# Run 'make detect-ip' to regenerate with your machine's current IP

# API Configuration - MUST use VITE_ prefix for Vite to read them
VITE_API_URL=http://$DETECTED_IP:8000
VITE_API_PORT=8000
VITE_HOST_IP=$DETECTED_IP

# Development Mode
VITE_ENVIRONMENT=development
EOF

echo -e "${GREEN}✓ Frontend IP configuration written to $FRONTEND_ENV_FILE${NC}"

# Note: We use a single .env file as the source of truth
# All services (Docker Compose, Python, shell scripts) read from root .env file
# This simplifies the configuration and avoids redundancy

# Export for current session (so subsequent commands in same shell can use it)
export LOREGUARD_HOST_IP="$DETECTED_IP"
export LOREGUARD_API_URL="http://$DETECTED_IP:8000"
export LOREGUARD_NORMALIZE_URL="http://$DETECTED_IP:8001"
export LOREGUARD_FRONTEND_URL="http://$DETECTED_IP:6060"
export VITE_API_URL="http://$DETECTED_IP:8000"
export VITE_HOST_IP="$DETECTED_IP"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  IP Detection Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Configuration files updated:${NC}"
echo -e "  • Root:     $ENV_FILE (single source of truth - used by Docker Compose and all services)"
echo -e "  • Frontend: $FRONTEND_ENV_FILE"
echo ""
echo -e "${BLUE}Detected IP: ${GREEN}$DETECTED_IP${NC}"
echo ""
echo -e "${BLUE}Environment variables exported for current session:${NC}"
echo -e "  LOREGUARD_HOST_IP=$DETECTED_IP"
echo -e "  VITE_API_URL=http://$DETECTED_IP:8000"
echo ""
echo -e "${YELLOW}💡 Tip: Docker Compose and all services automatically use the IP from .env file${NC}"
echo -e "${YELLOW}   You can source .env: source .env${NC}"

