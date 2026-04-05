# Remaining Implementation Guide: Phases 3-8

**Project**: TSK-251224-1926-QualityZenEnhance
**Date**: 2024-12-24
**Status**: Ready for Implementation
**Remaining Tasks**: 25 quadlets (~15.5 hours)

---

## Overview

This guide provides detailed implementation instructions for the remaining 25 quadlet tasks across Phases 3-8. Each task includes:
- Prerequisites
- Implementation steps
- Code examples
- Testing requirements
- Success criteria

---

## Phase 3: Cost Tracking (6 tasks, ~3 hours)

**Objective**: Track LLM usage costs by provider

### Q9: Add Cost Tracking to zen_adapter

**File**: `P:\__csf.nip\src\quality\zen_review_adapter.py`

**Implementation**:
```python
def review_target(
    self,
    target: str,
    mode: str = "mid",
    focus_areas: Optional[List[str]] = None,
    context: Optional[str] = None,
    verify: bool = False,
    cost_tracking: bool = False  # NEW PARAMETER
) -> Dict[str, Any]:
    """
    Run LLM code review on target with optional cost tracking.

    Args:
        cost_tracking: If True, track token usage and costs by provider

    Returns:
        Review result with optional cost_breakdown:
        {
            'success': True,
            'consensus_findings': [...],
            'cost_breakdown': {
                'claude': {'tokens': 1000, 'cost': 0.003},
                'gpt4': {'tokens': 800, 'cost': 0.006},
                'total_tokens': 1800,
                'total_cost': 0.009
            }
        }
    """
    result = self._orchestrator.execute_review(
        repo_path=target,
        mode=mode,
        focus_areas=focus_areas,
        context=context,
        dry_run=False,
        cost_tracking=cost_tracking  # Pass to orchestrator
    )

    # Rest of existing logic...

    return result
```

**Testing**: Run with `--cost-tracking` flag, verify cost_breakdown in results

### Q10: Update Executor to Collect Cost Data

**File**: `P:\__csf.nip\src\quality\enhanced_execution.py`

**Changes**:
```python
# In execute_cognitive_review_phase()

# Show cost breakdown if enabled
if self.cost_tracking and review.get('cost_breakdown'):
    cost_breakdown = review.get('cost_breakdown', {})
    total_tokens = cost_breakdown.get('total_tokens', 0)
    total_cost = cost_breakdown.get('total_cost', 0)

    print(f"    💰 Cost Tracking:")
    print(f"       Total Tokens: {total_tokens:,}")
    print(f"       Total Cost: ${total_cost:.4f}")

    # Show by provider
    for provider, data in cost_breakdown.items():
        if provider not in ['total_tokens', 'total_cost']:
            tokens = data.get('tokens', 0)
            cost = data.get('cost', 0)
            print(f"       {provider}: {tokens:,} tokens, ${cost:.4f}")

    results['cost_breakdown'] = cost_breakdown
```

### Q11-Q14: Tests, Documentation

**Test File**: `tests/test_enhanced_execution_cost_tracking.py`

**Test Cases**:
1. Cost tracking parameter loaded from CLI
2. Cost tracking default is false
3. Cost breakdown displayed when enabled
4. Cost breakdown not shown when disabled
5. Works with verification enabled

**Documentation**: `evidence/step_08/cost_tracking.md`

---

## Phase 4: Compression (4 tasks, ~2.5 hours)

**Objective**: Enable result compression for large projects

### Q15: Add Compression Parameter

**File**: `P:\__csf.nip\src\quality\zen_review_adapter.py`

