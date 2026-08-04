---
title: "Multi-terminal isolation and stale-data immunity: baseline requirements for shared-filesystem hooks"
concept_type: "architecture-decision"
created: 2026-08-04
agent: grok
host: both
tags: [multi-agent, concurrency, session-isolation, stale-data, hooks, quality-gates, shared-filesystem]
summary: >
  This workspace runs multiple AI agent sessions concurrently on a shared Windows
  filesystem (P:\). Any hook, scanner, or enforcement mechanism that reads or
  writes shared state must be designed for multi-terminal isolation (sessions
  must not interfere with each other) and stale-data immunity (sessions must not
  act on data another session changed underneath them). These are baseline
  requirements, not optional features. The quality gates system's cross-session
  evidence contamination bug (found 2026-08-04, fixed same day) is a case study
  in what happens when a new mechanism inherits a shared-filesystem pattern
  (glob matching) without inheriting the session-scoping that the existing
  mechanisms already have.
cognitive_load: 3
verification: multi-source-verified
---

# Multi-terminal isolation and stale-data immunity

## The baseline requirement

**Every mechanism that touches shared filesystem state on this host must
answer two questions:**

1. **Multi-terminal isolation:** can two sessions running simultaneously
   interfere with each other's state, evidence, or enforcement?

2. **Stale-data immunity:** can a session act on data that another session
   has changed since the first session last read it?

