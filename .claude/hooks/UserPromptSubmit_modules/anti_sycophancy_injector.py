"""Anti-sycophancy Layer 1 injector for UserPromptSubmit registry flow.

Registry-compatible equivalent of anti_sycophancy/advocate_injection.py with:
- Session+terminal scoped state (multi-terminal safe)
- Signature dedupe (avoid repeated inject spam)
- Escalation ladder (first trigger full/light, repeats reduce verbosity)

No TTL is used. State is updated deterministically by prompt signatures.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

MAX_RECENT_SIGNATURES = 24

HIGH_STAKES_PATTERNS = [
    r"is that (?:really|truly|actually)\s+(?:the\s+)?(?:best|optimal|right)",
    r"(?:shouldn't|wouldn't|couldn't)\s+we\s+(?:just|instead|rather)",
    r"you\s+(?:overcomplicated|overengineered|went too far)",
    r"(?:that's|it's|this is)\s+(?:way\s+)?too\s+(?:complex|complicated|much)",
    # Escalation-level pushback (user asserting AI is wrong about a fact)
    r"i\s+(?:just\s+)?told\s+you",
    r"you\s+(?:missed|overlooked|ignored|removed|deleted|changed)",
    r"did\s+you\s+just\s+remove",
    r"without\s+(?:even\s+)?consider(?:ing|ation)",
    r"(?:fire|replace)\s+you",
    r"(?:better|worse)\s+model",
    r"you'?re\s+(?:wrong|not\s+listening|ignoring)",
    r"(?:that's|it's|this\s+is)\s+(?:a\s+)?(?:bug|broken|error)",
    # Factual challenges - user contradicts a claim with their own knowledge
    r"i\s+thought\s+(?:we|it|all|our|the|this|that)\s+",
    r"(?:you'?re|you\s+are)\s+gaslighting",
    r"it\s+never\s+\w+\s+(?:until|before|unless)",
    r"that'?s\s+not\s+(?:what|how|true|right|correct)",
    r"(?:no|nope),?\s+(?:we|it|that|this)\s+(?:actually|already|never|always)",
    r"we\s+(?:already|never)\s+(?:had|have|did|do|were|are)\s+",
    # Direct contradiction of AI output
    r"(?:but|except)\s+(?:we|I|it)\s+(?:already|never|always|actually)",
    r"why\s+did\s+(?:you|our\s+hooks?|the\s+system)\s+(?:fail|miss|not)",
]

LOW_STAKES_PATTERNS = [
    r"are you sure",
    r"(?:is|are)\s+that\s+(?:necessary|needed)",
    r"(?:seems|looks)\s+(?:overly|unnecessarily)",
    r"(?:i\s+)?(?:don't|do not)\s+think",
    r"let's\s+not",
    # Gentle factual questions that imply disagreement
    r"(?:didn't|doesn't|isn't|aren't|wasn't|weren't)\s+(?:we|it|that|this)\s+(?:already|supposed)",
    r"what\s+(?:about|happened\s+to)\s+(?:the|our|my)",
]

HIGH_STAKES_REGEX = [re.compile(p, re.IGNORECASE) for p in HIGH_STAKES_PATTERNS]
LOW_STAKES_REGEX = [re.compile(p, re.IGNORECASE) for p in LOW_STAKES_PATTERNS]

FULL_ADVOCATE_PROTOCOL = """
<ADVOCATE_PROTOCOL>
The user is challenging your claim. Do NOT agree or apologize yet.

1) INVESTIGATE FIRST: Use tools (Read, Grep, Glob, Bash) to gather evidence about the disputed claim
2) Arguments supporting the user's position (with evidence)
3) Arguments supporting your prior claim (with evidence)
4) Conclusion based on what the evidence shows — not on who said it

Do not start with "You're right" or any agreement/apology before investigation.
Do not rewrite history — state what actually happened.

Before finalizing your response:
- State what behavior is actually in dispute.
- For each claim you make, mark its STATUS:
    STATUS: TESTED_IN_ENV   — you ran it with Bash and saw the output
    STATUS: INFERRING_FROM_CODE — you read the source and are reasoning about behavior
    STATUS: INFERRING_FROM_DOCS — you read documentation only
- If any claim is STATUS: INFERRING_FROM_DOCS and the user is challenging runtime behavior,
  you MUST run the command with Bash before asserting it.
