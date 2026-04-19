<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Please check if the plan file, reflects what we want to implement from the chat history file.

The plan file does reflect the architecture and behaviors from the chat-history file, and it also folds in the “missing 30–40%” that the review called out, with no obvious contradictions.[^1_1][^1_2]

Below is a concise alignment check by concept area.

## High‑level architecture

- Both files converge on the same three‑layer model: a **deterministic Python layer** (Path/Step 3), a **Claude reasoning layer** (Step 4), and a simple orchestrator that always runs deterministic analysis first and then reasoning over the JSON envelope.[^1_2][^1_1]
- The plan explicitly encodes this as “Python Deterministic Layer / Agents AI Reasoning Layer / Claude Orchestrator Layer” and preserves the sequencing “User → Path 3 code → Path 4 Claude → final output,” matching the final model in the chat history.[^1_1][^1_2]


## Closing the “missing 30–40%” design

- The review summary in the chat file lists missing pieces (Skill Self‑Health Check, Viability Gate, Chain Integrity Check, Session Goal Detector + GoalEvaluator, SessionReadinessEvaluator, cross‑session theme detection, canonical output sections, gto quick/review/feedback variants, anti‑fluff guardrails, confidence and effort envelopes, CoT self‑refine, 2‑pass GroundingValidator, reference file content).[^1_1]
- The plan introduces concrete tasks for each of these (TASK‑000/000a/000b/000c, TASK‑008, TASK‑009c/009d/009e, TASK‑012, TASK‑013d/013e, TASK‑016/017/018, TASK‑019, TASK‑020a/020b/020c/020d, TASK‑021a/021b/021c/021d), with acceptance criteria that mirror the intent in the conversation, so the previously missing design is now captured.[^1_2]


## Deterministic engine (Path 3) alignment

- The chat insists Path 3 be deterministic, JSON‑first, and always run, with: JSON artifacts for gaps/git/health, typed gaps with file/line, deterministic `formatrecommendednextsteps`, presence checkers, unfinished business detection, code marker scanning, state management, confidence/effort, cross‑session themes, and performance constraints.[^1_1]
- The plan’s Phase 1 (TASK‑001–TASK‑012, TASK‑008–TASK‑011, TASK‑009a–009e, TASK‑003–007, etc.) implements exactly these: JSON artifacts, detectors (UnfinishedBusinessDetector, CodeMarkerScanner, presence checkers), StateManager with versioning and corruption recovery, ResultsBuilder with confidence and effort, and cross‑session theme detection, plus explicit performance benchmarks and safety boundaries that the chat also called out.[^1_2]


## Step 4 / Claude reasoning layer

- The chat defines Step 4 as a single Claude phase that: always refines next steps; conditionally adds deep dives and learning items; works only over the Path‑3 JSON envelope; obeys guardrails (no new gaps, evidence‑linked, SPECULATIVE/LOW CONFIDENCE/INSUFFICIENT INFORMATION); and returns a structured result feeding checklist state and output sections.[^1_1]
- The plan reflects this via:
    - CriticalThinkingEvaluator integration and 3‑phase CoT self‑refine (TASK‑013, TASK‑020c).[^1_2]
    - GroundingValidator with 2‑pass review and exponential backoff (TASK‑014, TASK‑020d).[^1_2]
    - LearningAdvisor integration (TASK‑015).[^1_2]
    - GoalEvaluator and SessionReadinessEvaluator to drive Executive Snapshot readiness and goal status (TASK‑013d, TASK‑013e).[^1_2]
    - Anti‑fluff guardrails and mandatory confidence envelopes for all reasoning roles, wired into SKILL.md (TASK‑020b, referencesoutput‑template.md content).[^1_2]
    - Canonical 9‑section output, with Executive Snapshot, Pass/Fail confirmations, Recommended Next Steps, Critical Thinking Findings, conditional Deep Dives and Learning sections, and Did You Forget Anything?, matching the “fixed layout” described in the chat.[^1_1][^1_2]


## Hooks, state, variants, and best‑practice alignment

- The chat emphasizes wiring into existing hooks (`validateformat.py`, `checklistgate.py`, `sessionsummary.py`), using `.state` for checklists and cross‑session trends, and adding variants like `gto quick`, `gto review`, `gto feedback`, and a handoff checklist at SessionEnd.[^1_1]
- The plan adds these explicitly: SkillSelfHealthChecker checks hooks and state (TASK‑000a); StateManager writes terminal‑isolated state with atomic semantics (TASK‑008); SessionEnd handoff checklist and trend line (TASK‑021a); `gto quick`, `gto review`, and `gto feedback` with the exact behavioral constraints discussed (TASK‑021b/021c/021d).[^1_2]
- The plan also re‑imports the 14 “better than spec” ADR improvements (backoff, path sanitization, state versioning, symlink protection, circular‑handoff detection, coverage target, performance regression threshold, etc.) that the chat says should be adopted back into the design, and marks them as preserved improvements.[^1_1][^1_2]


## Any mismatches or omissions?

- Conceptually, the plan covers every “missing” element the chat review enumerates and formalizes them as tasks with acceptance criteria; there is no obvious area where the conversation calls for a behavior that the plan does not at least mention.[^1_1][^1_2]
- The main remaining work is implementation detail, not architecture: e.g., exact JSON schemas for Step‑4 outputs and the precise SKILL.md prompt text for Planner/Explainer/Learning behaviors are implied through reference files and output‑template guardrails but not exhaustively spelled out as separate artifacts beyond TASK‑012 and TASK‑020a/020b.[^1_1][^1_2]

If you want a stricter RTM‑style check, next step would be: extract the final “Path 3/Step 4” requirements list from the chat file as rows and verify every row maps to at least one TASK‑ID or reference file in the plan.

<div align="center">⁂</div>

[^1_1]: Is-the-conversation-about-skill-architecture-align.md

[^1_2]: plan-adr-20260321-gto-v3-architecture.md


---

# If you can do that, then do it please.

Here is an RTM-style mapping from the finalized chat requirements to concrete items in the plan file, split by Path/Step 3 vs Step 4 and supporting pieces.[^2_1][^2_2]

## Path 3 (deterministic engine) RTM

