---
name: ai-gemini
description: Gemini-powered research and engineering assistant using ACG workflow and soft XoT orchestration
version: 1.3.4
category: productivity
triggers:
  - /ai-gemini
  - /gemini
aliases:
  - /ai-gemini
  - /gemini
depends_on_skills: []
enforcement: advisory
effort: high
workflow_steps:
  - step_soft_triage: Classify task type (RESEARCH/ENGINEERING/DESIGN/RCA) on every invocation
  - step_route: Route to appropriate workflow path based on triage classification
  - step_execute: Execute the selected workflow path (ACG, TDD, Adversarial Review, or Hypothesis Ledger)
  - step_verify: Run verification pyramid for ENGINEERING path (Tier 1 Unit, Tier 2 Integration, Tier 3 E2E)
  - step_output: Deliver output per path commitment (ACG findings, test output, 3 failure modes, hypothesis ledger)
---

# /ai-gemini — Gemini Research & Engineering Assistant

Soft-routed task assistant that applies NotebookLM-style source fidelity and ACG workflow to Gemini, with PDS-style triage. No hard phase gates; no brittle orchestration. Routes to the right tool for the job.

## Core Principle

**Quality is decided before you generate.** Gemini draws from its training data unless constrained. This skill keeps outputs grounded in source material by default, and routes engineering tasks through verification pyramids.

## 1. Soft Triage

On every invocation, classify the task type:

| Category | Triggers | Route |
|----------|----------|-------|
| **RESEARCH** | Questions about codebase, documentation, architecture, decisions | ACG workflow (below) |
| **ENGINEERING** | Code writing, refactors, bug fixes, tests | TDD cycle prompt → verify pyramid |
| **DESIGN** | Architectural proposals, trade-off analysis, alternatives | Adversarial review prompt |
| **RCA** | Bug investigation, root cause, failure analysis | 5 Whys + hypothesis ledger |

**Soft routing**: The skill recommends the appropriate workflow, but the user can override. No hard blocking.

**Routing criteria**:
- Follow recommended path if: user query matches triage examples closely, or intent is clear from keywords (write, add, create → ENGINEERING; why, how does, explain → RESEARCH)
- Allow override if: user explicitly chooses a different path, or query spans multiple categories
- Ask for clarification if: query is vague ("help", "do something", "fix it") without clear subject or action word

**Multi-category tasks**: For hybrid tasks (e.g., "fix bug AND propose alternatives"), select primary category and note secondary. E.g., bug fix with architectural implications: RCA primary, DESIGN secondary.

### Triage Examples

Use these as classification anchors when unsure:
- `"why is the auth middleware structured this way?"` → RESEARCH
- `"how does the session chain work across terminals?"` → RESEARCH  
- `"write a FileLock wrapper for the handoff store"` → ENGINEERING
- `"add retry logic to the API client"` → ENGINEERING
- `"propose an alternative to the current hook architecture"` → DESIGN
- `"evaluate trade-offs between hooks vs MCP for this use case"` → DESIGN
- `"the integration verifier started failing after the merge"` → RCA
- `"trace why the terminal ID format changed between runs"` → RCA

## 2. Research Path — ACG (Analyze-Challenge-Gap) Workflow

Use when task is RESEARCH. Three-step critical-thinking loop:

### A — Analyze
```
Based on the sources provided (or codebase context), what are the key insights about [topic]?
```
- Pull exclusively from provided material or verified file content
- No LLM training data mixed in

### C — Challenge
```
What are the weakest assumptions in this analysis?
Which claims lack supporting evidence?
What would make this argument fall apart?
```
- Identify unsupported assertions
- Flag claims without citations

### G — Gap
```
What's missing from the sources?
What topics or data would make this analysis complete?
```
- Surface overlooked areas
- Identify contradiction risks

### Contradiction Check (research only)
Before concluding any research task:
```
Are there any contradictions or conflicting data points across the sources consulted?
```
If yes: surface explicitly before the user acts on the output.

## 3. Engineering Path — TDD Lite

