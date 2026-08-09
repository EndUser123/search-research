---
title: "Exec-gate plugin design rationale and reusable logic (retired 2026-07-22)"
created: 2026-07-22
source: session-2026-07-22
agent: grok
tags: [exec-gate, retired, design, reference, tests, state-machine, ttl-parser]
summary: >
  The exec-gate plugin was retired because its matcher-based approach over-blocked
  read-only bash commands. The design rationale, edge cases, state-machine logic, and
  test corpus are preserved here for any future revival (likely via bash-classify as
  a payload inspector rather than tool-name matcher). The plugin's UX gap (dialogue-
  mode-by-default, /exec release, TTL auto-expiry, session-keyed isolation) is real
  and not solved by Grok's native permission system.
cognitive_load: 4
---

## Summary

The plugin was retired because the PreToolUse matcher couldn't cleanly distinguish
`ls` from `rm -rf` — both go through `run_terminal_command`. The gap it targeted
(dialogue-mode-by-default + scoped release + auto-expiry + multi-terminal isolation)
is real and unfilled. This page preserves the hard-to-reconstruct logic for any
future attempt.

## Why retired (not "Grok already solved it")

**Correction to prior claims.** Grok's native permission system does NOT solve the
same problem. What Grok has:
- Read-only command auto-approval (overlaps with the plugin's read-only allowlist)
- Plan mode (structural edit rejection, but heavy workflow — plan file, approval flow)
- Permission rules (config-level mode switching, not quick toggle)

What Grok does NOT have (the gap the plugin tried to fill):
- A "dialogue mode by default" state — mutations blocked unless explicitly released
- A `/exec` slash-command UX for scoped authorization
- TTL-based auto-expiry back to blocked state
- Session-keyed isolation (terminal A's authorization doesn't leak to terminal B)

The gap is real. The implementation was wrong. Future revival should use a different
mechanism — most likely `bash-classify` as a payload inspector (see
[[read-only-vs-mutating-command-classification]]).

## Hard-to-reconstruct logic

### 1. Deny decision tree (gate.py `decide()`)

Five branches, each with a specific actionable reason string:

```
tool in READ_ONLY_TOOLS?
  → allow (defensive; matcher should already exclude)

flag_path(env) is None?  [GROK_SESSION_ID or GROK_PLUGIN_DATA missing]
  → deny: "Exec-gate: cannot read authorization state (GROK_SESSION_ID
           or GROK_PLUGIN_DATA unset)."

read_grant(path) == "CORRUPT"?  [file exists but unparseable JSON]
  → unlink the corrupt file (cleanup)
  → deny: "Exec-gate: authorization file is corrupt. Run /exec
           to re-authorize."

grant is None?  [file doesn't exist]
  → deny: "Exec-gate: dialogue mode active. Run /exec to authorize
           implementation work for this session."

now_iso() > grant["expires_at"]?  [TTL expired]
  → unlink the expired file (cleanup)
  → deny: "Exec-gate: authorization expired. Run /exec to re-authorize."

otherwise
  → allow
```

**Why this matters:** the reason strings are what the model sees when denied.
They must be actionable (tell the model what to do, not just what's wrong). The
5-branch tree covers every failure mode with a specific message — rewriting from
scratch means re-deriving what info the model needs to recover.

### 2. TTL parser (authorize.py `parse_ttl()`)

Accepts:
- `/exec` → 10 minutes (default)
- `/exec 30` → 30 minutes
- `/exec session` → 1440 minutes (24h; cleaned up by SessionEnd)
- `/exec 0` → None (reject: out of range)
- `/exec -5` → None (reject: negative)
- `/exec 9999` → None (reject: > 24h cap)
- `/execute` → None (reject: not exact match)
- `run /exec now` → None (reject: not exact match — must be entire prompt)

Regex: `^/exec(?:\s+(\d+|session))?\s*$`

**Why the exact-match requirement matters:** if `/exec` matched as a substring,
every prompt containing "/exec" would trigger authorization — including prompts
like "don't run /exec yet" or "what does /exec do?". The exact-match-on-entire-
prompt requirement prevents accidental authorization from conversational mentions.

### 3. State-file lifecycle (cleanup.py)

Three transitions:

- **SessionEnd:** remove `$GROK_PLUGIN_DATA/exec-grant-${GROK_SESSION_ID}`.
  Best-effort; missing file is not an error.
- **SessionStart orphan sweep:** glob `exec-grant-*` in plugin data dir; remove
  any file older than 4 hours (defensive — SessionEnd reliability is unverified
  in Grok 0.2.103).
- **Corrupt-flag cleanup (in gate.py):** if the flag file exists but is unparseable
  JSON, unlink it so the next `/exec` works cleanly.

**Why 4 hours?** Session duration upper bound for typical sessions. Short enough
that a crashed session's authorization doesn't persist indefinitely; long enough
that a legitimate long session doesn't get its flag swept mid-work.

### 4. Test corpus (21 tests)

The test file encodes edge cases that took real thought to enumerate. If revived,
start from this corpus:

**Deny/allow matrix:**
- `test_gate_denies_when_no_flag` — baseline: no flag → deny
- `test_gate_allows_when_valid_flag` — valid flag → allow
- `test_gate_denies_and_removes_expired_flag` — expired flag → deny + file removed
- `test_gate_allows_readonly_tools_without_flag` — read-only tools pass without flag
- `test_gate_denies_when_env_incomplete` — missing GROK_SESSION_ID → deny with NO_ENV reason
- `test_gate_denies_and_removes_corrupt_flag` — corrupt JSON → deny + file removed
- `test_gate_denies_run_terminal_command` — bash denied without flag
- `test_gate_denies_spawn_subagent` — subagent denied without flag
- `test_gate_different_sessions_isolated` — session A's flag doesn't authorize B

**TTL parser:**
- `test_parse_ttl_default` — `/exec` → 10
- `test_parse_ttl_custom_minutes` — `/exec 30` → 30, `/exec 1` → 1
- `test_parse_ttl_session` — `/exec session` → 1440
- `test_parse_ttl_rejects_non_exec` — other prompts → None
- `test_parse_ttl_rejects_out_of_range` — 0, -5, 9999 → None

**Grant writer:**
- `test_write_grant_creates_flag_file` — writes JSON with correct fields
- `test_write_grant_returns_none_on_missing_env` — no session ID → None

**Cleanup:**
- `test_remove_session_flag` — SessionEnd removes this session's flag
- `test_remove_session_flag_missing` — missing file → False (not error)
- `test_sweep_orphans_removes_old` — 5h-old file removed, recent file kept
- `test_sweep_orphans_empty_dir` — empty dir → 0 removed
- `test_sweep_orphans_no_dir` — nonexistent dir → 0 removed (not crash)

## What NOT to revive (the broken part)

**The tool-name matcher approach.** `"matcher": "search_replace|write|run_terminal_command|spawn_subagent"`
cannot distinguish `ls` from `rm -rf` because both go through `run_terminal_command`.
Any revival must inspect `toolInput.command` and classify it — via `bash-classify`
or equivalent AST parser. See [[read-only-vs-mutating-command-classification]].

## Related

- [[read-only-vs-mutating-command-classification]] — the three solutions analysis
- [[grok-pretooluse-deny-contract-verified]] — the mechanism verification (deny works)
- [[hook-failure-mode-taxonomy]] — why the matcher approach fails
- [[grok-per-hook-disable-layer-silent-suppression]] — why the plugin appeared not to fire
- multi-terminal-hook-state-isolation — the session-keyed flag-file pattern

## Auto-related

- [[exemption-logic-as-conflict-signal]]

## Sources

- `~/.grok/plugins/exec-gate/` (source archived to `P:/.data/evidence/exec-gate-retired-20260722/`)
- Session 2026-07-18 (original build)
- Session 2026-07-22 (retirement decision + this wiki page)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
