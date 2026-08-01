---
title: "Reusable internals catalog — shared utilities across skills"
created: 2026-07-29
source: session-019fa276 (operator: "we have a predictable problem, let's fix it")
tags: [reusable-internals, shared-utilities, dedup, atomic-io, transcript-mining, ttl-cache, file-locking, skill-graph]
agent: grok
host: both
cognitive_load: 2
verification: observed
summary: >
  Catalog of functions that are genuinely reusable across skills, with path,
  signature, stability level, and which skills already use them. Before writing
  a new atomic-write function, TTL cache, file lock, or transcript scanner,
  check this catalog. The `P:/.agents/__lib/` directory is the canonical shared
  utilities location; `__lib/` directories inside individual skills hold
  skill-specific internals that other skills may import.
relations:
  - target: wiki/concepts/workspace-improvement-cycle-6-stage-decomposition.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Reusable internals catalog

## Decision context

**The problem:** the workspace has 990 skills. Multiple skills independently
implement the same utilities — atomic writes, file locking, transcript scanning,
TTL caching. Each reinvention is slightly different, untested in the new context,
and creates maintenance burden when the pattern needs updating. The operator
feels this pain daily.

**The fix:** document the reusable internals in each SKILL.md under a
`## Reusable internals` section (done for harvest, close, email-skill, fmea).
This catalog is the cross-skill index — a single page listing all shared
utilities so a future skill author can find them before writing a new one.

## Shared utilities at `P:/.agents/__lib/`

| Module | Functions | Stability | Used by |
|--------|-----------|-----------|---------|
| `atomic_io.py` | `atomic_write_only(path, content)`, `atomic_write_with_lock(lock, path, content, timeout=30)` | **stable** | email-skill, close (indirectly) |

**Import pattern:**
```python
import sys; sys.path.insert(0, "P:/.agents/__lib")
from atomic_io import atomic_write_only, atomic_write_with_lock
```

## Skill-internal reusable functions

### Atomic I/O + file locking

| Function | Path | What it does | Stability |
|----------|------|-------------|-----------|
| `atomic_write_only` | `P:/.agents/__lib/atomic_io.py` | tmp+fsync+os.replace (no lock) | **stable** |
| `atomic_write_with_lock` | `P:/.agents/__lib/atomic_io.py` | + cross-platform file lock (msvcrt/fcntl) | **stable** |
| `try_claim(parent_id, event_id)` | `~/.grok/skills/harvest/scripts/store.py` | O_CREAT\|O_EXCL parent-level claim | **stable** |
| `acquire_lock` / `release_lock` | `P:/.agents/skills/email-skill/scripts/email_skill_lib/cache.py` | Advisory lock with stale-lock (PID) detection | **stable** |

**Before writing a new atomic-write or locking function:** use `atomic_io.py`
from `__lib/`. If you need parent-level arbitration, study `try_claim()` from
harvest. If you need stale-lock recovery, use `acquire_lock()` from email-skill.

### TTL caching

| Function | Path | What it does | Stability |
|----------|------|-------------|-----------|
| `read_cache(ttl_seconds=900)` | `email_skill_lib/cache.py` | Read JSON cache with TTL expiry + lock | **stable** |
| `write_cache(data)` | `email_skill_lib/cache.py` | Write cache atomically with lock | **stable** |

**Before writing a new cache:** use `read_cache`/`write_cache` from email-skill.
They handle locking, stale-lock recovery, and TTL. Generalize the cache path
parameter if needed.

### Transcript mining

| Function | Path | What it does | Stability |
|----------|------|-------------|-----------|
| `scan_sessions(n, extract_obligations)` | `P:/.agents/scripts/analyze_session_patterns.py` | Walk N session transcripts for mechanical signals (9 types) + operator corrections. Writes to `pending/` for harvest. | **stable** |
| `scan_continuation_coverage(session, handoffs, retro, cfg)` | `~/.grok/skills/close/__lib/continuation_coverage.py` | Extract continuation candidates from session transcripts. | **stable** |
| `detect_friction(session_id)` | `~/.grok/skills/close/__lib/friction_detector.py` | Find recurring friction patterns. Returns candidates with prevention hints. | **stable** |
| `extract_user_messages(chat_file)` | `P:/.agents/scripts/analyze_session_patterns.py` | Extract user messages from JSONL transcript. | **stable** |
| `scan_raw_signals(file_path)` | `P:/.agents/scripts/analyze_session_patterns.py` | Scan JSONL/segment for 9 mechanical signal types. Returns counts + samples. | **stable** |

