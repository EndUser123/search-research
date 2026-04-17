# Pre-Mortem: CHS FTS5 Consolidation

**Date**: 2026-03-28
**Target**: CHS FTS5 reindex from history.jsonl → chat_history.db

## Step 0: Constraints from CLAUDE.md

- Multi-terminal safety required (shared state must handle concurrent access)
- Evidence tiers for all claims (cite source)
- Hook design: no external API calls, standalone operation
- Path resolution: `P:/__csf/` convention for derived data

## Step 0.7: Kill Criteria

- If reindex produces <100k messages when source has 465k entries → abandon approach
- If FTS5 search returns garbage/no results for known queries → investigate
- If daemon can't connect to database after restart → investigate

## Step 1: Failure Scenario

"It's 6 months later. CHS FTS5 search is completely broken. The database is empty or corrupt. No search results return."

## Step 1.5: Fix Side Effects

The reindex approach introduces:
- **New risk**: Dependency on `PYTHONPATH=P:/packages/search-research/core` to work (not standard)
- **New risk**: The package's `search_research` import path is broken (can't import `search_research.core`)
- **New risk**: Database path hardcoded to `P:/__csf/data/` but install location is `P:/packages/search-research/`

## Step 2: Brainstorm Failure Causes (10+)

### Tech/Process Failures
1. **import_resolution** - `search_research.core` import fails because package maps `core/` to `search_research/` but `core/` doesn't have proper namespace init
2. **text_extraction_bug** - `extract_text_content` still stores JSON strings for some message types (tool_result content arrays not handled)
3. **turn_pairing_bug** - Turn building logic pairs wrong messages (adjacent pairs assume user→assistant pattern)
4. **database_locked** - WAL mode conflicts with daemon's concurrent access
5. **schema_drift** - FTS5 triggers not firing (schema.sql not applied or race condition on first insert)
6. **idempotency_bug** - Re-running reindex doesn't replace existing data (UPSERT not working properly)
7. **checkpoint_gap** - First reindex run consumed 465k entries, second run sees 0 new entries (already processed)
8. **path_staleness** - Discovery file points to stale daemon that crashed, new daemon on different pipe
9. **memory_bloat** - Loading entire 2.7GB history.jsonl into memory causes OOM on constrained systems
10. **timestamp_parsing** - Millisecond vs second timestamp confusion (parse_claude_timestamp divides by 1000)

### External Failures
11. **source_data_gone** - User moves/deletes `~/.claude/history.jsonl`
12. **database_moved** - User moves `P:/__csf/data/` contents
13. **permission_denied** - Database file locked by antivirus or other process

## Step 2.5: Cascade Analysis (Risks ≥ 6)

**import_resolution (7)**: Would prevent daemon startup entirely
→ Daemon falls back to legacy behavior → FTS5 never used → Search returns no results

**text_extraction_bug (8)**: Content stored as JSON strings instead of readable text
→ FTS5 indexes JSON → Queries for plain text return nothing
→ User sees "no results" for valid queries

**schema_drift (7)**: Triggers not created
→ FTS5 tables stay empty → BM25 returns nothing
→ Search appears broken

## Step 2.6: AI/LLM-Specific Risks

- **Hallucination**: `extract_text_content` assumed OpenAI format (`{"text": ...}`) but Claude Code uses `{"content": ...}` - already caught and fixed
- **Context overflow**: Running full reindex (~7 min) might cause LLM to lose track of progress mid-run
- **Tool misuse**: Edit vs Write tool confusion could corrupt the script during concurrent modification

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| import_resolution | Package import path broken | Tech |
| text_extraction_bug | Content extraction incomplete | Tech |
| turn_pairing_bug | Wrong pairing logic | Tech |
| database_locked | WAL mode conflict | Tech |
| schema_drift | Trigger not created | Tech |
| idempotency_bug | UPSERT not working | Tech |
| checkpoint_gap | Checkpoint prevents reingest | Process |
| path_staleness | Discovery file stale | Tech |
| memory_bloat | OOM on large file | Tech |
| timestamp_parsing | Time unit confusion | Tech |
| source_data_gone | External dependency | External |
| database_moved | External dependency | External |
| permission_denied | OS-level blocking | External |

## Step 3.5: Reference Class Forecasting

Historical patterns from similar migrations:
- ADR-20260321/25 consolidations had import path issues
- Previous `import_history_fast.py` had content extraction bugs
- Multi-terminal daemon startup had zombie process accumulation

## Step 3.6: Success Theater Detection

- **"389k messages indexed"** - metric looks good but doesn't verify FTS5 triggers fired
- **"FTS5 search tested"** - tested with one query but didn't test edge cases (empty results, JSON content)
- **"Database populated"** - counts check passes but content quality not verified

## Step 3.8: Operational Verification

