# /verify - Verification Orchestrator

**Unified 4-tier verification workflow with deep analysis modes**

## Overview

`/verify` provides systematic verification for skills, hooks, and features by running four tiers of checks:

1. **Tier 0 (Checklist)**: Fast-fail structured verification (NEW)
2. **Tier 1 (Component)**: Unit tests (pytest)
3. **Tier 2 (Integration)**: Hook/router integration with optional 6-lens deep analysis
4. **Tier 3 (E2E)**: Actual skill/workflow invocation with optional full state verification

**Core Principle**: **Verify before you trust.** All four tiers must pass for "verified" status.

## Installation

The skill is located at:
```
P:/.claude/skills/verify/
```

No additional installation required - uses existing dependencies:
- pytest (Tier 1)
- evidence_store.py (from TASK-000)
- PostToolUse_e2e_tracker.py (from TASK-003)

## Usage

### Basic Usage

```bash
# Verify a skill
python P:/.claude/skills/verify/__main__.py "skill:arch"

# Verify a hook
python P:/.claude/skills/verify/__main__.py "hook:breadcrumb_init"

# Verify a feature
python P:/.claude/skills/verify/__main__.py "feature:e2e"

# Auto-detect target type
python P:/.claude/skills/verify/__main__.py "arch"              # Detects: skill
python P:/.claude/skills/verify/__main__.py "src/handoff.py"    # Detects: code
```

### Advanced Usage

```bash
# Specify session ID for E2E tracking
python __main__.py "skill:arch" --session-id "my-session-123"

# JSON output format
python __main__.py "skill:arch" --output json

# Verbose mode (show detailed evidence)
python __main__.py "skill:arch" --verbose
```

### Advanced Verification Flags (NEW)

**Deep Lens Analysis** (`--deep-lens`):
```bash
# 6-lens code review (State/Edge-Case, Identity/Invariants, I/O, Concurrency, Errors, Tests)
python __main__.py "skill:code" --deep-lens
```

**Adversarial Review** (`--adversarial`):
```bash
# 9-agent stress testing (7 specialized agents + meta-analyst)
python __main__.py "skill:arch" --adversarial
```

**Full State Verification** (`--full-state`):
```bash
# Source→Logic→Read verification (separate read operation protocol)
python __main__.py "skill:code" --full-state --expected-files file1.py,file2.py
```

**Combined Modes**:
```bash
# Deep lens + adversarial review
python __main__.py "skill:arch" --deep-lens --adversarial

# Deep lens + full state verification
python __main__.py "skill:code" --deep-lens --full-state --expected-files src/main.py

# All three modes (most comprehensive)
python __main__.py "hook:init" --deep-lens --adversarial --full-state
```

**Performance Expectations**:
- Standard 4-tier: ~5-15 seconds
- With --deep-lens: ~10-20 seconds
- With --adversarial: ~30-60 seconds
- With --full-state: ~5-10 seconds additional

## Output Format

### Markdown Report (default)

```markdown
[VERIFY] Verification Report

**Target**: skill:arch
**Date**: 2026-03-10T10:00:00
**Verification ID**: 12345678-1234-1234-1234-123456789abc

## Overall Status
**Overall Status**: ✅ VERIFIED

**TIER1**: ✅ PASS
**TIER2**: ✅ PASS
**TIER3**: ✅ PASS

## Tier Evidence

### TIER1
**Status**: pass
**Evidence**:
```
tests/test_arch.py::test_arch_activation PASSED
tests/test_arch.py::test_arch_intent PASSED
2 passed in 0.15s
```
**Command**: `pytest tests/test_arch.py -v`

### TIER2
**Status**: pass
**Evidence**:
```
Skill file exists: P:/.claude/skills/arch/SKILL.md
```

### TIER3
**Status**: pass
**Evidence**:
```
Skill invocation found: arch
```
```

### JSON Report

```json
{
  "verification_id": "12345678-1234-1234-1234-123456789abc",
  "target": "skill:arch",
  "target_type": "skill",
  "target_name": "arch",
  "overall_status": "verified",
  "tier1": {
    "status": "pass",
    "evidence": "2 passed...",
    "command": "pytest tests/test_arch.py -v"
  },
  "tier2": {
    "status": "pass",
    "evidence": "Skill file exists..."
  },
  "tier3": {
    "status": "pass",
    "evidence": "Skill invocation found..."
  }
}
```

