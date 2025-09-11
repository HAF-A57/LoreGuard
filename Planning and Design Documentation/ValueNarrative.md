## LoreGuard: Rapid, Credible Facts and Perspectives Harvesting for Wargaming

### Audience
Headquarters Air Force Wargaming (HAF/WG) and Air Force Wargaming Institute (AFWI) leadership, directors, operations, and analyst teams.

### The Problem We Must Solve
Modern wargaming requires continuous awareness of fast‑moving developments across diplomacy, economics, information, and military domains. The relevant knowledge is distributed across thousands of global sources: ministries, DoD/Service doctrine, think tanks, journals, standards bodies, industry reports, academic archives, and credible public media. Human collection and triage at this scale is impractical. Valuable signals are buried in overwhelming noise; by the time a curated set is produced manually, it is often stale.

### What LoreGuard Is
LoreGuard is a companion system to MAGE that continuously discovers, retrieves, evaluates, and curates open‑source artifacts (documents, pages, datasets, media) at global scale to capture diverse facts and perspectives from the Information Space. It uses an LLM‑powered evaluation rubric—tailored to Air Force wargaming objectives—to grade artifacts into Signal, Noise, or Requires Human Review. Curated results flow into our Library and are immediately usable in MAGE for analysis, scenario design, and roleplay of various nation-states and organizations.

### Why It Matters (Value Proposition)
- **Speed to Insight**: Automates collection and first‑pass evaluation so analysts focus on interpreting diverse perspectives, not finding them.
- **Credibility at Scale**: Enforces a transparent rubric tied to AF wargaming priorities (credibility, relevance, rigor, timeliness), with auditable scoring and provenance.
- **Continuously Current**: Refreshes sources on schedule or on demand; detects and evaluates only net‑new artifacts.
- **Interoperable with MAGE**: Shares provider configurations, security, and UI patterns; curated artifacts flow seamlessly into wargame workflows.
- **Governed and Explainable**: Stores the rubric, prompts, model versions, and evidence used to grade each artifact so decisions can be reviewed and reproduced.

### Who Benefits
- **Wargame Directors**: Faster preparation cycles; higher confidence in the source base.
- **Analysts/Red/Blue Cells**: Less time on collection; more time on synthesis and COA development.
- **Leadership**: Clear traceability from artifacts to judgments used in games and post‑game analysis.

### How It Works (At a Glance)
1. Configure sources (sites, feeds, APIs) and schedules.
2. Retrieve and normalize artifacts (HTML/PDF/Docx/Media), including OCR when needed.
3. Extract metadata; run targeted “clarification” web checks (e.g., author reputation, organization credibility).
4. Apply the LLM rubric to score artifacts; label as Signal, Noise, or Requires Human Review.
5. Store everything with provenance; promote Signal to the Library used by MAGE.
6. Refresh on demand; only new or changed artifacts are re‑evaluated.

### Outcomes We Expect
- 10–100× increase in screened artifact volume with stable analyst headcount.
- Time‑to‑curated‑set reduced from weeks to hours.
- Transparent, repeatable grading aligned to AF wargaming requirements.
- Rapid re‑grading when priorities or rubrics change.

### Risks and How We Mitigate
- **Credibility drift**: Maintain rubric versioning and model‑prompt audit logs; periodic calibration against human gold sets.
- **Model bias or failure modes**: Ensemble checks, confidence thresholds, and human‑review queues for ambiguous cases.
- **Adversarial content/prompt injection**: Strict extraction, sandboxed crawlers, content sanitization, and evaluation guardrails.
- **Over‑collection and storage bloat**: Deduplication via hashing, content normalization, lifecycle policies, tiered storage.
- **Compliance/security**: RBAC, encryption at rest and in transit, source allowlists, and governance reviews.
- **On-premises deployment**: Full air-gapped capability with no cloud dependencies for classified environments.

### Relationship to MAGE
LoreGuard mirrors MAGE's UI patterns (three‑pane layout, integrated chatbot) and shares LLM provider configurations via the OpenAI API standard. Curated artifacts, metadata, and vectors are accessible to MAGE for retrieval‑augmented analysis, scenario development, and roleplay of diverse global perspectives and viewpoints.

### Call to Action
Pilot LoreGuard on a focused topic set (e.g., hypersonics and logistics) to validate throughput, grading accuracy, and analyst satisfaction. Iterate the rubric and pipeline before broad rollout.

### Initial KPIs
- Throughput: artifacts retrieved and graded per day
- Precision/recall against human gold set
- Time from source change to curated artifact availability
- Share of artifacts requiring human review (target band)

### Research Tasks (COMPLETED)
- [x] **Crawler Framework**: Scrapy + Playwright hybrid selected for anti-bot evasion and politeness
- [x] **Document Processing**: unstructured.io + GROBID + Tesseract tiered approach finalized
- [x] **Vector Database**: pgvector → Weaviate scaling path established
- [x] **Workflow Orchestration**: Temporal + Celery hybrid architecture defined
- [x] **UI Components**: shadcn/ui + TanStack Table with virtualization confirmed
- [x] **LLM Validation**: Pydantic v2 + function calling approach validated
- [x] **Storage Solutions**: MinIO on-premises object storage selected
- [x] **Signal Distribution**: Nextcloud Enterprise + SharePoint backup strategy
- [x] **Translation**: LibreTranslate + NLLB + Tower LLM ensemble approach
- [x] **Evidence Storage**: WARC format with structured extraction confirmed
- [x] **Calibration**: Stratified sampling + active learning methodology established

### Implementation Ready
All major technology decisions completed. Development team can begin implementation with complete technology stack and architectural guidance. See `FinalTechnologyRoadmap.md` for comprehensive implementation details.


