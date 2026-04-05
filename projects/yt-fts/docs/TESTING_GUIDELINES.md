# Testing Guidelines: Mocks vs Real Execution

**Status:** Draft - 2026-01-26
**Context:** SQL COUNT bug (COUNT vs COUNT DISTINCT) was not caught by mock-based tests.

## Core Principle

> **Real execution catches both implementation and behavioral bugs. Mocks only catch implementation bugs.**
>
> When unsure, use real execution.

## Decision Tree

```
What does the test verify?
├─ Function contract / API interface?
│  └─→ Mocks OK (verifying shape, not behavior)
│
├─ Internal logic (algorithms, calculations)?
│  ├─ Simple: Mocks OK
│  └─ Data access (SQL, files, external APIs): Real execution
│
├─ Data correctness (counts, sums, aggregations)?
│  └─→ Real execution REQUIRED
│     Example: SQL COUNT, stats calculations, financial logic
│
├─ User-visible behavior (output, display, timing)?
│  └─→ Real execution REQUIRED
│     Example: Console output, progress bars, UX flows
│
└─ Integration between modules?
   └─→ Real execution REQUIRED
      Example: Database + business logic, API + processing
```

## When Mocks Are Appropriate

| Use Case | Example | Why Mock OK |
|----------|---------|-------------|
| Interface contracts | Function receives dict with correct keys | Verifying shape, not value |
| "Was X called?" | `coordinator.add_task()` invoked | Implementation detail |
| Isolating units | Test algorithm independent of DB | Fast feedback |
| External services | YouTube API, S3 buckets | Avoid rate limits, cost |

## When Real Execution Is Required

| Use Case | Bug That Mocks Miss | Why Real Execution |
|----------|---------------------|-------------------|
| SQL queries | `COUNT(v.id)` vs `COUNT(DISTINCT v.id)` | Mock returns fixed value |
| Data aggregation | Wrong sum formula | Mock doesn't exercise query |
| Stats calculations | Off-by-one errors | Mock returns pre-computed |
| Output formatting | Wrong console output | Mock doesn't capture actual output |
| Integration bugs | DB schema mismatch | Mock doesn't touch real DB |

## Categorization Framework

### Category A: Keep Mocks (Low Risk)

Tests that verify:
- Function signatures
- Data structure shapes
- "Was method called?" contracts

### Category B: Refactor to Real Execution (High Risk)

Tests that verify:
- Database queries (SQL correctness)
- Statistics/calculations
- Data transformations
- Output formatting
- Integration between modules

### Category C: Delete (No Value)

Tests that:
- Only test the mock itself
- Verify nothing about production code
- Are duplicates of real-execution tests

## Test Strategy by Layer

| Layer | Strategy | Example |
|-------|----------|---------|
| Unit (single function) | Mocks OK for simple logic | Pure Python calculations |
| Integration (module boundary) | Real execution | DB + business logic |
| System (end-to-end) | Real execution | CLI command with real DB |
| SQL queries | Real execution ALWAYS | Any database access |

## Examples

### ❌ WRONG: Mock Test for SQL Logic

```python
@patch("yt_fts.db.channels.get_db_connection")
def test_channel_stats_count(self, mock_conn):
    # Mock returns fixed value - CANNOT catch SQL bugs
    mock_result = MagicMock()
    mock_result.fetchone.return_value = [100]
    mock_conn.execute.return_value = mock_result

    stats = get_channel_stats("UC123")
    assert stats["total"] == 100  # Passes even with COUNT(v.id) bug!
```

### ✅ CORRECT: Real Execution for SQL

```python
def test_channel_stats_counts_unique_videos_not_join_rows(tmp_path):
    # Creates real DB, runs real SQL
    db_path = create_test_db(tmp_path)

    # 2 videos, 4 subtitles each
    insert_test_data(db_path, videos=2, subtitles_per_video=4)

    stats = get_channel_stats_with_subs_and_playlists("UC123")

    # Bug would return 8 (2 × 4), correct returns 2
    assert stats["total"] == 2
```

## Implementation Strategy

### Phase 1: Discovery (Current)

```bash
# Find all mock-based tests
grep -r "MagicMock\|Mock\|patch" tests/ --include="*.py" -l > mock_tests.txt
# Result: 116 files
```

### Phase 2: Categorization

For each mock test file:
1. **What does it test?** (SQL, logic, interface, output?)
2. **Category A/B/C?** (Keep / Refactor / Delete)
3. **Priority?** (High: SQL/stats, Medium: output, Low: interface)

### Phase 3: Incremental Refactor

Per module (e.g., `tests/test_db_channels.py`):

1. **Create integration test** with real DB
2. **Verify new test fails** with current bug (if present)
3. **Fix bug** (if needed)
4. **Verify new test passes**
5. **Run regression** (`pytest tests/test_db*.py`)
6. **Remove/replace old mock tests** that are now redundant
7. **Commit**

### Phase 4: Guidelines Update

- Add to CLAUDE.md: "Behavioral vs Implementation Bugs"
- Add to TDD skill: Mock vs Real Execution decision tree
- Code review: Flag new mock tests for SQL/data logic

## Priority Matrix

| Module | Mock Tests | Priority | Reason |
|--------|-----------|----------|--------|
| `test_db_channels.py` | High | **P0** | SQL queries - direct bug impact |
| `test_database_stats.py` | Real DB | **P0** | Already correct - keep as reference |
| `test_batch_channel_helpers.py` | High | **P1** | Stats loading - data correctness |
| Display/output tests | Mixed | **P2** | Some need real execution |
| Simple helpers | Low | **P3** | Interface contracts OK |

## Success Criteria

- [ ] All SQL query tests use real DB
- [ ] All stats/calculation tests use real data
- [ ] Mock tests only for interface contracts
- [ ] New bug (SQL COUNT) has regression test
- [ ] Guidelines documented in CLAUDE.md
