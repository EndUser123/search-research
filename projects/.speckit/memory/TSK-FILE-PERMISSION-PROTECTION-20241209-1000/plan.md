# Enhanced File Permission Protection System
## Comprehensive Specification v1.0

### 1. Overview and Context

**Purpose**: Implement intelligent file permission protection that prevents writing to restricted directories while providing automated path suggestions to maintain developer productivity.

**Business Value**:
- Eliminates directory pollution in project root
- Reduces manual correction of file misplacements
- Maintains project structure integrity
- Provides developer-friendly guidance

**Scope Boundaries**:
- **In Scope**: Hook-based validation for Write tool operations
- **In Scope**: Intelligent path suggestion system
- **In Scope**: Violation tracking and analytics
- **Out of Scope**: Read operations validation
- **Out of Scope**: IDE-specific implementations
- **Out of Scope**: Network file operations

### 2. User Stories and Requirements

#### User Story 1: Root Directory Protection
**As a** developer
**I want** the system to prevent writing files directly to project root
**So that** project structure remains clean and organized

**Acceptance Criteria**:
- System blocks Write operations to `P:\__csf.nip\` root
- Clear error message explains why write was blocked
- Suggested alternative location is provided
- Existing valid write operations remain unaffected

#### User Story 2: Intelligent Path Suggestion
**As a** developer
**I want** automatic suggestions for correct file locations
**So that** I don't need to remember directory structure rules

**Acceptance Criteria**:
- Python files suggested for `external-tools/`
- Documentation suggested for `docs/`
- Configuration files suggested for `config/`
- Test files suggested for `tests/`
- Suggestions are based on file extension and context

#### User Story 3: Violation Tracking
**As a** system administrator
**I want** to track file permission violations
**So that** I can identify patterns and improve the system

**Acceptance Criteria**:
- All violations logged with timestamp
- Violation type classification
- Suggested path effectiveness tracking
- CLI command for viewing recent violations

#### User Story 4: TodoWrite Hook Fix
**As a** developer
**I want** the TodoWrite hook error resolved
**So that** I can use TodoWrite without constant reminders

**Acceptance Criteria**:
- TodoWrite hook error message no longer appears
- ViolationTracker module successfully imports
- Clean hook system operation without warnings
- Maintained TodoWrite functionality

### 3. Technical Specifications

#### Architecture Considerations
- **Hook Integration**: Leverage existing `pre_tool_use.py` infrastructure
- **Path Intelligence**: Rule-based engine for directory mapping
- **Violation Storage**: Extend existing JSON logging system
- **Configuration Management**: YAML-based directory rules

#### Integration Requirements
- Must integrate with existing hook system
- Must maintain compatibility with current Write tool workflow
- Must preserve existing security validations
- Must support Windows and Linux path formats

#### Performance Requirements
- Hook execution time < 100ms per operation
- No impact on allowed file operations
- Efficient pattern matching for path validation
- Minimal memory footprint

### 4. Implementation Guidance

#### Development Priorities
1. **Phase 1**: Fix violation_tracker.py module
2. **Phase 2**: Implement root directory detection
3. **Phase 3**: Add intelligent path suggestion
4. **Phase 4**: Enhance error messaging
5. **Phase 5**: Create configuration system

#### Testing Requirements
- Unit tests for each new method
- Integration tests with hook system
- Performance benchmarks
- Edge case validation

#### Deployment Considerations
- Backup existing hooks before modification
- Gradual rollout with monitoring
- Rollback plan for issues
- Documentation updates

### 5. Constitutional Compliance

**CSF NIP Constitution Principles Applied**:

1. **solo_first_architecture** ✅
   - Simple hook-based validation
   - No complex permission hierarchies
   - Solo developer maintainable

2. **background_services_prohibition** ✅
   - No background analytics service
   - No violation tracking daemon
   - Simple file-based logging only

3. **enterprise_bloat_prevention** ✅
   - No admin override mechanisms
   - No enterprise permission systems
   - Simple, direct validation

4. **value_driven_complexity** ✅
   - Clear value: prevents directory pollution
   - Minimal complexity: rule-based mapping
   - Essential for solo developer productivity

**Constitutional Design Decisions**:

- **No Analytics Dashboard**: Violates background_services_prohibition
- **No Override System**: Violates enterprise_bloat_prevention
- **No IDE Extensions**: Violates solo_first_architecture simplicity
- **No User Preference Collection**: Violates enterprise patterns
- **Simple File Logging**: Complies with all principles

**Constitution-Compliant Questions** (if needed):

1. Simple override?
   - One-time bypass flag
   - Manual file move
   - No complex system

2. File type mapping?
   - Basic extension rules
   - Context-aware suggestions
   - No complex configuration

3. Performance?
   - <100ms validation
   - No background processing
   - Minimal resource use

## Current State
- ✅ Hook system working (demonstrated by blocking write to C:\Users\...)
- ✅ Has `check_file_access()` method for validation
- ✅ Logs violations to `data/hook_violations/violations.json`
- ❌ Missing `violation_tracker.py` module (referenced but not found)
- ❌ No intelligent path suggestions
- ❌ Allows writes to `P:\__csf.nip\` root directory

## Implementation Steps

### Phase 1: Fix Missing Violation Tracker (30 minutes)
**File**: `P:\__csf.nip\src\csf_prevention_framework\violation_tracker.py`
- Create the missing violation tracking module
- Implement Violation class and ViolationTracker
- Add methods to record, analyze, and report violations
- Fix import error in hook system

### Phase 2: Enhance Path Validation (1 hour)
**File**: `P:\__csf.nip\.claude\hooks\pre_tool_use.py`
Add these methods to the PreToolUseHook class:

1. **Root Directory Detection**:
   ```python
   def is_root_directory_violation(self, path: Path) -> bool:
       # Check if attempting to write directly to P:\__csf.nip\
   ```

2. **Intelligent Path Suggestion**:
   ```python
   def suggest_correct_location(self, file_path: str, operation: str) -> str:
       # Map file extensions to appropriate directories
       # .py → external-tools/
       # .md → docs/
       # .json → data/
       # etc.
   ```

3. **Enhanced check_file_access()**:
   - Add root directory violation checks
   - Provide suggested paths in error messages
   - Maintain existing security validations

### Phase 3: Create Directory Rules Configuration (30 minutes)
**File**: `P:\__csf.nip\config\directory_rules.yml`
```yaml
allowed_directories:
  external-tools:
    extensions: ['.py', '.js', '.sh', '.bat']
    description: 'External tools and utilities'
  docs:
    extensions: ['.md', '.txt', '.pdf']
    description: 'Documentation'
  tests:
    extensions: ['.py', '.js', '.test']
    description: 'Test files'
  data:
    extensions: ['.json', '.csv', '.db']
    description: 'Data files'
  config:
    extensions: ['.yml', '.yaml', '.conf', '.ini']
    description: 'Configuration files'

