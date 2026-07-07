"""Hierarchical classification pipeline.

Stage 0: Deterministic overrides (pin, git, background commands)
Stage A: Background vs active-work (semantic threshold)
Stage B: Reasoning vs coding (semantic threshold + margin)
Stage C: Trivial-coding vs general-coding (word count + mechanical-edit heuristic)
Fallback: Conservative coding default if semantic layer unavailable
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .scorer import SemanticScorer, ScorerResult
from .deterministic import check_overrides, is_mechanical_edit

# Default thresholds (overridable via claude-model-router.json classifier section)
DEFAULTS = {
    "semantic_threshold": 0.55,
    "low_confidence_margin": 0.10,
    "background_threshold": 0.50,
    "reasoning_threshold": 0.60,
    "trivial_coding_max_words": 15,
    "followup_context_boost": 0.15,
}


@dataclass
class ClassifyResult:
    """Full classification result with observability metadata."""
    task_type: str                      # background | reasoning | coding | local-coding
    confidence: float                   # 0.0–1.0 (1.0 for deterministic overrides)
    margin: float                       # top - runner_up score
    source: str                         # override | semantic | fallback
    backend: str                        # rules | tfidf | none
    low_confidence: bool = False
    override: str | None = None         # which override fired (or None)
    stage_a: dict | None = None         # {"class": ..., "confidence": ...}
    stage_b: dict | None = None
    stage_c: dict | None = None
    class_scores: dict = field(default_factory=dict)
    top_2: list[str] = field(default_factory=list)


def _get_threshold(config: dict, key: str) -> float:
    """Read threshold from config.classifier section, falling back to DEFAULTS."""
    classifier_cfg = config.get("classifier", {})
    return classifier_cfg.get(key, DEFAULTS.get(key, 0.0))


def classify_pipeline(
    prompt: str,
    scorer: SemanticScorer | None,
    config: dict,
    context: dict | None = None,
) -> ClassifyResult:
    """Run the full hierarchical classification pipeline.

    Args:
        prompt: The user's prompt text.
        scorer: SemanticScorer instance (or None if unavailable).
        config: Merged config dict (from claude-model-router.json walk-up).
        context: Optional dict with prev_task_type, followup_boost, etc.

    Returns:
        ClassifyResult with task_type, confidence, and full observability metadata.
    """
    word_count = len(prompt.split())

    # ── Stage 0: Deterministic overrides ──────────────────────────────
    override = check_overrides(prompt)
    if override:
        return ClassifyResult(
            task_type=override,
            confidence=1.0,
            margin=1.0,
            source="override",
            backend="rules",
            override=override,
        )

    # ── Fallback if scorer unavailable ─────────────────────────────────
    if scorer is None or not getattr(scorer, "ready", True):
        return ClassifyResult(
            task_type="coding",
            confidence=0.0,
            margin=0.0,
            source="fallback",
            backend="none",
            low_confidence=True,
        )

    # ── Semantic scoring ───────────────────────────────────────────────
    try:
        result: ScorerResult = scorer.score(prompt, context)
    except Exception:
        return ClassifyResult(
            task_type="coding",
            confidence=0.0,
            margin=0.0,
            source="fallback",
            backend="none",
            low_confidence=True,
        )

    scores = result.class_scores
    bg_score = scores.get("background", 0.0)
    coding_score = scores.get("coding", 0.0)
    reasoning_score = scores.get("reasoning", 0.0)

    # ── Stage A: Background vs active-work ─────────────────────────────
    bg_threshold = _get_threshold(config, "background_threshold")
    active_score = max(coding_score, reasoning_score)
    if bg_score > active_score and bg_score > bg_threshold:
        return ClassifyResult(
            task_type="background",
            confidence=bg_score,
            margin=bg_score - active_score,
            source="semantic",
            backend=result.backend,
            stage_a={"class": "background", "confidence": bg_score},
            class_scores=scores,
            top_2=sorted(scores.keys(), key=lambda k: -scores[k])[:2],
            low_confidence=(bg_score - active_score) < _get_threshold(config, "low_confidence_margin"),
        )

    # ── Stage B: Reasoning vs coding ───────────────────────────────────
    reasoning_threshold = _get_threshold(config, "reasoning_threshold")
    min_margin = _get_threshold(config, "low_confidence_margin")
    margin_b = reasoning_score - coding_score

    stage_a_data = {"class": "active-work", "confidence": active_score}

    if reasoning_score > coding_score and reasoning_score > reasoning_threshold and margin_b > min_margin:
        return ClassifyResult(
            task_type="reasoning",
            confidence=reasoning_score,
            margin=margin_b,
            source="semantic",
            backend=result.backend,
            stage_a=stage_a_data,
            stage_b={"class": "reasoning", "confidence": reasoning_score},
            class_scores=scores,
            top_2=sorted(scores.keys(), key=lambda k: -scores[k])[:2],
            low_confidence=margin_b < min_margin,
        )

    # ── Stage C: Coding subtype (trivial vs general) ───────────────────
    trivial_max = int(_get_threshold(config, "trivial_coding_max_words"))
    is_trivial = word_count <= trivial_max and is_mechanical_edit(prompt)

    stage_b_data = {"class": "coding", "confidence": coding_score}
    stage_c_data = {"class": "trivial-coding" if is_trivial else "general-coding"} if is_trivial else None

    task_type = "local-coding" if is_trivial else "coding"

    return ClassifyResult(
        task_type=task_type,
        confidence=coding_score,
        margin=abs(margin_b),
        source="semantic",
        backend=result.backend,
        stage_a=stage_a_data,
        stage_b=stage_b_data,
        stage_c=stage_c_data,
        class_scores=scores,
        top_2=sorted(scores.keys(), key=lambda k: -scores[k])[:2],
        low_confidence=abs(margin_b) < min_margin,
    )
