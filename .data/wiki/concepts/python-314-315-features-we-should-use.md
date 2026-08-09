---
title: "Python 3.14 features to use now, 3.15 features to track"
concept_type: "technology-reference"
created: 2026-07-24
agent: grok
host: grok
verification: "official-docs-backed"
sources:
  - https://docs.python.org/3.14/whatsnew/3.14.html
  - https://docs.python.org/3.15/whatsnew/3.15.html
  - https://realpython.com/python-news-june-2026/
cognitive_load: 3
---

# Python 3.14 and 3.15 features we should use

## Decision context

**Why this research was needed:** we're running Python 3.14.0 and may have code patterns that could benefit from new stdlib features. Python 3.15 is in beta (feature freeze as of June 2026, final release ~October 2026). We need to know what's available now and what's coming so we can use the right tools and avoid reinventing stdlib functionality.

## Python 3.14 features (we're running this now)

### High-value features we should use immediately

**Template strings (t-strings, PEP 750)** — the biggest 3.14 feature for our codebase. t-strings return a `Template` object with separate static and interpolated parts, enabling safe string processing without injection risks. Use cases:
- **Safe shell commands** — `t`git commit -m {msg}`` processed by a handler that escapes the interpolation
- **Safe SQL** — no more manual quoting
- **Structured logging** — log the template parts separately from values
- We currently do manual string escaping in hooks; t-strings could replace that

**Deferred evaluation of annotations (PEP 649/749)** — annotations are no longer evaluated eagerly. This means:
- No more `from __future__ import annotations` needed
- Forward references work without string quoting
- New `annotationlib` module for introspecting annotations in VALUE, FORWARDREF, and STRING formats
- Our dataclass-heavy code (ContinuationCandidate, CoverageResult, Evidence) benefits from cleaner forward references

**`compression.zstd` module (PEP 784)** — Zstandard compression in the stdlib. Faster and better ratio than gzip. We could use it for:
- Compressing AAR session snapshots (currently raw JSON, 1-6MB each)
- Compressing mutation receipt files

**`concurrent.interpreters` module (PEP 734)** — subinterpreters in the stdlib. True multi-core parallelism without the GIL, with process-like isolation but thread-like efficiency. Limitations: startup cost, memory overhead, limited inter-interpreter sharing. Could be relevant for parallel hook processing.

**Bracketless except (PEP 758)** — `except TimeoutError, ConnectionRefusedError:` without parentheses. Small quality-of-life improvement.

**`map(strict=True)`** — like `zip(strict=True)`, validates equal-length iterables. We have parallel-list processing in several places.

**`compression` package** — new home for `lzma`, `bz2`, `gzip`, `zlib` under `compression.*`. Old names still work but `compression.*` is preferred.

### Features relevant to our hook system

**`concurrent.futures.InterpreterPoolExecutor`** — pool of subinterpreters for async execution. Separate from the `concurrent.interpreters` module.

**Incremental GC** — Python 3.14.0-3.14.4 had incremental GC (reduced pause times), but **3.14.5+ reverted to generational GC** due to memory pressure reports. Our production should be on 3.14.5+.

**`sys.remote_exec()` (PEP 768)** — zero-overhead debugger attachment to running processes. Could be useful for debugging stuck hooks or subagents.

**`asyncio ps` / `pstree`** — `python -m asyncio ps <PID>` shows running asyncio tasks as a table or tree. Useful for debugging async code.

### Breaking changes to watch

- `int()` no longer delegates to `__trunc__()` — must implement `__int__()` or `__index__()`
- `NotImplemented` in boolean context raises `TypeError`
- `-c` flag now auto-dedents its code argument
- `pickle` default protocol is now 5

## Python 3.15 features (coming ~October 2026)

### High-value features for our codebase

**Explicit lazy imports (PEP 810)** — declare imports as lazy for faster startup. Relevant for our hook scripts that pay import cost on every tool call.

**`frozendict` built-in (PEP 814)** — immutable dict type. Our receipt data, evidence bundles, and configuration objects should use `frozendict` where mutability isn't needed.

**`sentinel` built-in (PEP 661)** — replaces the `_MISSING = object()` pattern we use in several places. First-class sentinel values.

**UTF-8 default encoding (PEP 686)** — Python finally defaults to UTF-8. This eliminates the Windows `cp1252` silent corruption problem we've hit multiple times (documented in our file-editing protocol).

**Unpacking in comprehensions (PEP 798)** — `{**a, **b for ...}` syntax.

**Sampling profiler (PEP 799)** — `profiling.sampling` module with low-overhead statistical profiling. Could profile hook overhead precisely.

**Package startup files (PEP 829)** — `.start` files replace code-executing `.pth` files. Security improvement.

**Frame pointers by default (PEP 831)** — better profiling/observability via `perf` and similar tools.

**JIT compiler upgrades** — significantly improved JIT in 3.15.

### What this changes

1. **t-strings (3.14, available now)** — we should start using these in our hook scripts for safe command construction instead of manual string formatting
2. **UTF-8 default (3.15)** — eliminates an entire class of Windows encoding bugs we've documented in `file-editing-protocol.md`
3. **Lazy imports (3.15)** — our hooks pay ~60-110ms Python startup cost per call; lazy imports could reduce this
4. **`frozendict` (3.15)** — our dataclasses and evidence bundles should migrate to immutable dicts where appropriate
5. **`sentinel` (3.15)** — replaces ad-hoc `_MISSING = object()` patterns

## Related wiki concepts

- file-editing-protocol — the UTF-8 encoding issue this would help with
- [[quality-gate-hook-system-implementation]] — hooks that could benefit from lazy imports and t-strings
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