restricted_directories:
  - 'P:\__csf.nip\'
  - 'P:\__csf.nip\src\'
  - 'P:\__csf.nip\.git\'
  - 'P:\__csf.nip\node_modules\'
```

### Phase 4: Improve Error Messages (30 minutes)
Update the violation response format to include:
- Clear explanation of why write was blocked
- Suggested alternative location
- File type-specific guidance
- Quick fix option (one-command correction)

## Code Changes Required

### 1. New File: `src/csf_prevention_framework/violation_tracker.py`
```python
#!/usr/bin/env python3
"""
Constitutional file permission violation tracking system
Follows CSF NIP principles: simple, no background services, file-based logging only
"""

import json
import datetime
import threading
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ViolationType(Enum):
    ROOT_DIRECTORY_WRITE = "ROOT_DIRECTORY_WRITE"
    CSF_NIP_ROOT_WRITE = "CSF_NIP_ROOT_WRITE"
    RESTRICTED_DIRECTORY_ACCESS = "RESTRICTED_DIRECTORY_ACCESS"

@dataclass
class Violation:
    violation_id: str
    violation_type: ViolationType
    file_path: str
    suggested_path: Optional[str]
    timestamp: str
    user_context: Optional[str] = None
    auto_fix_available: bool = True
    metadata: Dict[str, str] = None

