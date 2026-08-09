# Review-Relay Improvements Design — Variant A: Dumb Pipe Preserved

**Variant:** A — relay remains a findings-agnostic, opaque-pipe transport; all new behavior lives in the skill and partner agents.
**Source concept:** `[[review-relay-improvements-stable-key-lease-calibration-convergence-detection]]`
**Inputs:** `evidence-brief.md`, `premise-verification-brief.md`, `domain-knowledge-brief.md`, `preflight-inventory.json`
**Date:** 2026-08-09
**Author role:** Senior software architect (Writer A in 3-variant design exercise)

---

## 0. Premise Acknowledgments

- **[FACT]** The relay (`P:/packages/codex-external-delegation/src/review-relay.mjs`) does not parse, inspect, or mutate findings. Findings appear only as opaque fields inside `result.json` (premise-verification brief #8, evidence-brief §5).
- **[FACT]** `ready_for_parent_review` is a **status enum value** in `result.status`, not a boolean field. The valid statuses are: `"failed" | "timed_out" | "ready_for_parent_review" | "expired" | "needs_review" | "submitted" | "partial" | "blocked"` (premise-verification brief #3).
- **[FACT]** The convergence auto-detection heuristic is documented in `~/.grok/skills/review-relay/SKILL.md:438-446`, not in the relay (premise-verification brief #5).
- **[FACT]** No notion of "section" or "per-section parallel review" exists in the relay (premise-verification brief #7).
- **[RESEARCH]** Pattern names ReviewingAgents, POIROT, GPT Researcher are real multi-agent frameworks per `domain-knowledge-brief.md`; treated as design inspirations, not authoritative citations for naming.
- **[INFERENCE]** Premise 10/11 (per-section parallel review may need splitProposal vs relay primitive) — answered below as a sidecar-file approach.
- **[UNKNOWN]** Premise 12 (`write_policy.forbidden_writes` semantics) — flagged in Open Questions.

---

## 1. Design Intent Contract

### Goal

Improve review-relay coordination in three measurable ways while keeping the relay itself an opaque-pipe transport:

1. **Finding lifecycle tracking** — prevent partners from re-verifying corrections they already agreed on, by exposing a durable, append-only per-session `findings.jsonl` sidecar that carries each finding's lifecycle state (`open | rebutted | upheld | resolved | superseded`).
2. **Continuous convergence score** — give the coordinator (and the operator-facing log) a numeric, weighted measure of how close the relay is to convergence, computed entirely from result history by the skill. The relay's existing status enum remains the only gate; the score is advisory.
3. **Per-section parallel review** — let partners concentrate on different proposal sections in parallel, by splitting the proposal into N section-files *before* the relay starts and merging per-section reviews *after*.

### Success Metrics (revised — Finding 1)

Metrics measure **user-pain reduction**, not preservation. The "0 lines added to relay" target moves to Non-Goals (it's a constraint, not a metric).

| Metric | Target | Measured by | Baseline (current state) |
|---|---|---|---|
| **Re-verification rate** — partners re-introducing previously-resolved findings | **0** per session | grep `findings.jsonl` for re-entries into `state:"resolved"` | Wiki concept: 42 findings / 16 turns, multiple re-introductions observed |
| **Operator file-read burden per convergence check** — files the operator must read to assess "are we done?" | **1 file** (`convergence_history.jsonl` via dashboard helper) | `__lib/dashboard.mjs::status()` invocation count | Wiki concept: 7 result.json files per convergence check |
| **Time-to-convergence** — wall-clock from review-init to `ready_for_parent_review` | **≤ 50%** of pre-design baseline on converged runs (was 7+ sessions) | timestamp diff from `event.json` review_initialized → last turn `ready_for_parent_review` | Pre-design baseline: ≥7 sessions (one per content edit) |
| **Partner prompt adoption rate** — % of partner turns that read `previous_findings_path` (when non-null) | **≥ 95%** within 30 days of Phase 2 | instrumented partner prompt logs `read_attempted: true` to scratchpad | Pre-design: 0% (no sidecar exists) |
| **Section-split wall-clock speedup** — 4-section split review wall-clock vs whole-doc baseline | **≤ 50%** of whole-doc wall-clock (realistic, not 25%) | end-to-end timing on test proposal | Pre-design: no split exists; whole-doc baseline only |
| **Existing test suite** | 100% pass without modification | `pnpm test` | Already 100% (must stay there) |

**Removed metric:** "0 lines added to `src/review-relay.mjs`" — this is a *constraint* (preserved as a Non-Goal below), not a *success metric*. Counting lines not added measures preservation, not improvement.

### Non-Goals (constraint inventory — preserved as design invariants, not measured as success)

- **The relay does not become an inspecting pipe.** No relay-level code reads or interprets finding content. (Premise #8, enforced.)
- **No replacement of `result.status` enum.** `ready_for_parent_review` keeps its meaning; the convergence score is an additional field, not a replacement. (Premise #3, enforced.)
- **No new role kinds.** The two-actor model (`first_actor` + `other`) is unchanged. Section-splitting happens *before* relay start; each section-review is a fresh two-actor relay.
- **No backward-incompatible relay schema change.** `RESULT_SCHEMA_VERSION` is bumped only when the *partners* need to read a new field. The relay itself tolerates the new field as opaque content.
- **No new filesystem primitives.** All new state lives in existing bucket paths (`findings.jsonl`, `convergence_history.jsonl`, `sections/<n>/`), no new lock files, no new atomic-write contracts.
- **No new lines in `src/review-relay.mjs`.** This is a *constraint* on the design, not a *goal* — measured by `git diff`, but the design succeeds without it. If the optimal long-term solution requires a relay change, this constraint yields. See §2 Architectural Justification for the framework that decides when.
- **Dumb-pipe subtlety preserved.** Although `previous_findings_path` (Component 1) is an additional input field on the tick surface, the relay does not parse, validate, or interpret its contents. The path is a string the relay passes through opaquely, identical to how it already passes `previous_result_path`. The relay's input contract for *content* is unchanged; only the set of opaque string fields grows. See §1.5 below.
- **All sidecar files use plain UTF-8.** `findings.jsonl`, `convergence_history.jsonl`, `merged-findings.jsonl`, and section proposal files must be plain UTF-8 with no BOM, no compression, and no encryption. This avoids cross-tool I/O errors (PowerShell default `cp1252` is unsafe; Python `open(..., encoding='utf-8')` is required).

### Failure Conditions (revised)

- **A user-pain metric regresses** (e.g., re-verification rate rises, time-to-convergence grows) → design failed; rollback.
- **Coordinator declares `ready_for_parent_review` on a proposal where partner prompt adoption rate is <50%** → adoption failure; require prompt-update PR before continuing.
- **Section-split review on a coupled document produces incoherent merged findings** → splitProposal coupling detection failed; fall back to whole-proposal review for that document.
- **Score < 0.7 on a converged run OR > 0.85 on a stuck run** → weights miscalibrated; trigger Phase 1.5 re-validation.
- **Any relay source file modified without §2 Architectural Justification approval** → invariant violated; revert and document.

### What Success and Failure Look Like

- **Success:** A future session on a 7-iteration proposal sees 0 partner turns that re-introduce a previously `resolved` finding; coordinator reads 1 dashboard file (not 7 result.json files) to assess convergence; section-split review on a 4-section design doc finishes in ≤ 50% of the whole-doc wall-clock time; relay code is byte-identical *unless* §2 Architectural Justification approves a change.
- **Failure:** Partners ignore the sidecar and re-verify (adoption rate <50%), OR the operator's reading burden increases (5+ files instead of 1 dashboard), OR the section-split produces incoherent findings on coupled documents, OR the score drives wrong decisions on real work (unvalidated weights shipped without Phase 1.5).

### Encoding, Bucket Convention, and Opaque-Field Discipline

**Bucket base convention.** Every bucket path in this design is derived from the relay's existing helper, `registryBucket(reviewKey)` (evidence-brief §1, review-relay.mjs:763). For this design, `reviewKey` continues to be the path-derived hash, and the bucket root is the relay's `registryRoot`. No new base path is introduced. Section files live under `<bucket>/sections/<n>/` *inside* the bucket, not as a new top-level path. The helper `getBucketBase(reviewKey)` is **a thin wrapper around `registryBucket`** — same path, different name for clarity in the skill-side helpers. Documented in `__lib/findings.mjs` and `__lib/convergence.mjs` headers.

**Opaque-field discipline.** `previous_findings_path` joins the relay's existing set of opaque string fields: `previous_result_path`, `previous_result_actor`, `previous_result_hash`. The relay treats all of these as pass-through strings. Partners that opt into reading `previous_findings_path` use a `read()` call on the resolved path; partners that don't ignore it. The relay never inspects the bytes. This satisfies F-08: the dumb-pipe invariant holds at the content level even when the input surface grows by one more opaque string.

**Encoding.** All new files use UTF-8, LF line endings, no BOM. Python helpers open with `encoding='utf-8'`. Node helpers use `fs.writeFileSync(path, content, 'utf8')`. This is consistent with the relay's existing `atomicWriteJson` (evidence-brief §3).

### Falsifiability (Finding 5)

The design's success metrics are observable. The design's *failure conditions* are observable. But the design is **partly** falsifiable — metrics measure improvement, not value. The following falsifiers (per the critical-friend review §3) name specific observations that would prove the design failed to deliver value:

| Falsifier | Observation | Implication |
|---|---|---|
| **F-1: Sidecar doesn't move the metric** | After Phase 2 ships, run 5 production sessions. If re-introduction rate of resolved findings is unchanged from baseline (the 42-finding/16-turn session), the sidecar is **infrastructure without benefit**. | The 1330 LoC of helpers are pure cost. Trigger: revert U-1 or escalate to partner-prompt redesign. |
| **F-2: Score is inverted** | After Phase 1.5 validation, run 5 production sessions. If converged runs (status `ready_for_parent_review`) score <0.7 on average AND stuck runs score >0.85, the score is inverted. | Unvalidated weights drive wrong decisions on real work. Trigger: re-tune via `REVIEW_RELAY_WEIGHTS` env override; if tuning fails, revert to heuristic-only. |
| **F-3: Per-section parallel is slower** | Run a 4-section split review on a real design doc. If parallel wall-clock is >50% of whole-doc baseline (the realistic, not optimistic, target), the speedup claim fails. | Component delivers coordination overhead, not speedup. Trigger: re-tune N cap (lower from 4 to 2); if still slow, revert. |
| **F-4: Multi-coordinator collision fires silently** | Two operators launch coordinators on the same proposal path without `opts.session_id`. Findings interleave; scores collide. Lifecycle state corrupts silently. | The opt-in session_id is insufficient. Trigger: switch to default-on (always include a session_id derived from `process.pid` + timestamp), or migrate to claim-by-script. |
| **F-5: Premise #12 was structurally unworkable** | (RESOLVED — see §6.10 #1) The premise was structurally OK; partners can write findings.jsonl via `turns/**` allow-list. Skill-written sidecars are not subject to write_policy. **This falsifier did not fire.** | N/A — premise resolved. |

**Combined falsifier for the whole design:** ship U-1..U-5, run 5 production sessions, measure all 5 user-pain metrics. If ≥3 regress or fail to improve over baseline, the design as a whole failed. Trigger: comprehensive rollback to Phase 0 (helpers-only, no partner adoption).

---

## 2. Architecture Summary

### The Dumb-Pipe Invariant

`review-relay.mjs` continues to expose only: `tick`, `submit`, `inspectState`, lease/receipt lifecycle, snapshot hashing. No new fields parsed. No new schema branches. No finding-level state machine.

### Where Each Improvement Lives

| Improvement | Lives in | Touches relay? |
|---|---|---|
| Finding lifecycle state | Sidecar `findings.jsonl` in bucket; partners read/write via existing scratchpad mechanism | No |
| Convergence score | New `convergence_history.jsonl` in bucket; computed by `~/.grok/skills/review-relay/__lib/convergence.mjs` from result history | No |
| Per-section split | Skill-side helper `__lib/split.mjs` produces `sections/<n>/*.md` files; relay runs N independent sessions on those files | No (relay sees each section as an ordinary proposal) |

### Why This Shape

- **Test stability** — relay tests in `tests/review-relay.test.mjs` are unaffected.
- **Backward compatibility** — existing two-actor sessions behave identically; the new helpers are opt-in.
- **Separation of concerns** — partner skill author writes findings; coordinator skill computes score; neither bleeds into the relay's transport contract.
- **Cost** — partner prompts grow by ~200 tokens (findings.jsonl reading instructions); coordinator gains ~100 tokens (convergence decision logic); section-split adds a coordinator step.

### What This Preserves vs Costs

**Preserves:** relay's findings-agnostic invariant; existing test suite; `result.status` semantics; lease logic; snapshot hashing; two-actor model.

**Costs:** partner-side complexity (must read+write sidecar); coordinator-side complexity (must compute score from history); operator must inspect `findings.jsonl` and `convergence_history.jsonl` directly since `inspectState` does not surface them (by design — the relay stays opaque).

### Architectural Justification for Dumb-Pipe Preservation (Finding 2)

The critical friend correctly identified that premise #8 ("the relay has never inspected findings") describes a historical pattern, not an architectural decision. The relay never inspected findings *because nothing required it to*. This section argues that **preserving the dumb-pipe invariant is the right long-term answer** anyway, with a graceful migration path documented for the case where future requirements force inspection.

**Argument 1: The relay's transport contract is documented and stable.** The contract surface — `tick`/`submit`/`inspectState`, lease lifecycle, snapshot hashing, `atomicWriteJson` — has been stable across N sessions and 7+ design iterations since 2026-08-08 (premise-verification brief #1, #2, #3). Stability of the transport contract is a **documented feature**, not an absence of code. Operators and partners depend on it.

**Argument 2: Future requirements can be met with sidecars.** The convergence score (Component 2) demonstrates this: a new requirement (numeric convergence signal) is met by adding a sidecar file and a skill-side helper, without touching the relay. This is the same pattern that `wiki/concepts/design-choice-audit-challenge-every-decision-against-first-principles.md` documents for handoffs: state discipline lives in skill-side files, not in the transport. Future requirements (cross-section correlation, adaptive lease, finding provenance, convergence prediction) **can** be met with additional sidecars — at the cost of `O(requirements)` files, not `O(requirements)` relay changes.

**Argument 3: Smart-pipe migration has higher future cost than sidecar accumulation.** Refactoring the relay to inspect findings is irreversible (changing what the relay *means*), and breaks every partner that has integrated against the opaque contract. Adding sidecars is reversible (delete a file) and additive (new partners ignore old sidecars). The cost ratio is at least **10:1 in favor of sidecars** for any specific future requirement, because the relay's existing partner integrations (the handoff pattern, the review-relay skill, external partner integrations) all depend on the opaque contract.

**Argument 4: Workspace pattern — smart components orchestrated BY skills, dumb components EXECUTED BY skills.** The workspace convention (per `wiki/concepts/llm-handoff-best-practices.md` §"Implications for a solution architect operating a fleet") is: skills are smart (compute, decide, validate); transports are dumb (move bytes, enforce leases, validate hashes). The relay is a transport. Making it smart violates the convention. Skill-side helpers (`findings.mjs`, `convergence.mjs`, `split.mjs`, `merge.mjs`) honor the convention.

**Argument 5: The dumb-pipe invariant is testable.** `git diff src/review-relay.mjs` returning empty is a one-line assertion. Smart-pipe migration requires re-deriving the entire test surface.

### Graceful Migration Path (the safety net for Finding 2)

If future requirements force relay inspection (and the above arguments fail), the migration path is:

1. **Add a parallel mechanism first.** Ship a *skill-side* finding state machine (this design) and let it accumulate usage.
2. **Promote to relay-side when adoption justifies it.** When ≥5 model pools, ≥3 sessions/week, and ≥30 days of production usage show the skill-side mechanism is bottlenecking, migrate the state machine into the relay as an opt-in parser gated by a new manifest flag (`write_policy.findings_state_machine: "skill" | "relay"`).
3. **Deprecate the skill-side mechanism** only after the relay-side mechanism is stable for ≥30 days. Keep `findings.jsonl` as the wire format; only the parser location moves.

**The migration is reversible at every step** — the wire format (`findings.jsonl`) is the contract; the parser location (skill or relay) is implementation. The cost of migration is bounded; the cost of *premature* smart-pipe adoption (this design's first attempt) is unbounded.

**Decision rule (encoded in DEC-12):** ship dumb-pipe first. Promote to smart-pipe only when (a) the skill-side mechanism has been a production bottleneck for ≥30 days AND (b) at least one of the cross-section-correlation / adaptive-lease / finding-provenance future requirements has materialized. Until then, dumb-pipe is the right answer.

---

## 3. Component 1 — Finding Lifecycle Tracking (ReviewingAgents pattern)

### Contract

**New sidecar file:** `<bucket>/findings.jsonl`

**Record schema:**
```json
{
  "finding_id": "F-001",
  "state": "open | rebutted | upheld | resolved | superseded",
  "raised_by": "actor_name",
  "raised_in_turn": 3,
  "claim": "string (opaque to relay)",
  "evidence_path": "string (opaque)",
  "transitions": [
    { "to_state": "upheld", "by_actor": "actor_name", "in_turn": 4, "note": "string" }
  ],
  "supersedes_id": "F-000 | null"
}
```

**State machine (validated in skill, not relay):**
```
open ──(partner rebuts)──▶ rebutted ──(partner upholds)──▶ upheld ──(partner resolves)──▶ resolved
 │                              │
 │                              └─(partner withdraws)──▶ superseded
 └─(partner withdraws)──▶ superseded
```
Terminal states: `resolved`, `superseded`. Transitions are append-only.

### How Partners Use It

1. Partner reads `findings.jsonl` at start of turn (in addition to `previous_result_path`).
2. For each finding in `open` or `rebutted` state raised by the *other* actor, partner decides: uphold, rebut, resolve, supersede.
3. Partner writes one JSONL record per transition to `findings.jsonl` inside its active scratchpad before submission.
4. The relay's existing submit flow copies the sidecar forward with `previous_result_path`-equivalent behavior: partners see prior turn's full `findings.jsonl` via a new `previous_findings_path` field in the tick input.

**Concrete partner-prompt template (the path is exposed as a templated string the partner's tool-using model reads):**

```markdown
## Prior findings (lifecycle state)

The previous partner's `findings.jsonl` is at:

  `{{previous_findings_path}}`

If the path is `null` (turn 1) or the file does not exist, treat the prior
findings list as empty and proceed without reading it.

To read it, use your `read` tool with that exact path. The file is JSONL;
each line is a self-contained record. Do not interpolate or modify the
path string before passing it to `read`. If the file is corrupt (a line
fails to parse), skip that line and log a warning to your scratchpad.
```

The partner skill `~/.grok/skills/review/SKILL.md` (U-5) carries this template verbatim. A unit test `test_partner_prompt_template.mjs` substitutes `{{previous_findings_path}}` with a fixture path and asserts that the resulting string contains the path unaltered — preventing template-engine regressions.

### New Tick Field (in the relay's existing tick surface)

| Field | Type | Meaning |
|---|---|---|
| `previous_findings_path` | string \| null | Absolute path to prior turn's `findings.jsonl` (or `null` on turn 1) |

The relay **does not parse this field** — it passes it through to the partner like every other input. Partners that don't read it ignore it; partners that do read it see lifecycle history.

### Sidecar File Persistence Across Turns

- Each turn writes its own scratchpad copy to `<bucket>/turns/<n>/active/findings.jsonl`.
- On submit, the controller copies the latest active `findings.jsonl` forward as `previous_findings_path` for the next turn.
- This mirrors how `previous_result_path` already works; no new relay mechanism.

**Write-policy check (mandatory before U-1 lands).** Before implementing U-1, the implementer must verify (a) the partner's active scratchpad `<bucket>/turns/<n>/active/` is permitted by `write_policy.forbidden_writes`, and (b) the controller's copy-forward logic (the same code that copies `result.json` forward) is extended to also copy `findings.jsonl`. If (a) fails, add an explicit allow-rule for `findings.jsonl` inside the active scratchpad (NOT for the bucket root — partners must not write outside their own active dir). If (b) fails, file a code-review finding: the sidecar cannot work without copy-forward.

**Missing-path fallback (mandatory in `__lib/findings.mjs`).** When a partner's tick arrives with `previous_findings_path: null` (turn 1), or with a path that does not resolve (`fs.existsSync` returns `false`), or with a file that is unreadable, `findings.readAll()` returns `{ records: [], warning: "<reason>" }`. The coordinator logs the warning to its scratchpad and proceeds. **Partners never crash on a missing path** — that is the contract.

**Bucket-root discipline.** All new files live *inside* `registryBucket(reviewKey)`. Section files use `<bucket>/sections/<n>/proposal.md`. Findings sidecar uses `<bucket>/turns/<n>/active/findings.jsonl`. Convergence history uses `<bucket>/convergence_history.jsonl`. The helper `getBucketBase(reviewKey)` in `__lib/findings.mjs` and `__lib/convergence.mjs` returns the same string as the relay's `registryBucket(reviewKey)` — they are aliases, not new paths. This prevents the multi-coordinator overlap risk that F-05 flags.

---

## 4. Component 2 — Continuous Convergence Score (POIROT pattern)

### Premise Correction (already integrated)

`ready_for_parent_review` is a **status enum value**, not a boolean. The design does **not** replace it. The convergence score is a **new advisory field** that the coordinator reads; the relay's status gate is unchanged.

### Score Computation (skill-side, in `__lib/convergence.mjs`)

Inputs:
- All `result.json` files for the review session (ordered by turn)
- All `findings.jsonl` records (Component 1)
- The number of distinct actors that have submitted ≥ 1 turn

Output: a record appended to `<bucket>/convergence_history.jsonl`:
```json
{
  "turn": 4,
  "computed_at": "ISO-8601",
  "score": 0.0,
  "components": {
    "finding_overlap_delta": 0.0,
    "actor_coverage": 0.0,
    "engagement_depth": 0.0
  },
  "weights": { "finding_overlap_delta": 0.5, "actor_coverage": 0.3, "engagement_depth": 0.2 }
}
```

### Component Definitions

| Component | Definition | Range | Computed from |
|---|---|---|---|
| `finding_overlap_delta` | 1 − (new findings this round / max(new,1) + still-open from prior round) | [0, 1] | result.json `findings` arrays, findings.jsonl `state` field |
| `actor_coverage` | actors with ≥ 1 turn / total declared actors | [0, 1] | manifest.actors |
| `engagement_depth` | min(turns_since_last_new_finding / 3, 1) | [0, 1] | finding timestamps |

**Weighted sum:** `score = 0.5*overlap + 0.3*coverage + 0.2*depth`. Weights are configurable via the skill's tuning constants.

### Weight Tuning (F-03)

The 0.5 / 0.3 / 0.2 defaults are reasoned but not empirically validated. To prevent silent mis-tuning, the helper exposes them as exported constants and reads overrides from an environment variable:

```javascript
// __lib/convergence.mjs
export const DEFAULT_WEIGHTS = Object.freeze({
  finding_overlap_delta: 0.5,
  actor_coverage: 0.3,
  engagement_depth: 0.2,
});

// Read at runtime; JSON-encoded, validates sum = 1.0 ± 0.001
export function loadWeights(env = process.env) {
  if (!env.REVIEW_RELAY_WEIGHTS) return DEFAULT_WEIGHTS;
  const parsed = JSON.parse(env.REVIEW_RELAY_WEIGHTS);
  const sum = Object.values(parsed).reduce((a, b) => a + b, 0);
  if (Math.abs(sum - 1.0) > 0.001) {
    throw new Error(`REVIEW_RELAY_WEIGHTS must sum to 1.0, got ${sum}`);
  }
  return parsed;
}
```

**Tuning recipe (operator-facing, ~10 min on a test proposal):**
1. Run a 6-turn review with default weights; record per-turn score from `convergence_history.jsonl`.
2. Inspect the distribution: if converged runs cluster around 0.7-0.8 and stuck runs cluster around 0.5-0.6, the weights discriminate well — keep defaults.
3. If scores are uniformly high (≥ 0.9 on non-converged runs), increase `finding_overlap_delta` weight (the overlap signal is being diluted).
4. If scores are uniformly low (< 0.5 on converged runs), increase `engagement_depth` weight (depth is the discriminator you're missing).
5. Export the working weights via `REVIEW_RELAY_WEIGHTS='{"finding_overlap_delta":0.6,"actor_coverage":0.25,"engagement_depth":0.15}'` in the coordinator's launch env.

**Telemetry.** `__lib/convergence.mjs` also exports `exportScoreDistribution(bucket)` which returns `{turn: N, score: S, components: {...}}[]` for offline analysis. No relay-side exposure; the operator runs the helper directly.

### Coordinator Decision Rule (revised — Finding 4)

```
IF score >= 0.85 AND last result.status not in {failed, timed_out, blocked}
   AND all declared actors have ≥ 1 turn
   AND Phase 1.5 validation has completed for this weight set
THEN coordinator may set status="ready_for_parent_review"
ELSE coordinator continues the relay
```

**The score is advisory, NOT the sole signal** (DEC-7 strengthened, Finding 4):
- The coordinator **MUST NOT** use the score as the sole input to the `ready_for_parent_review` decision.
- The coordinator **MUST** cross-check the score against at least one of: (a) zero new findings in the last complete round (the existing heuristic), (b) all open findings have `state: "upheld"` or `state: "resolved"` in `findings.jsonl`, (c) explicit operator override logged to the coordinator's scratchpad.
- A score ≥ 0.85 with any contested finding (`state: "open" | "rebutted"` for the same finding across two actors) **MUST NOT** trigger `ready_for_parent_review`.
- The relay's hard gate (`enforceParentReviewGate`) still requires all actors to have a committed turn and no high-severity findings open.

**Rationale:** "advisory" ≠ harmless. The critical friend's Pre-Mortem §5 scenario 2 documents that humans (and LLMs) treat numerical signals as evidence. Unvalidated weights + a single-signal decision rule produce wrong decisions on real work. The cross-check requirement forces the coordinator to read at least one more input, mitigating the single-signal failure mode.

**Phase 1.5 validation gate (new):** the `AND Phase 1.5 validation has completed` predicate in the decision rule means: until the score weights have been validated on ≥3 test proposals (per Phase 1.5 in §6.9), the score contributes 0 to the decision — the coordinator uses the existing heuristic only. This prevents F-2 (inverted score) from driving production decisions.

### Why No Relay Change

- `inspectState` does not surface the score. Coordinators read `convergence_history.jsonl` directly.
- The score never participates in the relay's status gate logic.
- If the score file is missing or malformed, the relay runs exactly as today.

### Operator Reading Burden: Dashboard Helper (Finding 6)

The design adds 4 new files to the operator's reading load (`findings.jsonl`, `convergence_history.jsonl`, `merged-findings.jsonl`, `merged-convergence.json`). Per the critical-friend Pre-Mortem §5 scenario 7, **the operator's reading burden must decrease, not increase**, for the design to deliver on its wiki-concept pain-point ("operator had to manually read 7 result JSONs").

**Solution: `__lib/dashboard.mjs` consolidates the operator's view into a single file.**

```javascript
// __lib/dashboard.mjs
export function status(bucket) {
  const findings = readFindingsSummary(bucket);     // {open, rebutted, upheld, resolved, superseded}
  const score = readLastScore(bucket);              // {score, components, weights, turn}
  const merged = readMergedSummary(bucket);        // null or {sections: N, score_min: X}
  const review = readReviewMeta(bucket);            // {review_id, started_at, last_turn, actors}
  return {
    review_id: review.review_id,
    elapsed: now() - new Date(review.started_at),
    findings: findings,
    score: score,
    merged: merged,
    next_action: deriveNextAction(findings, score, merged),
  };
}
```

**`next_action` derivation:**
- If `merged && merged.score_min >= 0.85 && findings.open === 0` → `"declare ready_for_parent_review"`
- If `findings.open === 0 && findings.rebutted === 0 && score.score >= 0.85` → `"declare ready_for_parent_review"`
- If `findings.open > 0 && findings.rebutted === 0` → `"await next actor's rebuttal"`
- If `findings.rebutted > 0` → `"mediate dispute"` (use coordinator judgment)
- Else → `"continue relay"`

**Operator flow change:** instead of reading 7 result JSONs + 4 new files, the operator runs `node -e "import('./__lib/dashboard.mjs').then(m => console.log(JSON.stringify(m.status(process.argv[1]), null, 2)))" <bucket>` and reads 1 JSON output. The helper is **a pure function** — no relay state, no partner state, no I/O beyond reading sidecars. Phase 1 ships the helper alongside `findings.mjs` and `convergence.mjs`.

**Operator reading burden metric:** measured by the success metric in §1 — "1 file = `convergence_history.jsonl` via dashboard helper, down from 7 result.json reads." The dashboard helper is the implementation of that metric.

---

## 5. Component 3 — Per-Section Parallel Review (GPT Researcher pattern)

### Premise Choice

Two implementations are possible:

**Option A (chosen):** Skill-side `splitProposal` divides the proposal into N section-files; coordinator runs N independent relay sessions in parallel; `mergeReviews` combines results. Relay sees each section as an ordinary single-proposal review.

**Option B (rejected):** Add a section-aware dispatch primitive to the relay. Rejected because it deepens relay responsibility, breaks dumb-pipe invariant, and adds a parallel-coordination primitive that doesn't exist in the controller today.

### Contract: `splitProposal(proposalPath, sections)` (skill helper)

Input: a markdown proposal file + a list of section headings (or a heading regex).

**Step 1: Coupling analysis (Finding 10).** Before splitting, `splitProposal` analyzes cross-section references. Design docs often have Section 3's "the contract MUST validate inputs" depending on Section 1's "the contract is the JSON schema in Appendix B" — a finding in Section 3 cannot be evaluated without Section 1.

```javascript
// __lib/split.mjs
export function analyzeCoupling(proposalText, sections) {
  const refs = detectCrossSectionReferences(proposalText, sections);
  // Returns: [{from_section: 3, to_section: 1, type: "term_reference" | "contract_reference" | "example_reference", weight: 0.0-1.0}]
  //   where weight = (# of cross-section mentions) / (# of section's total references)
  return refs;
}

export function splitProposal(proposalPath, sections, opts = {}) {
  const coupling = analyzeCoupling(readFile(proposalPath), sections);
  const coupledSections = sections.filter(s =>
    coupling.some(c => (c.from_section === s.n || c.to_section === s.n) && c.weight >= 0.3)
  );
  if (coupledSections.length > 0 && !opts.force_split) {
    return {
      ok: false,
      reason: "cross_section_coupling_detected",
      coupled_sections: coupledSections,
      suggestion: "fall_back_to_whole_proposal",
      coupling_report: coupling,
    };
  }
  // ... existing split logic
}
```

**Coupling detection heuristic (lightweight):**
- For each section, scan for mentions of other sections' titles, terms introduced in other sections, or contract names defined in other sections.
- A section is "coupled" if ≥30% of its references point to another section.
- If any section is coupled, `splitProposal` returns `{ok: false}` with a coupling report. The coordinator falls back to whole-proposal review for that document.
- If `opts.force_split === true`, the split proceeds anyway and the coupling report is included in the manifest for partner prompts to reference.

**Partner prompt impact:** when a section is split despite coupling, the partner prompt includes a "context preamble" listing the cross-section references. This gives the partner enough context to evaluate findings that depend on other sections, without requiring it to re-read the whole proposal.

**Cost:** the coupling analysis is ~50 LoC of regex/keyword matching. False-positive rate is acceptable (over-detection → falls back to whole-proposal, conservative). False-negative rate is bounded by the 30% weight threshold.

Output: `<proposal-dir>/sections/<n>/proposal.md` for each section, where each file contains the section's heading + body, plus a `sections/manifest.json`:
```json
{
  "split_at": "ISO-8601",
  "proposal_hash": "sha256",
  "coupling_report": [
    { "from_section": 3, "to_section": 1, "type": "contract_reference", "weight": 0.42 }
  ],
  "sections": [
    { "n": 1, "title": "Design Intent", "path": "sections/1/proposal.md", "anchor": "#design-intent" }
  ]
}
```

### Contract: `mergeReviews(reviewDir, sections)` (skill helper)

Input: the per-section review directories + the manifest.

Output: a single `merged-findings.jsonl` combining all section findings, and a `merged-convergence.json` with the **worst-of-N** convergence score.

**Worst-of-N definition (precise).** The merged `score` is `min(score_section_1, ..., score_section_N)`. If any section's review has not yet produced a `convergence_history.jsonl`, that section contributes `0.0` to the minimum. The merged score is the *minimum* (most conservative) because a single non-converged section invalidates the whole proposal's readiness claim. This resolves F-07: "worst" means `min`, not `max` and not `median`. Documented in `__lib/merge.mjs` header.

### Coordinator Workflow

```
1. splitProposal → N section-files
2. Launch N parallel `tick-and-submit` loops (one per section), each using a fresh reviewKey
3. After all N converge (per Component 2), call mergeReviews
4. Coordinator proceeds with merged findings as if it were a single review
```

### Why No Relay Change

- The relay runs unchanged on each section-file. The section split is invisible to the relay.
- Each section-review uses its own `reviewKey` (path-derived, so stable across turns within that section).
- The merge step is a pure post-processing transform on finding JSONL records; no relay API needed.

### ReviewKey Collision Avoidance for Parallel Section Reviews (F-02)

The path-derived `reviewKey` (evidence-brief §1) is `sha256(stableStringify(sortedPaths)).slice(0, 16)`. For N parallel section-reviews on N different section-files, the paths differ, so the keys differ — no collision.

**The collision risk F-02 raises is real only in one case:** an operator starts *two* parallel coordinators on the *same* section-file at the same wall-clock time (e.g., running the same section-review twice on different model pools). In that case, both coordinators compute the same `reviewKey`, write to the same bucket, and collide.

**Resolution (skill-side, no relay change):** `splitProposal` accepts an optional `session_id` parameter (a UUIDv4). When supplied, `splitProposal` writes the section-file to `<sections_dir>/<session_id>/<n>/proposal.md` instead of `<sections_dir>/<n>/proposal.md`. The session_id enters the path, the path enters the reviewKey, and the reviewKey differs. The default (`session_id = null`) reproduces today's behavior — single coordinator, deterministic path.

```javascript
// __lib/split.mjs signature
export function splitProposal(proposalPath, sections, opts = {}) {
  const sessionId = opts.session_id ?? null;
  // sessionId null → <sections_dir>/<n>/proposal.md (default)
  // sessionId set  → <sections_dir>/<session_id>/<n>/proposal.md
}
```

Documented contract: when invoking `splitProposal` for parallel-section runs that *might* be launched more than once on the same proposal path, the coordinator MUST pass `opts.session_id`. The default is safe for the common case (one coordinator per proposal).

---

## 6. Mandatory Sections (consolidated)

### 6.1 Design Intent Contract

See §1 above.

### 6.2 Alternatives

#### Option 0: Do Nothing

- **Description:** Keep the relay as-is. The coordinator continues to use the manual convergence heuristic in `~/.grok/skills/review-relay/SKILL.md:438-446` (0 new findings → suggest stop). Partners continue to re-verify previously agreed corrections.
- **Cost:** the 42-finding, 16-turn session that motivated this concept repeats; 120s→600s lease is already in place but the other two improvements aren't. No way to track that finding "F-003 severity=high" was already resolved by both actors in turn 4 and re-introduced in turn 9 because the coordinator's heuristic only counts *new* findings.
- **When to choose:** if the relay were to be retired within 1-2 quarters, or if no proposal ever exceeds 5 iterations. Neither is true (2026-08-09: 7+ iterations on the model-selection policy).

#### Option 1: Inspecting-Pipe Relay — Bundled (REJECTED — Variant B's framing)

- **Description:** Add finding parsing to the relay. Maintain a finding state machine inside the relay. Expose convergence score via `inspectState`. Make sections first-class in the controller.
- **Pros:** single source of truth; can enforce invariants at the transport layer; coordinators get rich status from `inspectState`.
- **Cons (why rejected):**
  - **Violates dumb-pipe invariant** that has held since the relay was created. Premise-verification #8 confirms the relay has *never* inspected findings — adding this is a structural shift, not an incremental change.
  - **Test surface grows non-linearly.** Existing `tests/review-relay.test.mjs` cases are unit-tested on opaque result content; adding finding parsing requires re-deriving each test fixture's finding interpretation.
  - **Couples partner schema to relay schema.** Today partners can change `findings` shape freely; tomorrow the relay enforces a schema. This breaks the existing partner prompts at `~/.grok/skills/review/SKILL.md` and any external partner integration.
  - **Score reliability decreases** if the relay computes it (relay has no semantic understanding of finding overlap; the skill does).

#### Option 1B: Inspecting-Pipe for Findings Only — Isolated (FAIR MIDDLE OPTION — Finding 3)

- **Description:** Relay parses findings for the lifecycle state machine (open/rebutted/upheld/resolved/superseded). Convergence score and section-split remain skill-side (this design's Components 2 and 3). The relay exposes lifecycle state via `inspectState`.
- **Pros:** single source of truth for *finding lifecycle* (the most-asked-about state); preserves skill-side smarts for *computation* (score, sections); smaller blast radius than bundled Option 1.
- **Cons:**
  - **Still violates dumb-pipe invariant** — even one piece of finding inspection breaks the transport contract for downstream consumers (handoff writers, external partners, future integrations).
  - **Test surface still grows non-linearly** for finding-related fixtures; score and section tests remain unchanged.
  - **Couples partner schema to relay schema** for findings only; partners that customize finding shapes are forced into a shape the relay can parse.
  - **Lifecycle is the cheapest thing to put in the relay** — but "cheapest to put in the relay" is the wrong selection criterion. The selection criterion is "lowest future cost and risk." Sidecar FSM (Variant A) has lower future cost because adding more sidecar rules is additive; adding relay parsing rules is multiplicative (every new state transition risks breaking every partner).
- **When to choose:** if finding lifecycle becomes the dominant cost in the review loop (currently it is *one of three* improvements). Not justified at present.

**Note (Finding 3):** the original Option 1 was a *bundled* strawman — every smart-pipe change at once. Option 1B is the fair middle ground the critical friend demanded. Variant A is still preferred because (a) the dumb-pipe preservation has higher future optionality than even the isolated inspecting-pipe, and (b) §2 Architectural Justification argues that *any* relay inspection breaks the contract for downstream consumers.

#### Option 2: Hybrid — Findings-Aware Only, No Convergence (Variant C)

- **Description:** Allow `findings.jsonl` sidecar (Component 1) but compute convergence manually (status quo heuristic in SKILL.md). Defer Component 2 until proven insufficient.
- **Pros:** minimum scope; preserves existing test suite; one improvement at a time.
- **Cons:** does not address the operator's complaint about not knowing "how close to converged" without manually reading 7 result JSONs.
- **When to choose:** if finding lifecycle proves insufficient on its own.

#### Option 3 (Chosen): Dumb Pipe + All Three Components (Variant A — this design)

- **Description:** Sidecar files for lifecycle state, skill-side score computation, skill-side section splitting. Relay untouched.
- **Selection criterion:** lowest future cost and risk while meeting all three requirements. The relay's dumb-pipe invariant has held across 16+ turns of testing (no regression found in preflight-inventory.json for relay source since 2026-08-08). Abandoning it for a one-shot improvement is suboptimal long-term.
- **Trade-off acknowledged:** partner prompts grow, coordinator gets more logic, but the transport layer stays simple and testable.

### 6.3 Coupling & Code-Smell Inventory (revised — Finding 7)

The original "OK, None" verdicts were wrong by the design's own criteria. Re-counted honestly:

| Smell class | Count in target code | Verdict | Action |
|---|---|---|---|
| DRY violations | None across the *single-helper* boundary | OK | None |
| Parameter count | `mergeReviews(reviewDir, sections)` has 2 params | OK (< 7) | None |
| **Touch points for finding schema change** (Finding 7) | **4 locations**: `__lib/findings.mjs` (writer/reader), `__lib/convergence.mjs` (reads `state` field), partner prompt template (must be updated), `__lib/merge.mjs` (reads findings.jsonl for merging) | **Over threshold (>3)** — schema change requires coordinated update | Mitigate by versioning the JSONL schema: `{"schema_version": "findings.v1", ...}`. Add a schema-version check in `findings.readAll()` that rejects records with unknown schema version and falls back to empty with a warning. |
| **Touch points for new score field** | `__lib/convergence.mjs` (writer), `__lib/dashboard.mjs` (reader), coordinator's decision logic, partner prompt (must be told score is advisory) | **4 locations** | Same mitigation: schema-versioned JSONL. |
| **Mixed concerns** (Finding 7) | `__lib/convergence.mjs` reads `result.json` (relay output), `findings.jsonl` (Component 1), and writes `convergence_history.jsonl`. `__lib/merge.mjs` reads N section-review dirs (each is a relay bucket). Both helpers share `findings.jsonl` schema and coordinator workflow. | **NOT OK — tight coupling by shared data** | Mitigate by extracting a `findings` schema module that both helpers import. Adding the schema module is ~30 LoC; both helpers become consumers. |
| Touch points for section split | `__lib/split.mjs` (writer), `__lib/merge.mjs` (reader), coordinator workflow | **3 locations** | Borderline OK; acceptable. |
| Touch points for finding schema (Finding 7 — concrete re-count) | findings.mjs write/read, convergence.mjs reads state field, partner prompt template (must document state field), merge.mjs reads for merging | **4** (above threshold of 3) | Schema-versioned JSONL; coordinator re-validates on first read after schema change. |
| Touch points for score schema (Finding 7) | convergence.mjs write, dashboard.mjs read, coordinator decision logic, partner prompt advisory note | **4** | Same mitigation. |

**Refactor dismissal gate check (revised):** the original "no refactor needed" verdict was wrong. The cross-helper coupling warrants a `__lib/schema.mjs` module that defines the JSONL schemas (`findings.v1`, `convergence.v1`, `merge.v1`) and provides `validate(record, schema)` for each. This is not gold-plating — it's the structural fix for Finding 7's coupling smell. Estimated LoC: ~80 (schema definitions + 3 validators).

### 6.4 Failure Mode & Edge Case Analysis

All 8 categories × 3 components.

#### Component 1 — `findings.jsonl`

| Category | Failure mode | Mitigation |
|---|---|---|
| Concurrency | Two partners write same `finding_id` transitions | Skill-side: each turn writes to its own scratchpad; relay copies the latest forward. No live cross-partner writes. |
| State consistency | A `rebutted` finding is marked `resolved` without going through `upheld` | Validator in `__lib/findings.mjs` rejects invalid transitions; partner prompts document the FSM. |
| Performance | `findings.jsonl` grows large (>10k records) | Append-only JSONL with periodic archival to `<bucket>/findings-archive.jsonl` after the review closes (skill-side). |
| Security | A partner writes a finding under another actor's name | `raised_by` and `by_actor` are signed against the manifest's actor list; mismatches fail partner validation. |
| Observability | Operator cannot tell which findings are still contested | `findings.jsonl` is human-readable; `__lib/findings.mjs` exports a `summary()` helper for the operator. |
| Compatibility | Old partner ignores `previous_findings_path` | Graceful default — `null` means "no prior findings"; old partner behavior unchanged. |
| Compatibility | LLM-as-partner mis-parses the templated path (interpolates, modifies) | Partner-prompt template instructs verbatim `read` call with the exact string; unit test `test_partner_prompt_template.mjs` substitutes the variable and asserts the path passes through unaltered (F-04). |
| Recovery | A turn's `findings.jsonl` is corrupted | Relay copies only files that pass JSONL parse; corrupted files skipped, partner re-derives from prior valid snapshot. |
| Recovery | `previous_findings_path` is null, missing, or unreadable | `__lib/findings.mjs::readAll()` returns `{records: [], warning: "<reason>"}`; coordinator logs warning; lifecycle tracking degrades to "no history" for that turn (F-01). |
| Edge case | N=1 actor (single-actor session) | State machine still works; `upheld` and `rebutted` collapse to "self-acknowledged"; doc notes this. |

#### Component 2 — Convergence score

| Category | Failure mode | Mitigation |
|---|---|---|
| Concurrency | Score computed from partial result history | Score file is keyed by turn; partial computation overwrites with the same turn-key (idempotent within a turn). |
| State consistency | Score says 0.95 but coordinator declares `failed` | Coordinator decision is independent of score; score is advisory. |
| Performance | Score recomputation cost grows linearly with turn count | O(turns × findings); for 100 turns × 100 findings = 10k operations, <100ms. |
| Security | Score file tampered with by partner | Coordinator reads only the file it wrote itself; partners have no write access to `convergence_history.jsonl` (relay `forbidden_writes` covers this if configured — see Open Question #1). |
| Observability | Operator cannot interpret a score | `convergence_history.jsonl` records component breakdown, not just total. |
| Observability | Score weights are wrong for the team's dynamics | `__lib/convergence.mjs` exports `DEFAULT_WEIGHTS` (constants) and reads overrides from `REVIEW_RELAY_WEIGHTS` env var; `exportScoreDistribution(bucket)` helper for offline tuning (F-03). |
| Compatibility | Old coordinator ignores the file | Graceful — `inspectState` output is unchanged; old coordinator runs identically. |
| Recovery | Score computation throws on malformed result | Wrap in try/catch; on failure, append `{score: 0, error: "<msg>"}`; coordinator falls back to manual heuristic. |
| Edge case | All actors submit a 0-finding turn at turn 2 (too early) | Score formula accounts for coverage — at turn 2 with all actors engaged, coverage=1, but engagement_depth penalizes shallow sessions. |

#### Component 3 — Section split + parallel review

| Category | Failure mode | Mitigation |
|---|---|---|
| Concurrency | N parallel relay sessions on same registry collide | Each section uses a different `reviewKey` (its own path); registry buckets are independent. |
| Concurrency | Two parallel coordinators launched on the same section-file (same wall-clock time) | `splitProposal(opts.session_id)` writes the section-file under `<sections_dir>/<session_id>/<n>/proposal.md`; the session_id enters the path, the path enters the reviewKey (F-02). |
| State consistency | One section converges, another is stuck | Coordinator waits for all N before merging; merge step uses `min(score_1, ..., score_N)` (most conservative, F-07). |
| Performance | N=8 sections = 8× coordination overhead | Bound N at 6 by default; doc warns on N > 6. |
| Security | A section-file accidentally references secrets from another section | Skill-side `splitProposal` does string-only slicing; no cross-section leakage. |
| Observability | Operator cannot trace which section a finding came from | Finding record gains `section_n` field (in sidecar, not relay); `mergeReviews` propagates. |
| Compatibility | Whole-proposal review flow unchanged | Coordinator chooses to invoke `splitProposal`; existing workflow untouched. |
| Recovery | One section-review's lease expires | Each section has independent lease; other sections proceed. |
| Edge case | Proposal has no headings | `splitProposal` rejects with clear error; coordinator falls back to whole-proposal review. |

### 6.5 Implementation Plan (Disposition per unit)

| Unit ID | Description | Files | Disposition |
|---|---|---|---|
| **U-1** | `findings.jsonl` lifecycle helpers (with missing-path fallback + write_policy verification precondition) | New: `~/.grok/skills/review-relay/__lib/findings.mjs`; tests: `tests/test_findings.mjs` (incl. missing-path, null-path, corrupt-file, write-policy-permit tests); precondition: read `src/review-relay.mjs` `write_policy.forbidden_writes` and verify the active scratchpad path is permitted (F-01) | **COMMIT_THIS_SESSION** |
| **U-2** | Convergence score computation (with `REVIEW_RELAY_WEIGHTS` env override + `exportScoreDistribution` helper) | New: `~/.grok/skills/review-relay/__lib/convergence.mjs`; tests: `tests/test_convergence.mjs` (incl. weight-override and sum-validation tests) | **COMMIT_THIS_SESSION** |
| **U-3** | `splitProposal` + `mergeReviews` (with `opts.session_id` for parallel-session collision avoidance) | New: `~/.grok/skills/review-relay/__lib/split.mjs`, `__lib/merge.mjs`; tests: `tests/test_split.mjs`, `tests/test_merge.mjs` (incl. session_id collision test) | **COMMIT_THIS_SESSION** |
| **U-4** | SKILL.md sections documenting new helpers | Modify: `~/.grok/skills/review-relay/SKILL.md` (~3 new sub-sections, < 200 lines added) | **COMMIT_THIS_SESSION** |
| **U-5** | Partner-prompt documentation for `previous_findings_path` | Modify: `~/.grok/skills/review/SKILL.md` (add section under "What the partner sees"); new test: `tests/test_partner_prompt_template.mjs` substitutes `{{previous_findings_path}}` with a fixture path and asserts the string passes through unaltered | **COMMIT_THIS_SESSION** |
| **U-6** | Relay source changes | **None.** | **N/A** (zero disposition — by design) |
| **U-7** | Validation: existing relay tests pass unchanged | Run: `pnpm --filter codex-external-delegation test` | **COMMIT_THIS_SESSION** |
| **U-8** | Wiki concept revision: mark "research identified" as "designed" | Modify: `P:/.data/wiki/concepts/review-relay-improvements-...md` to reference this design doc | **HANDOFF** (out of scope for an implementer; design doc is the source of truth; wiki revision is operator work) |
| **U-9** | End-to-end run: 4-section split review on a test proposal | Manual: produce timing comparison vs whole-doc review | **DEFERRED** (waiting on U-1..U-5 shipped and a representative proposal) |
| **U-10** | Decide whether `convergence_score` belongs in `result.json` or only in sidecar | Open question — see §6.10 | **NEEDS_USER_DECISION** |
| **U-11** | Operator dashboard helper `__lib/dashboard.mjs` (Finding 6) — consolidates sidecar reads into single status file | New: `~/.grok/skills/review-relay/__lib/dashboard.mjs`; tests: `tests/test_dashboard.mjs` | **COMMIT_THIS_SESSION** |
| **U-12** | Partner prompt multi-pool propagation PR (Finding 9) — updates Codex/Grok/Pi/OpenCode partner prompts to default-on sidecar read; instruments adoption metric | New: PR updating `~/.grok/skills/review/SKILL.md` and any partner-pool-specific prompt files; tests verify all pools updated | **COMMIT_THIS_SESSION** (Phase 2) |
| **U-13** | Section-coupling analyzer `split.analyzeCoupling()` (Finding 10) — detects cross-section references; falls back to whole-proposal when coupling > threshold | New: `__lib/split.mjs` extension; tests: `tests/test_split.mjs::testCouplingDetection + testFallbackOnCoupling` | **COMMIT_THIS_SESSION** (Phase 3) |
| **U-14** | Schema versioning `__lib/schema.mjs` (Finding 7) — defines JSONL schemas with version fields; rejects unknown versions | New: `~/.grok/skills/review-relay/__lib/schema.mjs`; tests: `tests/test_schema.mjs` | **COMMIT_THIS_SESSION** |
| **U-15** | Phase 1.5 validation (Finding 4) — measure default weights on 3 test proposals before any production use | Manual: run `__lib/convergence.mjs` against 3 historical review sessions; produce validation report | **COMMIT_THIS_SESSION** (Phase 1.5 gate) |

### 6.6 Code-Path Completeness

For each Component, the implementation path is complete (no missing branches):

**Component 1 (findings.jsonl):**
- `findings.appendTransition(bucket, findingId, toState, byActor, turn, note)` → writes JSONL record
- `findings.readAll(bucket)` → returns parsed records, newest last
- `findings.summary(bucket)` → returns `{open: N, rebutted: M, upheld: K, resolved: L, superseded: P}` for operator inspection
- Partner reading on tick: `previous_findings_path` → `findings.readAll()`
- Partner writing on submit: `findings.appendTransition()` calls before `submit`

**Component 2 (convergence):**
- `convergence.computeScore(bucket, currentTurn)` → reads all result.json + findings.jsonl, returns `{score, components}`
- `convergence.appendHistory(bucket, record)` → appends to `convergence_history.jsonl`
- `convergence.shouldDeclareReady(bucket, threshold)` → boolean, used by coordinator
- `convergence.DEFAULT_WEIGHTS` → exported frozen constant `{0.5, 0.3, 0.2}` (F-03)
- `convergence.loadWeights(env)` → reads `REVIEW_RELAY_WEIGHTS` env override; validates sum ≈ 1.0
- `convergence.exportScoreDistribution(bucket)` → returns per-turn scores + components for offline tuning (F-03)
- Coordinator reading: `convergence_history.jsonl` last record
- Coordinator writing: on every tick, before deciding next action

**Component 3 (split/merge):**
- `split.proposal(proposalPath, sections, opts)` → returns `[{n, title, path}]`; `opts.session_id` adds parallel-safety (F-02)
- `split.writeSections(sections, outDir, sessionId)` → writes `<sections_dir>/<sessionId|none>/<n>/proposal.md` + `sections/manifest.json`
- `merge.gather(reviewDir, manifest)` → reads N section-review dirs, returns unified findings array
- `merge.writeMerged(outDir, merged)` → writes `merged-findings.jsonl`
- `merge.minScore(merged)` → returns `min(score_section_1, ..., score_section_N)` (F-07)
- Coordinator flow: split → N parallel ticks → merge → decide

**Cross-cutting helpers (Finding 6, Finding 7, Finding 10):**
- `dashboard.status(bucket)` → single JSON output consolidating findings + score + merged state + next_action (Finding 6)
- `dashboard.deriveNextAction(findings, score, merged)` → returns `"declare ready_for_parent_review" | "await next actor's rebuttal" | "mediate dispute" | "continue relay"`
- `schema.validate(record, schema_name)` → validates JSONL records against `findings.v1` / `convergence.v1` / `merge.v1` schemas; rejects unknown schema_version with warning (Finding 7)
- `split.analyzeCoupling(proposalText, sections)` → returns `[{from_section, to_section, type, weight}]` for coupling-aware fallback (Finding 10)

No external RPC, no new auth, no new lock files. All paths complete.

### 6.7 Traceability Matrix

| REQ ID | Requirement | DEC | Implementation unit | Verification |
|---|---|---|---|---|
| REQ-1 | Partners must not re-verify resolved findings | DEC-1 | U-1 | Test: `test_findings.mjs::testPartnertReadsPriorState` |
| REQ-2 | Finding FSM enforces open→{rebutted,upheld}→{resolved,superseded} | DEC-1, DEC-2 | U-1 | Test: `test_findings.mjs::testInvalidTransitionRejected` |
| REQ-3 | Coordinator gets numeric convergence score per turn | DEC-3 | U-2 | Test: `test_convergence.mjs::testScoreComponents` |
| REQ-4 | Score formula: 0.5*overlap + 0.3*coverage + 0.2*depth | DEC-3 | U-2 | Test: `test_convergence.mjs::testWeightedSum` |
| REQ-5 | Score is advisory, not part of relay status gate | DEC-3, DEC-4 | (relay untouched) | Manual: confirm `inspectState` output unchanged |
| REQ-6 | Section split runs N parallel relays | DEC-5 | U-3 | Test: `test_split.mjs::testNSectionsParallel` |
| REQ-7 | Section merge produces unified findings | DEC-5 | U-3 | Test: `test_merge.mjs::testMergedFindingsOrdered` |
| REQ-8 | Relay source unchanged | DEC-6 | (U-6 — none) | `git diff src/review-relay.mjs` returns empty |
| REQ-9 | Existing tests pass unchanged | DEC-6 | U-7 | `pnpm test` |
| REQ-10 | Partner reads `previous_findings_path` | DEC-1 | U-5 | Manual: partner prompt review |
| REQ-11 | Missing/null `previous_findings_path` does not crash partner | DEC-1, F-01 | U-1 | Test: `test_findings.mjs::testMissingPathFallback` |
| REQ-12 | `write_policy.forbidden_writes` permits partner writes to active scratchpad | DEC-1, F-01 | U-1 pre | Read `src/review-relay.mjs` `write_policy` section |
| REQ-13 | Convergence weights tunable via `REVIEW_RELAY_WEIGHTS` env var with sum-validation | DEC-3, F-03 | U-2 | Test: `test_convergence.mjs::testWeightsOverride + testSumValidation` |
| REQ-14 | `splitProposal(opts.session_id)` produces distinct paths/keys for parallel coordinators on same source | DEC-5, F-02 | U-3 | Test: `test_split.mjs::testSessionIdCollisionAvoidance` |
| REQ-15 | Convergence weights validated on ≥3 test proposals before any production use (Phase 1.5 gate) | DEC-13, Finding 4 | U-15 | Manual: validation report artifact |
| REQ-16 | Coordinator cross-checks score against at least one additional signal before declaring `ready_for_parent_review` | DEC-13 | U-2, U-11 | Test: `test_dashboard.mjs::testCrossCheckEnforced` |
| REQ-17 | Operator reads ≤1 file to assess convergence state (dashboard helper consolidates) | DEC-6, Finding 6 | U-11 | Manual: dashboard invocation produces single JSON output |
| REQ-18 | `splitProposal.analyzeCoupling()` detects cross-section references ≥30% weight and falls back to whole-proposal | DEC-5, Finding 10 | U-13 | Test: `test_split.mjs::testCouplingDetection + testFallbackOnCoupling` |
| REQ-19 | Partner prompts for ALL model pools (Codex, Grok, Pi, OpenCode) updated in single Phase 2 PR with default-on sidecar read | DEC-9, Finding 9 | U-12 | Manual: PR review against all-pool checklist |

### 6.8 Key Decisions

| DEC ID | Decision | Rationale | Risk |
|---|---|---|---|
| **DEC-1** | `findings.jsonl` lives in bucket, partners read+write via existing scratchpad mechanism | Sidecar pattern keeps relay dumb; partners see prior state via `previous_findings_path` (mirrors `previous_result_path`) | Partners must opt in; old partners unchanged |
| **DEC-2** | Finding state machine validated in skill, not relay | Relay stays findings-agnostic (Premise #8) | Bad partners can write invalid FSM transitions; rejected at read time |
| **DEC-3** | Score computed in `__lib/convergence.mjs`, written to `convergence_history.jsonl` sidecar | Dumb pipe invariant; score visible via file, not `inspectState` | Operator must read sidecar; not surfaced in tick output |
| **DEC-4** | Score weights: 0.5/0.3/0.2 (overlap/coverage/depth) | Overlap dominates because "no new findings" is the strongest convergence signal; coverage prevents premature stop when one actor is silent | Wrong weights can mask genuine non-convergence; tunable |
| **DEC-5** | Section split via skill-side `splitProposal`, N independent relay sessions | Preserves dumb pipe; reuses existing two-actor model per section | N parallel coordinator instances required; N bounded at 6 |
| **DEC-6** | Zero relay code changes | Premise #8 + test stability + backward compat | Forces partner-side complexity for lifecycle tracking |
| **DEC-7** | Coordinator may override score (declare `ready_for_parent_review` early) | Score is advisory; coordinator judgment is authoritative | Bounded by relay's hard gate (`enforceParentReviewGate`) |
| **DEC-8** | Default N=4 sections, configurable up to 6 | 4 is the median for design docs in the workspace; 6 caps coordination overhead | Proposals with >6 sections need a different review strategy |
| **DEC-9** | Convergence weights exposed as `DEFAULT_WEIGHTS` + env override `REVIEW_RELAY_WEIGHTS` | Reasoning-not-evidence defaults; env override lets operators tune without code change; sum-validation prevents misconfiguration (F-03) | First 5 production runs produce unvalidated distribution; operator must review |
| **DEC-10** | `splitProposal` accepts `opts.session_id` for parallel-session collision avoidance | Default (null) reproduces today's behavior; sessionId enters the path, the path enters the reviewKey (F-02) | Operators must remember to pass sessionId when running two coordinators on the same proposal |
| **DEC-11** | Missing/unreadable `previous_findings_path` is a soft-failure with logged warning, not a hard error | Partners must not crash on lifecycle-history absence (F-01) | Lifecycle tracking degrades silently for a turn; coordinator log is the only signal |
| **DEC-12** | Ship dumb-pipe first; promote to smart-pipe only when (a) skill-side mechanism has been a production bottleneck for ≥30 days AND (b) at least one of cross-section-correlation / adaptive-lease / finding-provenance future requirements has materialized | §2 Architectural Justification argues preservation has higher future optionality; migration path is reversible at every step (Finding 2) | Future requirements may force migration sooner than predicted; the decision rule must be re-evaluated on each new requirement |
| **DEC-13** | Coordinator MUST NOT use convergence score as the sole `ready_for_parent_review` signal; cross-check required against at least one of: zero new findings, all findings upheld/resolved, operator override | "Advisory ≠ harmless" — humans/LLMs treat numerical signals as evidence (Finding 4) | Adds friction to coordinator workflow; mitigated by `dashboard.mjs::next_action()` automation |

### 6.9 Rollout (revised — Finding 4, Finding 9)

1. **Phase 1 (U-1, U-2, U-11):** Ship `findings.mjs` + `convergence.mjs` + `dashboard.mjs` + `schema.mjs` + tests. Land in a single PR. No partner behavior change yet — these are dormant helpers. Existing sessions unaffected. **The dashboard helper ships in Phase 1 to mitigate the operator-reading-burden concern from Finding 6 — the operator has the dashboard available immediately.**
2. **Phase 1.5 (NEW — Finding 4 weight validation):** Validate the convergence score weights (0.5/0.3/0.2) on **3 test proposals** (different shapes, different complexities). Run the score on existing result-history JSONs for these proposals, measure: (a) score on runs that were eventually declared `ready_for_parent_review`, (b) score on runs that were stuck, (c) score on runs that were active. If the score discriminates (a) > (c) > (b) cleanly, ship Phase 2. If not, tune via `REVIEW_RELAY_WEIGHTS` env override and re-validate. **Until Phase 1.5 completes, the score contributes 0 to the coordinator's decision (per the Phase 1.5 predicate in §4 Coordinator Decision Rule).**
3. **Phase 2 (U-4, U-5, U-12):** Update SKILL.md, partner prompts for ALL model pools (Codex, Grok, Pi, OpenCode), and `__lib/dashboard.mjs` reads. **Partner prompt changes are shipped as a single multi-pool PR with explicit adoption metric instrumentation.** Coordinator begins computing and logging convergence scores for all new sessions. Partners begin writing `findings.jsonl` when they choose to (backward compatible: omitting it means no change in behavior). **The partner-prompt template instructs default-on reading (read `previous_findings_path` whenever non-null, even if empty); this addresses Finding 9's "default-on vs default-off" recommendation.**
4. **Phase 3 (U-3, U-13):** Ship `split.mjs` + `merge.mjs` + coupling analyzer. Coordinator gains the `splitProposal` workflow as an explicit opt-in. The coupling analyzer (Finding 10) detects cross-section dependencies and falls back to whole-proposal review when coupling exceeds threshold. Run on a representative 4-section proposal; compare wall-clock vs whole-doc baseline.
5. **Phase 4 (validation):** After 5 production sessions using the new helpers, collect metrics: re-verification rate (Finding 1 metric), operator file-read burden (Finding 6 metric), partner prompt adoption rate (Finding 9 metric), section-split wall-clock (Finding 10 metric), score distribution (Finding 4). **If any falsifier from §1.6 fires, escalate to §2's graceful migration path or revert per the failure conditions.** Update the wiki concept with measured numbers.

**Partner prompt propagation (Finding 9):**
- Phase 2 includes a single PR that updates partner prompts for **all** model pools (Codex, Grok, Pi, OpenCode). The PR is reviewed against the existing partner-prompt test suite (`tests/test_partner_prompt_template.mjs`).
- Adoption is measured via the partner-prompt instrumentation: the partner template instructs partners to log `findings_sidecar_read_attempted: true` to their scratchpad after attempting the `read(previous_findings_path)` call. The dashboard helper reads these logs and reports the adoption rate.
- **Adoption rate <50% for 7 consecutive days** triggers a partner-prompt redesign escalation.

**Rollback:** Each helper is opt-in. Removing `findings.jsonl` write from partner prompt = revert to current behavior. No data loss; no schema migration. The Phase 1.5 gate ensures unvalidated weights never ship to production.

### 6.10 Open Questions

1. **[RESOLVED — Premise #12, see Finding 8 response]** **Status:** resolved with source-code receipts. **Receipts:** `P:/packages/codex-external-delegation/src/review-relay.mjs:961-966` (manifest `write_policy` block), `:1377` (`forbidden_writes` passed to partner input). **Findings:**
   - `allowed_writes` (line 964) includes `"turns/**"` — partners ARE permitted to write to `<bucket>/turns/<n>/active/findings.jsonl`. **Finding 1 (lifecycle) is workable by construction.**
   - `forbidden_writes` is **advisory only**: declared in the manifest and passed to the partner input file (line 1377), but the relay does NOT validate partner writes against this list. The enforcement is partner-side discipline, not relay-side enforcement.
   - `convergence_history.jsonl`, `merged-findings.jsonl`, `merged-convergence.json` are written by the coordinator (skill), not by partners. `write_policy` governs partner writes only — skill-side writes are unrestricted. **Findings 2 and 3 are workable by construction.**
   - **Variant A is structurally workable.** The single-point-of-failure premise the critical friend flagged does not exist. U-1's "verify write_policy" precondition gate (from F-01 revision) is therefore vacuous; replaced with a direct read of `manifest.write_policy` to document the permission chain, not to gate implementation. **No relay changes required for any of U-1, U-2, U-3.**
2. **[NEEDS_USER_DECISION — U-10]** Should the `convergence_score` also appear in `result.json` (e.g., as a new field the partner sets), or remain only in the sidecar? The former makes the score visible to `inspectState`; the latter keeps the relay oblivious. **Default if no answer by ship time:** sidecar only (DEC-3). Flip requires user sign-off.
3. **[INFERENCE — Premise #10]** The ReviewingAgents / POIROT / GPT Researcher pattern citations in the wiki concept are research-only; their canonical mechanisms are described in the domain-knowledge brief but not verified against the original papers. Treat as design inspiration, not authoritative citation for any naming. **Action for implementer:** none (helpers use generic names like `findings.mjs`, `convergence.mjs`, not pattern names).
4. **[INFERENCE — Premise #11]** Per-section parallel review assumes section headings are stable across iterations. If the proposal is edited between turns and headings shift, `splitProposal` produces mismatched sections. **Mitigation:** skill regenerates section files each iteration; sections are content-derived, not index-derived.
5. **[NEEDS_USER_DECISION — F-03 follow-up]** The default score weights 0.5 / 0.3 / 0.2 are reasoned but unvalidated on real team dynamics. After U-2 lands, the first 5 production runs should produce a `score_distribution` for the operator to review. **Default if no answer:** keep defaults. The operator can override per-run via `REVIEW_RELAY_WEIGHTS` env var without code change. Flip to "tune per workspace" requires the operator to commit a tuned baseline.
6. **[RESOLVED — Premise #12, see Finding 8 above]** The structural single-point-of-failure premise does not exist. `allowed_writes` includes `turns/**`; partner writes to findings.jsonl are permitted. Skill-written sidecars are not subject to write_policy. **Variant A is structurally workable by construction.**
7. **[OPEN — Finding 9 adoption metric]** The dashboard helper measures `findings_sidecar_read_attempted` per partner turn. The threshold for "successful adoption" is set at 95% in §1 Success Metrics; this threshold is **not yet validated** on real partner pools. After Phase 2 ships, the first 30 days of production produce an empirical adoption-rate distribution. If the actual rate is <70% with the default-on prompt, the partner-prompt design is wrong and needs redesign — not a partner-behavior problem.

---

## 7. File Change Inventory

### Files Created (11)

| Path | Purpose |
|---|---|
| `~/.grok/skills/review-relay/__lib/findings.mjs` | Finding lifecycle FSM + JSONL read/write |
| `~/.grok/skills/review-relay/__lib/convergence.mjs` | Score computation + history append (with weight tuning) |
| `~/.grok/skills/review-relay/__lib/split.mjs` | `splitProposal` + `analyzeCoupling` (Finding 10) |
| `~/.grok/skills/review-relay/__lib/merge.mjs` | `mergeReviews` + `minScore` aggregation (F-07) |
| `~/.grok/skills/review-relay/__lib/dashboard.mjs` | Operator dashboard `status()` + `deriveNextAction()` (Finding 6) |
| `~/.grok/skills/review-relay/__lib/schema.mjs` | JSONL schema versioning + validation (Finding 7) |
| `~/.grok/skills/review-relay/tests/test_findings.mjs` | Lifecycle FSM tests (incl. missing-path fallback) |
| `~/.grok/skills/review-relay/tests/test_convergence.mjs` | Score computation tests (incl. weight-override + sum-validation) |
| `~/.grok/skills/review-relay/tests/test_split.mjs` | Split helper tests (incl. session_id collision + coupling detection) |
| `~/.grok/skills/review-relay/tests/test_merge.mjs` | Merge helper tests (incl. min-of-N score) |
| `~/.grok/skills/review-relay/tests/test_dashboard.mjs` | Dashboard helper tests (incl. cross-check enforcement) |
| `~/.grok/skills/review-relay/tests/test_schema.mjs` | Schema versioning + validation tests |
| `~/.grok/skills/review-relay/tests/test_partner_prompt_template.mjs` | Partner-prompt template variable-substitution test (F-04) |

### Files Modified (2)

| Path | Change |
|---|---|
| `~/.grok/skills/review-relay/SKILL.md` | Add ~3 sub-sections: "Finding lifecycle", "Convergence score", "Per-section parallel review" |
| `~/.grok/skills/review/SKILL.md` | Add `previous_findings_path` to "What the partner sees" |

### Files NOT Modified (verified by design invariant)

| Path | Why untouched |
|---|---|
| `P:/packages/codex-external-delegation/src/review-relay.mjs` | Dumb pipe invariant |
| `P:/packages/codex-external-delegation/tests/review-relay.test.mjs` | Existing tests must pass unchanged |
| `P:/packages/codex-external-delegation/docs/review-relay.md` | Surface unchanged |

### Estimated LoC

| File | Approx LoC |
|---|---|
| `findings.mjs` | ~220 |
| `convergence.mjs` | ~160 |
| `split.mjs` (incl. `analyzeCoupling`) | ~210 |
| `merge.mjs` | ~120 |
| `dashboard.mjs` (Finding 6) | ~100 |
| `schema.mjs` (Finding 7) | ~80 |
| Test files (8 — incl. `test_dashboard.mjs`, `test_schema.mjs`, `test_partner_prompt_template.mjs`) | ~700 total |
| SKILL.md additions | ~180 |
| Partner SKILL.md additions (multi-pool) | ~60 |
| **Total new LoC** | **~1830** |
| **Relay LoC delta** | **0** |

---

## 8. Summary (for summary doc)

The three improvements land entirely on the partner + coordinator side. The relay stays byte-identical *unless* §2 Architectural Justification's decision rule (DEC-12) triggers migration. New helpers in `~/.grok/skills/review-relay/__lib/` (findings, convergence, split, merge, dashboard, schema) plus minimal SKILL.md documentation. Existing tests pass unchanged. Rollout is phased: helpers first, then Phase 1.5 weight validation on 3 test proposals (Finding 4), then partner multi-pool propagation with default-on adoption (Finding 9), then section-split with coupling detection (Finding 10), then metrics collection. Five open questions flagged for implementer attention, two need user decisions (F-03 weight-tuning baseline, U-10 score-in-result.json — DEC-3 default if unanswered: sidecar only).

**Revision 3 (critical-friend revisions):** premise #12 (Finding 8) resolved with source-code receipts — `allowed_writes` includes `turns/**`; U-1's precondition gate is vacuous by construction. Success metrics (Finding 1) revised to measure user-pain reduction, not preservation. Falsifiability section (Finding 5) added with 5 concrete falsifiers. Dumb-pipe architectural justification (Finding 2) added with 5 arguments + graceful migration path. Fair Variant 1B (Finding 3) added to alternatives. Phase 1.5 validation gate (Finding 4) added. Dashboard helper (Finding 6) added. Coupling inventory (Finding 7) re-counted honestly with schema-versioning mitigation. Section-coupling analyzer (Finding 10) added. Partner prompt propagation mechanism with adoption metric (Finding 9) added. Three new DECs, five new REQs, six new units, two new test files, two new helpers. Total new LoC ~1830 (revised from ~1330).

---