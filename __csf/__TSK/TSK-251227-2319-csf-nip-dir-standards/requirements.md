# Requirements Analysis: CSF NIP Directory Standards

## Functional Requirements

### FR-001: Policy Configuration System
- **Priority**: HIGH
- **Description**: Define canonical directory structure in JSON configuration
- **Acceptance Criteria**:
  - All 51 existing directories are categorized (required/allowed/questionable)
  - Consolidation rules are defined
  - Blocked file patterns at root are specified
  - Configuration is version-controlled

### FR-002: Path Validation Engine
- **Priority**: HIGH
- **Description**: Extend existing PathValidator for __csf.nip paths
- **Acceptance Criteria**:
  - Reuses PathValidator base class (no duplication)
  - Loads additional policy from __csf.nip_directory_policy.json
  - Returns {is_safe, violation_type, suggestion} for any path
  - Validates unknown directories
  - Validates blocked file patterns

### FR-003: Interactive Approval Workflow
- **Priority**: HIGH
- **Description**: "Block and ask for approval, then update standards" flow
- **Acceptance Criteria**:
  - Violations are blocked before execution (exit code 2)
  - User presented with 3 options: Approve+Update, Suggest, Deny
  - Approve option adds directory to policy and allows operation
  - Suggest option shows correct location but blocks
  - Deny option blocks with message
  - Policy updates are atomic (backup before write)

### FR-004: Directory Consolidation
- **Priority**: MEDIUM
- **Description**: Merge duplicate directories safely
- **Acceptance Criteria**:
  - .data/ + model_cache/ → data/
  - logs_backup/ → logs/
  - Dry-run mode shows what will happen
  - Conflict detection before execution
  - User confirmation required
  - No data loss (verify file counts before/after)

### FR-005: Canonical Documentation
- **Priority**: MEDIUM
- **Description**: Document canonical structure
- **Acceptance Criteria**:
  - All directories documented with purpose
  - File placement rules specified
  - Consolidation history tracked
  - Matches policy configuration

## Non-Functional Requirements

### NFR-001: Performance
- Validation must complete in <100ms for single path
- Policy load must complete in <50ms

### NFR-002: Compatibility
- Must work with existing deny_root_write.py hook
- Must not break existing P:/ root validation
- Must be compatible with Sapling backups

### NFR-003: Maintainability
- Code must reuse existing PathValidator patterns
- Policy must be single source of truth
- No duplicate validation logic

### NFR-004: Safety
- Policy updates must be atomic
- Consolidation must require confirmation
- No silent data loss

## Constraints

### C-001: Solo Developer
- No multi-team approval needed
- Direct policy updates acceptable
- Manual review for questionable directories

### C-002: Existing Infrastructure
- Must reuse path_validator.py patterns
- Must integrate with deny_root_write.py
- Policy format extends directory_policy.json

### C-003: Active Development
- __csf.nip is actively used
- Consolidation must not break imports
- Some directories may be in active use

## Dependencies

### External
- Python 3.12+
- SQLite (for TaskMaster - currently corrupted, workaround in place)
- JSON (for policy storage)

### Internal
- `P:/.claude/hooks/path_validator.py` (base class)
- `P:/.claude/hooks/config/directory_policy.json` (policy reference)
- `P:/__csf.nip/docs/file_location_standards.md` (existing standards)

## User Stories

### US-001: Unknown Directory Prevention
**As a** developer
**When I** create a new directory in __csf.nip root
**Then I** want to be blocked and asked if it should be added to policy
**So that** the canonical structure is maintained

### US-002: Misplaced File Detection
**As a** developer
**When I** create test files at __csf.nip root
**Then I** want to be told to put them in tests/
**So that** code organization is consistent

### US-003: Policy Evolution
**As a** developer
**When I** need a new directory type
**Then I** want to approve it and have policy auto-update
**So that** I don't have to manually edit JSON

### US-004: Safe Consolidation
**As a** developer
**When I** run directory consolidation
**Then I** want to see what will happen before confirming
**So that** I don't accidentally lose data

## Acceptance Test Matrix

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| AT-001 | Validate blocked pattern test_*.py at root | Violation + suggestion to tests/ |
| AT-002 | Validate unknown directory | Violation + approve/suggest/deny options |
| AT-003 | Approve adds to policy | Directory added, operation allowed |
| AT-004 | Consolidation dry-run | Plan shown, no changes made |
| AT-005 | Consolidation execute | Files moved, old dirs removed |
| AT-006 | Policy backup before update | .backup file created |
| AT-007 | Allowed directory passes | No violation, operation allowed |

## Risk Analysis

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking imports during consolidation | HIGH | MEDIUM | Scan references before moving |
| Policy corruption during update | HIGH | LOW | Atomic write with backup |
| False positive blocks | MEDIUM | LOW | Interactive approval override |
| Performance degradation | LOW | LOW | Reuse existing fast validator |

## Definition of Done

- [ ] All 5 functional requirements implemented
- [ ] All acceptance tests pass
- [ ] Policy configuration file created and validated
- [ ] Documentation complete
- [ ] Consolidation tool tested (dry-run)
- [ ] Interactive approval workflow tested
- [ ] Integration with deny_root_write.py verified
- [ ] No regressions in P:/ root validation

---

**TSK ID**: TSK-251227-2319-csf-nip-dir-standards
**Step**: 2 - Requirements Analysis
**Status**: Complete
