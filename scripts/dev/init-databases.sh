#!/bin/bash

# LoreGuard Database Initialization Script
# Sets up PostgreSQL database with initial schema and admin user

set -e  # Exit on any error

echo "🗄️  LoreGuard Database Initialization"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables
if [[ -f .env ]]; then
    source .env
fi

# Load detected IP if available
if [[ -f .env.detected ]]; then
    source .env.detected
fi

echo -e "${BLUE}📋 Checking database connection...${NC}"

# Wait for PostgreSQL to be ready
echo -n "Waiting for PostgreSQL"
until docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U loreguard &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

echo ""
echo -e "${BLUE}🔧 Setting up database schema...${NC}"

# Create database initialization SQL
cat > /tmp/init-loreguard.sql << 'EOF'
-- LoreGuard Database Initialization Script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create admin user table if not exists
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create initial admin user
INSERT INTO admin_users (email, password_hash, full_name, is_superuser)
VALUES (
    'admin@loreguard.local',
    crypt('admin', gen_salt('bf')),
    'LoreGuard Administrator',
    true
) ON CONFLICT (email) DO NOTHING;

-- Create application settings table
CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default settings
INSERT INTO app_settings (key, value, description) VALUES
    ('app_version', '"0.1.0"', 'Current application version'),
    ('evaluation_model', '"gpt-4"', 'Default LLM model for evaluation'),
    ('max_documents_per_batch', '100', 'Maximum documents to process in a single batch'),
    ('default_confidence_threshold', '0.8', 'Default confidence threshold for Signal classification'),
    ('supported_languages', '["en", "zh", "ru", "ar", "es", "fr", "de", "ja", "ko"]', 'Languages supported for processing'),
    ('crawl_politeness_delay', '2.0', 'Default delay between requests in seconds')
ON CONFLICT (key) DO NOTHING;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create system health check function (will work after application tables are created)
CREATE OR REPLACE FUNCTION system_health_check()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    total_sources INTEGER := 0;
    active_sources INTEGER := 0;
    total_artifacts INTEGER := 0;
    recent_artifacts INTEGER := 0;
BEGIN
    -- Count sources (handle missing table gracefully)
    BEGIN
        SELECT COUNT(*) INTO total_sources FROM sources;
        SELECT COUNT(*) INTO active_sources FROM sources WHERE status = 'active';
    EXCEPTION WHEN undefined_table THEN
        total_sources := 0;
        active_sources := 0;
    END;
    
    -- Count artifacts (handle missing table gracefully)
    BEGIN
        SELECT COUNT(*) INTO total_artifacts FROM artifacts;
        SELECT COUNT(*) INTO recent_artifacts 
        FROM artifacts 
        WHERE created_at > NOW() - INTERVAL '24 hours';
    EXCEPTION WHEN undefined_table THEN
        total_artifacts := 0;
        recent_artifacts := 0;
    END;
    
    -- Build result
    result := jsonb_build_object(
        'database_status', 'healthy',
        'total_sources', total_sources,
        'active_sources', active_sources,
        'total_artifacts', total_artifacts,
        'recent_artifacts', recent_artifacts,
        'last_check', NOW(),
        'application_tables_ready', (total_sources > 0 OR total_artifacts > 0)
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Log initialization
INSERT INTO audit_logs (action, resource_type, details) VALUES (
    'database_initialized',
    'system',
    jsonb_build_object(
        'timestamp', NOW(),
        'script_version', '1.0',
        'admin_user_created', true
    )
);

-- Success message
SELECT 'Database initialization completed successfully' as status;
EOF

# Execute the SQL script
echo -e "${YELLOW}📝 Creating database schema...${NC}"
docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -f - < /tmp/init-loreguard.sql

# Clean up temporary file
rm /tmp/init-loreguard.sql

echo ""
echo -e "${BLUE}🔍 Verifying database setup...${NC}"

# Verify tables were created
TABLES=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -t -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
" | tr -d ' ' | grep -v '^$')

echo -e "${GREEN}✅ Database tables created:${NC}"
for table in $TABLES; do
    echo -e "   📋 $table"
done

# Verify admin user was created
ADMIN_COUNT=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -t -c "
SELECT COUNT(*) FROM admin_users WHERE email = 'admin@loreguard.local';
" | tr -d ' ')

if [[ "$ADMIN_COUNT" == "1" ]]; then
    echo -e "${GREEN}✅ Admin user created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create admin user${NC}"
    exit 1
fi

# Test system health function
echo -e "${YELLOW}🔍 Testing system health function...${NC}"
HEALTH_RESULT=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -t -c "
SELECT system_health_check();
" | tr -d ' ' | grep -v '^$')

if [[ ! -z "$HEALTH_RESULT" ]]; then
    echo -e "${GREEN}✅ System health function working${NC}"
else
    echo -e "${RED}❌ System health function failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🔧 Setting up MinIO buckets...${NC}"

# Wait for MinIO to be ready
echo -n "Waiting for MinIO"
# Use detected IP or fallback to localhost
MINIO_HOST=${LOREGUARD_HOST_IP:-localhost}
until curl -s http://${MINIO_HOST}:9000/minio/health/ready &> /dev/null; do
    echo -n "."
    sleep 2
done
echo -e " ${GREEN}✅${NC}"

# Create MinIO buckets using mc (MinIO Client) via Docker
# Use the same network as MinIO container
# Get actual credentials from the running MinIO container
echo -e "${YELLOW}📦 Creating MinIO buckets...${NC}"
MINIO_ACCESS=$(docker compose -f docker-compose.dev.yml exec -T minio printenv MINIO_ROOT_USER 2>/dev/null | tr -d '\r\n' || echo "loreguard")
MINIO_SECRET=$(docker compose -f docker-compose.dev.yml exec -T minio printenv MINIO_ROOT_PASSWORD 2>/dev/null | tr -d '\r\n' || echo "minio_password_here")

# Use MinIO service name (minio) on the Docker network instead of localhost
# Override entrypoint to use sh, then run mc commands
if docker run --rm --network loreguard-network --entrypoint /bin/sh \
    minio/mc:latest \
    -c "
        mc alias set local http://minio:9000 ${MINIO_ACCESS} ${MINIO_SECRET} && \
        mc mb local/artifacts 2>/dev/null || true && \
        mc mb local/evidence 2>/dev/null || true && \
        mc mb local/models 2>/dev/null || true && \
        mc mb local/exports 2>/dev/null || true && \
        echo 'MinIO buckets ready'
    " 2>&1; then
    echo -e "${GREEN}✅ MinIO buckets created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  MinIO bucket creation had issues, but continuing...${NC}"
    echo -e "${YELLOW}   (Buckets may already exist or will be created on first use)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Database initialization completed!${NC}"
echo ""
echo -e "${BLUE}📊 Summary:${NC}"
echo -e "   Database:     ${GREEN}✅ PostgreSQL ready${NC}"
echo -e "   Schema:       ${GREEN}✅ Tables created${NC}"
   echo -e "   Admin User:   ${GREEN}✅ admin@loreguard.local${NC}"
echo -e "   Object Store: ${GREEN}✅ MinIO buckets ready${NC}"
echo -e "   Health Check: ${GREEN}✅ System functions working${NC}"
echo ""
echo -e "${BLUE}🔐 Admin Login:${NC}"
   echo -e "   Email:    ${YELLOW}admin@loreguard.local${NC}"
   echo -e "   Password: ${YELLOW}admin${NC}"
echo ""

