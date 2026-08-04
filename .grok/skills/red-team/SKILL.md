---
name: red-team
description: >
  Multi-agent adversarial review of any proposal, solution, design, or implementation
  before commitment. Planner → specialists → critic → root-cause clustering →
  PROCEED/REVISE/BLOCK verdict with minimum fix-set. Includes adaptive expansion,
  precision incentives, cross-model specialist dispatch, and finding classification.
  Use when: red-team, stress-test, pre-mortem, adversarial review, "is this safe",
  "what could go wrong", or before committing an architectural decision.
argument-hint: "<proposal or target to review>"
user-invocable: true
host: grok
domain: review
---

# /red-team — adversarial review with root-cause clustering

## Mission

Stress-test a proposal, design, implementation, or plan before commitment.
Produce one refined output: ranked weaknesses, verified findings, root-cause
clusters, concrete minimum fix-set, and a single go/no-go verdict.

## Pre-check — is this the right tool?

`/red-team` is a **trust/adversarial** workflow. Only proceed when the target
needs a trust verdict. Route elsewhere if:

| If the work is actually... | Use instead |
|---|---|
| Routine code/diff review | `/review` |
| Session retrospective | `/debrief` or `/aar` |
| Improving a concrete artifact | `/refactor` |
| Thought-partner dialogue | `/tp` |

## Wiki grounding (mandatory before dispatching specialists)

Query the wiki for existing knowledge before spawning specialists. This prevents
false-positive findings based on missing context.

# Use the built-in grep tool: grep pattern="<target keywords>" path="P:/.data/wiki/concepts/" -i

Pass wiki-confirmed premises to specialists as context. Pass contradictions as
pre-found attack vectors.

## Procedure

### Step 1 — Plan the attack

Identify the target's attack surfaces. Assign 3-6 specialists based on what
could go wrong. Standard roster:

| Specialist | Attacks |
|---|---|
| correctness/logic | Logic errors, off-by-one, wrong operators, invariant violations |
| state/concurrency | Race conditions, stale data, cross-session contamination, TOCTOU |
| security | Data leaks, access control gaps, injection vectors |
| scope/gap | What the system doesn't cover, missing patterns, bypass paths |
| performance | Timeouts, bottlenecks, resource leaks, N+1 |
| workflow | Process gaps, missing gates, operator friction, **post-commit hygiene** (version bumps, cache rebuilds, wiki-write-back gates, state-file cleanup), **feedback-loop completeness** (does the system re-verify after changes? does it close the loop?) |
| meta/self-reflection | **What attack surfaces did the other specialists' scopes MISS?** This specialist runs LAST (after all others return) and reviews: (1) which steps/phases of the target were NOT covered by any specialist's scope; (2) whether any specialist's findings hint at a deeper systemic issue the specialist wasn't scoped to investigate; (3) whether the target's own self-assessment (falsifier, provenance) has blind spots. This is the adaptive, open-ended layer — it catches what deterministic scope allocation misses. |

**Post-commit hygiene scope (added 2026-07-27):** the workflow specialist MUST check whether the target handles: (a) version bumps on edits, (b) cache rebuilds after config changes, (c) wiki-write-back quality gates (does the write go through /why Step 15-style review?), (d) state-file cleanup/migration on retirement, (e) commit-message quality. This scope was missing from the original roster, allowing gaps in /skill-dev (no version bump, no wiki gate) to go undetected until manual /tp review.

