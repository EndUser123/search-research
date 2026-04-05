#!/usr/bin/env python3
"""
Ralph Wiggum Stop Hook (v7.3: Session-isolated state files)

Prevents session exit when a ralph-loop is active.
Feeds Claude's output back as input to continue the loop.

This is a Claude Code stop hook that manages iterative execution
with support for completion promises and max iteration limits.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# Configure logging - warnings/errors to stderr, messages to stdout
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

import os
import subprocess
from datetime import datetime, timedelta

# Default paths (relative to project root)
# Matches TDD Guard's default output_dir
DEFAULT_TDD_GUARD_DIR = Path(".claude/tdd-guard/data")
DEFAULT_TEST_JSON = DEFAULT_TDD_GUARD_DIR / "test.json"
DEFAULT_HTMLCOV_INDEX = Path("htmlcov/index.html")


class RalphConfig:
    """Configuration for Ralph Loop test verification.

    v7 Simplification: Uses environment variables and sensible defaults.
    Path discovery matches TDD Guard's actual behavior.
    """

    @staticmethod
    def _get_env_typed(key: str, default, type_):
        """Get environment variable with type conversion and fallback."""
        try:
            return type_(os.environ.get(key, default))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_test_command() -> str:
        """Get test command from environment or default."""
        return os.environ.get("RALPH_TEST_COMMAND", "pytest -q")

    @staticmethod
    def get_test_timeout() -> int:
        """Get test timeout from environment or default."""
        return RalphConfig._get_env_typed("RALPH_TEST_TIMEOUT", 60, int)

    @staticmethod
    def get_coverage_threshold() -> float:
        """Get coverage threshold from environment or default."""
        return RalphConfig._get_env_typed("RALPH_COVERAGE_THRESHOLD", 80.0, float)

    @staticmethod
    def get_clock_skew_grace() -> int:
        """Get clock skew grace period from environment or default."""
        return RalphConfig._get_env_typed("RALPH_CLOCK_SKEW_GRACE", 30, int)

    @staticmethod
    def get_tdd_guard_output_dir() -> Path:
        """
        Get TDD Guard output directory.

        v7 Simplification: Only check environment variable.
        This matches TDD Guard's actual config reading.

        Returns:
            Path to TDD Guard output directory
        """
        env_dir = os.environ.get("TDD_GUARD_OUTPUT_DIR")
        if env_dir:
            return Path(env_dir)
        return DEFAULT_TDD_GUARD_DIR

    @staticmethod
    def get_test_json_path(project_root: Path) -> Path:
        """
        Get the path to test.json.

        Args:
            project_root: Project root directory

        Returns:
            Absolute path to test.json
        """
        output_dir = RalphConfig.get_tdd_guard_output_dir()

        if output_dir.is_absolute():
            return output_dir / "test.json"
        else:
            return project_root / output_dir / "test.json"

    @staticmethod
    def get_htmlcov_path(project_root: Path) -> Path:
        """
        Get the path to htmlcov/index.html for coverage parsing.

        Args:
            project_root: Project root directory

        Returns:
            Absolute path to htmlcov/index.html
        """
        return project_root / DEFAULT_HTMLCOV_INDEX


@dataclass(frozen=True)
class RalphLoopConfig:
    """Configuration for Ralph loop paths and settings."""
    project_root: Path
    data_dir: Path
    state_file: Path

    @classmethod
    def create(cls, project_root: Path | str = Path('P:/projects/ralph-wiggum-python'), session_id: str | None = None) -> RalphLoopConfig:
        """Create configuration with session-isolated state file.

        Args:
            project_root: Path to Ralph project
            session_id: Claude session ID (finds matching state file if provided)
        """
        root = Path(project_root)
        data_dir = root / '.data'

        # v7.3: If session_id provided, find matching state file
        state_file = data_dir / 'ralph-loop.local.md'  # fallback
        if session_id:
            session_prefix = session_id[:8]
            # Look for ralph-loop.{session_id}.md
            candidate = data_dir / f'ralph-loop.{session_prefix}.md'
            if candidate.exists():
                state_file = candidate
            else:
                # Try scanning for any state file with matching session_id
                for f in data_dir.glob('ralph-loop.*.md'):
                    if f.name != 'ralph-loop.latest.md':
                        try:
                            state_content = f.read_text()
                            if f"session_id: {session_prefix}" in state_content:
                                state_file = f
                                break
                        except OSError:
                            continue

        return cls(
            project_root=root,
            data_dir=data_dir,
            state_file=state_file,
        )


# ============================================================================
# Exceptions
# ============================================================================

class RalphLoopError(Exception):
    """Base exception for Ralph loop errors."""
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.details = details or {}
        super().__init__(message)


class StateFileError(RalphLoopError):
    """Raised when state file is missing or corrupted."""
    pass


class ValidationError(RalphLoopError):
    """Raised when state validation fails."""
    pass


class TranscriptError(RalphLoopError):
    """Raised when transcript operations fail."""
    pass


# ============================================================================
# Test Result Schema Validation (v7)
# ============================================================================

class TestResultSchema:
    """Schema validation for TDD Guard test.json output."""

    # Required fields and their expected types
    REQUIRED_FIELDS = {
        "total": int,
        "passed": int,
        "failed": int,
        "skipped": int,
        "hasFailures": bool,
        "hasTests": bool,
    }

    # Optional fields
    OPTIONAL_FIELDS = {
        "errors": int,
        "tests": list,
    }

    @classmethod
    def validate(cls, data: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate test.json structure.

        Args:
            data: Parsed JSON data from test.json

        Returns:
            (is_valid, error_message)
        """
        # Check required fields exist
        missing = [f for f in cls.REQUIRED_FIELDS if f not in data]
        if missing:
            return False, f"Missing required fields: {missing}"

        # Check field types
        for field, expected_type in cls.REQUIRED_FIELDS.items():
            if not isinstance(data[field], expected_type):
                return False, f"Field '{field}' has wrong type: expected {expected_type.__name__}, got {type(data[field]).__name__}"

        # Validate tests array if present
        if "tests" in data:
            if not isinstance(data["tests"], list):
                return False, "Field 'tests' must be a list"

            for i, test in enumerate(data["tests"][:5]):  # Check first 5
                if not isinstance(test, dict):
                    return False, f"Test {i} is not a dict"

                if "name" not in test:
                    return False, f"Test {i} missing 'name' field"

                if "outcome" not in test:
                    return False, f"Test {i} missing 'outcome' field"

                # v7: Validate outcome value
                if test["outcome"] not in ("passed", "failed", "skipped"):
                    return False, f"Test {i} has invalid outcome: {test['outcome']}"

        return True, None


