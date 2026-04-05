# Implementation Plan: Active Documentation Bridge

**TSK:** TSK-260113-ActiveDocumentation
**Date:** 2026-01-13
**Estimated Total:** 10-12 hours

---

## Task Breakdown (2-5 minute granularity)

### Phase 1: Constraint Reader Module (HIGH - 3 hours)

#### 1.1 Create ProjectConstraints dataclass [5 min]
**File:** `P:/__csf.nip/src/features/constraints/models.py`
```python
@dataclass
class ProjectConstraints:
    language_rules: list[str]
    coverage_minimum: float | None
    naming_conventions: list[str]
    tdd_required: bool
    forbidden_patterns: list[str]
    validation_commands: list[str]
```

#### 1.2 Create CLAUDE.md parser [20 min]
**File:** `P:/__csf.nip/src/features/constraints/claude_md_reader.py`
- Parse section headers (##)
- Extract constraint patterns from key sections:
  - "TDD Mandate" → tdd_required
  - "Python 2025 Standards" → language_rules
  - "Forbidden Patterns" → forbidden_patterns
- Handle missing CLAUDE.md gracefully (return empty constraints)

#### 1.3 Add caching layer [10 min]
- LRU cache with 1-hour TTL
- Cache key: file path + mtime
- Invalidate on file modification

#### 1.4 Write unit tests [30 min]
**File:** `P:/__csf.nip/tests/unit/test_claude_md_reader.py`
- Test with actual CLAUDE.md
- Test with missing CLAUDE.md
- Test with malformed CLAUDE.md
- Test cache invalidation

#### 1.5 Add __init__.py and exports [5 min]
**File:** `P:/__csf.nip/src/features/constraints/__init__.py`

---

### Phase 2: Modify /specify Command (HIGH - 2 hours)

#### 2.1 Import ConstraintReader into /specify [5 min]
**File:** `P:/.claude/commands/specify.md`

#### 2.2 Add constraint extraction step [15 min]
- Call ConstraintReader before generating specify.md
- Handle case where no CLAUDE.md exists

#### 2.3 Add "Project Rules" section to template [20 min]
```markdown
## Project Rules (from CLAUDE.md)

### Language Rules
- extracted rules here...

### Requirements
- TDD: RED → GREEN → REFACTOR
- Coverage: 85% minimum
```

#### 2.4 Test /specify with actual project [20 min]
- Run `/specify "test feature"` on real project
- Verify rules section appears
- Verify no crash when CLAUDE.md missing

#### 2.5 Update specify.md documentation [10 min]
- Document new constraint section
- Add examples

---

### Phase 3: SessionStart Constraint Display (HIGH - 1 hour)

#### 3.1 Create SessionStart_constraints.py hook [20 min]
**File:** `P:/.claude/hooks/SessionStart_constraints.py`
```python
def main():
    constraints = ConstraintReader().load(project_path)
    if constraints:
        display_constraint_banner(constraints)
```

#### 3.2 Format constraint banner [15 min]
```
════════════════════════════════════════════════════════════
📋 PROJECT CONSTRAINTS ACTIVE (from CLAUDE.md)
════════════════════════════════════════════════════════════
☑ TDD: RED → GREEN → REFACTOR required
☑ Coverage: 85% minimum
☑ Python 3.11+, mypy strict, Pydantic V2
════════════════════════════════════════════════════════════
```

#### 3.3 Test hook locally [10 min]
- Trigger SessionStart event
- Verify banner displays
- Verify no crash when CLAUDE.md missing

#### 3.4 Add hook to .gitignore if needed [5 min]

---

### Phase 4: Modify /plan Command (MEDIUM - 3 hours)

#### 4.1 Import ConstraintReader into /plan [5 min]
**File:** `P:/.claude/commands/plan.md`

#### 4.2 Read constraints from specify.md [15 min]
- Parse specify.md for "Project Rules" section
- Store in plan context

#### 4.3 Modify task template to include constraints [20 min]
```markdown
- [ ] Task description
  - Constraints:
    - TDD required
    - Type: mypy strict
  - Validation: pytest, mypy --strict
```

#### 4.4 Map constraints to tasks [30 min]
- Language rules → all tasks
- TDD required → implementation tasks
- Coverage → test tasks
- Validation commands → completion criteria

#### 4.5 Test /plan with constraints [20 min]
- Create test specify.md with rules
- Run `/plan` with specify.md input
- Verify tasks include constraint references

---

### Phase 5: Evidence Tracking (MEDIUM - 2 hours)

#### 5.1 Define constraint_validation.json schema [10 min]
```json
{
  "claude_md_path": "P:/.claude/CLAUDE.md",
  "constraints_extracted_at": "ISO timestamp",
  "constraints": {
    "tdd_required": true,
    "coverage_minimum": 85,
    "language_rules": ["python", "mypy strict"]
  },
  "tasks_with_constraints": 5,
  "validated_at": "ISO timestamp"
}
```

#### 5.2 Create constraint tracker module [30 min]
**File:** `P:/__csf.nip/src/features/constraints/tracker.py`
- `start_validation()` - records when constraints applied
- `record_task_constraints()` - maps task → constraints
- `finalize_validation()` - writes evidence JSON

#### 5.3 Integrate with CWO evidence system [30 min]
- Call tracker during CWO execution
- Write to `evidence/step_X/constraint_validation.json`

#### 5.4 Test evidence output [20 min]
- Run full CWO workflow
- Verify constraint_validation.json created
- Verify JSON schema valid

---

### Phase 6: Integration Testing (MEDIUM - 2 hours)

#### 6.1 End-to-end test: /specify → constraints [20 min]
- Run `/specify` with real project
- Verify specify.md contains rules section

#### 6.2 End-to-end test: /plan → constraint references [20 min]
- Run `/plan` with constraint-laden specify.md
- Verify tasks reference constraints

#### 6.3 End-to-end test: SessionStart display [10 min]
- Start new session
- Verify constraint banner appears

#### 6.4 End-to-end test: Evidence tracking [20 min]
- Run full CWO workflow
- Verify evidence contains constraint_validation.json

#### 6.5 Backward compatibility test [20 min]
- Test with project that has no CLAUDE.md
- Verify no crashes, graceful degradation

---

### Phase 7: Documentation (LOW - 1 hour)

#### 7.1 Update CLAUDE.md with constraint system [20 min]
- Document new constraint extraction
- Add examples

#### 7.2 Create CONSTRAINTS.md guide [20 min]
**File:** `P:/__csf.nip/docs/constraints_guide.md`
- How to write constraint sections in CLAUDE.md
- Constraint syntax reference

#### 7.3 Update /design skill if needed [10 min]

#### 7.4 Update review bundle [10 min]
- Include constraint system in architecture review

---

## Success Criteria

- [ ] ConstraintReader parses CLAUDE.md correctly
- [ ] /specify embeds "Project Rules" section
- [ ] /plan tasks reference applicable constraints
- [ ] SessionStart displays constraint banner
- [ ] Evidence tracks constraint validation
- [ ] No crashes when CLAUDE.md missing
- [ ] Unit tests pass (pytest tests/)
- [ ] End-to-end workflow validated

---

## Dependencies

- Existing: CWO12 workflow engine
- Existing: Hooks infrastructure
- Existing: shared_utils.py for state management
- New: ProjectConstraints dataclass
- New: ConstraintReader module

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| CLAUDE.md parsing breaks on format change | Use delimiters for constraint sections |
| Agent ignores constraint references | Add PreToolUse validation (future enhancement) |
| Performance overhead | LRU cache with 1-hour TTL |
| Project-specific overrides needed | Add optional override file (Phase 8) |

---

## Notes

- All phases can be developed independently
- Phase 1 (ConstraintReader) is prerequisite for Phases 2-5
- Phases 2-5 can be done in parallel after Phase 1
- Phase 6 (integration) requires Phases 1-5 complete