class ViolationTracker:
    """Simple, thread-safe violation tracker with file-based logging"""

    def __init__(self, violations_file: Optional[Path] = None):
        self.violations_file = violations_file or Path("data/hook_violations/violations.json")
        self._lock = threading.Lock()
        self._ensure_violations_directory()

    def _ensure_violations_directory(self):
        """Create violations directory if it doesn't exist"""
        self.violations_file.parent.mkdir(parents=True, exist_ok=True)

    def record_violation(self, violation: Violation) -> bool:
        """
        Record a violation with atomic write and error handling

        Returns:
            bool: True if successfully recorded, False otherwise
        """
        try:
            with self._lock:
                # Load existing violations
                violations = self._load_violations()

                # Add new violation
                violations.append(asdict(violation))

                # Keep only last 1000 violations to prevent file bloat
                if len(violations) > 1000:
                    violations = violations[-1000:]

                # Atomic write
                temp_file = self.violations_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(violations, f, indent=2, ensure_ascii=False)

                temp_file.replace(self.violations_file)
                return True

        except Exception as e:
            # Graceful degradation - don't break the hook system
            print(f"Warning: Failed to record violation: {e}", file=sys.stderr)
            return False

    def _load_violations(self) -> List[Dict]:
        """Load violations from file with fallback to empty list"""
        try:
            if self.violations_file.exists():
                with open(self.violations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except (json.JSONDecodeError, IOError):
            # File corrupted or unreadable, start fresh
            return []

    def get_recent_violations(self, hours: int = 24) -> List[Dict]:
        """
        Get violations from the last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            List of violation dictionaries
        """
        try:
            violations = self._load_violations()
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)

            recent = []
            for v in violations:
                try:
                    violation_time = datetime.datetime.fromisoformat(v['timestamp'])
                    if violation_time > cutoff:
                        recent.append(v)
                except (ValueError, KeyError):
                    # Skip malformed entries
                    continue

            return recent
        except Exception:
            return []
```

### 2. Modify: `.claude/hooks/pre_tool_use.py`
Add to `check_file_access()` method (around line 2470):
```python
# Check for root directory violations
if self.is_root_directory_violation(Path(normalized_path)):
    suggested = self.suggest_correct_location(file_path, operation)
    return {
        "allowed": False,
        "reason": f"Cannot write to project root. Suggested location: {suggested}",
        "severity": "high",
        "category": "directory_structure",
        "suggested_path": suggested,
        "auto_fix": f"Write to {suggested} instead"
    }
```

## Testing Plan

1. Test 1: Attempt to write Python file to `P:\__csf.nip\` root
   - Expected: Blocked with suggestion to use `external-tools/`

2. Test 2: Write Python file to `P:\__csf.nip\external-tools\`
   - Expected: Allowed

3. Test 3: Attempt to write to `P:\__csf.nip\src\`
   - Expected: Blocked with appropriate suggestion

4. Test 4: Verify existing functionality still works
   - Existing protections maintained
   - Normal operations unaffected

## Benefits

1. **Prevents Directory Pollution**: No more files in project root
2. **Developer-Friendly**: Clear suggestions for correct locations
3. **Maintains Security**: Builds on existing robust foundation
4. **Automated Guidance**: Reduces user intervention needed
5. **Trackable Patterns**: Violation tracking for improvement

## Risk Mitigation

1. **Backup Existing Hook**: Before modifying `pre_tool_use.py`
2. **Gradual Rollout**: Start with warnings, then blocks
3. **Override Mechanism**: Emergency bypass option
4. **Comprehensive Testing**: Verify all scenarios

## Success Metrics

- 100% prevention of root directory writes
- 90% auto-suggestion accuracy
- Zero false positives
- Developer productivity maintained
- Violation tracking operational

## Next Steps

1. Review and approve this plan
2. Begin Phase 1 implementation (fix violation_tracker.py)
3. Test after each phase
4. Deploy full enhancement
5. Monitor violation patterns for further improvement