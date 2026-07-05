---
description: Multi-agent adversarial review of any proposal/solution/design/implementation before commitment. Planner → specialists (gate, workflow, + dispatched) → critic → PROCEED/REVISE/BLOCK verdict.
---

# /red-team

User goal: $ARGUMENTS

You are the **Orchestrator** for `/red-team`.

## Mission
Stress-test a proposal / solution / design / implementation / plan before commitment, then produce one refined output: ranked weaknesses, verified findings, concrete fixes, and a single go/no-go verdict.

## When to use
- An important proposal, solution, architecture decision, CLAUDE.md / skill / command edit, hook / gate change, or implementation plan.
- **Not** for routine code review — use `/code-review`.
- **Not** for post-hoc failure imagination as a standalone exercise — use `/pre-mortem` (full 3-phase pipeline) when you want that alone.

## Context rules
- You have the full session transcript and repository via tools.
- Do not ask the user to paste artifacts you can inspect yourself.
- Search the repo and session before drafting.

## Findings handoff (disk-backed)

The orchestrator never holds specialist findings in its own context — only file paths. This keeps the long-lived orchestrator context small; findings load into the critic's ephemeral context instead. (Proven necessary: the adversarial-review family hit token walls under prose-paste and adopted this same disk-backed contract to fix it.)

**run_dir** — generate at the start of every run: `P:/.claude/.artifacts/red-team/{YYYYMMDD-HHMMSS}/`. Create the directory before dispatching specialists. The timestamp makes concurrent runs (same or other terminals) naturally non-colliding.

**Per-specialist path:** `{run_dir}/{specialist-name}.json` (e.g. `{run_dir}/security.json`).

**Findings schema** (each specialist writes this object):
```json
{
  "specialist": "<name>",
  "meta": { "angles_covered": ["..."], "gaps": ["could not assess ..."] },
  "findings": [
    {
      "id": "<SPEC>-<N>",
      "severity": "BLOCK|REVISE|NIT",
      "category": "<tag>",
      "location": "<file:line | doc section | null>",
      "title": "<one line>",
      "detail": "<2-3 sentences: what's wrong, why it matters>",
      "evidence": "<quoted code/tool output/citation — required for BLOCK/REVISE>",
      "confidence": "high|medium|low",
      "fix": "<concrete correction>",
      "claim_type": "existence|static-shape|behavior|non-code"
    }
  ]
}
```
Required: `id, severity, location, title, detail, evidence, fix`. Optional: `category, confidence, claim_type, meta`. `claim_type` tags which verification branch the critic should use (saves re-classification).

## Agent flow

### 1. Planner
Invoke the `red-team-planner` agent.
- Produces: proposal restatement, specialist angles to dispatch, candidate weaknesses, draft next steps.
- **Prospect pass (conditional)** — when the proposal references an external system or resembles a wiki-captured decision, the planner searches `P:/.data/wiki/` first (then the web) and writes `{run_dir}/prospect.md`. Specialists Read it before attacking. The planner decides if it fires; not always-on.

### 2. Specialists
Generate the `run_dir` (see Findings handoff above), create it, then dispatch the angles the Planner identified. Run applicable specialists **in parallel**.

Each specialist dispatch includes: the proposal under review (or pointer to it), the `run_dir`, and the instruction — *"Write your findings to `{run_dir}/<your-name>.json` per the schema in the orchestrator skill. Your response text must contain ONLY the file path — no prose, no findings inline."* If `{run_dir}/prospect.md` exists (planner fired the prospect pass), specialists Read it before attacking and weigh its priors.

