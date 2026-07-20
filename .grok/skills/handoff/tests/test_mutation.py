"""Mutation tests: each validator must catch its specific failure mode.

For each validator, we apply a mutation that the validator is supposed to
catch, and verify that the issue list contains a matching error. This guards
against regressions where a validator silently becomes a no-op (e.g., a regex
gets loosened, a constant gets renamed, a function returns early).

Mutation testing discipline:
  - Each test mutates ONE thing.
  - Each test asserts the SPECIFIC validator catches it (not just "some error").
  - Each test also asserts the issue severity is correct (error vs warning).
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = SKILL_ROOT / "__lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import pytest  # noqa: E402

from validators import (  # noqa: E402
    validate_header,
    validate_body_sections,
    validate_task_packets,
    validate_verbatim_message,
    validate_streams_section_format,
    validate_handoff_text,
    parse_frontmatter,
    extract_headings,
    extract_task_packets,
    HEADER_REQUIRED,
    BODY_REQUIRED_SECTIONS,
    TASK_PACKET_REQUIRED,
)


# ---------------------------------------------------------------------------
# validate_header mutations
# ---------------------------------------------------------------------------


def _base_header() -> dict[str, str]:
    return {
        "thread_id": "11111111-2222-3333-4444-555555555555",
        "parent_handoff_path": "none",
        "current_session_id": "66666666-7777-8888-9999-aaaaaaaaaaaa",
        "current_terminal_id": "term-A",
        "produced_at": "2026-07-20T12:34:56Z",
        "status": "open",
        "handoff_type": "investigation",
        "accurate_as_of_head": "abc1234def5678",
    }


@pytest.mark.parametrize("missing_field", HEADER_REQUIRED)
def test_header_rejects_missing_each_required_field(missing_field):
    """Mutate: remove exactly one required header field. Validator must catch each."""
    header = _base_header()
    del header[missing_field]
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == missing_field for i in errors), (
        f"validate_header did not catch missing field {missing_field!r}: {errors}"
    )


@pytest.mark.parametrize("empty_field", HEADER_REQUIRED)
def test_header_rejects_empty_each_required_field(empty_field):
    """Mutate: blank out exactly one required header field."""
    header = _base_header()
    header[empty_field] = "   "
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == empty_field for i in errors)


def test_header_rejects_non_uuid_thread_id():
    """Mutate: thread_id to a non-UUID string."""
    header = _base_header()
    header["thread_id"] = "not-a-uuid"
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("UUID" in i["message"] for i in errors)


def test_header_rejects_non_uuid_session_id():
    """Mutate: current_session_id to a non-UUID string."""
    header = _base_header()
    header["current_session_id"] = "session-1"
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "current_session_id" and "UUID" in i["message"] for i in errors)


def test_header_accepts_none_parent_path():
    """Sanity: 'none' parent_handoff_path is accepted (not flagged)."""
    header = _base_header()
    header["parent_handoff_path"] = "none"
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error" and i["field"] == "parent_handoff_path"]
    assert errors == []


def test_header_accepts_absolute_windows_parent_path():
    """Sanity: absolute Windows path is accepted."""
    header = _base_header()
    header["parent_handoff_path"] = r"P:\\docs\\handoffs\\x\\HANDOFF.md"
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error" and i["field"] == "parent_handoff_path"]
    assert errors == []


def test_header_accepts_absolute_posix_parent_path():
    """Sanity: absolute POSIX path is accepted."""
    header = _base_header()
    header["parent_handoff_path"] = "/home/user/handoffs/x/HANDOFF.md"
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error" and i["field"] == "parent_handoff_path"]
    assert errors == []


def test_header_rejects_relative_parent_path():
    """Mutate: parent_handoff_path to a relative path."""
    header = _base_header()
    header["parent_handoff_path"] = "docs/handoffs/x/HANDOFF.md"
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == "parent_handoff_path" for i in errors)


@pytest.mark.parametrize("bad_ts", [
    "July 20 2026",
    "2026-07-20",
    "2026-07-20 12:34:56",
    "yesterday",
    "",
])
def test_header_rejects_bad_timestamp(bad_ts):
    """Mutate: produced_at to various non-ISO-8601 forms."""
    header = _base_header()
    header["produced_at"] = bad_ts
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error" and i["field"] == "produced_at"]
    if bad_ts == "":
        # Empty is caught by the required-field check, not the format check.
        assert any("empty" in i["message"] for i in errors)
    else:
        assert any("ISO" in i["message"] for i in errors)


@pytest.mark.parametrize("bad_status", ["in-progress", "OPEN", "done", "pending", "", "open "])
def test_header_rejects_bad_status(bad_status):
    """Mutate: status to various disallowed forms (case-sensitive on enum)."""
    header = _base_header()
    header["status"] = bad_status
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error" and i["field"] == "status"]
    if bad_status.strip().lower() in {"open", "closed", "superseded"}:
        # "OPEN" uppercased normalizes to "open"; "open " trims to "open".
        assert errors == [], f"{bad_status!r} should normalize to allowed"
    else:
        assert errors, f"expected status rejection for {bad_status!r}"


@pytest.mark.parametrize("bad_type", ["implementation", "diagnostic", "architectural", "retrospective", "pizza", ""])
def test_header_v01_rejects_non_investigation_type(bad_type):
    """Mutate: handoff_type to anything other than 'investigation'.

    v0.1 only allows 'investigation'. v0.2 will loosen this — when it does,
    update HEADER_TYPE_ALLOWED_V01 and these tests together.
    """
    header = _base_header()
    header["handoff_type"] = bad_type
    issues = validate_header(header)
    errors = [i for i in issues if i["severity"] == "error" and i["field"] == "handoff_type"]
    if bad_type == "investigation":
        assert errors == []
    else:
        assert errors, f"v0.1 should reject type {bad_type!r}"


# ---------------------------------------------------------------------------
# validate_body_sections mutations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_section", BODY_REQUIRED_SECTIONS)
def test_body_rejects_missing_each_required_section(missing_section):
    """Mutate: remove one mandatory body section. Validator must catch each."""
    all_sections = list(BODY_REQUIRED_SECTIONS)
    headings = [s for s in all_sections if s != missing_section]
    issues = validate_body_sections(headings)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(i["field"] == missing_section for i in errors), (
        f"validate_body_sections did not catch missing section {missing_section!r}"
    )


def test_body_passes_when_all_sections_present():
    """Sanity: all required sections present -> no errors."""
    issues = validate_body_sections(list(BODY_REQUIRED_SECTIONS))
    assert [i for i in issues if i["severity"] == "error"] == []


def test_body_section_match_is_case_insensitive():
    """The validator lowercases input headings before comparison.

    extract_headings() returns lowercase; validate_body_sections compares
    against lowercase required-section constants. So passing uppercase
    headings to extract_headings produces lowercase output, which matches.
    """
    # Pass through extract_headings first (as the real pipeline does).
    body_with_upper = "\n".join(f"## {s.upper()}" for s in BODY_REQUIRED_SECTIONS)
    headings = []
    for line in body_with_upper.splitlines():
        s = line.lstrip()
        if s.startswith("## ") and not s.startswith("### "):
            headings.append(s[3:].strip())
    # Simulate the validator's internal lowercasing by extracting properly:
    from validators import extract_headings
    headings = extract_headings(body_with_upper)
    issues = validate_body_sections(headings)
    assert [i for i in issues if i["severity"] == "error"] == []


def test_body_section_match_strips_numbered_prefix():
    """Headings with a leading 'N. ' prefix are normalized before matching.

    Catches the regression where authors who number their sections
    ('## 1. Objective') silently fail validation. The prefix-stripping
    is a one-time normalization in extract_headings.
    """
    from validators import extract_headings
    body_with_numbers = "\n".join(f"## {i}. {s}" for i, s in enumerate(BODY_REQUIRED_SECTIONS, start=1))
    headings = extract_headings(body_with_numbers)
    # All required section names (lowercase, prefix-stripped) should be present.
    assert set(headings) == set(BODY_REQUIRED_SECTIONS), (
        f"numbered-prefix stripping failed; got: {headings}"
    )
    issues = validate_body_sections(headings)
    assert [i for i in issues if i["severity"] == "error"] == [], (
        f"validator rejected correctly-numbered headings: {issues}"
    )


# ---------------------------------------------------------------------------
# validate_task_packets mutations
# ---------------------------------------------------------------------------


def _base_packet() -> dict[str, str]:
    return {
        "id": "W-1",
        "goal": "do the thing",
        "in scope": "x",
        "out of scope": "y",
        "files / anchors": "x.ts",
        "acceptance": "tests pass",
        "falsifier": "if tests fail",
        "verification level required": "UNIT_TEST",
    }


@pytest.mark.parametrize("missing_field", TASK_PACKET_REQUIRED)
def test_packet_rejects_missing_each_required_field(missing_field):
    """Mutate: remove one task-packet sub-field."""
    pkt = _base_packet()
    del pkt[missing_field]
    issues = validate_task_packets([pkt])
    errors = [i for i in issues if i["severity"] == "error"]
    assert any(missing_field in i["field"] for i in errors), (
        f"validate_task_packets did not catch missing field {missing_field!r}"
    )


@pytest.mark.parametrize("bad_level", ["GUESS", "manual", "tested", "live", "unit_test"])
def test_packet_rejects_bad_verification_level(bad_level):
    """Mutate: verification level to disallowed forms.

    Note: empty string is excluded — an empty value means the field is
    missing, which is caught by the required-field check, not the
    enum check. The enum check only fires on a non-empty but invalid value.
    """
    pkt = _base_packet()
    pkt["verification level required"] = bad_level
    issues = validate_task_packets([pkt])
    errors = [i for i in issues if i["severity"] == "error"]
    if bad_level.strip().upper() in {"STATIC_INSPECTION", "UNIT_TEST", "LIVE_BEHAVIOR"}:
        assert not any("verification" in i["field"] for i in errors), (
            f"{bad_level!r} should normalize to allowed"
        )
    else:
        assert any("verification" in i["field"] for i in errors), (
            f"expected rejection for verification level {bad_level!r}"
        )


@pytest.mark.parametrize("trivial", ["n/a", "none", "—", "-"])
def test_packet_warns_on_trivial_falsifier(trivial):
    """Mutate: falsifier to trivial placeholder. Should be a warning, not error."""
    pkt = _base_packet()
    pkt["falsifier"] = trivial
    issues = validate_task_packets([pkt])
    errors = [i for i in issues if i["severity"] == "error" and "falsifier" in i["field"]]
    warnings = [i for i in issues if i["severity"] == "warn" and "falsifier" in i["field"]]
    assert errors == [], f"trivial falsifier should not be an error: {errors}"
    assert len(warnings) == 1, f"expected exactly one warning, got: {warnings}"


def test_packet_accepts_real_falsifier():
    """Sanity: a real falsifier sentence is not flagged."""
    pkt = _base_packet()
    pkt["falsifier"] = "if the dispatcher cannot be simplified below 8 branches without behavior change"
    issues = validate_task_packets([pkt])
    falsifier_issues = [i for i in issues if "falsifier" in i["field"]]
    assert falsifier_issues == []


# ---------------------------------------------------------------------------
# validate_verbatim_message mutations
# ---------------------------------------------------------------------------


def test_verbatim_rejects_no_quote_block():
    """Mutate: section present but no blockquote."""
    body = "## Last user message (verbatim)\n\nSome prose without a quote."
    issues = validate_verbatim_message(body)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("verbatim" in i["field"] for i in errors)


def test_verbatim_rejects_empty_quote():
    """Mutate: blockquote present but empty."""
    body = "## Last user message (verbatim)\n\n> "
    issues = validate_verbatim_message(body)
    errors = [i for i in issues if i["severity"] == "error"]
    assert any("verbatim" in i["field"] for i in errors)


def test_verbatim_warns_on_short_quote():
    """Mutate: blockquote present but suspiciously short (<5 chars)."""
    body = "## Last user message (verbatim)\n\n> hi"
    issues = validate_verbatim_message(body)
    warnings = [i for i in issues if i["severity"] == "warn"]
    assert any("short" in i["message"].lower() for i in warnings)


def test_verbatim_accepts_real_quote():
    """Sanity: a normal-length quoted message passes."""
    body = "## Last user message (verbatim)\n\n> can you simplify the widget dispatcher?"
    issues = validate_verbatim_message(body)
    assert issues == []


def test_verbatim_section_absent_is_silent():
    """If the section is absent, this validator returns no issues.

    (The mandatory-section check elsewhere catches the missing section;
    this validator should not double-report.)
    """
    body = "## Some other section\n\ncontent"
    issues = validate_verbatim_message(body)
    assert issues == []


# ---------------------------------------------------------------------------
# validate_streams_section_format mutations
# ---------------------------------------------------------------------------


def test_streams_section_absent_is_silent():
    """No 'Other outstanding streams' section -> validator returns []."""
    body = "## Some other section\n\ncontent"
    issues = validate_streams_section_format(body)
    assert issues == []


def test_streams_section_empty_warns():
    """Mutate: section present but no bullets."""
    body = "## Other outstanding streams\n\nSome prose without bullets."
    issues = validate_streams_section_format(body)
    warnings = [i for i in issues if i["severity"] == "warn"]
    assert any("no bullets" in i["message"].lower() for i in warnings)


def test_streams_section_bullet_without_status_warns():
    """Mutate: bullet exists but lacks Open/Closed marker."""
    body = "## Other outstanding streams\n\n- **widget-refactor** — some work here"
    issues = validate_streams_section_format(body)
    warnings = [i for i in issues if i["severity"] == "warn"]
    assert any("open" in i["message"].lower() or "closed" in i["message"].lower() for i in warnings)


def test_streams_section_bullet_with_open_status_passes():
    """Sanity: bullet with 'open' marker is accepted."""
    body = "## Other outstanding streams\n\n- **widget-refactor** — some work. OPEN."
    issues = validate_streams_section_format(body)
    assert issues == []


def test_streams_section_bullet_with_closed_status_passes():
    """Sanity: bullet with 'closed' marker is accepted."""
    body = "## Other outstanding streams\n\n- **widget-refactor** — done. CLOSED."
    issues = validate_streams_section_format(body)
    assert issues == []


# ---------------------------------------------------------------------------
# Integration: end-to-end mutation tests
# ---------------------------------------------------------------------------


# A minimal valid handoff for integration mutation tests.
_INTEGRATION_BASE = """\
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