| Chat requirement (Path 3) | Plan coverage |
| :-- | :-- |
| Always run full deterministic pipeline (no fast vs full dispatch) on every `gto` invocation. [^2_1] | Plan defines Phase 1 “Python Engine” as the mandatory pipeline; no mode-based skipping, and `gto quick` still runs the full engine then skips Claude reasoning only. (TASK‑021b, STEP 7a–7h description, “No modes, no skipping Path 3 always runs this full deterministic pipeline”). [^2_2] |
| Entry point `gtodeterministic.py` runs on scoped transcripts, not code; scope discovery via `get_all_transcript_paths` following handoff chain up to depth 50. [^2_1] | Scope discovery and deterministic entry are encoded in Implementation Plan “Scope Discovery” and “Deterministic Engine” steps and ASCII flow (Step 3 Scope Discovery, Step 4 Deterministic Engine) with max depth 50. [^2_2] |
| JSON artifacts only: `gapfinder.json`, `gitcontext.json`, `health.json`, no prose in artifacts. [^2_1] | Tasks specify JSON artifacts and schemas: `GapFinderSubagent` / `.evidence_gapfinder_*.json`, `GitContextSubagent` / `.evidence_gitcontext_*.json`, `HealthCalculatorSubagent` / `.evidence_health_*.json`, all “machine-structured no human prose”. (7a–7c descriptions, TASK‑002, TASK‑003, TASK‑011). [^2_2] |
| GapFinder: parse transcripts using pattern refs, detect error/test/frustration types, extract `filepath` + `linenumber`, output gaps with `id, turn, severity, type, message, filepath, linenumber`. [^2_1] | TASK‑010 “Enhance GapFinderSubagent” defines regex-based line extraction, validation, file paths, confidence scoring, and structured findings with file/line tuples; the implement-brief portion shows exact JSON fields on gap records. [^2_2] |
| GitContext: branch, status (`clean/dirty/norepo`), modified files, recent commits; fail-open when git missing. [^2_1] | 7b GitContextSubagent spec and TASK‑004–006 cover branch, status, modified files, recent commits, `norepo` status and non-fatal behavior. [^2_2] |
| Health engine: category weights (Tests 30, Docs 20, Git 20, Deps 15, Code Quality 15), severity deductions (Critical -20, High -10, etc.), synthetic git gap, presence checkers for tests/docs/deps. [^2_1] | 7c HealthCalculatorSubagent description plus referenceshealth-thresholds.md encode weights, banding, deductions, presence-check rules, synthetic git gap, and effort mapping. (TASK‑004–TASK‑006, TASK‑011; reference file content). [^2_2] |
| Presence checkers: TestPresenceChecker, DocsPresenceChecker, DependencyChecker, with structured statuses and gap types. [^2_1] | Explicit tasks for each: TASK‑004 “TestPresenceChecker”, TASK‑005 “DocsPresenceChecker”, TASK‑006 “DependencyChecker” with acceptance criteria for structured outputs and gap types. [^2_2] |
| Unfinished business detection using referencesunfinished-patterns.md (tasks, questions, dropped topics, pending decisions, partial implementations, deferred items). [^2_1] | TASK‑002 “UnfinishedBusinessDetector” plus reference file referencesunfinished-patterns.md content and STEP 7d specification (pattern categories, JSON shape, write `.evidence_unfinished_*.json`). [^2_2] |
| Code marker scanning: TODO/FIXME/HACK/XXX, `.gitignore` aware, path sanitization, size limits, symlink protection. [^2_1] | TASK‑003 “CodeMarkerScanner” includes `.gitignore` respect, whitelist extensions, 1MB cap, `Path.resolve` + root check, symlink `follow=False`, and boundary-condition tests (LOGIC/SEC findings fixed). [^2_2] |
| Deterministic Recommended Next Steps (Step 7h): group by domain, sorted CRITICAL→LOW, evidence-linked, RECURRING flag, effort estimates, “0. Do ALL…”. [^2_1] | TASK‑007 “format_recommended_next_steps” plus STEP 7h spec and examples, and SKILL/output-template sections describing domain groups, effort mapping, recurring label, and the “0. Do ALL Recommended Next Steps above.” footer. [^2_2] |
| Pattern enrichment step: attach pattern tags/codes per gap using reference pattern files. [^2_1] | STEP 7f Pattern Enrichment and TASK‑012 reference files define loading all three pattern reference files and enriching gaps with tags that then flow into ResultsBuilder. [^2_2] |
| Results JSON builder with deduplication, recurrence, confidence envelope, effort estimation, cross-session themes, state context. [^2_1] | TASK‑009a (InitialResultsBuilder), TASK‑009c (Confidence Scoring), TASK‑009d (Effort Estimation), TASK‑009e (Cross‑Session Theme Detection), and STEP 7g spec collectively match: composite key, source lists, recurrence counts, confidence rules, effort mapping, theme detection, and final `results` dict fields (terminalid, gaps, gapmetrics, gitcontext, health, unfinished, codemarkers, crosssessionthemes, statecontext, baselinenextsteps). [^2_2] |
| StateManager: terminal-isolated `.evidence/gto-state-<terminal>`, versioned schema, atomic writes with temp file, corruption recovery, orphaned tmp cleanup. [^2_1] | TASK‑008 “StateManager” defines directory per terminal, atomic write pattern, schema with version + gaps + metadata, JSON schema validation, tmp cleanup, fallback to empty state. [^2_2] |
| Multi-terminal safety tests and race handling. [^2_1] | TASK‑017 “multi-terminal safety tests” includes write-write/read-write race, corruption scenarios, recovery, and recurrence tracking tests. [^2_2] |
| Performance benchmarks (scanning performance, state write, agent overhead, regression thresholds). [^2_1] | TASK‑019 “performance benchmarks” sets explicit targets and regression detection relative to a 1.2 baseline. [^2_2] |

## Step 4 / Claude reasoning layer RTM

