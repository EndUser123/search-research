---
thread_id: tp-pool-composition-review-20260723
parent_handoff_path: P:\docs\handoffs\tp-model-pool-not-inline-fallback-20260722\HANDOFF.md
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
current_terminal_id: console
produced_at: 2026-07-23T14:25:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 86f1ac13c9b6fcacf700be88a37a6725cd9a968c
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8b39-95e3-7121-a8de-4e3f117e511a\chat_history.jsonl
---

# Handoff: /tp spawn pool — composition review (right models, enough, randomness)

## Objective

Investigate whether the `/tp` Step 2 spawn_subagent pool — currently `[nvidia-nemotron-3-ultra, glm-5-2, go-mimo-v2-5, parent-inherited]` (4 members as of 2026-07-23 15:19 UTC, after `ccr-ornith` was removed) — has the right membership, sufficient size, and the right selection algorithm; surface a recommendation (or recommendation set) before any further `/tp/SKILL.md` edit.

**Scope bounds:** Investigation only. **Do NOT modify `~/.grok/skills/tp/SKILL.md` Step 2** in this thread. The work scope is "investigate + recommend + (optionally) probe new models for the pool"; the ambient total is "the future-state `/tp` Step 2 once the user approves a recommendation." The implementation handoff is a separate thread that should be forked only after the user picks a path.

## Status

OPEN — pool exists and is functional (closed handoff `tp-model-pool-not-inline-fallback-20260722` shipped it 2026-07-22). **Mid-session update 2026-07-23:** the pool is now 4 members (ccr-ornith removed by commit `019c59d` in `~/.grok/` repo: "serialization error under load"). The handoff was written with the 5-member pool composition; this revision updates the membership facts and adds the second empirical evidence.

## Producing context

- **Date:** 2026-07-23
- **Producing session-id:** 019f8b39-95e3-7121-a8de-4e3f117e511a
- **Producing terminal-id:** console
- **Host/version:** Grok Build
- **Trigger:** this session was running `/tp` on the question "is there something we can tune to make things better and smoother?" The orchestrator spawned the fresh subagent with `model=nvidia-nemotron-3-ultra` (the first pool member per deterministic order). The user **cancelled the subagent** and asked the new question: "add a handoff file to look at fixing the spawning pool for '/tp'. are the models right, are there enough, why isn't the choice random?"

## Read-first list (ordered, with reasons)

1. **Parent handoff** `P:\docs\handoffs\tp-model-pool-not-inline-fallback-20260722\HANDOFF.md` — pool exists, here are the spawn_subagent compatibility constraints and the cost-regime ordering rationale. Without this context, the new questions have no anchor.
2. **`~/.grok/skills/tp/SKILL.md` Step 2 (lines 220-260)** — current pool implementation. The pool table is at lines 243-249; the selection loop is at lines 251-256.
3. **`~/.grok/tool-fallbacks.md` lines 57-77** — spawn_subagent compatibility table. The binding constraint on pool membership: not every model in config.toml works via spawn_subagent.
4. **`P:/.data/wiki/concepts/model-fleet-provider-pools.md`** — full model inventory across 8 providers (~48 models). The pool is a subset; this is the superset.
5. **`P:/.data/wiki/concepts/model-pool-not-chain.md`** — pool-not-chain principle. Selection is parallel-try, not ranked-fallback.
6. **`P:/.data/wiki/concepts/model-selection-from-pool-decision-framework.md`** — 6-element ordered filter for choosing pool members.

## Verified facts (with source paths)

