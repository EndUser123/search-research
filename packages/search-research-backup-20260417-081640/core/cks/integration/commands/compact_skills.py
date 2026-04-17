#!/usr/bin/env python3
"""Compact skill files by replacing migrated sections with CKS references.

This script directly edits skill files to replace bulk content with compact
CKS query references.
"""

import re
from pathlib import Path

SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"


# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent


def compact_testing_skills() -> None:
    """Compact testing-skills by replacing procedural content with CKS references."""
    skill_file = SKILLS_DIR / "testing-skills" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")

    # Find Action Protocol section and everything after it until Integration
    # Replace with CKS reference
    pattern = r"(## Action Protocol.*?)(?=\n## Integration with Constitution)"
    replacement = """## CKS: Extended Reference Documentation

**Detailed procedural documentation is stored in CKS.** Use `/cks` to query:

- **Action Protocol**: `/cks "testing-skills: Action Protocol"`
- **Test Report Template**: `/cks "testing-skills: Test Report Template"`
- **Common Failure Modes**: `/cks "testing-skills: Common Failure Modes"`
- **Quality Levels**: `/cks "testing-skills: Quality Levels"`
- **Pre-Deployment Checklist**: `/cks "testing-skills: Pre-Deployment Checklist"`
- **Testing Commands**: `/cks "testing-skills: Testing Commands"`

"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    skill_file.write_text(new_content, encoding="utf-8")

    # Print stats
    original_lines = len(content.split("\n"))
    new_lines = len(new_content.split("\n"))
    print(
        f"testing-skills: {original_lines} -> {new_lines} lines ({100*(1-new_lines/original_lines):.1f}% reduction)"
    )


def compact_sharing_skills() -> None:
    """Compact sharing-skills by replacing procedural content with CKS references."""
    skill_file = SKILLS_DIR / "sharing-skills" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")

    # Replace from Low-Friction Protocol to Common Scenarios
    pattern = r"(## Low-Friction Protocol.*?)(?=\n## Integration with Constitution)"
    replacement = """## CKS: Extended Reference Documentation

**Detailed procedural documentation is stored in CKS.** Use `/cks` to query:

- **Low-Friction Protocol**: `/cks "sharing-skills: Low-Friction Protocol (Personal Skills)"`
- **PR Workflow**: `/cks "sharing-skills: PR Workflow"`
- **PR Description Template**: `/cks "sharing-skills: PR Description Template"`
- **Branch Naming Conventions**: `/cks "sharing-skills: Branch Naming Conventions"`
- **Commit Message Conventions**: `/cks "sharing-skills: Commit Message Conventions"`
- **Pre-Sharing Checklist**: `/cks "sharing-skills: Pre-Sharing Checklist"`
- **Common Scenarios**: `/cks "sharing-skills: Common Scenarios"`

"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    skill_file.write_text(new_content, encoding="utf-8")

    original_lines = len(content.split("\n"))
    new_lines = len(new_content.split("\n"))
    print(
        f"sharing-skills: {original_lines} -> {new_lines} lines ({100*(1-new_lines/original_lines):.1f}% reduction)"
    )


def compact_writing_skills() -> None:
    """Compact writing-skills by replacing procedural content with CKS references."""
    skill_file = SKILLS_DIR / "writing-skills" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")

    # Replace from SKILL.md Template to Low-Friction Protocol
    # Note: writing-skills has nested sections that need careful handling
    # For now, replace key bulk sections

    # Replace SKILL.md Template section (big chunk)
    pattern1 = r"(## SKILL.md Template.*?)(?=\n## Lesson Routing)"
    replacement1 = """## CKS: Extended Reference Documentation

**Detailed procedural documentation is stored in CKS.** Use `/cks` to query:

- **SKILL.md Template**: `/cks "writing-skills: SKILL.md Template"`
- **Skill Writing Checklist**: `/cks "writing-skills: Skill Writing Checklist"`
- **Skill Name Conventions**: `/cks "writing-skills: Skill Name Conventions"`
- **Description Guidelines**: `/cks "writing-skills: Description Guidelines"`
- **Activation Trigger Quality**: `/cks "writing-skills: Activation Trigger Quality"`
- **Constitutional Integration**: `/cks "writing-skills: Constitutional Integration"`
- **Neural Cache Format**: `/cks "writing-skills: Neural Cache Format"`
- **Skill Quality Gates**: `/cks "writing-skills: Skill Quality Gates"`
- **Common Anti-Patterns**: `/cks "writing-skills: Common Anti-Patterns"`
- **Testing a New Skill**: `/cks "writing-skills: Testing a New Skill"`

"""

    new_content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
    skill_file.write_text(new_content, encoding="utf-8")

    original_lines = len(content.split("\n"))
    new_lines = len(new_content.split("\n"))
    print(
        f"writing-skills: {original_lines} -> {new_lines} lines ({100*(1-new_lines/original_lines):.1f}% reduction)"
    )


