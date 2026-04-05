#!/usr/bin/env python3
"""Generate atomic tasks for plan-review PHASE 7 breakdown."""

import json
from pathlib import Path

# Load existing result
result_path = Path('P:/__csf/.state/plan_review_result.json')
result = json.loads(result_path.read_text())

# Generate atomic tasks based on IMPLEMENTATION PLAN phases
atomic_tasks = []

# === PHASE 0: Canonical Path Alignment & Cleanup ===
atomic_tasks.append({
    'id': 'AT-001',
    'parent_phase': 'Phase 0',
    'summary': 'Standardize runtime paths in CHS config',
    'file': 'P:/__csf/src/modules/analysis/chat_search/src/config.py',
    'action': 'Update CHS_CONFIG to use canonical paths: P:/__csf/data/chat_history.db, P:/__csf/data/chat_history_faiss_424k, P:/__csf/data/chs_index_state.json',
    'acceptance_criteria': [
        'CHS_DATABASE_PATH points to P:/__csf/data/chat_history.db',
        'FAISS_INDEX_PATH points to P:/__csf/data/chat_history_faiss_424k',
        'INCREMENTAL_STATE_PATH points to P:/__csf/data/chs_index_state.json'
    ],
    'verification': 'python -c "from src.modules.analysis.chat_search.src.config import CHS_CONFIG; print(CHS_CONFIG)"',
    'estimated_minutes': 10
})

atomic_tasks.append({
    'id': 'AT-002',
    'parent_phase': 'Phase 0',
    'summary': 'Remove non-canonical FAISS folder',
    'file': 'P:/__csf/data/chat_history_faiss_with_text/',
    'action': 'Remove non-canonical FAISS directory if it exists (backup first)',
    'acceptance_criteria': [
        'Directory P:/__csf/data/chat_history_faiss_with_text does not exist',
        'No orphaned faiss_temp_* files in canonical index directory'
    ],
    'verification': 'Test-Path "P:/__csf/data/chat_history_faiss_with_text" | Should -Be $false',
    'estimated_minutes': 5
})

atomic_tasks.append({
    'id': 'AT-003',
    'parent_phase': 'Phase 0',
    'summary': 'Add preflight check for DB and index existence',
    'file': 'P:/__csf/src/modules/analysis/chat_search/src/chat_history_search.py',
    'action': 'Add ChatHistorySearcher.preflight_check() method that validates DB row count > 0 and FAISS index files exist',
    'acceptance_criteria': [
        'preflight_check() method exists',
        'Raises RuntimeError if DB is empty',
        'Raises RuntimeError if faiss_index.bin or metadata.pkl missing'
    ],
    'verification': 'python -c "from src.modules.analysis.chat_search.src.chat_history_search import ChatHistorySearcher; ChatHistorySearcher().preflight_check()"',
    'estimated_minutes': 15
})

# === PHASE 1: Streaming Ingestion ===
atomic_tasks.append({
    'id': 'AT-004',
    'parent_phase': 'Phase 1',
    'summary': 'Create JSONLWatcher class using ReadDirectoryChangesW',
    'file': 'P:/__csf/src/ingestion/jsonl_watcher.py',
    'action': 'Create JsonlWatcher class with win32file.ReadDirectoryChangesW, event debouncing (100ms), and callback support',
    'acceptance_criteria': [
        'Class JsonlWatcher exists at P:/__csf/src/ingestion/jsonl_watcher.py',
        'watch() method monitors session directory',
        'Fires callback on file change with 100ms debouncing'
    ],
    'verification': 'python -c "from src.ingestion.jsonl_watcher import JsonlWatcher"',
    'estimated_minutes': 60
})

