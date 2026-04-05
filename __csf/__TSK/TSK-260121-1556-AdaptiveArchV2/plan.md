# Implementation Plan: Adaptive Architect System v2

**TSK:** TSK-260121-1556-AdaptiveArchV2
**Created:** 2026-01-21 15:56
**Source:** Migration docs (arch-system-migration.md)
**Total Estimated Time:** 26-34 hours (all 4 phases)

---

## Overview

Transform monolithic `/arch` into complexity-aware routing system with 3 skill personas. Implementation divided into 4 incremental phases, each delivering value independently.

**Key Principle:** Each phase is independently valuable. Phase 1 is production-ready MVP.

---

## Prerequisites

1. **Existing Files Verified:**
   - `P:/.claude/skills/arch/SKILL.md` exists (v1 to be preserved)
   - `P:/__csf/src/lib/` directory exists

2. **Migration Docs Available:**
   - `C:\Users\brsth\Downloads\arch-system-migration.md` (complete implementation code)
   - `C:\Users\brsth\Downloads\arch-system-complete.md` (reference)

3. **Permissions:**
   - Write access to `P:/.claude/skills/arch/`
   - Write access to `P:/__csf/src/lib/`

---

## Phase 1: Core Router (6-8 hours) - MVP

**Deliverable:** Working router + 3 personas, v1 preserved, zero breaking changes

### Task 1.1: Rename v1 to arch-v1.md
**File:** `P:/.claude/skills/arch/SKILL.md` → `P:/.claude/skills/arch/arch-v1.md`
**Action:**
- Rename file
- Update YAML frontmatter:
  - `name: arch-v1`
  - `triggers: [arch-v1, arch-legacy]`
  - Add description: "(v1 monolithic legacy, 13 artifacts always deep)"
**Acceptance:**
- File renamed to `arch-v1.md`
- `SKILL.md` no longer exists at original path
- Triggers updated in frontmatter
**Verification:** `ls P:/.claude/skills/arch/` shows `arch-v1.md`
**Time:** 2 minutes

### Task 1.2: Create complexity_measure_v2.py
**File:** `P:/__csf/src/lib/complexity_measure_v2.py`
**Action:** Copy complete code from migration doc lines 134-349
**Source:** `arch-system-migration.md` File 1 section (400 lines)
**Acceptance:**
- File exists at specified path
- Contains `ComplexityScore` dataclass
- Contains `ComplexityMeasure` class with `measure()` method
- Has test cases in `if __name__ == "__main__"`
**Verification:**
```bash
cd P:/__csf/src
python -c "from lib.complexity_measure_v2 import measure_complexity; result = measure_complexity('swap two checks'); print(result.level)"
```
**Expected:** `TRIVIAL`
**Time:** 5 minutes

### Task 1.3: Create artifact_selector_v2.py
**File:** `P:/__csf/src/lib/artifact_selector_v2.py`
**Action:** Copy complete code from migration doc lines 357-570
**Source:** `arch-system-migration.md` File 2 section (250 lines)
**Acceptance:**
- File exists at specified path
- Contains `route_by_complexity()` function
- Contains `format_router_output()` function
- Has `ARTIFACTS_BY_PATH` and `PATH_INFO` constants
**Verification:**
```bash
cd P:/__csf/src
python -c "from lib.artifact_selector_v2 import route_by_complexity; print(route_by_complexity('TRIVIAL'))"
```
**Expected:** `FAST`
**Time:** 5 minutes

### Task 1.4: Create arch.md (Router)
**File:** `P:/.claude/skills/arch/arch.md`
**Action:** Copy complete markdown from migration doc lines 578-737
**Source:** `arch-system-migration.md` File 3 section
**Acceptance:**
- File exists with correct YAML frontmatter (`name: arch`, `triggers: [arch, architecture]`)
- Contains Stage 1 (import lib modules, measure complexity)
- Contains Stage 2 (format and display recommendation)
- Has Quick Reference table
- Has Manual Override Commands section
**Verification:** `ls P:/.claude/skills/arch/arch.md` shows file
**Time:** 5 minutes

### Task 1.5: Create arch-fast.md (Surgeon)
**File:** `P:/.claude/skills/arch/arch-fast.md`
**Action:** Copy complete markdown from migration doc lines 741-866
**Source:** `arch-system-migration.md` File 4 section
**Acceptance:**
- File exists with YAML frontmatter (`name: arch-fast`, `triggers: [arch-fast]`)
- Persona: Code Surgeon
- Output Structure: Decision, Options (2-3), Recommendation, Implementation, Ramifications
- Constraints: 1-5 KB max, no fake alternatives
**Verification:** `ls P:/.claude/skills/arch/arch-fast.md` shows file
**Time:** 3 minutes

