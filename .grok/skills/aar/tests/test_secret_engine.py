"""Phase 2 behavioural tests for the shared secret-matching engine.

Verifies:
- user-pasted sk-... credential detected (the C04 gap)
- tool-result credential detected
- assistant repetition detected
- redacted placeholders suppressed
- task_id and non-secret fixture strings NOT flagged
- duplicate secrets deduplicated
- output never contains the full credential value

Per spec: "Use synthetic credentials in tests. Never copy any of the 14
live values discovered in the Grok transcript." All test credentials below
are synthetic and use the sk-test* prefix that the engine suppresses by
default — but we also use non-suppressed synthetic forms for positive tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "__lib"))

import pytest

from secret_engine import (
    SECRET_PATTERN,
    SecretSource,
    ScanResult,
    scan_assistant_content,
    scan_file_diff,
    scan_text,
    scan_tool_call_args,
    scan_tool_result,
    scan_user_content,
    scan_many,
)
from detectors import (
    ALL_DETECTORS,
    detect_tool_result_secret_exposure,
    detect_user_paste_secret_warning,
    detect_secret_exposure,  # backward-compat alias
)
from event_model import Event, Role, ToolCall


# Synthetic test credentials. None of these are real.
# Real patterns use enough length to be a plausible credential; the engine
# does not know they are synthetic unless they hit the placeholder regex.
SYN_SK = "sk-abcd1234efgh5678ijkl9012mnop3456"  # 36 chars after sk-
SYN_AKIA = "AKIAIOSFODNN7EXAMPLE"  # AWS example format
SYN_GHP = "ghp_" + "a" * 36
SYN_BEARER = "Bearer " + "b" * 30


# ---------------------------------------------------------------------------
# Adapter source-classification tests
# ---------------------------------------------------------------------------


def test_user_content_finding_is_user_pasted():
    """The C04 gap: a user-pasted credential must be classified USER_PASTED."""
    text = f"my config has api_key = {SYN_SK}"
    result = scan_user_content(text, event_index=5)
    assert len(result.findings) >= 1
    f = result.findings[0]
    assert f.source_kind is SecretSource.USER_PASTED
    assert f.event_index == 5
    assert f.event_role == "user"


def test_tool_result_finding_is_tool_returned():
    text = f"cat .env\nAPI_KEY={SYN_SK}"
    result = scan_tool_result(text, event_index=10)
    assert len(result.findings) >= 1
    assert result.findings[0].source_kind is SecretSource.TOOL_RETURNED


def test_assistant_content_finding_is_assistant_repeated():
    text = f"I see your token is {SYN_SK}, let me use it"
    result = scan_assistant_content(text, event_index=7)
    assert len(result.findings) >= 1
    assert result.findings[0].source_kind is SecretSource.ASSISTANT_REPEATED


def test_tool_call_args_write_is_written_to_file():
    """When write_tool=True, the source classification is WRITTEN_TO_FILE."""
    text = f'{{"content": "API_KEY={SYN_SK}"}}'
    result = scan_tool_call_args(text, event_index=3, write_tool=True)
    assert len(result.findings) >= 1
    assert result.findings[0].source_kind is SecretSource.WRITTEN_TO_FILE


def test_tool_call_args_read_is_source_insufficient():
    """When write_tool=False, the source classification is SOURCE_INSUFFICIENT."""
    text = f'{{"path": "/etc/secrets/{SYN_SK}"}}'
    result = scan_tool_call_args(text, event_index=3, write_tool=False)
    assert len(result.findings) >= 1
    assert result.findings[0].source_kind is SecretSource.SOURCE_INSUFFICIENT


def test_file_diff_is_written_to_file():
    text = f"+API_KEY={SYN_SK}"
    result = scan_file_diff(text, event_index=12)
    assert len(result.findings) >= 1
    assert result.findings[0].source_kind is SecretSource.WRITTEN_TO_FILE


# ---------------------------------------------------------------------------
# Placeholder suppression
# ---------------------------------------------------------------------------


def test_redacted_placeholder_suppressed():
    """Placeholders like sk-test..., YOUR_API_KEY, EXAMPLE_KEY do not fire."""
    placeholders = [
        "sk-testabcdefghijklmnop",
        "sk-exampleabcdefghijklmnop",
        "sk-placeholderabcdefghijklmnop",
        "YOUR_API_KEY",
        "EXAMPLE_KEY here",
        "TEST_KEY value",
        "AKIATESTEXAMPLE123",
    ]
    for p in placeholders:
        result = scan_user_content(p)
        assert result.findings == [], f"placeholder {p!r} should be suppressed"


def test_task_id_not_flagged():
    """task_id strings like 'call_abc123...' are not credentials."""
    task_ids = [
        "call_abc123def456",
        "call_019f7568acad76939ab023c57609045a",
        "task_id=call_1234567890abcdef",
    ]
    for tid in task_ids:
        result = scan_tool_result(tid)
        assert result.findings == [], f"task_id {tid!r} should not be flagged"


def test_non_secret_sk_fixture_string_not_flagged():
    """Strings that happen to start with 'sk-' but are too short are not flagged."""
    short_sks = [
        "sk-short",                # too short
        "sk-1234567890",           # 10 chars after sk-, below 20 threshold
        "sk-ten_chars",            # under 20
    ]
    for s in short_sks:
        result = scan_user_content(s)
        assert result.findings == [], f"short string {s!r} should not be flagged"


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def test_duplicate_secrets_deduplicated():
    """When the same secret appears multiple times in the same source,
    deduplicated returns one entry per unique fingerprint."""
    text = f"key1={SYN_SK}\nkey2={SYN_SK}\nkey3={SYN_SK}"
    result = scan_user_content(text, event_index=1)
    assert len(result.findings) == 3  # all three occurrences
    deduped = result.deduplicated
    assert len(deduped) == 1  # but only one unique fingerprint
    assert deduped[0].kind == result.findings[0].kind


def test_scan_many_deduplicates_across_sources():
    """scan_many combines findings from multiple sources and deduplicates."""
    items = [
        (f"user paste {SYN_SK}", SecretSource.USER_PASTED, 1, "user"),
        (f"tool returned {SYN_SK}", SecretSource.TOOL_RETURNED, 2, "tool_result"),
        (f"assistant repeated {SYN_SK}", SecretSource.ASSISTANT_REPEATED, 3, "assistant"),
    ]
    combined = scan_many(items)
    # All three findings have the same fingerprint (same secret value),
    # but different source_kind. deduplicated collapses by (kind, fingerprint)
    # so all three remain (different kind classifications).
    fingerprints = {(f.kind, f.fingerprint) for f in combined.deduplicated}
    assert len(fingerprints) == 1  # same secret across all three


# ---------------------------------------------------------------------------
# Non-leaking guarantee
# ---------------------------------------------------------------------------


def test_output_never_contains_full_credential():
    """The full secret value must NEVER appear in any finding field."""
    text = f"my key is {SYN_SK} here"
    result = scan_user_content(text)
    assert len(result.findings) >= 1
    for f in result.findings:
        # Check all str fields on the finding
        assert SYN_SK not in f.fingerprint
        assert SYN_SK not in f.kind
        assert SYN_SK not in str(f.source_kind)
        assert SYN_SK not in str(f.event_index)
        assert SYN_SK not in str(f.event_role)


def test_fingerprint_is_redacted():
    """Fingerprint format must be redacted: <kind>:<first4>…<last2>#<digest>."""
    text = f"key={SYN_SK}"
    result = scan_user_content(text)
    assert len(result.findings) >= 1
    fp = result.findings[0].fingerprint
    # Must not contain the middle of the credential
    middle = SYN_SK[5:-3]
    assert middle not in fp
    # Must contain the kind prefix
    assert "SK_OPENAI:" in fp or "GENERIC_KEY:" in fp
    # Must end with a sha256-prefix-8 (8 hex chars after #)
    assert "#"[0] in fp
    after_hash = fp.split("#")[-1] if "#" in fp else ""
    assert len(after_hash) == 8, f"sha256 prefix should be 8 chars, got {after_hash!r}"