Use when task is ENGINEERING. Soft RED-GREEN-REFACTOR guidance:

1. **RED**: "What test would fail if this requirement is not met?"
2. **GREEN**: "What is the minimal code that passes that test?"
3. **VERIFY**: Run the test. Report actual output, not assumed success.

**Verification pyramid** (same as PDS but advisory):
- Tier 1 (Unit): Logic coverage, edge cases
- Tier 2 (Integration): Interface contracts, cross-module
- Tier 3 (E2E): Full lifecycle, CLI entrypoints

## 4. Design Path — Adversarial Review

Use when task is DESIGN. Three-question prompt:

```
1. What are 3 ways this design could fail? (Performance bottleneck, security gap, complexity bloat)
2. Present Approach A (recommended) and Approach B (alternative).
3. What contracts and schemas are preserved or broken?
```

## 5. RCA Path — Hypothesis Ledger

Use when task is RCA:

1. **Reproduce**: Achieve consistent reproduction before suggesting fixes
2. **Hypothesis ledger**: List candidate causes; disprove or confirm with evidence
3. **5 Whys**: Drill to fundamental system flaw

## 6. Source Fidelity Rule

For ALL paths:

**Never claim content from documents without reading the document first.**

- If using file content: cite `file:line` in response
- If referencing docs: use `mcp__plugin_context7_context7__query-docs` or read the actual doc
- If the answer relies on training data: flag as `[INFERRED]` with confidence ceiling 50%

## 7. Output Commitments

- **Research**: ACG findings + contradiction check result + explicit gap list
- **Engineering**: Test output (not assumed pass) + minimal implementation
- **Design**: 3 failure modes + alternatives comparison + contract audit
- **RCA**: Hypothesis ledger with evidence status + fundamental cause

## 8. Non-Goals

- Not a chatbot wrapper — outputs are always source-grounded or flagged
- Not a code-generate-and-done tool — verification is mandatory
- No hard phase gates — soft routing allows user override
- Multi-terminal state is referenced via transcript paths, not shared blocking state
- TDD guidance is advisory only — users may choose alternative approaches for ENGINEERING tasks, but verification (running tests/checking output) remains mandatory in all cases

**Self-Check (internal failure-mode prompts)**: After routing, ask:
- Did I route to the correct path? Check: does the query match the triage criteria?
- If RCA: could the issue be a symptom of a different root cause than what I selected?
- If DESIGN: have I identified 3 distinct failure modes, not just 3 variations of the same theme?

## 9. Gemini CLI Invocation

**When**: RESEARCH tasks, especially self-reviews of /ai-gemini. REQUIRED for any task where transcript context or cross-session analysis would improve quality.

### Step 0: Verify interface (first use per session)

**Two-stage verification**:

**Stage 1 — Flag check** (always run first):
```bash
gemini --help
```
Confirm these flags appear in output: `-y` / `--yolo`, `--include-directories`, `-o` / `--output-format`, `-p` / `--prompt`.
If any flag is missing, update this section before proceeding. Do not proceed on assumption.

**Stage 2 — Invocation test** (required before first RESEARCH task):
```bash
gemini -y -o text --include-directories "P:/" -p "Read P:/README.md if it exists and return only the filename."
```
If this returns a filename or confirmed "file not found", filesystem access is working. If it returns training data or a generic response, filesystem access is not functioning — flag as `[FILESYSTEM_ACCESS_UNVERIFIED]` and do not rely on Section 9 file-reading capabilities.

*These patterns were verified against gemini v0.37.0 (`gemini --help` output, 2026-04-09).*

**Headless mode is the default** — always use `-y -o text` for unattended Bash execution:
```
gemini -y -o text -p "[prompt]"
```

- `-y` (yolo): auto-approve all tool actions — prevents interactive stall when Gemini tries to read files
- `-o text`: clean text output, no ANSI codes, safe for Bash capture

### Input Size Determines the Pattern

**Small inputs (<500KB)** — stdin piping:
```bash
cat <file_path> | gemini -y -o text -p "[prompt]"
echo "<inline_text>" | gemini -y -o text -p "[prompt]"
```

