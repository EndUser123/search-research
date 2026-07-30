---
status: superseded
superseded_by: wiki/concepts/repo-map-alternatives-codebase-memory-jetbrains-context.md
title: "Repo Map Capability: Extract from Aider, Not Rebuild (SUPERSEDED — not applicable to prose-heavy workspaces)"
created: 2026-07-30
source: session-20260730
tags: [repo-map, tree-sitter, aider, codebase-navigation, decision, mcp, agent-capability, superseded]
summary: >
  **SUPERSEDED same-day by /tp critique.** The extraction technique is
  technically sound and the analysis (zero Git coupling, PageRank multipliers,
  internal dependency audit) remains valid reference for **code-heavy
  workspaces (200K+ LOC)**. But our workspace is a knowledge base: 733
  markdown concepts, 411 docs, ~61 editable Python files. Neither Aider's
  repomap nor Codebase-Memory parses markdown. The dominant navigation problem
  is semantic prose search, not call-graph traversal. Decision reversed:
  invest in prose-discovery tooling (skill-graph, wiki-index) instead.
  The technical content below is preserved as reference for when a genuine
  large-codebase scenario arises.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - https://github.com/Aider-AI/aider/blob/main/aider/repomap.py (Aider-AI, 2026) — full source read
  - https://github.com/Aider-AI/aider/blob/main/aider/queries/tree-sitter-languages/ (Aider-AI, 2026) — query files inspected
relations:
  - target: wiki/concepts/context-management-in-claude-code.md
    type: related
  - target: wiki/concepts/claude-code-cli-agent-configuration-and-workflow-patterns.md
    type: related
  - target: wiki/concepts/cli-based-ai-coding-agents.md
    type: related
---

# Repo Map Capability: Extract from Aider, Not Rebuild

