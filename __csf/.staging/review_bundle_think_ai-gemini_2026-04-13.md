# Review Bundle: /think + /ai-gemini Skills

**Generated**: 2026-04-13
**Scope**: Composite bundle — two related reasoning/research skills
**File Count**: 2 SKILL.md files, 5 incidental state files (intentional ignore)
**Execution Mode**: Single-agent (2 files, both are documentation)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-13
- **Scope**: `/think` and `/ai-gemini` skills
- **File Count**: 2 SKILL.md files
- **Execution Mode**: single-agent

### Domain & Purpose

`/think` and `/ai-gemini` are companion reasoning skills in the Claude Code skill ecosystem. `/think` provides adaptive reasoning depth selection (from `/truth` through `/sequential-thinking` to `/think` itself) with an internal critique-refine loop. `/ai-gemini` provides Gemini CLI-backed research and engineering assistance using an ACG (Analyze-Challenge-Gap) workflow with soft XoT orchestration.

Both skills operate in the "advisory" layer — they assist reasoning and analysis but do not directly modify hooks, skills, or the Claude Code runtime.

### Scale Metrics
- `/think` SKILL.md: 236 lines (v2.8.0 — added Claim Status + Validation Response Shape + Investigation Mode additions)
- `/ai-gemini` SKILL.md: 361 lines (v1.3.7)
- Both are **EXECUTION-type skills** — they delegate to external tools (Gemini CLI) or internal reasoning loops

### Environment
- **OS**: Windows 11 Pro (bash shell via Git Bash/WSL)
- **Primary language**: English
- **Framework**: Claude Code skill system (plugin structure via `.claude/skills/`)
- **Package managers**: npm (for Gemini CLI `@google/gemini-cli`)
- **Key external service**: Google Gemini API (via `gemini` CLI)

---

## 2. ARCHITECTURE OVERVIEW

### Skill Relationship

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ /think                                              │
│ Adaptive reasoning depth gate                       │
│ ────────────────────────────────────────────────── │
│ Modes:                                              │
│   • Evidence-audit (verify before claiming)         │
│   • Investigation (hypothesis + discriminating test)│
│   • Decision-tree (5D scaffold for SDLC decisions)    │
│   • Open-ended (3-branch critique before answer)   │
│                                                      │
│ Escalates to challenger agents:                    │
│   • /codex  → code, repo, debugging                 │
│   • /ai-gemini → broad framing, long-context       │
│   • /ai-qwen → diversity/second opinion            │
└─────────────────────────────────────────────────────┘
    │
    │ (when /ai-gemini is the challenger)
    ▼
