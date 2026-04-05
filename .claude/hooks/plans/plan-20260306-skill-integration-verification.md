# Implementation Plan: Skill Integration Verification System

**Created:** 2026-03-06
**Status:** DRAFT
**Objective:** Prevent "aspirational documentation" anti-pattern by automatically verifying skill integration claims

---

## 1. Problem Statement

**The Problem:**
User discovered that `async-bugs/SKILL.md` claimed integration with `/code` and `/refactor` skills (lines 107-109), but those integrations didn't actually exist. The documentation was aspirational, not factual. User had to explicitly ask: "is /async-bugs added to all the skills that can take advantage of it?" to discover this gap.

**Root Cause:**
Documentation written before implementation verification. No validation step in skill development workflow to check that:
- "suggest:" targets actually exist
- Target skills reciprocate the integration
- Integration code is actually implemented

**Impact:**
- Technical debt accumulates unnoticed
- User must explicitly discover gaps
- Trust in documentation erodes
- Downstream workflows break (e.g., expecting async-bugs to run in /code EXPLORE phase)

**Success Criteria:**
- ✅ Integration gaps detected automatically during documentation
- ✅ Immediate feedback when Write/Edit affects SKILL.md files
- ✅ Documentation matches implementation reality
- ✅ Workflow prevents aspirational documentation

---

## 2. Context Analysis

### Constitutional Constraints
- **Solo-dev constraints apply** (CLAUDE.md): Simple routing, not complex orchestration
- **Truthfulness required**: Validate claims before documentation
- **Evidence-based routing**: Understand context before routing
- **Professional quality appropriate**: Automated verification prevents technical debt
- **NOT enterprise bloat**: Single ~150-line module, not complex framework

### Technical Context
- **Hook Architecture**: PreToolUse, PostToolUse, Stop events available
- **Router Pattern**: PostToolUse_router.py for in-process execution (~5-10ms vs ~184ms subprocess)
- **Base Classes**: PostToolUseHook available (confirmed in `posttooluse/base.py`)
- **Existing Verification Patterns**:
  - `ObservableEffectVerifier` - pattern detection + effect verification
  - `CleanupTrackerHook` - two-phase verification (PostToolUse collects, Stop validates)
- **Skill Structure**: SKILL.md with YAML frontmatter containing "suggest:" field
- **Memory System**: `integration_verification.md` documents the anti-pattern

### Allowed APIs (Verified from Codebase)

**PostToolUseHook Base Class:**
```python
# Location: P:/.claude/hooks/posttooluse/base.py
class PostToolUseHook:
    env_var: str  # Environment variable to enable/disable
    default_enabled: bool = True
    tool_matcher: set[str] | None = None  # Which tools to match

    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        """Returns dict with 'passed', 'injection', etc."""
```

**Router Registration Pattern:**
```python
# Location: P:/.claude/hooks/PostToolUse_router.py
# Add to HOOK_PRIORITY and HOOK_DISPATCH dictionaries
HOOK_PRIORITY = {
    "integration_verifier": 3.5,  # After cleanup_tracker (3.0)
}
```

**SKILL.md Structure (Verified):**
```yaml
---
name: skill-name
description: ...
suggest:
  - /target-skill-1
  - /target-skill-2
---
```

### Anti-Patterns to Avoid
- ❌ Subprocess execution for performance-critical hooks (use in-process)
- ❌ Blocking documentation writes in advisory mode (use warnings only)
- ❌ Complex YAML parsing without regex fallback (graceful degradation)
- ❌ Hard-coded skill lists (use directory scanning)

---

## 3. Existing Implementation Discovery

### Current Verification Approaches

**1. Manual Script (EXISTING - HAS BUG)**
- **Location:** `P:/.claude/skills/verify-skill-integration.sh`
- **Status:** Created but has sed syntax error (line 17: unterminated 's' command)
- **Issues:**
  - Manual invocation required (easy to forget)
  - Not integrated with skill development workflow
  - Bash script (less portable than Python)

**2. testing-skills/SKILL.md (EXISTING - LIMITED SCOPE)**
- **Location:** `P:/.claude/skills/testing-skills/SKILL.md`
- **Scope:** Validates triggers, execution paths, structure
- **Gap:** Does NOT verify skill-to-skill integration claims
- **Quote:** "Validate trigger phrases actually invoke the skill" - no reciprocation check