# ============================================================================
# Test Result Verification (v7)
# ============================================================================

def _should_require_tests(completion_promise: str | None) -> bool:
    """
    Determine if tests should be required based on completion promise.
    """
    if not completion_promise or completion_promise == 'null':
        return False

    promise_upper = completion_promise.upper()
    test_keywords = ['TEST', 'PASS', 'COMPLETE', 'DONE', 'FIXED']

    return any(kw in promise_upper for kw in test_keywords)


class TestResultVerifier:
    """Verifies test results from TDD Guard or subprocess."""

    @classmethod
    def read_fresh_tdd_guard_results(
        cls,
        session_start: datetime,
        project_root: Path,
        grace_seconds: int = None
    ) -> dict[str, Any] | None:
        """
        Read TDD Guard results if test.json is from THIS session.

        v7: Simplified staleness check using only mtime.

        Args:
            session_start: When this Ralph Loop session started
            project_root: Project root directory
            grace_seconds: Clock skew tolerance (uses config if None)

        Returns:
            Test summary dict if fresh and valid results exist, None otherwise
        """
        if grace_seconds is None:
            grace_seconds = RalphConfig.get_clock_skew_grace()

        # Get test.json path (simplified in v7)
        test_json_path = RalphConfig.get_test_json_path(project_root)

        if not test_json_path.exists():
            return None

        # Check staleness using mtime
        try:
            test_mtime = datetime.fromtimestamp(test_json_path.stat().st_mtime)

            # Calculate effective threshold with grace period
            effective_threshold = session_start - timedelta(seconds=grace_seconds)

            # Stale if mtime is before threshold
            if test_mtime <= effective_threshold:
                return None

        except OSError:
            return None

        # Read and validate test.json
        try:
            content = test_json_path.read_text()
            test_data = json.loads(content)

            # Validate structure before using
            is_valid, error = TestResultSchema.validate(test_data)
            if not is_valid:
                # Invalid schema - don't use, trigger subprocess fallback
                sys.stderr.write(f"⚠️ TDD Guard test.json invalid: {error}\n")
                return None

            # Extract summary with CORRECT field names
            summary = {
                "total": test_data.get("total", 0),
                "passed": test_data.get("passed", 0),
                "failed": test_data.get("failed", 0),
                "skipped": test_data.get("skipped", 0),
                "has_failures": test_data.get("hasFailures", False),
                "has_tests": test_data.get("hasTests", False),
                "tests": test_data.get("tests", []),
            }

            # v7: Note about tests array truncation
            # TDD Guard only stores last 20 tests. If there are more failures,
            # they won't appear in test.json. This is a known limitation.

            return {
                "source": "tdd_guard",
                "summary": summary,
                "passed": not summary["has_failures"] and summary["has_tests"],
                "coverage_percent": cls._read_coverage_percent(project_root),
            }

        except (OSError, json.JSONDecodeError) as e:
            sys.stderr.write(f"⚠️ Failed to read test.json: {e}\n")
            return None

    @classmethod
    def _read_coverage_percent(cls, project_root: Path) -> float | None:
        """
        Read coverage percentage from pytest-cov HTML report.

        v7 Enhanced: Prioritizes overall coverage, not file-level.

        Returns:
            Coverage percentage if available, None otherwise
        """
        htmlcov_path = RalphConfig.get_htmlcov_path(project_root)

        if not htmlcov_path.exists():
            return None

        try:
            content = htmlcov_path.read_text()

            # v7: Try data-ratio attribute first (most reliable)
            # HTML structure: <td data-ratio="68 100">68%</td>
            match = re.search(r'data-ratio\s*=\s*"(\d+)\s+\d+"', content)
            if match:
                return float(match.group(1))

            # v7: Look for overall coverage table (better than text patterns)
            # Try to find the main coverage percentage, typically in a header or summary

            # Look for coverage in the first 2000 chars (likely to be summary)
            header_section = content[:2000]

            # Try to find "XX% coverage" or "Coverage: XX%" in header
            overall_match = re.search(r'Coverage:\s*(\d+)%', header_section, re.IGNORECASE)
            if overall_match:
                return float(overall_match.group(1))

            overall_match = re.search(r'(\d+)%\s+coverage', header_section, re.IGNORECASE)
            if overall_match:
                return float(overall_match.group(1))

            # Fallback to any percentage (might match file-level, but better than nothing)
            match = re.search(r'(\d+)%\s*cov', content, re.IGNORECASE)
            if match:
                return float(match.group(1))

        except (OSError, ValueError):
            pass

        return None

    @classmethod
    def run_tests_via_subprocess(
        cls,
        workdir: str,
        timeout: int = None,
        test_command: str = None
    ) -> dict[str, Any]:
        """
        Fallback: Run tests via subprocess when TDD Guard unavailable.

        v7: Workdir is required - uses project_root from state file.
        """
        if timeout is None:
            timeout = RalphConfig.get_test_timeout()

        if test_command is None:
            test_command = RalphConfig.get_test_command()

        try:
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=workdir,  # v7: Uses correct project directory
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'passed': result.returncode == 0,
                'source': 'subprocess'
            }
        except subprocess.TimeoutExpired:
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Test timeout after {timeout}s',
                'passed': False,
                'source': 'subprocess'
            }
        except Exception as e:
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'passed': False,
                'source': 'subprocess'
            }


