#!/usr/bin/env python3
"""
External Judge Integration for Stop.py.

Provides LLM-based quality assessment of responses against a structured rubric.
Used by _run_judge_evaluation() in Stop.py for external verdict generation.

Design principles:
- Terminal-scoped: Each terminal maintains isolated state
- Stale data immune: Reads fresh from files each evaluation
- Compact event immune: Uses file-based state, no in-memory caching
- Fail-open: Judge errors or unavailability don't block the response
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Paths
HOOKS_DIR = Path(__file__).resolve().parent.parent  # P:/.claude/hooks
RUBRIC_PATH = HOOKS_DIR / "__lib" / "judge_rubric.txt"
STATE_DIR = Path.home() / ".claude" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class JudgeConfig:
    """Configuration for external judge evaluation."""

    enabled: bool = True
    model: str = "sonnet"
    timeout_seconds: float = 30.0
    min_confidence_threshold: float = 0.7


@dataclass
class Verdict:
    """Structured verdict from the external judge."""

    score: float  # 0.0 - 1.0 overall quality score
    passes: bool  # True if score >= threshold
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: float = 1.0  # Judge confidence in verdict
    model_used: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None


def get_config() -> JudgeConfig:
    """Load judge configuration from environment.

    Defaults to enabled with sonnet model and 0.7 threshold.
    """
    return JudgeConfig(
        enabled=os.environ.get("EXTERNAL_JUDGE_ENABLED", "true").lower() == "true",
        model=os.environ.get("EXTERNAL_JUDGE_MODEL", "sonnet"),
        timeout_seconds=float(os.environ.get("EXTERNAL_JUDGE_TIMEOUT", "30.0")),
        min_confidence_threshold=float(
            os.environ.get("EXTERNAL_JUDGE_THRESHOLD", "0.7")
        ),
    )


def load_rubric() -> str:
    """Load the judge rubric from disk.

    Returns empty string if rubric file doesn't exist (fail-open).
    """
    try:
        if RUBRIC_PATH.exists():
            return RUBRIC_PATH.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def _get_terminal_id() -> str:
    """Detect terminal ID for state isolation."""
    raw = os.environ.get("WT_SESSION", "")
    if raw:
        return f"console_{raw}"
    return "unknown"


def _get_state_path() -> Path:
    """Get path to judge state file for current terminal."""
    terminal_id = _get_terminal_id()
    return STATE_DIR / f"judge_state_{terminal_id}.json"


def load_state() -> dict:
    """Load judge state for current terminal.

    Returns empty dict if state file doesn't exist.
    """
    path = _get_state_path()
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_state(state: dict) -> None:
    """Save judge state for current terminal.

    Uses atomic write to prevent corruption.
    """
    path = _get_state_path()
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


def evaluate_response(
    response: str,
    user_prompt: str,
    turn_mode: str = "analysis",
) -> Verdict:
    """Evaluate a response using the external judge.

    Args:
        response: The assistant's response text
        user_prompt: The original user prompt
        turn_mode: Current turn mode (control, exploration, analysis, plan, etc.)

    Returns:
        Verdict with score, issues, suggestions, and metadata.
        Returns error Verdict on failure (fail-open).
    """
    config = get_config()

    if not config.enabled:
        return Verdict(
            score=1.0,
            passes=True,
            confidence=1.0,
            model_used="disabled",
            latency_ms=0.0,
        )

    if not response or not response.strip():
        return Verdict(
            score=1.0,
            passes=True,
            confidence=1.0,
            model_used="empty-auto-pass",
            latency_ms=0.0,
        )

    start_time = time.perf_counter()

    try:
        rubric = load_rubric()

        # Build evaluation prompt
        prompt = _build_evaluation_prompt(
            response=response,
            user_prompt=user_prompt,
            turn_mode=turn_mode,
            rubric=rubric,
        )

        # Call external judge via Claude Code API
        verdict = _call_judge(prompt, config)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        verdict.latency_ms = elapsed_ms

        # Apply threshold
        verdict.passes = verdict.score >= config.min_confidence_threshold

        # Record verdict for telemetry
        _record_verdict(verdict, user_prompt, turn_mode)

        return verdict

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        # Fail-open: return passing verdict with error
        return Verdict(
            score=1.0,
            passes=True,
            confidence=0.0,
            model_used="error",
            latency_ms=elapsed_ms,
            error=str(e),
        )


def _build_evaluation_prompt(
    response: str,
    user_prompt: str,
    turn_mode: str,
    rubric: str,
) -> str:
    """Build the evaluation prompt for the judge."""

    rubric_section = f"\n\n## RUBRIC\n{rubric}" if rubric else ""

    return f"""You are an external quality judge evaluating an AI assistant response.

