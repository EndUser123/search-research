# Specification: CSF NIP Directory Standards Enforcement

## Goal

Apply file and folder standards to `P:/__csf.nip/` similar to the strict validation already enforced at `P:/` root, extending the existing path validation infrastructure to cover the 51 directories currently at `__csf.nip/` root.

## Why

- **Maintainability**: 51 top-level directories are difficult to navigate and maintain
- **Consistency**: P:/ root has strict validation; __csf.nip should match
- **Prevent violations**: Currently no enforcement for misplaced files within __csf.nip
- **Reduce duplication**: Multiple directories serve similar purposes (data/, .data/, model_cache/)

## What

**FR-001: Policy Definition**
- Create `__csf.nip_directory_policy.json` defining canonical structure
- Define required, allowed, and blocked directory patterns
- Document purpose of each directory

**FR-002: Validation Engine**
- Extend existing `path_validator.py` patterns for __csf.nip
- Create `csf_nip_path_validator.py` that reuses base validation logic
- Validate operations within __csf.nip/ tree

**FR-003: Interactive Approval**
- "Block and ask for approval" workflow
- Option to approve AND update policy
- Option to suggest correct location
- Option to deny

**FR-004: Directory Consolidation**
- Merge .data/ and model_cache/ into data/
- Merge logs_backup/ into logs/
- Safe migration with conflict detection

**FR-005: Documentation**
- Create canonical_directory_structure.md
- Document all directory purposes
- Track consolidation history

## All Needed Context

### Files

**Existing Infrastructure (Reuse):**
- `P:/.claude/hooks/path_validator.py` - Config-driven validation engine
- `P:/.claude/hooks/config/directory_policy.json` - v2.2.1 policy (P:/ root)
- `P:/.claude/hooks/deny_root_write.py` - Runtime enforcement
- `P:/.claude/hooks/path_suggester.py` - Intelligent routing suggestions

**Existing Standards (Fragmented):**
- `P:/__csf.nip/docs/file_location_standards.md` - KP-001 pattern
- `P:/__csf.nip/docs/file_organization_guide.md` - Directory typing system

**Files to Create:**
- `P:/__csf.nip/config/__csf.nip_directory_policy.json` - Policy definition
- `P:/.claude/hooks/csf_nip_path_validator.py` - Validation engine
- `P:/.claude/hooks/csf_nip_deny_violations.py` - Enforcement hook
- `P:/__csf.nip/scripts/consolidate_directories.py` - Consolidation tool
- `P:/__csf.nip/docs/canonical_directory_structure.md` - Documentation

### APIs

**PathValidator class** (from path_validator.py):
- `validate_operation(file_path: str) -> dict` - Returns {is_safe, violation_type, suggestion}
- `get_policy() -> dict` - Returns loaded policy
- `get_violations() -> list` - Returns current violations

**DirectoryPolicy class**:
- `load_config(config_path: str) -> dict` - Loads JSON policy
- `validate_against_policy(path: str, policy: dict) -> dict`

### Docs

**Existing Policy Structure** (directory_policy.json):
```json
{
  "version": "2.2.1",
  "root": {
    "required_directories": [...],
    "allowed_system_directories": [...],
    "blocked_root_patterns": [...]
  }
}
```

### Gotchas

- **TaskMaster database corrupted**: Use direct directory creation
- **Nested __csf.nip/__csf.nip/**: Accidental nesting to clean up
- **Relative log paths**: Already fixed in pre_tool_use.py (root cause from prior session)
- **51 directories**: Some may be in active use - verify before consolidating
- **Import references**: Must scan before moving any code directories

## Implementation Blueprint

### 1. Policy Definition (`__csf.nip_directory_policy.json`)

**Input**: Existing directory_policy.json structure
**Output**: Extended JSON config for __csf.nip

```json
{
  "version": "1.0.0",
  "csf_nip_root": {
    "required_directories": [
      {"path": "src", "purpose": "Library code"},
      {"path": "config", "purpose": "Configuration"},
      {"path": "docs", "purpose": "Documentation"},
      {"path": "tests", "purpose": "Test suite"},
      {"path": "scripts", "purpose": "Utility scripts"},
      {"path": "data", "purpose": "Databases, data files"},
      {"path": "logs", "purpose": "Application logs"}
    ],
    "allowed_subdirectories": [...],
    "blocked_root_patterns": [...],
    "consolidation_rules": [...]
  }
}
```

**Tests**:
- JSON syntax validation
- Required fields present
- No duplicate paths

### 2. Validator Extension (`csf_nip_path_validator.py`)

**Input**: Path from file operation
**Output**: {is_safe, violation_type, suggestion}

```python
class CSFNIPPathValidator(PathValidator):
    def validate_csf_nip_operation(self, file_path: str) -> dict:
        # Validates paths within __csf.nip/ tree
        # Returns safety assessment with suggestions
```

**Tests**:
- Test against blocked patterns
- Test against unknown directories
- Test allowed directories pass

### 3. Interactive Approval (`csf_nip_deny_violations.py`)

**Input**: Violation from validator
**Output**: User prompt + action (approve/deny/suggest)

```python
class InteractiveApprovalHandler:
    def handle_violation(self, file_path: str, violation: dict) -> None:
        # Print violation summary
        # Prompt for choice
        # Update policy if approved
        # Exit 2 (block) or 0 (allow)
```

**Tests**:
- Test approve flow (policy updates)
- Test suggest flow (correct location shown)
- Test deny flow (operation blocked)

### 4. Consolidation Tool (`consolidate_directories.py`)

**Input**: Dry-run or execute mode
**Output**: Execution plan + confirmation

```python
class DirectoryConsolidator:
    def plan_consolidation(self, dry_run: bool = True) -> list[dict]
    def execute_consolidation(self, plan: list[dict]) -> None
```

**Tests**:
- Dry-run produces plan
- Conflict detection works
- Confirmation required before execute

### 5. Documentation (`canonical_directory_structure.md`)

**Input**: Policy + current structure
**Output**: Complete directory reference

**Tests**:
- All directories documented
- No contradictions with policy

## Validation Loop

- **Level 1 (Syntax)**: `python -m json.tool __csf.nip_directory_policy.json`
- **Level 2 (Unit)**: `pytest tests/test_csf_nip_validator.py`
- **Level 3 (Integration)**: `python csf_nip_path_validator.py --validate`

## BDD Scenarios

**Scenario 1: Unknown directory blocked**
```
Given user attempts to create P:/__csf.nip/unknown_dir/file.py
When path_validator validates the path
Then operation is blocked with suggestion to approve or move
```

**Scenario 2: Interactive approval updates policy**
```
Given a violation is detected
When user chooses "approve and add to policy"
Then the directory is added to policy.json
And the operation is allowed
```

**Scenario 3: Consolidation preserves data**
```
Given .data/ and model_cache/ exist with files
When consolidation executes
Then all files are moved to data/
And source directories are removed
And no data is lost
```

**Scenario 4: Blocked pattern at root**
```
Given user creates test_foo.py at __csf.nip/ root
When validator checks the path
Then violation is raised with suggestion: tests/test_foo.py
```

---

**TSK ID**: TSK-251227-2319-csf-nip-dir-standards
**Created**: 2025-12-27
**Phase**: 1 - Discovery
