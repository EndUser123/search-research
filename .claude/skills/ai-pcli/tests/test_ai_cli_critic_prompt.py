"""Regression tests for the ai-cli critic prompt guardrails."""

from __future__ import annotations

from pathlib import Path


def test_ai_cli_critic_prompt_contains_strict_guardrails():
    prompt = Path("P:/.claude/agents/ai-cli-critic.md").read_text(encoding="utf-8")

    assert "hallucinated file paths, flags, APIs, or facts" in prompt
    assert "Treat consensus as a signal only, never as proof" in prompt
    assert "Do not downgrade unsupported claims just because multiple models agreed" in prompt
    assert "Do not accept invented file paths, line numbers, or flags" in prompt
    assert "grounding_status" in prompt