# ============================================================================
# Error Message Builder (DRY - single source of truth for error formats)
# ============================================================================

class ErrorMessageBuilder:
    """Builds consistent error messages across the codebase."""

    # Common message fragments
    HEADER = "Ralph loop"
    CORRUPTED_INTRO = "State file corrupted or incomplete"
    MANUAL_EDIT_HINT = "State file was manually edited or corrupted"
    RESTART_HINT = "Run /ralph-loop again to start fresh"

    # Common explanations
    EXPLANATIONS = {
        "manual_edit": "State file was manually edited",
        "corrupted_write": "File was corrupted during writing",
        "no_prompt": "No prompt text found",
        "malformed_frontmatter": "Malformed frontmatter (expected ---YAML---PROMPT)",
        "invalid_iteration": "'iteration' field is not a valid number",
        "invalid_max_iter": "'max_iterations' field is not a valid number",
    }

    @classmethod
    def build_corruption_error(
        cls,
        file_path: Path,
        problem: str,
        explanation_keys: list[str] | None = None,
    ) -> str:
        """Build a consistent corruption error message."""
        explanation_keys = explanation_keys or ["manual_edit", "corrupted_write"]

        explanations = "\n".join(
            f"  • {cls.EXPLANATIONS[key]}" for key in explanation_keys
        )

        return (
            f"{cls.HEADER}: {cls.CORRUPTED_INTRO}\n"
            f"File: {file_path}\n"
            f"Problem: {problem}\n\n"
            f"{f"This usually means:\n{explanations}\n\n" if explanations else ""}"
            f"{cls.RESTART_HINT}"
        )

    @classmethod
    def build_validation_error(
        cls,
        file_path: Path,
        field_name: str,
        value: Any,
    ) -> str:
        """Build a validation error for a specific field."""
        return cls.build_corruption_error(
            file_path,
            f"'{field_name}' field is not a valid number (got: {value!r})",
            explanation_keys=["manual_edit"],
        )


# ============================================================================
# State File Operations
# ============================================================================

