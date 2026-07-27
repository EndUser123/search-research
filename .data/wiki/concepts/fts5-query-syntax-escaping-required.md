---
title: "FTS5 query-syntax escaping required for MATCH with user input"
created: 2026-07-27
source: session-019fa48a (/why on qmd "no such column" error)
tags: [fts5, sqlite, search, query-parsing, escaping, qmd, bug-pattern, failure-pattern]
summary: >
  SQLite FTS5's MATCH operator interprets the query string as a query-expression
  language (with operators `-`, `:`, `^`, `"`, `*`, `(`, `)`, AND, OR, NOT, NEAR),
  NOT as a literal search string. Any application that passes user input directly
  to MATCH will fail on queries containing these characters with misleading
  "no such column: <token>" or syntax errors. The query must be escaped (wrapped
  in double quotes for phrase queries, or have special characters stripped) before
  reaching MATCH. This is NOT SQL injection — the query is already parameterized;
  it is FTS5's own query parser, a layer above SQL. Confirmed in qmd v0.1.2;
  fix applied via site-packages patch with idempotent re-applier.
cognitive_load: 2
verification: execution-confirmed
host: both
agent: grok
sources:
  - "session-019fa48a /why RCA (discriminating test)"
  - "P:/docs/handoffs/session-friction-fixes-20260727/HANDOFF.md (SF-01)"
  - "SQLite FTS5 Full-text Query Syntax documentation"
relations:
  - target: wiki/concepts/qmd-semantic-search-requires-llm-backend.md
    type: related
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
---

# FTS5 query-syntax escaping required for MATCH with user input

## Decision context (why this finding was needed)

A `/tp` invocation failed its wiki pattern-library query with `{"error": "no
such column: vs"}`. The query was `"skill port reuse architecture build-vs-port
context distillation transcript export"`. The operator asked `/why` to find the
root cause and fix it. A prior handoff had hypothesized "SQL injection without
escaping" — that hypothesis was **wrong** (the query was already parameterized).
The `/why` investigation confirmed the actual root cause via a discriminating
test and applied the correct fix.

## The failure

**Symptom:** `qmd search --query "<anything with hyphens, colons, or carets>"`
returns `{"error": "no such column: <token>"}`.

**Discriminating test (Tier 1, execution-confirmed):**

| Query | Result |
|---|---|
| `"build vs port"` (spaces) | ✅ works |
| `"build-vs-port"` (hyphens) | ❌ `no such column: vs` |
| `"vs"` (bare word) | ✅ works |

The trigger is the **hyphens**, not the word "vs" itself.

## Root cause

SQLite FTS5's `MATCH` operator takes a **query expression string**, not a
literal search string. The expression language has its own syntax:

- `-` = NOT prefix operator
- `:` = column-restriction separator (`column:term`)
- `^` = column-alias prefix
- `"..."` = phrase query
- `*` = suffix wildcard
- `(` `)` = grouping
- Bare uppercase words: `AND`, `OR`, `NOT`, `NEAR`

When a user query like `build-vs-port` reaches MATCH, FTS5 parses it as a query
expression. The hyphens split the expression, and components are interpreted as
column references or operators — not literal search terms. `vs` is parsed as a
column name against the single-column `chunks_fts(text)` table, producing
`no such column: vs`.

**This is NOT SQL injection.** The query was already parameterized correctly
(`f.text MATCH ?` with the query as a bound parameter). The bug is one layer
above SQL: FTS5's own query parser, which runs on the parameter's value after
SQLite binds it.

## The fix

Wrap the query in double quotes before passing to MATCH, making it an FTS5
**phrase query**. Within a phrase, special characters are literal:

```python
def _sanitize_fts5_query(query: str) -> str:
    escaped = query.replace('"', '""')  # double internal quotes per FTS5 rules
    return f'"{escaped}"'
```

Apply in every call site that passes user input to `MATCH`:
- `_bm25_search` — main BM25 channel
- `_check_strong_signal` — strong-signal probe

The vector search channel (`_vector_search`) is **not** affected — it passes
the query through an embedding model, not FTS5.

## Why this is systemic (not just a qmd bug)

Any application using SQLite FTS5 `MATCH` with unescaped user input has this
bug. The pattern will recur in:
- Any local search tool built on FTS5 (see [[qmd-semantic-search-requires-llm-backend]] for qmd's architecture)
- Any RAG pipeline that uses FTS5 for the keyword channel
- Any tool that accepts arbitrary user queries and passes them to FTS5

The defensive rule: **treat the FTS5 MATCH argument as a query-expression
language, not a literal string.** Sanitize at the boundary where user input
enters the system.

## Misdiagnosis risk

The original handoff hypothesized "SQL interpolation without escaping" — a
plausible but wrong narrative. The tell: the error message (`no such column: vs`)
is an FTS5-level error, not a SQL-level error. A SQL injection would more likely
produce a syntax error or unexpected table access. The error naming a bare token
as a "column" points specifically at FTS5's column-reference syntax.

This is an instance of [[reactive-pattern-matching-and-closure-pressure]]: the
first plausible narrative ("SQL injection") felt sufficient and was recorded
without a discriminating test. The `/why` investigation's Step 1 (verify the
observation) + Step 5 (read the actual source) corrected it. The
[[decision-and-fix-documentation-rule]] should have captured the preference
during the original session; the structural fix is in
[[mechanical-enforcement-over-behavioral-reminder]].

## Falsifier

This finding is wrong if:
- FTS5 MATCH does NOT interpret the query as an expression language (refuted by
  SQLite docs and the discriminating test)
- The fix (phrase-query wrapping) breaks legitimate FTS5 query-syntax use cases
  (not applicable here — qmd never intended user queries to be FTS5 expressions)
- A future SQLite version changes FTS5 to treat MATCH arguments literally
  (would make this fix unnecessary but not harmful)

## Recovery (for site-packages patches lost on upgrade)

```
python P:/.agents/scripts/qmd_fts5_patch.py
```

Idempotent: detects already-patched state and exits 0. Run after any
`pip install --upgrade qmd`. The script re-applies `_sanitize_fts5_query` and
patches both call sites.
