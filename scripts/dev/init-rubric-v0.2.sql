-- LoreGuard Enhanced Rubric v0.2
-- Refined for military wargaming with subcriteria and v1 prompt references

-- Insert enhanced rubric v0.2
INSERT INTO rubrics (id, version, categories, thresholds, prompts, is_active) VALUES (
    uuid_generate_v4(),
    'v0.2',
    '{
        "credibility": {
            "weight": 0.30,
            "guidance": "Evaluate author expertise, organizational reputation, publication venue standing, and corroboration strength. Critical for wargaming intelligence quality assurance.",
            "subcriteria": [
                "author_expertise: Military/policy credentials, publication history, institutional standing",
                "org_reputation: Think tank rankings, academic prestige, government authority, funding transparency",
                "venue_rigor: Peer review status, editorial standards, citation patterns, media credibility ratings",
                "corroboration: Cross-references from credible sources, fact-checking results, expert consensus"
            ],
            "scale": {"min": 0, "max": 5},
            "examples": {
                "5": "RAND report by recognized experts, extensive citations, peer-reviewed process",
                "3": "Think tank brief by credentialed analyst, standard editorial review, some citations",
                "1": "Blog post by unknown author, no citations, unverifiable claims"
            }
        },
        "relevance": {
            "weight": 0.30,
            "guidance": "Assess alignment with wargaming objectives, scenario utility, doctrinal relevance, and adversary perspective value. Highest priority for operational utility.",
            "subcriteria": [
                "wargaming_utility: Directly applicable to scenario development, COA analysis, or adversary modeling",
                "doctrinal_alignment: Relates to AF doctrine, strategy, operational concepts, or joint operations",
                "scenario_fit: Useful for specific wargaming contexts (great power competition, regional conflicts, technology impacts)",
                "perspective_value: Provides insight into how adversaries, partners, or populations think and act"
            ],
            "scale": {"min": 0, "max": 5},
            "examples": {
                "5": "Chinese military doctrine analysis directly applicable to Indo-Pacific scenarios",
                "3": "Regional security analysis with some wargaming applications",
                "1": "Generic topic with minimal connection to AF wargaming priorities"
            }
        },
        "rigor": {
            "weight": 0.15,
            "guidance": "Assess analytical methodology, data quality, reasoning soundness, and transparency. Ensures intelligence meets analytical standards.",
            "subcriteria": [
                "methodology: Clear analytical framework, logical reasoning, systematic approach",
                "evidence_quality: Primary sources cited, data provenance clear, claims supported with verifiable evidence",
                "transparency: Assumptions stated, limitations acknowledged, potential biases disclosed",
                "depth: Goes beyond surface observations to underlying dynamics, causes, and implications"
            ],
            "scale": {"min": 0, "max": 5},
            "examples": {
                "5": "Rigorous methodology, extensive primary sources, transparent assumptions, deep analysis",
                "3": "Standard analytical approach, adequate citations, some transparency, decent depth",
                "1": "Weak methodology, poor sourcing, opaque assumptions, superficial analysis"
            }
        },
        "timeliness": {
            "weight": 0.10,
            "guidance": "Evaluate publication recency, update frequency, and relevance to current conditions. Fast-moving topics (technology, current events) decay faster than strategic analysis.",
            "subcriteria": [
                "recency: Published within relevant timeframe (technology: <6mo, strategy: <2yr)",
                "currency: Reflects current conditions, recent developments, latest available information",
                "update_freq: Source demonstrates ongoing monitoring vs. one-off snapshot",
                "temporal_decay: Consider how quickly topic ages (cyber > weapons > doctrine > theory)"
            ],
            "scale": {"min": 0, "max": 5},
            "examples": {
                "5": "Recent analysis of fast-moving topic with latest data",
                "3": "Published within reasonable timeframe for topic, still relevant",
                "1": "Outdated analysis, superseded by events, stale information"
            }
        },
        "novelty": {
            "weight": 0.10,
            "guidance": "Assess originality, unique insights, alternative perspectives, and information advantage. Values non-obvious viewpoints and new findings.",
            "subcriteria": [
                "originality: New findings, fresh analysis, original research vs. synthesis of known information",
                "unique_perspective: Challenges conventional wisdom, offers alternative interpretation, provides insider view",
                "info_advantage: Provides data or perspective not widely available in open sources",
                "intellectual_value: Advances understanding beyond common knowledge, offers actionable insights"
            ],
            "scale": {"min": 0, "max": 5},
            "examples": {
                "5": "Original research with unique data or insider perspective providing new insights",
                "3": "Fresh perspective on known topic or useful synthesis of information",
                "1": "Rehash of commonly known information with no new value"
            }
        },
        "coverage": {
            "weight": 0.05,
            "guidance": "Evaluate completeness, clarity, structure, and usability for wargaming preparation. Well-organized analysis is more actionable.",
            "subcriteria": [
                "completeness: Addresses key aspects of topic comprehensively, not just selective focus",
                "clarity: Well-structured, clearly written, accessible to military/policy audience",
                "usability: Can be readily applied to wargaming preparation without extensive interpretation",
                "structure: Logical organization, good use of headings, tables, or visualizations"
            ],
            "scale": {"min": 0, "max": 5},
            "examples": {
                "5": "Comprehensive coverage, excellent structure, highly accessible and actionable",
                "3": "Adequate coverage, reasonable clarity, usable with some effort",
                "1": "Incomplete coverage, poor organization, difficult to extract value"
            }
        }
    }',
    '{
        "signal_min": 3.8,
        "review_min": 2.8,
        "noise_max": 2.8,
        "notes": "Signal (>=3.8): Auto-promote to Library for wargaming use. Review (2.8-3.8): Queue for human analyst evaluation. Noise (<2.8): Filter out as low-value."
    }',
    '{
        "evaluation": "prompt_ref_eval_v1",
        "metadata": "prompt_ref_meta_v1",
        "clarification": "prompt_ref_clarify_v1",
        "notes": "Uses enhanced v1 prompts with explicit wargaming guidance, few-shot examples, and edge case handling"
    }',
    false
) ON CONFLICT (version) DO UPDATE SET
    categories = EXCLUDED.categories,
    thresholds = EXCLUDED.thresholds,
    prompts = EXCLUDED.prompts,
    is_active = EXCLUDED.is_active;