class StateFileManager:
    """Handles loading, parsing, and updating the state file."""

    def __init__(self, config: RalphLoopConfig | None = None) -> None:
        self.config = config or RalphLoopConfig.create()

    def load(self) -> tuple[dict[str, Any], str]:
        """
        Load and parse the state file.

        Returns:
            Tuple of (frontmatter_dict, prompt_text)

        Raises:
            StateFileError: If state file is missing or corrupted
        """
        state_path = self.config.state_file

        if not state_path.exists():
            # No active loop - allow exit
            sys.exit(0)

        try:
            content = state_path.read_text(encoding='utf-8')
        except OSError as e:
            raise StateFileError(f"Failed to read state file: {e}")

        frontmatter, prompt_text = self._parse_content(content, state_path)
        return frontmatter, prompt_text

    def _parse_content(self, content: str, state_path: Path) -> tuple[dict[str, Any], str]:
        """Parse content, separating frontmatter from prompt."""
        parts = content.split('---')

        if len(parts) < 3:
            raise StateFileError(
                ErrorMessageBuilder.build_corruption_error(
                    state_path,
                    ErrorMessageBuilder.EXPLANATIONS["malformed_frontmatter"],
                )
            )

        frontmatter_text = parts[1].strip()
        prompt_text = '---'.join(parts[2:]).strip()

        if not prompt_text:
            raise StateFileError(
                ErrorMessageBuilder.build_corruption_error(
                    state_path,
                    ErrorMessageBuilder.EXPLANATIONS["no_prompt"],
                )
            )

        frontmatter = self._parse_frontmatter(frontmatter_text)

        # v7.2: Extract subtask count
        frontmatter['subtask_count'] = frontmatter.get('subtask_count')

        # v7.3: Extract session_id for validation
        frontmatter['session_id'] = frontmatter.get('session_id')

        return frontmatter, prompt_text

    def _parse_frontmatter(self, text: str) -> dict[str, Any]:
        """Parse YAML frontmatter."""
        try:
            frontmatter = yaml.safe_load(text)
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter is not a valid YAML dict")
            return frontmatter
        except (yaml.YAMLError, ValueError) as e:
            raise StateFileError(f"Failed to parse YAML frontmatter: {e}")

    def update_iteration(self, next_iteration: int) -> None:
        """Atomically update iteration counter in state file."""
        state_path = self.config.state_file

        try:
            content = state_path.read_text(encoding='utf-8')
            updated = re.sub(
                r'^iteration:\s*\d+',
                f'iteration: {next_iteration}',
                content,
                flags=re.MULTILINE
            )
            self._atomic_write(state_path, updated)
        except OSError as e:
            logger.error(f"Failed to update iteration: {e}")
            raise

    def update_iteration_with_timestamp(self, next_iteration: int) -> None:
        """Atomically update iteration counter and reset iteration_started_at (v8.1)."""
        state_path = self.config.state_file
        new_timestamp = datetime.now(timezone.utc).isoformat()

        try:
            content = state_path.read_text(encoding='utf-8')
            # Update iteration counter
            updated = re.sub(
                r'^iteration:\s*\d+',
                f'iteration: {next_iteration}',
                content,
                flags=re.MULTILINE
            )
            # Update iteration_started_at
            updated = re.sub(
                r'^iteration_started_at:\s*\S+',
                f'iteration_started_at: "{new_timestamp}"',
                updated,
                flags=re.MULTILINE
            )
            # If iteration_started_at doesn't exist (old format), add it after iteration line
            if 'iteration_started_at:' not in updated:
                updated = re.sub(
                    r'^(iteration:\s*\d+)',
                    r'\1\niteration_started_at: "' + new_timestamp + '"',
                    updated,
                    flags=re.MULTILINE
                )
            self._atomic_write(state_path, updated)
        except OSError as e:
            logger.error(f"Failed to update iteration: {e}")
            raise

    def cleanup(self) -> None:
        """Remove state file."""
        state_path = self.config.state_file
        try:
            if state_path.exists():
                state_path.unlink()
        except OSError as e:
            logger.error(f"Failed to remove state file: {e}")

    def _atomic_write(self, path: Path, content: str) -> None:
        """Write content atomically (temp file + rename)."""
        temp_path = path.with_suffix(path.suffix + '.tmp')
        temp_path.write_text(content, encoding='utf-8')
        temp_path.replace(path)


# ============================================================================
# State Validation
# ============================================================================

class StateValidator:
    """Validates state file contents."""

    def __init__(self, config: RalphLoopConfig | None = None) -> None:
        self.config = config or RalphLoopConfig.create()

    def validate(self, frontmatter: dict[str, Any]) -> None:
        """
        Validate state frontmatter.

        Raises:
            ValidationError: If validation fails
        """
        self._validate_iteration(frontmatter)
        self._validate_max_iterations(frontmatter)
        self._check_iteration_limit(frontmatter)

    def _validate_iteration(self, frontmatter: dict[str, Any]) -> None:
        iteration = frontmatter.get('iteration')
        if not self._is_valid_number(iteration):
            raise ValidationError(
                ErrorMessageBuilder.build_validation_error(
                    self.config.state_file,
                    'iteration',
                    iteration,
                )
            )

    def _validate_max_iterations(self, frontmatter: dict[str, Any]) -> None:
        max_iterations = frontmatter.get('max_iterations')
        if not self._is_valid_number(max_iterations):
            raise ValidationError(
                ErrorMessageBuilder.build_validation_error(
                    self.config.state_file,
                    'max_iterations',
                    max_iterations,
                )
            )

    def _check_iteration_limit(self, frontmatter: dict[str, Any]) -> None:
        iteration = frontmatter['iteration']
        max_iterations = frontmatter['max_iterations']

        if max_iterations > 0 and iteration >= max_iterations:
            print(f"🛑 Ralph loop: Max iterations ({max_iterations}) reached.")
            sys.exit(0)

    @staticmethod
    def _is_valid_number(value: Any) -> bool:
        """Check if value is a valid non-negative integer."""
        return isinstance(value, int) and value >= 0


# ============================================================================
# Transcript Operations
# ============================================================================

class TranscriptLoader:
    """Loads and parses transcript files."""

    def load_last_assistant_message(self, transcript_path: Path) -> dict[str, Any]:
        """
        Load the last assistant message from transcript (JSONL format).

        Returns:
            Last assistant message dict

        Raises:
            TranscriptError: If transcript is invalid or has no assistant messages
        """
        if not transcript_path.exists():
            raise TranscriptError(
                "Transcript file not found\n"
                f"Expected: {transcript_path}\n\n"
                "This is unusual and may indicate a Claude Code internal issue.\n"
                "Ralph loop is stopping."
            )

        try:
            content = transcript_path.read_text(encoding='utf-8')
        except OSError as e:
            raise TranscriptError(f"Failed to read transcript: {e}")

        return self._parse_jsonl(content, transcript_path)

    def _parse_jsonl(self, content: str, transcript_path: Path) -> dict[str, Any]:
        """Parse JSONL content and return last assistant message."""
        last_assistant_msg = None

        for line in content.strip().split('\n'):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if obj.get('role') == 'assistant':
                    last_assistant_msg = obj
            except json.JSONDecodeError:
                continue

        if last_assistant_msg is None:
            raise TranscriptError(
                "No assistant messages found in transcript\n"
                f"Transcript: {transcript_path}\n\n"
                "This is unusual and may indicate a transcript format issue\n"
                "Ralph loop is stopping."
            )

        return last_assistant_msg


