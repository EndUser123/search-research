# Phase 2 — Freshness-ruled runtime ground truth — Evidence Packet

**Date:** 2026-07-07
**Scope:** Build the runtime-ground-truth data file + the pure-text renderer
(parse + stale-mark + budget-cap), with tests. HARD PAUSE before the
live-injection wiring (Rule 4b).
**Program:** Close-the-Loop telemetry reliability (Phase 2)
**Status:** Deliverables 1–4 GREEN (shadow-safe). Injection wiring (deliverable 5)
PAUSED — router-forwarding finding below requires a decision.

---

## 1. Deliverables (this packet)

| Path | Role | Status |
|------|------|--------|
| `analysis/runtime-ground-truth.md` | data file: fact \| source \| verification_command \| last_verified \| expiry_trigger (6 seed rows) | ✅ shipped |
| `cc-aca-session/__lib/runtime_ground_truth.py` | renderer: parse → stale-mark → budget-cap (pure function, no IO in render) | ✅ shipped |
| `cc-aca-session/tests/test_runtime_ground_truth.py` | 8 pytest cases: parse, fresh, stale, session-scoped, calendar, budget, malformed-date, e2e | ✅ 8/8 green |

---

## 2. Raw test output

```
$ python -m pytest cc-aca-session/tests/test_runtime_ground_truth.py -v

test_parse_skips_header_and_separator PASSED                       [ 12%]
test_render_fresh_passes_through PASSED                           [ 25%]
test_render_stale_shows_reverify_command PASSED                   [ 37%]
test_session_scoped_trigger_is_always_stale PASSED                [ 50%]
test_calendar_trigger_far_future_fresh PASSED                     [ 62%]
test_budget_hard_cap PASSED                                       [ 75%]
test_malformed_date_treated_as_fresh PASSED                       [ 87%]
test_load_real_ground_truth_file PASSED                           [100%]
============================== 8 passed in 0.14s ==============================
```

End-to-end (`test_load_real_ground_truth_file`) parses the shipped
`runtime-ground-truth.md` against today (2026-07-07): 5 fresh rows render
plain, the "Today is 2026-07-07" row renders `[STALE — reverify: ...]`
because its trigger is `next session start` (session-scoped → always
re-verify, by design — never silently trust a session-scoped fact).

---

## 3. Design decisions

- **Pure renderer, no IO in `render()`.** SessionStart hot-path cost = one
  file read + parse + format. `load_and_render()` is the only IO entry;
  `render()` is pure on parsed rows → testable without filesystem.
- **Stale entries are NEVER dropped.** `[STALE — reverify: <cmd>]` keeps
  the fact visible AND surfaces the verification command, so the model can
  re-verify instead of citing an unchecked fact (Phase 2 core invariant:
  "never dropped or silently trusted").
- **Session-scoped triggers (`next session start`) = always stale.**
  Rationale: a fact that must be re-verified every session is, by
  definition, not verified THIS session until the command runs. Forcing
  the stale marker is the conservative choice.
- **Budget is a HARD cap on total output (header + rows).** Ponytail: the
  cap means total length, not "rows after headers." Initial impl
  double-counted headers → `test_budget_hard_cap` caught it (442 > 400).
  Fixed: pre-compute header size, reserve, then fit rows.
- **Protected slots documented but not yet wired.** `BUDGET_PROTECTED_CHARS`
  = 800 reserved for ground_truth + mechanism_manifest. The cross-injector
  budget arbiter (the actual truncation of OTHER injectors when total
  exceeds `BUDGET_TOTAL_CHARS=1800`) is deferred to the injection-wiring
  step — it can't be built until the injector is registered and its
  co-injectors are enumerable.

---

## 4. Router-forwarding finding (the HARD PAUSE trigger)

**Verified fact (grep, 2026-07-07):** `cc-aca-session/__lib/router.py` has
**no `additionalContext` / `hookSpecificOutput` forwarding.** Child hook
stdout is captured via `capture_output=True` (router.py:88, 92) and used
ONLY for block-decision detection; non-block JSON is discarded and the
router emits `{}` (router.py:107).