# ---------------------------------------------------------------------------
# Detector integration
# ---------------------------------------------------------------------------


def test_detect_user_paste_secret_warning_fires_on_user_message():
    """C04 gap fix: the new detector fires on user-pasted credentials."""
    events = [
        Event(index=0, role=Role.USER, text=f"here is my config with key {SYN_SK}"),
        Event(index=1, role=Role.ASSISTANT, text="thanks"),
    ]
    signals = detect_user_paste_secret_warning(events)
    assert len(signals) >= 1
    s = signals[0]
    assert "USER_PASTED" in s.detail or "user message contains credential" in s.detail
    # The full secret must NOT appear in the signal detail
    assert SYN_SK not in s.detail


def test_detect_user_paste_secret_warning_skips_synthetic_reason():
    """Harness-injected user content (synthetic_reason) does not fire."""
    events = [
        Event(
            index=0, role=Role.USER, text=f"compaction meta {SYN_SK}",
            synthetic_reason="compaction_meta",
        ),
    ]
    signals = detect_user_paste_secret_warning(events)
    assert signals == []


def test_detect_tool_result_secret_exposure_still_works():
    """The renamed detector still catches tool_result credentials."""
    events = [
        Event(index=0, role=Role.TOOL_RESULT, text=f"output: API_KEY={SYN_SK}"),
    ]
    signals = detect_tool_result_secret_exposure(events)
    assert len(signals) >= 1
    assert SYN_SK not in signals[0].detail


def test_backward_compat_alias_works():
    """detect_secret_exposure (alias) still works and points to the renamed detector."""
    events = [
        Event(index=0, role=Role.TOOL_RESULT, text=f"API_KEY={SYN_SK}"),
    ]
    via_alias = detect_secret_exposure(events)
    via_canonical = detect_tool_result_secret_exposure(events)
    assert via_alias == via_canonical


def test_both_secret_detectors_registered():
    """Both renamed + new detectors are in ALL_DETECTORS."""
    names = {d.__name__ for d in ALL_DETECTORS}
    assert "detect_tool_result_secret_exposure" in names
    assert "detect_user_paste_secret_warning" in names


# ---------------------------------------------------------------------------
# Cross-source provenance
# ---------------------------------------------------------------------------


def test_findings_distinguish_source_kinds():
    """A credential in user content vs tool_result vs assistant text must
    carry distinct source_kind classifications."""
    events = [
        Event(index=0, role=Role.USER, text=f"user {SYN_SK}"),
        Event(index=1, role=Role.TOOL_RESULT, text=f"tool {SYN_SK}"),
        Event(index=2, role=Role.ASSISTANT, text=f"assistant {SYN_SK}"),
    ]
    user_sigs = detect_user_paste_secret_warning(events)
    tool_sigs = detect_tool_result_secret_exposure(events)
    assert len(user_sigs) == 1
    assert len(tool_sigs) == 1
    assert "USER_PASTED" in user_sigs[0].detail
    assert "TOOL_RETURNED" in tool_sigs[0].detail
    # The two signals have different event_indices (0 vs 1)
    assert user_sigs[0].event_indices == (0,)
    assert tool_sigs[0].event_indices == (1,)
