---
description: "Multi-agent adversarial review of any proposal/solution/design/implementation before commitment. Modes: default (planner → specialists → critic → PROCEED/REVISE/BLOCK), pre-mortem (3-phase adaptive critique + Health Score + RNS + blinded consumer review), adversarial (external-LLM harness divergence for B-class blind spots). Trigger phrases: 'red-team this', 'stress-test this proposal', 'pre-mortem', 'adversarial review'. Absorbs /pre-mortem + /adv-review."
---

# /red-team

User goal: $ARGUMENTS

You are the **Orchestrator** for `/red-team`.

## Mission
Stress-test a proposal / solution / design / implementation / plan before commitment, then produce one refined output: ranked weaknesses, verified findings, concrete fixes, and a single go/no-go verdict.

## When to use
- An important proposal, solution, architecture decision, CLAUDE.md / skill / command edit, hook / gate change, or implementation plan.
- **Not** for routine code review — use `/code-review`.

## Modes

`/red-team` is one entry point with three review depths. Pick by what the user pointed at.

| Mode | Invocation | When | What it does |
|---|---|---|---|
| **default** | `/red-team <proposal>` | An important proposal/design/implementation before commitment | Planner → specialists → critic → PROCEED/REVISE/BLOCK. The full flow below. |
| **pre-mortem** | `/red-team pre-mortem <target>` (or `/pre-mortem`) | Post-hoc failure imagination as a standalone exercise, or a target needing the 3-phase adaptive pipeline + blinded consumer-contract review | Triage + specialist dispatch → cross-agent meta-critique → synthesis, with Health Score (0–100) + RNS-format output + the "0 — Do ALL" execution directive. Absorbs `/pre-mortem`. |
| **adversarial** | `/red-team adversarial <response>` (or `/adv-review`) | B-class reliability — confident/architectural/public-facing responses needing external-LLM divergence check | Dispatch to N external harnesses (agy / glm-5.2 / MiniMax-M3 / kimi-k2.7-code) in parallel, surface divergences, emit per-harness verdicts + divergence synthesis. Calibration mode (`--cases <corpus>`) runs the bad-thinking corpus. Absorbs `/adv-review`. This is also the backend for `/improve external-second-opinion`. |

**The unifying rule across all modes:** every finding flows through the disk-backed findings schema (`{run_dir}/{specialist}.json`) and the critic's verify / severity-gate / tiebreaker / verdict logic. No mode bypasses the gate. The difference is *what attack pattern seeds the findings*: default uses planner-first specialist dispatch, pre-mortem uses the 3-phase adaptive pipeline with blinded consumer review, adversarial uses external-LLM divergence.

**Engines stay canonical.** `/pre-mortem`'s 3-phase pipeline + references/phases/ + `__lib/premortem_io.py` + `.codex/` + `.pi/` adapters remain at `cc-skills-sdlc/skills/pre-mortem/`. `/adv-review`'s harness roster + verdict schema remain at `cc-skills-ai-api/skills/adv-review/`. `/red-team` routes to them; it does not vendor.

## Context rules
- You have the full session transcript and repository via tools.
- Do not ask the user to paste artifacts you can inspect yourself.
- Search the repo and session before drafting.

## Findings handoff (disk-backed)

The orchestrator never holds specialist findings in its own context — only file paths. This keeps the long-lived orchestrator context small; findings load into the critic's ephemeral context instead. (Proven necessary: the adversarial-review family hit token walls under prose-paste and adopted this same disk-backed contract to fix it.)

