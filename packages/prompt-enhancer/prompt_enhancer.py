import json
import os
from pathlib import Path

from schemas import EnhancementResult
from detect import triage
from context import (
    SessionContext,
    read_session_context,
    resolve_referent,
)


# Confidence floor below which the hook should not inject additionalContext.
# Tuned to allow Case-1 (continuation + last_subject, 0.75) and Case-2 (pronoun + last_subject, 0.7)
# to surface, while suppressing weaker inferences (0.5 = prior-prompt-text fallback).
DEFAULT_INJECT_THRESHOLD: float = float(7) / float(10)


def enhance(prompt: str, cwd: str, ctx: SessionContext | None = None) -> EnhancementResult:
    """Triage and enhance a user prompt.

    Args:
        prompt: The raw user prompt.
        cwd: Current working directory (reserved for future fs-based disambiguation).
        ctx: Optional pre-loaded session context. If None, this function reads
             the persisted context — but callers (hooks) should pass it in to
             avoid re-reading the file across enhance() and context-write logic.
    """
    result = triage(prompt)

    if result["classification"] == "bypass":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=[],
            analysis=f"bypass: {result['reason']}",
            safety_flags=[],
            estimated_tokens=0,
        )

    if result["classification"] == "clear":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=[],
            analysis=f"clear: {result['reason']}",
            safety_flags=[],
            estimated_tokens=_estimate_tokens(prompt),
        )

    if result["classification"] == "prohibited":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=[],
            analysis=f"prohibited: {result['reason']}",
            safety_flags=["prohibited: destructive without scope"],
            estimated_tokens=0,
        )

    if result["classification"] == "confirm":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=["confirm target scope before executing"],
            analysis=f"confirm: {result['reason']}",
            safety_flags=["destructive-but-ambiguous"],
            estimated_tokens=_estimate_tokens(prompt),
        )

    # Ambiguous path — attempt referent resolution from session context.
    if ctx is None:
        ctx = read_session_context()
    resolution = resolve_referent(prompt, ctx)
    if resolution is not None:
        clarified = f"{prompt}  ← likely means: {resolution.inferred_subject}"
        return EnhancementResult(
            clarified_intent=clarified,
            missing_details=[
                f"inferred subject: {resolution.inferred_subject}",
                "correct me if this referent is wrong",
            ],
            analysis=f"ambiguous→resolved: {resolution.source}",
            safety_flags=[],
            estimated_tokens=_estimate_tokens(clarified),
            inferred_subject=resolution.inferred_subject,
            confidence=resolution.confidence,
        )

    # No inference possible — fall back to the original generic hint, but at
    # low confidence so the hook can suppress injection if it likes.
    return EnhancementResult(
        clarified_intent=prompt,
        missing_details=["clarify: missing referent or underspecified"],
        analysis=f"ambiguous: {result['reason']}",
        safety_flags=[],
        estimated_tokens=_estimate_tokens(prompt),
        confidence=float(3) / float(10),
    )


def _estimate_tokens(text: str) -> int:
    return len(text.split()) * 4 // 3


def build_additional_context(result: EnhancementResult) -> str:
    # If we successfully inferred a subject, lead with that — it's the most
    # actionable signal for the model. Otherwise, fall back to the generic
    # "Prompt Clarification" header.
    if result.inferred_subject:
        lines = [
            "Prompt Context (inferred from prior turn)",
            f"• Likely subject: {result.inferred_subject}",
            f"• Original prompt: {result.clarified_intent}",
        ]
    else:
        lines = ["Prompt Clarification", f"• Intent: {result.clarified_intent}"]
    if result.missing_details:
        lines.append(f"• Clarified: {', '.join(result.missing_details)}")
    if result.safety_flags:
        lines.append(f"• Flags: {', '.join(result.safety_flags)}")
    if result.estimated_tokens:
        lines.append(f"• Tokens: ~{result.estimated_tokens} (for context budget tracking)")
    return "\n".join(lines)
