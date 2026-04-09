"""
Stop hook for sequential thinking iteration management.

Reads response output, saves to state file, increments iteration counter,
and manages loop completion or continuation.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from __lib.sequential_state import (
    add_intermediate_answer,
    set_final_answer,
    should_continue,
    update_state,
)

# State directory
STATE_DIR = Path("P:/").resolve() / ".claude" / "state" / "sequential-thinking"

# Import tag emission
sys.path.insert(0, str(Path(__file__).parent))
from UserPromptSubmit_modules.tag_emission import emit_tag  # noqa: E402       

_MODE_INSTRUCTIONS = {
    "critique": (
        "Critically analyze your previous answer and identify:\n"
        "1. Logical gaps or errors in the reasoning\n"
        "2. Unstated assumptions\n"
        "3. Alternative perspectives not considered\n"
        "4. Weakest parts of the argument\n"
        "Be specific and constructive."
    ),
    "improvement": (
        "Based on the critique, provide an improved final answer that:\n"      
        "1. Fixes the logical errors identified\n"
        "2. Strengthens weak areas with better support\n"
        "3. Acknowledges complexity where appropriate\n"
        "This is your final answer — make it comprehensive and well-reasoned."
    ),
}

# Investigation mode instructions (Layer 2)
_INVESTIGATION_PHASES = {
    "hypotheses": (
        "Generate 3+ alternative hypotheses BEFORE testing:\n"
        "1. \u23F3 H1: [most likely explanation] | Confirm with: [test] | Falsify with: [test]\n"
        "2. \u23F3 H2: [alternative cause] | Confirm with: [test] | Falsify with: [test]\n"
        "3. \u23F3 H3: [less likely but possible] | Confirm with: [test] | Falsify with: [test]\n\n"
        "**STATUS KEY**: \u23F3 Untested | \u2713 Confirmed | \u2717 Falsified"
    ),
    "testing": (
        "Test each hypothesis systematically using tools (Read, Grep, Bash).\n"
        "Update the status (\u2713/\u2717) for each hypothesis based on actual tool evidence."
    ),
    "conclusion": (
        "Declare root cause only after \u22652 hypotheses are tested (\u2713 or \u2717).\n"
        "State remaining uncertainty with [UNVERIFIED] if present."
    ),
}

# CHANGE-004: Hypothesis mode instructions
_HYPOTHESIS_MODE_MESSAGES = {
    "multi_hypothesis": """Generate 2-3 competing explanations for the problem.

For each hypothesis:
1. State the explanation clearly
2. Identify what evidence would support it
3. Identify what evidence would refute it

Maintain all hypotheses as equally plausible until evidence discriminates between them.

Format your hypotheses as:
H1: [explanation]
H2: [alternative explanation]
H3: [another alternative]""",
    "hypothesis_critique": """Evaluate each competing hypothesis against the evidence.

For each hypothesis:
1. Compare predictions to actual observations
2. Identify inconsistencies or contradictions
3. Rank hypotheses by explanatory power

Do NOT eliminate a hypothesis until you have strong evidence against it.""",
    "hypothesis_resolution": """Synthesize the best explanation from competing hypotheses.

1. Select the hypothesis best supported by evidence
2. Explain why other hypotheses were weaker
3. Identify what additional evidence would strengthen confidence