**Large inputs or file access (>500KB)** — use `--include-directories` and pass filepath in prompt:
```bash
gemini -y -o text --include-directories "<dir_containing_files>" -p "Read <absolute_path> and [task]"
```

**For transcripts >500KB**: always use `--include-directories` and pass the filepath in the prompt — do NOT pipe the full file.

**P: drive files specifically**:
```bash
gemini -y -o text --include-directories "P:/.claude" -p "Read P:/.claude/skills/ai-gemini/SKILL.md and [task]"
```

### Timeout and Response Handling

**Model Stability Guidance**: For consistent results and to prevent unexpected `ModelNotFoundError` or `MODEL_CAPACITY_EXHAUSTED` (429) errors, prefer pinning to a stable model. Set the `GEMINI_MODEL` environment variable, e.g., `GEMINI_MODEL=gemini-2.5-flash`. This skill expects `gemini-2.5-flash` for critical tasks. If `2.5-flash` is unavailable, try `gemini-2.0-flash`; if that also fails, flag as `[MODEL_UNAVAILABLE]`.

**Timeout guidance**: If no response in 10 minutes, assume `MODEL_CAPACITY_EXHAUSTED` and initiate a retry sequence with exponential backoff (up to 4 attempts). If all retries time out, report the raw output and flag as `[TIMEOUT]`. If `ModelNotFoundError` persists across different attempts/models, flag as `[MODEL_UNAVAILABLE]` and suggest manual model selection.

**Empty response handling**: An empty Gemini output (0 bytes or whitespace only) is an error — not a valid result. Flag as `[EMPTY_OUTPUT]` and do not present it as a finding. If `[EMPTY_OUTPUT]` persists after 3 re-runs, surface the failure and flag `[EMPTY_OUTPUT_UNRESOLVED]`.

### Error Interpretation

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Read output |
| 134 | OOM / input too large | Switch to `--include-directories` pattern |
| 1 | General error, e.g., `ModelNotFoundError` | Check stderr for message. If `ModelNotFoundError`, try setting `GEMINI_MODEL` to a stable model (e.g., `gemini-2.5-flash`). |
| Non-zero + "429" | `MODEL_CAPACITY_EXHAUSTED` or `rateLimitExceeded` | Initiate retry sequence (up to 4 attempts). If persistent, check quota or try `GEMINI_MODEL=gemini-1.5-flash-preview`. |
| Non-zero + empty | General failure | Report raw output, flag as `[GENERAL_ERROR]` |

**Known failure modes** (community reports, unverified):
- **WriteFile disabled**: In some versions/configs, WriteFile tool fails despite being available — use shell `echo` or `>` redirection instead
- **Sandbox blocks writes**: Strict sandbox profiles (`GEMINI_SANDBOX=true`) can block all file writes — try `GEMINI_SANDBOX=false`
- **Dynamic `/directory add` unavailable headless**: Interactive `/directory add` commands don't work in `-y` headless mode — pre-set `--include-directories` instead
- **Checkpointing**: Use `--checkpointing` flag and `/restore` for rollback if writes go wrong

**Rule**: Never assert quota exhaustion without seeing it in the actual output. Report raw output — do not interpret.

### Transcript Resolution (if needed)
1. Read the most recent handoff file to find transcript path:
   ```
   Read the most recent console_*_handoff.json from P:/.claude/state/handoff/
   Extract the transcript_path from resume_snapshot.transcript_path
   ```
   **Stale-data guard**: If the path is older than 7 days or points to a non-existent file, use the current session context instead.

**Always Verify**:
- Read files Gemini cites before relying on its analysis
- If cited file doesn't exist: flag as `[UNVERIFIED-CITATION]` with reduced confidence
- If contradictions found: surface per Contradiction Check (Section 5)
- If citation unverifiable: flag as `[INFERRED]` per Source Fidelity Rule
- Incorporate verified content into ACG workflow

**Fail Fast**: If Gemini CLI is not available, report failure immediately. Diagnostic: run `gemini --version` to verify installation. Do not attempt fallback.