atomic_tasks.append({
    'id': 'AT-005',
    'parent_phase': 'Phase 1',
    'summary': 'Extend IncrementalIndexUpdater for JSONL integration',
    'file': 'P:/__csf/src/search/backends/chs_incremental.py',
    'action': 'Add update_from_jsonl() method that parses new lines since watermark and adds to FAISS',
    'acceptance_criteria': [
        'update_from_jsonl(session_path: str, watermark_pos: int) method exists',
        'Returns (new_watermark, messages_added)',
        'Integrates with existing watermark tracking'
    ],
    'verification': 'python -c "from src.search.backends.chs_incremental import IncrementalIndexUpdater; assert hasattr(IncrementalIndexUpdater, \'update_from_jsonl\')"',
    'estimated_minutes': 45
})

atomic_tasks.append({
    'id': 'AT-006',
    'parent_phase': 'Phase 1',
    'summary': 'Integrate JSONLWatcher with UnifiedSemanticDaemon',
    'file': 'P:/__csf/src/daemons/unified_semantic_daemon.py',
    'action': 'Add JsonlWatcher instance to daemon, start watcher thread, wire callbacks to IncrementalIndexUpdater',
    'acceptance_criteria': [
        'Daemon starts JsonlWatcher on initialization',
        'New JSONL appends trigger incremental FAISS updates',
        'Watermark state persisted every 10 seconds'
    ],
    'verification': '# Start daemon, append to JSONL, verify index updates within 10s',
    'estimated_minutes': 60
})

# === PHASE 2: Query Cache (SemanticCache already exists) ===
atomic_tasks.append({
    'id': 'AT-007',
    'parent_phase': 'Phase 2',
    'summary': 'Integrate SemanticCache into UnifiedSemanticDaemon query path',
    'file': 'P:/__csf/src/daemons/unified_semantic_daemon.py',
    'action': 'Add SemanticCache between IPC handler and FAISS query layer with 1-hour TTL',
    'acceptance_criteria': [
        'QueryCache imported and instantiated in daemon',
        'Cache checked before FAISS search',
        'Cache hit rate tracked in metrics'
    ],
    'verification': '# Query same term twice, verify second query hits cache',
    'estimated_minutes': 30
})

# === PHASE 3: Monitoring ===
atomic_tasks.append({
    'id': 'AT-008',
    'parent_phase': 'Phase 3',
    'summary': 'Add Prometheus metrics endpoint to daemon',
    'file': 'P:/__csf/src/daemons/unified_semantic_daemon.py',
    'action': 'Add /metrics HTTP endpoint on port 9090 with ingestion_lag_seconds, cache_hit_rate, index_freshness_seconds',
    'acceptance_criteria': [
        'HTTP server listens on port 9090',
        'GET /metrics returns Prometheus format',
        'ingestion_lag_seconds gauge exported'
    ],
    'verification': 'curl http://localhost:9090/metrics | findstr ingestion_lag',
    'estimated_minutes': 45
})

atomic_tasks.append({
    'id': 'AT-009',
    'parent_phase': 'Phase 3',
    'summary': 'Add health check for index freshness and path consistency',
    'file': 'P:/__csf/src/daemons/unified_semantic_daemon.py',
    'action': 'Add /health endpoint that checks DB path, FAISS path, watermark age (<30s)',
    'acceptance_criteria': [
        'GET /health returns JSON with status: healthy/degraded',
        'Checks P:/__csf/data/chat_history.db exists',
        'Checks watermark timestamp is <30 seconds old'
    ],
    'verification': 'curl http://localhost:9090/health',
    'estimated_minutes': 30
})

# === PHASE 4: Migration ===
atomic_tasks.append({
    'id': 'AT-010',
    'parent_phase': 'Phase 4',
    'summary': 'Create FAISS index backup script',
    'file': 'P:/__csf/src/scripts/backup_faiss.py',
    'action': 'Create script that copies FAISS index directory to timestamped backup in P:/__csf/.backups/',
    'acceptance_criteria': [
        'Script exists at P:/__csf/src/scripts/backup_faiss.py',
        'Creates P:/__csf/.backups/faiss_YYYYMMDD_HHMMSS/',
        'Copies faiss_index.bin and metadata.pkl'
    ],
    'verification': 'python P:/__csf/src/scripts/backup_faiss.py; Test-Path P:/__csf/.backups/faiss_*',
    'estimated_minutes': 20
})