This is your final answer - make it comprehensive and well-reasoned.""",
}

def _extract_hypotheses_from_response(response_output: str) -> list:
    """Extract hypotheses from LLM response output.

    Args:
        response_output: The LLM response text

    Returns:
        List of hypothesis objects: [{"id": "H1", "claim": "...", "status": "active"}, ...]
    """
    extracted = []

    # Primary patterns: H1:, H2:, H3: prefixes (case-insensitive)
    for match in re.finditer(r'^\s*(H\d+)[:\s]+(.+?)$', response_output, re.MULTILINE | re.IGNORECASE):
        hypothesis_id = match.group(1).strip()
        claim = match.group(2).strip()
        if claim:
            extracted.append({"id": hypothesis_id, "claim": claim, "status": "active"})

    # Natural language variants
    variants = [
        (r'First hypothesis:\s*(.+?)(?:\n|$)', "H1"),
        (r'Second hypothesis:\s*(.+?)(?:\n|$)', "H2"),
        (r'Third hypothesis:\s*(.+?)(?:\n|$)', "H3"),
        (r'Hypothesis\s+1:\s*(.+?)(?:\n|$)', "H1"),
        (r'Hypothesis\s+2:\s*(.+?)(?:\n|$)', "H2"),
        (r'Hypothesis\s+3:\s*(.+?)(?:\n|$)', "H3"),
    ]

    for pattern, hypo_id in variants:
        match = re.search(pattern, response_output, re.IGNORECASE)
        if match:
            claim = match.group(1).strip()
            if claim and not any(h["id"] == hypo_id for h in extracted):
                extracted.append({"id": hypo_id, "claim": claim, "status": "active"})

    # Numbered list fallback
    numbered = list(re.finditer(r'^\s*(\d+)[.:]\s*(.+?)$', response_output, re.MULTILINE))
    if len(extracted) < 2 and len(numbered) >= 2:
        for i, match in enumerate(numbered[:3], start=1):
            claim = match.group(2).strip()
            if claim:
                extracted.append({"id": f"H{i}", "claim": claim, "status": "active"})

    return extracted[:3]  # Max 3 hypotheses


def _format_investigation_feedback(
    phase: str,
    hypothesis_details_or_text: list | str | None = None,
) -> str:
    """Format structured feedback for investigation mode.

    Supports two calling conventions:
    - Structured list (legacy): _format_investigation_feedback("testing", [{claim, status, ...}])
    - Raw text (new): _format_investigation_feedback("testing", response_output_string)

    Args:
        phase: Investigation phase (hypotheses, testing, conclusion)
        hypothesis_details_or_text: Either a list of hypothesis dicts, raw response text, or None

    Returns:
        Formatted feedback string
    """
    lines = [f"[SEQ] Investigation Mode \u2014 Phase: {phase.upper()}", ""]

    # --- Path A: structured hypothesis list (legacy callers) ---
    if isinstance(hypothesis_details_or_text, list) and hypothesis_details_or_text:
        hypothesis_details = hypothesis_details_or_text
        tested_count = sum(
            1 for h in hypothesis_details if h.get("status") in ("CONFIRMED", "FALSIFIED", "INCONCLUSIVE")
        )
        total = len(hypothesis_details)
        lines.append(f"Hypothesis Testing Progress: {tested_count}/{total} tested")
        lines.append("")

        for h in hypothesis_details:
            status = h.get("status", "UNTESTED").upper()
            claim = h.get("claim", h.get("name", "Unknown"))
            icon = "\u2713" if status == "CONFIRMED" else (
                "\u2717" if status == "FALSIFIED"
                else "?" if status == "INCONCLUSIVE"
                else "\u23f3"
            )
            lines.append(f"   {icon} {claim} \u2192 {status}")
            if status == "UNTESTED" and h.get("test_suggestion"):
                lines.append(f"      Suggested test: {h['test_suggestion']}")
        lines.append("")
        return "\n".join(lines)

    # --- Path B: raw response text (StopHook caller) ---
    if isinstance(hypothesis_details_or_text, str) and hypothesis_details_or_text:
        response_text = hypothesis_details_or_text
        hypotheses = re.findall(
            r"([\u23F3\u2713\u2717])\s*(H\d+:?\s*.*?)(?=\n|$)", response_text
        )
        if hypotheses:
            tested_count = sum(1 for icon, _ in hypotheses if icon in ("\u2713", "\u2717"))
            lines.append(f"Hypothesis Testing Progress: {tested_count}/{len(hypotheses)} tested")
            lines.append("")
            for icon, name in hypotheses:
                lines.append(f"   {icon} {name}")
            lines.append("")

    return "\n".join(lines)

def stop(data: dict) -> dict:
    terminal_id = data.get("terminal_id", "")
    response_output = data.get("response_output", "") or data.get("assistant_response", "") or ""

    active_session = _find_active_session(terminal_id)
    if not active_session:
        return {"allow": True}

    session_id = uuid.UUID(active_session["session_id"])
    current_iteration = active_session.get("current_iteration", 0)
    is_investigation = active_session.get("is_investigation", False)

    # CHANGE-004: Check hypothesis mode
    is_hypothesis_mode = active_session.get("hypothesis_mode", False)

    if response_output:
        add_intermediate_answer(session_id, response_output, terminal_id)

        # CHANGE-004: Extract and store hypotheses for hypothesis mode
        if is_hypothesis_mode and current_iteration == 0:
            extracted = _extract_hypotheses_from_response(response_output)
            if len(extracted) < 2:
                # Retry prompt injection
                return {
                    "allow": False,
                    "reason": "Please provide at least 2 distinct hypotheses (marked as H1:, H2:, or numbered list)."
                }
            update_state(session_id, {"hypotheses": extracted}, terminal_id)

    if should_continue(session_id, terminal_id=terminal_id):
        next_iteration = current_iteration + 1
        update_state(session_id, {"current_iteration": next_iteration}, terminal_id)

        # CHANGE-004: Hypothesis mode handling
        if is_hypothesis_mode:
            phase_order = ["multi_hypothesis", "hypothesis_critique", "hypothesis_resolution"]
            phase_key = phase_order[min(next_iteration, len(phase_order) - 1)]
            phase_instructions = _HYPOTHESIS_MODE_MESSAGES[phase_key]

            return {
                "allow": False,
                "reason": (
                    f"{emit_tag('SEQ')}\n"
                    f"<sequential_thinking_continuation>\n"
                    f"Iteration {next_iteration} of 2 \u2014 HYPOTHESIS MODE ({phase_key.upper()})\n"
                    f"</sequential_thinking_continuation>\n\n"
                    f"{phase_instructions}"
                ),
            }

        if is_investigation:
            phase_order = ["hypotheses", "testing", "conclusion"]
            phase_key = phase_order[min(next_iteration, len(phase_order) - 1)]
            phase_instructions = _INVESTIGATION_PHASES[phase_key]
            feedback = _format_investigation_feedback(phase_key, response_output)

            return {
                "allow": False,
                "reason": (
                    f"{emit_tag('SEQ')}\n"
                    f"<sequential_thinking_continuation>\n"
                    f"Iteration {next_iteration} of 2 \u2014 INVESTIGATION MODE ({phase_key.upper()})\n"
                    f"</sequential_thinking_continuation>\n\n"
                    f"{feedback}\n\n"
                    f"{phase_instructions}"
                ),
            }
        else:
            mode_key = "critique" if next_iteration == 1 else "improvement"
            return {
                "allow": False,
                "reason": (
                    f"{emit_tag('SEQ')}\n"
                    f"<sequential_thinking_continuation>\n"
                    f"Iteration {next_iteration} of 2 \u2014 {mode_key.upper()} MODE\n"
                    f"</sequential_thinking_continuation>\n\n"
                    f"{_MODE_INSTRUCTIONS[mode_key]}"
                ),
            }
    else:
        # Extract verdict (winning hypothesis ID) from hypothesis_resolution response
        if is_hypothesis_mode:
            verdict_match = re.search(
                r"(?:winning|best|selected|preferred)\s+hypothesis[^\n]*?(H[123])\b",
                response_output,
                re.IGNORECASE,
            )
            if verdict_match:
                update_state(session_id, {"verdict": verdict_match.group(1)}, terminal_id)
        set_final_answer(session_id, response_output, terminal_id)
        return {"allow": True}

def _find_active_session(terminal_id: str) -> dict | None:
    import time
    if not STATE_DIR.exists(): return None
    now = time.time()
    pattern = f"*_{terminal_id}.json" if terminal_id else "*.json"
    for state_file in STATE_DIR.glob(pattern):
        try:
            if now - state_file.stat().st_mtime > 7200:
                state_file.unlink()
                continue
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if state.get("active", False): return state
        except: continue
    return None

if __name__ == "__main__":
    import json, sys
    try: data = json.loads(sys.stdin.read())
    except: sys.exit(0)
    result = stop(data) or {}
    print(json.dumps({"allow": result.get("allow", True), "reason": result.get("reason", "")}))
