{
  "findings": [
    {
      "id": "PERF-001",
      "severity": "CRITICAL",
      "title": "Backward scan loads entire transcript into memory via readlines()",
      "description": "gather_context_with_boundaries() in transcript.py:936 calls f.readlines() which loads the ENTIRE transcript file into memory as a list, then iterates backwards. For large transcripts (50MB+ files with 50,000 entries), this causes unnecessary memory pressure. Additionally, gather_context_with_boundaries is called from _extract_and_format_user_context (snapshot_v2.py:950) which is invoked at RESTORE time, not capture time - meaning it reads and loads the entire transcript file a SECOND time separately from TranscriptParser caching.",
      "evidence": {
        "code_excerpt": "transcript.py:936: lines = f.readlines()  # Loads entire file\n# Then: for line in reversed(lines):",
        "file_path": "P:\\packages\\snapshot\\scripts\\hooks\\__lib\transcript.py",
        "line_number": "936",
        "function_name": "gather_context_with_boundaries",
        "proof": "f.readlines() materializes entire file into memory; reversed() then iterates. For a 50MB transcript (50,000 entries x ~1KB/entry): 50MB RAM allocation + GC pressure."
      },
      "impact": {
        "business_consequence": "Restore-time context injection causes O(n) memory spike on large sessions.",
        "user_visible": false
      },
      "recommendation": {
        "action": "Replace readlines() with collections.deque(maxlen=max_messages) for memory-efficient streaming",
        "code_fix": "from collections import deque\ndef gather_context_with_boundaries(...):\n    lines = deque(open(path), maxlen=max_messages)\n    for line in reversed(list(lines)):"
      },
      "confidence": "high"
    },
    {
      "id": "PERF-002",
      "severity": "MEDIUM",
      "title": "_read_last_phase scans entire JSONL accumulator file on every tool use",
      "description": "snapshot_accumulator.py:40-58 _read_last_phase() reads the ENTIRE accumulated.jsonl file on every PostToolUse call, doing a full backward iteration through all events.",
      "evidence": {
        "code_excerpt": "snapshot_accumulator.py:46: for line in reversed(list(f)):",
        "file_path": "P:\\packages\\snapshot\\scripts\\hooks\\__lib\\snapshot_accumulator.py",
        "line_number": "46",
        "function_name": "_read_last_phase",
        "proof": "Every PostToolUse triggers full file read. For 100 tool calls with 1000-line JSONL: 100 x O(n) reads."
      },
      "impact": {
        "business_consequence": "Performance degrades linearly with session length.",
        "user_visible": false
      },
      "recommendation": {
        "action": "Cache last phase in memory, invalidate on phase_transition events",
        "code_fix": "_last_phase_cache = {}\ndef _read_last_phase(path):\n    tid = extract_terminal_id(path)\n    if tid in _last_phase_cache:\n        return _last_phase_cache[tid]"
      },
      "confidence": "medium"
    },
    {
      "id": "PERF-003",
      "severity": "MEDIUM",
      "title": "TranscriptParser extraction methods do redundant full-pass iterations",
      "description": "Each extract_* method iterates the full cached entry list independently with its own filtering. For 6 methods x 50,000 entries = 300,000 redundant iterations.",
      "evidence": {
        "code_excerpt": "transcript.py:1720,1762,1811,1894,1961,2019: entries = self._get_parsed_entries()",
        "file_path": "P:\\packages\\snapshot\\scripts\\hooks\\__lib\transcript.py",
        "line_number": "1720,1762,1811,1894,1961,2019",
        "function_name": "Multiple extract_* methods",
        "proof": "6 methods x 50,000 entries filtered independently."
      },
      "impact": {
        "business_consequence": "Redundant CPU cycles on repeated filtering.",
        "user_visible": false
      },
      "recommendation": {
        "action": "Pre-compute type-filtered entry caches once",
        "code_fix": "def _get_filtered_entries(self, entry_type):\n    if not hasattr(self, \"_filtered_cache\"):\n        self._filtered_cache = {}\n    if entry_type not in self._filtered_cache:\n        self._filtered_cache[entry_type] = [e for e in self._get_parsed_entries() if e.get(\"type\") == entry_type]\n    return self._filtered_cache[entry_type]"
      },
      "confidence": "medium"
    },
    {
      "id": "PERF-004",
      "severity": "LOW",
      "title": "Multiple direct _get_parsed_entries() calls in PreCompact main()",
      "description": "PreCompact_snapshot_capture.py calls _get_parsed_entries() directly at lines 260, 375, and 474, plus multiple method calls that each iterate internally.",
      "evidence": {
        "code_excerpt": "PreCompact_snapshot_capture.py:260,375,474",
        "file_path": "P:\\packages\\snapshot\\scripts\\hooks\\PreCompact_snapshot_capture.py",
        "line_number": "260,375,474",
        "function_name": "main()",
        "proof": "3 direct calls plus method calls that each iterate internally."
      },
      "impact": {
        "business_consequence": "Minor CPU overhead.",
        "user_visible": false
      },
      "recommendation": {
        "action": "Get entries once, pass to methods that need them"
      },
      "confidence": "medium"
    },
    {
      "id": "PERF-005",
      "severity": "LOW",
      "title": "compute_file_content_hash lacks caching across invocations",
      "description": "_build_evidence_index computes file hashes for transcript + up to 5 active files with no caching across PreCompact runs.",
      "evidence": {
        "code_excerpt": "PreCompact_snapshot_capture.py:546,557",
        "file_path": "P:\\packages\\snapshot\\scripts\\hooks\\PreCompact_snapshot_capture.py",
        "line_number": "546,557",
        "function_name": "_build_evidence_index",
        "proof": "compute_file_content_hash reads entire file sequentially each time."
      },
      "impact": {
        "business_consequence": "Redundant I/O for repeated file hashing.",
        "user_visible": false
      },
      "recommendation": {
        "action": "Add @lru_cache on compute_file_content_hash with (path, mtime) key"
      },
      "confidence": "low"
    }
  ],
  "summary": {
    "critical_issue": "PERF-001: readlines() in gather_context_with_boundaries causes O(n) memory spike at restore time",
    "medium_issues": [
      "PERF-002: _read_last_phase full scan on every PostToolUse",
      "PERF-003: Redundant iteration by extract_* methods"
    ],
    "low_issues": [
      "PERF-004: Multiple _get_parsed_entries calls in PreCompact",
      "PERF-005: No hash caching for repeated file hashing"
    ],
    "not_an_issue": [
      "TranscriptParser._get_parsed_entries() IS cached - N+1 parsing is mitigated",
      "parallel_capture uses ThreadPoolExecutor correctly",
      "snapshot_files.py validates I/O within FileLock"
    ]
  }
}