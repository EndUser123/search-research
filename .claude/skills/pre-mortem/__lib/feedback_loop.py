"""Pre-mortem feedback loop for tracking predictions vs outcomes.

Stores pre-mortem predictions in memory and validates them against actual
outcomes to create a learning system.
"""

from __future__ import annotations

import json
import os
import re
import sys as _sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# GTO skill coverage for GTO session tracking
_gto_lib = Path("P:/.claude/skills")
if str(_gto_lib) not in _sys.path:
    _sys.path.insert(0, str(_gto_lib))
from gto.lib.skill_coverage_detector import _append_skill_coverage  # type: ignore[attr-defined]


def sanitize_project_name(project: str) -> str:
    """Sanitize project name for safe filename usage.

    Prevents CWE-22 path traversal by removing all characters except
    alphanumeric, underscore, and hyphen. Limits length to 50 chars.

    Args:
        project: Raw project name or identifier

    Returns:
        Sanitized project name safe for use in filenames
    """
    # Remove all characters except a-z, A-Z, 0-9, underscore, hyphen
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", project)
    # Limit length to prevent filename issues
    return sanitized[:50] if sanitized else "unnamed"


def _get_terminal_id() -> str:
    """Get terminal ID for session isolation.

    Uses skill_guard's terminal detection (same as handoff system) to ensure
    consistent terminal identification across the system. Terminal ID is stable
    across compactions within the same terminal session.

    Returns:
        Terminal identifier string.
    """
    try:
        import hashlib

        # skill_guard is at P:/packages/skill-guard/src
        skill_guard_root = Path(__file__).parent.parent.parent / "packages" / "skill-guard" / "src"
        if str(skill_guard_root) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(skill_guard_root))
        from skill_guard.utils.terminal_detection import detect_terminal_id

        return detect_terminal_id()
    except Exception:
        # Fallback: use a hash of the memory dir path for process isolation
        return (
            "fallback_"
            + str(os.getpid())
            + "_"
            + hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:4]
        )


