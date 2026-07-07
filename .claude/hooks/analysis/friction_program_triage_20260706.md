# Friction Program Triage — 2026-07-06

**Purpose:** Snapshot of where the prior-friction program actually stands, so the next
session doesn't re-derive what's already known. Cross-references
`stop_gate_retirement_candidates_20260701.md`; does not duplicate it.

**Source-of-truth reminder:** block counts from `diagnostics.db` are inflated by
synthetic test-fixture rows — use `logs/diagnostics/stop_blocks.jsonl` for retirement
decisions (per the 2026-07-06 addendum on `stop_gate_retirement_candidates_20260701.md`).

## Status of the four referenced tasks

### #815 — Resolve orphaned cc-aca-authority/reasoning Stop-gate tier [pending, body only]

- Created 2026-07-05 with embedded triage. Opening split is sound:
  - **3 confirmed dead duplicates** (safe to delete after logic-equivalence diff):
    `Stop_behavior_gates.py`→`behavior_audit` (Stop.py:3917),
    `Stop_lazy_workaround_gate.py`→`lazy_workaround_gate` (Stop.py:3926),
    `Stop_reasoning_quality_gate.py`→`reasoning_quality_gate` (Stop.py:3925).
  - **5 unique-but-dormant** (keep/re-wire/delete per gate): `Stop_safety_gate.py`
    (director decided leave-dormant 2026-06-18), `stop_permission_stall.py`,
    `StopHook_rca_reflector.py`, `Stop_self_reflection_gate.py`,
    `StopHook_drift_sentinel.py`.
- Body not started. Each dead-duplicate needs a logic-equivalence diff against its
  `IN_PROCESS_GATES` twin (not just name match — same trap that delayed diagnosis
  before commit 1df7bd9). Rollback: `git restore` after per-plugin version bump.

### #986 — Quiet recurring false-positive verification hooks [pending, root-cause unlocated]

Three hooks fail on skills verified PRESENT on disk. Cost ~6 turns/session in
false-positive silence workarounds:

1. `suggest:` integration-verification reports "not found" for siblings confirmed
   present by direct `ls` of cache. Worked around by emptying `suggest: []`.
2. `depends_on_skills` hook same FP class; field removed entirely to silence.
3. Skill-first gate blocks `/chs` and `/task` even when skill loaded this session
   — `[E_SKILL_FIRST_INLINE_BYPASS]` forces re-load.

**Discriminating signal**: `ls` says present, hook says missing — the resolution
likely checks the wrong root (source vs cache) or the wrong field. Origin to locate
at fix time: `cc-skills-sdlc/skills/uci/__lib/memory_integration.py` (suggest source)
and the skill-first gate in `execution_hooks`.

### #1090 — Skill-first gate FP: blocks tool batch even when skill loaded via slash command [pending]

Distinct defect from #986's third hook (same gate, same FP shape, but separate
mechanism). Verified facts from prior session:

- `/cc-skills-sdlc:task` command loaded the skill body into context (visible
  "Base directory for this skill..."), proving the skill WAS invoked.
- 6 parallel TaskCreate calls blocked with `E_SKILL_FIRST_PENDING_INTENT`.
- A redundant second `Skill("cc-skills-sdlc:task")` cleared the gate.

**Counterexample to verify before fix**: does the skill body appear in context
BEFORE the first tool_use turn? If yes → pure FP, fix as discrimination change
(credit slash-command invocation as satisfaction). If no → sequencing problem
(defer tool dispatch until skill load acks).

**Generalization**: same failure class as #882 (substring match on intent without
checking actual load state) and the broader "gate fires on label not artifact"
pattern.

### #1214 — Fix lazy-workaround proximity detector self-referential FP [pending]

Most precisely diagnosed of the four. Mechanism is DIFFERENT from #1122's stale-read
hypothesis:

- `_check_duplicate_acceptance_proximity` and `_check_dismissal_proximity` in
  `Stop_lazy_workaround_gate.py` (cc-aca-authority, dispatched via Stop.py:1916)
  match `expected` near `extra` when those words appear in prose DISCUSSING the
  gate's own behavior.
- Source is `last_assistant_message` (fresh), NOT stale transcript.
- Fix is two-part: (1) add self-referential exclusion to bypass proximity detectors
  when response discusses detection/gate patterns, (2) demote proximity blocks to
  warn-only (regex-based `LAZY_PATTERNS` stay as blocks).