```python
def review_target(
    self,
    target: str,
    mode: str = "mid",
    focus_areas: Optional[List[str]] = None,
    context: Optional[str] = None,
    verify: bool = False,
    cost_tracking: bool = False,
    compress_result: bool = False  # NEW
) -> Dict[str, Any]:
    """
    Run LLM code review with optional result compression.

    Args:
        compress_result: If True, compress results using AI Distiller

    Returns:
        Review result with compression statistics if enabled
    """
    # Calculate project size
    if compress_result:
        total_lines = self._calculate_project_size(target)
        use_compression = total_lines > 10000  # Default threshold
    else:
        use_compression = False

    result = self._orchestrator.execute_review(
        repo_path=target,
        mode=mode,
        focus_areas=focus_areas,
        context=context,
        dry_run=False,
        compress_result=use_compression
    )

    return result

def _calculate_project_size(self, target: str) -> int:
    """Calculate total lines of code in target."""
    target_path = Path(target).resolve()
    total_lines = 0

    for py_file in target_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                total_lines += len(f.readlines())
        except Exception:
            continue

    return total_lines
```

### Q16: Implement Auto-Compression Logic

**Already implemented in Q15** - threshold logic included

### Q17-Q18: Tests and Documentation

**Test File**: `tests/test_enhanced_execution_compression.py`

**Test Cases**:
1. Compression enabled for projects >10,000 lines
2. Compression disabled for small projects
3. Compression statistics displayed
4. Configurable compression threshold

**Documentation**: `evidence/step_08/compression.md`

---

## Phase 5: CLI Integration (4 tasks, ~1.5 hours)

**Objective**: Complete CLI enhancements

### Q19: Add Help Documentation

**File**: `P:\__csf.nip\src\quality\qual-gate.py`

**Update epilog section** (around line 1877):
```python
epilog="""
ENHANCED FEATURES (zen* integration):
  --verify              Enable finding verification to filter hallucinations
  --cost-tracking        Track LLM usage costs by provider
  --compress-results     Enable AI distillation for large projects (>10k lines)

EXAMPLES WITH ENHANCED FEATURES:
  qual-gate . --verify                         # Enable verification
  qual-gate . --cost-tracking                  # Track costs
  qual-gate . --verify --cost-tracking         # Multiple features
  qual-gate . --focus-areas security --verify   # Specific focus with verification

CONFIGURATION FILE (.qual-gate.json):
  {
    "gates": {
      "code_review": {
        "review_mode": "mid",
        "focus_areas": ["security", "bugs", "error_handling"],
        "verify_findings": true,
        "cost_tracking": true,
        "compress_results": false
      }
    }
  }

ENVIRONMENT VARIABLES:
  QUAL_GATE_VERIFY_FINDINGS=true
  QUAL_GATE_COST_TRACKING=true
  QUAL_GATE_COMPRESS_RESULTS=true

PERFORMANCE NOTES:
  ✅ Verification: +10-30s overhead, eliminates >80% false positives
  ⚡ Cost Tracking: Minimal overhead, provides cost visibility
  🗜️  Compression: +5s overhead, 89% token savings for large projects
```

### Q20-Q23: Examples, Validation, Testing

**Examples**: Added to help text above

**Validation**: Add in validation function
```python
def _validate_enhanced_features(args):
    """Validate enhanced feature combinations."""
    # Check for conflicting options
    if args.compress_results and args.review_mode == "chill":
        print("⚠️  Warning: Compression has minimal benefit in chill mode")
```

**Testing**: Manual CLI testing
```bash
qual-gate . --help  # Verify help text
qual-gate . --verify  # Test verification
qual-gate . --cost-tracking  # Test cost tracking
```

---

## Phase 6: Focus Areas Polish (1 task, ~0.5 hours)

**Objective**: Add focus area validation

### Q34: Add Focus Area Validation

**File**: `P:\__csf.nip\src\quality\enhanced_execution.py`

