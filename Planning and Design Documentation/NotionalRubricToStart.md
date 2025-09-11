## Notional Rubric (Initial Draft)

This rubric is configurable via the UI and versioned for evaluating facts and perspectives from the Information Space. Scores map to labels using thresholds. Scales are 0–5 per category, aggregated by weighted average.

### Categories and Guidance
- Credibility (weight 0.30)
  - Author identity, expertise, affiliation, and venue standing
  - Evidence of peer review or institutional rigor
- Relevance (weight 0.30)
  - Alignment with AF wargaming objectives, scenarios, and time horizon
  - Value for understanding diverse perspectives and roleplay scenarios
- Rigor & Methodology (weight 0.15)
  - Soundness of analysis, transparency of methods, cited data
- Timeliness (weight 0.10)
  - Publication date, recency to current events, update cadence
- Novelty & Insight (weight 0.10)
  - New findings, non‑obvious insights, unique perspectives, alternative viewpoints
- Coverage & Clarity (weight 0.05)
  - Completeness, structure, clarity, and replicability

### Thresholds (Initial)
- Signal: total_score ≥ 3.8 and Credibility ≥ 3.5 and Relevance ≥ 3.8
- Requires Human Review: 2.8 ≤ total_score < 3.8 or low confidence
- Noise: total_score < 2.8

### Output Schema (Conceptual)
```yaml
version: "v0.1"
categories:
  credibility:
    weight: 0.30
    guidance: |
      Evaluate author, org, venue, and corroboration strength.
    subcriteria:
      - author_expertise
      - organization_reputation
      - venue_rigor
      - citation_corroboration
  relevance:
    weight: 0.30
    guidance: |
      Assess alignment with specified scenarios and objectives.
    subcriteria:
      - scenario_alignment
      - doctrinal_relevance
      - operational_timeline
  rigor:
    weight: 0.15
    guidance: Assess methodology transparency and data quality.
    subcriteria: [method_transparency, data_quality, reasoning_soundness]
  timeliness:
    weight: 0.10
    subcriteria: [publication_recency, update_frequency]
  novelty:
    weight: 0.10
    subcriteria: [originality, unique_dataset]
  coverage:
    weight: 0.05
    subcriteria: [completeness, clarity]
thresholds:
  signal_min: 3.8
  review_min: 2.8
  noise_max: 2.8
prompts:
  evaluation: prompt_ref_eval_v0
  metadata: prompt_ref_meta_v0
  clarification: prompt_ref_clarify_v0
```

### Reviewer Policy (Initial)
- Auto‑promote to Library when label=Signal AND confidence ≥ 0.7
- Queue to Human Review when label=Review OR confidence < 0.7
- Allow Analyst override with comment; log to audit

### Implementation Tasks (Development Phase)
- [ ] **Stakeholder Validation**: Present rubric to AFWI for weight validation with exemplar artifacts
- [ ] **Domain Subcriteria**: Develop topic-specific subcriteria through subject matter expert input
- [ ] **Confidence Policy**: Implement ensemble voting + statistical confidence computation
- [ ] **Drift Monitoring**: Deploy automated calibration workflow with statistical drift detection

### Technical Implementation (RESEARCH COMPLETED)
- [x] **Rubric Schema**: YAML-based configuration with Pydantic validation
- [x] **UI Editor**: React-based rubric management interface with real-time preview
- [x] **Versioning**: Git-like versioning with backward compatibility
- [x] **Retraining Pipeline**: Temporal workflows for automated recalibration