class MessageExtractor:
    """Extracts content from assistant messages."""

    @staticmethod
    def extract_text_content(message: dict[str, Any]) -> str:
        """
        Extract text content from an assistant message.

        Handles message.content as either list of content blocks or plain text.
        """
        content = message.get('message', {}).get('content', [])

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text = block.get('text', '').strip()
                    if text:
                        text_parts.append(text)
            return '\n'.join(text_parts)

        return ''

    @staticmethod
    def extract_promise_text(output: str) -> str | None:
        """
        Extract text from <promise>...</promise> tags.

        Returns:
            Extracted promise text if found, None otherwise
        """
        match = re.search(r'<promise>(.*?)</promise>', output, re.DOTALL)
        if not match:
            return None

        promise_text = match.group(1)
        # Normalize whitespace
        promise_text = re.sub(r'^\s+|\s+$', '', promise_text)
        promise_text = re.sub(r'\s+', ' ', promise_text)

        return promise_text


# ============================================================================
# Hook Response Builder
# ============================================================================


def cleanup_zombie_states(data_dir: Path, max_age_hours: int = 1) -> int:
    """Remove state files older than max_age_hours.

    Args:
        data_dir: Directory containing state files
        max_age_hours: Maximum age in hours before cleanup

    Returns:
        Number of files cleaned up
    """
    from datetime import timedelta

    cleaned = 0
    cutoff = datetime.now() - timedelta(hours=max_age_hours)

    for state_file in data_dir.glob('ralph-loop.*.md'):
        if state_file.name == 'ralph-loop.latest.md':
            continue

        try:
            mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
            if mtime < cutoff:
                state_file.unlink()
                cleaned += 1
        except OSError:
            pass

    return cleaned


def get_subtask_info(subtask_count: int | None) -> dict[str, Any]:
    """
    Get subtask info from state file (v7.2: embedded, no TaskMaster).

    Args:
        subtask_count: Number of subtasks from state file

    Returns:
        Dict with subtask info
    """
    if not subtask_count:
        return {"has_subtasks": False, "total": 0}

    return {
        "has_subtasks": True,
        "total": subtask_count,
    }



class HookResponseBuilder:
    """Builds JSON responses for the stop hook."""

    @staticmethod
    def build_block_response(
        prompt_text: str,
        next_iteration: int,
        completion_promise: str | None,
    ) -> dict[str, str]:
        """Build JSON response to block stop and continue loop."""
        if completion_promise and completion_promise != 'null':
            system_msg = (
                f"🔄 Ralph iteration {next_iteration}{subtask_info} | "
                f"To stop: output {completion_promise} "
                f"(ONLY when statement is TRUE - do not lie to exit!)"
            )
        else:
            system_msg = (
                f"🔄 Ralph iteration {next_iteration}{subtask_info} | "
                "No completion promise set - loop runs infinitely"
            )

        return {
            'decision': 'block',
            'reason': prompt_text,
            'systemMessage': system_msg
        }



# ============================================================================
# Health Check (v7)
# ============================================================================

def _should_require_tests(completion_promise: str | None) -> bool:
    """
    Determine if tests should be required based on completion promise.
    """
    if not completion_promise or completion_promise == 'null':
        return False

    promise_upper = completion_promise.upper()
    test_keywords = ['TEST', 'PASS', 'COMPLETE', 'DONE', 'FIXED']

    return any(kw in promise_upper for kw in test_keywords)


