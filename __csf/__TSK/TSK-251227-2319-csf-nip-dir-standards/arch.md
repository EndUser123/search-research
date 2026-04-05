# Architecture Analysis: CSF NIP Directory Standards

## Decision: Extend Existing `directory_policy.json`

### Complexity Tax

| Option | Tax | Rationale |
|--------|-----|-----------|
| **Separate policy file** | +9 | New files, policy merging logic, drift risk |
| **Extend existing** | +3 | Configuration only, reuse infrastructure |

**Decision:** EXTEND EXISTING (+3 << +9)

---

## System Architecture

```
File Operation
    ↓
deny_root_write.py (hook)
    ↓
CSFNIPPathValidator.validate_csf_nip_operation()
    ↓
Check policy (allowed_subdirs, hidden_dirs, operational_dirs, blocked_patterns)
    ↓
┌─────────────────┬──────────────────┬─────────────────┐
│   SAFE          │   VIOLATION      │   QUESTIONABLE   │
│   Allow         │   → Interactive  │   → Block +      │
│   (exit 0)      │   Approval       │    manual review │
└─────────────────┴──────────────────┴─────────────────┘
```

---

## Components

### 1. Policy Extension (directory_policy.json)

**New sections:**
```json
{
  "csf_nip_directory": {
    "allowed_hidden_directories": [
      {"path": ".cache", "purpose": "Cache files"},
      {"path": ".cks", "purpose": "CKS data"},
      {"path": ".venv", "purpose": "Python virtual environment"},
      {"path": ".speckit", "purpose": "Speckit registry"},
      {"path": ".staging", "purpose": "Temporary work area"},
      {"path": ".archived", "purpose": "Archived items"},
      {"path": ".taskmaster", "purpose": "Task management"},
      {"path": ".aid", "purpose": "AI assistance data"},
      {"path": ".evidence", "purpose": "Evidence tracking"},
      {"path": ".ruff_cache", "purpose": "Ruff cache"},
      {"path": ".mypy_cache", "purpose": "MyPy cache"},
      {"path": ".sl", "purpose": "Sapling data"},
      {"path": ".github", "purpose": "GitHub integration"}
    ],
    "allowed_operational_directories": [
      {"path": "migrations", "purpose": "Database migrations"},
      {"path": "monitoring", "purpose": "System monitoring"},
      {"path": "diag", "purpose": "Diagnostic outputs"}
    ],
    "questionable_directories": [
      {"path": "root", "purpose": "UNCLEAR - evaluate"},
      {"path": "models", "purpose": "Consider merging to data/"},
      {"path": "knowledge_store", "purpose": "May duplicate CKS"},
      {"path": "__csf.nip", "purpose": "Nested copy - remove"},
      {"path": "tsk", "purpose": "Task shortcuts - evaluate"}
    ],
    "consolidation_rules": [
      {
        "sources": [".data", "model_cache"],
        "target": "data",
        "strategy": "move",
        "priority": "HIGH"
      },
      {
        "sources": ["logs_backup"],
        "target": "logs",
        "strategy": "merge",
        "priority": "HIGH"
      }
    ]
  }
}
```

### 2. CSFNIPPathValidator (NEW)

**File:** `P:/.claude/hooks/csf_nip_path_validator.py`

```python
from path_validator import PathValidator

class CSFNIPPathValidator(PathValidator):
    """Extends PathValidator for __csf.nip validation"""

    def validate_csf_nip_operation(self, file_path: str) -> dict:
        """
        Validate file operation within __csf.nip/

        Returns:
            {
                "is_safe": bool,
                "violation_type": str | None,
                "suggestion": str | None,
                "can_approve": bool  # True for UNKNOWN_DIR
            }
        """
```

### 3. InteractiveApprovalHandler (NEW)

**File:** `P:/.claude/hooks/csf_nip_deny_violations.py`

```python
class InteractiveApprovalHandler:
    """Handle violations with block-and-approve workflow"""

    VIOLATION_TYPES = {
        "UNKNOWN_DIR": {  # Can be approved
            "message": "Directory not in allowed list",
            "options": ["Approve & add to policy", "Suggest location", "Deny"]
        },
        "BLOCKED_PATTERN": {  # Cannot be approved
            "message": "File pattern blocked at root",
            "options": ["Suggest location", "Deny"]
        },
        "QUESTIONABLE_DIR": {  # Requires manual review
            "message": "Directory marked for manual review",
            "options": ["Suggest location", "Deny"]
        }
    }

    def handle_violation(self, file_path: str, violation: dict) -> None:
        """Handle violation - prompt user, take action"""

    def _approve_and_update_policy(self, dir_name: str) -> None:
        """Add directory to policy and allow operation"""

    def _suggest_correct_location(self, file_path: str) -> None:
        """Show correct location, block operation"""
```

### 4. Consolidation Tool (NEW)

**File:** `P:/__csf.nip/scripts/consolidate_directories.py`

