# ADR-20260329: Cleanup Prevention - Hook & Policy Enhancement

**Status**: Draft

**Context**: Manual `/cleanup` runs reveal recurring violation patterns:
- `setup.py` whitelisted despite being Python code (type mismatch)
- `Stop_behavior_gates.py` in workspace root instead of `.claude/hooks/`
- Junk files (`t`, `t.json`, `lyrics_analysis.json`, `.backup*`, session debris) accumulating

**Root Cause**: The system reacts to violations AFTER they accumulate, rather than preventing them at write-time.

---

## Findings

### Current Detection Capabilities

| Violation Type | Detection | Prevention |
|----------------|-----------|-------------|
| Path policy (root files) | `PreToolUse_directory_policy.py` + `path_validator.py` | Partial - blocks new writes |
| Type mismatch (whitelist bypass) | `type_validator.py` in cleanup.py | None |
| Build artifacts | Hardcoded `BUILD_ARTIFACT_PATTERNS` in cleanup.py | None |
| AI-generated temp files | `ai_generated_patterns` in directory_policy.json | None |
| Misplaced hooks | Path validator | None |
| Session debris | Not tracked | None |

### Gaps Identified

| Gap | Evidence | Severity |
|-----|----------|----------|
| `setup.py` in `allowed_config_files` despite being Python code | `directory_policy.json:79` | MEDIUM |
| No write-time interception for type mismatches | `cleanup.py:643-680` - only detected post-hoc | HIGH |
| Session debris patterns not in policy | `directory_policy.json` lacks `session_*`, `current_session.json` patterns | MEDIUM |
| No feedback loop from cleanup to policy | Violations found → fixed manually, no pattern added | HIGH |

---

## Design: Prevention-First Cleanup System

### Principle
**Fix at write-time, not detect-time.** The goal is to prevent violations before they accumulate, not detect them after the fact.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WRITE-TIME LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│  PreToolUse_directory_policy.py                                      │
│  ├── Validates: path allowed? (workspace_root policy)                │
│  ├── NEW: Validates: file type matches expected location?            │
│  └── NEW: Validates: pattern matches ai_generated_Policy?           │
│                                                                      │
│  PreToolUse_type_validator.py  [NEW - HIGH PRIORITY]                 │
│  ├── Catches: .py files in config whitelist (setup.py)               │
│  ├── Catches: .md files in hooks/ (documentation)                   │
│  └── Suggests: correct location based on type                        │
│                                                                      │
│  PreToolUse_ai_generated_guard.py  [NEW - MEDIUM]                   │
│  ├── Reads: ai_generated_patterns from directory_policy.json          │
│  ├── Blocks: temp_*.py, *_findings*.json, *_analysis.md >7 days    │
│  └── Suggests: tests/test_{name} for temp_*.py                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        POLICY LAYER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  directory_policy.json                                               │
│  ├── ADD: session_debris_patterns (session-*, current_session.json) │
│  ├── ADD: operational_data_patterns (logs/, diagnostics/)            │
│  ├── FIX: Remove setup.py from allowed_config_files                  │
│  └── FIX: Add explicit required_directories purpose fields           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        FEEDBACK LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│  cleanup.py [ENHANCE]                                                │
│  ├── After cleanup run: suggest pattern additions to policy          │
│  ├── Track: violation types → add to auto-cleanup patterns           │
│  └── NEW: --extract-pattern flag to export new patterns              │
│                                                                      │
│  PostToolUse_cleanup_telemetry.py  [NEW]                             │
│  └── After ANY file write: log to cleanup_history for pattern mining │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Fix Policy (TRIVIAL - 1 file)

Remove `setup.py` from `allowed_config_files` in `directory_policy.json:79`.

**Why**: It's a Python package file, not a config file. This single change eliminates the whitelist bypass that allowed the type mismatch violation.

### Phase 2: Write-Time Type Validation (MODERATE)

Create `PreToolUse_type_validator.py` that:
1. Loads `allowed_config_files` from directory_policy.json
2. For Write operations: checks if target file type matches its location
3. Blocks `.py` files being written to config locations
4. Suggests correct location (`.claude/hooks/` for Python hooks)

**Key invariant**: `*.py` files should NOT be in config file lists.

### Phase 3: Session Debris Patterns (TRIVIAL)

Add to `ai_generated_patterns` in directory_policy.json:

```json
{
  "pattern": "session-*.json",
  "purpose": "Session metadata debris",
  "max_age_days": 1,
  "auto_cleanup": true,
  "suggested_location": null
},
{
  "pattern": "current_session.json",
  "purpose": "Session state debris",
  "auto_cleanup": true
}
```

### Phase 4: Feedback Loop (MODERATE)

Enhance cleanup.py to:
1. After detecting a violation type 3+ times, suggest adding to policy
2. Add `--export-patterns` flag to output new pattern suggestions
3. Track violation history in `state/cleanup_violations.jsonl`

---

## Decision Record

| Choice | Option | Selected | Rationale |
|--------|--------|----------|-----------|
| Type validation timing | PreToolUse vs PostToolUse | PreToolUse | Blocks before write, not after |
| Pattern export | Ad-hoc vs systematic | Systematic | Enables continuous improvement |
| Policy location | Central vs distributed | Central | `directory_policy.json` is already authoritative |

---

## Risk Summary

- **Technical**: New PreToolUse hooks add latency. Mitigation: fail-open on errors.
- **Operational**: Pattern over-fitting (too many auto-cleanup patterns). Mitigation: 3-occurrence threshold before suggesting.
- **Integration**: Type validator must handle nested directories. Mitigation: use `Path.suffix` not just filename.

## Next Steps

1. Remove `setup.py` from `allowed_config_files` (Phase 1)
2. Create `PreToolUse_type_validator.py` (Phase 2)
3. Add session debris patterns (Phase 3)
4. Enhance cleanup feedback loop (Phase 4)
