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
    },
    "max_enhancers_per_prompt": 3,
    "max_enhancers_by_topic": {
        "implementation": 3,
        "diagnostic": 5,
        "meta_rca": 2,
        "decomposition": 4,
        "implementation_diagnostic": 5,
        "escape_hatch": 1,
    },
    "socratic_min_length": 200,
    "min_prompt_length": 30,
    "enhance_skills": True,
    "skip_skills": [
        "commit", "push", "search", "search-more", "obs", "timeline", "quota", "bgkill",
        "clear-notifications", "clear_restore", "checkpoint-list", "checkpoint-diff",
        "checkpoint-delete", "checkpoint-restore", "context-status", "llm-health",
        "llm-performance", "llm-models", "recent", "catchup", "session", "restore", "help",
    ],
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
        print("[cognitive_enhancers] Config warning: Missing 'enabled' key - defaulting to true", file=sys.stdout)


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
    r"does\s+(?:this|the|it|that)\s+"
    r"(?:need|require|want|have|support|work|exist)|"
    r"should\s+(?:i|we|this|the|it)\s+"
    r"(?:do|use|add|implement|update|change|modify)|"
    r"could\s+(?:this|the|it)\s+"
    r"(?:work|be|handle|support)|"
    r"would\s+(?:it|this)\s+"
    r"(?:be|work|make sense)|"
    r"is\s+(?:this|the|it)\s+"
    r"(?:correct|right|wrong|broken|sufficient)|"
    r"are\s+(?:we|you)\s+"
    r"(?:missing|needing|wanting)"
    r")\b\?",
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
        injection=(
            "**Assumption Check**: Before proceeding, explicitly state your key assumptions about: "
            "scope (what's included/excluded), existing code behavior (why it works this way), "
            "and user intent (what outcome they actually want). "
            "If any assumption is uncertain, flag it."
        ),
        topics=["implementation", "implementation_diagnostic"],
    ),
    Enhancer(
        name="outcome_anchoring",
        injection=(
            "**Outcome Anchor**: Before starting, define what 'done' looks like. "
            "What is the concrete acceptance criteria? What should work when this is complete? "
            "State it in 1-2 sentences, then work backward from that goal."
        ),
        topics=["implementation"],
    ),
    Enhancer(
        name="inversion_prompting",
        injection=(
            "**Inversion Check**: What would make this change fail? "
            "What's the most likely way this breaks existing behavior? "
            "Name one concrete risk, then mitigate it in your approach."
        ),
        topics=["implementation"],
    ),
    Enhancer(
        name="chestertons_fence",
        injection=(
            "**Chesterton's Fence**: You are modifying existing code. "
            "Before changing it, understand WHY it was written this way. "
            "Read the code you're about to change and state its current purpose. "
            "Only then proceed with modifications."
        ),
        topics=["implementation"],
    ),
    Enhancer(
        name="calibrated_confidence",
        injection=(
            "**Calibrated Confidence**: For key claims in your response, "
            "state confidence: HIGH (verified via tool output/docs), "
            "MEDIUM (based on code reading), or LOW (inference — flag it). "
            "Do not present LOW-confidence claims as facts."
        ),
        topics=["diagnostic", "implementation_diagnostic"],
    ),
    Enhancer(
        name="named_artifact_discovery",
        injection=(
            "**Artifact Discovery First**: When investigating a named system, package, or component "
            "that the user wants analyzed: do NOT assume you know where it lives from recently-loaded "
            "context. Recency in context ≠ authoritative location. "
            "Before your first tool call, explicitly state: "
            "(1) the named system/artifact you are looking for, "
            "(2) where you currently believe it lives and WHY you believe that, "
            "(3) the specific Glob or Grep search you will run to confirm before acting. "
            "A concept in the user's prompt is a search target, not a confirmed location."
        ),
        topics=["diagnostic"],
    ),
    Enhancer(
        name="socratic_decomposition",
        injection=(
            "**Decompose First**: This is a broad request. Before diving in, "
            "break it into 2-4 concrete sub-questions that need answering. "
            "Tackle them in order. If any sub-question changes the approach "
            "to later ones, say so."
        ),
        topics=["decomposition"],
    ),
    Enhancer(
        name="cynefin_classification",
        injection=(
            "**Cynefin Framework**: Classify this problem domain before investigating. "
            "Is this Clear (known cause-effect, apply SOPs), Complicated (investigate to find cause), "
            "Complex (probe-sense-respond, experimentation needed), or Chaotic (act first to stabilize)? "
            "Select the appropriate analysis approach based on domain classification."
        ),
        topics=["diagnostic", "meta_rca"],
    ),
    Enhancer(
        name="hanlons_razor",
        injection=(
            "**Hanlon's Razor**: Before attributing issues to malice or intentional sabotage, "
            "consider simpler explanations: bugs, confusion, mistakes, time pressure, or misunderstanding. "
            "What evidence supports malice vs. incompetence vs. systemic causes?"
        ),
        topics=["diagnostic"],
    ),
    Enhancer(
        name="devils_advocate",
        injection=(
            "**Devil's Advocate**: Stress-test this proposal by finding counterarguments. "
            "What's the strongest argument against this approach? "
            "Who would be hurt by this decision? What happens if we're wrong? "
            "What's a simpler alternative? Address these before proceeding."
        ),
        topics=["implementation"],
    ),
    Enhancer(
        name="comparative_analysis",
        injection=(
            "**Comparative Analysis First**: Before suggesting any solution, follow 'Search → Evaluate → Implement': "
            "1. Generate 2-3 diverse approaches first (don't commit to first idea). "
            "2. Evaluate tradeoffs of each approach. "
            "3. Select optimal based on: native > custom, prompting > scripting, discovery-first > build-new. "
            "**Check**: Did I search existing implementations before suggesting new code? "
            "**Check**: Is this the BEST option after comparison, or just the FIRST option I thought of?"
        ),
        topics=["implementation"],
    ),
    Enhancer(
        name="escape_hatch_gate",
        injection=(
            "**Escape Hatch Check**: You are using the [SINGLE ROOT CAUSE CONFIRMED] escape hatch. "
            "Before you submit, perform one final Inversion Check: "
            "Name one way this 'confirmed' cause could still be a red herring. "
            "What evidence would absolutely disprove it?"
        ),
        topics=["escape_hatch"],
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
    if not prompt: return False
    stripped = prompt.strip()
    skill = _extract_skill_name(stripped)
    if skill is not None:
        if not config.get("enhance_skills", True): return False
        if skill in config.get("skip_skills", []): return False
        return True
    if len(stripped) < config.get("min_prompt_length", 30): return False
    if _QUESTION_ONLY_RE.match(stripped) and not (
        _IMPL_RE.search(stripped) or _PLAN_RE.search(stripped) or
        _OUTCOME_RE.search(stripped) or _DIAGNOSTIC_RE.search(stripped) or
        _DECOMPOSITION_RE.search(stripped) or _QUESTION_INTENT_RE.search(stripped)
    ):
        return False
    return True


def _detect_intent(prompt: str) -> dict[str, bool]:
    if _NEGATION_IMPL_RE.search(prompt) and not _MULTI_INTENT_RESCUE_RE.search(prompt):
        impl_blocked = True
    else:
        impl_blocked = False

    explicit_implementation = bool(_IMPL_RE.search(prompt) or _OUTCOME_RE.search(prompt))
    planning_implementation = bool(_PLAN_RE.search(prompt))

    intent = {
        "implementation": bool(explicit_implementation or planning_implementation) and not impl_blocked,
        "diagnostic": bool(_DIAGNOSTIC_RE.search(prompt)) or any(re.search(p, prompt, re.IGNORECASE) for p in INVESTIGATION_TRIGGERS),
        "meta_rca": False,
        "escape_hatch": bool(_SINGLE_RC_ESCAPE_RE.search(prompt)),
        "decomposition": False,
        "implementation_diagnostic": False,
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
    if intent.get("implementation"): return "implementation intent detected"
    return f"matched {len(enhancers)} intent topics"


def _build_injection(enhancers: list[Enhancer], intent: dict[str, bool] | None = None, prompt_length: int = 0) -> str:
    if not enhancers: return ""
    framework_tags = []
    for enhancer in enhancers:
        tags = get_framework_tags_for_enhancer(enhancer.name)
        if tags:
            framework_tags.extend(tags)
            for tag in tags:
                is_valid, warning = validate_tag_emission(tag)
                log_tag_emission(tag_type=tag, tag_category="framework", is_valid=is_valid, has_warning=warning is not None, warning_message=warning, source="cognitive_enhancers")

    tags_str = " ".join(f"[{tag}]" for tag in framework_tags)
    rationale = _get_rationale(intent, enhancers, prompt_length) if intent else "unknown reason"
    tag_header = f"{tags_str}\nWhy: {rationale}\n\n"

    injections = [e.injection for e in enhancers]
    frameworks_text = "\n\n".join(injections)
    framework_names = [e.name.replace("_", " ").title() for e in enhancers]
    tag_instruction = (
        f"**TAG EMISSION REQUIRED**: Begin your response with the framework tags above. "
        f"This provides visibility into which cognitive frameworks are active. "
        f"Active frameworks: {', '.join(framework_names)}\n\n"
    )

    return tag_header + tag_instruction + frameworks_text


@register_hook("cognitive_enhancers", priority=11.0)
def cognitive_enhancers(context: HookContext) -> HookResult:
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

    return HookResult(context=injection, tokens=token_count, priority=11.0)
