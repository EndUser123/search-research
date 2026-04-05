"""Session analyzer for /gto skill.

Analyzes conversation transcripts to identify:
- TODO/FIXME markers mentioned in conversation
- Unfinished work tasks
- Session metrics (turns, duration, etc.)
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SessionAnalyzer:
    """Analyze conversation sessions for gaps and opportunities."""

    def __init__(self, transcript_path: str | Path) -> None:
        """Initialize analyzer with transcript path.

        Args:
            transcript_path: Path to conversation transcript file
        """
        # Keep original value for test compatibility
        self.transcript_path = transcript_path
        # Use Path object for internal operations
        self._path_obj = Path(transcript_path)
        logger.info(f"SessionAnalyzer initialized with {self.transcript_path}")

    def extract_todos(self, text: str) -> list[str]:
        """Extract TODO/FIXME markers from text.

        Args:
            text: Conversation text to search

        Returns:
            List of TODO/FIXME strings found
        """
        # Pattern for TODO/FIXME markers (require standalone marker word)
        # Use negative lookbehind to avoid matching "todos" as "todo"
        todo_pattern = re.compile(
            r"\b(TODO|FIXME|HACK|XXX)\b:?\s*(.+?)(?=\n|$)",
            re.IGNORECASE | re.MULTILINE
        )

        matches = todo_pattern.findall(text)
        todos = [f"{marker}: {content}" for marker, content in matches]

        logger.debug(f"Found {len(todos)} TODO/FIXME markers")
        return todos

    def detect_unfinished_work(self, conversation: str) -> list[str]:
        """Detect unfinished work from conversation patterns.

        Looks for:
        - Task statements without completion confirmations
        - "I'll" / "I will" statements without "done" / "complete"
        - Questions without answers

        Args:
            conversation: Conversation text

        Returns:
            List of unfinished task descriptions
        """
        unfinished = []

        # Look for task initiation patterns (more permissive)
        # Match phrases like "I'll implement X", "I will create Y"
        task_starts = re.finditer(
            r"(?:I'll|I will|Let me|Starting to|Working on|start working|begin(?:ning)?|going to)\s+([^.!\?]+)",
            conversation,
            re.IGNORECASE
        )

        # Look for completion confirmations
        # Require first-person statements to avoid false positives
        completion_patterns = [
            r"(?:I've|I have)\s+(?:completed|finished|implemented|done)",
            r"I\s+(?:have\s+)?(?:completed|finished|implemented|done)\s+(?:it|the|this|that)",
        ]
        has_completion = any(
            re.search(pattern, conversation, re.IGNORECASE)
            for pattern in completion_patterns
        )

        # If we have task starts but no completion, mark as unfinished
        task_starts_list = list(task_starts)
        if task_starts_list and not has_completion:
            for match in task_starts_list:
                task = match.group(1).strip()
                if len(task) > 5:  # Filter out very short matches
                    unfinished.append(task)

        logger.debug(f"Found {len(unfinished)} unfinished tasks")
        return unfinished

    def analyze_session(self) -> dict[str, Any]:
        """Perform full session analysis.

        Returns:
            Structured report with todos, unfinished work, and metrics
        """
        # Try to read transcript file
        conversation_text = ""
        if self._path_obj.exists():
            try:
                conversation_text = self._path_obj.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read transcript: {e}")
                conversation_text = ""
        else:
            logger.info(f"Transcript file not found: {self._path_obj}")

        # Extract todos and unfinished work
        todos = self.extract_todos(conversation_text)
        unfinished = self.detect_unfinished_work(conversation_text)

        # Calculate session metrics
        session_metrics = {
            "conversation_length": len(conversation_text),
            "todo_count": len(todos),
            "unfinished_count": len(unfinished),
            "transcript_exists": self._path_obj.exists(),
        }

        report = {
            "todos": todos,
            "unfinished_work": unfinished,
            "session_metrics": session_metrics,
        }

        logger.info(
            f"Session analysis complete: {len(todos)} todos, "
            f"{len(unfinished)} unfinished tasks"
        )

        return report
