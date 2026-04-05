"""CKS Context Injection Hook

Detects trigger phrases and injects relevant context from CKS database.
Uses keyword search (fast, no model loading) for hook compatibility.

This hook is registered manually in registry.py to avoid circular import.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path for CKS imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import base classes directly
from UserPromptSubmit_modules.base import HookContext, HookResult

# Trigger phrases from documentation
TRIGGER_PHRASES = [
    # Explicit requests
    "check cks", "cks context", "search cks", "query cks",
    # Prior context signals
    "prior context", "previous conversation", "past discussion",
    "we discussed", "we talked about", "as we mentioned",
    # Frustration/memory signals
    "you forget", "been down this road", "we've done this before",
    "you keep making", "same mistake", "already told you",
    # Historical reference
    "remember when", "last time", "earlier we", "before you",
]


def _should_trigger_cks(prompt: str) -> bool:
    """Check if prompt contains CKS trigger phrases."""
    prompt_lower = prompt.lower()
    return any(phrase in prompt_lower for phrase in TRIGGER_PHRASES)


def _query_cks(prompt: str, max_results: int = 5) -> list[dict]:
    """Query CKS database for relevant entries.

    Uses keyword search only (semantic search too slow for hooks).
    """
    try:
        # Import CKS database path
        cks_db_path = project_root / "__csf" / "data" / "cks.db"

        if not cks_db_path.exists():
            return []

        import sqlite3

        # Keyword search via SQL (fast, no model loading)
        conn = sqlite3.connect(cks_db_path)
        cursor = conn.cursor()

        # Search in title and content
        query = f"%{prompt}%"
        cursor.execute(
            """
            SELECT id, type, title, content, metadata
            FROM entries
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY usage_count DESC, created_at DESC
            LIMIT ?
            """,
            (query, query, max_results)
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "content": row[3],
                "metadata": row[4],
            })

        conn.close()
        return results

    except Exception as e:
        # Fail silently - CKS unavailable shouldn't break hook
        # NOTE: Hooks must NOT print to stdout (Claude Code treats it as error)
        # Log to file instead of stdout
        try:
            import time
            log_dir = Path("P:/.claude/state/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "cks_context_errors.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [ERROR] CKS query failed: {e}\n")
        except Exception:
            pass  # Fail silently if logging fails
        return []


def _format_cks_context(results: list[dict], prompt: str) -> str:
    """Format CKS results as context injection."""
    if not results:
        return ""

    # Filter out low-quality entries
    filtered = []
    for r in results:
        content = r.get("content", "")
        # Skip template content
        if "[FILL]" in content or "[TODO]" in content:
            continue
        # Skip very short entries
        if len(content.strip()) < 50:
            continue
        filtered.append(r)

    if not filtered:
        return ""

    lines = [
        "## 📚 Related Context from CKS",
        ""
    ]

    for i, result in enumerate(filtered[:3], 1):  # Max 3 results
        entry_type = result.get("type", "memory")
        title = result.get("title", "") or f"Entry {result.get('id')}"
        content = result.get("content", "")

        # Truncate long content
        if len(content) > 500:
            content = content[:500] + "..."

        lines.append(f"**{i}. [{entry_type}] {title}**")
        lines.append(content)
        lines.append("")

    lines.extend([
        "---",
        "*Consider this prior context if relevant.*",
        ""
    ])

    return "\n".join(lines)


def cks_context_hook(context: HookContext) -> HookResult:
    """Inject CKS context when trigger phrases detected.

    This function is registered manually in registry.py to avoid circular import.
    """
    # Check if enabled via environment
    if os.environ.get("CKS_INTEGRATION_ENABLED", "true").lower() not in ("1", "true", "yes"):
        return HookResult.empty()

    # Fast path: skip if no trigger phrase
    if not _should_trigger_cks(context.prompt):
        return HookResult.empty()

    # Query CKS for relevant entries
    results = _query_cks(context.prompt, max_results=5)

    if not results:
        return HookResult.empty()

    # Format and return context
    formatted_context = _format_cks_context(results, context.prompt)

    if not formatted_context:
        return HookResult.empty()

    return HookResult.context_injection(formatted_context)


# Add context_injection as a class method for compatibility
HookResult.context_injection = lambda content: HookResult(
    context=content,
    tokens=len(content.split()),
    priority=5.0
)
