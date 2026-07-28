---
title: "Built-in grep tool over shell ripgrep for wiki concept search"
created: 2026-07-28
source: session-2026-07-28
tags: [search, grep, ripgrep, wiki, tools, qmd, vector-search, optimization]
summary: >
  For a wiki of ~380 markdown files, ripgrep (via the built-in grep tool)
  is the optimal search method. Vector/semantic search (qmd) was removed
  after research confirmed plain text search wins for small plain-text
  corpora. Skills should instruct the LLM to use the native grep tool,
  not shell out to rg via run_terminal_command — the native tool IS
  ripgrep with lower latency and no subprocess overhead.
agent: grok
host: grok
cognitive_load: 1
verification: multi-source-verified
sources:
  - https://www.llamaindex.ai/blog/is-grep-all-you-need-lexical-vs-sematic-search-for-agents (LlamaIndex, 2026-05-26)
  - https://www.shaped.ai/blog/why-grep-is-beating-your-vector-db (Shaped.ai, 2026-04-23)
relations:
  - target: wiki/concepts/vector-search-vs-plain-text-search.md
    type: extends
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: related
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: complements
---

# Built-in grep tool over shell ripgrep for wiki concept search

## Decision context

**Why this research was needed:** Session 2026-07-28 removed qmd (the
semantic search tool used for wiki concept lookup) and replaced it with
ripgrep fallbacks across 13 skills. The operator asked: why ripgrep? Why
not something else? What's optimal for searching ~380 markdown wiki
concept files?

This is both a tool-selection decision (ripgrep vs vector search) and an
interface decision (built-in grep tool vs shell subprocess).

## What the research says

Three independent sources confirm that lexical search (ripgrep) beats
vector/semantic search for small plain-text corpora:

1. **PwC study** (cited in [[vector-search-vs-plain-text-search]]): grep
   beat vector search on ALL 5 AI models tested (GPT, Gemini, etc.) for
   question-answering over conversation history.

2. **Claude Code** (cited in same concept): built a local vector DB,
   then removed it because plain search across real files beat it.

3. **LlamaIndex** (Sen et al., arxiv 2605.15184): "For small, plain-text
   corpora (a codebase, a docs folder, a handful of markdown notes) lexical
   search is fast, predictable, and gives agents exactly the precision they
   need." Semantic search only wins at scale (millions of docs) or with
   unstructured formats (PDFs, Office files).

Our wiki has 380 markdown files — firmly in the "grep is optimal" range.

## The interface decision: built-in tool vs shell

Grok Build's built-in `grep` tool IS ripgrep under the hood. The initial
qmd replacement instructed skills to run `rg -l -i "keywords"` via
`run_terminal_command`. That's an unnecessary subprocess:

| Approach | Latency | Naturalness | Error surface |
|----------|---------|-------------|---------------|
| Shell `rg` via `run_terminal_command` | Process spawn + shell parsing | Indirect (LLM writes shell, shell runs rg) | PowerShell quoting, pipe failures |
| Built-in `grep` tool | Direct tool call | Native (LLM calls tool directly) | Minimal — tool handles paths |

The built-in tool is faster (no process spawn overhead), more natural
(the LLM calls a tool, not writes shell), and has a smaller error surface
(no PowerShell quoting issues, no pipe failures).

## What this means for our workspace

1. **qmd is uninstalled.** The 13 skills that previously called `qmd search`
   now instruct the LLM to use the built-in grep tool with
   `path="P:/.data/wiki/concepts/"`.

2. **The auto-link pipeline** (`wiki_after_write.py`) previously used qmd
   to find wikilink candidates. It now reports "no qualifying concept
   neighbors found" when qmd is absent. This is a degradation — auto-linking
   no longer works. A future enhancement could use the grep tool to find
   candidates, but that requires reworking the Python script to call
   ripgrep internally rather than qmd.

3. **The retirement check** in the wiki skill previously used `qmd search`
   to find overlapping concepts. It now uses the built-in grep tool. This
   is keyword-only (no semantic matching), but the research confirms this
   is sufficient for our corpus size.

4. **Known limitation:** the grep approach requires the searcher to use
   the source's vocabulary, not their own framing vocabulary. This is
   documented in [[causal-mechanism-claims-require-source-receipts-before-durable-write]]
   § "grepping with the searcher's vocabulary." The structural fix there
   (run TWO searches with different vocabulary) applies here too.

## Falsifier

If the wiki grows beyond ~5,000 concepts, or if unstructured formats
(PDFs, Office files) become a significant portion of the corpus, lexical
search will hit scaling limits (latency, recall, signal-to-noise). At
that point, a hybrid approach (BM25 + semantic) would become optimal.
Until then, the built-in grep tool is the right choice.

## Sources

- [Is grep all you need? Lexical vs Semantic Search for Agents](https://www.llamaindex.ai/blog/is-grep-all-you-need-lexical-vs-sematic-search-for-agents) (LlamaIndex, 2026-05-26) — confirms grep wins for small plain-text corpora
- [Why grep is beating your Vector DB](https://www.shaped.ai/blog/why-grep-is-beating-your-vector-db) (Shaped.ai, 2026-04-23) — industry trend of grep over vector DBs
- [[vector-search-vs-plain-text-search]] (our wiki, 2026-07-27) — PwC study + Claude Code's vector DB removal

## Receipts

- `~/.grok/config.toml` — no qmd references remain
- `~/.grok/tool-fallbacks.md` — qmd entry removed
- 13 skill files updated to use built-in grep tool (commit 48e5a05)
- qmd package uninstalled: `pip uninstall qmd` confirmed (command not found)