def check_strict_tdd_requirements(
    project_root: Path,
    iteration_start: datetime,
    test_timeout: int
) -> str | None:
    """
    Strict TDD validation for Ralph loops (v8.1).

    Checks:
    1. .py files modified THIS ITERATION have corresponding test files
    2. Coverage for new modules is ≥80%
    3. Tests were run during session (not skipped)

    Note: Only checks files modified since iteration_start, not session_start.
    This allows multi-day Ralph sessions without checking all historical files.

    Args:
        project_root: Root directory of the project
        iteration_start: When the current iteration started (for file scope)
        test_timeout: Timeout for test execution

    Returns:
        Error message if TDD requirements not met, None if all pass
    """
    # Find Python files modified/created since iteration start (not session start!)
    new_py_files: list[Path] = []
    test_dirs = [
        project_root / "tests",
        project_root / "test",
        project_root / "src" / "tests",
    ]

    # Find .py files in project (exclude common non-source dirs)
    exclude_dirs = {
        ".venv", "venv", "env", ".env",
        "__pycache__", ".pytest_cache",
        "htmlcov", ".tox", ".mypy_cache",
        "node_modules", ".git",
        "build", "dist", "*.egg-info",
    }

    for py_file in project_root.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        # Skip test files (we're checking source files have tests)
        if py_file.name.startswith("test_") or py_file.parent.name in ("tests", "test"):
            continue

        # Skip __init__.py (not test-worthy on its own)
        if py_file.name == "__init__.py":
            continue

        # Skip files not modified/created since session start
        # Use mtime as proxy for when file was worked on
        try:
            mtime = datetime.fromtimestamp(py_file.stat().st_mtime, tz=session_start.tzinfo)
            if mtime >= session_start:
                new_py_files.append(py_file)
        except (OSError, ValueError):
            continue

    if not new_py_files:
        # No new code files - nothing to validate
        return None

    # Check 1: Verify corresponding test files exist
    missing_tests: list[tuple[Path, list[Path]]] = []
    for py_file in new_py_files:
        # Find potential test file locations
        module_name = py_file.stem
        possible_test_names = [
            f"test_{module_name}.py",
            f"{module_name}_test.py",
        ]

        # Look in same directory
        test_candidates = [py_file.parent / name for name in possible_test_names]
        # Look in tests/ directories
        for test_dir in test_dirs:
            if test_dir.exists():
                for name in possible_test_names:
                    test_candidates.append(test_dir / name)

        found = any(t.exists() for t in test_candidates)
        if not found:
            missing_tests.append((py_file, test_candidates))

    if missing_tests:
        missing_list = "\n  ".join(str(f.relative_to(project_root)) for f, _ in missing_tests)
        return (
            "📋 MISSING TEST FILES\n\n"
            f"The following new .py files lack corresponding test files:\n"
            f"  {missing_list}\n\n"
            f"Create test_*.py files for each new module before continuing.\n"
            f"Example: test_batch_config.py for batch_config.py"
        )

    # Check 2: Verify coverage ≥80% for new modules
    try:
        # Try to get coverage from TDD Guard results
        tdd_guard_dir = project_root / DEFAULT_TDD_GUARD_DIR
        coverage_json = tdd_guard_dir / "coverage.json"

        if coverage_json.exists():
            try:
                cov_data = json.loads(coverage_json.read_text())
                files = cov_data.get("files", {})

                # Check coverage for each new file
                low_coverage: list[tuple[str, float]] = []
                for py_file in new_py_files:
                    rel_path = str(py_file.relative_to(project_root))
                    # Normalize path for coverage lookup
                    for cov_path, cov_info in files.items():
                        if rel_path in cov_path or cov_path.endswith(rel_path):
                            summary = cov_info.get("summary", {})
                            percent = summary.get("percent_covered", 0)
                            if percent < 80:
                                low_coverage.append((rel_path, percent))
                            break

                if low_coverage:
                    cov_list = "\n  ".join(f"{f}: {c:.1f}%" for f, c in low_coverage)
                    return (
                        "📊 COVERAGE BELOW THRESHOLD\n\n"
                        f"The following new modules have <80% coverage:\n"
                        f"  {cov_list}\n\n"
                        f"Add tests to reach ≥80% coverage before continuing."
                    )
            except (OSError, json.JSONDecodeError):
                pass
    except Exception:
        # Coverage check is best-effort - don't block on errors
        pass

    # Check 3: Verify tests were actually run (check for recent test results)
    test_json_path = project_root / DEFAULT_TEST_JSON
    if test_json_path.exists():
        try:
            test_data = json.loads(test_json_path.read_text())
            # Check if tests passed
            if test_data.get("hasFailures", True) or test_data.get("failed", 0) > 0:
                return (
                    "❌ TESTS ARE FAILING\n\n"
                    f"Tests: {test_data.get('passed', 0)}/{test_data.get('total', 0)} passing, "
                    f"{test_data.get('failed', 0)} failed\n\n"
                    f"Fix failing tests before continuing."
                )
        except (OSError, json.JSONDecodeError):
            pass

    # All TDD requirements met
    return None


