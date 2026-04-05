# Implementation Plan: Test Adversarial Runner Markdown Summary Enhancement

**Status:** DRAFT
**Date:** 2026-03-17
**Objective:** Create and execute comprehensive test plan for TASK-004A markdown summary enhancement in adversarial_runner.py

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 | ⏳ PENDING | Create test plan document |
| Phase 2 | ⏸️ DEFERRED | Execute test suite (blocked by Phase 1) |
| Phase 3 | ⏸️ DEFERRED | Verify results and document (blocked by Phase 2) |

---

## Problem Statement

The TASK-004A markdown summary enhancement was implemented in `adversarial_runner.py` to add human-readable markdown summaries alongside JSON output. However, no end-to-end testing was performed to verify:

1. The markdown file is actually created
2. The markdown content is properly formatted
3. The JSON output includes `markdown_path` and `state_dir` fields
4. The `--show` flag still works for detailed findings
5. Multi-terminal isolation works correctly

**REQ-001**: Create test plan that covers all 5 test objectives
**REQ-002**: Execute tests and document results
**REQ-003**: Verify context efficiency (97% reduction maintained)
**REQ-004**: Validate markdown formatting and content quality

---

## Context Analysis

### Current Implementation

**File**: `P:\.claude\skills\plan-workflow\lib\adversarial_runner.py`

**Key Functions Added**:
- `markdown_summary(plan_path, summary)` - Generates formatted markdown from JSON summary
- `write_markdown_summary(plan_path, summary)` - Writes markdown to `.claude/hooks/plans/`
- Updated `main()` to call `write_markdown_summary()` and include paths in JSON output

**Expected Behavior**:
- Markdown file written to: `.claude/hooks/plans/<basename>-adversarial-summary.md`
- JSON output includes:
  - `markdown_path`: Path to generated markdown file
  - `state_dir`: Terminal-scoped state directory
- Markdown includes severity icons (🔴🟠🟡🟢), status, findings list, and instructions

### Multi-Terminal Constraints

- ✅ Markdown files written to shared location (`.claude/hooks/plans/`)
- ✅ State files remain terminal-scoped (`.claude/state/terminals/{terminal_id}/adversarial-reviews/`)
- ✅ No cross-terminal pollution in state files
- ⚠️ Markdown location is intentionally shared (for human review)

### Test Environment

**Python Version**: 3.12+
**Test Runner**: pytest or bash scripts
**Test Plan File**: Minimal test fixture (`.claude/hooks/plans/test-plan.md`)

---

## Existing Implementation Discovery

### Markdown Generation Code

```python
def markdown_summary(plan_path: str, summary: dict[str, Any]) -> str:
    """Generate Markdown summary from JSON summary."""
    plan_name = Path(plan_path).name
    lines = []

    lines.append(f"# Adversarial Review Summary: `{plan_name}`")
    lines.append("")
    lines.append(f"**Status:** {summary['status']}")
    lines.append(f"**Total Findings:** {summary['total_findings']}")
    lines.append(f"**High Severity:** {summary['high_findings']}")
    lines.append(f"**Shown:** {summary['shown_findings']} of {summary['total_findings']}")
    lines.append("")

    # ... formatting code with severity icons

    return "\n".join(lines)
```

### State Directory Management

```python
def get_state_dir() -> Path:
    """Get terminal-scoped state directory."""
    terminal_id = get_terminal_id()
    if terminal_id:
        return get_terminal_state_dir(terminal_id) / "adversarial-reviews"
    else:
        return ROOT / ".claude/state/adversarial-reviews"
```

**Terminal ID Source**: Environment variable or fallback detection

---

## Test Discovery

### Test Categories

| Test ID | Category | Description | Priority |
|---------|----------|-------------|----------|
| T-001 | JSON Field Verification | Verify JSON includes `markdown_path` and `state_dir` | HIGH |
| T-002 | File Creation | Verify markdown file is created at expected path | HIGH |
| T-003 | Content Validation | Verify markdown has proper formatting and structure | HIGH |
| T-004 | Show Flag | Verify `--show` flag retrieves agent details | MEDIUM |
| T-005 | Multi-Terminal Isolation | Verify state files go to terminal-specific directory | MEDIUM |
| T-006 | Context Efficiency | Verify context reduction (97% target maintained) | LOW |

### Test Gaps Identified

**Current State**:
- Syntax verified via `py_compile` (pass)
- No end-to-end execution tests
- No markdown content validation
- No multi-terminal isolation tests
- No context size measurements

---

## Proposed Solution

### Test Plan Approach

Create minimal test fixture and execute 5-point test suite:

**Point 1: Create Test Plan Fixture**
- Minimal markdown file with basic plan structure
- Location: `P:\.claude\hooks\plans\test-plan.md`

