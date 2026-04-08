from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import Stop  # type: ignore
import dependency_chain_guard as dcg


def test_blocks_ranking_that_ignores_established_prerequisite() -> None:
    data = {
        "assistant_response": (
            "By reliability: 1. Whisper audio. 2. Selenium Chrome. 3. yt-dlp + browser cookies."
        ),
        "transcript": [
            {
                "role": "assistant",
                "content": "To use Whisper, yt-dlp must first download the audio.",
            }
        ],
    }

    result = dcg.check(data)

    assert result is not None
    assert result["decision"] == "block"
    assert "`whisper`" in result["reason"].lower()
    assert "`yt-dlp`" in result["reason"].lower()


def test_allows_ranking_when_dependency_is_acknowledged() -> None:
    data = {
        "assistant_response": (
            "By reliability end-to-end: 1. Selenium Chrome. "
            "2. yt-dlp + browser cookies. "
            "5. Whisper, because it still depends on yt-dlp downloading audio first."
        ),
        "transcript": [
            {
                "role": "assistant",
                "content": "To use Whisper, yt-dlp must first download the audio.",
            }
        ],
    }

    result = dcg.check(data)

    assert result is None


def test_blocks_bypass_claim_when_context_established_dependency() -> None:
    data = {
        "assistant_response": "Whisper bypasses YouTube entirely, so it is the most reliable option.",
        "transcript": [
            {
                "role": "assistant",
                "content": "If yt-dlp can't get the audio URL, Whisper never fires.",
            }
        ],
    }

    result = dcg.check(data)

    assert result is not None
    assert result["decision"] == "block"
    assert "bypass" in result["reason"].lower()


def test_stop_gate_chain_includes_dependency_and_comparative_guards() -> None:
    gate_names = [name for name, _ in Stop.IN_PROCESS_GATES]

    assert "dependency_chain_guard" in gate_names
    assert "comparative_claim_guard" in gate_names