┌─────────────────────────────────────────────────────┐
│ /ai-gemini                                           │
│ Gemini CLI orchestrator                             │
│ ────────────────────────────────────────────────── │
│ Soft Triage (4 categories):                        │
│   • RESEARCH → ACG workflow                        │
│   • ENGINEERING → TDD lite + verify pyramid        │
│   • DESIGN → adversarial review (3 failure modes) │
│   • RCA → 5 Whys + hypothesis ledger              │
│                                                      │
│ Execution: Bash → gemini CLI wrapper               │
│   • Wrapper: pwsh -File P:/scripts/agentic-cli.ps1 │
│   • Output: captured to file, then ACG applied     │
└─────────────────────────────────────────────────────┘
```

### Entry Points
- `/think` — invoked directly, no external tool dependency
- `/ai-gemini` — invoked directly, spawns `gemini` CLI via PowerShell wrapper

---

## 3. EXECUTION AND DATA FLOW

### /think Execution Flow

1. **Classify prompt type** (open-ended, decision, investigation, evidence query)
2. **Select depth tier**: `/truth` → evidence-audit → `/decision-tree` → `/sequential-thinking` → `/think`
3. **Internal loop**: Generate first answer → critique once → refine
4. **External challenger**: If uncertainty remains, suggest `/codex`, `/ai-gemini`, or `/ai-qwen`
5. **Output**: Compact recommendation with tradeoffs, evidence citation, reversibility note

**No external tool calls.** Pure reasoning loop.

### /ai-gemini Execution Flow

1. **Soft triage** → classify as RESEARCH/ENGINEERING/DESIGN/RCA
2. **Route** → workflow path based on triage
3. **Execute** via Gemini CLI wrapper:
   ```bash
   pwsh -File P:/scripts/agentic-cli.ps1 -cli "gemini" -command "-y -o text -p [prompt]" -outputPath "P:/tmp/gemini_output.txt"
   ```
4. **Read output file**
5. **Apply ACG workflow** (for RESEARCH): Analyze → Challenge → Gap → Contradiction check
6. **Deliver** per path commitment

**Gemini CLI Verification** (mandatory per session, before first use):
- Stage 1: `gemini --help` → verify `-y`, `--include-directories`, `-o`, `-p` flags
- Stage 2: `gemini -y -o text --include-directories "P:/" -p "Read P:/README.md if it exists and return only the filename."` → verify filesystem access

---

## 4. COMPONENT INVENTORY

### Core Logic

#### `/think` SKILL.md (`P:/.claude/skills/think/SKILL.md`)
- **Responsibility**: Adaptive reasoning depth gate — select right reasoning mode for prompt
- **Key functions**: Branch selection, depth ladder, evidence-audit loop, decision-tree scaffold, reasoning frames
- **Claim Status** (SKILL.md:73-81): New explicit labeling for ideas not yet verified — `Verified` (direct evidence), `Inferred` (reasonable from verified evidence), `Unproven` (hypothesis/guess). Separates unverified ideas from settled recommendation.
- **Validation Response Shape** (SKILL.md:84-89): Ordered response format — verified facts → inferred ideas → unproven/hypotheses → next validation step. Keeps categories separate rather than merged.
- **Investigation Mode additions**: Recommends `/search`, `/research`, or `/all` when they would materially improve confidence, rather than guessing.
- **Output contract**: Problem statement, depth tier, recommendation, tradeoffs, evidence step, reversibility note
- **Known limitations**: No external verification; relies on Claude's reasoning only

#### `/ai-gemini` SKILL.md (`P:/.claude/skills/ai-gemini/SKILL.md`)
- **Responsibility**: Gemini CLI orchestration for RESEARCH/ENGINEERING/DESIGN/RCA tasks
- **Key functions**: Soft triage, ACG workflow, TDD lite, adversarial review, hypothesis ledger
- **Output**: Path-dependent (ACG findings, test output, failure modes, hypothesis ledger)
- **Known limitations**:
  - Gemini CLI may return `[MODEL_CAPACITY_EXHAUSTED]` (429)
  - Empty output (0 bytes) requires 3 retries before `[EMPTY_OUTPUT_UNRESOLVED]`
  - `gemini-1.5-flash-preview` fallback is unverified; `gemini-2.5-flash` is primary model

### Utilities

| Component | Path | Responsibility |
|-----------|------|----------------|
| `agentic-cli.ps1` | `P:/scripts/agentic-cli.ps1` | PowerShell wrapper that captures Gemini CLI output to file |

### Configuration

| Component | Path | Responsibility |
|-----------|------|----------------|
| `gemini_model` env var | Shell env | **Deprecated** — use `-m` flag instead |
| `-m gemini-2.5-flash` | CLI flag | Primary model pin (reliable across shell sessions) |
| `-m gemini-2.0-flash` | CLI flag | Fallback model |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
- **Soft routing**: `/ai-gemini` recommends a path but allows user override — no hard blocking
- **Source fidelity**: Gemini must cite actual files; claims without citations flagged `[UNVERIFIED]`
- **Evidence-first**: `/think` requires verification before claiming repo state
- **Binary assertions**: ENGINEERING path uses PASS/FAIL checks, not 1-10 scores

### Technology Constraints
- **Gemini CLI required**: `/ai-gemini` will not function without `@google/gemini-cli` npm package
- **Model stability**: Use `-m` flag, not `GEMINI_MODEL` env var (env var may not persist across sessions)
- **500KB threshold**: Transcripts/files >500KB must use `--include-directories` pattern, not stdin piping

### Things That Must NOT Change
- `/ai-gemini` must read files cited before relying on analysis (Source Fidelity Rule)
- Gemini CLI invocation must use `-y -o text` flags for headless operation
- Evidence claims must cite `file:line` format

---

## 6. KNOWN ISSUES

| Issue | Impact | Workaround |
|-------|--------|------------|
| `MODEL_CAPACITY_EXHAUSTED` (429) on Gemini API | RESEARCH tasks fail mid-run | Retry with backoff (up to 4 attempts); fallback to `gemini-2.0-flash` |
| `[EMPTY_OUTPUT]` (0 bytes from Gemini) | Invalid result treated as success | Retry up to 3 times; flag `[EMPTY_OUTPUT_UNRESOLVED]` if persistent |
| `gemini-1.5-flash-preview` unverified | Model selection guidance may be wrong | Use `gemini-2.5-flash` (verified v0.37.0) or `gemini-2.0-flash` |
| `GEMINI_MODEL` env var unreliable | Model not pinned across shell sessions | Use `-m` flag explicitly on every invocation |
| `[BAD-CITATION]` (invented file:line) | False claims presented as fact | Gemini must cite existing files; invented citations flagged and discarded |

---

## 7. INTEGRATION POINTS

### /think Escalation Targets
| Challenger | When to use |
|-----------|-------------|
| `/codex` | Code, repo behavior, implementation detail, debugging, refactors, architecture |
| `/ai-gemini` | Broad framing, long-context critique, creative alternatives |
| `/ai-qwen` | Model diversity, fresh ranking when branches are close |

### /ai-gemini External Tool
| Tool | Purpose |
|------|---------|
| `gemini` CLI (`@google/gemini-cli`) | Research and engineering analysis via Gemini model |
| `pwsh -File P:/scripts/agentic-cli.ps1` | Output capture wrapper for headless execution |
| `mcp__plugin_context7_context7__query-docs` | Optional doc lookup for RESEARCH path |

---

## 8. INPUT/OUTPUT CONTRACT

### /think

| Phase | Reads | Writes | Constraint |
|-------|-------|--------|------------|
| Invocation | User prompt | N/A | Prompt text is sole input |
| Reasoning loop | Internal reasoning state | Recommendation | Internal only, no external reads |
| Challenger suggestion | N/A | Challenger recommendation | Advisory only |

### /ai-gemini

| Phase | Reads | Writes | Constraint |
|-------|-------|--------|------------|
| Soft triage | User prompt | Route recommendation | Soft (user can override) |
| Gemini invocation | `P:/scripts/agentic-cli.ps1` + prompt | `P:/tmp/gemini_output.txt` | Must capture stdout |
| ACG apply | `P:/tmp/gemini_output.txt` | ACG findings | Post-process only |
| Final output | ACG findings | Structured response per path | Deliverable is path-dependent |

**Quality gate**: No post-completion gate. Skill is advisory.

---

## 9. AGENT DISPATCH DEFINITIONS

Neither skill dispatches parallel agents. `/think` is a pure reasoning loop. `/ai-gemini` invokes the Gemini CLI as a Bash subprocess (serial, not parallel).

### /think — No Agent Dispatch
This skill does not dispatch subagents.

### /ai-gemini — Serial Bash Invocation

| Property | Value |
|----------|-------|
| **Agent type** | Bash subprocess (via `pwsh -File`) |
| **Role** | RESEARCH/ENGINEERING/DESIGN/RCA analysis via Gemini |
| **Prompt excerpt** | `gemini -y -o text -m gemini-2.5-flash -p "[user task]"` |
| **What it reads** | User task from prompt + optionally files via `--include-directories` |
| **Output file** | `P:/tmp/gemini_output.txt` (captured via wrapper) |
| **Dispatch order** | Serial (Bash blocks until Gemini returns) |

---

## 10. FAILURE SCENARIOS

### Failure 1: Gemini MODEL_CAPACITY_EXHAUSTED mid-research

**Trigger**: `gemini -y -o text -p "analyze X"` → exit code 429
**Propagation**: Bash command fails → output file empty → retry attempted
**Detection**: Exit code 1 + "429" in stderr → retry with backoff
**Actual vs expected**: Expected analysis, got rate limit error
**Root cause**: Gemini API quota exhaustion
**Fix applied**: SKILL.md:249 — retry with exponential backoff (up to 4 attempts), then flag `[TIMEOUT]`

### Failure 2: Empty Gemini output (0 bytes)

**Trigger**: `gemini` returns 0-byte stdout
**Propagation**: Output file exists but is empty → treated as valid result
**Detection**: Size check on output file before reading
**Actual vs expected**: Expected content, got empty file
**Root cause**: Gemini model crash or output truncation
**Fix applied**: SKILL.md:251 — flag `[EMPTY_OUTPUT]`, retry up to 3 times, then `[EMPTY_OUTPUT_UNRESOLVED]`

### Failure 3: Invented citation (BAD-CITATION)

**Trigger**: Gemini cites `file:line` that does not exist
**Propagation**: Analysis appears sourced → user acts on false claim
**Detection**: Verification step (read cited file) fails
**Actual vs expected**: Cited content does not exist at claimed location
**Root cause**: Gemini hallucinating citations from training data
**Fix applied**: SKILL.md:102 — flag `[BAD-CITATION]`, discard the claim

### Failure 4: Model not found (ModelNotFoundError)

**Trigger**: `gemini -y -o text -p "X"` → exit code 1 + `ModelNotFoundError`
**Propagation**: CLI fails → SKILL.md:259 → try `-m gemini-2.5-flash` flag explicitly
**Detection**: stderr message contains `ModelNotFoundError`
**Actual vs expected**: Default model unavailable
**Fix applied**: SKILL.md:240 — explicit `-m` flag overrides env var; `gemini-2.0-flash` fallback

### Failure 5: /think premature closure (first adequate answer)

**Trigger**: `/think` answers without internal critique on ambiguous/high-stakes prompt
**Propagation**: Weak recommendation accepted without alternative branches considered
**Detection**: Prompt is broad/ambiguous → depth ladder requires escalation to deeper tier
**Actual vs expected**: User gets shallow answer on complex problem
**Fix applied**: SKILL.md:39-46 — 3-branch pattern (creative/skeptical/pragmatic) required for open-ended prompts; SKILL.md:169 — "do not recommend first answer without challenging it once"

---

## 11. APPENDIX: CHANGELOG HIGHLIGHTS

### /think (v2.8.0)
- v2.8.0: **Claim Status** — explicit `Verified`/`Inferred`/`Unproven` labeling for unverified ideas; separates from settled recommendation
- v2.8.0: **Validation Response Shape** — ordered format (verified → inferred → unproven → next validation step)
- v2.8.0: **Reasoning Frames** — situation-based frame selection matrix (decision matrix, tree search, causal graph, pre-mortem, challenger debate)
- v2.8.0: External challenger policy with domain-based escalations (`/codex`, `/ai-gemini`, `/ai-qwen`)
- v2.8.0: Investigation mode recommends `/search`/`/research`/`/all` when they would improve confidence
- v2.7.x: Evidence-audit mode formalized, `/truth-av` deprecated

### /ai-gemini (v1.3.7)
- v1.3.7: Model stability via `-m` flag (SKILL.md:228)
- v1.3.6: Citation enforcement (SKILL.md:98-102)
- v1.3.5: Binary assertions for ENGINEERING path
- v1.3.4: Section 9 overhaul with error interpretation, timeout guidance
- v1.3.0: Step 0 interface verification (mandatory `gemini --help` check)
- v1.2.0: `-y -o text` flags for headless, 500KB threshold, P: drive syntax

---

*Bundle generated by `/review_bundle` skill — 2026-04-13*