**Point 2: Run Runner in Light Mode**
- Execute: `python .claude/skills/plan-workflow/lib/adversarial_runner.py "test-plan.md" --mode=light`
- Capture stdout JSON output

**Point 3: Verify JSON Output**
- Check for `markdown_path` field
- Check for `state_dir` field
- Validate file paths are absolute and well-formed

**Point 4: Verify Markdown File**
- Check file exists at expected location
- Verify markdown structure (headers, status line, findings)
- Verify severity icons present
- Verify instructions section present

**Point 5: Test --show Flag**
- Execute: `python .claude/skills/plan-workflow/lib/adversarial_runner.py "test-plan.md" --show compliance`
- Verify agent-specific details returned

**Point 6: Test Multi-Terminal Isolation**
- Set `TERMINAL_ID` environment variable
- Verify state files go to terminal-specific directory
- Verify markdown file still created in shared location

---

## Implementation Plan

### TASK-001: Create Test Fixture

**File**: `P:\.claude\hooks\plans\test-plan.md`

**Content**:
```markdown
# Test Plan for Adversarial Runner

## Objective
Test fixture for TASK-004A markdown summary enhancement.

## Requirements
- REQ-001: Markdown generation works
- REQ-002: JSON output includes new fields
- REQ-003: Context efficiency maintained

## Implementation Status
- Phase 1: Complete
- Phase 2: Pending
```

**Acceptance Criteria**:
- [ ] File created at correct path
- [ ] Valid markdown format
- [ ] Contains test objective and requirements

**Prerequisites**: None
**Effort**: 1 (Trivial)

---

### TASK-002: Create Test Script

**File**: `P:\.claude\skills\plan-workflow\tests\test_markdown_summary.py`

**Content**:
```python
#!/usr/bin/env python3
"""Test adversarial runner markdown summary enhancement."""

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add parent directories for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[3]  # -> P:/
RUNNER = ROOT / ".claude/skills/plan-workflow/lib/adversarial_runner.py"


def test_json_output_fields():
    """T-001: Verify JSON includes markdown_path and state_dir fields."""
    with TemporaryDirectory() as tmpdir:
        test_plan = Path(tmpdir) / "test-plan.md"
        test_plan.write_text("# Test Plan\n\n## Objective\nTest fixture.\n")

        result = subprocess.run(
            [sys.executable, str(RUNNER), str(test_plan), "--mode=light"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Runner failed: {result.stderr}"

        output = json.loads(result.stdout)
        assert "markdown_path" in output, "Missing markdown_path field"
        assert "state_dir" in output, "Missing state_dir field"

        md_path = Path(output["markdown_path"])
        assert md_path.exists(), f"Markdown file not found: {md_path}"
        assert md_path.name == "test-plan-adversarial-summary.md"

        state_dir = Path(output["state_dir"])
        assert "adversarial-reviews" in str(state_dir), "State directory path wrong"

    print("✓ T-001: JSON output fields verified")


def test_markdown_content():
    """T-003: Verify markdown has proper formatting and structure."""
    with TemporaryDirectory() as tmpdir:
        test_plan = Path(tmpdir) / "test-plan.md"
        test_plan.write_text("# Test Plan\n\n## Objective\nTest fixture.\n")

        subprocess.run(
            [sys.executable, str(RUNNER), str(test_plan), "--mode=light"],
            cwd=str(ROOT),
            capture_output=True,
        )

        md_path = ROOT / ".claude/hooks/plans/test-plan-adversarial-summary.md"
        content = md_path.read_text()

        # Check for required sections
        assert "# Adversarial Review Summary:" in content
        assert "**Status:**" in content
        assert "**Total Findings:**" in content
        assert "## Findings" in content or "## Agent Errors" in content
        assert "## Detailed Reports" in content
        assert "python .claude/skills/plan-workflow/lib/adversarial_runner.py" in content

        # Check for severity icons
        severity_icons = ["🔴", "🟠", "🟡", "🟢"]
        assert any(icon in content for icon in severity_icons), "Missing severity icons"

    print("✓ T-003: Markdown content verified")


def test_show_flag():
    """T-004: Verify --show flag retrieves agent details."""
    with TemporaryDirectory() as tmpdir:
        test_plan = Path(tmpdir) / "test-plan.md"
        test_plan.write_text("# Test Plan\n\n## Objective\nTest fixture.\n")

        result = subprocess.run(
            [sys.executable, str(RUNNER), str(test_plan), "--show", "compliance"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"--show failed: {result.stderr}"

        output = json.loads(result.stdout)
        assert output["agent"] == "adversarial-compliance" or output["agent"] == "compliance"
        assert "findings" in output or "error" in output

    print("✓ T-004: --show flag verified")


def test_multi_terminal_isolation():
    """T-005: Verify state files go to terminal-specific directory."""
    import os

    with TemporaryDirectory() as tmpdir:
        test_plan = Path(tmpdir) / "test-plan.md"
        test_plan.write_text("# Test Plan\n\n## Objective\nTest fixture.\n")

        # Set terminal ID
        os.environ["TERMINAL_ID"] = "test_terminal_123"

        try:
            result = subprocess.run(
                [sys.executable, str(RUNNER), str(test_plan), "--mode=light"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Runner failed: {result.stderr}"

            output = json.loads(result.stdout)
            state_dir = Path(output["state_dir"])

            # Verify terminal ID in path
            assert "test_terminal_123" in str(state_dir), f"Terminal ID not in path: {state_dir}"

            # Verify state directory exists
            assert state_dir.exists(), f"State directory not found: {state_dir}"

            # Verify agent state files exist
            agent_files = list(state_dir.glob("*.json"))
            assert len(agent_files) > 0, f"No agent state files found in: {state_dir}"

        finally:
            # Clean up environment
            os.environ.pop("TERMINAL_ID", None)

    print("✓ T-005: Multi-terminal isolation verified")


if __name__ == "__main__":
    print("Running adversarial runner markdown summary tests...")
    test_json_output_fields()
    test_markdown_content()
    test_show_flag()
    test_multi_terminal_isolation()
    print("\n✅ All tests passed!")
```

