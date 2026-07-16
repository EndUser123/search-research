"""Completion detection for Claude Code terminal output.

Heuristic: poll the screen buffer every *poll_interval*.  When the last line
stops changing for *idle_timeout* AND matches a prompt pattern, consider the
response complete.

The prompt pattern is auto-detected at startup: scrape the first line/cursor
position when the adapter starts and learn what "idle looks like."
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable


# ── Default prompt patterns ───────────────────────────────────────────────────

# Common patterns that indicate Claude Code is waiting for input.
PROMPT_PATTERNS = [
    re.compile(r">>>\s*$"),          # Python REPL
    re.compile(r"PS\s+.*>+\s*$"),   # PowerShell prompt
    re.compile(r"\$\s+.*>\s*$"),    # Generic command prompt
    re.compile(r"❯\s*$"),           # zsh/oh-my-zsh prompt
    re.compile(r"#\s*$"),           # Root shell
    re.compile(r"\.{3,}\s*$"),      # Continuation prompt
    re.compile(r"\S+@\S+.*[#$>]\s*$"),  # user@host prompt
]

# If none of the above match, we fall back to "last line is short and
# not obviously a code/error output."
MAX_PROMPT_LENGTH = 80   # Prompts are usually short


@dataclass
class CompletionResult:
    """Result of a completion detection cycle."""

    complete: bool
    last_line: str
    all_lines: list[str]
    idle_seconds: float
    method: str  # "prompt_pattern", "idle_timeout", "silence"


class CompletionDetector:
    """Detect when Claude Code has finished responding and returned to idle.

    Usage::

        detector = CompletionDetector(screen_reader_fn)
        result = detector.poll()
        if result.complete:
            response_text = "\\n".join(result.all_lines)
    """

    def __init__(
        self,
        screen_reader_fn: Callable[[], list[str]],
        *,
        idle_timeout: float = 1.5,
        poll_interval: float = 0.2,
        max_prompt_length: int = MAX_PROMPT_LENGTH,
    ):
        self._reader = screen_reader_fn
        self._idle_timeout = idle_timeout
        self._poll_interval = poll_interval
        self._max_prompt_length = max_prompt_length

        self._last_line: str = ""
        self._last_change: float = time.monotonic()
        self._start_time: float = time.monotonic()
        self._initial_snapshot: list[str] = []
        self._collected_lines: list[str] = []

    def reset(self) -> None:
        """Reset the detector state for a new injection cycle."""
        self._last_line = ""
        self._last_change = time.monotonic()
        self._start_time = time.monotonic()
        self._initial_snapshot = self._reader()
        self._collected_lines = []

    def poll(self) -> CompletionResult:
        """Poll the screen buffer and check for completion.

        Call this periodically (matching ``poll_interval``) while injecting.
        """
        lines = self._reader()
        if not lines:
            return CompletionResult(
                complete=False, last_line="", all_lines=[],
                idle_seconds=time.monotonic() - self._last_change,
                method="no_output",
            )

        current_last = lines[-1].strip() if lines else ""
        now = time.monotonic()

        # Track accumulated output (filter out unchanged lines from pre-injection)
        if not self._initial_snapshot:
            self._initial_snapshot = lines
        # Collect new lines — anything that differs from initial or has appeared
        # since we started tracking.
        for line in lines:
            if line.rstrip() not in [l.rstrip() for l in self._collected_lines]:
                self._collected_lines.append(line.rstrip())

        # Check if the last line changed
        if current_last != self._last_line:
            self._last_line = current_last
            self._last_change = now

        idle_seconds = now - self._last_change

        # If we haven't seen any activity yet, not complete
        if idle_seconds < self._idle_timeout:
            return CompletionResult(
                complete=False, last_line=current_last, all_lines=self._collected_lines,
                idle_seconds=idle_seconds, method="active",
            )

        # Idle timeout reached — check if the last line looks like a prompt
        if self._is_prompt(current_last):
            return CompletionResult(
                complete=True, last_line=current_last, all_lines=self._collected_lines,
                idle_seconds=idle_seconds, method="prompt_pattern",
            )

        # If the output is completely silent from the start (no response at all)
        if idle_seconds > 10.0:
            return CompletionResult(
                complete=True, last_line=current_last, all_lines=self._collected_lines,
                idle_seconds=idle_seconds, method="silence_timeout",
            )

        return CompletionResult(
            complete=False, last_line=current_last, all_lines=self._collected_lines,
            idle_seconds=idle_seconds, method="waiting",
        )

    def _is_prompt(self, line: str) -> bool:
        """Check if *line* looks like a shell/REPL prompt."""
        if not line:
            return False
        if len(line) > self._max_prompt_length:
            return False
        for pattern in PROMPT_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def extract_response_text(self, result: CompletionResult) -> str:
        """Extract the actual response text from the collected output.

        Strips the injected prompt line and trailing prompt from the output.
        """
        if not result.all_lines:
            return ""

        lines = list(result.all_lines)

        # Remove the trailing prompt line (last line)
        if lines and self._is_prompt(lines[-1]):
            lines = lines[:-1]

        # Find the injection boundary: the first line that looks like it
        # contains the injected message.  If we can't find it, return
        # everything (safe fallback).
        return "\n".join(lines).strip()