- Measured 31% FP-rate from `__csf/.staging/fp_labels.jsonl` (29 labels on this gate)
  is likely understated — the discriminator between meta-discussion and lazy prose
  isn't tight.

## Third FP mechanism on the staleness re-reader (NOT NEW — see task #1218)

The user surfaced a concrete third FP mechanism on the staleness re-reader block,
beyond the two already in scope (firing on unrelated turns, re-firing after
satisfaction per #1059's shape):

**Mechanism 3 — tool-type selectivity in the staleness flag**: the block fires
even after Grep re-verifies the same file, because the flag's "edited-after-read"
bit clears only on a `Read` tool call, not on Grep/Glob. So a model that does
the right thing (re-greps the same path to confirm a deletion landed) still gets
flagged as "no recent evidence for this claim" on the next turn.

**Status: already covered.** This is the same gate surface addressed by
task #1218 ("Add telemetry to 3 invisible Stop gates — staleness/commitment/
task-list"), with the source-of-truth handoff at
`P:/.claude/.artifacts/friction-reduction-handoff-20260706.md` section 2B. All
three mechanisms (unrelated-turn firing, post-satisfaction re-fire, tool-type
selectivity) are invisible-gate FP shapes on the same staleness-tracker, not
three separate fixes. The single discriminator is "did this turn produce fresh
evidence for the claim that's flagged?" — and the tracker currently only credits
`Read`, missing `Grep` and `Glob`.

**Where the implementation actually lives**: a grep for `edited_after_read` /
`staleness_re_reader` / `last_verified_at` returned nothing in `P:/.claude/hooks/`
(only one hit on `content_filter_skips.jsonl`, which is the skip log, not the
implementation). Per the handoff section 2B, the staleness re-reader "fires via
injected text, not a recorded block event" — so the flag is in the injection
source, not in a Stop gate. Likely candidates: a UserPromptSubmit or PostToolUse
injector whose freshness check uses `Read` mtime only.

**Recommended shape** (matches task #1218 step 1–4 verbatim, just enriched with
the third mechanism): one investigation, not three fixes. Step 1: locate each
gate's source file + emission site. Step 2: add one-line diagnostics.db logging
gated by `STOP_TELEMETRY`. Step 3: run ≥7 days, measure. Step 4: classify each
gate and demote/fix/remove per retirement-doc procedure.

**Addendum to #1218**: when telemetry lands, count fires that follow a
Grep/Glob re-verification of the same path. That count is the FP-mechanism-3
evidence base — separate from the unrelated-turn and post-satisfaction counts.
Update task #1218 description to include this third mechanism explicitly.

## Other carryover items from the prior session (decisions deferred, not lost)

1. **`response_intent.py` orphan** — its only plugin consumers were the deleted
   `Stop_approval_gate.py` / `Stop_commit_gate.py` (removed in 1df7bd9); only tests
   use it now. Scope-creep relative to that commit. Document here so a future task
   picks it up: either delete (tests update) or document as test-fixture-only
   utility.
2. **`Stop_safety_gate.py` moot edits** — field normalization and `check_protocol`
   removal from an earlier secret-scan investigation are still in tree, touching a
   gate that isn't dispatched. Two coherent options:
   - Revert for purity (low value, churn for its own sake).
   - Accept as legitimate dead-code cleanup (the `check_protocol` removal is a
   mild positive — it was an FP landmine; the normalization is harmless).
   Recommendation: accept, document in plugin CLAUDE.md.
3. **Pre-existing working-tree noise** — many M/M files unrelated to the
   gate-deletion scope (SessionStart.py, violation_tracker, marketplace.json,
   submodules, docs/) were not staged in 1df7bd9. They're not regression risk for
   this program but they crowd `git status` and slow review.

## What this doc does NOT do

- Does not delete code. Reversible gate retirement belongs in a separate, scoped
  task per the addendum's "demote-to-telemetry-and-monitor, not delete" rule.
- Does not bump plugin versions. That's step 3 of the Plugin Mutation Checklist
  and fires only when a plugin file actually changes.
- Does not touch the 166 pre-existing hook-test failures (#1144) — different
  problem class (test isolation / fixture drift), different program.