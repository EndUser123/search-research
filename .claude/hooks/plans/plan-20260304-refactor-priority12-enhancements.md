# Plan: Implement Priority 1+2 Refactoring Enhancements for /refactor Skill

## Overview

Add professional-grade safety enhancements to the `/refactor` skill: Priority 1 (rollback planning + behavior characterization) and Priority 2 (complexity triage + import hygiene). Total effort: ~5 hours for documented-only changes to SKILL.md specification.

## Architecture

**Module structure:** Single file modification
- `P:/.claude/skills/refactor/SKILL.md` — Extend TDD Phase Implementation section with new capabilities

**Key components:**
1. **Rollback Planning** — Git-based recovery plans stored in `.evidence/refactor/rollbacks/`
2. **Behavior Characterization** — Capture inputs/outputs/side-effects before refactoring
3. **Complexity Triage** — Detect high-complexity files (CC ≥ 15) for safer handling
4. **Import Hygiene** — Detect unused imports, circular dependencies, dead code

## Data Flow

```
/refactor invocation
    ↓
DISCOVER phase (5 agents analyze code)
    ↓
CONSTITUTIONAL FILTER
    ↓
TDD Phase (ENHANCED):
    ├─ RED Phase with behavior characterization
    ├─ Rollback plan creation (.evidence/refactor/rollbacks/{timestamp}.json)
    ├─ GREEN Phase with behavior verification
    └─ REGRESSION Phase
    ↓
Complexity triage flags high-risk files
Import hygiene detects integration issues
    ↓
Refactoring with safety nets
```

## Error Handling

**Documentation changes only** — No runtime code to handle. The skill specification guides execution; errors occur during skill invocation (handled by Claude Code runtime).

## Test Strategy

**Documentation validation:**
- Positive: Verify new sections are present in SKILL.md
- Negative: Verify no contradictions with existing TDD workflow
- Edge cases: Constitutional filter compliance for new patterns

**Integration test:**
- Run `/refactor P:\packages\arch --dry-run` to verify enhancements work
- Check rollback plan generation
- Verify behavior characterization output
- Validate complexity triage flags
- Confirm import hygiene detection

## Standards Compliance

**Markdown documentation:**
- Follow existing /refactor SKILL.md formatting
- Maintain consistent indentation and structure
- Use Python code blocks with type hints

**Constitutional compliance:**
- ✅ Professional quality standards (testing rigor, observability)
- ✅ AI-assisted scalability (parallel agents, automated testing)
- ❌ Enterprise team bloat (multi-human workflows prohibited)
- ✅ Clean abstractions (when justified by complexity)

## Ramifications

**Impact on existing code:** None (documentation-only change)

**Breaking changes:** None (additive only to TDD workflow)

**Backwards compatibility:** Full — existing /refactor workflows unchanged, new features are additive

**Future considerations:** These patterns align with professional solo dev + AI workforce model

## Pre-Mortem Analysis

**Failure Mode 1: Rollback plans fail silently**
- Root cause: Git state changes during refactoring, rollback command invalid
- Prevention: Store git commit hash, validate rollback before applying
- Test: Simulate git state changes, verify rollback plan detection

**Failure Mode 2: Behavior characterization overhead too high**
- Root cause: Capturing side-effects on every function call is expensive
- Prevention: Characterization only for TDD phase, not production
- Test: Measure performance on test refactor, verify acceptable overhead

**Failure Mode 3: Complexity triage misses high-risk files**
- Root cause: Cyclomatic complexity threshold too high, misses dangerous code
- Prevention: Set CC ≥ 15 threshold, calibrate with real data
- Test: Run on known complex files, verify detection accuracy