- [FACT] `/tp` SKILL.md Step 2 current pool = `[nvidia-nemotron-3-ultra, glm-5-2, go-mimo-v2-5, parent-inherited]` (4 members). Source: `~/.grok/skills/tp/SKILL.md:243-249`. Verified by direct read this turn (post-`019c59d` state).
- [FACT] Pool lanes: Reasoning = `{nemotron-3-ultra, glm-5-2, parent-inherited}` (3); Code = `{go-mimo-v2-5}` (1). Source: pool table column "Lane" in `/tp/SKILL.md:243-249`. The /tp critique is a Reasoning-lane task.
- [FACT] Pool cost regimes: Free = `{nemotron-3-ultra}` (1); Subscription = `{glm-5-2}` (1, rationed); Paid OR = `{go-mimo-v2-5}` (1); Paid Grok = `{parent-inherited}` (1). Source: pool table column "Cost" in `/tp/SKILL.md:243-249`.
- [FACT] Pool is **deterministic** — try members in fixed order, first success wins. Source: `/tp/SKILL.md:251-256` ("for slug in [...]: spawn_subagent(...) if spawn returned content: break").
- [FACT] Pool probed 2026-07-22 (1 day ago). Source: `/tp/SKILL.md:236-242` ("All 4 models below passed a spawn_subagent compatibility probe... 2026-07-22"). Note: parent-inherited is the 4th, not probed (the default).
- [FACT] Known-broken models via spawn_subagent (excluded from pool): `nvidia-diffusiongemma-26b` (empty content), `go-deepseek-v4-*`, `go-kimi-*` (serialization), `go-qwen3-*` (401), `mistral-medium-latest` (422), **`ccr-ornith` (removed 2026-07-23 by commit `019c59d`: serialization error under load)**. Source: `~/.grok/skills/tp/SKILL.md:241` and `tool-fallbacks.md:59-60`.
- [FACT] This session cancelled the fresh subagent (Nemotron-3-ultra, first pool member) before completion. The cancellation came after the user explicitly rejected the deterministic-always-first pattern with the question "why isn't the choice random?"
- [FACT] Another `/tp` invocation in this session (per commit `019c59d` message) had: nemotron failed, ccr-ornith failed (serialization error under load), glm-5-2 succeeded. The operator flagged ccr-ornith should have already been removed; it was removed.
- [FACT] The closed parent handoff solved inline-fallback, NOT pool composition. Its Resolution section (lines 158-167) confirms "ALL TASKS COMPLETE" but does not address whether the pool members are the right ones, whether 5 (now 4) is enough, or whether deterministic selection is correct.

## Current state

**What works:**
- Pool exists; 4 members (after ccr-ornith removal 2026-07-23); spawn_subagent compatibility verified 2026-07-22 for the surviving 3.
- Selection loop is straightforward: try in order, first success wins.
- Inline fallback is preserved as last resort with disclosure.
- Model disclosure in Step 3 names which pool member ran.

**What's not yet investigated:**
- Whether the pool members are the **right** models for the task (Reasoning lane vs Code lane fit). 3 of 4 are Reasoning; the only Code-lane model (mimo) is untested at this prompt size.
- Whether 4 is enough (gap analysis against the full 48-model fleet). The pool shrunk 5→4 mid-session; if the trend continues, the pool size question becomes "is 3 sufficient before falling to inline?"
- Whether deterministic selection is correct (vs randomized, vs hybrid).
- Whether the cost-regime ordering is optimal (free-first is logical but Means nemotron-3-ultra (the free option) is also the one that fails on real prompts).

**Concern raised this session:**
- The user observed that the spawn always picks the first pool member (deterministic). They want **variety** — either by adding more members, by randomizing selection, or both.

## Critical empirical evidence (2026-07-23, this session)

The user's cancelled spawn — nemotron-3-ultra, the **first pool member** — actually completed in the background with a failure. This is direct evidence for the user's three questions. The next session should weight this heavily.

**Failure receipt (raw):**

```
Status: failed
Exit Code: 1
Error: serialization error: invalid type: null, expected u32 at line 1 column 331
Prompt: 98,243 tokens (actual /tp-sized prompt, NOT the 2026-07-22 trivial "Reply READY" probe)
Output produced: 494 tokens across 2 model calls
API duration: 44,477 ms
Wall-clock: 47.61 s
Slug: nvidia/nemotron-3-ultra-550b-a55b (i.e. nvidia-nemotron-3-ultra)
```

**What this proves:**

1. **The 2026-07-22 "tested OK" finding is misleading for real workloads.** That probe was a 1-token `Reply READY` test. This test was a 98,243-token real /tp prompt. Same model. Different prompt size. Different result. The "model is OK" claim was scoped to trivial prompts and should be re-verified for real prompts.

