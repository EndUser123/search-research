# Cognitive Feedback Loop Orchestrator (CFLO)

## Overview

CFLO is a closed-loop multi-agent orchestration system that coordinates builder and verifier agent cycles with automatic convergence detection. It enables self-correcting agent workflows through iterative improvement loops.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   CognitiveFeedbackLoopOrchestrator             │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐      ┌────────────────┐                   │
│  │ Builder Agents │ ───▶ │ Verifier Agents│                   │
│  └────────────────┘      └────────────────┘                   │
│         │                        │                             │
│         └────────────────────────┘                             │
│                    │                                           │
│            ┌───────▼────────┐                                 │
│            │ Convergence    │ ◀── Custom Callback             │
│            │ Detection      │     (converged, score, issues)   │
│            └───────────────┘                                 │
│                    │                                           │
│            ┌───────▼────────┐                                 │
│            │ Loop Control   │                                 │
│            │ (continue/     │                                 │
│            │  halt/converge)│                                 │
│            └───────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent Registry (`agent_registry.py`)

CFLO-scoped registry for managing builder and verifier agents.

**Key Classes:**
- `AgentRole` enum: BUILDER, VERIFIER, ORCHESTRATOR, ANALYZER
- `AgentDefinition`: Agent metadata (name, role, capability, config)
- `AgentRegistry`: Role-based lookup and CFLO-scoped singleton

**Usage:**
```python
from core.agent_registry import get_cflo_agent_registry, AgentRole

registry = get_cflo_agent_registry()
builders = registry.get_by_role(AgentRole.BUILDER)
```

### 2. Orchestrator (`cognitive_feedback_loop_orchestrator.py`)

Main loop controller with state persistence and timeout protection.

**Key Classes:**
- `LoopState` enum: IDLE, BUILDING, VERIFYING, CONVERGED, HALTED_ERROR, HALTED_TIMEOUT
- `LoopConfig`: Configuration (max_iterations, timeout, convergence_threshold)
- `CognitiveFeedbackLoopOrchestrator`: Main orchestrator

**Usage:**
```python
from core.cognitive_feedback_loop_orchestrator import CognitiveFeedbackLoopOrchestrator

orchestrator = CognitiveFeedbackLoopOrchestrator(
    builder_agents=["code-critic", "simplifier"],
    verifier_agents["tdd-test-writer"],
    convergence_check=lambda result: (
        result.get("issues_count", 0) == 0,
        1.0,
        []
    )
)

result = orchestrator.run("Refactor auth module for testability")
```

### 3. Stop Hook (`cflo_stop_hook.py`)

Blocks workflow stop when CFLO loop is active (preventing premature termination).

**Decision Logic:**
- No state file → Allow stop
- State in (BUILDING, VERIFYING) → Block stop
- State in (CONVERGED, HALTED_ERROR, HALTED_TIMEOUT) → Allow stop
- Stale state (>5 min) → Allow stop

## State Persistence

CFLO state is persisted to `.claude/state/cflo_state_{terminal_id}.json`:

```json
{
  "state": "verifying",
  "iteration": 3,
  "current_score": 0.87,
  "builder_agents": ["code-critic"],
  "verifier_agents": ["tdd-test-writer"],
  "last_update": "2026-02-07T16:30:00Z",
  "start_time": "2026-02-07T16:25:00Z",
  "issues": ["Missing type hints"]
}
```

## Convergence Detection

Custom callback function signature:

```python
def convergence_check(
    builder_output: dict[str, Any],
    verifier_output: dict[str, Any],
    iteration: int,
) -> tuple[bool, float, list[str]]:
    """
    Returns:
        - converged: bool - Whether to stop the loop
        - score: float - Quality score (0.0 to 1.0)
        - issues: list[str] - Remaining issues for next iteration
    """
    issues = extract_issues(verifier_output)
    converged = len(issues) == 0 or iteration >= max_iterations
    score = calculate_quality_score(builder_output, verifier_output)
    return converged, score, issues
```

## Multi-Terminal Isolation

CFLO uses `terminal_detection.detect_terminal_id()` for concurrent session safety:

```
P:\.claude\state\
├── cflo_state_terminal_1.json
├── cflo_state_terminal_2.json
└── cflo_state_terminal_3.json
```

## Error Handling

### TDD Failure Detection
```python
if _contains_tdd_failure(verifier_output):
    return IterationResult.HALT_ERROR
```

### Security Violation Detection
```python
if _contains_security_violation(verifier_output):
    return IterationResult.HALT_ERROR
```

### Timeout Protection
```python
with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(execute_agent, task)
    result = future.result(timeout=agent_timeout)
```

## Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Agent Registry | 7 | Role lookup, registration, scoping |
| Orchestrator | 8 | State machine, persistence, timeout |
| Integration | 14 | End-to-end workflows, multi-terminal |
| Stop Hook | 10 | Decision logic, staleness, error handling |

**Total:** 40 tests passing

## Configuration

### Default Values
- `DEFAULT_MAX_ITERATIONS`: 10
- `DEFAULT_CONVERGENCE_THRESHOLD`: 0.95
- `DEFAULT_PROGRESS_TIMEOUT_SECONDS`: 300 (5 minutes)

### Custom Configuration
```python
config = LoopConfig(
    max_iterations=15,
    convergence_threshold=0.98,
    progress_timeout_seconds=600
)
```

## Integration Points

### TDD Workflow
CFLO integrates with TDD skills for automated test-driven development:
- `tdd-test-writer`: Generates failing tests (RED phase)
- `tdd-implementer`: Implements code to pass tests (GREEN phase)
- `tdd-refactorer`: Improves code quality (REFACTOR phase)

### Quality Gates
Layer 4 quality gate agents can serve as verifiers:
- `quality-gate`: Filters findings by confidence threshold
- `adversarial-review`: Parallel security/quality analysis

## Files

| File | Purpose |
|------|---------|
| `src/core/agent_registry.py` | Agent registration and lookup |
| `src/core/cognitive_feedback_loop_orchestrator.py` | Main orchestrator |
| `src/core/cflo_stop_hook.py` | Stop hook integration |
| `tests/core/test_cflo_agent_registry.py` | Registry tests |
| `tests/core/test_cflo_orchestrator.py` | Orchestrator tests |
| `tests/core/test_cflo_integration.py` | Integration tests |
| `tests/core/test_cflo_stop_hook.py` | Stop hook tests |

## Implementation Status

- ✅ Phase 1: Agent Registry
- ✅ Phase 2: Core Orchestrator
- ✅ Phase 3: Stop Hook Integration
- ✅ Phase 4: Integration Tests
- ✅ TDD: RED → GREEN → REFACTOR complete

---

**Last Updated:** 2026-02-07
**Status:** Production Ready
