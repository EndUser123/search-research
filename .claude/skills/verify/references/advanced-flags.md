# Advanced Verification Flags

## --deep-lens: 6-Lens Code Review

**Purpose**: Systematic multi-dimensional code analysis across 6 quality dimensions

**Usage**:
```bash
/verify --deep-lens skill:code
/verify --deep-lens hook:breadcrumb_init
/verify --deep-lens feature:e2e
```

**What it does**:
- **State/Edge-Case Lens**: Verifies state management, boundary conditions, edge case handling
- **Identity/Invariants Lens**: Checks identity preservation, invariant assertions, consistency
- **I/O Validation Lens**: Validates input sanitization, output validation, schema compliance
- **Concurrency/TOCTOU Lens**: Detects race conditions, atomic operations, locking issues
- **Errors/Logging Lens**: Verifies error paths, logging coverage, graceful degradation
- **Tests/Coverage Lens**: Analyzes test coverage %, missing scenarios, test quality

**Output**: Enhanced Tier 2 report with 6-lens analysis in `deep_lens_results`

## --adversarial: 9-Agent Stress Testing

**Purpose**: Adversarial review using 7 specialized agents + 1 meta-analyst

**Usage**:
```bash
/verify --adversarial skill:arch
/verify --adversarial hook:init
/verify --adversarial feature:e2e
```

**What it does**:
Dispatches 7 specialized agents in parallel (single message pattern):
- **adversarial-compliance**: Specification violations, solo-dev constraints
- **adversarial-performance**: Bottlenecks, scalability concerns
- **adversarial-quality**: Maintainability, technical debt
- **adversarial-security**: Data exposure, access control gaps
- **adversarial-testing**: Coverage gaps, brittle tests
- **code-critic**: Design issues, code smells
- **qa-engineer**: Test completeness, edge cases

Meta-analysis via **adversarial-critic**:
- Consensus detection across agents
- Blind spot identification
- Bias and contradiction analysis
- Calibration verification

**Output**: Adversarial review report with:
- Individual agent summaries (confidence-filtered, 80+ threshold)
- Meta-analysis findings
- Overall verdict (PASS/FAIL/CONDITIONAL)
- Actionable recommendations

## --full-state: Source->Logic->Read Verification

**Purpose**: Full state verification using separate read operation protocol

**Usage**:
```bash
/verify --full-state skill:code --expected-files file1.py,file2.py
/verify --full-state hook:init
```

**What it does**:
1. **Define Source of Truth**: Characterize state source (file/directory, existence, permissions, metadata)
2. **Run Logic**: Verify the logic operation executed (write/edit/delete)
3. **Separate Read Operation**: Read actual state independently (no caching)
4. **Compare Expected vs Actual**: Detect mismatches, stale data, silent write failures

**Use cases**:
- Verifying file writes created expected content
- Confirming state changes applied correctly
- Detecting silent write failures (permission errors, disk full)
- Validating cache invalidation
- Checking multi-terminal state isolation

**Output**: Enhanced Tier 3 report with `full_state_results`:
- File-by-file verification status
- State match/mismatch details
- Differences list with specific issues

## Combining Flags

Multiple flags can be combined for comprehensive verification:

```bash
# Deep lens + adversarial review
/verify --deep-lens --adversarial skill:arch

# Deep lens + full state verification
/verify --deep-lens --full-state skill:code --expected-files src/main.py

# All three modes (most comprehensive)
/verify --deep-lens --adversarial --full-state hook:init
```

## Performance Expectations

- **Standard 4-tier**: ~5-15 seconds
- **With --deep-lens**: ~10-20 seconds (6-lens analysis adds depth)
- **With --adversarial**: ~30-60 seconds (9-agent parallel dispatch)
- **With --full-state**: ~5-10 seconds additional (file I/O verification)

**Note**: All modes run Tier 0 checklist first for fast-fail behavior
