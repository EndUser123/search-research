#!/usr/bin/env python3
"""model_tier.py — classify the model behind a turn as strong (Claude) or weak.

Weak models (MiniMax-*, glm-*, deepseek, kimi, … routed in via CCR / opencode-go
/ direct SDK) cannot satisfy the full epistemic/rubric contract this hook stack
injects. On those models the Stop quality gates (sycophancy, lazy-closure,
epistemic format) and the heavy UserPromptSubmit rubric injectors produce a
capitulation doom-loop instead of better answers. This module lets callers
suppress *quality* enforcement for weak models while leaving all *policy*
(safety) gates fully active.

Detection: read the last real assistant ``message.model`` from the transcript
JSONL named by ``data["transcript_path"]``. Claude Code writes ``message.model``
regardless of transport — originally verified under the now-retired Bifrost
gateway (``MiniMax-M3``, ``glm-5.1``, ``MiniMax-M2.7``, alongside genuine
``claude-opus-4-8`` / ``claude-sonnet-4-6``) and still holds under CCR: a
``claude-`` prefix test cleanly separates strong from weak. ``<synthetic>``
entries (compaction/injected turns carry no real model) are skipped.

Fail-open to STRONG: on any read/parse error, or when no model can be resolved,
treat the turn as strong so a real Claude turn never loses its gates. The only
cost of a false-strong is the status quo (gates stay on); a false-weak would
silently drop safety-adjacent quality enforcement, which we never want by
accident.

Tuning (settings.json ``env`` or process env):
  MODEL_TIER_GATING_ENABLED   default "true"  — master switch; "false" disables.
  STRONG_MODEL_PREFIXES       default "claude-" — comma-separated; case-insensitive.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Cap reverse-scan work on pathological transcripts. The active model lives in
# the most recent assistant entry, so the tail is all we need; this bounds cost
# on multi-MB transcripts without changing results in practice.
_MAX_TAIL_LINES = 4000

# Sentinel model string Claude Code writes for compaction / injected entries.
_SYNTHETIC = "<synthetic>"


def _strong_prefixes() -> tuple[str, ...]:
    raw = os.environ.get("STRONG_MODEL_PREFIXES", "claude-")
    return tuple(p.strip().lower() for p in raw.split(",") if p.strip())


def _gating_enabled() -> bool:
    return os.environ.get("MODEL_TIER_GATING_ENABLED", "true").strip().lower() != "false"


def active_model(data: dict) -> str | None:
    """Return the model string of the most recent real assistant turn, or None.

    Reads ``data["transcript_path"]`` and reverse-scans for the last assistant
    entry whose ``message.model`` is set and not ``<synthetic>``. Returns None on
    missing path, missing file, or any read/parse error (caller fails open).
    """
    transcript_path = data.get("transcript_path") if isinstance(data, dict) else None
    if not transcript_path:
        return None
    try:
        p = Path(transcript_path)
        if not p.exists():
            return None
        with p.open(encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return None

    for line in reversed(lines[-_MAX_TAIL_LINES:]):
        # Cheap pre-filter: skip the json.loads cost for lines without a model.
        if '"model"' not in line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        msg = obj.get("message")
        if not isinstance(msg, dict):
            continue
        model = msg.get("model")
        if model and model != _SYNTHETIC:
            return model
    return None


def model_tier(data: dict) -> str:
    """Classify the active model as ``"strong"`` or ``"weak"`` (fail-open strong)."""
    model = active_model(data)
    if not model:
        return "strong"
    lowered = model.lower()
    if any(lowered.startswith(pfx) for pfx in _strong_prefixes()):
        return "strong"
    return "weak"


def is_weak_model(data: dict) -> bool:
    """True iff the active model is a non-Claude (weak) model and gating is on.

    Quality gates and rubric injectors call this to decide whether to suppress
    themselves. Returns False (no suppression) when gating is disabled or the
    model resolves to / fails open to strong.
    """
    if not _gating_enabled():
        return False
    return model_tier(data) == "weak"
