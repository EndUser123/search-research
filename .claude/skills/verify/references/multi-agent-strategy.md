# Multi-Agent Verification Strategy

The /verify skill uses multiple agents across verification tiers to reduce same-model bias and improve detection coverage.

## Agent Assignments by Tier

### Tier 0: Checklist Verification
- **Agent**: Same model (lead session)
- **Rationale**: Checklist verification is deterministic and fast (< 5 seconds)
- **Scope**: Systematic checks of required elements (problem statement, context, solution, risks, tests)

### Tier 1: Component Tests
- **Agent**: pytest framework (tool-based)
- **Rationale**: Automated test runner provides objective pass/fail results
- **Scope**: Unit tests for individual components

### Tier 2: Integration Check
- **Agent**: /testing-skills subagent (delegated)
- **Rationale**: Separate agent reduces bias from lead implementation
- **Scope**: Hook/router integration, chain execution

### Tier 3: E2E Test
- **Agent**: /trace subagent (delegated) + manual verification
- **Rationale**: Different agent + manual oversight provides deepest verification
- **Scope**: Actual skill/workflow invocation with real execution evidence

## Bias Reduction Strategy

- **Separation of concerns**: Each tier uses different verification approach
- **Agent diversity**: Different agents for Tiers 2-3 reduce same-model confirmation bias
- **Evidence hierarchy**: Each tier builds on previous, catching different failure modes
- **Independent failure**: Any tier can independently fail, preventing false positives

## When Multi-Agent Matters Most

- **Complex skills**: High risk of implementation bias affecting verification
- **Critical workflows**: Production impact requires thorough verification
- **Integration-heavy code**: Hook chains and router logic benefit from multiple perspectives
