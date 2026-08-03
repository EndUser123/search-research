# Codegraph Scope Definition

**Date:** 2026-08-03
**Phase:** 2 (Tree-sitter scope definition)
**Status:** COMPLETE — decision recorded
**Measurement script:** `P:/tmp/codegraph_scope_measure.py`
**Raw results:** `P:/tmp/codegraph_scope_results.json`

---

## Decision

**Global single graph.** Both abandonment criteria pass with wide margin:

| Criterion | Threshold | Measured | Margin |
|-----------|-----------|----------|--------|
| Filtered file count | < 50,000 | **6,402** | 87% headroom |
| Cold build time | < 300s | **58.73s** | 80% headroom |

A per-package on-demand graph is unnecessary at this scale. The full workspace parses in under a minute with zero errors.

---

## ROOT_SCOPES

Directories containing operator-authored source code:

| Root | Files kept | Files excluded | Description |
|------|-----------|----------------|-------------|
| `P:/packages/.claude-marketplace/plugins` | 2,687 | 5,119 | Plugin source (canonical) |
| `P:/projects` | 1,979 | 66 | Project code |
| `P:/.claude/hooks` | 1,149 | 2 | Hook scripts |
| `P:/packages/yt-is` | 190 | 0 | YouTube ingestion package |
| `P:/.agents` | 213 | 0 | Agent scripts and skills |
| `P:/.claude/tests` | 108 | 0 | Hook tests |
| `P:/packages/research_runtime` | 35 | 0 | Research runtime |
| `P:/.grok/skills` | 25 | 0 | Grok skills (Python portions) |
| `P:/.claude/scripts` | 10 | 0 | Maintenance scripts |
| `P:/packages/installers` | 4 | 0 | Fleet installers |
| `P:/packages/wiki-search-fts5` | 2 | 0 | Wiki search |
| **Total** | **6,402** | **5,187** | |

---

## Filter exclusions

Directory names excluded from the walk (matched against any path component):

`__pycache__`, `.venv`, `venv`, `site-packages`, `node_modules`, `.tox`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.git`, `.speckit`, `*.egg-info`

### Directories excluded entirely (not in ROOT_SCOPES)

These top-level directories contain only vendored/duplicate/temporary code:

| Excluded directory | .py files | Reason |
|--------------------|-----------|--------|
| `P:/packages/tts-reader/` | 13,408 | Vendored TTS package |
| `P:/packages/.github_repos/` | 10,606 | Cloned external repos |
| `P:/.claude/worktrees/` | 27,520 | Git worktrees (duplicate copies) |
| `P:/.worktrees/` | 8,969 | Top-level worktrees |
| `P:/.venv/` | 6,857 | Virtual environment |
| `P:/.claude/.venv/` | 1,156 | Nested virtual environment |
| `P:/tmp/` | 176 | Temporary scripts |

Excluding these removes ~68,000 files from consideration. The remaining 6,402 files represent the actual operator-authored codebase.

### Key finding: plugins/ is 66% vendored

The PoC (session 019fc0a7) reported 7,806 .py files under `plugins/` excluding `__pycache__`. The expanded filter (also excluding `site-packages`, `node_modules`, `.venv`, etc.) reveals that only **2,687** of those are operator source. The remaining **5,119** are vendored dependencies shipped inside plugin directories. This means the real source footprint is 3× smaller than the PoC suggested.

---

## Build benchmark

| Metric | Value |
|--------|-------|
| Files parsed | 6,402 |
| Function definitions | 63,258 |
| Call sites | 400,130 |
| Parse errors | 0 |
| **Cold build time** | **58.73s** |
| Parse rate | 109 files/s |

The cold build is dominated by file I/O (6,402 small files across 11 roots). The PoC's warm-cache rate was 640–880 files/s; the production graph should expect ~10s warm builds.

Build rate held steady at 101–109 files/s across all 6 checkpoints (every 1,000 files), confirming no degradation as the walker crosses root boundaries.

---

## Comparison to PoC (session 019fc0a7)

| Metric | PoC (plugins/ only, excl `__pycache__`) | Phase 2 (all roots, full exclusions) |
|--------|-----------------------------------------|--------------------------------------|
| Files scanned | 7,806 | 6,402 |
| Function defs | 70,783 | 63,258 |
| Call sites | 605,936 | 400,130 |
| Cold build | 61.70s | 58.73s |
| Parse errors | 0 | 0 |

The Phase 2 scan covers more roots but fewer total files because the expanded filter excludes vendored dependencies the PoC included. The lower def/call counts reflect the removal of non-operator code.

---

## Implications for Phase 3

The production graph should:

1. **Use a single global index** — no per-package sharding needed at 6,402 files.
2. **Apply the same ROOT_SCOPES and EXCLUDED_DIRS** defined here.
3. **Expect ~60s cold builds, ~10s warm** — the SessionStart staleness hook (Phase 3) should trigger an async rebuild, not block session start.
4. **Estimate ~150 MB in-memory** (scaling from PoC's ~190 MB at 606K call sites → ~100 MB at 400K call sites, minus the forward index the red-team recommended dropping).
5. **Cache path:** `P:/tmp/codegraph/` (gitignored).

---

## Acceptance criteria status

- [x] Scope doc exists with measured file count — **6,402 files**
- [x] Build time benchmarked — **58.73s cold**
- [x] Decision recorded — **global graph**, both abandonment criteria pass
- [x] Falsifier check — file count is 13% of threshold, not above 50K
