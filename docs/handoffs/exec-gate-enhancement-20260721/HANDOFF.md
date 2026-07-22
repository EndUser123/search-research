---
thread_id: 18a85cda-3fa8-47e2-b2bb-f2b55ac77450
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console_9f699e91-fb33-4b67-a977-2e7a
produced_at: 2026-07-21T14:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: exec-gate enhancement (extend existing plugin with preflight integration)

## 1. Objective (one sentence)

Extend the existing `~/.grok/plugins/exec-gate/` plugin with criticality-class TTLs, preflight-artifact integration, and composition detection, following the 5-PR plan at `P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md`.

## 2. Status

**OPEN — plan written, no code started.** The plan is ready for implementation. PR 1 (multi-class grant support) is the foundation; it has no dependencies and extends existing patterns cleanly.

## 3. Producing context

- **Date:** 2026-07-21
- **Session:** `019f821c-854e-76c1-a755-add284838bdf`
- **Terminal:** `console_9f699e91-fb33-4b67-a977-2e7a`
- **No parent handoff** (root-level planning artifact).
- **Origin:** this session pivoted from CCR fleet work to `/design` and runtime foundation, then produced this exec-gate enhancement plan as a concrete deliverable.

## 4. Current state

- **Plan exists:** `P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md` (5 PRs, dependencies documented).
- **No code started:** all 5 PRs are READY but UNTOUCHED.
- **Three Open decisions** need user input before PR 3 (see §5).
- **Code-review R-001** (the `2>&1` in Python Setup snippet) was already fixed in the source before this handoff; verify before next `/design` run. The plan is ready for implementation. PR 1 (multi-class grant support) is the foundation; it has no dependencies and extends existing patterns cleanly.

## 5. Read-first list (ordered)

1. **`P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md`** — the 5-PR enhancement plan. This is the primary document. Read it in full before starting.
2. **`~/.grok/plugins/exec-gate/README.md`** — what exec-gate already does (dialogue mode, session-keyed grants, TTL-based auth)
3. **`~/.grok/plugins/exec-gate/scripts/gate.py`** — the PreToolUse hook (deny-by-default, read-only tools always allowed)
4. **`~/.grok/plugins/exec-gate/hooks/hooks.json`** — the correct hook JSON shape (nested `hooks: [...]` array)
5. **`P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md`** — verified deny contract (Python hook shape, exit codes, env vars, multi-terminal isolation)
6. **`~/.grok/skills/tp/SKILL.md`** — Mode 7 (fabricated causal chain) — the defense this enhancement is partly motivated by

## 6. Verified facts

- [FACT] All three missing features (criticality-class TTLs, preflight-artifact integration, criticality map + composition detection) are cleanly extendable against exec-gate's session-keyed state model. No fundamental conflicts.
- [FACT] exec-gate's existing hook JSON shape is correct and working (uses nested `hooks: [...]` array per Grok's `10-hooks.md` spec).
- [FACT] `spawn_subagent` is already in the matcher (hooks.json:3). The design doc reviewer flagged this as missing; it was already present.
- [FACT] Multi-terminal isolation is verified via `GROK_SESSION_ID` (test_gate_different_sessions_isolated).

- `[FACT]` All three missing features (criticality-class TTLs, preflight-artifact integration, criticality map + composition detection) are cleanly extendable against exec-gate's session-keyed state model. No fundamental conflicts.
- `[FACT]` exec-gate's existing hook JSON shape is correct and working (uses nested `hooks: [...]` array per Grok's `10-hooks.md` spec).
- `[FACT]` `spawn_subagent` is already in the matcher (hooks.json:3). The design doc reviewer flagged this as missing; it was already present.
- `[FACT]` Multi-terminal isolation is verified via `GROK_SESSION_ID` (test_gate_different_sessions_isolated).

## 7. Open decisions

### Decision 1: Default TTL table
- **Question:** auth=4h, docs=24h, production=1h, default=10min — confirm or adjust?
- **Currently leading:** proposed defaults; no user input yet.

