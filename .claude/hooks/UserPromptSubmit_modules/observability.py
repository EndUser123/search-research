"""Observability Module - Track selections and metrics for cognitive/reasoning systems.

This module tracks:
- Selection rates per mode/framework
- Confidence distribution
- Token overhead

All metrics are logged to .claude/data/reasoning_metrics.jsonl in JSONL format.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from UserPromptSubmit_modules.cognitive_enhancers import Enhancer

# Metrics data directory
METRICS_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "data"
METRICS_FILE = METRICS_DIR / "reasoning_metrics.jsonl"


@dataclass
class CognitiveSelectionEvent:
    """Event data for cognitive framework selection."""

    timestamp: str
    enhancers: list[str]  # Enhancer names
    enhancer_count: int
    intent: dict[str, bool]  # Intent flags
    tokens: int
    rationale: str


@dataclass
class ReasoningModeEvent:
    """Event data for reasoning mode selection."""

    timestamp: str
    mode: str
    confidence: int
    fallback: bool
    tokens: int


@dataclass
class TagEmissionEvent:
    """Event data for tag emission with validation."""

    timestamp: str
    tag_type: str
    tag_category: str  # "framework", "mode", "deprecated", "invalid"
    is_valid: bool
    has_warning: bool
    warning_message: str | None
    source: str  # "cognitive_enhancers", "reasoning_mode_selector", etc.


def log_cognitive_selection(
    enhancers: list[Enhancer],
    intent: dict[str, bool],
    tokens: int,
    rationale: str,
) -> None:
    """Log a cognitive framework selection event.

    Args:
        enhancers: Selected cognitive enhancers
        intent: Detected intent flags
        tokens: Token count for injection
        rationale: Rationale for selection
    """
    try:
        # Ensure metrics directory exists
        METRICS_DIR.mkdir(parents=True, exist_ok=True)

        # Create event
        event = CognitiveSelectionEvent(
            timestamp=datetime.now().isoformat(),
            enhancers=[e.name for e in enhancers],
            enhancer_count=len(enhancers),
            intent=intent,
            tokens=tokens,
            rationale=rationale,
        )

        # Append to metrics file (JSONL format - one JSON per line)
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    except Exception as e:
        # Fail-safe - logging errors never break hooks
        print(
            f"[OBSERVABILITY] Failed to log cognitive selection: {e}", file=__import__("sys").stdout
        )


def log_reasoning_mode(
    mode: str,
    confidence: int,
    fallback: bool,
    tokens: int,
) -> None:
    """Log a reasoning mode selection event.

    Args:
        mode: Selected reasoning mode
        confidence: Confidence score (0-4)
        fallback: Whether this was a fallback selection
        tokens: Token count for injection
    """
    try:
        # Ensure metrics directory exists
        METRICS_DIR.mkdir(parents=True, exist_ok=True)

        # Create event
        event = ReasoningModeEvent(
            timestamp=datetime.now().isoformat(),
            mode=mode,
            confidence=confidence,
            fallback=fallback,
            tokens=tokens,
        )

        # Append to metrics file (JSONL format)
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    except Exception as e:
        # Fail-safe - logging errors never break hooks
        print(f"[OBSERVABILITY] Failed to log reasoning mode: {e}", file=__import__("sys").stdout)


def log_tag_emission(
    tag_type: str,
    tag_category: str,
    is_valid: bool,
    has_warning: bool,
    warning_message: str | None = None,
    source: str = "unknown",
) -> None:
    """Log a tag emission event for telemetry.

    Args:
        tag_type: Tag identifier (e.g., "ASUM", "COG", "SEQ")
        tag_category: Category - "framework", "mode", "deprecated", "invalid"
        is_valid: Whether tag passed validation
        has_warning: Whether validation produced a warning
        warning_message: Optional warning message from validation
        source: Source module emitting the tag
    """
    try:
        # Ensure metrics directory exists
        METRICS_DIR.mkdir(parents=True, exist_ok=True)

        # Create event
        event = TagEmissionEvent(
            timestamp=datetime.now().isoformat(),
            tag_type=tag_type,
            tag_category=tag_category,
            is_valid=is_valid,
            has_warning=has_warning,
            warning_message=warning_message,
            source=source,
        )

        # Append to metrics file (JSONL format)
        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    except Exception as e:
        # Fail-safe - logging errors never break hooks
        print(f"[OBSERVABILITY] Failed to log tag emission: {e}", file=__import__("sys").stdout)


def get_metrics_summary() -> dict:
    """Get summary statistics from metrics log.

    Returns:
        Dictionary with selection counts, confidence distribution, etc.
    """
    try:
        if not METRICS_FILE.exists():
            return {"error": "Metrics file not found"}

        events = []
        with open(METRICS_FILE, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        # Note: Empty events list is valid - file exists but no metrics logged yet
        # Continue to calculate summary with 0 counts

        # Separate cognitive, reasoning, and tag events
        cognitive_events = []
        reasoning_events = []
        tag_events = []

        for event in events:
            if "tag_type" in event and "tag_category" in event:
                tag_events.append(event)
            elif "mode" in event and "confidence" in event:
                reasoning_events.append(event)
            else:
                cognitive_events.append(event)

        # Calculate statistics
        summary = {
            "total_events": len(events),
            "cognitive_events": len(cognitive_events),
            "reasoning_events": len(reasoning_events),
            "tag_events": len(tag_events),
        }

        # Cognitive statistics
        if cognitive_events:
            enhancer_counts = {}
            for e in cognitive_events:
                for enhancer in e.get("enhancers", []):
                    # Use enhancer.name as key (Enhancer objects are unhashable due to list[str] topics field)
                    enhancer_name = enhancer.name if isinstance(enhancer, object) and hasattr(enhancer, 'name') else enhancer
                    enhancer_counts[enhancer_name] = enhancer_counts.get(enhancer_name, 0) + 1

            total_tokens = sum(e.get("tokens", 0) for e in cognitive_events)
            avg_tokens = total_tokens / len(cognitive_events) if cognitive_events else 0

            summary["cognitive"] = {
                "most_common_enhancers": sorted(
                    enhancer_counts.items(), key=lambda x: x[1], reverse=True
                )[:5],
                "total_tokens": total_tokens,
                "avg_tokens": avg_tokens,
            }

        # Reasoning statistics
        if reasoning_events:
            mode_counts = {}
            for e in reasoning_events:
                mode = e.get("mode", "unknown")
                mode_counts[mode] = mode_counts.get(mode, 0) + 1

            confidence_dist = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
            for e in reasoning_events:
                conf = str(e.get("confidence", 0))
                confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

            fallback_count = sum(1 for e in reasoning_events if e.get("fallback", False))

            summary["reasoning"] = {
                "mode_distribution": mode_counts,
                "confidence_distribution": confidence_dist,
                "fallback_rate": fallback_count / len(reasoning_events) if reasoning_events else 0,
            }

        # Tag statistics
        if tag_events:
            # Tag type distribution
            tag_type_counts = {}
            category_counts = {}
            deprecation_warnings = 0
            validation_failures = 0

            for e in tag_events:
                tag_type = e.get("tag_type", "unknown")
                tag_type_counts[tag_type] = tag_type_counts.get(tag_type, 0) + 1

                category = e.get("tag_category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

                if e.get("has_warning", False):
                    deprecation_warnings += 1

                if not e.get("is_valid", True):
                    validation_failures += 1

            summary["tags"] = {
                "tag_type_distribution": tag_type_counts,
                "category_distribution": category_counts,
                "deprecation_warning_rate": deprecation_warnings / len(tag_events)
                if tag_events
                else 0,
                "validation_failure_rate": validation_failures / len(tag_events)
                if tag_events
                else 0,
                "most_common_tags": sorted(
                    tag_type_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
            }

        return summary

    except Exception as e:
        return {"error": f"Failed to read metrics: {e}"}
