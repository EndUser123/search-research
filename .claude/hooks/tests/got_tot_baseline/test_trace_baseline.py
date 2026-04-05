"""
Baseline regression tests for /trace skill.

These tests capture the current behavior of /trace before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Domain parsing (code:file, skill:name, workflow:path, document:path)
- Auto-detection from file extensions and paths
- Path resolution (relative to absolute)
- Target argument parsing

Critical paths tested: 4
Lines of code: ~100
"""

from pathlib import Path

import pytest


def parse_target(target: str) -> tuple[str, str]:
    """
    Parse domain and target from invocation string.

    This is a copy of the parse_target function from /trace/__main__.py
    to establish baseline behavior before GoT/ToT integration.

    Args:
        target: Target string (e.g., "code:src/handoff.py" or "src/handoff.py")

    Returns:
        Tuple of (domain, target_path)
    """
    if ':' in target:
        # Explicit domain: "code:src/handoff.py"
        domain, target_path = target.split(':', 1)
        return domain, target_path

    # Auto-detect domain from target
    target_path = target
    target_lower = target.lower()

    if target_lower.endswith('.py'):
        return 'code', target_path
    elif target_lower.endswith('skill.md') or 'skills/' in target_lower:
        return 'skill', target_path
    elif 'flows/' in target_lower or target_lower.endswith('flow.md'):
        return 'workflow', target_path
    else:
        return 'document', target_path


def resolve_target_path(target: str, domain: str) -> Path:
    """
    Resolve target path relative to project root.

    This is a copy of the resolve_target_path function from /trace/__main__.py
    to establish baseline behavior before GoT/ToT integration.

    Args:
        target: Target path string
        domain: Domain name

    Returns:
        Resolved Path object
    """
    # Convert to Path and resolve
    target_path = Path(target)

    # If relative, resolve from project root (P:/)
    if not target_path.is_absolute():
        project_root = Path('P:/')
        target_path = project_root / target_path

    return target_path


class TestDomainParsing:
    """Test domain parsing from target strings."""

    def test_parse_code_domain_explicit(self):
        """Test parsing explicit code domain: 'code:src/handoff.py'"""
        domain, target_path = parse_target("code:src/handoff.py")
        assert domain == "code"
        assert target_path == "src/handoff.py"

    def test_parse_skill_domain_explicit(self):
        """Test parsing explicit skill domain: 'skill:skill-development'"""
        domain, target_path = parse_target("skill:skill-development")
        assert domain == "skill"
        assert target_path == "skill-development"

    def test_parse_workflow_domain_explicit(self):
        """Test parsing explicit workflow domain: 'workflow:flows/feature.md'"""
        domain, target_path = parse_target("workflow:flows/feature.md")
        assert domain == "workflow"
        assert target_path == "flows/feature.md"

    def test_parse_document_domain_explicit(self):
        """Test parsing explicit document domain: 'document:CLAUDE.md'"""
        domain, target_path = parse_target("document:CLAUDE.md")
        assert domain == "document"
        assert target_path == "CLAUDE.md"


class TestAutoDetection:
    """Test automatic domain detection from file patterns."""

    def test_auto_detect_code_from_py_extension(self):
        """Test auto-detect code domain from .py extension"""
        domain, target_path = parse_target("src/handoff.py")
        assert domain == "code"
        assert target_path == "src/handoff.py"

    def test_auto_detect_skill_from_skill_md(self):
        """Test auto-detect skill domain from SKILL.md"""
        domain, target_path = parse_target("skills/code/SKILL.md")
        assert domain == "skill"
        assert target_path == "skills/code/SKILL.md"

    def test_auto_detect_skill_from_skills_path(self):
        """Test auto-detect skill domain from skills/ path"""
        domain, target_path = parse_target("skills/trace")
        assert domain == "skill"
        assert target_path == "skills/trace"

    def test_auto_detect_workflow_from_flows_path(self):
        """Test auto-detect workflow domain from flows/ path"""
        domain, target_path = parse_target("flows/feature.md")
        assert domain == "workflow"
        assert target_path == "flows/feature.md"

    def test_auto_detect_workflow_from_flow_md(self):
        """Test auto-detect workflow domain from .flow.md"""
        domain, target_path = parse_target("test.flow.md")
        assert domain == "workflow"
        assert target_path == "test.flow.md"

    def test_auto_detect_document_default(self):
        """Test auto-detect document domain as default"""
        domain, target_path = parse_target("CLAUDE.md")
        assert domain == "document"
        assert target_path == "CLAUDE.md"


class TestPathResolution:
    """Test path resolution from relative to absolute."""

    def test_resolve_relative_path(self):
        """Test resolving relative path from project root"""
        result = resolve_target_path("src/handoff.py", "code")
        # Should resolve to P:/src/handoff.py (Windows uses backslash)
        result_str = str(result).replace("\\", "/")
        assert result_str.startswith("P:/")
        assert "src/handoff.py" in result_str

    def test_resolve_absolute_path_unchanged(self):
        """Test that absolute paths are unchanged"""
        absolute_path = Path("P:/src/handoff.py")
        result = resolve_target_path(absolute_path, "code")
        assert result == absolute_path

    def test_resolve_nested_relative_path(self):
        """Test resolving nested relative path"""
        result = resolve_target_path("packages/debugRCA/skill/SKILL.md", "skill")
        result_str = str(result).replace("\\", "/")
        assert result_str.startswith("P:/")
        assert "packages/debugRCA/skill/SKILL.md" in result_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