atomic_tasks.append({
    'id': 'AT-011',
    'parent_phase': 'Phase 4',
    'summary': 'Create migration script with rollback',
    'file': 'P:/__csf/src/scripts/migrate_streaming.py',
    'action': 'Create migration script that: 1) backs up index, 2) enables streaming daemon, 3) supports --rollback flag',
    'acceptance_criteria': [
        'Script has --rollback flag to restore from backup',
        'Enables CHS_STREAMING_INGESTION_ENABLED feature flag',
        'Restores backup on error'
    ],
    'verification': 'python P:/__csf/src/scripts/migrate_streaming.py --dry-run',
    'estimated_minutes': 30
})

# === PHASE 5: Integration Testing ===
atomic_tasks.append({
    'id': 'AT-012',
    'parent_phase': 'Phase 5',
    'summary': 'Create end-to-end test: create chat → search → verify found',
    'file': 'P:/__csf/src/modules/analysis/chat_search/tests/test_e2e_streaming.py',
    'action': 'Write E2E test that creates temp JSONL, appends message, waits 5s, searches via daemon, verifies result',
    'acceptance_criteria': [
        'Test file exists',
        'test_streaming_ingestion_e2e() test function',
        'Asserts search result contains test message content'
    ],
    'verification': 'pytest P:/__csf/src/modules/analysis/chat_search/tests/test_e2e_streaming.py -v',
    'estimated_minutes': 45
})

atomic_tasks.append({
    'id': 'AT-013',
    'parent_phase': 'Phase 5',
    'summary': 'Create load test: 100 concurrent queries',
    'file': 'P:/__csf/src/modules/analysis/chat_search/tests/test_load.py',
    'action': 'Write load test that spawns 100 threads, each sends unique query, measures p95 latency <20ms',
    'acceptance_criteria': [
        'Test file exists',
        'test_concurrent_queries_100() test function',
        'Asserts p95_latency_ms < 20'
    ],
    'verification': 'pytest P:/__csf/src/modules/analysis/chat_search/tests/test_load.py -v',
    'estimated_minutes': 45
})

atomic_tasks.append({
    'id': 'AT-014',
    'parent_phase': 'Phase 5',
    'summary': 'Create chaos test: 100 msg/sec burst simulation',
    'file': 'P:/__csf/src/modules/analysis/chat_search/tests/test_chaos.py',
    'action': 'Write chaos test that appends 100 messages rapidly to JSONL, verifies all indexed within 30s via polling fallback',
    'acceptance_criteria': [
        'Test file exists',
        'test_burst_ingestion_100msgs() test function',
        'Asserts all 100 messages searchable within 30s'
    ],
    'verification': 'pytest P:/__csf/src/modules/analysis/chat_search/tests/test_chaos.py -v',
    'estimated_minutes': 60
})

# Calculate totals
total_minutes = sum(t['estimated_minutes'] for t in atomic_tasks)

# Add to result
result['phase_breakdown'] = {
    'pass': True,
    'atomic_tasks': atomic_tasks,
    'total_estimated_minutes': total_minutes,
    'task_count': len(atomic_tasks)
}

# Update summary
result['summary']['atomic_tasks_generated'] = len(atomic_tasks)
result['summary']['total_estimated_hours'] = round(total_minutes / 60, 1)

# Write updated result
result_path.write_text(json.dumps(result, indent=2))

print('=== PHASE 7: TASK BREAKDOWN COMPLETE ===')
print(f'Atomic Tasks Generated: {len(atomic_tasks)}')
print(f'Total Estimated Time: {total_minutes} minutes ({round(total_minutes/60, 1)} hours)')
print(f'\nOutput updated: {result_path}')