2. **Deterministic selection is currently failing silently.** When the first pool member fails, `/tp` walks to the second (ccr-ornith, 31.8s) and then to inline. The user cancellation in this session means the user observed the slowness/experience and pulled the band-aid off. Without intervention, the failure mode is "slow opaque degradation."

3. **The "why isn't the choice random" question has a concrete root cause.** Deterministic + first member unreliable = the failure mode the user wants to avoid. Randomization would have hit ccr-ornith (working) on retry instead of the failing nemotron-3-ultra.

4. **Latency was 6× the documented 7.5s.** The pool table records `nvidia-nemotron-3-ultra` at 7.5s. Real /tp workloads run at 44.5s on the same model. The 7.5s figure is also scoped to trivial prompts.

**What this does NOT prove:**

- Doesn't prove nemotron-3-ultra is broken for all use cases. It broke on a 98k-token prompt with a specific output structure (the response had a `null` field where the dispatcher expected a `u32`). Smaller prompts may still work.
- Doesn't prove the other pool members will fail similarly. We have one data point.
- Doesn't prove randomization is the right fix. It would mask the symptom, not address it (the slow unreliable model would still be in the pool).

**Action implication for the next session:**

The investigation should now include:
- A real-prompt probe of all 4 non-parent pool members (not just thin "Reply READY" probes).
- Whether nemotron-3-ultra should be moved down in the pool order (or temporarily removed) until real-prompt reliability is verified.
- Whether randomized selection should be adopted as a near-term defense against per-model degradation.

## Second empirical evidence (2026-07-23, concurrent ~15:19 UTC)

