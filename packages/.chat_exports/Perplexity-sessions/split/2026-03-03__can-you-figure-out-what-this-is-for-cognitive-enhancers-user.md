---
title: "Can you figure out what this is for?
''''
Cognitive Enhancers - UserPromptSubmit Hook Module
==========================="
date: "2026-03-03"
mode: "COPILOT"
uuid: "9f66efac-a968-484b-93e4-a7d0c4aaad92"
entry_count: 6
---

## Human

Can you figure out what this is for?
""""
Cognitive Enhancers - UserPromptSubmit Hook Module
===================================================


Seven lightweight context injections that make the LLM reason better:


1. assumption_surfacing    (priority 11.5) - Surface unstated assumptions before work begins
2. outcome_anchoring       (priority 11.4) - Define "done" before starting
3. inversion_prompting     (priority 11.6) - "What would make this fail?"
4. chestertons_fence       (priority 11.7) - Understand existing code before changing it
5. calibrated_confidence   (priority 11.8) - Force confidence labeling on claims
6. socratic_decomposition  (priority 11.3) - Break vague mega-prompts into sub-questions
7. analysis_protocol_gate  (priority 11.2) - Inject FAP checklist for failure-analysis prompts


All configurable via cognitive_enhancers_config.json.
To disable any enhancer, set its key to false in the config file.
To disable ALL enhancers, set "enabled" to false.


Skills (slash commands) get cognitive enhancement by default.
Operational skills like /commit, /push, /search are blacklisted
via "skip_skills" in the config. New skills automatically benefit
unless explicitly added to the skip list.
"""
from __future__ import annotations


import json
import re
import threading
from pathlib import Path


from .base import HookContext, HookResult
from .registry import register_hook


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


CONFIG_PATH = Path(__file__).resolve().parent.parent / "cognitive_enhancers_config.json"


_DEFAULT_CONFIG = {
    "enabled": True,
    "assumption_surfacing": True,
    "outcome_anchoring": True,
    "inversion_prompting": True,
    "chestertons_fence": True,
    "calibrated_confidence": True,
    "socratic_decomposition": True,
    "analysis_protocol_gate": True,
    "socratic_min_length": 200,
    "min_prompt_length": 30,
    "enhance_skills": True,
    "skip_skills": [
        "commit", "push", "search", "search-more", "obs", "timeline",
        "quota", "bgkill", "clear-notifications", "clear_restore",
        "checkpoint-list", "checkpoint-diff", "checkpoint-delete",
        "checkpoint-restore", "context-status", "llm-health",
        "llm-performance", "llm-models", "recent", "catchup",
        "session", "restore", "help",
    ],
}



def _load_config() -> dict:
    """Load config with defaults. Fail open on any error."""
    config = dict(_DEFAULT_CONFIG)
    try:
        if CONFIG_PATH.exists():
            user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config.update(user_config)
    except Exception:
        pass
    return config



# ---------------------------------------------------------------------------
# Intent detection patterns
# ---------------------------------------------------------------------------


_IMPL_RE = re.compile(
    r"\b(build|create|implement|refactor|optimize|add|write|develop|code|make|"
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


_DIAGNOSTIC_RE = re.compile(
    r"\b(debug|investigate|diagnose|analyze|explain\s+why|root\s+cause|"
    r"figure\s+out|what's\s+wrong|what\s+caused|troubleshoot|"
    r"why\s+does|why\s+is|why\s+did|how\s+does|what\s+happens)\b",
    re.IGNORECASE,
)


_SPECIFIC_REF_RE = re.compile(
    r"(?:[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z]+|"  # file.ext pattern
    r"[a-zA-Z_][a-zA-Z0-9_]*::\w+|"  # Class::method
    r"def\s+\w+|class\s+\w+|"  # explicit def/class
    r"line\s+\d+|L\d+)",  # line references
    re.IGNORECASE,
)


_QUESTION_ONLY_RE = re.compile(r"^[^.!]*\?\s*$", re.MULTILINE)
_SLASH_RE = re.compile(r"^\s*/[a-z]", re.IGNORECASE)



def _extract_skill_name(prompt: str) -> str | None:
    """Extract skill name from a slash command, or None if not a slash command."""
    if not _SLASH_RE.match(prompt.strip()):
        return None
    return prompt.strip().lstrip("/").split()[0] if prompt.strip() else None



def _is_actionable_prompt(prompt: str, config: dict) -> bool:
    """Check if prompt is substantial enough to warrant cognitive injection.


    Slash commands pass through UNLESS the skill is blacklisted
    or enhance_skills is disabled. This means new implementation-oriented
    skills automatically get cognitive enhancement.
    """
    if not prompt or len(prompt.strip()) < config.get("min_prompt_length", 30):
        return False
    stripped = prompt.strip()
    # Handle slash commands: allow unless blacklisted
    skill = _extract_skill_name(stripped)
    if skill is not None:
        if not config.get("enhance_skills", True):
            return False
        skip_list = config.get("skip_skills", [])
        if skill in skip_list:
            return False
        # Non-blacklisted skill — fall through to remaining checks
    if _QUESTION_ONLY_RE.match(stripped) and not _IMPL_RE.search(stripped):
        return False
    return True



def _has_impl_intent(prompt: str) -> bool:
    return bool(_IMPL_RE.search(prompt))



def _has_modify_intent(prompt: str) -> bool:
    return bool(_MODIFY_RE.search(prompt))



def _has_plan_or_impl_intent(prompt: str) -> bool:
    return bool(_IMPL_RE.search(prompt) or _PLAN_RE.search(prompt))



def _has_diagnostic_or_impl_intent(prompt: str) -> bool:
    return bool(_IMPL_RE.search(prompt) or _DIAGNOSTIC_RE.search(prompt) or _PLAN_RE.search(prompt))



def _is_vague_long_prompt(prompt: str, config: dict) -> bool:
    """Check if prompt is long but lacks specific code references.


    Fires when the prompt is substantial (200+ chars by default)
    but doesn't reference specific files, functions, or line numbers,
    suggesting it's a vague mega-prompt that needs decomposition.
    """
    min_len = config.get("socratic_min_length", 200)
    if len(prompt.strip()) < min_len:
        return False
    # If prompt has specific code references, it's targeted enough
    if _SPECIFIC_REF_RE.search(prompt):
        return False
    return True



# ---------------------------------------------------------------------------
# Enhancer 1: Assumption Surfacing
# ---------------------------------------------------------------------------


_ASSUMPTION_INJECTION = (
    "**Assumption Check**: Before proceeding, explicitly state your key assumptions about: "
    "scope (what's included/excluded), existing code behavior (why it works this way), "
    "and user intent (what outcome they actually want). "
    "If any assumption is uncertain, flag it."
)



@register_hook("assumption_surfacing", priority=11.5)
def assumption_surfacing(context: HookContext) -> HookResult:
    """Surface unstated assumptions before implementation work begins."""
    config = _load_config()
    if not config.get("enabled") or not config.get("assumption_surfacing"):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _has_impl_intent(prompt):
        return HookResult.empty()
    return HookResult(context=_ASSUMPTION_INJECTION, tokens=len(_ASSUMPTION_INJECTION) // 4, priority=11.5)



# ---------------------------------------------------------------------------
# Enhancer 2: Outcome Anchoring
# ---------------------------------------------------------------------------


_OUTCOME_INJECTION = (
    "**Outcome Anchor**: Before starting, define what 'done' looks like. "
    "What is the concrete acceptance criteria? What should work when this is complete? "
    "State it in 1-2 sentences, then work backward from that goal."
)



@register_hook("outcome_anchoring", priority=11.4)
def outcome_anchoring(context: HookContext) -> HookResult:
    """Define 'done' before starting implementation."""
    config = _load_config()
    if not config.get("enabled") or not config.get("outcome_anchoring"):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _has_plan_or_impl_intent(prompt):
        return HookResult.empty()
    return HookResult(context=_OUTCOME_INJECTION, tokens=len(_OUTCOME_INJECTION) // 4, priority=11.4)



# ---------------------------------------------------------------------------
# Enhancer 3: Inversion Prompting
# ---------------------------------------------------------------------------


_INVERSION_INJECTION = (
    "**Inversion Check**: What would make this change fail? "
    "What's the most likely way this breaks existing behavior? "
    "Name one concrete risk, then mitigate it in your approach."
)



@register_hook("inversion_prompting", priority=11.6)
def inversion_prompting(context: HookContext) -> HookResult:
    """Force failure-mode thinking before implementation."""
    config = _load_config()
    if not config.get("enabled") or not config.get("inversion_prompting"):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _has_impl_intent(prompt):
        return HookResult.empty()
    return HookResult(context=_INVERSION_INJECTION, tokens=len(_INVERSION_INJECTION) // 4, priority=11.6)



# ---------------------------------------------------------------------------
# Enhancer 4: Chesterton's Fence
# ---------------------------------------------------------------------------


_FENCE_INJECTION = (
    "**Chesterton's Fence**: You are modifying existing code. "
    "Before changing it, understand WHY it was written this way. "
    "Read the code you're about to change and state its current purpose. "
    "Only then proceed with modifications."
)



@register_hook("chestertons_fence", priority=11.7)
def chestertons_fence(context: HookContext) -> HookResult:
    """Understand existing code before changing it."""
    config = _load_config()
    if not config.get("enabled") or not config.get("chestertons_fence"):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _has_modify_intent(prompt):
        return HookResult.empty()
    return HookResult(context=_FENCE_INJECTION, tokens=len(_FENCE_INJECTION) // 4, priority=11.7)



# ---------------------------------------------------------------------------
# Enhancer 5: Calibrated Confidence
# ---------------------------------------------------------------------------


_CONFIDENCE_INJECTION = (
    "**Calibrated Confidence**: For key claims in your response, "
    "state confidence: HIGH (verified via tool output/docs), "
    "MEDIUM (based on code reading), or LOW (inference — flag it). "
    "Do not present LOW-confidence claims as facts."
)



@register_hook("calibrated_confidence", priority=11.8)
def calibrated_confidence(context: HookContext) -> HookResult:
    """Force confidence calibration on diagnostic and implementation claims."""
    config = _load_config()
    if not config.get("enabled") or not config.get("calibrated_confidence"):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _has_diagnostic_or_impl_intent(prompt):
        return HookResult.empty()
    return HookResult(context=_CONFIDENCE_INJECTION, tokens=len(_CONFIDENCE_INJECTION) // 4, priority=11.8)



# ---------------------------------------------------------------------------
# Enhancer 6: Socratic Decomposition
# ---------------------------------------------------------------------------


_SOCRATIC_INJECTION = (
    "**Decompose First**: This is a broad request. Before diving in, "
    "break it into 2-4 concrete sub-questions that need answering. "
    "Tackle them in order. If any sub-question changes the approach "
    "to later ones, say so."
)



@register_hook("socratic_decomposition", priority=11.3)
def socratic_decomposition(context: HookContext) -> HookResult:
    """Decompose vague, lengthy prompts into sub-questions before acting."""
    config = _load_config()
    if not config.get("enabled") or not config.get("socratic_decomposition"):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _is_vague_long_prompt(prompt, config):
        return HookResult.empty()
    return HookResult(context=_SOCRATIC_INJECTION, tokens=len(_SOCRATIC_INJECTION) // 4, priority=11.3)


@register_hook("coach_note_reader", priority=5.0)
def coach_note_reader(_context: HookContext) -> HookResult:
    """Inject coach note from previous Stop advisory if present."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop_advisory import read_and_clear_coach_note


        note = read_and_clear_coach_note()  # reads session scope from env vars
        if not note:
            return HookResult.empty()


        injection = f"**Coach Note** (from previous turn): {note}"
        return HookResult(context=injection, tokens=len(injection) // 4, priority=5.0)
    except Exception:
        return HookResult.empty()



# ---------------------------------------------------------------------------
# Enhancer 7: analysis_protocol_gate (priority 11.2)
# ---------------------------------------------------------------------------
# Fires before all other cognitive enhancers when the prompt signals a
# failure-analysis, RCA, or "missing principle" conversation.
#
# Two-layer trigger:
#   Layer 1: Regex (fast path) — matches explicit RCA/correction language
#   Layer 2: Semantic similarity (all-MiniLM-L6-v2) against 10 FAP prototypes
#            Mid-band (MID_SIM..HIGH_SIM) escalates to claude-haiku classifier
# ---------------------------------------------------------------------------



try:
    import numpy as _np
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


_FAP_MODEL: _SentenceTransformer | None = None
_FAP_MODEL_LOCK = threading.Lock()
_FAP_MODEL_LOADING = False



def _load_fap_model() -> _SentenceTransformer | None:
    """Load sentence-transformers model; return cached instance."""
    global _FAP_MODEL, _FAP_MODEL_LOADING
    if not _ST_AVAILABLE:
        return None
    if _FAP_MODEL is not None:
        return _FAP_MODEL
    with _FAP_MODEL_LOCK:
        if _FAP_MODEL is not None:
            return _FAP_MODEL
        if _FAP_MODEL_LOADING:
            return None  # Still loading — skip Layer 2 this call
        _FAP_MODEL_LOADING = True
        try:
            _FAP_MODEL = _SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _FAP_MODEL = None
        finally:
            _FAP_MODEL_LOADING = False
    return _FAP_MODEL



def _prewarm_fap_model() -> None:
    """Pre-warm model in background so first real call doesn't block."""
    threading.Thread(target=_load_fap_model, daemon=True).start()



_prewarm_fap_model()


# --- Layer 1: Regex patterns ---


_RCA_PATTERN = re.compile(
    r'\b(root\s+cause|why\s+did\s+(?:it|this|that)\s+(?:fail|break|happen)|'
    r'what\s+caused|diagnos[ei]|post[-\s]?mortem|incident\s+review|'
    r'failure\s+analysis|bug\s+report|retrospective|investigate\s+(?:the|this|why))\b',
    re.IGNORECASE,
)


_META_PRINCIPLE_PATTERN = re.compile(
    r'\b(wrong\s+(?:level|abstraction|approach|layer)|'
    r'missing\s+(?:principle|pattern|abstraction|invariant|gap[s]?)|'
    r'broader\s+(?:principle|pattern|issue|problem)|'
    r'(?:this|the)\s+(?:fix|patch|solution)\s+(?:doesn\'t|won\'t)\s+(?:scale|generalize|hold)|'
    r'(?:should|need\s+to)\s+(?:generalize|step\s+back|zoom\s+out|think\s+bigger))\b',
    re.IGNORECASE,
)


_CORRECTION_PATTERN = re.compile(
    r'\b(you\s+(?:missed|ignored|overlooked|skipped)|'
    r"that's\s+(?:not\s+right|wrong|incorrect|not\s+the\s+point)|"
    r"that\s+doesn't\s+(?:address|fix|solve)\s+(?:the|my)|"
    r'still\s+(?:missing|not\s+addressing|wrong)|'
    r'you\s+(?:are|were|re)\s+(?:still\s+)?(?:solving|fixing|patching)\s+the\s+wrong)\b',
    re.IGNORECASE,
)


# --- Layer 2: Semantic similarity thresholds and prototypes ---


_HIGH_SIM: float = 0.82   # Auto-fire above this
_MID_SIM: float  = 0.65   # Escalate to LLM classifier between MID and HIGH
_CLASSIFIER_TIMEOUT: float = 3.0  # seconds — Windows-safe threading timeout


_FAP_PROTOTYPES = [
    "You're solving the problem at the wrong level of abstraction",
    "What's the root cause of this failure?",
    "I think you're missing a more general principle here",
    "That fix doesn't address the underlying issue",
    "Can you do a post-mortem on what went wrong?",
    "What class of bug is this? Are there other instances?",
    "You're patching symptoms, not the cause",
    "This feels like the wrong abstraction level to me",
    "What invariant would catch this entire class of bugs?",
    "You missed the broader pattern — this isn't just one hook",
]


_FAP_PROTO_EMBEDDINGS: _np.ndarray | None = None
_FAP_PROTO_LOCK = threading.Lock()



def _get_proto_embeddings(model: _SentenceTransformer) -> _np.ndarray | None:
    """Compute and cache prototype embeddings."""
    global _FAP_PROTO_EMBEDDINGS
    if _FAP_PROTO_EMBEDDINGS is not None:
        return _FAP_PROTO_EMBEDDINGS
    with _FAP_PROTO_LOCK:
        if _FAP_PROTO_EMBEDDINGS is not None:
            return _FAP_PROTO_EMBEDDINGS
        try:
            _FAP_PROTO_EMBEDDINGS = model.encode(_FAP_PROTOTYPES, normalize_embeddings=True)
        except Exception:
            return None
    return _FAP_PROTO_EMBEDDINGS



def _cosine_max(prompt_vec: _np.ndarray, proto_vecs: _np.ndarray) -> float:
    """Return max cosine similarity between prompt vector and all prototypes."""
    sims = proto_vecs @ prompt_vec
    return float(sims.max())



def _llm_classifier_call(prompt: str) -> bool:
    """Call claude-haiku to classify mid-band prompts. Returns True = fire FAP."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        examples = (
            "YES: 'You're solving this at the wrong abstraction level'\n"
            "YES: 'What's the root cause here?'\n"
            "YES: 'That fix doesn't address the underlying issue'\n"
            "NO: 'Can you fix this bug for me?'\n"
            "NO: 'How do I implement this feature?'\n"
            "NO: 'What does this code do?'\n"
        )
        sys_prompt = (
            "You classify user prompts. Answer only YES or NO.\n"
            "YES = prompt asks for failure analysis, root cause, missing principle, "
            "or meta-level correction of an LLM's reasoning approach.\n"
            "NO = prompt is a normal task, question, or implementation request.\n\n"
            f"Examples:\n{examples}"
        )
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=10,
            system=sys_prompt,
            messages=[{"role": "user", "content": prompt[:500]}],
        )
        answer = msg.content[0].text.strip().upper()
        return answer.startswith("YES")
    except Exception:
        return False  # Fail open — don't fire FAP on classifier error



def _llm_classify_with_timeout(prompt: str, timeout: float) -> bool:
    """Run LLM classifier in a daemon thread with timeout (Windows-safe)."""
    result: list[bool] = [False]


    def _worker() -> None:
        result[0] = _llm_classifier_call(prompt)


    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout)
    return result[0]



def _should_inject_fap(prompt: str) -> bool:
    """Two-layer FAP trigger. Returns True if FAP injection should fire."""
    if not prompt or len(prompt.strip()) < 15:
        return False


    # Layer 1: Regex fast path
    if (_RCA_PATTERN.search(prompt) or
            _META_PRINCIPLE_PATTERN.search(prompt) or
            _CORRECTION_PATTERN.search(prompt)):
        return True


    # Layer 2: Semantic similarity
    if not _ST_AVAILABLE:
        return False
    model = _load_fap_model()
    if model is None:
        return False


    try:
        proto_vecs = _get_proto_embeddings(model)
        if proto_vecs is None:
            return False
        prompt_vec = model.encode([prompt], normalize_embeddings=True)[0]
        sim = _cosine_max(prompt_vec, proto_vecs)


        if sim >= _HIGH_SIM:
            return True
        # Removed API call - use local classification only
        # Medium-similarity edge cases are skipped rather than causing timeout
        return False
    except Exception:
        return False



_FAP_INJECTION = (
    "**Failure Analysis Protocol active.**\n"
    "Before diagnosing: (1) lock scope to the specific instance, (2) confirm you "
    "have the artifact (don't proceed on descriptions), (3) build a 3-hop causal chain, "
    "(4) generalization scan — name ≥1 other system sharing this failure class, "
    "(5) classify fixes S/D/R, (6) design the failure path (degradation marker), "
    "(7) codification gate — fix is incomplete without a test invariant.\n"
    "Full protocol: P:/docs/failure-analysis-protocol.md"
)



@register_hook("analysis_protocol_gate", priority=11.2)
def analysis_protocol_gate(context: HookContext) -> HookResult:
    """Inject FAP checklist when prompt signals failure analysis or meta-correction."""
    config = _load_config()
    if not config.get("enabled") or not config.get("analysis_protocol_gate", True):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _should_inject_fap(prompt):
        return HookResult.empty()
    return HookResult(
        context=_FAP_INJECTION,
        tokens=len(_FAP_INJECTION) // 4,
        priority=11.2,
    )

"

## Assistant

This is a Claude Code **UserPromptSubmit** hook module that automatically injects “thinking scaffolds” into your prompts so the LLM reasons more rigorously before coding, planning, or doing failure analysis.[1][2]

## What it does

- Hooks into the `UserPromptSubmit` event so every substantial prompt can be analyzed before Claude responds, and extra context text can be injected via `additionalContext`.[2][3][1]
- Detects prompt intent (implement, modify, plan, debug, diagnose, etc.) with regexes and basic heuristics, then selectively fires one or more “cognitive enhancers” based on that intent.  
- Uses a JSON config (`cognitive_enhancers_config.json`) to turn individual enhancers on/off, tune thresholds (e.g., min length, socratic_min_length), and blacklist operational slash-skills that should not be decorated.  

## The seven “cognitive enhancers”

Each enhancer is a small prompt fragment injected ahead of your actual request, effectively acting as a local reasoning policy for Claude Code.[1][2]

| Enhancer name             | Trigger intent                                          | Purpose in practice                                                                 |
|---------------------------|--------------------------------------------------------|-------------------------------------------------------------------------------------|
| assumption_surfacing      | Implementation-oriented prompts                        | Force the model to state assumptions about scope, existing behavior, and user goal. |
| outcome_anchoring         | Plan or implementation prompts                         | Define “done” and acceptance criteria before designing or coding.                   |
| inversion_prompting       | Implementation prompts                                 | Ask “what would make this fail?” and require a concrete risk plus mitigation.      |
| chestertons_fence         | Modify/refactor/change prompts                         | Make the model explain why current code exists before changing it.                 |
| calibrated_confidence     | Diagnostic or implementation prompts                   | Require HIGH/MEDIUM/LOW confidence labeling for key claims.                        |
| socratic_decomposition    | Long, vague prompts without specific code references   | Break mega-prompts into 2–4 sub-questions and tackle them sequentially.            |
| analysis_protocol_gate    | Failure analysis / RCA / “wrong abstraction” prompts   | Inject a detailed Failure Analysis Protocol checklist (scope, causal chain, S/D/R).|

The last one (“Failure Analysis Protocol active…”) is a gate that only fires when the text looks like root-cause-analysis, meta-level correction, or “you’re solving the wrong problem” feedback, using regex plus optional sentence-transformers similarity against prototype RCA phrases.[4][5]

## How it plugs into your workflow

- Implemented as a Python hook module using the Claude Code hooks API; functions are registered with `@register_hook("...")` and given priorities so they stack predictably when multiple enhancers fire on the same prompt.[2][1]
- Maintains a default config in code but overlays it with `cognitive_enhancers_config.json` if present, “fail open” so that errors in the config don’t break your workflow.  
- Treats slash-commands as skills: most skills are enhanced by default except for a configurable `skip_skills` list of operational commands like `/commit`, `/push`, `/search`, etc., so only “thinking” skills get cognitive scaffolding.[4]

In short, this file is an opinionated prompt-engineering plugin for Claude Code: a set of pre-prompt injections that systematically upgrade Claude’s reasoning quality, safety, and meta-cognition at prompt time, without you having to remember to ask for that process each time.

## Human

Do you see any gaps or opportunities with it?

## Assistant

Yes. It’s already strong, but there are several clear opportunities to tighten it and extend its impact.[1][2]

## 1. Control and escape hatches

- Add an explicit “bypass” convention (e.g., leading `*` or `!`) so power users can skip all enhancers for a single prompt without editing config.[3]
- Consider a lightweight “mode” flag (e.g., `#fast`, `#deep`) to dial scaffolding up or down per prompt instead of only global config.  

## 2. Ask-user and interaction hooks

- Right now everything is one-way injection; for genuinely ambiguous prompts, you could optionally trigger an AskUser-style clarification instead of just scaffolding.[2][3]
- Example: if `_is_vague_long_prompt` fires and confidence in intent is low, ask 1–2 disambiguation questions before proceeding, then update the prompt.  

## 3. More nuanced intent detection

- The regex intent detector is good but brittle; there’s no distinction between “small local change” and “large refactor,” nor between UX copy edits and core-logic changes.  
- You could tier enhancers based on additional signals (file types, recent tool use, plan mode on/off) so heavy protocols like FAP don’t trigger on lightweight edits.[2]

## 4. Coverage gaps in cognitive scaffolds

- There’s no explicit “context hygiene” or “plan-of-record” enhancer (e.g., “summarize the current repo/task state first”), which Claude Code best-practices highlight as high leverage.[4]
- You might add: a “CIF” injector (Context–Intent–Format) for under-specified prompts, or a “test-first” enhancer that biases toward writing/ updating tests before implementation.  

## 5. Performance and model-loading concerns

- The sentence-transformers + numpy path for FAP is powerful but heavy; on some setups the first call will be slow and you already have locking and prewarm logic.  
- Consider: (a) making FAP’s semantic layer optional via config, (b) caching similarity decisions per session, or (c) using cheaper local heuristics unless a “RCA keyword” is present.[5]

## 6. Integration with other hooks and skills

- This module is isolated at UserPromptSubmit; you could coordinate with PreToolUse hooks to reinforce calibrated confidence when tools return ambiguous or conflicting signals.[6][2]
- Certain project-specific skills (e.g., `/deploy`, `/migrate-db`) might deserve mandatory FAP or inversion checks; a per-skill enhancer map in config would give finer control than a single skip list.  

## 7. Observability and self-improvement

- There’s no telemetry: you don’t log which enhancers fired, how often, or whether users overrode them.  
- Adding a minimal log or structured event output would let you see if, for example, socratic_decomposition is firing too often and causing “prompt fatigue,” which prompt-engineering literature warns about.[7][8]

## Human

can we make it not 'heavy' and not 'brittle' at the same time?

## Assistant

Yes, but you need to change *where* you spend complexity rather than just adding more of it.[1][2]

## 1. Make heuristics do 80%, not 100%

- Keep fast regex/length checks as the primary router, but narrow their scope to very obvious cases (e.g., “post‑mortem”, “root cause”, “refactor this function”).  
- Drop or simplify the semantic-embedding FAP layer; for edge-y, ambiguous prompts, let the main LLM handle meta‑reasoning with a generic “meta‑check” scaffold instead of a separate model.[3][4]

## 2. Use cheap “meta scaffolds” instead of heavy classifiers

- Instead of: “if semantic sim > threshold then inject FAP”, use: “if vague/diagnostic-ish, prepend a short, generic failure-analysis scaffold” and let the model decide whether to fully invoke it.[5][1]
- This trades brittle intent classification for stable instructions like “If this looks like failure analysis, follow these steps; otherwise answer normally,” which modern LLMs handle well.  

## 3. Add user-visible modes, not hidden magic

- Introduce lightweight, user-controlled modes in the prompt (e.g., `#rca`, `#safety`, `#fast`) that directly toggle specific enhancers without routing through complex intent logic.[6]
- Heuristics then only auto-fire the most obviously correct enhancer; everything else is opt‑in, which reduces brittleness because the user can steer when the router is uncertain.  

## 4. Prefer “soft triggers” over hard gates

- Where you’re unsure, inject *guidance* instead of *requirements*: “If appropriate, first break this into sub‑questions” rather than always forcing Socratic decomposition on long prompts.[2][1]
- Soft triggers mean a misfire costs little—the model can decide “not appropriate here,” which lets you simplify detection logic and avoid heavy side-chains.  

## 5. Design for graceful degradation

- Make each enhancer independently safe to over-apply: short, generic, and cheap in tokens so that a false positive is mildly annoying, not catastrophic.  
- With that constraint, you can accept simpler, non-embedding heuristics, because the worst-case outcome is “extra reasoning help,” not protocol spam or latency spikes.[7][2]

## Human

are there popular repos that follow the same idea you are proposing?  what can we copy from them?

## Assistant

There are a few good patterns in the wild that line up with what you’re trying to do, and you can steal ideas from them without adding much weight.[1][2]

## 1. intent-kit: mixed routing, simple graph

intent-kit is a Python framework for intent-driven workflows that combines keyword/regex, classic ML, and LLM-based classifiers in a single “intent graph.” Useful ideas to copy:[1]

- **Layered routing:** Start with cheap rules (regex, length, obvious keywords) and only fall back to smarter routing when needed, instead of always running embeddings.  
- **Explicit intent enum/config:** Treat “enhancers” as first-class intent nodes with names and metadata, not just ad-hoc functions; this makes routing more testable and debuggable.  
- **Deterministic behavior:** Define all valid “enhancer intents” and transitions up front, so you can reason about which scaffolds may fire and write unit tests for them.[1]

Applied to your module: map each cognitive enhancer to a small intent node, and have a tiny router function that chooses nodes via simple rules first, no sentence-transformers required.

## 2. seedling: config-driven topics and intents

seedling is “simple and scalable intent recognition using LLMs,” built around YAML topic/intent definitions rather than hardcoded logic.[2]

What to copy:

- **Config-first taxonomy:** Move the mapping from prompt → “this is implementation/diagnostic/rca/meta” into config (topics and intents), so your regexes are just helpers, not the source of truth.  
- **Topic grouping:** Group enhancers under higher-level topics like “implementation safety,” “failure analysis,” “prompt decomposition,” and let a single topic selection decide which specific enhancer fires.[2]
- **Pluggable classifier:** Keep your current regex router, but make it one strategy behind an interface; later you can drop in a tiny LLM-based classifier or embeddings without rewriting hook logic.  

This would make your system less brittle: you edit YAML/JSON to evolve how prompts map to topics, instead of touching Python and regexes every time.

## 3. Scaffold / scaffolding repos: small, composable templates

Scaffold-style prompting work focuses on reusable reasoning templates (“scaffolds”) that can be selected or combined per task.[3][4]

What to copy:

- **Tiny, composable scaffolds:** Keep each enhancer extremely short and focused so misfires are cheap; that lets you rely more on simple heuristics because the downside is low.  
- **Meta-prompts with “if appropriate” language:** Many scaffolds are written as conditional guidance (“If this is X, then do Y”), which lets the LLM self-filter when the router guessed wrong.[4]
- **Named scaffolds:** Give each injection a stable name/id and brief description in config, so you can experiment (A/B) and log usage.  

For your module, this means rewriting injections to be 1–2 lines with “if appropriate” phrasing and giving them IDs you can log and toggle.

## 4. Concrete changes you could make

Putting it together, here’s what you can directly copy/adapt:

- **Config-driven enhancer graph:**  
  - Define `topics` (e.g., `implementation`, `diagnostic`, `meta_rca`) and list which enhancers can attach to each, in JSON/YAML.  
  - Use your regexes only to pick a topic; then select enhancers from that topic via simple rules (e.g., at most 2 per prompt).  

- **Strategy interface for intent detection:**  
  - Create `IntentDetector` with a `detect(prompt) -> {topic, flags}`; start with a purely heuristic implementation.  
  - Later, optionally add a `LLMIntentDetector` (like seedling’s LLM backend) behind a config flag, without touching hook registrations.[5][2]

- **Make misfires cheap:**  
  - Shorten injections and make them conditional (“If this seems like modifying existing code, first …”), copying the “soft scaffold” style from meta-prompting guides.[4]
  - Then remove heavy semantic FAP logic entirely or gate it behind `"fap_semantic_enabled": false` by default.  

- **Add minimal observability:**  
  - Borrow intent-kit’s emphasis on reliability and testability: log `{prompt_hash, detected_topic, enhancers_fired}` so you can see where heuristics are wrong and adjust rules, not models.[6][1]

These patterns let you stay lightweight (no mandatory embeddings, no extra API calls) while being less brittle, because routing becomes config-driven, testable, and tolerant of occasional misfires.

## Human

please create working code that has your ideas implemented.

## Assistant

Here’s a refactored, working version of your hook module that bakes in the ideas we discussed: lightweight, config‑driven topics, soft scaffolds, no heavy embeddings, and testable routing. You can drop this in as `cognitive_enhancers.py` (or similar) in your Claude Code hooks package and wire it to `UserPromptSubmit` as before.[1][2]

```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import HookContext, HookResult
from .registry import register_hook


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cognitive_enhancers_config.json"


@dataclass
class Enhancer:
    key: str
    topic: str
    injection: str
    max_per_prompt: int = 1
    # If True, this enhancer is cheap/small enough that occasional misfires are acceptable
    soft: bool = True


_DEFAULT_CONFIG = {
    "enabled": True,
    # Global knobs
    "min_prompt_length": 30,
    "socratic_min_length": 200,
    "enhance_skills": True,
    "skip_skills": [
        "commit", "push", "search", "search-more", "obs", "timeline",
        "quota", "bgkill", "clear-notifications", "clear_restore",
        "checkpoint-list", "checkpoint-diff", "checkpoint-delete",
        "checkpoint-restore", "context-status", "llm-health",
        "llm-performance", "llm-models", "recent", "catchup",
        "session", "restore", "help",
    ],
    # Topic toggles (high‑level routing targets)
    "topics": {
        "implementation": True,
        "diagnostic": True,
        "meta_rca": True,
        "decomposition": True,
    },
    # Per‑enhancer toggles
    "enhancers": {
        "assumption_surfacing": True,
        "outcome_anchoring": True,
        "inversion_prompting": True,
        "chestertons_fence": True,
        "calibrated_confidence": True,
        "socratic_decomposition": True,
        "failure_analysis_soft": True,
        "coach_note_reader": True,
    },
    # Max number of enhancers to inject per prompt
    "max_enhancers_per_prompt": 3,
    # Explicit modes users can request in the prompt (e.g. "#rca", "#fast")
    "modes": {
        "rca": {"topic": "meta_rca"},
        "deep": {"topic": "implementation"},
        "fast": {"disable_all": True},
    },
}


def _load_config() -> dict:
    """Load config with defaults. Fail open on any error."""
    config = json.loads(json.dumps(_DEFAULT_CONFIG))  # deep copy
    try:
        if CONFIG_PATH.exists():
            user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # shallow merge for simplicity; you can make this smarter if needed
            for k, v in user_config.items():
                if isinstance(v, dict) and isinstance(config.get(k), dict):
                    config[k].update(v)
                else:
                    config[k] = v
    except Exception:
        pass
    return config


# ---------------------------------------------------------------------------
# Enhancer definitions (soft, small scaffolds)
# ---------------------------------------------------------------------------

ENHANCERS: Dict[str, Enhancer] = {
    "assumption_surfacing": Enhancer(
        key="assumption_surfacing",
        topic="implementation",
        injection=(
            "**Assumption Check (if appropriate)**: "
            "Briefly state your key assumptions about scope, existing behavior, "
            "and the user's real goal before proposing changes."
        ),
    ),
    "outcome_anchoring": Enhancer(
        key="outcome_anchoring",
        topic="implementation",
        injection=(
            "**Outcome Anchor (if appropriate)**: "
            "In 1–2 sentences, describe what 'done' looks like and what should "
            "work when this is complete, then work backward from that target."
        ),
    ),
    "inversion_prompting": Enhancer(
        key="inversion_prompting",
        topic="implementation",
        injection=(
            "**Inversion Check (if appropriate)**: "
            "Name one realistic way this change could fail or break behavior, "
            "and show how your approach mitigates that risk."
        ),
    ),
    "chestertons_fence": Enhancer(
        key="chestertons_fence",
        topic="implementation",
        injection=(
            "**Chesterton's Fence (if appropriate)**: "
            "If you're modifying existing code, first explain why it was likely "
            "written this way and what problem it currently solves."
        ),
    ),
    "calibrated_confidence": Enhancer(
        key="calibrated_confidence",
        topic="diagnostic",
        injection=(
            "**Calibrated Confidence (if appropriate)**: "
            "Label key claims as HIGH (tool-verified), MEDIUM (from code reading), "
            "or LOW (speculative), and avoid stating LOW confidence items as facts."
        ),
    ),
    "socratic_decomposition": Enhancer(
        key="socratic_decomposition",
        topic="decomposition",
        injection=(
            "**Decompose First (if appropriate)**: "
            "If this request is broad, break it into 2–4 concrete sub-questions "
            "and tackle them in order, noting if answers change later steps."
        ),
    ),
    "failure_analysis_soft": Enhancer(
        key="failure_analysis_soft",
        topic="meta_rca",
        injection=(
            "**Failure Analysis (if appropriate)**: "
            "If this is about understanding a failure or root cause, first lock "
            "scope to a concrete instance, outline a short causal chain, and then "
            "suggest at least one change that would prevent this class of issue."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Intent detection patterns (lightweight)
# ---------------------------------------------------------------------------

_IMPL_RE = re.compile(
    r"\b(build|create|implement|refactor|optimize|add|write|develop|code|make|"
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

_DIAGNOSTIC_RE = re.compile(
    r"\b(debug|investigate|diagnose|analyze|explain\s+why|root\s+cause|"
    r"figure\s+out|what's\s+wrong|what\s+caused|troubleshoot|"
    r"why\s+does|why\s+is|why\s+did|how\s+does|what\s+happens)\b",
    re.IGNORECASE,
)

_META_RCA_RE = re.compile(
    r"\b(root\s+cause|post[-\s]?mortem|incident\s+review|failure\s+analysis|"
    r"retrospective|underlying\s+issue|wrong\s+abstraction|wrong\s+level)\b",
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
_SLASH_RE = re.compile(r"^\s*/[a-z]", re.IGNORECASE)
_MODE_TAG_RE = re.compile(r"#([a-zA-Z0-9_]+)")


def _extract_skill_name(prompt: str) -> Optional[str]:
    """Extract skill name from a slash command, or None if not a slash command."""
    stripped = prompt.strip()
    if not _SLASH_RE.match(stripped):
        return None
    return stripped.lstrip("/").split()[0] if stripped else None


def _extract_modes(prompt: str) -> List[str]:
    """Extract inline mode tags like '#rca' or '#fast' from the prompt."""
    return [m.group(1).lower() for m in _MODE_TAG_RE.finditer(prompt)]


def _is_actionable_prompt(prompt: str, config: dict) -> bool:
    """Check if prompt is substantial enough to warrant cognitive injection."""
    if not prompt or len(prompt.strip()) < config.get("min_prompt_length", 30):
        return False
    stripped = prompt.strip()
    # Handle slash commands: allow unless blacklisted
    skill = _extract_skill_name(stripped)
    if skill is not None:
        if not config.get("enhance_skills", True):
            return False
        skip_list = config.get("skip_skills", [])
        if skill in skip_list:
            return False
        # Non-blacklisted skill — continue
    # Pure one-line questions that are not implementation-related can pass through
    if _QUESTION_ONLY_RE.match(stripped) and not _IMPL_RE.search(stripped):
        return False
    return True


def _is_vague_long_prompt(prompt: str, config: dict) -> bool:
    """Long prompts without concrete code references are treated as 'vague'."""
    min_len = config.get("socratic_min_length", 200)
    if len(prompt.strip()) < min_len:
        return False
    if _SPECIFIC_REF_RE.search(prompt):
        return False
    return True


@dataclass
class DetectedIntent:
    topic: Optional[str]
    flags: Dict[str, bool]


def _detect_intent(prompt: str, config: dict, modes: List[str]) -> DetectedIntent:
    """
    Lightweight intent detection.
    - Uses explicit modes (#rca, #deep, #fast) when present.
    - Otherwise, uses regex + heuristics to select a primary topic.
    """
    text = prompt.strip()

    # Mode overrides
    topics_cfg = config.get("topics", {})
    modes_cfg = config.get("modes", {})
    flags: Dict[str, bool] = {}

    for mode in modes:
        mode_cfg = modes_cfg.get(mode)
        if not mode_cfg:
            continue
        if mode_cfg.get("disable_all"):
            return DetectedIntent(topic=None, flags={"disable_all": True})
        topic = mode_cfg.get("topic")
        if topic and topics_cfg.get(topic, True):
            return DetectedIntent(topic=topic, flags={"from_mode": True})

    # Heuristic routing
    impl = bool(_IMPL_RE.search(text) or _PLAN_RE.search(text))
    diag = bool(_DIAGNOSTIC_RE.search(text))
    meta_rca = bool(_META_RCA_RE.search(text))
    vague = _is_vague_long_prompt(text, config)

    if meta_rca and topics_cfg.get("meta_rca", True):
        return DetectedIntent(topic="meta_rca", flags={"meta_rca": True})
    if diag and topics_cfg.get("diagnostic", True):
        return DetectedIntent(topic="diagnostic", flags={"diagnostic": True})
    if impl and topics_cfg.get("implementation", True):
        return DetectedIntent(topic="implementation", flags={"implementation": True})
    if vague and topics_cfg.get("decomposition", True):
        return DetectedIntent(topic="decomposition", flags={"decomposition": True})

    # No strong signal; no primary topic
    return DetectedIntent(topic=None, flags={})


def _select_enhancers(intent: DetectedIntent, prompt: str, config: dict) -> List[Enhancer]:
    """Select a small set of enhancers for this prompt based on topic + heuristics."""
    if intent.flags.get("disable_all"):
        return []

    max_total = config.get("max_enhancers_per_prompt", 3)
    enabled_map: Dict[str, bool] = config.get("enhancers", {})
    result: List[Enhancer] = []

    topic = intent.topic

    def _add(key: str) -> None:
        if len(result) >= max_total:
            return
        if not enabled_map.get(key, True):
            return
        enh = ENHANCERS.get(key)
        if not enh:
            return
        if topic and enh.topic != topic:
            return
        result.append(enh)

    # Topic-specific defaults
    if topic == "implementation":
        _add("assumption_surfacing")
        # Only add Chesterton's Fence if we see modify-ish language
        if _MODIFY_RE.search(prompt):
            _add("chestertons_fence")
        _add("outcome_anchoring")
        _add("inversion_prompting")
    elif topic == "diagnostic":
        _add("calibrated_confidence")
        _add("failure_analysis_soft")
    elif topic == "meta_rca":
        _add("failure_analysis_soft")
        _add("calibrated_confidence")
    elif topic == "decomposition":
        _add("socratic_decomposition")
        # Implementation hints can still help in vague prompts
        _add("assumption_surfacing")

    # If no topic or no enhancers selected, fall back to a minimal set
    if not result and _is_vague_long_prompt(prompt, config):
        # Gentle default for mega-prompts
        _add("socratic_decomposition")

    return result


def _build_injection(enhancers: List[Enhancer]) -> str:
    """Combine multiple enhancer injections into a single context block."""
    if not enhancers:
        return ""
    # Keep them short and ordered; separate with blank lines
    parts = [e.injection for e in enhancers]
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main cognitive enhancers hook
# ---------------------------------------------------------------------------

@register_hook("cognitive_enhancers", priority=11.0)
def cognitive_enhancers(context: HookContext) -> HookResult:
    """
    Unified UserPromptSubmit hook that:
    - Inspects prompt & modes.
    - Selects at most N small, soft enhancers.
    - Injects them as additional context.
    """
    config = _load_config()
    if not config.get("enabled", True):
        return HookResult.empty()

    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()

    modes = _extract_modes(prompt)
    intent = _detect_intent(prompt, config, modes)
    enhancers = _select_enhancers(intent, prompt, config)
    if not enhancers:
        return HookResult.empty()

    injection = _build_injection(enhancers)
    if not injection:
        return HookResult.empty()

    return HookResult(
        context=injection,
        tokens=len(injection) // 4,
        priority=11.0,
    )


# ---------------------------------------------------------------------------
# Coach note reader stays as a separate, low-priority hook
# ---------------------------------------------------------------------------

@register_hook("coach_note_reader", priority=5.0)
def coach_note_reader(_context: HookContext) -> HookResult:
    """Inject coach note from previous Stop advisory if present."""
    config = _load_config()
    if not config.get("enhancers", {}).get("coach_note_reader", True):
        return HookResult.empty()

    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop_advisory import read_and_clear_coach_note

        note = read_and_clear_coach_note()  # reads session scope from env vars
        if not note:
            return HookResult.empty()

        injection = f"**Coach Note** (from previous turn): {note}"
        return HookResult(
            context=injection,
            tokens=len(injection) // 4,
            priority=5.0,
        )
    except Exception:
        return HookResult.empty()
```

### How this implements the ideas

- **No heavy embeddings / extra models:** All routing is regex + length + optional `#mode` tags; there’s no sentence‑transformers or external API classifier in the hook path.[3]
- **Config-driven topics and enhancers:** Topics (`implementation`, `diagnostic`, `meta_rca`, `decomposition`) and per‑enhancer toggles live in config, not scattered across code; you can evolve behavior by editing JSON.[4][1]
- **Soft, short scaffolds:** Each injection is a small, conditional hint (“if appropriate”) so false positives are cheap and you don’t need brittle, ultra-precise detection.[5]
- **User modes instead of magic:** Inline tags like `#rca` or `#fast` let power users steer routing explicitly, matching best practices from intent frameworks.[6][1]
- **Single unified hook:** Instead of seven separate hooks racing by priority, there’s one `cognitive_enhancers` hook that decides which scaffolds to apply and injects them in a single block, which is easier to reason about and test with fixture prompts.[2][1]

You can now adjust behavior by editing `cognitive_enhancers_config.json`, add new enhancers by updating `ENHANCERS` and `_select_enhancers`, and optionally later plug in a more advanced intent detector behind `_detect_intent` without touching the hook registrations.

## Human

"## Architecture Review: Proposed `cognitive_enhancers.py` Refactor

This is an **ARCHITECTURE_REVIEW** ΓÇö evaluating Stephen Collins's refactored hook design against our current implementation.

---

### Current State vs. Proposed Design

| Aspect | Current Implementation | Proposed Refactor |
|--------|----------------------|-------------------|
| **Intent Detection** | Sentence-transformers + API fallback | Pure regex + length heuristics |
| **Hook Structure** | 7 separate hooks @register_hook | 1 unified hook + 1 coach_note hook |
| **Configuration** | JSON config (partial) | Full JSON-driven topics/enhancers |
| **Injection Style** | Direct, mandatory | "Soft" (if appropriate) |
| **User Control** | None | Inline modes (#rca, #fast) |
| **Dependencies** | sentence-transformers, numpy | Standard library only |

---

### Analysis: What This Solves

Γ£à **Our 56-second timeout issue** ΓÇö Eliminates API call entirely (we removed it, but this design never had it)  
Γ£à **Complexity** ΓÇö Single hook instead of 7 competing priorities  
Γ£à **Maintainability** ΓÇö Config-driven, no code changes for tuning  
Γ£à **Performance** ΓÇö No embedding model loading (~500ms saved)  

---

### Analysis: Trade-offs and Risks

ΓÜá∩╕Å **Detection Accuracy Loss**

```python
# Current: Semantic similarity thresholding
sim = _compute_similarity(prompt, _FAP_PROTOTYPES)
if sim >= 0.85: inject_FAP()
elif sim >= 0.65: escalate_to_API()  # We removed this

# Proposed: Regex patterns only
if _META_RCA_RE.search(prompt): inject_FAP()
```

**Risk**: False negatives increase. Our current system catches semantically-related prompts ("system crashed", "production failure") that regex might miss.

---

ΓÜá∩╕Å **"Soft" Injections May Be Ignored**

```python
injection = "**Failure Analysis (if appropriate)**: If this is about..."
```

**Risk**: LLMs learn to skip conditional hints. Our current mandatory injections ("**MANDATORY OPERATING RULES**") have higher compliance.

---

ΓÜá∩╕Å **Topic Gating Creates Silos**

```python
if topic == "implementation":
    _add("assumption_surfacing")
elif topic == "diagnostic":
    _add("calibrated_confidence")
```

**Risk**: Some prompts need both (e.g., "debug why the refactored login fails"). Current system allows overlap.

---

### Compatibility with Our Fix

**Our change** (line 549):
```python
if sim >= _HIGH_SIM:
    return True
# Removed API call - use local classification only
return False
```

**Proposed design** removes the entire similarity system, which is consistent with our fix but more aggressive.

---

### Recommendation

**Option A: Hybrid Approach** ΓÇö Keep semantic similarity for FAP detection (high-value), use proposed config system for everything else.

```python
# Keep: FAP detection with embeddings
if _is_failure_analysis_prompt(prompt):  # Semantic similarity
    return _FAP_INJECTION

# Adopt: Proposed config-driven routing for other enhancers
topics = config.get("topics", {})
enhancers = _select_from_config(intent.topic)
```

**Rationale**: 
- Failure analysis protocols are critical (we've seen 56-second consequences)
- Other enhancers (assumption surfacing, outcome anchoring) can tolerate regex-based detection
- Soft scaffolds are acceptable for non-critical injections

**Option B: Full Migration** ΓÇö Adopt proposed design as-is, accept higher false negative rate.

**Rationale**:
- Simpler codebase
- Faster hook execution (~100ms vs ~600ms)
- Zero external dependencies
- Power users can explicitly request modes (#rca) when needed

---

### Migration Path

If adopting Option A (hybrid):

1. **Keep**: `_compute_similarity()` and FAP prototypes for `analysis_protocol_gate`
2. **Replace**: Other 6 enhancers with proposed config system
3. **Test**: Validate that failure-analysis prompts still trigger at 85% similarity
4. **Rollback**: Config can disable new system if issues arise

---

### Conclusion

The proposed refactor is **well-designed** and aligns with our timeout fix. The main trade-off is detection accuracy vs. simplicity.

**My recommendation**: **Option A (Hybrid)** ΓÇö Keep semantic similarity for FAP, adopt config-driven approach for other enhancers. This preserves the value of our current system while gaining the maintainability benefits of the proposed design.

**Verdict**: Γ£à **Recommended with modification** ΓÇö Don't remove embeddings entirely, use them selectively for high-value gates (FAP, vague directive detection)."

## Assistant

You basically wrote your own design review arguing for a hybrid, and I agree with that conclusion: keep embeddings only for FAP/analysis_protocol_gate, and move everything else to the lighter, config‑driven hook.

Here’s how I’d refine and operationalize what you wrote.

## 1. Validity of your concerns

- The detection-accuracy risk is real: embedding-based routing can catch semantically similar RCA prompts that regex will miss (e.g., colloquial descriptions of “prod is on fire” without RCA keywords).[1][2]
- Soft scaffolds *can* be ignored more often than hard rules, but meta‑prompting work shows well-designed scaffolds still improve behavior if they are concise and clearly framed as operating procedures rather than vague suggestions.[3][4]
- Topic gating causing silos is avoidable: you can allow cross-topic enhancer combos explicitly in config (e.g., diagnostic+implementation) instead of hard `elif` branching.

So Option A (hybrid) is reasonable, but I’d scope embeddings *tightly* to FAP routing only.

## 2. Concrete hybrid architecture

You can implement the hybrid like this:

- Keep your existing `analysis_protocol_gate` (with sentence-transformers) as a **separate hook** that only decides “inject FAP block or not.”  
- Replace the other six enhancers with the unified `cognitive_enhancers` hook from the refactor (regex + config + soft scaffolds, no embeddings).  
- Ensure the FAP hook runs *before* `cognitive_enhancers` via higher priority, but keep FAP idempotent and small enough that having both FAP and soft scaffolds is OK.

Example priority plan:

```text
analysis_protocol_gate (embeddings)  priority 11.8  # FAP only
cognitive_enhancers (config-driven)  priority 11.0
coach_note_reader                    priority 5.0
```

This directly matches hybrid routing patterns seen in embedding-based routers: a high-value semantic gate plus cheaper rule-based downstream routing.[5][2]

## 3. Tweaks I’d make to your Option A

To address your concerns without reintroducing heaviness:

- **FAP embeddings as optional “premium” path**  
  - Add `"fap_semantic_enabled": true` in config; if turned off, FAP falls back to regex-only and you’re effectively at Option B without code changes.  
  - Keep the similarity thresholds fairly high (e.g., 0.82–0.85) so you don’t pay embedding cost for ambiguous prompts.[2]

- **Allow multi-topic enhancer combos**  
  - In the unified hook, instead of strict `elif topic == "implementation"` etc., use a topic→enhancer mapping in config that allows a list per topic and per “combo” topic, like `"implementation_diagnostic": ["assumption_surfacing", "calibrated_confidence"]`.  
  - Detect combined intents (impl + diag) and map to that combo topic, so prompts like “refactor and debug” get both kinds of scaffolds.  

- **Strengthen “soft” language for critical paths**  
  - For FAP itself, keep it closer to “operating procedure” than “if appropriate,” since empirical work on scaffolding suggests clearer, stepwise rules get better adherence.[4][3]
  - For non-critical enhancers, the “if appropriate” phrasing is fine and keeps misfires cheap.

## 4. Recommended migration path in practice

What I’d actually ship, stepwise:

1. **Split hooks**  
   - Keep `analysis_protocol_gate` mostly as-is (embeddings + regex), with API call removed as you already did.  
   - Introduce `cognitive_enhancers.py` unified hook for the other cognitive injections.

2. **Config switches**  
   - Add `fap_semantic_enabled` and `fap_only_regex` toggles.  
   - Add topic/enhancer config exactly like the refactor, plus a `combo_topics` map for multi-intent prompts.

3. **Instrumentation (cheap logging)**  
   - Log: `{prompt_hash, is_fap, sim_score (if used), topic, enhancers_fired}` to a local file or debug console.  
   - After a week, inspect how often FAP is triggered via embeddings vs regex and how often it correlates with high-value incidents.[6][7]

4. **Tuning phase**  
   - If you see FAP embedding hits that regex would miss and they correlate with useful interventions, keep embeddings; otherwise, you have data to justify flipping `fap_semantic_enabled` off and fully migrating to the simple design.

## 5. Verdict on your review

Your written recommendation (“Option A (Hybrid) – keep semantic similarity for FAP, use config-driven approach for everything else”) is sound and aligns with how embedding-based routing is normally treated: as a specialized, high-value decision layer, not a general dependency.[5][2]

If you implement the split along those lines, you get:

- Timeouts and latency under control (no API, embeddings only on a small subset of prompts).  
- A simpler, testable core for most scaffolds.  
- The ability to dial FAP semantics on/off via config based on real-world data, not guesswork.