**3. skill-development/SKILL.md (EXISTING - NO VERIFICATION STEP)**
- **Location:** `P:/.claude/skills/skill-development/SKILL.md`
- **Step 5:** "Validate and Test" - mentions testing but no integration verification
- **Gap:** No systematic check for integration claims

**4. ObservableEffectVerifier (REFERENCE PATTERN)**
- **Location:** `P:/.claude/hooks/posttooluse/observable_effect_verifier.py`
- **Pattern:**
  - PostToolUse hook triggers on Edit/Write
  - Reads file content to detect patterns (e.g., `logging.FileHandler`)
  - Runs verifiers to check effects (e.g., log files exist)
  - Returns warnings via `additionalContext`
- **Key Code:**
```python
class ObservableEffectVerifier(PostToolUseHook):
    env_var = "SEV_ENABLED"
    default_enabled = True
    tool_matcher = {"Edit", "Write"}

    def process(self, tool_name, tool_input, tool_response):
        file_path = self._extract_file_path(tool_input, tool_response)
        content = Path(file_path).read_text()

        for verifier in self.verifiers:
            result = verifier.verify(content)
            if not result.passed:
                return {"injection": result.warning}
```

**5. CleanupTrackerHook (REFERENCE PATTERN)**
- **Location:** `P:/.claude/hooks/posttooluse/cleanup_tracker_hook.py`
- **Pattern:** PostToolUse accumulates data → Stop hook analyzes
- **Key Code:**
```python
class CleanupTrackerHook(PostToolUseHook):
    def process(self, tool_name, tool_input, tool_response):
        # Accumulate tool usage to session file
        session_id = self._extract_session_id(tool_input)
        history_file = f"cleanup_history_{session_id}.json"
        # Append to history...
```

### Integration Points Discovered

**1. Router Registration (PostToolUse_router.py)**
- **Line ~16124:** HOOK_PRIORITY dictionary
- **Line ~16150:** HOOK_DISPATCH dictionary
- **Pattern:** Add hook name, priority, and runner function

**2. Settings Configuration (settings.json)**
- **Location:** `P:/.claude/settings.json`
- **Section:** `env` - for environment variables like `INTEGRATION_VERIFIER_ENABLED`
- **Section:** `hooks.PostToolUse` - for hook registration

**3. YAML Frontmatter Examples**
- **async-bugs/SKILL.md:** Lines 107-109 (the problematic integration claims)
- **code/SKILL.md:** suggest: section includes `/async-bugs` (now implemented)
- **refactor/SKILL.md:** suggest: section includes `/async-bugs` (now implemented)

---

## 4. Test Discovery

### Existing Test Patterns

**Hook Tests:**
- **Location:** `P:/.claude/hooks/tests/`
- **Examples:**
  - `test_observable_effect_verifier.py` (16 tests)
  - `test_cleanup_tracker.py` (19 tests)
  - `test_hook_registration.py` (verifies hooks are registered)
- **Pattern:** pytest with JSON stdin payloads for hook input simulation

**Skill Tests:**
- **Location:** Various skill directories have `tests/` subdirectories
- **Pattern:** Test trigger phrases, execution paths, integration

### Required Test Scenarios

**Unit Tests (integration_verifier.py):**
1. ✅ Non-SKILL.md files are skipped
2. ✅ SKILL.md without suggest: field passes
3. ✅ Missing suggest: targets trigger warnings
4. ✅ One-way integrations trigger warnings
5. ✅ Valid bidirectional integrations pass
6. ✅ YAML parse failure falls back to regex extraction
7. ✅ Malformed frontmatter handled gracefully

**Integration Tests (router registration):**
1. ✅ Hook is registered in PostToolUse_router.py
2. ✅ Hook executes on Write to SKILL.md files
3. ✅ Warnings appear in additionalContext
4. ✅ Environment variable enables/disables hook
5. ✅ Performance baseline <100ms (ObservableEffectVerifier requirement)

**Regression Tests (async-bugs scenario):**
1. ✅ async-bugs SKILL.md triggers verification
2. ✅ Missing /code integration detected
3. ✅ Missing /refactor integration detected
4. ✅ After implementing integrations, verification passes

### Test Data Required

**Sample SKILL.md Files:**
- Valid skill with bidirectional integrations
- Invalid skill with missing targets
- Invalid skill with one-way integrations
- Malformed YAML frontmatter
- Non-skill file (should be skipped)

---

## 5. Proposed Solution

