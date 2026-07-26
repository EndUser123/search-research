---
thread_id: precommit-sibling-collision-hook-20260725
parent_handoff_path: none
current_session_id: 019f96f5-dc4a-79d0-9e17-396f2a582186
current_terminal_id: console_9f93f0d3-0b5b-4985-b779-6a2c
produced_at: 2026-07-26T01:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: beb1a58
---

# Handoff: pre-commit hook for sibling-session commit collision warning

## Objective

Implement a pre-commit hook that warns when about to commit files a sibling session has committed recently (within ~1 hour). Prevents silent overwrites and the "blindly overwrite" failure mode documented in `~/.grok/AGENTS.md` rule 3 (added this session).

## Why this matters

This session hit the commit-collision pattern **twice** (concurrent sessions committed v3 of a skill and a sibling wiki concept while this session was working on the same area). The current mitigation is behavioral (AGENTS.md rule 3: "check `git log` before staging overlapping files"). Behavior rules decay under closure pressure; structural enforcement (a hook) catches what the behavior misses.

## Scope

- **Trigger**: `pre-commit` hook fires on `git commit`
- **Check**: for each file in the staged set, `git log --since="1 hour ago" --name-only -- <file>`; if any commit by a different session (heuristic: commit message contains a session ID not matching the current one, or author timestamp within the window) touches the same file, warn
- **Action**: **warn, not block** (block would block legitimate fast-follow commits). The hook prints: "WARNING: file X was committed by session Y at <sha> <time> ago. Read that commit before proceeding? Re-run with --no-verify to bypass."
- **Bypass**: `git commit --no-verify` (standard pre-commit bypass)

## Alternatives considered

1. **Block instead of warn** — too aggressive; legitimate fast-follow commits would be blocked
2. **Check on `git add` (pre-add hook)** — git doesn't have pre-add hooks
3. **Modify AGENTS.md rule 3 to be stricter** — already as strict as prose can be; the issue is prose vs. structural enforcement
4. **Scanner-level check at `/close`** — wrong layer; collisions happen at commit time, not close time

## Acceptance criteria

- [ ] Pre-commit hook installed at `P:\.git\hooks\pre-commit` (and `~/.grok/.git/hooks/pre-commit` if applicable)
- [ ] Hook reads staged file list via `git diff --cached --name-only`
- [ ] Hook runs `git log --since="1 hour ago"` per file
- [ ] Hook identifies "different session" commits by parsing session IDs from commit messages (format: `(019f....)` suffix or session-id-in-message heuristic)
- [ ] Hook prints structured warning (not raw git output)
- [ ] `--no-verify` bypasses cleanly
- [ ] Hook does NOT block — exit 0 always (warn only)
- [ ] Test: simulate by committing a file in one terminal, then staging the same file in another within 1 hour
- [ ] Hook completes in <2s for typical staged sets

## Out of scope

- Cross-host collision detection (single-host only)
- Merge-conflict prevention (different problem; git already handles)
- Push-time collision detection (different layer; pre-push hooks are the wrong tool)

## Dependencies

- Requires: nothing
- Blocks: nothing
- Non-blocking to: other improvements

## Implementation sketch

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
set -euo pipefail
staged=$(git diff --cached --name-only)
[ -z "$staged" ] && exit 0
current_session="${GROK_SESSION_ID:-${CLAUDE_SESSION_ID:-unknown}}"
warnings=0
for f in $staged; do
    recent=$(git log --since="1 hour ago" --format="%H|%ci|%s" -- "$f" 2>/dev/null || true)
    if [ -n "$recent" ]; then
        while IFS='|' read -r sha when msg; do
            # Skip commits by the current session (heuristic: msg contains current session id)
            if echo "$msg" | grep -q "$current_session"; then continue; fi
            # Skip if the SHA IS the staged content (already committed in this session)
            warnings=$((warnings + 1))
            echo "⚠️  Sibling-session commit on $f:" >&2
            echo "   $sha ($when): $msg" >&2
        done <<< "$recent"
    fi
done
if [ $warnings -gt 0 ]; then
    echo "" >&2
    echo "Read those commits before proceeding. Bypass: git commit --no-verify" >&2
fi
exit 0  # warn, never block
```

(Operator: review the heuristic for "different session" — the commit-message-contains-session-ID convention may need to be tightened.)

## Related artifacts

- `~/.grok/AGENTS.md` rule 3 (added this session)
- Session 019f96f5 had 2 collision incidents (v3 commit + sibling wiki concept)
- Wiki concept: `causal-mechanism-claims-require-source-receipts-before-durable-write.md` (the receipt discipline this hook would structurally reinforce)

## Status

OPEN — ready for implementation
