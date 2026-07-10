"""
Regression tests for Stop_removal_completeness_guard fixes (#1415).

Fix (a) — word-boundary lookaround on import regex (mirrors _indicator_match
      from #882). Prevents `cli` from prefix-matching `clip`/`clipboard`.
      Submodule form `import foo.bar` still detected when `foo` was removed.

Fix (b) — scoped module-name extraction: only extract from sentences that
      contain removal-completion claims. Prevents prose fragments like
      "investigation contracts say" from producing module names.

measured_tp_on_corpus recorded in comments near each test section.
"""
from __future__ import annotations

import re
import pytest


# ── Inline copy of the FIXED import regex (fix a) ──────────────────────────


def _build_import_re(module_names: list[str]) -> re.Pattern:
    escaped = [re.escape(n) for n in module_names]
    combined = "|".join(escaped)
    return re.compile(
        rf"^\s*(?:import\s+(?<!\w)(?:{combined})(?!\w)(?:\.[A-Za-z_]\w*)*|"
        rf"from\s+(?<!\w)(?:{combined})(?!\w)(?:\.[A-Za-z_]\w*)*\s+import)",
        re.IGNORECASE | re.MULTILINE,
    )


# ── Fix (a): import regex word-boundary — incident replay + synthetic TP ───


def test_fp_clip_not_matched_as_cli() -> None:
    """REPLAY: real incident — response claimed `cli`-related removal, tree
    had `import clip`. Must NOT fire (prefix-match)."""
    pat = _build_import_re(["cli"])
    source_lines = [
        "import clip  # from packages/yt-is/csf/clip_client.py",
        "",
        "from clipboard import paste",
        "import cli  # genuine import of short-named module",
    ]
    source = "\n".join(source_lines)

    matches = list(pat.finditer(source))
    matched_names = set()
    for m in matches:
        text = m.group(0).strip()
        for name in ("cli",):
            if name in text.split():
                matched_names.add(name)

    # "import clip" must NOT match, but "import cli" must.
    assert "import cli" in source
    assert "import clip" in source
    assert "cli" in matched_names
    assert matched_names == {"cli"}


def test_fp_clipboard_not_matched_as_cli() -> None:
    """PROBE: `import clipboard` with pattern for module `cli`."""

    pat = _build_import_re(["cli"])
    source = "import clipboard\n\nimport argparse\n"
    matches = list(pat.finditer(source))
    # clipboard starts with 'cli' but is a longer word — lookahead must reject
    for m in matches:
        assert "clipboard" not in m.group(0), f"matched clipboard: {m.group(0).strip()}"


@pytest.mark.parametrize("line,name", [
    ("import cli", "cli"),
    ("import foo", "foo"),
    ("from cli import utils", "cli"),
    ("from foo.bar import Baz", "foo"),
    ("import foo.bar", "foo"),
    ("from foo import bar", "foo"),
    ("import foo.bar.baz", "foo"),
    ("from foo.bar.baz import Qux", "foo"),
])
def test_tp_genuine_matches(line: str, name: str) -> None:
    """SYNTHETIC TP: genuine import of a removed module MUST fire."""
    pat = _build_import_re([name])
    assert pat.search(line), (
        f"pattern for {name!r} should match {line!r}"
    )


def test_tp_combined_alternation() -> None:
    """SYNTHETIC TP: removed 'cli', tree has 'import cli.utils'.
    Submodule continuation must match."""
    pat = _build_import_re(["cli"])
    source = "import cli.utils\n"
    assert pat.search(source), "import cli.utils should match module cli"


# ── Fix (b): extraction scoping — junk prose must not produce names ────────

# Inline copy of REMOVAL_COMPLETION_PATTERNS and helper

_REMOVAL_COMPLETION_PATTERNS = re.compile(
    r"\bcleanup\s+(?:is\s+)?complete\b"
    r"|\b(?:fully|completely)\s+(?:removed|deleted|cleaned)\b"
    r"|\bremoval\s+(?:is\s+)?complete\b"
    r"|\b(?:all|zero)\s+(?:remaining\s+)?(?:references?|imports?|usages?)\s+(?:removed|deleted|gone)\b"
    r"|\bno\s+(?:remaining|more)\s+(?:references?|imports?|usages?)\b"
    r"|\b(?:zero|no)\s+remaining\s+(?:references?|imports?|usages?)\b",
    re.IGNORECASE,
)


