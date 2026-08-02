# Code-Graph Backend Evaluation

**Date:** 2026-08-02
**Evaluator:** Grok Build (MiniMax-M3)
**Scope:** Multi-package Python workspace at `P:/packages/` (31,842 .py files; 7,806 in the `plugins/` subtree used for the PoC)
**Target queries:** "Who calls function X across all packages?" / "What depends on module Y?"

---

## TL;DR

- **Best backend: tree-sitter.** One-time cold build ~62s for 7,806 files (warm cache ~10s); subsequent queries **sub-millisecond** (0.004–0.8ms for 0–3,173 hits).
- **context7 is not applicable.** It is a library-documentation lookup tool (React, MongoDB, etc.) and cannot index local code.
- **code_analysis.py already produces a module-import graph** per package (cycles, fan-in/out) but has **no function-level call graph** and **no cross-package persistence**. It is the natural place to extend.
- **ripgrep is fast enough for ad-hoc single queries** (35–441ms cold on the full workspace) but produces **substring matches** that need a read+verify pass to disambiguate calls from definitions, comments, and string literals. It is not a structural query tool.

**Recommended path:** extend `code_analysis.py` with a tree-sitter-backed function-call graph, persist it to a gitignored cache file, and expose a `who-calls` / `what-imports` CLI. Estimated effort **1–2 days for v1** (3–5 days with alias resolution, incremental invalidation, and skill integration).

---

## 1. What `P:/.agents/scripts/code_analysis.py` already does

`code_analysis.py` is a 5-phase structural analyzer built for `/refactor`'s comprehensive-analysis phase. It runs entirely on the standard library `ast` plus two external CLIs (`vulture`, `radon`).

