# Handoff prompt — KB durability work (search-research / CHS)

Copy everything below into a fresh session.

---

You are continuing KB-durability work in `P:/packages/.claude-marketplace/plugins/search-research` (Claude Code plugin monorepo, solo developer, Windows 11). Read `P:/.claude/CLAUDE.md` (Constitution v9) first — key rules: fail fast, verify with evidence, state planned changes and wait for "do it", sequential file edits, absence claims require a `**`-glob of the package root (not one subdir).

## Verified state (2026-07-07, search-research v0.1.71, all claims file-backed)

DONE and tested (32 tests green):
- `core/chunking/smart_chunker.py` — content-addressed chunk IDs: `chunk_with_metadata(text, doc_id)` returns records with `chunk_id = sha256(doc_id|char_start|char_end|text_sha256)`, chunker name/version/params. Tests: `tests/unit/test_smart_chunker.py` (9).
- `core/chs/schema.sql` + `core/chs/db.py` — `embedding_runs` table, `embedding_run_id` columns on sessions/turns, `ensure_embedding_run_schema()` migration, `first_prompt` added to sessions (was missing vs code).
- `core/chs/scripts/backfill_embeddings.py` — run manifests (`<db_dir>/embedding_runs/<run_id>.json` + table row), model/dim resolution (`--model`/`--dim` > `embeddings_config` > defaults), single-transaction writes, fail-fast dim guard, `--re-embed`, `--golden-cases <path> --min-recall` post-run eval gate. Returns a dict now (was int). Tests: `core/chs/tests/test_backfill_run_provenance.py` (6), `tests/test_backfill_embeddings.py` (rewritten, 5).
- `core/chs/eval/retrieval_eval.py` — golden-case recall harness; stable-key matching (message_id, content sha256, session_key); FTS + semantic-sessions modes; CI exit codes. Tests: `core/chs/tests/test_retrieval_eval.py` (9).
- `core/chs/search.py::search_semantic_sessions` — model/dim-aware: infers query dim (no hardcoded 384), `expected_model` filter, WARNING on mixed state, raises on total mismatch. Tests: `core/chs/tests/test_semantic_model_aware.py` (6).
- `core/chs/eval/DURABILITY_STATUS.md` — honest scope doc. Read it; it is the source of truth for wired vs dormant.

Also done earlier (separate plugin): cc-model-router v0.2.18 — cheap-cognitive exemplars route to haiku; eval verified (background precision 1.0, reasoning recall 1.0).

## Outstanding (priority order)

1. **Populate `core/chs/eval/golden_cases.jsonl`** (~50 real cases from the user's chat history DB, `P:/__csf/data/chat_history.db`). Format: `core/chs/eval/golden_cases.example.jsonl`. Use `required_session_keys` for the semantic gate. Everything is wired to consume this file; it is the last missing piece of the eval loop.
2. **SmartChunker fate (needs user decision first):** CKS ingestion (`core/cks/document_ingest.py`) uses its own positional `DocumentChunker`; SmartChunker has zero production consumers. Either wire it in with a re-chunk migration, or delete it. Do not leave it dormant.
3. **Last hardcoded-model sites:** `core/chs/indexer.py:253` (literal model string + 384, can race backfill), `core/chs/config.py:25` (`DEFAULT_EMBEDDING_DIMENSIONS = 768` contradicts CHS 384 — check callers before changing).

## Gotchas

- A prior red-team run (artifacts: `P:/.claude/.artifacts/*/red-team/20260707-100616/`) overturned "already done" claims twice. Verify existence claims by grep/read at point of use; a status table is not evidence.
- If working via a sandboxed mount of P:, freshly written files may be served stale/truncated to the sandbox. Verify with host-side reads; run tests against exact-content copies if needed. Definitive check on the user's machine: `pytest core/chs/tests/ tests/ tests/unit/test_smart_chunker.py` from the search-research root (Python 3.11+; `core/__init__.py` uses `datetime.UTC`).
- After plugin edits: bump `.claude-plugin/plugin.json` version and reload (version-keyed cache).
- Cutover discipline for any model swap: copy DB → `--re-embed --model X --dim N` on the copy → `--golden-cases` gate must pass → swap by config. Never re-embed the live DB in place.
