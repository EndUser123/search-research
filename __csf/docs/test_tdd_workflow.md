# Unified Test/TDD Workflow Guide

**Purpose:** Complete guide to the test analysis and TDD workflow integration.

**Last updated:** 2026-01-28

---

## Overview

The test/TDD ecosystem consists of two main skills and supporting modules:

| Component | Purpose | Skill File |
|-----------|---------|------------|
| `/test` | Coverage analysis and gap identification | `.claude/skills/test/SKILL.md` |
| `/tdd` | Test-driven development workflow | `.claude/skills/tdd/SKILL.md` |
| Test Analysis Modules | Caching, scoring, trends, baselines, classification | `__csf/src/quality/test_analysis/` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                              │
│                      "/test my_module.py"                           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        /test SKILL                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. Discover Tests       → Find all test files               │   │
│  │ 2. Classify Tests      → TestClassifier (auto-detect type)  │   │
│  │ 3. Scan Patterns       → Solo-dev violation detection      │   │
│  │ 4. Run Pytest-Cov      → Real coverage numbers             │   │
│  │ 5. Analyze Coverage    → Map gaps to code                  │   │
│  │ 6. Score Gaps          → GapScorer (priority ranking)       │   │
│  │ 7. Store Snapshot      → Coverage trends + baselines       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       OUTPUT REPORT                                 │
│  • Coverage % (pytest-cov)                                          │
│  • Test gaps by type (unit, integration, edge case, error path)     │
│  • Prioritized recommendations (P0-P3)                               │
│  • Solo-dev violations                                              │
│  • Trend analysis vs baseline                                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      .test_gaps.json                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  {                                                             │   │
│    "target": "my_module.py",                                   │   │
│    "gaps": [                                                   │   │
│      {"priority": 1, "type": "error_path",                     │   │
│       "name": "corrupted_json", "score": 85.0,                │   │
│       "rationale": "Critical: data safety risk"},              │   │
│      ...                                                       │   │
│    ]                                                           │   │
│  }                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        /tdd SKILL                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. Load .test_gaps.json                                      │   │
│  │ 2. For each gap (priority order):                             │   │
│  │    a. RED phase: Write failing test                           │   │
│  │    b. GREEN phase: Implement feature                          │   │
│  │    c. REFactor phase: Improve code                            │   │
│  │ 3. Update gap status → complete                               │   │
│  │ 4. Compare to baseline → detect drift                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      COVERAGE SNAPSHOT                               │
│  • New coverage stored in trends                                   │
│  • Compared to baseline                                             │
│  • Regression detection                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module Integration

### 1. Incremental Cache (`incremental_cache.py`)

**Purpose:** Avoid re-analyzing unchanged code.

**Usage in /test:**
```python
from quality.test_analysis import get_cached_analysis, save_analysis

# Check if we have fresh analysis
cached = get_cached_analysis(target_path)
if cached:
    # Use cached test files, coverage data
    test_files = cached.test_files
    coverage = cached.coverage
else:
    # Run fresh analysis
    test_files = discover_tests(target_path)
    coverage = run_pytest_cov(target_path)

    # Save for next time
    save_analysis(target_path, test_files, coverage)
```

**When cache is invalidated:**
- File modification time changes
- File size changes
- Manual invalidation via `invalidate_target()`

---

### 2. Test Classifier (`test_classifier.py`)

**Purpose:** Auto-detect test types (unit, integration, edge case, error path, regression).

**Usage in /test:**
```python
from quality.test_analysis import TestClassifier

classifier = TestClassifier()

# Classify a single test
result = classifier.classify_test("test_empty_input")
# result.test_type = "edge_case"
# result.confidence = 0.6
# result.reasons = ["Name matches edge case pattern"]

# Classify all tests in file
results = classifier.classify_tests_in_file("tests/test_api.py")
for r in results:
    print(f"{r.test_name} -> {r.test_type} (confidence: {r.confidence})")
```

**Classification patterns:**

| Type | Name Patterns | AST Indicators |
|------|--------------|----------------|
| **Unit** | `test_<function>()` | Low complexity, few external calls |
| **Integration** | `_*_integration`, `_*_flow`, `_*_e2e` | High complexity, many external calls |
| **Edge Case** | `_*_edge`, `_*_empty`, `_*_null`, `_*_zero` | Boundary conditions |
| **Error Path** | `_*_error`, `_*_exception`, `_*_invalid` | Try/except blocks, assertRaises |
| **Regression** | `_*_regression`, `_*_bug_123` | Bug/issue references |

