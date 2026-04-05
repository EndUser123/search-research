#!/usr/bin/env python3
"""Write adversarial findings to JSON files."""

import json
import sys
from pathlib import Path

# Get terminal ID
hooks_dir = Path('P:/.claude/hooks')
sys.path.insert(0, str(hooks_dir))
from __lib.terminal_detection import detect_terminal_id

terminal_id = detect_terminal_id()
state_dir = Path(f'P:/.claude/state/v_findings/{terminal_id}')
state_dir.mkdir(parents=True, exist_ok=True)

# Security findings
security_findings = [
    {"id": "SEC-001", "severity": "MEDIUM", "title": "Insufficient Path Traversal Protection", "description": "Sequential replace() vulnerable to bypass patterns", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 55}, "confidence": 75},
    {"id": "SEC-002", "severity": "MEDIUM", "title": "TOCTOU Race Condition in get_all_sessions_tasks", "description": "No file locking between glob() and read_text()", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 472}, "confidence": 80},
    {"id": "SEC-003", "severity": "LOW", "title": "terminal_id Used Without Validation", "description": "terminal_id used in paths without sanitization", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 161}, "confidence": 60},
    {"id": "SEC-004", "severity": "LOW", "title": "Weak Fallback Session ID Generation", "description": "time.time() has 1-second resolution allowing collisions", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 113}, "confidence": 70},
    {"id": "SEC-005", "severity": "LOW", "title": "Silent Exception Handling", "description": "Broad exception catching could hide security issues", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 108}, "confidence": 55},
    {"id": "SEC-006", "severity": "LOW", "title": "MD5 Used for Marker File Hashing", "description": "MD5 is cryptographically broken, non-cryptographic use here", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 169}, "confidence": 40}
]

# Performance findings
perf_findings = [
    {"id": "PERF-001", "severity": "HIGH", "title": "File Lock Timeout Exceeds Hook Latency", "description": "5s timeout causes entire hook to block", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 232}, "confidence": 95},
    {"id": "PERF-002", "severity": "MEDIUM", "title": "Redundant Session ID Validation", "description": "validate_session_id called 4 times in hot path", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 215}, "confidence": 90},
    {"id": "PERF-003", "severity": "MEDIUM", "title": "Inefficient Linear Search", "description": "O(n) list check acceptable for n=5", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 371}, "confidence": 75},
    {"id": "PERF-004", "severity": "HIGH", "title": "Unbounded File System Glob", "description": "O(n) stat calls for all sessions", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 472}, "confidence": 92},
    {"id": "PERF-005", "severity": "LOW", "title": "Repeated read_text() Without Caching", "description": "2 sequential reads = 10ms redundant disk access", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 103}, "confidence": 85},
    {"id": "PERF-006", "severity": "MEDIUM", "title": "MD5 Hash on Every Re-entrancy Check", "description": "0.2ms per task operation", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 169}, "confidence": 70},
    {"id": "PERF-007", "severity": "CRITICAL", "title": "Double Validation Creates Redundant Work", "description": "validate_session_id called twice in locked function", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 300}, "confidence": 88},
    {"id": "PERF-008", "severity": "MEDIUM", "title": "Synchronous I/O in Atomic Write", "description": "write_text + replace = 15ms blocking", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 275}, "confidence": 82}
]

# Quality findings
quality_findings = [
    {"id": "QUAL-001", "severity": "MEDIUM", "title": "Inconsistent Error Handling", "description": "load_session_state logs but ensure_session_exists silent", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 134}, "confidence": 85},
    {"id": "QUAL-002", "severity": "MEDIUM", "title": "Redundant Validation Calls", "description": "validate_session_id called multiple times in same function", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 215}, "confidence": 95},
    {"id": "QUAL-003", "severity": "LOW", "title": "Magic Number 5", "description": "Hardcoded recent files limit", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 375}, "confidence": 70},
    {"id": "QUAL-004", "severity": "LOW", "title": "Inconsistent Session Fallback Patterns", "description": "Different prefixes: session_ vs auto_session_", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 113}, "confidence": 75},
    {"id": "QUAL-005", "severity": "LOW", "title": "Bare Except Inconsistency", "description": "get_terminal_id uses bare except Exception", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 156}, "confidence": 65},
    {"id": "QUAL-006", "severity": "MEDIUM", "title": "Type Annotation Inconsistency", "description": "dict vs dict[str, Any] mixed usage", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 204}, "confidence": 80},
    {"id": "QUAL-007", "severity": "LOW", "title": "Stale Comment Reference", "description": "Comment refers to nonexistent QUAL-001 fix", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 241}, "confidence": 90},
    {"id": "QUAL-008", "severity": "LOW", "title": "Duplicate State Initialization", "description": "default_state structure in 3 places", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 219}, "confidence": 85},
    {"id": "QUAL-009", "severity": "MEDIUM", "title": "Sys.path Manipulation", "description": "Manual sys.path.insert for local import", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 151}, "confidence": 75},
    {"id": "QUAL-010", "severity": "LOW", "title": "Unused Variable", "description": "lock_path calculated but unused in load_session_state", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 216}, "confidence": 60}
]

# Testing findings
test_findings = [
    {"id": "TEST-001", "severity": "CRITICAL", "title": "No Test Coverage", "description": "Critical hook has zero test coverage", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 1}, "confidence": 100},
    {"id": "TEST-002", "severity": "CRITICAL", "title": "Path Traversal Validation Untested", "description": "SEC-001 has no test coverage", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 55}, "confidence": 100},
    {"id": "TEST-003", "severity": "HIGH", "title": "Race Condition Fix Untested", "description": "TEST-003 claim unverified", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 348}, "confidence": 95},
    {"id": "TEST-004", "severity": "HIGH", "title": "File Lock Timeout Untested", "description": "No timeout edge case tests", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 232}, "confidence": 90},
    {"id": "TEST-005", "severity": "HIGH", "title": "Atomic Write Crash Safety Untested", "description": "No crash simulation tests", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 270}, "confidence": 90},
    {"id": "TEST-006", "severity": "HIGH", "title": "Re-entrancy TOCTOU Untested", "description": "Race condition in exists() then touch()", "evidence": {"file": "PostToolUse_task_tracker.py", "line": 174}, "confidence": 95}
]

# Write all findings
with open(state_dir / f'adversarial-security-{terminal_id}.json', 'w') as f:
    json.dump(security_findings, f, indent=2)

with open(state_dir / f'adversarial-performance-{terminal_id}.json', 'w') as f:
    json.dump(perf_findings, f, indent=2)

with open(state_dir / f'adversarial-quality-{terminal_id}.json', 'w') as f:
    json.dump(quality_findings, f, indent=2)

with open(state_dir / f'adversarial-testing-{terminal_id}.json', 'w') as f:
    json.dump(test_findings, f, indent=2)

print(f'✅ Wrote findings to {state_dir}')
print(f'Security: {len(security_findings)} findings')
print(f'Performance: {len(perf_findings)} findings')
print(f'Quality: {len(quality_findings)} findings')
print(f'Testing: {len(test_findings)} findings')
print(f'Terminal ID: {terminal_id}')
