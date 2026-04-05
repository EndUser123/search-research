#!/usr/bin/env python3
"""
TDD Diagnostics - Automatic problem detection and recovery guidance.

Runs after TDD blocks to detect problematic patterns and suggest fixes.
Proactively checks for known issues from archive/TDD_PROBLEMS_AND_FIXES.md
"""

import json
import sys
from collections import Counter
from datetime import datetime

from tdd_core import STATE_DIR, debug_log


class TDDDiagnostics:
    """Detects TDD problems and provides recovery guidance."""

    # Problem signatures and their fixes
    PROBLEMS = {
        "llm_ignores_gate": {
            "symptoms": [
                "Block followed by implementation in same session",
                "TDD Violation message immediately followed by code",
            ],
            "detection": "check_block_then_implement",
            "severity": "high",
            "fix_ref": "Problem 1 in archive/TDD_PROBLEMS_AND_FIXES.md",
            "fix_command": "cp P:/.claude/hooks/archive/PreToolUse_tdd_blocker.py P:/.claude/hooks/",
        },
        "stuck_in_awaiting_red": {
            "symptoms": [
                "Multiple consecutive blocks for same impl file",
                "Tests run but phase doesn't advance",
                "No state transition > 10 minutes",
            ],
            "detection": "check_stuck_phase",
            "severity": "high",
            "fix_ref": "Problem 2 in archive/TDD_PROBLEMS_AND_FIXES.md",
            "fix_hint": "Add TDD_BYPASS=1 to is_tdd_enabled() in tdd_core.py",
        },
        "state_corruption": {
            "symptoms": [
                "State file exists but invalid JSON",
                "Phase value is unknown/invalid",
                "Multiple active cycles for same test file",
            ],
            "detection": "check_state_corruption",
            "severity": "medium",
            "fix_ref": "Problem 2 - Manual reset in archive/TDD_PROBLEMS_AND_FIXES.md",
            "fix_command": "rm -rf P:/.claude/hooks/hooks/.state/tdd-state/",
        },
    }

    def __init__(self):
        self.detections = Counter()
        self.first_seen = {}
        self.alerts_issued = {}

    def log_event(self, event_type: str, details: dict | None = None):
        """Log a diagnostic event for pattern detection."""
        log_file = STATE_DIR / "tdd_diagnostics.jsonl"

        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().isoformat()
            entry = {
                "timestamp": timestamp,
                "event": event_type,
                "details": details or {},
            }
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
            debug_log(f"tdd_diagnostics: logged {event_type}")
        except OSError:
            pass

    def check_block_then_implement(self, recent_events: list) -> bool:
        """
        Problem 1: Check if LLM is ignoring gate blocks.

        Pattern: TDD Violation block → immediate implementation attempt
        """
        debug_log("tdd_diagnostics: checking block_then_implement")

        # Look for block followed by Write/Edit within 5 events
        for i, event in enumerate(recent_events):
            if event.get("event") == "tdd_block":
                # Check next few events for implementation
                for next_event in recent_events[i+1:i+5]:
                    if next_event.get("event") in ("write", "edit"):
                        tool = next_event.get("tool", "?")
                        file_path = next_event.get("file_path", "")
                        debug_log(f"tdd_diagnostics: FOUND block -> {tool} pattern")

                        # Check if this keeps happening
                        key = "llm_ignores_gate"
                        self.detections[key] += 1

                        if self.detections[key] >= 3:
                            return self._alert(key, {
                                "block_target": file_path,
                                "implement_tool": tool,
                                "count": self.detections[key],
                            })

        return False

    def check_stuck_phase(self) -> bool:
        """
        Problem 2: Check if stuck in AWAITING_RED.

        Pattern: Repeated blocks for same phase, no transitions
        """
        debug_log("tdd_diagnostics: checking stuck_phase")

        if not STATE_DIR.exists():
            return False

        # Check all state files
        for state_file in STATE_DIR.glob("tdd.*.json"):
            try:
                with open(state_file) as f:
                    state = json.load(f)

                phase = state.get("phase", "")
                created = state.get("created_at", "")
                updated = state.get("updated_at", "")

                if phase == "awaiting_red":
                    # Check how long it's been stuck
                    try:
                        if updated:
                            updated_time = datetime.fromisoformat(updated)
                            age_minutes = (datetime.now() - updated_time).total_seconds() / 60

                            # If stuck > 30 minutes, alert
                            if age_minutes > 30:
                                key = f"stuck_awaiting_red_{state_file.stem}"
                                if key not in self.alerts_issued:
                                    self.alerts_issued[key] = True
                                    return self._alert("stuck_in_awaiting_red", {
                                        "state_file": str(state_file),
                                        "age_minutes": int(age_minutes),
                                        "test_file": state.get("test_file"),
                                    })
                    except ValueError:
                        pass

            except (json.JSONDecodeError, OSError):
                self.log_event("state_corruption", {"file": str(state_file)})

        return False

    def check_state_corruption(self) -> bool:
        """
        Problem 3: Check for corrupted state files.

        Pattern: Invalid JSON, unknown phases, duplicate states
        """
        debug_log("tdd_diagnostics: checking state_corruption")

        if not STATE_DIR.exists():
            return False

        issues = []

        for state_file in STATE_DIR.glob("tdd.*.json"):
            try:
                with open(state_file) as f:
                    state = json.load(f)

                phase = state.get("phase", "")
                valid_phases = ["idle", "awaiting_red", "red_confirmed",
                               "green_confirmed", "refactoring"]

                if phase not in valid_phases:
                    issues.append(f"Invalid phase in {state_file.name}: {phase}")

            except (json.JSONDecodeError, OSError) as e:
                issues.append(f"Cannot read {state_file.name}: {e}")

        if issues:
            return self._alert("state_corruption", {"issues": issues})

        return False

    def _alert(self, problem_key: str, details: dict) -> bool:
        """Issue alert with recovery guidance."""
        problem = self.PROBLEMS.get(problem_key, {})

        alert = f"""
⚠️ TDD PROBLEM DETECTED: {problem_key.upper()}

{'=' * 60}

SYMPTOMS DETECTED:
{chr(10).join(f'  • {s}' for s in problem.get('symptoms', []))}

DETAILS:
{json.dumps(details, indent=2)}

RECOVERY:
  See: {problem.get('fix_ref', 'archive/TDD_PROBLEMS_AND_FIXES.md')}
"""

        if problem.get("fix_command"):
            alert += f"\nQUICK FIX:\n  {problem['fix_command']}"
        elif problem.get("fix_hint"):
            alert += f"\nFIX HINT:\n  {problem['fix_hint']}"

        alert += f"\n{'=' * 60}"

        # Print to stderr for visibility
        print(alert, file=sys.stderr)

        # Log the alert
        self.log_event(f"alert_{problem_key}", details)

        # Also write to alert file for easy checking
        alert_file = STATE_DIR / "tdd_alerts.log"
        try:
            with open(alert_file, "a") as f:
                f.write(f"\n{datetime.now().isoformat()} {problem_key}\n{alert}\n\n")
        except OSError:
            pass

        return True