### Architecture: Hook-Based Verification (Option 1 from /arch analysis)

**Primary Component:** `PostToolUse_integration_verifier.py`

**How It Works:**
1. **Trigger:** User runs Write/Edit on SKILL.md file
2. **Extract:** Parse YAML frontmatter to find "suggest:" targets
3. **Verify:** For each suggested skill:
   - Check if target skill exists (SKILL.md file present)
   - Check if target skill mentions this skill (reciprocation)
4. **Report:** Return warnings via `additionalContext` if gaps found

**Integration Points:**
- Register in `PostToolUse_router.py` (existing router infrastructure)
- Use `PostToolUseHook` base class (existing base class)
- Follow ObservableEffectVerifier pattern (reference implementation)

**Configuration:**
```json
// In settings.json
{
  "env": {
    "INTEGRATION_VERIFIER_ENABLED": "true",
    "INTEGRATION_VERIFIER_MODE": "warn"
  }
}
```

**Design Rationale:**
- ✅ **Immediate feedback** - catches gaps during documentation, not later
- ✅ **Follows existing patterns** - ObservableEffectVerifier, CleanupTrackerHook
- ✅ **Low friction** - warnings, not blocks (advisory mode first)
- ✅ **In-process execution** - ~5-10ms vs ~184ms subprocess (router-based)
- ✅ **Automatic** - no manual invocation needed
- ✅ **Solo-dev appropriate** - professional quality, not enterprise bloat

### Alternative: Enhance testing-skills (NOT RECOMMENDED)
- **Pros:** Leverages existing meta-skill, no new code
- **Cons:** Manual invocation, reactive (catches gaps after documentation), easy to forget

### Alternative: Fix Manual Script (NOT RECOMMENDED)
- **Pros:** Already exists, simple bash
- **Cons:** Manual only, not integrated, has sed bug, friction to remember

---

## 6. Implementation Plan

### Prevention Checklist Verification ✅

Before implementation, the following prevention checklist items (from plan-workflow skill) have been verified:

- [x] **Integration Points Defined**: All external systems, APIs, and modules identified in Section 3
- [x] **Import Paths Verified**: PostToolUseHook base class, router infrastructure confirmed existing
- [x] **Path Calculations Tested**: SKILL.md file paths, router paths validated against actual structure
- [x] **Configuration Documented**: Environment variables, settings.json changes specified
- [x] **Tests Outlined**: Unit, integration, and regression test scenarios documented in Section 4

**Note**: Section 3 "Existing Implementation Discovery" serves as the comprehensive discovery record that satisfies all prevention checklist requirements.

### Phase 1: Core Implementation (Week 1)

**Task 1.1: Create IntegrationVerifier Class**
- **File:** `P:/.claude/hooks/posttooluse/integration_verifier.py`
- **Effort:** M
- **Steps:**
  1. Create class extending `PostToolUseHook`
  2. Implement `env_var = "INTEGRATION_VERIFIER_ENABLED"`
  3. Implement `tool_matcher = {"Write", "Edit"}`
  4. Implement `process()` method:
     - Extract file_path from tool_input
     - Skip non-SKILL.md files
     - Read SKILL.md content
     - Parse YAML frontmatter (with regex fallback)
     - Extract "suggest:" targets
     - Verify each target exists and reciprocates
     - Return warnings via additionalContext
- **Acceptance Criteria:**
  - Class implements PostToolUseHook interface
  - Returns correct JSON structure
  - Skips non-SKILL.md files
  - Handles YAML parse failures gracefully

**Task 1.2: Register in Router**
- **File:** `P:/.claude/hooks/PostToolUse_router.py`
- **Effort:** S
- **Steps:**
  1. Add import hook for integration_verifier (after line 25)
  2. Add to HOOK_PRIORITY dictionary (priority: 3.5)
  3. Add to HOOK_DISPATCH dictionary
  4. Create runner function (if needed for pattern)
- **Acceptance Criteria:**
  - Hook appears in router output
  - Executes when Write/Edit affects SKILL.md
  - Priority ordering correct (after cleanup_tracker)

**Task 1.3: Add Configuration**
- **File:** `P:/.claude/settings.json`
- **Effort:** S
- **Steps:**
  1. Add `INTEGRATION_VERIFIER_ENABLED=true` to env section
  2. Add `INTEGRATION_VERIFIER_MODE=warn` to env section
- **Acceptance Criteria:**
  - Environment variables are set
  - Hook is enabled by default
  - Advisory mode (warn) is default