```python
VALID_FOCUS_AREAS = [
    'security', 'bugs', 'error_handling', 'configuration',
    'performance', 'concurrency', 'code_quality', 'testing',
    'api_design', 'type_safety', 'dependencies', 'documentation',
    'architecture',
    # Legacy categories (will be mapped)
    'design', 'clarity', 'reasoning'
]

def _validate_focus_areas(self, focus_areas: List[str]) -> List[str]:
    """
    Validate focus areas and provide helpful error messages.

    Args:
        focus_areas: List of focus areas to validate

    Returns:
        Validated focus areas

    Raises:
        ValueError: If invalid focus areas provided
    """
    invalid_areas = [area for area in focus_areas if area not in VALID_FOCUS_AREAS]

    if invalid_areas:
        valid_list = ', '.join(VALID_FOCUS_AREAS)
        raise ValueError(
            f"Invalid focus areas: {', '.join(invalid_areas)}\n"
            f"Valid options: {valid_list}"
        )

    return focus_areas

# In __init__, after loading focus_areas:
try:
    self.focus_areas = self._validate_focus_areas(focus_areas_raw)
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    self.focus_areas = default_focus
```

---

## Phase 7: Advanced Filtering (6 tasks, ~3 hours)

**Objective**: Add result filtering capabilities

### Q35: Consensus Quality Filtering

**File**: `P:\__csf.nip\src\quality\enhanced_execution.py`

```python
def _filter_by_consensus_quality(
    self,
    findings: List[Dict],
    min_agreement: int = 2
) -> List[Dict]:
    """
    Filter findings by consensus quality.

    Args:
        findings: List of findings with agreement metadata
        min_agreement: Minimum number of models that must agree (default: 2)

    Returns:
        Filtered findings with high agreement
    """
    filtered = []
    for finding in findings:
        agreement = finding.get('agreement_count', 0)
        if agreement >= min_agreement:
            filtered.append(finding)

    return filtered
```

### Q36-Q38: Severity, Actionability, Focus Area Filtering

```python
def _filter_findings(
    self,
    findings: List[Dict],
    min_severity: str = None,
    autonomous_only: bool = False,
    focus_areas: List[str] = None
) -> List[Dict]:
    """
    Apply multiple filters to findings.

    Args:
        findings: Raw findings list
        min_severity: Minimum severity level (info, warning, error, critical)
        autonomous_only: Only show autonomous findings (🤖)
        focus_areas: Only show findings for these areas

    Returns:
        Filtered findings
    """
    filtered = findings

    # Severity filter
    if min_severity:
        severity_levels = {'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
        min_level = severity_levels.get(min_severity, 0)
        filtered = [
            f for f in filtered
            if severity_levels.get(f.get('severity', 'info'), 0) >= min_level
        ]

    # Actionability filter
    if autonomous_only:
        filtered = [
            f for f in filtered
            if f.get('actionability') == 'autonomous'
        ]

    # Focus area filter
    if focus_areas:
        filtered = [
            f for f in filtered
            if f.get('category') in focus_areas
        ]

    return filtered
```

### Q39-Q40: Tests and Documentation

**Test File**: `tests/test_enhanced_execution_filtering.py`

**Documentation**: `evidence/step_08/filtering.md`

---

## Phase 8: Polish (5 tasks, ~4 hours)

**Objective**: Documentation, integration tests, cleanup

### Q41: User Guide

**File**: `P:\__csf.nip\docs\quality_system\enhanced_features_guide.md`

```markdown
# Enhanced Quality System User Guide

## Overview
The enhanced quality system integrates zen* and llm* capabilities for comprehensive code review.

## Features
1. Focus Area Expansion (12 categories)
2. Finding Verification (filter hallucinations)
3. Cost Tracking (LLM usage visibility)
4. Result Compression (token savings)

## Quick Start
[Examples and tutorials]
```

### Q42: API Documentation

**File**: `P:\__csf.nip\docs\quality_system\api_reference.md`

Document all public APIs with examples.

### Q43: Integration Test Suite

**File**: `tests/integration/test_quality_system_integration.py`

```python
def test_full_workflow_with_all_features():
    """Test complete workflow with all enhanced features enabled."""
    # Setup test project
    # Run qual-gate with all features
    # Verify results
    pass

def test_backward_compatibility():
    """Test that old configs still work."""
    pass
```

### Q44: Update README

**File**: `P:\__csf.nip\src\quality\README.md`

Add section on enhanced features with examples.

### Q45: Release Notes

