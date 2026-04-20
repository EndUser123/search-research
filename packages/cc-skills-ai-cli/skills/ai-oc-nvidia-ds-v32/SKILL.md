---
name: ai-oc-nvidia-ds-v32
description: OpenCode-powered research and engineering assistant using ACG workflow and DeepSeek v3.2 via NVIDIA NGC
version: 1.0.0
category: productivity
triggers:
  - /ai-oc-nvidia-ds-v32
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

# /ai-oc-nvidia-ds-v32 — OpenCode + DeepSeek v3.2 via NVIDIA NGC

Soft-routed task assistant that applies NotebookLM-style source fidelity and ACG workflow to OpenCode with the DeepSeek v3.2 model via NVIDIA NGC, with PDS-style triage. No hard phase gates; no brittle orchestration. Routes to the right tool for the job.

## Core Principle

**Quality is decided before you generate.** DeepSeek v3.2 draws from its training data unless constrained. This skill keeps outputs grounded in source material by default, and routes engineering tasks through verification pyramids.

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

Use when task is RESEARCH. The ACG loop is MY cognitive process — OpenCode provides the raw material in ONE call.

### Step 1 — Call OpenCode once (get raw analysis)
```bash
opencode run "[prompt]" --model nvidia/deepseek-ai/deepseek-v3.2 --format json 2>&1
```
- Pull the raw analysis from OpenCode
- Do NOT run multiple OpenCode calls for each ACG phase — ACG is what YOU do with the material
- One OpenCode call, then apply Steps 2-4 yourself

### Step 2 — Analyze (my cognition)
```
Based on the OpenCode output, what are the key insights?
What claims are well-supported vs. inferred?
```
- Distill what OpenCode said into structured findings
- Flag uncited claims as `[UNVERIFIED]`

### Step 3 — Challenge (my cognition)
```
What are the weakest assumptions?
What would make this argument fall apart?
What gaps exist between stated design and actual implementation?
```
- Identify unsupported assertions
- Cross-check against file:line citations you can verify

### Step 4 — Gap (my cognition)
```
What's missing from the OpenCode analysis?
What would make this analysis complete?
```
- Surface overlooked areas
- Identify contradiction risks

### Contradiction Check (research only)
Before concluding any research task:
```
Are there any contradictions between what OpenCode reported and what the files actually show?
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
- If referencing docs: read the actual doc first
- If the answer relies on training data: flag as `[INFERRED]` with confidence ceiling 50%

## 7. Output Commitments

- **Research**: RNS-formatted findings with health score, domain-grouped actions, file:line citations
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

## 9. OpenCode CLI Invocation

**When**: RESEARCH tasks, especially self-reviews of /ai-oc-nvidia-ds-v32. REQUIRED for any task where transcript context or cross-session analysis would improve quality.

**CLI**: `opencode` (in PATH at `C:\Users\brsth\AppData\Roaming\npm\opencode.cmd`)

### Step 0: Verify interface (first use per session)

**Stage 1 — Flag check**:
```bash
opencode --help
```
Confirm these flags appear in output: `run`, `--model`, `--format`, `--prompt`.

**Stage 2 — Invocation test** (required before first RESEARCH task):
```bash
opencode run "Say hello" --model nvidia/deepseek-ai/deepseek-v3.2 --format json
```
If this returns a response, OpenCode CLI is working. If it returns an error or empty output, flag as `[INVOCATION_FAILED]` and investigate.

### Orchestrator Workflow

When this skill is invoked:

1. **Invoke via wrapper** — captures CLI output to a file:
   ```bash
   pwsh -File P:/packages/cc-skills-ai-cli/skills/ai-cli-codex/scripts/agentic-cli.ps1 -cli "opencode" -command "run [your prompt] --model nvidia/deepseek-ai/deepseek-v3.2 --format json" -outputPath "P:/tmp/opencode_output.json"
   ```
   Replace `[your prompt]` with the task description from the user's request.

2. **Read the output file** — parse JSONL and extract text content:
   - The file contains JSONL with `{"type":"text","text":"..."}` events
   - Extract the `text` field from each event and concatenate

3. **Apply ACG workflow** to the extracted text:
   - **Analyze**: What are the key insights? What claims are well-supported vs. inferred?
   - **Challenge**: What are the weakest assumptions? What would make this argument fall apart?
   - **Gap**: What is missing? What would make this analysis complete?

4. **Deliver the final result** — present only the ACG findings, not the raw CLI output.

### Input Patterns

**Small inputs (<500KB)** — inline prompt:
```
pwsh -File P:/packages/cc-skills-ai-cli/skills/ai-cli-codex/scripts/agentic-cli.ps1 -cli "opencode" -command "run Analyze P:/path/to/file.py --model nvidia/deepseek-ai/deepseek-v3.2 --format json" -outputPath "P:/tmp/opencode_output.json"
```

**Large inputs (>500KB)** — pass filepath in prompt:
```
pwsh -File P:/packages/cc-skills-ai-cli/skills/ai-cli-codex/scripts/agentic-cli.ps1 -cli "opencode" -command "run Read P:/path/to/file.md --model nvidia/deepseek-ai/deepseek-v3.2 --format json" -outputPath "P:/tmp/opencode_output.json"
```

### Timeout and Response Handling

**Timeout guidance**: If no response in 10 minutes, flag as `[TIMEOUT]` and report the failure.

**Empty response handling**: An empty output file (0 bytes or whitespace only) is an error — not a valid result. Flag as `[EMPTY_OUTPUT]` and do not present it as a finding. If `[EMPTY_OUTPUT]` persists after 2 re-runs, surface the failure and flag `[EMPTY_OUTPUT_UNRESOLVED]`.

### Error Interpretation

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Read output file at returned path |
| Non-zero | General error | Check stderr for message |

**Fail Fast**: If OpenCode CLI is not available, report failure immediately. Diagnostic: run `opencode --version` to verify installation. Do not attempt fallback.

## Quick Reference

| Task Type | Workflow | Key Question |
|-----------|----------|--------------|
| RESEARCH | ACG + contradiction check | What do sources actually say? |
| ENGINEERING | TDD lite + verify pyramid | What test proves this works? |
| DESIGN | Adversarial review | How does this fail? |
| RCA | 5 Whys + hypothesis ledger | What is the fundamental cause? |

## Changelog

### 1.0.0
- Initial release (adapted from /ai-oc-terminus)
- OpenCode CLI uses `opencode run` for headless mode
- Model: `nvidia/deepseek-ai/deepseek-v3.2` via NVIDIA NGC
- Ranked #1 in NVIDIA model benchmark (2026-04-10): inline code delivery, fast, parses cleanly from JSON output
- Benchmarks: palindrome ✓, apple math ✓, 8-ball puzzle ✓ (information theory reasoning), PriorityQueue ✓ (inline code)
