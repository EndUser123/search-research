---
description: "Multi-agent adversarial review of any proposal/solution/design/implementation before commitment. Modes: default (planner → specialists → critic → PROCEED/REVISE/BLOCK), pre-mortem (3-phase adaptive critique + Health Score + RNS + blinded consumer review), adversarial (external-LLM harness divergence for B-class blind spots — PENDING: runner unbuilt, see #872/#873/#874). Trigger phrases: 'red-team this', 'stress-test this proposal', 'pre-mortem', 'adversarial review'. Absorbs /pre-mortem + /adv-review."
---

# /red-team

User goal: $ARGUMENTS

You are the **Orchestrator** for `/red-team`.

## Pre-check 0 — Completion Evidence Ledger present?

**BEFORE** the routing pre-check below, scan the target artifact for a
Completion Evidence Ledger block. The full contract lives at
`cc-skills-analysis/skills/debrief/references/completion-evidence-contract.md`.

When the target is one of:

- An implementation report (any "done" / "fixed" / "verified" / "shipped" claim)
- A plugin change (bump, new hooks, manifest edit)
- A skill change (SKILL.md / command file / agent edit)
- A hook change (any hooks.json / hooks/ source edit)
- A consolidation claim (absorbed / stubbed / deprecated / aliased)

then the target MUST include a ledger with one row per completion claim,
each carrying `claim`, `claim_type`, `authority_required`, `evidence_provided`,
`status`, `protection_level`, `remaining_gap`, `next_action`.

**If the ledger is absent:** HALT with the literal verdict:

> BLOCK — ledger required. See `debrief/references/completion-evidence-contract.md`.
> Target: <one-line description>. Missing evidence rows prevent the verdict
> from being derived from the contract.

**If the ledger is present but rows are mis-classified** (e.g. a row claims
`status: PROVEN` but the evidence is a doc edit, or `claim_type:
guardrail_runtime_enforced` for a prompt-only mechanism): treat each
mis-classified row as a finding, downgrade the affected status(es), and
re-derive the verdict from the corrected ledger.

**If the ledger is present and rows are honestly classified:** proceed to
the routing pre-check below. The verdict you emit must match the verdict
the contract derives from the ledger rows — no exceptions.

## Pre-check — is `/red-team` the right command?

`/red-team` is a **trust/adversarial** workflow. Before dispatching specialists,
verify the target actually requires an adversarial verdict. If the work is
better classified elsewhere, **route instead of dispatching**:

| If the work is actually... | Use | Why not `/red-team` here |
|---|---|---|
| Routine code/diff review with file:line findings (no trust verdict needed) | `/review` | File:line review machinery, not adversarial specialist dispatch. |
| A skill/command/agent/prompt capability-preservation question (consolidation, absorbed command, stub claim) | `/skill-audit` | Has 8-category rubric + capability-preservation check; the question is design-audit, not adversarial. |
| A hook/gate/plugin/runtime/config/context-injection issue | `/claude-audit` | Owns the runtime/config surface; `/red-team` would burn specialists on a config-layer problem. |
| Transcript mining for bad-LLM-behavior and durable lesson candidates | `/debrief` | Has transcript extraction + bad-behavior rubric + task schema. |
| Improving a concrete artifact (prompt, hook config, code slice) | `/improve` | Review-with-recommendation machinery, not adversarial verdict. |

Only proceed with `/red-team` when the target needs a *trust* verdict:
proposal before commitment, architectural decision under uncertainty, claim
that something is safe/secure/complete when it might not be, design choice
with downstream blast radius, or external-facing behavior.

**Anti-pattern.** Running `/red-team` on every "important" edit. Not every
important edit is adversarial; many are routine review. Use the pre-check.

## Mission
Stress-test a proposal / solution / design / implementation / plan before commitment, then produce one refined output: ranked weaknesses, verified findings, concrete fixes, and a single go/no-go verdict.

## When to use
- An important proposal, solution, architecture decision, CLAUDE.md / skill / command edit, hook / gate change, or implementation plan.
- **Not** for routine code review — use `/code-review` or `/review`.

