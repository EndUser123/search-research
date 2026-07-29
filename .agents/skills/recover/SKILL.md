---
name: recover
description: >
  Recover deleted, overwritten, or missing files using git history, session
  transcripts, and checkpoint snapshots. Use when a file is missing after
  concurrent agent activity, accidentally deleted, or overwritten. Adapted
  from Claude-side "recover" for Grok Build (session transcripts at
  ~/.grok/sessions/, not ~/.claude/projects/).
host: both
provides: [file-recovery]
domain: fleet-ops
---

# /recover — File recovery for multi-agent shared filesystems

Recover deleted, overwritten, or missing files using multiple fallback
sources: **git history**, **session transcripts**, and **file-history
snapshots**. Designed for the multi-agent shared filesystem at `P:\`
where concurrent sessions can silently overwrite each other's work.

## When to use

- File is missing after a concurrent agent session
- "Where did X go?" / "file was deleted" / "restore X"
- File content changed unexpectedly (overwrite by another session)
- `edit-then-verify` protocol detected a vanished write

## Recovery sources (priority order)

### 1. Git (fastest, most reliable)
```bash
git -C "P:/" log --all --full-history -- <file_path>  # Find commits touching file
git -C "P:/" show <commit>:<file_path>               # Preview content at commit
git -C "P:/" restore --source=<commit> <file_path>   # Restore (P:/ repo only)
```
**When:** file was ever committed to git at `P:\`. Works for deleted AND modified files.

For `~/.grok/` files:
```bash
git -C "$env:USERPROFILE/.grok" log --all --oneline -- <relative_path>
git -C "$env:USERPROFILE/.grok" show HEAD~1:<relative_path>
```

### 2. Grok session transcripts (for untracked files)

Grok Build stores session transcripts at `~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl`.

```python
import json, os, glob

target_path = "P:/path/to/missing/file.py"
sessions_dir = os.path.expanduser("~/.grok/sessions")

# Find recent sessions
for session_dir in sorted(glob.glob(f"{sessions_dir}/*/*"), key=os.path.getmtime, reverse=True)[:10]:
    chat_file = os.path.join(session_dir, "chat_history.jsonl")
    if not os.path.exists(chat_file):
        continue
    with open(chat_file, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                # Look for Write/Edit/search_replace tool calls with matching file_path
                content = str(event.get("message", {}).get("content", ""))
                if target_path.lower() in content.lower() and ("write" in content.lower() or "search_replace" in content.lower()):
                    print(f"Found in {chat_file}")
                    # Extract the content from the tool call
            except (json.JSONDecodeError, KeyError):
                pass
```

**When:** file was written by an LLM tool call in a prior session but never committed to git. This is the most common recovery case on multi-agent filesystems.

### 3. Compaction segments (for pre-compaction content)

If the session has compacted, pre-compaction content lives in:
```
~/.grok/sessions/<encoded-cwd>/<session-id>/compaction/segment_NNN.md
```

These are frozen transcript chunks. Search them for file paths and Write/Edit operations.

### 4. `.tmp` staging files

The `edit-then-verify` protocol writes `.tmp` files before `os.replace`. If a write failed mid-operation, the `.tmp` file may still exist:
```bash
Get-ChildItem -Path "P:/" -Recurse -Filter "*.tmp" -ErrorAction SilentlyContinue
```

## Recovery workflow

### Phase 1: Identify the target
- Get file path from operator or from session context
- Check if the path currently exists: `Test-Path <path>`
- Note the expected content (what should be there)

### Phase 2: Try git first (always)
- Search git history for the file
- If found, preview the most recent version
- If the file was committed, this is the recovery — done

### Phase 3: Search session transcripts
- Scan recent session `chat_history.jsonl` files for Write/Edit/search_replace calls targeting the file
- Extract the content from the most recent tool call
- If found, this is the recovery source

### Phase 4: Check compaction segments
- If the session has compacted, search segment files
- These contain the full pre-compaction transcript including tool calls

### Phase 5: Present options + restore
```
RECOVERY OPTIONS for <filename>:

1. Git restore from <commit> (<date>)
   Source: git log commit <hash>
   Preview: <first 3 lines>

2. Transcript from session <id> (<date>)
   Source: search_replace tool call
   Content length: N chars

3. Compaction segment <NNN> (<date>)
   Source: pre-compaction transcript
   Content length: N chars

Choose option [1-3] or skip:
```

## Grok Build differences from Claude Code

| Aspect | Claude Code | Grok Build |
|---|---|---|
| Session transcripts | `~/.claude/projects/` | `~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl` |
| File history | `~/.claude/file-history/` | None (use git + transcripts) |
| Checkpoints | `/rewind` built-in | None |
| Tool names in transcripts | `Write`, `Edit` | `write`, `search_replace` |
| Compaction | `~/.claude/compaction/` | `~/.grok/sessions/.../compaction/segment_NNN.md` |

## Prevention (complementary)

The `edit-then-verify` protocol in AGENTS.md is the primary prevention:
write `.tmp` → verify → `os.replace`. For tracked files, auto-commit after
verification (per AGENTS.md "Working in the shared main tree" rule).

`/recover` is the fallback when prevention fails — which it does on
multi-agent filesystems where concurrent sessions can collide.

## References

- AGENTS.md § "File editing protocol" — the prevention layer
- `wiki/concepts/notebooklm-cli-operational-gotchas.md` — "vanishing writes" documented as UNKNOWN root cause
- Adapted from Claude-side `recover` skill (cc-skills-utils)
