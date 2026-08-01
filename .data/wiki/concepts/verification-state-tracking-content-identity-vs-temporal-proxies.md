---
title: "Verification state tracking: content identity vs temporal proxies"
concept_type: "design-decision"
created: 2026-07-24
agent: grok
host: grok
verification: "web-research-backed"
sources:
  - https://github.com/affaan-m/everything-claude-code (content-hash-cache-pattern)
  - https://github.com/Dicklesworthstone/coding_agent_session_search (BLAKE3 dedup + state tracking)
  - https://www.danmercede.online/ (per-file hash lockfile pattern)
  - Bazel action cache keys (content-addressable build verification)
  - rsync checksum-based sync (block-level change detection)
cognitive_load: 2
---

# Verification state tracking: content identity vs temporal proxies

## Decision context

**Problem:** Our quality-gate Stop hook tracks whether the agent's verification
(pytest, etc.) covers the current file state. The current implementation uses
three temporal proxies: (1) an incremental scan window (new transcript lines
since last Stop), (2) an order-based latch (`code_modified_after_verification`),
and (3) a time-window check (`stale_by_time`: nudge timestamps >10 min old).
All three produce false positives under normal workflows (edit→test→commit,
long prose after test, wiki edits). We needed to know the optimal approach.

**What alternatives were explored:**
- Time-window-only (current `stale_by_time`): false positives on any turn >10 min
- Order-based latch (current `code_modified_after_verification`): false positives on edit→test→edit→test
- Scan-window-scoped flags: loses state across windows (empty window after test window)
- Content hashing: **selected** — measures the actual invariant

## The optimal approach: content-addressable verification

**Replace all temporal proxies with a single content-identity check.**

### How it works

1. At PostToolUse (search_replace/write): hash the modified file, store hash in nudge state
2. At the next verification command (pytest, etc.): record the set of file hashes that existed when verification ran
3. At Stop hook: re-hash each modified file. If current hash == verified hash for all files → verification is valid
4. If any hash differs → verification is stale

### Why this is optimal (evidence from adjacent domains)

| Domain | What they use | Why they abandoned timestamps |
|--------|--------------|------------------------------|
| **Build systems** (Bazel, Buck) | Content-addressable action cache keys | mtime changes don't mean content changed; rebuilds were wasted |
| **File sync** (rsync, syncthing) | Block-level checksums | mtime is unreliable across filesystems, NFS, git operations |
| **CI/CD cache invalidation** | Hash of input files as cache key | Timestamp-based cache misses were too frequent |
| **Database replication** | LSN/WAL positions, not wall clock | Temporal ordering breaks under clock skew |
| **Content dedup** (BLAKE3 in coding_agent_session_search) | Content hash of (role + content + timestamp) | Dedup by content, not by when it happened |

**Every domain that faced "is this state still valid?" abandoned temporal
proxies in favor of content identity.** The pattern is universal because
timestamps, ordering latches, and time windows are all *proxies* for the
actual invariant: "has the content changed?"

### Why the scan window is the wrong abstraction

The scan window (incremental transcript lines since last Stop) is a
*performance optimization* for transcript scanning — it avoids re-reading
the full transcript. That's legitimate and should stay for the transcript
scan itself.

But using the scan window as a *verification scope* is wrong. Verification
validity is not "did verification happen in the last N lines." It's "does
the current file content match what was on disk when verification ran."
Those are different questions, and the scan window answers the wrong one.

### Performance cost

- File hash: ~74ms per file (SHA-256, measured on this host)
- 5 modified files: ~370ms total
- Against 60s hook timeout and 5s+ pytest runtime: negligible

### Implementation

Replace `stale_by_time`, `code_modified_after_verification`, and the
scan-window-scoped verification flags with:

```python
# At PostToolUse (quality_nudge.py):
entry = {
    "file": file_path,
    "file_hash": _hash_file(file_path),  # NEW
    "modified_at": time.time(),  # keep for hints, not for staleness
}

# At verification command time (quality_gate.py transcript scan):
verified_hashes = {}  # {file_path: hash_at_verification_time}
# When a verification command is found, snapshot all modified files' hashes

# At Stop hook decision:
current_hash = _hash_file(fp)
if current_hash == verified_hashes.get(fp):
    # File unchanged since verification — receipt valid
    pass
else:
    # File changed since verification — stale
    block()
```

### What to keep from the current design

- **Nudge state entries** — still useful for file-hint messages ("run pytest on these files")
- **Scan window for transcript scanning** — legitimate performance optimization
- **`verification_ran` flag** — still needed to detect "no verification at all"
- **Claim detection** — unchanged

### What to remove

- `code_modified_after_verification` (order latch)
- `_is_verification_stale()` / `stale_by_time` (time window)
- `VERIFICATION_MAX_AGE_SECONDS` (time threshold)

## Related wiki concepts

- [[quality-gate-hook-system-implementation]] — the hook system this applies to
- [[mandatory-step-enforcement-code-over-prose]] — the enforcement principle
- [[mutation-receipt-patterns-for-ai-agent-file-ownership]] — complementary hash-based pattern
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
