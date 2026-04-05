# Exit Criteria Validation Reference (Step 4.5)

**CRITICAL ENFORCEMENT**: This step runs ACTUAL verification commands to validate exit criteria BEFORE trusting the phase's self-reported PHASE_RESULT. This prevents phases from incorrectly reporting PASS when criteria aren't met.

**Purpose**: Independent verification of exit criteria using real commands, not phase self-reporting.

**When to run**: After EVERY phase completes (P1-P5), before parsing PHASE_RESULT.

## Validation Functions

```python
import subprocess
import re
from pathlib import Path

def validate_p1_exit_criteria(target: str, flags: list[str]) -> tuple[bool, list[str]]:
    """
    Validates P1 exit criteria by running actual verification commands.

    Exit Criteria from phases/p1.md:
    - [ ] All existing tests pass
    - [ ] New tests cover core logic paths
    - [ ] Known bugs are fixed with regression tests
    - [ ] `/test` shows no critical gaps
    - [ ] TestQualityDetector shows no high-severity issues (empty_test, no_assertions)

    Args:
        target: The file/directory being validated
        flags: Active flags (e.g., --publish, --force)

    Returns:
        (passed, violations): passed=False means HALT immediately
    """
    violations = []

    # Check 1: All existing tests pass (CRITICAL - always blocking)
    try:
        result = subprocess.run(
            ["pytest", target, "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            match = re.search(r'(\d+) failed', result.stdout)
            if match:
                failed = int(match.group(1))
                violations.append(f"Exit criteria violated: {failed} tests failing")
        else:
            if "failed" in result.stdout:
                match = re.search(r'(\d+) failed', result.stdout)
                if match:
                    violations.append(f"Exit criteria violated: {match.group(1)} tests failing")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        violations.append(f"Cannot verify test results: {e}")

    # Check 2: Coverage adequate (HIGH - blocking with --publish)
    # For now, skip coverage check in validation (requires pytest-cov setup)

    # Check 3: TestQualityDetector (HIGH - always blocking)
    try:
        import sys
        commands_path = Path(__file__).parent.parent.parent / "skills" / "p" / "lib"
        if commands_path.exists():
            sys.path.insert(0, str(commands_path))
            from commands.duplicates import TestQualityDetector

            detector = TestQualityDetector()
            issues = detector.scan(Path(target))

            high_severity = [i for i in issues if i.severity in ['critical', 'high']]
            if high_severity:
                violations.append(f"Test quality issues: {len(high_severity)} high-severity (empty_test, no_assertions)")
    except (ImportError, ModuleNotFoundError):
        pass

    return (len(violations) == 0, violations)


def validate_p2_exit_criteria(target: str, flags: list[str]) -> tuple[bool, list[str]]:
    """Validates P2 exit criteria."""
    violations = []

    from hooks.terminal_detection import detect_terminal_id
    terminal_id = detect_terminal_id()
    findings_file = Path(f".claude/findings/adversarial-review-{terminal_id}.json")
    if findings_file.exists():
        import json
        with open(findings_file) as f:
            findings = json.load(f)

        critical = sum(1 for f in findings if f.get("severity") == "CRITICAL")
        high = sum(1 for f in findings if f.get("severity") == "HIGH")

        if critical > 0 or high > 0:
            violations.append(f"Blocking findings remain: {critical} CRITICAL, {high} HIGH")

    return (len(violations) == 0, violations)


def validate_p3_exit_criteria(target: str, flags: list[str]) -> tuple[bool, list[str]]:
    """Validates P3 exit criteria."""
    violations = []

    validation_marker = Path(".claude/state/validation-complete.marker")
    if not validation_marker.exists():
        violations.append("Validation not complete: blocking stages failed")

    return (len(violations) == 0, violations)


def validate_p4_exit_criteria(target: str, flags: list[str]) -> tuple[bool, list[str]]:
    """P4 generates documentation - no blocking validation."""
    return (True, [])


def validate_p5_exit_criteria(target: str, flags: list[str]) -> tuple[bool, list[str]]:
    """P5 certification - no blocking validation."""
    return (True, [])


# Phase dispatcher
def validate_phase_exit_criteria(phase: int, target: str, flags: list[str]) -> tuple[bool, list[str]]:
    """
    Dispatches to appropriate validation function based on phase number.

    Args:
        phase: Phase number (1-5)
        target: File/directory being validated
        flags: Active flags from command line

    Returns:
        (passed, violations): passed=False means HALT
    """
    validators = {
        1: validate_p1_exit_criteria,
        2: validate_p2_exit_criteria,
        3: validate_p3_exit_criteria,
        4: validate_p4_exit_criteria,
        5: validate_p5_exit_criteria,
    }

    validator = validators.get(phase)
    if validator:
        return validator(target, flags)

    return (True, [])
```

## Integration into Workflow

```python
# After Step 4 (phase subagent completes), BEFORE parsing PHASE_RESULT:

# Step 4.5: Validate Exit Criteria
if "--force" not in flags:
    passed, violations = validate_phase_exit_criteria(phase, target, flags)

    if not passed:
        print("## Pipeline Status: HALTED")
        print(f"**Status:** HALTED at Phase {phase}")
        print(f"**Reason:** Exit criteria validation failed")
        print(f"**Violations:**")
        for violation in violations:
            print(f"  - {violation}")
        print()
        print("### Action Required")
        print("Exit criteria must be satisfied before phase can complete.")
        print("Fix the issues above, then re-run `/p` to continue.")
        print()
        print("**Note:** Use `/p --force` to bypass validation (not recommended).")
        return  # Exit /p execution
    else:
        from pathlib import Path
        from datetime import datetime
        state_dir = Path(".claude/state")
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_file = state_dir / f"p{phase}-complete.marker"
        timestamp = datetime.now().isoformat()
        marker_file.write_text(f"Phase {phase} completed at {timestamp}\n")

        if phase == 3:
            validation_marker = state_dir / "validation-complete.marker"
            validation_marker.write_text(f"Validation completed at {timestamp}\n")

        import sys
        print(f"Created phase marker: {marker_file}", file=sys.stderr)
else:
    print("**WARNING:** --force flag set - bypassing exit criteria validation")
```

## Why This Matters

The original `/p` design relied on LLM honesty to verify exit criteria. In the session context, this led to reporting PASS with 3 failing tests - violating exit criterion #1. This automated validation runs actual commands (pytest, TestQualityDetector) to independently verify criteria before allowing phase completion.

**Bypass Option**: Use `--force` flag only in emergencies (e.g., to continue after fixing a false-positive blocking issue).
