"""Unified detection engine for cognitive & reasoning systems.

Consolidates three separate detection systems into a single-pass pattern matcher:
- 10 cognitive frameworks (cognitive_enhancers.py)
- 4 reasoning modes (reasoning_mode_selector.py)
- 7 think profiles (think_trigger.py)

Performance: Single-pass regex compilation at module load, O(n) detection.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Import performance monitoring (graceful degradation if unavailable)
try:
    from performance_monitor import log_detection_performance

    PERF_MONITOR_AVAILABLE = True
except ImportError:
    PERF_MONITOR_AVAILABLE = False
    log_detection_performance = None

# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass(frozen=True)
class UnifiedDetectionResult:
    """Result from unified detection engine.

    Attributes:
        matched_frameworks: List of cognitive framework names matched
        matched_modes: List of reasoning mode names matched
        matched_profiles: List of think profile names matched
        intent_classification: Primary intent (implementation/diagnostic/etc.)
        synergy_candidates: List of dicts with framework/mode/score/rationale
        timing_ms: Time taken for detection in milliseconds
    """

    matched_frameworks: list[str] = field(default_factory=list)
    matched_modes: list[str] = field(default_factory=list)
    matched_profiles: list[str] = field(default_factory=list)
    intent_classification: str | None = None
    synergy_candidates: list[dict] = field(default_factory=list)
    timing_ms: float = 0.0


# =============================================================================
# COGNITIVE FRAMEWORKS (10 total)
# =============================================================================

_COGNITIVE_FRAMEWORKS: dict[str, dict[str, any]] = {
    "assumption_surfacing": {
        "patterns": [
            r"implement",
            r"build",
            r"create",
            r"add",
            r"develop",
            r"write",
            r"design",
            r"refactor",
            r"should we (?:use|choose|pick)",
        ],
        "intent": "implementation",
    },
    "outcome_anchoring": {
        "patterns": [
            r"should (?:this|it|we)",
            r"what (?:should|will|would)",
            r"goal",
            r"objective",
            r"outcome",
            r"deliverable",
            r"build (?:a|the)? (?:new |)?\w+",
            r"create (?:a|the)? (?:new |)?\w+",
            r"add (?:a |the |)?\w+ (?:system|feature|function)",
            r"implement (?:a |the |)?\w+",
            r"new (?:feature|system|function)",
        ],
        "intent": "implementation",
    },
    "inversion_prompting": {
        "patterns": [
            r"what could break",
            r"what if (?:it|this) fails",
            r"how might this",
            r"failure mode",
            r"edge case",
            r"what could go wrong",
            r"break (?:this |it |)?",
            r"what'?s the worst",
            r"how might this fail",
            r"auth(?:entication)?",
            r"system",
            r"feature",
            r"function",
        ],
        "intent": "implementation",
    },
    "chestertons_fence": {
        "patterns": [
            r"modify",
            r"change",
            r"refactor",
            r"update",
            r"existing",
            r"legacy",
            r"current (?:code|system|implementation)",
            r"system (?:for|design|architecture)",
            r"handling",
        ],
        "intent": "implementation",
    },
    "calibrated_confidence": {
        "patterns": [
            r"debug",
            r"investigate",
            r"diagnose",
            r"figure out",
            r"why (?:is|does|did|won't|can't)",
            r"error",
            r"issue",
            r"problem",
            r"fix",
        ],
        "intent": "diagnostic",
    },
    "socratic_decomposition": {
        "patterns": [
            r"how (?:should|do|can|to|would)",
            r"build (?:a|the)? system",
            r"create (?:a|the)? system",
            r"design (?:a|the)? system",
            r"what'?s the best way",
            r"break (?:this |it |)?down",
        ],
        "intent": "decomposition",
    },
    "cynefin_classification": {
        "patterns": [
            r"investigate",
            r"explore",
            r"understand",
            r"analyze",
            r"assess",
            r"characterize",
        ],
        "intent": "diagnostic",
    },
    "hanlons_razor": {
        "patterns": [
            r"why (?:is|does|did)",
            r"not working",
            r"stopped working",
            r"broken",
            r"weird",
            r"strange",
            r"unexpected",
            r"root cause",
            r"memory leak",
        ],
        "intent": "diagnostic",
    },
    "devils_advocate": {
        "patterns": [
            r"evaluate",
            r"review",
            r"assess",
            r"pros and cons",
            r"tradeoff",
            r"should we",
            r"vs\.?",
            r"versus",
            r"alternative",
        ],
        "intent": "implementation_diagnostic",
    },
    "named_artifact_discovery": {
        "patterns": [
            # Requires explicit investigation verb + a named artifact pattern
            # Bare nouns (system, package, component) removed: too broad, fire on every debug session
            r"(?:investigate|debug|diagnose|look into|look at)\s+(?:why|the|this)?.+(?:system|package|component|service|module)",
            r"why (?:is|does|did|isn't|won't|can't).+(?:system|package|component|service|module)",
            r"(?:the|this|our|my)\s+\w+\s+(?:system|package|component|service|module).+(?:not working|broken|failing|wrong)",
        ],
        "intent": "diagnostic",
    },
}


# =============================================================================
# REASONING MODES (4 total)
# =============================================================================

_REASONING_MODES: dict[str, list[str]] = {
    "sequential": [
        r"step by step",
        r"then",
        r"first.*then",
        r"after.*then",
        r"sequentially",
        r"in order",
    ],
    "multi_agent": [
        r"multiple perspective",
        r"different (?:viewpoint|angle|approach)",
        r"pros and cons",
        r"evaluate from",
        r"opinion",
        r"stakeholder",
    ],
    "graph": [
        r"explore",
        r"alternative",
        r"different (?:approach|option|path)",
        r"branch",
        r"consider multiple",
    ],
    "two_stage": [
        r"analyze.*then",
        r"think.*then.*code",
        r"plan.*then",
        r"first.*analyze",
        r"reasoning.*implementation",
    ],
}


# =============================================================================
# THINK PROFILES (7 total)
# =============================================================================


def _stem(word: str, suffixes: str) -> str:
    """Generate regex pattern for word variations.

    Args:
        word: Base word (e.g., "bug")
        suffixes: Suffix options separated by | (e.g., "s|gy")

    Returns:
        Regex pattern matching word + any suffix
    """
    return rf"{word}(?:{suffixes})?"


_THINK_PROFILES: dict[str, dict[str, any]] = {
    "debug_rca": {
        "strong": [
            r"flaky",
            r"intermittent(?:ly)?",
            r"race condition",
            r"root cause",
            r"stack trace",
            r"traceback",
            _stem("regress", "ed|ing|ion|ions"),
            r"not working",
            r"stopped working",
            r"keeps? (?:happening|failing|crashing|breaking)",
            r"why (?:does|is|did|isn't|won't|can't|doesn't)",
        ],
        "weak": [
            _stem("bug", "s|gy"),
            _stem("break", "s|ing"),
            _stem("broke", "n|d"),
            _stem("crash", "ed|ing|es"),
            _stem("error", "s|ed"),
            _stem("exception", "s"),
            _stem("fail", "ed|ing|s|ure|ures"),
        ],
        "weak_threshold": 2,
    },
    "tradeoff_decision": {
        "strong": [
            r"should we use",
            r"pick between",
            r"choose between",
            r"option (?:a|b|1|2)",
            r"vs\.?",
            r"versus",
            r"or.*or",
        ],
        "weak": [
            r"tradeoff",
            r"pros and cons",
            r"advantage",
            r"disadvantage",
            r"benefit",
            r"downside",
            r"better",
            r"best",
        ],
        "weak_threshold": 1,
    },
    "architecture": {
        "strong": [
            r"should we split",
            r"microservice",
            r"system architecture",
            r"service boundar",
            r"design (?:the|a)? system",
            r"architectural?",
        ],
        "weak": [
            r"component",
            r"module",
            r"layer",
            r"tier",
            r"structure",
            r"organiz",
        ],
        "weak_threshold": 2,
    },
    "pre_commit_risk": {
        "strong": [
            r"about to deploy",
            r"pushing to main",
            r"shipping to production",
            r"release",
            r"merge",
            r"deploy(?:ing|ment)?",
        ],
        "weak": [
            r"production",
            r"prod",
            r"main branch",
            r"master",
            r"live",
            r"going live",
        ],
        "weak_threshold": 2,
    },
    "security_review": {
        "strong": [
            r"sql injection",
            r"xss",
            r"csrf",
            r"security audit",
            r"vulnerability",
            r"attack vector",
            r"exploit",
        ],
        "weak": [
            r"secure",
            r"security",
            r"auth(?:entication|orization)?",
            r"permission",
            r"access control",
            r"encrypt",
        ],
        "weak_threshold": 2,
    },
    "performance_analysis": {
        "strong": [
            r"slow",
            r"sluggish",
            r"latency",
            r"performance bottleneck",
            r"optimize",
        ],
        "weak": [
            _stem("perform", "ance|ed|ing"),
            r"fast",
            r"efficient",
            r"speed",
            r"responsive",
        ],
        "weak_threshold": 2,
    },
    "multi_file_refactor": {
        "strong": [
            r"refactor.*multiple",
            r"across.*file",
            r"restructure.*codebase",
            r"split.*module",
        ],
        "weak": [
            r"refactor",
            r"restructure",
            r"reorganize",
            r"split",
            r"extract",
        ],
        "weak_threshold": 2,
    },
}


# =============================================================================
# PATTERN COMPILATION (module load time, once)
# =============================================================================

_COMPILED_PATTERNS: dict[str, dict[str, re.Pattern | list[re.Pattern]]] = {}

# Compile cognitive framework patterns
for framework_name, framework_data in _COGNITIVE_FRAMEWORKS.items():
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in framework_data["patterns"]]
    _COMPILED_PATTERNS[framework_name] = {"patterns": patterns}

# Compile reasoning mode patterns
for mode_name, mode_patterns in _REASONING_MODES.items():
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in mode_patterns]
    _COMPILED_PATTERNS[f"mode_{mode_name}"] = {"patterns": patterns}

# Compile think profile patterns
for profile_name, profile_data in _THINK_PROFILES.items():
    strong_patterns = [re.compile(p, re.IGNORECASE) for p in profile_data["strong"]]
    weak_patterns = [re.compile(p, re.IGNORECASE) for p in profile_data["weak"]]
    _COMPILED_PATTERNS[f"profile_{profile_name}"] = {
        "strong_patterns": strong_patterns,
        "weak_patterns": weak_patterns,
        "weak_threshold": profile_data["weak_threshold"],
    }


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================#

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "implementation": [
        r"implement",
        r"build",
        r"create",
        r"add",
        r"develop",
    ],
    "diagnostic": [
        r"debug",
        r"investigate",
        r"diagnose",
        r"fix",
        r"error",
    ],
    "meta_rca": [
        r"root cause",
        r"why does",
        r"why is",
        r"why did",
    ],
    "decomposition": [
        r"how should",
        r"how to",
        r"how do",
    ],
}

_INTENT_PATTERN_CACHE: dict[str, list[re.Pattern]] = {
    intent: [re.compile(p, re.IGNORECASE) for p in patterns]
    for intent, patterns in _INTENT_KEYWORDS.items()
}


def _classify_intent(prompt: str) -> str | None:
    """Classify the primary intent of the prompt.

    Args:
        prompt: User prompt text

    Returns:
        Intent classification (implementation/diagnostic/etc.) or None
    """
    for intent, patterns in _INTENT_PATTERN_CACHE.items():
        for pattern in patterns:
            if pattern.search(prompt):
                return intent
    return None


# =============================================================================
# SYNERGY DETECTION
# =============================================================================#


def _detect_synergies(
    matched_frameworks: list[str],
    matched_modes: list[str],
) -> list[dict]:
    """Detect framework+mode synergy combinations using synergy_detector.

    Args:
        matched_frameworks: List of matched cognitive frameworks
        matched_modes: List of matched reasoning modes

    Returns:
        List of synergy dicts {framework, mode, score, rationale}
    """
    # Use synergy_detector for detailed scoring and rationales
    from UserPromptSubmit_modules.synergy_detector import detect_synergies

    match = detect_synergies(matched_frameworks, matched_modes)
    return match.synergies


# =============================================================================
# MAIN DETECTION FUNCTION
# =============================================================================#


def detect_prompt(prompt: str) -> UnifiedDetectionResult:
    """Detect cognitive frameworks, reasoning modes, and think profiles.

    Single-pass detection using pre-compiled regex patterns.

    Args:
        prompt: User prompt text to analyze

    Returns:
        UnifiedDetectionResult with all matches and metadata
    """
    start_time = time.perf_counter()

    matched_frameworks = []
    matched_modes = []
    matched_profiles = []

    # Detect cognitive frameworks
    for framework_name in _COGNITIVE_FRAMEWORKS:
        framework_key = framework_name
        if framework_key in _COMPILED_PATTERNS:
            patterns = _COMPILED_PATTERNS[framework_key]["patterns"]
            if any(pattern.search(prompt) for pattern in patterns):
                matched_frameworks.append(framework_name)

    # Detect reasoning modes
    for mode_name in _REASONING_MODES:
        mode_key = f"mode_{mode_name}"
        if mode_key in _COMPILED_PATTERNS:
            patterns = _COMPILED_PATTERNS[mode_key]["patterns"]
            if any(pattern.search(prompt) for pattern in patterns):
                matched_modes.append(mode_name)

    # Detect think profiles (strong + weak pattern matching)
    for profile_name in _THINK_PROFILES:
        profile_key = f"profile_{profile_name}"
        if profile_key in _COMPILED_PATTERNS:
            profile_data = _COMPILED_PATTERNS[profile_key]

            # Check strong patterns (1 match triggers)
            strong_match = any(
                pattern.search(prompt) for pattern in profile_data["strong_patterns"]
            )

            # Check weak patterns (threshold matches trigger)
            weak_count = sum(
                1 for pattern in profile_data["weak_patterns"] if pattern.search(prompt)
            )
            weak_threshold = profile_data["weak_threshold"]
            weak_match = weak_count >= weak_threshold

            if strong_match or weak_match:
                matched_profiles.append(profile_name)

    # Classify intent
    intent_classification = _classify_intent(prompt)

    # Detect synergies
    synergy_candidates = _detect_synergies(matched_frameworks, matched_modes)

    # Calculate timing
    end_time = time.perf_counter()
    timing_ms = (end_time - start_time) * 1000

    result = UnifiedDetectionResult(
        matched_frameworks=matched_frameworks,
        matched_modes=matched_modes,
        matched_profiles=matched_profiles,
        intent_classification=intent_classification,
        synergy_candidates=synergy_candidates,
        timing_ms=timing_ms,
    )

    # Log performance metrics (non-blocking)
    if PERF_MONITOR_AVAILABLE and log_detection_performance:
        try:
            log_detection_performance(prompt, result)
        except Exception:
            # Performance logging must never break detection
            pass

    return result


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================#

# Verify patterns compiled at module load
assert len(_COMPILED_PATTERNS) > 0, "No patterns compiled - module initialization failed"


# =============================================================================
# HOOK INTEGRATION
# =============================================================================


@register_hook("unified_detection", priority=1.0)
def unified_detection_hook(context: HookContext) -> HookResult:
    """Run unified detection engine and store result in context data.

    This ensures subsequent hooks (synergy_detector, tag_emission, etc.)
    can reuse the detection results without re-running pattern matching.

    Priority: 1.0 (runs before all other hooks)
    """
    result = detect_prompt(context.prompt)

    # Store in context data for subsequent hooks (side-effect)
    context.data["unified_detection_result"] = result

    # Detection itself has no text injection
    return HookResult.empty()