### Task 1.6: Create arch-deep.md (Architect)
**File:** `P:/.claude/skills/arch/arch-deep.md`
**Action:** Copy complete markdown from migration doc lines 870-988
**Source:** `arch-system-migration.md` File 5 section
**Acceptance:**
- File exists with YAML frontmatter (`name: arch-deep`, `triggers: [arch-deep]`)
- Persona: Systems Architect
- 11 stages: Verify Complexity → Adversarial Challenge
- Context Sources section for Phase 2+
**Verification:** `ls P:/.claude/skills/arch/arch-deep.md` shows file
**Time:** 5 minutes

### Task 1.7: Create arch-precedent.md (Historian)
**File:** `P:/.claude/skills/arch/arch-precedent.md`
**Action:** Copy complete markdown from migration doc lines 992-1103
**Source:** `arch-system-migration.md` File 6 section
**Acceptance:**
- File exists with YAML frontmatter (`name: arch-precedent`, `triggers: [arch-precedent]`)
- Persona: Systems Architect + Historian
- Part 1: Full Analysis (same as arch-deep)
- Part 2: Record the Decision (ADR/Docs/Archive options)
- ADR Template included
**Verification:** `ls P:/.claude/skills/arch/arch-precedent.md` shows file
**Time:** 5 minutes

### Task 1.8: Test Phase 1 Integration
**Action:** Verify all components work together
**Tests:**
1. `/arch "should I swap two checks?"` → TRIVIAL → Recommends /arch-fast
2. `/arch "introduce a service"` → MODERATE → Recommends /arch-deep
3. `/arch "redesign schema"` → COMPLEX → Recommends /arch-deep, hints /arch-precedent
4. `/arch-v1 "any query"` → Runs full v1 monolithic (backward compat)
**Acceptance:** All 4 tests pass
**Verification:** Manual invocation of each command
**Time:** 15 minutes

---

## Phase 2: Knowledge Integration (8-10 hours)

**Deliverable:** Context gathering from CKS, ADR index, constitutional constraints, dependencies

### Task 2.1: Create mentalmodelselector.py
**File:** `P:/__csf/src/lib/mentalmodelselector.py`
**Action:** Create mental model selection module (100 lines)
**Acceptance:**
- Maps decision types to RCA frameworks
- `select_mental_models(query, max_models=3)` function
- Returns relevant cognitive frameworks
**Verification:** Unit test with sample query
**Time:** 2 hours

### Task 2.2: Create ckssemanticsearch.py
**File:** `P:/__csf/src/lib/ckssemanticsearch.py`
**Action:** Create CKS semantic search module (80 lines)
**Acceptance:**
- Integrates with unified_semantic_daemon
- `search_patterns(query, limit=5)` function
- Returns historical patterns from CKS
**Verification:** Unit test with CKS query
**Time:** 2 hours

### Task 2.3: Create adrindexlookup.py
**File:** `P:/__csf/src/lib/adrindexlookup.py`
**Action:** Create ADR index lookup module (80 lines)
**Acceptance:**
- Reads ADR index from `P:/__csf/docs/adr/index.md`
- `get_precedent_adrs(query)` function
- Returns related past decisions
**Verification:** Unit test with ADR lookup
**Time:** 1.5 hours

### Task 2.4: Create constitutionalcontext.py
**File:** `P:/__csf/src/lib/constitutionalcontext.py`
**Action:** Create solo-dev constraints module (60 lines)
**Acceptance:**
- Reads `P:/CLAUDE.md` solo-dev constraints
- `get_constraints()` function
- Returns forbidden patterns for solo-dev
**Verification:** Unit test returns constraints
**Time:** 1 hour

### Task 2.5: Create dependencyscanning.py
**File:** `P:/__csf/src/lib/dependencyscanning.py`
**Action:** Create dependency scanning module (100 lines)
**Acceptance:**
- Scans file imports for coupling analysis
- `analyze_dependencies(files)` function
- Returns coupling map and risk score
**Verification:** Unit test on sample code
**Time:** 2 hours

### Task 2.6: Integrate Phase 2 into arch-deep and arch-precedent
**Files:** `P:/.claude/skills/arch/arch-deep.md`, `arch-precedent.md`
**Action:** Add "Context Sources" section calling Phase 2 modules
**Acceptance:**
- Skills import and use Phase 2 lib modules
- Context displayed in analysis output
**Verification:** `/arch-deep` query shows CKS patterns, ADRs, constraints
**Time:** 1.5 hours

---

## Phase 3: Enhancement Modes (6-8 hours)

**Deliverable:** Optional mode flags (--zen, --deep, --debate, --challenge)

### Task 3.1: Create enhancementrouter.py
**File:** `P:/__csf/src/lib/enhancementrouter.py`
**Action:** Create enhancement mode router (150 lines)
**Acceptance:**
- Parses mode flags: `--zen`, `--deep`, `--debate`, `--challenge`
- `EnhancementRouter` class with `route()` method
- Each mode modifies analysis depth/approach
**Verification:** Unit test each mode
**Time:** 3 hours