| Chat requirement (Step 4) | Plan coverage |
| :-- | :-- |
| Step 4 runs after Path 3, never skips it, and uses only the JSON envelope (gaps, gapmetrics, gitcontext, health, baselinenextsteps). [^2_1] | Plan describes Step 8 “Claude Reasoning Step” taking results JSON, with explicit inputs (sessiongoal, gaps, metrics, gitcontext, health, baselinenextsteps) and forbids reading transcripts/git directly; flow diagrams and “Path 4 scope final” text reinforce this. [^2_2] |
| Envelope schema: gaps (id/turn/severity/type/message/file/line), gapmetrics, gitcontext, health, baseline next steps. [^2_1] | Implement-brief segments in the plan give the exact structures for `gaps`, `gapmetrics`, `gitcontext`, `health`, and `baselinenextsteps`, matching the conversation’s field lists. [^2_2] |
| Step 4 outputs: `refinednextsteps` (required), `deepdives` (conditional), `learningitems` (conditional), all structured JSON. [^2_1] | The plan’s Step 8 roles (8a Planner, 8b Explainer, 8c LearningAdvisor) describe these three outputs and their JSON shapes; STEP 9 Section 5 clarifies how `refinednextsteps` vs `baselinenextsteps` are used. [^2_2] |
| Planner (8a): always runs; input = results JSON + baselinenextsteps; output = refinednextsteps reordered by priority (critical/high/medium/low, recurring prioritized), clearer language, evidence-linked, health trend-aware urgency. [^2_1] | ROLE 8a Planner spec in the plan exactly encodes: input, reorder rules, evidence linkage, trend interpretation, and the note that Planner refines and replaces Step 7h baseline. [^2_2] |
| Explainer (8b): triggered if `health.overallscore ≤ 80` or `gapmetrics.critical > 0`; produces deepdives with title, gapids, explanation, hypothesis, diagnostic actions and confidence. [^2_1] | ROLE 8b Explainer spec, including trigger condition, structure of each deep dive, and confidence field, plus the summary in TASK‑013/TASK‑020c/020d, covers this behavior. [^2_2] |
| Learning (8c / LearningAdvisor): conditional on gap types (userfrustration, repeated test failure, etc.); produces learningitems for CLAUDE.md or learn/reflect with suggested content and prompts. [^2_1] | TASK‑015 “LearningAdvisor integration” and ROLE 8c in the implement brief describe learningitems structure, triggers by gap types, and outputs for CLAUDE.md/learn/reflect. [^2_2] |
| GroundingValidator: two-pass grounding check, identifies ungrounded references, final ungrounded items go to debug log only; auto-retry with backoff. [^2_1] | TASK‑014 and STEP 8f detail the two-pass algorithm, classification of ungrounded items, final behavior (debug log only), and exponential backoff/timeouts. [^2_2] |
| CriticalThinkingEvaluator: 3-phase CoT self-refine, strict guardrails, operates over results JSON only. [^2_1] | TASK‑013 “CriticalThinkingEvaluator integration” plus TASK‑020c describe 3-phase CoT / self-refine, with timeouts/backoff and structured findings integrated into results JSON. [^2_2] |
| GoalEvaluator: uses SessionGoalDetector output and transcripts to classify goal status (met/partially_met/abandoned/unstated) with evidence. [^2_1] | TASK‑013d “GoalEvaluator” defines input (sessiongoal + transcripts), statuses, evidence requirements, and integration into Executive Snapshot. [^2_2] |
| SessionReadinessEvaluator: READY / NEEDS WORK / CRITICAL ISSUES based on seven criteria; appear in Executive Snapshot and Section 2 Pass/Fail. [^2_1] | TASK‑013e plus STEP 8g spec codify the exact criteria set and mapping to readiness signals, and the plan notes that this appears in Section 1 and Section 2 of the output. [^2_2] |
| Confidence envelope per gap and per finding: `confidence`, `confidencereason`, `assumptions`, `invalidatedby`, `speculative`. [^2_1] | TASK‑009c (per-gap confidence) and referencesoutput-template.md + TASK‑020b (guardrails) require this envelope on all findings and warn if missing labels when confidence is not high. [^2_2] |
| Effort estimates per gap and next step (5min/30min/2hr, plus rules for markers, git dirty, missing lock/README/CLAUDE). [^2_1] | Effort mapping appears twice: once in referenceshealth-thresholds.md and again in TASK‑009d and Step 7h spec; SKILL/output sections instruct including effort indicators and explicit text examples. [^2_2] |
| SPECULATIVE, LOW CONFIDENCE, INSUFFICIENT INFORMATION labels; anti-fluff guardrails; no praise, no generic advice, no hallucinated IDs. [^2_1] | TASK‑020b “Anti-Fluff Guardrails” plus referencesoutput-template.md define these labels and “NEVER/ALWAYS” rules, and assert they apply to all reasoning roles; validateformat.py warns when labels are missing. [^2_2] |
| Fixed presentation layout for Step 4 outputs integrated into 9 canonical sections: Snapshot, Pass/Fail, Unfinished Business, Cross-Session Themes, Recommended Next Steps, Critical Thinking Findings, Deep Dives, Learning \& Documentation, Did You Forget Anything?. [^2_1] | TASK‑020a lays out all 9 output sections, mandatory vs conditional visibility, and how Step 9 `format_output(results_json)` assembles them; Section 5/6 details align with the chat’s final “fixed layout” description. [^2_2] |
| Hook and `.state` wiring: Step 4 writes refinednextsteps and unresolved items into `.state/gto-checklist-<terminal>.json`; hooks read this; session summary shows health trend and open/closed counts. [^2_1] | STEP 5e “Update Checklist State” in the ASCII diagram, TASK‑021a “Handoff Checklist at SessionEnd”, and TASK‑021d “gto feedback Variant” together describe writing checklist state, and using that in `sessionsummary.py` for trends and checklists. [^2_2] |

## Other missing items (from “30–40% missing” list)

| Missing item from chat review | Where covered in plan |
| :-- | :-- |
| Skill Self-Health Check (verify references, hooks, .state writable, etc.). [^2_1] | TASK‑000a “SkillSelfHealthChecker” with detailed checks and caching behavior. [^2_2] |
| Viability Gate (hard-stop preconditions before any analysis). [^2_1] | TASK‑000 “ViabilityGate” with enumerated checks, messages, and unit tests. [^2_2] |
| Chain Integrity Check (JSONL/handoff chain validation). [^2_1] | TASK‑000b “ChainIntegrityCheck” with readable/valid JSONL checks, contiguous sequence, partial-scope behavior. [^2_2] |
| Session Goal Detector (patterns like “today I want to…”). [^2_1] | TASK‑000c “SessionGoalDetector” with patterns and tests. [^2_2] |
| Cross-session theme detection. [^2_1] | TASK‑009e “Cross-Session Theme Detection” and inclusion of `crosssessionthemes` in results JSON and Section 4. [^2_2] |
| Executive Snapshot + Pass/Fail confirmations. [^2_1] | TASK‑020a sections 1–2 define exact content and rules. [^2_2] |
| `gto quick`, `gto review`, `gto feedback` variants with specific behavior. [^2_1] | TASK‑021b/021c/021d describe each variant’s behavior and coupling to core pipeline and Step 8. [^2_2] |
| Handoff checklist at SessionEnd. [^2_1] | TASK‑021a extends `sessionsummary.py` to output trend line + handoff checklist. [^2_2] |
| CoT self-refine for CriticalThinkingEvaluator. [^2_1] | TASK‑020c. [^2_2] |
| GroundingValidator 2-pass. [^2_1] | TASK‑020d and STEP 8f. [^2_2] |
| Reference file content explicitly specified (patterns, thresholds, template, questions). [^2_1] | TASK‑012 and the in-plan content blocks for `referencesunfinished-patterns.md`, `referenceshealth-thresholds.md`, `referencesoutput-template.md`, `referencescritical-thinking-questions.md`. [^2_2] |

## Gaps / assumptions

- The chat calls out needing explicit JSON schemas for Step‑4 outputs and possibly separate SKILL.md snippet definitions for Planner/Explainer/Learning; the plan gives field-level shapes and behavior descriptions but does not present formal JSON Schema documents as separate artifacts.[^2_2][^2_1]
- The mapping above assumes that the implement-brief embedded in the plan is authoritative for field lists and that there is no additional external spec that would further constrain naming or types.[^2_1][^2_2]

