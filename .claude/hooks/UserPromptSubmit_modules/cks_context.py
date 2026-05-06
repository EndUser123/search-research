"""CKS Context Injection Hook

Detects trigger phrases and injects relevant context from CKS database.
Uses keyword search (fast, no model loading) for hook compatibility.

On analysis/final-answer turns, also automatically injects the 3 most recent
CKS corrections (last 24h) that semantically match the user prompt.

Hybrid retrieval: when CKS_CORRECTION_SEMANTIC=true, merges semantic search
(via CKS.search with vector embeddings) with keyword overlap scoring.
The keyword path is always preserved as fallback.

This hook is registered manually in registry.py to avoid circular import.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path for CKS imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import base classes directly
from UserPromptSubmit_modules.base import HookContext, HookResult

# Import turn mode classifier
import_path = str(Path(__file__).resolve().parents[1] / "__lib" / "turn_mode")
if import_path not in sys.path:
    sys.path.insert(0, import_path)
from turn_mode import classify as classify_turn_mode

# Trigger phrases from documentation
TRIGGER_PHRASES = [
    # Explicit CKS requests
    "check cks", "cks context", "search cks", "query cks",
    # Prior context signals
    "prior context", "previous conversation", "past discussion",
    "we discussed", "we talked about", "as we mentioned",
    # Historical reference
    "remember when", "last time", "earlier we", "before you",
    # Cross-session context questions (the natural way to ask)
    "what did we discuss", "what did we talk about", "what were we discussing",
    "what did i ask about", "what were we working on",
    "earlier today", "yesterday we", "last session",
    "in a previous session", "before this session",
]

# === Auto-correction injection for analysis/final-answer turns ===

CORRECTION_INJECTION_MODES = ("analysis", "final-answer", "meta")

# Hybrid semantic retrieval: merges CKS.search() vector results with keyword scoring
CKS_SEMANTIC_ENABLED = os.environ.get("CKS_CORRECTION_SEMANTIC", "false").lower() in ("1", "true", "yes")


def _should_inject_recent_corrections(prompt: str) -> bool:
    """Check if prompt warrants automatic recent-correction injection."""
    if os.environ.get("CKS_CORRECTION_AUTO_INJECT", "true").lower() not in ("1", "true", "yes"):
        return False
    try:
        data = {"user_prompt": prompt, "response": ""}
        mode = classify_turn_mode(data)
        return mode in CORRECTION_INJECTION_MODES
    except Exception:
        return False


def _query_semantic_corrections(prompt: str, max_results: int = 3, hours: int = 24) -> list[dict]:
    """Query CKS corrections via vector embedding similarity.

    Uses CKS.search() with enable_semantic=True to find corrections with
    semantic similarity even when keyword overlap is zero. Falls back to
    empty list on any error (fail-open, never blocks injection).
    """
    try:
        from cks.unified import CKS

        cks_db_path = Path("P:/__csf/data/cks.db")
        if not cks_db_path.exists():
            return []

        with CKS(db_path=cks_db_path, enable_semantic=True) as cks:
            results = cks.search(
                query=prompt,
                entry_type="correction",
                limit=max_results,
            )

        if not results:
            return []

        # Use UTC consistently — DB stores created_at in UTC (ISO format with +00:00)
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        recent = [
            r for r in results
            if r.get("created_at", "") > cutoff
        ]
        return recent[:max_results]

    except Exception:
        return []


def _query_recent_corrections(prompt: str, max_results: int = 3, hours: int = 24) -> list[dict]:
    """Query CKS for recent corrections matching the user prompt keywords."""
    try:
        cks_db_path = Path("P:/__csf/data/cks.db")
        if not cks_db_path.exists():
            return []

        import sqlite3

        conn = sqlite3.connect(cks_db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")

        cursor.execute(
            """
            SELECT id, type, title, content, metadata, created_at
            FROM entries
            WHERE type = 'correction'
              AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (cutoff,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        import re

        # Strip punctuation for robust keyword matching
        # "authentication," → "authentication", "web-app" → "web app"
        def _normalize(text: str) -> set[str]:
            if not text:
                return set()
            # Replace common separators with spaces, then split and strip remaining punctuation
            normalized = re.sub(r'[-_/]', ' ', text.lower())
            words = [w.strip().strip('.,!?;:"\'()[]{}') for w in normalized.split()]
            return set(w for w in words if w)

        prompt_words = _normalize(prompt)
        scored = []
        for row in rows:
            entry_words = _normalize((row[2] or "") + " " + (row[3] or ""))
            overlap = len(prompt_words & entry_words)
            scored.append((overlap, row))

        # Sort by overlap desc, then created_at desc
        scored.sort(key=lambda x: (x[0], x[1][5]), reverse=True)

        # Filter: only return results with at least 1 keyword overlap
        # (name promises "matching", so don't return non-matching entries)
        relevant = [(score, row) for score, row in scored if score > 0]
        return [
            {
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "content": row[3],
                "metadata": row[4],
                "created_at": row[5],
            }
            for _, row in relevant[:max_results]
        ]

    except Exception:
        return []


def _query_hybrid_corrections(prompt: str, max_results: int = 3, hours: int = 24) -> list[dict]:
    """Merge keyword and semantic correction results for hybrid retrieval.

    Strategy: keyword results first (high precision), then semantic-only results
    (high recall for symptom/vocabulary mismatch). No combined score — keeps
    the ranking simple and deterministic. Fails open to keyword-only on any error.
    """
    keyword_results = _query_recent_corrections(prompt, max_results=max_results, hours=hours)
    keyword_ids = {r["id"] for r in keyword_results}

    if not CKS_SEMANTIC_ENABLED:
        return keyword_results

    semantic_results = _query_semantic_corrections(prompt, max_results=max_results, hours=hours)

    # Deduplicate: keep all keyword results + semantic-only results
    semantic_only = [r for r in semantic_results if r["id"] not in keyword_ids]

    merged = keyword_results + semantic_only[:max_results - len(keyword_results)]
    return merged[:max_results]


def _format_recent_corrections(results: list[dict], prompt: str) -> str:
    """Format recent corrections as context injection."""
    if not results:
        return ""

    lines = [
        "## Recent CKS Corrections",
        "",
    ]
    for i, result in enumerate(results, 1):
        title = result.get("title", "") or f"Correction {result.get('id')}"
        content = result.get("content", "")
        created = result.get("created_at", "")
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"{i}. **{title}**")
        if created:
            lines.append(f"   _{created[:10]}_")
        lines.append(f"   {content}")
        lines.append("")

    lines.append("*Recent corrections auto-injected by cks_context hook.*")
    return "\n".join(lines)


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
        cks_db_path = Path("P:/__csf/data/cks.db")

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
    """Inject CKS context when trigger phrases detected, plus recent corrections on analysis/final-answer turns.

    This function is registered manually in registry.py to avoid circular import.
    """
    # Check if enabled via environment
    if os.environ.get("CKS_INTEGRATION_ENABLED", "true").lower() not in ("1", "true", "yes"):
        return HookResult.empty()

    parts = []

    # 1. Existing trigger-phrase logic (unchanged)
    if _should_trigger_cks(context.prompt):
        results = _query_cks(context.prompt, max_results=5)
        if results:
            formatted = _format_cks_context(results, context.prompt)
            if formatted:
                parts.append(formatted)

    # 2. Auto-inject recent corrections on analysis/final-answer turns
    if _should_inject_recent_corrections(context.prompt):
        corrections = _query_hybrid_corrections(context.prompt, max_results=3, hours=24)
        if corrections:
            formatted = _format_recent_corrections(corrections, context.prompt)
            if formatted:
                parts.append(formatted)

    if not parts:
        return HookResult.empty()

    combined = "\n\n".join(parts)
    return HookResult.context_injection(combined)


# Add context_injection as a class method for compatibility
HookResult.context_injection = lambda content: HookResult(
    context=content,
    tokens=len(content.split()),
    priority=5.0
)
