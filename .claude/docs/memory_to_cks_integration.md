# Memory to CKS Integration - COMPLETE

**Date**: 2026-03-14
**Status**: ✅ Operational

## Problem Solved

Memory files from `C:\Users\brsth\.claude\projects\P--\memory\` were not integrated into CKS, causing repeated architecture mistakes (e.g., Git + multi-terminal race conditions).

## Solution Implemented

### 1. Memory Ingestion Script

**File**: `P:\.claude\hooks\scripts\ingest_memory_to_cks.py`

**Features**:
- Parses 40 memory files into 331 chunks by `##` headers
- Auto-categorizes as pattern/knowledge/correction
- Adds source file metadata
- Test-run mode for verification

**Usage**:
```bash
# Test run (no ingestion)
python P:\.claude\hooks\scripts\ingest_memory_to_cks.py --test-run

# Actual ingestion
python P:\.claude\hooks\scripts\ingest_memory_to_cks.py

# Ingest single file
python P:\.claude\hooks\scripts\ingest_memory_to_cks.py --file questioning_patterns.md
```

**Ingestion Results**:
- 40 files processed
- 331 chunks created
- By type: 141 knowledge, 128 pattern, 62 correction

### 2. Hook Trigger Word Extensions

**File**: `P:\.claude\hooks\PreToolUse_investigation_gate.py` (line 82)

**Added Triggers**:
```python
HOOK_TRIGGERS = [
    'debug', 'investigate', 'diagnose', 'monitor', 'stuck', 'error',
    # NEW: Memory-specific triggers
    'git', 'multi-terminal', 'concurrent', 'race condition',
    'ttl', 'time to live', 'session state', 'shared state',
    'state management', 'cache', 'storage',
]
```

## How It Works Now

### Before (Manual Memory Check)
```
User: "How should we handle state for Ralph loops?"
AI: "Use Git as source of truth" ❌
User: "But Git has race conditions..."
AI: [Checks memory] "You're right, use terminal-local files"
```

### After (Automatic CKS Retrieval)
```
User: "How should we handle state for Ralph loops?"
[Hook detects 'state' trigger]
[Hook queries CKS via query_cks_daemon()]
[CKS returns working_principles.md + questioning_patterns.md]
AI: "Based on memory: use terminal-local files (Git has race conditions)..." ✅
```

## Verification

Test queries confirmed CKS finds memory content:
- ✅ "git multi-terminal race condition" → reasoning_flaws.md
- ✅ "questioning patterns" → questioning_patterns.md
- ✅ "working principles" → working_principles.md
- ✅ "time to live" → questioning_patterns.md

## Trigger Words Now Active

When user messages contain these terms, CKS auto-retrieval activates:
- **Infrastructure**: git, multi-terminal, concurrent, race condition, ttl, session state, shared state, cache, storage
- **Investigation**: debug, investigate, diagnose, monitor, stuck, error

## Re-Ingestion

To update CKS after memory changes:

```bash
# Re-ingest all memory files
python P:\.claude\hooks\scripts\ingest_memory_to_cks.py

# Or re-ingest specific file
python P:\.claude\hooks\scripts\ingest_memory_to_cks.py --file questioning_patterns.md
```

## Technical Details

- **CKS Location**: `P:/__csf/data/cks.db`
- **Memory Location**: `C:/Users/brsth/.claude/projects/P--/memory/`
- **Hook**: `PreToolUse_investigation_gate.py` (registered in `PreToolUse.py` router)
- **CKS Auto-Retrieval**: Uses `query_cks_daemon()` with caching
- **Chunking Strategy**: Splits by `##` headers, max 919 chars per entry

## Next Steps

Memory files now proactively surface during architecture decisions. The system prevents the class of mistakes documented in:
- `questioning_patterns.md` - Meta-cognitive patterns
- `working_principles.md` - Engineering heuristics
- `reasoning_flaws.md` - Reasoning anti-patterns

No manual memory checking required - CKS auto-retrieval handles it.

## Multi-Terminal Safety

**Problem**: If 5 terminals start simultaneously, all would detect stale memory and trigger concurrent ingestion, wasting resources and potentially causing contention.

**Solution**: PID-based lock file with automatic stale lock cleanup.

**Implementation**:
- **Lock File**: `P:/.claude/state/memory_cks_ingest.lock`
- **Lock Contents**: `{"pid": 12345, "timestamp": "2026-03-14T..."}`
- **Acquisition Logic**:
  1. Try to create lock file with current PID
  2. If lock exists, check if it's stale (>5 minutes) or PID is dead
  3. If stale/dead, take over the lock; otherwise skip
  4. Always release lock in `finally` block

**Verification** (2026-03-14):
```
Simulating 5 terminals starting simultaneously...
Terminal 1: [INGESTED] ✅ Memory CKS auto-ingestion
Terminal 2: [SKIPPED]
Terminal 3: [SKIPPED]
Terminal 4: [SKIPPED]
Terminal 5: [SKIPPED]

Summary:
  Terminals that ingested: 1/5
  Terminals that skipped: 4/5
  Result: PASS - Multi-terminal safe!
  Lock file cleanup: PASS
```

**Behavior**:
- First terminal acquires lock and ingests
- Other terminals detect lock and skip gracefully
- Lock automatically released after ingestion (even on failure)
- Stale locks (5+ minutes) cleaned up automatically
- No manual intervention required
