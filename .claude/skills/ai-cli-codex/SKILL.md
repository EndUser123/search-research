---
name: ai-cli-codex
version: 1.0.0
status: new
description: Codex-powered intelligent task assistant with soft-triage routing — RESEARCH/ENGINEERING/DESIGN/RCA paths via ACG workflow
category: ai-llm
enforcement: strict
triggers:
  - /ai-cli-codex
workflow_steps:
  - step_triage: Classify task type (RESEARCH/ENGINEERING/DESIGN/RCA) from query keywords
  - step_route: Route to appropriate workflow based on triage
  - step_execute: Run Codex CLI with workflow-specific prompt
  - step_analyze: Apply workflow (ACG/TDD/Adversarial/Hypothesis)
  - step_output: Deliver findings with citations, PASS/FAIL, or failure modes
---

# /ai-cli-codex

**Intelligent Codex command:** `/ai-cli-codex` routes tasks to the right workflow using soft triage, then executes via Codex CLI with ACG (Analyze-Challenge-Gap) methodology.

## Soft Triage Routes

| Category | Triggers | Route |
|---------|----------|-------|
| **RESEARCH** | Questions about codebase, architecture, decisions | ACG workflow |
| **ENGINEERING** | Code writing, refactors, bug fixes, tests | TDD cycle + verify pyramid |
| **DESIGN** | Architectural proposals, trade-off analysis | Adversarial review |
| **RCA** | Bug investigation, root cause analysis | 5 Whys + hypothesis ledger |

## Execution Directive

**Step 1:** Classify task type from query keywords:
- write/add/create → ENGINEERING
- why/how does/explain → RESEARCH
- propose/evaluate/trade-off → DESIGN
- fix/debug/trace/failing → RCA

**Step 2:** Route to appropriate workflow prompt

**Step 3:** Run Codex CLI via wrapper:
```bash
pwsh -File P:/packages/cc-skills-ai-cli/scripts/agentic-cli.ps1 -cli "codex" -command "exec [workflow_prompt]" -outputPath "P:/tmp/codex_output.txt"
```

**Step 4:** Read output, apply workflow step (Analyze/Challenge/Gap), deliver findings

**DO NOT:**
- Provide your own analysis instead of running Codex
- Skip the triage step — always classify first
- Mix paths — pick one primary route

---

## Workflow Detail

### RESEARCH → ACG (Analyze-Challenge-Gap)
```
1. Analyze: What are the key insights? What claims are well-supported vs inferred?
2. Challenge: What are the weakest assumptions? What would make this fall apart?
3. Gap: What is missing? What would make this complete?
4. Contradiction check: Do Codex claims match the actual files?
```

### ENGINEERING → TDD Lite
```
1. RED: What test would fail if requirement is not met?
2. GREEN: What minimal code passes that test?
3. VERIFY: Run the test. Report PASS/FAIL — not a score.
```

### DESIGN → Adversarial Review
```
1. Consider: How would this fail under concurrent load?
   Consider: Which assumption is the weakest link?
   Consider: What if network partitions during execution?
2. Present Approach A (recommended) vs Approach B (alternative)
3. What contracts/schemas are preserved or broken?
```

### RCA → Hypothesis Ledger
```
1. Reproduce: Achieve consistent reproduction first
2. List candidate causes, disprove/confirm with evidence
3. 5 Whys: Drill to fundamental system flaw
```

## Source Fidelity Rule

Every factual claim must cite source. Uncited claims → `[UNVERIFIED]`. Claims contradicting files → surface explicitly.

## Citation Format

`[source: file:line]` — e.g., `[source: src/auth.py:42]`
Invented citations (file doesn't exist) → `[BAD-CITATION]` — do not use the claim.

## Binary Assertions

For ENGINEERING: report PASS/FAIL for each check:
- "generated code compiles without error" → PASS/FAIL
- "all generated tests pass" → PASS/FAIL
- "output matches required schema" → PASS/FAIL

No 1-10 scores. Binary outcomes are automatable and stable.

## Verification Pyramid (ENGINEERING)

- **Tier 1 (Unit):** Logic coverage, edge cases
- **Tier 2 (Integration):** Interface contracts, cross-module
- **Tier 3 (E2E):** Full lifecycle, CLI entrypoints

## Codex CLI Invocation

**Headless mode** (default): `codex exec "[prompt]"`

**Wrapper pattern** (for file capture):
```bash
pwsh -File P:/packages/cc-skills-ai-cli/scripts/agentic-cli.ps1 -cli "codex" -command "exec [prompt]" -outputPath "P:/tmp/codex_output.txt"
```

**Model:** Auto-selects best model unless `--model` is specified.

## Quick Reference

| Task Type | Workflow | Key Question |
|-----------|---------|--------------|
| RESEARCH | ACG + contradiction check | What do sources actually say? |
| ENGINEERING | TDD lite + verify pyramid | What test proves this works? |
| DESIGN | Adversarial review | How does this fail? |
| RCA | 5 Whys + hypothesis ledger | What is the fundamental cause? |

## File Reference

- `references/codex-cli.md` — Codex CLI flags, setup, error codes
