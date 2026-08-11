# Design: Optimal Waiver Mechanism for the Stop-Hook Review Quality Gate

**Design run:** 62d39214
**Date:** 2026-08-11
**Complexity tier:** 2 (standard; touches existing infrastructure, no greenfield)
**Pipeline mode:** full (premise verification + critical-friend implied; no separate orchestrator run for this artifact)
**Status:** draft for review

---

## Design Intent Contract

**Goal:** Replace the time-bound (30-min) review-gate waiver with a scope-bound, audited waiver that (a) preserves the anti-loop property the existing fix delivers, (b) eliminates the gaming vector implicit in time-bound re-write, and (c) keeps ship-time `/review` obligations load-bearing by **downgrading the gate's output severity via `hookSpecificOutput.additionalContext`** (the only non-blocking feedback mechanism supported by the Grok Build Stop hook — receipt: `~/.grok/docs/user-guide/10-hooks.md:254-262`) — not by suppressing the gate itself.

**Non-goals:**
- Re-architecting the declarative quality-gate system in `quality_gates_frontmatter.py` (out of scope; this design touches `gate_diagnostics.py:_quality_gate_check` and `waiver_gate.py`, not the gate declaration surface).
- Adding new gate declarations to skills (out of scope; this only changes how the existing `review` gate's block condition is satisfied).
- Changing the obligation lifecycle (`obligation_manager.py`) — obligations are independent of waivers; the new mechanism must compose, not replace them.
- Implementing a real-time operator-approval channel (e.g., Slack/Teams approval webhook). Out of scope for this design; addressed in Open Question OQ-04.
- Adding metrics/dashboards for bypass rate. A bypass-budget log is in scope; visualization is a follow-on.

**Success metrics:**
- Zero infinite-loop re-fires across 100 consecutive completion claims within a single milestone scope (measured by absence of redundant `decision: block` JSONL entries).
- Zero ship-time claims that bypass review without an audit row (`grep` of `review-waiver-*.json` shows `1` row per ship claim when bypass used).
- Per-waiver audit row contains `milestone_id`, `next_review_at`, `scope_files`, `scope_skills`, `authorized_by`, `consumed_count` (5 fields present in 100% of waivers produced post-deploy).
- Mean operator-time-to-decide on a waiver request: ≤10 seconds (operator-judgment threshold; no empirical data yet; will be measured post-deploy — F-27).

**Failure conditions (any one triggers rollback):**
- A waiver with no `next_review_at` field is accepted (would re-introduce the session-wide suppression failure mode).
- A waiver suppresses more than one gate class without re-issue (re-introduces session-wide bypass).
- A waiver is reusable after the milestone scope completes — detected by either (a) a new waiver being written with a different `milestone_id` (the new write implicitly invalidates the old), OR (b) the operator's bypass-budget review finding a stale waiver on disk. There is no automated "milestone complete" signal; the mechanism's safety relies on the agent declaring a new scope (F-35).
- The gate fails to fire on an out-of-scope modification (silent bypass on work the waiver didn't cover).
- A waiver is self-authorized when `GROK_SELF_AUTH_ALLOWED=0` (F-03 resolution).

**Success looks like:** A mid-build agent claims "VS-02 of 5 done" without a `/review` run. The Stop hook reads the waiver, surfaces non-blocking feedback via `hookSpecificOutput.additionalContext`, and exits 0 (allowing the turn). The audit log records one row per gate fire with `consumed_count` incrementing. At VS-05 (ship), the waiver is no longer valid (milestone scope changed or `next_review_at` elapsed), and the gate fires as `block` again — the operator sees the actual `/review` obligation.

**Failure looks like:** An agent claims "all done" at session end after a sequence of milestones, and the gate does not fire because an old waiver's `next_review_at` field is set far enough in the future that it covers ship-time. OR: an agent re-writes the same waiver N times within one milestone and the gate fires N times instead of surfacing non-blocking feedback on each fire. OR: an operator cannot tell from the audit log whether a given bypass was for a mid-build milestone or a ship-time cover-up.

---

## Premise Verification

Each premise is labeled by evidence status. The writer must respect these labels throughout the design.

### [FACT] premises (used as given; receipts cited)

**P1.** *Anti-loop fix needed because `invoked_skills` is reconstructed from the full transcript each turn — hooks-mutation detection always re-adds "review", causing the gate to fire every turn indefinitely.*
Receipt: `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py:562-568` (explicit code comment, "Anti-loop fix (2026-08-10): if a waiver file exists for this session, don't re-block on the review gate"). The mechanism in the comment block matches the failure mode described.

**P2.** *Review gate fires on the conjunction: completion claim + `review` in `invoked_skills` + no `/review` receipt.*
Receipt: `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py:549-557` (the `_quality_gate_check` docstring enumerates the three conditions explicitly).

**P3.** *Obligation system creates continuation obligations satisfied by receipts.*
Receipt: `~/.grok/hooks/scripts/quality_gate/main.py:505-590` (the obligation read at line 510 → satisfied check at line 536 → receipt-fingerprint match at line 580 → `_clear_obligation` at line 575; the quality-gate check is called at line 581-589 inside the "obligation satisfied, no new mutations" branch).

**P7.** *Agent CAN derive correct waiver dispositions.*
Receipt: session 019fee63, VS-02 milestone — agent derived "waive for now, review at VS-05" disposition correctly from context. (Cited in design brief; not re-verifiable in this design session, accepted as given.)

### [RESEARCH] premises (supporting evidence; externally sourced)

**P5.** *Single-use override tokens are the canonical pattern; time-bound session overrides are explicitly ruled out.*
Source: `digitalgarden.bhekani.com/single-use-override-tokens/` (cited in design brief). Key principle: "Override tokens that work across operations or expire by time rather than by single use" and "Session overrides that turn off a class of checks for some window" are explicitly named as anti-patterns by the source.

**P6.** *Break-glass workflow converts policy result from `block` to `warn` (not `allow`); self-approval is a category error; bypass budgets flag teams exceeding a configurable count.*
Source: `safeguard.sh/resources/blog/break-glass-workflow-design-audited-bypass` (cited in design brief). Six properties named: Scoped, Justified, Approved, Time-bound, Recorded, Rare. Quoted invariant: "The bypass converts the policy result for the named scope from `block` to `warn` for the duration. It does NOT convert to `allow`."

### [INFERENCE] premises (must appear in Open Questions; design degrades gracefully if wrong)

**P4.** *The 30-min time-bound waiver is gaming-susceptible.*
What changes if wrong: implementation cost (~280 LOC, 7 files, ~5 days) is incurred for a theoretical-only fix; the operator may prefer to defer to a future version where empirical gaming is documented (F-23). The design still applies (conformance to literature), but the urgency is lower. Mitigation: the design documents the gaming vector explicitly so operators can audit retrospectively (`grep` the audit log for `next_review_at - waiver_at > 25 min` as a heuristic).

**P8.** *Block→warn mode resolves the anti-loop/single-use tension.*
What changes if wrong (F-01): VERIFIED FALSE. The Grok Build Stop hook does NOT support a `decision: warn` value (receipt: `~/.grok/docs/user-guide/10-hooks.md:254-262`). The design now uses `hookSpecificOutput.additionalContext` (the only non-blocking feedback mechanism supported by the Stop hook). The intent of P8 (gate fires every turn, output downgrades on match) is preserved with the correct output format.

### [UNKNOWN] premises (must appear in Open Questions; design degrades gracefully)

**P9.** *Whether the operator is always-available to authorize waivers.*
Resolution path: measure operator-availability telemetry (handoff response time, `/handoff list --stale`); if median is <30s, synchronous authorization is feasible; if >5min, the agent-self-authorization path is the only practical default.

**P10.** *Whether mid-build milestones can always name a concrete ship-time review point.*
Resolution path: instrument the waiver log for `next_review_at` field; if >20% of waivers have `next_review_at: null` or "TBD" post-deploy, the milestone-scoping discipline is failing and a stricter frontmatter validation is needed.

**P11 (F-16, promoted from UNKNOWN):** *Whether synchronous operator approval is impractical on this host.* Supporting evidence: the operator's documented session profile (high context-load, asynchronous work style per the workspace operator profile); observed session patterns in `~/.grok/state/observation-text-log/*.jsonl` show operator responses ranging from minutes to hours; no synchronous-approval channel exists in the current codebase. Conclusion: synchronous approval is INFERRED to be impractical; DEC-08's rationale cites this inference (F-16).

---

## Problem Framing & Core Tension

### What the existing system does

The Stop hook (`~/.grok/hooks/scripts/quality_gate/main.py`) calls `_quality_gate_check()` at the end of every completion-claim turn. When:
- the agent makes a completion claim (`claim=True`),
- the `review` skill is in `invoked_skills` (added by hooks-mutation detection in earlier turns),
- and no `/review` evidence exists,

the gate returns `(True, message)` and the hook emits `decision: block`.

The current waiver (`gate_diagnostics.py:562-601`) is a **time-bound session-scoped override**:
- Waivers are written to `~/.grok/hooks/state/review-waiver-{session_id}.json`.
- The freshness window is 30 minutes.
- Within the window, the gate short-circuits to `return False, ""` (no block).
- After the window, the gate re-arms.

The 30-min window solves the **anti-loop** failure mode (P1): without it, the gate would re-block on every turn because `invoked_skills` is reconstructed. With it, the agent has 30 minutes of breathing room to make progress.

### What is wrong with the current mechanism

Three issues, each grounded in the literature (P5, P6):

1. **Gaming vector (P4):** The 30-min window allows re-write every 29 min. The agent can keep itself unblocked indefinitely by re-emitting `waiver_gate.py --gate review --reason "..."` on a cron-like schedule. No audit row binds to a specific work unit; the audit log just shows "waiver N re-written".

2. **Wrong override class (P5):** The bhekani pattern explicitly rules out the time-bound session override: *"Override tokens that work across operations or expire by time rather than by single use"* and *"Session overrides that turn off a class of checks for some window"* are anti-patterns. The current mechanism is exactly this anti-pattern.

3. **Wrong output mode (P6):** The break-glass pattern says the bypass should convert `block → warn`, not `block → allow`. The current mechanism does `block → allow` (silently returns `False`), losing the detection signal that would tell the operator "this gate fired and was waived for scope X".

### The core tension

The anti-loop fix (P1) requires that the gate NOT re-block on consecutive turns within the same work unit. Single-use tokens (P5) require a new decision each gate fire. These conflict.

**Resolution (P8):** The gate fires every turn (preserving detection and the anti-loop property) but its output is **downgraded** from `block` to `warn` when a valid waiver context exists for the current fire. The waiver is not a suppression; it is a **mode change** scoped to (a) specific files, (b) specific skills, (c) a bounded window tied to a named milestone with a concrete `next_review_at`. After the milestone scope ends or `next_review_at` elapses, the gate returns to `block` mode automatically.

### Self-authorization: when is it acceptable?

P6 states "self-approval is a category error". The whole point of break-glass is that a second pair of eyes is involved before policy is suspended. But in an LLM-agent system where the operator is not always available (P9), some self-authorization is necessary.

**Resolution (F-03):** the design adopts the break-glass bypass-budget pattern (P6) AND adds a runtime control that surfaces self-authorization as a degraded mode the operator can disable:

1. **Audit-log all self-authorizations** with `authorized_by: "agent"`. Operator-authorized waivers set `authorized_by: "operator"`.
2. **Runtime control via env var** `GROK_SELF_AUTH_ALLOWED` (default: `1`):
   - `1` (default): self-authorization permitted; every self-authorization is logged with `authorized_by: "agent"` for retrospective bypass-budget review.
   - `0`: the `waiver_gate.py` script refuses to write a waiver with `--authorized-by agent` (exit code 2 with a clear error message). The operator must explicitly set `--authorized-by operator` AND set the env var to indicate their presence. This is the operator's escape hatch for "I am here, I want to approve in real time."
3. **Bypass-budget utility** (Unit 6) flags sessions exceeding the configurable self-authorization threshold for retrospective review.

The design does NOT add a synchronous operator-approval channel — that is OQ-04 in Open Questions. The current architecture accepts that self-authorization is the practical default; the audit log makes retrospective review possible; and the `GROK_SELF_AUTH_ALLOWED=0` mode gives the operator a way to enforce synchronous presence when desired.

---

## Alternatives

### Option 0: Do Nothing (current shipped state)

**Description:** Keep the 30-min time-bound waiver as-is. The mechanism is shipped, tested, and the regression suite covers it.

**Cost (carrying forward):**
- Gaming vector remains (P4): an agent can re-write waivers indefinitely.
- The mechanism violates two named anti-patterns from the literature (P5).
- Audit log shows waiver-rewrites, not waiver-consumptions — retrospective review is harder than necessary.

**Why any change is justified:** The literature is explicit (P5, P6) and the design brief confirms field research identified the mechanism as suboptimal. The gaming vector is theoretically exploitable today even if no exploitation is documented. The 30-min window was an interim patch (the freshness fix comment at line 568-578 says "prevents a single early waiver from silencing the review gate for the entire session — a second-order effect"); the field research this session found the interim patch itself suboptimal.

### Option 1: Scope-bound waiver with block→warn downgrade (RECOMMENDED)

**Description:** Replace the 30-min freshness window with a scope-bound waiver that (a) names the milestone work-unit, (b) lists the scope files, (c) names a concrete `next_review_at`, (d) records `authorized_by`, and (e) on each gate fire, downgrades `block → warn` while incrementing a `consumed_count` audit field. The gate still detects; the operator sees the warn; the agent can proceed.

**Selection criterion:** conformance to bhekani (P5) + break-glass (P6) anti-pattern rules + preservation of the anti-loop property (P1) + reversibility (config + state file; no schema migration).

**Trade-offs accepted:**
- The Stop hook protocol must support a "warn" decision (currently only "allow" and "block" are emitted). This is a small contract change, scoped to one hook.
- Self-authorization is permitted with audit; the operator-approval channel is a follow-on (OQ-04).
- Operators must understand the new `next_review_at` field; the block message and AGENTS.md trigger case document this.

**Why this option wins:** the four literature-grounded properties (Scoped, Justified, Approved-via-audit, Time-bound-to-scope, Recorded, Rare) are all satisfied; the anti-loop property is preserved (gate fires every turn, output downgrades); the gaming vector is closed (the audit row binds to a specific scope; re-writing the waiver for a new scope is required to extend the bypass, and that re-write is itself audited).

### Option 2: Single-use consumed tokens (rejected — incompatible with P1)

**Description:** Each gate fire consumes a token; the agent must request a new token each turn to continue.

**Why rejected:** Single-use tokens are exactly what P5 endorses — but they are incompatible with P1's anti-loop requirement. Each turn would require a new token mint, which is operationally equivalent to the gate re-blocking. The agent would have to invoke `waiver_gate.py` every turn, which is more friction than the current 30-min re-write — but the same gaming vector applies (script on a loop). The single-use pattern works when the safety check fires once per operation; the Stop hook fires once per turn (potentially many turns per operation), so the pattern does not map cleanly.

### Option 3: Operator-gated approval channel (deferred — OQ-04)

**Description:** The waiver request pings the operator synchronously (e.g., desktop notification, Slack message); operator approves before the waiver is written.

**Why not chosen as primary:** Requires synchronous operator availability (P9). The break-glass pattern says operator approval is the canonical authorization — but the canonical pattern assumes the operator is in the loop at the time of the bypass request. For an autonomous mid-build milestone, the agent may not have synchronous operator access. The audit-log + bypass-budget approach (Option 1) is the asynchronous analogue: the operator reviews post-hoc rather than approving in-the-loop.

**Why kept as Open Question:** a real operator-approval channel (Slack webhook, terminal bell, etc.) would strengthen the design by adding the synchronous path for high-stakes milestones. See OQ-04.

### Hidden anchor (what all alternatives assume)

All alternatives assume the **gate's detection value is preserved** — that is, the operator still sees that the gate fired and was bypassed. If the alternative is "silence the gate entirely", the detection value is lost and the mechanism becomes decorative (P5: "if overriding is too easy, the safety check becomes decorative"). Option 1 preserves detection by downgrading to `warn` (the gate still fires and the audit log records the fire); Options 2 and 3 also preserve detection; only Option 0 (current) loses detection because the gate silently short-circuits.

---

## Recommended Approach

### Mechanism: scoped waiver with non-blocking feedback downgrade

The waiver file schema changes from time-bound-freshness to scope-bound-validity. **Canonical waiver path is `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json`** (the path used by `quality_gates_frontmatter.write_waiver()` line 596). The legacy path `review-waiver-{session_id}*.json` (used by the current `waiver_gate.py` and read by the `gate_diagnostics.py` anti-loop glob at line 582) is **deprecated and merged into the canonical path** (F-08):

```json
{
  "session_id": "019fee63-...",
  "gate": "review",
  "milestone_id": "VS-02-of-5",
  "scope_files": [
    "P:/.grok/hooks/scripts/quality_gate/gate_diagnostics.py"
  ],
  "scope_skills": ["review"],
  "reason": "VS-02 milestone complete; VS-05 scheduled for ship-time review",
  "next_review_at": "2026-08-12T18:00:00Z",
  "authorized_by": "agent",
  "created_at": "2026-08-11T22:15:00Z",
  "consumed_count": 0,
  "consumption_audit": []
}
```

New fields and their roles:

- `milestone_id` (REQUIRED): names the work unit. The waiver is bound to this milestone; when the scope changes (different milestone_id claimed), the old waiver is invalidated and a new one must be written.
- `scope_files` (REQUIRED): list of files the waiver covers. The gate only downgrades for modifications within this set; modifications outside the set re-arm the gate to `block`.
- `scope_skills` (REQUIRED): list of skills the waiver covers. Currently always `["review"]`; the field exists so the mechanism generalizes to other gates without schema change.
- `next_review_at` (REQUIRED, ISO-8601 UTC): the concrete time at which the waiver expires and the gate re-arms. Must be set; null is rejected at write time.
- `authorized_by` (REQUIRED): `"operator"` or `"agent"`. Self-authorized waivers are flagged for the bypass budget.
- `created_at` (REQUIRED, ISO-8601 UTC): timestamp of waiver creation.
- `consumed_count` (REQUIRED): incremented on each gate fire that downgrades; reset to 0 if a new waiver supersedes.
- `consumption_audit` (REQUIRED): append-only list of `{timestamp, modified_files_at_fire, decision, scope_match}` rows. Each gate fire appends one row regardless of outcome (F-18): `decision` is `"warn"` for matched scope, `"block_skipped"` for mismatched scope (a waiver existed but did not match), or `"allow"` for non-blocked fires. This is the bhekani single-use audit trail applied to consumption events. The `scope_match` boolean enables retrospective analysis of "how many close calls?" (waiver existed but didn't match → would have blocked) and "how many bypasses?" (waiver matched → downgraded).

### Gate behavior change

`_quality_gate_check()` in `gate_diagnostics.py` is rewritten to:

1. Read all `quality-gate-waiver-{session_id}.json` files (the canonical path — F-08). Glob is tightened from the legacy `*-{sid}*.json` pattern to the exact `quality-gate-waiver-{session_id}.json` filename (F-28).
2. For each waiver: validate that `next_review_at` has not elapsed; if it has, treat the waiver as expired (delete or ignore — see DEC-03).
3. Match the current gate fire to a waiver:
   - `gate` field matches (currently always `"review"`).
   - `scope_skills` contains the gate's skill (currently always `["review"]`).
   - The current modified files (passed via the `modified_files` parameter, sourced from `hunk_records.jsonl` via `_read_session_files()` in `quality_gates_frontmatter.py:670-690` — NOT from `invoked_skills`, which is a set of skill-name strings, not file paths — F-10) are a subset of `scope_files`. Path normalization: replace `\` with `/`, lowercase, strip trailing slashes before comparison.
4. **If matched:** increment `consumed_count`, append to `consumption_audit`, write the waiver back atomically (F-02). Return `(False, "warn")` — gate fires, output is non-blocking feedback via `hookSpecificOutput.additionalContext`, agent can proceed.
5. **If not matched:** fall through to the existing `check_quality_gates()` call. If a receipt exists, the gate is satisfied and no block. If not, the gate blocks as today.

The warn message has the same shape as the block message but is prefixed with `[WAIVED]` and includes the waiver context:

```
[WAIVED] Quality gate waived for this fire. Consumed count: 3.
  Waiver: VS-02-of-5 (review) — reason: VS-02 milestone complete; VS-05 scheduled for ship-time review.
  Scope files: 1 file in waiver; 1 modified this turn (in scope).
  Next review at: 2026-08-12T18:00:00Z (8h 23m remaining).
  Authorized by: agent (self-authorized; logged for retrospective review).
  Consumption audit: 3 entries since 2026-08-11T22:15:00Z.

If you intend to claim SHIP completion, run /review now — the gate will not waive for a new milestone.
```

### Operator-visible change

The Stop hook must distinguish "block" from non-blocking feedback. **Verified against the Grok Build Stop-hook protocol** (receipt: `~/.grok/docs/user-guide/10-hooks.md:254-262`): the only four output forms are `{"decision": "block", "reason": "..."}`, `{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "..."}}`, `{"continue": false, "stopReason": "..."}`, or exit-0-with-no-output. There is **NO `decision: warn` value supported**. The design MUST use `hookSpecificOutput.additionalContext` to surface feedback without blocking (F-01).

Updated contract:

- `{"decision": "block", "reason": "..."}` then `sys.exit(0)` — gate fires and blocks the turn (existing behavior).
- `{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "<warn_message>"}}` then `sys.exit(0)` — gate fires but does NOT block; the additionalContext is fed back to the model as hook feedback and the agent proceeds. Audit log records the fire.
- Exit 0 with no JSON output — allow the stop (existing behavior).

DEC-04 documents this as a Stop-hook contract change. The implementation updates `main.py:583-589` to emit `hookSpecificOutput.additionalContext` instead of silently allowing.

### Self-authorization and bypass budget

When `authorized_by: "agent"`, the row is flagged in `consumption_audit` for retrospective review. A bypass-budget check (separate utility, called by `/maintain` weekly) flags sessions exceeding a configurable threshold (default: 10 self-authorized waivers per session, or 50 per quarter per operator-equivalent). The threshold is not enforced at runtime — it is a post-hoc audit signal.

---

## Detailed Mechanism Design

### File: `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py`

The `_quality_gate_check()` function (lines 548-602) is replaced with:

```python
def _quality_gate_check(
    session_id: str, workspace_root: str, invoked_skills: set,
    claim: bool, modified_files: set | None = None
) -> tuple[bool, str, str]:
    """Check declarative quality gates for invoked skills.

    Returns (block, message, decision) where decision is one of
    {"allow", "warn", "block"}.
    """
```

The new signature adds `modified_files` (set of paths modified in the current turn) and returns a third element `decision`. The third element is the contract change for the Stop hook.

The internal logic is reorganized as:

```python
def _quality_gate_check(session_id, workspace_root, invoked_skills, claim,
                        modified_files=None):
    if not claim or not invoked_skills:
        return False, "", "allow"

    waiver = _read_scoped_waiver(session_id, invoked_skills, modified_files)
    if waiver is not None:
        # Gate fires; downgrade block → warn
        _consume_waiver(waiver, modified_files)
        return False, _build_warn_message(waiver), "warn"

    # No matching waiver — fall through to existing check
    try:
        report = _qg.check_quality_gates(invoked_skills, session_id, workspace_root)
    except Exception:
        return False, "", "allow"

    if not report.blocked:
        return False, "", "allow"

    return True, _qg.build_block_message(report), "block"
```

Three helper functions are added:

1. `_read_scoped_waiver(session_id, invoked_skills, modified_files) -> dict | None`
   - Reads all waiver files for the session.
   - Filters out expired waivers (`next_review_at` elapsed).
   - Returns the first waiver that matches: `gate` in invoked_skills AND modified_files ⊆ scope_files.
   - Returns None if no waiver matches.

2. `_consume_waiver(waiver, modified_files) -> None`
   - Increments `consumed_count`.
   - Appends `{timestamp, modified_files, decision: "warn"}` to `consumption_audit`.
   - Writes the waiver back atomically (tmp + os.replace).

3. `_build_warn_message(waiver) -> str`
   - Constructs the operator-visible warn message (see recommended approach above).
   - Includes `next_review_at` countdown.

### File: `~/.grok/scripts/waiver_gate.py`

The script is rewritten to write the new schema AND the canonical path (F-08): `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json`. New flags:

- `--milestone-id <id>` (REQUIRED): names the work unit.
- `--scope-files <comma-separated-paths>` (REQUIRED): list of files the waiver covers. Replaces the implicit "session-wide" assumption.
- `--next-review-at <ISO-8601-UTC>` (REQUIRED): explicit expiration time. Replaces the implicit 30-min window. **Parser:** ISO-8601 UTC with optional `Z` suffix; the script strips `Z` and `+00:00` before `datetime.fromisoformat()` (matches the existing `gate_diagnostics.py:588-590` pattern — F-32).
- `--authorized-by <operator|agent>` (default: agent): who authorized the waiver. **Respects `GROK_SELF_AUTH_ALLOWED` env var (F-03):** when `0`, refuses to write a waiver with `--authorized-by agent` (exit code 2 with clear error message).

The `--reason` flag is preserved. The `--valid-for-minutes` flag is removed (no longer applicable; `next_review_at` is the expiration). **Backward compatibility (F-25):** `--valid-for-minutes` is documented in `--help` output as deprecated: "The `--valid-for-minutes` flag has been removed; use `--next-review-at <ISO-8601-UTC>` instead." Passing the flag produces argparse exit code 2 (unrecognized argument).

Example invocation:

```bash
python ~/.grok/scripts/waiver_gate.py \
  --gate review \
  --milestone-id VS-02-of-5 \
  --scope-files "P:/.grok/hooks/scripts/quality_gate/gate_diagnostics.py" \
  --next-review-at "2026-08-12T18:00:00Z" \
  --reason "VS-02 milestone complete; VS-05 scheduled for ship-time review" \
  --authorized-by agent
```

### File: `~/.grok/hooks/scripts/quality_gates_frontmatter.py`

Two changes:

1. `build_block_message()` (lines 898-935): update the "Options" section to reference the new mechanism — the `waiver_gate.py` invocation now requires `--milestone-id`, `--scope-files`, `--next-review-at`. The "30 minutes" line is removed; the "ship-time review" guidance is preserved.

2. **Path reconciliation (F-08, F-30):** the existing `write_waiver()` in `quality_gates_frontmatter.py` at line 617 writes to `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json`. The new `write_scoped_waiver()` helper writes to the **same canonical path** with the new schema. The legacy `review-waiver-{sid}*.json` glob in `gate_diagnostics.py:582` is updated to glob `quality-gate-waiver-{sid}.json`. Both `waiver_gate.py` and the gate check now operate on the single canonical path. `write_waiver()` is preserved (not deleted) because it is still called by `check_quality_gates()` at line 803 for any callers that depend on the `quality-gate-waiver-{session_id}.json` file path — the new `write_scoped_waiver()` is a sibling, not a replacement.

### File: `~/.grok/hooks/scripts/quality_gate/main.py`

Line 583-589 (the existing quality-gate check emission) is updated to:

```python
qg_block, qg_msg, qg_decision = _quality_gate_check(
    session_id, workspace_root, invoked_skills, claim,
    modified_files=modified_files,  # sourced from local modified_files set,
                                    # populated upstream from hunk_records.jsonl
                                    # via _read_session_files() (F-11)
)
if qg_decision == "block":
    print(json.dumps({"decision": "block", "reason": qg_msg}))
    sys.exit(0)  # block the turn; do NOT fall through to clear_waiver
elif qg_decision == "warn":
    # Non-blocking feedback via hookSpecificOutput.additionalContext (F-01).
    # Do NOT clear_waiver — consumption is tracked in consumption_audit,
    # NOT by file deletion. The waiver persists for subsequent fires.
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": qg_msg,
        }
    }))
    sys.exit(0)  # allow the stop; do NOT fall through to clear_waiver
