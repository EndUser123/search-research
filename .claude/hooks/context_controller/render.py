"""Pure rendering layer for the context controller.

Two public renderers, both pure functions:

1. **render_compact_packet(...)** — produces a compact markdown block
   suitable for compact-mode / session-start injection. Pulls from
   envelope (read-only), phase classification, and health assessment.
   Truncates long lists to bounded line counts; never emits more than
   MAX_PACKET_LINES total lines.

2. **render_phase_banner(...)** — produces a single-line phase banner
   suitable for a PreToolUse hint or hook injection.

No I/O, no globals, no LLM calls. Deterministic: identical input →
identical output. The v1 contract is keyword-only + render-only, so
the renderer never lies about what was found and never fabricates
envelope content.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from policy import HealthAssessment, PhaseClassification

MAX_PACKET_LINES = 30
MAX_LIST_ITEMS = 8
MAX_TEXT_CHARS = 240
_ELLIPSIS = "…"


def _truncate(text, limit=MAX_TEXT_CHARS):
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= limit:
        return text
    return text[: limit].rstrip() + _ELLIPSIS


def _bounded_list(value, limit=MAX_LIST_ITEMS):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    out = []
    for item in items:
        s = _truncate(str(item))
        if s:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def _envelope_section_lines(envelope):
    if not envelope:
        return []
    resume = envelope.get("resume_snapshot")
    if not isinstance(resume, Mapping):
        return []

    lines = []

    goal = _truncate(resume.get("goal", ""))
    if goal:
        lines.append(f"**Goal:** {goal}")

    current_task = _truncate(resume.get("current_task", ""))
    if current_task:
        lines.append(f"**Current task:** {current_task}")

    next_step = _truncate(resume.get("next_step", ""))
    if next_step:
        lines.append(f"**Next step:** {next_step}")

    active_files = _bounded_list(resume.get("active_files"))
    if active_files:
        lines.append("**Active files:**")
        for f in active_files:
            lines.append(f"  - `{f}`")

    recent_decisions = _bounded_list(resume.get("recent_decisions"))
    if recent_decisions:
        lines.append("**Recent decisions:**")
        for d in recent_decisions:
            lines.append(f"  - {d}")

    blockers = _bounded_list(resume.get("blockers"))
    if blockers:
        lines.append("**Blockers:**")
        for b in blockers:
            lines.append(f"  - {b}")

    open_questions = _bounded_list(resume.get("open_questions"))
    if open_questions:
        lines.append("**Open questions:**")
        for q in open_questions:
            lines.append(f"  - {q}")

    return lines


def _phase_line(classification):
    if classification is None:
        return "**Phase:** general"
    return f"**Phase:** {classification.phase} _(rule: {classification.rule_name})_"


def _hint_lines(assessment):
    if assessment is None or not assessment.hints:
        return []
    out = []
    if assessment.should_compact:
        out.append("**Compact recommended.**")
    if assessment.should_start_fresh:
        out.append("**Fresh session recommended for the new phase.**")
    for hint in assessment.hints:
        out.append(f"  - {hint}")
    return out


@dataclass(frozen=True)
class RenderedPacket:
    lines: tuple
    truncated: bool
    phase: Optional[str]


def render_compact_packet(
    *,
    envelope=None,
    classification=None,
    health_assessment=None,
    subagent_recommended=False,
    max_lines=MAX_PACKET_LINES,
):
    if not isinstance(max_lines, int) or max_lines < 1:
        max_lines = MAX_PACKET_LINES

    lines = []
    lines.append("## Context Controller — Resume Packet")
    lines.append("")
    lines.append(_phase_line(classification))

    for line in _hint_lines(health_assessment):
        lines.append(line)

    if subagent_recommended:
        lines.append("")
        lines.append(
            "_Subagent delegation advisory:_ prompt looks like a "
            "multi-step investigation (controller does not auto-dispatch)."
        )

    envelope_lines = _envelope_section_lines(envelope)
    if envelope_lines:
        lines.append("")
        lines.append("### From prior session")
        lines.extend(envelope_lines)

    truncated = len(lines) > max_lines
    if truncated:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip() + " _[…truncated]_"

    seen = set()
    deduped = []
    for ln in lines:
        if ln in seen:
            continue
        seen.add(ln)
        deduped.append(ln)

    return RenderedPacket(
        lines=tuple(deduped),
        truncated=truncated,
        phase=classification.phase if classification is not None else None,
    )


def render_phase_banner(classification):
    if classification is None:
        return "Phase: general"
    return f"Phase: {classification.phase} (rule: {classification.rule_name})"


__all__ = [
    "MAX_LIST_ITEMS",
    "MAX_PACKET_LINES",
    "MAX_TEXT_CHARS",
    "RenderedPacket",
    "render_compact_packet",
    "render_phase_banner",
]