If the answer to either is "yes" or "I didn't check," the mechanism is
unsafe for this workspace. These are not edge cases — this host regularly
runs 3-8 concurrent sessions across multiple terminals, all reading and
writing to the same `P:\` and `~/.grok` trees.

## What the workspace already does

The existing enforcement mechanisms (quality_gate.py receipts,
close_accounting.py, close_authority.py) already solve these problems
correctly:

### Session-scoped state directories

Receipts and state files use per-session directories keyed by session_id:

```
~/.grok/hooks/state/quality-receipts-<session_id>/*.json
~/.grok/hooks/state/quality-gate-<session_id>.json
~/.grok/hooks/state/quality-obligation-<session_id>.json
P:/.artifacts/close-evidence/<session_id>.json
```

Each file contains an internal `session_id` field that is validated on read
(`quality_gate.py:447`: `if r.get("session_id") != session_id: continue`).
A foreign session's state file is rejected even if it ends up in the
right directory.

### Content-based session filtering

`close_accounting.py:scan_check_receipts()` (line 541+) finds all
`check-run.json` files under `.artifacts/`, then parses each one and
filters by `manifest.get("session_id") != session_id` (lines 619-622).
Only evidence from the current session satisfies the scanner.

### Atomic writes

State files use tmp + `os.replace()` for atomic writes
(`quality_gate.py:482-488`, `quality_gates_frontmatter.py:write_waiver()`).
Concurrent writers don't corrupt each other's state.

### Mtime-based staleness detection

`PreToolUse_skill_staleness.py` tracks per-session mtime caches for
SKILL.md files. If another session edits a file, the mtime changes and
the next read surfaces a warning. `UserPromptSubmit_quota_availability.py`
uses `(mtime, size)` tuple comparison for the same purpose.

## Case study: the quality gates contamination bug (2026-08-04)

### What happened

The quality gates system (built this session) used `glob.glob()` to check
whether evidence artifacts exist:

```python
# quality_gates_frontmatter.py:check_evidence() — ORIGINAL (BUGGY)
matches = glob.glob("P:/.artifacts/**/check-run.json", recursive=True)
```

This matched ANY session's `check-run.json` anywhere under `.artifacts/`.
On a multi-agent host, Session B invoking `/ship` could satisfy its
quality gate using Session A's evidence — passing enforcement without
actually running `/check`.

### Root cause

The glob pattern inherited the workspace's shared-directory convention
(`P:/.artifacts/`) without inheriting the session-scoping that every
existing mechanism applies. The artifact directory layout uses terminal
IDs (`console_<uuid>`, `noterm`), not session IDs — so path-based
`{session_id}` substitution would produce zero matches (worse than the
bug). Session IDs live in file *content*, not file paths.

### The fix

Content-based session scoping for JSON evidence files, borrowing the
pattern from `close_accounting.py:619-622`:

```python
# quality_gates_frontmatter.py:check_evidence() — FIXED
if session_id and session_field:
    session_matches = []
    for m in matches:
        if not m.lower().endswith(".json"):
            session_matches.append(m)  # non-JSON: can't filter, passthrough
            continue
        try:
            data = json.loads(Path(m).read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get(session_field) == session_id:
                session_matches.append(m)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue  # corrupt file: skip
    matches = session_matches if session_matches else []
```

Gates declare which content field to filter on in frontmatter:

```yaml
quality_gates:
  - evidence: "P:/.artifacts/**/check-run.json"
    session_field: "session_id"   # filter by content field
  - evidence: "P:/.artifacts/**/FINDINGS.md"
    # no session_field — markdown can't be content-filtered (documented limitation)
```

### Known limitation

Markdown and plaintext evidence (e.g., `FINDINGS.md`) cannot use
content-based session scoping because they have no structured session
binding. This is a documented limitation. The evidence passes through
unscooped — any session's FINDINGS.md satisfies the gate. A future
improvement could embed a session header in /review's output format,
enabling content-based filtering for markdown artifacts.

## Design checklist for new shared-state mechanisms

Before shipping any hook, scanner, or enforcement mechanism that reads
or writes shared filesystem state:

1. **Per-session state files:** use `<mechanism>-<session_id>.json` naming.
   Internal `session_id` field validated on read.

2. **Content-based session filtering:** when matching evidence artifacts
   across sessions, parse JSON content and filter by `session_id` field.
   Do NOT rely on path-based session scoping unless the directory layout
   is confirmed to use session IDs (it doesn't on this host — it uses
   terminal IDs).

3. **Atomic writes:** use tmp + `os.replace()`. Never append-and-pray
   to shared state files.

4. **Mtime staleness check:** when caching filesystem state, store
   `(mtime, size)` tuples. If either changed, invalidate the cache.

5. **Fail-open on errors, fail-closed on forgery:** broken state files
   should not crash the hook (fail-open, exit 0). Forged or mismatched
   session bindings should block (fail-closed, exit 0 with block message).

6. **Non-JSON evidence:** document that markdown/plaintext evidence cannot
   be session-scoped via content. Either accept the limitation explicitly
   or embed session metadata in the output format.

## How to test for contamination

The test pattern from `test_quality_gates_frontmatter.py`:

```python
def test_rejects_glob_match_from_wrong_session(self):
    """The contamination bug: glob matches another session's file."""
    with tempfile.TemporaryDirectory() as tmp:
        # Session A's file
        file_a = Path(tmp) / "run-A" / "check-run.json"
        _make_evidence_file(file_a, json.dumps({"session_id": "session-A"}))

        # Session B's file
        file_b = Path(tmp) / "run-B" / "check-run.json"
        _make_evidence_file(file_b, json.dumps({"session_id": "session-B"}))

        pattern = f"{tmp}/**/check-run.json"

        # Session B finds its own file
        found_b, _, _ = qg.check_evidence(pattern, session_id="session-B", ...)
        assert found_b is True

        # Session C (no file) finds nothing
        found_c, _, _ = qg.check_evidence(pattern, session_id="session-C", ...)
        assert found_c is False
```

Every new evidence-matching mechanism should have this test shape: two
sessions' artifacts on disk, verify each session only sees its own.

## Related concepts

- [[auto-commit-authority-isolation]] — concurrent-session fail-closed for git auto-commit
- [[concurrent-cdp-auth-contention]] — multi-terminal auth isolation for browser state
- [[inference-chains-bare-numbers-destructive-write]] — destructive-write preflight requirements
- AGENTS.md § "Claims require receipts; narrative sufficiency is not verification" — the broader receipt discipline

## Falsifier

This baseline requirement is wrong if:

- The workspace moves to per-session isolated filesystems (each session
  gets its own `P:\` tree). Then shared-state isolation is structural and
  the checklist is unnecessary overhead.
- Session IDs become embedded in artifact directory paths (e.g.,
  `P:/.artifacts/<session_id>/...`), making path-based session scoping
  viable. Then content-based filtering becomes redundant.
- The workspace drops to single-session operation. Then concurrent-state
  hazards don't exist in practice (though the design should still be
  safe for the occasional second session).

None of these are true today. The baseline holds.
