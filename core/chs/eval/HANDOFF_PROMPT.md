# Handoff prompt — KB durability completion, round 3 (search-research / CHS / CKS)

Copy everything below into a fresh session.

---

You are completing KB-durability work in `P:/packages/.claude-marketplace/plugins/search-research` (Claude Code plugin monorepo, solo developer, Windows 11). Read `P:/.claude/CLAUDE.md` (Constitution v9) and `core/chs/eval/DURABILITY_STATUS.md` (source of truth for wired vs dormant vs broken) before touching anything.

**Authorization: the full work plan below is pre-authorized. Do not stop to ask permission between items.** Stop only for destructive actions (deleting user data, operating on the live DB in place) or when evidence contradicts this brief — in that case, report the contradiction with file:line evidence and continue with the rest.

## Verified state (2026-07-07)

- Provenance layer wired on CHS sessions path: `embedding_runs` table + JSON manifests, per-row `embedding_run_id`, model/dim resolution (flags > `embeddings_config` > defaults), single-transaction backfill with fail-fast dim guard, `--golden-cases`/`--min-recall` post-run eval gate, model/dim-aware `search_semantic_sessions`.
- Golden eval: `core/chs/eval/retrieval_eval.py` harness (handles TEXT message_id and legacy integer id result shapes); `golden_cases.jsonl` = 26 DB-sourced cases pinned by `session_key`; generator `generate_golden_cases.py --db <path>`.
- Baseline: FTS recall 0.115 on the work copy `data/chs_eval_work.db` (2 GB). This number reflects XML-heavy `first_prompt` query extraction, NOT search health. Only 454/2752 sessions have embeddings.
- `indexer.py` and `config.py` hardcoded-model sites fixed (resolve_model; 384 aligned).
- Prior sessions shipped three verified false claims: "already done" existence claims (×2, caught by red-team) and "FTS5 doesn't support parameterized MATCH" (false — see item 2). Every claim you ship must be backed by file:line or test output. A status table is not evidence.

## Work plan — execute all, in order

**1. Complete embeddings on the work copy and record the real semantic baseline.**
Run `backfill_embeddings` against `data/chs_eval_work.db` (NOT the live DB) until all sessions with text are embedded (2298 pending). Batch if the daemon is slow; the script is resumable (WHERE embedding IS NULL). Then run the semantic-sessions eval via `--golden-cases core/chs/eval/golden_cases.jsonl --min-recall 0.0` and record mean recall in DURABILITY_STATUS.md as the regression floor. If recall is near zero, improve `generate_golden_cases.py` query extraction (strip XML/command wrappers harder, prefer human sentences; consider using summary_short as query when available), regenerate, re-run — the queries must be things a human would actually type.

**2. Fix FTS MATCH parameterization properly (top residual gap in DURABILITY_STATUS.md).**
Current state: `search.py` interpolates `MATCH '{escaped_query}'` (≈lines 163/192/197/237); injection safety hangs entirely on quote-doubling in `escape_fts5_query` (`utils.py`). FTS5 DOES support `MATCH ?`. Correct fix: (a) `**`-glob and grep ALL callers of `escape_fts5_query` across the package — some may rely on interpolation-style escaping; (b) split the function: FTS5-syntax escaping (keep) vs SQL-quote doubling (remove for parameterized callers); (c) revert the four MATCH sites to bound `?` parameters; (d) tests: a query containing `'; DROP TABLE sessions;--`, quotes, brackets, and FTS operators must neither error nor inject; recall on the 26 golden cases must not regress vs the recorded FTS baseline.

**3. Wire SmartChunker into CKS ingestion (decision made: wire, don't delete — task #1272).**
`core/cks/document_ingest.py` uses positional `DocumentChunker` (sequential `chunk_index`). Replace its chunking internals with `SmartChunker.chunk_with_metadata(text, doc_id)` so every CKS chunk carries `chunk_id` (content-addressed), `text_sha256`, `chunker_name/version`. Grep `DocumentChunk` consumers first; extend the dataclass with identity fields rather than breaking the interface. Migration script re-emits existing chunks under content-addressed IDs into a NEW table/namespace — never overwrite the working index. Tests: identity stability across rebuilds; chunk-count parity old-vs-new on the same document.

**4. Deprecation drill on the work copy (the whole point of this architecture).**
`--re-embed --model <distinct-name>` (same dim is fine), gate against golden cases. Verify: two+ `embedding_runs` rows, manifests on disk, mixed-state WARNING fires during partial state, `search_semantic_sessions` raises with wrong `expected_model` after cutover. Record drill outcome + timings in DURABILITY_STATUS.md.

**5. Ship `/chs-eval` (task #1274).**
Skill under `skills/chs-eval/SKILL.md` following the repo convention (check an existing skill for structure): runs the golden eval against the configured DB, prints per-case + mean recall, nonzero exit below threshold. Artifacts to `.claude/.artifacts/{terminal_id}/chs-eval/` per the monorepo convention — never into the skill's own directory.

**6. Close out.**
Update DURABILITY_STATUS.md (move closed items to wired; keep gaps honest). Bump `.claude-plugin/plugin.json` version (version-keyed cache). Full test run: `pytest core/chs/tests/ tests/ tests/unit/test_smart_chunker.py`. End with an evidence ledger: every "done" claim → file:line or test output.

## Gotchas (cost prior sessions real time)

- Absence claims require a `**`-glob of the package root, not one subdir.
- Sandboxed mounts of P: may serve freshly written files stale or truncated. Verify with host-side reads; definitive check is pytest on the user's machine (Python 3.11+; `core/__init__.py` uses `datetime.UTC`).
- `escape_fts5_query` mangles queries aggressively (strips `.`/`,`/`?`, rewrites tokens) — when FTS results look wrong, inspect the escaped query first.
- Stale `__pycache__` can execute old bytecode while tracebacks display new source; clear it when traceback lines look impossible.
- Never operate on the live DB (`P:/.data/chat_history.db`) in place. Work copy: `data/chs_eval_work.db`.