If you want, the next concrete step is: export just the Path‑3/Step‑4 portions of this table into a CSV and drop it into your repo as `gto-v3-rtm.csv` to track implementation status per TASK‑ID.

<div align="center">⁂</div>

[^2_1]: Is-the-conversation-about-skill-architecture-align.md

[^2_2]: plan-adr-20260321-gto-v3-architecture.md


---

# I'm more concerned if we're missing anything from the solution or the plan

Nothing major is missing at the architecture/behavior level; the gaps now are mostly “formalization” and “testability,” not missing concepts.[^3_1][^3_2]

## 1. Solution-level coverage

From the conversation’s final model, the core solution elements are all present in the plan:

- Deterministic engine (Path 3): JSON artifacts, typed gaps with file/line, health scoring, presence checkers, unfinished business, code markers, state manager, recurrence/themes, deterministic Recommended Next Steps, performance targets. All of these appear as concrete tasks with acceptance criteria.[^3_2][^3_1]
- Claude reasoning layer (Step 4): single phase after Path 3, using only the JSON envelope; Planner, Explainer, Learning behaviors; GoalEvaluator, SessionReadinessEvaluator; CriticalThinkingEvaluator with CoT self-refine; GroundingValidator 2-pass; guardrails, confidence and effort envelopes; and fixed output layout with 9 sections. All of these are explicitly captured in tasks and reference files.[^3_1][^3_2]
- Hooks and state integration: checklist updates from Step 4, sessionsummary using trends and checklist state, non-blocking pre-run hooks, multi-terminal safety, variants (gto quick/review/feedback), handoff checklist at SessionEnd. These behaviors are all present as tasks (000a, 008, 017, 021a–d) plus flow diagrams.[^3_2][^3_1]

So at the “what should this system do?” level, the plan matches the agreed solution.

## 2. Plan-level gaps or ambiguities

Where things are thinner (and could bite you later) is in **formality and verifiability**, not in missing features:

- JSON schemas are implicit, not formal: the plan shows field lists and examples for `results`, `refinednextsteps`, `deepdives`, `learningitems`, etc., but there is no single, authoritative schema artifact (e.g., `results.schema.json`, `step4.schema.json`). That makes contract drift more likely.[^3_1][^3_2]
- SKILL.md snippets for Step‑4 roles are described, but not fully written as copy‑pasteable prompts in the plan itself; the behavior is clear, but the exact text is only partially present via referencesoutput-template.md and critical-thinking-questions.md.[^3_2][^3_1]
- Variant behavior is specified (gto quick/review/feedback) but the interplay of flags, environment variables, and CLI interface is not fully spelled out as a single “mode matrix.” You can infer it, but it’s not consolidated.[^3_2]
- Test coverage targets and categories are present (TASK‑016–018, 80% coverage), but there is no explicit mapping from each major behavior (e.g., theme detection, SessionReadinessEvaluator criteria, guardrail violations) to specific test cases in a checklist-like way.[^3_2]

These are “how precise is the spec?” issues rather than “we forgot a whole subsystem.”

## 3. Concrete “missing” items you may want to add

If your concern is “is there anything important we talked about that the plan does not yet *pin down enough to be unambiguous*?”, the likely additions are:

- A small set of **JSON schema files** (or at least tables) for: `results.json`, Step‑4 output (`refinednextsteps`, `deepdives`, `learningitems`), and the checklist state file.[^3_1][^3_2]
- A dedicated section in the plan (or separate doc) with the **final SKILL.md fragments** for: Planner, Explainer, Learning, GoalEvaluator, SessionReadinessEvaluator, and the Step‑8 guardrails block, so there is zero room for prompt drift.[^3_1][^3_2]
- A one-page **mode/variant matrix** (rows = `gto`, `gto quick`, `gto review`, `gto feedback`; columns = “run Path 3?”, “run Step 4?”, “which sections shown?”, “hooks triggered?”).[^3_2]
- A **test RTM** (similar to what we just did, but for tests): map each critical behavior (ViabilityGate, ChainIntegrityCheck, theme detection, readiness signal boundaries, guardrails warnings, agent timeout degradation) to at least one integration or unit test ID.[^3_2]

If you’d like, next step can be: define the `results.json` + Step‑4 output schemas explicitly (as JSON or markdown tables), and then you can plug them into both code and SKILL.md as the single source of truth.

<div align="center">⁂</div>

[^3_1]: Is-the-conversation-about-skill-architecture-align.md

[^3_2]: plan-adr-20260321-gto-v3-architecture.md


---

# Those are all great ideas. Please provide a prompt I can take to the simpler LLM to implement to address them.

Use this as a single shot prompt you hand to the other model; edit repo paths/names as needed.

***

You are an expert engineer helping finalize a GTO v3 architecture plan and its implementation contracts.

You have two inputs:

1) `Is-the-conversation-about-skill-architecture-align.md` – conversation/solution design.
2) `plan-adr-20260321-gto-v3-architecture.md` – ADR + implementation plan.

Your job is to **add missing formalization and testability detail** without changing any existing decisions.

## Overall rules

- Do NOT change or delete any existing requirements, tasks, or decisions.
- You MAY:
    - Add new subsections, tables, and examples.
    - Add clearly-marked new tasks (TASK-1xx) if needed.
    - Tighten wording where it is ambiguous, but do not contradict the ADR.
- Prefer **concise, mechanical specifications** (schemas, tables, matrices) over prose.
- When in doubt, align with the conversation file as the functional “source of truth”.

***

## Deliverable 1: Results JSON schema

Goal: Make the deterministic engine’s output contract explicit and machine-checkable.

Using both files, produce a **single authoritative schema** for the Path‑3 engine result (what `gtodeterministic.py` returns before Step 4):

1. Define a schema for `results.json` including (but not limited to) these top-level fields, with correct types and nullability:
    - `terminal_id`
    - `timestamp`
    - `session_count`
    - `partial_scope`
    - `session_goal`
    - `gaps[]` records
    - `gap_metrics`
    - `git_context`
    - `health`
    - `unfinished[]`
    - `code_markers[]`
    - `cross_session_themes[]`
    - `state_context`
    - `baseline_next_steps[]`
2. For each nested object type, define the fields and constraints, aligning with the conversation’s examples. In particular, make sure you cover:
    - Gap record: `id`, `turn`, `severity`, `type`, `message`, `filepath`, `line_number`, `sources[]`, `recurrence_count`, `first_seen_run`, `confidence`, `confidence_reason`, `assumptions`, `invalidated_by`, `speculative`, `effort_estimate`, `pattern_tag`.
    - `gap_metrics`: `total`, `critical`, `high`, `medium`, `low`.
    - `git_context`: `branch`, `status` (enum: `clean`, `dirty`, `norepo`), `modified_files[]`, `recent_commits[]`.
    - `health`: `overall_score`, `category_scores` (tests/docs/git/dependencies/code_quality), `top_contributors[]` with explicit reference to gap ids.
    - `unfinished[]`: categories from `referencesunfinished-patterns.md` with references into turns.
    - `code_markers[]`: marker type, file, line, and context.
    - `cross_session_themes[]`: theme id, `gap_type`, `occurrence_count`, `of_last_n_runs`, `first_seen`, `last_seen`, `gap_ids[]`.
    - `baseline_next_steps[]`: domain, severity, description, linked `gap_ids[]`, `effort_estimate`, recurrence flags.
