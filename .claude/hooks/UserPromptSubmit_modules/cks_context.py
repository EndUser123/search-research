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

def _normalize(text: str) -> set[str]:
    """Strip punctuation for robust keyword matching.

    "authentication," -> "authentication", "web-app" -> {"web", "app"}
    """
    import re

    if not text:
        return set()
    normalized = re.sub(r"[-_/]", " ", text.lower())
    words = [w.strip().strip(".,!?;:\"'()[]{}") for w in normalized.split()]
    return set(w for w in words if w)


# === Auto-correction injection for analysis/final-answer turns ===

CORRECTION_INJECTION_MODES = ("analysis", "final-answer", "meta")
# Thresholds calibrated to reality: keyword results carry a hardcoded 0.5,
# and empirical max semantic similarity is ~0.47 (unified.py:67). 0.7 filtered
# out 100% of results — the hook was silently dead.
CORRECTION_RELEVANCE_THRESHOLD = 0.4
KNOWLEDGE_RELEVANCE_THRESHOLD = 0.4
# Character budget (~300 tokens). Deliberately small: flood-avoidance is the
# priority; empty injection is the correct default.
MAX_INJECTION_CHARS = 1200

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

        prompt_words = _normalize(prompt)
        scored = []
        for row in rows:
            entry_words = _normalize((row[2] or "") + " " + (row[3] or ""))
            overlap = len(prompt_words & entry_words)
            scored.append((overlap, row))

        # Sort by overlap desc, then created_at desc
        scored.sort(key=lambda x: (x[0], x[1][5]), reverse=True)

        # Filter: require >=2 keyword overlaps. One shared word is noise on
        # short prompts; two is the cheapest precision floor that survived
        # corpus review (flood-avoidance directive, 2026-07-03).
        relevant = [(score, row) for score, row in scored if score >= 2]
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


def _query_hybrid_corrections(prompt: str, max_results: int = 5, hours: int = 24) -> list[dict]:
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

    # Add relevance scores for filtering (default to 0.5 for keyword-only results)
    scored = []
    for r in merged:
        # Keyword results don't have semantic similarity, default to 0.5
        score = r.get("similarity", 0.5)
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]


# Curated types only. "decision" excluded on purpose: 104 auto-captured decision
# rows are mostly sentence fragments (measured 2026-07-03); re-admit only after
# the Stop_cks_decision_capture extractor is fixed and rows are backfilled.
HOOK_KNOWLEDGE_TYPES = ("knowledge", "pattern", "insight", "learning")

# ponytail: default OFF. The semantic path opens CKS(enable_semantic=True) inline,
# loading torch+FAISS+model in a fresh subprocess every analysis-turn firing (~9s,
# returns empty, blew the UserPromptSubmit 15s ceiling). Keyword CKS over 78 rows is
# sub-ms and returns the same empty result today. Re-enable by setting
# CKS_KNOWLEDGE_SEMANTIC=true in settings.json — but only AFTER the semantic daemon
# is reliable (#669 broken FAISS imports, #934 pipe-busy health-check).
KNOWLEDGE_SEMANTIC_ENABLED = os.environ.get("CKS_KNOWLEDGE_SEMANTIC", "false").lower() in ("1", "true", "yes")
KNOWLEDGE_AUTO_INJECT_ENABLED = os.environ.get("CKS_KNOWLEDGE_AUTO_INJECT", "true").lower() in ("1", "true", "yes")


def _query_knowledge_base(prompt: str, max_results: int = 2) -> list[dict]:
    """Query CKS durable knowledge entries via semantic search (no time window).

    Unlike corrections (ephemeral, 24h), knowledge/pattern/decision entries are
    durable and should be searchable regardless of age. Uses semantic search so
    queries like "glm-5.1 model availability" match entries about "z.ai endpoint
    configuration" even without keyword overlap.
    """
    if not KNOWLEDGE_AUTO_INJECT_ENABLED:
        return []
    try:
        from cks.unified import CKS

        cks_db_path = Path("P:/__csf/data/cks.db")
        if not cks_db_path.exists():
            return []

        with CKS(db_path=cks_db_path, enable_semantic=KNOWLEDGE_SEMANTIC_ENABLED) as cks:
            results = cks.search(query=prompt, limit=max_results * 3)

        # Filter to durable knowledge types only
        filtered = [r for r in results if r.get("type") in HOOK_KNOWLEDGE_TYPES]
        return filtered[:max_results]

    except Exception:
        return []


