# Architecture Decision: Cognitive Reasoning Cross-Category Triggers

**Date:** 2025-03-14
**Template:** fast
**Query:** what organization will provide us optimal outcomes if we allowed modes to work across different triggers?

---

## Decision Statement

Reorganizing the three-layer cognitive reasoning system (frameworks/modes/profiles) to allow cross-category triggers via a compatibility matrix, preserving semantic clarity while enabling valuable cross-pollination between reasoning modes, think profiles, and cognitive frameworks.

---

## Options

### Option A: Flat single-category organization

**Pro:** Simpler mental model - everything is a "cognitive pattern"

**Pro:** Cross-pollination automatic - any pattern can trigger any enhancement

**Pro:** Easier to extend - just add new patterns to one list

**Con:** Lose semantic distinctions between "how we think" (mode) vs "what problem we're solving" (profile) vs "what cognitive pattern to apply" (framework)

**Con:** 252 possible combinations become one flat list - harder to reason about system behavior

**Differs on:** Semantic clarity vs combinatorial flexibility

---

### Option B: Current three-layer separation

**Pro:** Clear semantic boundaries (structure/approach/pattern)

**Pro:** Compositional - 4 × 7 × 9 = 252 combinations available

**Pro:** Intent-based routing - implementation vs diagnostic gets different layers

**Con:** More complex to understand and maintain

**Con:** Misses cross-category synergies (e.g., "debug_rca" profile could benefit from "multi_agent" mode but currently isolated)

**Differs on:** Semantic organization vs combinatorial coverage

---

### Option C: Matrix-based organization (RECOMMENDED)

**Pro:** Best of both - keep semantic categories but enable cross-triggers

**Pro:** Explicit compatibility matrix defines which layer combinations make sense

**Pro:** Can add "wildcard" patterns that trigger across categories

**Con:** More complex data structure (3D matrix: layer × pattern × compatibility)

**Con:** Requires manual curation of compatibility matrix

**Differs on:** Rich composition vs maintenance overhead

---

## Recommendation

**Option C** - Matrix-based organization with compatibility rules.

**Why:**
- Preserves semantic clarity (you still know WHAT type of thinking each pattern represents)
- Enables cross-pollination where valuable (debug_rca + multi_agent makes sense)
- Maintains performance (single-pass detection unchanged, just smarter routing)
- Extensible (can add new compatibility rules without breaking existing behavior)

**Key insight:** Current `unified_detection.py` (P:\.claude\hooks\UserPromptSubmit_modules\unified_detection.py lines 30-51) already returns all three lists (`matched_frameworks`, `matched_modes`, `matched_profiles`). Option C adds a **compatibility layer** that says "when X, Y, and Z patterns all match, apply enhancement W" - this enables the cross-category synergies you're asking about.

---

## Implementation

**Current code** (`unified_detection.py` lines 30-51):
```python
@dataclass(frozen=True)
class UnifiedDetectionResult:
    matched_frameworks: list[str] = field(default_factory=list)
    matched_modes: list[str] = field(default_factory=list)
    matched_profiles: list[str] = field(default_factory=list)
```

**Proposed change** - Add compatibility matrix:

```python
# New: Compatibility matrix for cross-category triggers
_COMPATIBILITY_MATRIX: dict[tuple[str, str, str], str] = {
    # (framework, mode, profile) -> enhancement_to_apply
    ("assumption_surfacing", "multi_agent", "debug_rca"): "parallel_assumption_checking",
    ("socratic_decomposition", "graph", "architecture"): "branching_decomposition",
    # Add more as discovered
}

# Extend UnifiedDetectionResult
@dataclass(frozen=True)
class UnifiedDetectionResult:
    matched_frameworks: list[str]
    matched_modes: list[str]
    matched_profiles: list[str]
    compatible_combinations: list[str] = field(default_factory=list)  # NEW
```

**Router logic** (in each hook):
```python
# Check for compatible combinations first
for (framework, mode, profile), enhancement in _COMPATIBILITY_MATRIX.items():
    if (framework in result.matched_frameworks and
        mode in result.matched_modes and
        profile in result.matched_profiles):
        # Apply combined enhancement instead of separate ones
        result.compatible_combinations.append(enhancement)
```

**Rollback:** Remove `compatible_combinations` field, revert to independent hook execution.

---

## Quick Ramifications

- **Break anything?** No - backward compatible. Existing behavior unchanged unless compatibility matrix entries added.
- **Edge cases:** Conflicting combinations (multiple matches) - precedence rule: compatibility matrix takes priority over individual hooks.
- **Constraints:** Performance - matrix lookup is O(1), negligible overhead to current single-pass detection.

---

## Confidence

**Confidence: 75%** — Codebase analysis shows current architecture is well-structured with clean separation (`unified_detection.py` lines 1-100). Compatibility matrix extends this without breaking changes. Uncertainty: no production data on which cross-category combinations are actually valuable.

---

## Adversarial Self-Review

**Weakest assumption:** Compatibility matrix can be manually curated effectively. If wrong: Matrix becomes unmaintainable burden, sparse coverage makes feature worthless. **Mitigation:** Start with 3-5 high-value combinations (based on CKS failure patterns), measure usage, expand only when proven.
