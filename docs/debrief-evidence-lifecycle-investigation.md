# Debrief Evidence Lifecycle Investigation

**Date:** 2026-07-13 (updated 2026-07-13)
**Repository:** `P:/packages/.claude-marketplace/plugins/cc-skills-analysis`
**HEAD:** `6807a6710277a1db2d897631ce74e55084c5b0cf`
**Method:** Source inspection of all directly relevant runtime paths. Live concurrency test exercised the `record_dream_review()` writer implementation directly (imported from consumed path `skills/debrief/__lib/dream_state.py`). The production SessionEnd trigger path was established by source tracing (`SessionEnd_debrief_reflect.py` line 408) — not by a live two-session dispatcher collision.

---

## 1. Current Live Evidence-Lifecycle Graph

```
TRANSCRIPT (session.jsonl)
 │
 ├──[SessionEnd hook]──→ __lib/router.py
 │                          └→ debrief/hooks/SessionEnd_debrief_reflect.py
 │                               reads tail 3000 lines
 │                               calls LLM (local or hosted)
 │                               writes candidates.json
 │                               (advisory, human review required)
 │
 ├──[Manual /debrief <file>]──→ scripts/debrief.py plan
 │                                  └→ chunk_plan.py (read transcript)
 │                                  └→ extraction prompt from template
 │                               scripts/debrief.py run
 │                                  └→ debrief_core.run()
 │                                       ├→ detect_victim_log()
 │                                       ├→ detect_opportunity_log()
 │                                       ├→ detect_deferred_reminder_cycle()
 │                                       ├→ Layer 0: discover initial findings
 │                                       ├→ classify_layer()
 │                                       ├→ locate_layer()   [via Agent]
 │                                       ├→ recuse_layer()   [via Agent]
 │                                       ├→ verify_layer()   [/truth gate]
 │                                       ├→ extract_generalizable_principle()
 │                                       ├→ write_layer()    [defect pipeline]
 │                                       ├→ write_opportunity_layer() [opportunity]
 │                                       └→ returns dict with findings + task bodies
 │                                  └→ gap_engine_adapter (if --gap-detectors)
 │                                       └→ gap_engine/orchestrator.py
 │                                            └→ __lib/* (deterministic detectors)
 │                                            └→ carryover.json (per session-id)
 │                                            └→ artifacts/ (output JSON)
 │
 ├──[Manual /debrief chain]──→ LLM-driven protocol (SKILL.md instructions)
 │                                recap → gaps → friction → red-team → rns → SCORES
 │                                (no runtime code enforces the sequence)
 │
 └──[Close gate]──→ scripts/debrief.py close
                       verifies source-file rename [Phase 8]
                       verifies breadcrumb task exists [Phase 9]
                       verifies ACCOUNTING: sentinel in breadcrumb

DREAM_STATE (~/.claude/.artifacts/debrief/dream-state.json)
    records: topic, findings, last_actioned, last_reviewed, reviews count
    provides: should_re_review() → prevents re-review within threshold_days

DOWNSTREAM CONSUMERS:
    TaskCreate/TaskUpdate    ← debrief_core returns task bodies; LLM invokes tools
    Renamed transcript file  ← rename_tag.py
    Breadcrumb task          ← marks where next debrief should start
    candidates.json          ← human review (SessionEnd hook output)
    Dormant hooks            ← NOT CONNECTED TO ANY FLOW
```

## 2. Proven Strengths

**S1 — Seven-stage state machine enforces finding quality.** `debrief_core` enforces a strict DISCOVERED→CLASSIFIED→LOCATED→VERIFIED→WRITTEN pipeline. No finding can become a task without passing `/truth` verification and having an `origin_file:line`. The selfcheck proves: UNVERIFIED truth_callable → 0 written tasks; VERIFIED → written task with TLDR + DISCRIMINATING TEST fields.

**S2 — Cross-session idempotency via dream_state.** `dream_state.py` records topics reviewed per session-id, with `should_re_review()` preventing re-review within a configurable threshold (default 7 days). Topics that were `actioned` are never re-reviewed. Topics that were only surfaced are eligible after the threshold. State file at `~/.claude/.artifacts/debrief/dream-state.json` survives compaction and session boundaries.