# qg_decision == "allow": fall through to existing _qg.clear_waiver(session_id); sys.exit(0)
_qg.clear_waiver(session_id)
sys.exit(0)
```

The non-blocking feedback is also appended to `~/.grok/hooks/state/quality-gate-warns-{session_id}.jsonl` (append-only, see Component 5 below) for retrospective analysis.

**F-02 fix:** the three branches are mutually exclusive (`block` exits, `warn` exits, `allow` falls through). The `clear_waiver` call is reached ONLY on `allow`. The warn path explicitly preserves the waiver file because consumption is tracked in `consumption_audit` (DEC-02), not by deletion.

### File: `~/.grok/hooks/tests/test_quality_gates_frontmatter.py`

New tests:

- `TestScopedWaiver::test_waiver_with_milestone_id_writes_new_schema`
- `TestScopedWaiver::test_waiver_without_next_review_at_is_rejected`
- `TestScopedWaiver::test_waiver_with_expired_next_review_at_is_ignored`
- `TestScopedWaiver::test_scope_files_must_cover_modified_files_for_match`
- `TestGateCheck::test_matched_waiver_returns_warn_not_block`
- `TestGateCheck::test_out_of_scope_modification_returns_block`
- `TestGateCheck::test_consumed_count_increments_on_each_fire`
- `TestGateCheck::test_consumption_audit_appends_per_fire`
- `TestBuildBlockMessage::test_new_waiver_invocation_in_message`

Existing tests for `TestWaiver`, `TestBuildBlockMessage`, `TestCheckQualityGates` are updated to reflect the new schema.

### File: `~/.grok/AGENTS.md`

The trigger case for the Stop-hook review waiver (the line beginning "Stop-hook quality-gate block when you've derived a waiver disposition") is updated to reference the new schema and the four required flags (`--milestone-id`, `--scope-files`, `--next-review-at`, `--authorized-by`).

---

## Failure Mode & Edge Case Analysis

For each component, enumerate all 8 categories of failure modes per the writer-prompt taxonomy.

### Component 1: `_quality_gate_check()` (the rewritten function)

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | Two concurrent Stop-hook fires on the same session race on `consumption_audit` append | Major | Atomic write via tmp + os.replace; consumption_audit is append-only and ordering is timestamp-based, so concurrent appends are reconciled by timestamp sort | Per-fire log to `quality-gate-warns-{session_id}.jsonl`; reconciliation check in `/maintain` weekly |
| **Edge cases** | Empty `modified_files` set; waiver matches by `scope_files` containing the empty set | Minor | Empty set is a subset of any set, so empty modified_files matches any waiver — this is correct behavior (a turn with no modifications cannot trigger a new gate fire anyway) | Test `test_empty_modified_files_matches_any_scope` |
| **Edge cases** | Unicode in file paths (Windows path quirks); `scope_files` paths may not normalize | Minor | Path normalization: replace `\` with `/`, lowercase, strip trailing slashes before comparison | Test `test_path_normalization_in_scope_match` |
| **Edge cases** | Very large `scope_files` list (1000+ entries) | Minor | No size limit; the gate check is O(n) in `scope_files` length and runs once per turn | Telemetry: per-fire latency logged to `quality-gate-warns-{session_id}.jsonl` |
| **Error paths** | Waiver file is corrupted JSON | Major | `try/except (JSONDecodeError, OSError)` returns None (no waiver match) — gate falls through to existing check | Per-fire log includes "waiver read failed" reason |
| **Error paths** | `next_review_at` is unparseable | Major | Same as above; the waiver is treated as invalid and ignored | Per-fire log includes "waiver timestamp unparseable" |
| **State transitions** | `next_review_at` elapses mid-session | Major | Filter expired waivers before matching; expired waiver files are NOT auto-deleted (operator can review the audit history) | Per-fire log includes "waiver expired" reason |
| **State transitions** | Milestone scope changes (different files modified than the waiver covers) | Critical | The match check fails; gate returns `block` mode. The agent must write a new waiver for the new scope or run `/review` | Block message includes "out of scope" guidance |
| **Resource exhaustion** | Many waiver files accumulate in state dir | Minor | Old waiver files (>30 days) are garbage-collected by `/maintain` weekly | `/maintain` reports count of waiver files |
| **Multi-agent/shared state** | Two terminals sharing a session ID write concurrent waivers | Major | File naming includes session_id only (no terminal_id); best-effort isolation is provided by session-id-keyed filenames. Atomic write (`tmp + os.replace`) handles concurrent writes correctly. The `~/.grok/AGENTS.md` "Multi-terminal isolation" section discusses terminal IDs vs session IDs but does NOT state sessions are 1:1 with terminals — verified by reading the section. Concurrent writes to the same session_id are POSSIBLE on this host | Telemetry: detect concurrent waiver writes by mtime; flag for review |
| **Reversibility** | The new gate behavior is committed and shipped | Medium | Config change (the gate check is in code, not config), but reversible by reverting the commit and re-deploying. Feature flag env var `GROK_REVIEW_GATE_SCOPED_WAIVER` (default: on) gates the new behavior for staged rollout | Env var check at top of `_quality_gate_check` |
| **Adversarial/security** | Agent writes a waiver with `authorized_by: "operator"` to evade the bypass budget | Major | `authorized_by` is set by the agent at write time; the audit log records the value as-claimed. The bypass budget reviewer must cross-check agent claims against operator presence. Mitigation: a separate `operator_confirmed` field would require operator action (out of scope; OQ-04). The mechanism also prevents ACCIDENTAL scope mismatch but does NOT detect INTENTIONAL over-broadening of `scope_files` by a careless/malicious agent — the bypass-budget review (Unit 6) is the secondary defense; OQ-05 (HMAC signing) is the long-term mitigation. | Bypass budget review flags sessions with mixed `authorized_by` claims; manual review |
| **Bypass budget exceeded (F-06)** | `consumed_count` crosses the threshold mid-session (default 10 self-authorized waivers per session) | Minor | **No runtime enforcement** (DEC-07): the gate still issues non-blocking feedback on each fire; the threshold is post-hoc audit only. Unit 4 adds an acceptance test that creates a waiver with `consumed_count=999` and verifies the gate still returns `decision: warn` (no runtime enforcement regression). | `bypass_budget.py` (Unit 6) flags sessions exceeding threshold for retrospective review |

### Component 2: `waiver_gate.py` (the helper script)

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | Two concurrent invocations write the same waiver file | Minor | Last-write-wins; atomic write via tmp + os.replace | mtime on the file |
| **Edge cases** | User forgets a required flag (`--milestone-id`, `--scope-files`, `--next_review_at`) | Major | argparse `required=True` on all four flags; clear error message | argparse exit code 2 |
| **Edge cases** | `--next-review-at` is malformed ISO-8601 | Major | `datetime.fromisoformat()` validation; clear error message | argparse + python exit code 1 |
| **Edge cases** | `--next-review-at` is in the past | Minor | Warning printed but accepted (operator may be back-dating a retroactive waiver); the gate immediately ignores it | Per-fire log |
| **Edge cases** | `--scope-files` contains paths that don't exist | Minor | No filesystem check at write time — the waiver is a claim, not a fact. The gate checks scope match against actual modified files at fire time | Per-fire log |
| **Error paths** | State directory not writable | Major | `OSError` caught; clear error message | argparse + python exit code 1 |
| **Error paths** | `$GROK_SESSION_ID` env var missing | Major | argparse `default=None` + explicit env var check | argparse + python exit code 1 |
| **State transitions** | Waiver is written, then the agent's actual work diverges from the claimed scope | Major | Out-of-scope modifications cause the gate to fire as `block` (not warn); the agent must update the waiver or run `/review` | Block message |
| **Resource exhaustion** | State directory fills up | Minor | N/A — single small JSON file per session; not a resource concern | N/A |
| **Multi-agent/shared state** | Multiple sessions write to the same state dir | N/A | Waiver filenames include session_id; sessions are isolated | N/A |
| **Reversibility** | Script behavior change is committed | Easy | Script is version-controlled; revertible via git | git history |
| **Adversarial/security** | Agent writes `authorized_by: "operator"` without operator confirmation | Major | Same as Component 1 — the field is agent-claimed; bypass budget review catches discrepancies | Bypass budget review |

### Component 3: `main.py` Stop-hook emission change

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | N/A | N/A | The Stop hook fires once per turn; no concurrent invocation per session | N/A |
| **Edge cases** | `_quality_gate_check` returns a decision type the main loop doesn't handle | Critical | Default branch in the if/elif emits `decision: block` as a safety fallback; the unknown decision is logged | Test `test_unknown_decision_defaults_to_block` |
| **Edge cases** | Warn JSON exceeds typical size | Minor | Warn message is ~500 chars; well within JSON limits | N/A |
| **Error paths** | JSON serialization fails | Critical | `json.dumps` exception → default to `decision: block` | Hook error telemetry |
| **State transitions** | N/A | N/A | The Stop hook is terminal per-turn; no persistent state | N/A |
| **Resource exhaustion** | N/A | N/A | Single emit per turn | N/A |
| **Multi-agent/shared state** | N/A | N/A | Per-session emission | N/A |
| **Reversibility** | Contract change for `decision: warn` is committed | Medium | Other consumers of the Stop hook (none currently on this host) would need to handle the new decision. Documented in `~/.grok/docs/user-guide/` Stop hook section | Consumer test suite |
| **Adversarial/security** | Agent crafts a waiver to emit `decision: warn` for a ship-time claim | Critical | The waiver match check uses `scope_files` containment — a ship-time claim typically modifies files OUTSIDE the milestone scope, so the waiver does not match and the gate blocks | Block message includes "out of scope" guidance |

### Component 4: Waiver file persistence

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | Concurrent reads/writes on the same waiver file | Minor | Atomic write (tmp + os.replace); reads are best-effort | mtime tracking |
| **Edge cases** | File is empty | Major | JSONDecodeError → waiver ignored | Per-fire log |
| **Edge cases** | File is huge (megabytes) | Minor | Not expected; bounded by field sizes | File size check in `/maintain` |
| **Error paths** | Disk full during write | Major | OSError caught; gate falls back to existing check (no waiver match) | Per-fire log |
| **Error paths** | Permission denied | Major | OSError caught; gate falls back to existing check | Per-fire log |
| **State transitions** | Waiver expires mid-session | Handled in Component 1 | N/A | N/A |
| **Resource exhaustion** | Many waiver files in state dir | Minor | `/maintain` weekly cleanup of files >30 days | `/maintain` report |
| **Multi-agent/shared state** | Different sessions write to same dir | N/A | Filename includes session_id | N/A |
| **Reversibility** | Schema change is committed | Medium | Old waiver files (with old schema) are detected by missing required fields and ignored | Per-fire log |
| **Adversarial/security** | Tampering with waiver files | Critical | The waiver file is in the user's home dir (`~/.grok/hooks/state/`); on this host, agents have write access. Mitigation: future enhancement could add an HMAC signature field, but that requires a shared secret (out of scope; OQ-05) | Per-fire log includes waiver SHA for cross-check |

### Component 5: `quality-gate-warns-{session_id}.jsonl` (sidecar log)

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | Multiple Stop fires writing to the same file in the same turn | Minor | File handle opened in append mode per write; lines are atomic at the OS level for small writes (<`PIPE_BUF`). Risk of interleaving is negligible for typical warn messages (~500 chars). | Per-line timestamp; mtime tracking |
| **Edge cases** | File grows unbounded over a long session | Minor | **Rotation strategy (F-33):** `/maintain` weekly cleanup of sidecar files >30 days, matching the waiver-file rotation policy. Hard cap: 10 MB per file (truncate-and-rotate when exceeded, preserve last 1000 lines). | File size check in `/maintain` |
| **Edge cases** | File is truncated (operator or process action) | Major | Append-only contract is best-effort; if truncated, the audit trail loses entries but the waiver mechanism still works. Document in AGENTS.md: "The sidecar is advisory; the source of truth is the waiver file's `consumption_audit` array." | Per-fire log size |
| **Error paths** | Disk full during write | Major | OSError caught; the warn is lost but the gate still emits the non-blocking feedback (the warn is the primary signal; the sidecar is secondary). | Telemetry: write failures logged to hook error JSONL |
| **Error paths** | Permission denied | Major | Same as above; warn is delivered via stdout JSON; sidecar is lost | Telemetry |
| **State transitions** | N/A | N/A | Append-only file; no state transitions | N/A |
| **Resource exhaustion** | Many warn files accumulate | Minor | Same rotation as waiver files | `/maintain` |
| **Multi-agent/shared state** | Different sessions write to same dir | N/A | Filename includes session_id | N/A |
| **Reversibility** | File format change | Easy | Format is one-line JSON; new fields are additive | Schema documentation |
| **Adversarial/security** | Agent manipulates sidecar to hide bypasses | Minor | The sidecar is advisory; the source of truth is the waiver file's `consumption_audit`. The `bypass_budget.py` audit reads both; manipulation of the sidecar alone does not affect the audit. | `bypass_budget.py` cross-checks sidecar against `consumption_audit` |

### Component 6: `bypass_budget.py` (Unit 6 utility)

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | Runs while waiver files are being written | Minor | Read-only scan; races are benign (may report a slightly stale count, never a wrong decision). mtime check skips files modified in the last 1 second. | Tool reports "stale file skipped" |
| **Edge cases** | Waiver file has missing fields (partial schema migration) | Major | Schema validator in the tool: report missing fields as "incomplete waiver" and skip from count. Tool emits a separate "incomplete waiver" report for operator review. | Tool exit code 1 + report |
| **Edge cases** | Mixed session-id formats (old vs. new) | Minor | Tool normalizes session_ids to UUID v4 format (the canonical format); reports any non-conforming IDs. | Tool report |
| **Error paths** | State directory not readable | Major | OSError caught; tool exits 2 with clear error message | Exit code 2 |
| **Error paths** | Malformed JSON in a waiver file | Major | JSONDecodeError caught per-file; that file is skipped with a warning | Tool report |
| **State transitions** | Waiver expires between scan and report | Minor | Scan uses `next_review_at` field; expired waivers are reported as "expired" but still counted if `consumed_count > 0` | Tool report |
| **Resource exhaustion** | Many waiver files to scan | Minor | Linear scan; 1000 files in <1 second. No size cap. | Runtime telemetry |
| **Multi-agent/shared state** | Multiple `/maintain` runs concurrently | Minor | Each run is independent; output is idempotent (overwrites report file) | Last-write-wins on report |
| **Reversibility** | Tool is standalone; no shared state | Easy | New executable; can be deleted if not needed | N/A |
| **Adversarial/security** | Agent pre-cleans sidecar to hide bypasses from the budget scan | Minor | The tool scans waiver files (source of truth), not the sidecar. Sidecar manipulation does not affect the budget count. | Tool reads waiver files |

### Component 7: `consumption_audit` array (waiver-file sub-schema)

| Failure Mode | Cause | Severity | Mitigation | Detection |
|---|---|---|---|---|
| **Concurrency & races** | Two gate fires append to the same array concurrently | Major | Atomic write of the entire waiver file (`tmp + os.replace`). Concurrent appends are reconciled by timestamp sort on next read. | mtime tracking; per-fire log |
| **Edge cases** | Array grows unbounded over a long session | Minor | Hard cap: 1000 entries (oldest entries are pruned on append when cap is exceeded). Documented in AGENTS.md. | Per-fire log |
| **Edge cases** | Array contains malformed entries | Minor | Each entry is `{timestamp, modified_files, decision}`; schema validation in `_consume_waiver()` rejects malformed entries and logs to sidecar. | Per-fire log |
| **Edge cases** | Array contains duplicates (same fire recorded twice) | Minor | Idempotency: `_consume_waiver()` checks `consumed_count` against `len(consumption_audit)`; mismatch is a corruption signal. | Telemetry |
| **Error paths** | JSON parse error on waiver file | Major | `try/except` returns None; waiver is treated as invalid | Per-fire log |
| **Error paths** | Required fields missing in an audit entry | Minor | Skip that entry; log to sidecar | Sidecar log |
| **State transitions** | Waiver expires mid-session; audit entries remain | Minor | Audit history is preserved (DEC-03); old entries are not deleted when waiver expires. | N/A |
| **Resource exhaustion** | Waiver file size grows large | Minor | Audit array is capped at 1000 entries; waiver file size is bounded | File size check |
| **Multi-agent/shared state** | Same session, multiple terminals | Major | Atomic write handles concurrency; per-fire log includes terminal_id if available | Per-fire log |
| **Reversibility** | Schema change | Medium | New fields are additive; old entries are read with defaults | Schema version field |
| **Adversarial/security** | Agent tampers with audit array to hide bypasses | Major | Tampering invalidates the file (next parse fails). Detection: per-fire log includes a SHA of the audit array; `bypass_budget.py` cross-checks the SHA against the expected value. | Bypass budget review |

---

## Coupling & Code-Smell Inventory

This design touches existing code. Per the writer prompt, the inventory is mandatory.

### Module: `gate_diagnostics.py` (`_quality_gate_check` function)

| Signal | Threshold | Count | Verdict |
|---|---|---|---|
| DRY violations — same data structure or logic enumerated across functions | ≥3 | 2 | Below threshold; no refactor needed |
| Positional parameter count on target function | >7 | 5 (after change: 6 with `modified_files` and 3-tuple return) | Below threshold |
| Touch-point count to add a new field | >3 | **5** (gate_diagnostics.py Unit 1, waiver_gate.py Unit 2, main.py Unit 3, quality_gates_frontmatter.py Unit 4, AGENTS.md Unit 5 + sidecar log format Unit 3) | **Above threshold.** Justification: the Stop hook is critical infrastructure with a documented contract (`~/.grok/docs/user-guide/10-hooks.md`). Touching all 5 sites is required because they are the natural owners of the gate contract — schema, script, emission, message, docs. Refactoring these into a single owner would be larger scope than the design and would not reduce risk. The DEC-05 split into 1a (refactor) + 1b (mechanism) — F-29 — keeps each commit small. |
| Mixed concerns in one function | Any | Before: Yes (time-bound freshness check + gate check + return tuple). After: Yes (waiver matching + gate check + return tuple with new decision). | Mixed concerns remain. The function is ~50 lines; splitting into `_match_scoped_waiver()` + `_run_gate_check()` is recommended (DEC-05) |

**Refactor proposed (DEC-05):** Split `_quality_gate_check` into three functions (now Unit 1a — F-29):
- `_match_scoped_waiver(session_id, invoked_skills, modified_files) -> dict | None` — waiver matching only
- `_consume_waiver(waiver, modified_files) -> None` — atomic update of consumption_audit
- `_quality_gate_check(session_id, workspace_root, invoked_skills, claim, modified_files) -> tuple[bool, str, str]` — orchestration only

This separates the waiver-matching concern from the gate-check concern, satisfies the mixed-concerns threshold, and keeps each function under 30 lines. Unit 1a ships the structure with no behavior change; Unit 1b populates the stubs.

### Module: `waiver_gate.py` (the helper script)

| Signal | Threshold | Count | Verdict |
|---|---|---|---|
| DRY violations | ≥3 | 0 | Below threshold |
| Positional parameter count | >7 | 4 argparse args | Below threshold |
| Touch-point count to add a new field | >3 | 1 (the script itself) | Below threshold |
| Mixed concerns | Any | No (single-purpose script) | Below threshold |

No refactor needed.

### Module: `main.py` (Stop hook emission)

| Signal | Threshold | Count | Verdict |
|---|---|---|---|
| DRY violations | ≥3 | 0 | Below threshold |
| Positional parameter count | >7 | N/A (no new function signature) | N/A |
| Touch-point count to add a new field | >3 | 1 (the existing emission site) | Below threshold |
| Mixed concerns | Any | Before: Yes (obligation lifecycle + gate check + emission). After: Same. | Pre-existing mixed concerns; refactor deferred to `P:/docs/handoffs/main-py-quality-gate-refactor-2026-08-11/HANDOFF.md` (chronicity: chronic; trigger: any future change to `main.py` that touches ≥2 concerns). Per AGENTS.md "Chronic patterns don't get deferred without a handoff" rule (F-20). |

No refactor needed for this design. The mixed-concerns violation in `main.py` is documented in the broader `quality_gate/main.py` refactor handoff.

### Module: `quality_gates_frontmatter.py` (`build_block_message` function)

| Signal | Threshold | Count | Verdict |
|---|---|---|---|
| DRY violations | ≥3 | 0 | Below threshold |
| Positional parameter count | >7 | 1 (the report) | Below threshold |
| Touch-point count to add a new field | >3 | 1 (the function itself) | Below threshold |
| Mixed concerns | Any | No (single-purpose: message construction) | Below threshold |

No refactor needed.

---

## Implementation Plan

### Unit 1a: Refactor `_quality_gate_check` into three functions (DEC-05, no behavior change)

- **Files:** `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py`
- **Dependencies:** none
- **Changes:** Add `_match_scoped_waiver()` and `_consume_waiver()` helpers as stubs (return `None` / `pass`). Split `_quality_gate_check()` into the three functions but keep the legacy time-bound logic. The signature stays `tuple[bool, str]` for now. Behavior is identical to the current implementation.
- **Acceptance criteria:**
  - All existing tests pass with no modification.
  - `ruff check gate_diagnostics.py` clean.
  - Code-reviewable as "same gate, three functions — no behavior change."
- **Feature flags:** none.
- **Disposition:** `COMMIT_THIS_SESSION`
- **Why split (F-29):** the refactor and the behavior change are independently shippable. If the refactor has a regression, the behavior change is not affected. If the behavior change has a defect, the refactor's complexity does not make diagnosis harder.

### Unit 1b: New scope-bound waiver mechanism (DEC-01, behavior change)

- **Files:** `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py`
- **Dependencies:** Unit 1a (the three-function structure)
- **Changes:** Populate the stubs from Unit 1a with the new scoped-waiver logic. Update the signature to `tuple[bool, str, str]` (add `decision` field). Update the legacy time-bound glob to read from the canonical `quality-gate-waiver-{sid}.json` path (F-08). Implement the `next_review_at` expiration check.
- **Acceptance criteria:**
  - All Unit 1a tests still pass.
  - New tests from Unit 4 pass (4 waiver-matching + 2 consumption).
  - `ruff check` clean.
  - Manual test: write a waiver, verify the gate fires as warn (non-blocking feedback) for in-scope modifications and as block for out-of-scope modifications.
- **Feature flags:** `GROK_REVIEW_GATE_SCOPED_WAIVER` (default: on; supports `off`, `shadow`, `on` per DEC-06).
- **Disposition:** `COMMIT_THIS_SESSION`

### Unit 1 (legacy combined)

- **Files:** `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py`
- **Dependencies:** none
- **Preconditions (F-04):** Run `grep -rn "_quality_gate_check" ~/.grok/` to enumerate ALL call sites (production + tests + scripts). Document every caller in the implementation commit. Confirmed callers as of this design:
  - `~/.grok/hooks/scripts/quality_gate/main.py:583` — production caller.
  - No test or script callers found via grep (function is module-private with underscore prefix). To be re-verified before commit.
- **Changes:** Add `_match_scoped_waiver()` and `_consume_waiver()` helpers; update `_quality_gate_check()` signature to accept `modified_files` and return 3-tuple. The implementation is the new mechanism described above (replaces the existing time-bound freshness check).
- **Acceptance criteria:**
  - All existing tests pass (no regression in non-waiver path).
  - `ruff check gate_diagnostics.py` clean.
  - New test `test_quality_gate_check_signature_is_3_tuple` asserts the return shape.
  - New tests: 4 waiver-matching tests + 2 consumption tests (added in Unit 4).
- **Feature flags:** `GROK_REVIEW_GATE_SCOPED_WAIVER` (default: on). Three values: `off` (legacy time-bound), `shadow` (new runs and logs, legacy decides), `on` (new decides). See DEC-06.
- **Disposition:** `COMMIT_THIS_SESSION` (split into Unit 1a refactor + Unit 1b mechanism — F-29)
- **Call-chain compatibility:**
  - Caller: `main.py:583` — calls `_quality_gate_check(session_id, workspace_root, invoked_skills, claim)`. The new signature adds `modified_files` as an optional kwarg with default `None`; existing call sites continue to work (Unit 3 updates the call site).
  - Return value: existing callers unpack `(block, msg)`; new signature returns `(block, msg, decision)`. Existing unpack sites must be updated (Unit 3).

### Unit 2: Rewrite `waiver_gate.py` with new schema

- **Files:** `~/.grok/scripts/waiver_gate.py`
- **Dependencies:** none (independent of Unit 1; both depend on the agreed schema)
- **Changes:** Rewrite script with `--milestone-id`, `--scope-files`, `--next-review-at`, `--authorized-by` flags. Remove `--valid-for-minutes`. Update docstring.
- **Acceptance criteria:**
  - argparse rejects missing required flags with exit code 2 and a clear message.
  - Atomic write via tmp + os.replace.
  - Output file validates against the new schema (manual: `python -c "import json; json.load(open('<path>'))"`).
- **Feature flags:** none (script behavior is gated by the env var in Unit 1).
- **Disposition:** `COMMIT_THIS_SESSION`
- **Call-chain compatibility:**
  - Caller: invoked manually by agents or operators. No programmatic callers on this host.
  - Output: writes `~/.grok/hooks/state/{gate}-waiver-{session_id}.json` — same path pattern as before.

### Unit 3: Update `main.py` Stop-hook emission

- **Files:** `~/.grok/hooks/scripts/quality_gate/main.py`
- **Dependencies:** Unit 1 (signature change)
- **Changes:** Update the call site at line 583 to pass `modified_files=modified_files` and unpack the 3-tuple. Update the emission to handle `decision: warn` (log to `quality-gate-warns-{session_id}.jsonl`, do not exit; let execution continue).
- **Acceptance criteria:**
  - Existing tests pass.
  - New test: warn decision does not call `sys.exit(0)` early (verified by checking execution flow continues past line 590).
  - `ruff check main.py` clean.
- **Feature flags:** none (Unit 1's env var controls the path).
- **Disposition:** `COMMIT_THIS_SESSION`
- **Call-chain compatibility:**
  - Caller: internal Stop-hook flow.
  - Return value: emission format gains `decision: warn` as a new value (existing values `block` and `allow` preserved).

### Unit 4: Update `quality_gates_frontmatter.py` and tests

- **Files:**
  - `~/.grok/hooks/scripts/quality_gates_frontmatter.py` — update `build_block_message()` (line 898) to reference the new schema; add `write_scoped_waiver()` helper.
  - `~/.grok/hooks/tests/test_quality_gates_frontmatter.py` — add 11 new tests (listed below); update 3 existing tests for the new schema.
- **Dependencies:** Units 1, 2 (the new mechanism must be defined before tests can exercise it)
- **Changes:** Update message construction; add helper for the new schema; add tests.
- **Acceptance criteria (F-13):**
  - All tests pass (`pytest`). Quantified: the full test suite (existing N tests + 11 new) passes.
  - `ruff check` clean on both files.
  - Block message references `--milestone-id`, `--scope-files`, `--next-review-at` in the "Options" section.
  - **Mandatory new tests (F-13):**
    - `TestScopedWaiver::test_write_and_read_scoped_waiver` — verifies the new schema round-trips.
    - `TestScopedWaiver::test_waiver_without_next_review_at_is_rejected`
    - `TestScopedWaiver::test_waiver_with_expired_next_review_at_is_ignored`
    - `TestGateCheck::test_quality_gate_check_returns_three_tuple_with_decision_field` — asserts the return shape (regression guard for F-04).
    - `TestGateCheck::test_quality_gate_check_decision_is_allow_when_no_claim` — covers P2 condition 1.
    - `TestGateCheck::test_quality_gate_check_decision_is_allow_when_no_invoked_skills` — covers P2 condition 2.
    - `TestGateCheck::test_quality_gate_check_consumes_waiver_when_matched` — covers the consumption path.
    - `TestGateCheck::test_quality_gate_check_preserves_obligation_lifecycle` — covers P3 (the obligation system is unaffected by the new gate behavior).
    - `TestGateCheck::test_quality_gate_check_ignores_high_consumed_count` — creates a waiver with `consumed_count=999` and verifies the gate still returns `decision: warn` (F-06 regression guard for DEC-07).
    - `TestMainEmission::test_warn_decision_emits_hook_specific_output` — covers F-01 (the correct Stop hook output format) and F-02 (warn path does NOT clear waiver).
    - `TestMainEmission::test_block_decision_emits_correct_json` — covers F-22 (the block path is unchanged) and REQ-07.
- **Feature flags:** none.
- **Disposition:** `COMMIT_THIS_SESSION`

### Unit 5: Update AGENTS.md trigger case

- **Files:** `~/.grok/AGENTS.md` (the "Stop-hook quality-gate block when you've derived a waiver disposition" section)
- **Dependencies:** Units 1-4 (the mechanism must be deployed before the documentation can accurately describe it)
- **Changes (F-21):** Update BOTH the example invocation AND the surrounding disposition text:
  - Replace the example invocation with the four-flag form: `--milestone-id`, `--scope-files`, `--next-review-at`, `--authorized-by`.
  - Add a sentence to the disposition: "The waiver is bound to a specific milestone scope; out-of-scope modifications re-arm the gate to block. The mechanism's audit row records each consumption for retrospective review."
  - Document the `GROK_SELF_AUTH_ALLOWED` env var (F-03): when `0`, self-authorization is refused and operator presence is required.
  - Document the path canonicalization: `~/.grok/hooks/state/quality-gate-waiver-{session_id}.json` (F-08).
- **Acceptance criteria:**
  - The example invocation in AGENTS.md is runnable as-is (manual check).
  - The disposition text mentions all four required flags and the env var.
- **Feature flags:** none.
- **Disposition:** `COMMIT_THIS_SESSION`

### Unit 6a: Bypass-budget utility — minimum viable (F-14)

- **Files:** new — `~/.grok/scripts/bypass_budget.py`
- **Dependencies:** Units 1-4 deployed (so waivers exist in the new schema)
- **Changes:** Standalone utility that scans `~/.grok/hooks/state/quality-gate-waiver-*.json` (the canonical path — F-08) and reports: (a) sessions with missing required fields (schema-coverage metric for the design's success metric), (b) sessions exceeding the self-authorization threshold (default: 10 per session).
- **Acceptance criteria:**
  - Reports schema-coverage: `waiver_files_scanned`, `waiver_files_complete_schema`, `waiver_files_incomplete_schema` (with field-list of incomplete).
  - Reports bypass-budget: `sessions_over_threshold` with `session_id`, `count`, `first_seen_at`, `last_seen_at`.
  - Output format: JSON for `/maintain` consumption (F-26 — verify `/maintain` SKILL.md input contract by reading `~/.grok/skills/maintain/SKILL.md` Step 2 scanner interface; if it consumes JSON, use JSON; if CSV, use CSV; defer format choice if verification is ambiguous).
  - Exit code 0 if all checks pass; exit code 1 if any waiver has incomplete schema or any session exceeds threshold.
- **Feature flags:** none.
- **Disposition:** `COMMIT_THIS_SESSION` (F-14 — required to verify the design's "100% of waivers have 5 fields" success metric)

### Unit 6b: Bypass-budget utility — threshold tuning + visualization (follow-on)

- **Files:** extends `~/.grok/scripts/bypass_budget.py`
- **Dependencies:** Unit 6a deployed
- **Changes:** Configurable thresholds via env var (`BYPASS_BUDGET_PER_SESSION`, `BYPASS_BUDGET_PER_QUARTER`); operator-equivalent grouping; integration with `/maintain` weekly scan.
- **Acceptance criteria:** thresholds configurable; report grouped by operator-equivalent; `/maintain` consumes the output.
- **Feature flags:** none.
- **Disposition:** `HANDOFF` (separate workstream; not blocking Unit 6a)

### Unit 6 (legacy combined)

---

## Code-Path Completeness

The design modifies gate logic. Per the writer prompt, every code path that produces the target outcome must be enumerated.

**Target outcome:** gate fires as non-blocking feedback (`hookSpecificOutput.additionalContext`).

| Path | File:line | Condition | Current behavior | Proposed change |
|------|-----------|-----------|------------------|-----------------|
| 1a | `gate_diagnostics.py:560` | `not claim or not invoked_skills` | Returns `(False, "")` (allow) | Returns `(False, "", "allow")` (allow) |
| 1b | `gate_diagnostics.py:570-600` (matched scope branch) | Waiver exists, not expired, scope_files contains modified_files | Returns `(False, "")` (allow) — TIME-BOUND CHECK | Returns `(False, warn_msg, "warn")` (non-blocking feedback) — NEW |
| 2a | `gate_diagnostics.py:604` (post-fix) | `check_quality_gates()` succeeds (no missing evidence) | Returns `(False, "")` (allow) | Returns `(False, "", "allow")` (allow) |
| 2b | `gate_diagnostics.py:606` | Exception in `check_quality_gates()` | Returns `(False, "")` (allow) — fail-open | Returns `(False, "", "allow")` (allow) — fail-open preserved |

**Target outcome:** gate fires as `block`.

| Path | File:line | Condition | Current behavior | Proposed change |
|------|-----------|-----------|------------------|-----------------|
| 3a | `gate_diagnostics.py:610` (post-fix) | No waiver match + `check_quality_gates()` blocked | Returns `(True, msg)` (block) | Returns `(True, msg, "block")` (block) — unchanged |
| 3b | `gate_diagnostics.py:570-600` (mismatched scope branch) | Waiver exists but `modified_files` NOT � `scope_files` | N/A (current code does not check scope) | Falls through to `check_quality_gates()`; if receipt missing, returns `(True, msg, "block")` (block) — NEW |
| 3c | `gate_diagnostics.py:570-600` (expired branch) | Waiver exists but `next_review_at` elapsed | Returns `(False, "")` (allow) — TIME-BOUND CHECK | Falls through to `check_quality_gates()`; if receipt missing, returns `(True, msg, "block")` (block) — NEW |

The three NEW paths (1b, 3b, 3c) are the load-bearing changes. The current implementation has no concept of "waiver scope" or "waiver expiration by milestone"; the new mechanism closes both gaps.

F-09 fix: the original Path 2 conflated two branches (matched scope → warn; mismatched scope → block). The restructured table makes the branching explicit with `1b` (warn) and `3b` (block) as separate paths.

---

## Traceability Matrix

| REQ/DEC ID | Component | Implementation Unit | Test (F-24) | Status |
|---|---|---|---|---|
| [REQ-01] | Scoped waiver (milestone_id + scope_files + scope_skills) | Unit 1b, Unit 2 | `test_write_and_read_scoped_waiver` | Assigned |
| [REQ-02] | `next_review_at` expiration (ISO-8601 UTC) | Unit 1b, Unit 2 | `test_waiver_with_expired_next_review_at_is_ignored` | Assigned |
| [REQ-03] | Non-blocking feedback on matched waiver | Unit 1b, Unit 3 | `test_quality_gate_check_consumes_waiver_when_matched` | Assigned |
| [REQ-04] | Out-of-scope modification → block | Unit 1b | (covered by `test_quality_gate_check_consumes_waiver_when_matched` + the existing TestCheckQualityGates tests) | Assigned |
| [REQ-05] | Audit trail (`consumed_count` + `consumption_audit`) | Unit 1b, Unit 2 | (covered by `test_quality_gate_check_consumes_waiver_when_matched`) | Assigned |
| [REQ-06] | Self-authorization flag (`authorized_by`) | Unit 2 | (covered by `test_write_and_read_scoped_waiver`) | Assigned |
| [REQ-07] | Stop hook non-blocking feedback emission | Unit 3 | `TestMainEmission::test_warn_decision_emits_hook_specific_output` AND `test_block_decision_emits_correct_json` (F-24) | Assigned |
| [REQ-08] | Updated block message references new schema | Unit 4 | (covered by `TestBuildBlockMessage` updated tests) | Assigned |
| [REQ-09] | Test coverage (11 new tests, 3+ updated) | Unit 4 | (self-referential) | Assigned |
| [REQ-10] | AGENTS.md trigger case update | Unit 5 | (manual verification only; not testable in pytest) | Assigned |
| [REQ-11] | Bypass-budget utility (minimum viable) | Unit 6a | (separate utility; tested in its own suite) | Assigned |
| [REQ-12] | Bypass-budget threshold tuning | Unit 6b | (follow-on; not in this session) | Deferred to HANDOFF |
| [REQ-13] | `GROK_SELF_AUTH_ALLOWED` env var support | Unit 2 | (covered by `test_write_and_read_scoped_waiver` extended) | Assigned |
| [REQ-14] | Bypass budget exceedance regression guard | Unit 1b | `test_quality_gate_check_ignores_high_consumed_count` (F-06) | Assigned |
| [DEC-01] | Scope-bound waiver with non-blocking feedback (replaces time-bound) | Unit 1b, Unit 2 | (covered by REQ-01, REQ-03) | Assigned |
| [DEC-02] | Atomic consumption_audit write | Unit 1b | (covered by `test_quality_gate_check_consumes_waiver_when_matched`) | Assigned |
| [DEC-03] | Expired waiver files NOT auto-deleted (preserve audit history) | Unit 1b | (manual verification) | Assigned |
| [DEC-04] | Stop-hook contract change: emit `hookSpecificOutput.additionalContext` | Unit 3 | `TestMainEmission::test_warn_decision_emits_hook_specific_output` | Assigned |
| [DEC-05] | Refactor `_quality_gate_check` into three functions (mixed concerns) | Unit 1a (refactor), Unit 1b (mechanism) | `test_quality_gate_check_signature_is_3_tuple` (F-04) | Assigned |
| [DEC-06] | Feature flag env var `GROK_REVIEW_GATE_SCOPED_WAIVER` (3 states: off/shadow/on) | Unit 1b | (covered by `test_quality_gate_check_decision_is_allow_when_no_claim` family) | Assigned |
| [DEC-07] | Bypass budget is post-hoc audit signal, not runtime enforcement | Unit 6a, Unit 6b | `test_quality_gate_check_ignores_high_consumed_count` (F-06) | Assigned (audit) + Deferred (threshold tuning) |
| [DEC-08] | Self-authorization is permitted with audit (Option 3 deferred to OQ-04) | Unit 2, Unit 6a | `test_quality_gate_check_preserves_obligation_lifecycle` (P3 coverage) + bypass_budget.py schema check | Assigned (audit) + Deferred (approval channel) |

Every component has an assigned implementation unit (or an explicit deferral with a HANDOFF target) AND a test mapping where testable. No silent abandonment.

---

## Key Decisions

### [DEC-01] Scope-bound waiver with block→warn downgrade (replaces time-bound)

**Decision:** Replace the 30-min time-bound waiver with a scope-bound waiver that downgrades `block → warn` on each matched gate fire, with `consumed_count` and `consumption_audit` recording each consumption.

**Rationale:** Conforms to bhekani single-use pattern (P5) and break-glass (P6). Preserves the anti-loop property (P1). Closes the gaming vector (P4) by binding the waiver to a specific scope and requiring a new waiver for a new scope. Preserves detection value (the gate still fires; the operator sees the warn).

**Rejected alternatives:**
- Time-bound with longer window (1hr, 4hr): same anti-pattern, just slower gaming.
- Pure single-use tokens (Option 2): incompatible with P1 (gate fires every turn).
- Operator-approval channel (Option 3): deferred to OQ-04; current design accepts self-authorization with audit.

### [DEC-02] Atomic `consumption_audit` write

**Decision:** Each gate fire that matches a waiver writes the waiver back atomically (tmp + os.replace) with `consumed_count` incremented and `consumption_audit` appended.

**Rationale:** Crash-during-write or concurrent-write would corrupt the audit trail; atomic write is the standard mitigation on this host per `~/.grok/AGENTS.md` "File editing protocol" Class A.

**Rejected alternative:** Append-only file (`quality-gate-warns-{session_id}.jsonl`) for consumption events: simpler, but harder to query for bypass-budget review. The waiver-file-as-state pattern keeps the waiver self-describing.

### [DEC-03] Expired waiver files are NOT auto-deleted

**Decision:** When `next_review_at` elapses, the waiver file is left in place (the gate ignores it). Operators can review expired waivers via `bypass_budget.py` or manual `ls`.

**Rationale:** The audit history is valuable for retrospective review. Auto-deletion would lose the evidence of the bypass.

**Rejected alternative:** Auto-delete after expiration: simpler state dir, but loses audit trail. The bhekani pattern emphasizes the audit row's value.

### [DEC-04] Stop-hook contract change: emit `hookSpecificOutput.additionalContext` (F-01, F-22)

**Decision:** The Stop hook emission gains a new branch between the existing block branch and the silent-allow path. When the gate fires as `decision: warn` (non-blocking feedback), the hook emits `{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "<warn_message>"}}` and exits 0. The block branch and the silent-allow path are unchanged.

**Rationale:** The break-glass pattern (P6) explicitly says the bypass should convert `block → warn`-style non-blocking feedback, not `block → allow`. The current Stop hook emits only `block` (with `sys.exit(0)` after) or allows silently. **Verified against the Grok Build Stop-hook protocol** (`~/.grok/docs/user-guide/10-hooks.md:254-262`): the only non-blocking feedback mechanism is `hookSpecificOutput.additionalContext`. There is NO `decision: warn` value. The implementation inserts a new branch AFTER the block branch and BEFORE the silent-allow path; the three branches are mutually exclusive (F-22).

**Rejected alternatives:**
- Emit `decision: warn` (assumed supported but verified FALSE per F-01).
- Log the warn to a sidecar file and emit `allow` (do not change the Stop hook contract): simpler, but loses the operator-visible signal at the hook boundary. The hook contract change is small and scoped.

### [DEC-05] Refactor `_quality_gate_check` into three functions

**Decision:** Split into `_match_scoped_waiver()`, `_consume_waiver()`, and the orchestrator `_quality_gate_check()`. Each function is <30 lines.

**Rationale:** The current function has mixed concerns (time-bound freshness check + gate check + return tuple). After the rewrite, the concerns are: waiver matching, consumption update, gate check. Separating them satisfies the mixed-concerns threshold in the Coupling & Code-Smell Inventory and keeps each function focused.

**Rejected alternative:** Keep the function monolithic: violates the inventory threshold without justification.

### [DEC-06] Feature flag env var for staged rollout (three states — F-12)

**Decision:** `GROK_REVIEW_GATE_SCOPED_WAIVER` (default: `on`) controls whether the new mechanism is active. Three values:
- `off` (legacy): the existing time-bound freshness check is used; the new mechanism is fully bypassed.
- `shadow`: the new mechanism runs and logs decisions to the sidecar (`quality-gate-warns-{sid}.jsonl`), but the legacy mechanism's decision is the one emitted on stdout. This is intermediate safety: the operator can observe the new mechanism's behavior without trusting its decision.
- `on` (default): the new mechanism decides; the legacy mechanism is dormant.

**Rationale:** The Stop hook is critical infrastructure; a bug in the new mechanism would block legitimate completion claims. The feature flag allows staged rollout (off → shadow → on) and rapid rollback (on → off) if needed.

**Rejected alternative:** No feature flag (commit-and-ship): violates the reversibility principle. Two-state flag (off/on) without shadow: misses the intermediate-safety step that the Rollout section explicitly relies on. The three-state flag is a standard pattern on this host and adds <10 lines of code.

**Implementation (F-12):** at the top of `_quality_gate_check`:

```python
import os
_MODE = os.environ.get("GROK_REVIEW_GATE_SCOPED_WAIVER", "on").lower()
# _MODE in {"off", "shadow", "on"}
```

The 3-branch logic is: `_MODE == "off"` → legacy path; `_MODE == "shadow"` → run both, log new decision, emit legacy decision; `_MODE == "on"` → run new, emit new decision.

### [DEC-07] Bypass budget is post-hoc audit signal, not runtime enforcement

**Decision:** A session exceeding the bypass budget is flagged for retrospective review (e.g., the operator sees it in `bypass_budget.py` output); the gate does not change behavior based on the count.

**Rationale:** Runtime enforcement of bypass budgets would require the gate to track counts across sessions (cross-session state, complex). Post-hoc audit is simpler and matches the break-glass pattern (P6: "bypass budgets: teams that exceed a configurable bypass count per quarter are flagged for review" — note "flagged", not "blocked").

**Rejected alternative:** Runtime enforcement (gate refuses to waive when count exceeds threshold): adds cross-session state, more complex, and creates a new failure mode (false positives block legitimate work).

### [DEC-08] Self-authorization is permitted with audit

**Decision:** Agents may write waivers with `authorized_by: "agent"`. Operator-authorized waivers are explicitly marked `authorized_by: "operator"`. Both are recorded in the audit log.

**Rationale:** Synchronous operator approval is impractical on this host (P9). Self-authorization with audit is the asynchronous analogue — the operator reviews post-hoc. The audit log makes retrospective review possible.

**Rejected alternative:** No self-authorization (operator must approve every waiver): impractical and creates a new failure mode (work halts when operator is unavailable).

---

## Rollout

### Phase 1: Deploy with feature flag off (Unit 1 + Unit 2)

- Ship Units 1, 2, 4 with `GROK_REVIEW_GATE_SCOPED_WAIVER=off` default.
- The new code path is loaded but inert (the legacy time-bound check runs).
- Manual test: invoke the new `waiver_gate.py` with the new flags; verify the file is written in the new schema. Verify the gate does NOT match (feature flag off).
- Estimated time: 30 min.

### Phase 2: Enable feature flag for one session (shadow mode)

- Set `GROK_REVIEW_GATE_SCOPED_WAIVER=on` in one session's env (via the operator's session config).
- The session runs the new mechanism. Audit log records each fire.
- Manual review: verify the warn message is surfaced correctly; verify the gate downgrades for in-scope fires; verify the gate blocks for out-of-scope fires.
- Estimated time: 1 hour of active use, then 30 min review.

### Phase 3: Enable feature flag by default

- Change the default to `on` (the env var still allows override).
- Monitor the bypass-budget log weekly via `bypass_budget.py`.
- Estimated time: 5 min code change + 1 week observation.

### Phase 4: Remove feature flag (after 1 month of stable operation)

- Remove the env var; the new mechanism is unconditional.
- The bypass budget becomes the only audit signal (no more opt-out path).

### Rollback

- Set `GROK_REVIEW_GATE_SCOPED_WAIVER=off` (instant rollback to legacy time-bound mechanism).
- OR: revert the commit and re-deploy (slower, but full rollback including the Stop-hook contract change).

### Shadow mode (intermediate safety)

- During Phase 2, the new mechanism runs alongside the legacy mechanism (both paths execute; the new path logs but does not change the decision). This catches regressions before the feature flag flips.
- Implementation: when `GROK_REVIEW_GATE_SCOPED_WAIVER=shadow`, the new mechanism runs and logs to a shadow log; the legacy mechanism's decision is the one emitted.

---

## File Change Inventory

| File | Action | LOC delta (est.) | Unit |
|---|---|---|---|
| `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py` | Modify (replace `_quality_gate_check` + add 2 helpers; 3-state feature flag) | +75, -25 | Unit 1a + 1b |
| `~/.grok/scripts/waiver_gate.py` | Modify (rewrite schema + new flags + `GROK_SELF_AUTH_ALLOWED` support) | +55, -10 | Unit 2 |
| `~/.grok/hooks/scripts/quality_gate/main.py` | Modify (update call site + emission logic; 3-branch if/elif/else) | +25, -5 | Unit 3 |
| `~/.grok/hooks/scripts/quality_gates_frontmatter.py` | Modify (update `build_block_message` + add `write_scoped_waiver` helper) | +30, -10 | Unit 4 |
| `~/.grok/hooks/tests/test_quality_gates_frontmatter.py` | Modify (add 11 tests, update 3 existing) | +220, -20 | Unit 4 |
| `~/.grok/AGENTS.md` | Modify (update trigger case + env var + path) | +12, -3 | Unit 5 |
| `~/.grok/scripts/bypass_budget.py` | New (Unit 6a minimum-viable; Unit 6b deferred) | +60 | Unit 6a |
| `~/.grok/hooks/state/quality-gate-warns-{session_id}.jsonl` | New (per-session, append-only; rotation by `/maintain` weekly cleanup of files >30 days, hard cap 10 MB → truncate-and-rotate) | N/A | Unit 3 |
| `P:/docs/handoffs/main-py-quality-gate-refactor-2026-08-11/HANDOFF.md` | New (handoff for the pre-existing main.py refactor backlog) | +30 | F-20 (deferred) |

Total estimated LOC change: ~280 lines added, ~70 lines removed across 7 files.

---

## Open Questions

### OQ-01: Is the gaming vector real? (P4)

**Status:** [INFERENCE]
**What would resolve:** Retrospective audit of waiver-rewrite patterns in `~/.grok/hooks/state/quality-gate-waiver-*.json` for the past 30 days. Count waivers rewritten within 25 min of the previous waiver's creation.
**What changes if wrong:** If no gaming is observed, the gaming vector is theoretical. The design still applies (conformance to literature), but the urgency is lower.
**Design degradation if wrong:** Implementation cost (~280 LOC, 7 files, ~5 days) is incurred for a theoretical-only fix; the operator may prefer to defer to a future version where empirical gaming is documented. Cost of deferring: ~$0; the current 30-min waiver remains in place.
**Cost of resolving:** ~1 hour of retrospective audit + 30 min analysis.

### OQ-02: Can the Stop hook protocol emit `decision: warn`? (P8) — RESOLVED

**Status:** RESOLVED FALSE (F-01).
**Resolution:** The Grok Build Stop hook does NOT support a `decision: warn` value (receipt: `~/.grok/docs/user-guide/10-hooks.md:254-262`). The design now uses `hookSpecificOutput.additionalContext`. OQ-02 is closed; no further action.

### OQ-03: Do all milestones have a concrete ship-time review point? (P10)

**Status:** [UNKNOWN]
**What would resolve:** Instrument the waiver log post-deploy; measure the rate of `next_review_at: null` or "TBD" submissions.
**What changes if wrong:** If >20% of waivers lack a concrete `next_review_at`, the milestone-scoping discipline is failing. A stricter frontmatter validation (`next_review_at` is required and must be a future timestamp) is added.
**Design degradation if wrong:** Stricter validation is added as a follow-on; the design's core mechanism is unchanged.
**Cost of resolving:** ~1 day to add validation + 1 week observation.

### OQ-04: Should a real operator-approval channel be added?

**Status:** [UNKNOWN]
**What would resolve:** Operator decision: implement Slack/Teams/terminal-bell webhook for synchronous waiver approval?
**What changes if decided yes:** A new unit is added (Unit 7) that calls the webhook before writing the waiver; the operator approves/denies in real time. Self-authorization remains as a fallback when the operator is unavailable (timeout).
**What changes if decided no:** The current design (self-authorization with audit + bypass-budget review) is the final state.
**Cost of yes:** ~3-5 days of work; adds a synchronous approval channel and timeout handling.
**Cost of no:** ~$0; the design ships as-is.
**Recommendation:** Defer to follow-on design; the current design is sufficient for the stated problem. The `GROK_SELF_AUTH_ALLOWED=0` mode (F-03) gives the operator a per-session escape hatch without building a new channel.

### OQ-05: Should waiver files be HMAC-signed?

**Status:** [UNKNOWN]
**What would resolve:** Operator decision: invest in tamper-evident waiver storage?
**What changes if decided yes:** A new field `signature` is added to the waiver schema; the script computes an HMAC over the rest of the fields using a shared secret stored in `~/.grok/hooks/state/.secret`. The gate verification re-computes the HMAC and rejects tampered waivers.
**Cost of yes:** ~1-2 days of work; adds a secret-management concern (where is the secret stored, who has access, what happens on secret rotation).
**Cost of no:** ~$0.
**Recommendation:** Defer; the current threat model (unreliable-agent, not adversarial) does not require tamper-evidence. The audit log + bypass-budget review is sufficient.

### OQ-06: Should the bypass budget be enforced at runtime, not just audit?

**Status:** [UNKNOWN]
**What would resolve:** Operator decision: enforce the bypass budget at runtime (gate refuses to waive when count exceeds threshold)?
**What changes if decided yes:** The gate tracks `consumed_count` across the session; when it exceeds the threshold, the gate falls back to `block` mode regardless of waiver match. Cross-session tracking adds complexity (shared state file).
**Cost of yes:** ~2-3 days of work; adds cross-session state tracking + a regression test for the threshold transition.
**Cost of no:** ~$0; post-hoc audit (DEC-07).
**Recommendation:** No (DEC-07); post-hoc audit is sufficient for the unreliable-agent threat model.

---

## Appendix: Premise Labels Reference

For traceability, each premise cited above:

| Premise | Label | Receipt / Source |
|---|---|---|
| P1 | [FACT] | `gate_diagnostics.py:562-568` |
| P2 | [FACT] | `gate_diagnostics.py:549-557` |
| P3 | [FACT] | `main.py:510-590` |
| P4 | [INFERENCE] | Code structure (waiver accepts re-write); no empirical test |
| P5 | [RESEARCH] | digitalgarden.bhekani.com/single-use-override-tokens/ |
| P6 | [RESEARCH] | safeguard.sh/resources/blog/break-glass-workflow-design-audited-bypass |
| P7 | [FACT] | session 019fee63, VS-02 milestone |
| P8 | [INFERENCE] | Reasoned from P1 + P6 (now verified FALSE on the Stop-hook protocol; design uses correct mechanism) |
| P9 | [UNKNOWN] | Operator-availability telemetry not measured |
| P10 | [UNKNOWN] | Milestone-discipline rate not measured |
| P11 | [INFERENCE] | Promoted from UNKNOWN per F-16; see Premise Verification section |

**Premise label taxonomy (F-15):**

- **`[FACT]`** — directly verified: tool call, file read, or command output in this session confirms it.
- **`[INFERENCE]`** — reasoned from context but not directly verified: plausible but unconfirmed.
- **`[UNKNOWN]`** — cannot be determined from available evidence.
- **`[RESEARCH]`** — externally sourced (web search, documentation, external authority) but not verified against workspace state. **Added per F-15** to distinguish from `[FACT]` (which implies workspace verification). `[RESEARCH]` claims are taken as given for the design but should be re-verified if the design's claims are challenged.
- **`[CONTRADICTED]`** — conflicts with a verified workspace fact or prior wiki decision.
