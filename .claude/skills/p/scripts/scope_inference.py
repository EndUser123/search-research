#!/usr/bin/env python3
"""
Scope inference for /p pipeline.

Determines what to analyze when /p is invoked without explicit arguments.
Uses chat context and session ledger instead of git for multi-terminal safety.

Priority order:
1. Explicit path argument (passed in, no inference needed)
2. Chat context: files from recent tool calls (last 10)
3. Session ledger: files read in current terminal session
4. Fallback: ask user to specify scope

Multi-terminal safe:
- Each terminal has own chat history
- Each terminal has own session ledger
- No cross-terminal state sharing
- No TTL or staleness issues
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class ScopeInference:
    """Result of scope inference."""

    source: Literal["explicit", "chat_context", "session_ledger", "none"]
    paths: list[str]
    confidence: Literal["high", "medium", "low"]
    reason: str


def get_terminal_id() -> str:
    """
    Get terminal ID for session isolation.

    Uses same logic as investigation-ledger for consistency.
    """
    # Try environment variable first (set by Claude Code)
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if terminal_id:
        return terminal_id

    # Try session ID
    session_id = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if session_id:
        return f"session_{session_id[:8]}"

    # Fallback: PID-based (unique per process)
    return f"pid_{os.getpid()}"


def infer_from_chat_context(
    recent_tool_calls: list[dict] | None = None,
    window: int = 10,
) -> ScopeInference:
    """
    Infer scope from recent tool usage in chat history.

    Args:
        recent_tool_calls: List of recent tool call dicts (optional, for testing)
        window: Number of recent turns to consider

    Returns:
        ScopeInference with inferred paths
    """
    if recent_tool_calls is None:
        # In actual use, this would be populated from the conversation
        # For now, return empty
        return ScopeInference(
            source="chat_context",
            paths=[],
            confidence="low",
            reason="No chat context available",
        )

    files = []
    for call in recent_tool_calls[-window:]:
        tool_name = call.get("tool_name", "")
        tool_input = call.get("tool_input", {})

        # Extract paths from file operations
        if tool_name in ("Read", "Edit", "Write"):
            path = tool_input.get("path", "")
            if path:
                files.append(path)
        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            if pattern:
                # Extract directory from glob pattern
                parts = pattern.split("*")[0].split("/")
                if parts:
                    files.append("/".join(parts[:-1]) if len(parts) > 1 else ".")
        elif tool_name == "Grep":
            path = tool_input.get("path", ".")
            if path and path != ".":
                files.append(path)

    if not files:
        return ScopeInference(
            source="chat_context",
            paths=[],
            confidence="low",
            reason=f"No file operations in last {window} turns",
        )

    # Find common parent directory
    paths_obj = [Path(f).parent for f in files if f]
    if not paths_obj:
        return ScopeInference(
            source="chat_context",
            paths=list(set(files)),
            confidence="medium",
            reason="Using specific files from chat history",
        )

    # Find deepest common ancestor
    common = paths_obj[0]
    for p in paths_obj[1:]:
        try:
            common = Path(os.path.commonpath([common, p]))
        except ValueError:
            # Paths on different drives or no common path
            common = Path(".")

    common_str = str(common) if str(common) != "." else "."

    return ScopeInference(
        source="chat_context",
        paths=[common_str],
        confidence="high" if len(files) >= 3 else "medium",
        reason=f"Inferred from {len(set(files))} file(s) in chat history",
    )


def infer_from_session_ledger() -> ScopeInference:
    """
    Infer scope from investigation-ledger (files read this session).

    Returns:
        ScopeInference with paths from session ledger
    """
    try:
        # Add hooks directory to path for ledger import
        hooks_dir = Path(__file__).parent.parent.parent.parent / "hooks"
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from investigation_ledger.ledger import get_files_read, get_investigation_stats

        files_read = get_files_read()
        stats = get_investigation_stats()

        if not files_read:
            return ScopeInference(
                source="session_ledger",
                paths=[],
                confidence="low",
                reason=f"No files in session ledger (files_read={stats['files_read']})",
            )

        # Find common parent
        paths_obj = [Path(f).parent for f in files_read]
        if not paths_obj:
            return ScopeInference(
                source="session_ledger",
                paths=list(set(files_read)),
                confidence="medium",
                reason="Using specific files from session ledger",
            )

        # Find deepest common ancestor
        common = paths_obj[0]
        for p in paths_obj[1:]:
            try:
                common = Path(os.path.commonpath([common, p]))
            except ValueError:
                common = Path(".")

        common_str = str(common) if str(common) != "." else "."

        return ScopeInference(
            source="session_ledger",
            paths=[common_str],
            confidence="high" if len(files_read) >= 3 else "medium",
            reason=f"Inferred from {len(files_read)} file(s) in session ledger",
        )

    except ImportError:
        return ScopeInference(
            source="session_ledger",
            paths=[],
            confidence="low",
            reason="Session ledger not available",
        )
    except Exception as e:
        return ScopeInference(
            source="session_ledger",
            paths=[],
            confidence="low",
            reason=f"Error reading session ledger: {e}",
        )


def infer_scope(
    explicit_path: str | None = None,
    recent_tool_calls: list[dict] | None = None,
    require_explicit: bool = False,
) -> ScopeInference:
    """
    Infer scope for /p pipeline execution.

    Args:
        explicit_path: User-provided path argument (highest priority)
        recent_tool_calls: Recent tool calls from chat history
        require_explicit: If True, don't infer, only use explicit path

    Returns:
        ScopeInference with determined scope
    """
    # 1. Explicit argument always wins
    if explicit_path:
        return ScopeInference(
            source="explicit",
            paths=[explicit_path],
            confidence="high",
            reason="User provided explicit path",
        )

    if require_explicit:
        return ScopeInference(
            source="none",
            paths=[],
            confidence="low",
            reason="Explicit path required but not provided",
        )

    # 2. Try chat context first (most recent, most relevant)
    chat_inference = infer_from_chat_context(recent_tool_calls)
    if chat_inference.paths and chat_inference.confidence != "low":
        return chat_inference

    # 3. Fall back to session ledger
    ledger_inference = infer_from_session_ledger()
    if ledger_inference.paths and ledger_inference.confidence != "low":
        return ledger_inference

    # 4. No clear scope - return empty
    return ScopeInference(
        source="none",
        paths=[],
        confidence="low",
        reason="No clear scope from context or session",
    )


def format_prompt_for_user(inference: ScopeInference) -> str:
    """
    Format a prompt asking user to specify scope.

    Args:
        inference: The inference result that triggered the prompt

    Returns:
        Formatted prompt string
    """
    return f"""No clear scope from conversation or session.

What should /p analyze?

Options:
  - /p <path>        # Specific directory (e.g., /p src/)
  - /p all           # Full codebase (slow, not recommended)
  - /p .             # Current directory only

Inference source: {inference.source}
Reason: {inference.reason}
"""


def main() -> int:
    """CLI entry point for testing scope inference."""
    import json

    # Test mode: explicit path
    if len(sys.argv) > 1:
        explicit_path = sys.argv[1]
        inference = infer_scope(explicit_path=explicit_path)
    else:
        # No argument: test inference
        inference = infer_scope()

    result = {
        "source": inference.source,
        "paths": inference.paths,
        "confidence": inference.confidence,
        "reason": inference.reason,
        "terminal_id": get_terminal_id(),
    }

    print(json.dumps(result, indent=2))

    if inference.source == "none":
        print("\n" + format_prompt_for_user(inference), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
