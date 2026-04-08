from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import StopHook_drift_sentinel
from __lib__.drift_sentinel import extract_paragraphs, detect_drift


def test_extract_paragraphs() -> None:
    # Splits on \n\n
    text = "This is the first paragraph and it is definitely longer than fifty characters.\n\nThis is the second paragraph and it is also quite long with more than fifty characters in total.\n\nAnd here is a third paragraph that also exceeds the fifty character minimum threshold requirement."
    paras = extract_paragraphs(text)
    assert len(paras) == 3

    # Splits on \n when no \n\n
    text2 = "This is a long line number one that exceeds fifty characters.\nThis is a long line number two that also exceeds fifty characters.\n\nAnother separate block here."
    paras2 = extract_paragraphs(text2)
    assert len(paras2) >= 2

    # Ignores short paragraphs
    text3 = "abc\n\nThis is a much longer paragraph that has more than fifty characters."
    paras3 = extract_paragraphs(text3)
    assert len(paras3) == 1
    assert "abc" not in paras3[0]


def test_detect_drift_no_drift() -> None:
    """Near-identical text returns high similarity (no drift)."""
    source = [
        "Authentication is handled via OAuth 2.0 with JWT tokens for secure access."
    ]
    response = "Authentication is handled via OAuth 2.0 with JWT tokens for secure access."
    result = detect_drift(response, source)
    assert result["drift_detected"] is False
    assert result["min_similarity"] >= 0.75


def test_detect_drift_with_drift() -> None:
    """Fabricated content returns low similarity (< 0.75)."""
    source = ["Authentication is handled via OAuth 2.0 with JWT tokens."]
    response = "The document says authentication uses SAML 2.0\n\nThis is a long paragraph that discusses SSO protocols and how identity providers work with SAML authentication mechanisms."
    result = detect_drift(response, source)
    assert result["drift_detected"] is True
    assert result["min_similarity"] < 0.75


def test_detect_drift_empty_source() -> None:
    """Empty source list fails open."""
    response = "Something completely fabricated without any source."
    result = detect_drift(response, [])
    assert result["drift_detected"] is False


def test_detect_drift_empty_response() -> None:
    """Empty response fails open."""
    source = ["Some source text that is definitely real and valid content."]
    result = detect_drift("", source)
    assert result["drift_detected"] is False


def test_detect_drift_threshold_boundary() -> None:
    """Content at exactly 0.75 returns no drift (strict inequality)."""
    # The threshold is < 0.75, so content at exactly 0.75 should NOT trigger drift
    source = [
        "Python is a widely used programming language that supports multiple paradigms including object-oriented programming."
    ]
    response = "Python is a widely used programming language that supports multiple paradigms including object-oriented programming and functional programming."
    result = detect_drift(response, source)
    # At boundary: if similarity is exactly 0.75 or higher, drift_detected should be False
    assert result["drift_detected"] is False


def test_stop_hook_skips_short_response() -> None:
    assert StopHook_drift_sentinel._should_run_drift_check("short", ["source one", "source two"]) is False


def test_stop_hook_skips_when_not_enough_sources() -> None:
    response = "This is a sufficiently long response that would otherwise trigger drift analysis."
    assert StopHook_drift_sentinel._should_run_drift_check(response, ["only one source"]) is False


def test_stop_hook_lazy_imports_detector() -> None:
    response = "This is a sufficiently long response that should be truncated before analysis." * 20
    sources = ["source one" * 40, "source two" * 40]
    with patch("__lib__.drift_sentinel.detect_drift") as detector:
        detector.return_value = {"drift_detected": False, "min_similarity": 1.0}
        result = StopHook_drift_sentinel._detect_drift(response, sources)
    assert result["drift_detected"] is False