## TURN MODE: {turn_mode}

## USER PROMPT
{user_prompt}

## RESPONSE TO EVALUATE
{response}
{rubric_section}

## OUTPUT FORMAT
Return a JSON object with:
- "score": float 0.0-1.0 (overall quality)
- "issues": list of strings (specific problems found)
- "suggestions": list of strings (improvement recommendations)
- "confidence": float 0.0-1.0 (confidence in this verdict)

Respond ONLY with the JSON object, no additional text."""


def _call_judge(prompt: str, config: JudgeConfig) -> Verdict:
    """Call the external judge API.

    Uses subprocess to call Claude Code with the judge prompt.
    Falls back to heuristic evaluation if subprocess fails.
    """
    import subprocess

    judge_script = HOOKS_DIR / "__lib" / "_judge_subprocess.py"

    try:
        # Write prompt to temp file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            result = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--print",
                    "--model",
                    config.model,
                    "--no-input",
                    f"@{prompt_file}",
                ],
                capture_output=True,
                text=True,
                timeout=config.timeout_seconds,
                cwd=str(HOOKS_DIR),
            )

            # Parse JSON response
            try:
                data = json.loads(result.stdout.strip())
                return Verdict(
                    score=float(data.get("score", 0.5)),
                    passes=True,
                    issues=data.get("issues", []),
                    suggestions=data.get("suggestions", []),
                    confidence=float(data.get("confidence", 0.8)),
                    model_used=config.model,
                )
            except (json.JSONDecodeError, ValueError, KeyError):
                # Fall back to heuristic evaluation
                return _heuristic_evaluate(result.stdout, prompt)

        finally:
            try:
                Path(prompt_file).unlink()
            except Exception:
                pass

    except Exception as e:
        # Fall back to heuristic evaluation
        return _heuristic_evaluate(None, prompt, error=str(e))


def _heuristic_evaluate(
    text: Optional[str],
    prompt: str,
    error: Optional[str] = None,
) -> Verdict:
    """Heuristic evaluation when external judge is unavailable.

    Applies simple scoring rules without LLM call.
    """
    issues: list[str] = []
    suggestions: list[str] = []
    score = 0.8  # Baseline

    # Check response length - auto-pass empty/short (judge may run on
    # tool-only turns where the "response" is just tool output, not prose)
    if not text or len(text) < 50:
        return Verdict(
            score=1.0,
            passes=True,
            confidence=1.0,
            model_used="heuristic-auto-pass",
            latency_ms=0.0,
        )

    # Check for common quality issues
    text_lower = text.lower()

    # Check for deflection patterns
    if "let me check" in text_lower and "i didn't" in text_lower:
        score -= 0.2
        issues.append("Claims to investigate without evidence")

    # Check for hedging without substance
    if text.count("maybe") > 3 or text.count("perhaps") > 2:
        score -= 0.1
        issues.append("Excessive hedging")

    # Check for directness
    if text.startswith("well,") or text.startswith("so,"):
        score -= 0.05
        issues.append("Response starts with filler")

    if error:
        suggestions.append(f"External judge unavailable: {error}")

    # Normalize score
    score = max(0.0, min(1.0, score))

    return Verdict(
        score=score,
        passes=score >= 0.7,
        issues=issues,
        suggestions=suggestions,
        confidence=0.5,  # Lower confidence for heuristic
        model_used="heuristic",
    )


def _record_verdict(
    verdict: Verdict,
    user_prompt: str,
    turn_mode: str,
) -> None:
    """Record verdict for telemetry."""
    state = load_state()

    # Update statistics
    stats = state.get("stats", {"total": 0, "passed": 0, "failed": 0})
    stats["total"] += 1
    if verdict.passes:
        stats["passed"] += 1
    else:
        stats["failed"] += 1

    state["stats"] = stats
    state["last_verdict"] = {
        "score": verdict.score,
        "passes": verdict.passes,
        "model": verdict.model_used,
        "latency_ms": verdict.latency_ms,
        "turn_mode": turn_mode,
        "timestamp": time.time(),
    }

    save_state(state)


def get_stats() -> dict:
    """Get judge statistics for current terminal."""
    state = load_state()
    return state.get("stats", {"total": 0, "passed": 0, "failed": 0})