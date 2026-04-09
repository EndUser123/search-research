# Review Bundle: ai-gemini

**Generated**: 2026-04-09
**Scope**: P:\\.claude\\skills\\ai-gemini\\
**File Count**: 1 (SKILL.md only — docs-first skill)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: ai-gemini
- **Version**: 1.3.1
- **Category**: productivity
- **Trigger**: /ai-gemini, /gemini
- **Enforcement**: advisory
- **Effort**: high

### Domain & Purpose

`/ai-gemini` is a soft-routed research and engineering assistant that applies ACG (Analyze-Challenge-Gap) critical-thinking workflow, TDD-lite, adversarial review, and RCA hypothesis ledger depending on task type. It uses Gemini CLI for transcript analysis and cross-session research. It is critical for grounding Gemini outputs in source material rather than training data.

### Scale Metrics
- **File Count**: 1 (SKILL.md — docs-first skill, no Python backing)
- **Lines**: ~267 (SKILL.md)
- **Sections**: 9 numbered sections + changelog
- **Change Frequency**: Active (1.3.1 just released)

### Your Environment
- **OS**: Windows 11 Pro 10.0.26200
- **Shell**: bash
- **Primary Language**: Markdown (skill documentation)
- **External Tool**: Gemini CLI v0.37.0

---

