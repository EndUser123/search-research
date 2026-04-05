# [TASK_ID]: Task Decomposition - [TASK_NAME]

## Project Information
- **Task ID**: [TASK_ID]
- **Task Count**: [TASK_COUNT] atomic sub-tasks
- **TDD Cycles**: [TDD_COUNT] (RED→GREEN→REFACTOR)
- **Complexity Level**: [COMPLEXITY_LEVEL] ([COMPLEXITY_DESCRIPTION])
- **Estimated Effort**: [ESTIMATED_HOURS]
- **Priority**: [PRIORITY]

## Primary Tasks

### 1. [Task 1 Name] (RED→GREEN→REFACTOR)

#### [TC-001] RED Phase - Verify [Requirement]
**Type**: Test-First Validation
**Priority**: [PRIORITY]
**Dependencies**: None
**Estimated Effort**: [TIME]

**Test Cases** (Write failing tests):
- [ ] Test: Verify [requirement]
- [ ] Test: Verify [requirement]
- [ ] Test: Verify [requirement]

**Expected Failure**:
- [Expected outcome]

**TDD Cycle**: RED → [Implementation TC-002] → GREEN

#### [TC-002] GREEN Phase - Create [Implementation]
**Type**: Implementation
**Priority**: [PRIORITY]
**Dependencies**: TC-001 (RED written)
**Estimated Effort**: [TIME]

**Implementation** (Minimal code to pass RED tests):
```[LANGUAGE]
# [Code example]
```

**Evidence Required**:
- [Evidence item 1]
- [Evidence item 2]
- [Evidence item 3]

**TDD Cycle**: [TC-001] RED → TC-002 GREEN → [TC-003] REFACTOR

#### [TC-003] REFACTOR Phase - Add [Enhancement]
**Type**: Quality Improvement
**Priority**: [PRIORITY]
**Dependencies**: TC-002 (GREEN achieved)
**Estimated Effort**: [TIME]

**Refactoring Goals**:
1. [Goal 1]
2. [Goal 2]
3. [Goal 3]
4. [Goal 4]

**Validation**:
- [ ] [Validation 1]
- [ ] [Validation 2]
- [ ] [Validation 3]
- [ ] [Validation 4]

**TDD Cycle**: [TC-001→TC-002] → TC-003 REFACTOR ✅

---

## Summary

### Task Statistics
- **Total Tasks**: [TASK_COUNT]
- **RED Phases**: [RED_COUNT] ([TC_LIST])
- **GREEN Phases**: [GREEN_COUNT] ([TC_LIST])
- **REFACTOR Phases**: [REFACTOR_COUNT] ([TC_LIST])

### Time Estimates
- **Phase 1**: [TIME] ([TC_RANGE])
- **Phase 2**: [TIME] ([TC_RANGE])
- **Phase 3**: [TIME] ([TC_RANGE])
- **Total**: **[TOTAL_TIME]**

### Dependencies
- All TDD cycles must complete before moving to next phase
- [Additional dependencies]

### Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]
- [ ] [Criterion 4]

---
**Task Decomposition Status**: ✅ COMPLETE
**Ready for Execution**: YES
**Next Action**: Begin TC-001 - [Task 1 Name] (RED Phase)