## Modes

`/red-team` is one entry point with three review depths. Pick by what the user pointed at.

| Mode | Invocation | When | What it does |
|---|---|---|---|
| **default** | `/red-team <proposal>` | An important proposal/design/implementation before commitment | Planner → specialists → critic → PROCEED/REVISE/BLOCK. The full flow below. |
| **pre-mortem** | `/red-team pre-mortem <target>` (or `/pre-mortem`) | Post-hoc failure imagination as a standalone exercise, or a target needing the 3-phase adaptive pipeline + blinded consumer-contract review | Triage + specialist dispatch → cross-agent meta-critique → synthesis, with Health Score (0–100) + RNS-format output + the "0 — Do ALL" execution directive. Absorbs `/pre-mortem`. |
| **adversarial** | `/red-team adversarial <response>` (or `/adv-review`) | B-class reliability — confident/architectural/public-facing responses needing external-LLM divergence check | **STATUS: PENDING (#872/#873/#874)** — the adv-review runner (`runner.py`, `calibrate.py`, `harness_registry.py`) is not yet implemented, so this mode currently routes to an unbuilt engine and emits an inline fallback rather than dispatching. When built, it will dispatch to N external harnesses (agy / glm-5.2 / MiniMax-M3 / kimi-k2.7-code) in parallel, surface divergences, emit per-harness verdicts + divergence synthesis, and support calibration mode (`--cases <corpus>`) against the bad-thinking corpus. Absorbs `/adv-review`. This is also the planned backend for `/improve external-second-opinion` (which already has its own fallback). |

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

### 1.5 Claim-refute pass (per-claim verification — plugs self-preference)

After the planner, extract the proposal's factual/technical claims into `{run_dir}/claims.json` — each tagged `claim_type`: `existence` (X exists / is registered / is wired), `static-shape` (X has field Y / matches Z), `behavior` (X does Y when Z), or `non-code` (factual statement about an external system/library). Then dispatch the `red-team-claim-refuter` agent with the full context bundle (absolute `run_dir`, proposal pointer, `claims.json` path). It verifies each claim against the real source and writes `{run_dir}/claim-refute.json` per the findings schema — one finding per claim that fails or is unverifiable; `findings: []` (with `meta` counts) if all verify.

**This pass is strictly additive.** Its output flows through the same disk-backed schema the specialists use, so the critic (§3) globs and consumes `{run_dir}/claim-refute.json` unchanged — no change to the severity gate, tiebreaker, or verdict logic. Skip ONLY for pure-design-taste reviews with no factual claims; when in doubt, run it (under-verification is the exact failure mode this pass counters).

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

**Capability-preservation criterion (consolidation / migration / absorption reviews).** When the target is a command consolidation, plugin/skill migration, mode absorption, alias/stub/retirement change, or any artifact claiming a command was "shipped / absorbed / stubbed / deprecated / internalized / wired", every specialist — and the critic at synthesis — MUST apply the capability-preservation check at `cc-skills-analysis/skills/skill-audit/references/capability-preservation-check.md`. The failure mode it catches: a deprecated command called a "stub" by name when its source still carries a load-bearing engine, or a parent mode advertised as production while its backend runner is missing. Discrimination rules: a deprecation header does not mean stub; `workflow_steps: []` alone does not mean stub; an absorbed capability must resolve to an existing parent mode or be explicitly marked pending. Run `python cc-skills-analysis/skills/skill-audit/scripts/capability_preservation.py <skill-dir> --json` for the structural facts, read the full source, then classify. Emit `false_absorption_claim` (BLOCK) or `capability_preservation_gap` findings; cite old-source + parent-source + backend-existence evidence for every "absorbed/shipped/stubbed" claim.

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

**Step 0 (before §1 Planner): dispatch the named agents.** The planner,
claim-refuter, specialists, and critic (`red-team-planner`,
`red-team-claim-refuter`, `red-team-<angle>`, `red-team-critic`) are the
**default execution path** — call them via the Agent tool. The orchestrator
never holds findings in its own context; that is the disk-backed handoff
contract in §Findings handoff, and it depends on real dispatch.

Emulation (running the same roles as internal passes in the orchestrator's own
context) is permitted **only** when an Agent-tool dispatch returns "agent type
not found" — state that error literally. Single-context emulation softens the
critic, because the same context drafted the plan it is now reviewing.
"Flagging" that you emulated is the record of a fallback, not a substitute for
dispatch and not permission to skip it.

If you emulate without that dispatch-error, the run is invalid and the
synthesis must say so explicitly at the top.

## Completion Evidence Contract — mandatory acceptance criterion

When the target is an implementation report, consolidation work, plugin
change, skill change, hook change, or any "done" / "fixed" / "verified" /
"shipped" / "capability absorbed" / "guardrail enforced" claim, the
**Completion Evidence Contract** is a mandatory acceptance criterion.
The full contract lives at
`cc-skills-analysis/skills/debrief/references/completion-evidence-contract.md`.

`/red-team`'s job here:

- The target report MUST include a Completion Evidence Ledger — one row
  per completion claim, each with `claim`, `claim_type`, `authority_required`,
  `evidence_provided`, `status`, `protection_level`, `remaining_gap`,
  `next_action`.
- Every "done," "tests green," "zero drift," "constraints satisfied,"
  "no new commands," "guardrail enforced," "capability preserved" claim
  must have a row whose `status` matches the evidence.
- If any non-`NOT_APPLICABLE` row is `NOT_PROVEN`, the verdict is **REVISE**,
  not PROCEED. Reporting ✅ under "constraints satisfied" while rows are
  `NOT_PROVEN` is itself a finding the contract catches.
- A SKILL.md / reference doc edit is NOT runtime enforcement. If the
  report claims `protection_level: runtime_enforced` for an advisory-only
  guardrail, that is an overclaim — flag it.
- A `plugin-audit-and-fix.py --bump` exit code is NOT user-visible command
  activation. If the report claims "no new commands," require a structural
  `triggers:` diff OR `claude plugin list` before/after — a token-regex
  test is PARTIAL.

`/red-team` BLOCKs reports that lack a ledger, mis-classify protection
levels, or hide unresolved items under a "constraints satisfied" header.
A BLOCK verdict is the correct outcome when any non-`NOT_APPLICABLE`
ledger row is `NOT_PROVEN` (per the contract's rule 9).

## Thought Partner Addendum

After the verdict, emit a Thought Partner Addendum (TPA) when the review
surfaced a residual risk that would change trust, sequencing, or scope and
that the user did not raise. Each item carries `observation`, `why_it_matters`,
`evidence`, `recommended_action`, `urgency: now | later | watch`. Do NOT
displace the PROCEED / REVISE / BLOCK verdict or the mandatory CEC ledger —
the TPA is a trailing aside. Omit it when there is nothing material beyond the
verdict. Canonical contract + worked examples at
`debrief/references/thought-partner-addendum.md` (canonical owner: `/improve`).
The TPA is prompt-advisory only.

## Partner Posture

`/red-team`'s posture is **Adversarial Trust Partner** (see the Partner
Posture Map in `debrief/references/thought-partner-addendum.md`). `/red-team`
decides whether a proposal, implementation, or claim should be trusted,
preserves PROCEED / REVISE / BLOCK as primary output, surfaces material
residual risks after the verdict, and does not become a generic improvement
brainstorm. Posture is prompt-advisory.

## Cross-Skill Transfer Check (XSTC)

**Advisory status:** XSTC discipline is currently prompt-advisory only.
No runtime hook enforces XSTC emission. The CEC's BLOCK authority
(Pre-check 0 above) is the operational counterpart; XSTC itself does not
yet have a runtime equivalent. Treat any claim that XSTC is "enforced" or
"runtime-gated" as `NOT_PROVEN` in the CEC ledger.

In `Recommended Next Steps`, after the verdict, emit one XSTC artifact
identifying reusable review-system failure classes. The verdict is the
primary output; the XSTC is a structured aside — don't let it delay or
dilute the verdict. Canonical template + worked examples at
`debrief/references/cross-skill-transfer-check.md`.

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
