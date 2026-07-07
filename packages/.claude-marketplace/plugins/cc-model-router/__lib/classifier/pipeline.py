"""Hierarchical classification pipeline.

Stage 0: Deterministic overrides (pin, git, background commands)
Stage A: Background vs active-work (semantic margin comparison)
Stage B: Reasoning vs coding (semantic margin comparison)
Stage C: Trivial-coding vs general-coding (word count + mechanical-edit heuristic)
Fallback: Conservative coding default if semantic layer unavailable

Decision strategy: MARGIN-BASED, not absolute thresholds.
TF-IDF cosine scores for same-class are ~[0.26, 0.38], cross-class ~[0.00, 0.08].
We pick the class with the highest score and use the margin between top-1 and top-2
as the confidence signal. No absolute threshold gates — they don't work with
cosine similarity scores that top out at ~0.38.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .scorer import SemanticScorer, ScorerResult
from .deterministic import check_overrides, is_mechanical_edit

# Default thresholds — tuned for TF-IDF cosine similarity score ranges.
# These are MARGINS (differences between top scores), not absolute score gates.
DEFAULTS = {
    "low_confidence_margin": 0.02,
    "trivial_coding_max_words": 15,
    "followup_context_boost": 0.15,
}


@dataclass
class ClassifyResult:
    """Full classification result with observability metadata."""
    task_type: str
    confidence: float
    margin: float
    source: str
    backend: str
    low_confidence: bool = False
    override: str | None = None
    stage_a: dict | None = None
    stage_b: dict | None = None
    stage_c: dict | None = None
    class_scores: dict = field(default_factory=dict)
    top_2: list[str] = field(default_factory=list)


def _get_threshold(config: dict, key: str) -> float:
    classifier_cfg = config.get("classifier", {})
    return classifier_cfg.get(key, DEFAULTS.get(key, 0.0))


def classify_pipeline(
    prompt: str,
    scorer: SemanticScorer | None,
    config: dict,
    context: dict | None = None,
) -> ClassifyResult:
    word_count = len(prompt.split())

    # ── Stage 0: Deterministic overrides ──────────────────────────────
    override = check_overrides(prompt)
    if override:
        return ClassifyResult(
            task_type=override, confidence=1.0, margin=1.0,
            source="override", backend="rules", override=override,
        )

    # ── Fallback if scorer unavailable ─────────────────────────────────
    if scorer is None or not getattr(scorer, "ready", True):
        return ClassifyResult(
            task_type="coding", confidence=0.0, margin=0.0,
            source="fallback", backend="none", low_confidence=True,
        )

    # ── Semantic scoring ───────────────────────────────────────────────
    try:
        result: ScorerResult = scorer.score(prompt, context)
    except Exception:
        return ClassifyResult(
            task_type="coding", confidence=0.0, margin=0.0,
            source="fallback", backend="none", low_confidence=True,
        )

    scores = result.class_scores
    sorted_classes = sorted(scores.keys(), key=lambda k: -scores[k])
    top_class = sorted_classes[0]
    runner_up = sorted_classes[1] if len(sorted_classes) > 1 else ""
    top_score = scores[top_class]
    runner_up_score = scores.get(runner_up, 0.0)
    margin = top_score - runner_up_score
    min_margin = _get_threshold(config, "low_confidence_margin")
    low_conf = margin < min_margin

    top_2_list = sorted_classes[:2]

    # ── Stage A: Background wins head-to-head ─────────────────────────
    if top_class == "background" and not low_conf:
        return ClassifyResult(
            task_type="background", confidence=top_score, margin=margin,
            source="semantic", backend=result.backend,
            stage_a={"class": "background", "confidence": top_score},
            class_scores=scores, top_2=top_2_list, low_confidence=low_conf,
        )

    active_score = max(scores.get("coding", 0.0), scores.get("reasoning", 0.0))
    stage_a_data = {"class": "active-work", "confidence": active_score}

    # ── Stage B: Reasoning vs coding — head-to-head ───────────────────
    coding_score = scores.get("coding", 0.0)
    reasoning_score = scores.get("reasoning", 0.0)
    margin_b = reasoning_score - coding_score

    if reasoning_score > coding_score and margin_b > min_margin:
        return ClassifyResult(
            task_type="reasoning", confidence=reasoning_score, margin=margin_b,
            source="semantic", backend=result.backend,
            stage_a=stage_a_data,
            stage_b={"class": "reasoning", "confidence": reasoning_score},
            class_scores=scores, top_2=top_2_list, low_confidence=low_conf,
        )

    # ── Stage C: Coding subtype ───────────────────────────────────────
    trivial_max = int(_get_threshold(config, "trivial_coding_max_words"))
    is_trivial = word_count <= trivial_max and is_mechanical_edit(prompt)
    stage_b_data = {"class": "coding", "confidence": coding_score}
    stage_c_data = {"class": "trivial-coding"} if is_trivial else None
    task_type = "local-coding" if is_trivial else "coding"

    return ClassifyResult(
        task_type=task_type, confidence=coding_score, margin=abs(margin_b),
        source="semantic", backend=result.backend,
        stage_a=stage_a_data, stage_b=stage_b_data, stage_c=stage_c_data,
        class_scores=scores, top_2=top_2_list, low_confidence=low_conf,
    )
