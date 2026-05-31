

# -- FIX 3: table/blockquote newline exemption ------------------------------------

def test_capitulation_inside_markdown_table_not_blocked():
    """FIX 3 (live repro): capitulation phrase inside a table cell is NOT blocked.

    Root cause: whitespace normalization stripped newlines, so _is_inside_quoted_content
    could not detect the table via rfind('\\n'). Fix: preserve newlines in normalization.
    """
    table_resp = (
        "Here is my analysis:\n\n"
        "| Block | Label | Why |\n"
        "|---|---|---|\n"
        '| Capitulation on "You\'re right to challenge it" | TRUE positive | the gate worked |\n\n'
        "That is the finding."
    )
    result = detect_lazy_closure(table_resp, has_bash_evidence=False)
    assert result is None, (
        f"Should NOT block capitulation inside table cell, got: {result}"
    )


def test_capitulation_inside_blockquote_not_blocked():
    """FIX 3: capitulation phrase on a blockquote line is NOT blocked.

    Blockquote lines start with '> ', which _is_inside_quoted_content detects via
    line-prefix check after rfind('\\n'). This only works when newlines are preserved.
    """
    blockquote_resp = (
        "Here is the transcript:\n\n"
        "> You're right, I was wrong about that.\n\n"
        "That was the prior model output being quoted."
    )
    result = detect_lazy_closure(blockquote_resp, has_bash_evidence=False)
    assert result is None, (
        f"Should NOT block capitulation inside blockquote, got: {result}"
    )


def test_bare_capitulation_still_blocked():
    """FIX 3 (preserved TRUE POSITIVE): bare capitulation as model assertion is blocked.

    The fix must not weaken bare (unquoted) capitulation detection.
    This is the catch that found a real error this session.
    """
    response = "You're right, I was wrong about that."
    result = detect_lazy_closure(response, has_bash_evidence=False)
    assert result is not None, "Should BLOCK bare capitulation in model assertion"
    assert result.pattern_type == "sycophancy_capitulation"


def test_capitulation_with_bash_evidence_true_still_exempt():
    """Preserved: has_bash_evidence=True exempts bare capitulation (existing exemption)."""
    response = "You're right, I was wrong about that."
    result = detect_lazy_closure(response, has_bash_evidence=True)
    assert result is None, (
        f"Should NOT block when has_bash_evidence=True, got: {result}"
    )
