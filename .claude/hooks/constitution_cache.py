#!/usr/bin/env python3
from __future__ import annotations

"""
Constitution Cache for Hooks

Loads constitutional rules from .claude/CLAUDE.md and constitution.md
using existing parsing logic, cached for process lifetime.

Self-contained rule pattern matching for constitutional enforcement.
"""
import functools
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConstitutionalRule:
    """A single constitutional rule."""
    rule_type: str  # MANDATORY, FORBIDDEN, ACCEPT, REQUIRE, AVOID
    category: str   # development, architecture, security, testing, general
    content: str
    source: str     # CLAUDE.md or constitution.md


# Rule patterns - handles discovery.py format AND CLAUDE.md emoji format
RULE_PATTERNS = [
    # Standard markdown bold format (from discovery.py)
    (r"\*\*MANDATORY\*\*:\s*(.+)", "MANDATORY"),
    (r"\*\*FORBIDDEN\*\*:\s*(.+)", "FORBIDDEN"),
    (r"\*\*ACCEPT\*\*:\s*(.+)", "ACCEPT"),
    (r"\*\*REQUIRE\*\*:\s*(.+)", "REQUIRE"),
    (r"\*\*AVOID\*\*:\s*(.+)", "AVOID"),
    (r"\*\*MUST\*\*:\s*(.+)", "MANDATORY"),
    (r"\*\*MUST NOT\*\*:\s*(.+)", "FORBIDDEN"),
    (r"\*\*SHOULD\*\*:\s*(.+)", "REQUIRE"),
    (r"\*\*SHOULD NOT\*\*:\s*(.+)", "AVOID"),
    (r"^-\s*\*\*MANDATORY\*\*:\s*(.+)$", "MANDATORY"),
    (r"^-\s*\*\*FORBIDDEN\*\*:\s*(.+)$", "FORBIDDEN"),
    (r"^-\s*\*\*ACCEPT\*\*:\s*(.+)$", "ACCEPT"),
    (r"^-\s*\*\*REQUIRE\*\*:\s*(.+)$", "REQUIRE"),
    (r"^-\s*\*\*AVOID\*\*:\s*(.+)$", "AVOID"),
]

# Emoji-based patterns (CLAUDE.md uses this format: - ❌ Do NOT ..., - ✅ ...)
EMOJI_PATTERNS = [
    (r"(?m)^- ❌.+?Do NOT (?:generate|create|suggest|implement) (.+?)(?:$|\.|\n)", "FORBIDDEN"),
    (r"(?m)^- ❌(.+)$", "FORBIDDEN"),
    (r"(?m)^- ✅.+?Should (.+)$", "REQUIRE"),
    (r"(?m)^- ✅(.+)$", "ACCEPT"),
]

# Section-based patterns (e.g., "**FORBIDDEN BEHAVIORS:**", "**DEPLOYMENT CONFUSION PATTERNS (PROHIBITED):**")
SECTION_PATTERNS = [
    ("**FORBIDDEN BEHAVIORS:**", "FORBIDDEN"),
    ("**REQUIRED BEHAVIORS:**", "REQUIRE"),
    ("**MANDATORY**", "MANDATORY"),
    ("**PROHIBITED**", "FORBIDDEN"),
    ("**PERMITTED**", "ACCEPT"),
]

# Bold header section patterns (e.g., "**DEPLOYMENT CONFUSION PATTERNS (PROHIBITED):**")
# Captures sections with markdown bold headers containing rule type keywords
# Note: The colon comes BEFORE the closing **, not after
BOLD_HEADER_PATTERNS = [
    (r"\*\*[^*]+\(PROHIBITED\):\*\*", "FORBIDDEN"),
    (r"\*\*[^*]+\(FORBIDDEN\):\*\*", "FORBIDDEN"),
    (r"\*\*[^*]+PROHIBITED[^*]*:\*\*", "FORBIDDEN"),
    (r"\*\*[^*]+\(PERMITTED\):\*\*", "ACCEPT"),
    (r"\*\*[^*]+\(REQUIRED\):\*\*", "REQUIRE"),
    (r"\*\*[^*]+\(MANDATORY\):\*\*", "MANDATORY"),
]


def _determine_category(rule_content: str) -> str:
    """Determine rule category from content (reused from discovery.py)."""
    content_lower = rule_content.lower()

    if any(kw in content_lower for kw in ['test', 'tdd', 'testing', 'spec']):
        return 'testing'
    elif any(kw in content_lower for kw in ['architect', 'design', 'structur', 'pattern']):
        return 'architecture'
    elif any(kw in content_lower for kw in ['security', 'auth', 'validat', 'sanitiz']):
        return 'security'
    elif any(kw in content_lower for kw in ['solo', 'individu', 'background', 'autonom']):
        return 'development'
    elif any(kw in content_lower for kw in ['document', 'comment', 'readme']):
        return 'documentation'
    elif any(kw in content_lower for kw in ['perform', 'optim', 'cach', 'speed']):
        return 'performance'

    return 'general'


