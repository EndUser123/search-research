"""Behavior tests: the validators accept well-formed handoffs and reject malformed ones.

These tests use complete handoff documents (not snippets) to verify the
end-to-end validation pipeline. Each test corresponds to a behavior the skill
contract specifies.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure __lib is importable when run from anywhere.
SKILL_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = SKILL_ROOT / "__lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import pytest  # noqa: E402

from validators import (  # noqa: E402
    validate_handoff_text,
    is_valid,
    parse_frontmatter,
    extract_headings,
    extract_task_packets,
)


# ---------------------------------------------------------------------------
# Test fixtures — complete handoff documents
# ---------------------------------------------------------------------------

VALID_HANDOFF = """\
---
thread_id: 11111111-2222-3333-4444-555555555555
parent_handoff_path: none
current_session_id: 66666666-7777-8888-9999-aaaaaaaaaaaa
current_terminal_id: term-A
produced_at: 2026-07-20T12:34:56Z
status: open
handoff_type: investigation
accurate_as_of_head: abc1234def5678
---

# Handoff: example feature work

## Objective

Investigate whether the widget dispatcher can be simplified.

## Status

OPEN

## Producing context

- Date: 2026-07-20
- Session: 66666666-7777-8888-9999-aaaaaaaaaaaa
- Terminal: term-A

## Read-first list

1. `src/widget.ts` — current dispatcher
2. `src/widget.test.ts` — existing tests

## Verified facts

- [FACT] Widget dispatcher has 14 branches (`src/widget.ts:42-180`)

## Current state

Investigation complete; no code changes made.

## Task packets

### W-1: simplify-dispatcher

- goal: reduce dispatch branches from 14 to 6
- in scope: `src/widget.ts` only
- out of scope: tests, types
- files / anchors: `src/widget.ts:42-180`
- acceptance: branch count <= 6; all tests pass
- falsifier: if any of branches 7-14 cannot be merged into the first 6 without behavior change
- verification level required: UNIT_TEST

## Open decisions

None.

## Hard constraints

- No behavior change to public API

## Cross-reference couplings

- `src/widget.ts` → imported by `src/app.ts`. If dispatcher signature changes, app.ts breaks.
- This handoff's `accurate_as_of_head` → `abc1234def5678`. If HEAD moves, re-verify `src/widget.ts:42-180`.

## Other outstanding streams

- **auth-refactor** — separate work; OPEN

## Explicit non-goals

- Do not touch the auth module

## Resumption protocol

1. Read `src/widget.ts`
2. Confirm branch count

## Suggested next invocation

`/go simplify src/widget.ts`

## Last user message (verbatim)

> can you simplify the widget dispatcher?

## Epistemic labels

