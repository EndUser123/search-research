"""Testing strategy router for UserPromptSubmit.

Injects a compact test-selection contract when the prompt is about testing,
bug fixes, features, or hook/stateful workflows.
"""

from __future__ import annotations

import os
import re

from .base import HookContext, HookResult
from .registry import register_hook
from .testing_contract import build_testing_contract

TESTING_STRATEGY_ENABLED = os.environ.get("TESTING_STRATEGY_ROUTER_ENABLED", "true").lower() == "true"
MIN_PROMPT_LENGTH = 24

_SLASH_COMMAND_RE = re.compile(r"^\s*/([a-z0-9-]+)(?:\s+(.*))?$", re.IGNORECASE)

_REGRESSION_RE = re.compile(
    r"\b(bug|fix|broken|error|crash|regression|failing|failed|doesn't work|does not work|issue|defect|restore|reproduce|reproduce the failure)\b",
    re.IGNORECASE,
)
_INTEGRATION_RE = re.compile(
    r"\b(hook|router|state|compaction|resume|persistence|filesystem|file system|registry|boundary|cross-module|cross module|end-to-end|e2e|smoke|io|i/o|workflow)\b",
    re.IGNORECASE,
)
_UNIT_RE = re.compile(
    r"\b(unit|pure logic|helper|validation|transform|parser|deterministic|isolated|local contract|small function|method)\b",
    re.IGNORECASE,
)
_TESTING_INTENT_RE = re.compile(
    r"\b(test|tests|testing|tdd|verify|coverage|pytest|assert|regression|integration|smoke|snapshot|golden)\b",
    re.IGNORECASE,
)
_SNAPSHOT_RE = re.compile(
    r"\b(snapshot|golden|rendered output|generated text|skill body|policy text|hook-injected)\b",
    re.IGNORECASE,
)


def _is_substantial_prompt(prompt: str) -> bool:
    return bool(prompt and len(prompt.strip()) >= MIN_PROMPT_LENGTH)


def _extract_command_name(prompt: str) -> str | None:
    match = _SLASH_COMMAND_RE.match(prompt.strip())
    if match:
        return match.group(1)
    return None


def _classify_test_style(prompt: str) -> str | None:
    """Classify the test strategy the prompt is asking for."""
    command = _extract_command_name(prompt or "")
    normalized = prompt.strip()

    if command in {"code", "t", "tdd", "sqa", "sqd", "verify", "qa"}:
        if _SNAPSHOT_RE.search(normalized):
            return "snapshot_first"
        if _REGRESSION_RE.search(normalized):
            return "regression_first"
        if _INTEGRATION_RE.search(normalized):
            return "integration_first"
        if _UNIT_RE.search(normalized):
            return "unit_first"
        if command in {"code", "sqa", "sqd", "verify", "qa"}:
            return "balanced"
        return "balanced"

    if not _is_substantial_prompt(normalized):
        return None
    if not _TESTING_INTENT_RE.search(normalized):
        return None

    if _SNAPSHOT_RE.search(normalized):
        return "snapshot_first"
    if _REGRESSION_RE.search(normalized):
        return "regression_first"
    if _INTEGRATION_RE.search(normalized):
        return "integration_first"
    if _UNIT_RE.search(normalized):
        return "unit_first"
    return "balanced"


def _build_injection(style: str) -> str:
    contract = build_testing_contract(style=style)
    return contract


@register_hook("testing_strategy_router", priority=2.1)
def strategy_router(context: HookContext) -> HookResult:
    if not TESTING_STRATEGY_ENABLED:
        return HookResult.empty()

    style = _classify_test_style(context.prompt)
    if style is None:
        return HookResult.empty()

    return HookResult(context={"additionalContext": _build_injection(style)})