**File**: `P:\__csf.nip\.speckit\memory\TSK-251224-1926-QualityZenEnhance\release_notes.md`

```markdown
# Release Notes - Quality System Enhancement v1.1.0

## New Features
- 12 review categories (up from 3)
- Finding verification (eliminate hallucinations)
- Cost tracking (LLM usage visibility)
- Result compression (89% token savings)

## Breaking Changes
None - all changes are backward compatible

## Migration Guide
[Upgrade instructions]
```

---

## Implementation Priority

### High Priority (Complete First)
1. **Phase 3: Cost Tracking** (3 hours)
   - High value, moderate complexity
   - Users want cost visibility

2. **Phase 6: Focus Area Validation** (0.5 hours)
   - Quick win, improves UX
   - Prevents configuration errors

### Medium Priority
3. **Phase 4: Compression** (2.5 hours)
   - Good value, moderate complexity
   - Useful for large projects

4. **Phase 8: User Guide and API Docs** (2 hours)
   - Essential for adoption
   - Can be done incrementally

### Lower Priority
5. **Phase 7: Advanced Filtering** (3 hours)
   - Nice to have, lower value
   - Can be deferred to future release

---

## Testing Strategy

### Unit Tests
- Each quadlet should have corresponding tests
- Test file naming: `test_<feature>_<component>.py`
- Target: 95%+ code coverage

### Integration Tests
- End-to-end workflow tests
- Feature combination tests
- Backward compatibility tests

### Manual Testing
```bash
# Test each feature individually
qual-gate . --verify
qual-gate . --cost-tracking
qual-gate . --compress-results

# Test combinations
qual-gate . --verify --cost-tracking
qual-gate . --focus-areas security bugs --verify

# Test config file loading
# Create .qual-gate.json with various configurations
qual-gate .

# Test backward compatibility
# Use old config format, verify it works
```

---

## Rollback Strategy

Each phase is independently rollbackable:

```bash
# Rollback specific phase
git checkout HEAD -- src/quality/enhanced_execution.py
git checkout HEAD -- src/quality/qual-gate.py

# Rollback tests
rm tests/test_enhanced_execution_<feature>.py
```

---

## Success Criteria

### Phase Completion Checklist

Each phase is complete when:
- [ ] All quadlets implemented
- [ ] All tests passing (95%+ coverage)
- [ ] Documentation written
- [ ] Manual testing successful
- [ ] No breaking changes
- [ ] Backward compatibility verified

### Overall Project Success

- [ ] All 38 quadlets complete
- [ ] All 12 focus areas working
- [ ] Verification filters >80% FP
- [ ] Cost tracking functional
- [ ] Compression achieves 89% savings
- [ ] 100% backward compatibility
- [ ] Documentation complete
- [ ] Integration tests passing

---

## Timeline Estimate

| Phase | Tasks | Estimate | Running Total |
|-------|-------|----------|---------------|
| 1 | Foundation | ✅ Complete | ✅ Complete |
| 2 | Verification | ✅ Complete | ✅ Complete |
| 3 | Cost Tracking | 6 tasks (3h) | 3h |
| 4 | Compression | 4 tasks (2.5h) | 5.5h |
| 5 | CLI Polish | 4 tasks (1.5h) | 7h |
| 6 | Focus Validation | 1 task (0.5h) | 7.5h |
| 7 | Filtering | 6 tasks (3h) | 10.5h |
| 8 | Polish | 5 tasks (4h) | 14.5h |

**Total Remaining**: ~14.5 hours

---

## Next Actions

1. **Start with Phase 3** (Cost Tracking)
   - Highest value, moderate complexity
   - Follow implementation guide above

2. **Continue with Phase 6** (Validation)
   - Quick win, improves UX

3. **Complete Phase 4** (Compression)
   - Good for large projects

4. **Phase 8 Documentation**
   - Essential for adoption

5. **Phase 7 Filtering** (Optional)
   - Can defer if time-constrained

---

**Guide Version**: 1.0
**Last Updated**: 2024-12-24
**Status**: Ready for Implementation