## 2. ARCHITECTURE OVERVIEW

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 1. SOFT TRIAGE (classify task type)                 │
│    RESEARCH / ENGINEERING / DESIGN / RCA            │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 2. WORKFLOW ROUTING (soft — user can override)      │
│                                                     │
│  RESEARCH → ACG (Analyze-Challenge-Gap)             │
│  ENGINEERING → TDD Lite + Verify Pyramid           │
│  DESIGN → Adversarial Review                        │
│  RCA → 5 Whys + Hypothesis Ledger                   │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 3. OUTPUT (per path commitment)                     │
│                                                     │
│  RESEARCH → ACG findings + gap list                 │
│  ENGINEERING → test output + minimal impl          │
│  DESIGN → 3 failure modes + alternatives          │
│  RCA → hypothesis ledger + fundamental cause       │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 4. GEMINI CLI INVOCATION (Section 9)               │
│    Headless mode: -y -o text                        │
│    File scoping: --include-directories              │
│    Error handling: MODEL_CAPACITY_EXHAUSTED vs     │
│    rateLimitExceeded distinction                   │
└─────────────────────────────────────────────────────┘
```

### Key Files
| File | Purpose |
|------|---------|
| `SKILL.md` | Entire skill — docs-first, no Python backing |

### External Dependencies
- Gemini CLI (`gemini`) — external npm package
- `mcp__plugin_context7__query-docs` — for doc queries

---

## 3. EXECUTION AND DATA FLOW

### Triage Flow
1. User query → keyword matching → category assigned
2. Keywords: write/add/create → ENGINEERING; why/how/explain → RESEARCH
3. Multi-category: primary + secondary noted
4. Vague query: ask for clarification

### Path Execution
- **No hard phase gates** — soft routing allows override
- **ENGINEERING**: TDD-lite is advisory only (Non-Goal: "users may choose alternative approaches")
- **RESEARCH**: Source Fidelity Rule enforced — cite file:line or flag `[INFERRED]`

### Gemini CLI Flow (Section 9)
1. Step 0: `gemini --help` verify flags (first use per session)
2. Size check: <500KB → stdin piping; >500KB → `--include-directories`
3. Headless: `gemini -y -o text -p "[prompt]"`
4. Output captured → returned to user

### Error Handling
- `MODEL_CAPACITY_EXHAUSTED` (exit non-zero + reason) → retry with backoff (transient)
- `rateLimitExceeded` + quota % → wait for reset window (user quota)
- Fail-fast if Gemini CLI unavailable → diagnostic: `gemini --version`

---

## 4. COMPONENT INVENTORY

### Core Logic (Section 1-8)
| Component | Path | Responsibility | Limitation |
|-----------|------|---------------|------------|
| Soft Triage | SKILL.md:31-62 | Classify query to workflow path | Vague queries require clarification |
| ACG Workflow | SKILL.md:63-96 | Analyze-Challenge-Gap for RESEARCH | No hard verification |
| TDD Lite | SKILL.md:98-109 | Advisory RED-GREEN-REFACTOR for ENGINEERING | Advisory only, not enforced |
| Adversarial Review | SKILL.md:111-120 | 3-question design critique | Advisory only |
| Hypothesis Ledger | SKILL.md:121-128 | RCA path — 5 Whys + hypothesis tracking | Requires reproducible symptom |
| Source Fidelity Rule | SKILL.md:129-137 | Mandates file:line citation or [INFERRED] flag | Relies on LLM compliance |

### External CLI Integration (Section 9)
| Component | Path | Responsibility | Limitation |
|-----------|------|---------------|------------|
| Step 0 Verification | SKILL.md:163-172 | Verify `gemini --help` flags before use | Assumes CLI installed |
| Headless Invocation | SKILL.md:174-180 | `-y -o text` for unattended mode | YOLO auto-approves all actions |
| Size-Based Routing | SKILL.md:182-200 | Stdin vs `--include-directories` based on size | >500KB threshold hardcoded |
| Error Interpretation | SKILL.md:202-212 | MODEL_CAPACITY_EXHAUSTED vs rateLimitExceeded | Depends on error message format |
| Transcript Resolution | SKILL.md:214-220 | Parse handoff JSON → transcript path | 7-day staleness guard |

### Version History (Changelog)
| Version | Key Changes |
|---------|-------------|
| 1.3.1 | Split 429 into MODEL_CAPACITY_EXHAUSTED vs rateLimitExceeded |
| 1.3.0 | Added Step 0 verification + v0.37.0 evidence |
| 1.2.0 | Section 9 overhaul with `-y -o text`, size-based patterns |
| 1.1.0 | Added Section 9, workflow_steps, multi-category guidance |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Source grounding over training data** — Core Principle: "Gemini draws from training data unless constrained"
2. **Soft routing over hard gates** — User override always allowed
3. **Verification mandatory** — Source Fidelity Rule requires file:line citation
4. **No multi-terminal blocking** — State via transcript paths only

### Technology Constraints
- Gemini CLI must be installed (`gemini --version` verification)
- External doc queries via `mcp__plugin_context7__query-docs`
- No Python backing — docs-first skill

### Performance SLAs
- 500KB threshold for stdin vs `--include-directories` routing
- 7-day staleness guard for transcript paths

### Things That Must NOT Change
- Core Principle (source grounding) — foundational to entire skill
- Source Fidelity Rule (file:line or [INFERRED])
- Step 0 verification before CLI use
- MODEL_CAPACITY_EXHAUSTED vs rateLimitExceeded distinction

---

## 6. KNOWN ISSUES

| # | Severity | Issue | Evidence | Workaround |
|---|----------|-------|----------|------------|
| 1 | HIGH | **Gemini filesystem access unverified** — Section 9's verification premise depends on Gemini actually reading files via `--include-directories`. Test failed with MODEL_CAPACITY_EXHAUSTED before confirming. | SKILL.md:190-200; pre-mortem p3.md:2.1 | Verify with `gemini -y -o text --include-directories "P:/" -p "Read a known file"` when capacity available |
| 2 | MEDIUM | **No test/integration guidance for Section 9** — new CLI mechanism added with no verification procedure | pre-mortem p3.md:4.4 | None |
| 3 | MEDIUM | **Gemini model/version not pinned** — skill assumes generic "Gemini" without specifying Pro/Ultra/2.0. Capabilities differ. | pre-mortem p3.md:4.1 | None |
| 4 | LOW | **ACG acronym not spelled out on first use** — "ACG (Analyze-Challenge-Gap)" at line 63 but acronym introduced at line 25 without definition | SKILL.md:25 vs 63 | Minor — context makes meaning obvious |
| 5 | LOW | **'advisory' enforcement unexplained in body** — frontmatter says `enforcement: advisory` but body never explains what that means | SKILL.md:13 | Partially addressed by Non-Goal clarification |

---

## 7. INTEGRATION POINTS

### Skill Triggers
- `/ai-gemini` — primary trigger
- `/gemini` — alias

### Suggest Links
- None currently defined (`depends_on_skills: []`, `suggest: []`)

### External Tool Integration
| Tool | Used In | Purpose |
|------|---------|---------|
| `gemini` CLI | Section 9 | Headless RESEARCH, self-reviews |
| `mcp__plugin_context7__query-docs` | Section 6 | Doc queries |
| `WebSearch` / `WebFetch` | Section 9 (implied) | External research |

### Handoff Points
- Transcript path resolution via handoff JSON (`console_*_handoff.json`)
- Session chain via `transcript_path` in `resume_snapshot`

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

**Triage Phase**:
- **Reads**: User query (text)
- **Writes**: None
- **Gate**: None (soft classification)

**Routing Phase**:
- **Reads**: Triage classification
- **Writes**: None
- **Gate**: User can override (soft gate)

**Execution Phase (per path)**:
- **Reads**: User query + any file content cited by user
- **Writes**: Output to user
- **Gate**: Source Fidelity Rule (file:line citation or [INFERRED] flag)

**Gemini CLI Phase (Section 9)**:
- **Reads**: `--include-directories` path + prompt
- **Writes**: CLI output to stdout
- **Gate**: Step 0 `gemini --help` verification

### Agent Read Sources
- N/A — this skill does not dispatch parallel agents

### Quality Gates
- **Source Fidelity Gate**: Claims without file:line citation must be marked `[INFERRED]`
- **Fail-Fast Gate**: Gemini CLI unavailable → report immediately

---

## 9. AGENT DISPATCH DEFINITIONS

N/A — ai-gemini does not dispatch agents. It is an LLM-executed skill with Gemini CLI as the only external tool.

---

## 10. FAILURE SCENARIOS

### Failure 1: Gemini Training Data Bias
**Trigger**: User asks RESEARCH question → Gemini responds with training data
**Propagation**: No file:line citation → Source Fidelity Rule violated → output is ungrounded
**Detection**: Self-check (did I cite a file?) or user flags response
**Actual vs Expected**: Gemini "sounds confident" but has no source backing
**Root Cause**: SKILL.md:29 — "Gemini draws from training data unless constrained" — constraint not enforced structurally

### Failure 2: MODEL_CAPACITY_EXHAUSTED Misclassified
**Trigger**: Gemini CLI returns 429 with `MODEL_CAPACITY_EXHAUSTED` reason
**Propagation**: Error message not read → assumed user quota exhaustion → user told to wait
**Detection**: Error table at SKILL.md:209 correctly identifies both types
**Actual vs Expected**: User told to wait when actually server-side transient issue
**Root Cause**: Prior to 1.3.1, all 429s treated as "rate limit, check quota"
**Verified Fix**: SKILL.md:209-210 — split into MODEL_CAPACITY_EXHAUSTED (retry) vs rateLimitExceeded (wait)

### Failure 3: Filesystem Access Assumption Wrong
**Trigger**: `--include-directories` used to scope workspace, but Gemini cannot read filesystem
**Propagation**: Prompt asks to read file → Gemini responds without reading → verification mandate violated silently
**Detection**: Source Fidelity Rule would catch missing citations, but if Gemini doesn't try to read, no citation to flag
**Actual vs Expected**: Verification premise depends on filesystem access being real
**Root Cause**: Unverified assumption — pre-mortem p3.md:2.1 flagged as HIGH

### Failure 4: TDD Enforcement Contradiction
**Trigger**: ENGINEERING path says "TDD cycle prompt" (implies mandatory) but frontmatter says `enforcement: advisory`
**Propagation**: User expects TDD enforcement → skill delivers only soft guidance → user dissatisfaction
**Detection**: skill-audit Lens 8 flagged as PRINCIPLE_ENFORCEMENT_MISMATCH
**Actual vs Expected**: Body implies mandatory, frontmatter says advisory
**Verified Fix**: SKILL.md:152 — added "TDD guidance is advisory only" to Non-Goals

---

## 11. APPENDIX: SAMPLE RUNS / LOGS

### MODEL_CAPACITY_EXHAUSTED Log (2026-04-09)
```
Attempt 1 failed with status 429. Retrying with backoff...
_GaxiosError: [{
  "error": {
    "code": 429,
    "message": "No capacity available for model gemini-3-flash-preview on the server",
    "errors": [{"message": "No capacity available for model gemini-3-flash-preview on the server", "reason": "MODEL_CAPACITY_EXHAUSTED", "domain": "cloudcode-pa.googleapis.com"}],
    "status": "RESOURCE_EXHAUSTED"
  }
}]
```
**Interpretation**: Server-side capacity exhausted, NOT user quota. Action: retry with backoff.

### Error Table (SKILL.md:204-210)
```
| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Read output |
| 134 | OOM / input too large | Switch to `--include-directories` pattern |
| 1 | General error | Check stderr for message |
| Non-zero + "MODEL_CAPACITY_EXHAUSTED" | Server-side capacity exhausted | Retry with backoff — this is transient |
| Non-zero + "rateLimitExceeded" + quota % shown | User quota exhausted | Wait for reset window |
```
