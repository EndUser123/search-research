"""Hierarchical classification pipeline — Phase 1 (deterministic).

Stage 0: Deterministic overrides (pin, git, background commands)
Phase 1: Deterministic task inference (code markers, reasoning indicators,
         tool-call patterns, context size). Replaces TF-IDF scorer.
Fallback: Conservative coding default.

Decision strategy: DETERMINISTIC RULES, not TF-IDF scoring.
Code + <64k tokens → local-coding (ornith)
Reasoning indicators → reasoning (glm/zai)
Tool-call patterns → coding (sonnet)
Default → sonnet
"""
from __future__ import annotations

import re
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

    # ── Phase 1: Deterministic task inference ──────────────────────────
    # Replaces TF-IDF scoring. Runs BEFORE the scorer-None fallback so
    # deterministic rules fire even when no scorer is loaded.
    # 1. Code markers + <64k tokens → local-coding (ornith)
    # 2. Reasoning indicators → reasoning (glm/zai)
    # 3. Tool-call patterns → coding (sonnet, not local)
    # 4. Default → sonnet (coding)
    # 4. Default → sonnet

    # Estimate token count (rough: word_count * 1.3)
    estimated_tokens = int(word_count * 1.3)

    # Code markers (function definitions, imports, class declarations)
    code_markers = re.compile(
        r'\b(def|class|function|const|let|var|fn|pub|import|from|include|export|async|await|return|yield)\b',
        re.IGNORECASE
    )

    # Reasoning indicators (design, architecture, tradeoffs, analysis)
    reasoning_indicators = re.compile(
        r'\b(design|architecture|tradeoff|tradeoffs|compare|evaluate|plan|strategy|analyze|assess|review|why|how should|should we|what if|consider|recommend)\b',
        re.IGNORECASE
    )

    # Tool-call patterns (function calls, API usage, SDK integration)
    tool_call_patterns = re.compile(
        r'\b(invoke|call|execute|run|fetch|request|send|post|get|put|delete|api|sdk|library|package|module|method)\b',
        re.IGNORECASE
    )

    # Check patterns
    has_code = bool(code_markers.search(prompt))
    has_reasoning = bool(reasoning_indicators.search(prompt))
    has_tool_calls = bool(tool_call_patterns.search(prompt))

    # Decision logic
    if has_code and estimated_tokens < 64000:
        # Code + under 64k tokens → local coding (ornith)
        return ClassifyResult(
            task_type="local-coding", confidence=1.0, margin=1.0,
            source="deterministic", backend="rules",
            stage_a={"class": "local-coding", "confidence": 1.0},
        )
    elif has_reasoning:
        # Reasoning indicators → reasoning (glm/zai)
        return ClassifyResult(
            task_type="reasoning", confidence=1.0, margin=1.0,
            source="deterministic", backend="rules",
            stage_b={"class": "reasoning", "confidence": 1.0},
        )
    elif has_tool_calls and not has_reasoning:
        # Tool-call patterns without reasoning → coding (sonnet)
        return ClassifyResult(
            task_type="coding", confidence=1.0, margin=1.0,
            source="deterministic", backend="rules",
            stage_a={"class": "coding", "confidence": 1.0},
        )
    else:
        # Default → sonnet (coding)
        return ClassifyResult(
            task_type="coding", confidence=1.0, margin=1.0,
            source="deterministic", backend="rules",
            stage_a={"class": "coding", "confidence": 1.0},
        )

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