def _format_knowledge_context(results: list[dict], prompt: str) -> str:
    """Format knowledge base results as context injection."""
    if not results:
        return ""

    lines = [
        "## Relevant CKS Knowledge",
        "",
    ]
    for i, result in enumerate(results, 1):
        title = result.get("title", "") or f"Entry {result.get('id')}"
        entry_type = result.get("type", "knowledge")
        content = result.get("content", "")
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"{i}. **[{entry_type}] {title}**")
        lines.append(f"   {content}")
        lines.append("")

    lines.append("*Knowledge auto-injected by cks_context hook.*")
    return "\n".join(lines)


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

    Keyword-overlap scoring over all entries (few hundred rows, sub-ms).
    Replaces the old `LIKE '%<entire prompt>%'` which could never match a
    multi-word prompt as a single substring.
    """
    try:
        cks_db_path = Path("P:/__csf/data/cks.db")

        if not cks_db_path.exists():
            return []

        import sqlite3

        conn = sqlite3.connect(cks_db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, type, title, content, metadata
            FROM entries
            ORDER BY usage_count DESC, created_at DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        prompt_words = _normalize(prompt)
        scored = []
        for row in rows:
            entry_words = _normalize((row[2] or "") + " " + (row[3] or ""))
            overlap = len(prompt_words & entry_words)
            # >=2 overlaps: same precision floor as the corrections path
            if overlap >= 2:
                scored.append((overlap, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "content": row[3],
                "metadata": row[4],
            }
            for _, row in scored[:max_results]
        ]

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

    for i, result in enumerate(filtered[:2], 1):  # Max 2 results (flood-avoidance)
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


def _injected_ids_file(session_id: str) -> Path:
    state_dir = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state")) / "cks_context_injected"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{session_id}.json"


def _load_injected_ids(session_id: str | None) -> set:
    """Entry ids already injected this session (dedupe). Fail-open to empty."""
    if not session_id:
        return set()
    try:
        import json

        return set(json.loads(_injected_ids_file(session_id).read_text(encoding="utf-8")))
    except Exception:
        return set()


def _mark_injected(session_id: str | None, ids: set) -> None:
    if not session_id or not ids:
        return
    try:
        import json

        f = _injected_ids_file(session_id)
        existing = _load_injected_ids(session_id)
        f.write_text(json.dumps(sorted(existing | ids)), encoding="utf-8")
    except Exception:
        pass  # Dedupe is best-effort; never block injection


def _dedupe(results: list[dict], seen: set) -> list[dict]:
    """Drop entries already injected this session (entries without id pass through)."""
    return [r for r in results if r.get("id") is None or r["id"] not in seen]


def cks_context_hook(context: HookContext) -> HookResult:
    """Inject CKS context when trigger phrases detected, plus recent corrections on analysis/final-answer turns.

    This function is registered manually in registry.py to avoid circular import.
    """
    # Check if enabled via environment
    if os.environ.get("CKS_INTEGRATION_ENABLED", "true").lower() not in ("1", "true", "yes"):
        return HookResult.empty()

    parts = []
    seen_ids = _load_injected_ids(context.session_id)
    new_ids: set = set()

    def _track(results: list[dict]) -> None:
        new_ids.update(r["id"] for r in results if r.get("id") is not None)

    # 1. Existing trigger-phrase logic (unchanged)
    if _should_trigger_cks(context.prompt):
        results = _dedupe(_query_cks(context.prompt, max_results=5), seen_ids)
        if results:
            formatted = _format_cks_context(results, context.prompt)
            if formatted:
                parts.append(formatted)
                _track(results)

    # 2. Auto-inject recent corrections on analysis/final-answer turns (with relevance gating)
    if _should_inject_recent_corrections(context.prompt):
        corrections = _query_hybrid_corrections(context.prompt, max_results=5, hours=24)
        # Filter by relevance threshold
        corrections = [c for c in corrections if c.get("similarity", 0) >= CORRECTION_RELEVANCE_THRESHOLD]
        corrections = _dedupe(corrections, seen_ids)
        if corrections:
            formatted = _format_recent_corrections(corrections, context.prompt)
            if formatted:
                parts.append(formatted)
                _track(corrections)

    # 3. Auto-inject relevant knowledge on analysis/final-answer turns (with relevance gating)
    if _should_inject_recent_corrections(context.prompt):
        knowledge = _query_knowledge_base(context.prompt, max_results=2)
        # Threshold applies only when a similarity score exists (semantic path).
        # Keyword-path results carry no score; they already passed keyword match.
        knowledge = [
            k for k in knowledge
            if k.get("similarity") is None or k["similarity"] >= KNOWLEDGE_RELEVANCE_THRESHOLD
        ]
        knowledge = _dedupe(knowledge, seen_ids)
        if knowledge:
            formatted = _format_knowledge_context(knowledge, context.prompt)
            if formatted:
                parts.append(formatted)
                _track(knowledge)

    if not parts:
        return HookResult.empty()

    # Character budgeting (~300 tokens). The old code compared len() in chars
    # against a 500-"token" constant — a units bug that capped output at ~125 tokens.
    combined = "\n\n".join(parts)
    if len(combined) > MAX_INJECTION_CHARS:
        combined = combined[:MAX_INJECTION_CHARS - 50] + "\n... [truncated]"

    _mark_injected(context.session_id, new_ids)
    return HookResult.context_injection(combined)


# Add context_injection as a class method for compatibility
HookResult.context_injection = lambda content: HookResult(
    context=content,
    tokens=len(content.split()),
    priority=5.0
)