**Before writing a new transcript scanner:** use `scan_raw_signals()` from
analyze_session_patterns for mechanical signals. Use `detect_friction()` from
close for friction pattern detection. Use `scan_continuation_coverage()` for
goal/opportunity extraction.

### Workspace scanning

| Function | Path | What it does | Stability |
|----------|------|-------------|-----------|
| `scan_all(session_id, ...)` | `~/.grok/skills/close/__lib/close_accounting.py` | Run all 14 close gates. Returns Evidence. | **stable** |
| `scan_open_handoffs(chain, days)` | `~/.grok/skills/close/__lib/coverage_scan.py` | Lightweight frontmatter-only handoff scan (~3s). | **stable** |
| `scan_open_handoffs()` | `P:/.agents/scripts/workspace_opportunity_scan.py` | Scan handoffs for EXECUTE_OR_DEFER vs RESEARCH. | **stable** |

### AST analysis

| Function | Path | What it does | Stability |
|----------|------|-------------|-----------|
| `scan_file(filepath)` / `scan_pipeline(path)` | `P:/.agents/skills/fmea/scripts/fmea_scan.py` | AST-based I/O boundary detection + FMEA table generation. Cached by file mtime. | **stable** |
| `BoundaryVisitor(filepath)` | `P:/.agents/skills/fmea/scripts/fmea_scan.py` | AST visitor class — subclass to add custom boundary types. | **stable** |

## What NOT to reinvent

Before writing any of these, check the catalog:

1. **Atomic file writes** → `P:/.agents/__lib/atomic_io.py`
2. **File locking** → `email_skill_lib/cache.py` (`acquire_lock`/`release_lock`)
3. **TTL caching** → `email_skill_lib/cache.py` (`read_cache`/`write_cache`)
4. **Transcript scanning** → `P:/.agents/scripts/analyze_session_patterns.py`
5. **Handoff scanning** → `~/.grok/skills/close/__lib/coverage_scan.py`
6. **Friction detection** → `~/.grok/skills/close/__lib/friction_detector.py`
7. **AST boundary analysis** → `P:/.agents/skills/fmea/scripts/fmea_scan.py`
8. **Claim-based concurrency** → `~/.grok/skills/harvest/scripts/store.py`
9. **Event-sourced state** → `~/.grok/skills/harvest/scripts/store.py`
10. **Workspace opportunity scan** → `P:/.agents/scripts/workspace_opportunity_scan.py`

## Falsifier

This catalog is wrong if:
- Functions are listed as "stable" but their signatures change without notice
- The import patterns break when paths move
- New skills keep reinventing these utilities despite the catalog existing
  (catalog is write-only — nobody reads it)
- The catalog goes stale (functions removed but catalog not updated)

The last point is the real risk. This catalog should be maintained whenever a
function is added, removed, or its signature changes. The `## Reusable internals`
sections in individual SKILL.md files are the source of truth; this catalog is
the cross-skill index.

## Receipts

- `atomic_io.py`: inspected at `P:/.agents/__lib/atomic_io.py` lines 38-66 (`atomic_write_only`), lines 78-125 (`atomic_write_with_lock`)
- `try_claim`: inspected at `~/.grok/skills/harvest/scripts/store.py` lines 103-128
- `acquire_lock`/`release_lock`: inspected at `P:/.agents/skills/email-skill/scripts/email_skill_lib/cache.py` lines 157-250
- `scan_raw_signals`: inspected at `P:/.agents/scripts/analyze_session_patterns.py` (added this session, commit `efe8891`)
- `detect_friction`: at `~/.grok/skills/close/__lib/friction_detector.py` (used by /todo via `todo_format.py`)
- `scan_pipeline`: at `P:/.agents/skills/fmea/scripts/fmea_scan.py` (built this session, commit `05cb160`)

## Related

- [[workspace-improvement-cycle-6-stage-decomposition]] — the SENSE layer depends on reusing transcript scanners
- [[mechanical-enforcement-over-behavioral-reminder]] — shared utilities are mechanical enforcement
- [[shared-directory-contamination-pattern]] — the bug class that FMEA catches
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
