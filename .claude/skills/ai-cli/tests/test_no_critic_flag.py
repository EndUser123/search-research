"""Regression tests for the ai-cli critic opt-out flag."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from ai_cli import main


def test_no_critic_flag_is_accepted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    mock_results = {"qwen": {"output": "Response", "error": None}}

    with patch("ai_cli.run_parallel_llm", return_value=mock_results):
        with patch.object(
            sys,
            "argv",
            [
                "ai_cli.py",
                "test query",
                "--output-format",
                "json",
                "--no-critic",
                "--qwen-only",
            ],
        ):
            try:
                main()
            except SystemExit:
                pass

    output_files = list(Path(tmp_path).glob("output_*.json"))
    assert output_files, "Expected JSON output file to be written"