## Tier Details

### Tier 0: Checklist Verification (NEW)

**What**: Fast-fail structured verification using checklists

**How**: Runs checklist verification based on target type (skill/hook/feature)

**Evidence**: Checklist items checked, items passed, findings

**Exit codes**: 0 = pass, 1 = fail

**Fast-fail**: If Tier 0 fails, remaining tiers are skipped

### Tier 1: Component Tests

**What**: Unit tests for the target component

**How**: Runs pytest with appropriate selectors

**Evidence**: Test output showing pass/fail counts

**Exit codes**: 0 = pass, 1 = fail

### Tier 2: Integration Check

**What**: Verify hook/router integration works

**How**:
- Check hook registration in router files
- Verify hook file exists
- Test hook chain execution (if applicable)

**Evidence**: Hook registration status, file existence

**Skip conditions**: Non-hook targets (code, features)

### Tier 3: E2E Test

**What**: Verify actual skill/workflow invocation

**How**: Query evidence_store for tool events

**Evidence**: Skill/tool invocation from current session

**Skip conditions**:
- No session_id provided
- Tier 1 or Tier 2 failed
- evidence_store not available

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tiers passed (verified) |
| 1 | One or more tiers failed |
| 2 | Invalid target format |
| 130 | Interrupted by user (Ctrl+C) |

## Integration with Existing Systems

### Dependencies

- **TASK-000**: evidence_store.py (session-scoped tool events)
- **TASK-002**: StopHook_unverified_stance.py (completion claim verification)
- **TASK-003**: PostToolUse_e2e_tracker.py (workflow tracking)

### Related Skills

- **/trace**: Deep manual verification (delegates for complex cases)
- **/testing-skills**: Skill QA (delegates for skill validation)

## Testing

Run the test suite:

```bash
cd P:/.claude/skills/verify
pytest tests/test_verify.py -v
```

Test coverage includes:
- Target detection (skill, hook, code, feature)
- Tier 1 execution (pass/fail/skip)
- Tier 2 integration checks
- Tier 3 E2E evidence lookup
- Full verification workflow (all tiers)
- Report generation (markdown, JSON)
- Real skill/hook verification (integration tests)

## Architecture

```
verify/
├── SKILL.md              # Skill definition
├── README.md             # This file
├── __main__.py           # Entry point (CLI)
├── core/
│   ├── __init__.py
│   ├── verifier.py       # Verification orchestrator
│   └── state_manager.py  # Multi-terminal state isolation
├── tiers/
│   ├── __init__.py
│   ├── tier0_checklist.py   # Checklist verification (FAST-FAIL)
│   ├── tier1_component.py   # Component tests
│   ├── tier2_integration.py  # Integration checks
│   ├── tier3_e2e.py          # E2E verification
│   ├── deep_lens_verifier.py # 6-lens code review (NEW)
│   ├── full_state_verifier.py # Source→Logic→Read verification (NEW)
│   ├── adversarial_coordinator.py # 9-agent adversarial review (NEW)
│   └── tests/
│       ├── test_full_state_verifier.py
│       └── test_deep_lens_verifier.py
└── tests/
    ├── __init__.py
    └── test_verify.py    # Test suite
```

## New Components (v2.0)

### Deep Lens Verifier
- 6-lens code review framework
- Lenses: State/Edge-Case, Identity/Invariants, I/O, Concurrency, Errors, Tests
- Integrated into Tier 2 with `--deep-lens` flag

### Full State Verifier
- Source→Logic→Read verification protocol
- Prevents assumptions about correct writes without verification
- Integrated into Tier 3 with `--full-state` flag

### Adversarial Coordinator
- 9-agent stress testing (7 specialized + 1 meta-analyst)
- Parallel dispatch pattern for efficiency
- Result envelope pattern for context management
- Integrated with `--adversarial` flag

## Version History

- **v1.0.0** (2026-03-10): Initial release
  - 3-tier verification workflow
  - Evidence-based reporting
  - Integration with TASK-000/002/003 components
  - TDD approach with comprehensive tests

## License

Part of the Cognitive Steering Framework (CSF) project.
