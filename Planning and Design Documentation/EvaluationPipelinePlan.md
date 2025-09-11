## LoreGuard Evaluation Pipeline Plan

### Audience
Applied ML/LLM engineers and analysts responsible for rubric design, calibration, and evaluation quality.

### Objectives
- Convert heterogeneous artifacts into structured, evaluable representations capturing facts and perspectives
- Extract metadata and gather clarification evidence about viewpoints and narratives
- Apply a versioned rubric via LLMs to score artifacts and label them based on perspective value
- Calibrate and monitor performance against human gold sets for diverse viewpoint assessment
- Enable re‑grading when rubrics or models change to adapt perspective evaluation criteria

### Pipeline Stages
1) Ingest
- Inputs: source configs, discovered URIs
- Outputs: `Artifact(uri, content_hash, mime, fetched_at)`; raw blob stored

2) Normalize
- Convert to text+structure (HTML→text, PDF OCR, docx parsing)
- Extract basic metadata: title, authors, org, pub_date, language
- Emit `NormalizedArtifact(ref, text, tokens, metadata)`

3) Clarification
- Targeted web queries to enrich credibility and context: author reputation, organizational affiliation, prior citations, publication venue standing, corroboration hits, perspective bias indicators
- Evidence stored with references/links and timestamps for viewpoint validation
- Emit `ClarificationSignals{author_reputation, org_type, citations, venue_rank, corroboration_count, recency, geo, perspective_bias}`

4) Evaluation
- Inputs: `NormalizedArtifact`, `ClarificationSignals`, `Rubric(version)`
- LLM prompts with JSON schema enforce `scores{category: {subscores..., weight}}`, `label`, and `confidence`
- Ensemble/consensus: optional multi‑model or multi‑prompt voting; abstain when low confidence
- Outputs: `Evaluation(artifact_id, rubric_version, scores, label, confidence, model_id, prompt_ref)`

5) Persist & Publish
- Store evaluation with provenance; compute vectors and hybrid search fields
- Promote `Signal` to Library; queue `Requires Human Review`
- Metrics/logs emitted per stage

### Rubric Design
- Versioned rubric with categories (e.g., Credibility, Relevance, Rigor, Timeliness, Novelty, Coverage)
- Each category has: weight, scoring guidance, failure conditions, scoring scale (0–5), and aggregation formula
- Thresholds map total score to labels: Signal/Noise/Review
- JSON schema for structured output; UI editor to modify weights, text, and thresholds

### Prompting Strategy
- System prompt: policy, safety, and role
- Task prompts per stage (metadata extraction, clarification queries, evaluation)
- Few‑shot exemplars tied to calibration sets
- Guardrails: maximum context, escaped inputs, citation verification checks

### Calibration & Monitoring
- Gold sets: human‑labeled artifacts across domains
- Procedures: periodic evaluation, drift detection, rubric/model A/B testing
- Metrics: precision/recall on Signal, inter‑rater agreement, abstain rate, average confidence
- Dashboards: per‑category score distributions; confusion matrices

### Regrading Mechanics
- Triggered by rubric version publish or model/prompt change
- Batch processing with backpressure controls
- Store deltas; reconcile Library label changes with audit log

### Failure Modes & Safeguards
- Low‑quality OCR → fallback engines, human queue
- Prompt injection → sanitize inputs, no tool execution in eval context
- Over‑scoring specific sources → per‑source normalization, cap weights, calibration alerts
- Rate limits → budget per job, backoff, retry with jitter

### Contracts (Schemas - conceptual)
- `Rubric` (JSON):
  - `version`: string
  - `categories`: array of { `id`, `weight`, `guidance`, `subcriteria`[] }
  - `thresholds`: { `signal_min`, `review_min`, `noise_max`}
  - `prompts`: { `metadata`, `clarification`, `evaluation` }
- `Evaluation` (JSON):
  - `artifact_id`, `rubric_version`, `model_id`, `prompt_ref`
  - `scores`: map `category_id` → { `score`, `subscores` }
  - `label`: enum
  - `confidence`: number 0–1
  - `evidence_refs`: array

### Research Tasks (ALL COMPLETED)
- [x] **JSON Schema Validation**: Pydantic v2 with OpenAI function calling integration
- [x] **Ensemble Strategy**: Multi-model voting with confidence-based abstention policy
- [x] **Calibration Workflow**: Streamlit interface + active learning + inter-rater reliability
- [x] **LLM Guardrails**: Function calling + JSON schema validation + input sanitization
- [x] **Multilingual Handling**: polyglot detection + LibreTranslate + NLLB/Tower LLM translation
- [x] **Bias Review Process**: Statistical drift detection + human calibration + audit logging

### Implementation Ready
Complete evaluation pipeline architecture defined with all validation, calibration, and quality assurance components specified.


