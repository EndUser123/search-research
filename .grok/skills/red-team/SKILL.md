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

```
qmd search --collection wiki "<target keywords>" --limit 10
```

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
| workflow | Process gaps, missing gates, operator friction |

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

**Cross-model specialist (one per run):** one specialist uses a cross-model model
for decorrelated blind-spot detection. Pool (try order):

1. `glm-5-2` (subscription, best tool-calling)
2. `go-mimo-v2-5` (OpenRouter, paid, verified working)
3. `minimax-m3` (subscription, chat-only — reasoning specialist only)
4. parent-inherited (last resort)

**Do NOT use Claude or Anthropic models** (operator constraint).

If using `spawn_subagent` with a model slug, set `capability_mode="read-only"`.
If the model fails (max_tokens, transport error), fall back to parent-model for
that specialist and disclose in synthesis.

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
      "fix": "<concrete correction>"
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