def ralph_health_check() -> dict[str, Any]:
    """
    Check Ralph Loop health status.

    Returns:
        Health status dict with running state, iteration info, and test results.
    """
    config = RalphLoopConfig.create()

    if not config.state_file.exists():
        return {
            "status": "not_running",
            "state_file": str(config.state_file)
        }

    try:
        state_manager = StateFileManager(config)
        frontmatter, _ = state_manager.load()

        # Get test result if available
        test_result = None
        test_json_path = RalphConfig.get_test_json_path(Path.cwd())
        if test_json_path.exists():
            try:
                test_data = json.loads(test_json_path.read_text())
                test_result = {
                    "total": test_data.get("total", 0),
                    "passed": test_data.get("passed", 0),
                    "failed": test_data.get("failed", 0),
                    "has_failures": test_data.get("hasFailures", False),
                    "timestamp": datetime.fromtimestamp(test_json_path.stat().st_mtime).isoformat()
                }
            except (OSError, json.JSONDecodeError):
                pass

        return {
            "status": "running",
            "state_file": str(config.state_file),
            "iteration": frontmatter.get("iteration", 0),
            "max_iterations": frontmatter.get("max_iterations", 0),
            "started_at": frontmatter.get("started_at"),
            "test_required": frontmatter.get("test_required", False),
            "test_result": test_result,
            "project_root": frontmatter.get("project_root", str(Path.cwd()))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================================================
# Main Entry Point
# ============================================================================

def read_hook_input() -> str:
    """Read hook input from stdin (advanced stop hook API)."""
    return sys.stdin.read()


def main() -> None:
    """Main stop hook execution with test verification (v7)."""
    # Read hook input FIRST - need session_id before creating config
    hook_input = read_hook_input()

    # Parse hook input to get session_id early
    hook_session_id = ''
    try:
        hook_obj = json.loads(hook_input)
        hook_session_id = hook_obj.get('session_id', '')
    except (json.JSONDecodeError, TypeError):
        hook_session_id = ''

    # Now create config with session_id
    config = RalphLoopConfig.create(session_id=hook_session_id)
    state_manager = StateFileManager(config)
    validator = StateValidator(config)
    transcript_loader = TranscriptLoader()

    try:
        # v7.3: Cleanup zombie states before loading
        cleanup_zombie_states(config.data_dir, max_age_hours=1)

        # Load and validate state
        frontmatter, prompt_text = state_manager.load()
        validator.validate(frontmatter)

        # Extract fields from frontmatter
        iteration = frontmatter['iteration']
        max_iterations = frontmatter['max_iterations']
        completion_promise = frontmatter.get('completion_promise')

        # v7.2: Subtask count
        subtask_count = frontmatter.get('subtask_count')

        # v7.3: Validate session_id (detect stale state from other terminal)
        state_session_id = frontmatter.get('session_id')
        if state_session_id and hook_session_id:
            state_prefix = state_session_id[:8]
            hook_prefix = hook_session_id[:8]
            if state_prefix != hook_prefix:
                # State file belongs to different session - allow exit
                sys.exit(0)

        # v7: test_required - check for new field or default based on completion promise
        # v8: RALPH LOOP ALWAYS REQUIRES TESTS - TDD is mandatory for Ralph
        is_ralph_loop = frontmatter.get('source') == 'ralph'
        test_required_from_promise = _should_require_tests(completion_promise)

        if is_ralph_loop:
            # Ralph loops ALWAYS require tests - TDD is mandatory
            test_required = True
        else:
            # Other workflows use promise-based detection
            test_required = frontmatter.get('test_required', test_required_from_promise)

        # Get configurable values from state file or environment
        test_timeout = frontmatter.get('test_timeout', RalphConfig.get_test_timeout())
        coverage_threshold = frontmatter.get('coverage_threshold', RalphConfig.get_coverage_threshold())

        # v7: Get project_root from state file, or use cwd
        project_root_str = frontmatter.get('project_root', str(Path.cwd()))
        project_root = Path(project_root_str)

        # Get session start time for staleness check
        started_at_str = frontmatter.get('started_at')
        if started_at_str:
            try:
                session_start = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
            except ValueError:
                # If started_at is malformed, allow exit (backward compat)
                sys.exit(0)
        else:
            # No started_at = old state file format, allow exit
            sys.exit(0)

        # v8.1: Get iteration start time for TDD validation (files changed THIS iteration only)
        # Falls back to session_start for backward compatibility
        iteration_started_at_str = frontmatter.get('iteration_started_at', started_at_str)
        if iteration_started_at_str:
            try:
                iteration_start = datetime.fromisoformat(iteration_started_at_str.replace('Z', '+00:00'))
            except ValueError:
                iteration_start = session_start
        else:
            iteration_start = session_start

        # Parse hook input to get transcript path
        try:
            hook_obj = json.loads(hook_input)
            transcript_path = Path(hook_obj['transcript_path'])
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise RalphLoopError(f"Failed to parse hook input: {e}")

        # Load and parse transcript
        last_msg = transcript_loader.load_last_assistant_message(transcript_path)
        last_output = MessageExtractor.extract_text_content(last_msg)

        if not last_output:
            raise RalphLoopError(
                "Assistant message contained no text content\n"
                "Ralph loop is stopping."
            )

        # Check for completion promise
        promise_detected = False
        if completion_promise and completion_promise != 'null':
            promise_text = MessageExtractor.extract_promise_text(last_output)
            if promise_text and promise_text == completion_promise:
                promise_detected = True

        # ====================================================================
        # Strict TDD Validation (v8: Ralph-only)
        # ====================================================================

        if is_ralph_loop:
            # Enforce strict TDD rules for Ralph loops
            # v8.1: Use iteration_start to check only files modified THIS iteration
            tdd_block_reason = check_strict_tdd_requirements(
                project_root, iteration_start, test_timeout
            )
            if tdd_block_reason:
                next_iteration = iteration + 1
                # v8.1: Reset iteration_started_at for next iteration
                state_manager.update_iteration_with_timestamp(next_iteration)

                failure_prompt = (
                    f"❌ TDD Requirements Not Met (iteration {next_iteration}/{max_iterations})\n"
                    f"{tdd_block_reason}\n\n"
                    f"📋 TDD RULES:\n"
                    f"  1. Write test BEFORE code (Red phase)\n"
                    f"  2. Write minimal code to pass (Green phase)\n"
                    f"  3. Run tests to verify (Refactor phase)\n\n"
                    f"  Each new .py file must have a corresponding test_*.py file.\n"
                    f"  Coverage for new modules must be ≥80%.\n\n"
                    f"Original task:\n\n{prompt_text}"
                )

                response = {
                    'decision': 'block',
                    'reason': failure_prompt,
                    'systemMessage': f"🔄 Ralph iteration {next_iteration} | TDD Requirements"
                }
                print(json.dumps(response, ensure_ascii=False))
                sys.exit(0)

        # ====================================================================
        # Test verification
        # ====================================================================

        test_result = None  # None = not checked, or dict with results

        if test_required:
            # Try reading fresh TDD Guard results first
            grace_seconds = RalphConfig.get_clock_skew_grace()
            test_result = TestResultVerifier.read_fresh_tdd_guard_results(
                session_start, project_root, grace_seconds
            )

            # If no fresh TDD Guard results, run subprocess
            if test_result is None:
                # v7: Use project_root from state file for correct working directory
                test_result = TestResultVerifier.run_tests_via_subprocess(
                    str(project_root),
                    timeout=test_timeout
                )

            # Check if tests passed
            if not test_result['passed']:
                next_iteration = iteration + 1
                # v8.1: Reset iteration_started_at for next iteration
                state_manager.update_iteration_with_timestamp(next_iteration)

                # Build failure feedback
                if test_result['source'] == 'tdd_guard':
                    summary = test_result['summary']
                    failed_tests = [
                        t for t in summary.get('tests', [])
                        if t.get('outcome') == 'failed'
                    ]

                    failure_prompt = (
                        f"❌ Tests failed (iteration {next_iteration}/{max_iterations})\n"
                        f"Tests: {summary['passed']}/{summary['total']} passing, "
                        f"{summary['failed']} failed\n\n"
                        f"Failed tests:\n"
                    )
                    for test in failed_tests[:5]:
                        failure_prompt += f"  ❌ {test['name']}\n"
                        if test.get('failure'):
                            failure_prompt += f"     {test['failure'][:200]}\n"

                    if len(failed_tests) > 5:
                        failure_prompt += f"  ... and {len(failed_tests) - 5} more (showing first 5)\n"

                    if test_result.get('coverage_percent') is not None:
                        cov = test_result['coverage_percent']
                        failure_prompt += f"\nCoverage: {cov:.1f}%\n"

                    # v7.2: Add subtask status
                    subtask_status = get_subtask_status(tm_parent_id, tm_subtask_ids)
                    if subtask_status["has_subtasks"]:
                        failure_prompt += f"\nSubtasks: {subtask_status['completed']}/{subtask_status['total']} complete"
                        for detail in subtask_status['details'][:3]:
                            emoji = "✅" if detail['status'] == 'completed' else "⏳"
                            failure_prompt += f"\n  {emoji} {detail['title']}"

                    failure_prompt += f"\nOriginal task:\n\n{prompt_text}"

                else:  # subprocess source
                    failure_prompt = (
                        f"❌ Tests failed (iteration {next_iteration}/{max_iterations})\n"
                        f"Source: subprocess\n"
                        f"Working directory: {project_root}\n"
                        f"Exit code: {test_result['exit_code']}\n\n"
                        f"{test_result['stdout']}\n"
                        f"{test_result['stderr']}\n\n"
                        f"Original task:\n\n{prompt_text}"
                    )

                response = {
                    'decision': 'block',
                    'reason': failure_prompt,
                    'systemMessage': f"🔄 Ralph iteration {next_iteration} | Tests failing"
                }
                print(json.dumps(response, ensure_ascii=False))
                sys.exit(0)

            # Tests passed - check coverage gate
            coverage_percent = test_result.get('coverage_percent')
            if coverage_percent is not None and coverage_percent < coverage_threshold:
                next_iteration = iteration + 1
                # v8.1: Reset iteration_started_at for next iteration
                state_manager.update_iteration_with_timestamp(next_iteration)

                coverage_gap = coverage_threshold - coverage_percent
                summary = test_result.get('summary', {})

                failure_prompt = (
                    f"❌ Coverage gate failed (iteration {next_iteration}/{max_iterations})\n"
                    f"Coverage: {coverage_percent:.1f}% < {coverage_threshold:.0f}% required\n"
                    f"Gap: {coverage_gap:.1f}% coverage needed\n"
                    f"Tests: {summary.get('passed', 0)}/{summary.get('total', 0)} passing\n\n"
                    f"Write tests for uncovered code and retry.\n\n"
                    f"Original task:\n\n{prompt_text}"
                )

                response = {
                    'decision': 'block',
                    'reason': failure_prompt,
                    'systemMessage': f"🔄 Ralph iteration {next_iteration} | Coverage: {coverage_percent:.1f}%"
                }
                print(json.dumps(response, ensure_ascii=False))
                sys.exit(0)

        # ====================================================================
        # Check completion conditions
        # ====================================================================

        # Allow exit if:
        # - Tests not required: promise detected only
        # - Tests required: tests passed AND promise detected
        # - With subtasks: all subtasks complete
        can_complete = False

        if not test_required:
            can_complete = promise_detected
        elif test_result is not None:
            can_complete = test_result['passed'] and promise_detected

        if can_complete:
            print(f"✅ Ralph loop complete")
            print(f"   Iterations: {iteration}/{max_iterations}")
            if test_result is not None:
                cov_str = f"{test_result.get('coverage_percent', 0):.1f}%" if test_result.get('coverage_percent') else "N/A"
                print(f"   Tests: PASSED (source: {test_result['source']}, coverage: {cov_str})")
            state_manager.cleanup()
            sys.exit(0)

        # ====================================================================
        # Continue loop
        # ====================================================================

        next_iteration = iteration + 1
        # v8.1: Reset iteration_started_at for next iteration
        state_manager.update_iteration_with_timestamp(next_iteration)

        response = HookResponseBuilder.build_block_response(
            prompt_text,
            next_iteration,
            completion_promise
        )
        print(json.dumps(response, ensure_ascii=False))
        sys.exit(0)

    except RalphLoopError as e:
        print(f"⚠️ {e}", file=sys.stderr)
        state_manager.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"⚠️ Ralph loop: Unexpected error: {e}", file=sys.stderr)
        state_manager.cleanup()
        sys.exit(0)




if __name__ == '__main__':
    main()
