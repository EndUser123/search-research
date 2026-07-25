# `/check` as Conditional Orchestrator — Design Document

| Field | Value |
|---|---|
| Document status | **Draft for review** |
| Date | 2026-07-25 |
| Owner | /check skill maintainer |
| Target skill | `/check` (multi-concern session verification) |
| Research basis | `P:/.data/wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md` |
| Implementation mode | Extend, do not replace. All **121** existing tests must continue to pass (verified `pytest --collect-only` 2026-07-25). |

---

## 1. Overview / Problem Statement

### 1.1 What this design proposes

Make `/check` a **conditional orchestrator** that routes deterministic detector signals to **specialized verifier sub-agents**. Today `/check` runs a uniform "one verifier per concern" pipeline; the new design adds a signal-routing layer in front of that pipeline so:

1. Two new detectors (`post_verification_mutation`, `scope_claim_mismatch`) emit precise signals that map to focused verifier specializations.
2. The orchestrator reads `signal_counts` and dispatches **only the verifiers whose signals fired** (plus the standard per-concern verifiers).
3. The receipt-system evaluation summary (`~/.grok/hooks/state/receipt-shadow-evaluation/sessions/<session_id>.json`) is attached to the evidence packet as an **optional bucket** so verifiers can cite it.
4. One specialization (post-verification mutation) runs on a **different model family** to decorrelate blind spots.
5. When no new signals fire, the pipeline is **functionally equivalent** to today's behavior at the verifier-dispatch layer: zero new verifiers spawned, zero new concerns added. The preprocessor + routing layer adds a small constant overhead (target ≤ 20 ms p95) but does not change which verifiers run or which verdicts they produce.

### 1.2 Why now

Three converging observations make this the right time:

