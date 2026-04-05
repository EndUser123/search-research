# Implementation Plan: CSF NIP Directory Standards

## Overview

Apply file and folder standards to `P:/__csf.nip/` by extending the existing `directory_policy.json` configuration and creating validation/enforcement components.

---

## Phase 1: Policy Extension (Configuration Only)

### Task 1.1: Extend directory_policy.json

**File:** `P:/.claude/hooks/config/directory_policy.json`

**Action:** Add new sections to `csf_nip_directory`

**Sections to add:**

1. **allowed_hidden_directories** (13 entries)
2. **allowed_operational_directories** (3 entries)
3. **questionable_directories** (5 entries for manual review)
4. **consolidation_rules** (2 rules)

**Expected result:** All 51 directories categorized in policy

**Validation:** `python -m json.tool directory_policy.json`

---

## Phase 2: Validation Engine

### Task 2.1: Create CSFNIPPathValidator

**File:** `P:/.claude/hooks/csf_nip_path_validator.py` (NEW)

**Components:**

```python
from path_validator import PathValidator, DirectoryPolicy
from pathlib import Path
from typing import Any

class CSFNIPPathValidator(PathValidator):
    """Extends PathValidator for __csf.nip validation"""

    def __init__(self):
        super().__init__()
        self._build_csf_validation_rules()

    def validate_csf_nip_operation(self, file_path: str) -> dict[str, Any]:
        """
        Validate file operation within __csf.nip/

        Returns:
            {
                "is_safe": bool,
                "violation_type": str | None,  # UNKNOWN_DIR, BLOCKED_PATTERN, QUESTIONABLE
                "suggestion": str | None,
                "can_approve": bool
            }
        """

    def _build_csf_validation_rules(self):
        """Build validation rules from extended policy"""
        # Load new sections
        self.hidden_dirs = set(...)
        self.operational_dirs = set(...)
        self.questionable_dirs = set(...)
```

**Test:** `python -c "from csf_nip_path_validator import CSFNIPPathValidator; print('OK')"`

---

## Phase 3: Interactive Approval

### Task 3.1: Create InteractiveApprovalHandler

**File:** `P:/.claude/hooks/csf_nip_deny_violations.py` (NEW)

**Components:**

```python
import json
import shutil
import sys
from pathlib import Path

class InteractiveApprovalHandler:
    """Handle violations with block-and-approve workflow"""

    def __init__(self):
        self.policy_path = Path("P:/.claude/hooks/config/directory_policy.json")

    def handle_violation(self, file_path: str, violation: dict) -> None:
        """
        Handle violation - prompt user, take action

        Prints violation summary and prompts:
        [1] Approve & add to policy
        [2] Suggest correct location
        [3] Deny

        Exits with code 0 (allow) or 2 (block)
        """

    def _approve_and_update_policy(self, dir_name: str) -> None:
        """Add directory to allowed_subdirectories and allow"""

    def _suggest_location(self, file_path: str, violation: dict) -> None:
        """Show correct location, block operation"""
```

**Test:** Simulate violation, test each option

### Task 3.2: Integrate with deny_root_write.py

**File:** `P:/.claude/hooks/deny_root_write.py` (MODIFY)

**Changes:**
1. Import `CSFNIPPathValidator` and `InteractiveApprovalHandler`
2. Add check for `__csf.nip/` paths
3. Call validator for __csf.nip paths
4. Call handler for violations

**Code location:** After existing P:/ root validation

**Test:** Create file in unknown __csf.nip directory, verify prompt appears

---

## Phase 4: Consolidation Tool

### Task 4.1: Create DirectoryConsolidator

**File:** `P:/__csf.nip/scripts/consolidate_directories.py` (NEW)

**Components:**

```python
from pathlib import Path
import shutil

class DirectoryConsolidator:
    """Consolidate duplicate directories"""

    def __init__(self):
        self.consolidation_rules = [
            {"sources": [".data", "model_cache"], "target": "data"},
            {"sources": ["logs_backup"], "target": "logs"}
        ]

    def plan_consolidation(self, dry_run: bool = True) -> list[dict]:
        """
        Generate consolidation plan

        Returns list of:
        {
            "source": "path/to/source",
            "target": "path/to/target",
            "file_count": N,
            "conflicts": [...]
        }
        """

    def execute_consolidation(self, plan: list[dict]) -> None:
        """Execute consolidation with confirmation"""
```

**Test:** Run dry-run, verify plan looks correct

---

## Phase 5: Documentation

### Task 5.1: Create canonical_directory_structure.md

**File:** `P:/__csf.nip/docs/canonical_directory_structure.md` (NEW)

**Sections:**
1. Overview
2. Required Directories (with purposes)
3. Allowed Subdirectories (with purposes)
4. Hidden Directories (with purposes)
5. File Placement Rules
6. Blocked Patterns
7. Consolidation History

---

## Implementation Order

| Phase | Tasks | Files | Risk |
|-------|-------|-------|------|
| 1. Policy | 1.1 | directory_policy.json | LOW (JSON only) |
| 2. Validator | 2.1 | csf_nip_path_validator.py | LOW (extends existing) |
| 3. Approval | 3.1, 3.2 | csf_nip_deny_violations.py, deny_root_write.py | MEDIUM (new logic) |
| 4. Consolidation | 4.1 | consolidate_directories.py | MEDIUM (data move) |
| 5. Documentation | 5.1 | canonical_directory_structure.md | LOW (docs only) |

**Recommended execution order:** 1 → 2 → 5 → 3 → 4

(Rationale: Get policy and docs done first, validator can be tested standalone, approval integration last, consolidation manual)

---

## File Inventory

### Files to Create (5)

| File | Purpose | Lines (est) |
|------|---------|-------------|
| `P:/.claude/hooks/csf_nip_path_validator.py` | Validation engine | 150 |
| `P:/.claude/hooks/csf_nip_deny_violations.py` | Interactive approval | 200 |
| `P:/__csf.nip/scripts/consolidate_directories.py` | Consolidation tool | 250 |
| `P:/__csf.nip/docs/canonical_directory_structure.md` | Documentation | 200 |

### Files to Modify (2)

| File | Changes | Lines |
|------|---------|-------|
| `P:/.claude/hooks/config/directory_policy.json` | Add 4 sections | +100 |
| `P:/.claude/hooks/deny_root_write.py` | Import + validation call | +20 |

---

## Validation Loop

Each phase should complete:

1. **Syntax check**
   - JSON: `python -m json.tool`
   - Python: `python -m py_compile`

2. **Import check**
   - `python -c "import module; print('OK')"`

3. **Functionality check**
   - Validator: Test with known safe/unsafe paths
   - Handler: Test each option (approve/suggest/deny)
   - Consolidator: Test dry-run mode

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Policy corruption | Backup before write: `policy.json.backup` |
| Import break | Grep scan before consolidation |
| False positive | Interactive approval available |
| Data loss | Dry-run + confirmation required |

---

## Next Step

After this plan: Step 6 (Task Decomposition with `/quadlet`)

---

**TSK ID**: TSK-251227-2319-csf-nip-dir-standards
**Step**: 5 - Implementation Planning
**Status**: Complete