def run_diagnostics() -> dict:
    """
    Run all TDD diagnostics and return results.

    Called by PostToolUse after TDD-related events.
    """
    diag = TDDDiagnostics()

    # Load recent events from diagnostics log
    log_file = STATE_DIR / "tdd_diagnostics.jsonl"
    recent_events = []

    if log_file.exists():
        try:
            with open(log_file) as f:
                lines = f.readlines()
                # Get last 100 events
                for line in lines[-100:]:
                    try:
                        recent_events.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass

    results = {
        "llm_ignores_gate": diag.check_block_then_implement(recent_events),
        "stuck_in_awaiting_red": diag.check_stuck_phase(),
        "state_corruption": diag.check_state_corruption(),
        "timestamp": datetime.now().isoformat(),
    }

    return results


def main():
    """CLI entry point for manual diagnostics."""
    print("TDD Diagnostics\n" + "=" * 40)

    results = run_diagnostics()

    problems_found = [k for k, v in results.items() if v is True]

    if problems_found:
        print(f"\nProblems detected: {', '.join(problems_found)}")
        print("\nCheck alerts log for details:")
        print(f"  cat {STATE_DIR / 'tdd_alerts.log'}")
    else:
        print("\nNo problems detected.")

    return 0 if not problems_found else 1


if __name__ == "__main__":
    sys.exit(main())
