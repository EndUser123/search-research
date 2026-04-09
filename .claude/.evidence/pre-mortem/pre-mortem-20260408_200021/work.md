/ai-gemini skill review

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

## 2. Research Path — ACG Workflow

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
- No multi-terminal blocking — all state is advisory only

## 9. Gemini CLI Invocation

**When**: RESEARCH tasks where you need richer analysis than current context provides.

**How**: Invoke Gemini CLI via Bash tool. Pass:
- Session transcript path (Gemini can read it directly)
- Any other filepaths you want it to have access to
- A permissive prompt that lets Gemini decide what to search

```
!gemini --read <session_transcript_path> [optional additional filepaths] [permissive prompt]
```

**Prompt Style**: Be permissive — trust Gemini to search for what it needs:
- "Analyze [topic]. Search for relevant files, docs, or prior discussions as needed."
- "Read the session transcript and prior discussions if relevant."
- Don't over-constrain — let Gemini decide what context to use.

**Example**:
1. First resolve the transcript path via `/search "session chain"` or by reading `P:/packages/handoff/.claude/state/handoff/*.json` to find `resume_snapshot.transcript_path`
2. Then invoke: `!gemini --read <actual_transcript_path> [optional additional filepaths] [permissive prompt]`

Example: `!gemini --read C:\Users\brsth\.claude\projects\P--\4e23db8a-a30d-48ba-9bb7-93c0a383daa0.jsonl P:/packages/auth "Analyze the auth middleware architecture. Search for relevant code, docs, or prior discussions. Cite specific lines when useful."`

**Always Verify**:
- Read files Gemini cites before relying on its analysis
- Gemini has filesystem access — it can find and read files directly
- Do not assume Gemini's citations are accurate without verification
- Incorporate verified content into ACG workflow

**Fail Fast**: If Gemini CLI is not available, report failure immediately. Do not attempt fallback.

## Quick Reference

| Task Type | Workflow | Key Question |
|-----------|----------|--------------|
| RESEARCH | ACG + contradiction check | What do sources actually say? |
| ENGINEERING | TDD lite + verify pyramid | What test proves this works? |
| DESIGN | Adversarial review | How does this fail? |
| RCA | 5 Whys + hypothesis ledger | What is the fundamental cause? |
