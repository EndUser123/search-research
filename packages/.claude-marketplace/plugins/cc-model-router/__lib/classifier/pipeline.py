"""Hierarchical classification pipeline — Phase 1 (deterministic).

Stage 0: Deterministic overrides (pin, git, background commands)
Phase 1: Deterministic task inference (code markers, reasoning indicators,
         tool-call patterns, context size). Replaces TF-IDF scorer.
Fallback: Conservative coding default.

Decision strategy: DETERMINISTIC RULES, not TF-IDF scoring.
Code + <64k tokens → local-coding (ornith)
Reasoning indicators → reasoning (glm/zai)
Tool-call patterns → coding (sonnet)
Structured-output (json/schema) → coding (sonnet)  [local 9B fails schema, #991]
Default free-form → local-coding (ornith, free, high-quality per #991)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .scorer import SemanticScorer
from .deterministic import check_overrides


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

    # Structured-output signals — schema/JSON-constrained requests. The local 9B
    # returns empty content under json_schema (task #991), so these must escalate
    # to coding (sonnet) even when the prompt is otherwise free-form.
    structured_output_indicators = re.compile(
        r'\b(?:json|schema|response_format|structured\s+output|valid\s+json|as\s+json|in\s+json|json\s+output)\b',
        re.IGNORECASE
    )

    # Check patterns
    has_code = bool(code_markers.search(prompt))
    has_reasoning = bool(reasoning_indicators.search(prompt))
    has_tool_calls = bool(tool_call_patterns.search(prompt))
    has_structured = bool(structured_output_indicators.search(prompt))

    # Decision logic. Structured-output guard: the local 9B returns empty content
    # under json_schema (task #991), so has_structured excludes local-coding on
    # every path. Reasoning (glm-5.2) and coding (sonnet) both handle schema fine.
    if has_code and estimated_tokens < 64000 and not has_structured:
        # Code + under 64k tokens + free-form → local coding (ornith)
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
    elif has_structured:
        # Schema/JSON-constrained output → coding (sonnet); local 9B fails
        # structured output (task #991).
        return ClassifyResult(
            task_type="coding", confidence=1.0, margin=1.0,
            source="deterministic", backend="rules",
            stage_a={"class": "coding", "structured": True},
        )
    else:
        # Default: free-form coding → local (ornith, free). Modern 9B
        # (Qwen3.5-arch) produces high-quality free-form code (task #991).
        return ClassifyResult(
            task_type="local-coding", confidence=1.0, margin=1.0,
            source="deterministic", backend="rules",
            stage_a={"class": "local-coding", "confidence": 1.0},
        )