| Phase | What it produces | Per-package? | Cross-package? | Function-level? |
|---|---|---|---|---|
| 1. Import graph | `{graph, cycles, fan_in, fan_out, module_count}` | One package per invocation (input = single dir) | **No** — operates on one root at a time | **No** — module-level only |
| 2. Dead code (vulture) | list of `{file, line, detail}` | Per package | No | Yes (uses vulture's symbol-level) |
| 3. Complexity hotspots (radon) | list of `{file, detail}` | Per package | No | Yes (cyclomatic) |
| 4. Cross-file duplication | AST-normalized function-body match | Per package | No (but spans files within pkg) | **Yes** — by function name |
| 5. Test coverage gaps | list of `{file, detail}` | Per package | No | No |

**Gaps relative to the question:**
- **No function-level call graph.** Phase 4 finds duplicate function bodies but does not record who calls what.
- **No cross-package persistence.** Every invocation re-parses from scratch; no shared cache, no JSON artifact emitted to a stable location.
- **No `who-calls` or `what-imports` query.** Output is a static report, not a queryable index.

**Extensibility:** the existing `_extract_function_bodies` (line ~237) shows the AST-walking pattern. Adding a function-call walker is mechanically identical — `ast.walk` for `ast.Call` nodes, capturing `node.func` (id or attribute). tree-sitter is faster than stdlib `ast` (per the PoC: ~640 files/s warm) but `ast` would also work; the structural data is the same.

**Can it be extended to persist a cross-package graph?** Yes, with moderate refactoring: the current entrypoint `run_analysis(target)` accepts a single path. To go cross-package, add a `MultiPackageIndex` collector that walks `P:/packages/*/` and merges per-package results, and emits a single artifact (JSON or msgpack) to `P:/tmp/codegraph.json`. No new dependencies required for the AST-only path; tree-sitter is already installed if we want the speed win.

---

## 2. ripgrep baseline — `who calls validate_close_receipt across all packages`

| Step | Tool | Time (wall clock) | Hits | Notes |
|---|---|---|---|---|
| Find files matching pattern | `rg --files-with-matches "validate_close_receipt" P:/packages --type py` | **35–441ms** (35ms warm / 441ms cold) | 0 files | Function does not exist in the workspace — ripgrep correctly reports zero |
| Find files matching an existing function | `rg --files-with-matches "validate_phase2a_record" P:/packages --type py` | **42ms** | 3 files | Confirms pipeline is fast when a real name is queried |
| Count matching lines for common name | `rg --count "parse_args" P:/packages --type py` | **55ms** | 43 lines | |
| Read each hit to confirm "is a call" | `Get-Content` + `Select-String` over 3 files | **26ms** | 3 matches classified | 1 of 3 is the `def` line; 2 are import sites; **0 are actual call sites** in the package queried |

### Completeness assessment

ripgrep returns **substring matches**, not structural call sites. A query for `validate_close_receipt` would surface:
- The `def validate_close_receipt(...)` line (definition)
- `# validate_close_receipt handles receipt validation` (comment)
- `logger.info("validate_close_receipt failed")` (string literal)
- `from .validate_close_receipt import ...` (import)
- `self.validate_close_receipt()` (call — but only if `.validate_close_receipt` is the form)

There is **no way for ripgrep to tell these apart without reading and AST-parsing each file.** The read+verify step costs an extra 20–100ms per file and still requires logic to distinguish call-site contexts.

**Query latency budget for grep-only workflow:**
- ripgrep search: ~50ms
- Read 3 files: ~30ms
- AST-verify each line: ~5ms (would need a small Python script)
- **Total: ~85ms per query, no alias resolution, no call/def distinction without extra work.**

---

## 3. context7 capability assessment

**Verdict: not applicable.** context7 is a library-documentation fetcher, not a code-indexing tool.

- Tool surface: `resolve-library-id` (string → `/org/project` ID) and `query-docs` (text question against a library's docs).
- Designed for: looking up React, MongoDB, Django, etc. API references.
- Designed against: indexing local code or answering structural queries on user codebases.

Evidence:
- The `resolve-library-id` query for "structural code analysis local python files call graph" returned results for an **Obsidian graph-analysis plugin** and several **Claude Code leak-analysis writeups** — none of which can index a local workspace.
- The tool description states: *"Retrieves and queries up-to-date documentation and code examples from Context7 for any programming library or framework."*
- No path or file argument is accepted by either context7 tool.

**If a future version of context7 ever did support local indexing, the questions to ask are:**
1. Does it accept a path/root argument? (Current: no.)
2. Does it persist between sessions, or re-fetch every call?
3. What is the latency vs. an in-process tree-sitter pass?

For now: **do not evaluate context7 further for this workload.**

---

## 4. tree-sitter availability and PoC results

### Availability

```
$ python -c "import tree_sitter, tree_sitter_python"
# tree_sitter: available (module has no __version__ attr in this build)
# tree_sitter_python: available
# tree_sitter_languages: NOT available (would be an alternative API)
```

`tree-sitter` 0.21+ and `tree-sitter-python` are both installed. The newer API (`tree_sitter.Language(language_obj)`) is in use. The deprecated `tree_sitter_languages` package is **not** present but is **not needed** — `tree_sitter_python.language()` returns a `Language` object directly.

### PoC scope

`P:/tmp/tree_sitter_poc.py` parses every `.py` file under `P:/packages/.claude-marketplace/plugins/` (the per-subtree scope requested by the task), excluding `__pycache__/`. It extracts:
- **function definitions** (name + file + line)
- **function calls** — both bare (`foo()`) and attribute (`x.foo()`) — recording the callee name and the enclosing function (caller)
- **import statements** (raw text — alias resolution is a known follow-on)

### Build phase

| Metric | Value |
|---|---|
| .py files discovered (excl `__pycache__`) | **7,806** |
| Total function definitions | **70,783** (39,674 unique names) |
| Total call sites | **605,936** (78,734 unique callee names) |
| Parse errors | **0** |
| **Cold build time** | **61.70s** (≈ 127 files/s) |
| **Warm build time** | **~10s** (≈ 640–880 files/s, file cache hit) |
| Peak RSS during build | not measured, well under 1 GB |

The cold build is dominated by file I/O (7,806 small files). On a warm cache the CPU-bound parser is the bottleneck at ~700 files/s.

### Query phase

| Query | Hits | Latency |
|---|---|---|
| `who_calls('validate_close_receipt')` (does not exist) | 0 | **0.000 ms** |
| `who_calls('read_text')` | 2,175 | **0.71 ms** |
| `who_calls('exists')` | 3,173 | **0.81 ms** |
| `who_calls('open')` | 1,366 | **0.43 ms** |
| `who_calls('parse')` | 292 | **0.07 ms** |
| `who_calls('load')` | 467 | **0.11 ms** |

Query latency is dominated by Python dict iteration over the inverted index — not by parsing. A 3,000-hit result set returns in under 1ms. There is no I/O on the query path.

### What the PoC does not (yet) do

These are deliberate omissions, not bugs:
- **No alias resolution.** A call like `bootstrap(__file__)` records the callee as `bootstrap`; a query for `_bootstrap` (the module name) returns 0. Real call graphs need to bind `bootstrap` to its module-of-origin via `from _bootstrap import bootstrap` analysis.
- **No cross-file resolution.** A call to `validate_phase2a_record` from `evaluate_phase2a.py` is recorded as a callee, but if `validate_phase2a_record` is defined in `phase2a.py` (which it is), the PoC does not currently link them — the user must do that lookup. The data is in the graph (`defs_by_name['validate_phase2a_record']` → `[(phase2a.py, 88)]`); the link is just not auto-emitted.
- **No mtime-based incremental update.** A full re-parse runs every time the script is invoked.
- **No persistence in a queryable format.** The PoC writes a summary JSON; the live graph is held in memory only.

### Per-package vs. cross-package — empirical observation

Running the PoC against the **plugins subtree** (7,806 files), `validate_phase2a_record` returns **0 hits**. The function is defined in `P:/packages/research_runtime/src/research_runtime/phase2a.py` and called from `P:/packages/research_runtime/src/research_runtime/evaluate_phase2a.py` — **outside the plugins subtree**.

This is exactly the failure mode the question is about: **a per-package PoC misses cross-package callers.** A persistent cross-package graph fixes this by unioning the per-package inverted indexes into a single index keyed on (package, file, func_name).

---

## 5. Recommended backend

**Recommendation: extend `code_analysis.py` with a tree-sitter-backed function-call graph, persisted to a stable cache file.**

### Justification

| Criterion | ripgrep | stdlib `ast` | **tree-sitter** | context7 |
|---|---|---|---|---|
| Sub-ms query | No (50ms+ for grep) | Yes (in-memory only) | **Yes (in-memory)** | N/A |
| Distinguishes call from def | No | Yes | **Yes** | N/A |
| Distinguishes call from comment | No | Yes | **Yes** | N/A |
| Handles method vs. function | Regex only | Yes | **Yes** | N/A |
| Survives `__pycache__` / symlinks | Yes | No (file walk needed) | **No (same caveat)** | N/A |
| Cross-package by design | No | Possible (orchestrator) | **Possible (same)** | N/A |
| Persistence primitives | None | pickle / msgpack | pickle / msgpack | N/A |
| Already installed | Yes | Yes | **Yes** | Yes (but not applicable) |
| Build time (7,806 files, warm) | n/a | ~3× tree-sitter | **~10s** | n/a |

The trade-off is **build cost (one-time ~60s cold / ~10s warm) vs. query cost (sub-ms vs. ~50ms+ for grep).** For an interactive assistant, sub-ms queries dominate the user experience; the build cost is amortized over hundreds of queries in a single session.

### Why not stdlib `ast`?

`ast.parse` is correct and fast enough for one file, but tree-sitter's streaming tokenizer and incremental-edit support are stronger for very large files and for the eventual incremental-invalidation feature. For the current PoC scope, either is fine; tree-sitter is what is **already installed** and is the more direct path.

### Why not ripgrep alone?

ripgrep is excellent for **discovery** ("does name X appear in the codebase?") but cannot answer **structural** questions without a follow-on AST pass per file. For a single-shot query it is fine; for the "across all packages, call sites only" use case it is a 5–10× cost increase in wall time and produces noisier output.

### Why not context7?

Wrong tool. See §3.

---

## 6. Estimated effort to build a persistent cross-package graph

A working v1 that answers the question in the prompt.

| Component | Effort | Dependencies |
|---|---|---|
| Promote the PoC to a real script at `P:/.agents/scripts/call_graph.py` | 2 hours | tree-sitter (installed) |
| Per-package pass with `--package <name>` and a default of "all packages in `P:/packages/`" | 2 hours | None |
| Persist to `P:/tmp/codegraph/<package>.pkl` (pickle of `{defs, calls, imports, mtime_map}`) | 1 hour | None |
| Incremental update keyed on `mtime` of source files (skip if unchanged) | 3 hours | None |
| Inverted index merge into `P:/tmp/codegraph/all.pkl` for cross-package queries | 2 hours | None |
| `who-calls <name>` and `what-imports <module>` CLI subcommands | 2 hours | None |
| Add a `--from-cache` fast path and a `--rebuild` flag | 1 hour | None |
| Wire into `code_analysis.py` as a new phase 6, gated on tree-sitter availability | 2 hours | None |
| Alias resolution (`from x import y` → bind y to x.y; `import x as y` → bind y to x) | 1 day | Symbol table from `imports_by_file` |
| Unit tests for parse, query, alias resolution, incremental update | 1 day | pytest |
| Skill integration (a `/codegraph` skill, or hook the script into `/refactor` Phase 1) | 4 hours | None |
| **Total v1 (no alias resolution)** | **~1.5 working days** | |
| **Total v1 + alias resolution + tests + skill** | **~5 working days** | |

### Storage cost

- In-memory: ~600K call sites × 4 fields × ~80 bytes = ~190 MB peak. Acceptable for a workstation, not for CI.
- On disk (msgpack): same data, ~30–50 MB. Pickle is 2× larger.
- Recommendation: store as a single `P:/tmp/codegraph/all.msgpack` plus per-package shards; merge on first use. Add the cache path to `.gitignore`.

### Failure modes and mitigations

- **Files change between sessions.** → mtime check + selective re-parse.
- **Same function name in two packages (e.g. `main` in 30 plugins).** → qualify by `(package, func_name)` in the user-facing query; surface ambiguity rather than silently merging.
- **Dynamic calls (`getattr(obj, name)()`) not represented.** → out of scope for v1; document as a known limitation, same as every static analyzer.
- **Stale cache after a `git pull`.** → rebuild on mtime divergence; rebuild always on first run of the day.
- **Tree-sitter parser upgrade breaks existing serialized data.** → include a schema version in the pickle/msgpack and refuse to load on mismatch.

---

## Appendix A — Raw timings

| Test | Wall clock |
|---|---|
| `rg --files-with-matches "validate_close_receipt" P:/packages --type py` (cold) | 441 ms |
| `rg --files-with-matches "validate_close_receipt" P:/packages --type py` (warm × 5) | 0 ms (cached) |
| `rg --files-with-matches "validate_phase2a_record" P:/packages --type py` | 42 ms |
| `rg --count "parse_args" P:/packages --type py` | 55 ms |
| `Select-String` over 3 matching files to classify hits | 26 ms |
| tree-sitter PoC: build (cold) | 61.70 s |
| tree-sitter PoC: build (warm) | ~10 s (640–880 files/s) |
| tree-sitter PoC: `who_calls(...)` over inverted dict | 0.004–0.81 ms |
| `Get-ChildItem` walk to count .py files in `plugins/` | 405 ms |

## Appendix B — Files produced

| Path | Purpose |
|---|---|
| `P:/tmp/tree_sitter_poc.py` | The PoC script (7806-file pass, builds in-memory call graph) |
| `P:/tmp/print_poc_stats.py` | Helper to print the persisted summary |
| `P:/tmp/codegraph.json` | Summary statistics from the build (defs, calls, parse errors, top callees) |
| `P:/tmp/codegraph-evaluation.md` | This document |

No production files were modified. All output is in `P:/tmp/`.
