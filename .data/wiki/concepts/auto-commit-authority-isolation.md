---
title: "Auto-commit authority isolation: concurrent-session fail-closed"
concept_type: "decision-analysis"
created: 2026-07-19
agent: grok
host: windows
verification: "web-research-backed"
cognitive_load: 3
---

# Auto-commit authority isolation: concurrent-session fail-closed

## Decision

Make auto-commit **fail-closed when another session is active on the same repo**, and **fail-open when the session is alone**. This satisfies three hard requirements:

1. **Multi-terminal isolation** — no session stages another session's work
2. **Stale-data immunity** — the concurrency check is fresh each Stop (reads the session registry at decision time, not a cached flag)
3. **No out-of-scope deletion** — the existing deletion-exclusion filter stays unchanged in both modes

## Mechanism

Add a concurrency check at the top of `auto_commit()` in `cc-skills-utils_Stop_auto_commit.py`:

```python
def _other_session_active(cwd: Path) -> bool:
    """Check the session registry for another session on the same repo path.
    Fresh read every Stop — no cached flag, immune to stale data."""
    try:
        registry_path = Path(os.environ.get("CLAUDE_PROJECT_DIR", cwd)) / ".claude" / ".artifacts" / "session_registry.jsonl"
        if not registry_path.exists():
            return False  # no registry → solo session
        my_session = os.environ.get("CLAUDE_SESSION_ID", "")
        my_terminal = os.environ.get("CLAUDE_TERMINAL_ID", os.environ.get("WT_SESSION", ""))
        now = time.time()
        TTL = 300  # 5-minute heartbeat window
        for line in registry_path.read_text(encoding="utf-8-sig").splitlines():
            entry = json.loads(line)
            if entry.get("session_id") == my_session:
                continue  # skip self
            if entry.get("cwd") and Path(entry["cwd"]).resolve() != cwd.resolve():
                continue  # different repo
            ts = entry.get("ts") or entry.get("started_at") or ""
            if ts:
                from datetime import datetime
                try:
                    entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                    if now - entry_time > TTL:
                        continue  # stale entry, skip
                except (ValueError, OSError):
                    continue
            return True  # found a live concurrent session
        return False
    except Exception:
        return False  # fail-open on any error — solo assumption
```

Then at the top of `auto_commit()`:

```python
def auto_commit(cwd, do_push=False, transcript_path=None, boundary=None):
    if not is_git_repo(cwd):
        return False
    # Fail-closed when concurrent sessions share this repo
    if boundary is None and _other_session_active(cwd):
        return False  # don't commit without ownership when others are active
    # ... existing code unchanged ...
```

## What this does

| Session state | Behavior | Why |
|---------------|----------|-----|
| Solo (no other session on same repo) | Auto-commit ON (current behavior) | Solo dev benefits from auto-save |
| Concurrent (another session detected on same repo) | Auto-commit OFF unless `/go` boundary is set | Prevents foreign capture of another session's work |
| In a worktree | Auto-commit ON (isolation is structural) | Worktree isolation makes collision impossible |
| `/go` boundary active | Auto-commit ON (explicit ownership) | The session explicitly declared what it owns |

## Why this satisfies the three requirements

### Multi-terminal isolation

When two sessions share `P:\`, both detect each other via the registry. Neither commits without `/go` ownership. The only way to get a commit through is:
- Use a worktree (structural isolation)
- Use `/go` with explicit file ownership (session declares what it owns)

Both paths are authority-bound. No whole-tree sweep is possible.

### Stale-data immunity

The check reads `session_registry.jsonl` fresh from disk every Stop. No cached flag. If session B exits, its last registry entry has a timestamp. Session A's next Stop reads the file, sees the entry is older than TTL (300s), skips it, and resumes solo auto-commit. No stale "another session is active" belief persists after the other session is gone.

### No out-of-scope deletion

The deletion-exclusion filter (`_get_changed_paths` skipping `D` status) runs unchanged in both modes. The concurrency check only decides whether to enter `auto_commit()` at all — it doesn't modify the staging path. When the check blocks, nothing runs. When it allows (solo or `/go`), the existing code runs byte-for-byte.

## Evidence supporting this approach

- *"Fail-closed is the responsible default for trust and long-term velocity. Silent failures or bad auto-actions cause far bigger productivity disasters than a pause-and-escalate."* — AI coding agent community (2026)
- *"Prefer warnings + fallback over hard blocks. Use fail-closed only for critical milestones."* — The critical milestone is "another session is active on the same repo"
- ADR-008 already provides the session registry infrastructure. This change reads it; it doesn't duplicate it.
- The existing `/go` boundary mechanism already provides the ownership path. This change makes it the *required* path when concurrent.

## Evidence against (and why it doesn't apply here)

- *"Fail-closed is too brittle for solo developers."* — True when applied unconditionally. This is conditional: fail-closed only when concurrent. Solo work is unaffected.
- *"Worktrees are the real fix."* — ADR-008 agrees and shipped Layer 1. But nothing enforces worktree usage today. This is the bridge until enforcement exists.
- *"The mtime fast-path already solves this."* — No. The mtime fast-path optimizes *when* to run. This fixes *what* to stage (or rather, when not to stage at all). They're complementary.

## Relationship to prior work

| Document | What it covers | Relationship to this |
|----------|---------------|---------------------|
| `auto_commit_mtime_fastpath_design.md` | Performance: skip auto-commit when index unchanged | Complementary — ships independently |
| `auto-commit-authority-isolation-handoff-2026-07-19.md` | Diagnosis + options 1-4 + task packets | This implements Option 2 (fail-closed) conditionally |
| ADR-008 | Worktree-per-session architecture | This is the bridge until ADR-008 enforcement ships |

## Implementation plan

1. Add `_other_session_active()` helper (~20 lines) to `cc-skills-utils_Stop_auto_commit.py`
2. Add the concurrency gate at the top of `auto_commit()` (3 lines)
3. Write tests: solo → commits; concurrent → no commit; concurrent exits → commits resume; worktree → commits; `/go` boundary → commits
4. Bump plugin version, rebuild cache
5. Ship

No changes to settings.json, router.py, or any other hook. One file, ~25 lines.

## Auto-related

- [[multi-terminal-git-coordination-primitives]]
- [[adr-epistemic-deliberation-architecture-20260711]]
- [[Deep-Research-with-Gemini-CLIimplementation]]

