-- LoreGuard Database Initialization Script
-- This script sets up the basic database structure for development

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create basic tables based on the data model from architecture docs

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    schedule VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    last_run TIMESTAMP WITH TIME ZONE,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Artifacts table
CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id),
    uri TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    mime_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    normalized_ref TEXT
);

-- Metadata table
CREATE TABLE IF NOT EXISTS metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID REFERENCES artifacts(id),
    title TEXT,
    authors TEXT[],
    organization TEXT,
    pub_date TIMESTAMP WITH TIME ZONE,
    topics TEXT[],
    geo_location TEXT,
    language VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Clarifications table
CREATE TABLE IF NOT EXISTS clarifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID REFERENCES artifacts(id),
    signals JSONB NOT NULL DEFAULT '{}',
    evidence_ref TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rubrics table
CREATE TABLE IF NOT EXISTS rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) UNIQUE NOT NULL,
    categories JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    prompts JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID REFERENCES artifacts(id),
    rubric_version VARCHAR(50) REFERENCES rubrics(version),
    model_id VARCHAR(100),
    scores JSONB NOT NULL,
    label VARCHAR(50),
    confidence DECIMAL(3,2),
    prompt_ref TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    timeline JSONB DEFAULT '[]',
    retries INTEGER DEFAULT 0,
    error TEXT,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Library items table
CREATE TABLE IF NOT EXISTS library_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID REFERENCES artifacts(id),
    snapshot_id UUID,
    tags TEXT[],
    is_signal BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_artifacts_source_id ON artifacts(source_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_content_hash ON artifacts(content_hash);
CREATE INDEX IF NOT EXISTS idx_metadata_artifact_id ON metadata(artifact_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_artifact_id ON evaluations(artifact_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_library_items_artifact_id ON library_items(artifact_id);
CREATE INDEX IF NOT EXISTS idx_library_items_is_signal ON library_items(is_signal);

-- Insert a default rubric
INSERT INTO rubrics (version, categories, thresholds, prompts, is_active) VALUES (
    'v0.1',
    '{
        "credibility": {"weight": 0.30, "guidance": "Evaluate author, org, venue, and corroboration strength."},
        "relevance": {"weight": 0.30, "guidance": "Assess alignment with specified scenarios and objectives."},
        "rigor": {"weight": 0.15, "guidance": "Assess methodology transparency and data quality."},
        "timeliness": {"weight": 0.10, "guidance": "Evaluate publication recency and update frequency."},
        "novelty": {"weight": 0.10, "guidance": "Assess originality and unique insights."},
        "coverage": {"weight": 0.05, "guidance": "Evaluate completeness and clarity."}
    }',
    '{
        "signal_min": 3.8,
        "review_min": 2.8,
        "noise_max": 2.8
    }',
    '{
        "evaluation": "prompt_ref_eval_v0",
        "metadata": "prompt_ref_meta_v0",
        "clarification": "prompt_ref_clarify_v0"
    }',
    true
) ON CONFLICT (version) DO NOTHING;

