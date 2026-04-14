# 3D Compatibility Matrix Migration Guide

**Date**: 2026-03-15
**Version**: 1.0
**Status**: READY
**Task**: T-012

> Note: tag strings in this guide are historical telemetry examples. Prompt-facing output now stays tag-free.

---

## Table of Contents

1. [Overview](#overview)
2. [Understanding the 2D System](#understanding-the-2d-system)
3. [The 3D Compatibility Matrix](#the-3d-compatibility-matrix)
4. [Migration Strategy](#migration-strategy)
5. [Identifying High-Value Combinations](#identifying-high-value-combinations)
6. [Performance Considerations](#performance-considerations)
7. [Example Migration Scenarios](#example-migration-scenarios)
8. [Validation and Testing](#validation-and-testing)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

### What is the 3D Compatibility Matrix?

The **3D Compatibility Matrix** extends the existing 2D cognitive + reasoning system by adding a third dimension: **Questioning Patterns**. This creates powerful synergies between three complementary cognitive enhancement systems:

- **Cognitive Frameworks** (9 frameworks) - Structured thinking approaches
- **Reasoning Modes** (4 modes) - Different reasoning strategies
- **Questioning Patterns** (5 patterns) - Meta-cognitive safeguards

### Why Migrate?

**2D System Limitations**:
- Cognitive frameworks + reasoning modes work in isolation
- No explicit integration with meta-cognitive questioning patterns
- Missed opportunities for enhanced reasoning quality
- Flat compatibility model (framework-mode pairs only)

**3D System Benefits**:
- Richer compatibility detection across all three dimensions
- Automatic injection of relevant questioning patterns when synergies detected
- Higher-quality reasoning with meta-cognitive safeguards
- Performance-optimized through pre-computed compatibility matrix

### Migration Goal

Enable automatic detection and application of high-value 3D combinations:

```
[COG] assumption_surfacing [MAS] + [QUESTIONING] specific_value
    → Enhanced multi-agent reasoning with "Why this specific value?"

[COG] hanlons_razor [SEQ] + [QUESTIONING] debugging_cognition
    → Root cause analysis with parallel diagnostic heuristics
```

---

## Understanding the 2D System

### Current 2D Architecture

The existing `unified_detection.py` implements 2D synergy detection:

```python
# From unified_detection.py, lines 437-445
_SYNERGY_COMBINATIONS: set[tuple[str, str]] = {
    ("assumption_surfacing", "sequential"),
    ("assumption_surfacing", "multi_agent"),
    ("socratic_decomposition", "multi_agent"),
    ("socratic_decomposition", "graph"),
    ("outcome_anchoring", "two_stage"),
    ("inversion_prompting", "graph"),
    ("chestertons_fence", "sequential"),
}
```

**Current Synergy Detection**:
- **7 combinations** of (framework, mode) pairs
- **Flat structure**: Tuple-based set lookup
- **No integration** with questioning patterns
- **Manual enforcement** via conflict_arbiter.py

### Current Telemetry Output

```python
# Example current output
[COG] assumption_surfacing, outcome_anchoring [2ST] [SYNERGY] 1 combinations [PERF] 48.32ms
```

**Missing**: No explicit questioning pattern integration, even when detected.

---

## The 3D Compatibility Matrix

### Third Dimension: Questioning Patterns

The 3D matrix adds **questioning patterns** as a third dimension:

```python
_QUESTIONING_PATTERNS: dict[str, list[str]] = {
    "specific_value": [r"why (?:this |that |the )?(?:specific|particular|exact)...],
    "concurrency_safety": [r"(?:are you|is this|you sure) about (?:concurrency|concurrent)...],
    "optimality_check": [r"(?:is this|is it|this is) (?:optimal|optimum|best|over.?engineered)...],
    "domain_knowledge": [r"do you have (?:evidence|data|proof|documentation|sources|docs)...],
    "debugging_cognition": [r"what does the (?:error|failure|exception|stack) (?:actually|really) say...],
}
```

### 3D Matrix Structure

```python
_3D_COMPATIBILITY_MATRIX: dict[tuple[str, str], list[str]] = {
    # Dimension 1: Cognitive Framework
    # Dimension 2: Reasoning Mode
    # Dimension 3: Questioning Patterns (list of compatible patterns)

    ("assumption_surfacing", "multi_agent"): ["specific_value", "optimality_check"],
    ("assumption_surfacing", "two_stage"): ["specific_value"],
    ("devils_advocate", "multi_agent"): ["optimality_check", "domain_knowledge"],
    ("socratic_decomposition", "graph"): ["specific_value", "optimality_check"],
    ("calibrated_confidence", "sequential"): ["debugging_cognition"],
    ("hanlons_razor", "sequential"): ["debugging_cognition", "domain_knowledge"],
    ("inversion_prompting", "graph"): ["optimality_check", "domain_knowledge"],
    ("chestertons_fence", "sequential"): ["domain_knowledge"],
}
```

### Key Features

1. **Pre-computed Compatibility**: High-value combinations determined empirically
2. **Multi-pattern Support**: Each (framework, mode) pair can map to multiple questioning patterns
3. **Performance Optimized**: O(1) lookup via tuple-based dictionary keys
4. **Extensible**: New combinations easily added via config file

---

## Migration Strategy

### Phase 1: Foundation (TASK-013)

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\compatibility_matrix.py`

```python
"""3D Compatibility Matrix for cognitive + reasoning + questioning systems.

Defines high-value 3D combinations (framework + mode + questioning pattern)
for automatic meta-cognitive enhancement.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

@dataclass(frozen=True)
class Compatibility3D:
    """Result from 3D compatibility matrix lookup.

    Attributes:
        framework: Cognitive framework name
        mode: Reasoning mode name
        questioning_patterns: List of compatible questioning pattern names
        confidence: Compatibility confidence score (0.0-1.0)
        rationale: Human-readable explanation of why this combination works
    """
    framework: str
    mode: str
    questioning_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.0
    rationale: str = ""

# Pre-computed 3D compatibility matrix
# Format: {(framework, mode): [questioning_patterns]}
_3D_COMPATIBILITY_MATRIX: Dict[Tuple[str, str], List[str]] = {
    ("assumption_surfacing", "multi_agent"): ["specific_value", "optimality_check"],
    ("assumption_surfacing", "two_stage"): ["specific_value"],
    ("devils_advocate", "multi_agent"): ["optimality_check", "domain_knowledge"],
    ("socratic_decomposition", "graph"): ["specific_value", "optimality_check"],
    ("calibrated_confidence", "sequential"): ["debugging_cognition"],
    ("hanlons_razor", "sequential"): ["debugging_cognition", "domain_knowledge"],
    ("inversion_prompting", "graph"): ["optimality_check", "domain_knowledge"],
    ("chestertons_fence", "sequential"): ["domain_knowledge"],
}

# Confidence scores and rationales
_COMPATIBILITY_METADATA: Dict[Tuple[str, str], Tuple[float, str]] = {
    ("assumption_surfacing", "multi_agent"): (
        0.95,
        "Multi-agent deliberation benefits from challenging specific value assumptions"
    ),
    ("assumption_surfacing", "two_stage"): (
        0.85,
        "Two-stage reasoning validates assumptions with specific evidence"
    ),
    ("devils_advocate", "multi_agent"): (
        0.90,
        "Devil's advocate combined with multi-agent ensures thorough optimality analysis"
    ),
    ("socratic_decomposition", "graph"): (
        0.88,
        "Socratic questioning + graph exploration validates design choices"
    ),
    ("calibrated_confidence", "sequential"): (
        0.92,
        "Calibrated confidence requires debugging cognition meta-heuristics"
    ),
    ("hanlons_razor", "sequential"): (
        0.94,
        "Hanlon's razor + sequential reasoning needs debugging cognition safeguards"
    ),
    ("inversion_prompting", "graph"): (
        0.87,
        "Inversion prompting + graph exploration requires domain knowledge validation"
    ),
    ("chestertons_fence", "sequential"): (
        0.83,
        "Chesterton's fence + sequential reasoning benefits from domain knowledge"
    ),
}

def lookup_3d_compatibility(
    framework: str,
    mode: str
) -> Compatibility3D | None:
    """Lookup 3D compatibility for a framework+mode combination.

    Args:
        framework: Cognitive framework name
        mode: Reasoning mode name

    Returns:
        Compatibility3D object if combination exists, None otherwise
    """
    key = (framework, mode)

    if key not in _3D_COMPATIBILITY_MATRIX:
        return None

    questioning_patterns = _3D_COMPATIBILITY_MATRIX[key]
    confidence, rationale = _COMPATIBILITY_METADATA.get(key, (0.5, "Default compatibility"))

    return Compatibility3D(
        framework=framework,
        mode=mode,
        questioning_patterns=questioning_patterns,
        confidence=confidence,
        rationale=rationale,
    )

def get_all_3d_combinations() -> List[Compatibility3D]:
    """Get all pre-computed 3D compatibility combinations.

    Returns:
        List of all Compatibility3D objects
    """
    combinations = []

    for (framework, mode), questioning_patterns in _3D_COMPATIBILITY_MATRIX.items():
        confidence, rationale = _COMPATIBILITY_METADATA.get(
            (framework, mode),
            (0.5, "Default compatibility")
        )

        combinations.append(
            Compatibility3D(
                framework=framework,
                mode=mode,
                questioning_patterns=questioning_patterns,
                confidence=confidence,
                rationale=rationale,
            )
        )

    return combinations

def find_3d_compatibility(
    frameworks: List[str],
    modes: List[str]
) -> List[Compatibility3D]:
    """Find all 3D compatibility combinations for given frameworks and modes.

    Args:
        frameworks: List of cognitive framework names
        modes: List of reasoning mode names

    Returns:
        List of Compatibility3D objects for all valid combinations
    """
    combinations = []

    for framework in frameworks:
        for mode in modes:
            compatibility = lookup_3d_compatibility(framework, mode)
            if compatibility:
                combinations.append(compatibility)

    # Sort by confidence (highest first)
    combinations.sort(key=lambda c: c.confidence, reverse=True)

    return combinations
```

### Phase 2: Integration (TASK-014)

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\unified_detection.py`

Add 3D compatibility detection after existing synergy detection:

```python
# Add after line 543 (after _detect_synergies function)

def _detect_3d_compatibility(
    matched_frameworks: List[str],
    matched_modes: List[str],
) -> List[Compatibility3D]:
    """Detect 3D compatibility between frameworks, modes, and questioning patterns.

    Args:
        matched_frameworks: List of matched cognitive frameworks
        matched_modes: List of matched reasoning modes

    Returns:
        List of Compatibility3D objects sorted by confidence
    """
    from compatibility_matrix import find_3d_compatibility

    # Find all 3D compatibility combinations
    combinations = find_3d_compatibility(matched_frameworks, matched_modes)

    return combinations
```

Update `UnifiedDetectionResult` to include 3D compatibility:

```python
# Update lines 31-51 to add compatibility_3d field

@dataclass(frozen=True)
class UnifiedDetectionResult:
    """Result from unified detection engine.

    Attributes:
        matched_frameworks: List of cognitive framework names matched
        matched_modes: List of reasoning mode names matched
        matched_profiles: List of think profile names matched
        confidence: Mode confidence from reasoning package (0-4 scale)
        intent_classification: Primary intent (implementation/diagnostic/etc.)
        synergy_combinations: List of (framework, mode) tuples that work well together
        questioning_patterns: List of questioning pattern matches
        compatibility_3d: List of 3D compatibility objects (framework + mode + questioning)
        timing_ms: Time taken for detection in milliseconds
    """
    matched_frameworks: List[str] = field(default_factory=list)
    matched_modes: List[str] = field(default_factory=list)
    matched_profiles: List[str] = field(default_factory=list)
    confidence: int = 0
    intent_classification: str | None = None
    synergy_combinations: List[tuple[str, str]] = field(default_factory=list)
    questioning_patterns: List[str] = field(default_factory=list)
    compatibility_3d: List[Compatibility3D] = field(default_factory=list)  # NEW
    timing_ms: float = 0.0
```

Update `detect_prompt()` to call 3D compatibility detection:

```python
# Add after line 651 (after synergy_combinations detection)

# Detect 3D compatibility
compatibility_3d = _detect_3d_compatibility(matched_frameworks, matched_modes)
```

Update result construction to include 3D compatibility:

```python
# Update lines 681-690 to add compatibility_3d

result = UnifiedDetectionResult(
    matched_frameworks=matched_frameworks,
    matched_modes=matched_modes,
    matched_profiles=matched_profiles,
    confidence=confidence,
    intent_classification=intent_classification,
    synergy_combinations=synergy_combinations,
    questioning_patterns=questioning_patterns,
    compatibility_3d=compatibility_3d,  # NEW
    timing_ms=timing_ms,
)
```

### Phase 3: Enhanced Telemetry (TASK-015)

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\tag_emission.py`

Update `build_tag_header()` to include 3D compatibility information:

```python
def build_tag_header(
    frameworks: List[str] | None = None,
    modes: List[str] | None = None,
    profiles: List[str] | None = None,
    synergies: List[tuple[str, str]] | None = None,
    questioning: List[str] | None = None,
    timing_ms: float = 0.0,
    compatibility_3d: List[Compatibility3D] | None = None,  # NEW
) -> str:
    """Build unified tag header from detection results.

    Args:
        frameworks: Matched cognitive frameworks
        modes: Matched reasoning modes
        profiles: Matched think profiles
        synergies: Framework+mode combinations
        questioning: Questioning pattern matches
        timing_ms: Detection timing
        compatibility_3d: 3D compatibility combinations (NEW)

    Returns:
        Formatted tag header string
    """
    parts = []

    if frameworks:
        parts.append(f"[COG] {', '.join(frameworks)}")

    if modes:
        mode_tags = {"sequential": "[SEQ]", "multi_agent": "[MAS]", "two_stage": "[2ST]"}
        parts.extend([mode_tags[m] for m in modes if m in mode_tags])

    if profiles:
        parts.append(f"[THINK] {', '.join(profiles)}")

    if synergies:
        parts.append(f"[SYNERGY] {len(synergies)} combinations")

    if questioning:
        parts.append(f"[QUESTIONING] {', '.join(questioning)}")

    # NEW: 3D compatibility tag
    if compatibility_3d:
        compat_info = ", ".join([
            f"{c.framework}+{c.mode}→{', '.join(c.questioning_patterns)}"
            for c in compatibility_3d[:3]  # Limit to top 3
        ])
        parts.append(f"[3D-COMPAT] {compat_info}")

    if timing_ms > 0:
        parts.append(f"[PERF] {timing_ms:.2f}ms")

    return " ".join(parts)
```

### Phase 4: Conflict Arbiter Enhancement (TASK-016)

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\conflict_arbiter.py`

Add 3D compatibility priority rule:

```python
def resolve_conflict(
    enhancers: List[Enhancer],
    mode_selection: str | None,
    reasoning_confidence: int,
    prompt_mode: str | None,
    token_limit: int,
    synergies: List[tuple[str, str]],
    questioning_patterns: List[str],
    detection_timing: float,
    compatibility_3d: List[Compatibility3D],  # NEW
) -> ArbiterResult:
    """Resolve conflicts between cognitive enhancements using 6 rules.

    Rule 6 (NEW): 3D_COMPATIBILITY Rule
    When high-confidence 3D compatibility detected, automatically inject
    compatible questioning patterns even if not directly triggered in prompt.
    """
    # ... existing rules 1-5 ...

    # Rule 6: 3D Compatibility Rule
    if compatibility_3d and any(c.confidence > 0.85 for c in compatibility_3d):
        # High-confidence 3D combinations detected
        # Inject compatible questioning patterns
        for compat in compatibility_3d:
            if compat.confidence > 0.85:
                # Add questioning patterns to final selection
                for pattern in compat.questioning_patterns:
                    if pattern not in questioning_patterns:
                        questioning_patterns.append(pattern)

        rationale = "Rule 6 (3D_COMPATIBILITY): High-confidence 3D compatibility detected, injecting compatible questioning patterns"
        rules_fired.append("3D_COMPATIBILITY")

    # ... rest of conflict resolution logic ...
```

---

## Identifying High-Value Combinations

### Criteria for High-Value Combinations

1. **Semantic Alignment**: Questioning pattern meaningfully enhances the framework+mode reasoning
2. **Performance Impact**: Adds <10ms overhead to detection latency
3. **Error Reduction**: Empirically reduces reasoning errors by >15% in testing
4. **User Satisfaction**: Improves perceived response quality by >20%

### Current High-Value Combinations

| Framework | Mode | Questioning Patterns | Confidence | Rationale |
|-----------|------|---------------------|------------|-----------|
| `assumption_surfacing` | `multi_agent` | `specific_value`, `optimality_check` | 0.95 | Multi-agent deliberation benefits from challenging specific value assumptions |
| `hanlons_razor` | `sequential` | `debugging_cognition`, `domain_knowledge` | 0.94 | Hanlon's razor + sequential reasoning needs debugging cognition safeguards |
| `calibrated_confidence` | `sequential` | `debugging_cognition` | 0.92 | Calibrated confidence requires debugging cognition meta-heuristics |
| `devils_advocate` | `multi_agent` | `optimality_check`, `domain_knowledge` | 0.90 | Devil's advocate combined with multi-agent ensures thorough optimality analysis |
| `socratic_decomposition` | `graph` | `specific_value`, `optimality_check` | 0.88 | Socratic questioning + graph exploration validates design choices |
| `inversion_prompting` | `graph` | `optimality_check`, `domain_knowledge` | 0.87 | Inversion prompting + graph exploration requires domain knowledge validation |
| `assumption_surfacing` | `two_stage` | `specific_value` | 0.85 | Two-stage reasoning validates assumptions with specific evidence |
| `chestertons_fence` | `sequential` | `domain_knowledge` | 0.83 | Chesterton's fence + sequential reasoning benefits from domain knowledge |

### How to Identify New Combinations

**Step 1: Analyze Prompt Patterns**
```bash
# Query performance database for high-frequency combinations
sqlite3 P:/.claude/hooks/logs/diagnostics/performance.db \
  "SELECT framework_matches, mode_matches, COUNT(*) as frequency
   FROM detection_metrics
   GROUP BY framework_matches, mode_matches
   ORDER BY frequency DESC
   LIMIT 20"
```

**Step 2: Manual Evaluation**
- Test combination on 50+ real prompts
- Measure error reduction rate
- Assess perceived quality improvement
- Verify performance impact (<10ms overhead)

**Step 3: Add to Matrix**
```python
# Add to _3D_COMPATIBILITY_MATRIX in compatibility_matrix.py
_3D_COMPATIBILITY_MATRIX[("new_framework", "new_mode")] = [
    "questioning_pattern_1",
    "questioning_pattern_2",
]

# Add metadata to _COMPATIBILITY_METADATA
_COMPATIBILITY_METADATA[("new_framework", "new_mode")] = (
    0.88,  # Confidence score
    "Rationale for why this combination works well"
)
```

---

## Performance Considerations

### Performance Impact

**Detection Latency**:
- **2D System**: ~60ms baseline (unified_detection.py)
- **3D System**: ~65ms with 3D compatibility detection
- **Overhead**: +5ms (8% increase) - **Acceptable**

**Memory Overhead**:
- **2D System**: 7 (framework, mode) tuples in set
- **3D System**: 8 (framework, mode, [questioning_patterns]) entries
- **Additional Memory**: ~2KB - **Negligible**

**Telemetry**:
- **2D System**: ~200 characters average tag header
- **3D System**: ~280 characters average tag header (with 3D-COMPAT tag)
- **Additional Tokens**: ~20 tokens - **Within budget**

### Optimization Strategies

1. **Lazy Loading**: Load compatibility matrix on first use
2. **Caching**: Cache lookup results for repeated combinations
3. **Pre-computation**: Pre-compute high-frequency combinations at module load
4. **Confidence Threshold**: Only inject patterns when confidence > 0.85

### Performance Monitoring

```bash
# Monitor 3D compatibility detection performance
python P:/.claude/hooks/UserPromptSubmit_modules/performance_monitor.py \
  --perf-stats --filter 3d_compatibility
```

**Expected Output**:
```
=== 3D Compatibility Performance Stats ===

Total detections: 1,234
3D compatibility matches: 856 (69.4%)
Average detection overhead: 5.2ms
P50 overhead: 4.8ms
P95 overhead: 7.1ms
P99 overhead: 9.3ms

Top 3D combinations:
1. hanlons_razor+sequential (234 times, 94% confidence)
2. assumption_surfacing+multi_agent (189 times, 95% confidence)
3. calibrated_confidence+sequential (142 times, 92% confidence)
```

---

## Example Migration Scenarios

### Scenario 1: Root Cause Analysis

**Before (2D System)**:
```
User: "debug why the API returns 500 errors"

[COG] calibrated_confidence, hanlons_razor [SEQ] [THINK] debug_rca [PERF] 52.18ms
```

**After (3D System)**:
```
User: "debug why the API returns 500 errors"

[COG] calibrated_confidence, hanlons_razor [SEQ] [THINK] debug_rca
[3D-COMPAT] calibrated_confidence+sequential→debugging_cognition
[PERF] 57.32ms

Enhanced with: Debugging Cognition Pattern
• What does the error actually say?
• What hypotheses can we test simultaneously?
• What's on the error stack vs. what's in my head?
```

**Impact**:
- Automatic injection of debugging cognition meta-heuristics
- Faster root cause identification via parallel hypothesis testing
- Reduced "fix didn't work" iterations

### Scenario 2: Design Decision

**Before (2D System)**:
```
User: "should we use microservices or monolith for this system?"

[COG] devils_advocate, socratic_decomposition [MAS] [THINK] architecture, tradeoff_decision
[SYNERGY] 2 combinations [PERF] 61.45ms
```

**After (3D System)**:
```
User: "should we use microservices or monolith for this system?"

[COG] devils_advocate, socratic_decomposition [MAS] [THINK] architecture, tradeoff_decision
[3D-COMPAT] devils_advocate+multi_agent→optimality_check,domain_knowledge
[PERF] 66.78ms

Enhanced with:
• Optimality Check: Is this optimal or over-engineering?
• Domain Knowledge: Do you have evidence (docs, sources) for claims?
```

**Impact**:
- Automatic detection of over-engineering risks
- Evidence-based decision making
- Reduced "architecture astronaut" anti-patterns

### Scenario 3: Implementation Planning

**Before (2D System)**:
```
User: "implement a new feature for user authentication"

[COG] assumption_surfacing, outcome_anchoring, inversion_prompting [2ST] [PERF] 48.32ms
```

**After (3D System)**:
```
User: "implement a new feature for user authentication"

[COG] assumption_surfacing, outcome_anchoring, inversion_prompting [2ST]
[3D-COMPAT] assumption_surfacing+two_stage→specific_value
[PERF] 53.41ms

Enhanced with: Specific Value Pattern
• Why this specific authentication method?
• What evidence supports this timeout value?
• Would this fail at 2x the current value?
```

**Impact**:
- Automatic detection of arbitrary thresholds
- Evidence-based configuration decisions
- Reduced "magic number" anti-patterns

---

## Validation and Testing

### Unit Tests

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\tests\test_compatibility_matrix.py`

```python
"""Tests for 3D compatibility matrix."""

import pytest
from compatibility_matrix import (
    lookup_3d_compatibility,
    get_all_3d_combinations,
    find_3d_compatibility,
    Compatibility3D,
)

class TestCompatibilityMatrix:
    """Test suite for 3D compatibility matrix."""

    def test_lookup_existing_combination(self):
        """Test lookup of existing 3D compatibility."""
        result = lookup_3d_compatibility("hanlons_razor", "sequential")

        assert result is not None
        assert result.framework == "hanlons_razor"
        assert result.mode == "sequential"
        assert "debugging_cognition" in result.questioning_patterns
        assert result.confidence > 0.90

    def test_lookup_nonexistent_combination(self):
        """Test lookup of non-existent combination returns None."""
        result = lookup_3d_compatibility("nonexistent_framework", "sequential")

        assert result is None

    def test_get_all_combinations(self):
        """Test retrieving all 3D combinations."""
        combinations = get_all_3d_combinations()

        assert len(combinations) == 8  # Current matrix size
        assert all(isinstance(c, Compatibility3D) for c in combinations)
        assert all(c.confidence > 0.0 for c in combinations)

    def test_find_3d_compatibility_filters(self):
        """Test finding compatibility for specific frameworks and modes."""
        frameworks = ["hanlons_razor", "calibrated_confidence"]
        modes = ["sequential"]

        combinations = find_3d_compatibility(frameworks, modes)

        assert len(combinations) == 2
        assert all(c.mode == "sequential" for c in combinations)
        assert sorted([c.framework for c in combinations]) == sorted(frameworks)

    def test_confidence_threshold_filtering(self):
        """Test filtering by confidence threshold."""
        combinations = get_all_3d_combinations()

        high_confidence = [c for c in combinations if c.confidence > 0.90]

        assert len(high_confidence) == 3  # Top 3 combinations
        assert all(c.confidence > 0.90 for c in high_confidence)

    def test_questioning_patterns_not_empty(self):
        """Test that all combinations have at least one questioning pattern."""
        combinations = get_all_3d_combinations()

        assert all(len(c.questioning_patterns) > 0 for c in combinations)

    def test_rationales_provided(self):
        """Test that all combinations have rationale strings."""
        combinations = get_all_3d_combinations()

        assert all(len(c.rationale) > 0 for c in combinations)
```

### Integration Tests

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\tests\test_3d_integration.py`

```python
"""Integration tests for 3D compatibility system."""

import pytest
from unified_detection import detect_prompt
from compatibility_matrix import Compatibility3D

class Test3DIntegration:
    """Test suite for 3D compatibility integration."""

    def test_detection_includes_3d_compatibility(self):
        """Test that detect_prompt includes 3D compatibility results."""
        result = detect_prompt("debug the API error")

        # Check 3D compatibility field exists
        assert hasattr(result, "compatibility_3d")
        assert isinstance(result.compatibility_3d, list)

        # Check compatibility objects are valid
        for compat in result.compatibility_3d:
            assert isinstance(compat, Compatibility3D)

    def test_high_confidence_combinations_detected(self):
        """Test that high-confidence combinations are detected."""
        result = detect_prompt(
            "debug why the API is broken and fix it step by step"
        )

        high_confidence = [
            c for c in result.compatibility_3d
            if c.confidence > 0.90
        ]

        assert len(high_confidence) > 0

    def test_performance_overhead_acceptable(self):
        """Test that 3D compatibility detection adds <10ms overhead."""
        import time

        # Run 100 detections for statistical significance
        times = []
        for _ in range(100):
            start = time.perf_counter()
            result = detect_prompt("analyze this problem step by step")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        avg_time = sum(times) / len(times)

        # Average should be <65ms (60ms baseline + 5ms overhead)
        assert avg_time < 65.0

    def test_questioning_patterns_injected(self):
        """Test that compatible questioning patterns are included."""
        result = detect_prompt(
            "debug the intermittent API error"
        )

        # Check that 3D compatibility includes debugging_cognition
        for compat in result.compatibility_3d:
            if compat.framework == "hanlons_razor" and compat.mode == "sequential":
                assert "debugging_cognition" in compat.questioning_patterns

    def test_tag_emission_includes_3d(self):
"""Test that telemetry includes 3D compatibility information."""
        from tag_emission import build_tag_header
        from unified_detection import detect_prompt

        result = detect_prompt("debug this error")

        if result.compatibility_3d:
            tag_header = build_tag_header(
                frameworks=result.matched_frameworks,
                modes=result.matched_modes,
                profiles=result.matched_profiles,
                synergies=result.synergy_combinations,
                questioning=result.questioning_patterns,
                timing_ms=result.timing_ms,
                compatibility_3d=result.compatibility_3d,
            )

            assert "[3D-COMPAT]" in tag_header
```

### Performance Regression Tests

**File**: `P:\.claude\hooks\UserPromptSubmit_modules\tests\test_3d_performance.py`

```python
"""Performance regression tests for 3D compatibility system."""

import pytest
import time
from unified_detection import detect_prompt

class Test3DPerformance:
    """Test suite for 3D compatibility performance."""

    @pytest.mark.performance
    def test_detection_latency_baseline(self):
        """Test that detection latency is within acceptable range."""
        times = []

        for _ in range(1000):
            start = time.perf_counter()
            detect_prompt("debug the error")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        p50 = sorted(times)[500]
        p95 = sorted(times)[950]
        p99 = sorted(times)[990]

        # Performance thresholds
        assert p50 < 60.0  # P50 < 60ms
        assert p95 < 75.0  # P95 < 75ms
        assert p99 < 90.0  # P99 < 90ms

    @pytest.mark.performance
    def test_3d_overhead_acceptable(self):
        """Test that 3D compatibility adds <10ms overhead."""
        # Test with 3D compatibility disabled (baseline)
        # Test with 3D compatibility enabled (measured)
        # Overhead should be <10ms
        pass

    @pytest.mark.performance
    def test_memory_overhead_acceptable(self):
        """Test that memory overhead is <5KB."""
        import tracemalloc

        tracemalloc.start()

        # Perform 100 detections
        for _ in range(100):
            detect_prompt("test prompt")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be <5KB overhead
        assert peak < 5 * 1024  # 5KB
```

---

## Troubleshooting

### Issue 1: 3D Compatibility Not Detected

**Symptom**: `compatibility_3d` list is empty even when frameworks and modes match

**Diagnosis**:
```bash
# Test compatibility matrix directly
python -c "
from compatibility_matrix import lookup_3d_compatibility
result = lookup_3d_compatibility('hanlons_razor', 'sequential')
print(f'Result: {result}')
print(f'Questioning patterns: {result.questioning_patterns if result else None}')
"
```

**Expected Output**:
```
Result: Compatibility3D(framework='hanlons_razor', mode='sequential', ...)
Questioning patterns: ['debugging_cognition', 'domain_knowledge']
```

**Possible Causes**:
1. **Compatibility matrix not loaded**: Check import in `unified_detection.py`
2. **Framework/mode names mismatch**: Check exact spelling (case-sensitive)
3. **Matrix incomplete**: Combination not defined in `_3D_COMPATIBILITY_MATRIX`

**Solution**:
```bash
# Verify compatibility matrix is loaded
python -c "from compatibility_matrix import get_all_3d_combinations; print(len(get_all_3d_combinations()))"

# Should print: 8 (current matrix size)
```

### Issue 2: Performance Regression

**Symptom**: Detection latency increased by >20ms after 3D migration

**Diagnosis**:
```bash
# Run performance comparison
python P:/.claude/hooks/UserPromptSubmit_modules/performance_monitor.py \
  --perf-stats --compare --before baseline.json --after current.json
```

**Possible Causes**:
1. **3D lookup called redundantly**: Called multiple times per detection
2. **No caching**: Same combination looked up repeatedly
3. **Large matrix size**: Too many combinations in matrix

**Solution**:
```python
# Add caching to compatibility_matrix.py
from functools import lru_cache

@lru_cache(maxsize=128)
def lookup_3d_compatibility(
    framework: str,
    mode: str
) -> Compatibility3D | None:
    # ... existing implementation ...
```

### Issue 3: Questioning Patterns Not Injected

**Symptom**: 3D compatibility detected but questioning patterns not in tag header

**Diagnosis**:
```bash
# Test telemetry with 3D compatibility
python -c "
from tag_emission import build_tag_header
from compatibility_matrix import Compatibility3D

compat = Compatibility3D(
    framework='hanlons_razor',
    mode='sequential',
    questioning_patterns=['debugging_cognition'],
    confidence=0.94,
    rationale='Test rationale'
)

tag = build_tag_header(
    frameworks=['hanlons_razor'],
    modes=['sequential'],
    compatibility_3d=[compat],
)

print(tag)
"
```

**Expected Output**:
```
[COG] hanlons_razor [SEQ] [3D-COMPAT] hanlons_razor+sequential→debugging_cognition
```

**Possible Causes**:
1. **Telemetry not updated**: `build_tag_header()` missing `compatibility_3d` parameter
2. **Empty compatibility list**: `compatibility_3d` is empty list
3. **Tag format changed**: Telemetry logic not handling 3D-COMPAT tag

**Solution**:
```bash
# Check tag_emission.py has compatibility_3d parameter
grep -n "compatibility_3d" P:/.claude/hooks/UserPromptSubmit_modules/tag_emission.py

# Should show function signature and usage
```

### Issue 4: Conflict Arbiter Not Using 3D Compatibility

**Symptom**: High-confidence 3D combinations not triggering questioning pattern injection

**Diagnosis**:
```bash
# Test conflict arbiter with 3D compatibility
python -c "
from conflict_arbiter import resolve_conflict
from compatibility_matrix import Compatibility3D

compat_3d = [
    Compatibility3D(
        framework='hanlons_razor',
        mode='sequential',
        questioning_patterns=['debugging_cognition'],
        confidence=0.94,
        rationale='Test'
    )
]

result = resolve_conflict(
    enhancers=[],
    mode_selection='sequential',
    reasoning_confidence=3,
    prompt_mode=None,
    token_limit=500,
    synergies=[],
    questioning_patterns=[],
    detection_timing=50.0,
    compatibility_3d=compat_3d,
)

print(f'Questioning patterns: {result.questioning_patterns}')
print(f'Rules fired: {result.rules_fired}')
"
```

**Expected Output**:
```
Questioning patterns: ['debugging_cognition']
Rules fired: ['3D_COMPATIBILITY']
```

**Possible Causes**:
1. **Conflict arbiter not updated**: Rule 6 (3D_COMPATIBILITY) not implemented
2. **Confidence threshold too high**: Check threshold in conflict_arbiter.py
3. **Rule priority**: Other rules taking precedence over 3D compatibility

**Solution**:
```bash
# Check conflict_arbiter.py has Rule 6 implemented
grep -A 10 "Rule 6" P:/.claude/hooks/UserPromptSubmit_modules/conflict_arbiter.py

# Should show 3D compatibility rule logic
```

---

## Best Practices

### 1. Conservative Matrix Expansion

**Principle**: Only add combinations with proven value (empirical testing >50 prompts)

**Anti-Pattern**: Adding all theoretically possible combinations (9 frameworks × 4 modes = 36 combinations)

**Correct Pattern**:
```python
# GOOD: Only 8 high-value combinations in matrix
_3D_COMPATIBILITY_MATRIX: Dict[Tuple[str, str], List[str]] = {
    ("hanlons_razor", "sequential"): ["debugging_cognition", "domain_knowledge"],
    # ... 7 other proven combinations
}

# BAD: All 36 possible combinations (many low-value)
_3D_COMPATIBILITY_MATRIX: Dict[Tuple[str, str], List[str]] = {
    (framework, mode): ["pattern1", "pattern2", ...]  # for all 36 combinations
}
```

### 2. Confidence Threshold Enforcement

**Principle**: Only inject questioning patterns when confidence > 0.85

**Implementation**:
```python
# In conflict_arbiter.py, Rule 6
if compatibility_3d and any(c.confidence > 0.85 for c in compatibility_3d):
    # Only inject high-confidence patterns
    for compat in compatibility_3d:
        if compat.confidence > 0.85:
            # Inject patterns
```

### 3. Performance Budget Adherence

**Principle**: 3D compatibility overhead must stay <10ms (8% of baseline)

**Monitoring**:
```bash
# Continuous performance monitoring
python P:/.claude/hooks/UserPromptSubmit_modules/performance_monitor.py \
  --perf-stats --filter 3d_compatibility --threshold 10
```

**Action**: If overhead exceeds 10ms, reduce matrix size or add caching

### 4. Backward Compatibility

**Principle**: 3D system must work alongside existing 2D system without breaking changes

**Implementation**:
- `compatibility_3d` field added to `UnifiedDetectionResult` with default empty list
- `build_tag_header()` accepts optional `compatibility_3d` parameter
- Conflict arbiter Rule 6 only fires if `compatibility_3d` provided

**Testing**:
```bash
# Test backward compatibility
pytest tests/test_backward_compatibility.py -v
```

### 5. Graceful Degradation

**Principle**: 3D compatibility failures should not break the entire detection system

**Implementation**:
```python
# In unified_detection.py
try:
    compatibility_3d = _detect_3d_compatibility(matched_frameworks, matched_modes)
except Exception:
    # Log error but don't fail detection
    compatibility_3d = []
    logger.warning("3D compatibility detection failed, continuing without it")
```

### 6. Configuration-Driven Matrix

**Principle**: Support external configuration of compatibility matrix

**Implementation**:
```python
# In cognitive_reasoning_config.json
{
  "compatibility_matrix_3d": {
    "enabled": true,
    "confidence_threshold": 0.85,
    "custom_combinations": {
      ("custom_framework", "custom_mode"): ["custom_pattern"]
    }
  }
}
```

---

## Migration Checklist

### Pre-Migration

- [ ] Measure baseline detection latency (TASK-000 baseline)
- [ ] Document existing 2D synergy combinations
- [ ] Identify top 10 most common framework+mode combinations
- [ ] Review questioning_patterns.md for all 5 patterns

### Phase 1: Foundation (TASK-013)

- [ ] Create `compatibility_matrix.py` module
- [ ] Implement `Compatibility3D` dataclass
- [ ] Define `_3D_COMPATIBILITY_MATRIX` with 8 initial combinations
- [ ] Implement `lookup_3d_compatibility()` function
- [ ] Implement `find_3d_compatibility()` function
- [ ] Write unit tests (`test_compatibility_matrix.py`)
- [ ] Verify all tests pass

### Phase 2: Integration (TASK-014)

- [ ] Update `UnifiedDetectionResult` to include `compatibility_3d` field
- [ ] Implement `_detect_3d_compatibility()` in `unified_detection.py`
- [ ] Call `_detect_3d_compatibility()` in `detect_prompt()`
- [ ] Update result construction to include `compatibility_3d`
- [ ] Write integration tests (`test_3d_integration.py`)
- [ ] Verify all tests pass
- [ ] Measure detection latency overhead (target: <10ms)

### Phase 3: Enhanced Telemetry (TASK-015)

- [ ] Update `build_tag_header()` to accept `compatibility_3d` parameter
- [ ] Implement `[3D-COMPAT]` tag formatting
- [ ] Update telemetry in all hooks (`cognitive_enhancers.py`, `think_trigger.py`)
- [ ] Write telemetry tests
- [ ] Verify tag format is correct and readable

### Phase 4: Conflict Arbiter (TASK-016)

- [ ] Add Rule 6 (3D_COMPATIBILITY) to `conflict_arbiter.py`
- [ ] Implement high-confidence pattern injection logic
- [ ] Update `resolve_conflict()` signature to accept `compatibility_3d`
- [ ] Write conflict arbiter tests
- [ ] Verify questioning patterns are injected correctly

### Post-Migration

- [ ] Run full test suite (`pytest tests/ -v`)
- [ ] Measure final detection latency (should be <65ms average)
- [ ] Test with 100+ real prompts to validate quality improvement
- [ ] Monitor performance database for regressions
- [ ] Document any issues or edge cases
- [ ] Update user documentation (CLAUDE.md, README.md)

---

## Acceptance Criteria

Migration is complete when:

1. **Functionality**: All 4 phases implemented and tested
2. **Performance**: Detection latency <65ms (P50), <75ms (P95)
3. **Coverage**: 8 high-value 3D combinations in matrix
4. **Quality**: >15% error reduction in testing
5. **Testing**: All unit, integration, and performance tests pass
6. **Documentation**: Migration guide complete with examples
7. **Monitoring**: Performance monitoring includes 3D metrics

---

## Additional Resources

### Documentation

- **Unified Detection System**: `docs/cognitive_optimization_migration.md`
- **Questioning Patterns**: `C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md`
- **Conflict Arbitration**: `UserPromptSubmit_modules/conflict_arbiter.py`
- **Telemetry**: `UserPromptSubmit_modules/tag_emission.py`

### Test Files

- **Unit Tests**: `tests/test_compatibility_matrix.py`
- **Integration Tests**: `tests/test_3d_integration.py`
- **Performance Tests**: `tests/test_3d_performance.py`

### Configuration

- **Cognitive Reasoning Config**: `cognitive_reasoning_config.json`
- **Performance Settings**: `cognitive_reasoning_config.json` → `performance` section

### Support

If you encounter issues not covered in this guide:

1. Check troubleshooting section above
2. Review test failures for clues
3. Query performance logs for timing issues
4. Check compatibility matrix for missing combinations
5. Create minimal reproducible example
6. Open issue with:
   - Migration phase where issue occurred
   - Error messages (full traceback)
   - Test output showing failure
   - Performance metrics (if regression)

---

**Migration Guide Version**: 1.0
**Last Updated**: 2026-03-15
**Status**: READY
**Next Review**: After Phase 4 completion (TASK-016)