**Task 1.4: Create Unit Tests**
- **File:** `P:/.claude/hooks/tests/test_integration_verifier.py`
- **Effort:** M
- **Steps:**
  1. Create test file with pytest
  2. Test: Non-SKILL.md files skipped
  3. Test: SKILL.md without suggest: passes
  4. Test: Missing targets trigger warnings
  5. Test: One-way integrations trigger warnings
  6. Test: Valid integrations pass
  7. Test: YAML parse failure fallback
  8. Test: Malformed frontmatter handling
- **Acceptance Criteria:**
  - All tests pass
  - Coverage >80%
  - Test execution time <1 second

### Phase 2: Documentation Updates (Week 1)

**Task 2.1: Update skill-development/SKILL.md**
- **File:** `P:/.claude/skills/skill-development/SKILL.md`
- **Effort:** S
- **Steps:**
  1. Locate Step 5: "Validate and Test"
  2. Add integration verification step:
     ```markdown
     **Step 5.5: Integration Verification**
     Run integration verification check:
     bash P:/.claude/hooks/posttooluse/integration_verifier.py <skill-name>

     Verifies that "suggest:" targets exist and reciprocate.
     ```
  3. Update validation checklist
- **Acceptance Criteria:**
  - Step 5.5 added to workflow
  - Validation checklist includes integration verification
  - Documentation is clear and actionable

**Task 2.2: Document in CLAUDE.md**
- **File:** `P:/.claude/hooks/CLAUDE.md` (hooks directory documentation)
- **Effort:** S
- **Steps:**
  1. Locate "Observable Effect Verifier" section
  2. Add new section: "Integration Verifier" below it
  3. Document purpose, architecture, configuration
  4. Add to "PostToolUse hooks" table
- **Acceptance Criteria:**
  - New section added to P:/.claude/hooks/CLAUDE.md
  - Follows existing documentation patterns
  - Includes purpose, architecture, configuration

**Task 2.3: Update integration_verification.md**
- **File:** `C:\Users\brsth\.claude\projects\P--\memory\integration_verification.md`
- **Effort:** S
- **Steps:**
  1. Update "Implementation Status" section
  2. Mark Phase 1 complete (hook implementation)
  3. Mark Phase 2 complete (documentation updates)
  4. Add note about verification script deprecation
- **Acceptance Criteria:**
  - Implementation status reflects completion
  - Deprecation notice added for verify-skill-integration.sh
  - Memory entry is accurate

### Phase 3: Testing and Validation (Week 2)

**Task 3.1: Integration Testing**
- **Effort:** M
- **Steps:**
  1. Create test SKILL.md files (valid, invalid, malformed)
  2. Run hook on test files via router
  3. Verify warnings appear correctly
  4. Verify performance <100ms requirement
  5. Test environment variable enable/disable
- **Acceptance Criteria:**
  - All test scenarios pass
  - Performance baseline met
  - Environment variable works correctly

**Task 3.2: Regression Testing**
- **Effort:** M
- **Steps:**
  1. Create async-bugs regression test
  2. Verify hook detects missing /code integration
  3. Verify hook detects missing /refactor integration
  4. After implementing integrations, verify hook passes
- **Acceptance Criteria:**
  - async-bugs scenario detected correctly
  - Integrations verified after implementation
  - No false positives

**Task 3.3: Fix sed Bug in verify-skill-integration.sh**
- **File:** `P:/.claude/skills/verify-skill-integration.sh`
- **Effort:** S
- **Steps:**
  1. Locate line 17 with unterminated 's' command
  2. Fix sed syntax error
  3. Test script on async-bugs scenario
  4. Add deprecation notice to script header
- **Acceptance Criteria:**
  - Script runs without errors
  - Correctly detects integration gaps
  - Deprecation notice present

### Phase 4: Rollout and Monitoring (Week 2)

**Task 4.1: Deploy in Advisory Mode**
- **Effort:** S
- **Steps:**
  1. Verify all phases complete
  2. Run on test SKILL.md files
  3. Monitor for false positives (1 week)
  4. Tune extraction patterns if needed
- **Acceptance Criteria:**
  - Advisory mode deployed
  - No false positives in testing
  - Performance baseline met

**Task 4.2: Update Workflow Documentation**
- **Effort:** S
- **Steps:**
  1. Announce new verification capability
  2. Update skill-development workflow docs
  3. Provide examples of warnings and fixes