### Decision 2: Composition rule strictness
- **Question:** strict (require explicit multi-class `/exec`) vs lenient (require higher-TTL class's grant)?
- **Currently leading:** TBD; user input needed.

### Decision 3: Preflight artifact location
- **Question:** per-class files vs single file with per-class entries?
- **Currently leading:** TBD; user input needed.

### AAR findings (from session 019f821c)

Two AAR findings are noted in the plan's risks section:
- **AAR-OPP-006** (worktree-write detection): candidate for PR 5 or PR 6 scope — a SessionEnd hook that detects wiki concept writes from worktree sessions that don't exist at canonical path.
- **AAR-OPP-005** (context firewall validation): a `/design` skill validation task, not exec-gate work.

Two AAR findings from session 019f821c are noted in the plan's risks section:

- **AAR-OPP-006** (worktree-write detection): candidate for PR 5 or PR 6 scope — a SessionEnd hook that detects wiki concept writes from worktree sessions that don't exist at canonical path.
- **AAR-OPP-005** (context firewall validation): a `/design` skill validation task, not exec-gate work. Tracked in the plan so it isn't lost.

## 8. Task packets

### TP-1: Multi-class grant flag support (foundation)
- goal: Extend exec-gate to support multiple grant flags per session, not just one.
- in scope: modify `~/.grok/plugins/exec-gate/scripts/gate.py` to parse and enforce multiple class flags.
- out of scope: TTL logic (PR 3), preflight integration (PR 4).
- files / anchors: `~/.grok/plugins/exec-gate/scripts/gate.py`, `~/.grok/plugins/exec-gate/README.md`
- acceptance: 2+ grant flags on a single session; both honored independently.
- falsifier: only one grant flag is honored; second flag silently ignored.
- verification level required: UNIT_TEST

### TP-2: Extend `discovery_audit.py` schema
- goal: Update the preflight audit script to recognize new preflight-artifact fields.
- in scope: modify `P:/.agents/skills/preflight/scripts/discovery_audit.py` schema.
- out of scope: runtime integration (PR 4).
- files / anchors: `P:/.agents/skills/preflight/scripts/discovery_audit.py`
- acceptance: preflight artifacts can declare criticality class; audit reports it.
- falsifier: criticality class field not in audit output.
- verification level required: UNIT_TEST

### TP-3: Criticality map + class lookup (depends on TP-1)
- goal: Add per-class TTL logic; per-class grant lookup.
- in scope: extend `~/.grok/plugins/exec-gate/scripts/gate.py` with TTL config + lookup.
- out of scope: preflight authorization (PR 4).
- files / anchors: `~/.grok/plugins/exec-gate/scripts/gate.py`
- acceptance: TTL table configurable per class; lookup honors expiry.
- falsifier: TTL ignored; grants never expire.
- verification level required: UNIT_TEST

### TP-4: Preflight-artifact authorization path (depends on TP-2, TP-3)
- goal: Allow preflight artifacts to authorize tool calls without separate grant.
- in scope: add `preflight_artifact` branch to `gate.py` decision tree.
- out of scope: docs / AAR cleanup (PR 5).
- files / anchors: `~/.grok/plugins/exec-gate/scripts/gate.py`
- acceptance: artifact with `criticality: auth` is honored as an auth grant.
- falsifier: artifact ignored; only `~/.grok/plugins/exec-gate/` state honored.
- verification level required: UNIT_TEST

### TP-5: Documentation + dangling-citation fixup + AAR-OPP-006
- goal: Update README; clean up dangling citations; add SessionEnd hook for worktree-write detection.
- in scope: docs; SessionEnd hook per AAR-OPP-006.
- out of scope: any new exec-gate logic.
- files / anchors: `~/.grok/plugins/exec-gate/README.md`, SessionEnd hook script.
- acceptance: README reflects new features; AAR-OPP-006 mitigation in place.
- falsifier: docs stale; AAR-OPP-006 unaddressed.
- verification level required: STATIC_INSPECTION

## 9. Hard constraints

1. **Multi-terminal isolation.** State files are keyed by `GROK_SESSION_ID` (test_gate_different_sessions_isolated). Don't relax this.
2. **Fail-closed on state corruption.** Corrupt state files are deleted, not recovered (`gate.py:120-140`). Don't paper over corruption with defaults.
3. **Nested hooks array.** Hook JSON uses nested `hooks: [...]` array per Grok's `10-hooks.md` spec. Don't flatten to single-command format.
4. **Session-keyed state (no global grants).** State is per-session. No shared global grant table.
5. **AAR-OPP-005 scope.** Context firewall validation is a `/design` skill task, NOT exec-gate work. Don't absorb it.

## 10. Cross-reference couplings

This handoff depends on:
- `~/.grok/plugins/exec-gate/README.md` — what exec-gate does (dialogue mode, session-keyed grants, TTL-based auth)
- `~/.grok/plugins/exec-gate/scripts/gate.py` — the PreToolUse hook (deny-by-default, read-only tools always allowed)
- `~/.grok/plugins/exec-gate/hooks/hooks.json` — the correct hook JSON shape (nested `hooks: [...]` array)
- `P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md` — verified deny contract (Python hook shape, exit codes, env vars, multi-terminal isolation)
- `P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md` — the 5-PR enhancement plan (read in full before starting)
- `~/.grok/skills/tp/SKILL.md` Mode 7 — the fabricated-causal-chain defense this enhancement partly motivates

## 11. Resumption protocol

For the next session:

1. **Read this handoff** in full.
2. **Read the plan** at `P:/docs/plans/exec-gate-preflight-enhancement-2026-07-20.md`.
3. **Confirm the 3 Open decisions** with the user (TTL table, composition rule strictness, preflight artifact location).
4. **Start with TP-1** (foundation; no dependencies).
5. **TP-2 in parallel** with TP-1 (independent).
6. **TP-3 after TP-1**; **TP-4 after TP-2 and TP-3**; **TP-5 last**.
7. **Run `pytest ~/.grok/plugins/exec-gate/tests/ -v`** at each PR boundary; do not merge with failing tests.

## 12. Suggested next invocation

```
Confirm the 3 open decisions on the exec-gate enhancement plan
(TTL table defaults, composition rule strictness, preflight artifact
location), then implement TP-1 (multi-class grant support) as the foundation.
PRs 2-5 follow per the dependency graph in §6.
```

## 13. Last user message (verbatim)

> "exec-gate enhancement (extend existing plugin with preflight integration)"

## 14. Explicit non-goals

- Do NOT port the cc-aca-* enforcement suite. That's a separate decision tracked elsewhere.
- Do NOT add new tool-gate mechanisms beyond the deny-by-default contract. The deny contract is canonical; don't reinvent it.
- Do NOT change the multi-terminal isolation invariants. Session-keyed state stays session-keyed.
- Do NOT modify `gate.py` exit codes. The existing codes (0 allow, 2 block, 1 error) are part of the verified contract.
- Do NOT add blocking on `~/.grok/plugins/exec-gate/scripts/state.py:120-140` corruption. Fail-closed by deletion is the contract.

## 15. Epistemic labels

- [FACT] Plan written and reviewed; PRs 1-5 defined with dependencies.
- [FACT] `~/.grok/plugins/exec-gate/scripts/gate.py` reads in full; deny-by-default + read-only allow-list confirmed.
- [FACT] `~/.grok/plugins/exec-gate/hooks/hooks.json` uses nested `hooks: [...]` array.
- [FACT] `spawn_subagent` already in matcher (hooks.json:3); design doc reviewer was wrong about this being missing.
- [INFERENCE] The proposed TTL table (auth=4h, docs=24h, production=1h, default=10min) is reasonable but unconfirmed.
- [INFERENCE] Strict composition rule is safer than lenient; lenient risks accidental privilege escalation.
- [UNKNOWN] Real production behavior under composition; no live-run data exists.
- [UNKNOWN] Whether the preflight-artifact branch interacts correctly with the existing TTL state.

1. Default TTL table — proposed: auth=4h, docs=24h, production=1h, default=10min. Confirm or adjust.
2. Composition rule strictness — strict (require explicit multi-class `/exec`) vs lenient (require higher-TTL class's grant).
3. Preflight artifact location — per-class files vs single file with per-class entries.

## 8. Other outstanding streams

- **yt-is fetch** — `P:/docs/handoffs/yt-is-fetch-resume-20260720/HANDOFF.md` — source-add failure unresolved. Separate workstream, no dependency on exec-gate.