- [FACT] branch count verified by reading source
- [INFERENCE] simplification is feasible because branches 7-14 share structure
- [UNKNOWN] whether the simplification will pass performance review
"""

# Handoff missing one mandatory header field.
MISSING_THREAD_ID = VALID_HANDOFF.replace("thread_id: 11111111-2222-3333-4444-555555555555\n", "")

# Handoff with a malformed thread_id.
BAD_THREAD_ID = VALID_HANDOFF.replace(
    "thread_id: 11111111-2222-3333-4444-555555555555",
    "thread_id: not-a-uuid",
)

# Handoff missing a mandatory body section.
MISSING_SECTION = VALID_HANDOFF.replace("## Objective\n", "## Renamed Section\n")

# Handoff with a task packet missing the falsifier.
PACKET_MISSING_FALSIFIER = VALID_HANDOFF.replace(
    "- falsifier: if any of branches 7-14 cannot be merged into the first 6 without behavior change\n",
    "",
)

# Handoff with a trivial falsifier.
PACKET_TRIVIAL_FALSIFIER = VALID_HANDOFF.replace(
    "- falsifier: if any of branches 7-14 cannot be merged into the first 6 without behavior change",
    "- falsifier: n/a",
)

# Handoff with bad verification level.
PACKET_BAD_VERIFICATION = VALID_HANDOFF.replace(
    "- verification level required: UNIT_TEST",
    "- verification level required: GUESS",
)

# Handoff where verbatim section is paraphrased instead of quoted.
VERBATIM_PARAPHRASED = VALID_HANDOFF.replace(
    '> can you simplify the widget dispatcher?',
    'The user wanted the widget dispatcher simplified.',
)

# Handoff where verbatim section is empty.
VERBATIM_EMPTY = VALID_HANDOFF.replace(
    '> can you simplify the widget dispatcher?',
    '',
)

# Handoff with bad status.
BAD_STATUS = VALID_HANDOFF.replace("status: open", "status: in-progress")

# Handoff with bad type.
BAD_TYPE = VALID_HANDOFF.replace("handoff_type: investigation", "handoff_type: pizza")

# Handoff with bad timestamp.
BAD_TIMESTAMP = VALID_HANDOFF.replace(
    "produced_at: 2026-07-20T12:34:56Z",
    "produced_at: July 20 2026",
)

# Handoff with non-absolute parent_handoff_path.
BAD_PARENT_PATH = VALID_HANDOFF.replace(
    "parent_handoff_path: none",
    "parent_handoff_path: relative/path/handoff.md",
)


# ---------------------------------------------------------------------------
# Behavior tests
# ---------------------------------------------------------------------------


def test_valid_handoff_passes():
    """A complete, well-formed handoff has zero error-severity issues."""
    issues = validate_handoff_text(VALID_HANDOFF)
    errors = [i for i in issues if i["severity"] == "error"]
    assert errors == [], f"valid handoff reported errors: {errors}"


def test_is_valid_convenience_returns_true_for_valid():
    assert is_valid(VALID_HANDOFF) is True


def test_missing_thread_id_is_error():
    """Missing required header field is an error, not a warning."""
    issues = validate_handoff_text(MISSING_THREAD_ID)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("thread_id" in i["field"] for i in errors), (
        f"expected thread_id error, got: {errors}"
    )


def test_bad_thread_id_shape_is_error():
    """thread_id that is not UUID-shaped is rejected."""
    issues = validate_handoff_text(BAD_THREAD_ID)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("thread_id" in i["field"] and "UUID" in i["message"] for i in errors)


def test_missing_body_section_is_error():
    """Missing mandatory body section (Objective) is an error."""
    issues = validate_handoff_text(MISSING_SECTION)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("objective" in i["field"] for i in errors), (
        f"expected 'objective' missing-section error, got: {errors}"
    )


def test_packet_missing_falsifier_is_error():
    """Task packet missing the falsifier field is an error."""
    issues = validate_handoff_text(PACKET_MISSING_FALSIFIER)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("falsifier" in i["field"] for i in errors), (
        f"expected falsifier error, got: {errors}"
    )


def test_packet_trivial_falsifier_is_warning_not_error():
    """Trivial falsifier ('n/a') is a warning, not an error — does not block."""
    issues = validate_handoff_text(PACKET_TRIVIAL_FALSIFIER)
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warn"]
    assert not any("falsifier" in i["field"] for i in errors), (
        f"trivial falsifier should be warning, not error: {errors}"
    )
    assert any("falsifier" in i["field"] for i in warnings), (
        f"expected falsifier warning, got: {warnings}"
    )


def test_packet_bad_verification_level_is_error():
    """Unknown verification level is rejected."""
    issues = validate_handoff_text(PACKET_BAD_VERIFICATION)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("verification" in i["field"] for i in errors)


def test_verbatim_paraphrased_is_error():
    """Paraphrased user message (not a blockquote) fails the verbatim check."""
    issues = validate_handoff_text(VERBATIM_PARAPHRASED)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("verbatim" in i["field"] for i in errors), (
        f"expected verbatim error, got: {errors}"
    )


def test_verbatim_empty_is_error():
    """Empty blockquote area fails the verbatim check."""
    issues = validate_handoff_text(VERBATIM_EMPTY)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("verbatim" in i["field"] for i in errors)


def test_bad_status_is_error():
    """Status outside the allowed set is rejected."""
    issues = validate_handoff_text(BAD_STATUS)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "status" for i in errors)


def test_bad_type_is_error():
    """handoff_type outside the v0.1 allowed set is rejected."""
    issues = validate_handoff_text(BAD_TYPE)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "handoff_type" for i in errors)


def test_bad_timestamp_is_error():
    """Non-ISO-8601 timestamp is rejected."""
    issues = validate_handoff_text(BAD_TIMESTAMP)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "produced_at" for i in errors)


def test_bad_parent_path_is_error():
    """parent_handoff_path that is neither 'none' nor absolute is rejected."""
    issues = validate_handoff_text(BAD_PARENT_PATH)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "parent_handoff_path" for i in errors)


def test_missing_accurate_as_of_head_is_error():
    """Missing the accurate_as_of_head header field is an error.

    Promoted to mandatory in v0.1.1 — captures git HEAD at production time
    so readers can detect staleness against current `git rev-parse HEAD`.
    """
    missing = VALID_HANDOFF.replace("accurate_as_of_head: abc1234def5678\n", "")
    issues = validate_handoff_text(missing)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "accurate_as_of_head" for i in errors), (
        f"expected accurate_as_of_head error, got: {errors}"
    )


def test_missing_cross_reference_couplings_section_is_error():
    """Missing the 'Cross-reference couplings' body section is an error.

    Promoted to mandatory in v0.1.1 after corpus review showed the
    load-bearing value of the dependency map (only the best handoff in
    the workspace had it; the rest suffered for its absence).
    """
    missing = VALID_HANDOFF.replace("## Cross-reference couplings\n", "## Renamed\n")
    issues = validate_handoff_text(missing)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("cross-reference couplings" in i["field"] for i in errors), (
        f"expected cross-reference couplings missing-section error, got: {errors}"
    )


# ---------------------------------------------------------------------------
# Parser behavior (separate from validation)
# ---------------------------------------------------------------------------


def test_frontmatter_parser_handles_quotes():
    """Quoted values have their quotes stripped."""
    text = "---\nstatus: \"open\"\nkey: 'value'\n---\nbody"
    fm, body = parse_frontmatter(text)
    assert fm["status"] == "open"
    assert fm["key"] == "value"
    assert body == "body"


def test_frontmatter_parser_strips_comments():
    """Lines starting with # inside frontmatter are ignored."""
    text = "---\n# this is a comment\nstatus: open\n---\nbody"
    fm, _ = parse_frontmatter(text)
    assert fm == {"status": "open"}


def test_frontmatter_parser_no_frontmatter():
    """Files without frontmatter return empty dict and full body."""
    text = "# just a heading\n\nbody text"
    fm, body = parse_frontmatter(text)
    assert fm == {}
    assert body == text


def test_extract_headings_only_level_2():
    """Level-3 and deeper headings are not extracted."""
    body = "## Foo\n### Bar\n## Baz\n#### Qux"
    headings = extract_headings(body)
    assert headings == ["foo", "baz"]


def test_extract_task_packets_basic():
    """Task packets are parsed with id, goal, and bullet fields."""
    body = """\
## Task packets

### W-1: do the thing

- in scope: x
- out of scope: y
- falsifier: if x breaks
- verification level required: UNIT_TEST

### W-2: another thing

- goal inherited from heading
"""
    packets = extract_task_packets(body)
    assert len(packets) == 2
    assert packets[0]["id"] == "W-1"
    assert packets[0]["goal"] == "do the thing"
    assert packets[0]["in scope"] == "x"
    assert packets[1]["id"] == "W-2"


def test_extract_task_packets_none_when_section_absent():
    body = "## Some other section\n\ncontent"
    assert extract_task_packets(body) == []
