{
  "findings": [
    {
      "id": "SEC-001",
      "severity": "CRITICAL",
      "title": "Haiku subprocess spawns claude with unsandboxed transcript content",
      "description": "PreCompact spawns claude subprocess for Haiku summarization passing transcript content directly without sanitization.",
      "evidence": {
        "code_excerpt": "subprocess.Popen",
        "file_path": "P:/packages/snapshot/scripts/hooks/PreCompact_snapshot_capture.py",
        "line_number": 959,
        "function_name": "main",
        "proof": "Transcript text from haiku_prompt.py passed as prompt."
      },
      "impact": {
        "business_consequence": "Unexpected claude subprocess behavior",
        "customer_visible": false,
        "regulatory_impact": "Data exposure"
      },
      "recommendation": {
        "action": "Sanitize transcript content"
      },
      "confidence": "medium"
    },
    {
      "id": "SEC-002",
      "severity": "HIGH",
      "title": "Transcript path validation uses resolve() following symlinks",
      "description": "validate_envelope uses Path.resolve() which follows symlinks allowing bypass.",
      "evidence": {
        "code_excerpt": "Path.resolve()",
        "file_path": "P:/packages/snapshot/scripts/hooks/__lib/snapshot_v2.py",
        "line_number": 476,
        "function_name": "validate_envelope",
        "proof": "resolve() follows symlinks before boundary check."
      },
      "impact": {
        "business_consequence": "File access via symlink traversal",
        "customer_visible": false,
        "regulatory_impact": "Unauthorized file access"
      },
      "recommendation": {
        "action": "Use os.path.realpath()"
      },
      "confidence": "medium"
    },
    {
      "id": "SEC-003",
      "severity": "HIGH",
      "title": "SNAPSHOT_PROJECT_ROOT allows arbitrary directory control",
      "description": "SNAPSHOT_PROJECT_ROOT env var overrides project root without validation.",
      "evidence": {
        "code_excerpt": "os.environ.get",
        "file_path": "P:/packages/snapshot/scripts/hooks/__lib/project_root.py",
        "line_number": 41,
        "function_name": "detect_project_root",
        "proof": "Used in multiple modules."
      },
      "impact": {
        "business_consequence": "Arbitrary file write",
        "customer_visible": false,
        "regulatory_impact": "File manipulation"
      },
      "recommendation": {
        "action": "Validate SNAPSHOT_PROJECT_ROOT"
      },
      "confidence": "high"
    },
    {
      "id": "SEC-004",
      "severity": "MEDIUM",
      "title": "Active session file in user home directory",
      "description": "SessionStart writes to Path.home()/.claude/ not project directory.",
      "evidence": {
        "code_excerpt": "Path.home()",
        "file_path": "P:/packages/snapshot/scripts/hooks/SessionStart_snapshot_restore.py",
        "line_number": 137,
        "function_name": "main",
        "proof": "Session tracking leaks outside project."
      },
      "impact": {
        "business_consequence": "Cross-project info leakage",
        "customer_visible": false,
        "regulatory_impact": "Minor info disclosure"
      },
      "recommendation": {
        "action": "Write to project_root/.claude/state/"
      },
      "confidence": "high"
    },
    {
      "id": "SEC-005",
      "severity": "MEDIUM",
      "title": "Session registry path hardcoded to P: drive",
      "description": "DEFAULT_REGISTRY_PATH hardcoded to P:/.claude/.artifacts/.",
      "evidence": {
        "code_excerpt": "P:/.claude/.artifacts/",
        "file_path": "P:/packages/snapshot/scripts/hooks/__lib/session_registry.py",
        "line_number": 16,
        "function_name": "query_registry",
        "proof": "Fails on Unix."
      },
      "impact": {
        "business_consequence": "Registry fails on non-Windows",
        "customer_visible": false,
        "regulatory_impact": "Platform issue"
      },
      "recommendation": {
        "action": "Use platform-aware path"
      },
      "confidence": "high"
    },
    {
      "id": "SEC-006",
      "severity": "LOW",
      "title": "PreCompact has no stdin size bound",
      "description": "SessionStart bounds stdin to 10MB but PreCompact does not.",
      "evidence": {
        "code_excerpt": "sys.stdin.read()",
        "file_path": "P:/packages/snapshot/scripts/hooks/PreCompact_snapshot_capture.py",
        "line_number": 239,
        "function_name": "_read_hook_input",
        "proof": "Inconsistent protection."
      },
      "impact": {
        "business_consequence": "Memory exhaustion possible",
        "customer_visible": false,
        "regulatory_impact": "Availability"
      },
      "recommendation": {
        "action": "Add 10MB bound"
      },
      "confidence": "high"
    }
  ]
}