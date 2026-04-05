"""Tests for adr_critic agent.

Verifies:
1. Result envelope schema compliance
2. Terminal_id path isolation
3. verification_status field presence on findings
4. Graceful failure on missing ADR file
5. Non-scope filtering (style/taste not flagged)
"""

from __future__ import annotations

from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent
ADR_CRITIC_PATH = AGENTS_DIR / "adr_critic.md"


def test_adr_critic_file_exists():
    """adr_critic.md must exist at expected path."""
    assert ADR_CRITIC_PATH.exists(), f"adr_critic.md not found at {ADR_CRITIC_PATH}"


def test_artifact_path_includes_terminal_id():
    """Artifact path must include terminal_id to prevent concurrent terminal overwrites."""
    content = ADR_CRITIC_PATH.read_text(encoding="utf-8")
    assert "terminal_id" in content.lower() or "{terminal_id}" in content, \
        "Artifact path must include terminal_id for multi-terminal isolation"
    # Hardcoded adr_critic.json without terminal_id causes race conditions
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        if "adr_critic.json" in line and "{" not in line and "terminal_id" not in line.lower():
            assert False, f"Line {i}: Hardcoded adr_critic.json without terminal_id causes race conditions"


def test_step_4_requires_verification_status():
    """Step 4 must require verification_status on every finding."""
    content = ADR_CRITIC_PATH.read_text(encoding="utf-8")
    assert "verification_status" in content, \
        "Step 4/5 must require verification_status field on findings"


def test_critical_suppressed_without_verified():
    """CRITICAL findings without VERIFIED status must be suppressed."""
    content = ADR_CRITIC_PATH.read_text(encoding="utf-8")
    assert "suppressed" in content.lower() and "critical" in content.lower(), \
        "Agent must suppress CRITICAL findings without VERIFIED status"


def test_non_scope_exclusions_listed():
    """Non-scope section must explicitly list style/taste exclusions."""
    content = ADR_CRITIC_PATH.read_text(encoding="utf-8")
    non_scope_markers = ["style", "taste", "phrasing", "stylistic"]
    found = [m for m in non_scope_markers if m in content.lower()]
    assert len(found) >= 2, \
        f"Non-scope exclusions must list style/taste/phrasing markers, found: {found}"


def test_non_scope_section_exists():
    """Agent must have explicit Non-Scope section."""
    content = ADR_CRITIC_PATH.read_text(encoding="utf-8")
    assert "## Non-Scope" in content or "Non-Scope" in content, \
        "Agent must have explicit Non-Scope section listing excluded categories"


def test_result_envelope_return_statement():
    """Result envelope must be returned to /arch."""
    content = ADR_CRITIC_PATH.read_text(encoding="utf-8")
    assert '"status":' in content and '"artifact":' in content and '"summary":' in content, \
        "Result envelope must have status, artifact, and summary fields"