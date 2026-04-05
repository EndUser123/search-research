# Implementation Plan: Hybrid Documentation Validation Model

**Created:** 2025-03-07
**Status:** DRAFT
**Objective:** Transform /docs-validate from pure reactive skill to hybrid model with automatic validation and user configuration

---

## 1. Problem Statement

The /docs-validate skill currently uses a **pure reactive invocation model**:
- Users must manually run `/docs-validate <path>` to check documentation quality
- No automatic validation when documentation is edited
- Quality assurance depends entirely on user memory and initiative
- Inconsistent validation coverage across skills ecosystem

**Why this matters:**
- Documentation quality issues (circular refs, missing files, version conflicts) go undetected
- No systematic quality assurance across the skills ecosystem
- Users can ship documentation that violates all quality standards
- Reactive-only model creates quality variance: validated skills vs. never-validated skills

---

## 2. Context Analysis

### Current State

**Existing Components:**

1. **/docs-validate skill** (`P:/.claude\skills\docs-validate/SKILL.md`)
   - Manual invocation via `/docs-validate <path>` command
   - Uses DocumentationValidator class from /package
   - Provides reactive validation with detailed issue reporting
   - Workflow: Identify target → Run validation → Categorize issues → Suggest fixes → Generate report

2. **PostToolUse_documentation_validator.py hook** (`P:/.claude\hooks/PostToolUse_documentation_validator.py`)
   - **ALREADY EXISTS** - validates /package directory documentation after Write/Edit operations
   - Returns warning dict (non-blocking by default)
   - Only activates for /package directory, not general skills
   - Graceful degradation if DocumentationValidator unavailable

3. **DocumentationValidator class** (`P:/.claude\skills\package\resources\validate_docs.py`)
   - Validation checks: circular_reference, missing_file, version_conflict
   - API: `validator = DocumentationValidator(docs_dir)` → `issues = validator.validate()`
   - Returns list of issue dicts with severity, type, file, message, fix fields

### Allowed APIs

**Confirmed from documentation discovery:**

**PostToolUse Hook Protocol** (from PROTOCOL.md):
- Input: `{"tool_name": str, "tool_input": dict, "tool_response": any}`
- Output: Warning dict `{"warning": "message"}` (non-blocking) OR empty dict `{}`
- Exit code: Always 0 (warnings shown via stdout)

**DocumentationValidator API** (from validate_docs.py):
- Constructor: `DocumentationValidator(docs_dir: Path)`
- Method: `validate() -> List[Dict[str, str | int]]`
- Issue dict structure: `{severity: "HIGH|MEDIUM", type: str, file: str, message: str, fix: str}`

**Hook Configuration Pattern** (from CLAUDE.md):
- Environment variables: `HOOK_NAME_ENABLED` (default: true), `HOOK_NAME_MODE` (default: warn)
- Settings files: `.claude/plugin-name.local.md` with YAML frontmatter
- Graceful degradation: Hooks return early if dependencies unavailable

### Anti-patterns to Avoid

1. **Blocking by default** - Should warn first, allow opt-in to blocking mode
2. **Breaking existing workflow** - Keep manual `/docs-validate` command functional
3. **Duplicating DocumentationValidator logic** - Reuse existing class, don't reimplement
4. **Hardcoded paths** - Use path discovery patterns like _find_package_root()
5. **Silent failures** - Always provide user feedback, use graceful degradation with warnings

---

## 3. Existing Implementation Discovery

### Current Hook Implementation

**PostToolUse_documentation_validator.py** (existing):
```python
def run(data: dict) -> dict:
    # Only validates Write/Edit operations on .md files in /package directory
    if tool_name not in ("Write", "Edit"):
        return {}
    if not _is_markdown_file(file_path):
        return {}
    if not _is_package_file(file_path):
        return {}

    # Import DocumentationValidator and run validation
    from validate_docs import DocumentationValidator
    validator = DocumentationValidator(package_root)
    issues = validator.validate()

    # Return warning dict if issues found
    if issues:
        return _format_validation_warnings(issues)
    return {}
```

**Gap identified:** Hook only works for /package directory, not general skills

### Current Skill Implementation

**/docs-validate skill** (SKILL.md):
- Manual invocation pattern
- Integration section mentions PostToolUse hook as "optional integration"
- No automatic validation triggers
- No configuration system

**Gap identified:** Skill frames automatic validation as optional add-on rather than core pattern

---

## 4. Test Discovery

### Test Scenarios

**Unit Tests** (verify hook behavior):
1. PostToolUse hook triggers on Write/Edit of .md files in skills directories
2. Hook returns warning dict with validation issues
3. Hook returns empty dict when no issues found
4. Hook gracefully handles DocumentationValidator import errors
5. Configuration file parsing (.claude/docs-validate.local.md)
6. Mode switching (suggestive/blocking/off)