**S3 — Deterministic finding IDs via SHA-256.** `_stable_fid()` produces reproducible 8-hex-digit IDs from source path + symptom text, so the same transcript run twice produces byte-identical outputs. This makes runs auditable and cross-referencable.

**S4 — Separate defect and opportunity pipelines.** `write_layer()` (defects, vertically recursed) and `write_opportunity_layer()` (lateral, no origin_file required) are distinct code paths with different guard rails. Opportunities require `idea` + `generalization_test` or they are rejected. This prevents phantom defect tasks from opportunity-shaped inputs.

**S5 — Close gate enforces completion accounting.** `mode_close()` refuses exit 0 unless the source file is tagged (Phase 8 rename ran) AND a non-completed breadcrumb task exists AND the `ACCOUNTING: N findings → A tasked, B fixed, C deferred, D external` sentinel is present. This is structural — the gate regex-matches the sentinel as a structure invariant, not an NLP value check.

**S6 — Fallback chain for input resolution.** `resolve_export.py` handles missing explicit paths: session_id → export file operation; stale export detection; fallback to re-export. If session_chain import fails, `/recap` falls back to the current transcript file.

## 3. Proven Live Gaps

**G1 — SessionEnd hook output has no live consumer path.** `SessionEnd_debrief_reflect.py` writes `candidates.json` to `~/.claude/.artifacts/debrief/` but no automated process reads, promotes, or merges those candidates into the debrief state machine. The SKILL.md explicitly says "hook output must not be mistaken for the full debrief verification." Candidates require human review. In practice, the gap between "candidates exist" and "candidates are reviewed" is unbridged. No breadcrumb, notification, or `/main` integration surfaces pending candidates.

**Classification:** `PROVEN_LIVE_GAP` — candidate extraction runs but has no downstream consumer path from extraction to actionable state.

**G2 — Carryover state is per-session-id with no cross-terminal dedup.** `carryover.json` is keyed by `--session-id` passed to the gap engine. In multi-terminal workflows, the same finding may be surfaced independently in terminal A and terminal B. The gap_engine `__lib/dedupe.py` deduplicates within a single run using finding fingerprints, but there is no cross-terminal carryover merge — terminal A's `carryover.json` and terminal B's `carryover.json` are independent files. The `dream_state.py` is also per-machine (stored at `~/.claude/.artifacts/debrief/dream-state.json`) — if two terminals run `/debrief` on the same session, they don't share dream-state awareness.

**Classification:** `KNOWN_BENIGN_UNDER_CURRENT_CONSUMERS` — see §9. Concurrency testing confirmed the race is reproducible (~5.5% rate) against the exact consumed `dream_state` writer implementation. Under current production inputs (all consumers write the same `"system_efficiency"` topic with identical findings and `actioned=False`), lost updates do not affect any gate, decision, or user-visible output. See `P:/docs/dream-state-concurrency-report.md` for full test procedure and evidence.

**This must be revisited if:** (a) `reviews` influences a gate or ranking; (b) production writers emit different findings or topics concurrently; (c) any production caller uses `actioned=True`; (d) dream state gains an automated consumer; (e) dream state becomes authoritative rather than advisory.

**G3 — `/debrief chain` internal artifact flow is opaque.** The SKILL.md describes a protocol: recap→gaps→friction→red-team→rns→SCORES. No code enforces that the RNS step receives findings from the gap step. The LLM may or may not pass them. This means the "SCORES" output (completeness/optimality/satisfaction) may be computed from different inputs on different runs with no way to audit what went into it.

**Classification:** `PROVEN_LIVE_GAP` — the chain mode produces a downstream deliverable (SCORES) with no validated artifact flow. An LLM-driven gate that cannot be audited for input provenance.

**G4 — `/debrief` default mode depends on LLM to invoke Agent subagents for locate and recurse.** `debrief_core.run()` requires two callbacks (`layer_extractor` and `source_tree_resolver`) that are implemented by the LLM calling Agent() subagents. If the LLM skips or short-circuits these calls, findings stay at CLASSIFIED or LOCATED with `recursion_exhausted=True`. There is no timer, watchdog, or automated fallback.

**Classification:** `SOURCE_ONLY_RISK` — this is by-design (the model is the investigator), but it means a weaker model or lazy execution produces "stuck" findings that `recursion_exhausted` flags. The flag exists; the risk is that it gets ignored.