3. Output the schema in TWO forms:
    - a) A **JSON Schema–style document** (not necessarily fully strict, but close enough to drive validation tooling).
    - b) A compact **Markdown table** version that can be pasted directly into the ADR/plan.

Keep it consistent with the current plan; if there’s a conflict between plan and convo, respect the plan but add a brief note.

***

## Deliverable 2: Step‑4 output schema (Claude reasoning layer)

Goal: Make Step‑4’s contracts explicit.

Based on the “Step 4” descriptions, define the **exact JSON output envelope** that the Claude reasoning phase produces and returns before final SKILL.md formatting:

1. Define a top-level Step‑4 result object that at minimum contains:
    - `refined_next_steps[]` (required)
    - `deep_dives[]` (optional, empty list if none)
    - `learning_items[]` (optional, empty list if none)
    - `goal_evaluator` result
    - `session_readiness` result
    - `critical_thinking_findings[]` (with required confidence envelope)
    - Any additional fields referenced in the ADR (e.g., risk/handoff blockers).
2. For each array/object, define its schema. For example:
    - `refined_next_steps[]`: `id`, `domain`, `severity`, `title`, `description`, `gap_ids[]`, `evidence` (file/line or artifact), `effort_estimate`, `recurring_count` / flag, `confidence` envelope.
    - `deep_dives[]`: `title`, `gap_ids[]`, `explanation`, `hypothesis`, `diagnostic_actions[]`, `confidence` envelope.
    - `learning_items[]`: `target` (enum: `CLAUDE.md`, `learn`, `reflect`), `prompt_or_content`, `gap_ids[]`, `reason`, `confidence`.
    - `goal_evaluator`: `goal_text`, `status` (enum: `met`, `partially_met`, `abandoned`, `unstated`), `evidence`, `confidence`.
    - `session_readiness`: `signal` (enum: `READY TO HANDOFF`, `NEEDS WORK`, `CRITICAL ISSUES`), `criteria_results` (the 7 booleans defined in the plan), `failing_criteria[]`.
    - `critical_thinking_findings[]`: category (COMPLETENESS/RISK/BLIND_SPOTS/MOMENTUM/HANDOFF), plus text and full confidence envelope.
3. Explicitly encode:
    - The **confidence envelope** fields that MUST appear on every finding: `confidence`, `confidence_reason`, `assumptions`, `invalidated_by`, `speculative` (boolean).
    - Which lists are “always present but may be empty” vs “omitted when not applicable”. Match the ADR’s 9-section rules.

Again, produce:

- a) A JSON-Schema-like object.
- b) Markdown tables summarizing the fields.

***

## Deliverable 3: SKILL.md reasoning-role snippets

Goal: Turn the described Step‑4 roles into **copy-pasteable prompt blocks**.

Using `referencesoutput-template.md`, `referencescritical-thinking-questions.md`, and the plan:

1. Write **short, concrete prompt snippets** for each reasoning role:
    - Planner (Step 8a).
    - Explainer (Step 8b).
    - LearningAdvisor (Step 8c).
    - CriticalThinkingEvaluator (if not already fully written; otherwise, just cross-check).
    - GroundingValidator (Step 8f).
    - GoalEvaluator.
    - SessionReadinessEvaluator.
2. For each snippet:
    - Make it **self-contained** (it must state inputs, outputs, constraints).
    - Refer explicitly to the schemas you defined in Deliverable 2.
    - Include the anti-fluff guardrails:
        - Never invent gaps or file/line references.
        - Always attach the confidence envelope.
        - Use SPECULATIVE / LOW CONFIDENCE / INSUFFICIENT INFORMATION tags correctly.
    - Make clear **what NOT to do** (e.g., “do not re-detect gaps; only operate on `results.json` from the engine”).
3. Output them as Markdown sections that can be dropped straight into SKILL.md, e.g.:
```markdown
### Role: Planner (Step 8a)

SYSTEM:
<instructions...>

INPUT:
- JSON object with fields: ...

OUTPUT:
- JSON object with field `refined_next_steps`: ...
```

Keep them concise but precise.

***

## Deliverable 4: Mode/variant matrix

Goal: Make the behavior of `gto`, `gto quick`, `gto review`, `gto feedback` unambiguous.

1. From the plan, reconstruct what each variant does in terms of:
    - Runs Path‑3 deterministic engine? (Y/N)
    - Runs Step‑4 reasoning? (which pieces: Planner, Explainer, Learning, CT, etc.)
    - Which of the 9 canonical output sections are rendered.
    - Which hooks run (pre-run checklist/validateformat, post-run sessionsummary, etc.).
    - Whether it updates `.state` (history, checklist) or is read-only.
2. Produce a **single Markdown table** with rows = modes and columns = these behaviors.
3. If the plan is ambiguous on any cell, do NOT invent new behavior; instead:
    - Add a “TODO / decision required” note in that cell.
    - Optionally suggest a minimal default that is consistent with the rest, clearly marked as recommendation, not fact.

***

## Deliverable 5: Test RTM for critical behaviors

Goal: Ensure test coverage is explicitly mapped to behaviors.

Using TASK‑016–018 and the conversation:

1. Create a **test requirement matrix** that maps **critical behaviors** to test types. For example, rows like:
    - ViabilityGate hard-stops and messages.
    - ChainIntegrityCheck partial-scope behavior.
    - SessionGoalDetector patterns.
    - StateManager corruption recovery and atomicity.
    - Cross-session theme detection thresholds.
    - Effort estimate mapping.
    - Confidence envelope assignments.
    - Readiness signal boundaries (READY/NEEDS WORK/CRITICAL).
    - Guardrails (warnings when a finding lacks confidence label, etc.).
    - GroundingValidator’s two-pass behavior.
    - Agent timeout + exponential backoff.
    - Multi-terminal race conditions.
    - Mode behavior (quick vs full vs review vs feedback).
2. For each row, add:
    - The **expected behavior** (one sentence).
    - The **test type** (unit/integration/end-to-end).
    - A suggested **test ID or name** to use (e.g., `test_viability_gate_missing_transcripts_hard_stop`).
3. Output this as a Markdown table matching the existing tasks (e.g., cross-referencing TASK‑016/017/018).

***

## Output format

Return all deliverables in a single Markdown document with clear headings:

