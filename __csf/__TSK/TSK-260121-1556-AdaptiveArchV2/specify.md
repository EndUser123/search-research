# Specification: Adaptive Architect System v2

**TSK:** TSK-260121-1556-AdaptiveArchV2
**Created:** 2026-01-21 15:56
**Status:** Draft
**Source:** Migration docs provided by user

---

## Overview

Transform the monolithic `/arch` skill into a complexity-aware routing system with proportional analysis depth. The new system measures decision complexity and routes to appropriate skill personas (surgeon/architect/historian) instead of running full 13-artifact analysis on every query.

**Key Change:** "Swap two checks" no longer takes 60+ minutes with 13 artifacts. It routes to `/arch-fast` (3 artifacts, 5 minutes).

---

## Current State

**v1 arch system (`P:/.claude/skills/arch/SKILL.md`):**
- Monolithic, runs 13-artifact analysis on EVERY decision
- Problem: Wastes 60+ minutes on trivial decisions
- Result: Tool feels heavyweight; users avoid it for small decisions

---

## Requirements

### Functional Requirements

**FR-1: Complexity Measurement Router**
- System must measure decision complexity in <2 seconds
- Classify into: TRIVIAL (0-20), SIMPLE (20-40), MODERATE (40-70), COMPLEX (70-100)
- Route to appropriate skill path based on complexity
- Display recommendation with confidence score

**FR-2: Three Skill Personas**
- `/arch-fast` (Code Surgeon): TRIVIAL/SIMPLE decisions, 3-5 artifacts, 5-15 min
- `/arch-deep` (Systems Architect): MODERATE/COMPLEX decisions, 10 artifacts, 40-90 min
- `/arch-precedent` (Historian): COMPLEX + precedent-setting, 13 artifacts + ADR/docs option, 90+ min

**FR-3: Manual Override**
- User can force any path regardless of complexity measurement
- No penalty for overriding
- System displays all override options

**FR-4: Backward Compatibility**
- Existing v1 skill preserved as `/arch-v1`
- Zero breaking changes
- v1 remains accessible for users who prefer monolithic analysis

**FR-5: Lib Module Naming**
- New lib files use migration doc versions with different names
- Preserve existing `complexity_measure.py`, `artifact_selector.py`
- New files: `complexity_measure_v2.py`, `artifact_selector_v2.py`

### Non-Functional Requirements

**NFR-1: Performance**
- Router completes in <3 seconds
- Complexity measurement <2 seconds
- Fast path output <5 KB, <5 minutes

**NFR-2: Reliability**
- Confidence scoring 80%+ accuracy
- No false positives on complexity classification
- Graceful fallback if lib modules fail

**NFR-3: Maintainability**
- Clean separation: router → personas → lib modules
- Each skill independently testable
- Phase 1 MVP complete without Phases 2-4

---

## User Stories

### US-1: Quick Decision Routing
**As a** developer
**I want** trivial decisions to get quick analysis
**So that** I don't waste 60 minutes on "swap two checks"

**Acceptance:**
- `/arch "should I swap two checks?"` → TRIVIAL detected → recommends `/arch-fast`
- `/arch-fast` completes in <5 minutes with 1-2 KB output

### US-2: Manual Override Freedom
**As a** developer
**I want** to force deep analysis even when system says trivial
**So that** I can trust my own judgment about code complexity

**Acceptance:**
- `/arch-deep "trivial query"` runs full analysis without complaint
- System displays override options after every routing

### US-3: Backward Compatibility
**As a** developer
**I want** v1 monolithic analysis still available
**So that** existing workflows aren't broken

**Acceptance:**
- `/arch-v1` works exactly as before
- All 13 artifacts, same behavior
- Triggered via `/arch-v1` or `/arch-legacy`

### US-4: Proportional Analysis Depth
**As a** developer
**I want** complex decisions to get full analysis
**So that** high-stakes changes get proper scrutiny

**Acceptance:**
- `/arch "redesign schema"` → COMPLEX detected → recommends `/arch-deep`
- Hints at `/arch-precedent` for precedent-setting decisions
- Deep analysis runs 40-90 minutes with 10+ artifacts

---

## Implementation Phases

### Phase 1: Core Router (6-8 hrs) - MVP
**Files:**
1. `P:/__csf/src/lib/complexity_measure_v2.py` - Linguistic/structural/risk scoring (0-100)
2. `P:/__csf/src/lib/artifact_selector_v2.py` - Routing logic, path metadata
3. `P:/.claude/skills/arch/arch.md` - NEW router entry point
4. `P:/.claude/skills/arch/arch-fast.md` - Code Surgeon persona
5. `P:/.claude/skills/arch/arch-deep.md` - Systems Architect persona
6. `P:/.claude/skills/arch/arch-precedent.md` - Historian persona
7. `P:/.claude/skills/arch/arch-v1.md` - Renamed from SKILL.md (preserved)

**Deliverable:** Working router + 3 personas, v1 preserved, zero breaking changes

### Phase 2: Knowledge Integration (8-10 hrs)
**Files:**
8. `mentalmodelselector.py` - RCA frameworks
9. `ckssemanticsearch.py` - Pattern history
10. `adrindexlookup.py` - Past decisions
11. `constitutionalcontext.py` - Solo-dev constraints
12. `dependencyscanning.py` - Coupling map

### Phase 3: Enhancement Modes (6-8 hrs)
**File:**
13. `enhancementrouter.py` - Modes: --zen, --deep, --debate, --challenge

### Phase 4: Stack-Specific Analysts (6-8 hrs)
**Files:**
14. `stackdetector.py` - Detect framework
15. `arch-python.md` - Async/GIL/type hints
16. `arch-data-pipeline.md` - ETL/backpressure
17. `arch-cli.md` - POSIX/exit codes

---

## Success Criteria

- [ ] Router measures complexity in <2 seconds
- [ ] TRIVIAL decisions route to FAST (5 min, 1-2 KB)
- [ ] COMPLEX decisions route to DEEP (40-90 min, 8-30 KB)
- [ ] Manual overrides work without complaint
- [ ] `/arch-v1` still works (backward compatible)
- [ ] All 4 phases implemented
- [ ] Lib files use `_v2` suffix (preserve existing)
- [ ] Testing demonstrates 12× speedup on trivial decisions

---

## Migration Strategy

**Step 1: Rename v1**
- `P:/.claude/skills/arch/SKILL.md` → `arch-v1.md`
- Update triggers: `arch-v1`, `arch-legacy`

**Step 2: Add lib modules (_v2 suffix)**
- `complexity_measure_v2.py` (preserve existing)
- `artifact_selector_v2.py` (preserve existing)

**Step 3: Create new skills**
- `arch.md` (router)
- `arch-fast.md`, `arch-deep.md`, `arch-precedent.md`

**Step 4: Test**
- Verify router classification accuracy
- Verify manual overrides
- Verify backward compatibility

---

## Out of Scope

- Removing v1 monolithic (preserved, not deleted)
- Modifying existing `complexity_measure.py`, `artifact_selector.py`
- Breaking changes to existing workflows
- External dependencies beyond current lib structure
