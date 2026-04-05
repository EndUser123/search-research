"""Base classes for UserPromptSubmit hooks.

Defines HookResult and HookContext used across all UserPromptSubmit modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class HookResult:
    """Result from a UserPromptSubmit hook.

    Attributes:
        context: Injected context text (None if no injection)
        tokens: Estimated token count for injected content
        priority: Hook priority (lower = earlier execution)
    """

    def __init__(
        self,
        context: str | dict | None,
        tokens: int = 0,
        priority: float = 10.0,
        tokens_added: int | None = None,
    ):
        """Initialize HookResult with backward compatibility for tokens_added parameter.

        Args:
            context: Injected context text
            tokens: Estimated token count
            priority: Hook priority (lower = earlier)
            tokens_added: Alias for tokens (for backward compatibility with tests)
        """
        self.context = context
        # If tokens_added is provided, use it; otherwise use tokens
        self.tokens = tokens_added if tokens_added is not None else tokens
        self.priority = priority

    def is_empty(self) -> bool:
        """Check if result has no context to inject."""
        return not self.context

    @classmethod
    def empty(cls) -> HookResult:
        """Create an empty result (no injection)."""
        return cls(context=None, tokens=0)

    def __eq__(self, other: object) -> bool:
        """Check equality based on context and tokens."""
        if not isinstance(other, HookResult):
            return False
        return self.context == other.context and self.tokens == other.tokens

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"HookResult(context={self.context!r}, tokens={self.tokens})"


@dataclass
class HookContext:
    """Shared context passed between hooks.

    Attributes:
        prompt: The user's prompt text
        data: Additional data from the event (tool inputs, etc.)
        session_id: Current Claude Code session ID
        terminal_id: Terminal/worktree ID for isolation
    """

    prompt: str
    data: dict[str, Any]
    session_id: str | None = None
    terminal_id: str | None = None