## 4. Source-Only Risks

**R1 — `/truth` contract mode returns UNVERIFIED by default.** `debrief_core.verify_with_truth()` is a contract stub — it always returns `{"status": "UNVERIFIED", ...}`. The LLM must invoke the `/truth` skill separately and patch the finding's `verified_status` field. If the LLM fails to call `/truth`, the finding stays at LOCATED with `recursion_exhausted=True`. A dodge-able gate.

**Classification:** `SOURCE_ONLY_RISK` — by-design, but the gate is advisory (model must choose to verify).

**R2 — SessionEnd hook uses hardcoded paths.** `SessionEnd_debrief_reflect.py` line 19: `sys.path.insert(0, "P:/packages/.claude-marketplace/...")`. Hardcoded Windows path with `P:/` drive. Breaks on any other drive or platform.

**Classification:** `SOURCE_ONLY_RISK` — works on the current machine. Future CI or different machine would break.

**R3 — Dream state per-terminal with no cross-terminal coherency.** `dream-state.json` at `~/.claude/.artifacts/debrief/dream-state.json` is per-machine, but terminal A may have reviewed topic X while terminal B has not. `should_re_review()` returns True for terminal B on a topic terminal A just reviewed.

**Classification:** `SOURCE_ONLY_RISK` — low impact unless two terminals are actively duplicating work.

## 5. Duplicate or Unused Mechanisms

**D1 — Dormant gap_engine hooks vs active lifecycle overlap.** The four dormant hooks (pretooluse, posttooluse, sessionstart, stop) implement:

| Dormant hook | Capability | Active equivalent |
|---|---|---|
| `pretooluse.py` | Blocks destructive commands during GAP runs | No active equivalent. But this is a one-off blocker for a specific session-id — the ACA safety plugin (`cc-aca-safety`) already handles destructive command prevention across ALL sessions. |
| `posttooluse.py` | Captures tool failures + file changes to JSONL | ACA observability + epistemic plugins already capture tool failures. File changes logged by snapshot + session tracking. Duplicate. |
| `sessionstart.py` | Shows prior GAP run summary | Debrief should_re_review() + close gate already inform the user about prior findings via breadcrumb tasks. |
| `stop.py` | Validates artifact JSON + RNS markers | Skill-guard Stop hook + debrief close gate already verify artifact validity. |

**Classification:** `DUPLICATED_CAPABILITY` for posttooluse and stop hooks. `DUPLICATED_CAPABILITY` for pretooluse (vs ACA safety). `DUPLICATED_CAPABILITY` for sessionstart (vs dream_state + close gate). No dormant hook provides a capability the active lifecycle lacks. The delta is zero.

**D2 — `test_write_hook_output.py` tests `common.write_hook_output()` — a function used only by the dormant hooks.** If the hooks are never registered, these tests verify unreachable code.

**Classification:** `DUPLICATED_CAPABILITY` — test coverage for unregistered code.

## 6. Downstream-Consumer Map

| Producer | Output | Consumer | Mechanism | Live? |
|---|---|---|---|---|
| `debrief_core.run()` | Task body dicts (TLDR, TITLE, VERIFIED FACTS, CAUSAL CHAIN, etc.) | LLM → `TaskCreate` / `TaskUpdate` | LLM invokes TaskCreate tool with body as description | YES |
| `debrief_core.run()` | Finding dicts (state, category, kind, origin) | `mode_close()` → ACCOUNTING sentinel | Regex-matched in breadcrumb task body | YES |
| `scripts/debrief.py close` | Exit code (0=passed, >0=failed) | Claude Code execution flow | Exit code checked by caller | YES |
| `__lib/dream_state.py` | `dream-state.json` (topic, findings, last_reviewed) | `should_re_review()` → debrief re-review gate | Python function call | YES |
| `SessionEnd_debrief_reflect.py` | `candidates.json` | **NO CONSUMER** | Written to disk, no reader | **NO** |
| Gap engine orchestrator | `artifact.json` (RNS machine output) | Gap engine's own verify + deploy phase | Within orchestrator flow | CONDITIONAL (only during gap runs) |
| `gap_engine_adapter.py` | Shaped findings dicts | `debrief_core.run()` | Called in `--gap-detectors` mode | CONDITIONAL (only with flag) |
| Dormant hooks | Various (stderr output, decision blocks) | **NO CONSUMER** | Not registered | **NO** |