**Integration Tests** (verify end-to-end flow):
1. User edits SKILL.md → hook shows warning message
2. User sets mode=blocking → hook blocks writes with quality issues
3. User sets mode=blocking → hook returns valid JSON with permissionDecision=deny field
4. User sets mode=off → hook skips validation
5. Manual `/docs-validate` command still works
6. Warning message format matches existing pattern

**Edge Cases**:
- DocumentationValidator module not found (graceful degradation)
- Invalid settings file (fallback to defaults)
- Circular references in settings validation itself
- Concurrent writes to same file
- Path resolution for symlinked skills

### Verification Commands

```bash
# Unit tests
pytest P:/.claude/hooks/tests/test_documentation_validator_hook.py -v

# Integration test
# Edit a SKILL.md with circular reference
# Verify hook shows warning

# Manual verification
/docs-validate P:/.claude/skills/test-skill
# Should still work as before
```

---

## 5. Proposed Solution

### Architecture: Smart Hybrid Model

**Three-tier validation approach:**

**Tier 1: Automatic Non-Blocking Validation** (default)
- PostToolUse hook validates all .md file writes in skills directories
- Returns warning dict (non-blocking)
- Shows issue summary in Claude response
- User can ignore and continue work

**Tier 2: User-Configurable Strictness** (opt-in)
- Settings file: `.claude/docs-validate.local.md`
- Configuration options:
  - `mode: suggestive|blocking|off` (default: suggestive)
  - `severity_threshold: high|medium|low` (default: medium)
  - `auto_validate: true|false` (default: true)
- Blocking mode returns permissionDecision=deny via JSON protocol

**Tier 3: Manual Full Validation** (always available)
- `/docs-validate <path>` command continues to work
- Provides comprehensive validation report
- Useful for pre-publish validation sweeps

### Key Design Decisions

**1. Extend Existing Hook** (not create new hook)
- Modify `PostToolUse_documentation_validator.py` to work for all skills
- Remove /package-only restriction
- Add configuration file reading
- Add mode switching logic

**2. Non-Blocking by Default** (user-friendly)
- Default mode: suggestive (warnings, no blocking)
- Users must opt-in to blocking mode
- Prevents breaking existing workflows

**3. Graceful Degradation** (robustness)
- If DocumentationValidator unavailable → return warning about unavailability
- If settings file invalid → use defaults
- If validation errors → don't break the write operation

**4. Preserve Manual Command** (backwards compatibility)
- `/docs-validate` skill continues to work as-is
- No changes to skill workflow
- Hook adds automatic validation, doesn't replace manual invocation

### Component Changes

**Modified Files:**
1. `P:/.claude/hooks/PostToolUse_documentation_validator.py`
   - Add settings file reading
   - Add mode switching (suggestive/blocking/off)
   - Remove /package-only restriction
   - Add permissionDecision for blocking mode

**New Files:**
1. `P:/.claude/hooks/tests/test_documentation_validator_hook.py`
   - Unit tests for hook behavior
   - Configuration tests
   - Mode switching tests

2. `P:/.claude/skills/docs-validate/examples/docs-validate.local.md`
   - Settings file template
   - Configuration examples

**Updated Files:**
1. `P:/.claude/skills/docs-validate/SKILL.md`
   - Update "Integration" section to position hooks as core (not optional)
   - Add "Configuration" section explaining modes
   - Add "Quick Start" for opt-in to automatic validation

---

## 6. Implementation Plan

### Phase 1: Extend Hook for All Skills (1-2 hours)

**Tasks:**
1. Remove /package-only restriction from PostToolUse_documentation_validator.py
2. Add path discovery for general skills directories
3. Test hook activates on any .md file write in skills/

