# Specification: CKS → Semgrep Auto-Fix Integration

## Goal
Integrate Semgrep's auto-fix capability with CKS (Code Knowledge System) by storing Semgrep YAML rules in CKS metadata and extracting them at runtime.

## Why
- **Business value**: Detect → Fix workflow requires automatic fix application, not just detection
- **User impact**: 95% of violations can be auto-fixed, reducing manual intervention
- **Technical necessity**: Current CKS pattern detection has no auto-fix capability; building generic checkers from scratch duplicates Semgrep's mature functionality

## What
**FR-001**: Store Semgrep YAML rules in CKS `entries.metadata` field as JSON
**FR-002**: Extract YAML from CKS at runtime, merge multiple rules into single config
**FR-003**: Write temp .semgrep.yml file, invoke `semgrep --autofix`
**FR-004**: Parse Semgrep JSON output, return unified violations + fixes applied
**FR-005**: Verification loop - re-run Semgrep without --autofix to confirm fixes

## All Needed Context
- **Files**:
  - `P:/__csf.nip/src/quality/unified_analyzer.py` - Current analyzer with CKS integration
  - `P:/__csf.nip/data/cks.db` - CKS database (entries table: id, type, title, content, metadata)
  - `P:/__csf.nip/src/cks/cks_query_interface.py` - CKS query interface
- **APIs**:
  - CKS query: `SELECT metadata FROM entries WHERE type='python_standard'`
  - Semgrep CLI: `semgrep --config <file> --json --autofix <target>`
- **Docs**:
  - https://semgrep.dev/docs/writing-rules/overview/
  - https://semgrep.dev/docs/CLI-reference/
- **Gotchas**:
  - Windows subprocess invocation may need shell=True or full path
  - Multiple YAML rules need merging (single "rules:" header)
  - Temp file cleanup required (use tempfile.NamedTemporaryFile or try/finally)
  - Semgrep returncode: 0 = no issues, 1 = issues found (not an error)

## Implementation Blueprint

### 1. CKS Schema Extension (No schema change - metadata already JSON)
- **Input**: Existing CKS entries table
- **Output**: Metadata format: `{"semgrep_yaml": "rules:\n  - id: ...", "severity": "ERROR"}`
- **Tests**: Verify metadata JSON can store multi-line YAML strings

### 2. CKS Query Method
- **Input**: Language filter (e.g., "python")
- **Output**: List of semgrep_yaml strings from metadata
- **Tests**: Query returns valid YAML, handles empty results

### 3. YAML Merger
- **Input**: Multiple semgrep_yaml strings
- **Output**: Single merged YAML with "rules:" header
- **Tests**: Valid YAML structure, all rules included

### 4. Semgrep Runner
- **Input**: Merged YAML, target path
- **Output**: Parsed violations + fixes_applied list
- **Tests**: Correct subprocess invocation, temp file cleanup, JSON parsing

### 5. Verification Loop
- **Input**: Target path after autofix
- **Output**: Confirmation all violations resolved
- **Tests**: Re-run without --autofix, compare counts

## Validation Loop
- **Level 1 (Syntax)**: `python -c "import yaml; yaml.safe_load(config)"`
- **Level 2 (Unit)**: `pytest tests/test_semgrep_cks_integration.py`
- **Level 3 (Integration)**: Run on test file with known violations, verify fixes applied

## BDD Scenarios

**Scenario 1: Happy path - Single rule autofix**
```
Given CKS contains semgrep_yaml with "no-pickle" rule
When target file contains "import pickle"
Then Semgrep autofix replaces with "import json"
And violation count goes from 1 to 0
```

**Scenario 2: Multiple rules merged**
```
Given CKS contains 3 semgrep_yaml entries for Python
When queried for language="python"
Then merged YAML contains "rules:" with all 3 rule entries
And all rules run in single Semgrep invocation
```

**Scenario 3: Temp file cleanup**
```
Given Semgrep execution completes (success or error)
When temp file was created
Then temp file is deleted (missing_ok=True)
```
