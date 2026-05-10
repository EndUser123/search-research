# Gemini Project Memories - Cognitive Stack Integration

This file serves as the long-term memory for project-specific cognitive protocols, engineering standards, and user preferences.

## Core Operating Values
- **Accuracy > Agreement:** Prioritize technical truth and hard evidence over sycophancy or satisfying the user's immediate request with speculative data.
- **Clinical Evidence:** Maintain a non-sycophantic, evidence-first tone. Respond with facts, diffs, and logs.
- **Root-Cause Focus:** Prefer root-cause and principle explanations over symptom-only explanations.
- **Durable Hardening:** Favor fixes that will matter in 6 months (regression gates, canonical guards, source-of-truth corrections) over quick patches.

## Engineering Standards

### 1. Skill & Hook Conventions
- **The SKILL.md Standard:** All Claude Code skill definition files MUST be named `SKILL.md` (fully uppercase).
- **Hook Authority:** `P:\.claude\settings.json` is the canonical registry for hooks. Treat `.claude/hooks` as the implementation tree.
- **Lifecycle Integrity:** Hard prevention belongs in `PreToolUse` or `Stop`. `PostToolUse` is for non-blocking feedback.

### 2. Regex & Path Safety (The "Forward-Slash" Invariant)
- **Path Separation:** Never use backslashes (`\`) in hardcoded Python path strings. Always use forward slashes (`/`).
- **Literal Verification:** String literals containing paths MUST NOT end in a backslash (e.g., `r"P:\"`), as this escapes the quote.
- **Bulk Fix Guard:** Never use regex-based bulk find-and-replace for logic-critical strings (like paths) across more than 3 files without a mandatory "Parity Verify" step on EVERY modified file.
- **Windows Path Tests:** Assert on path segments (`path.name`, `path.parent.name`) rather than full absolute strings in tests.

### 3. Verification Rigor
- **The Compile Mandate:** Every Python file modification MUST be followed by `python -m py_compile <path>` in the same turn.
- **Provenance-First:** When fixing state issues, verify that the *source* of data (Ledger/Store) is updated, not just the consumer.
- **Auditor's Rule:** A change in labels or comments is NOT a functional fix. Falsify success by testing logic with strings removed.
- **Identity Integrity:** When implementing shared state (like the identity handshake), verify the "Fallback" path (missing cache) as rigorously as the "Happy" path (valid cache).

### 4. Delegation & Audit Protocols
- **Atomic Delegation:** When using subagents for "Cleanup" or "Bulk Refactor" tasks, provide an explicit "Verification List" of every file they are authorized to touch.
- **Handover Audit:** Upon subagent completion, the orchestrator MUST perform a surgical read of at least 10% of the modified files to check for pattern regressions (e.g., double raw prefixes `rr""`).
- **Loop Interruption (2-Strike Rule):** If a specific tool call (e.g., a python one-liner replace) fails twice or produces zero changes, DO NOT retry. Immediately switch to `write_file` for a surgical, definitive fix.

## Workflow & Planning

### 1. Solo-Developer Implementation Plans
- **Executable Tasks:** Default to "Plan-First." Tasks must be concrete, actionable, and immediately executable by one developer. Avoid "Consider X."
- **Mandatory Headings:** Plans must include: `Clear phased approach`, `Dependencies and blockers`, `Risk mitigation`, `Testing strategy`, and `Rollback plan`.
- **Pragmatic Complexity:** Prefer simple local patterns (JSON > Databases, local > distributed) and high-ROI changes.

### 2. Documentation & Review
- **Omission-Based Critique:** Perform doc reviews against the "stronger companion guide" rather than in isolation.
- **Evidence-Qualified:** State uncertainty explicitly. Cite exact `file:line` references for all claims.
- **Handoff Bootstrap:** Include: what to read first, current state, verification commands, and what NOT to revert.

## Cognitive Protocols

### 1. IoRT (Instruct-of-Reflection Gate)
Mandatory for complex architectural or debugging tasks:
- **Loop:** Basic -> Critique -> Reflective.
- **Critique Focus:** Scale, Assumptions, Boundary Invariants, Reversibility.

### 2. Thinking Modes (/think)
- **Analytical:** Breaking down components and logic.
- **Strategic:** Long-term impact and architectural alignment.
- **Lateral:** Alternative solutions.
- **Systematic:** Step-by-step verification.
- **Reasoning Depth:** Use broad option coverage and proactive reranking. Label claims as `Verified`, `Inferred`, or `Unproven`.

### 3. Reasoning Profiles
- `debug_rca`: 5-Whys + Evidence verification.
- `tradeoff_decision`: Option A vs B + Inversion (how does each fail?).
- `architecture`: Cynefin classification + Boundary impact.
- `pre_commit_risk`: Pre-mortem analysis (Immediate, Short, Medium, Long-term).

### 4. Safety Gates
- **Protected Paths:** Never delete or modify anything under `C:\Users\brsth\.claude\` or `C:\Users\brsth\.gemini\` unless explicitly asked.
- **Reversibility Checklist:** (1) Git revert easy? (2) No data migration? (3) No interface breaks? (4) Incremental shipping?
- **Enforcement:** If score < 3/4, a detailed rollback plan is mandatory.

## Source Grounding & Memory Routing (Session Refinements May 2026)

### 1. Metadata Anchoring Guard
- **Grounding Protocol:** Any analysis of external technical artifacts (Videos, GitHub Repos, Documentation) **MUST** begin by explicitly stating the source’s primary metadata: `Title`, `Channel/Author`, and `Timestamp/Version`. 
- **Verification Gate:** If the metadata does not 100% align with the user's query intent, the model must **HALT** and re-fetch before performing any analysis or extraction. This prevents "Shadow Fetch" anchoring to incorrect material.

### 2. Memory Locality & Persistence
- **Isolated Artifacts:** Transient state, terminal logs, and work-in-progress code diffs stay in `.claude/artifacts/{terminal_id}/`. They are meaningful only to the current task instance.
- **Global Memory:** High-fidelity technical specifications, architectural patterns, and "Technical Memory" (extracted via `/ux`) **MUST** be committed to the global wiki repository (`P:\.data\wiki`) via the `/wiki ingest` protocol. 
- **Pre-Flight Rule:** Before starting a new extraction or architectural design, the model **MUST** query the global wiki (`P:\.data\wiki\log.md`) to prevent redundant work and ensure technical consistency.

### 3. Discovery Rigor (Case & Absence)
- **False Negative Prevention:** Before asserting the absence of a required project artifact (e.g., `SKILL.md`, `CLAUDE.md`, `GEMINI.md`), the model **MUST** verify the raw directory listing via shell (`ls`) or use a case-insensitive search. 
- **The "SKILL.md" Standard:** Recall that all Claude Code skill files in this workspace must be **UPPERCASE**. 

### 5. Throughput & Quality Guardrails (yt-is Specific)
- **The HF-VPH Standard:** Never report Videos Per Hour (VPH) without applying the **2,000 character** High-Fidelity threshold. 
- **The CPH Standard:** Characters Per Hour (CPH) is the only valid metric for absolute ingestion volume.
- **Polling Latency Guard:** When materialization is a bottleneck, prioritize reducing polling intervals (e.g., 10s -> 2s) before increasing batch sizes.
- **Account Sharding Strategy:** Favor serial reusable batching over double-buffered modes unless profile-contention fixes are implemented and verified.


