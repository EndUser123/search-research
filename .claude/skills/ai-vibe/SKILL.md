---
name: ai-vibe
description: Vibe-powered research and engineering assistant using ACG workflow and soft XoT orchestration
version: 1.0.0
category: productivity
triggers:
  - /ai-vibe
  - /vibe
aliases:
  - /ai-vibe
  - /vibe
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

# /ai-vibe — Vibe Research & Engineering Assistant

Soft-routed task assistant that applies NotebookLM-style source fidelity and ACG workflow to Vibe, with PDS-style triage. No hard phase gates; no brittle orchestration. Routes to the right tool for the job.

## Core Principle

**Quality is decided before you generate.** Vibe draws from its training data unless constrained. This skill keeps outputs grounded in source material by default, and routes engineering tasks through verification pyramids.

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

### Citation Enforcement
Every factual claim must cite its source:
- Format: `[source: file:line]` after each claim
- Uncited claims: flag as `[UNVERIFIED]`
- Invented citations (file doesn't exist): flag as `[BAD-CITATION]` and do not use the claim
- Flag claims with single source as `[LOW-CONFIDENCE]`; multiple independent sources increase confidence

## 3. Engineering Path — TDD Lite

Use when task is ENGINEERING. Soft RED-GREEN-REFACTOR guidance:

1. **RED**: "What test would fail if this requirement is not met?"
2. **GREEN**: "What is the minimal code that passes that test?"
3. **VERIFY**: Run the test. Report actual output, not assumed success.

**Binary Assertions**: For each output, define objective pass/fail checks:
- "generated code compiles without error" → PASS/FAIL
- "all generated tests pass" → PASS/FAIL
- "output matches the required schema" → PASS/FAIL
Report each assertion as PASS or FAIL — not a 1-10 score. Binary outcomes are automatable, composable, debuggable, and stable.

**Verification pyramid** (same as PDS but advisory):
- Tier 1 (Unit): Logic coverage, edge cases
- Tier 2 (Integration): Interface contracts, cross-module
- Tier 3 (E2E): Full lifecycle, CLI entrypoints

## 4. Design Path — Adversarial Review

Use when task is DESIGN. Three-question prompt with rhetorical framing:

```
1. Consider: How would this design fail under concurrent load?
   Consider: Which assumption is the weakest link in this design?
   Consider: What happens when the network is partitioned during execution?
2. Present Approach A (recommended) and Approach B (alternative).
3. What contracts and schemas are preserved or broken?
```
Rhetorical questions produce deeper investigation than direct instructions — the implementer examines the surrounding context rather than making a mechanical patch.

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

## 9. Vibe CLI Invocation

**When**: RESEARCH tasks, especially self-reviews of /ai-vibe. REQUIRED for any task where transcript context or cross-session analysis would improve quality.

### Step 0: Verify interface (first use per session)

**Two-stage verification**:

**Stage 1 — Flag check** (always run first):
```bash
vibe --help
```
Confirm these flags appear in output: `-p` / `--prompt`, `--output`.
If any flag is missing, update this section before proceeding. Do not proceed on assumption.

**Stage 2 — Invocation test** (required before first RESEARCH task):
```bash
vibe -p "Say hello"
```
If this returns a response, Vibe CLI is working. If it returns an error or empty output, flag as `[INVOCATION_FAILED]` and investigate.

*These patterns were verified against Vibe CLI (vibe --help output, 2026-04-09).*

**Headless mode is the default** — always use `-p` for unattended Bash execution:
```
vibe -p "[prompt]"
```

- `-p` (prompt): Run in programmatic mode — send prompt and exit
- `--output {text,json,streaming}`: Output format selection

### Input Size Determines the Pattern

**Small inputs (<500KB)** — stdin piping:
```bash
cat <file_path> | vibe -p "[prompt]"
echo "<inline_text>" | vibe -p "[prompt]"
```

**Large inputs (>500KB)** — use file reference in prompt:
```bash
vibe -p "Read <absolute_path> and [task]"
```

### Timeout and Response Handling

**Timeout guidance**: If no response in 5 minutes, flag as `[TIMEOUT]` and report the failure.

**Empty response handling**: An empty Vibe output (0 bytes or whitespace only) is an error — not a valid result. Flag as `[EMPTY_OUTPUT]` and do not present it as a finding. If `[EMPTY_OUTPUT]` persists after 2 re-runs, surface the failure and flag `[EMPTY_OUTPUT_UNRESOLVED]`.

### Error Interpretation

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Read output |
| 1 | General error | Check stderr for message |
| Non-zero + empty | General failure | Report raw output, flag as `[GENERAL_ERROR]` |

**Fail Fast**: If Vibe CLI is not available, report failure immediately. Diagnostic: run `vibe --version` to verify installation. Do not attempt fallback.

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
| Install | `vibe --version` | Version number | Reinstall: check Vibe documentation |
| Headless | `vibe -p "Say hello"` | Response in stdout | Check installation, try `vibe` interactively |
| Output Format | `vibe -p "Say hello" --output text` | Text output | Flag `[OUTPUT_FORMAT_ISSUE]` |

## Changelog

### 1.0.0
- Initial release (adapted from ai-gemini SKILL.md)
- Vibe CLI uses `-p` for programmatic mode, no yolo flag needed
- No model selection flag (unlike Gemini which has `-m`)
- No filesystem access capabilities (unlike Gemini with `--include-directories`)