def _parse_rules(content: str, source: str) -> list[ConstitutionalRule]:
    """Parse rules from content using both standard and emoji patterns."""
    rules = []

    # Try standard RULE_PATTERNS first
    for pattern, rule_type in RULE_PATTERNS:
        matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            rule_content = match.group(1).strip()
            if not rule_content or len(rule_content) < 3:
                continue
            rules.append(ConstitutionalRule(
                rule_type=rule_type,
                category=_determine_category(rule_content),
                content=rule_content,
                source=source
            ))

    # Try emoji patterns (for CLAUDE.md format)
    for pattern, rule_type in EMOJI_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            rule_content = match.group(1).strip()
            # Skip if too short or looks like noise
            if not rule_content or len(rule_content) < 5:
                continue
            # Clean up common artifacts
            rule_content = re.sub(r'^\s*[-•*]\s*', '', rule_content)
            # Skip if already captured
            if any(r.content == rule_content for r in rules):
                continue
            rules.append(ConstitutionalRule(
                rule_type=rule_type,
                category=_determine_category(rule_content),
                content=rule_content,
                source=source
            ))

    # Parse section-based rules (e.g., "#### Background Services (PROHIBITED)")
    # This captures bullets under prohibited/permitted sections
    lines = content.split('\n')
    current_section_type = None  # FORBIDDEN, PERMITTED, etc.

    for i, line in enumerate(lines):
        # Check for section headers like "#### Background Services (PROHIBITED)"
        section_match = re.search(r'####.+?\((PROHIBITED|PERMITTED|REQUIRED|MANDATORY)\)', line)
        if section_match:
            section_keyword = section_match.group(1)
            if section_keyword == 'PROHIBITED':
                current_section_type = 'FORBIDDEN'
            elif section_keyword == 'PERMITTED':
                current_section_type = 'ACCEPT'
            elif section_keyword == 'REQUIRED':
                current_section_type = 'REQUIRE'
            elif section_keyword == 'MANDATORY':
                current_section_type = 'MANDATORY'
            continue

        # Capture bullets under the current section
        if current_section_type and line.strip().startswith('- '):
            rule_content = line.strip()[2:].strip()  # Remove "- " prefix
            if rule_content and len(rule_content) > 5:
                # Skip if already captured
                if not any(r.content == rule_content for r in rules):
                    rules.append(ConstitutionalRule(
                        rule_type=current_section_type,
                        category=_determine_category(rule_content),
                        content=rule_content,
                        source=source
                    ))

        # Reset section type on empty lines or new headers
        if line.startswith('##') or line.startswith('#'):
            current_section_type = None

    # Parse bold header sections (e.g., "**DEPLOYMENT CONFUSION PATTERNS (PROHIBITED):**")
    # This handles CLAUDE.md sections with markdown bold headers
    lines = content.split('\n')
    current_section_type = None

    for i, line in enumerate(lines):
        # Check for bold header sections
        for pattern, rule_type in BOLD_HEADER_PATTERNS:
            match = re.search(pattern, line)
            if match:
                current_section_type = rule_type
                break
        else:
            # Check for subsection headers that might end the section
            if line.startswith('#') and not line.startswith('##'):
                current_section_type = None
                continue

        # Capture bullets under the current bold header section
        if current_section_type and line.strip().startswith('- '):
            bullet_text = line.strip()[2:].strip()  # Remove "- " prefix

            # Extract rule content from various bullet formats:
            # 1. "- **Bold text** description" -> extract bold part
            # 2. `- "quoted phrase" description` -> extract quoted part
            # 3. "- plain text" -> use as-is
            rule_content = None

            # Try to extract **bold** part
            bold_match = re.search(r'\*\*([^*]+)\*\*', bullet_text)
            if bold_match:
                rule_content = bold_match.group(1).strip()
            # Try to extract "quoted" part
            elif '"' in bullet_text:
                quoted_match = re.search(r'"([^"]+)"', bullet_text)
                if quoted_match:
                    rule_content = quoted_match.group(1).strip()
            # Use entire bullet text
            else:
                rule_content = bullet_text

            if rule_content and len(rule_content) > 3:
                # Clean up common artifacts
                rule_content = re.sub(r'\s+:\s*$', '', rule_content)  # Remove trailing colon
                # Skip if already captured
                if not any(r.content == rule_content for r in rules):
                    rules.append(ConstitutionalRule(
                        rule_type=current_section_type,
                        category=_determine_category(rule_content),
                        content=rule_content,
                        source=source
                    ))

    return rules