**Acceptance Criteria:**
- Hook validates Write/Edit operations on any skills/*/.md file
- Hook returns appropriate warnings for non-package skills
- Unit tests pass for general skills validation

**Rollback:** Revert changes to PostToolUse_documentation_validator.py

### Phase 2: Add Configuration System (1-2 hours)

**Tasks:**
1. Add settings file reading function
2. Parse `.claude/docs-validate.local.md` YAML frontmatter
3. Extract mode, severity_threshold, auto_validate settings
4. Add defaults: mode=suggestive, severity_threshold=medium, auto_validate=true

**Acceptance Criteria:**
- Hook reads settings file if present
- Invalid settings file falls back to defaults
- Missing settings file uses defaults
- Unit tests for configuration parsing

**Rollback:** Remove configuration reading code, keep hardcoded defaults

### Phase 3: Add Mode Switching (2-3 hours)

**Tasks:**
1. Implement suggestive mode (default): return warning dict
2. Implement blocking mode: return permissionDecision=deny with JSON protocol
3. Implement off mode: skip validation entirely
4. Add mode validation (only allow suggestive/blocking/off)

**Acceptance Criteria:**
- Suggestive mode: warning shown, write operation completes
- Blocking mode: write operation blocked, reason shown, returns valid JSON with permissionDecision=deny field
- Off mode: no validation performed
- Unit tests for all three modes
- **Note:** Draft mode not implemented in this phase (future enhancement)

**Rollback:** Remove mode switching logic, always use suggestive mode

### Phase 4: Update Documentation (1 hour)

**Tasks:**
1. Update /docs-validate/SKILL.md "Integration" section
2. Add "Configuration" section with examples
3. Create settings file template in examples/
4. Update hook documentation in CLAUDE.md

**Acceptance Criteria:**
- SKILL.md explains automatic validation is now default
- Configuration examples provided
- Settings template shows all options
- Documentation consistent with implementation

**Rollback:** Revert documentation changes

### Phase 5: Testing & Validation (1-2 hours)

**Tasks:**
1. Write unit tests for hook behavior
2. Write integration tests for end-to-end flow
3. Test edge cases (missing validator, invalid settings, etc.)
4. Manual verification of `/docs-validate` command still works

**Acceptance Criteria:**
- All unit tests pass
- Integration tests validate hook triggers correctly
- Edge cases handled gracefully
- Manual command continues to work

**Rollback:** N/A (testing phase)

### Total Estimated Time: 6-10 hours

---

## 7. Risks, Success Criteria, Dependencies

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Hook breaks existing workflow** | Medium | High | Default to suggestive mode (non-blocking), require opt-in for blocking |
| **Configuration file complexity** | Low | Medium | Provide simple template, clear examples, graceful fallback |
| **Path resolution failures** | Medium | Medium | Use proven _find_package_root() pattern, test with symlinked skills |
| **Performance impact on every write** | Low | Low | Validation is fast (<100ms), only runs on .md files |
| **Mode switching confusion** | Low | Medium | Clear documentation, simple three-option mode (off/suggestive/blocking) |

### Success Criteria

**Functional Requirements:**
- [ ] Hook validates all .md files in skills directories (not just /package)
- [ ] Configuration system works with .claude/docs-validate.local.md
- [ ] Three modes work: off (no validation), suggestive (warnings), blocking (rejects writes)
- [ ] Manual `/docs-validate` command continues to work
- [ ] Graceful degradation when DocumentationValidator unavailable

**Quality Requirements:**
- [ ] Unit test coverage ≥80% for new functionality
- [ ] No regression in existing hook behavior for /package directory
- [ ] Warning message format matches existing pattern
- [ ] Documentation updated and accurate

**User Experience Requirements:**
- [ ] Default behavior (suggestive mode) doesn't break existing workflows
- [ ] Configuration is simple and discoverable
- [ ] Error messages are clear and actionable
- [ ] Performance impact negligible (<100ms per write)

### Dependencies

**Required:**
- DocumentationValidator class exists at `P:/.claude\skills\package\resources\validate_docs.py`
- Hook infrastructure supports PostToolUse events
- YAML parsing library available (standard library)

**Optional:**
- None - all functionality can be implemented with existing infrastructure

### Pre-Mortem Analysis

**Failure Scenario 1:** "6 months later, users complain hook is too noisy and they've disabled it"

**Root Cause:**
- False positives on incomplete edits
- Warning shown on every save, even during drafting
- No way to temporarily disable without editing settings file

**Preventive Actions:**
1. Default to suggestive mode (warnings, not blocking)
2. Only validate on Write/Edit completion, not during drafting
3. Provide easy mode=off option in settings
4. **Note:** "Draft mode" that skips validation is a **future enhancement** (out-of-scope for Phase 1-5)

**Failure Scenario 2:** "Hook incorrectly blocks valid writes, users can't save documentation"

**Root Cause:**
- Blocking mode enabled by mistake
- False positive in validation logic
- Configuration file parsing error

**Preventive Actions:**
1. Default to suggestive mode (blocking requires opt-in)
2. Extensive testing before enabling blocking mode
3. Graceful degradation: validation errors → warnings, not blocks
4. Clear documentation about blocking mode implications

**Failure Scenario 3:** "Performance degradation on every documentation save"

**Root Cause:**
- Validation too slow (>1 second)
- Running full validation on every keystroke
- Path resolution scanning entire filesystem

**Preventive Actions:**
1. Target <100ms validation time (measured in testing)
2. Only validate on Write/Edit tool completion (not during typing)
3. Use efficient path discovery (existing _find_package_root pattern)
4. Cache DocumentationValidator instances if needed

---

## Next Actions

1. **Review plan** - Verify approach aligns with user requirements
2. **Approve plan** - Get user sign-off on implementation strategy
3. **Begin Phase 1** - Extend hook for all skills
4. **Track progress** - Update task list as phases complete

**Command to start implementation:**
```bash
# Begin Phase 1: Extend Hook for All Skills
cd P:/.claude/hooks
# Modify PostToolUse_documentation_validator.py
# Test with skills outside /package directory
```