---

### 3. Gap Scorer (`gap_scorer.py`)

**Purpose:** Prioritize test gaps by risk, complexity, change frequency, proximity, and constitutional violations.

**Usage in /test:**
```python
from quality.test_analysis import GapScorer, TestGap, ScoringContext

# Prepare context
context = ScoringContext(
    target_path="src/mymodule.py",
    recently_changed_files=["src/mymodule.py"],  # From git log
    covered_functions={"test_helper_func"},       # Already tested
    days_lookback=30
)

# Create gap
gap = TestGap(
    gap_id="gap_1",
    type="error_path",
    name="corrupted_json_recovery",
    file="src/mymodule.py",
    line=42
)

# Score it
scorer = GapScorer(context)
score = scorer.score_gap(gap)
# score.total_score = 85.0
# score.priority = "P1"
# score.rationale = "High: High-risk or frequently changed code"
# score.factors = ["High risk (error_path)", "Recently changed", "Near tested code"]

# Score multiple gaps
gaps = [gap1, gap2, gap3]
scores = scorer.score_gaps(gaps)  # Sorted by score DESC
```

**Scoring breakdown:**
- **Risk (30 pts)**: error_path=25, solo_dev=30, integration=22, edge_case=18, function=15
- **Complexity (25 pts)**: AST cyclomatic complexity → normalized
- **Change Frequency (20 pts)**: Recently changed=20, stable=8
- **Proximity (15 pts)**: Near tested code=12, isolated=5
- **Constitutional (+50 pts)**: Solo-dev violations auto-P0

---

### 4. Coverage Trends (`coverage_trends.py`)

**Purpose:** Track coverage over time, detect trends and regressions.

**Usage in /test:**
```python
from quality.test_analysis import add_snapshot, analyze_trend, detect_regression

# After running pytest-cov, record snapshot
add_snapshot(
    percent=84.0,
    statements=100,
    missing=16,
    modules={"mymodule.py": {"stmts": 50, "miss": 8, "cover": 84.0}}
)

# Analyze trend
analysis = analyze_trend(period="30d")
# analysis.overall_trend = "improving"
# analysis.overall_change = +4.2%
# analysis.regressions = []  # No regressions

# Check for regression since last snapshot
regressions = detect_regression()
if regressions:
    print(f"WARNING: Coverage regression detected!")
    for r in regressions:
        print(f"  {r.module}: {r.previous}% → {r.current}% ({r.change}%)")
```

**Trend classifications:**
- **Regression**: ≤ -5% change
- **Declining**: -5% to -2% change
- **Stable**: -2% to +2% change
- **Improving**: ≥ +2% change

---

### 5. Baseline Storage (`baseline_storage.py`)

**Purpose:** Store and compare against coverage baselines (golden, release, feature).

**Usage in /test:**
```python
from quality.test_analysis import (
    create_baseline,
    compare_to_baseline,
    BaselineType
)

# Create golden baseline
baseline = create_baseline(
    name="v1.0-golden",
    baseline_type=BaselineType.GOLDEN,
    branch="main",
    commit="abc123",
    percent=85.0,
    statements=100,
    missing=15
)

# Compare current state to baseline
diff = compare_to_baseline(
    name="v1.0-golden",
    current_percent=82.0,
    current_statements=100,
    current_missing=18
)
# diff.status = "behind"
# diff.percent_diff = -3.0
# diff.is_regressing = False  # Not > -5%
```

**Baseline types:**
- **Golden**: Established quality standard
- **Release**: Last release baseline
- **Feature**: Feature branch baseline
- **Temporary**: Temporary comparison point

---

## Complete Workflow Examples

### Example 1: New Feature Development

```
# 1. Write code with TDD
/tdd implement "user authentication feature"

# 2. After implementation, check coverage
/test "auth.py"

# Output shows:
# - Coverage: 78% (missing error paths for invalid tokens)
# - Gaps: [P1] test_invalid_token (error path)

# 3. Write missing tests
/tdd implement "test_invalid_token"

# 4. Re-check coverage
/test "auth.py"

# Output shows:
# - Coverage: 92% (↑ 14% from baseline)
# - Trend: improving
# - Status: ahead of baseline
```

---

### Example 2: Regression Detection

