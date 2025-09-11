#!/bin/bash

# LoreGuard Sample Data Loading Script
# Loads realistic sample data for development and testing

set -e  # Exit on any error

echo "📊 LoreGuard Sample Data Loading"
echo "==============================="
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
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please run from the LoreGuard root directory"
    exit 1
fi

echo -e "${BLUE}📋 Preparing sample data...${NC}"

# Create sample data SQL script
cat > /tmp/load-sample-data.sql << 'EOF'
-- LoreGuard Sample Data Loading Script

-- Clear existing sample data (keep admin users)
DELETE FROM library_items;
DELETE FROM evaluations;
DELETE FROM clarifications;
DELETE FROM document_metadata;
DELETE FROM artifacts;
DELETE FROM jobs;
DELETE FROM rubrics;
DELETE FROM sources WHERE name LIKE '%Sample%' OR name LIKE '%Test%';

-- Insert sample sources
INSERT INTO sources (id, name, type, config, schedule, status, tags, created_at) VALUES
    (
        uuid_generate_v4(),
        'NATO Strategic Communications Centre',
        'rss',
        '{"url": "https://stratcomcoe.org/feed", "user_agent": "LoreGuard/1.0", "politeness_delay": 2.0}',
        '0 */4 * * *',
        'active',
        '["nato", "strategic", "communications", "europe"]',
        NOW() - INTERVAL '7 days'
    ),
    (
        uuid_generate_v4(),
        'RAND Corporation Publications',
        'rss',
        '{"url": "https://www.rand.org/pubs.xml", "user_agent": "LoreGuard/1.0", "politeness_delay": 3.0}',
        '0 */6 * * *',
        'active',
        '["rand", "policy", "research", "defense"]',
        NOW() - INTERVAL '5 days'
    ),
    (
        uuid_generate_v4(),
        'Center for Strategic and International Studies',
        'web',
        '{"base_url": "https://www.csis.org", "selectors": [".post-title", ".post-content"], "max_depth": 2}',
        '0 */8 * * *',
        'active',
        '["csis", "international", "security", "policy"]',
        NOW() - INTERVAL '3 days'
    ),
    (
        uuid_generate_v4(),
        'Defense News',
        'rss',
        '{"url": "https://www.defensenews.com/rss/", "user_agent": "LoreGuard/1.0", "politeness_delay": 1.5}',
        '0 */2 * * *',
        'active',
        '["defense", "news", "military", "technology"]',
        NOW() - INTERVAL '1 day'
    ),
    (
        uuid_generate_v4(),
        'Sample Paused Source',
        'api',
        '{"endpoint": "https://api.example.com/documents", "auth_type": "bearer"}',
        '0 0 * * *',
        'paused',
        '["sample", "test", "api"]',
        NOW() - INTERVAL '10 days'
    );

-- Get source IDs for artifacts
WITH source_ids AS (
    SELECT id, name FROM sources 
    WHERE name IN (
        'NATO Strategic Communications Centre',
        'RAND Corporation Publications', 
        'Center for Strategic and International Studies',
        'Defense News'
    )
)

-- Insert sample artifacts with realistic content
INSERT INTO artifacts (id, source_id, uri, content_hash, mime_type, version, created_at)
SELECT 
    uuid_generate_v4(),
    s.id,
    uri,
    content_hash,
    mime_type,
    1,
    created_at
