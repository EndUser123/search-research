# Handoff prompt — KB durability completion (search-research / CHS / CKS)

Copy everything below into a fresh session.

---

You are completing KB-durability work in `P:/packages/.claude-marketplace/plugins/search-research` (Claude Code plugin monorepo, solo developer, Windows 11). Read `P:/.claude/CLAUDE.md` (Constitution v9) first.

**Authorization: the full work plan below is pre-authorized. Do not stop to ask permission between items.** Stop only if you hit something destructive (deleting user data, touching the live DB in place) or if evidence contradicts this brief.

## Verified state (2026-07-07, search-research v0.1.71)

The CHS sessions path is durability-complete and tested (32+ tests green):
content-addressed chunk IDs in `core/chunking/smart_chunker.py` (`chunk_with_metadata`); `embedding_runs` provenance table + per-row `embedding_run_id` + JSON manifests; `backfill_embeddings.py` with `--model/--dim` resolution (flags > `embeddings_config` > defaults), single-transaction writes, fail-fast dim guard, `--re-embed`, and a `--golden-cases`/`--min-recall` post-run eval gate; model/dim-aware `search_semantic_sessions` (infers query dim, filters mismatched rows loudly, raises on total mismatch); golden eval harness `core/chs/eval/retrieval_eval.py` (stable-key matching: message_id / content sha256 / session_key); `golden_cases.jsonl` populated with 50 session_key-pinned cases (content-hash pins were stripped — they were unmatchable and capped recall at 0.5; the generator is patched, don't re-add them).

`core/chs/eval/DURABILITY_STATUS.md` is the source of truth for wired vs dormant. Update it as you close items.

## Work plan — execute all, in order

**1. Baseline the eval loop (do this first; it validates everything else).**
Copy the live DB (`P:/__csf/data/chat_history.db`) to a work copy. Run `backfill_embeddings --dry-run`, then `--golden-cases core/chs/eval/golden_cases.jsonl --min-recall 0.0` against the copy to get the true baseline mean recall. Record the number in DURABILITY_STATUS.md. If baseline recall is poor (<0.5), diagnose (likely: sessions missing embeddings → backfill first, or queries too long for semantic match → tune generator MAX_USER_LEN and regenerate) before proceeding.

**2. Wire SmartChunker into CKS ingestion (decision already made: wire, don't delete).**
`core/cks/document_ingest.py` uses a positional `DocumentChunker` (sequential `chunk_index`, no content hash). Replace its chunking internals with `SmartChunker.chunk_with_metadata(text, doc_id)` so every CKS chunk carries `chunk_id`, `text_sha256`, `chunker_name/version`. Keep the existing `DocumentChunk` interface if downstream code depends on it — add the identity fields rather than breaking consumers (grep consumers first). Write a migration script that re-emits existing chunks under content-addressed IDs into a NEW table/namespace (never overwrite the only working index), plus tests: identity stability across rebuilds, old-vs-new chunk count parity on the same document.

**3. Kill the last hardcoded-model sites.**
- `core/chs/indexer.py:253`: writes embeddings with a literal model string + 384 and can race a backfill. Route it through the same resolution as `backfill_embeddings.resolve_model` and tag `embedding_run_id` on its writes.
- `core/chs/config.py:25`: `DEFAULT_EMBEDDING_DIMENSIONS = 768` contradicts CHS's 384. Grep every reader of `EMBEDDING_DIMENSIONS`/`embedding_dim` config, determine which paths actually consume 768, then converge on `embeddings_config` (the DB table) as the single source of truth with 384 as fallback. If a 768 consumer exists, document why before changing anything.

**4. Run the deprecation drill end-to-end (the doc's Phase-5 exercise).**
On the DB copy: `--re-embed` with the default model, gate must pass at the step-1 baseline; then simulate a model swap (`--model` with a distinct name, same dim is fine if no second model is installed — the point is exercising run provenance, mixed-state detection, and the gate). Verify: two `embedding_runs` rows, manifests on disk, `search_semantic_sessions` warns/raises correctly when queried with the wrong expected_model. Record the drill outcome in DURABILITY_STATUS.md.

**5. Wire the eval into the workflow.**
Add a skill or slash command (follow the repo's `skills/<name>/SKILL.md` convention) so `/chs-eval` runs the golden eval against the configured DB and reports mean recall. Optionally register a scheduled/weekly smoke run if the repo has a convention for it — check first, don't invent infrastructure.

**6. Close out.** Update DURABILITY_STATUS.md (move closed items to "wired", keep residual gaps honest), bump `.claude-plugin/plugin.json` version, run the full affected test suite (`pytest core/chs/tests/ tests/ tests/unit/test_smart_chunker.py`), and end with an evidence ledger: every "done" claim backed by file:line or a test run output. A status table is not evidence.

## Gotchas (cost prior sessions real time)

- Absence claims require a `**`-glob of the package root, not one subdir. Two prior sessions shipped false "already done / doesn't exist" claims.
- If working via a sandboxed mount of P:, freshly written files may be served stale or truncated to the sandbox. Verify with host-side reads; run tests against exact-content copies if needed. Definitive check is pytest on the user's machine (Python 3.11+; `core/__init__.py` uses `datetime.UTC`).
- Never re-embed or migrate the live DB in place. Copy → operate → gate → swap by config.
- `tests/__init__.py` exists (package-style test imports); clear stale `__pycache__` if tracebacks show source/bytecode mismatch.
- After plugin edits: bump plugin.json version (version-keyed cache).
