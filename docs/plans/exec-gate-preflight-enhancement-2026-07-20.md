# Enhancement Plan: exec-gate Preflight Integration

**Date:** 2026-07-20
**Status:** Draft for implementation
**Source:** `/go` run 2026-07-20, scoping out of the aborted `/design` run at `C:\Users\brsth\AppData\Local\Temp\grok-design-e961f614\`
**Owner:** operator (solo)
**Authority:** this plan supersedes the design doc at the temp path above; the design doc is stale once this plan ships

---

## 1. What exec-gate already does (verified)

Code read in full: `~/.grok/plugins/exec-gate/{README.md, hooks/hooks.json, scripts/{gate.py, authorize.py, cleanup.py}, tests/test_gate.py}`. All file:line references below are from this read.

### Architecture

| Component | Role | Source |
|---|---|---|
| `hooks/hooks.json` | Registers 4 hook events (PreToolUse, UserPromptSubmit, SessionStart, SessionEnd) | hooks.json:1-49 |
| `scripts/gate.py` | PreToolUse decision: deny mutating tools unless valid grant flag exists | gate.py:67-105 |
| `scripts/authorize.py` | UserPromptSubmit: detects `/exec [N|session]` and writes grant flag | authorize.py:60-78 |
| `scripts/cleanup.py` | SessionEnd removes this session's flag; SessionStart sweeps orphans >4h old | cleanup.py:22-55 |
| `tests/test_gate.py` | Unit tests covering decide/parse_ttl/write_grant/cleanup; 16 test functions | test_gate.py |

### Capabilities already implemented

1. **PreToolUse deny-by-default** on `search_replace`, `write`, `run_terminal_command`, `spawn_subagent` (hooks.json:3). Read-only tools always allowed (gate.py:27-37).
2. **Multi-terminal isolation via `GROK_SESSION_ID`.** Flag file is `exec-grant-<session-id>` (gate.py:48-54). Terminal A's grant cannot satisfy terminal B's gate. **Verified by test** `test_gate_different_sessions_isolated` (test_gate.py:118-123).
3. **TTL-based authorization.** `/exec` (10 min default), `/exec 30` (custom), `/exec session` (24h upper bound; SessionEnd cleanup is the real lifecycle bound) (authorize.py:14-28, 60-78).
4. **Hook JSON shape — already correct.** Uses the nested `{"matcher": "...", "hooks": [{"type": "command", "command": "...", "timeout": N}]}` form (hooks.json:5-13). This is the shape the design doc got wrong (review Issue 1).
5. **Corrupt-flag recovery.** If the grant file is unparseable, the gate deletes it and denies with a clear reason (gate.py:84-92). Tested by `test_gate_denies_and_removes_corrupt_flag`.
6. **Stale-flag cleanup.** Expired flags are deleted by the gate on access (gate.py:96-103). Orphan sweep handles sessions that didn't SessionEnd cleanly (cleanup.py:33-54).
7. **Deny reason is always actionable.** Every deny path includes the exact command to recover (`Run /exec to authorize...`, `Run /exec to re-authorize`, etc.).
8. **Stdin/stdout contract.** Reads JSON payload from stdin, writes `{"decision":"allow"|"deny","reason":"..."}` to stdout, exits 2 on deny / 0 on allow (gate.py:135-147).

### What's missing (the gap this plan closes)

| Gap | Impact |
|---|---|
| One flat TTL (10 min default, configurable per `/exec`) | Cannot express "auth-scope valid 4h, production-launch valid 1h" |
| Authorization is manual `/exec` only | Agent cannot earn authorization by producing a fresh `/preflight` artifact; every work session requires human `/exec` |
| No criticality classifier | Gate treats all mutating tools identically; cannot gate `python bin/csf-source fetch` harder than a typo fix |
| No composition detection | Cannot flag `auth + production` or lethal-trifecta combinations |
| Wiki concept page `grok-pretooluse-deny-contract-verified.md` referenced in README | **Does not exist** (verified via `Get-ChildItem -Recurse P:/.data/wiki -Filter "*pretooluse*"`). Citation is a dangling reference. |

---

## 2. Three missing features (extendability verified)

For each feature, I traced exec-gate's actual architecture to confirm clean extension. All three are cleanly extendable. No fundamental conflicts with the session-keyed state model.

### Feature A: Criticality-class TTLs

**Current state:** `authorize.py` writes a single `ttl_minutes` field in the grant (authorize.py:60-78). `gate.py` checks `expires_at` against now (gate.py:95-103). One TTL per session.

**Required change:** multiple concurrent grants, one per criticality class. Flag filename changes from `exec-grant-<sid>` to `exec-grant-<sid>-<class>`. Gate, given a tool call, computes the criticality class from the payload + criticality map (Feature C), then checks the matching class-specific grant.

**Default TTLs (from user direction 2026-07-20):**
- `auth` — 4h
- `docs` — 24h
- `production` — 1h
- `default` (mutation not matching any class) — 10 min (preserves current behavior)

**Extendability verdict:** clean. The flag-file pattern is per-session already; making it per-session-per-class is a filename change + a lookup change. Tests extend naturally (parameterize existing tests by class).

**Backward compat:** `/exec` (no args) writes the `default` class grant, preserving today's behavior. `/exec auth 4h` is the new shape.

### Feature B: Preflight-artifact integration

**Current state:** the only way to authorize is the human `/exec` command. The agent cannot earn authorization.

**Required change:** add a third authorization path. The gate accepts a fresh `/preflight` artifact as authorization for matching scope.

**Mechanism:** the gate looks for `preflight-<sid>-<class>.json` (or a single `preflight-<sid>.json` with per-class entries — design choice in implementation). If the artifact exists, is fresh (per-class TTL from Feature A), and its `scope_targets` overlap the tool call's scope, the gate allows.

**Bootstrap path:** the agent runs `/preflight --scope <X> --target <Y>` which invokes `discovery_audit.py`. That script currently writes to whatever `--output PATH` is specified. The enhancement adds a default output path under `$GROK_PLUGIN_DATA/preflight-<sid>-<class>.json` and stamps `generated_at`, `expires_at`, `terminal_id`, `session_id`, `scope_targets`. (These fields are confirmed missing from `discovery_audit.py`'s current schema — see evidence-brief.md "discovery_audit.py output schema" section.)

**Anti-circumvention:** the artifact is signed with the session ID and validated by the gate. The agent cannot forge it without already having write access (which the gate controls). The critical dependency is that the preflight invocation happens before the gate allows writes — the agent must run `/preflight` first, which is a read-only operation the gate already allows.

**Extendability verdict:** clean, with one caveat. The artifact path must be writable by `/preflight` and readable by the gate, both operating under the same `$GROK_PLUGIN_DATA`. The session-keyed model extends naturally.

**Caveat to flag:** `discovery_audit.py` currently doesn't write `session_id` or `expires_at`. The enhancement requires extending `discovery_audit.py`'s schema (a small change to `audit()` return dict, ~10 lines) — or wrapping it in a shell that adds those fields post-hoc. The cleaner path is extending the script.

### Feature C: Criticality map + composition detection

**Current state:** the gate has no concept of what kind of mutation is being attempted. All mutating tools are equivalent.

**Required change:** introduce a `criticality-map.json` at `$GROK_PLUGIN_ROOT/criticality-map.json` that classifies commands/paths into criticality classes. The gate reads the tool payload (specifically `toolInput.command` for Bash, `toolInput.file_path` for Edit/Write), matches against the map, and determines the class.

**Map schema (proposed):**

```json
{
  "classes": {
    "auth": {
      "ttl_minutes": 240,
      "matchers": [
        {"tool": "run_terminal_command", "pattern": "storage_state\\.json|nlm-auth|nlm_auth"},
        {"tool": "search_replace", "pattern": "csf/nlm_auth_check\\.py|csf/nlm_keepalive\\.py"}
      ]
    },
    "production": {
      "ttl_minutes": 60,
      "matchers": [
        {"tool": "run_terminal_command", "pattern": "bin/csf-source|bin/yt-is"}
      ]
    },
    "hooks": {
      "ttl_minutes": 240,
      "matchers": [
        {"tool": "search_replace", "pattern": "\\.grok/hooks/|\\.claude/hooks/"}
      ]
    },
    "docs": {
      "ttl_minutes": 1440,
      "matchers": [
        {"tool": "search_replace", "pattern": "\\.md$|docs/"}
      ]
    }
  },
  "default_class": {"ttl_minutes": 10},
  "composition_rules": [
    {"if_classes": ["auth", "production"], "require": "explicit_acknowledge"},
    {"if_classes": ["auth", "hooks"], "require": "explicit_acknowledge"}
  ]
}
```

**Composition detection (lethal-trifecta):** when a single tool call matches multiple classes (e.g., editing a file under `csf/nlm_auth_check.py` which is both `auth` and `production`), the gate requires an explicit `/exec <class1> <class2>` acknowledgement. Simple class matches use the per-class grant as before.

**Extendability verdict:** clean. The gate already has the payload; it just doesn't read `toolInput` fields. Adding the matcher logic is ~30 lines.

**Caveat to flag:** regex matching on `toolInput.command` is bypassable by command wrapping (review Issue 8 from the design-doc review). The mitigation is that critical paths are also gated at the file level via `search_replace` matchers — agents that try to bypass by writing to a new file and executing it still hit the `run_terminal_command` matcher on execution. Not perfect; document the residual risk.

---

## 3. Correct hook JSON shape (already correct in exec-gate)

The design doc got this wrong (flat shape); exec-gate already has it right. For reference, the correct shape for any new hooks added by this enhancement:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "search_replace|write|run_terminal_command|spawn_subagent",
        "hooks": [
          {
            "type": "command",
            "command": "python \"${GROK_PLUGIN_ROOT}/scripts/gate.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Key invariants (verified from `~/.grok/docs/user-guide/10-hooks.md:128-145`):
- Outer: event name (`PreToolUse`) → array of `{matcher, hooks: [...]}`
- Each hook entry: `{type: "command"|"http", command: "...", timeout: N}`
- `matcher` is regex applied to tool name
- Timeout default 5s; **all hook failures are fail-open**; only explicit `{"decision":"deny"}` blocks

**`spawn_subagent` already in matcher.** hooks.json:3 already includes it. The design doc's reviewer flagged this as a missing-matcher issue (review Issue 5); it was actually present in exec-gate but would have been missing in the new-from-scratch design.

---

## 4. PR plan

Five PRs, ordered by dependency. Each is independently mergeable and reviewable. No big-bang.

### PR 1: Multi-class grant flag support (Feature A foundation)

**Files:**
- `~/.grok/plugins/exec-gate/scripts/authorize.py` — extend `write_grant(env, ttl_minutes, class_name="default")` to write `exec-grant-<sid>-<class>`; update `/exec` parsing to accept `/exec <class> <ttl>` form
- `~/.grok/plugins/exec-gate/scripts/gate.py` — extend `flag_path` and `read_grant` to take `class_name`; gate looks up class based on (initially) the tool name only (Feature C adds the criticality map in PR 3)
- `~/.grok/plugins/exec-gate/scripts/cleanup.py` — sweep `exec-grant-<sid>-*` pattern
- `~/.grok/plugins/exec-gate/tests/test_gate.py` — add tests for multi-class grants

**Behavior:** `/exec` still works as today (writes `default` class). `/exec auth 4h` is new. `/exec production 1h` is new. Multiple concurrent grants allowed.

**Dependencies:** none. This is the foundation.

**Verify:** `pytest ~/.grok/plugins/exec-gate/tests/` passes including new tests; `/exec auth 4h` produces a class-specific grant file.

### PR 2: Extend discovery_audit.py schema (Feature B prerequisite)

**Files:**
- `P:/.agents/skills/preflight/scripts/discovery_audit.py` — extend `audit()` return dict to include `terminal_id`, `session_id`, `generated_at`, `expires_at` (computed from a new `--ttl-minutes` arg, default per-class or 60 min fallback)
- `P:/.agents/skills/preflight/scripts/discovery_audit.py` argparse — add `--terminal-id`, `--session-id`, `--ttl-minutes`, `--output-class` args
- `P:/.agents/skills/preflight/tests/test_discovery_audit.py` — add schema-field tests

**Behavior:** `discovery_audit.py` now writes the four new fields. Existing fields unchanged (backward compatible).

**Dependencies:** none (independent of exec-gate).

**Verify:** run preflight, confirm JSON output contains the new fields with correct values.

### PR 3: Criticality map + class lookup (Feature C)

**Files:**
- `~/.grok/plugins/exec-gate/criticality-map.json` — new file, schema per §2 Feature C above
- `~/.grok/plugins/exec-gate/scripts/gate.py` — load map at startup; classify tool call by reading `toolInput.command` / `toolInput.file_path` and matching against map; resolve to class name; check class-specific grant
- `~/.grok/plugins/exec-gate/scripts/authorize.py` — `/exec <class>` now means "authorize the named class," validated against the map
- `~/.grok/plugins/exec-gate/tests/test_gate.py` — add classification tests (one per matcher type + composition case)

**Behavior:** gate now classifies each call. Class lookup misses fall back to `default_class`. Composition (multi-class match) requires explicit multi-class `/exec`.

**Dependencies:** PR 1 (multi-class grants).

**Verify:** unit tests pass; manual test that `python bin/csf-source fetch` triggers `production` class without a grant and is denied with the actionable reason.

### PR 4: Preflight-artifact authorization path (Feature B)

**Files:**
- `~/.grok/plugins/exec-gate/scripts/gate.py` — add a preflight-artifact check before falling back to deny. Path: `$GROK_PLUGIN_DATA/preflight-<sid>-<class>.json`. Validate: file exists, JSON parses, `session_id` matches current session, `generated_at + ttl_minutes > now`, `scope_targets` overlap the current tool call's scope.
- `~/.grok/plugins/exec-gate/scripts/authorize.py` — no change (`/exec` is still the manual path)
- `~/.grok/plugins/exec-gate/README.md` — document that running `/preflight` is now an alternate authorization path
- `~/.grok/plugins/exec-gate/tests/test_gate.py` — add tests for preflight-artifact grants (valid, expired, wrong session, wrong scope)

**Behavior:** the agent can run `/preflight --scope <X> --target <Y>` (read-only, always allowed) to produce an artifact; subsequent tool calls in matching scope are authorized without manual `/exec`.

**Dependencies:** PR 2 (schema), PR 3 (class lookup).

**Verify:** unit tests pass; manual end-to-end: run preflight for a scope, then a matching mutation is allowed without `/exec`.

### PR 5: Documentation + dangling-citation fix

**Files:**
- `~/.grok/plugins/exec-gate/README.md` — update to reflect multi-class, preflight integration, criticality map; bump version to 0.2.0
- `~/.grok/plugins/exec-gate/plugin.json` — version bump
### File: `P:/.data/wiki/concepts/grok-pretooluse-deny-contract-verified.md` — **already exists** (recovered 2026-07-21)
The page was originally written 2026-07-19 in a worktree session but never synced to the canonical location. On 2026-07-21 it was recovered from the worktree copy at `~/.grok/worktrees/repo/subagent-019f7cbb-.../.data/wiki/concepts/` and promoted to `P:/.data/wiki/concepts/`. The companion page `grok-pretooluse-matcher-and-readonly-fastpath.md` was also promoted. Both are now canonical. PR 5 should verify both pages exist and are consistent with the exec-gate README's citations, not create them.
- `~/.grok/AGENTS.md` — add "Mandatory Preflight" section (this is Prompt 3, done separately but tracked here for completeness)

**Behavior:** docs match shipped behavior; dangling citation resolved.

**Dependencies:** PRs 1-4 (documents what shipped).

**Verify:** README's citation resolves; wiki page exists and is accurate.

---

## 5. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Regex-based command matching bypassable by wrapping | Medium | Document residual risk; also gate at file-write level so writing a new bypass script still hits `run_terminal_command` matcher on execution |
| Multi-class grants grow unbounded per session | Low | Cleanup.py sweep extended to `exec-grant-<sid>-*` pattern; SessionEnd removes all classes for the session |
| `/preflight` artifact forgery | Medium | Artifact must be under `$GROK_PLUGIN_DATA` which the agent doesn't have direct write access to outside the `/preflight` script; gate validates `session_id` matches |
| Criticality map maintenance burden | Low | Map is small (~5-10 classes initially); new packages add entries, not new schema |
| Fail-open on hook crash | Existing (from base exec-gate) | Already documented in exec-gate README; unchanged by this enhancement |

### From AAR session 019f821c (2026-07-21)

**AAR-OPP-006: Worktree-write detection (candidate for PR 5 scope).**
Wiki concept pages written from worktree subagent sessions land in the
worktree's local copy, not the canonical `P:/.data/wiki/concepts/` path.
This stranded the `grok-pretooluse-deny-contract-verified.md` page for 3
days (2026-07-19 to 2026-07-21). A SessionEnd hook could scan for writes
to `*/.data/wiki/concepts/*.md` from worktree-scoped sessions and warn if
those files don't exist at the canonical path. This fits PR 5's scope
(documentation + dangling-citation fixup) or could be a separate PR 6
if PR 5 is already large enough.

**AAR-OPP-005: Context firewall needs second-problem validation.**
The `/design` Step 0.5 context-firewall pattern worked at n=2 in session
019f821c (design doc authorship + /check verification). The circuit
breaker thresholds (soft ~3000 / hard ~8000 words) may need tuning for
different design task shapes. The next `/design` run on a different
problem should be observed to confirm the pattern generalizes. This is
not an exec-gate work item — it's a `/design` skill validation task.
Tracked here only because the AAR surfaced it and it would otherwise
be lost.

---

## 6. Open questions (need user input before PR 3)

1. **Default TTL table** — proposed: auth=4h, docs=24h, production=1h, default=10min. Confirm or adjust.
2. **Composition rule strictness** — when a call matches multiple classes, require explicit `/exec <class1> <class2>` (strict) or just require the higher-TTL class's grant (lenient)? Strict is safer; lenient is less friction.
3. **Preflight artifact location** — `$GROK_PLUGIN_DATA/preflight-<sid>-<class>.json` (per-class, parallel to grant flags) vs `$GROK_PLUGIN_DATA/preflight-<sid>.json` (single file with per-class entries). Per-class files are simpler to reason about; single file is fewer files.

---

## 7. Out of scope

- Replacing the existing exec-gate architecture (this plan extends it, not replaces)
- Building a parallel gate (rejected by reviewer Issue 2 — would duplicate working code)
- Anything related to the yt-is fetch itself (that's Prompt 4's scope)
- Migration of `P:/.claude/hooks/*.py` PreToolUse routers (those are off in this session per compat flag; separate concern)

---

## References

- `~/.grok/plugins/exec-gate/README.md` (existing plugin docs)
- `~/.grok/plugins/exec-gate/hooks/hooks.json` (correct hook JSON shape, verified)
- `~/.grok/plugins/exec-gate/scripts/{gate,authorize,cleanup}.py` (existing implementation)
- `~/.grok/plugins/exec-gate/tests/test_gate.py` (existing test coverage)
- `P:/.agents/skills/preflight/SKILL.md` (preflight skill contract)
- `P:/.agents/skills/preflight/scripts/discovery_audit.py` (artifact schema — needs extension per PR 2)
- `C:\Users\brsth\AppData\Local\Temp\grok-design-e961f614\evidence-brief.md` (lossless-maximal compaction of source-of-truth docs; this plan's claims about hook surface, schema gaps, and mandate wording trace to this brief)
- `C:\Users\brsth\AppData\Local\Temp\grok-design-e961f614\grok-design-review-e961f614.md` (reviewer findings Issues 1, 2, 5 directly motivated this plan's shape)