- `## Results JSON schema`
- `## Step-4 output schema`
- `## SKILL.md reasoning-role snippets`
- `## Mode and variant matrix`
- `## Test RTM`

Assume another engineer will paste your output into the ADR/plan and then implement code and tests against it.

---

# This should show our planning skill.  How would you update it to fix all the problems that you identified so that when it is used next time, we don't have those issues.

The planning skill itself is solid; the problems that showed up in the GTO v3 work were mostly about **how we used it** and **what it enforces**, not its core plumbing. To avoid those issues next time, the planning skill needs to:

1) enforce stronger contracts on plans (schemas, RTM completeness),
2) make “missing design/formalization” a first‑class failure mode, and
3) steer the LLM into concrete artifacts (schemas, matrices, prompts) instead of just prose.

Below is a minimal set of upgrades you can make to `/planning` so that a future GTO‑style plan cannot “look good but be 30–40% under‑specified”.

***

## 1. Add explicit “Design Formalization” checks

Problem observed: GTO v3 plan missed explicit JSON contracts, output schema, mode matrix, and test RTM, even though the narrative architecture was correct.[^5_1][^5_2][^5_3]

Update `auto_verify.py` to add a **new check category**, e.g. `design_formalization`:

- New check function, roughly:
    - `check_design_formalization(plan_markdown: str) -> list[finding]`
    - Requirements for any “architecture/engine/skill” plan:
        - **Results/engine schema present**: a section or code block clearly defining the deterministic output shape (e.g. `results.json`), with field names and types.
        - **Reasoning‑layer / Step‑4 schema present**: same, for any Claude reasoning layer (refined steps, deep dives, learning items).
        - **Output layout contract present**: a short section that defines canonical output sections (e.g., 9 sections) and when each appears.
        - **Mode/variant behavior specified**: a table with rows = modes/variants, columns = “runs deterministic engine?”, “runs reasoning?”, “sections rendered”, “hooks/state behavior”.
        - **Test RTM present**: table mapping critical behaviors to at least one test each.
- For each missing item, emit a HIGH‑priority finding like:
    - `id`: `FORM-001`
    - `category`: `design_formalization`
    - `priority`: `HIGH`
    - `title`: `Missing results.json schema`
    - `description`: explain what’s missing, e.g. “Plan describes engine behavior but does not define an explicit results.json schema with fields and types.”
    - `recommendation`: “Add a ‘Results JSON schema’ section with either JSON Schema or a field table.”
- Integrate into `verify_plan()` so it runs for all architecture/engine plans (detect via tags or ADR topic), or conservatively for all ADR‑scoped plans.[^5_1]

This ensures next time the plan must include the schemas and contracts that were missing this time.

***

## 2. Strengthen RTM coverage for design requirements

Problem: RTM coverage check exists but didn’t flag that **solution‑level requirements** from the conversation (e.g., “Step‑4 must not read transcripts/git”, “confidence envelope on all findings”) were not all mapped to tasks.[^5_2][^5_3][^5_1]

Extend `check_rtm_coverage()` in `auto_verify.py`:

- Today: It maps “requirements → tasks” at a generic level.[^5_1]
- Needed additions:
    - Recognize **design‑level requirements** inside the plan such as:
        - “Step 4 must only read Path‑3 JSON.”
        - “All findings must have confidence, assumptions, invalidated_by, speculative.”
        - “GroundingValidator must be 2‑pass; ungrounded items go to debug log only.”
        - “SessionReadinessEvaluator uses the 7 criteria with specific READY/NEEDS WORK/CRITICAL rules.”
    - Require that each such requirement is mapped to **at least one TASK‑ID** *or* to a named artifact (e.g., “results.schema.json”) in an RTM table.

Implementation pattern:

- Parse sections like “Requirements” and “What is remaining in Path 4?” into a set of requirement statements.
- Parse any RTM table or list in the plan.
- For each requirement, if there is no row mapping it to TASK‑xxx or test ids, raise a MEDIUM/HIGH priority RTM finding.

This will force a future GTO v4 plan to explicitly trace every behavioral requirement to tasks/tests.

***

## 3. Add a “Prompt/Skill Snippet Completeness” check

Problem: Step‑4 roles (Planner, Explainer, Learning, GoalEvaluator, SessionReadinessEvaluator) were behaviorally defined but not turned into concrete SKILL.md snippets, which increases drift risk.[^5_3][^5_2]

Add a new check in `auto_verify.py` for **prompt/spec completeness**:

- When the plan mentions **roles/agents** (e.g., “Planner”, “Explainer”, “LearningAdvisor”, “GroundingValidator”, “CriticalThinkingEvaluator”), require that there is:
    - A dedicated subsection per role, with:
        - Inputs (explicit JSON structure names).
        - Outputs (explicit schema names).
        - Guardrails (anti‑fluff rules, confidence envelope).
- If the plan contains role names but no corresponding snippet/section with that structure, emit a finding:
    - `category`: `prompt_contracts`
    - `priority`: HIGH
    - `title`: `Missing SKILL.md snippet for role: Planner`
    - `recommendation`: “Add a ‘Role: Planner’ section with SYSTEM/INPUT/OUTPUT and reference the Step‑4 schema.”

This targets the exact gap that caused Step‑4 to be described but not fully pinned down.

***

## 4. Tighten auto-fix to scaffold missing sections, not just rename

Problem: auto_fix currently “Add missing sections” and “Rename to canonical names”, but for GTO v3 we needed **templated content** for key sections (schemas, mode matrix, test RTM), not just headings.[^5_1]

Extend `auto_fix.py`:

- For known section names (e.g., `Results JSON schema`, `Step-4 output schema`, `Mode and variant matrix`, `Test RTM`):
    - If missing, add **scaffolded placeholders** with explicit TODO markers, e.g.:

```markdown
## Results JSON schema

TODO: Define the engine results JSON schema. At minimum include:
- terminal_id, timestamp, session_count, partial_scope, session_goal
- gaps[], gap_metrics, git_context, health, unfinished[], code_markers[], cross_session_themes[], state_context, baseline_next_steps[]
```

- This way, even if the user forgets to write these sections, the plan gets patched into a state where the missing content is highly visible and structured.

Ensure auto-fix logs these as `sections_added` so verification can still flag them until they are filled.

***

## 5. Extend FINDINGS_SCHEMA to support design/formalization issues

Problem: Current findings schema is oriented around “implementation gaps” and “missing sections”, but we now also want to flag **missing contracts** and **formalization** as first‑class issues.[^5_1]

Update `FINDINGS_SCHEMA.md`:

- Add new `category` values such as:
    - `design_formalization`
    - `prompt_contracts`
    - `schema_coverage`
- Document that these categories are **required** for architecture/skill plans and give short examples for each.
- Make clear that these categories are as serious as `task_completeness` and `rtm_coverage`, not cosmetic.

