{
  "findings": [
    {
      "id": "SEC-001",
      "severity": "HIGH",
      "title": "FileLock timeout fallback bypasses lock protection in evidence_store.py",
      "description": "The _write_spool_event() function in evidence_store.py (lines 350-373) has a FileLock with timeout=0.5s, but on TimeoutError it falls through to a lock-free temp file write. This was partially fixed (CRIT-001 removed the earlier fallback) but the temp file fallback at line 367-372 still executes on ANY exception from the FileLock block, not just TimeoutError.",
      "evidence": {
        "code_excerpt": "if FILE_LOCK_AVAILABLE:\n    try:\n        with FileLock(lock_path, timeout=0.5):\n            with spool_path.open(\"a\", encoding=\"utf-8\", newline=\"\\n\") as fh:\n                fh.write(line)\n            return True\n    except TimeoutError:\n        # FileLock timed out - do NOT fall through to lock-free write.\n        pass\n    except Exception:\n        # FileLock error - proceed to fallback, not lock-free write\n        pass\n\n# Fallback: unique temp file\nfallback = EVIDENCE_SPOOL_DIR / f\"event_{int(time.time() * 1000)}_{os.getpid()}.jsonl\"",
        "file_path": "P:/.claude/hooks/evidence_store.py",
        "line_number": 349,
        "function_name": "_write_spool_event",
        "proof": "Line 361 `except Exception: pass` followed by lines 367-372 creates temp file WITHOUT lock protection. When FileLock fails for any reason other than TimeoutError, the code proceeds to an unprotected write. This could cause data corruption in concurrent multi-terminal scenarios."
      },
      "impact": {
        "business_consequence": "Concurrent hook executions can corrupt evidence spool files, leading to lost or intermingled tool event records",
        "customer_visible": false,
        "regulatory_impact": "Data integrity violation - evidence trail may be unreliable for audit/compliance"
      },
      "recommendation": {
        "action": "Change the exception handling to only proceed to temp file fallback on TimeoutError, not all Exception types. Alternatively, acquire the lock on the temp file approach too.",
        "code_fix": "except TimeoutError:\n    # FileLock timed out - use unique temp file as fallback\n    pass  # Fall through to temp file below\n# Do NOT catch Exception - any other error should propagate\n\n# Fallback: unique temp file (still needs protection)\nfallback = EVIDENCE_SPOOL_DIR / f\"event_{int(time.time() * 1000)}_{os.getpid()}.jsonl\"\ntry:\n    with FileLock(fallback.with_suffix('.lock'), timeout=0.5):\n        with fallback.open(\"a\", encoding=\"utf-8\", newline=\"\\n\") as fh:\n            fh.write(line)\n    return True\nexcept Exception:\n    return False"
      },
      "confidence": "high"
    },
    {
      "id": "SEC-002",
      "severity": "LOW",
      "title": "Regex patterns compiled at module import time (performance, not strictly security)",
      "description": "Multiple hook files compile regex patterns at module load time (top-level re.compile()). While not a direct security vulnerability, this violates the lazy initialization recommendation in the work and could cause startup latency.",
      "evidence": {
        "code_excerpt": "SESSION_ID_RE = re.compile(r\"^[a-f0-9\\-]{36}$\")\nTERMINAL_ID_SANITIZE_RE = re.compile(r\"[^A-Za-z0-9._-]+\")",
        "file_path": "P:/.claude/hooks/evidence_store.py",
        "line_number": 31,
        "function_name": "module-level",
        "proof": "Multiple files have module-level compiled regexes: assumption_audit_v2.py (EQUIVALENCE_LINK_RE, NON_EQUIVALENCE_STATE_RE, CODE_QUOTE_PATTERN), artifact_claims.py (_AGREEMENT_PREFIX_RE, _ARTIFACT_TOKEN_RE), narrative_intent_detector.py (INTENT_RE, HEDGE_RE), etc. These are compiled once at import regardless of whether they're needed."
      },
      "impact": {
        "business_consequence": "Increased hook startup time; memory overhead from unused regex patterns; slower session initialization",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "Implement lazy static initialization using functools.lru_cache(maxsize=1) on functions that return compiled regexes, or use class-based lazy compilation",
        "code_fix": "# Instead of:\nSESSION_ID_RE = re.compile(r\"^[a-f0-9\\-]{36}$\")\n\n# Use lazy initialization:\n@functools.lru_cache(maxsize=1)\ndef _get_session_id_re():\n    return re.compile(r\"^[a-f0-9\\-]{36}$\")\n\n# Or at module level only compile when first needed\n_SESSION_ID_RE = None\ndef SESSION_ID_RE():\n    global _SESSION_ID_RE\n    if _SESSION_ID_RE is None:\n        _SESSION_ID_RE = re.compile(r\"^[a-f0-9\\-]{36}$\")\n    return _SESSION_ID_RE"
      },
      "confidence": "medium"
    },
    {
      "id": "SEC-003",
      "severity": "LOW",
      "title": "No hard 200ms timeout budget implemented for hooks",
      "description": "The work recommends a 200ms hard timeout budget on all hooks, but no such timeout exists. Found timeouts are 5s, 10s, 15s, 30s in various locations (evidence_store.py timeout=30s, file_lock_manager.py LOCK_TIMEOUT_SECONDS=0.5s, etc.). The 200ms budget is not enforced.",
      "evidence": {
        "code_excerpt": "conn = sqlite3.connect(EVIDENCE_DB_PATH, timeout=30.0)\n...\nLOCK_TIMEOUT_SECONDS = 0.5  # Fail-fast timeout (500ms)",
        "file_path": "P:/.claude/hooks/evidence_store.py",
        "line_number": 62,
        "function_name": "_connect",
        "proof": "No 200ms timeout enforcement found in hook execution path. The 0.5s FileLock timeout and 30s SQLite timeout are the only timeout mechanisms, both far exceeding the recommended 200ms."
      },
      "impact": {
        "business_consequence": "Hooks could introduce latency beyond the 200ms budget recommended for responsive UX",
        "customer_visible": true,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "If 200ms is a hard requirement, implement timeout enforcement at the hook importer/runner level. Otherwise document the actual latency SLA.",
        "code_fix": "# At hook runner level:\ndef execute_hook_with_timeout(hook_name, timeout=0.2):\n    start = time.time()\n    result = execute_hook(hook_name)\n    elapsed = time.time() - start\n    if elapsed > timeout:\n        logger.warning(f\"Hook {hook_name} exceeded {timeout}s budget: {elapsed:.3f}s\")\n    return result"
      },
      "confidence": "medium"
    },
    {
      "id": "SEC-004",
      "severity": "LOW",
      "title": "QueueHandler for hook I/O not implemented",
      "description": "The work recommends QueueHandler for hook I/O to handle concurrent write pressure, but no queue-based I/O was found. Evidence spool writes go directly to disk via FileLock or temp files.",
      "evidence": {
        "code_excerpt": "No QueueHandler imports or usage found",
        "file_path": "P:/.claude/hooks",
        "line_number": 0,
        "function_name": "N/A",
        "proof": "Grep for 'QueueHandler|queue.Queue' in hooks/ returned no matches. The QueueHandler pattern from Python's logging module is not used for any hook I/O operations."
      },
      "impact": {
        "business_consequence": "High concurrent hook activity could cause I/O contention on evidence spool writes",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "Consider implementing async queue-based spooling for high-throughput scenarios if hook performance degrades under concurrent load",
        "code_fix": "import queue\nimport threading\n\n_spool_queue: queue.Queue | None = None\n\ndef _get_spool_queue() -> queue.Queue:\n    global _spool_queue\n    if _spool_queue is None:\n        _spool_queue = queue.Queue(maxsize=1000)\n        # Start background writer thread\n        t = threading.Thread(target=_spool_writer, daemon=True)\n        t.start()\n    return _spool_queue"
      },
      "confidence": "medium"
    },
    {
      "id": "SEC-005",
      "severity": "INFO",
      "title": "SQLite WAL mode already implemented in evidence_store.py",
      "description": "The work recommends SQLite WAL for handoff state, but this is already implemented. evidence_store.py (line 64-68) sets WAL mode via PRAGMA journal_mode=WAL with graceful fallback to DELETE mode if WAL is unavailable.",
      "evidence": {
        "code_excerpt": "requested_mode = (os.environ.get(\"EVIDENCE_DB_JOURNAL_MODE\", \"WAL\") or \"WAL\").upper()\nif requested_mode not in {\"WAL\", \"DELETE\", \"TRUNCATE\", \"PERSIST\", \"MEMORY\", \"OFF\"}:\n    requested_mode = \"WAL\"\ntry:\n    conn.execute(f\"PRAGMA journal_mode={requested_mode}\")\nexcept sqlite3.DatabaseError:\n    try:\n        conn.execute(\"PRAGMA journal_mode=DELETE\")",
        "file_path": "P:/.claude/hooks/evidence_store.py",
        "line_number": 64,
        "function_name": "_connect",
        "proof": "WAL mode is already the default and properly implemented with fallback. No action needed."
      },
      "impact": {
        "business_consequence": "None - already implemented",
        "customer_visible": false,
        "regulatory_impact": "None"
      },
      "recommendation": {
        "action": "No action needed - WAL is already implemented",
        "code_fix": "N/A"
      },
      "confidence": "high"
    }
  ]
}