## Objective

Investigate X.

## Status

OPEN

## Producing context

- Date: 2026-07-20

## Read-first list

1. `file.ts`

## Verified facts

- [FACT] something

## Current state

Done.

## Task packets

### T-1: do it

- goal: do it
- in scope: x
- out of scope: y
- files / anchors: x.ts
- acceptance: pass
- falsifier: if fail
- verification level required: UNIT_TEST

## Open decisions

None.

## Hard constraints

- None

## Cross-reference couplings

- None identified.

## Explicit non-goals

- Nothing

## Resumption protocol

1. Read x.ts

## Suggested next invocation

`/go x`

## Last user message (verbatim)

> please do the thing

## Epistemic labels

- [FACT] x
"""


def test_integration_base_is_valid():
    """Sanity: the integration base handoff passes with zero errors."""
    issues = validate_handoff_text(_INTEGRATION_BASE)
    errors = [i for i in issues if i["severity"] == "error"]
    assert errors == [], f"integration base has errors: {errors}"


def test_integration_removing_any_required_section_is_caught():
    """End-to-end: removing any required body section produces an error.

    This catches the regression where a section is silently dropped by
    a future refactor.
    """
    for section_marker in [
        "## Objective",
        "## Status",
        "## Producing context",
        "## Read-first list",
        "## Verified facts",
        "## Current state",
        "## Task packets",
        "## Open decisions",
        "## Hard constraints",
        "## Cross-reference couplings",
        "## Explicit non-goals",
        "## Resumption protocol",
        "## Suggested next invocation",
        "## Last user message (verbatim)",
        "## Epistemic labels",
    ]:
        mutated = _INTEGRATION_BASE.replace(section_marker, "## Renamed")
        issues = validate_handoff_text(mutated)
        errors = [i for i in issues if i["severity"] == "error"]
        assert errors, f"section removal not caught: {section_marker!r}"


def test_integration_corrupting_header_field_is_caught():
    """End-to-end: corrupting any header field is caught somewhere."""
    mutations = [
        ("thread_id: 11111111-2222-3333-4444-555555555555", "thread_id: bad"),
        ("current_session_id: 66666666-7777-8888-9999-aaaaaaaaaaaa", "current_session_id: bad"),
        ("produced_at: 2026-07-20T12:34:56Z", "produced_at: yesterday"),
        ("status: open", "status: pending"),
        ("handoff_type: investigation", "handoff_type: other"),
        ("accurate_as_of_head: abc1234def5678", "accurate_as_of_head: "),
    ]
    for original, mutated_value in mutations:
        mutated = _INTEGRATION_BASE.replace(original, mutated_value)
        issues = validate_handoff_text(mutated)
        errors = [i for i in issues if i["severity"] == "error"]
        assert errors, f"header mutation not caught: {original!r} -> {mutated_value!r}"


def test_integration_removing_packet_subfield_is_caught():
    """End-to-end: removing a task packet sub-field is caught.

    Note: 'goal' is excluded because the packet parser inherits goal from
    the `### <id>: <goal>` heading line, so removing the goal bullet alone
    leaves goal populated. That is correct parser behavior.
    """
    for subfield in [
        "- in scope: x",
        "- out of scope: y",
        "- files / anchors: x.ts",
        "- acceptance: pass",
        "- falsifier: if fail",
        "- verification level required: UNIT_TEST",
    ]:
        mutated = _INTEGRATION_BASE.replace(subfield + "\n", "")
        issues = validate_handoff_text(mutated)
        errors = [i for i in issues if i["severity"] == "error"]
        assert errors, f"packet subfield removal not caught: {subfield!r}"