### Task 3.2: Integrate enhancement modes into skills
**Files:** `arch-fast.md`, `arch-deep.md`, `arch-precedent.md`
**Action:** Add mode flag parsing and routing
**Acceptance:**
- Skills accept mode flags in ARGUMENTS
- Pass to enhancementrouter
- Output reflects selected mode
**Verification:** `/arch-deep "query" --zen` shows minimal context
**Time:** 2 hours

### Task 3.3: Test all enhancement modes
**Action:** Verify each mode produces distinct output
**Tests:**
1. `--zen`: Minimal context, fastest
2. `--deep`: Maximum context, slowest
3. `--debate`: Multi-perspective experts
4. `--challenge`: Adversarial focus
**Acceptance:** All 4 modes produce distinct outputs
**Verification:** Manual test each mode
**Time:** 1 hour

---

## Phase 4: Stack-Specific Analysts (6-8 hours)

**Deliverable:** Automatic stack detection + domain-specific analyst skills

### Task 4.1: Create stackdetector.py
**File:** `P:/__csf/src/lib/stackdetector.py`
**Action:** Create stack detection module (100 lines)
**Acceptance:**
- Detects framework from imports (Python, Data Pipeline, CLI)
- `detect_stack(code_context)` function
- Returns stack type for routing
**Verification:** Unit test with Python, data, CLI code
**Time:** 2 hours

### Task 4.2: Create arch-python.md
**File:** `P:/.claude/skills/arch/arch-python.md`
**Action:** Create Python-specific analyst skill (200 lines)
**Acceptance:**
- Triggers: `/arch-python`
- Python-specific concerns: async, GIL, type hints
- Integrates with stackdetector
**Verification:** Skill file exists and loads
**Time:** 1.5 hours

### Task 4.3: Create arch-data-pipeline.md
**File:** `P:/.claude/skills/arch/arch-data-pipeline.md`
**Action:** Create data pipeline analyst skill (200 lines)
**Acceptance:**
- Triggers: `/arch-data-pipeline`
- Data-specific concerns: ETL, backpressure, Spark
- Integrates with stackdetector
**Verification:** Skill file exists and loads
**Time:** 1.5 hours

### Task 4.4: Create arch-cli.md
**File:** `P:/.claude/skills/arch/arch-cli.md`
**Action:** Create CLI analyst skill (200 lines)
**Acceptance:**
- Triggers: `/arch-cli`
- CLI-specific concerns: POSIX, exit codes, signals
- Integrates with stackdetector
**Verification:** Skill file exists and loads
**Time:** 1.5 hours

### Task 4.5: Integrate stack detection into router
**File:** `P:/.claude/skills/arch/arch.md`
**Action:** Add stack detection hint to router output
**Acceptance:**
- Router detects stack if code context provided
- Suggests stack-specific analyst
**Verification:** `/arch "query"` with Python code suggests `/arch-python`
**Time:** 1 hour

---

## Dependencies

**Internal:**
- Existing `P:/.claude/skills/arch/SKILL.md` (to be renamed)
- Existing `P:/__csf/src/lib/` directory
- Existing `P:/CLAUDE.md` for constitutional context

**External:**
- None (all implementation is self-contained)

**Blocking:**
- None (can start immediately)

---

## Testing Strategy

### Unit Tests
- Each lib module has `if __name__ == "__main__"` test cases
- Verify imports work
- Verify core functions return expected types

### Integration Tests
- Phase 1: Test router classification accuracy
- Phase 2: Test context gathering from CKS/ADR
- Phase 3: Test each enhancement mode
- Phase 4: Test stack detection

### Manual Tests
- Invoke `/arch` with sample queries at each complexity level
- Verify manual overrides work
- Verify backward compatibility (`/arch-v1`)

---

## Rollback Plan

**If Phase 1 fails:**
1. Delete new files: `arch.md`, `arch-fast.md`, `arch-deep.md`, `arch-precedent.md`
2. Rename `arch-v1.md` back to `SKILL.md`
3. Delete `complexity_measure_v2.py`, `artifact_selector_v2.py`
4. System restored to original state

**If later phases fail:**
- Phase 1 remains functional (independent phases)
- Failed phase modules can be disabled/removed
- Router continues working without optional features

---

## Success Criteria

- [ ] Phase 1: Router recommends correct path 80%+ of time
- [ ] Phase 1: Trivial decisions complete in <5 minutes (12× faster)
- [ ] Phase 1: Manual overrides work without complaint
- [ ] Phase 1: `/arch-v1` still works (backward compatible)
- [ ] Phase 2: Context gathering from CKS/ADR works
- [ ] Phase 3: All 4 enhancement modes produce distinct output
- [ ] Phase 4: Stack detection suggests correct specialist
- [ ] All 17 files created successfully
- [ ] All unit tests pass
- [ ] All integration tests pass

---

## Total Time Estimate

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1 | 8 tasks | 6-8 hours |
| Phase 2 | 6 tasks | 8-10 hours |
| Phase 3 | 3 tasks | 6-8 hours |
| Phase 4 | 5 tasks | 6-8 hours |
| **Total** | **22 tasks** | **26-34 hours** |