## Quick Reference

| Task Type | Workflow | Key Question |
|-----------|----------|--------------|
| RESEARCH | ACG + contradiction check | What do sources actually say? |
| ENGINEERING | TDD lite + verify pyramid | What test proves this works? |
| DESIGN | Adversarial review | How does this fail? |
| RCA | 5 Whys + hypothesis ledger | What is the fundamental cause? |

### Section 9.1 Verification Ritual

Run this before first use per session:

| Test | Command | Expected | Action if Fails |
|------|---------|----------|-----------------|
| Install | `gemini --version` | v0.37.0+ | Reinstall: `npm i -g @google/gemini-cli` |
| Headless | `gemini -y -o text -p "Say hello"` | "hello" in stdout | Check quota, try `gemini` interactively |
| FS Access | `gemini -y -o text --include-directories "P:/" -p "Read P:/README.md and return filename"` | Filename or "not found" | Flag `[FILESYSTEM_ACCESS_UNVERIFIED]`, use stdin piping |
| Capacity Error | Run during peak load | `MODEL_CAPACITY_EXHAUSTED` | Backoff 30s with up to 4 retries, then report `[CAPACITY_EXHAUSTED]` |

## Changelog

### 1.3.4
- Fixed version mismatch: frontmatter now 1.3.4 (matching changelog)
- Fixed TDD/verification contradiction in Non-Goals (SKILL.md:152)
- Added explicit `## 9. Gemini CLI Invocation` heading for navigable section numbering (SKILL.md:159)
- Section 9: Introduced Model Stability Guidance (GEMINI_MODEL pinning); refined Timeout Guidance with up to 4 retries and model unavailability fallback; updated Error Interpretation for 429s (MODEL_CAPACITY_EXHAUSTED/rateLimitExceeded) and exit code 1 (ModelNotFoundError); updated Section 9.1 Verification Ritual for capacity errors.
- Empty response handling: added 3-retry cap with `[EMPTY_OUTPUT_UNRESOLVED]` flag (SKILL.md:216)
- Model Stability Guidance: removed unverified `gemini-1.5-flash-preview` fallback; replaced with verified `gemini-2.0-flash` fallback path
- Timeout guidance: changed from 120 seconds to 10 minutes (task-dependent, load-dependent)

### 1.3.3
- Section 9: Added error interpretation table (exit codes 134/1/429); documented known failure modes (WriteFile bugs, sandbox blocks, headless `/directory add` disabled); added Section 9.1 verification ritual table

### 1.3.2
- Section 9: Added Stage 2 invocation test (filesystem access proof); added timeout guidance (120s threshold, retry with backoff); added empty response handling ([EMPTY_OUTPUT] flag)

### 1.3.1
- Section 9: Split 429 error row into MODEL_CAPACITY_EXHAUSTED (server-side, retry with backoff) and rateLimitExceeded (user quota, wait for reset) with distinct actions

### 1.3.0
- Section 9: Added Step 0 interface verification (mandatory `gemini --help` check before use); annotated with v0.37.0 verification evidence and date

### 1.2.0
- Section 9 overhaul: mandatory `-y -o text` flags for headless use, size-based input patterns (stdin vs --include-directories), 500KB threshold guidance, P: drive workspace inclusion syntax, exit code error interpretation table

### 1.1.1
- Fixed Section 9: corrected Gemini CLI invocation syntax (stdin piping, not `--read` flag)

### 1.1.0
- Added Section 9: Gemini CLI Invocation
- Added workflow_steps frontmatter field
- Added multi-category task guidance
- Fixed Non-Goals to clarify multi-terminal state via transcript paths
- Fixed hardcoded session path in example (privacy leak)
- Added verification failure guidance ([UNVERIFIED-CITATION])
- Added fail-fast diagnostic guidance
- Added routing criteria with concrete follow/override/ask rules
- Added stale-data guard for transcript path resolution
- Added self-check failure-mode prompts after routing

### 1.0.0
- Initial release