FROM source_ids s
CROSS JOIN (
    VALUES 
        ('https://stratcomcoe.org/publications/nato-strategic-assessment-2024', 'a1b2c3d4e5f6', 'application/pdf', NOW() - INTERVAL '2 days'),
        ('https://stratcomcoe.org/publications/hybrid-threats-analysis', 'b2c3d4e5f6a1', 'text/html', NOW() - INTERVAL '1 day'),
        ('https://www.rand.org/pubs/research_reports/RR4234.html', 'c3d4e5f6a1b2', 'text/html', NOW() - INTERVAL '3 days'),
        ('https://www.rand.org/pubs/perspectives/PE350.html', 'd4e5f6a1b2c3', 'application/pdf', NOW() - INTERVAL '4 days'),
        ('https://www.csis.org/analysis/future-warfare-2030', 'e5f6a1b2c3d4', 'text/html', NOW() - INTERVAL '1 day'),
        ('https://www.csis.org/analysis/cyber-deterrence-strategies', 'f6a1b2c3d4e5', 'text/html', NOW() - INTERVAL '2 days'),
        ('https://www.defensenews.com/digital-show-dailies/modern-day-marine/2024/09/10/ai-integration-military-operations/', '123456789abc', 'text/html', NOW() - INTERVAL '6 hours'),
        ('https://www.defensenews.com/naval/2024/09/09/next-gen-naval-systems-development/', '234567890bcd', 'text/html', NOW() - INTERVAL '12 hours')
) AS sample_data(uri, content_hash, mime_type, created_at)
WHERE s.name = CASE 
    WHEN sample_data.uri LIKE '%stratcomcoe%' THEN 'NATO Strategic Communications Centre'
    WHEN sample_data.uri LIKE '%rand%' THEN 'RAND Corporation Publications'
    WHEN sample_data.uri LIKE '%csis%' THEN 'Center for Strategic and International Studies'
    WHEN sample_data.uri LIKE '%defensenews%' THEN 'Defense News'
END;

-- Insert document metadata for artifacts
WITH artifact_data AS (
    SELECT 
        a.id as artifact_id,
        a.uri,
        a.created_at
    FROM artifacts a
    WHERE a.content_hash IN ('a1b2c3d4e5f6', 'b2c3d4e5f6a1', 'c3d4e5f6a1b2', 'd4e5f6a1b2c3', 'e5f6a1b2c3d4', 'f6a1b2c3d4e5', '123456789abc', '234567890bcd')
)
INSERT INTO document_metadata (id, artifact_id, title, authors, organization, pub_date, topics, geo_location, language)
SELECT 
    uuid_generate_v4(),
    a.artifact_id,
    title,
    authors,
    organization,
    a.created_at,
    topics,
    geo_location,
    'en'
FROM artifact_data a
CROSS JOIN (
    VALUES 
        ('NATO Strategic Assessment: Eastern European Defense Posture 2024', 'NATO Strategic Communications Centre', 'NATO', '["defense", "strategy", "eastern europe", "security"]', 'Europe'),
        ('Hybrid Threats in the Information Domain: Analysis and Countermeasures', 'NATO StratCom COE Research Team', 'NATO', '["hybrid warfare", "information", "disinformation", "countermeasures"]', 'Global'),
        ('Future Military Capabilities: Technology Integration and Strategic Implications', 'RAND Defense Research Division', 'RAND Corporation', '["military technology", "capabilities", "strategy", "innovation"]', 'United States'),
        ('Perspectives on Modern Deterrence Theory and Practice', 'Dr. Sarah Mitchell, Dr. James Chen', 'RAND Corporation', '["deterrence", "strategy", "defense policy", "international relations"]', 'Global'),
        ('The Future of Warfare in 2030: Emerging Technologies and Strategic Challenges', 'CSIS Defense and Security Department', 'Center for Strategic and International Studies', '["future warfare", "emerging technology", "strategy", "defense"]', 'Global'),
        ('Cyber Deterrence Strategies for Nation-State Actors', 'Dr. Michael Rodriguez, Dr. Lisa Wang', 'Center for Strategic and International Studies', '["cyber security", "deterrence", "nation state", "cyber warfare"]', 'Global'),
        ('AI Integration in Military Operations: Current Status and Future Prospects', 'Defense Technology Correspondent', 'Defense News', '["artificial intelligence", "military", "technology", "operations"]', 'United States'),
        ('Next-Generation Naval Systems: Development and Deployment Strategies', 'Naval Affairs Reporter', 'Defense News', '["naval systems", "technology", "development", "maritime"]', 'Global')
) AS metadata(title, authors, organization, topics, geo_location)
WHERE a.uri LIKE '%' || CASE 
    WHEN metadata.title LIKE '%NATO Strategic Assessment%' THEN 'nato-strategic-assessment'
    WHEN metadata.title LIKE '%Hybrid Threats%' THEN 'hybrid-threats-analysis'
    WHEN metadata.title LIKE '%Future Military Capabilities%' THEN 'RR4234'
    WHEN metadata.title LIKE '%Perspectives on Modern%' THEN 'PE350'
    WHEN metadata.title LIKE '%Future of Warfare%' THEN 'future-warfare-2030'
    WHEN metadata.title LIKE '%Cyber Deterrence%' THEN 'cyber-deterrence-strategies'
    WHEN metadata.title LIKE '%AI Integration%' THEN 'ai-integration-military'
    WHEN metadata.title LIKE '%Next-Generation Naval%' THEN 'next-gen-naval-systems'