**run_dir** — generate at the start of every run: `P:/.claude/.artifacts/{session_id}/red-team/{YYYYMMDD-HHMMSS}/`. Create the directory before dispatching specialists. Use the **full session_id** (the runtime session UUID from `$CLAUDE_SESSION_ID` or the transcript filename stem) — NOT `terminal_id`/`$WT_SESSION`, which is shared across concurrent sessions in one Windows Terminal. The `session_id` segment makes concurrent runs in the same terminal non-colliding; the timestamp orders runs within a session. (Deviates from the monorepo's `{terminal_id}/{skill_name}/` convention deliberately — terminal_id collides; see plugin CLAUDE.md.)

**Per-specialist path:** `{run_dir}/{specialist-name}.json` (e.g. `{run_dir}/security.json`).

**Findings schema** (each specialist writes this object):
```json
{
  "specialist": "<name>",
  "writer_session": "<session_id — proves which session wrote this>",
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
Required: `id, severity, location, title, detail, evidence, fix, writer_session`. Optional: `category, confidence, claim_type, meta`. `claim_type` tags which verification branch the critic should use (saves re-classification). Schema is codified in `__lib/findings_schema.py` (unit-tested).

## Agent flow

### 1. Planner
Invoke the `red-team-planner` agent.
- Produces: proposal restatement, specialist angles to dispatch, candidate weaknesses, draft next steps.
- **Prospect pass (conditional)** — when the proposal references an external system or resembles a wiki-captured decision, the planner searches `P:/.data/wiki/` first (then the web) and writes `{run_dir}/prospect.md`. Specialists Read it before attacking. The planner decides if it fires; not always-on.

### 2. Specialists
Generate the `run_dir` (see Findings handoff above), create it, then dispatch the angles the Planner identified. Run applicable specialists **in parallel**.

**Crash-recovery contract (FM-1):** before dispatching any specialist, write `{run_dir}/_run.json` with `{started_at, session_id, status: "in-progress"}`. After synthesis, rewrite it with `status: "complete", verdict: <v>`. A run_dir whose `_run.json` shows `status: "in-progress"` older than `RED_TEAM_RUN_TTL` seconds (default 86400) is orphaned — a later session may archive it.

**Specialist timeout (PERF-5):** each specialist dispatch carries a wall-clock budget. If a specialist has not returned its file path within `RED_TEAM_SPECIALIST_TIMEOUT` seconds (default 300), mark it `DEFERRED — timeout` in the dispatch manifest and continue. Do not wait indefinitely; one stalled specialist must not block synthesis.

Each specialist dispatch includes: the proposal under review (or pointer to it), the `run_dir`, and the instruction — *"Write your findings to `{run_dir}/<your-name>.json` per the schema in the orchestrator skill. Your response text must contain ONLY the file path — no prose, no findings inline."* If `{run_dir}/prospect.md` exists (planner fired the prospect pass), specialists Read it before attacking and weigh its priors.

Project-local specialists (under `P:/.claude/agents/`). The two **always-consider** specialists are NON-OPTIONAL — they run on every /red-team invocation regardless of how narrow the proposal seems, regardless of ponytail/auto-mode/decision-phase framing. Skipping an always-consider specialist invalidates the synthesis. Dispatch the conditional specialists whenever the planner identifies their angle — and when uncertain whether an angle applies, **dispatch it** (over-dispatch is cheap; under-dispatch silently misses whole failure classes).

- `red-team-gate-reviewer` — **always-consider (non-optional)**. Gates, hooks, matchers, guardrails, calibration.
- `red-team-workflow-reviewer` — **always-consider (non-optional)**. CLAUDE.md, skills, commands, task-tracking, workflow quality.
- `red-team-security` — data leaks, access control, injection, trust boundaries.
- `red-team-performance` — timeouts, bottlenecks, N+1, races, resource exhaustion.
- `red-team-logic` — off-by-one, inverted conditionals, wrong operators, ambiguous precedence, category overlap.
- `red-team-state` — state isolation, stale-data hazards, cross-run contamination, multi-terminal scoping, concurrency, handoff integrity. Dispatch on any proposal touching persisted artifacts, caches, run dirs, session-scoped behavior, or concurrent terminals.
- `red-team-failure-modes` — "imagine it failed catastrophically, why?" with web research for domain anti-patterns.
- `red-team-plugin` — dispatch on plugin/tool/MCP proposals: manifests, dispatch double-fire, source-vs-cache drift, version-bump/cache hygiene, integration guardrails.
- `red-team-testing` — dispatch on gate/agent/critical-path changes: tests, evals, harnesses, regression + entry-point-launch coverage.

**Every dispatch carries the full context bundle** — no bare one-liner prompts. Each specialist prompt MUST include: (a) the **absolute** `run_dir` path (never the literal `{run_dir}` placeholder — bind it), (b) the proposal pointer (`{run_dir}/prospect.md` and/or `{run_dir}/proposal.md`), (c) the specific target under review (file paths, hook names, session evidence), (d) the specialist's concrete task, (e) the output-path instruction and the "response text = file path only" rule. A specialist that receives only an output path cannot do its job and will return empty.

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

**Telemetry emission (non-optional — the directive's loop starts here):** after the verdict is produced, write one telemetry line so the run is observable by the self-improvement layer:

```
python "<plugin_root>/__lib/telemetry.py" commit \
  --run-dir <run_dir> --session-id <id> --verdict <verdict> \
  --dispatched <comma-list> --deferred <comma-list> \
  [--duration-s <seconds>] [--operator-outcome accepted|partial|overridden|unknown]
```

The writer derives `counts`/`critic_conflicts_resolved`/`top_categories` from `{run_dir}/critic.json` defensively (a missing critic produces a partial line with `parse_error`, never an exception). If the command itself fails, note it in the Review note section; **do not abort the run** — the verdict is the user-facing deliverable, telemetry is best-effort. `operator_outcome` defaults to `unknown`; update it later if the operator accepts/overrides the verdict (`python telemetry.py recent` reads back; manual edit of `P:/.claude/state/red-team/telemetry.jsonl` to amend `operator_outcome` is acceptable).

## ROI frame
`ROI ≈ (debug-time saved) × (recurrence frequency) ÷ (effort to land)`

Qualitative ROI is allowed. Quantitative performance attribution requires actual timing / telemetry / profiling evidence — never invent measurements.

## Final output format

### Specialist dispatch manifest
- Lists every specialist in the skill (`gate-reviewer`, `workflow-reviewer`, `security`, `performance`, `logic`, `state`, `failure-modes`, `plugin`, `testing`) with one of: **DISPATCHED** (ran, findings in critic) or **DEFERRED — <one-line reason>**. The two always-consider specialists may not be DEFERRED; if one is, the synthesis is invalid and must say so explicitly at the top. This makes omission visible in the user-facing output instead of silent.

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

### Long-Term Efficiency / Effectiveness Opportunities

This optional section captures lessons from this review that could improve future
reviews, gates, skills, workflows, or context retrieval — beyond the immediate
ship/no-ship decision. It is **not** for BLOCK/REVISE defects (those belong in Verified
findings) but for systemic patterns worth preserving.

When populating this section, use the shared promotion opportunity schema:

```
OPP-XXX: [high/medium/low] [promotes to: skill|hook|prompt|config|test|docs|cks_or_wiki|task|backlog|reject]
Observation: What pattern or failure mode was observed
Evidence: Finding ID or file:line or specialist output
Reusable lesson: What future reviews or skills should apply
Proposed action: Concrete improvement step
Uniqueness: new | strengthens_existing | duplicate | rejected
Falsification: What would prove this lesson wrong
```

**Rules:**

- **Must not derail the verdict**: The verdict (PROCEED/REVISE/BLOCK) is based on
  proposal correctness and risk. Opportunity capture is a separate durable-learning
  path and does not affect the go/no-go decision.
- **No weak or vague observations**: Only patterns with concrete evidence and clear
  reusable lessons. One-off issues without generalizable value belong in Verified
  findings or NITs, not here.
- **Every entry must have a validation/falsification path**: State how to verify the
  improvement works or what evidence would refute it.
- **Check for duplicates before promoting**: If this strengthens an existing
  opportunity, say which one (e.g., `strengthens_existing: OPP-047`).

This section is **advisory by default** — it produces reviewable candidates, not
automatic writes to wiki/CKS or the task queue. The workflow can queue candidates
to `.claude/.artifacts/wiki_ingest/proposed_notes/{session_id}.jsonl` for later review,
but `/red-team` does not silently write them.

When this section is empty or no opportunities were identified, omit the heading entirely.

## Implementation note for the model
- If named agents exist in the environment, call them (preferred).
- If they do not, emulate the same flow with separate internal passes using the same roles — but flag this: single-context emulation tends to soften the critic, because the same context drafted the plan it is now reviewing.

## Adjacent systems (do not duplicate)
- `/code-review` — routine code review (file:line shaped).
- `/pre-mortem` → now `/red-team pre-mortem` (3-phase adaptive critique with Health Score + RNS). The standalone entry is a deprecation stub; the engine (`cc-skills-sdlc/skills/pre-mortem/`) is the source of truth for the phase prompts, blinded consumer-contract review, and `.codex`/`.pi` adapters. `/red-team` default mode differs from pre-mortem mode by: planner-first pass, explicit proposal / non-code framing, single PROCEED/REVISE/BLOCK verdict, and the ordered tiebreaker at synthesis (no Health Score, no RNS).
- `/adversarial-review` agent → parallel code review (file:line shaped). Distinct from `/red-team adversarial` mode, which dispatches to **external LLM harnesses** for B-class divergence checks, not internal agents.

## Suggest

`/red-team` cross-suggests (post-verdict, not mid-attack):
- `/review` — when findings touch implementation quality the user should run a structured review on.
- `/improve` — when the verdict surfaces a design or process improvement (not a defect).
- `/claude-audit` — when findings implicate runtime env (settings.json, hooks, MCP).
- `/skill-audit` — when findings implicate skill design (systemic, not one-off).
- `/wiki` — when the Long-Term Opportunities section produces a durable candidate worth persisting.

## Self-Improvement Directive (Phase 3, observe layer)

`/red-team` improves through **eval-driven feedback loops**, not live autonomous rewriting. The system gets better by observing outcomes, capturing failures, converting them to evals, proposing targeted changes, and shipping only changes that improve a measured baseline.

**Non-negotiable invariants:**
- `/red-team` does **not** rewrite its own production prompts, verdict rules, or policy at runtime.
- Production behavior changes come from the offline improvement workflow (Phase 3b `/red-team-improve`), not runtime reflection.
- Real incidents are converted into durable evals whenever feasible.
- Improvement is judged by measured outcomes, not by self-description of being "better."

**Mandatory telemetry:** every run appends one structured line to `P:/.claude/state/red-team/telemetry.jsonl` (see §4 Synthesis). The schema, writer, and CLI live in `__lib/telemetry.py` + `__lib/telemetry_schema.py`. Override path with `RED_TEAM_STATE_DIR`.

**Incident capture:** when a run misses an issue, overfires, routes poorly, wastes time, or returns malformed output, record it:
```
python "<plugin_root>/__lib/incidents.py" add --category <routing|formatting|critic-calibration|specialist-miss|stale-state|latency|other> \
  --run-id <run_id> --summary "..." [--expected ... --observed ... --impact ... --evidence ... --root-cause ...]
```
Incidents live at `P:/.claude/state/red-team/incidents.jsonl`. The improvement workflow (Phase 3b) reads them, clusters repeats, and proposes changes.

**Safe automation vs human-gated:**
- *Automatable:* collecting telemetry, clustering incidents, drafting candidate fixes, generating eval cases, running offline regression.
- *Human-gated (never auto-applied):* critic policy changes, severity-rule changes, prompt/routing modifications, anything that weakens evidence or verification standards.

**Phase status:** 3a (this layer — telemetry + incidents) ships now. 3b (`/red-team-improve` workflow + eval corpus) lands after ≥5 real runs emit telemetry, so the loop is designed against observed data, not imagined patterns.
