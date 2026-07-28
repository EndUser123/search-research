---
thread_id: qmd-fts5-replacement-20260727
parent_handoff_path: P:/docs/handoffs/qmd-viability-evaluation-20260725/HANDOFF.md
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T20:41:50Z
status: open
handoff_type: investigation
accurate_as_of_head: a498b5ed06dcb5ebd1e9989537d4b7b6f9f5f0b6
---

# HANDOFF: Replace qmd with a minimal FTS5-only search wrapper

> **Read this block first.** This handoff carries a producing-session
> *evaluation* plus an *author subagent's verification pass*. Several load-bearing
> references in the producing session's notes were checked against the tree at
> write time and **corrected** (see "Verified facts" → "Evidence-verification
> corrections"). A cold-start reader should rely on the corrected receipts, not
> on the original session shorthand.

## Objective (one sentence)

Replace qmd v0.1.2 (dead upstream, accumulating site-packages patches, only one
of its five components provides real value) with a ~200-LOC workspace-owned,
English-only, stdlib-only SQLite FTS5 search wrapper that preserves the
per-token FTS5 query-quoting fix we already proved correct, and retire the qmd
dependency for wiki search.

## Status

## Status

**OPEN — ready-to-implement, externally validated.** The evaluation is complete
and the design is concrete enough to build. No code has been written for the
replacement yet; the existing qmd install + patches remain the live search path
until the wrapper passes acceptance criteria.

**External validation (2026-07-27 /www):** the /www investigation (session
019fa48a) independently confirmed FTS5 is sufficient for ~1000 markdown docs.
Key citations: (1) Karpathy's llm-wiki pattern (July 2026) explicitly recommends
"FTS5 (SQLite) or BM25" for markdown wikis at 300-500 pages; (2) BrainDB
benchmarks FTS5 at <1ms vs Pinecone's 50-200ms; (3) BM25 wins 92% vs 78% on
exact matches at small scale. `sqlite-vec` (Alex Garcia) is the escape hatch
if embeddings are ever needed — same DB file, same query code path.

**Precondition before building:** run a 30-query recall benchmark against the
actual wiki to confirm FTS5 top-5 recall is above ~75%. Build the benchmark
from known-answer test cases before committing to the replacement.

See `P:/.data/wiki/concepts/workspace-infrastructure-investment-priorities-2026.md`
Track D for full evidence + sources.

## Producing context

This handoff was written by a subagent on session `019fa48a` (Grok Build,
terminal `grok-build-terminal`). The **evaluation findings** originate from the
same session's qmd-viability work; the **handoff document** was authored on
2026-07-27 with a verification pass over every cited path. Where the producing
session's notes named an artifact the author could not locate on disk, the
discrepancy is recorded explicitly below rather than silently propagated.

Thread lineage: this continues `qmd-architecture-20260725` (the parent handoff
that scoped the keep/replace/exit-trigger decision). The parent's "Option D"
(raw sqlite-fts5, ~200-300 LOC) is the option chosen here; this handoff is its
implementation brief.

## Read-first list

Ordered by importance for a cold-start reader.

1. **`P:/.agents/scripts/qmd_fts5_patch.py`** — the per-token FTS5 quoting fix
   you MUST port. `_sanitize_fts5_query` (lines 72-88) is the canonical,
   verified implementation. Its module docstring (lines 1-31) is the primary
   receipt for the bug, the fix, and the discriminating test.
2. **`P:/.agents/scripts/wiki_search.py`** — the *existing replacement boundary*.
   Its docstring (lines 1-29) explicitly states this module is the single point
   qmd is allowed to be touched, so that replacing qmd changes only this file.
   Any new wrapper must integrate with (or supersede) this shim.
3. **`P:/docs/handoffs/qmd-viability-evaluation-20260725/HANDOFF.md`** — the
   parent handoff. Contains the option matrix (B/D/F/I/K), the database
   inventory (76 docs / 650 chunks / 1024-dim / 56 MB at
   `~/.config/qmd/qmd.db`), and the "subprocess-as-degradation-boundary"
   insight that motivates the shim architecture.
4. **`P:/.data/wiki/concepts/qmd-patch-durability-strategy.md`** — the 2026-07-20
   decision to keep patching, **with its own re-evaluation trigger**: line 86 +
   lines 133/154 name "re-evaluate Option B/F if N+1 patches needed or upstream
   unreachable." This handoff is that re-evaluation firing.
5. **`P:/.data/wiki/concepts/agents-md-construction-best-practices.md`** —
   progressive-disclosure principle. Relevant to how the wrapper should expose
   its surface (small API, not a re-implementation of all five qmd components).
6. **`P:/docs/handoffs/session-friction-fixes-20260727/HANDOFF.md`** (SF-01) —
   the sibling handoff documenting the FTS5 query-parser fix as a friction
   item, including the (later-corrected) SQL-injection hypothesis.
7. The three `.patch` sources:
   `P:/packages/.claude-marketplace/plugins/cc-skills-utils/__lib/qmd_fts5_patch.patch`,
   `.../qmd_cli_main.patch`,
   `.../qmd_llm_sentence_tf.patch` — the patches these retire.

## Verified facts (with source paths)

All items below were mechanically verified by the author subagent at write time
(git HEAD `a498b5e`). Tier 1 = directly read/executed this authoring pass; the
producing-session items are labeled with their original receipt.

- **[FACT, Tier 1]** qmd database exists at `~/.config/qmd/qmd.db`, size
  56,344,576 bytes (~56 MB). *Receipt:* `Get-Item` this pass. Confirms the
  parent handoff's "56MB" inventory.
- **[FACT, Tier 1]** `_sanitize_fts5_query` is defined at
  `P:/.agents/scripts/qmd_fts5_patch.py:72-88`. The algorithm: split on
  whitespace, escape `"` → `""` inside each token, wrap each token in
  `"…"`, join with spaces (preserves FTS5 implicit-AND). *Receipt:* file read
  this pass.
- **[FACT, Tier 1]** The patch script is idempotent and self-verifying: it
  checks for both the function definition **and** ≥2 call-site wirings
  (`_bm25_search` + `_check_strong_signal`) before declaring "already patched"
  (`qmd_fts5_patch.py:50-58`). *Receipt:* file read this pass.
- **[FACT, Tier 1]** The patch docstring records the discriminating test that
  isolated the bug: `"build vs port"` (spaces) works, `"build-vs-port"`
  (hyphens) fails, `"vs"` alone works — isolating the trigger to FTS5
  special-character interpretation, **not** SQL injection
  (`qmd_fts5_patch.py:1-31`). *Receipt:* file read this pass.
- **[FACT, Tier 1]** An existing replacement boundary exists:
  `P:/.agents/scripts/wiki_search.py`. Its docstring states "If qmd is ever
  replaced … only THIS FILE changes — every consumer keeps working." It
  currently delegates to live qmd via `from qmd import connect`. *Receipt:*
  file read this pass.
- **[FACT, Tier 1]** `.agents/` currently contains `scripts/` and `skills/` but
  **no `lib/` directory.** The user's proposed target `P:/.agents/lib/wiki_search/`
  would be a new tree. *Receipt:* `Get-ChildItem` this pass.
- **[FACT, Tier 1]** Three `.patch` source files exist at
  `P:/packages/.claude-marketplace/plugins/cc-skills-utils/__lib/`:
  `qmd_fts5_patch.patch`, `qmd_cli_main.patch`, `qmd_llm_sentence_tf.patch`.
  *Receipt:* directory listing this pass.
- **[FACT, producing session]** qmd upstream is dead: `chengzhag/qmd-py`
  returns 404 since at least 2026-07-20. *Receipt:* cited in
  `qmd-patch-durability-strategy.md` and the parent handoff.
- **[FACT, producing session]** Only FTS5 (BM25 keyword) search provides clear
  value for ~400 wiki concepts; vector/RRF/expansion/reranking were each
  evaluated as marginal-or-negative (expansion "caused" a correctness defect and
  adds LLM-backend latency). *Receipt:* producing session's evaluation; the
  component-value breakdown is summarized in "Current state."

### Evidence-verification corrections (READ — avoids phantom references)

The producing session's notes contained three references that do **not** resolve
on disk as described. They are recorded here so a fresh session does not waste
time chasing them:

1. **`[[qmd-viability-evaluation-20260725]]` is a handoff, not a wiki concept.**
   No wiki concept by that slug exists under `P:/.data/wiki/concepts/`. The
   real artifact is the parent handoff at
   `P:/docs/handoffs/qmd-viability-evaluation-20260725/HANDOFF.md` (linked in
   Read-first #3). *Receipt:* `Get-ChildItem … -Filter "*viability*"` returned
   no wiki files; the handoff path verified to exist.

2. **`conversation-distillation-review-packet-export.md` does NOT document the
   FTS5 per-token quoting approach.** Its actual contents are about
   conversation distillation / review-packet export (tool-call path
   extraction, relevance filtering, two-tier output). It mentions
   `qmd/core/expansion.py` only in passing (semantic-expansion context). The
   **real** receipt for the FTS5 quoting design is `qmd_fts5_patch.py:72-88`
   (Read-first #1). *Receipt:* grep of the concept file for
   `fts5|sanitize|per-token|BM25|tokenizer` returned no matches; headings
   enumerated this pass.

3. **`CORR-003` and `CORR-004` do not exist on disk, and no regression-test
   file exists.** Searches across `P:/.data/wiki`, `P:/docs`, and `P:/.agents`
   found only `CORR-001`/`CORR-002` (red-team handoff) and `CORR-002`/`MAINT-005`
   (inside `qmd_fts5_patch.py`). There is **no** `test*.py` under `P:/.agents`.
   The "CORR-003 regression test" referenced in the producing notes is
   session-internal and was not materialized. The **actual** verification
   receipt for the FTS5 fix is: (a) `qmd_fts5_patch.py` docstring
   ("Fix verified same session: the failing query returned 3 results after
   patch") and (b) sibling handoff `session-friction-fixes-20260727` SF-01.
   *Implication for this handoff:* acceptance criterion #5 ("test suite runs
   from workspace") requires **building** a regression test as part of this
   work — there is none to reuse.

4. **"4+ site-packages patches" vs three `.patch` source files.** The producing
   session counts *logical fixes* (FTS5 escaping, llm_backend, timeout,
   embedding-model = 4+); the on-disk *source patches* are three files (the
   timeout/cli fix is folded into `qmd_cli_main.patch`). Both counts are
   consistent; the fresh session should treat the three `.patch` files as the
   authoritative patch inventory.

## Current state

**Live search path (today):** consumers call `P:/.agents/scripts/wiki_search.py`
(`WikiSearch` class) → lazy-imports qmd → `collection.hybrid_search()`. The FTS5
quoting fix is injected into site-packages by running
`python P:/.agents/scripts/qmd_fts5_patch.py` after any qmd
install/upgrade. Search works for the ~76 indexed wiki docs.

**Component value (producing-session evaluation):**

| qmd component | Value for ~400 wiki concepts | Disposition in replacement |
|---|---|---|
| FTS5 (BM25 keyword) | **High** — the only clearly valuable component | **Keep** — core of the wrapper |
| Vector search (sqlite-vec) | Marginal — trigram/substring already handled by FTS5 tokenizer | Drop |
| RRF fusion | Low — channels overlap heavily for short docs | Drop |
| Query expansion | **Negative** — adds latency, needs LLM backend, introduced a correctness defect | Drop |
| Reranking | Low — initial ranking sufficient for 400 docs | Drop |

**Why replace now (trigger firing):** the re-evaluation trigger in
`qmd-patch-durability-strategy.md` (N+1 patches OR upstream unreachable for M
months) is met on both axes — upstream dead ~3+ months, patch set at 3 source
files / 4+ logical fixes and growing. The clean-slate test ("would you install
qmd today?") says no, and the component-value table shows 4 of 5 components add
cost without value for this corpus.

## Task packets

### PKG-01: Build the FTS5-only search package (stdlib-only wrapper replacing qmd for wiki search, porting the verified per-token query-quoting fix)

- in scope: Package skeleton (CLI + library); `search(collection, query, top_k)` against SQLite FTS5; port `_sanitize_fts5_query` verbatim from `qmd_fts5_patch.py:72-88`; `python -m wiki_search search …` entry point; English-only docstrings/comments/identifiers.
- out of scope: vector search, RRF, query expansion, reranking, multi-DB backends, Chinese-language support, re-indexing tooling beyond what acceptance needs.
- files / anchors: new module (location = Open Decision OD-1); port source `P:/.agents/scripts/qmd_fts5_patch.py:72-88`; integrate with existing `P:/.agents/scripts/wiki_search.py`.
- acceptance: `python -m wiki_search search --collection wiki --query "build-vs-port" --top-k 5` returns >=1 result (no FTS5 syntax error); query "model routing" returns both adjacent and non-adjacent docs (implicit-AND, not phrase query); no import outside stdlib (`sqlite3, json, pathlib, argparse`).
- falsifier: the hyphenated query "build-vs-port" raises an FTS5 syntax error OR returns zero results — proves the per-token quoting was not ported correctly. A second falsifier: the multi-term query returns ONLY docs containing the exact adjacent phrase — proves implicit-AND was broken into a phrase query.
- verification level required: LIVE_BEHAVIOR

### MIG-01: Database strategy reuse-vs-new (decide whether the wrapper reads the existing ~/.config/qmd/qmd.db or builds a new FTS5-only DB, and implement the chosen path)

- in scope: Inspect the qmd DB schema (FTS5 table name, column layout, chunk vs. document granularity); determine whether a stdlib `sqlite3` reader can query it read-only without qmd; if reusing, write a read-only connector; if new, write a one-time indexer over `P:/.data/wiki/concepts/*.md`.
- out of scope: migrating embeddings/vector tables (not needed — vector search is dropped); preserving qmd metadata the wrapper doesn't use.
- files / anchors: `~/.config/qmd/qmd.db` (read-only inspection); qmd schema discoverable via `sqlite3 .schema` or `PRAGMA table_info`.
- acceptance: all existing wiki concepts are searchable through the wrapper (criterion #3). If reusing the DB: a read-only `SELECT … FROM <fts5_table> WHERE <fts5_table> MATCH ?` returns results without qmd present. If new DB: the indexer covers 100% of `P:/.data/wiki/concepts/*.md`.
- falsifier: a wiki concept that qmd currently returns for a known query is missing from the wrapper's results — proves the DB strategy lost coverage (>5% of concepts dropped would be a coverage disaster, not a nit).
- verification level required: LIVE_BEHAVIOR

### TEST-01: Workspace test suite plus FTS5 regression (build a pytest suite in the workspace, not site-packages, that locks in FTS5 quoting behavior, since no regression test exists today)

- in scope: A test that asserts the hyphenated query returns results (the bug that was fixed); a test that asserts multi-term queries do implicit-AND, not phrase matching; a test that the sanitizer output is the expected per-token-quoted string for representative inputs (hyphens, colons, quotes, empty, single token).
- out of scope: benchmarking, coverage thresholds beyond the FTS5 contract.
- files / anchors: `tests/` inside the new package; mirror the discriminating test recorded in `qmd_fts5_patch.py:24-29`.
- acceptance: `pytest` from the workspace runs green; tests do not import qmd; the hyphenated-query test fails if the sanitizer is removed (proving it actually guards the behavior).
- falsifier: removing `_sanitize_fts5_query` from the call path does NOT turn the hyphenated-query test red — proves the test is not actually guarding the fix (a mock/theater test).
- verification level required: UNIT_TEST

## Open decisions

- **OD-1 — Module location.** The producing brief proposes
  `P:/.agents/lib/wiki_search/`. Verified facts: `.agents/lib/` does not exist;
  `.agents/scripts/` is the established pattern and already holds
  `wiki_search.py` (the documented replacement boundary) and `qmd_fts5_patch.py`.
  Two viable paths: (a) build the new package at `.agents/lib/wiki_search/` and
  re-point the existing `scripts/wiki_search.py` shim to delegate to it; (b)
  replace the shim's internals in place under `.agents/scripts/`. **Selection
  criterion:** lowest future coupling + consistency with the existing
  replacement-boundary docstring. The author leans (a) if a package is wanted
  for `python -m wiki_search`, but the fresh session should confirm against the
  operator's `.agents/` layout preference before creating a new top-level dir.
- **OD-2 — DB reuse vs. new (see MIG-01).** Reuse is lower-cost (content
  already indexed) but couples the wrapper to qmd's schema; a new DB is cleaner
  but requires an indexer and a re-index of ~400 concepts. Decide after
  inspecting the qmd FTS5 schema read-only.
- **OD-3 — Retiring qmd.** This handoff builds the replacement; it does NOT
  uninstall qmd or delete the `.patch` files. A separate, operator-gated step
  should flip consumers fully off qmd and remove the patches once the wrapper
  has run cleanly. (Destructive git / dependency removal is human-gated per
  AGENTS.md.)

## Hard constraints

- **Stdlib only.** No `pip install` for the wrapper itself. `sqlite3, json,
  pathlib, argparse` only. (Vector search is explicitly dropped, so no
  `sqlite-vec`, no `sentence-transformers`.)
- **Port the quoting fix verbatim in behavior.** The replacement MUST replicate
  `_sanitize_fts5_query`'s per-token quoting. This is the single non-obvious
  correctness invariant; getting it wrong reintroduces the exact bug the patch
  was written to fix.
- **English-only.** Docstrings, comments, identifiers, CLI output — all English.
  (qmd's source is partially Chinese-language; the replacement removes that
  readability burden.)
- **No silent success.** If the DB can't be opened or a query is malformed,
  fail fast with an actionable message (mirror `WikiSearchError` in the
  existing shim).
- **Preserve the replacement boundary.** Whatever the location, consumers must
  import the wrapper, not qmd. Do not re-introduce direct `from qmd import …`
  in consumer code.
- **Non-destructive.** Do not delete qmd, the patches, or the existing DB during
  this work. Build alongside; cutover is a separate operator-gated step.

## Cross-reference couplings

- **Parent handoff** `qmd-viability-evaluation-20260725`: this work implements
  that handoff's "Option D" and closes its Track B (qmd architecture) decision
  in favor of replace.
- **`qmd-patch-durability-strategy.md`**: this handoff is the re-evaluation that
  concept's trigger (R2 / lines 86, 133, 154) was written to surface. On
  successful cutover, that concept should be updated (superseded or marked
  "resolved by replacement") — promote that decision when closing.
- **`session-friction-fixes-20260727` (SF-01)**: documented the FTS5 fix as a
  friction item with an initial (incorrect) SQL-injection hypothesis;
  `qmd_fts5_patch.py` corrected the root cause to FTS5 query-syntax. This
  handoff's TEST-01 materializes the regression test SF-01 lacked.
- **`wiki_search.py` shim**: the new wrapper's public surface (`search`,
  `add_document`, `list_documents`, `info`) should match the shim's so existing
  consumers need no changes beyond the import target.
- **`agents-md-construction-best-practices.md`**: progressive-disclosure — keep
  the wrapper's API small (search + minimal index/list), do not re-expose the
  four dropped components.

## Explicit non-goals

- **Not** uninstalling qmd or deleting the `.patch` files (operator-gated, OD-3).
- **Not** building vector search, RRF, expansion, or reranking — evaluated as
  marginal-or-negative and explicitly out of scope.
- **Not** a general-purpose search engine. This serves ~400 wiki concepts;
  do not generalize prematurely.
- **Not** rewriting qmd's indexer wholesale. Reuse the indexed DB if the schema
  permits (MIG-01); only build a new indexer if reuse is infeasible.
- **Not** changing consumer call sites in this handoff beyond what the wrapper's
  API parity makes free.

## Resumption protocol

A cold-start session resuming this handoff:

1. **Read** `qmd_fts5_patch.py` (the quoting fix to port) and
   `wiki_search.py` (the boundary to preserve) — both in Read-first.
2. **Resolve OD-1** (location) and **OD-2** (DB strategy) before writing code —
   inspect `~/.config/qmd/qmd.db` schema read-only with `sqlite3`/`PRAGMA`.
3. **Build PKG-01**, porting `_sanitize_fts5_query` behavior exactly.
4. **Build TEST-01** alongside (the regression test does not exist yet — see
   Evidence-verification correction #3).
5. **Run the acceptance criteria** in order; criteria #1 and #2 are the
   discriminating tests for the quoting + implicit-AND invariants.
6. **Do not** uninstall qmd or delete patches on success — that is OD-3,
   operator-gated.
7. On green: update `qmd-patch-durability-strategy.md` to record the replacement
   decision (Cross-reference couplings), and propose cutover to the operator.

## Suggested next invocation

`/go` (plain-language task) to implement PKG-01 + TEST-01 once OD-1/OD-2 are
resolved; or `/plan` if the fresh session wants to lock the package layout and
DB strategy into a written plan before coding. After implementation, `/check`
against the acceptance criteria, then `/review` before cutover (this touches the
search path other sessions depend on — proactive-verification triggers apply).

## Last user message (verbatim)

> Write a handoff document for replacing qmd with a minimal FTS5-only search
> wrapper. Save it to P:/docs/handoffs/qmd-fts5-replacement-20260727/HANDOFF.md
> [covering: OBJECTIVE replace qmd v0.1.2 with a ~200-LOC workspace-owned
> SQLite FTS5 search wrapper; BACKGROUND citing qmd-patch-durability-strategy,
> qmd-viability-evaluation-20260725, agents-md-construction-best-practices;
> KEY FINDINGS (FTS5 only valuable component; vector/RRF/expansion/reranking
> marginal-or-negative; upstream dead; 4+ patches; broken test imports fixed;
> _sanitize_fts5_query is the correct per-token FTS5 quoting approach); DESIGN
> at P:/.agents/lib/wiki_search/, must provide qmd-search-equivalent, must NOT
> need vector/RRF/expansion/reranking, must handle FTS5 escaping; reuse
> ~/.config/qmd/qmd.db or new DB; ACCEPTANCE CRITERIA 1-6; use /handoff chain
> header format with Read-first, acceptance criteria, and falsifier sections.]

## Epistemic labels

- **[FACT]** — database existence/size, `_sanitize_fts5_query` location and
  algorithm, existing shim, `.agents/` layout, three `.patch` files, qmd
  upstream-dead (cited), the three evidence-verification corrections. All
  grounded in tool output this authoring pass or cited wiki/handoff receipts.
- **[INFERENCE]** — "4 of 5 components add cost without value for this corpus"
  synthesizes the producing session's component-value table; the per-component
  dispositions (drop) are the producing session's evaluation, not re-measured
  by this author. The author leans (a) on OD-1 — labeled as a lean, not a fact.
- **[UNKNOWN]** — whether a stdlib `sqlite3` reader can query `qmd.db`'s FTS5
  tables read-only without qmd present (MIG-01 must inspect the schema). Whether
  `CORR-003`/`CORR-004` were ever durable anywhere this author did not search.