This lets downstream tools and your own reading distinguish “you forgot the schema” from “you forgot test names”.

***

## 6. Add targeted tests for these new behaviors

Problem: The planning skill has good tests, but none for “missing design contracts” detection.[^5_1]

Add tests under `tests/`:

- `test_auto_verify_design_formalization.py`:
    - Plans missing results schema should trigger FORM‑001.
    - Plans missing Step‑4 schema should trigger FORM‑002.
    - Plans with both schemas and mode matrix should **not** raise these findings.
- `test_auto_verify_prompt_contracts.py`:
    - Plan that mentions “Planner” without a role snippet triggers HIGH finding.
    - Plan with proper role snippet passes.
- Update `test_rtm.py`:
    - Add cases for design requirements mapping (e.g., Step‑4 not reading transcripts must have a TASK mapping).
- Optionally: small integration tests where a minimal GTO‑v3‑style plan is run through the planning skill and must fail until schemas/prompts/matrix/RTM are added.

This ensures your planning skill actually enforces the new rules.

***

## 7. Summary of changes to make

Concretely, to “fix all the problems” next time:

- **In `auto_verify.py`:**
    - Add `check_design_formalization()`.
    - Extend `check_rtm_coverage()` to include design-level requirements.
    - Add `check_prompt_contracts()` to ensure roles have SKILL.md snippets.
- **In `auto_fix.py`:**
    - When a plan is recognized as an architecture/engine/skill plan, scaffold:
        - `## Results JSON schema`
        - `## Step-4 output schema`
        - `## Mode and variant matrix`
        - `## Test RTM`
- **In `FINDINGS_SCHEMA.md`:**
    - Extend `category` and examples to include the new design-oriented categories.
- **In `tests/`**:
    - Add tests for these new checks and adjust RTM tests accordingly.

If you want a concrete prompt for a simpler LLM to update `/planning` accordingly (similar to what you asked for GTO), say so and this can be turned into a copy-paste implementation brief scoped specifically to this skill.

<div align="center">⁂</div>

[^5_1]: review_bundle_planning_20260321.md

[^5_2]: Is-the-conversation-about-skill-architecture-align.md

[^5_3]: plan-adr-20260321-gto-v3-architecture.md


---

# yes pleas

Here is a single prompt you can give to the simpler LLM to upgrade the `/planning` skill so it enforces the missing contracts next time.

***

You are helping improve an existing Claude Code skill located at `P:\.claude\skills\planning\`.

You have three key files:

- `__lib/auto_verify.py` – deterministic verification engine.[^6_1]
- `__lib/auto_fix.py` – auto-fix of structural issues.[^6_1]
- `FINDINGS_SCHEMA.md` – schema for verification findings.[^6_1]

Your goal: **strengthen this planning skill so it forces architecture/skill plans (like GTO v3) to include missing formalization pieces**, specifically:

- Explicit engine (`results.json`) schema.
- Explicit Step‑4 / reasoning-layer output schema.
- A mode/variant behavior matrix.
- A test RTM that maps critical behaviors to tests.
- Concrete SKILL.md prompt snippets for each reasoning role mentioned.

Do NOT change any existing behavior or decisions; only extend with new checks, scaffolding, and tests.

Work in small, explicit steps.

***

## Step 1 – Extend FINDINGS_SCHEMA for design/formalization

Open `FINDINGS_SCHEMA.md` and modify it as follows:

1. In the `category` description, add these new allowed values:
    - `design_formalization`
    - `prompt_contracts`
    - `schema_coverage`
2. For each new category, add a short example finding, e.g.:
    - `design_formalization`: Missing explicit results JSON schema in the plan.
    - `prompt_contracts`: Role “Planner” referenced but SKILL.md snippet not defined.
    - `schema_coverage`: Requirements mention Step‑4 output but no formal schema is provided.

Keep the style consistent with existing examples.

When done, show the updated `FINDINGS_SCHEMA.md` content.

***

## Step 2 – Add design-formalization check to auto_verify.py

Open `__lib/auto_verify.py`.

Add a new function, **without** breaking the existing eight checks:

```python
def check_design_formalization(plan_markdown: str) -> list[dict[str, Any]]:
    """
    New check: ensure architecture/skill plans include explicit schemas and matrices.

    Expected sections (by heading or equivalent):
    - "Results JSON schema" (or similar)
    - "Step-4 output schema" / "Claude reasoning output schema"
    - "Mode and variant matrix" / "Modes and variants"
    - "Test RTM" / "Test requirements matrix"
    """
    findings: list[dict[str, Any]] = []

    lower = plan_markdown.lower()

    # Helper to check for presence of section headings.
    def has_section(*keywords: str) -> bool:
        return any(k.lower() in lower for k in keywords)

    # 1. Results JSON / engine schema
    if not has_section("results json schema", "engine results schema", "results schema"):
        findings.append({
            "id": "FORM-001",
            "category": "design_formalization",
            "priority": "HIGH",
            "title": "Missing results.json schema",
            "description": (
                "Plan describes engine behavior but does not define an explicit "
                "results JSON schema (fields and types) for the deterministic layer."
            ),
            "recommendation": (
                "Add a 'Results JSON schema' section with a JSON Schema or table "
                "defining terminal_id, timestamp, session_count, gaps[], gap_metrics, "
                "git_context, health, unfinished[], code_markers[], cross_session_themes[], "
                "state_context, baseline_next_steps[]."
            ),
        })

    # 2. Step-4 / reasoning-layer schema
    if not has_section("step-4 output schema", "step 4 output schema",
                       "reasoning output schema", "claude reasoning output schema"):
        findings.append({
            "id": "FORM-002",
            "category": "design_formalization",
            "priority": "HIGH",
            "title": "Missing Step-4 output schema",
            "description": (
                "Plan defines a reasoning layer (e.g., Planner/Explainer/Learning) but "
                "does not define an explicit JSON output schema for refined_next_steps, "
                "deep_dives, and learning_items."
            ),
            "recommendation": (
                "Add a 'Step-4 output schema' section describing the JSON structure for "
                "refined_next_steps, deep_dives, learning_items, goal_evaluator, and "
                "session_readiness."
            ),
        })

    # 3. Mode / variant matrix
    if not has_section("mode and variant matrix", "modes and variants", "mode/variant matrix"):
        findings.append({
            "id": "FORM-003",
            "category": "design_formalization",
            "priority": "MEDIUM",
            "title": "Missing mode/variant matrix",
            "description": (
                "Plan mentions different modes or variants (e.g., quick/full/review/feedback) "
                "but does not include a table describing which phases run and which sections "
                "are rendered for each mode."
            ),
            "recommendation": (
                "Add a 'Mode and variant matrix' table with rows for each mode and columns "
                "for: runs deterministic engine, runs reasoning layer, sections rendered, "
                "hooks and state behavior."
            ),
        })

    # 4. Test RTM
    if not has_section("test rtm", "test requirements matrix", "test requirement matrix"):
        findings.append({
            "id": "FORM-004",
            "category": "design_formalization",
            "priority": "MEDIUM",
            "title": "Missing test RTM",
            "description": (
                "Plan does not include a test requirements matrix mapping critical behaviors "
                "to specific unit/integration tests."
            ),
            "recommendation": (
                "Add a 'Test RTM' section that lists critical behaviors (ViabilityGate, "
                "SessionReadinessEvaluator, GroundingValidator, etc.) and maps each to "
                "one or more test cases."
            ),
        })

    return findings