**Acceptance Criteria**:
- [ ] Test script created
- [ ] All 5 test functions implemented
- [ ] Tests use temporary directories for isolation
- [ ] Cleanup after each test

**Prerequisites**: TASK-001
**Effort**: 3 (Moderate)

---

### TASK-003: Execute Test Suite

**Action**: Run test script and capture results

**Command**:
```bash
python .claude/skills/plan-workflow/tests/test_markdown_summary.py
```

**Acceptance Criteria**:
- [ ] All 4 test functions pass
- [ ] No assertion errors
- [ ] Output shows verification ticks

**Prerequisites**: TASK-002
**Effort**: 2 (Simple)

---

### TASK-004: Document Results

**File**: `P:\.claudehooks\plans\test-plan-adversarial-summary-test-results.md`

**Content**:
```markdown
# Test Results: Adversarial Runner Markdown Summary

**Date:** 2026-03-17
**Tester:** Claude (via test_markdown_summary.py)

## Test Summary

| Test ID | Status | Result | Notes |
|---------|--------|--------|-------|
| T-001 | PASS | ✓ | JSON fields verified |
| T-003 | PASS | ✓ | Markdown content verified |
| T-004 | PASS | ✓ | --show flag verified |
| T-005 | PASS | ✓ | Multi-terminal isolation verified |

## Context Efficiency

**Target**: 97% reduction (30KB → 1KB)
**Actual**: To be measured

## Conclusion

The markdown summary enhancement (TASK-004A) is working as designed:
- Markdown files generated correctly
- JSON output includes new fields
- Show flag functionality preserved
- Multi-terminal isolation working

## Recommendations

1. Add test to CI/CD pipeline
2. Create permanent test fixture instead of temporary files
3. Add performance regression test for context size
```

**Acceptance Criteria**:
- [ ] Results document created
- [ ] All test outcomes documented
- [ ] Context efficiency measured
- [ ] Recommendations documented

**Prerequisites**: TASK-003
**Effort**: 1 (Trivial)

---

## Risks, Success Criteria, Dependencies

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test fixture incompatible with agents | LOW | MEDIUM | Use minimal valid plan structure |
| Terminal ID detection fails on Windows | MEDIUM | HIGH | Test both with and without TERMINAL_ID |
| Markdown file conflicts between tests | LOW | LOW | Use unique test plan names |
| State directory cleanup issues | LOW | LOW | Clean up after each test |

### Success Criteria

**All tasks complete when:**
- [ ] Test script executes without errors
- [ ] All 4 test assertions pass
- [ ] Markdown file generated with proper formatting
- [ ] JSON output includes required fields
- [ ] Multi-terminal isolation verified
- [ ] Results documented in markdown file

### Dependencies

**External Dependencies:**
- Python 3.12+ subprocess module
- `get_terminal_id()` function from `__lib/runtime_env`
- `get_terminal_state_dir()` function from `__lib/state_paths`

**Internal Dependencies:**
- `adversarial_runner.py` (implementation under test)
- Agent scripts in `.claude/skills/plan-workflow/agents/`

**Blocked By:** None

### Rollback Strategy

If tests fail:
1. Investigate failure mode (syntax, path, isolation)
2. Fix implementation or adjust test expectations
3. Re-run tests until pass
4. Update ADR or implementation plan with findings

---

## Next Actions

1. Execute test plan:
   ```bash
   python P:\.claude\skills\plan-workflow\tests\test_markdown_summary.py
   ```

2. Verify results document created

3. Update implementation plan with test results

4. Add tests to regular test suite if passing