```
# 1. Run coverage check
/test "payment.py"

# Output shows:
# - Coverage: 68% (↓ 8% from baseline)
# - Trend: REGRESSION
# - Regressions: [payment.py: 75% → 68%]

# 2. Investigate
# Recent commit removed test for refund_edge_case
# Gap scorer marks it P0 (solo-dev: data safety)

# 3. Fix
/tdd implement "test_refund_edge_case"

# 4. Verify
/test "payment.py"
# - Coverage: 74% (↑ 6%, stable vs baseline)
```

---

### Example 3: Gap Prioritization

```
# 1. Full analysis
/test "api/"

# Output shows gaps scored:
# ┌──────────────────────────────┬───────┬───────────┬─────────────────┐
# │ Gap                           │ Score │ Priority │ Rationale       │
# ├──────────────────────────────┼───────┼───────────┼─────────────────┤
# │ corrupted_json_recovery      │  85.0 │ P1        │ High risk       │
# │ concurrent_access_race       │  78.0 │ P1        │ Recently changed│
# │ empty_input_handling          │  62.0 │ P2        │ Edge case       │
# │ timezone_boundary            │  45.0 │ P3        │ Low risk        │
# └──────────────────────────────┴───────┴───────────┴─────────────────┘

# 2. Work in priority order
/tdd implement "P1 gaps for api/"
```

---

## Data Flow Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   /test skill   │────▶│ Test Analysis   │────▶│  State Files    │
│                 │     │     Modules     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ .test_gaps.json │     │   Pytest-cov    │     │ .claude/state/  │
│                 │     │                 │     │                 │
│ • Gaps          │     │ • Coverage %    │     │ • Cache         │
│ • Priorities    │◀────│ • Missing lines │     │ • Trends        │
│ • Types         │     │                 │     │ • Baselines     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│   /tdd skill    │
│                 │
│ • Load gaps     │
│ • RED phase     │
│ • GREEN phase   │
│ • REFactor phase│
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  New Coverage   │
│                 │
│ • Updated %     │
│ • Trend delta   │
│ • Baseline diff │
└─────────────────┘
```

---

## Quick Reference

### Command Summary

| Command | Purpose | Output |
|---------|---------|--------|
| `/test <target>` | Coverage analysis + gap identification | Report + .test_gaps.json |
| `/tdd implement "<gap>"` | Implement test using TDD | Test code + updated gap status |
| `/tdd implement "all"` | Implement all gaps in priority order | All tests + final coverage |
| `/verify` | Run tests and check for regressions | Test results + regression check |

### Module Quick Reference

```python
# Cache
from quality.test_analysis import get_cached_analysis, save_analysis
cached = get_cached_analysis(target)
save_analysis(target, test_files, coverage)

# Classification
from quality.test_analysis import TestClassifier
classifier = TestClassifier()
result = classifier.classify_test("test_name")

# Scoring
from quality.test_analysis import GapScorer
scorer = GapScorer(context)
score = scorer.score_gap(gap)

# Trends
from quality.test_analysis import add_snapshot, analyze_trend
add_snapshot(percent, statements, missing, modules)
analysis = analyze_trend(period="30d")

# Baselines
from quality.test_analysis import create_baseline, compare_to_baseline
create_baseline(name, type, branch, commit, percent, statements, missing)
diff = compare_to_baseline(name, current_percent, ...)
```

---

## File Locations

| Component | Path |
|-----------|------|
| Test skill | `.claude/skills/test/SKILL.md` |
| TDD skill | `.claude/skills/tdd/SKILL.md` |
| Test modules | `__csf/src/quality/test_analysis/` |
| Gap file | `.test_gaps.json` (project root) |
| Cache | `~/.claude/state/test_analysis_cache.json` |
| Trends | `~/.claude/state/test_coverage_trends.json` |
| Baselines | `~/.claude/state/test_baselines.json` |

---

## Best Practices

1. **Run /test before committing** — Catch coverage regressions early
2. **Use TDD for new features** — RED → GREEN → REFactor
3. **Check trends weekly** — Monitor coverage direction
4. **Update baselines on release** — Track quality over time
5. **Address P0 gaps immediately** — Constitutional violations and data safety
6. **Leverage the cache** — Reuse analysis for unchanged code
7. **Trust the scorer** — Prioritize based on data, not gut feel

---

**Version:** 1.0
**Modules:** incremental_cache, gap_scorer, coverage_trends, baseline_storage, test_classifier