1. **The receipt system has been in shadow mode** since 2026-07-22 (`quality_gate.py` enforces the old gate; the new gate's decisions are only logged). It is producing telemetry but not driving any user-visible behavior. `/check` is the natural consumer.
2. **The final-verification no-change rule** (`~/.grok/AGENTS.md` § "File editing protocol" → "Verification", line 298) is currently unmechanized. A verifier that detects file edits after the last verification command would catch the failure mode directly.
3. **The /www research** (`ai-agent-verification-orchestration-best-practices-2026.md`) confirms the orchestrator + specialized sub-agent architecture is the mainstream 2026 pattern (Gas Town, Conductor, Qodo) — not a research curiosity.

### 1.3 What this design is not

- It is not a new skill. `/check` stays one skill.
- It is not a rewrite of the existing 10 detectors. They are unchanged.
- It is not a replacement for `/review`. The two remain complementary (see `check-vs-review-complementary-not-redundant.md`).
- It is not a migration to a multi-agent framework (LangGraph, Gas Town, etc.). The orchestrator remains the parent agent plus `spawn_subagent`.

---

## 2. Goals / Non-Goals

### 2.1 Goals

| ID | Goal | Acceptance criterion |
|---|---|---|
| G1 | `/check` becomes a conditional orchestrator that dispatches verifiers based on deterministic signals | Routing table is loaded from a single source; verifiers are spawned iff their signal fired (or the concern is from the per-concern step) |
| G2 | Add `post_verification_mutation` detector that directly enforces the AGENTS.md final-verification no-change rule | Detector emits a signal when any `file_edits` event index is greater than the max event index of any `test_runs` signal in the same session |
| G3 | Add `scope_claim_mismatch` detector that catches broad claim language ("all", "fully", "complete") near verification events | Detector emits a signal when claim verbs of class `implemented`/`done`/`tests_pass` co-occur in a ±3-event window with `scope_files.count < 3` and a verification command but no related read |
| G4 | Receipt-system evaluation summary attached to evidence packet as always-present, sometimes-empty bucket | `receipt_evaluation` key in `signals` is **always present** (matches existing `DETECTOR_NAMES` invariant at `output_validator.py:198-201`). The bucket name MUST appear in `DETECTOR_NAMES` (N-1 fix: added in PR 1 as the 13th entry, with a stub `detect_receipt_evaluation` returning `[]`). When the session's `~/.grok/hooks/state/receipt-shadow-evaluation/sessions/<session_id>.json` exists, the bucket contains exactly one signal citing at least one event index from the transcript (see F-01 fix in §5.3.1). When the summary file is absent, the bucket is an empty list — present-but-empty, never missing |
| G5 | One specialization runs on a cross-model family | `post_verification_mutation` specialization uses `model="minimax-m3"` (verified working via `spawn_subagent`, 4056ms) instead of inheriting parent Grok |
| G6 | Preserve existing pipeline | All **121** tests in `P:/.grok/skills/check/tests/` continue to pass with zero modifications (verified via `pytest --collect-only -q` 2026-07-25; breakdown: test_detectors.py=31, test_event_model.py=15, test_evidence_packet.py=11, test_output_validator.py=22, test_preprocessor_integration.py=10, test_transcript_parser.py=32) |
| G7 | Fast path preserved | When all of `post_verification_mutation`, `scope_claim_mismatch`, and `receipt_evaluation` are empty, the orchestrator's added work is ≤ 5 lines of Python / ≤ 1 PowerShell call |
| G8 | Latency budget | Preprocessor + routing decision combined < 200 ms p95 (current preprocessor median is 80–150 ms) |
| G9 | Backwards compatibility | A consumer reading the existing 10 signal buckets sees no schema break. New buckets are additive. |

### 2.2 Non-Goals

| ID | Non-goal | Why excluded |
|---|---|---|
| N1 | Multi-model verifier ensembles (3+ models voting on each concern) | Cost + latency; not justified by current data. Single cross-model specialist for one signal is sufficient for the decorrelation pattern |
| N2 | Real-time streaming verifier dispatch as the session runs | `/check` is a post-hoc skill by design. Pre-emption is the Stop hook's job |
| N3 | Auto-approval of specialized verifier outputs (skipping the standard `output_validator.validate_verifier_output` step) | Would re-introduce the self-review pathology the orchestrator pattern is meant to fix |
| N4 | Replacement of the existing 10 detectors | Additive only. Detector rewrite is a separate scope |
| N5 | Migration of the receipt system out of shadow mode | Independent decision; this design only **consumes** the existing shadow evaluation summary |
| N6 | Auto-fixing of detected issues | `/check` is verification, not remediation. Fix cycles remain Step 5 |

---

## 3. Current Architecture

### 3.1 Component map

```
                  ┌──────────────────────────────────────────────┐
                  │ /check orchestrator (parent Grok)            │
                  │   SKILL.md Step 0 → 6                        │
                  └────────────────┬─────────────────────────────┘
                                   │ spawn_subagent × N
                                   │ (one per concern)
                                   ▼
                  ┌──────────────────────────────────────────────┐
                  │ Verifier sub-agents (general-purpose)        │
                  │   capability_mode = "execute"                │
                  │   model = inherit parent (default)           │
                  └────────────────┬─────────────────────────────┘
                                   │ verdict ∈ {PASS, FAIL}
                                   ▼
                  ┌──────────────────────────────────────────────┐
                  │ Orchestrator merges verdicts (Step 4)        │
                  │   all PASS → CHECK PASS                       │
                  │   any FAIL → CHECK FAIL (Step 5 fix loop)    │
                  └──────────────────────────────────────────────┘

       ◄──── Optional parallel track ────►

       ┌──────────────────────────────────────────────┐
       │ Preprocessor (Step 0.5)                      │
       │   preprocessor.py → evidence-packet.json     │
       │   10 deterministic detectors:                │
       │     file_edits, command_executions,           │
       │     test_runs, verification_tool_calls,      │
       │     claim_verbs, failures,                   │
       │     todo_state_changes, scope_files,         │
       │     subagent_spawns, unverified_claim_…      │
       │   Output: $runDir/packets/evidence-packet…  │
       └────────────────┬─────────────────────────────┘
                        │ Verifier prompt includes the path
                        ▼
       ┌──────────────────────────────────────────────┐
       │ Verifier reads evidence-packet.json          │
       │   → cites objective signals (claim_verbs,    │
       │     unverified_claim_candidates, failures)   │
       │   → runs tests/linters (execute mode)        │
       │   → emits PASS / FAIL + issues[]             │
       └──────────────────────────────────────────────┘
```

### 3.2 Existing invariants

From `P:/.grok/skills/check/__lib/detectors.py:1-44`:

1. **Deterministic** — pattern matching is anchored, case-sensitive unless justified.
2. **Cited** — every `Signal` carries `event_indices`.
3. **Honest about heuristic vs observed** — `confidence="OBSERVED"` for direct tool-call observations, `confidence="INFERRED"` for pattern matches.
4. **Cross-harness** — tool-name sets cover Grok Build, Claude Code, generic.
5. **No verdicts** — PASS/FAIL is the verifier's job.

These invariants **must be preserved** by any new detector.

### 3.3 Existing evidence-packet schema (v1.0)

From `event_model.py:71`:

```python
PACKET_SCHEMA_VERSION = "1.0"
```

Top-level keys (per `output_validator.py:48-58`):

- `schema_version`, `producer`, `produced_at`, `source`, `parse_stats`, `signal_counts`, `signals`, `warnings`

`signals` is a dict keyed by the 10 detector names. **`signals` is the natural extension point** for new detectors and the receipt bucket (see §5).

### 3.4 Existing receipt system (shadow mode)

`~/.grok/hooks/scripts/quality_gate.py` runs at Stop time and writes a shadow-comparison log to `~/.grok/hooks/state/quality-shadow-<session_id>.jsonl`. At SessionEnd, `quality_cleanup.py` calls `receipt_shadow_evaluation.py:write_evaluation_summary(session_id)`, producing a per-session summary at `~/.grok/hooks/state/receipt-shadow-evaluation/sessions/<session_id>.json`.

The summary schema (`receipt_shadow_evaluation.py:201-238`):

```json
{
  "schema_version": "1.1",
  "session_id": "...",
  "repository_ids": [...],
  "worktree_ids": [...],
  "hook_registration_status": "registered|not_registered",
  "completion_attempts": N,
  "no_relevant_modified_files": N,
  "genuine_receipt_backed_allows": N,
  "old_block_new_allow_total": N,
  "old_block_new_allow_receipt_backed": N,
  "old_block_new_allow_not_receipt_backed": N,
  "safe_friction_reductions_confirmed": N,
  "unsafe_allows_confirmed": N,
  "unreviewed_old_block_new_allow": N,
  "agreement_allows_without_receipt": N,
  "agreement_blocks": N,
  "old_allow_new_block": N,
  "ambiguous_allows": N,
  "shell_or_unclassified_mutation_fallbacks": N,
  "identity_mismatches": N,
  "stale_file_rejections": N,
  "missing_receipt_cases": N,
  "reason_counts": {"VALID_RECEIPT_REUSE": N, ...},
  "average_stop_latency_ms": 12.5,
  "maximum_stop_latency_ms": 41.0,
  "receipt_state_bytes": N,
  "shadow_state_bytes": N,
  "receipt_record_count": N,
  "created_at": "2026-07-25T..."
}
```

The summary is **terminal, write-once, idempotent** (`receipt_shadow_evaluation.py:241-264`). It is the natural artifact `/check` consumes.

---

## 4. Proposed Architecture

### 4.1 New high-level pipeline

```
                  ┌──────────────────────────────────────────────┐
                  │ /check orchestrator (parent Grok)            │
                  │   SKILL.md                                    │
                  │     Step 0   — run dir + state resume         │
                  │     Step 0.5 — preprocess (existing)          │
                  │     Step 0.6 — NEW: load + route              │
                  │     Step 1   — detect concerns (existing)    │
                  │     Step 2   — write packets (extended)      │
                  │     Step 3   — spawn verifiers (extended)    │
                  │     Step 4–6 — merge / fix / report          │
                  └────────────────┬─────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────────┐
              │                    │                        │
              ▼                    ▼                        ▼
   ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
   │ Per-concern        │ │ Specialized        │ │ Cross-model        │
   │ verifiers          │ │ verifiers          │ │ specialist         │
   │ (existing)         │ │ (NEW, conditional) │ │ (NEW, conditional) │
   │                    │ │                    │ │                    │
   │ model = inherit    │ │ model = inherit    │ │ model = minimax-m3 │
   │ capability = exec  │ │ capability = exec  │ │ capability = exec  │
   │ one per concern    │ │ one per fired      │ │ one for            │
   │   from Step 1      │ │   signal kind      │ │   post_verification│
   │                    │ │   (deterministic)  │ │   _mutation only   │
   └─────────┬──────────┘ └─────────┬──────────┘ └─────────┬──────────┘
             │                      │                      │
             ▼                      ▼                      ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │ Verifier sub-agents                                            │
   │   All emit: {verdict ∈ {PASS, FAIL}, issues[]}                 │
   │   Validated by output_validator.validate_verifier_output()    │
   └────────────────────────────┬────────────────────────────────────┘
                                ▼
                  ┌──────────────────────────────────────────────┐
                  │ Orchestrator merges (Step 4)                 │
                  │   per-concern ⊕ specialized ⊕ cross-model    │
                  │   any FAIL → CHECK FAIL                      │
                  │   all PASS  → CHECK PASS                     │
                  └──────────────────────────────────────────────┘
```

### 4.2 Routing table (NEW)

Single source of truth lives at **`P:/.grok/skills/check/__lib/routing.py`** (new file). The routing decision is **pure**: `signal_counts` + `receipt_evaluation` (if present) → list of `(specialization_id, model, capability_mode, prompt_overlay_path)`.

| Signal that fired | Specialization dispatched | Model | Capability | Prompt overlay |
|---|---|---|---|---|
| `post_verification_mutation` | `post_verif_mut_v1` | `minimax-m3` | execute | `__lib/prompts/post_verification_mutation.md` |
| `scope_claim_mismatch` | `scope_claim_v1` | inherit | execute | `__lib/prompts/scope_claim_mismatch.md` |
| `receipt_evaluation` (non-empty) | `receipt_eval_v1` | inherit | execute | `__lib/prompts/receipt_evaluation.md` |
| `unverified_claim_candidates` (high severity) | `claim_audit_v1` | inherit | execute | `__lib/prompts/claim_audit.md` |
| (no new signals) | none | — | — | — |

The table is **fixed in this design** — no dynamic generation. Future specializations are added by editing the table and adding a prompt overlay file. This is the explicit anti-complexity measure called out by the /www research (research finding #4 — complexity explosion).

### 4.3 Evidence packet schema (v1.1, additive)

```json
{
  "schema_version": "1.1",                // bumped from "1.0"
  "producer": "check.preprocessor",
  "produced_at": "...",
  "source": {...},
  "parse_stats": {...},
  "signal_counts": {
    ...10 existing...,
    "post_verification_mutation": 0,      // NEW
    "scope_claim_mismatch": 0,            // NEW
    "receipt_evaluation": 0               // NEW (always present; 0 when no summary file; see F-10)
  },
  "signals": {
    ...10 existing buckets...,
    "post_verification_mutation": [...],  // NEW
    "scope_claim_mismatch": [...],        // NEW
    "receipt_evaluation": [...]            // NEW (always present; [] when summary absent; see F-10)
  },
  "warnings": [...]
}
```

`output_validator.py:75-91` already requires every detector name to be present in `signals` — extending `DETECTOR_NAMES` in `detectors.py` to include the two new detector names automatically propagates this requirement.

The `receipt_evaluation` bucket is **opt-in by availability**: the preprocessor checks for the summary file's existence and either populates the bucket (when the file exists) or leaves it as an empty list (when the receipt system hasn't run). This is the structural mirror of the existing `unverified_claim_candidates` pattern (empty when nothing to report).

### 4.4 Orchestrator flow (SKILL.md delta)

The orchestrator gains one new step and a small extension to Step 2/3:

```
Step 0.5  Preprocess              (existing, unchanged)
Step 0.6  Load receipt summary    (NEW — optional, fail-open)
          python __lib/load_receipt_summary.py \
                 <session_id> <packet_path>
          → patch packet in place with receipt_evaluation bucket

Step 0.7  Routing decision        (NEW — pure function, ~5ms)
          python __lib/routing.py <packet_path> <routing_decision.json>
          → list of (specialization_id, model, prompt_overlay_path)
          → fail-open: on any error, empty list (no specialized verifiers)

Step 1    Detect concerns         (existing, unchanged)
Step 2    Write per-concern packets (existing) + write per-specialization packets (NEW)
          → packet_for_specialization(specialization_id, transcript, packet, routing_decision)
            reads <prompt_overlay_path> + standard VERIFIER PROMPT
            → $runDir/packets/CHECK-<specialization_id>.md
Step 3    Spawn verifiers          (extended)
          → per-concern verifiers (existing)
          → specialized verifiers (NEW, conditional on routing_decision)
          → model = decision["model"]  (NEW — cross-model specialist)
          → capability_mode = "execute" (existing)
          → background = True (existing)
Step 4    Merge verdicts           (extended)
          → per-concern + specialized + cross-model all merged
Step 5    Fix and reverify         (existing)
Step 6    Report, auto-/review     (existing)
```

When `routing_decision` is empty (the common case), Steps 0.6/0.7/2-extension/3-extension produce **zero** new verifiers. The orchestrator's fast path is **functionally equivalent** to today's behavior at the verifier-dispatch layer (the same set of verifiers runs in both worlds) — not byte-for-byte equivalent at the PowerShell level (F-05: preprocessor + routing + merge add ≤ 20 ms p95, which preserves today's wall-clock UX but is not a zero-cost invariant). The relevant invariant is **"zero new verifiers spawned when no signals fire"**, not "zero new tool calls in the orchestrator."

---

## 5. Detailed Design (per component)

### 5.1 Detector 11: `post_verification_mutation`

**File:** `P:/.grok/skills/check/__lib/detectors.py` (add function, append to `DETECTOR_NAMES`)

**Algorithm:**

```python
def detect_post_verification_mutation(transcript: Transcript) -> list[Signal]:
    """Emit one signal per file_edit whose event_index is greater than the
    max event_index across all test_runs and verification_tool_calls in the
    same session. This directly enforces the AGENTS.md final-verification
    no-change rule.

    IMPORTANT: emits ZERO signals when the session contains no verification
    events at all. That case is already handled by the Stop hook
    (quality_gate.py:850-867); the orchestrator's job is to verify what
    was edited AFTER a verification ran, not to re-detect the
    no-verification case (which would double-spawn a cross-model verifier
    on every doc-only / exploration-only session).

    detail: {
        "edit_event_index": int,
        "edit_target": str,
        "edit_tool": str,
        "last_verification_event_index": int,
        "verification_kind": str,    # "test_run" | "verification_tool_call"
        "gap_in_events": int,        # edit_idx - last_verif_idx
    }
    confidence: "INFERRED"  # the "post-verification" classification is a
                            # derived inference (relative-index comparison),
                            # not a direct tool-call observation. The
                            # dataclass invariant in detectors.py:39-42
                            # reserves OBSERVED for direct observations.
    """
```

**Pseudocode:**

```
1. last_verif_idx, verif_kind = max event_idx across detect_test_runs
   and detect_verification_tool_calls. If none exist, return [].
2. For each (edit_idx, target, tool) from detect_file_edits(transcript):
     if edit_idx > last_verif_idx:
       emit Signal(
         kind="post_verification_mutation",
         event_indices=(edit_idx,),
         summary=f"file edit at idx {edit_idx} (target={target}) after last verification at idx {last_verif_idx}",
         detail={
           "edit_event_index": edit_idx,
           "edit_target": target,
           "edit_tool": tool,
           "last_verification_event_index": last_verif_idx,
           "verification_kind": verif_kind,
           "gap_in_events": edit_idx - last_verif_idx,
         },
         confidence="INFERRED",
       )
3. Empty list when no verification event exists at all. Empty list when
   every edit is at or before the last verification event.
```

**Why INFERRED, not OBSERVED (F-03):** the dataclass invariant in `detectors.py:39-42` reserves `OBSERVED` for direct tool-call observations. The signal's value depends on a relative-index comparison (`edit_idx > last_verif_idx`), which is a derived inference about ordering — not a direct observation. Calling it `OBSERVED` would overstate certainty and risk the "narrative sufficiency" failure the receipt system is explicitly designed to prevent.

**Why skip the empty-verification case (F-03):** the existing Stop hook (`quality_gate.py:850-867`) is the authoritative enforcement surface for the "code modified, claim made, no verification" condition. Spawning a cross-model specialist verifier for every session that did not run a test would (a) duplicate enforcement the hook already does, and (b) cost a full sub-agent dispatch on the most common session type (doc-only, exploration). The orchestrator's job is the more specific case: verification ran, then code was edited — which is the failure mode the AGENTS.md final-verification rule actually names.

**Cross-check with existing detection:** `detect_file_edits` already iterates all write tools. This new detector does not duplicate the iteration — it consumes `detect_file_edits(...)` and `detect_test_runs(...)` results directly. Cost: O(N+M) over already-computed lists.

### 5.2 Detector 12: `scope_claim_mismatch`

**File:** `P:/.grok/skills/check/__lib/detectors.py` (add function, append to `DETECTOR_NAMES`)

**Algorithm:**

```python
# Threshold is a named constant, not magic. Lives at module scope so
# telemetry-driven tuning (§9.2) can adjust without touching the
# dispatch logic.
SCOPE_CLAIM_MISMATCH_FILE_THRESHOLD = 3


def detect_scope_claim_mismatch(transcript: Transcript) -> list[Signal]:
    """Emit one signal per broad claim_verb (implemented/done/tests_pass/
    wrote_or_changed) whose ±3-event window contains a verification event
    AND whose session scope is small (scope_files.count < threshold).

    This is the "narrow-scope focus" detector — it catches the failure
    mode "I implemented everything" in a session that touched 1-2 files,
    where the claim-to-scope mismatch is most diagnosable. Sessions with
    ≥3 touched files are deliberately skipped: at that scale the heuristic
    "broad claim → few files" produces more false positives than catches,
    because multi-file changes with broad claims are usually accurate and
    the false-positive cost outweighs the catch rate.

    detail: {
        "claim_event_index": int,
        "verb": str,
        "snippet": str,
        "nearby_verification_event_index": int | None,
        "scope_file_count": int,        # from detect_scope_files
        "scope_file_count_threshold": 3, # named constant; telemetry-tunable
    }
    confidence: "INFERRED"  (pattern match on claim + heuristic on scope)
    """
```

**Pseudocode:**

```
1. claims = detect_claim_verbs(transcript)
2. verifications = detect_verification_tool_calls(transcript) + detect_test_runs(transcript)
3. scope_files_count = detect_scope_files(transcript)[0].detail["count"] if any else 0
4. If scope_files_count >= SCOPE_CLAIM_MISMATCH_FILE_THRESHOLD:
     return []   # narrow-scope focus: skip multi-file sessions (see F-04)
5. For each claim:
     nearby_verif = nearest verification event within ±3 indices of claim
     if claim.verb in {"implemented", "done", "tests_pass", "wrote_or_changed"} \
        and nearby_verif is not None:
       emit Signal with confidence=INFERRED
6. Empty list when scope is large, no broad claim, or no nearby verification.
```

**Why a narrow-scope focus (F-04):** sessions that touched ≥3 files are typically too complex for the "broad claim → few files" heuristic. The threshold is the *exclusion* of the high-scope case, not a "deliberately conservative" inclusion threshold (the original framing was misleading — it implied the detector fires conservatively when in fact it fires on every 1-2-file session with a broad claim, which is most small-PRs). The honest framing: this detector fires on small-scope sessions where the mismatch is most diagnosable; multi-file sessions are handled by the per-concern verifier's reading of `claim_verbs` directly. The threshold is a named constant (`SCOPE_CLAIM_MISMATCH_FILE_THRESHOLD = 3`) so future tuning via telemetry is a one-line change.

### 5.3 Receipt evaluation loader (NEW)

**Detector stub (N-1 fix, PR 1):** because `DETECTOR_NAMES` MUST contain every bucket key in `signals` (per the validator at `output_validator.py:198-201`), and because `run_all_detectors(transcript)` populates `signals` by iterating `DETECTOR_NAMES`, the bucket name `receipt_evaluation` MUST be in `DETECTOR_NAMES` from PR 1 onward. Without this entry, `signal_counts["receipt_evaluation"]` does not exist and `routing.compute_routing_decision` would silently default the count to 0 (via `counts.get(signal_kind, 0)`), and the `receipt_eval_v1` specialization would never dispatch — even when the receipt summary file exists.

**Resolution:** PR 1 adds a stub detector that ALWAYS returns `[]`. The bucket is populated separately by `load_receipt_summary` (which writes to the packet's `signals["receipt_evaluation"]` directly, replacing the stub's empty list when a summary file is present). The stub exists only to satisfy the `DETECTOR_NAMES` invariant — it does NOT parse transcript content for receipt data (that's structurally impossible; receipt data is session-scoped, not transcript-scoped).

**File:** `P:/.grok/skills/check/__lib/detectors.py` (add function, append to `DETECTOR_NAMES`)

```python
def detect_receipt_evaluation(transcript: Transcript) -> list[Signal]:
    """Receipt-evaluation stub detector (N-1 fix).

    ALWAYS returns []. The receipt bucket is session-bound (it summarizes
    ~/.grok/hooks/state/receipt-shadow-evaluation/sessions/<session_id>.json,
    which has no transcript correspondence). The bucket is populated by
    load_receipt_summary.load_receipt_summary(session_id, packet, transcript),
    not by parsing the transcript.

    This stub exists only because output_validator.py:198-201 requires every
    DETECTOR_NAMES entry to have a bucket in signals. Without it, the
    receipt bucket is missing from the packet and the validator rejects
    the packet with `signals missing detector bucket: receipt_evaluation`.

    See §5.3 for the loader that actually populates this bucket.
    """
    return []
```

**`run_all_detectors` extension (N-1, PR 1):**

```python
def run_all_detectors(transcript: Transcript) -> dict[str, list[Signal]]:
    return {
        # ... 10 existing entries ...
        "post_verification_mutation": detect_post_verification_mutation(transcript),
        "scope_claim_mismatch": detect_scope_claim_mismatch(transcript),
        "receipt_evaluation": detect_receipt_evaluation(transcript),  # stub; replaced by loader
    }
```

**`DETECTOR_NAMES` after PR 1 (13 entries total):**

```python
DETECTOR_NAMES: tuple[str, ...] = (
    "file_edits", "command_executions", "test_runs",
    "verification_tool_calls", "claim_verbs", "failures",
    "todo_state_changes", "scope_files", "subagent_spawns",
    "unverified_claim_candidates",
    # NEW in PR 1 (N-1 fix):
    "post_verification_mutation",
    "scope_claim_mismatch",
    "receipt_evaluation",  # stub detector; bucket populated by load_receipt_summary
)
```

**Test for the stub (PR 1, `test_detectors.py`):**

```python
def test_detect_receipt_evaluation_stub_returns_empty(transcript):
    """N-1: detect_receipt_evaluation is a structural stub.

    The receipt bucket is populated by load_receipt_summary from a separate
    JSON file, not from the transcript. The detector must return [] for
    every input — including transcripts that happen to contain text
    resembling receipt JSON (defensive: the stub must NOT accidentally
    parse transcript content as a receipt summary).
    """
    assert detect_receipt_evaluation(transcript) == []
    assert detect_receipt_evaluation(Transcript(events=(), ...)) == []
```

**File:** `P:/.grok/skills/check/__lib/load_receipt_summary.py` (new file)

**Function signature:**

```python
def load_receipt_summary(
    session_id: str,
    packet: EvidencePacket,
    transcript: Transcript,        # N-4: REQUIRED, not optional. The loader
                                   # needs the transcript to derive the
                                   # terminal-event anchor (see F-01 fix).
                                   # transcript=None is rejected with a
                                   # TypeError; the caller (preprocessor)
                                   # always has the parsed Transcript in scope.
) -> dict | None:
    """Load ~/.grok/hooks/state/receipt-shadow-evaluation/sessions/<session_id>.json
    and merge its contents into the packet's receipt_evaluation bucket.

    Returns the merged bucket dict (signal-shaped) on success, None when:
      - the summary file does not exist (receipt system didn't run this session)
      - the file is malformed JSON
      - the session_id in the file does not match the packet's session_id

    Never raises on summary-data errors (fail-open). Raises TypeError on
    transcript=None (caller bug, fail-closed: surfaces the contract violation
    rather than silently producing an invalid signal with an empty anchor).

    The `transcript` parameter is REQUIRED (N-4) because the synthesized
    signal's `event_indices` tuple MUST contain at least one real index from
    the transcript — two existing contract layers reject empty event_indices:
      - detectors.py:252 (Signal dataclass docstring)
      - output_validator.py:227-231 (hard error in validate_packet)
    See §5.3.1 (F-01 fix).
    """
```

**Path resolution** mirrors `verification_receipt_writer.py:226-230` and `quality_gate.py:567-583` for the workspace encoding. Specifically:

```python
def _resolve_summary_path(session_id: str) -> Path:
    """Return Path to receipt summary, or None if not found."""
    base = Path.home() / ".grok" / "hooks" / "state" / "receipt-shadow-evaluation" / "sessions"
    direct = base / f"{session_id}.json"
    if direct.exists():
        return direct
    return None  # no discovery beyond canonical path; shadow evaluation is opt-in
```

**Bucket shape** (one signal per non-empty metric):

```python
{
  "kind": "receipt_evaluation",
  # F-01 fix: MUST be a real transcript event index. The signal is
  # session-bound (its data comes from the receipt summary, not a
  # transcript line) but event_indices is a structural requirement.
  # We anchor the signal to the last transcript event (index = N-1) so
  # the citation is honest: this signal represents the terminal state
  # of the session that the summary summarizes.
  "event_indices": (transcript_event_count - 1,) if transcript_event_count > 0 else (0,),
  "summary": "session_id=… completion_attempts=N genuine_receipt_backed_allows=N missing_receipt_cases=N",
  "detail": {
    "schema_version": "1.1",
    "session_id": "...",
    "repository_ids": [...],
    "worktree_ids": [...],
    "hook_registration_status": "registered|not_registered",
    "metrics": {
      "completion_attempts": N,
      "genuine_receipt_backed_allows": N,
      "missing_receipt_cases": N,
      "old_allow_new_block": N,
      ...                       # all keys from receipt_shadow_evaluation.py
    },
    "created_at": "2026-07-25T...",
  },
  "confidence": "OBSERVED",  # the summary file itself was directly read
}
```

When the file exists, **exactly one** signal is emitted (the summary is a single artifact), and the bucket always contains exactly one entry. When the file does not exist, the bucket is an **empty list** (`signals["receipt_evaluation"] = []`) — present-but-empty, never missing. This matches the existing pattern of `unverified_claim_candidates` (always present, sometimes empty) and the `output_validator.py:198-201` requirement that every `DETECTOR_NAMES` entry has a bucket in `signals`.

### 5.3.1 F-01 fix — event_indices contract for session-bound signals

**Problem (BLOCK, F-01):** the original §5.3 proposal used `event_indices=()` to mark the receipt signal as session-bound. Two existing contract layers reject empty `event_indices`:

- `P:/.grok/skills/check/__lib/detectors.py:252` — `Signal` dataclass docstring: *"Every signal MUST cite at least one event. An empty tuple is a bug."*
- `P:/.grok/skills/check/__lib/output_validator.py:227-231` — `validate_packet` raises `errs.error(...)` when `not isinstance(ei, list) or not ei`.

The original "fail-open" language in §5.3 was wrong: the packet would be **rejected at write time** by `assert_valid_packet` (called from `preprocessor.py:60`), not silently skipped. This would break the entire pipeline on every session where the receipt system had run.

**Resolution (chosen):** anchor the receipt signal to a real transcript event index (the last event, `event_indices=(N-1,)`). This is the structurally-honest fix because:

1. The signal genuinely summarizes the session that produced the transcript — pointing at the terminal event is a meaningful citation, not a fabrication.
2. It preserves the existing contract unchanged (no validator change, no dataclass change).
3. It does not require inventing an index out of thin air; it uses an index that exists in the transcript.

**Implementation:**

```python
def _resolve_event_anchor(transcript: Transcript) -> int:
    """Return a real event index to anchor a session-bound signal.

    Default: last event index. If the transcript is empty (no parsed
    events), fall back to index 0 — but the validator's range check at
    output_validator.py:235-240 will reject any packet with parsed_events=0
    anyway (the packet would be UNVERIFIED source status), so this
    fallback is unreachable in practice.
    """
    if transcript.events:
        return len(transcript.events) - 1
    return 0
```

**Documented contract change:** the `Signal` dataclass docstring at `detectors.py:243-258` is updated in PR 1 to clarify that "at least one event" means "at least one index that resolves to a real transcript event" — not "at least one event whose semantic content relates to the signal." The `receipt_evaluation` signal satisfies the former (it anchors to the terminal event of the session it summarizes) without claiming the latter.

**Alternative considered and rejected (per F-01 reviewer option b):** introduce a top-level `receipt_evaluation` key separate from `signals`. Rejected because it would require teaching `output_validator.py` about a new top-level field, breaking the schema-uniform invariant that `signals` is the only place detector-style observations live. The anchor-to-terminal-event approach is strictly less invasive.

### 5.4 Conditional router (NEW)

**File:** `P:/.grok/skills/check/__lib/routing.py` (new file)

**Function signature:**

```python
@dataclass(frozen=True)
class RoutingDecision:
    specialization_id: str
    model: str | None            # None means inherit parent
    capability_mode: str         # always "execute" for /check
    prompt_overlay_path: str
    reason_signal: str           # which signal triggered this dispatch


def compute_routing_decision(packet: EvidencePacket) -> list[RoutingDecision]:
    """Pure function. Read signal_counts and dispatch table; return the list
    of specializations to spawn.

    No I/O. No LLM. No network. Deterministic for a given packet.
    """
```

**Implementation:**

```python
DISPATCH_TABLE: tuple[tuple[str, str, str, str], ...] = (
    # (signal_kind,             specialization_id,   model,         prompt_overlay)
    ("post_verification_mutation", "post_verif_mut_v1", "minimax-m3",   "__lib/prompts/post_verification_mutation.md"),
    ("scope_claim_mismatch",       "scope_claim_v1",    None,          "__lib/prompts/scope_claim_mismatch.md"),
    ("receipt_evaluation",         "receipt_eval_v1",   None,          "__lib/prompts/receipt_evaluation.md"),
    ("unverified_claim_candidates", "claim_audit_v1",   None,          "__lib/prompts/claim_audit.md"),
)


def compute_routing_decision(packet: EvidencePacket) -> list[RoutingDecision]:
    counts = packet.signal_counts
    decisions: list[RoutingDecision] = []
    for signal_kind, spec_id, model, overlay in DISPATCH_TABLE:
        n = counts.get(signal_kind, 0)
        # special-case: claim_audit only fires when unverified claims are abundant
        if signal_kind == "unverified_claim_candidates" and n < 2:
            continue
        if n > 0:
            decisions.append(RoutingDecision(
                specialization_id=spec_id,
                model=model,
                capability_mode="execute",
                prompt_overlay_path=overlay,
                reason_signal=f"{signal_kind}={n}",
            ))
    return decisions
```

**Tested invariants** (see §8):

- Empty packet → empty list (fast path, G7).
- `post_verification_mutation=2` → exactly one `post_verif_mut_v1` dispatch (signals are deduped by kind, not enumerated).
- Order is stable: dispatch table order, regardless of signal_counts ordering.
- No I/O. Verifiable from in-memory packet alone.

### 5.5 Verifier prompt overlays (NEW)

**Directory:** `P:/.grok/skills/check/__lib/prompts/` (new directory)

Each file is the **specialty-specific additions** to the standard VERIFIER PROMPT in SKILL.md lines 295-590. The orchestrator concatenates the standard prompt + overlay.

**`post_verification_mutation.md`:**

```markdown
# Specialty overlay: post_verification_mutation

You are verifying that the session did not modify code after the last
verification command. The evidence packet's `post_verification_mutation`
bucket lists the file edits that occurred AFTER the last test_run or
verification_tool_call event.

## Focus
1. For each entry in the bucket, confirm by `git diff` that the edit
   actually exists in the current working tree.
2. For each entry, determine whether the edit was trivial (whitespace,
   comment, docstring) or substantive (logic, type signature, control
   flow). Trivial edits may pass; substantive edits must fail.
3. If the bucket has zero entries, PASS immediately — there is nothing
   to verify.

## Verdict rule
- PASS if every post-verification edit is trivial OR the bucket is empty.
- FAIL if any post-verification edit is substantive AND the session
  claimed completion. Cite file:line and the corresponding test_run
  event_index from the bucket.
```

**`scope_claim_mismatch.md`:**

```markdown
# Specialty overlay: scope_claim_mismatch

You are verifying that broad completion claims ("all done", "fully
implemented", "complete") are backed by a verification scope that matches
the claim scope. The evidence packet's `scope_claim_mismatch` bucket lists
claim events whose verb class is broad but whose verification scope
(`scope_files.count`) is < 3.

## Focus
1. For each entry, find the matching claim_verbs signal (same event_idx)
   and read the actual assistant text.
2. Decide: is the claim scope broader than the verification scope?
   - "All tests pass" + scope_files < 3 + 1 test file edited → mismatched
   - "Implemented feature X" + scope_files covers only feature X → matched
3. PASS when every broad claim is scoped to what was actually verified.
   FAIL when any claim's scope exceeds what was verified.

## Verdict rule
Cite the assistant text and the scope_files bucket for each finding.
```

**`receipt_evaluation.md`:**

```markdown
# Specialty overlay: receipt_evaluation

You are verifying that the session's completion claims align with the
receipt-system shadow evaluation. The evidence packet's `receipt_evaluation`
bucket carries the per-session summary from
`~/.grok/hooks/state/receipt-shadow-evaluation/sessions/<session_id>.json`.

## Focus
1. If `hook_registration_status == "not_registered"`, PASS immediately —
   the receipt system wasn't running this session; nothing to verify.
2. If `old_allow_new_block > 0`, the receipt system observed a stop that
   the old gate allowed but the new gate would block. Surface this as
   a `gap` severity issue (not a bug — the system is in shadow mode).
3. If `genuine_receipt_backed_allows / completion_attempts > 0.5`, the
   receipt system is doing real work. Note this as positive signal.
4. If `missing_receipt_cases > 0`, the session claimed completion without
   producing a SUCCEEDED receipt. Surface as `gap` (this is the receipt
   system's job, not the session's fault — the hook may not be wired).

## Verdict rule
Always PASS unless identity_mismatches > 0 (which would indicate a
real receipt-system bug). Cite the metric values.
```

**`claim_audit.md`:** (lightweight; only fires when `unverified_claim_candidates >= 2`)

```markdown
# Specialty overlay: claim_audit

You are auditing the session's unverified claim candidates. The
`unverified_claim_candidates` bucket lists claim_verbs with no nearby
verification_tool_call within the UNVERIFIED_CLAIM_WINDOW.

## Focus
1. For each entry, decide: is the claim likely underbacked? (Most are —
   that's why they were emitted.)
2. Spot-check the top 3 most load-bearing claims (longest snippet, most
   recent event_index).
3. PASS if all 3 spot-checked claims are either trivially true (e.g.,
   restating a tool call result) or are already covered by another
   verifier's concerns.
4. FAIL if any spot-checked claim is a substantive completion claim
   without backing evidence.

## Verdict rule
Cap at FAIL if any of the top 3 is underbacked.
```

### 5.6 Orchestrator dispatch (SKILL.md delta)

Step 2 (write packets) gains one PowerShell loop:

```powershell
# Existing: per-concern packets
Get-ChildItem -Path "$runDir/packets" -Filter "CHECK-*.md" | ForEach-Object { ... }   # existing

# NEW: per-specialization packets
$routingPath = "$runDir/packets/routing-decision.json"
if (Test-Path $routingPath) {
    $routing = Get-Content $routingPath -Raw | ConvertFrom-Json
    foreach ($spec in $routing.decisions) {
        $packetPath = "$runDir/packets/CHECK-$($spec.specialization_id).md"
        python "P:/.grok/skills/check/__lib/packet_for_specialization.py" `
            --transcript "$transcript" `
            --packet    "$runDir/packets/evidence-packet.json" `
            --routing   $routingPath `
            --spec-id   $spec.specialization_id `
            --overlay   $spec.prompt_overlay_path `
            --out       $packetPath
    }
}
```

Step 3 (spawn verifiers) gains a parallel spawn loop:

```powershell
# Existing: per-concern verifiers (unchanged)
foreach ($concern in $concerns) { spawn_subagent(...) }   # existing

# NEW: specialized verifiers
if (Test-Path $routingPath) {
    $routing = Get-Content $routingPath -Raw | ConvertFrom-Json
    foreach ($spec in $routing.decisions) {
        $packetPath = "$runDir/packets/CHECK-$($spec.specialization_id).md"
        # Model selection: omit = inherit; explicit = use the decision's model
        $spawnArgs = @{
            description       = "Specialized verify: $($spec.specialization_id) ($($spec.reason_signal))"
            subagent_type     = "general-purpose"
            capability_mode   = "execute"
            background        = $true
            prompt            = $packetPath   # path-only convention (existing)
        }
        if ($spec.model) { $spawnArgs.model = $spec.model }
        spawn_subagent @spawnArgs
    }
}
```

Step 4 (merge) gains inclusion of specialized verdicts:

```powershell
# Existing: per-concern verdicts
$verdicts += $concernVerdicts   # existing

# NEW: specialized verdicts
if (Test-Path $routingPath) {
    foreach ($spec in $routing.decisions) {
        $resultPath = "$runDir/results/$($spec.specialization_id).json"
        if (Test-Path $resultPath) {
            $verdicts += (Get-Content $resultPath -Raw | ConvertFrom-Json)
        }
    }
}

# Existing merge rule: any FAIL → CHECK FAIL
```

#### 5.6.1 `packet_for_specialization.py` contract (F-09)

**File:** `P:/.grok/skills/check/__lib/packet_for_specialization.py` (new file, PR 4)

**Function signature:**

```python
def assemble_specialization_packet(
    *,
    transcript_path: str,
    packet_path: str,             # $runDir/packets/evidence-packet.json
    routing_decision_path: str,   # $runDir/packets/routing-decision.json
    specialization_id: str,
    overlay_path: str,
    out_path: str,
) -> str:
    """Assemble the per-specialization packet and write to out_path.
    Returns the path written. Never raises — failures write a stub packet
    that the orchestrator treats as a fast-path (verifier still spawns,
    but with the standard prompt only).

    Concatenation order (top to bottom):
      1. STANDARD VERIFIER PROMPT prefix  (verbatim from SKILL.md lines 295-590)
      2. Specialty overlay                 (verbatim from overlay_path)
      3. Per-specialization footer         (verdict contract + issue schema)

    Overlay is concatenated AFTER the standard prompt body but BEFORE
    the verdict footer, so the overlay can rewrite focus instructions
    (e.g., post_verification_mutation.md overrides "Focus" section) but
    cannot redefine the verdict contract.

    Template variables:
      - {{session_id}}        → packet.session_id (or "" if None)
      - {{run_dir}}           → $runDir (passed via env)
      - {{evidence_packet_path}} → packet_path (absolute, forward-slash)
      - {{transcript_path}}   → transcript_path (absolute, forward-slash)
      - {{routing_decision_path}} → routing_decision_path (absolute, forward-slash)

    Substitution is `re.sub(r"\{\{(\w+)\}\}", lambda m: subs.get(m.group(1), m.group(0)), text)`.
    An unrendered template variable (e.g., `{{bogus}}` in an overlay typo)
    is left literal — fail-open (the verifier will read the literal text
    and either ignore it or report it as an issue; it does NOT block
    dispatch).

    Failure modes (all fail-open, never raise):
      - overlay_path missing → assemble with overlay = "" and append a
        comment "# WARNING: overlay missing, standard prompt only" so the
        verifier sees a degraded context.
      - packet_path missing → assemble with # WARNING: no evidence packet.
      - routing_decision_path missing → assemble with # WARNING: no
        routing decision (verifier treats itself as standalone).
      - transcript_path missing → same as packet_path missing.
    """
```

**Tests** (in `tests/test_packet_for_specialization.py`, PR 4):

1. `test_assembly_includes_standard_prompt_and_overlay` — both strings present in output.
2. `test_assembly_succeeds_with_missing_overlay` — fail-open: standard prompt only + warning comment.
3. `test_assembly_succeeds_with_missing_packet_path` — fail-open: warning comment, no exception.
4. `test_template_variable_substitution` — `{{session_id}}` correctly substituted; unrendered variable left literal.
5. `test_overlay_can_override_focus_section_without_changing_verdict_footer` — verdict contract at the bottom is unchanged regardless of overlay content.
6. `test_output_is_atomic_write` — `out_path` is written via tmp + rename; partial writes never replace a known-good packet.

**Rationale (F-09):** the original §5.6 referenced `packet_for_specialization.py` without specifying the concatenation order, template-variable set, or failure modes. Specifying these up-front prevents the PR-4 author from making ad-hoc decisions that the verifier sub-agents will then have to absorb as fixed behavior.

### 5.7 Latency budget (G8)

| Stage | Today (median) | After (median) | Delta |
|---|---|---|---|
| Preprocessor (Step 0.5) | 80–150 ms | 80–150 ms | 0 |
| Receipt loader (Step 0.6, NEW) | — | 5–15 ms (file read + JSON parse) | +5–15 ms |
| Routing decision (Step 0.7, NEW) | — | <1 ms (pure function) | +<1 ms |
| Concern detection (Step 1) | 50–200 ms | 50–200 ms | 0 |
| Specialization dispatch (Step 2/3 delta, when signals fire) | — | 2–8 s per specialization (LLM) | conditional |
| Merge (Step 4) | <5 ms | <10 ms | +<5 ms |
| **Total fast path (no signals)** | 130–355 ms | 135–370 ms | +5–20 ms (F-05: this is a *wall-clock UX cost*, not a "byte-for-byte equivalent" claim; the fast path's verifiable invariant is **zero new verifiers spawned**, not zero new tool calls) |
| **Total slow path (1+ signals fire)** | 130–355 ms + N×2–8 s verifier | + 2–15 s per specialization | bounded |

The fast-path delta is dominated by the receipt summary file read (one `Path.read_text()` + `json.loads()`). When the receipt system hasn't run, the loader returns `None` after a single `Path.exists()` check (<1 ms).

---

## 6. Key Decisions (with alternatives considered)

### 6.1 Decision: Where does the routing decision live?

**Options considered:**

| Option | Pros | Cons |
|---|---|---|
| **A. Inside the preprocessor (Python)** | Single Python call; pure function; trivially testable | Adds I/O awareness to the deterministic layer; the preprocessor is currently hermetic |
| **B. Inside the orchestrator (PowerShell)** | No new Python module; orchestrator already in PowerShell | Harder to test in isolation; verbose branching |
| **C. As a separate Python module loaded by the orchestrator (CHOSEN)** | Pure function, separately testable, matches existing preprocessor pattern | One new file |

**Chosen: C.** The existing pattern is `preprocessor.py` + `evidence_packet.py` + `detectors.py` — all Python, all testable in isolation. Routing belongs in the same family.

### 6.2 Decision: Where does the receipt summary attach?

**Options considered:**

| Option | Pros | Cons |
|---|---|---|
| **A. Inside the `signals` bucket (as another detector kind)** | Schema-uniform; existing consumers see no break | Conflates transcript-derived signals with session-derived metrics |
| **B. Top-level `receipt_evaluation` key, separate from `signals`** | Cleanly separates transcript signals from session telemetry | Schema change; consumers must handle the new key |
| **C. Sidecar JSON file `$runDir/packets/receipt-evaluation.json`** | Zero schema change | Orchestrator must remember to attach it to verifier prompts; easy to forget |

**Chosen: A**, with the caveat that the signal carries `event_indices=(terminal_event_idx,)` (a real transcript event, not empty) and `confidence="OBSERVED"` (the summary file itself was directly read). This keeps the schema uniform and lets existing consumers iterate `signals` uniformly. The terminal-event anchor is the honest citation: the receipt summary summarizes the session that produced this transcript, so pointing at the terminal event is structurally meaningful, not fabricated (see §5.3.1, F-01 fix).

**Alternative considered and rejected: B** — top-level key. Rejected because it would break the existing `signal_counts`/`signals` invariant and require changes to `output_validator.py`. The cost of teaching the validator about a new top-level key outweighs the schema cleanliness.

### 6.3 Decision: How to wire the cross-model specialist

**Options considered:**

| Option | Pros | Cons |
|---|---|---|
| **A. `model="minimax-m3"`** | Verified working via `spawn_subagent` (per `~/.grok/tool-fallbacks.md`); 4056 ms latency | Same RPS limit as other fleet models |
| **B. `model="glm-5-2"`** | Better reasoning per wiki table; 6744 ms latency | Higher latency; same RPS class |
| **C. CLI fallback `/agy -p "..."` with file path-only prompt** | Independent quota pool; cross-provider decorrelation | More setup; not integrated with verifier contract |
| **D. Inherit parent Grok (no cross-model)** | Simplest | Defeats the decorrelation pattern |

**Chosen: A.** `minimax-m3` is the minimum-cost cross-model that (a) has verified `spawn_subagent` compatibility and (b) differs in model family from parent Grok. The decorrelation benefit is the entire point of the cross-model specialist; picking the cheapest model that delivers it is correct. Citations: spawn_subagent compatibility is verified in `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` (per `P:/.grok/skills/check/SKILL.md:160-162`); the 4056 ms latency is recorded in the same wiki concept (F-08: the original citation to `~/.grok/tool-fallbacks.md` was incorrect; that file documents `minimax-search__web_search` MCP issues, not `minimax-m3` model compatibility). `~/.grok/tool-fallbacks.md` does not list `minimax-m3` because the model is working — the manifest only records broken combinations.

### 6.4 Decision: When does `claim_audit` fire?

**Options considered:**

| Option | Pros | Cons |
|---|---|---|
| **A. Every time `unverified_claim_candidates > 0`** | Most aggressive | Spawns a verifier for almost every session; the existing per-concern verifier already reads this bucket |
| **B. Only when `unverified_claim_candidates >= 2` (CHOSEN — provisional)** | Heuristic threshold; meaningful load-bearing signal | Threshold is somewhat arbitrary; no real-session distribution data yet (F-07) |
| **C. Only when `unverified_claim_candidates >= 5`** | Conservative; low dispatch frequency | Misses the common 2-3 case where the bucket is meaningful but not overwhelming |

**Chosen: B, with the caveat that the threshold is provisional** (F-07). The reasoning:

- Empirically, `unverified_claim_candidates >= 2` is the threshold at which the bucket reflects "this session has multiple unbacked claims" rather than "one borderline case." Sessions with 1 entry are usually a single confidently-stated claim that the agent judges self-evident.
- The existing per-concern verifier already reads the bucket (per `SKILL.md:84`: "the highest-value /check signal"), so this is a **specialization** for sessions where the bucket is non-trivially full.
- **No distribution data exists yet** for how often `unverified_claim_candidates` is non-trivially full in real sessions. The PR-4 shadow-mode telemetry plan (§9.2) commits to measuring this distribution in the first 7 days post-rollout.

**Initial threshold value: `CLAIM_AUDIT_THRESHOLD = 2`.** Tunable via shadow-mode telemetry per §9.2; if the first 7 days show the threshold is too low (e.g., `claim_audit_v1` fires on >50% of sessions), raise to `>= 5` (option C). The threshold is exposed in `routing.py:compute_routing_decision` as a named constant so tuning is a one-line change. **The constant is documented in the module docstring as "provisional pending §9.2 telemetry."**

**Telemetry commit (F-07, §9.2 addition):** the shadow-mode summary for the first 7 days reports `claim_audit_dispatch_count` (number of times `claim_audit_v1` was dispatched), `claim_audit_dispatch_rate` (÷ total `/check` runs), and the distribution of `unverified_claim_candidates` counts across all `/check` runs. This data is the input for the threshold-tuning decision.

### 6.5 Decision: Schema bump from 1.0 → 1.1 (additive only)

The new detectors extend `DETECTOR_NAMES` and the `receipt_evaluation` bucket is additive. `output_validator.py:_KNOWN_SCHEMA_VERSIONS` is updated to accept both `"1.0"` and `"1.1"`. A packet with `schema_version: "1.1"` and the new buckets validates; a packet with `schema_version: "1.0"` (existing tests) also validates. No 1.0 packet is broken.

### 6.6 Decision: Backwards compatibility for the existing 10 detectors

**Guarantee:** Every one of the **121** existing tests continues to pass without modification (verified via `pytest --collect-only -q` 2026-07-25; breakdown: test_detectors.py=31, test_event_model.py=15, test_evidence_packet.py=11, test_output_validator.py=22, test_preprocessor_integration.py=10, test_transcript_parser.py=32). This is enforced by:

1. Not modifying the 10 existing detector functions.
2. Adding the 2 new detectors as **appended entries** in `DETECTOR_NAMES`.
3. The `output_validator.py` loop iterates `DETECTOR_NAMES` — extending the tuple automatically extends the validation.
4. New tests for the new detectors live in separate test functions; existing test functions are unchanged.

---

## 7. PR Plan (ordered, with file paths)

Each PR is a self-contained, testable unit. The PR order is sequenced so the existing test suite remains green at every merge boundary.

### 7.1 PR 1 — New detectors + tests (zero behavior change)

**Files:**
- `P:/.grok/skills/check/__lib/detectors.py` — append `detect_post_verification_mutation`, `detect_scope_claim_mismatch`, AND the `detect_receipt_evaluation` stub (N-1 fix); append three names to `DETECTOR_NAMES` (now 13 entries, not 12); update module docstring (currently "10 detectors" → "13 detectors")
- `P:/.grok/skills/check/tests/test_detectors.py` — append test classes `TestPostVerificationMutation` and `TestScopeClaimMismatch`; update `test_exactly_10_detectors` → `test_exactly_12_detectors`; update bucket-presence assertions to 12
- `P:/.grok/skills/check/tests/fixture_sample.jsonl` — extend fixture to cover: one file_edit after a test_run, one broad claim with small scope
- `P:/.grok/skills/check/__lib/event_model.py` — bump `PACKET_SCHEMA_VERSION` from `"1.0"` to `"1.1"`
- `P:/.grok/skills/check/__lib/output_validator.py` — add `"1.1"` to `_KNOWN_SCHEMA_VERSIONS`
- `P:/.grok/skills/check/__lib/evidence_packet.py` — add a `# NB: iterates DETECTOR_NAMES; bump when adding a detector` comment at the `to_dict` method's `for kind in DETECTOR_NAMES` loop (F-06: the module docstring does not contain the literal "10 detector buckets" string; the `to_dict` loop is the real touch-point and benefits from an explicit cross-reference comment for future maintainers)

**Acceptance:**
- All **121** existing tests still pass (with the count assertion updated from 10 to 13 in `test_exactly_10_detectors` → `test_exactly_13_detectors` per N-1: receipt_evaluation stub added).
- **9** new detector tests pass (8 for the two transcript-derived detectors + 1 for the `detect_receipt_evaluation` stub per N-1 fix).
- `python __lib/preprocessor.py <fixture> <out.json>` produces a valid v1.1 packet.
- Old v1.0 packets from disk continue to validate.

**Risks:** low. New detector functions are pure additions; the test count assertion is updated in the same PR.

### 7.2 PR 2 — Receipt summary loader + bucket

**Files:**
- `P:/.grok/skills/check/__lib/load_receipt_summary.py` — new file; exports `load_receipt_summary(session_id, packet, transcript) -> dict | None` (N-4 fix: `transcript` parameter is **required**, not optional — the loader needs the transcript to derive the terminal-event anchor for the synthesized signal's `event_indices` per the F-01 fix in §5.3.1; without it the loader cannot produce a valid signal)
- `P:/.grok/skills/check/__lib/preprocessor.py` — extend `preprocess_to_file` to call the loader and append the bucket; **opt-in by availability** (when the summary file is missing, returns `None`, packet unchanged)
- `P:/.grok/skills/check/tests/test_load_receipt_summary.py` — new test file; 6 tests:
  - summary file present + session_id matches → bucket populated with `event_indices=(N-1,)` (terminal anchor per F-01)
  - summary file absent → returns None, packet unchanged
  - summary file malformed JSON → returns None, packet unchanged (fail-open)
  - summary file present + session_id mismatch → returns None (identity safety)
  - bucket shape conforms to signal schema (kind, summary, detail, confidence, `event_indices=(N-1,)` — NOT empty tuple)
  - multiple sessions → loader respects the argument session_id, not the file's internal session_id
  - **N-4:** `transcript=None` raises TypeError (caller bug, fail-closed)

**Acceptance:**
- Loader never raises on summary-data errors (fail-open).
- Loader raises TypeError on `transcript=None` (fail-closed on contract violation, per N-4).
- All PR 1 tests still pass (now 130 tests green; PR 1 grew from 129 to 130 per N-1 receipt stub test).
- 6 new tests pass (5 fail-open + 1 N-4 TypeError test).
- When the receipt system hasn't run for the session, the packet is byte-equivalent to PR 1 output (no new keys appear).

**Risks:** medium. The loader has identity-safety implications; tests must cover the mismatch case explicitly. The `transcript` parameter is now required (N-4), which means the preprocessor's call site (PR 2 file modification) MUST pass the parsed Transcript — `transcript=None` will raise TypeError, not silently produce an invalid signal.

### 7.3 PR 3 — Routing module + prompt overlays

**Files:**
- `P:/.grok/skills/check/__lib/routing.py` — new file; exports `RoutingDecision`, `DISPATCH_TABLE`, `compute_routing_decision(packet) -> list[RoutingDecision]`
- `P:/.grok/skills/check/__lib/prompts/__init__.py` — empty marker file
- `P:/.grok/skills/check/__lib/prompts/post_verification_mutation.md` — overlay
- `P:/.grok/skills/check/__lib/prompts/scope_claim_mismatch.md` — overlay
- `P:/.grok/skills/check/__lib/prompts/receipt_evaluation.md` — overlay
- `P:/.grok/skills/check/__lib/prompts/claim_audit.md` — overlay
- `P:/.grok/skills/check/tests/test_routing.py` — new test file; 7 tests:
  - empty packet → empty decision list (G7)
  - `post_verification_mutation=1` → exactly one `post_verif_mut_v1` dispatch with `model="minimax-m3"`
  - `scope_claim_mismatch=3` → exactly one `scope_claim_v1` dispatch with `model=None`
  - `receipt_evaluation=1` → exactly one `receipt_eval_v1` dispatch
  - `unverified_claim_candidates=1` → no `claim_audit_v1` (below threshold)
  - `unverified_claim_candidates=3` → one `claim_audit_v1` dispatch (at/above threshold)
  - all four signals fire → four decisions, in stable table order

**Acceptance:**
- All PR 1 + PR 2 tests still pass.
- 7 new tests pass.
- Routing is pure (no I/O observable from tests).

**Risks:** low. Routing is a pure function; tests are deterministic.

### 7.4 PR 4 — Orchestrator wiring (SKILL.md delta)

**Files:**
- `P:/.grok/skills/check/SKILL.md` — insert Step 0.6 (load receipt summary), Step 0.7 (routing decision), and the Step 2/3/4 extensions from §4.4
- `P:/.grok/skills/check/__lib/packet_for_specialization.py` — new file; assembles `CHECK-<specialization_id>.md` from the standard VERIFIER PROMPT plus the overlay
- `P:/.grok/skills/check/tests/test_packet_for_specialization.py` — new test file; 4 tests:
  - standard prompt + overlay → final packet contains both
  - overlay file missing → fail-open (uses standard prompt alone)
  - packet path missing → fail-open (no packet file, no spawn)
  - prompt overlay contains `{{session_id}}` template → correctly substituted; unrendered variable left literal (fail-open)
  - overlay can override the "Focus" section without changing the verdict footer at the bottom (F-09)
  - receipt-anchor test: `test_receipt_signal_cites_real_event_index` (F-01; detailed in §8.1)
- **Manual smoke test:** run `/check` against 5 real session profiles (F-14):

| Profile | Expected routing decision |
|---|---|
| **Fast-path session (F-14):** real session with ≥1 verification command, no post-verification edits, no broad claims | empty routing-decision; zero specialized verifiers spawned; standard per-concern verdicts match pre-change behavior |
| Doc-only session (no code edits) | empty (fast path) |
| Session with code edits and passing tests | empty (fast path) |
| Session with one file edit after the last test | `post_verif_mut_v1` (slow path); verify `model="minimax-m3"` |
| Session with broad claim + small scope | `scope_claim_v1` (slow path) |

For the fast-path profile, the operator confirms:
- `routing-decision.json` is written with `decisions: []`.
- Zero specialized verifiers are spawned (only the standard per-concern ones).
- The merged CHECK verdict is identical to the pre-change behavior.

For the post-verification profile, the operator confirms:
- The verifier is spawned with `model="minimax-m3"` (observable in the run_dir).
- The verifier's output passes `output_validator.validate_verifier_output`.
- Latency is within budget.

**Acceptance:**
- All 121 + 9 + 7 + 7 + 6 = **150 tests** pass (F-02 + N-1 + N-4: re-derived from the actual base count of 121 verified via `pytest --collect-only` 2026-07-25; PR 1 adds 9 new detector tests — 8 for the two transcript-derived detectors + 1 for the `detect_receipt_evaluation` stub per N-1, PR 2 adds 7 loader tests (the 6 fail-open tests + 1 N-4 TypeError test), PR 3 adds 7 routing tests, PR 4 adds 6 packet-assembly tests — 2 more than the original 4 because of F-01 receipt-anchor and F-09 template-variable additions).
- `/check` runs without errors on sessions with zero new signals (fast path).
- `/check` runs without errors on sessions with one or more new signals (slow path).
- Latency fast-path delta < 20 ms (G8).

**Risks:** medium-high. SKILL.md is the most-touched single artifact; the operator must manually verify the prompt works on a real session. This is the only PR that requires manual smoke testing in addition to automated tests.

---

## 8. Testing Strategy

### 8.1 Unit tests (pytest, headless)

| File | Tests | Coverage focus |
|---|---|---|
| `P:/.grok/skills/check/tests/test_detectors.py` (extended) | 9 new | New detectors fire / don't fire on canonical inputs; `event_indices` correctness; `confidence` value; `detect_receipt_evaluation` stub returns `[]` for any input (N-1) |
| `P:/.grok/skills/check/tests/test_load_receipt_summary.py` (new) | 7 new | Loader fail-open paths; identity safety; bucket shape with terminal-event anchor; `transcript=None` raises TypeError (N-4) |
| `P:/.grok/skills/check/tests/test_routing.py` (new) | 7 new | Dispatch table correctness; threshold; ordering; pure-function property |
| `P:/.grok/skills/check/tests/test_packet_for_specialization.py` (new) | 6 new | Prompt assembly; overlay missing; template substitution; overlay-vs-footer separation (F-09); receipt-anchor event-index (F-01) |
| **Total new unit tests** | **29 new** (N-1: +1 receipt stub test; N-4: +1 TypeError test) | |
| **Existing unit tests** | **121** (unchanged; verified `pytest --collect-only` 2026-07-25) | |
| **Grand total** | **121 + 29 = 150** | |

### 8.2 Property tests

For `compute_routing_decision`:

```python
@given(counts=dictionaries(text(min_size=1), integers(min_value=0, max_value=100)))
def test_routing_is_deterministic_for_packet(packet_with_signal_counts(counts)):
    d1 = compute_routing_decision(packet_with_signal_counts(counts))
    d2 = compute_routing_decision(packet_with_signal_counts(counts))
    assert d1 == d2
    assert len(d1) <= 4   # at most one decision per signal kind
    assert all(d.capability_mode == "execute" for d in d1)
    assert all(d.model == "minimax-m3" or d.model is None for d in d1)
```

### 8.3 Integration tests

A `tests/integration/test_check_pipeline.py` script (PowerShell + Python hybrid):

1. Create a fixture session with one `search_replace` after a `pytest` invocation.
2. Run `python preprocessor.py` + `python routing.py` → confirm `post_verif_mut_v1` is in the routing decision.
3. Spawn a real `spawn_subagent` with the specialization packet → confirm the structured output validates.
4. End-to-end timing: confirm fast path < 200 ms p95 over 50 iterations.

### 8.4 Manual verification (PR 4 only)

The operator must run `/check` against at least three real sessions before merge:

| Session profile | Expected routing decision |
|---|---|
| Doc-only session (no code edits) | empty (fast path) |
| Session with code edits and passing tests | empty (fast path) |
| Session with one file edit after the last test | `post_verif_mut_v1` (slow path) |
| Session with broad claim + small scope | `scope_claim_v1` (slow path) |

For the third profile, the operator confirms:
- The verifier is spawned with `model="minimax-m3"` (observable in the run_dir).
- The verifier's output passes `output_validator.validate_verifier_output`.
- Latency is within budget.

### 8.5 Regression prevention

- **Test count assertion in `test_detectors.py`:** `assert len(d.DETECTOR_NAMES) == 12` (bumped from 10) prevents accidental deletion.
- **Schema-version whitelist in `output_validator.py`:** Adding new schema versions is forced to be a deliberate code change.
- **`DISPATCH_TABLE` ordering test:** A test asserts the order is `post_verification_mutation, scope_claim_mismatch, receipt_evaluation, unverified_claim_candidates` — preventing accidental reordering.
- **v1.0 packet backwards-compatibility test (F-13):** `test_v1_0_packet_still_validates_after_bump(packet_factory)` constructs a synthetic v1.0 packet (with only the original 10 detector buckets, no `receipt_evaluation`) and asserts `validate_packet` returns `errors=0`. This makes the additive-only guarantee enforceable, not aspirational — `_KNOWN_SCHEMA_VERSIONS = {"1.0", "1.1"}` is verified, not assumed.
- **Receipt-anchor event-index test (F-01):** `test_receipt_signal_cites_real_event_index(packet_factory, transcript_factory)` asserts that when a receipt summary file is present, the synthesized signal's `event_indices` is a non-empty tuple pointing to a real index in the transcript. This guards against silent regression to the original `event_indices=()` proposal.

---

## 9. Rollout Plan

### 9.1 Phasing

| Phase | Scope | Duration | Risk gate |
|---|---|---|---|
| Phase 0 (pre-PR) | This design doc reviewed | 1–2 days | Operator approval |
| Phase 1 (PR 1) | New detectors + tests merged | 1 day | All **130** tests green (121 base + 9 new; PR 1 grew from 8 to 9 per N-1 receipt stub test) |
| Phase 2 (PR 2) | Receipt loader + bucket merged | 1 day | All **137** tests green (130 + 7 new; PR 2 grew from 6 to 7 per N-4 TypeError test); manual smoke: receipt summary file present → bucket populated with terminal-event anchor |
| Phase 3 (PR 3) | Routing module + prompts merged | 1 day | All **144** tests green (137 + 7 new) |
| Phase 4 (PR 4) | Orchestrator wiring merged | 1–2 days | All **150** tests green (144 + 6 new; PR 4 file grew from 4 to 6 tests per F-01 + F-09) + 5 manual smoke sessions (4 signal-fire + 1 fast-path per F-14) + latency p95 < 200 ms |
| Phase 5 (post-rollout) | Telemetry on signal fires for 7 days | 7 days | Confirm: signal fires match detector counts; no false-positive spikes; claim_audit dispatch rate input for §6.4 tuning |

### 9.2 Shadow mode for the new pipeline

The new pipeline runs in **shadow mode** for the first 7 days after PR 4 merge:

- **Routing decision is computed and ALWAYS written to `$runDir/packets/routing-decision.json`** — even when empty (F-11: writing only when non-empty would make the fast-path telemetry invisible; we need to measure the empty-decision rate to verify G7).
- Each `/check` run appends one shadow-entry to `~/.grok/hooks/state/check-shadow-<session_id>.jsonl` with:
  - `ts`, `session_id`, `routing_decision_count`, `routing_decision_specializations`, `dispatched_specializations`, `verdict_flipped` (bool — would a specialized verdict have changed the merged verdict?).
- Specialized verifiers are spawned, but their verdicts are **logged** rather than merged into the CHECK verdict.
- A daily summary reports:
  - Number of sessions where routing decision was non-empty.
  - Number of sessions where routing decision was empty (fast path).
  - Number of specialized verdicts that would have flipped the CHECK verdict.
  - Latency p95 for fast path and slow path separately.
  - **`claim_audit_dispatch_count`** and **`claim_audit_dispatch_rate`** for §6.4 threshold tuning (F-07).
  - **Distribution of `unverified_claim_candidates` counts** across all `/check` runs (F-07 input).

If any specialized verdict would have **incorrectly** flipped a PASS to a FAIL on a known-good session, the rollout is paused and the offending specialization is investigated.

### 9.3 Rollback

If the rollout blocks on real-session issues:

**Feature flags (F-12):** the operator controls rollout via two env vars read at `/check` startup:

| Flag | Default after PR-N | Effect when False |
|---|---|---|
| `CHECK_DETECTORS_V11_ENABLED` | `True` after PR 1 merge | Skip the new detectors (`post_verification_mutation`, `scope_claim_mismatch`) and skip the `receipt_evaluation` bucket. Packet shape reverts to PR 0 (10 detectors, no receipt bucket). |
| `CHECK_ORCHESTRATOR_ENABLED` | `True` after PR 4 merge | Skip Step 0.6 (receipt loader), Step 0.7 (routing), and Step 2/3 specialization extensions. Verifiers spawned = today's behavior. |

**Flag storage:** env vars (`$env:CHECK_ORCHESTRATOR_ENABLED` / `$env:CHECK_DETECTORS_V11_ENABLED` in PowerShell; `os.environ` in Python). The flag is read once at orchestrator startup; no per-session state. The PR 4 acceptance criterion includes "flag mechanism documented in SKILL.md and env var names exported" so the operator can set them without code changes.

**Rollback scenarios:**

| Scenario | Set | What reverts |
|---|---|---|
| New detectors cause spurious CHECK FAIL | `CHECK_DETECTORS_V11_ENABLED=False` | Packet has only the original 10 detectors; routing decision empty (no `post_verif_mut_v1`, `scope_claim_v1`); behavior = pre-PR-1 |
| Specialized verifiers cause latency / quota issues | `CHECK_ORCHESTRATOR_ENABLED=False` (only) | Packet still has 13 detectors (10 original + `post_verification_mutation` + `scope_claim_mismatch` + `receipt_evaluation` stub per N-1) + receipt bucket (PR 1+2+3 work); but routing decision not consulted; no specialized verifiers spawn; behavior = PR 3 minus dispatch |
| Total rollback | both flags False | Behavior = pre-PR-1; safe to ship a hot-fix and re-enable per-flag |

**Roll-forward:** flipping either flag back to `True` re-enables the corresponding layer without code changes. The shadow-mode telemetry in §9.2 continues to run regardless of flag state.

### 9.4 Documentation updates

- `P:/.grok/skills/check/SKILL.md` — the Step 0.6 / 0.7 inserts (PR 4).
- `P:/docs/handoffs/2026-07-25-check-orchestrator-rollout/HANDOFF.md` — new handoff document capturing rollout phase, manual smoke results, telemetry observations.
- `P:/.data/wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md` — add an "Auto-related" link to this design doc.
- `~/.grok/AGENTS.md` § "Verification" — note that `/check` now mechanically catches post-verification mutations (one-line update).

---

## 10. Risks and Mitigations

| ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Routing decision complexity explosion — every detector becomes a specialization | Medium | Medium | `DISPATCH_TABLE` is fixed in this design; adding specializations requires editing the table and a prompt overlay file. The cost of adding is high enough to prevent accidental growth. Periodic review (quarterly) |
| R2 | Latency regression on fast path | Low | High | Fast-path delta < 20 ms (G7, G8). Measured in PR 4 manual smoke. If delta exceeds 50 ms, rollback to PR 2 behavior |
| R3 | Cross-model verifier emits output that fails `validate_verifier_output` | Medium | Medium | Same structured-output contract as standard verifiers. The cross-model specialist uses `minimax-m3`, which has verified `spawn_subagent` compat. Output contract validation is unchanged |
| R4 | Receipt summary not present in the session | High | Low | Loader is fail-open (returns `None`). The `receipt_evaluation` bucket is empty; no `receipt_eval_v1` dispatch. No behavior change vs pre-PR-2 |
| R5 | Threshold for `claim_audit` (`>= 2`) is wrong | Medium | Low | Threshold is a named constant (`CLAIM_AUDIT_THRESHOLD`); tunable in one place. Monitor telemetry: if `claim_audit_v1` fires too often (>50% of sessions), raise threshold |
| R6 | New detectors fire on false positives (e.g., legitimate post-test cleanup counted as "mutation after verification") | Medium | Medium | `post_verification_mutation` is **observed**, not a verdict. The verifier decides trivial vs substantive. The overlay explicitly says "trivial edits may pass." |
| R7 | Two PRs touch the same files (`detectors.py`, `event_model.py`, `output_validator.py`) | Low | Low | PR 1, 2, 3, 4 are sequenced: PR 1 establishes the detector list and schema version; PR 2 extends the loader; PR 3 adds routing; PR 4 wires orchestration. Each PR is independently mergeable |
| R8 | Operator misses the manual smoke sessions for PR 4 | Low | High | Pre-flight checklist in PR 4 description includes "operator has run /check on 4 sessions" as a merge gate |
| R9 | Existing 121 tests break because `DETECTOR_NAMES` order matters | Low | High | PR 1 updates `test_exactly_10_detectors` → `test_exactly_12_detectors` and any test that asserts on `DETECTOR_NAMES` order. The detectors module is the only place order is defined |
| R10 | (Superseded by F-01 fix in §5.3.1.) The original design's `event_indices=()` proposal collided with two contract layers (`Signal` docstring + `output_validator.py:227-231`). The resolution is to anchor the receipt signal to the terminal transcript event (`event_indices=(N-1,)`), which is a real event index that satisfies both contract layers without modification. No `output_validator.py` change is required. **PR 2 adds `test_receipt_signal_cites_real_event_index`** as the structural enforcement that the anchor is real, not aspirational. |

### 10.1 Risk mitigation that lives outside this design

- **R11: The cross-model specialist (minimax-m3) hits a quota limit and the verifier hangs.** Mitigated by `~/.grok/tool-fallbacks.md` documenting the fallback to CLI `/agy -p ...`. The orchestrator's Step 3 already has a 10-minute wait window per verifier (existing behavior); if exceeded, the verifier is reported as a timeout and treated as FAIL with `severity: gap`. **Operator action: monitor quota dashboards for minimax-m3 during the 7-day shadow phase.**
- **R12: A new detector emits too many signals and inflates the evidence packet.** Mitigated by the existing `Signal.event_indices` policy: signals must cite at least one real event index. For `receipt_evaluation` (session-bound), the terminal-event anchor (`N-1`) is the structural enforcement — it is a real index, not a fabrication. **Operator action: monitor packet sizes during the shadow phase.**

---

## Appendix A: File-by-File Change Inventory

| File | PR | Action | LOC delta |
|---|---|---|---|
| `P:/.grok/skills/check/__lib/detectors.py` | 1 | Append 3 detector functions (`detect_post_verification_mutation`, `detect_scope_claim_mismatch`, `detect_receipt_evaluation` stub per N-1) + 3 entries in `DETECTOR_NAMES` | +90 / +3 |
| `P:/.grok/skills/check/__lib/event_model.py` | 1 | Bump `PACKET_SCHEMA_VERSION` | +1 / -1 |
| `P:/.grok/skills/check/__lib/output_validator.py` | 1 | Add `"1.1"` to `_KNOWN_SCHEMA_VERSIONS`. **No empty-event_indices allowlist** (N-3 fix: F-01 removed the empty-tuple proposal; the validator's empty-event_indices check at `output_validator.py:227-231` stays intact, and the receipt signal uses a real terminal-event anchor instead) | +1 / 0 |
| `P:/.grok/skills/check/__lib/evidence_packet.py` | 1 | Add `# NB: iterates DETECTOR_NAMES; bump when adding a detector` comment at the `to_dict` method's `for kind in DETECTOR_NAMES` loop (F-06 fix) | +2 / 0 |
| `P:/.grok/skills/check/tests/test_detectors.py` | 1 | Add 9 tests (8 for transcript-derived detectors + 1 for `detect_receipt_evaluation` stub per N-1); update count assertion from 10 to 13 | +100 / -2 |
| `P:/.grok/skills/check/tests/fixture_sample.jsonl` | 1 | Extend fixture | +5 / 0 |
| `P:/.grok/skills/check/__lib/load_receipt_summary.py` | 2 | New file; exports `load_receipt_summary(session_id, packet, transcript)` (N-4: `transcript` is required, not optional, so the loader can derive the terminal-event anchor for the synthesized signal per F-01) | +85 |
| `P:/.grok/skills/check/__lib/preprocessor.py` | 2 | Call loader; merge bucket | +20 / 0 |
| `P:/.grok/skills/check/tests/test_load_receipt_summary.py` | 2 | New file (7 tests per N-4: 6 fail-open + 1 TypeError on `transcript=None`) | +130 |
| `P:/.grok/skills/check/__lib/routing.py` | 3 | New file | +90 |
| `P:/.grok/skills/check/__lib/prompts/__init__.py` | 3 | New file (empty) | +0 |
| `P:/.grok/skills/check/__lib/prompts/post_verification_mutation.md` | 3 | New file | +30 |
| `P:/.grok/skills/check/__lib/prompts/scope_claim_mismatch.md` | 3 | New file | +30 |
| `P:/.grok/skills/check/__lib/prompts/receipt_evaluation.md` | 3 | New file | +40 |
| `P:/.grok/skills/check/__lib/prompts/claim_audit.md` | 3 | New file | +30 |
| `P:/.grok/skills/check/tests/test_routing.py` | 3 | New file | +130 |
| `P:/.grok/skills/check/SKILL.md` | 4 | Insert Steps 0.6, 0.7; extend Steps 2, 3, 4 | +90 / 0 |
| `P:/.grok/skills/check/__lib/packet_for_specialization.py` | 4 | New file | +60 |
| `P:/.grok/skills/check/tests/test_packet_for_specialization.py` | 4 | New file (extended to 6 tests in revision per F-01 + F-09) | +80 → +130 |

**Total new files:** 12 (1 Python loader, 1 Python router, 1 Python packet assembler, 4 prompt overlays, 1 prompt `__init__`, 4 test files, 1 fixtures extension). **Total modified files:** 6. **Total LOC delta:** +1,310 / -7 (revised from +1,260 to reflect: (a) N-4 fix adds the TypeError contract to `load_receipt_summary.py` — +5 LOC; (b) N-4 fix adds the 7th test (`transcript=None` raises TypeError) — +20 LOC; (c) the prior +1,260 already accounted for N-1 stub detector + 1 test (+20 LOC), F-06 docstring-to-real-comment substitution (+2 LOC), and the F-01/F-09 expansion of `test_packet_for_specialization.py` from 4 to 6 tests, plus the §5.3.1 and §5.6.1 contract specifications).

---

## Appendix B: Verifier Output Contract (unchanged)

The structured contract that all verifiers (per-concern, specialized, cross-model) must satisfy:

```json
{
  "verdict": "PASS" | "FAIL",
  "checklist": ["item 1", "item 2", ...],
  "action_trace": [...],
  "evaluation": {
    "correctness": "...",
    "adequacy": "...",
    "excess": "...",
    "edge_cases": "..."
  },
  "issues": [
    {
      "severity": "bug" | "gap" | "regression" | "suggestion",
      "description": "...",
      "evidence": "...",
      "suggestion": "..."
    }
  ]
}
```

Enforced by `output_validator.validate_verifier_output` (`P:/.grok/skills/check/__lib/output_validator.py:269-335`). The contract is **unchanged** by this design.

---

## Appendix C: Glossary

- **Specialization** — a verifier sub-agent with a narrow focus area, dispatched only when its signal fires.
- **Cross-model specialist** — a specialization that runs on a different model family from the parent orchestrator, for blind-spot decorrelation.
- **Receipt** — `VERIFICATION_SUCCEEDED` artifact emitted by `verification_receipt_writer.py` when a verification command exits 0 with non-empty scope.
- **Shadow mode** — operation where a new gate's decisions are logged but not enforced. The receipt system is in shadow mode since 2026-07-22.
- **Dispatch table** — the fixed mapping from `signal_kind` to `specialization_id`. Lives at `routing.py:DISPATCH_TABLE`.
- **Routing decision** — the list of `(specialization_id, model, prompt_overlay_path)` tuples produced by `compute_routing_decision(packet)`.
- **Signal** — an objective, citable observation produced by a detector (`detectors.py:Signal`). Carries `event_indices`, `summary`, `detail`, `confidence`.

---

## Appendix D: References

- Research: `P:/.data/wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md`
- Existing /check: `P:/.grok/skills/check/SKILL.md`
- Existing detectors: `P:/.grok/skills/check/__lib/detectors.py`
- Existing evidence packet: `P:/.grok/skills/check/__lib/evidence_packet.py`
- Existing preprocessor: `P:/.grok/skills/check/__lib/preprocessor.py`
- Existing validator: `P:/.grok/skills/check/__lib/output_validator.py`
- Receipt writer: `~/.grok/hooks/scripts/verification_receipt_writer.py`
- Receipt Stop gate: `~/.grok/hooks/scripts/quality_gate.py`
- Receipt shadow summary: `~/.grok/hooks/scripts/receipt_shadow_evaluation.py`
- Worktree identity: `~/.grok/hooks/scripts/worktree_identity.py`
- /check vs /review: `P:/.data/wiki/concepts/check-vs-review-complementary-not-redundant.md`
- Final-verification no-change rule: `~/.grok/AGENTS.md` § "File editing protocol" → "Verification" line 298
- Completion-language discipline: `~/.grok/AGENTS.md` § "Hard rules" → "Completion-language discipline"
- Model selection policy: `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` (minimax-m3 spawn_subagent compat and 4056ms latency verified 2026-07-24)
- Tool fallbacks: `~/.grok/tool-fallbacks.md` (does NOT list minimax-m3 — that file documents broken combinations; minimax-m3 is working, so its absence is correct)

---

*Document version: 1.0. End of design.*