class PreMortemFeedbackLoop:
    """Manages pre-mortem prediction storage and outcome validation."""

    def __init__(self, memory_dir: Path | None = None):
        """Initialize feedback loop with memory directory.

        Args:
            memory_dir: Directory for storing pre-mortem records. Defaults to
                       ~/.claude/projects/P--/memory/premortem/
        """
        if memory_dir is None:
            memory_dir = Path.cwd() / ".claude" / "memory" / "premortem"

        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def store_prediction(
        self,
        project: str,
        predictions: list[dict[str, Any]],
        kill_criteria: list[dict[str, Any]],
        terminal_id: str | None = None,
    ) -> Path:
        """Store pre-mortem predictions for later validation.

        Args:
            project: Project name or identifier
            predictions: List of risk predictions with mitigations
            kill_criteria: List of abandonment criteria

        Returns:
            Path to stored prediction file
        """
        timestamp = datetime.now().isoformat()
        safe_project = sanitize_project_name(project)

        # Multi-terminal safety: use provided terminal_id or process ID
        # This prevents filename collisions when multiple terminals run concurrently
        terminal_suffix = terminal_id or f"pid{os.getpid()}"
        filename = f"premortem_{safe_project}_{terminal_suffix}_{timestamp.replace(':', '-')}.md"
        filepath = self.memory_dir / filename

        content = f"""# Pre-Mortem: {project}

**Date**: {timestamp}
**Status**: PENDING VALIDATION

## Kill Criteria

{self._format_kill_criteria(kill_criteria)}

## Predictions

{self._format_predictions(predictions)}

## Validation Status

**Status**: PENDING
**Next Review**: {(datetime.now() + timedelta(days=30)).isoformat()}

To validate this pre-mortem:
1. Check if any predicted failures occurred
2. Check if mitigations prevented predicted failures
3. Identify missed predictions (false negatives)
4. Document lessons learned for future pre-mortems
"""

        # Write with restrictive permissions (0o600 = owner read/write only)
        # On Windows, use os.chmod after write; on Unix, use mode parameter
        filepath.write_text(content, encoding="utf-8")
        filepath.chmod(0o600)  # owner read/write only

        # Log skill coverage for GTO session tracking (best-effort)
        try:
            tid = _get_terminal_id()
            _append_skill_coverage(
                target_key=str(filepath),
                skill="/pre-mortem",
                terminal_id=tid,
                git_sha=None,
            )
        except Exception:
            pass  # best-effort

        return filepath

    def _format_kill_criteria(self, criteria: list[dict[str, Any]]) -> str:
        """Format kill criteria for markdown output."""
        if not criteria:
            return "No kill criteria defined."

        lines = []
        for i, criterion in enumerate(criteria, 1):
            lines.append(
                f"{i}. **{criterion.get('type', 'Unknown')}**: {criterion.get('description', '')}"
            )
            if "threshold" in criterion:
                lines.append(f"   - Threshold: {criterion['threshold']}")
        return "\n".join(lines)

    def _format_predictions(self, predictions: list[dict[str, Any]]) -> str:
        """Format predictions for markdown output."""
        if not predictions:
            return "No predictions defined."

        lines = []
        for i, pred in enumerate(predictions, 1):
            risk_score = pred.get("risk_score", 0)
            description = pred.get("description", "")
            mitigation = pred.get("mitigation", "No mitigation specified")

            emoji = "🔴" if risk_score >= 9 else "🟡" if risk_score >= 6 else "🟢"

            lines.append(f"{emoji} **RISK:{risk_score}** - {description}")
            lines.append(f"   - **Mitigation**: {mitigation}")
            lines.append("   - **Status**: PENDING VALIDATION")
            lines.append("")

        return "\n".join(lines)

    def validate_prediction(
        self, prediction_file: Path, actual_outcomes: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate a pre-mortem prediction against actual outcomes.

        Args:
            prediction_file: Path to stored prediction file
            actual_outcomes: Dictionary of actual outcomes

        Returns:
            Validation results with accuracy metrics
        """
        content = prediction_file.read_text(encoding="utf-8")

        # Parse predictions from file
        predictions = self._parse_predictions_from_file(content)

        # Calculate accuracy metrics
        total_predictions = len(predictions)
        correct_predictions = 0
        missed_failures = 0
        false_alarms = 0

        validation_results = []

        for pred in predictions:
            risk_desc = pred["description"]
            predicted_likely = pred.get("risk_score", 0) >= 6

            # Check if this risk actually occurred
            actually_occurred = self._check_if_risk_occurred(risk_desc, actual_outcomes)

            if actually_occurred and predicted_likely:
                correct_predictions += 1
                validation_results.append(
                    {
                        "risk": risk_desc,
                        "status": "CORRECT",
                        "predicted": True,
                        "actual": True,
                    }
                )
            elif not actually_occurred and not predicted_likely:
                correct_predictions += 1
                validation_results.append(
                    {
                        "risk": risk_desc,
                        "status": "CORRECT (negative)",
                        "predicted": False,
                        "actual": False,
                    }
                )
            elif actually_occurred and not predicted_likely:
                missed_failures += 1
                validation_results.append(
                    {
                        "risk": risk_desc,
                        "status": "MISSED (false negative)",
                        "predicted": False,
                        "actual": True,
                    }
                )
            else:
                false_alarms += 1
                validation_results.append(
                    {
                        "risk": risk_desc,
                        "status": "FALSE ALARM (false positive)",
                        "predicted": True,
                        "actual": False,
                    }
                )

        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0

        results = {
            "accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "missed_failures": missed_failures,
            "false_alarms": false_alarms,
            "total_predictions": total_predictions,
            "validation_results": validation_results,
        }

        # Update prediction file with validation results
        self._update_prediction_with_validation(prediction_file, results)

        return results

    def _parse_predictions_from_file(self, content: str) -> list[dict[str, Any]]:
        """Parse predictions from stored markdown file."""
        predictions = []
        current_prediction = None

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Match prediction lines: 🔴 **RISK:9** - Description
            if line.startswith("🔴") or line.startswith("🟡") or line.startswith("🟢"):
                if "RISK:" in line:
                    # Extract risk score and description
                    import re

                    match = re.search(r"RISK:(\d+).*?-\s*(.+)", line)
                    if match:
                        risk_score = int(match.group(1))
                        description = match.group(2).strip()
                        current_prediction = {
                            "risk_score": risk_score,
                            "description": description,
                        }
                        predictions.append(current_prediction)

            # Match mitigation lines: - **Mitigation**: Action
            elif line.startswith("-") and "Mitigation" in line and current_prediction:
                # Handle both "Mitigation:" and "**Mitigation**:" formats
                if "**Mitigation**:" in line:
                    mitigation = line.split("**Mitigation**:", 1)[1].strip()
                elif "Mitigation:" in line:
                    mitigation = line.split("Mitigation:", 1)[1].strip()
                else:
                    mitigation = "No mitigation specified"
                current_prediction["mitigation"] = mitigation

        return predictions

    def _check_if_risk_occurred(self, risk_desc: str, actual_outcomes: dict[str, Any]) -> bool:
        """Check if a predicted risk actually occurred.

        This is a simple heuristic-based implementation. In production,
        this would need more sophisticated matching or manual review.
        """
        # Check for keyword matches in outcomes
        outcomes_text = json.dumps(actual_outcomes).lower()
        risk_keywords = risk_desc.lower().split()

        # Simple keyword matching (could be improved with NLP)
        match_count = sum(1 for keyword in risk_keywords if keyword in outcomes_text)
        return match_count >= len(risk_keywords) / 2  # At least 50% keyword match

    def _update_prediction_with_validation(
        self, prediction_file: Path, results: dict[str, Any]
    ) -> None:
        """Update prediction file with validation results."""
        content = prediction_file.read_text(encoding="utf-8")

        validation_section = f"""

## Validation Results (validated {datetime.now().isoformat()})

**Accuracy**: {results["accuracy"]:.1%}
**Correct Predictions**: {results["correct_predictions"]}/{results["total_predictions"]}
**Missed Failures**: {results["missed_failures"]}
**False Alarms**: {results["false_alarms"]}

### Detailed Results

"""

        for result in results["validation_results"]:
            status_emoji = "✅" if "CORRECT" in result["status"] else "❌"
            validation_section += f"{status_emoji} **{result['status']}**: {result['risk']}\n"

        # Update status from PENDING to VALIDATED
        content = content.replace("**Status**: PENDING", "**Status**: VALIDATED")

        # Append validation section before the file ends
        updated_content = content + validation_section

        prediction_file.write_text(updated_content, encoding="utf-8")

    def get_pending_validations(self, days_threshold: int = 30) -> list[Path]:
        """Get pre-mortems pending validation that are older than threshold.

        Args:
            days_threshold: Number of days after which to prompt for validation

        Returns:
            List of prediction files pending validation
        """
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        pending_files = []

        for filepath in self.memory_dir.glob("premortem_*.md"):
            # Extract timestamp from filename
            try:
                parts = filepath.stem.split("_")
                if len(parts) >= 3:
                    # Filename format: premortem_{project}_YYYY-MM-DDTHH-MM-SS.ffffff
                    # We need to convert dashes to colons ONLY in the time portion (after T)
                    timestamp_str = parts[-1]
                    if "T" in timestamp_str:
                        # Split at T, replace dashes with colons in time portion only
                        date_part, time_part = timestamp_str.split("T", 1)
                        time_part = time_part.replace("-", ":")
                        date_str = f"{date_part}T{time_part}"
                    else:
                        # Fallback: try parsing as-is
                        date_str = timestamp_str
                    file_date = datetime.fromisoformat(date_str)

                    if file_date < threshold_date:
                        # Check if still pending
                        content = filepath.read_text(encoding="utf-8")
                        if "PENDING" in content:
                            pending_files.append(filepath)
            except (ValueError, IndexError):
                continue

        return pending_files
