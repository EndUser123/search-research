#!/usr/bin/env python3
from __future__ import annotations

"""
Violation Reporter Module
========================
Handles violation reporting and tracking for the deny_root_write hook.
This module only handles violation reporting, integrating with ViolationTracker.

Consolidated from P:\\__csf\\.claude\\hooks\\ to P:\\.claude\\hooks\\
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
hooks_dir = Path(__file__).resolve().parent
from typing import Any

import logging as _li
_logger = _li.getLogger(__name__)
_hook_log_dir = hooks_dir / 'logs' / 'diagnostics'
_hook_log_dir.mkdir(parents=True, exist_ok=True)
_handler = _li.FileHandler(_hook_log_dir / 'hook_stderr.log', encoding='utf-8')
_handler.setFormatter(_li.Formatter('%(asctime)s %(levelname)s %(message)s'))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)


class ViolationReporter:
    """
    Handles violation reporting and tracking.
    Falls back to stderr logging when ViolationTracker is unavailable.
    """

    def __init__(self, storage_path: str | Path | None = None):
        """
        Initialize violation reporter.

        Args:
            storage_path: Optional storage path for violation data
        """
        if storage_path is None:
            storage_path = hooks_dir / "hooks/data/violations"

        self.storage_path = Path(storage_path)
        self._violation_tracker = None
        self._tracker_checked = False

    def _get_allowed_root_patterns(self) -> list[str]:
        """
        Load allowed root patterns from directory_policy.json at runtime.

        Returns:
            List of allowed path patterns from policy file
        """
        import json

        policy_path = Path(__file__).resolve().parent / "config" / "directory_policy.json"
        try:
            with open(policy_path, encoding='utf-8') as f:
                policy = json.load(f)
            root_config = policy.get("workspace_root", {})
            patterns = root_config.get("allowed_root_patterns", [])
            return [p.get("pattern", p) if isinstance(p, dict) else p for p in patterns]
        except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError):
            # Fallback to hardcoded list if policy can't be loaded
            return [".claude", "__csf", "docs", "packages", "projects", "scripts"]

    def _get_violation_tracker(self):
        """
        Get ViolationTracker instance if available.

        Returns:
            ViolationTracker instance or None if unavailable
        """
        if self._tracker_checked:
            return self._violation_tracker

        self._tracker_checked = True

        try:
            # Try to import ViolationTracker from CSF Prevention Framework
            framework_path = PROJECT_ROOT / "__csf" / "src/csf_prevention_framework"
            if str(framework_path) not in sys.path:
                sys.path.insert(0, str(framework_path))

            from violation_tracker import (
                ViolationCategory,
                ViolationSeverity,
                ViolationTracker,
            )

            # Try to create storage directory, but don't fail if we can't
            try:
                self.storage_path.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                # Can't create storage dir - fall back to stderr logging
                _logger.warning(f"Cannot create violation storage: {e}")
                self._violation_tracker = None
                return None

            # Try with optional params, fall back to basic init
            try:
                self._violation_tracker = ViolationTracker(
                    storage_path=self.storage_path, auto_categorize=True, enable_trending=True
                )
            except TypeError:
                # Fallback if ViolationTracker doesn't support these params
                self._violation_tracker = ViolationTracker(storage_path=self.storage_path)

            self._violation_tracker.ViolationSeverity = ViolationSeverity
            self._violation_tracker.ViolationCategory = ViolationCategory

        except ImportError:
            self._violation_tracker = None
        except (PermissionError, OSError) as e:
            # Permission errors accessing storage - fall back gracefully
            _logger.warning(f"Violation tracking disabled (permission error): {e}")
            self._violation_tracker = None
        except Exception as e:
            # Any other error, just disable tracking
            _logger.warning(f"Violation tracking disabled: {e}")
            self._violation_tracker = None

        return self._violation_tracker

    def report_violation(
        self,
        file_path: str,
        violation_type: str,
        user_context: dict[str, Any] | None = None,
        tool_input: dict[str, Any] | None = None,
        verbose: bool = True,
    ) -> bool:
        """
        Report a hook violation.

        Args:
            file_path: The file path that was blocked
            violation_type: Type of violation (ROOT_WRITE, PROTECTED_WRITE, etc.)
            user_context: User and session context information
            tool_input: Original tool input for evidence collection
            verbose: Whether to print verbose output

        Returns:
            True if violation was successfully tracked, False otherwise
        """
        tracker = self._get_violation_tracker()

        if not tracker:
            self._log_violation_to_stderr(file_path, violation_type, verbose)
            return False

        try:
            severity, category = self._classify_violation(violation_type)
            evidence = self._create_violation_evidence(
                file_path, violation_type, user_context, tool_input
            )
            session_context = self._extract_session_context(tool_input)
            metadata = self._create_metadata(
                file_path, violation_type, session_context, user_context
            )

            violation = tracker.track_violation(
                severity=severity,
                category=category,
                title=f"Hook Violation: {violation_type}",
                description=f"Root protection hook blocked {violation_type.lower()} for file: {file_path}",
                artifact_path=file_path,
                rule_id="HOOK-ROOT-PROTECTION",
                location_info="Hook: deny_root_write.py",
                evidence=evidence,
                recommendation="Use appropriate subdirectories within project structure",
                auto_fix_available=False,
                tags={"hook", "root-protection", violation_type.lower()},
                metadata=metadata,
            )

            if verbose:
                print(
                    f"🚨 Violation tracked: {violation.violation_id} - {violation_type}",
                    )
            return True

        except (PermissionError, OSError) as e:
            # Permission errors - log to stderr instead
            if verbose:
                _logger.error(f"Error reading violations file: {e}")
            self._log_violation_to_stderr(file_path, violation_type, verbose)
            return False
        except Exception as e:
            if verbose:
                _logger.error(f"Error tracking violation: {e}")
            self._log_violation_to_stderr(file_path, violation_type, verbose)
            return False

    def _log_violation_to_stderr(
        self, file_path: str, violation_type: str, verbose: bool = True
    ) -> None:
        """Fallback logging to stderr when ViolationTracker is unavailable."""
        if verbose:
            _logger.debug(f"{violation_type}: {file_path}")

    def _classify_violation(self, violation_type: str) -> tuple:
        """Classify violation severity and category."""
        tracker = self._get_violation_tracker()
        if not tracker:
            return None, None

        ViolationSeverity = tracker.ViolationSeverity
        ViolationCategory = tracker.ViolationCategory

        if violation_type in ["ROOT_DIRECTORY_WRITE", "ROOT_LEVEL_WRITE"]:
            return ViolationSeverity.CRITICAL, ViolationCategory.SECURITY
        elif violation_type == "SYMLINK_ESCAPE":
            return ViolationSeverity.CRITICAL, ViolationCategory.SECURITY
        elif violation_type == "PROTECTED_DIRECTORY_WRITE":
            return ViolationSeverity.MAJOR, ViolationCategory.GOVERNANCE
        elif violation_type == "CLAUDE_DIRECTORY_VIOLATION":
            return ViolationSeverity.MAJOR, ViolationCategory.GOVERNANCE
        elif violation_type == "OUTSIDE_PROJECT_WRITE":
            return ViolationSeverity.MINOR, ViolationCategory.COMPLIANCE
        else:
            return ViolationSeverity.ADVISORY, ViolationCategory.COMPLIANCE

    def _create_violation_evidence(
        self,
        file_path: str,
        violation_type: str,
        user_context: dict[str, Any] | None,
        tool_input: dict[str, Any] | None,
    ) -> str:
        """Create comprehensive evidence for the violation."""
        evidence_parts = [
            f"Violation Type: {violation_type}",
            f"Target File: {file_path}",
            f"Timestamp: {datetime.now().isoformat()}",
            "Hook: deny_root_write.py",
        ]

        _SENSITIVE_KEYS = {"api_key", "token", "secret", "password", "credential", "auth", "private_key"}
        if tool_input:
            evidence_parts.append("Tool Input Details:")
            for key, value in tool_input.items():
                if key != "file_path" and not any(s in key.lower() for s in _SENSITIVE_KEYS):
                    evidence_parts.append(f"  {key}: {value}")

        if user_context:
            evidence_parts.append("User Context:")
            for key, value in user_context.items():
                evidence_parts.append(f"  {key}: {value}")

        evidence_parts.extend(
            [
                f"System Platform: {sys.platform}",
                f"Current Working Directory: {os.getcwd()}",
                f"Environment Variables: CLAUDE_PROJECT_DIR={os.environ.get('CLAUDE_PROJECT_DIR', 'Not set')}",
            ]
        )

        return "\n".join(evidence_parts)

    def _extract_session_context(self, tool_input: dict[str, Any] | None) -> dict[str, Any]:
        """Extract session context from environment and tool input."""
        return {
            "user_id": os.environ.get("USER", "claude-session"),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", f"session-{uuid.uuid4().hex[:8]}"),
            "timestamp": datetime.now().isoformat(),
            "environment": os.environ.get("CLAUDE_ENVIRONMENT", "development"),
            "project_dir": os.environ.get("CLAUDE_PROJECT_DIR", ""),
            "tool_operation": tool_input.get("tool_name", "Unknown") if tool_input else "Unknown",
        }

    def _create_metadata(
        self,
        file_path: str,
        violation_type: str,
        session_context: dict[str, Any],
        user_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create metadata for analytics."""
        metadata = {
            "hook_name": "deny_root_write",
            "violation_type": violation_type,
            "file_path": file_path,
            "normalized_path": file_path.replace("\\", "/"),
            "detection_timestamp": datetime.now().isoformat(),
            "session_context": session_context,
            "host_info": {
                "hostname": os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")),
                "platform": sys.platform,
            },
        }

        if user_context:
            metadata["user_context"] = user_context

        return metadata

    def format_violation_message(
        self, violation_type: str, file_path: str, include_recommendation: bool = True
    ) -> str:
        """Format violation message with actionable guidance AND machine-parseable correction.

        The message ends with a structured block that Claude Code can parse:

        ```
        ===HOOK_CORRECTION===
        BLOCKED: <original_path>
        USE_INSTEAD: <corrected_path>
        ACTION: Retry write operation with corrected path
        ===END_CORRECTION===
        ```

        This enables CC to automatically recover from path violations.
        """
        normalized_path = file_path.replace("\\", "/").lower()
        filename = normalized_path.split("/")[-1]

        # Plan files get specific redirect message
        if ".claude/plans" in normalized_path or ".claude\\plans" in file_path.lower():
            corrected_path = f"P:/.claude/plans/{filename}"
            message = (
                f"🚫 PLAN WRITE BLOCKED: {filename}\n"
                "   Plans must stay in P:/.claude/plans/\n"
                f"   Correct location: {corrected_path}"
            )
            return self._append_correction_block(message, file_path, corrected_path)

        # BLOCKED_PATTERN gets specific suggestions based on filename
        if violation_type == "BLOCKED_PATTERN":
            corrected_path = self._suggest_correct_path(filename)
            message = f"🚫 BLOCKED: {filename}\n"
            message += "   Reason: Root-level file pollution\n"
            message += f"   Correct location: {corrected_path}"
            return self._append_correction_block(message, file_path, corrected_path)

        # BLOCKED_ROOT_PATTERN: P:/ root default-deny blocking
        if violation_type == "BLOCKED_ROOT_PATTERN":
            allowed_patterns = self._get_allowed_root_patterns()
            allowed_str = ", ".join(f"`{p}`" for p in allowed_patterns)
            corrected_path = self._suggest_correct_path(filename)
            message = (
                f"🚫 ROOT WRITE BLOCKED: {filename}\n"
                f"   Reason: P:/ root uses default-deny allowlist\n"
                f"   Allowed top-level paths: {allowed_str}\n"
                f"   Correct location: {corrected_path}"
            )
            return self._append_correction_block(message, file_path, corrected_path)

        # RESTRICTED_PATH: User-only directories (docs/, etc.)
        if violation_type.startswith("RESTRICTED_PATH"):
            # Extract suggestion from violation_type: "RESTRICTED_PATH: .claude/docs/"
            suggestion = (
                violation_type.split(":", 1)[1].strip()
                if ":" in violation_type
                else ".claude/docs/"
            )
            # Remove trailing slash to avoid double slashes
            suggestion = suggestion.rstrip("/")
            corrected_path = f"P:/{suggestion}/{filename}"
            message = (
                f"🚫 RESTRICTED PATH: {filename}\n"
                f"   Reason: This directory is reserved for user-authored content\n"
                f"   Use .claude/docs/ for Claude-generated documentation\n"
                f"   Correct location: {corrected_path}"
            )
            return self._append_correction_block(message, file_path, corrected_path)

        # Base message for other violation types
        message = f"🚫 ROOT WRITE BLOCKED: {filename}"

        if include_recommendation:
            guidance = [
                "",
                "Slash command? → P:/.claude/skills/{filename}",
                "Framework code? → P:/__csf/src/[feature]/{filename}",
                "Project file? → P:/projects/[name]/{filename}",
                "Staging/temp? → P:/__csf/.staging/{filename}",
                "",
                "💡 Keep features self-contained with their configs",
                "⚠️  Scan session: Other misplaced files?",
            ]

            message = message + "\n" + "\n".join(guidance)

        # Add machine-parseable correction block for Claude Code
        corrected_path = self._suggest_correct_path(filename)
        message = self._append_correction_block(message, file_path, corrected_path)

        return message

    def _suggest_correct_path(self, filename: str) -> str:
        """
        Suggest the correct path based on filename pattern.

        Args:
            filename: The filename to suggest a path for

        Returns:
            Suggested correct path
        """
        import fnmatch

        suggestions = {
            # Test files -> tests/
            "test_*.py": "P:/__csf/tests/{filename}",
            "*_test.py": "P:/__csf/tests/{filename}",
            # Report files -> reports/
            "*_report*.json": "P:/__csf/reports/{filename}",
            "*_results*.json": "P:/__csf/reports/{filename}",
            "*_REPORT.md": "P:/__csf/reports/{filename}",
            "*_DEPLOYMENT*.md": "P:/__csf/reports/{filename}",
            # Scripts -> scripts/
            "fix_*.py": "P:/__csf/scripts/{filename}",
            "clean_*.py": "P:/__csf/scripts/{filename}",
            "simple_*.py": "P:/__csf/scripts/{filename}",
            # Logs -> logs/
            "*.log": "P:/__csf/logs/{filename}",
            # Databases -> data/
            "*.db": "P:/__csf/data/{filename}",
            "*.db-shm": "P:/__csf/data/{filename}",
            "*.db-wal": "P:/__csf/data/{filename}",
        }

        for pattern, path_template in suggestions.items():
            if fnmatch.fnmatch(filename, pattern):
                return path_template.format(filename=filename)

        # Default: staging area
        return f"P:/__csf/.staging/{filename}"

    def _append_correction_block(self, message: str, blocked_path: str, corrected_path: str) -> str:
        """Append machine-parseable correction block AND write to file for CC.

        This structured block enables CC to:
        1. Detect that a correction is available
        2. Extract the correct path programmatically
        3. Retry the operation with the fixed path

        Also writes to P:/.claude/session_data/hook_correction.json for reliable access.
        """
        import json
        from pathlib import Path

        # Write correction to file for reliable CC access
        correction_file = Path("P:/.claude/session_data/hook_correction.json")
        try:
            correction_file.parent.mkdir(parents=True, exist_ok=True)
            correction_data = {
                "blocked_path": blocked_path,
                "corrected_path": corrected_path,
                "timestamp": datetime.now().isoformat(),
                "action": "Retry write with corrected_path",
            }
            correction_file.write_text(json.dumps(correction_data, indent=2))
        except Exception:
            pass  # Don't fail the hook if file write fails

        correction_block = f"""

===HOOK_CORRECTION===
BLOCKED: {blocked_path}
USE_INSTEAD: {corrected_path}
ACTION: Retry write operation with USE_INSTEAD path. Do NOT retry with BLOCKED path.
===END_CORRECTION==="""

        return message + correction_block