## 7. Mechanism Comparison for Each Proven Gap

### G1: SessionEnd candidates have no consumer

| Option | Activation scope | Identity isolation | Duplication risk | Noise risk | Recoverability | User benefit |
|---|---|---|---|---|---|---|
| No change | None | N/A | High (candidates accumulate) | Candidates written but ignored ⇒ silent backlog | Manual find | None |
| Add "/main" polling reader | Session lifecycle (read candidates file fresh each start) | Terminal-scoped (candidates per session-id) | Low (dedup by existing dream_state) | Low (coverage_scope field documents limitation) | Candidates.json file persists | Pending candidates surfaced on session start |
| Wire as debrief pre-feed | Skill invocation (use candidates to seed initial_findings for next /debrief run) | Session-scoped | Medium (could re-feed already-processed findings) | Low (debrief_core's dedup filter handles repeats) | Candidates text survives in artifact dir | Reduces /debrief manual input |

**Recommended:** No change — G1 is a quality-of-life improvement, not a correctness gap. Candidates are a feature that was explicitly scoped as "human review only" and the SKILL.md says so. Adding automation would change the contract without proven demand.

### G3: Chain-mode artifact flow is opaque

| Option | Verifiability | Implementation cost | User benefit |
|---|---|---|---|
| No change | Low (LLM-driven) | None | None (status quo) |
| Add SCORES provenance ledger to SKILL.md | Medium (prompt the LLM to record what it consumed) | Low (documentation change) | Future audit trail |
| Implement as code pipeline | High (each step produces file-backed artifacts) | High (orchestrator rewrite) | Full traceability |

**Recommended:** No change — chain mode's SCORES output is advisory (enforcement: advisory in SKILL.md frontmatter). The LLM-driven protocol is by-design for flexibility. Adding code enforcement would constrain the flexibility without proven demand for auditability.

## 8. One Smallest Justified Next Workstream

`NO_CHANGE_JUSTIFIED`

The evidence lifecycle inspection found:

- **3 PROVEN_LIVE_GAPS** — all have been evaluated against available mechanisms. Two (G1, G3) are by-design with explicitly documented scope limitations. One (G2 — the original cross-terminal dedup framing) was reclassified after live concurrency testing confirmed the race exists but produces no material impact under current consumers. See §9 and `P:/docs/dream-state-concurrency-report.md`.

- **0 dormant hooks provide a new capability** — the four gap_engine hooks all duplicate existing mechanisms: ACA safety (pretooluse), ACA observability + epistemic (posttooluse), dream_state + close gate (sessionstart/stop). The delta is zero.

- **All active lifecycle stages are connected** — the debrief_core state machine → mode_close gate → TaskCreate → breadcrumb path is live and enforced. The SessionEnd hook produces candidates.json (unconsumed) which is explicitly by-design. The chain mode is LLM-driven (by-design).

- **The only structural gap** is cross-terminal carryover dedup (G2), which would require either a shared state file with advisory locking or a centralized carryover store. Either approach would add complexity for an edge case (same finding surfaced in two terminals) with no evidence of recurring occurrence.

The recommended action is to preserve the current lifecycle and deferred investment until usage evidence justifies a specific improvement.

## 9. Live Acceptance Scenario (if change were recommended)

*Not applicable — no change is recommended.*

---

## Summary

| Category | Count | Details |
|---|---|---|
| `ALREADY_COVERED` | 4 | All four dormant hooks duplicate existing active capabilities |
| `PROVEN_LIVE_GAP` | 2 | G1 (unconsumed candidates), G3 (chain mode opacity) |
| `KNOWN_BENIGN_UNDER_CURRENT_CONSUMERS` | 1 | G2 renamed: dream-state race reproduced but no material impact under current production inputs |
| `SOURCE_ONLY_RISK` | 3 | R1 (truth contract stub), R2 (hardcoded paths), R3 (per-terminal dream state) |
| `DUPLICATED_CAPABILITY` | 5 | 4 dormant hooks + 1 orphaned test file |
| `BLOCKED_EVIDENCE_INSUFFICIENT` | 0 | |

`NO_CHANGE_JUSTIFIED`
