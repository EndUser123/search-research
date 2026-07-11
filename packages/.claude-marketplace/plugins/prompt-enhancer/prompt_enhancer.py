import json
import os
from pathlib import Path

from schemas import EnhancementResult
from detect import triage


# Confidence floor below which the hook should not inject additionalContext.
# Ambiguous prompts return 0.3 and thus inject NOTHING: the consuming model
# holds the full conversation and resolves referents itself. The deleted
# referent-inference path (resolve_referent/session context, removed 2026-07-11)
# injected wrong anchors — first-file-ref in a pasted prior prompt is not the
# discourse subject.
DEFAULT_INJECT_THRESHOLD: float = float(7) / float(10)


def enhance(prompt: str, cwd: str) -> EnhancementResult:
    """Triage and enhance a user prompt.

    Args:
        prompt: The raw user prompt.
        cwd: Current working directory (reserved for future fs-based disambiguation).
    """
    result = triage(prompt)

    if result["classification"] == "bypass":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=[],
            analysis=f"bypass: {result['reason']}",
            safety_flags=[],
        )

    if result["classification"] == "clear":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=[],
            analysis=f"clear: {result['reason']}",
            safety_flags=[],
        )

    if result["classification"] == "prohibited":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=[],
            analysis=f"prohibited: {result['reason']}",
            safety_flags=["prohibited: destructive without scope"],
        )

    if result["classification"] == "confirm":
        return EnhancementResult(
            clarified_intent=prompt,
            missing_details=["confirm target scope before executing"],
            analysis=f"confirm: {result['reason']}",
            safety_flags=["destructive-but-ambiguous"],
        )

    # Ambiguous path — return the generic hint at low confidence (below the
    # inject threshold) so the hook injects nothing. Referent resolution was
    # deliberately removed: the model has the conversation and resolves "it"
    # natively; a deterministic guess only ever adds a wrong anchor.
    return EnhancementResult(
        clarified_intent=prompt,
        missing_details=["clarify: missing referent or underspecified"],
        analysis=f"ambiguous: {result['reason']}",
        safety_flags=[],
        confidence=float(3) / float(10),
    )


def build_additional_context(result: EnhancementResult) -> str:
    lines = ["Prompt Clarification", f"• Intent: {result.clarified_intent}"]
    if result.missing_details:
        lines.append(f"• Clarified: {', '.join(result.missing_details)}")
    if result.safety_flags:
        lines.append(f"• Flags: {', '.join(result.safety_flags)}")
    return "\n".join(lines)
