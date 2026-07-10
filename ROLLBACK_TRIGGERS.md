# Rollback Decision Triggers

**Created**: 2026-03-15
**Purpose**: Define explicit rollback criteria for each Phase 6 cleanup task.

---

## Rollback Trigger Template

Each cleanup task has:
1. **Rollback triggers**: When to STOP and restore from checkpoint
2. **Checkpoint tag**: Git tag for easy rollback
3. **Recovery time objective (RTO)**: Maximum time to restore service

---

## TASK-019: Remove Legacy Backends

### Rollback Triggers (STOP cleanup, restore from checkpoint)

1. **Test suite failures**:
   - Any test suite fails with > 5% test failures
   - Integration tests fail with import errors
   - Backend health checks fail on migrated backends

2. **Performance regression**:
   - Search latency > 15% slower than baseline
   - Memory usage > 20% higher than baseline
   - Backend timeout errors > 2% of queries

3. **Critical path failures**:
   - `/find` CLI command fails
   - `/all` skill returns no results
   - CKS/CHS queries fail

4. **User-reported issues**:
   - Blocking bug in production
   - Data corruption detected
   - Security vulnerability introduced

### How to Rollback

```bash
# 1. Revert to checkpoint
git revert cleanup-pre-task-019-YYYYMMDD-HHMM

# 2. Verify tests pass
pytest P://__csf/tests/lib/find/ -v
pytest P://packages/.claude-marketplace/plugins/search-research/tests/ -v

# 3. Verify CLI works
python P://__csf/src/cli/nip/search_enhanced.py "test query"

# 4. Notify stakeholders
# Post to #development channel with rollback details
```

### Checkpoint Tag
```
cleanup-pre-task-019-YYYYMMDD-HHMM
```

### Recovery Time Objective
**RTO**: 15 minutes (git revert + test verification)

---

## TASK-020: Remove Legacy Infrastructure

### Rollback Triggers (STOP cleanup, restore from checkpoint)

1. **Import errors**:
   - Any module fails to import
   - Circular import errors
   - Missing dependency errors

2. **Cache/health failures**:
   - Query cache corruption
   - Backend health tracking stops working
   - Streaming search fails

3. **CLI failures**:
   - `search_enhanced.py` crashes
   - LSP query tool fails
   - Memory module fails

### How to Rollback

```bash
# 1. Revert to checkpoint
git revert cleanup-pre-task-020-YYYYMMDD-HHMM

# 2. Verify imports work
python -c "from search import search_stream, QueryCache, BackendHealth"
python -c "from search_research import AsyncSearchRouter"

# 3. Verify CLI works
python P://__csf/src/cli/nip/search_enhanced.py "test query"

# 4. Notify stakeholders
```

### Checkpoint Tag
```
cleanup-pre-task-020-YYYYMMDD-HHMM
```

### Recovery Time Objective
**RTO**: 10 minutes (git revert + import verification)

---

## TASK-021: Remove Legacy Router

### Rollback Triggers (STOP cleanup, restore from checkpoint)

1. **Router failures**:
   - `UnifiedAsyncRouter` fails to initialize
   - `AsyncSearchRouter` crashes
   - Mode routing fails

2. **CLI crashes**:
   - `/find` skill fails completely
   - Search returns no results for all queries
   - Timeout errors on all queries

3. **Integration failures**:
   - CLI importers fail
   - Memory module importers fail
   - Test importers fail

### How to Rollback

```bash
# 1. Revert to checkpoint
git revert cleanup-pre-task-021-YYYYMMDD-HHMM

# 2. Verify router works
python -c "from search_research import AsyncSearchRouter, UnifiedAsyncRouter"

# 3. Verify CLI works
python P://__csf/src/cli/nip/search_enhanced.py "test query"

# 4. Run full integration tests
pytest P://packages/.claude-marketplace/plugins/search-research/tests/integration/ -v

# 5. Notify stakeholders
```

