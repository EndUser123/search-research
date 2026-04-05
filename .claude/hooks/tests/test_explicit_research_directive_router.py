#!/usr/bin/env python3
"""Tests for explicit research directive handling in UserPromptSubmit_router."""

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_run_explicit_research_directive_fires():
    from UserPromptSubmit_router import run_explicit_research_directive

    prompt = "do internet research on how to invoke agent teams"
    result = run_explicit_research_directive({"prompt": prompt}, prompt)

    assert result is not None
    assert result.get("required") is True
    assert "BLOCKED: no web access" in result.get("context", "")


def test_run_explicit_research_directive_noop_without_directive():
    from UserPromptSubmit_router import run_explicit_research_directive

    prompt = "what is the status of this task?"
    result = run_explicit_research_directive({"prompt": prompt}, prompt)

    assert result is None