@functools.lru_cache(maxsize=1)
def load_constitution(project_root: str = "P:/") -> dict:
    """
    Load and cache constitution rules from both sources.

    First call: ~5-10ms (file I/O + parsing)
    Subsequent calls: ~0ms (cached)

    Args:
        project_root: Path to project root

    Returns:
        dict with:
            - 'all_rules': list[ConstitutionalRule]
            - 'by_type': dict[str, list[ConstitutionalRule]]
            - 'by_category': dict[str, list[ConstitutionalRule]]
            - 'by_source': dict[str, list[ConstitutionalRule]]
    """
    rules = []
    root_path = Path(project_root)

    # Load .claude/CLAUDE.md
    claude_path = root_path / ".claude" / "CLAUDE.md"
    if claude_path.exists():
        try:
            rules.extend(_parse_rules(
                claude_path.read_text(encoding='utf-8'),
                "CLAUDE.md"
            ))
        except Exception:
            # Fail gracefully - return empty rules if file can't be read
            pass

    # Load constitution.md (if exists)
    constitution_path = root_path / "constitution.md"
    if constitution_path.exists():
        try:
            rules.extend(_parse_rules(
                constitution_path.read_text(encoding='utf-8'),
                "constitution.md"
            ))
        except Exception:
            pass

    # Build indexes
    rule_types = ['MANDATORY', 'FORBIDDEN', 'ACCEPT', 'REQUIRE', 'AVOID']
    categories = ['development', 'architecture', 'testing', 'security', 'documentation', 'performance', 'general']
    sources = ['CLAUDE.md', 'constitution.md']

    return {
        'all_rules': rules,
        'by_type': {
            rt: [r for r in rules if r.rule_type == rt]
            for rt in rule_types
        },
        'by_category': {
            cat: [r for r in rules if r.category == cat]
            for cat in categories
        },
        'by_source': {
            src: [r for r in rules if r.source == src]
            for src in sources
        }
    }


# Convenience query functions
def get_mandatory(category: str | None = None, project_root: str = "P:/") -> list[str]:
    """Get MANDATORY rules, optionally filtered by category."""
    rules = load_constitution(project_root)['by_type']['MANDATORY']
    if category:
        rules = [r for r in rules if r.category == category]
    return [r.content for r in rules]


def get_forbidden(category: str | None = None, project_root: str = "P:/") -> list[str]:
    """Get FORBIDDEN rules, optionally filtered by category."""
    rules = load_constitution(project_root)['by_type']['FORBIDDEN']
    if category:
        rules = [r for r in rules if r.category == category]
    return [r.content for r in rules]


def get_required(category: str | None = None, project_root: str = "P:/") -> list[str]:
    """Get REQUIRE rules, optionally filtered by category."""
    rules = load_constitution(project_root)['by_type']['REQUIRE']
    if category:
        rules = [r for r in rules if r.category == category]
    return [r.content for r in rules]


def get_avoid(category: str | None = None, project_root: str = "P:/") -> list[str]:
    """Get AVOID rules, optionally filtered by category."""
    rules = load_constitution(project_root)['by_type']['AVOID']
    if category:
        rules = [r for r in rules if r.category == category]
    return [r.content for r in rules]


def get_by_category(category: str, project_root: str = "P:/") -> dict[str, list[str]]:
    """Get all rules for a category, grouped by type."""
    rules = load_constitution(project_root)['by_category'].get(category, [])
    return {
        'MANDATORY': [r.content for r in rules if r.rule_type == 'MANDATORY'],
        'FORBIDDEN': [r.content for r in rules if r.rule_type == 'FORBIDDEN'],
        'ACCEPT': [r.content for r in rules if r.rule_type == 'ACCEPT'],
        'REQUIRE': [r.content for r in rules if r.rule_type == 'REQUIRE'],
        'AVOID': [r.content for r in rules if r.rule_type == 'AVOID'],
    }


def find_rules(keyword: str, project_root: str = "P:/") -> list[ConstitutionalRule]:
    """Find rules containing a keyword (case-insensitive)."""
    all_rules = load_constitution(project_root)['all_rules']
    keyword_lower = keyword.lower()
    return [r for r in all_rules if keyword_lower in r.content.lower()]


def clear_cache() -> None:
    """Clear the constitution cache (useful for testing)."""
    load_constitution.cache_clear()


# CLI for testing
if __name__ == "__main__":
    import sys

    project_root = sys.argv[1] if len(sys.argv) > 1 else "P:/"

    # Test loading
    constitution = load_constitution(project_root)

    print("Constitution Cache Test")
    print("======================")
    print(f"Total rules: {len(constitution['all_rules'])}")
    print("By source:")
    for source, rules in constitution['by_source'].items():
        if rules:
            print(f"  {source}: {len(rules)} rules")
    print("\nBy type:")
    for rule_type, rules in constitution['by_type'].items():
        if rules:
            print(f"  {rule_type}: {len(rules)} rules")
    print("\nBy category:")
    for category, rules in constitution['by_category'].items():
        if rules:
            print(f"  {category}: {len(rules)} rules")

    # Test query functions
    print("\nSolo dev MANDATORY rules:")
    solo_rules = get_mandatory(category='development', project_root=project_root)
    for rule in solo_rules:
        print(f"  - {rule[:80]}...")