END || '%';

-- Insert sample rubric
INSERT INTO rubrics (id, version, name, description, categories, thresholds, is_active, created_at) VALUES (
    uuid_generate_v4(),
    'v2.1',
    'Military Wargaming Relevance Assessment',
    'Evaluates documents for relevance to military wargaming scenarios, strategic planning, and operational analysis',
    '[
        {
            "id": "credibility",
            "name": "Source Credibility",
            "weight": 0.25,
            "description": "Reliability and trustworthiness of the source and authors",
            "scale": {"min": 0, "max": 5},
            "criteria": [
                "Author expertise and credentials",
                "Institutional reputation",
                "Peer review and citation history",
                "Bias and objectivity assessment"
            ]
        },
        {
            "id": "relevance", 
            "name": "Military Relevance",
            "weight": 0.30,
            "description": "Direct applicability to military operations, strategy, and wargaming",
            "scale": {"min": 0, "max": 5},
            "criteria": [
                "Military operational relevance",
                "Strategic planning applicability", 
                "Wargaming scenario utility",
                "Tactical insights and lessons"
            ]
        },
        {
            "id": "timeliness",
            "name": "Timeliness and Currency", 
            "weight": 0.20,
            "description": "Recency and ongoing relevance of the information",
            "scale": {"min": 0, "max": 5},
            "criteria": [
                "Publication date relevance",
                "Current event applicability",
                "Future trend indicators",
                "Historical context value"
            ]
        },
        {
            "id": "novelty",
            "name": "Information Novelty",
            "weight": 0.15,
            "description": "Uniqueness and new insights provided",
            "scale": {"min": 0, "max": 5},
            "criteria": [
                "New information or perspectives",
                "Unique analytical insights",
                "Previously unreported facts",
                "Novel methodological approaches"
            ]
        },
        {
            "id": "coverage",
            "name": "Geographic/Thematic Coverage",
            "weight": 0.10,
            "description": "Breadth and depth of coverage for wargaming scenarios",
            "scale": {"min": 0, "max": 5},
            "criteria": [
                "Geographic scope relevance",
                "Thematic depth and breadth",
                "Multi-domain considerations",
                "Cross-cultural perspectives"
            ]
        }
    ]',
    '{"signal_min": 3.5, "review_min": 2.5, "noise_max": 2.4}',
    true,
    NOW() - INTERVAL '30 days'
);

-- Insert sample evaluations
WITH eval_data AS (
    SELECT 
        a.id as artifact_id,
        r.id as rubric_id,
        r.version as rubric_version,
        dm.title
    FROM artifacts a
    JOIN document_metadata dm ON a.id = dm.artifact_id
    CROSS JOIN rubrics r
    WHERE r.version = 'v2.1'
    LIMIT 8
)
INSERT INTO evaluations (id, artifact_id, rubric_id, rubric_version, scores, label, confidence, total_score, model_id, created_at)
SELECT 
    uuid_generate_v4(),
    ed.artifact_id,
    ed.rubric_id,
    ed.rubric_version,
    scores,
    label,
    confidence,
    total_score,
    'gpt-4-0613',
    NOW() - INTERVAL '1 day'
FROM eval_data ed
CROSS JOIN (
    VALUES 
        ('{"credibility": 4.2, "relevance": 4.5, "timeliness": 4.0, "novelty": 3.8, "coverage": 4.1}', 'Signal', 0.92, 4.18),
        ('{"credibility": 3.8, "relevance": 4.2, "timeliness": 3.5, "novelty": 3.2, "coverage": 3.9}', 'Signal', 0.87, 3.76),
        ('{"credibility": 4.5, "relevance": 3.9, "timeliness": 3.2, "novelty": 4.1, "coverage": 3.7}', 'Signal', 0.89, 3.84),
        ('{"credibility": 3.2, "relevance": 3.8, "timeliness": 4.2, "novelty": 2.9, "coverage": 3.4}', 'Signal', 0.81, 3.58),
        ('{"credibility": 3.9, "relevance": 3.1, "timeliness": 2.8, "novelty": 3.5, "coverage": 3.2}', 'Review', 0.75, 3.21),
        ('{"credibility": 2.8, "relevance": 2.9, "timeliness": 3.1, "novelty": 2.5, "coverage": 2.7}', 'Review', 0.68, 2.78),
        ('{"credibility": 4.1, "relevance": 4.3, "timeliness": 4.5, "novelty": 3.7, "coverage": 4.0}', 'Signal', 0.94, 4.15),
        ('{"credibility": 3.5, "relevance": 4.0, "timeliness": 4.2, "novelty": 3.3, "coverage": 3.8}', 'Signal', 0.88, 3.78)
) AS eval_scores(scores, label, confidence, total_score)
LIMIT 8;

