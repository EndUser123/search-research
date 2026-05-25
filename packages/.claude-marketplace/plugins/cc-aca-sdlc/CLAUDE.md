# cc-aca-sdlc

ACA SDLC plugin -- TDD enforcement gates, test-state tracking, implementation verification, completion gates, and development workflow discipline.

## Plugin Structure



## Hook Inventory

### PreToolUse (2 hooks)

| Hook | Purpose |
|------|---------|
| PreToolUse_tdd95_gate.py | TDD compliance gate -- requires tests before implementation |
| PreToolUse_tdd_contract_gate.py | TDD contract enforcement for code changes |

### PostToolUse (2 hooks)

| Hook | Purpose |
|------|---------|
| PostToolUse_tdd_state.py | TDD state tracking after tool execution |
| PostToolUse_tdd_state_tracker.py | Detailed test-state tracking for TDD cycle |

### Stop (3 hooks)

| Hook | Purpose |
|------|---------|
| StopHook_tdd_continuation.py | TDD cycle continuation -- enforces red-green-refactor loop |
| Stop_task_completion_gate.py | Task completion verification gate |
| Stop_ralph_loop.py | Ralph loop detection and prevention |

### Start (1 hook)

| Hook | Purpose |
|------|---------|
| preflight_require_tdd.py | Preflight check requiring TDD mode for implementation tasks |

## Module Classification

| Module | Location | Why |
|--------|----------|-----|
| hook_base.py | Global __lib__/ | 41+ consumers across all domains |
| skill_guard_path | Global __lib__/ | Cross-domain skill guard consumers |

No plugin-local modules needed -- all dependencies have cross-domain consumers.

## Compatibility Layer

Original hooks in P:/.claude/hooks/ are backed up as .pre-sdlc and replaced with compatibility wrappers that delegate to plugin hooks via importlib.util.

Wrappers use globals().update() re-export pattern to expose run() and main() for in-process and subprocess invocation.

## Bootstrap Pattern

All hooks use the 4-line bootstrap header placed after from __future__ import annotations and before regular imports.

## Domain Boundary

**SDLC owns:**
- TDD enforcement and compliance gates
- Test-state tracking through TDD cycles
- Implementation verification and completion gates
- Development workflow discipline (Ralph loop, task completion)
- Preflight TDD requirement checks

**NOT in this plugin:**
- Filesystem protection (cc-aca-safety)
- Git permission enforcement (cc-aca-authority)
- Observability/telemetry (cc-aca-observability)
- Reasoning quality (cc-aca-reasoning)