A separate `/tp` invocation in this session (running concurrently with this handoff's preparation) produced a different failure pattern, captured in commit `019c59d` (authored by Claude Sonnet 4.6 in `~/.grok/` repo).

**Receipt (from commit message):**

```
fix: remove ccr-ornith from /tp spawn pool (serialization error under load)
ccr-ornith hit a serialization error during the 2026-07-23 /tp critique
(nemotron also failed; glm-5-2 succeeded). Operator flagged it should have
already been removed. Removed from pool table, selection pseudocode,
example disclosures, and cross-family reference. Pool is now 3 models +
parent.
```

**What this adds:**

1. **ccr-ornith also failed serialization under load.** Not the same prompt size as my evidence (commit message doesn't specify), but the same failure family. ccr-ornith was Code-lane (free local), so the failure mode spans both Reasoning and Code lanes.

2. **glm-5-2 succeeded.** Reasoning-lane, subscription (rationed). The pool now has one confirmed-working member on real prompts. This is the only positive evidence we have.

3. **The pool dropped from 5 to 4 members.** `~/.grok/skills/tp/SKILL.md` lines 243-249 now show `[nvidia-nemotron-3-ultra, glm-5-2, go-mimo-v2-5, parent-inherited]`. ccr-ornith was removed from the pool table, selection pseudocode, example disclosures, and cross-family reference. The "Known-broken slugs" line (line 241) was updated to include ccr-ornith.

4. **The operator's directive was clear.** "ccr-ornith should have already been removed." This is feedback on the pool's historical membership — the user is signaling that the pool should have been pruned earlier, not just now.

**Combined evidence (this session's two `/tp` failures + the glm-5-2 success):**

| Pool member | Lane | Real-prompt verdict this session |
|---|---|---|
| nvidia-nemotron-3-ultra | Reasoning | **FAILED** (serialization error, 98k tokens) |
| glm-5-2 | Reasoning | **PASSED** (per commit `019c59d` message) |
| go-mimo-v2-5 | Code | Untested at this prompt size |
| parent-inherited | Reasoning | (assumed working — fallback) |
| ~~ccr-ornith~~ | ~~Code~~ | ~~FAILED~~ (removed 2026-07-23 by `019c59d`) |

**Implication for the investigation:**

- **TK-COMPOSITION-01 (lane fit) is now answerable.** 3 Reasoning + 1 Code. glm-5-2 (Reasoning) succeeded. ccr-ornith (Code) failed. mimo (Code) untested. Net: Reasoning lane is empirically better than Code lane on real prompts, but the sample is small (n=2).
- **TK-SIZE-01 (Reasoning-lane free options) is more urgent.** The only free Reasoning member (nemotron) is the one that fails. The fallback Reasoning member (glm-5-2) is rationed. The pool has 1 confirmed-working free-or-paid Reasoning member for real prompts.
- **TK-RANDOM-01 is sharpened.** With nemotron (1st) and ornith (2nd, now removed) both failing, deterministic-always-first was a single point of failure. Randomization would have hit glm-5-2 (Reasoning, working) on retry.

## Task packets

### TK-COMPOSITION-01: Right lane for the task?

**Goal:** Determine whether the pool should be Reasoning-only or mixed (Reasoning + Code). The /tp critique is a Reasoning-lane task by the SKILL contract; the pool currently has 3 Reasoning + 2 Code.

**In scope:** Lane analysis of current pool; assessment of whether ornith (Code lane, free local) and mimo (Code lane, paid OR) belong in a Reasoning task pool.

**Out of scope:** Modifying `/tp/SKILL.md`.

**Files / anchors:** `/tp/SKILL.md:243-249` (pool table).

**Acceptance:** Recommendation with evidence — Reasoning-only, mixed, or split (Reasoning primary / Code fallback). Cite specific reasoning for each included Code-lane model.

**Falsifier:** Recommendation is wrong if ornith (Code lane) produces critiques rated ≥parent-inherited (Reasoning) on a benchmark of 5+ recent /tp invocations. (If Code lane is fine for critique, the lane-fit argument fails.)

**Verification level required:** STATIC_INSPECTION + benchmark.

**Estimate:** ~30 min for analysis. Benchmark is open-ended.

### TK-COMPOSITION-02: Right family diversity?

**Goal:** Determine whether the pool covers enough model families for cross-family lens diversity. Currently 4 cross-family + 1 same-model (parent).

**In scope:** Family-diversity analysis of current pool (Nemotron=NVIDIA, Ornith=CCR local, GLM=Zhipu, Mimo=OpenRouter/MiniMax, parent=Grok).

**Out of scope:** Probing new models (covered in TK-SIZE-01).

**Files / anchors:** `/tp/SKILL.md:243-249`; `model-fleet-provider-pools.md`.

**Acceptance:** Position on whether the current 4-family set is sufficient, or whether 5-6 families is needed for genuine lens diversity.

**Falsifier:** If 4 families produce critiques that are 80%+ similar (same blind spots), increase family diversity is needed.

**Verification level required:** STATIC_INSPECTION + critique-quality comparison.

**Estimate:** ~20 min.

### TK-COMPOSITION-03: Right cost regime ordering?

**Goal:** Determine whether "free-first" is the right ordering when the free Reasoning-lane option (nemotron) is unavailable.

**In scope:** Cost-regime tradeoffs. nemotron-3-ultra is free Reasoning (7.5s). If nemotron is busy/rate-limited, fallback to ccr-ornith (free local but Code lane, 31.8s) — slower by 4×. Is the cost savings worth the latency? Should a paid-Reasoning (parent-inherited) sit higher than ccr-ornith?

**Out of scope:** Procurement / paying for additional Reasoning-lane quotas.

**Files / anchors:** `/tp/SKILL.md:243-249`.

**Acceptance:** Position on whether the order `[nemotron, ornith, glm, mimo, parent]` is optimal, or whether a different order (e.g., `[nemotron, glm, parent, ornith, mimo]`) better respects the "Right lane for the task" finding.

**Falsifier:** Recommendation is wrong if the proposed ordering produces a higher /tp critique acceptance rate across 10+ invocations.

**Verification level required:** STATIC_INSPECTION + benchmark.

**Estimate:** ~20 min.

### TK-SIZE-01: Gap analysis — Reasoning-lane free options

**Goal:** Identify Reasoning-lane models that are (a) free, (b) cross-family, and (c) potentially compatible with spawn_subagent. The Reasoning-lane free pool is currently 1 (nemotron).

**In scope:** Survey of `model-fleet-provider-pools.md` for Reasoning-lane free models. Candidates from the pool concept: `zen-nemotron-3-ultra-free`, `or-nemotron-ultra-free`, `or-hy3-free`, `zen-deepseek-v4-flash-free`, `zen-north-mini-code-free`, `zen-mimo-v2-5-free`, `zen-nemotron-3-ultra-free`. None of these have been probed via spawn_subagent.

**Out of scope:** Probing non-Reasoning-lane models.

**Files / anchors:** `model-fleet-provider-pools.md`, `tool-fallbacks.md`.

**Acceptance:** List of 3-5 candidate Reasoning-lane free slugs with probe plan. Probe plan: `spawn_subagent(model=slug, prompt="Reply READY")` per slist, record success/error/latency.

**Falsifier:** Recommendation is wrong if 0 new Reasoning-lane free models pass spawn_subagent probe (the gap is structural, not addressable).

**Verification level required:** Unit-test-style probe (the spawn_subagent READY test).

**Estimate:** ~15 min for survey; ~10 min per probe.

### TK-SIZE-02: Gap analysis — cross-family non-free options

**Goal:** Identify Reasoning-lane models that are (a) cross-family, (b) not Grok, (c) potentially compatible with spawn_subagent. The non-parent cross-family Reasoning pool is currently 2 (nemotron, glm).

**In scope:** Survey of Reasoning-lane paid slugs across providers. Candidates: `or-laguna-m1-free`, `gemma-4-31b-it`, `mistral-medium-latest` (excluded — 422), any other Reasoning-lane slugs.

**Out of scope:** Models already in the pool.

**Files / anchors:** `model-fleet-provider-pools.md`.

**Acceptance:** List of 2-3 candidate Reasoning-lane paid slugs with probe plan.

**Falsifier:** Same as TK-SIZE-01.

**Verification level required:** Unit-test-style probe.

**Estimate:** ~10 min.

### TK-SIZE-03: Pool size sweet spot

**Goal:** Determine whether 5 is the right pool size, or whether it's too small (always picks first or second) or too large (slow probing).

**In scope:** Pool-size analysis. Tradeoffs: more members = more diversity but more probe time + more failure modes; fewer members = faster but narrower.

**Out of scope:** Pool size < 3 (insufficient diversity).

**Files / anchors:** `/tp/SKILL.md:243-249`.

**Acceptance:** Recommended pool size with reasoning. Reference: distribution of successful pool member activations across 10+ invocations.

**Falsifier:** Specific claim — "if the pool is too small, the same first member fires 70%+ of the time."

**Verification level required:** STATIC_INSPECTION + operational telemetry.

**Estimate:** ~15 min.

### TK-RANDOM-01: Randomized selection — pros and cons

**Goal:** Analyze whether randomized selection would be better than deterministic.

**Argument FOR randomization:**
- If the first pool member is degraded (slow, low-quality), deterministic always picks it.
- Random spreads load across providers.
- Random makes the pool self-healing against per-model outages.

**Argument AGAINST randomization:**
- Deterministic is reproducible (easier to debug).
- Random may pick a weaker model first.
- Random breaks the user's mental model ("nemotron is the first model").
- Random requires a fairness mechanism (avoid picking the same model twice).

**In scope:** Tradeoff analysis.

**Out of scope:** Implementation.

**Acceptance:** Position on whether randomized, deterministic, or hybrid is best.

**Falsifier:** Specific claim — "if deterministic, the same model fires 80%+ of the time, randomization has merit."

**Verification level required:** STATIC_INSPECTION.

**Estimate:** ~15 min.

### TK-RANDOM-02: Hybrid selection — random first, deterministic fallback

**Goal:** If randomization is preferred, design a hybrid: randomize the first 2-3 picks, then deterministic fallback.

**In scope:** Algorithm design. Options: (a) seeded random from session ID; (b) random with retry (each model fails 2x before being skipped); (c) round-robin with last-used memory.

**Out of scope:** Persistent state across sessions (would require shared file; high cost).

**Acceptance:** Hybrid algorithm with rationale. Pseudocode acceptable.

**Falsifier:** Specific claim — "if the hybrid picks the same model twice in 3 consecutive invocations, the random seed is bad."

**Verification level required:** STATIC_INSPECTION + algorithm walkthrough.

**Estimate:** ~15 min.

### TK-RANDOM-03: Diversity monitoring

**Goal:** Determine how to track which pool member actually serves each /tp invocation, and surface the distribution to the operator.

**In scope:** Telemetry design. Options: (a) write to a JSONL log at a session-scoped temp path; (b) embed in the existing quality-gate trace log; (c) emit via Stop hook event.

**Out of scope:** Real-time dashboards.

**Acceptance:** Recommendation with reasoning.

**Falsifier:** Recommendation is wrong if logging adds >50ms per /tp invocation (impact vs benefit).

**Verification level required:** STATIC_INSPECTION + benchmark.

**Estimate:** ~15 min.

## Open decisions

### D1: Deterministic vs randomized selection (the user's direct question)

**Question:** Should the pool try in fixed order, or randomize?

**Options:**
- **Deterministic** (current) — predictable, reproducible, but always picks nemotron first.
- **Random** — spreads load, self-healing, but less reproducible.
- **Hybrid** (random first 2, deterministic fallback) — best of both, but more complex.

**Selection criterion:** Reproducibility vs. diversity. The /tp critique is a reasoning task where reproducibility matters less than diversity (we want a fresh lens, not a fixed lens).

**Currently leading:** Hybrid (random first 2, deterministic fallback) — but the user has not picked.

**Evidence that would change the lead:** Telemetry on which pool member actually fires most often over 20+ invocations.

### D2: Lane composition (Reasoning-only vs mixed)

**Question:** Should the pool be Reasoning-only, or keep Code-lane models?

**Options:**
- **Reasoning-only** — better fit for the /tp task, but smaller pool, may need to probe new Reasoning lanes.
- **Mixed** (current) — broader family diversity, but Code lane may produce weaker critiques.

**Selection criterion:** Lane fit vs. family diversity.

**Currently leading:** Reasoning-only — but requires probing new Reasoning-lane free models (TK-SIZE-01).

**Evidence that would change the lead:** Empirical critique quality comparison.

### D3: Pool size (5 vs more)

**Question:** Is 5 the right size?

**Options:**
- **5** (current) — fast, but always picks first.
- **8-10** — more diversity, more probe time.
- **3-4** — narrower, faster fallback.

**Selection criterion:** Probe latency vs. diversity.

**Currently leading:** 8-10 (rationale: more diversity, probe latency is <1s per failed spawn).

**Evidence that would change the lead:** Operational telemetry on activation distribution.

## Hard constraints

- **spawn_subagent compatibility is the binding constraint.** Not every model in config.toml works. Pool must be the spawn_subagent-compatible subset only.
- **Multi-model host.** Pool must respect provider quotas. Don't add a model that will 429 after 1 call.
- **Edit-verify pattern.** Any change to `/tp/SKILL.md` requires read-back verification.
- **No destructive git.** This is a shared multi-agent workspace.
- **Original handoff scope.** `/tp` is the orchestrator's skill; investigation is the work, not modification.
- **The user's framing was honest.** "Why isn't the choice random" is a real question, not a leading question. Treat it as an open design decision, not a directive.

## Cross-reference couplings

- `/tp/SKILL.md:243-249` (pool table) → depends on this handoff's recommendation. If the recommendation is "add model X," this table changes.
- `~/.grok/tool-fallbacks.md:59-60` (spawn_subagent compatibility) → feeding TK-SIZE-01/02. If `tool-fallbacks.md` is updated with new probes, this handoff's gap analysis is stale.
- Parent handoff `tp-model-pool-not-inline-fallback-20260722` → the pool exists because of this. If the closed handoff is reopened, the relationship is direct.
- This handoff's `accurate_as_of_head: 86f1ac13c9b6fcacf700be88a37a6725cd9a968c` → if HEAD moves, re-verify cited paths before acting.

## Other outstanding streams (not handed off)

- **Quality gate hook continued development** — multiple `stop-hook-*` handoffs in `P:\docs\handoffs\`. The user has been iterating on the verification/recipe gating. Not in scope for this handoff.
- **Skill consolidation / skill-location audit** — `skill-consolidation-20260722`, `skill-location-audit-and-optimization-20260722`. The user mentioned "we have a handoff project, but we are not ready for that yet." Not in scope for this handoff.
- **/www backends (DDG, Exa, Tavily, Brave)** — `www-skill-add-youtube-ddg-backends-20260722`. This turn made the fan-out recipe structural. Not in scope for this handoff.

## Explicit non-goals

- **Do NOT modify `/tp/SKILL.md` in this thread.** The work is investigation + recommendation. Implementation is a separate thread.
- **Do NOT modify `tool-fallbacks.md` in this thread** (probes can be run, but the table update is part of the implementation handoff).
- **Do NOT add new models to the pool.** Wait for the user to pick a path.
- **Do NOT implement hybrid selection.** Recommendation only.
- **Do NOT add /tp telemetry now.** Investigate first; implement after user approves.

## Resumption protocol

1. Read the parent handoff first (the closed one — pool exists, here are constraints).
2. Read `/tp/SKILL.md:220-260` (current pool implementation).
3. Read `tool-fallbacks.md:57-77` (binding constraint).
4. Run TK-COMPOSITION-01 through TK-COMPOSITION-03 (lane, family, cost-regime analysis) — these are fast (~70 min total).
5. Run TK-SIZE-01 through TK-SIZE-03 (gap analysis + size) — these require probes (~50 min).
6. Run TK-RANDOM-01 through TK-RANDOM-03 (randomness analysis) — these are reasoning-only (~45 min).
7. Produce a single recommendation with evidence: "Pool should be [X models] in [Y order] with [Z selection algorithm]."
8. Surface the recommendation to the user. **Do NOT modify `/tp/SKILL.md`** until the user picks a path.

## Suggested next invocation

```
Investigate the /tp spawn_subagent pool composition. Read the parent handoff
at P:\docs\handoffs\tp-model-pool-not-inline-fallback-20260722\HANDOFF.md first.

The user has raised three questions:
1. Are the models right? (lane fit, family diversity, cost regime)
2. Are there enough? (gap analysis against the 48-model fleet)
3. Why isn't the choice random? (deterministic vs randomized vs hybrid)

Run task packets TK-COMPOSITION-01 through TK-RANDOM-03. Probe new models
where indicated (TK-SIZE-01, TK-SIZE-02). Then produce a single recommendation.

DO NOT modify ~/.grok/skills/tp/SKILL.md. The work is investigation only.
The implementation handoff forks after the user picks a path.
```

## Last user message (verbatim)

> "add a handoff file to look at fixing the spawning pool for '/tp'.  are the models right, are there enough, why isn't the choice random?"

## Epistemic labels per claim

- [FACT] Pool composition (5 members, lanes, costs) — verified by direct read of `/tp/SKILL.md:243-249`.
- [FACT] Pool is deterministic — verified by direct read of `/tp/SKILL.md:251-256`.
- [FACT] Pool probed 2026-07-22 — verified by direct read of `/tp/SKILL.md:236-242`.
- [FACT] User cancelled the nemotron-3-ultra spawn this session — observed in the tool call history.
- [FACT] Known-broken slugs — verified by direct read of `tool-fallbacks.md:59-60`.
- [INFERENCE] The user's "why isn't the choice random" question implies preference for randomization.
- [INFERENCE] The user's cancellation of the nemotron-3-ultra spawn was motivated by the deterministic-always-first pattern.
- [INFERENCE] Lane fit (Reasoning vs Code) is correlated with critique quality — but not directly verified.
- [INFERENCE] Family diversity (4 cross-family + 1 same-model) is sufficient for lens diversity — but the threshold is unverified.
- [UNKNOWN] Empirical critique quality comparison across lanes — not measured.
- [UNKNOWN] Optimal pool size — depends on operational telemetry not yet collected.
- [UNKNOWN] Whether the user prefers randomized, hybrid, or current deterministic — not explicitly stated.
