---
doc_type: prd
tracks:
  - ".claude/hooks/*.py"
  - ".claude/settings.json"
  - ".claude/hooks/ARCHITECTURE.md"
significance:
  min_lines_changed: 5
sync_trigger: write
---

# Product Requirements Document: Claude Code Hooks

**Status:** Accepted
**Created:** 2026-01-13
**Version:** 1.1
**Purpose:** Document structural enforcement hooks for Claude Code

---

## Problem Statement

Claude Code's advisory documentation (CLAUDE.md) is not sufficient for enforcing behavioral rules. When advisory documentation conflicts with user requests, the AI may:

1. **Overcomplicate** solutions instead of reading existing code
2. **Cascade failures** trying the same fixes repeatedly
3. **Generate zombie code** through incomplete refactors
4. **Dismiss concerns** without proper investigation
5. **Claim success** without verification evidence
6. **Execute unparseable** commands (eval, exec, arbitrary code)
7. **Use complex shell** patterns that are hard to verify
8. **Make vague directives** without architecture first
9. **Violate constitutional** rules (CLAUDE.md constraints)

**Root Cause:** Advisory documentation can be ignored. There is no structural enforcement layer.

## Goals

1. **Deterministic Blocking:** Prevent specific harmful patterns before tool execution
2. **Evidence Requirements:** Require verification before success claims
3. **Context Preservation:** Track session state for intelligent gating
4. **Zero False Positives:** Never block legitimate work
5. **Constitutional Enforcement:** Enforce CLAUDE.md constraints structurally

## Requirements

### Core Functional Requirements

| ID | Requirement | Hook Type | Implementation |
|----|------------|-----------|----------------|
| **FR-001** | Block tool execution with clear reason | PreToolUse, Stop | All blocking hooks return `{continue: false, reason: "..."}` |
| **FR-002** | Track failures across session for Catch-22 detection | PostToolUse | `recursive_failure_detector.py` + `failure_recorder.py` |
| **FR-003** | Validate success claims before response completion | Stop | `stop_success_validator.py`, `StopHook_spec_compliance.py` |
| **FR-004** | Provide bypass mechanism | All | Declaration format: `"Investigation complete: ..."` or env var |
| **FR-005** | Log block events for analysis | All | `hook_tracker.py` shared infrastructure |

### Constitutional Requirements

| ID | Requirement | CLAUDE.md Section | Implementation |
|----|------------|-------------------|----------------|
| **FR-006** | Block complex shell patterns | J.5 | `shell_complexity_gate.py` |
| **FR-007** | Block unparseable/arbitrary code execution | C.1 | `unparseable_command_gate.py` |
| **FR-008** | Detect Catch-22 (recursive failure) | D.5 | `recursive_failure_detector.py` |
| **FR-009** | Gate vague directives with architecture | C.1 | `PreToolUse_vague_directive_gate.py` |
| **FR-010** | Enforce spec compliance | All | `StopHook_spec_compliance.py` |

### Non-Functional Requirements

| ID | Requirement | Target | Status |
|----|------------|--------|--------|
| **NFR-001** | Performance (Layer 0 timeout) | ≤3 seconds | ✓ Met |
| **NFR-002** | Reliability (exit code) | Always exit 0 | ✓ Met |
| **NFR-003** | Testable logic | Unit tests pass | ✓ Met |
| **NFR-004** | Solo-dev friendly | No enterprise infrastructure | ✓ Met |
| **NFR-005** | Documentation sync | Frontmatter-based | ✓ Met |

## Success Criteria

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Blocks overcomplication loops | ARCHITECTURE.md §Investigation Gate | ✓ Implemented |
| Detects Catch-22 scenarios | ARCHITECTURE.md §Companion Hook Pattern | ✓ Implemented |
| Validates success claims | ARCHITECTURE.md §Constitutional Hooks Table | ✓ Implemented |
| Constitutional enforcement | ARCHITECTURE.md §Constitutional Infrastructure | ✓ Implemented |
| Frontmatter sync tracking | All `*.md` have frontmatter | ✓ Implemented |
| Compatible with `/doc` | Frontmatter discovery | ✓ Ready |

*See [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details.*

## Implementation Timeline

See [CHANGELOG.md](CHANGELOG.md) for version history:

- **v2.0** (2026-01-13): Constitutional infrastructure + frontmatter sync
- **v1.0** (Earlier): Initial hook system

## Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Better prompting only | Zero overhead | Fundamentally advisory, can be ignored | Rejected |
| External guardrails | Language-agnostic | Separate system, sync issues | Rejected |
| Claude Code built-in | Deep integration | No control over implementation | Deferred |
| **Hooks system** | Structural enforcement, user-controlled | Requires maintenance | **Selected** |

## Rationale

Advisory documentation (CLAUDE.md) is necessary but not sufficient. The AI can ignore it when faced with conflicting directives. Hooks provide structural enforcement that cannot be bypassed without explicit user action.

The hooks system follows the principle: **"Make it easy to do the right thing, and hard to do the wrong thing."**

### Why Hooks Over Other Approaches

1. **User Control:** Hooks run locally, can be disabled via environment variables
2. **Explicit Bypass:** Declaration format allows intentional override
3. **Observable:** Block events are logged and reviewable
4. **Composable:** Multiple hooks can be layered for different concerns

---

*Last updated: 2026-01-13*