**Failure Mode 4: Import hygiene false positives**
- Root cause: Detects legitimate dynamic imports or type check imports
- Prevention: Allow common patterns (TYPE_CHECKING, typing.TYPE_CHECKING, # noqa, # type: ignore)
- Test: Run on codebase with type hints, verify no false positives

## Observability Planning

**What to monitor:**
- Rollback plan creation rate vs. total refactorings
- Behavior characterization completion time
- Complexity triage detection rate
- Import hygiene findings rate
- User feedback on enhancement usefulness

**Where to look:**
- Manual /refactor invocations (review enhancement outputs)
- `.evidence/refactor/rollbacks/` directory (verify rollback plans created)
- Test runs on `P:\packages\arch` (validate all enhancements work)

**Alert thresholds:** None (manual skill invocation only)

## Tasks

### Task 1: Add Rollback Planning to TDD Workflow
**Location:** Lines 146-195 in SKILL.md (TDD Phase Implementation section)

**Add rollback plan creation before RED phase:**
```markdown
def create_rollback_plan(finding: dict) -> dict:
    """Generate rollback plan before refactoring.

    Args:
        finding: Refactoring finding with file paths and changes

    Returns:
        dict: Rollback plan with git state and recovery commands
    """
    import subprocess
    from datetime import datetime

    return {
        'timestamp': datetime.now().isoformat(),
        'files_changed': finding.get('files', []),
        'git_commit_before': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            text=True
        ).strip(),
        'rollback_command': 'git revert HEAD',
        'test_baseline': 'pytest tests/ -v',  # Store test command
        'finding_id': finding.get('id', 'unknown')
    }

# Store in .evidence/refactor/rollbacks/{timestamp}.json
```

**Integration point:** Add to `refactor_with_tdd()` function before calling `red_phase()`.

**Success criteria:**
- Rollback plan created before each refactoring
- Stored in `.evidence/refactor/rollbacks/` directory
- Contains git commit hash for recovery
- Includes test baseline command

### Task 2: Add Behavior Characterization
**Location:** Lines 146-195 in SKILL.md (TDD Phase Implementation section)

**Add behavior capture before refactoring:**
```markdown
def characterize_behavior(func, inputs):
    """Capture current behavior before refactoring.

    Args:
        func: Function to characterize
        inputs: Input arguments for the function

    Returns:
        dict: Behavior snapshot with inputs, outputs, side-effects, performance
    """
    import time
    from typing import Any

    # Track state changes
    state_before = get_state_snapshot()

    # Measure performance
    start_time = time.perf_counter()
    try:
        output = func(*inputs)
        success = True
    except Exception as e:
        output = str(e)
        success = False
    end_time = time.perf_counter()

    # Detect side-effects
    state_after = get_state_snapshot()
    side_effects = detect_state_changes(state_before, state_after)

    return {
        'input': inputs,
        'output': output,
        'success': success,
        'side_effects': side_effects,
        'duration_ms': (end_time - start_time) * 1000
    }

def verify_behavior_preserved(before: dict, after: dict) -> bool:
    """Verify behavior preserved after refactoring.

    Args:
        before: Behavior characterization before refactoring
        after: Behavior characterization after refactoring

    Returns:
        bool: True if behavior preserved (within tolerance), False otherwise
    """
    # Compare outputs
    if before['output'] != after['output']:
        return False

    # Check performance within 10% tolerance
    if after['duration_ms'] > before['duration_ms'] * 1.1:
        return False

    # Verify no new side-effects
    if set(after['side_effects']) - set(before['side_effects']):
        return False

    return True
```

**Integration point:** Call `characterize_behavior()` in `red_phase()`, verify in `green_phase()`.

**Success criteria:**
- Behavior captured before refactoring
- Verification after refactoring confirms behavior preserved
- Performance tolerance: 10% slowdown acceptable
- Side-effect detection works for file I/O, state changes

### Task 3: Add Complexity Triage
**Location:** Lines 228-246 in SKILL.md (Agent 2 specification section)

**Extend Agent 2 (adversarial-performance) scope:**
```markdown
**Agent 2: `adversarial-performance` — DRY/Simplicity focus**
- Existing scope: Duplication, extraction, concurrency analysis
- **NEW: Complexity triage** — Detect high-complexity files requiring safer handling

**Complexity triage process:**
For each file in target scope:
1. Calculate cyclomatic complexity (McCabe metric)
2. Flag files with CC ≥ 15 as HIGH_COMPLEXITY
3. Flag files with CC ≥ 20 as VERY_HIGH_COMPLEXITY
4. Recommend enhanced safety measures for high-complexity files:
   - Extra characterization tests
   - Smaller, incremental changes
   - Manual review before automated refactoring
```

**Output format:**
```
COMPLEXITY-001: HIGH_COMPLEXITY
File: src/complex_module.py
Cyclomatic Complexity: 18
Recommendation: Use smaller incremental changes, extra characterization tests
Priority: HIGH (complexity increases refactoring risk)
```

**Success criteria:**
- Complexity calculated for each file
- High-complexity files (CC ≥ 15) flagged
- Very-high-complexity files (CC ≥ 20) get enhanced recommendations
- Integrates with existing Agent 2 workflow

### Task 4: Add Import Hygiene Detection
**Location:** Lines 228-246 in SKILL.md (Agent 3 specification section)

**Extend Agent 3 (adversarial-quality) scope:**
```markdown
**Agent 3: `adversarial-quality` — Conventions focus**
- Existing scope: Type hints, patterns, maintainability
- **NEW: Import hygiene** — Detect unused imports, circular dependencies, dead code

**Import hygiene checks:**
1. **Unused imports:** Detect imported modules never referenced in code
2. **Circular dependencies:** Detect modules that import each other
3. **Dead code:** Detect unused functions, classes, variables
4. **Import ordering:** Verify PEP 8 compliance (stdlib, third-party, local)

**Allowed patterns** (false positive prevention):
- `from typing import TYPE_CHECKING` (used for type hints only)
- `if TYPE_CHECKING:` blocks (type checking imports)
- `# noqa` comments (explicitly allowed)
- `# type: ignore` comments (explicitly allowed)

**Output format:**
```
IMPORT-001: Unused import detected
File: src/module.py:5
Import: `import os` (never referenced)
Action: Remove unused import
Impact: Cleaner code, faster imports
```

```
IMPORT-002: Circular dependency detected
Files: src/auth.py → src/user.py → src/auth.py
Action: Restructure to break cycle
Impact: Prevents import errors, improves testability
```

**Success criteria:**
- Unused imports detected with line numbers
- Circular dependencies mapped between modules
- Dead code flagged (unused functions/variables)
- Import ordering violations reported
- False positive prevention works for TYPE_CHECKING patterns

### Task 5: Update TDD Phase Implementation Section
**Location:** Lines 146-195 in SKILL.md

**Integrate all enhancements into TDD workflow:**
```markdown
def refactor_with_tdd(finding: dict):
    """Full TDD cycle: exemption → rollback → characterize → RED → refactor → GREEN → REGRESSION."""
    if is_exempt_from_tdd(finding['file_path']):
        apply_refactoring(finding)
        return

    # Step 1: Create rollback plan
    rollback_plan = create_rollback_plan(finding)
    save_rollback_plan(rollback_plan)

    # Step 2: Characterize current behavior
    behavior_before = characterize_behavior(target_function, test_inputs)

    # Step 3: RED phase
    test_file = red_phase(finding)

    # Step 4: Apply refactoring
    apply_refactoring(finding)

    # Step 5: GREEN phase with behavior verification
    behavior_after = characterize_behavior(target_function, test_inputs)
    if not verify_behavior_preserved(behavior_before, behavior_after):
        raise RuntimeError("Behavior changed unexpectedly - rollback required")

    green_phase(finding, test_file)

    # Step 6: REGRESSION phase
    regression_phase(finding)

    # Step 7: Cleanup rollback plan on success
    cleanup_rollback_plan(rollback_plan['timestamp'])
```

**Success criteria:**
- All 7 steps documented in TDD workflow
- Rollback plan integrated at start
- Behavior characterization before/after
- Behavior verification in GREEN phase
- Rollback cleanup on success

### Task 6: Update Evidence Storage Documentation
**Location:** Lines 392-416 in SKILL.md (Evidence Collection section)

**Add new storage locations:**
```markdown
### Evidence Storage

All artifacts stored in `P:\.evidence/` — subdirectories: `commands/`, `tests/`, `files/`, `state/`, `refactor/`.

**New directories:**
- `.evidence/refactor/rollbacks/` — Rollback plans with git state
- `.evidence/refactor/behavior/` — Behavior characterizations

| Phase | Evidence Required | Verification |
|-------|------------------|--------------|
| Rollback planning | Rollback plan JSON with git commit | Rollback plan created before refactoring |
| Characterization | Behavior snapshots (before/after) | Behavior preserved within 10% tolerance |
| Refactoring | Post-change test results | `verify_tdd_green()` passes |
| Regression | Full suite results | No new failures introduced |
```

**Success criteria:**
- New evidence directories documented
- Storage format specified (JSON for rollbacks)
- Verification requirements clear
- Evidence requirements table updated

### Task 7: Test Enhancements on Real Code
**Location:** Integration test

**Test command:**
```bash
# Run /refactor with --dry-run on test package
/refactor P:\packages\arch --dry-run
```

**Verification checklist:**
- [ ] Rollback plans generated in `.evidence/refactor/rollbacks/`
- [ ] Behavior characterization output in console/logs
- [ ] Complexity triage flags high-complexity files (if any)
- [ ] Import hygiene detects unused imports (if any)
- [ ] All enhancements work without breaking existing workflow
- [ ] Constitutional filter compliance maintained

**Success criteria:**
- Dry run completes without errors
- All enhancement outputs visible
- No conflicts with existing 5-agent system
- Ready for production use

## Implementation Order

1. **Task 1** — Add rollback planning (1 hour) — Foundation for safe refactoring
2. **Task 2** — Add behavior characterization (2 hours) — Prevents subtle bugs
3. **Task 5** — Update TDD workflow section (30 min) — Integrate Tasks 1+2
4. **Task 3** — Add complexity triage (1 hour) — Catches high-risk files
5. **Task 4** — Add import hygiene (1 hour) — Prevents integration bugs
6. **Task 6** — Update evidence documentation (15 min) — Document new storage
7. **Task 7** — Test on real code (15 min) — Validate enhancements work

**Estimated effort:** 5 hours total (documentation-only changes)

## Implementation Status

**PENDING** — Plan created, awaiting implementation

**Next steps:**
1. Execute tasks in implementation order
2. Update `P:\.claude\skills\refactor\SKILL.md` with all enhancements
3. Test on `P:\packages\arch` with `--dry-run`
4. Validate all enhancements work correctly