Project-local specialists (under `P:/.claude/agents/`). Always-consider first two; dispatch the rest when the Planner identifies the angle:
- `red-team-gate-reviewer` — always-consider. Gates, hooks, matchers, guardrails, calibration.
- `red-team-workflow-reviewer` — always-consider. CLAUDE.md, skills, commands, task-tracking, workflow quality.
- `red-team-security` — data leaks, access control, injection, trust boundaries.
- `red-team-performance` — timeouts, bottlenecks, N+1, races, resource exhaustion.
- `red-team-logic` — off-by-one, inverted conditionals, wrong operators, ambiguous precedence, category overlap.
- `red-team-state` — state isolation, stale-data hazards, cross-run contamination, multi-terminal scoping, concurrency, handoff integrity. Dispatch on any proposal touching persisted artifacts, caches, run dirs, session-scoped behavior, or concurrent terminals.
- `red-team-failure-modes` — "imagine it failed catastrophically, why?" with web research for domain anti-patterns.
- `red-team-plugin` — dispatch on plugin/tool/MCP proposals: manifests, dispatch double-fire, source-vs-cache drift, version-bump/cache hygiene, integration guardrails.
- `red-team-testing` — dispatch on gate/agent/critical-path changes: tests, evals, harnesses, regression + entry-point-launch coverage.

Collect only the path each specialist returns. Do not Read the findings files yourself — that defeats the handoff.

### 3. Critic
Invoke the `red-team-critic` agent. Pass it the `run_dir` — NOT pasted findings. The critic globs `{run_dir}/*.json`, Reads each, aggregates, then runs its existing verify / severity-gate / tiebreaker / verdict logic.
- Verifies findings against the codebase (VERIFIED / UNVERIFIED / NON_REPRODUCIBLE).
- Severity-gates: BLOCK / REVISE / NIT (no count cap).
- Resolves contradictions via the ordered tiebreaker: correctness/security → root-cause → reversible → smaller-diff.
- Emits one verdict: PROCEED / REVISE / BLOCK.

### 4. Synthesis
Produce one final user-visible output **only after** the Critic completes.
- Incorporate all BLOCK issues.
- Incorporate or explicitly resolve every REVISE issue.
- Do not show intermediate drafts unless the user asks.

## ROI frame
`ROI ≈ (debug-time saved) × (recurrence frequency) ÷ (effort to land)`

Qualitative ROI is allowed. Quantitative performance attribution requires actual timing / telemetry / profiling evidence — never invent measurements.

## Final output format

### Proposal restated
- One paragraph.

### Verdict
PROCEED | REVISE | BLOCK

### Verified findings
- BLOCK (all)
- REVISE
- NIT (batched)

### Suppressed
- N CRITICAL findings moved here as NON_REPRODUCIBLE (verification contradicted them). One line each: finding + the contradicting evidence. UNVERIFIED findings are NOT suppressed — they stay in Verified findings, downgraded and flagged `[unverified]`.

### Contradiction resolutions
- Each conflict between specialists + which tiebreaker rule (1–4) decided it.

### Recommended next steps
- Numbered (no cap — list every real step; fewer is fine, never pad). Each: target artifact(s), action, expected impact, validation signal, time-horizon (short-term or long-term), and priority (High / Med / Low).
- Short-term steps address immediate ship/no-ship concerns.
- Long-term steps encode structural refactors or design changes whose ROI comes from reduced future debug-time and recurrence.

### Review note
- One line: the critic verdict + whether revisions were applied.

## Implementation note for the model
- If named agents exist in the environment, call them (preferred).
- If they do not, emulate the same flow with separate internal passes using the same roles — but flag this: single-context emulation tends to soften the critic, because the same context drafted the plan it is now reviewing.

## Adjacent systems (do not duplicate)
- `/code-review` — routine code review (file:line shaped).
- `/pre-mortem` — adaptive adversarial critique, 3-phase (triage+specialist → meta-critique → synthesis). `/red-team` differs by: planner-first pass, explicit proposal / non-code framing, single PROCEED/REVISE/BLOCK verdict, and the ordered tiebreaker at synthesis.
- `/adversarial-review` agent — parallel code review (file:line shaped).
