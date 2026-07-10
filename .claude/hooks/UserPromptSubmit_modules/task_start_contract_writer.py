#!/usr/bin/env python3
"""
Task Start Contract Writer - Auto-creates task contracts for substantive software-dev prompts.

Integration point: UserPromptSubmit hook (via registry pattern).
Runs on every prompt to detect substantive task starts and create/update contracts
that the existing Stop task_contract_fit gate can then enforce.

Supported task classes:
- bug_diagnosis: "why is X crashing", "root cause of Y", "diagnose Z"
- bug_fix: "fix the bug", "patch X", "resolve the crash"
- implementation: "implement feature X", "add Y", "create Z module"
- refactor: "refactor X", "restructure Y"
- architecture_recommendation: "architect X", "design recommendation for Y"

Design constraints:
- Narrow and deterministic: No broad semantic classification.
- Terminal-scoped: Uses HookContext.terminal_id for multi-terminal isolation.
- Update semantics: Same task = update description; different task = replace.
- No reintroduction of lexical anchor matching at Stop-time.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Quote-aware request envelope (owned by unified_detection). Imported here so
# detection runs against outer user-authored text only — quoted/fenced proposal
# content can never contribute implementation/diagnostic intent signals.
try:
    from UserPromptSubmit_modules.request_envelope import strip_quoted_spans as _strip_spans
    from UserPromptSubmit_modules.unified_detection import ensure_request_envelope
except ImportError:  # pragma: no cover - test/standalone import paths
    from request_envelope import strip_quoted_spans as _strip_spans  # type: ignore[no-redef]

    def ensure_request_envelope(context):  # type: ignore[misc]
        return None


def _outer_text(prompt: str) -> str:
    """Return prompt with quoted/fenced/blockquote spans removed (outer text)."""
    if not prompt:
        return ""
    outer, _spans = _strip_spans(prompt)
    return outer.strip()

# Import the task contract helper (already implemented)
try:
    from __lib.task_contract import load_contract, save_contract, clear_contract
except ImportError:
    # Fallback for testing without __lib__ in path
    import sys
    from pathlib import Path
    hooks_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(hooks_dir / "__lib"))
    from task_contract import load_contract, save_contract, clear_contract

# ── Telemetry ────────────────────────────────────────────────────────────────

_TELEMETRY_LOG = None  # Lazy init to avoid import order issues


def _get_telemetry_log_path():
    global _TELEMETRY_LOG
    if _TELEMETRY_LOG is None:
        from pathlib import Path
        _TELEMETRY_LOG = Path(__file__).resolve().parent.parent / "logs" / "diagnostics" / "task_contract_writer_telemetry.jsonl"
        _TELEMETRY_LOG.parent.mkdir(parents=True, exist_ok=True)
    return _TELEMETRY_LOG


def _log_telemetry(event: str, terminal_id: str, fields: dict[str, Any]) -> None:
    """Append structured telemetry for task contract writer."""
    try:
        import json
        import time
        entry = {
            "timestamp": time.time(),
            "feature": "task_contract_writer",
            "event": event,
            "terminal_id": terminal_id,
            **fields,
        }
        with _get_telemetry_log_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass  # Observability must never change hook behavior


# ── Task type classification ────────────────────────────────────────────────

class TaskType(str, Enum):
    """Task type enum for contract routing (internal only)."""
    CODE_CHANGE = "code_change"         # bug_fix, implementation, refactor
    CODE_DIAGNOSIS = "code_diagnosis"   # bug_diagnosis
    OPERATIONAL_INGEST = "operational_ingest"  # /crawl, wiki update, ingest
    RESEARCH_DESIGN = "research_design"        # architecture, design, compare
    OTHER = "other"                            # chat, meta, control


# Operational/ingest task patterns (don't attach code contracts)
_OPERATIONAL_INGEST_RE = re.compile(
    r"\b(/crawl|/wiki|/ingest|wiki\s+update|index\s+update|"
    r"qmd\s+update|crawl\s+and\s+(?:update|ingest|index)|"
    r"refresh\s+(?:knowledge|index|wiki)|"
    r"update\s+(?:knowledge|index|wiki)\b)",
    re.IGNORECASE
)

# Research/design task patterns (don't attach code contracts)
_RESEARCH_DESIGN_ALT = (
    r'design\s+(?:pattern|system|approach|solution)|'
    r'architect(?:ure)?|propose\s+architecture|system\s+design|'
    r'compare\s+(?:options|approaches|frameworks|libraries)|'
    r'evaluate\s+(?:options|alternatives|tradeoffs)|'
    r'should\s+we\s+(?:use|choose|implement|refactor)'
)
_RESEARCH_DESIGN_RE = re.compile(r'\b(' + _RESEARCH_DESIGN_ALT + r')\b', re.IGNORECASE)

# Code change patterns. Bare "make" deliberately excluded — "make sense" / "make
# sure" must never classify as implementation. Detection runs on outer text
# (see _outer_text) so quoted proposal content cannot contribute either.
_CODE_CHANGE_ALT = (
    r'implement|add\s+(?:a\s+)?|create\s+(?:a\s+)?|'
    r'build|write|develop|introduce|fix\s+the?|'
    r'patch|resolve|repair|update\s+(?:function|module|class|method)|'
    r'add\s+(?:to|into|in)|modify\s+(?:function|module|class|method)|'
    r'change\s+(?:the\s+)?(?:code|function|logic|behavior)|'
    r'replace\s+(?:function|method|code|logic)|'
    r'add\s+(?:error|validation|handler|check)'
)
_CODE_CHANGE_RE = re.compile(r'\b(' + _CODE_CHANGE_ALT + r')\b', re.IGNORECASE)


def _classify_task_type(prompt: str) -> TaskType:
    """Classify task type for contract routing.

    Separates 'what kind of task' from 'which contract applies'.
    Only CODE_CHANGE and CODE_DIAGNOSIS get the full code contract.

    Detection runs on outer text (quotes/fences removed) so quoted proposal
    content cannot signal implementation/diagnosis.
    """
    if not prompt:
        return TaskType.OTHER

    normalized = prompt.strip()
    outer = _outer_text(prompt)

    # Check for operational/ingest tasks first (highest specificity) — operate
    # on the raw prompt so slash commands like /crawl still resolve.
    if _OPERATIONAL_INGEST_RE.search(normalized):
        return TaskType.OPERATIONAL_INGEST

    # Check for research/design tasks — on outer text.
    if _RESEARCH_DESIGN_RE.search(outer):
        return TaskType.RESEARCH_DESIGN

    # Code diagnosis: explicit diagnostic signals (outer text only)
    has_diag_kw = bool(_BUG_DIAGNOSIS_TRIGGERS_RE.search(outer))
    has_diag_q = bool(_BUG_DIAGNOSIS_QUESTION_RE.search(outer) or _BUG_DIAGNOSIS_SHORT_QUESTION_RE.match(outer.strip()) or _BUG_DIAGNOSIS_CAUSE_RE.search(outer))
    if has_diag_kw and has_diag_q:
        return TaskType.CODE_DIAGNOSIS

    # Code change: explicit action/creation signals (outer text only)
    if _CODE_CHANGE_RE.search(outer):
        return TaskType.CODE_CHANGE

    # Refactor is a code change (outer text only)
    if _REFACTOR_RE.search(outer):
        return TaskType.CODE_CHANGE

    return TaskType.OTHER


# ── Detection patterns ────────────────────────────────────────────────────────

# Bug diagnosis: diagnostic keywords + question/causal indicators.
# Word-boundary regex; no bare substring matches like "crash" inside "crash
# recovery policy doc". Multi-word phrases use \s+ to avoid "race condition"
# matching "race" alone.
_BUG_DIAGNOSIS_TRIGGERS_RE = re.compile(
    r"\b(?:crash(?:es|ing)?|errors?|fails?|failing|failed|failure|"
    r"bugs?|issues?|broken|undefined|null|exception|traceback|"
    r"underflow|overflow|deadlock|race\s+condition|stack\s+trace)\b",
    re.IGNORECASE,
)
# Legacy frozenset retained for any external consumer / introspection.
_BUG_DIAGNOSIS_TRIGGERS = frozenset({
    "crash", "crashing", "crashes",
    "error", "errors",
    "fail", "fails", "failing", "failed",
    "bug", "bugs",
    "issue", "issues",
    "broken",
    "null", "undefined", "exception",
    "stack trace", "traceback",
    "overflow", "underflow",
    "deadlock", "race condition",
})
# Matches "why is X", "what is causing X", "what causes X"
_BUG_DIAGNOSIS_QUESTION_RE = re.compile(
    r"\b(why|what|how|debug|diagnose|investigate|root cause|cause of|trace|causing|caused by)\b",
    re.IGNORECASE
)
# Matches prompts that START with a question word (short diagnostic questions)
_BUG_DIAGNOSIS_SHORT_QUESTION_RE = re.compile(
    r"^(why|what|how|debug|diagnose|investigate)\b",
    re.IGNORECASE
)
# Matches "what is causing" / "what causes" (explicit causal questions)
_BUG_DIAGNOSIS_CAUSE_RE = re.compile(
    r"what\s+(?:is\s+)?(?:causing|causes|triggering|triggered)\b",
    re.IGNORECASE
)

# Bug fix: word-boundary regex for fix keywords (not bare substring "fix").
_FIX_TRIGGERS_RE = re.compile(
    r"\b(?:fix(?:es|ed|ing)?|patch(?:es|ed|ing)?|resolve[ds]?|"
    r"resolving|repair(?:s|ed|ing)?|recover(?:s|ed|ing)?|heal(?:s|ed|ing)?)\b",
    re.IGNORECASE,
)
# Legacy frozenset retained for compatibility.
_FIX_TRIGGERS = frozenset({
    "fix", "fixing", "fixed",
    "patch", "patching",
    "resolve", "resolving", "resolved",
    "repair", "repairing",
    "recover", "recovering",
    "heal", "healing",
})
# Exploration patterns that suggest this is a discussion, not a fix request
_EXPLORATION_RE = re.compile(
    r"\b(should we|alternative|tradeoff|trade-off|pros and cons|"
    r"better approach|consider|worth considering|versus|vs\.)\b",
    re.IGNORECASE
)

# Implementation: word-boundary regex. NOTE: bare "make" is intentionally
# excluded — "make sense", "make sure" must never trigger implementation.
_IMPL_TRIGGERS_RE = re.compile(
    r"\b(?:implement(?:s|ed|ing|ation)?|create[ds]?|creating|"
    r"build(?:s|ing|built)?|writ(?:e|es|ing|ten)?|develop(?:s|ed|ing|ment)?|"
    r"add(?:s|ed|ing)?|introduce[ds]?|introducing)\b",
    re.IGNORECASE,
)
# Legacy frozenset (for introspection / external callers; not used in
# detection after the word-boundary migration).
_IMPL_TRIGGERS = frozenset({
    "implement", "implementation",
    "create", "creating", "created",
    "build", "building", "built",
    "write", "writing", "writes",
    "develop", "developing", "developed",
    "add", "adding", "added",
    "make", "making", "makes",
    "introduce", "introducing",
})
_IMPL_EXCLUDE_RE = re.compile(
    r"\b(fix|patch|repair|resolve|bug|broken|error|crash)\b",
    re.IGNORECASE
)

# Refactor: explicit refactor keyword only
_REFACTOR_RE = re.compile(r"\brefactor(?:ing|ed|s)?\b", re.IGNORECASE)

# Architecture recommendation: architect/design keyword
_ARCH_RE = re.compile(
    r"\b(architect(?:ure|ing|ed)?|design\s+(?:pattern|system|approach|solution)|"
    r"propose\s+architecture|system\s+design)\b",
    re.IGNORECASE
)

# Software-dev keywords for context-aware continuation
_SOFTWARE_DEV_KEYWORDS = frozenset({
    "bug", "bugs", "error", "errors", "exception", "crash", "crashing",
    "fix", "fixing", "fixed", "patch", "patching", "resolve", "resolving",
    "implement", "implementation", "add", "adding", "create", "creating",
    "build", "building", "write", "writing", "refactor", "refactoring",
    "test", "testing", "tests", "debug", "debugging", "debugged",
    "code", "function", "method", "class", "module", "api", "endpoint",
    "database", "query", "sql", "config", "configuration", "deploy",
    "deploying", "deployment", "install", "installing", "setup", "setting up",
    "runtime", "startup", "start", "running", "run", "execute", "execution",
    "variable", "constant", "import", "export", "return", "parameter",
    "argument", "callback", "handler", "event", "loop", "condition",
    "null", "undefined", "none", "empty", "missing", "undefined",
    "stack", "trace", "traceback", "overflow", "leak", "memory",
    "timeout", "connection", "request", "response", "header", "body",
    "auth", "authentication", "authorization", "token", "session",
    "file", "path", "directory", "folder", "script", "shell", "command",
    "terminal", "console", "output", "input", "stdin", "stdout", "stderr",
    "hook", "hooks", "plugin", "skill", "command", "cli", "tool",
})

# Control patterns: skip these
_CONTROL_RE = re.compile(
    r"^(stop|skip|bypass|override|ignore|actually|wait|"
    r"redo|re-read|recheck|re-examine|re-open)\b",
    re.IGNORECASE
)

# ── Task class detection ──────────────────────────────────────────────────────


def _detect_task_class(prompt: str) -> str | None:
    """Classify the prompt into a supported task class, or None if not applicable.

    Returns:
        One of: "bug_diagnosis", "bug_fix", "implementation", "refactor",
        "architecture_recommendation", or None (not a task start).

    Detection runs against OUTER TEXT (quotes/fences/blockquote stripped) so
    quoted proposal content cannot contribute intent signals. Word-boundary
    regexes replace substring `in` checks; bare "make" is intentionally
    excluded from impl triggers.
    """
    if not prompt:
        return None

    normalized = prompt.strip()
    outer = _outer_text(prompt)
    outer_lower = outer.lower()

    # Skip control commands
    if _CONTROL_RE.match(normalized):
        return None

    # ── bug_diagnosis ──────────────────────────────────────────────────────────
    has_diag_kw = bool(_BUG_DIAGNOSIS_TRIGGERS_RE.search(outer))
    has_question_kw = bool(_BUG_DIAGNOSIS_QUESTION_RE.search(outer))
    has_short_question = bool(_BUG_DIAGNOSIS_SHORT_QUESTION_RE.match(outer))
    has_cause_question = bool(_BUG_DIAGNOSIS_CAUSE_RE.search(outer))
    # Must have diagnostic keyword AND (question word OR causal indicator)
    if has_diag_kw and (has_question_kw or has_short_question or has_cause_question):
        return "bug_diagnosis"

    # ── bug_fix ───────────────────────────────────────────────────────────────
    has_fix_kw = bool(_FIX_TRIGGERS_RE.search(outer))
    has_exploration = bool(_EXPLORATION_RE.search(outer))
    has_impl_kw = bool(_IMPL_TRIGGERS_RE.search(outer))
    # When both fix and impl keywords present, impl takes precedence
    # (e.g., "fix the build script" → impl, "build a fix" → impl)
    if has_fix_kw and not has_exploration and not has_impl_kw:
        # Additional check: must not be a question (bug_diagnosis handles questions)
        if "?" not in outer or "fix" in outer_lower:
            return "bug_fix"

    # ── implementation ────────────────────────────────────────────────────────
    has_impl_exclude = bool(_IMPL_EXCLUDE_RE.search(outer))
    if has_impl_kw and not has_impl_exclude:
        return "implementation"

    # ── exploration BEFORE refactor ──────────────────────────────────────────
    # "Should we refactor" is exploration, not a refactor task
    if has_exploration:
        return None

    # ── refactor ──────────────────────────────────────────────────────────────
    if _REFACTOR_RE.search(outer):
        return "refactor"

    # ── architecture_recommendation ────────────────────────────────────────────
    if _ARCH_RE.search(outer):
        return "architecture_recommendation"

    return None


# ── Required outputs mapping ─────────────────────────────────────────────────


_TASK_REQUIRED_OUTPUTS: dict[str, list[str]] = {
    "bug_diagnosis": ["root_cause", "fix", "verification_commands"],
    "bug_fix": ["root_cause", "fix", "tests", "verification_commands"],
    "implementation": ["fix", "tests", "verification_commands"],
    "refactor": ["fix", "tests", "verification_commands"],
    "architecture_recommendation": ["fix", "verification_commands"],
}


# ── Update semantics ──────────────────────────────────────────────────────────


def _compute_task_id(prompt: str) -> str:
    """Derive a stable task_id from the prompt's subject matter.

    Uses a hash of the normalized, keywords-extracted prompt content
    to produce a consistent ID across re-prompts of the same task.
    """
    import hashlib
    normalized = prompt.strip().lower()
    # Remove common filler words to get at the subject
    filler = {"the", "a", "an", "to", "for", "of", "in", "on", "at", "by",
              "is", "are", "was", "were", "be", "been", "being"}
    words = [w for w in normalized.split() if w not in filler and len(w) > 1]
    subject = " ".join(sorted(set(words)))[:100]
    digest = hashlib.md5(subject.encode()).hexdigest()[:8]
    return f"tc-{digest}"


def _tasks_are_related(task_id: str, existing: dict, new_prompt: str) -> bool:
    """Check if new_prompt is likely the same task as the existing contract.

    Uses word overlap to determine relatedness, independent of task_id
    (which may differ due to minor wording changes).
    """
    # Overlap check: significant word overlap suggests same task
    existing_words = set((existing.get("description") or "").lower().split())
    new_words = set(new_prompt.strip().lower().split())
    if not existing_words:
        return False
    overlap = len(existing_words & new_words) / len(existing_words)
    return overlap >= 0.5


# ── Core contract management ──────────────────────────────────────────────────


def _ensure_contract(
    terminal_id: str,
    task_class: str,
    prompt: str,
) -> str:
    """Create or update a task contract for this terminal.

    Returns:
        Action taken: "create", "update", "replace", or "skip"
    """
    task_id = _compute_task_id(prompt)
    existing = load_contract(terminal_id)

    description = _summarize_prompt(prompt)
    required_outputs = _TASK_REQUIRED_OUTPUTS.get(task_class, [])

    if existing is None:
        # No existing contract - create new
        save_contract(
            terminal_id,
            task_id=task_id,
            description=description,
            required_outputs=required_outputs,
            task_class=task_class,
        )
        _log_telemetry("contract_create", terminal_id, {
            "task_class": task_class,
            "task_id": task_id,
            "required_outputs": required_outputs,
        })
        return "create"

    # Existing contract found - check if same task
    if _tasks_are_related(task_id, existing, prompt):
        # Same task - update description and required_outputs
        save_contract(
            terminal_id,
            task_id=task_id,
            description=description,
            required_outputs=required_outputs,
            task_class=task_class,
        )
        _log_telemetry("contract_update", terminal_id, {
            "task_class": task_class,
            "task_id": task_id,
            "required_outputs": required_outputs,
        })
        return "update"

    # Different task - replace
    save_contract(
        terminal_id,
        task_id=task_id,
        description=description,
        required_outputs=required_outputs,
        task_class=task_class,
    )
    _log_telemetry("contract_replace", terminal_id, {
        "task_class": task_class,
        "task_id": task_id,
        "required_outputs": required_outputs,
    })
    return "replace"


def _summarize_prompt(prompt: str) -> str:
    """Create a short description of the task from the prompt."""
    # Truncate and clean up
    cleaned = prompt.strip()[:200]
    if len(prompt) > 200:
        cleaned = cleaned.rsplit(" ", 1)[0] + "..."
    return cleaned


# ── Hook registration ─────────────────────────────────────────────────────────

def _fallback_terminal_id() -> str:
    """Fallback terminal ID when context.terminal_id is empty (no WT_SESSION).

    Mirrors PreToolUse_delegation_gate._detect_terminal_id() fallback chain:
    WT_SESSION -> CLAUDE_TERMINAL_ID -> hash(PID+cwd).
    """
    import hashlib
    import os as _os
    fallback = _os.environ.get("CLAUDE_TERMINAL_ID", "")
    if fallback:
        return f"console_{fallback}"
    pid = _os.getpid()
    cwd = _os.getcwd()
    return f"unknown_{hashlib.md5(f'{pid}:{cwd}'.encode()).hexdigest()[:12]}"


@register_hook("task_start_contract_writer", priority=4.0)
def task_start_contract_writer(context: HookContext) -> HookResult:
    """UserPromptSubmit hook that auto-creates task contracts on substantive prompts.

    Priority 4.0 runs:
    - AFTER skill detection hooks (so we can avoid conflicts with skill contracts)
    - BEFORE most context injection hooks

    Quote-aware + fail-open: the shared request envelope classifies the prompt
    into evaluation / implementation / diagnosis / research / status / mixed /
    ambiguous. Only implementation + diagnosis may create code contracts;
    evaluation, research, status, mixed, and ambiguous prompts never create a
    contract — even when implementation/diagnosis words appear inside quoted
    proposal text.

    Context-aware continuation:
    - If explicit task phrasing → create/update as now
    - If ambiguous phrasing BUT active contract exists from recent turns → update
    - If evaluation/research/status/mixed → never update (fail open).
    """
    # Extract terminal_id; fall back to PID+cwd hash when WT_SESSION is absent
    terminal_id = context.terminal_id or _fallback_terminal_id()

    prompt = context.prompt or ""
    outer = _outer_text(prompt)

    # Quote-aware request envelope (owned by unified_detection). If unavailable
    # for any reason, fall through to the legacy behavior below.
    envelope = ensure_request_envelope(context)
    if envelope is not None:
        # Fail-open gate: non-action modes never create a code contract.
        if envelope.mode in ("evaluation", "research", "status", "mixed"):
            _log_telemetry("contract_skip", terminal_id, {
                "reason": f"{envelope.mode}_mode",
                "envelope_reason": envelope.reason,
                "outer_preview": outer[:50],
                "prompt_preview": prompt[:50],
            })
            return HookResult.empty()
        # Ambiguous + no clear action signal: defer to legacy detection below;
        # if nothing resolves, continue skip path naturally.

    # First: try explicit task class detection (now quote-aware + word-boundary)
    task_class = _detect_task_class(prompt)

    if task_class is None:
        # No explicit task class detected.
        # Check for context-aware continuation: ambiguous prompt + active contract + dev keywords
        existing = load_contract(terminal_id)
        if existing and existing.get("status") != "completed":
            # Only update if existing contract is a code type AND envelope mode
            # is genuinely ambiguous (not evaluation/research/status/mixed).
            envelope_allows_continuation = (
                envelope is None or envelope.mode == "ambiguous"
            )
            if envelope_allows_continuation:
                existing_class = existing.get("task_class", "")
                code_classes = {"bug_diagnosis", "bug_fix", "implementation", "refactor"}
                # Dev-keyword check runs on OUTER text so quoted content cannot
                # manufacture a continuation signal.
                has_dev_keywords = any(kw in outer.lower() for kw in _SOFTWARE_DEV_KEYWORDS)
                if existing_class in code_classes and has_dev_keywords:
                    action = _ensure_contract(terminal_id, existing_class, prompt)
                    _log_telemetry("contract_context_update", terminal_id, {
                        "action": action,
                        "reason": "ambiguous_with_active_contract",
                        "prompt_preview": prompt[:50],
                    })
                    return HookResult.empty()

        # No explicit task AND no context for continuation → skip
        _log_telemetry("contract_skip", terminal_id, {
            "reason": "not_a_task_start",
            "prompt_preview": prompt[:50] if prompt else "",
        })
        return HookResult.empty()

    # Validate: only CODE_CHANGE and CODE_DIAGNOSIS get code contracts
    task_type = _classify_task_type(prompt)
    if task_type not in (TaskType.CODE_CHANGE, TaskType.CODE_DIAGNOSIS):
        _log_telemetry("contract_skip", terminal_id, {
            "reason": f"task_type_{task_type.value}",
            "task_class": task_class,
            "prompt_preview": prompt[:50] if prompt else "",
        })
        return HookResult.empty()

    # Explicit task class detected - ensure contract exists
    action = _ensure_contract(terminal_id, task_class, prompt)

    # The contract is written to disk - no context injection needed.
    # The Stop task_contract_fit gate will pick it up and enforce completion.
    _log_telemetry("contract_active", terminal_id, {
        "action": action,
        "task_class": task_class,
        "task_type": task_type.value,
        "prompt_preview": prompt[:50] if prompt else "",
    })
    return HookResult.empty()


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        # (prompt, expected_task_class_or_None)
        # Bug diagnosis
        ("Why is the parser crashing on empty input?", "bug_diagnosis"),
        ("root cause of the null pointer exception", "bug_diagnosis"),
        ("debug why the test is failing", "bug_diagnosis"),
        ("diagnose the crash at startup", "bug_diagnosis"),
        ("What is causing the stack overflow?", "bug_diagnosis"),
        # Bug fix
        ("fix the null pointer in handler.py", "bug_fix"),
        ("patch the race condition in the worker", "bug_fix"),
        ("resolve the memory leak", "bug_fix"),
        ("fix the bug where sessions timeout early", "bug_fix"),
        # Implementation
        ("implement a rate limiter for the API", "implementation"),
        ("add a retry mechanism to the client", "implementation"),
        ("create a new module for cache management", "implementation"),
        ("build a health check endpoint", "implementation"),
        ("write a logging utility", "implementation"),
        # Refactor
        ("refactor the auth module to use JWT", "refactor"),
        ("refactoring the database layer", "refactor"),
        # Architecture
        ("architect the microservices communication", "architecture_recommendation"),
        ("design pattern for the plugin system", "architecture_recommendation"),
        # NOT task starts
        ("Should we refactor or consolidate?", None),  # exploration
        ("stop", None),  # control
        ("What is the weather like?", None),  # question without task keywords
        ("Tell me about the codebase", None),  # info request
        ("run the tests", None),  # control (short imperative)
        ("actually, re-read the file", None),  # control
    ]

    print("Task Start Contract Writer Self-Test")
    print("=" * 60)

    failed = 0
    for prompt, expected in test_cases:
        actual = _detect_task_class(prompt)
        status = "✓" if actual == expected else "✗"
        if actual != expected:
            failed += 1
            print(f"{status} '{prompt[:45]}' → expected={expected}, actual={actual}")
        else:
            print(f"{status} '{prompt[:45]}' → {actual}")

    print(f"\n{'All passed' if failed == 0 else f'{failed} FAILED'}")