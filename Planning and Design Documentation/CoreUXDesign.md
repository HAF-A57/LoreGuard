## LoreGuard Core UX Design

### Audience
Product/design, analysts, and engineering. This document defines IA, flows, and core interaction patterns.

### UX Principles
- **Analyst speed**: Prioritize search, filtering, and keyboard shortcuts for rapid perspective discovery.
- **Transparency**: Show rubric scores, provenance, and model info inline for viewpoint validation.
- **Consistency with MAGE**: Three‑pane layout, dark/light modes, familiar controls.
- **Scalability**: Lists and queries must perform with hundreds of thousands of artifacts and perspectives.
- **Governed flexibility**: Admins can change rubrics and regrade safely to adapt perspective evaluation.

### Layout: Three‑Pane Shell
1. Side Navigation (left):
   - Dashboard
   - Sources
   - Artifacts
   - Evaluation
   - Library
   - Jobs & Queues
   - Admin (Providers, Rubrics, Integrations, Access)
2. Content List (center):
   - Index views with saved filters, quick facets, bulk actions
3. Details/Workspace (right):
   - Inspector for the selected entity (source, artifact, job)
   - Integrated chatbot panel (toggle) for context‑aware assistance

### Global Elements
- Global search bar with entity scope switcher (Artifacts, Sources, Library, Jobs)
- Status toasts, job progress indicators, and background task tray
- Dark/light theme toggle

### Key Screens and Flows

1) Sources
- List: source name, type (website/API/feed), status, last run, new items
- Filters: type, tag, health, schedule, auth required
- Actions: create, edit, duplicate, disable, run now
- Details: configuration (URL patterns, sitemaps, API keys), crawl policy, content rules, expected file types, dedup keys
- Flow: Create Source → Validate (dry‑run fetch and parse) → Save → Schedule

2) Artifacts
- List: title, source, author, date, type, score, label (Signal/Noise/Review), version
- Facets: topic tags, time, type, score range, label, source, geography
- Actions: open, compare versions, export, add note, assign reviewer, re‑evaluate
- Details: preview (sanitized), metadata, rubric breakdown, clarification evidence, provenance, hash and dedup info
- Bulk: select → regrade with rubric(version), label override, export, move to Library

3) Evaluation
- Views: rubric versions, prompt templates, model settings, calibration sets
- Actions: create/edit rubric, A/B test prompts/models, run calibration batch, publish rubric version
- Compare: side‑by‑side rubric score deltas across versions; acceptance threshold tuning

4) Library
- Curated Signal artifacts ready for MAGE
- Facets: topic, scenario tag, time, origin, confidence
- Actions: link to MAGE workspace, export package, snapshot set

5) Jobs & Queues
- Pipeline job list with stages (ingest → extract → clarify → evaluate → store)
- Per‑job timeline, logs, retries, error triage; requeue button
- Scheduler view: upcoming runs, cron editor, blackout windows

6) Admin
- LLM Providers: add provider using OpenAI‑compatible schema; set defaults
- Access control: roles (Admin, Analyst, Reviewer, Operator)
- Integrations: SharePoint/S3, web proxy, identity provider, webhooks

### Chatbot Integration
- Context: understands currently selected entity and user filters for perspective analysis
- Capabilities: explain evaluation scores, summarize perspective deltas across sources, draft source configs, generate saved filters, create calibration sets for viewpoint assessment
- Safety: restricted actions require explicit confirmation and role checks

### Information Architecture
- Entities: `Source`, `Artifact`, `Evaluation`, `Rubric`, `Job`, `Provider`, `CalibrationSet`, `LibraryItem`
- Tagging: hierarchical topics; scenario tags for wargaming alignment
- Versioning: rubric versions; model/prompt versions; artifact content versions

### Usability and Accessibility
- Keyboard shortcuts: navigation, approve/reject, regrade, open chatbot
- Pagination + virtualization; infinite scroll for lists >50k
- WCAG AA, high‑contrast mode, screen reader labels

### Notifications and Feedback
- Toasts for quick success/failure; persistent job tray with progress
- Email/Teams webhook for important events (source failure, rubric publish)

### Research Tasks (COMPLETED)
- [x] **Component Libraries**: shadcn/ui + Radix UI primitives selected for MAGE consistency
- [x] **Data Virtualization**: TanStack Table + TanStack Virtual for 100K+ row performance
- [x] **Reviewer Workflows**: Active learning selection + Streamlit annotation interface
- [x] **Search Language**: PostgreSQL full-text + pgvector hybrid search with faceted filtering
- [x] **Chatbot Integration**: Context-aware assistance with restricted admin action confirmations

### UI Implementation Ready
Complete three-pane layout specification with virtualized tables, accessibility compliance, and MAGE design consistency established.


