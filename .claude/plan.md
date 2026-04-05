# TASK-006: Synergy Detection Implementation

## Overview

Implement synergy detection for cognitive frameworks and reasoning modes to identify complementary combinations that enhance each other's effectiveness.

## Architecture

### Component: Synergy Detector

**File**: `P:/.claude/hooks/UserPromptSubmit_modules/synergy_detector.py` (NEW)

**Purpose**: Detect when cognitive framework + reasoning mode combinations create synergistic effects greater than their individual contributions.

### Synergy Matrix

Define framework × mode compatibility matrix with synergy scores:

| Framework | Mode | Synergy Score | Rationale |
|-----------|------|---------------|-----------|
| `assumption_surfacing` | `sequential` | 0.9 | Surface assumptions before step-by-step reasoning prevents blind spots |
| `socratic_decomposition` | `multi_agent` | 0.85 | Decompose for multiple perspectives enables richer debate |
| `inversion_prompting` | `two_stage` | 0.8 | Pre-mortem in reasoning phase catches flaws early |
| `first_principles` | `multi_agent` | 0.75 | Different foundational assumptions revealed through debate |
| `assumption_surfacing` | `multi_agent` | 0.7 | Make implicit assumptions explicit for group discussion |
| `devil_advocate` | `sequential` | 0.65 | Challenge assumptions before committing to reasoning path |
| `socratic_decomposition` | `sequential` | 0.6 | Question decomposition aligns with step-by-step process |

**Scoring**:
- 0.9-1.0: Exceptional synergy (strongly prefer combination)
- 0.7-0.9: High synergy (prefer combination)
- 0.5-0.7: Moderate synergy (neutral preference)
- <0.5: Low synergy (no special handling)

### Data Structures

```python
from dataclasses import dataclass
from typing import dict

@dataclass(frozen=True)
class SynergyRule:
    """Single-source definition for a framework+mode synergy."""
    framework: str
    mode: str
    score: float
    rationale: str

@dataclass
class SynergyMatch:
    """Detected synergies from prompt analysis."""
    synergies: list[dict]  # Each: {framework, mode, score, rationale}
    top_synergies: list[dict]  # Top 3 by score
    total_score: float  # Sum of all synergy scores
```

### Detection Flow

```
Unified Detection Result (from T-001)
    ↓
Extract matched_frameworks and matched_modes
    ↓
Lookup synergy matrix for all combinations
    ↓
Score and rank synergies (descending by score)
    ↓
Return top 3 synergies with rationale
```

## Error Handling

**Missing config**: Use hardcoded default matrix (graceful degradation)
**Invalid score**: Clamp to [0.0, 1.0] range
**No matches detected**: Return empty SynergyMatch (not an error)

## Test Strategy

### Unit Tests
1. **Synergy matrix validation**
   - All scores in [0.0, 1.0] range
   - All frameworks/modes exist in matrix
   - No duplicate entries

2. **Detection logic**
   - Single framework+mode match returns correct synergy
   - Multiple matches return top 3 sorted correctly
   - No matches returns empty result

3. **Performance**
   - Detection <5ms for typical input (1000 chars)
   - Matrix lookup is O(1) per combination

4. **Edge cases**
   - Empty framework list → no synergies
   - Empty mode list → no synergies
   - Unknown framework/mode → skip gracefully

### Integration Tests
1. **Router integration**
   - synergy_detector called from UserPromptSubmit_router.py
   - SynergyMatch added to additionalContext
   - Tag emission: `[SYNERGY: framework+mode (score)]`

## Standards Compliance

**Python Standards** (`//p`):
- Type hints for all function signatures
- Frozen dataclasses for immutable config
- f-strings for string formatting
- Docstrings for all public functions
- ruff linting (apply auto-fix)

**Performance Standards**:
- Single-pass matrix lookup (no nested loops)
- Pre-compiled patterns at module load time
- Cache synergy matrix as module-level constant

**Integration Standards**:
- Returns SynergyMatch dataclass (not dict)
- Compatible with unified_detection.UnifiedDetectionResult
- Tag format: `[SYNERGY: assumption_surfacing+sequential (0.9)]`

## Ramifications

**Impact on existing code**:
- **Breaking changes**: None (new module)
- **Performance**: <5ms overhead per request
- **Memory**: ~500 bytes for synergy matrix (negligible)
- **Dependencies**: Requires unified_detection from T-001

**Integration points**:
- T-009: conflict_arbiter.py will use synergy scores to override fast mode cap
- T-011: UserPromptSubmit_router.py will add [SYNERGY] tags

**Migration considerations**:
- None (new feature, no migration needed)

## Pre-Mortem Analysis

**Failure Mode 1: Synergy scores are subjective and arbitrary**
- **Root Cause**: No empirical validation of framework+mode combinations
- **Prevention**: Document rationale for each score, allow config file overrides
- **Test**: User study to validate scores against actual performance
- **Observability**: Log synergy detections, monitor user feedback

**Failure Mode 2: Matrix becomes outdated as frameworks/modes change**
- **Root Cause**: Hardcoded matrix doesn't evolve with system
- **Prevention**: Load matrix from config file (cognitive_frameworks_config.json)
- **Test**: Config loading fallback to hardcoded defaults
- **Observability**: Monitor for unknown framework/mode warnings

**Failure Mode 3: False synergies waste tokens**
- **Root Cause**: Low-score synergies (<0.5) still emit tags
- **Prevention**: Only report top 3 synergies with score >=0.5
- **Test**: Verify threshold enforcement in tests
- **Observability**: Track synergy tag frequency in logs

**Failure Mode 4: Performance degradation with large matrices**
- **Root Cause**: O(n×m) lookup for n frameworks × m modes
- **Prevention**: Pre-compute matrix at load time, O(1) lookup via dict
- **Test**: Benchmark with 10 frameworks × 4 modes
- **Observability**: Performance monitoring in unified_detection

## Execution Plan

### Task 1: Create synergy_detector.py module (45 min)
1. Create file with dataclass definitions
2. Define default synergy matrix (7 rules)
3. Implement detect_synergies() function
4. Add type hints and docstrings
5. Apply ruff linting

### Task 2: Create unit tests (45 min)
1. Create tests/test_synergy_detector.py
2. Test synergy matrix validation
3. Test detection logic (single/multiple/no matches)
4. Test performance baseline (<5ms)
5. Test edge cases

### Task 3: Integration testing (30 min)
1. Verify router integration
2. Check tag emission format
3. Test with unified_detection output
4. Verify graceful degradation

### Task 4: Documentation (15 min)
1. Update cognitive_frameworks_config.json with synergy_matrix section
2. Document synergy rules in CLAUDE.md
3. Add examples of synergy detection
4. Update task-006 completion summary

## Success Criteria

- [ ] synergy_detector.py created with all 7 synergy rules
- [ ] Unit tests pass (100% coverage)
- [ ] Performance <5ms for typical input
- [ ] Integration with unified_detection working
- [ ] Top 3 synergies reported correctly
- [ ] Documentation updated
- [ ] Git commit with all changes
- [ ] TASK-006 marked complete