- ✅ Verified: `messages_fts` count matches `messages` count (389,332)
- ✅ Verified: Sample content shows plain text (not JSON strings)
- ✅ Verified: FTS5 query returns results for known phrase
- ✅ Verified: CRIT-002 - `tool_result` content stored as JSON string (NOT extracted) - confirmed via DB sample ID=5
- ❌ Not verified: Daemon restart reconnection
- ❌ Not verified: Multi-terminal concurrent access
- ❌ Not verified: Incremental reindex (checkpoint behavior)

### CRIT-002 Verification (2026-03-28)

**Status: CONFIRMED BUG**

Message ID=5 in database shows content:
```json
{"tool_use_id":"call_b8e2z1e2n3","type":"tool_result","content":"     1→---\n     2→name: '/main'\n     3→category: 'System'..."}
```

**Root cause**: `extract_text_content()` at `reindex_from_jsonl.py:90-91` handles `tool_result` as `else: json.dumps(block)` instead of extracting `block.get("content")`.

**Fix required**: Add `elif block.get("type") == "tool_result": parts.append(block.get("content", ""))` in the content list loop.

## Step 4: Risk Ratings

| ID | Cause | L | I | Score |
|----|-------|---|---|-------|
| text_extraction_bug | Content still JSON for some types | 3 | 3 | 9 |
| schema_drift | FTS5 triggers not created | 2 | 3 | 9 |
| path_staleness | Discovery file stale | 2 | 3 | 9 |
| import_resolution | Package import broken | 3 | 2 | 8 |
| checkpoint_gap | Can't reindex incrementally | 2 | 3 | 8 |
| turn_pairing_bug | Wrong pairs built | 2 | 3 | 8 |
| idempotency_bug | Reindex no-ops | 2 | 3 | 8 |
| database_locked | Concurrent access fails | 2 | 2 | 6 |
| memory_bloat | OOM on large file | 2 | 2 | 6 |
| timestamp_parsing | Time offset errors | 1 | 3 | 5 |
| source_data_gone | External dependency | 1 | 3 | 5 |
| database_moved | External dependency | 1 | 3 | 5 |
| permission_denied | OS-level blocking | 1 | 2 | 4 |

## Step 5: Top 3 Risks + Actions

### CRIT-001 | FTS5 triggers may not fire for all insert paths (Risk 9)
- **Evidence**: schema.sql has triggers but reindex uses direct INSERT statements
- **Action**: Verify triggers fire by checking `SELECT COUNT(*) FROM turns_fts` matches expected after reindex

### CRIT-002 | Text extraction may still miss tool_result content arrays (Risk 9)
- **Evidence**: Sample ID=5 shows `tool_result` stored as JSON string `{"tool_use_id":"...", "content":"..."}`
- **Action**: Check all tool_result messages have extracted content, not raw JSON

### CRIT-003 | Daemon path resolution may fail on restart (Risk 8)
- **Evidence**: `_csf_root = Path("P:/__csf")` is hardcoded, package at `P:/packages/search-research/`
- **Action**: Test daemon restart and verify `_get_chs_db_path()` returns correct path

## Step 6: Warning Signs to Monitor

- Database file size not growing after reindex
- FTS5 query returns 0 results for queries that should match
- Daemon fails to start with "pipe busy" error repeatedly
- Reindex run says "0 messages ingested" on subsequent runs (checkpoint working) or "389k messages" again (checkpoint not working)

## Step 7: Adversarial Validation (8 agents)

### Testing Agent Findings
- **database_locked (Risk 6)**: Multi-terminal concurrent access NOT verified
  - Action: Add concurrent access test with threading

### Performance Agent Findings
- **idempotency_bug**: Check-then-act should be INSERT OR IGNORE (eliminates 465k SELECTs)
- **memory_bloat**: OOM risk - process incrementally by session, don't accumulate all in memory
- **Recommended fix order**: INSERT OR IGNORE → batch commits → executemany() → streaming

### Compliance Agent Findings
- Security controls (chat_search_security.py) not integrated into core CHS data flow
- raw_json column credential exposure risk
- P:/__csf/ path convention validation question

### Logic Agent Findings
- CRIT-001 mischaracterizes current risk (init_db vs schema.sql consistency)
- CRIT-003 underconfident (timestamp parsing)
- **tool_result handling confirmed missing** in extract_text_content
- Incremental reindex support via indexer_checkpoint
- Turn pairing with assistant-first sessions question

### QA Agent Findings
- Timestamp format question: Real history.jsonl shows seconds not milliseconds
- tool_result content arrays - theoretical vs actual question

### Quality Agent Findings
- Unused indexer_checkpoints table (maintenance burden)

### Critic Agent Findings
- tool_result concrete example needed
- Integration test question: full reindex + FTS5 query

## Summary

The reindex script works for initial population, but has verified issues:
1. **CRIT-002 CONFIRMED**: tool_result content stored as JSON string (not extracted)
2. Daemon restart path not tested
3. Incremental reindex (checkpoint) behavior unknown
4. Multi-terminal concurrent access not tested