</ADVOCATE_PROTOCOL>
""".strip()

LIGHT_ADVOCATE_PROTOCOL = """
<ADVOCATE_PROTOCOL_LIGHT>
Before agreeing:
1) Restate the conclusion and the specific evidence that supported it.
2) Check whether this challenge actually invalidates that evidence.
3) Update the conclusion only if the evidence is genuinely undermined.
</ADVOCATE_PROTOCOL_LIGHT>
""".strip()

HIGH_FOLLOWUP_PROTOCOL = """
<ADVOCATE_PROTOCOL_FOLLOWUP>
Continue adversarial reasoning, but be concise:
- 1 strongest pro argument
- 1 strongest counterargument
- final decision tied to evidence
</ADVOCATE_PROTOCOL_FOLLOWUP>
""".strip()


def _is_enabled() -> bool:
    return os.environ.get("ANTI_SYCOPHANCY_ENABLED", "true").lower() in ("1", "true", "yes")


def _safe_id(value: str | None) -> str:
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _resolve_scope(context: HookContext) -> tuple[str, str]:
    data = context.data or {}
    session_id = (
        context.session_id
        or data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or ""
    )
    terminal_id = (
        context.terminal_id
        or data.get("terminal_id")
        or data.get("terminalId")
        or data.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID")
        or ""
    )
    return str(session_id), str(terminal_id)


def _state_dirs() -> list[Path]:
    primary = Path("P:/.claude/hooks/state/anti_sycophancy_injector")
    fallback = Path(tempfile.gettempdir()) / "claude_hooks" / "state" / "anti_sycophancy_injector"
    if os.environ.get("PYTEST_CURRENT_TEST"):
        # Keep pytest runs hermetic: never read/write real hook state.
        return [fallback]
    return [primary, fallback]


def _state_file_candidates(session_id: str, terminal_id: str) -> list[Path]:
    filename = f"{_safe_id(session_id)}__{_safe_id(terminal_id)}.json"
    candidates: list[Path] = []
    for base in _state_dirs():
        try:
            base.mkdir(parents=True, exist_ok=True)
            candidates.append(base / filename)
        except OSError:
            continue
    return candidates


def _load_state(paths: list[Path]) -> dict:
    for path in paths:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


def _save_state(paths: list[Path], state: dict) -> None:
    for path in paths:
        try:
            path.write_text(json.dumps(state), encoding="utf-8")
            return
        except OSError:
            continue
    return


def _normalize_prompt(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _signature(text: str) -> str:
    return hashlib.sha1(_normalize_prompt(text).encode("utf-8")).hexdigest()


def _classify_prompt(prompt: str) -> str:
    if any(rx.search(prompt) for rx in HIGH_STAKES_REGEX):
        return "high"
    if any(rx.search(prompt) for rx in LOW_STAKES_REGEX):
        return "low"
    return "none"


def _next_consecutive_count(state: dict, trigger_level: str) -> int:
    prev_level = str(state.get("last_trigger_level", "none"))
    prev_count = int(state.get("consecutive_trigger_count", 0))
    if prev_level == trigger_level:
        return prev_count + 1
    return 1


def _select_protocol(trigger_level: str, consecutive: int) -> str | None:
    if trigger_level == "high":
        if consecutive <= 1:
            return FULL_ADVOCATE_PROTOCOL
        return HIGH_FOLLOWUP_PROTOCOL
    if trigger_level == "low":
        if consecutive <= 1:
            return LIGHT_ADVOCATE_PROTOCOL
        # Anti-pattern guard: repeated low-stakes injections create prompt numbness.
        return None
    return None


def _update_state(state: dict, sig: str, trigger_level: str, consecutive: int) -> dict:
    recent = state.get("recent_signatures", [])
    if not isinstance(recent, list):
        recent = []
    recent = [str(x) for x in recent if isinstance(x, str)]
    if sig not in recent:
        recent.append(sig)
    if len(recent) > MAX_RECENT_SIGNATURES:
        recent = recent[-MAX_RECENT_SIGNATURES:]
    return {
        "version": 1,
        "last_trigger_level": trigger_level,
        "consecutive_trigger_count": consecutive if trigger_level != "none" else 0,
        "last_signature": sig,
        "recent_signatures": recent,
    }


def _challenge_marker_path(session_id: str, terminal_id: str) -> Path:
    """Return path for cross-hook challenge marker (read by Stop.py)."""
    filename = f"challenge__{_safe_id(session_id)}__{_safe_id(terminal_id)}.json"
    for base in _state_dirs():
        try:
            base.mkdir(parents=True, exist_ok=True)
            return base / filename
        except OSError:
            continue
    return (
        Path(tempfile.gettempdir())
        / "claude_hooks"
        / "state"
        / "anti_sycophancy_injector"
        / filename
    )


def _write_challenge_marker(session_id: str, terminal_id: str, trigger_level: str) -> None:
    """Write marker so Stop.py knows a challenge was detected this turn."""
    import time

    marker = _challenge_marker_path(session_id, terminal_id)
    try:
        marker.write_text(
            json.dumps(
                {
                    "timestamp": time.time(),
                    "trigger_level": trigger_level,
                    "session_id": session_id,
                    "terminal_id": terminal_id,
                }
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def _clear_challenge_marker(session_id: str, terminal_id: str) -> None:
    """Clear marker when no challenge is active."""
    marker = _challenge_marker_path(session_id, terminal_id)
    try:
        if marker.exists():
            marker.unlink()
    except OSError:
        pass


@register_hook("anti_sycophancy_injector", priority=9.0)
def run_anti_sycophancy_injector(context: HookContext) -> HookResult | None:
    """Inject advocate protocol when skepticism patterns are present."""
    if not _is_enabled():
        return None

    prompt = context.prompt or ""
    if not prompt.strip():
        return None

    session_id, terminal_id = _resolve_scope(context)
    scoped_state_paths = _state_file_candidates(session_id, terminal_id)
    state = _load_state(scoped_state_paths)

    trigger_level = _classify_prompt(prompt)
    sig = _signature(prompt)

    if trigger_level == "none":
        cleared = _update_state(state, sig, "none", 0)
        _save_state(scoped_state_paths, cleared)
        _clear_challenge_marker(session_id, terminal_id)
        return None

    recent = state.get("recent_signatures", [])
    if isinstance(recent, list) and sig in recent:
        # Exact prompt signature already seen in this session+terminal scope.
        return None

    consecutive = _next_consecutive_count(state, trigger_level)
    protocol = _select_protocol(trigger_level, consecutive)
    new_state = _update_state(state, sig, trigger_level, consecutive)
    _save_state(scoped_state_paths, new_state)

    # Write challenge marker for Stop.py structural gate
    _write_challenge_marker(session_id, terminal_id, trigger_level)

    if not protocol:
        return None

    return HookResult(context=protocol, tokens=len(protocol) // 4)