**Implication:** The plan's "Sessionstart injection via cc-aca-session
(router.py registration)" cannot be satisfied by merely adding a hook to
`SESSIONSTART_HOOKS` — a child hook emitting
`{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":...}}`
would have its context silently dropped by the router.

**Cross-reference (grep, 2026-07-07):** 10 SessionStart hooks in
`P:/.claude/hooks/` DO emit `additionalContext` via `hookSpecificOutput`
(e.g. `SessionStart_cc_health.py:80`). These are registered **directly in
settings.json**, not through the cc-aca-session router — confirming the
direct-registration path is the proven injection surface, and the plugin
router is currently injection-inert.

---

## 5. HARD PAUSE — decision required (Rule 4b)

The injection wiring requires one of:

| Option | Change | Blast radius | Invariant impact |
|--------|--------|--------------|------------------|
| **A** | Edit `cc-aca-session/__lib/router.py` to collect child `additionalContext` and forward it in the router's own stdout | Shared helper used by all cc-aca-session SessionStart/SessionEnd dispatch; concurrent-session-impacting | Preserves "dispatch via router.py" invariant; closes the router's injection-inert gap |
| **B** | Register `aca_session_ground_truth_inject.py` as a SEPARATE direct `settings.json` SessionStart entry (bypass the cc-aca-session router for this one injector) | One new settings.json line; no shared-helper change | **Violates** the CLAUDE.md dispatch invariant ("a plugin dispatches via EITHER router.py OR hooks.json — never both") |
| **C** | Verify whether `snapshot/__lib/router.py` already forwards `additionalContext`; if so, adopt its pattern for cc-aca-session's router (variant of A with a proven template) | Same as A | Same as A |

**Selection criterion:** reversibility × invariant-preservation ×
concurrent-session safety. Option A/C preserves the dispatch invariant
and fixes the underlying gap (the router can't inject), at the cost of a
shared-helper edit. Option B is smaller but introduces a documented
invariant violation that will recur for every future SessionStart
injector in this plugin.

**Recommendation: Option C** — verify snapshot's router forwarding first
(read-only, ~1 tool call), and if it forwards, clone the pattern into
cc-aca-session's router. This avoids inventing a new forwarding shape and
matches an in-fleet precedent. If snapshot does NOT forward, fall back to
Option A (design the forwarding shape, with the multi-child
additionalContext merge strategy made explicit).

**Awaiting approval before:** any router.py edit, settings.json addition,
plugin version bump, cache rebuild, or `/reload-plugins`.

---

## 6. Unresolved items

- **#906 auto-commit:** Phase 2 deliverables 1–4 NOT yet auto-committed
  (the new files are under `P:/.claude/hooks/analysis/` and
  `cc-aca-session/__lib/` + `tests/`, all tracked paths — #906 may pick
  them up; if so, SHA will be recorded here when observed).
- **Cross-injector budget arbiter** deferred to injection-wiring step
  (see §3).
- **Snapshot router forwarding** unverified — Option C prerequisite
  (one read-only Grep, to run at resume).
- **Knowledge-cutoff row** (`calendar 2027-01`) is a placeholder anchor;
  the real model-family-change trigger should be refined when the
  external-fact claim shape (Phase 3) can detect model-ID claims.

---

## 7. Gate criteria satisfied (Phase 2 partial — render layer)

- ✅ runtime-ground-truth.md ships the schema + 6 seed rows (incl. the
  plan's mandated seed entry: Gold corpus canonical path)
- ✅ Renderer parses the table, marks stale entries with reverify command,
  never silently trusts, never drops
- ✅ Budget hard-cap enforced (total output, not rows-after-headers)
- ✅ 8/8 tests green incl. e2e against the shipped file
- ✅ Session-scoped triggers treated as always-stale (conservative)
- ⏸️ SessionStart injection NOT yet wired (HARD PAUSE, §5)
- ⏸️ Cross-injector cumulative budget arbiter NOT yet wired (deferred to
  injection step)