### Checkpoint Tag
```
cleanup-pre-task-021-YYYYMMDD-HHMM
```

### Recovery Time Objective
**RTO**: 20 minutes (git revert + full test verification)

---

## TASK-022: Clean Up Test Files

### Rollback Triggers (STOP cleanup, restore from checkpoint)

1. **Test coverage drops**:
   - Coverage drops > 5% from baseline
   - Critical backend tests missing
   - Integration tests removed

2. **CI failures**:
   - CI pipeline fails
   - Test discovery fails
   - Pytest collection errors

### How to Rollback

```bash
# 1. Revert to checkpoint
git revert cleanup-pre-task-022-YYYYMMDD-HHMM

# 2. Verify test discovery
pytest P://__csf/tests/lib/find/ --collect-only

# 3. Verify coverage
pytest P://packages/.claude-marketplace/plugins/search-research/tests/ --cov=search_research --cov-report=term

# 4. Notify stakeholders
```

### Checkpoint Tag
```
cleanup-pre-task-022-YYYYMMDD-HHMM
```

### Recovery Time Objective
**RTO**: 10 minutes (git revert + test verification)

---

## TASK-023: Final Verification

### Rollback Triggers (STOP, escalate to user)

1. **Any test suite fails**:
   - Unit tests fail
   - Integration tests fail
   - Performance tests fail

2. **CLI issues**:
   - `/find` skill fails
   - `/all` skill fails
   - Any CLI command crashes

3. **Performance regression**:
   - Latency > 10% above baseline
   - Memory usage > 15% above baseline

### How to Rollback

```bash
# 1. Revert to final checkpoint
git revert migration-complete-YYYYMMDD

# 2. Run full test suite
pytest P://packages/.claude-marketplace/plugins/search-research/tests/ -v
pytest P://__csf/tests/lib/find/ -v

# 3. Verify all CLI tools
python P://__csf/src/cli/nip/search_enhanced.py "test query"

# 4. Escalate to user for decision
```

### Checkpoint Tag
```
migration-complete-YYYYMMDD
```

### Recovery Time Objective
**RTO**: 30 minutes (full verification required)

---

## General Rollback Protocol

### Step 1: Identify the Trigger
- Determine which rollback trigger was activated
- Document the specific failure with evidence

### Step 2: Execute Rollback
```bash
# Get checkpoint tag from rollback documentation
git tag -l "cleanup-pre-task-XXX-*" | sort | tail -1

# Revert to checkpoint
git revert <checkpoint-tag>
```

### Step 3: Verify Restoration
- Run affected test suite
- Verify CLI tools work
- Check for import errors

### Step 4: Document and Notify
- Update this document with lessons learned
- Post to #development channel
- Schedule root cause analysis

---

## Checkpoint Naming Convention

```
cleanup-pre-task-XXX-YYYYMMDD-HHMM
migration-complete-YYYYMMDD
```

Examples:
- `cleanup-pre-task-019-20260315-143000`
- `cleanup-pre-task-020-20260315-150000`
- `migration-complete-20260315`

---

## Monitoring During Cleanup

### Continuous Checks
1. **After each task**: Run affected test suite
2. **After each phase**: Run full integration tests
3. **Daily**: Check CLI tool functionality

### Metrics to Monitor
- Test pass rate (target: 100%)
- Search latency (target: < baseline + 10%)
- Memory usage (target: < baseline + 15%)
- Error rate (target: < 1%)

### Escalation Path
1. **Test failures**: Retry once, then rollback
2. **Performance regression**: Rollback immediately
3. **User-reported issue**: Rollback immediately, investigate later

---

## References

- Migration Plan: `P://packages/.claude-marketplace/plugins/search-research/MIGRATION.md`
- API Differences: `P://packages/.claude-marketplace/plugins/search-research/API_DIFFERENCES.md`
- Test Suite: `P://packages/.claude-marketplace/plugins/search-research/tests/`
- CLI Tool: `P://__csf/src/cli/nip/search_enhanced.py`
