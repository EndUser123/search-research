"""
Cognitive Enhancers - UserPromptSubmit Hook Module
===================================================

11 lightweight context injections that make the LLM reason better:

1. assumption_surfacing    - Surface unstated assumptions before work begins
2. outcome_anchoring       - Define "done" before starting
3. inversion_prompting     - "What would make this fail?"
4. chestertons_fence       - Understand existing code before changing it
5. calibrated_confidence   - Force confidence labeling on claims
6. named_artifact_discovery - Recency in context ≠ authoritative location
7. socratic_decomposition  - Break vague mega-prompts into sub-questions
8. cynefin_classification  - Problem domain classification (Clear/Complicated/Complex/Chaotic)
9. hanlons_razor           - Distinguish malice from stupidity (bugs before blame)
10. devils_advocate        - Stress-test proposals with counterarguments
11. comparative_analysis   - Search → Evaluate → Implement before committing

All configurable via cognitive_enhancers_config.json.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import copy
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.conflict_arbiter import ArbiterResult, resolve_conflict
from UserPromptSubmit_modules.observability import log_cognitive_selection, log_tag_emission
from UserPromptSubmit_modules.registry import register_hook
from UserPromptSubmit_modules.tag_registry import (
    DEPRECATED_TAG_COG,
    FRAMEWORK_TAGS,
    get_framework_tags_for_enhancer,
    validate_tag_emission,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cognitive_enhancers_config.json"

# Rough character-to-token ratio for estimation
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class Enhancer:
    """Cognitive enhancer definition."""

    name: str
    injection: str
    topics: tuple[str, ...]

_DEFAULT_CONFIG = {
    "enabled": True,
    "topics": {
        "implementation": True,
        "diagnostic": True,
        "meta_rca": True,
        "decomposition": True,
        "implementation_diagnostic": True,
        "escape_hatch": True,
        "question": True,  # Universal cognitive gate for simple questions
    },
    "enhancers": {
        "assumption_surfacing": True,
        "outcome_anchoring": True,
        "inversion_prompting": True,
        "chestertons_fence": True,
        "calibrated_confidence": True,
        "named_artifact_discovery": True,
        "socratic_decomposition": True,
        "cynefin_classification": True,
        "hanlons_razor": True,
        "devils_advocate": True,
        "comparative_analysis": True,
        "escape_hatch_gate": True,
        "assumption_check": True,  # Minimal universal cognitive enhancement
    },
    "max_enhancers_per_prompt": 3,
    "max_enhancers_by_topic": {
        "implementation": 3,
        "diagnostic": 5,
        "meta_rca": 2,
        "decomposition": 4,
        "implementation_diagnostic": 5,
        "escape_hatch": 1,
        "question": 1,  # One minimal enhancer for questions
    },
    "socratic_min_length": 200,
    "modes": {
        "rca": {"topic": "meta_rca"},
        "deep": {"topic": "implementation"},
        "fast": {"disable_all": True},
    },
}


def _load_config() -> dict:
    """Load config with defaults. Fail open on any error."""
    config = copy.deepcopy(_DEFAULT_CONFIG)
    try:
        if CONFIG_PATH.exists():
            user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            _validate_config(user_config)
            for key, value in user_config.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value
    except Exception:
        pass
    return config


def _validate_config(config: dict) -> None:
    """Validate config schema. Emits warnings to stdout, never raises."""
    if "enabled" not in config:
        _logger.warning("[cognitive_enhancers] Config warning: Missing 'enabled' key - defaulting to true")


# ---------------------------------------------------------------------------
# Intent detection patterns
# ---------------------------------------------------------------------------

_IMPL_RE = re.compile(
    r"\b(build|create|implement|refactor|optimize|enhance|add|write|develop|code|make|"
    r"set\s+up|configure|change|modify|update|fix|replace|rewrite|convert|migrate|"
    r"hook\s+up|wire\s+up|integrate|extend|extract)\b",
    re.IGNORECASE,
)

_MODIFY_RE = re.compile(
    r"\b(refactor|change|modify|update|fix|replace|rewrite|convert|migrate|"
    r"restructure|rename|move|extract|split|merge|consolidate|simplify|"
    r"remove|delete|deprecate|upgrade|downgrade)\b",
    re.IGNORECASE,
)

_PLAN_RE = re.compile(
    r"\b(plan|design|architect|strategy|approach|how\s+should|what's\s+the\s+best)\b",
    re.IGNORECASE,
)

_OUTCOME_RE = re.compile(
    r"\b("
    r"what\s+should|"
    r"deliverable|"
    r"acceptance\s+criteria|"
    r"done\s+look\s+like|"
    r"success\s+look\s+like|"
    r"outcome|"
    r"goal"
    r")\b",
    re.IGNORECASE,
)

_DIAGNOSTIC_RE = re.compile(
    r"\b(debug|investigate|diagnose|analyze|explain\s+why|root\s+cause|"
    r"figure\s+out|what's\s+wrong|what\s+caused|troubleshoot|"
    r"why\s+does|why\s+is|why\s+did|how\s+does|what\s+happens|"
    r"characterize|classify|problem\s+domain|investigation)\b",
    re.IGNORECASE,
)

_DECOMPOSITION_RE = re.compile(
    r"\b("
    r"break\s+down|"
    r"decompose|"
    r"split\s+(?:this|the)?\s*(?:task|problem|work)?\s*(?:into)?|"
    r"smaller\s+subtasks?|"
    r"step\s+by\s+step|"
    r"subtasks?"
    r")\b",
    re.IGNORECASE,
)

_SPECIFIC_REF_RE = re.compile(
    r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]+|"
    r"[a-zA-Z_][a-zA-Z0-9_]*::\w+|"
    r"def\s+\w+|class\s+\w+|"
    r"line\s+\d+|L\d+)",
    re.IGNORECASE,
)

_QUESTION_ONLY_RE = re.compile(r"^[^.!]*\?\s*$", re.MULTILINE)

# Questions that indicate decision/intent requiring cognitive enhancement
_QUESTION_INTENT_RE = re.compile(
    r"\b("
    r"does\s+.+?\?|"
    r"should\s+.+?\?|"
    r"could\s+.+?\?|"
    r"would\s+.+?\?|"
    r"is\s+(?:this|the|it|that)\s+"
    r"(?:correct|right|wrong|broken|sufficient|ok|okay|best|needed|required|safe)\??|"
    r"is\s+(?:this|the|it|that)\s+\w+\s+\w+|"
    r"are\s+(?:we|you)\s+"
    r"(?:missing|needing|wanting|using|doing)\??"
    r")",
    re.IGNORECASE,
)

_SLASH_RE = re.compile(r"^\s*/[a-z]", re.IGNORECASE)
_MODE_RE = re.compile(r"#(\w+)")

_NEGATION_IMPL_RE = re.compile(
    r"\b(don't|do not|never|no|not)\s+(implement|create|build|write|add|make)\b", re.IGNORECASE
)

_MULTI_INTENT_RESCUE_RE = re.compile(
    r"[,;.]\s*(?:but|however|instead|rather)\s+.*\b(implement|create|build|write|add|make)\b",
    re.IGNORECASE,
)

# Investigation trigger patterns for Layer 1
INVESTIGATION_TRIGGERS = [
    r"investigat(?:e|ing)",
    r"diagnos(?:e|is|ing)",
    r"debug(?:ging|ger)?",
    r"root cause",
    r"why (?:does|is|did|won't|can't|doesn't)",
    r"not working",
    r"stopped working",
    r"keeps? (?:happening|failing|crashing|breaking)",
]

# Escape hatch pattern for Phase 2.1
_SINGLE_RC_ESCAPE_RE = re.compile(r"\[SINGLE ROOT CAUSE CONFIRMED\]", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Enhancer definitions
# ---------------------------------------------------------------------------

_ENHANCERS: list[Enhancer] = [
    Enhancer(
        name="assumption_surfacing",
        injection="**Assumption Check**: State the key assumptions about scope, current behavior, and user intent. Flag anything uncertain.",
        topics=["implementation", "implementation_diagnostic"],
    ),
    Enhancer(
        name="outcome_anchoring",
        injection="**Outcome Anchor**: Define done in one sentence and work backward from it.",
        topics=["implementation"],
    ),
    Enhancer(
        name="inversion_prompting",
        injection="**Inversion Check**: Name the most likely failure mode and mitigate it.",
        topics=["implementation"],
    ),
    Enhancer(
        name="chestertons_fence",
        injection="**Chesterton's Fence**: Read the existing code first and state its purpose before changing it.",
        topics=["implementation"],
    ),
    Enhancer(
        name="calibrated_confidence",
        injection="**Calibrated Confidence**: Mark claims HIGH only when verified; do not state LOW-confidence claims as facts.",
        topics=["diagnostic", "implementation_diagnostic"],
    ),
    Enhancer(
        name="named_artifact_discovery",
        injection="**Artifact Discovery**: Do not trust recent context for location; name the target and confirm it with Glob/Grep first.",
        topics=["diagnostic"],
    ),
    Enhancer(
        name="socratic_decomposition",
        injection="**Decompose First**: Break broad requests into 2-4 sub-questions and answer them in order.",
        topics=["decomposition"],
    ),
    Enhancer(
        name="cynefin_classification",
        injection="**Cynefin**: Classify the domain first, then choose the right analysis style.",
        topics=["diagnostic", "meta_rca"],
    ),
    Enhancer(
        name="hanlons_razor",
        injection="**Hanlon's Razor**: Prefer bugs, confusion, or process issues before malice.",
        topics=["diagnostic"],
    ),
    Enhancer(
        name="devils_advocate",
        injection="**Devil's Advocate**: State the strongest counterargument and a simpler alternative before proceeding.",
        topics=["implementation"],
    ),
    Enhancer(
        name="comparative_analysis",
        injection="**Comparative Analysis**: Search first, compare 2-3 options, then recommend the best one.",
        topics=["implementation"],
    ),
    Enhancer(
        name="escape_hatch_gate",
        injection="**Escape Hatch Check**: Before claiming a single root cause, name one way it could still be wrong.",
        topics=["escape_hatch"],
    ),
    Enhancer(
        name="assumption_check",
        injection="**Question Check**: Before answering, verify what you're being asked. Don't assume intent - state your understanding and check if it's correct.",
        topics=["question"],
    ),
]


# ---------------------------------------------------------------------------
# Intent detection functions
# ---------------------------------------------------------------------------


def _extract_skill_name(prompt: str) -> str | None:
    if not _SLASH_RE.match(prompt.strip()):
        return None
    return prompt.strip().lstrip("/").split()[0] if prompt.strip() else None


def _is_actionable_prompt(prompt: str, config: dict) -> bool:
    """Check if prompt should receive cognitive enhancement.

    All non-empty prompts receive enhancement. The intent detection
    determines WHICH enhancers are selected — not this gate.
    """
    if not prompt: return False
    stripped = prompt.strip()
    if not stripped: return False

    # Slash commands always pass through
    if _extract_skill_name(stripped) is not None:
        return True

    # Pure questions without implementation/diagnostic keywords: still enhance
    # (assumption_surfacing and question_check are useful for all questions)
    return True


def _detect_intent(prompt: str) -> dict[str, bool]:
    if _NEGATION_IMPL_RE.search(prompt) and not _MULTI_INTENT_RESCUE_RE.search(prompt):
        impl_blocked = True
    else:
        impl_blocked = False

    explicit_implementation = bool(_IMPL_RE.search(prompt) or _OUTCOME_RE.search(prompt))
    planning_implementation = bool(_PLAN_RE.search(prompt))
    question_intent = bool(_QUESTION_INTENT_RE.search(prompt))

    intent = {
        "implementation": bool(explicit_implementation or planning_implementation) and not impl_blocked,
        "diagnostic": bool(_DIAGNOSTIC_RE.search(prompt)) or any(re.search(p, prompt, re.IGNORECASE) for p in INVESTIGATION_TRIGGERS),
        "meta_rca": False,
        "escape_hatch": bool(_SINGLE_RC_ESCAPE_RE.search(prompt)),
        "decomposition": False,
        "implementation_diagnostic": False,
        "question": question_intent,  # NEW: Universal cognitive gate for questions
    }

    if intent["implementation"] and intent["diagnostic"]:
        intent["implementation_diagnostic"] = True

    if _DECOMPOSITION_RE.search(prompt):
        intent["decomposition"] = True
    elif len(prompt.strip()) >= 200 and not _SPECIFIC_REF_RE.search(prompt):
        intent["decomposition"] = True

    if intent["decomposition"] and not explicit_implementation and not intent["diagnostic"]:
        intent["implementation"] = False

    return intent


def _select_enhancers(intent: dict[str, bool], config: dict) -> list[Enhancer]:
    selected = []
    enabled_topics = config.get("topics", {})
    enabled_enhancers = config.get("enhancers", {})

    for enhancer in _ENHANCERS:
        if not enabled_enhancers.get(enhancer.name, True): continue
        if any(enabled_topics.get(topic, True) and intent.get(topic, False) for topic in enhancer.topics):
            selected.append(enhancer)

    max_by_topic = config.get("max_enhancers_by_topic", {})
    detected_topics = [t for t, active in intent.items() if active and t in max_by_topic]

    if detected_topics:
        topic_limits = [max_by_topic.get(t, config.get("max_enhancers_per_prompt", 3)) for t in detected_topics]
        max_enhancers = max(topic_limits)
    else:
        max_enhancers = config.get("max_enhancers_per_prompt", 3)

    return selected[:max_enhancers]


def _get_rationale(intent: dict[str, bool], enhancers: list[Enhancer], prompt_length: int = 0) -> str:
    if intent.get("meta_rca"): return "meta_rca topic detected (root cause analysis mode)"
    if intent.get("implementation_diagnostic"): return "implementation + diagnostic intent detected"
    if intent.get("diagnostic"): return "diagnostic intent detected (investigate to find cause)"
    if intent.get("decomposition"): return f"long vague prompt detected (length: {prompt_length} chars)"
    if intent.get("question"): return "question intent detected (verify understanding before answering)"
    if intent.get("implementation"): return "implementation intent detected"
    return f"matched {len(enhancers)} intent topics"


def _build_injection(enhancers: list[Enhancer], intent: dict[str, bool] | None = None, prompt_length: int = 0) -> str:
    if not enhancers: return ""

    tag_codes: list[str] = []
    for enhancer in enhancers:
        tags = get_framework_tags_for_enhancer(enhancer.name)
        if tags:
            for tag in tags:
                is_valid, warning = validate_tag_emission(tag)
                log_tag_emission(tag_type=tag, tag_category="framework", is_valid=is_valid, has_warning=warning is not None, warning_message=warning, source="cognitive_enhancers")
                if is_valid and warning is None and tag not in tag_codes:
                    tag_codes.append(tag)

    rationale = _get_rationale(intent, enhancers, prompt_length) if intent else "unknown reason"
    injections = [e.injection for e in enhancers]
    frameworks_text = "\n\n".join(injections)
    framework_names = [e.name.replace("_", " ").title() for e in enhancers]
    tag_instruction = f"**Use these frameworks**: {', '.join(framework_names)}.\n\n"

    base = f"Why: {rationale}\n\n{tag_instruction}{frameworks_text}"

    if not tag_codes:
        return base

    tag_line = " ".join(f"[{t}]" for t in tag_codes)
    return (
        f"{base}\n\n"
        f"<cognitive-tags>\n"
        f"Append this exact line at the very end of your first reply "
        f"to this user message (not in later replies or after tool use):\n"
        f"Tags: {tag_line}\n"
        f"</cognitive-tags>"
    )


@register_hook("cognitive_enhancers", priority=11.0)
def cognitive_enhancers(context: HookContext) -> HookResult:
    # Budget guard — initialize budget before safety check
    SAFETY_MODULES = {"behavior_contract", "operating_rules", "verify_before_claim", "truthfulness_gate"}
    _mod_name = "cognitive_enhancers"
    budget = context.data.get("remaining_budget", 20000)
    min_chars = 400

    if _mod_name not in SAFETY_MODULES and budget < min_chars:
        context.data.setdefault("skipped_budget", []).append(_mod_name)
        return HookResult.empty()

    config = _load_config()
    if not config.get("enabled", True): return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config): return HookResult.empty()

    mode: str | None = None
    mode_match = _MODE_RE.search(prompt)
    forced_topic: str | None = None
    if mode_match:
        mode = mode_match.group(1)
        mode_config = config.get("modes", {}).get(mode, {})
        forced_topic = mode_config.get("topic")
        if mode_config.get("disable_all", False): return HookResult.empty()

    if forced_topic:
        intent = dict.fromkeys(["implementation", "diagnostic", "meta_rca", "decomposition", "implementation_diagnostic", "escape_hatch"], False)
        intent[forced_topic] = True
    else:
        intent = _detect_intent(prompt)

    selected = _select_enhancers(intent, config)
    if not selected: return HookResult.empty()

    arbiter_result: ArbiterResult = resolve_conflict(enhancers=selected, mode_selection=None, reasoning_confidence=0, prompt_mode=mode, token_limit=500)
    selected = arbiter_result.enhancers
    if not selected: return HookResult.empty()

    prompt_length = len(prompt.strip())
    injection = _build_injection(selected, intent, prompt_length)
    if not injection: return HookResult.empty()

    token_count = len(injection) // CHARS_PER_TOKEN
    rationale = _get_rationale(intent, selected, prompt_length)
    log_cognitive_selection(enhancers=selected, intent=intent, tokens=token_count, rationale=rationale)

    # Update remaining budget
    context.data["remaining_budget"] = budget - len(injection)

    return HookResult(context=injection, tokens=token_count, priority=11.0)