-- Insert sample jobs
INSERT INTO jobs (id, job_type, status, source_id, config, progress, started_at, completed_at, error_message, created_at) 
SELECT 
    uuid_generate_v4(),
    job_type,
    status,
    s.id,
    config,
    progress,
    started_at,
    completed_at,
    error_message,
    created_at
FROM sources s
CROSS JOIN (
    VALUES 
        ('crawl', 'completed', '{"max_pages": 50, "politeness_delay": 2.0}', 100, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', NULL, NOW() - INTERVAL '3 hours'),
        ('crawl', 'running', '{"max_pages": 100, "politeness_delay": 1.5}', 67, NOW() - INTERVAL '30 minutes', NULL, NULL, NOW() - INTERVAL '45 minutes'),
        ('evaluate', 'completed', '{"rubric_version": "v2.1", "batch_size": 10}', 100, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '30 minutes', NULL, NOW() - INTERVAL '2 hours'),
        ('crawl', 'failed', '{"max_pages": 25, "politeness_delay": 3.0}', 0, NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours 30 minutes', 'Connection timeout after 30 seconds', NOW() - INTERVAL '5 hours')
) AS job_data(job_type, status, config, progress, started_at, completed_at, error_message, created_at)
WHERE s.status = 'active'
LIMIT 12;

-- Insert sample library items (Signal documents)
WITH signal_artifacts AS (
    SELECT 
        a.id as artifact_id,
        e.id as evaluation_id,
        dm.title,
        dm.organization,
        e.confidence,
        e.total_score
    FROM artifacts a
    JOIN document_metadata dm ON a.id = dm.artifact_id
    JOIN evaluations e ON a.id = e.artifact_id
    WHERE e.label = 'Signal'
    ORDER BY e.total_score DESC
    LIMIT 5
)
INSERT INTO library_items (id, artifact_id, evaluation_id, priority, tags, curator_notes, distribution_status, created_at)
SELECT 
    uuid_generate_v4(),
    sa.artifact_id,
    sa.evaluation_id,
    CASE 
        WHEN sa.total_score > 4.0 THEN 'high'
        WHEN sa.total_score > 3.7 THEN 'medium'
        ELSE 'normal'
    END,
    CASE sa.organization
        WHEN 'NATO' THEN '["nato", "alliance", "strategic"]'
        WHEN 'RAND Corporation' THEN '["research", "policy", "analysis"]'
        WHEN 'Center for Strategic and International Studies' THEN '["csis", "international", "security"]'
        ELSE '["defense", "military", "news"]'
    END,
    'Automatically curated based on high evaluation score (' || sa.total_score || ') and confidence (' || sa.confidence || ')',
    'approved',
    NOW() - INTERVAL '12 hours'
FROM signal_artifacts sa;

-- Update statistics
INSERT INTO app_settings (key, value, description) VALUES
    ('last_sample_data_load', to_jsonb(NOW()), 'Timestamp of last sample data loading')
ON CONFLICT (key) DO UPDATE SET 
    value = EXCLUDED.value,
    updated_at = NOW();

-- Log the data loading
INSERT INTO audit_logs (action, resource_type, details) VALUES (
    'sample_data_loaded',
    'system',
    jsonb_build_object(
        'timestamp', NOW(),
        'sources_loaded', (SELECT COUNT(*) FROM sources WHERE created_at > NOW() - INTERVAL '1 hour'),
        'artifacts_loaded', (SELECT COUNT(*) FROM artifacts WHERE created_at > NOW() - INTERVAL '1 hour'),
        'evaluations_loaded', (SELECT COUNT(*) FROM evaluations WHERE created_at > NOW() - INTERVAL '1 hour'),
        'library_items_loaded', (SELECT COUNT(*) FROM library_items WHERE created_at > NOW() - INTERVAL '1 hour')
    )
);

-- Return summary
SELECT 
    (SELECT COUNT(*) FROM sources) as total_sources,
    (SELECT COUNT(*) FROM artifacts) as total_artifacts,
    (SELECT COUNT(*) FROM document_metadata) as total_metadata,
    (SELECT COUNT(*) FROM evaluations) as total_evaluations,
    (SELECT COUNT(*) FROM library_items) as total_library_items,
    (SELECT COUNT(*) FROM jobs) as total_jobs,
    'Sample data loaded successfully' as status;
EOF

echo -e "${YELLOW}📝 Loading sample data into database...${NC}"

# Execute the SQL script
docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -f - < /tmp/load-sample-data.sql

# Clean up temporary file
rm /tmp/load-sample-data.sql

echo ""
echo -e "${BLUE}🔍 Verifying sample data...${NC}"

# Get data counts
DATA_SUMMARY=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U loreguard -d loreguard -t -c "
SELECT 
    (SELECT COUNT(*) FROM sources) as sources,
    (SELECT COUNT(*) FROM artifacts) as artifacts,
    (SELECT COUNT(*) FROM document_metadata) as metadata,
    (SELECT COUNT(*) FROM evaluations) as evaluations,
    (SELECT COUNT(*) FROM library_items) as library_items,
    (SELECT COUNT(*) FROM jobs) as jobs;
" | tr -d ' ' | grep -v '^$')

if [[ ! -z "$DATA_SUMMARY" ]]; then
    echo -e "${GREEN}✅ Sample data loaded successfully${NC}"
    
    # Parse and display counts
    IFS='|' read -r sources artifacts metadata evaluations library_items jobs <<< "$DATA_SUMMARY"
    
    echo -e "${BLUE}📊 Data Summary:${NC}"
    echo -e "   Sources:       ${YELLOW}$sources${NC} (including NATO, RAND, CSIS, Defense News)"
    echo -e "   Artifacts:     ${YELLOW}$artifacts${NC} (sample documents and publications)"
    echo -e "   Metadata:      ${YELLOW}$metadata${NC} (titles, authors, topics, locations)"
    echo -e "   Evaluations:   ${YELLOW}$evaluations${NC} (LLM assessment results)"
    echo -e "   Library Items: ${YELLOW}$library_items${NC} (curated Signal documents)"
    echo -e "   Jobs:          ${YELLOW}$jobs${NC} (crawling and processing jobs)"
else
    echo -e "${RED}❌ Failed to verify sample data${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🎯 Sample Data Features:${NC}"
echo -e "   ${GREEN}✅ Realistic Sources${NC}: NATO, RAND Corporation, CSIS, Defense News"
echo -e "   ${GREEN}✅ Document Variety${NC}: PDFs, HTML articles, research reports"
echo -e "   ${GREEN}✅ Rich Metadata${NC}: Titles, authors, organizations, topics, locations"
echo -e "   ${GREEN}✅ LLM Evaluations${NC}: Confidence scores, Signal/Review/Noise labels"
echo -e "   ${GREEN}✅ Curated Library${NC}: High-value Signal documents ready for distribution"
echo -e "   ${GREEN}✅ Job History${NC}: Completed, running, and failed processing jobs"
echo -e "   ${GREEN}✅ Geographic Scope${NC}: Global, Europe, United States coverage"
echo -e "   ${GREEN}✅ Topic Diversity${NC}: Defense, strategy, technology, cyber security"

echo ""
echo -e "${GREEN}🎉 Sample data loading completed!${NC}"
echo ""
echo -e "${BLUE}🌐 Test the data:${NC}"
echo -e "   View sources:    ${YELLOW}curl http://localhost:8000/api/v1/test/sources-simple${NC}"
echo -e "   View artifacts:  ${YELLOW}curl http://localhost:8000/api/v1/test/artifacts-simple${NC}"
echo -e "   Frontend UI:     ${YELLOW}http://localhost:5173${NC}"
echo ""