> **⚠️ SUPERSEDED 2026-07-30 (same day).** A `/tp` fresh-lens critique measured
> the actual workspace surface: 733 markdown concepts vs ~61 real Python files
> (excluding plugin cache contamination). Neither repomap nor Codebase-Memory
> parses markdown. The dominant navigation problem is semantic prose search,
> not call-graph traversal. The scale perception ("500+ pages, large multi-root
> codebase") was inflated by plugin caches (~54K `.py` files in cache dirs).
>
> **The technical analysis below remains valid** for code-heavy workspaces
> (200K+ LOC monorepos, enterprise refactoring, microservice architecture
> analysis). The extraction path, dependency audit, and PageRank multiplier
> documentation are correct. This decision was reversed because it doesn't
> apply to a knowledge-base workspace, not because the technique is wrong.
>
> **When to revisit:** if the workspace evolves toward a large codebase
> (e.g., building a substantial application with 500+ source files), this
> decision becomes relevant again. Until then, grep + existing prose-discovery
> tools (`build_skill_graph.py`, `index_skills.py`, `skill-catalog.md`)
> cover the actual surface.

## Decision context

Our AI coding agents (Grok Build, Claude Code, OpenCode) navigate large multi-root
codebases using grep and file-reading. This burns context tokens and misses structural
relationships (which functions call which, where classes are defined, import chains).
The workspace has 500+ wiki concept pages, 100+ skills, multi-root plugin marketplace
code — structural navigation via text search is a measurable bottleneck.

> **Correction (from critique):** the "500+ pages" are markdown, not code. The
> actual navigable code surface is ~61 files. The scale framing was wrong.

The question was: what is the best way to give every agent in the fleet a compressed
architectural map of the codebase at low token cost? Three options were evaluated:
(1) adopt Aider as a full CLI tool, (2) build a repo map from scratch, (3) extract
Aider's repo map logic as a shared capability.

## The ranking algorithm is the valuable IP

Aider's `repomap.py` uses tree-sitter to parse files into ASTs, extracts definition
and reference tags, builds a `networkx.MultiDiGraph`, and runs **PageRank** to rank
which symbols are most central to the codebase. The output is a compressed tree
format fitted to a token budget via binary search.

What makes it non-trivial is the **importance multipliers** applied before PageRank:

| Rule | Multiplier | Rationale |
|------|-----------|-----------|
| Identifier mentioned in current task context | ×10 | Surface symbols related to active work |
| Snake/kebab/camel case, ≥8 chars | ×10 | Meaningful names > `i`, `x`, `fn` |
| Private (`_` prefix) | ×0.1 | Internal detail, deprioritized |
| Defined in >5 files | ×0.1 | Too common to be informative |
| Referenced by files in active context | ×50 | Dependencies of active work matter most |

Plus **personalization**: files in the active task get boosted PageRank personalization,
centering the map around current work. These multipliers are the result of extensive
real-world tuning. Rebuilding them from scratch would mean months of "why does my map
show the wrong things?" debugging.

## Aider's repomap.py has zero Git coupling

GLM-5.2 recommended against extraction, claiming the module is "deeply coupled to
its internal GitRepo class and assumes a single Git root." **This is false.**

Source receipt: `repomap.py` (read in full from
`https://raw.githubusercontent.com/Aider-AI/aider/main/aider/repomap.py`). The file
contains zero Git imports, zero `GitRepo` references, zero git-history weighting.
The `root` parameter is a plain directory path for `os.path.relpath()`. File lists
are passed in by the caller from wherever they originate.

The three internal dependencies are all trivially replaceable:
- **`dump.py`** (~15 lines): debug print utility. Called once in a commented-out line.
- **`special.py`** (~180 lines): static list of "important files" (README, pyproject.toml, etc.). Self-contained, copy as-is.
- **`waiting.py`** (~150 lines): terminal spinner animation. Replace with no-op class (3 lines).

## What this means for our workspace

**Implementation path (~1.5 hours):**

1. Copy `repomap.py` + `special.py` + `queries/tree-sitter-languages/*.scm` (27 files)
   into `P:/.agents/scripts/repo_map/`
2. Strip 3 internal deps: remove `dump`/`waiting` imports, add no-ops
3. Replace `self.main_model.token_count()` with character estimate (`len(text) // 4`)
   — the 15% tolerance in the binary search makes precision unnecessary
4. Replace `self.io.read_text()` with `Path.read_text()`
5. Multi-root support: modify `get_rel_fname()` to accept multiple roots (~10 lines)
6. CLI wrapper: `python repo_map.py <path1> <path2> ...` → compressed tree to stdout
7. MCP server later: wrap as `get_repo_map` tool once output quality is validated
8. PostToolUse hook integration: invalidate cache entry for edited files

**External dependencies (pip install):**
`tree-sitter tree-sitter-languages grep_ast networkx diskcache pygments`

All mature packages. `grep_ast` (Aider author's library) provides `TreeContext`
rendering and tree-sitter wrappers — purpose-built for this use case.

**The `.scm` query files are the unsung asset.** These define what counts as a
"definition" vs "reference" for each language (Python's is 10 lines). They're MIT/
Apache licensed from upstream tree-sitter projects, modified by Aider. Copy all 27
verbatim — only Python and TypeScript are immediately relevant, but the rest cost
nothing.

## Why not adopt Aider as a full tool

We already have sophisticated orchestration (Grok Build + skills + hooks + multi-agent
fan-out + cross-model second opinions). Aider is a full agent that would compete with
our existing architecture. The repo map is the one capability we lack; everything else
Aider does (file editing, git commits, model routing) we already have via other tools.
Adding a 7th CLI to coordinate (Grok Build + Claude Code + OpenCode + PI + AGY + Codex
+ MMX) adds coordination cost for one feature. The right move is to extract the
capability, not the platform.

See [[capability-vs-packaging-in-ai-coding-tool-selection]] for the general principle:
when evaluating a tool for adoption, separate the capability it provides from the
packaging it comes in. Adopt capabilities; steal packaging ideas.

## Falsifier

This decision is wrong if:
- Aider's ranking quality doesn't transfer to multi-root workspaces (the personalization
  and multiplier logic assumes a single project context — our workspace spans 5+ roots
  with different purposes)
- The `grep_ast` or `tree-sitter-languages` packages prove unstable on Windows 11
  (tree-sitter has had Windows compatibility issues historically)
- A dedicated MCP repo-map server (like `pdavis68/RepoMapper` referenced in
  [[context-management-in-claude-code]]) turns out to already solve this with less
  integration effort

If any of these hold, revisit the from-scratch or MCP-server-first approaches.

> **Update 2026-07-30:** Falsifiers 1 and 2 were never tested, and the
> `/tp` critique confirmed falsifier 1 is structurally likely (PageRank over
> mixed-purpose roots ranks dense marketplace code as most central). See
> [[repo-map-alternatives-codebase-memory-jetbrains-context]] for the
> full reversal rationale and the workspace surface measurement (733
> markdown vs 61 Python files).

## Sources

- [aider/repomap.py](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py) (Aider-AI, 2026) — full source read; confirmed zero Git coupling, identified ranking algorithm and importance multipliers
- [aider/queries/tree-sitter-languages/](https://github.com/Aider-AI/aider/tree/main/aider/queries/tree-sitter-languages) (Aider-AI, 2026) — 27 `.scm` query files inspected; MIT/Apache licensed
- [aider/dump.py](https://github.com/Aider-AI/aider/blob/main/aider/dump.py), [aider/special.py](https://github.com/Aider-AI/aider/blob/main/aider/special.py), [aider/waiting.py](https://github.com/Aider-AI/aider/blob/main/aider/waiting.py) (Aider-AI, 2026) — all three internal deps read; confirmed trivially replaceable
- [Aider Repository Map documentation](https://aider.chat/docs/repomap.html) — conceptual overview

## Receipts

- `repomap.py` full source read from `https://raw.githubusercontent.com/Aider-AI/aider/main/aider/repomap.py` — confirmed zero `import git`, zero `GitRepo` references, zero git-history weighting
- `repomap.py` internal dependencies: `dump.py` (~15 lines, debug print), `special.py` (~180 lines, static file list), `waiting.py` (~150 lines, spinner animation) — all read and confirmed trivially replaceable
- `queries/tree-sitter-languages/*.scm` — 27 query files inspected, define definition vs reference patterns per language
- PageRank multipliers: lines in `repomap.py` `get_ranked_tags()` — identifiers mentioned in context ×10, meaningful names ×10, private ×0.1, >5 files ×0.1, referenced by active files ×50

## Related concepts

- [[repo-map-alternatives-codebase-memory-jetbrains-context]] — the `/tp` critique and reversal
- [[context-management-in-claude-code]] — MCP repo-map server references
- [[capability-vs-packaging-in-ai-coding-tool-selection]] — the extraction-not-adoption principle
- [[skill-dependency-graph-research-2026]] — prior decision that AST extraction isn't worth it for the prose surface (same conclusion, different substrate)
