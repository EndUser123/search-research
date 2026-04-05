# Adversarial Validation Agents

This document describes the 8 adversarial subagents used in Step 7 of the pre-mortem workflow.

## Agent Lineup

### adversarial-compliance — Specification Violations

**Detects**: Constitutional violations, solo-dev inappropriate patterns, spec deviations

**Catches**:
- "Team approval gates" in solo-dev projects
- Missing verification requirements
- Spec deviations without approval

### adversarial-performance — Performance Bottlenecks

**Detects**: Timeouts, N+1 patterns, cascading failures, scalability limits

**Catches**:
- "Processes 10K items synchronously" (timeout risk)
- Unbounded loops
- Missing connection pooling
- No pagination for large datasets

### adversarial-security — Security Vulnerabilities

**Detects**: Data leaks, access control gaps, encryption issues, injection risks

**Catches**:
- "Log sensitive data to stdout"
- Missing input validation
- Hardcoded credentials
- SQL injection patterns

### adversarial-quality — Quality Concerns

**Detects**: Maintainability risks, tech debt, code smells, coupling issues

**Catches**:
- "Copy-pasted code across 10 files"
- Missing error handling
- God objects
- Tight coupling

### adversarial-testing — Testing Gaps

**Detects**: Missing scenarios, brittle tests, coverage gaps, edge cases

**Catches**:
- "Only happy path tested"
- No failure scenario coverage
- Brittle assertions
- Missing integration tests

### adversarial-critic — Meta-Analysis

**Detects**: Consensus gaps, blind spots, bias patterns, contradiction detection

**Provides**:
- Confidence calibration on all findings (0-100% based on evidence quality)
- Cross-validation of other agents' findings
- Blind spot detection when all agents agree

**Catches**:
- "All agents agree → possible blind spot"
- "Single agent → likely bias"
- Contradictions between findings

### code-critic — General Code Review

**Detects**: Logic errors, implementation gaps, architectural issues

**Catches**:
- "Fix breaks existing feature"
- Missing integration points
- Logic bugs
- Architectural inconsistencies

### qa-engineer — Verification Perspective

**Detects**: Missing acceptance criteria, untestable requirements, validation gaps

**Catches**:
- "Success criteria undefined"
- No way to verify fix works
- Untestable requirements
- Missing validation gates

## Integration Workflow

```python
from lib.adversarial_review_coordinator import run_subagent_review

# After Step 6 (Monitor Warning Signs)
adversarial_findings = run_subagent_review(
    plan_content=pre_mortem_output,  # Use pre-mortem as "plan"
    subagents=[
        'adversarial-compliance',
        'adversarial-performance',
        'adversarial-quality',
        'adversarial-security',
        'adversarial-testing',
        'adversarial-critic',
        'code-critic',
        'qa-engineer'
    ]
)

# Merge adversarial findings into pre-mortem output
# adversarial-critic provides confidence calibration
```

## Confidence Calibration Rules

adversarial-critic adjusts confidence based on evidence quality:

| Evidence Quality | Confidence Adjustment |
|-----------------|----------------------|
| Tier 1 (execution artifacts, test output) | Boost to 80-100% |
| Tier 2 (official docs, peer review) | Boost to 70-85% |
| Tier 3 (static analysis, logical derivation) | Reduce to 50-70% |
| Tier 4 (speculation, unverified claims) | Reduce to 20-50% |

## Output Format

Pre-mortem output includes "ADVERSARIAL VALIDATION" section after TOP PRIORITIES:

### HIGH Priority Adversarial Findings

#### PERF-001: Context burden kills adoption [45% confidence]
- **Category**: Performance
- **Source**: adversarial-performance
- **Description**: 100+ line context prompts per review create friction
- **Recommendation**: Create prompt template library for common plan types
- **Calibration**: [OVERCONFIDENT] Original 85% → 45% (no usage data evidence)

### Filtered Out (Low Value)

The following are automatically filtered to reduce noise:
- YAGNI violations ("add progress indicator for future use")
- Premature optimization ("optimize for scale before needed")
- Over-engineering ("create abstraction layer for single use")
- Nitpicks (style issues with minimal impact)

## Opt-Out

Disable adversarial validation with `--no-adversarial` flag.

Use ONLY when:
- System is offline (no subagent access)
- Known adversarial review bug for specific scenario
- Extreme time pressure (document why adversarial was skipped)