```

Then, in `verify_plan()` (or equivalent main function that aggregates checks), make sure to:

- Load the plan markdown as a string (you already do this for other checks).
- Call `check_design_formalization(plan_markdown)` and extend the findings list with the result.

Show the diff or the full updated `auto_verify.py`.

***

## Step 3 – Add prompt-contracts check for reasoning roles

In the same `auto_verify.py`, add another check to ensure that if roles are mentioned (Planner, Explainer, etc.), they have concrete SKILL.md-style snippets:

```python
REASONING_ROLE_KEYWORDS = [
    "Role: Planner",
    "Role: Explainer",
    "Role: LearningAdvisor",
    "Role: CriticalThinkingEvaluator",
    "Role: GroundingValidator",
    "Role: GoalEvaluator",
    "Role: SessionReadinessEvaluator",
]

def check_prompt_contracts(plan_markdown: str) -> list[dict[str, Any]]:
    """
    Ensure that any mentioned reasoning roles have explicit prompt/spec sections.
    """
    findings: list[dict[str, Any]] = []
    lower = plan_markdown.lower()

    # Detect role mentions in free text.
    roles_mentioned: list[str] = []
    for name in ["planner", "explainer", "learningadvisor",
                 "criticalthinkingevaluator", "groundingvalidator",
                 "goalevaluator", "sessionreadinessevaluator"]:
        if name in lower:
            roles_mentioned.append(name)

    # Detect formal role sections by heading.
    has_formal_section = {
        name: any(k.lower() in lower for k in [f"role: {name}", f"### role: {name}"])
        for name in roles_mentioned
    }

    for name in roles_mentioned:
        if not has_formal_section[name]:
            findings.append({
                "id": f"PROMPT-{name.upper()}",
                "category": "prompt_contracts",
                "priority": "HIGH",
                "title": f"Missing SKILL.md-style snippet for role '{name}'",
                "description": (
                    f"Plan references reasoning role '{name}' but does not include a "
                    "dedicated 'Role: <Name>' section describing SYSTEM, INPUT, and OUTPUT "
                    "contracts."
                ),
                "recommendation": (
                    "Add a 'Role: {Name}' section with:"
                    " - SYSTEM instructions (guardrails, no new gaps, etc.)"
                    " - INPUT JSON schema name and fields"
                    " - OUTPUT JSON schema name and fields, including confidence envelope."
                ),
            })

    return findings
```

Wire this into `verify_plan()` alongside the other checks, passing the same `plan_markdown` string.

***

## Step 4 – Extend RTM check for design-level requirements

Still in `__lib/auto_verify.py`, extend `check_rtm_coverage()` (or add a new helper it calls) so that:

- It looks for **design-level requirement phrases** like:
    - “Step 4 must not read transcripts”
    - “Every finding must include confidence, assumptions, invalidated_by, speculative”
    - “GroundingValidator runs 2 passes”
    - “SessionReadinessEvaluator uses 7 criteria (health, critical gaps, git clean, unfinished, goal, CLAUDE.md updated, CT blockers)”
- It expects to find these requirements **referenced in an RTM table** or mapping section that explicitly ties them to TASK IDs or test IDs.
- If a requirement phrase is found in the plan text but **no matching row exists in the RTM table**, emit a `category: "schema_coverage"` or `category: "rtm_coverage"` finding, with MEDIUM or HIGH priority.

You can implement this with simple substring matching and a heuristic RTM parser; it does not need to be perfect, just good enough to prevent “obviously missing mapping” cases.

Show the updated `check_rtm_coverage()` (or the new helper) and `verify_plan()` integration.

***

## Step 5 – Scaffold missing sections in auto_fix.py

Open `__lib/auto_fix.py`.

Enhance `fix_plan(plan_path: str) -> dict` so that, when operating on an architecture/engine/skill plan (you can detect this by presence of keywords like “deterministic engine”, “Step 4”, “results JSON”, etc.), it:

- Ensures these section headings exist:
    - `## Results JSON schema`
    - `## Step-4 output schema`
    - `## Mode and variant matrix`
    - `## Test RTM`

Implementation:

- Read the plan markdown into a string.
- For each heading, if not present (case-insensitive), append a scaffolded section at the end:

```markdown
## Results JSON schema

TODO: Define the deterministic engine results JSON schema (results.json).
At minimum, include:
- terminal_id, timestamp, session_count, partial_scope, session_goal
- gaps[], gap_metrics, git_context, health, unfinished[], code_markers[],
  cross_session_themes[], state_context, baseline_next_steps[]
```

- Add each added heading name to `sections_added` in the return dict.

Do not attempt to auto-generate full schemas; just scaffold.

Show the updated `auto_fix.py`.

***

## Step 6 – Add/extend tests

Under `P:\.claude\skills\planning\tests\`, add new test modules:

1. `test_auto_verify_design_formalization.py`:
    - A minimal plan **without** any of the four sections should trigger FORM‑001..004.
    - A plan **with** those section headings (even stubbed) should not trigger FORM‑001..004.
2. `test_auto_verify_prompt_contracts.py`:
    - Plan mentioning “Planner” and “Explainer” but lacking `Role: Planner`/`Role: Explainer` sections should trigger PROMPT‑PLANNER / PROMPT‑EXPLAINER findings.
    - Plan with proper `### Role: Planner` and `### Role: Explainer` sections should not.
3. Extend `test_rtm.py`:
    - Add at least one case where a design requirement string is present but no RTM mapping is present → expect a `schema_coverage`/`rtm_coverage` finding.
    - Add a case where both requirement and mapping are present → no such finding.

You can create minimal in-memory markdown strings and call `verify_plan()` via a helper that accepts a string, or write temp files if that’s easier.

***

## Step 7 – Show final state

Finally, show:

- Updated `FINDINGS_SCHEMA.md`.
- Updated `__lib/auto_verify.py`.
- Updated `__lib/auto_fix.py`.
- New/updated test files.

Make sure all new code is:

- Python 3.14 compatible.
- Using only stdlib.
- Following the existing style in this repo.

Do not invent new behavior beyond what is requested above.

<div align="center">⁂</div>

[^6_1]: review_bundle_planning_20260321.md

