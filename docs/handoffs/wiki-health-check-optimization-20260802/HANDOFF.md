---
title: "Optimize wiki_health_check.py: 62s runtime from double-read + sequential I/O"
created: 2026-08-02
source: session-019fc303
status: OPEN
yaml_status: open
assignee: unassigned
session: 019fc303-700f-7711-b376-12da1aff578a
tags: [performance, wiki, optimization, pipeline]
---

# Optimize wiki_health_check.py: 62s runtime from double-read + sequential I/O

## Objective

Reduce `wiki_health_check.py` runtime from ~62s to <15s by eliminating double-read and parallelizing file I/O.

## Context

During session 019fc303, `/maintain` pre-flight testing revealed that `wiki_health_check.py` takes ~62 seconds to run. The script lives at:

```
P:/packages/.claude-marketplace/plugins/cc-skills-utils/skills/main/scripts/wiki_health_check.py
```

It is called by `/maintain` Step 1 (DIAGNOSE) and `/workspace-health` checks. At 62s, it dominates the DIAGNOSE phase.

## Root cause analysis

| Bottleneck | Lines | Impact |
|---|---|---|
| **Double-read**: frontmatter pass (lines 110-115) and link extraction pass (lines 128-129) each call `read_text()` separately on the same files | `run_check()` | ~2x wasted I/O |
| **Sequential I/O**: no threading — 300+ files read one at a time | entire `run_check()` | Windows NTFS small-file reads ~5-10ms each × 600 reads |
| **Regex on every file**: `LINK_RE.findall(text)` scans full content | line 131 | CPU-bound, minor vs I/O |

## Three optimization options (effort vs payoff)

### Option 1: Single-pass read (S effort, ~2x speedup)

Combine frontmatter + link extraction in one `read_text()` call per file. Instead of:

```python
# Current: two passes
for path in md_files:
    frontmatter[stem] = _parse_frontmatter(path.read_text(...))
for stem, path in pages.items():
    text = path.read_text(...)
    # extract links
```

Do:

```python
# Optimized: one pass
for path in md_files:
    text = path.read_text(...)
    frontmatter[stem] = _parse_frontmatter(text)
    # extract links from same text
```

**Risk:** none — pure refactor, same logic.
**Expected:** 62s → ~30s.

### Option 2: ThreadPoolExecutor parallel I/O (M effort, ~4-6x speedup)

Use `concurrent.futures.ThreadPoolExecutor` to read files in parallel (I/O-bound, threads work well):

```python
from concurrent.futures import ThreadPoolExecutor

def read_and_parse(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    return path.stem, text, _parse_frontmatter(text), path.stat().st_mtime

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(read_and_parse, md_files))
```

**Risk:** low — threads for file I/O is well-established. Need to verify thread safety of `_parse_frontmatter` (it's pure parsing, should be fine).
**Expected:** 62s → ~10-15s.

### Option 3: Mtime-based cache (M-L effort, ~10x+ on repeat runs)

Cache the graph to a JSON file. Only re-read files whose mtime changed since last run. On repeat runs with few changes, runtime drops to <5s.

```python
cache_path = vault / "_state" / "health_cache.json"
# Load cache, filter to changed files, re-read only those, merge
```

**Risk:** medium — cache invalidation bugs; stale results if mtime lies (rare on NTFS but possible with rapid successive edits).
**Expected:** 62s → <5s on repeat runs (first run same as Option 2).

## Recommended approach

Implement Option 1 first (immediate 2x, zero risk), then Option 2 (parallel I/O). Option 3 only if 10-15s is still too slow.

## Implementation constraint

The script lives in the `cc-skills-utils` plugin source tree. Two options:
- **Patch the plugin directly** — changes take effect immediately but may be overwritten if the plugin is reinstalled from the marketplace
- **Wrapper script** — write a parallel version at `P:/.data/wiki/scripts/wiki_health_check_fast.py` that delegates to the original for `--fix` mode but uses the optimized engine for default/`--json` mode

The wrapper approach is safer for a marketplace-sourced script.

## Acceptance criteria

- [ ] `wiki_health_check.py --json` completes in <15s (down from 62s)
- [ ] Output shape unchanged (same JSON structure consumed by `/maintain` and `/workspace-health`)
- [ ] No test regressions in existing wiki tests