```python
class DirectoryConsolidator:
    """Consolidate duplicate directories per consolidation_rules"""

    def plan_consolidation(self, dry_run: bool = True) -> list[dict]:
        """Generate consolidation plan"""

    def execute_consolidation(self, plan: list[dict]) -> None:
        """Execute consolidation with safety checks"""
```

---

## Directory Categorization (51 → Categorized)

| Category | Count | Directories |
|----------|-------|-------------|
| **Already allowed** | 18 | src, commands, config, docs, tests, scripts, tools, reports, logs, .staging, .speckit, backups, research, examples, external-tools, plans, production, exports |
| **Hidden dirs** (add) | 13 | .cache, .cks, .venv, .ruff_cache, .mypy_cache, .sl, .github, .archived, .aid, .evidence, .taskmaster, .claude, .data |
| **Operational** (add) | 3 | migrations, monitoring, diag |
| **Questionable** (manual) | 5 | root, models, knowledge_store, tsk, __csf.nip (nested) |
| **To consolidate** | 3 | .data, model_cache, logs_backup |
| **System/cache** (ignore) | 9 | __pycache__, node_modules, .git, .vscode, etc. |

---

## Data Flow: Validation + Approval

```
┌─────────────────────────────────────────────────────────────┐
│  User creates: P:/__csf.nip/new_dir/file.py                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│  deny_root_write.py hook                                    │
│  - Detects __csf.nip/ path                                  │
│  - Calls CSFNIPPathValidator                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│  CSFNIPPathValidator.validate_csf_nip_operation()          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Normalize path                                     │  │
│  │ 2. Extract directory name                             │  │
│  │ 3. Check against policy:                              │  │
│  │    - allowed_subdirectories (18)                       │  │
│  │    - allowed_hidden_directories (13) NEW              │  │
│  │    - allowed_operational_directories (3) NEW          │  │
│  │    - questionable_directories (manual review)          │  │
│  │    - blocked_root_patterns (14)                       │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
         SAFE                    UNSAFE
            │                         │
            v                         v
      Allow (exit 0)          InteractiveApprovalHandler
                                   ├─ Print violation
                                   ├─ Show options
                                   ├─ Get user choice
                                   │
                      ┌───────────┼───────────┐
                      │           │           │
                   APPROVE      SUGGEST      DENY
                      │           │           │
                      v           v           v
              Update policy    Show      Exit 2
              + allow          correct   (block)
              (exit 0)        location
                              Exit 2
                              (block)
```

---

## Integration with deny_root_write.py

**Change required in `deny_root_write.py`:**

```python
# Add import
from csf_nip_path_validator import CSFNIPPathValidator
from csf_nip_deny_violations import InteractiveApprovalHandler

# In validation function:
if file_path.lower().startswith("p:/__csf.nip/"):
    validator = CSFNIPPathValidator()
    result = validator.validate_csf_nip_operation(file_path)

    if not result["is_safe"]:
        handler = InteractiveApprovalHandler()
        handler.handle_violation(file_path, result)
        # handler exits appropriately
```

---

## Failure Mode Analysis

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Policy JSON corruption | JSON validate on load | Backup before write |
| Import break (consolidation) | Grep scan before move | Require confirmation |
| False positive block | User can approve | Interactive override |
| Data loss (consolidation) | File count compare | Dry-run + confirm |

---

## Implementation Order

1. **Phase 1: Policy Extension** (Configuration only, no code)
   - Add `allowed_hidden_directories` section
   - Add `allowed_operational_directories` section
   - Add `questionable_directories` section
   - Add `consolidation_rules` section

2. **Phase 2: Validation Engine**
   - Create `csf_nip_path_validator.py`
   - Extend PathValidator base class
   - Implement `validate_csf_nip_operation()`
   - Test with existing policy

3. **Phase 3: Interactive Approval**
   - Create `csf_nip_deny_violations.py`
   - Implement `InteractiveApprovalHandler`
   - Integrate with `deny_root_write.py`
   - Test approve/suggest/deny flows

4. **Phase 4: Consolidation Tool**
   - Create `consolidate_directories.py`
   - Implement dry-run mode
   - Implement execute mode with confirmation
   - Run consolidation (manual trigger)

---

## Testing Strategy

| Test Type | Description |
|-----------|-------------|
| **Unit** | Test CSFNIPPathValidator with all violation types |
| **Integration** | Test deny_root_write.py with new validator |
| **Interactive** | Test approval workflow (approve, suggest, deny) |
| **Consolidation** | Test dry-run and execute modes |
| **Regression** | Verify P:/ root validation still works |

---

## Success Criteria

- [ ] All 51 directories categorized in policy
- [ ] Validator correctly identifies violations
- [ ] Interactive approval adds to policy and allows
- [ ] Suggest shows correct location
- [ ] Deny blocks operation
- [ ] Consolidation dry-run produces plan
- [ ] Consolidation execute completes safely
- [ ] P:/ root validation unaffected (regression test)

---

**TSK ID**: TSK-251227-2319-csf-nip-dir-standards
**Step**: 4 - Architecture Analysis
**Status**: Complete