**Meta/self-reflection specialist dispatch rules:**
- Runs AFTER all other specialists return (Step 3 verification complete)
- Receives: the target + ALL other specialists' finding summaries (not full JSON, just titles + severities)
- Does NOT re-investigate the same surfaces — its job is to find what was MISSED
- If it finds nothing, that's a valid result (the other specialists were comprehensive)
- If it finds a gap, add it as a standalone finding with `severity: ADVISORY` (it's a coverage gap, not a target defect)

### Step 2 — Dispatch specialists (parallel)

Spawn each specialist as a **read-only** subagent. Each specialist:
- receives the target + context bundle ONLY (not full conversation)
- reads the target files independently
- writes findings to `{run_dir}/{specialist}.json`
- returns ONLY the file path (no inline prose)

> **Wait-all-before-conclude gate (mandatory):** before Step 3 (verify) or any synthesis output, issue `get_command_or_subagent_output(task_ids=[every-specialist-id], timeout_ms=<positive>)` and require every specialist to return `completed` or explicitly failed. "Task not found" is a mechanical error (typo, lost ID) — re-read `spawn_subagent` return to recover the correct ID; do NOT re-spawn duplicates. See [[parallel-subagent-wait-all-gate]].

**run_dir:** `P:/.artifacts/red-team/{session_id}/{YYYYMMDD-HHMMSS}/`

**Precision incentive (add to every specialist prompt):**

> Each finding that the critic marks `non_reproducible` reduces your specialist's
> quality signal. Prefer fewer high-confidence findings over many speculative ones.
> If you are <70% confident a finding is real, either drop it or label it
> `[speculative]`.
>
> For each finding, the `fix` field must state what design or implementation
> would make this class of failure impossible — not just "patch this instance."
> The adversarial posture finds what's wrong; the constructive alternative
> makes the fix structurally sound. A finding without a resilient alternative
> is incomplete.

**Cross-model specialist (one per run):** one specialist uses a cross-model model
for decorrelated blind-spot detection. Pool (try order):

1. `glm-5-2` (subscription, best tool-calling)
2. `go-mimo-v2-5` (OpenRouter, paid, verified working)
3. `minimax-m3` (subscription, 4,500 calls/5h — capable code reader)
4. parent-inherited (last resort)

> **M3 spawn truncation note (2026-07-27):** the `spawn_subagent` dispatch path
> may impose a lower output token budget than direct API for certain task shapes,
> causing `max_tokens_truncation` on tasks that require reading multiple files +
> writing large structured JSON (observed in `/review`: 2 of 3 specialist
> attempts). **The fix is to decompose the specialist's scope into smaller tasks**
> (per-file, per-attack-surface) so each spawn produces a small output. Any model
> — including M3 — handles small tasks fine. Do NOT switch models as the primary
> fix; shrink the task. See `~/.grok/tool-fallbacks.md` and `/review` Step 4.

**Do NOT use Claude or Anthropic models** (operator constraint).

If using `spawn_subagent` with a model slug, set `capability_mode="read-only"`.
If the model fails (transport error, auth, serialization — not truncation), fall
back to parent-model for that specialist and disclose in synthesis.

**Model routing for ALL specialists (MANDATORY):** every specialist — not just
the cross-model one — must have an explicit `model` parameter when spawned.
Omitting `model` causes non-deterministic routing (observed 2026-07-27 in
`/review`: two specialists routed to MiniMax-M3 and truncated; the root issue
was omitted model, not M3 itself). Route by specialist type:

| Specialist type | Model | Why |
|---|---|---|
| correctness, state/concurrency, security, scope, performance, workflow (code-reading specialists) | Parent-inherited Grok | Best reasoning + sufficient output for multi-file analysis + JSON writing |
| Cross-model specialist (one per run) | `glm-5-2` (preferred) or pool above | Decorrelated blind-spot detection |
| Meta/self-reflection (runs last, reads summaries) | Parent-inherited Grok | Synthesis requires strong reasoning |

**If any specialist truncates** (`max_tokens_truncation`): the task scope was too
large. Decompose into smaller tasks (per-file, per-attack-surface) and re-dispatch.
Do NOT switch models as the primary fix — shrink the task.

### Step 3 — Verify specialist outputs

For each specialist response:
1. Check the reported file exists on disk
2. Load the JSON findings
3. Verify each BLOCK/REVISE finding against the actual source (read the cited file:line)
4. Mark as `verified` or `non_reproducible`

If a specialist reported `WRITE_FAILED` or the file doesn't exist: note as
coverage gap, do not fabricate findings.

### Step 4 — Expansion gate (optional, bounded)

After all specialists return, review combined findings for genuinely new attack
surfaces not covered by any specialist's scope. Trigger expansion (all three):
1. A finding reveals a defect class no specialist was scoped to investigate
2. Severity is HIGH or CRITICAL
3. High confidence the operator would want it investigated now

If triggered: dispatch up to 2 additional specialists (one-shot, no recursion).

### Step 5 — Root-cause clustering

Group findings where multiple specialists independently identified the same
underlying problem. For each cluster:

- **cluster_id:** RC-1, RC-2, etc.
- **root_cause:** one sentence
- **members:** list of finding IDs
- **amplification:** how many specialists found it
- **severity:** highest among members (collapsed — 5 BLOCKs for same cause = 1 BLOCK × 5 amplified)
- **fix:** the single change that addresses all members

Rank clusters by impact × amplification.

### Step 6 — Finding classification

Tag each cluster/finding with exactly one class:

| Class | Meaning | Action |
|---|---|---|
| `architectural` | Design itself is wrong | Redesign needed; may block ship |
| `implementation` | Design sound, code has bugs | Fix the code |
| `definitional` | Term/threshold undefined | Define or downgrade |
| `deferrable` | Real but safe to defer | Backlog item |

### Step 7 — Synthesis and verdict

Output:

1. **Classification summary** (class counts)
2. **Root-cause clusters** (ranked)
3. **Standalone findings** (not clustered)
4. **Minimum fix-set** (prioritized — addresses all architectural + implementation BLOCKs)
5. **Deferred items** (explicit list of what NOT to fix now)
6. **Verdict** (one of):

| Verdict | When |
|---|---|
| `PROCEED` | No BLOCK findings; design is sound |
| `REVISE` | BLOCK or high-amplification REVISE findings; fixable |
| `BLOCK` | Architectural flaw; design won't work |

### Step 8 — Telemetry

Record a one-line summary: specialist count, findings raw/verified, clusters,
verdict, cross-model specialist used, latency.

### Step 9 — Post-verdict routing (mandatory for REVISE/BLOCK)

When the verdict is `REVISE` or `BLOCK`, the minimum fix-set is actionable work
that needs a next-session pickup artifact. Route unresolved findings:

- **REVISE verdict:** invoke `/handoff <target-name>-red-team-fixes` with the
  minimum fix-set, root-cause clusters, and verification criteria. A future
  session picks this up to implement the fixes.
- **BLOCK verdict:** invoke `/handoff <target-name>-red-team-blocked` with the
  architectural flaw, alternatives considered, and what would need to change
  for the design to become viable.
- **PROCEED verdict:** no handoff needed — the design is sound.

Findings without a handoff evaporate — the operator has to re-run the red-team
to recover them. This mirrors `/friction`'s post-output routing.

## Save step: persist systemic attack/failure patterns to wiki (NEW 2026-07-25)

After the verdict, check whether the red-team surfaced a **systemic attack or failure pattern** worth saving to the wiki. Red-team findings about structural/design-level weaknesses are exactly the kind of knowledge that compounds — future red-teams (Wiki grounding, Step 0.5) and `/wargame` sessions should find them.

**Mechanical gate — an attack/failure pattern is wiki-worthy ONLY if ALL of:**
1. The finding is **architectural** (class `architectural` from Step 6) — not a code-level implementation bug
2. Has **verified evidence** (BLOCK or REVISE severity, verified in Step 3)
3. **Named abstractly** (e.g., `fail-open-on-import-error-pattern` not `2026-07-25-auth-bypass`)
4. **Cross-target reusable** (would apply to a different proposal/design in a different subsystem)
5. **Not already in the wiki** (Wiki grounding query would have surfaced it; refine instead of duplicate)
6. Has a **falsifier** (what observation would show this attack vector does NOT apply)

If all 6 pass: write to `P:/.data/wiki/concepts/<slug>.md` per SCHEMA.md frontmatter, log via `append_log.py`. Cite the cluster ID and run_dir as sources.

If any fails: the finding stays in the red-team output only.

**Reference:** `/why` Step 15 mechanical gate; wiki concept `wiki-integrated-skills-query-save-pattern`. This closes the loop with the Wiki grounding step.

## Modes

| Mode | Invocation | When |
|---|---|---|
| **default** | `/red-team <target>` | Standard adversarial review |
| **quick** | `/red-team quick <target>` | 2 specialists only, no expansion, fast triage |
| **deep** | `/red-team deep <target>` | 6+ specialists, full expansion, pre-mortem phase |

## Findings schema (each specialist writes this)

```json
{
  "specialist": "<name>",
  "writer_session": "<session_id>",
  "meta": { "angles_covered": ["..."], "gaps": ["..."] },
  "findings": [
    {
      "id": "<SPEC>-<N>",
      "severity": "BLOCK|REVISE|ADVISORY",
      "title": "<one line>",
      "detail": "<what's wrong, why it matters>",
      "evidence": "<quoted code/citation — required for BLOCK/REVISE>",
      "confidence": "high|medium|low",
      "fix": "<resilient alternative: what design makes this class of failure impossible, not just a patch for this instance>"
    }
  ]
}
```

On write failure: respond with `WRITE_FAILED: <reason>` — never report a path
that doesn't exist.

## Context rules

- Read target files yourself; do not ask the operator to paste them
- Search the repo and wiki before dispatching
- Each specialist gets only the target + context bundle, not the full conversation
- The orchestrator holds only file paths, not findings content (context discipline)

## Provenance

v1 (2026-07-23): overlay extending the bundled plugin red-team skill.
v2 (2026-07-24): **standalone** — plugin disabled (`config.toml [plugins] disabled`).
Base procedure inlined from the plugin command. Overlay features retained:
adaptive expansion, precision incentives, cross-model specialist, root-cause
clustering, finding classification, minimum fix-set.