- **Acceptance Criteria:**
  - Workflow updated
  - Examples provided
  - Users aware of new verification

**Task 4.3: Add Scheduled Verification to /main Health Checks**
- **File:** `P:/.claude/skills/_tools/skill_integration_check.py` (NEW), `P:/.claude/skills/_tools/main_health.py` (MODIFY)
- **Effort:** S
- **Steps:**
  1. Create skill_integration_check.py module
  2. Implement check_all_skills() function to verify integrations
  3. Add "skill_integration" to CHECKS dictionary in main_health.py
  4. Test via: `python P:/.claude/skills/_tools/main_health.py`
- **Acceptance Criteria:**
  - /main health includes skill_integration check
  - Verifies all skill integrations bidirectionally
  - Returns pass/warning/critical status
  - Integrated with existing health check framework

---

## 7. Risks, Success Criteria, Dependencies

### Top Risks

**Risk 1: False Positives (MEDIUM)**
- **Description:** Hook flags valid integrations as gaps due to YAML parsing issues
- **Mitigation:** Regex fallback for YAML parse failures; graceful degradation
- **Owner:** Developer
- **Status:** Mitigated by regex fallback in Task 1.1

**Risk 2: Performance Degradation (LOW)**
- **Description:** Hook adds latency to all Write/Edit operations on SKILL.md files
- **Mitigation:** In-process execution (~5-10ms target); only affects SKILL.md files
- **Owner:** Developer
- **Status:** Mitigated by router-based execution (Task 1.2)

**Risk 3: YAML Parsing Complexity (MEDIUM)**
- **Description:** SKILL.md frontmatter may not be valid YAML
- **Mitigation:** Implement regex fallback for suggest: extraction
- **Owner:** Developer
- **Status:** Mitigated by dual-parser approach in Task 1.1

**Risk 4: User Confusion About Warnings (LOW)**
- **Description:** Users don't understand what integration warnings mean
- **Mitigation:** Clear warning messages; documentation in CLAUDE.md
- **Owner:** Technical Writer
- **Status:** Mitigated by documentation in Task 2.2

### Success Criteria

**Phase 1 Success:**
- ✅ IntegrationVerifier class created and extends PostToolUseHook
- ✅ Hook registered in router and executes on SKILL.md Write/Edit
- ✅ Unit tests pass with >80% coverage
- ✅ Performance baseline <100ms met

**Phase 2 Success:**
- ✅ skill-development/SKILL.md includes integration verification step
- ✅ CLAUDE.md documents Integration Verifier section
- ✅ integration_verification.md updated with implementation status

**Phase 3 Success:**
- ✅ Integration tests pass all scenarios
- ✅ Regression test detects async-bugs scenario
- ✅ sed bug in verify-skill-integration.sh fixed

**Phase 4 Success:**
- ✅ Advisory mode deployed without false positives
- ✅ Workflow documentation updated
- ✅ Users aware of new verification capability

**Overall Success:**
- ✅ Integration gaps detected automatically during documentation
- ✅ No aspirational documentation accumulates
- ✅ Documentation matches implementation reality

### Dependencies

**Internal Dependencies:**
- `P:/.claude/hooks/posttooluse/base.py` - PostToolUseHook base class (EXISTING)
- `P:/.claude/hooks/PostToolUse_router.py` - Router registration (EXISTING)
- `P:/.claude/settings.json` - Configuration (EXISTING)
- `P:/.claude/skills/*/SKILL.md` - Skill files (EXISTING)

**External Dependencies:**
- Python 3.11+ (already required)
- pytest (already required for tests)
- No new package dependencies required

**Blocking Dependencies:**
- None - all dependencies are existing codebase components

### Rollback Strategy

**If Hook Causes Issues:**
1. Set `INTEGRATION_VERIFIER_ENABLED=false` in settings.json
2. Hook will be disabled immediately
3. Can re-enable after fixing issues

**If Documentation Updates Cause Confusion:**
1. Revert documentation changes via git
2. Clarify documentation in follow-up commit

### Next Actions

1. **Start Phase 1:** Create IntegrationVerifier class (Task 1.1)
2. **Create Test Plan:** Write test scenarios before implementation (Task 1.4)
3. **Monitor Performance:** Measure execution time during development
4. **Tune Patterns:** Adjust YAML parsing if false positives detected

---

**Plan Status:** DRAFT - Ready for review via `/plan-workflow review`
