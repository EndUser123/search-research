"""Behavior contract injector for UserPromptSubmit.

Keeps the model grounded and concise before generation, reducing reliance on
Stop-time blocking hooks for avoidable style and epistemic failures.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from cc_diagnostic_logger import log_hook_invocation
except Exception:  # pragma: no cover - observability must fail open
    log_hook_invocation = None

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.unified_detection import ensure_unified_detection_result
from UserPromptSubmit_modules.registry import register_hook

_ENABLED_ENV = "LLM_BEHAVIOR_CONTRACT_ENABLED"
MIN_PROMPT_LENGTH = 20
CONTRACT_PATH = Path(__file__).resolve().parents[2] / "templates" / "llm_behavior_contract.md"
_FALLBACK_CONTRACT = (
    "**LLM BEHAVIOR CONTRACT**\n\n"
    "If the question is concrete, answer directly. "
    "If a claim is not verified, mark it as inference or unknown. "
    "If you did not use a tool or run code, do not say you did. "
    "If evidence is missing, say what is missing. "
    "If you recommend an option, name the criterion. "
    "If the question is simple, stay brief.\n\n"
    "**Behavioral Rubric**\n"
    "If the user corrects your frame, adopt the correction and stop defending the prior one. "
    "If the next step is obvious, do it instead of narrating intent. "
    "If you are blocked, ask one precise question or run the narrowest useful check. "
    "If multiple paths exist, choose the shortest evidence-first path and say why."
)
_CASUAL_PROMPTS = {
    "thanks",
    "thank you",
    "ok",
    "okay",
    "got it",
    "sounds good",
    "cool",
    "great",
    "nice",
    "yes",
    "no",
}
_QUESTION_PREFIXES = (
    "what ",
    "why ",
    "how ",
    "when ",
    "where ",
    "who ",
    "which ",
    "can you ",
    "could you ",
    "would you ",
    "should we ",
    "should i ",
)
_ACTION_PREFIXES = (
    "implement ",
    "build ",
    "create ",
    "add ",
    "design ",
    "refactor ",
    "debug ",
    "fix ",
    "analyze ",
    "review ",
    "compare ",
    "explain ",
    "summarize ",
    "verify ",
)


@lru_cache(maxsize=1)
def _read_contract() -> str:
    try:
        text = CONTRACT_PATH.read_text(encoding="utf-8").strip()
        return text or _FALLBACK_CONTRACT
    except Exception:
        return _FALLBACK_CONTRACT


def build_behavior_contract() -> str:
    """Return the canonical behavior contract text."""
    return _read_contract()


def append_behavior_contract(base_text: str) -> str:
    """Append the contract once; keep output idempotent."""
    contract = build_behavior_contract()
    if contract in base_text:
        return base_text
    if not base_text.strip():
        return contract
    return f"{base_text.rstrip()}\n\n{contract}"


def contract_clauses() -> list[str]:
    """Return the contract split into compact clauses for tests."""
    text = build_behavior_contract()
    clauses = [block.strip() for block in text.split("\n\n") if block.strip()]
    return clauses


def _should_inject(context: HookContext) -> bool:
    prompt = context.prompt or ""
    stripped = prompt.strip()
    if not stripped:
        return False
    normalized = " ".join(stripped.lower().split())
    if normalized in _CASUAL_PROMPTS:
        return False
    if stripped.startswith("/"):
        return False

    shared_result = ensure_unified_detection_result(context)
    if (
        shared_result.intent_classification
        or shared_result.matched_frameworks
        or shared_result.matched_modes
        or shared_result.matched_profiles
    ):
        return True

    if any(normalized.startswith(prefix) for prefix in _QUESTION_PREFIXES):
        return True
    if any(normalized.startswith(prefix) for prefix in _ACTION_PREFIXES):
        return True

    if len(stripped) < MIN_PROMPT_LENGTH:
        return False

    return "?" in stripped or "," in stripped or " and " in normalized or " or " in normalized


def _is_enabled() -> bool:
    return os.environ.get(_ENABLED_ENV, "true").lower() in ("1", "true", "yes")


@register_hook("behavior_contract", priority=11.6)
def behavior_contract(context: HookContext) -> HookResult:
    """Inject the response behavior contract for substantive prompts."""
    if not _is_enabled():
        return HookResult.empty()

    if not _should_inject(context):
        return HookResult.empty()

    contract = build_behavior_contract()
    if log_hook_invocation is not None:
        try:
            log_hook_invocation(
                hook_name="behavior_contract",
                event_type="UserPromptSubmit",
                action="inject",
                injection_content=contract,
                reason="behavior_contract_injection",
                turn_id=context.data.get("turn_id"),
                session_id=context.session_id,
                terminal_id=context.terminal_id,
            )
        except Exception:
            # Observability should never break injection.
            pass
    return HookResult(context=contract, tokens=len(contract) // 4, priority=11.6)