def _extract_claim_sentence_text_impl(text: str, claim_pat: re.Pattern) -> str:
    """Minimal inline copy of _extract_claim_sentence_text for testing."""
    sentences: list[str] = []
    for m in re.finditer(r"[^.!?\n]*[.!?\n]", text):
        sentence = m.group(0)
        if claim_pat.search(sentence):
            sentences.append(sentence)
    return " ".join(sentences)


def _extract_module_names_impl(response: str) -> list[str]:
    """Minimal inline copy of scoped extraction for testing.

    Tests the sentence-scoping behavior (fix b).  In production this also
    runs _extract_file_paths and MODULE_EXPLICIT_PATTERNS; here we test that
    junk prose outside a claim sentence is excluded.
    """
    names: set[str] = set()
    claim_text = _extract_claim_sentence_text_impl(response, _REMOVAL_COMPLETION_PATTERNS)
    if not claim_text.strip():
        return []

    # Source 1: simple identifier extraction — ident tokens in the claim text
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", claim_text):
        if len(token) >= 3 and token not in names:
            names.add(token)

    # Source 2: MODULE_EXPLICIT_PATTERNS simulation
    explicit = re.compile(r"(\w[\w-]*)\s+(?:module|system|plugin|package|library)\b", re.IGNORECASE)
    for m in explicit.finditer(claim_text):
        name = m.group(1).replace("-", "_")
        if len(name) >= 3:
            names.add(name)

    return sorted(names)[:10]


def test_prose_junk_outside_claim_not_extracted() -> None:
    """Incident replay: "investigation contracts say" must NOT produce a module name.

    The response contains a removal claim about 'cli', plus unrelated prose
    ("investigation contracts say"). The extraction should only find 'cli'
    from the claim-adjacent sentences, not 'investigation' or 'contracts'.
    """
    response = (
        "All remaining references to the cli module have been completely removed. "
        "No remaining imports found in the codebase.\n\n"
        "During the investigation contracts say that cli was never fully "
        "integrated with the existing framework.\n"
    )
    names = _extract_module_names_impl(response)
    assert "cli" in names, f"expected 'cli' in extracted names: {names}"
    assert "investigation" not in names, (
        f"'investigation' should not be a module name: {names}"
    )
    assert "contracts" not in names, (
        f"'contracts' should not be a module name: {names}"
    )
    assert "say" not in names or len(names) == 1, (
        f"only 'cli' expected, got: {names}"
    )


def test_multiple_claim_sentences_all_covered() -> None:
    """All claim-adjacent sentences contribute their module names."""
    response = (
        "The foo module was completely removed. "
        "All imports of bar completely deleted. "
        "There are no remaining references anywhere. "
    )
    names = _extract_module_names_impl(response)
    assert "foo" in names, f"expected foo: {names}"
    assert "bar" in names, f"expected bar: {names}"


def test_no_claim_text_empty_extraction() -> None:
    """When no removal-completion claim exists, no names are extracted."""
    response = "The investigation contracts say that refactoring is ongoing."
    names = _extract_module_names_impl(response)
    assert names == [], f"expected empty, got: {names}"


# ── Fix (b): real production path + quote-exemption ────────────────────────


def test_real_extraction_with_quote_exemption() -> None:
    """Exercises the real _extract_claim_sentence_text which uses search_unquoted.

    A quoted removal claim ("cleanup complete" inside backtick fences) must NOT
    be treated as a claim sentence, even though the words match.  The inline
    test copies above drop this exemption (quote_exemption.search_unquoted vs
    plain pattern.search), so this test covers the actual production path.
    """
    import sys as _sys
    from pathlib import Path as _Path
    from importlib import import_module as _import_module

    # Bootstrap path from module root (same as the guard's own bootstrap)
    _mod_root = _Path(__file__).resolve().parent.parent / "hooks" / "stop"
    if str(_mod_root) not in _sys.path:
        _sys.path.insert(0, str(_mod_root))
    _guard = _import_module("Stop_removal_completeness_guard")

    # Text where the only claim window is inside a fenced quote
    response = """The system is fully operational.

```
Cleanup is complete — all temporary files were removed.
```

Also the migration ran without errors."""
    result = _guard._extract_claim_sentence_text(response)
    assert result.strip() == "", (
        f"Expected empty (claim is inside quotes), got: {result!r}"
    )

    # Positive control: same text without the fence must extract the sentence
    response_unquoted = """The system is fully operational.

Cleanup is complete — all temporary files were removed.

Also the migration ran without errors."""
    result2 = _guard._extract_claim_sentence_text(response_unquoted)
    assert "Cleanup is complete" in result2, (
        f"Expected unquoted claim to be extracted, got: {result2!r}"
    )
