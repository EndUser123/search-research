"""Tests for contract-preserving implementation enforcement.

Verifies:
1. CLAUDE.md has Contract-Preserving Implementation section with required principles
2. Stop_semantic_critic.py has contract-preserving criterion in software_rca
3. Stop_semantic_critic.py has contract-preserving criterion in general_diagnostic
4. Remediation templates push toward contract-preserving behavior
5. No /contract_fix skill exists (skill-based approach removed)
"""

import pathlib


def test_claude_md_has_contract_section():
    """CLAUDE.md has Contract-Preserving Implementation section with required principles."""
    claude_md = pathlib.Path("P:/.claude/CLAUDE.md").read_text()

    assert "Contract-Preserving Implementation" in claude_md
    assert "trusted vs hostile" in claude_md
    assert "classifications and invariants" in claude_md
    assert "What would make the fix wrong" in claude_md
    assert "One successful run proof of correctness" not in claude_md
    assert "Focused edge-case tests" in claude_md
    assert "contract_fix" not in claude_md


def test_claude_md_excludes_skill_reference():
    """CLAUDE.md does not reference removed /contract_fix skill."""
    claude_md = pathlib.Path("P:/.claude/CLAUDE.md").read_text()

    assert "/contract_fix" not in claude_md
    assert "supported by the" not in claude_md.lower() or "skill" not in claude_md.lower()


def test_software_rca_has_contract_criterion():
    """software_rca prompt includes contract-preserving criterion."""
    content = pathlib.Path("P:/.claude/hooks/Stop_semantic_critic.py").read_text()

    software_rca_start = content.index('"software_rca": """')
    remaining = content[software_rca_start + 20:]
    prompt_end = remaining.index('"""')
    software_rca_prompt = remaining[:prompt_end]

    assert "contract it preserves" in software_rca_prompt
    assert "patch the symptom" in software_rca_prompt


def test_general_diagnostic_has_contract_criterion():
    """general_diagnostic prompt includes contract-preserving criterion."""
    content = pathlib.Path("P:/.claude/hooks/Stop_semantic_critic.py").read_text()

    gen_start = content.index('"general_diagnostic": """')
    remaining = content[gen_start + 24:]
    prompt_end = remaining.index('"""')
    gen_prompt = remaining[:prompt_end]

    assert "contract it preserves" in gen_prompt
    assert "patch the symptom" in gen_prompt


def test_software_rca_remediation_is_contract_preserving():
    """software_rca remediation template pushes toward contract-preserving behavior."""
    content = pathlib.Path("P:/.claude/hooks/Stop_semantic_critic.py").read_text()

    assert '"software_rca": (' in content
    assert "contract" in content.lower()
    assert "focused tests" in content.lower()
    assert "edge cases" in content.lower()


def test_general_diagnostic_remediation_is_contract_preserving():
    """general_diagnostic remediation template pushes toward contract-preserving behavior."""
    content = pathlib.Path("P:/.claude/hooks/Stop_semantic_critic.py").read_text()

    assert '"general_diagnostic": (' in content
    assert "contract" in content.lower()
    assert "falsify" in content.lower()
    assert "edge cases" in content.lower()


def test_contract_fix_skill_removed():
    """contract_fix skill directory does not exist."""
    skill_dir = pathlib.Path("P:/.claude/skills/contract_fix")
    assert not skill_dir.exists()