def compact_session_handoff() -> None:
    """Compact session-handoff by replacing procedural content with CKS references."""
    skill_file = SKILLS_DIR / "session-handoff" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")

    # Replace from Context Transfer Methods to When to Use This Skill
    pattern = r"(## Context Transfer Methods.*?)(?=\n## When to Use This Skill)"
    replacement = """## CKS: Extended Reference Documentation

**Detailed procedural documentation is stored in CKS.** Use `/cks` to query:

- **Context Transfer Methods**: `/cks "session-handoff: Context Transfer Methods"`
- **Handoff Triggers**: `/cks "session-handoff: Handoff Triggers"`
- **Common Patterns**: `/cks "session-handoff: Common Patterns"`
- **Continuity Anti-Patterns**: `/cks "session-handoff: Continuity Anti-Patterns"`
- **Quick Reference Commands**: `/cks "session-handoff: Quick Reference Commands"`

"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    skill_file.write_text(new_content, encoding="utf-8")

    original_lines = len(content.split("\n"))
    new_lines = len(new_content.split("\n"))
    print(
        f"session-handoff: {original_lines} -> {new_lines} lines ({100*(1-new_lines/original_lines):.1f}% reduction)"
    )


def compact_architecture_decision_framework() -> None:
    """Compact architecture-decision-framework by replacing procedural content with CKS references."""
    skill_file = SKILLS_DIR / "architecture-decision-framework" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")

    # Replace from Step 1 to Examples
    pattern = r"(## Step 1 — Clarify the proposal.*?)(?=\n## Examples)"
    replacement = """## CKS: Extended Reference Documentation

**Detailed decision framework documentation is stored in CKS.** Use `/cks` to query:

- **Step 1**: `/cks "architecture-decision-framework: Step 1 — Clarify the proposal"`
- **Step 2**: `/cks "architecture-decision-framework: Step 2 — Problem check (ENHANCED)"`
- **Step 2.5**: `/cks "architecture-decision-framework: Step 2.5 — Constitutional Impact Analysis (NEW)"`
- **Step 3**: `/cks "architecture-decision-framework: Step 3 — Simpler alternative"`
- **Step 4**: `/cks "architecture-decision-framework: Step 4 — Complexity tax"`
- **Step 5**: `/cks "architecture-decision-framework: Step 5 — Boundary stability"`
- **Step 6**: `/cks "architecture-decision-framework: Step 6 — Stop signals (ENHANCED)"`
- **Step 7**: `/cks "architecture-decision-framework: Step 7 — Output (significant changes only)"`
- **Step 7.5**: `/cks "architecture-decision-framework: Step 7.5 — Value Completeness Check (Anti-Satisficing Gate)"`
- **Step 8**: `/cks "architecture-decision-framework: Step 8 — Execution Handoff"`
- **Examples**: `/cks "architecture-decision-framework: Examples"`
- **Quick Decision Tree**: `/cks "architecture-decision-framework: Quick Decision Tree (ENHANCED)"`

"""

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    skill_file.write_text(new_content, encoding="utf-8")

    original_lines = len(content.split("\n"))
    new_lines = len(new_content.split("\n"))
    print(
        f"architecture-decision-framework: {original_lines} -> {new_lines} lines ({100*(1-new_lines/original_lines):.1f}% reduction)"
    )


def main() -> None:
    """Compact all migrated skill files."""
    print("Compacting skill files...\n")

    compact_testing_skills()
    compact_sharing_skills()
    compact_writing_skills()
    compact_session_handoff()
    compact_architecture_decision_framework()

    print("\nDone! Content migrated to CKS and skill files compacted.")


if __name__ == "__main__":
    main()
