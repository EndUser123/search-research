#!/usr/bin/env python3
"""Skill Migration to CKS - Migrate procedural skill content to searchable vector database.

Unlike Neural Cache (structured entries), skills have markdown sections that should be
chunked semantically for retrieval. This script handles section-based migration.

Usage:
    python -m cks.integration.commands.skill_migration --list
    python -m cks.integration.commands.skill_migration --dry-run --skill testing-skills
    python -m cks.integration.commands.skill_migration --migrate --skill testing-skills
    python -m cks.integration.commands.skill_migration --compact --skill testing-skills
"""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

# Path setup
# script is at: P:\\\\__csf/src/features/cks/integration/commands/skill_migration.py
# P:\\\\ root is 6 levels up
# skills are at P:\\\\.claude/skills
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent  # P:\\\\ root
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
# Main CKS database (1.2GB, where all queries happen)
CKS_DB_PATH = PROJECT_ROOT / "__csf" / "data" / "cks.db"


class SectionType(Enum):
    """Types of sections found in skills."""

    FRONTMATTER = "frontmatter"
    RESPONSE_FORMAT = "response_format"
    OBJECTIVE = "objective"
    ACTIVATION = "activation"
    ROLE = "role"
    PROTOCOL = "protocol"
    TEMPLATE = "template"
    CHECKLIST = "checklist"
    EXAMPLE = "example"
    PATTERN = "pattern"
    INTEGRATION = "integration"
    NEURAL_CACHE = "neural_cache"
    METADATA = "metadata"
    OTHER = "other"


@dataclass
class SkillSection:
    """A section of a skill file."""

    title: str
    content: str
    section_type: SectionType
    level: int = 1  # Heading level (1-6)
    line_start: int = 0
    line_end: int = 0


@dataclass
class MigrationStats:
    """Statistics for skill migration."""

    total_sections: int = 0
    migrated_sections: int = 0
    failed_sections: int = 0
    total_lines: int = 0
    kept_lines: int = 0
    migrated_lines: int = 0


@dataclass
class SkillConfig:
    """Configuration for migrating a specific skill."""

    name: str
    path: Path
    keep_sections: list[str] = field(default_factory=list)
    migrate_sections: list[str] = field(default_factory=list)
    description: str = ""

    @classmethod
    def for_skill(cls, skill_name: str, skills_dir: Path) -> "SkillConfig":
        """Get configuration for a specific skill."""
        # Try SKILL.md first, then skill.md
        skill_path = skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            skill_path = skills_dir / skill_name / "skill.md"

        configs = {
            "testing-skills": cls(
                name="testing-skills",
                path=skill_path,
                keep_sections=[
                    "Response Format",
                    "Objective",
                    "Activation Triggers",
                    "Role & Interaction Style",
                ],
                migrate_sections=[
                    "Action Protocol",
                    "Test Report Template",
                    "Common Failure Modes",
                    "Quality Levels",
                    "Pre-Deployment Checklist",
                    "Testing Commands",
                ],
                description="Quality gate for validating new skills",
            ),
            "sharing-skills": cls(
                name="sharing-skills",
                path=skill_path,
                keep_sections=[
                    "Response Format",
                    "Objective",
                    "Activation Triggers",
                    "Role & Interaction Style",
                ],
                migrate_sections=[
                    "Low-Friction Protocol",
                    "PR Workflow",
                    "PR Description Template",
                    "Branch Naming Conventions",
                    "Commit Message Conventions",
                    "Pre-Sharing Checklist",
                    "Common Scenarios",
                ],
                description="Automates skill upstreaming via GitHub PR",
            ),
            "writing-skills": cls(
                name="writing-skills",
                path=skill_path,
                keep_sections=[
                    "Response Format",
                    "Objective",
                    "Activation Triggers",
                    "CKS: Extended Reference Documentation",
                    "Lesson Routing",
                    "Status",
                ],
                migrate_sections=[
                    "Skill Writing Checklist",
                    "Skill Name Conventions",
                    "Description Guidelines",
                    "Activation Trigger Quality",
                    "Constitutional Integration",
                    "Neural Cache Format",
                    "Skill Quality Gates",
                    "Common Anti-Patterns",
                    "Testing a New Skill",
                    "Low-Friction Protocol",
                ],
                description="Meta-skill for writing SKILL.md files",
            ),
            "research_internal": cls(
                name="research_internal",
                path=skill_path,
                keep_sections=[
                    "When to Use",
                    "Quick Reference",
                    "Direct Execution",
                    "Command Location",
                ],
                migrate_sections=[
                    "Provider Selection Guide",
                    "Advanced Options",
                    "Auto Mode Selection",
                    "Query Expansion",
                    "HyDE Enhancement",
                    "Auto-Learning",
                    "ML Enhancements",
                    "Output Formats",
                    "GitHub Repository Search",
                    "URL Fetching",
                    "Examples by Use Case",
                    "Integration with CSF",
                    "Research Storage",
                    "API Keys Required",
                    "Constitutional Notes",
                    "Troubleshooting",
                ],
                description="Multi-source research with 10+ providers",
            ),
            "session-handoff": cls(
                name="session-handoff",
                path=skill_path,
                keep_sections=[
                    "Core Principles",
                    "Session Start Checklist",
                ],
                migrate_sections=[
                    "Context Transfer Methods",
                    "Handoff Triggers",
                    "Common Patterns",
                    "Continuity Anti-Patterns",
                    "Quick Reference Commands",
                ],
                description="Continuity across Claude Code sessions",
            ),
            "architecture-decision-framework": cls(
                name="architecture-decision-framework",
                path=skill_path,
                keep_sections=[
                    "Response Format",
                    "Objective",
                    "Step 0",
                ],
                migrate_sections=[
                    "Step 1",
                    "Step 2",
                    "Step 3",
                    "Step 4",
                    "Step 5",
                    "Step 6",
                    "Step 7",
                    "Step 8",
                    "Examples",
                    "Quick Decision Tree",
                ],
                description="Evaluate structural code changes before implementation",
            ),
        }

        return configs.get(skill_name, cls(name=skill_name, path=skill_path))


class SkillParser:
    """Parse skill files into sections."""

    def __init__(self, skill_path: Path) -> None:
        self.skill_path = skill_path
        self.content = ""
        self.sections: list[SkillSection] = []

    def parse(self) -> list[SkillSection]:
        """Parse the skill file into sections."""
        self.content = self.skill_path.read_text(encoding="utf-8")
        lines = self.content.split("\n")

        sections = []
        current_section = SkillSection(
            title="_frontmatter",
            content="",
            section_type=SectionType.FRONTMATTER,
            level=0,
            line_start=0,
        )

        for i, line in enumerate(lines):
            # Check for markdown headings
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Save previous section if it has content
                if current_section.title != "_frontmatter" and current_section.content.strip():
                    current_section.line_end = i
                    current_section.content = current_section.content.strip()
                    sections.append(current_section)
                elif current_section.title == "_frontmatter" and current_section.content.strip():
                    # Keep frontmatter
                    current_section.line_end = i
                    current_section.content = current_section.content.strip()
                    sections.append(current_section)

                # Start new section
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                section_type = self._classify_section(title)

                current_section = SkillSection(
                    title=title,
                    content="",
                    section_type=section_type,
                    level=level,
                    line_start=i + 1,
                )
            else:
                current_section.content += line + "\n"

        # Add last section
        current_section.line_end = len(lines)
        current_section.content = current_section.content.strip()
        if current_section.content:
            sections.append(current_section)

        self.sections = sections
        return sections

    def _classify_section(self, title: str) -> SectionType:
        """Classify a section by its title."""
        title_lower = title.lower()

        if "response format" in title_lower:
            return SectionType.RESPONSE_FORMAT
        if "objective" in title_lower:
            return SectionType.OBJECTIVE
        if "activation" in title_lower:
            return SectionType.ACTIVATION
        if "role" in title_lower or "interaction" in title_lower:
            return SectionType.ROLE
        if "protocol" in title_lower or "action" in title_lower:
            return SectionType.PROTOCOL
        if "template" in title_lower:
            return SectionType.TEMPLATE
        if "checklist" in title_lower:
            return SectionType.CHECKLIST
        if "example" in title_lower or "scenario" in title_lower:
            return SectionType.EXAMPLE
        if "pattern" in title_lower:
            return SectionType.PATTERN
        if "integration" in title_lower:
            return SectionType.INTEGRATION
        if "neural cache" in title_lower:
            return SectionType.NEURAL_CACHE
        if "status" in title_lower or "metadata" in title_lower:
            return SectionType.METADATA

        return SectionType.OTHER

    def get_stats(self) -> dict:
        """Get statistics about the parsed skill."""
        return {
            "total_sections": len(self.sections),
            "section_types": {
                st.name: sum(1 for s in self.sections if s.section_type == st) for st in SectionType
            },
            "total_lines": len(self.content.split("\n")),
        }


class SkillMigrator:
    """Migrate skill content to CKS using direct SQLite access."""

    def __init__(self, db_path: Path | None = None, dry_run: bool = False) -> None:
        self.db_path = db_path or CKS_DB_PATH
        self.dry_run = dry_run
        self.stats = MigrationStats()
        self._conn: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.db_path))
            self._ensure_schema()
        return self._conn

    def _ensure_schema(self) -> None:
        """Ensure CKS database schema exists."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Knowledge nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Vector nodes table for semantic search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_nodes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                vector_id TEXT UNIQUE,
                model_name TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes (schema uses 'type' not 'node_type', and title is in metadata)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type
            ON knowledge_nodes(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_metadata
            ON knowledge_nodes(metadata)
        """)

        conn.commit()

    def _generate_section_id(self, skill_name: str, section_title: str) -> str:
        """Generate unique section ID."""
        content = f"skill_{skill_name}_{section_title}"
        return f"skill_{hashlib.md5(content.encode()).hexdigest()[:16]}"

    def ingest_section(
        self,
        skill_name: str,
        section: SkillSection,
        config: SkillConfig,
    ) -> bool:
        """Ingest a single section into CKS."""
        if self.dry_run:
            print(f"  [DRY RUN] Would ingest: {skill_name} - {section.title}")
            return True

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            section_id = self._generate_section_id(skill_name, section.title)

            # Prepare metadata
            metadata = {
                "title": f"{skill_name}: {section.title}",
                "category": "skill_documentation",
                "source": f"skill:{skill_name}",
                "section_type": section.section_type.value,
                "skill_name": skill_name,
                "section_title": section.title,
                "ingestion_date": datetime.now().isoformat(),
            }

            # Prepare structured content
            structured_content = json.dumps(
                {
                    "title": section.title,
                    "content": section.content,
                    "section_type": section.section_type.value,
                    "skill_name": skill_name,
                }
            )

            # Insert knowledge node (schema: id, type, content, metadata, created_at, updated_at)
            # Title goes into metadata, not a separate column
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_nodes
                (id, type, content, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    section_id,
                    "skill_section",
                    structured_content,
                    json.dumps(metadata),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            print(f"  Error ingesting section '{section.title}': {e}")
            return False

    def migrate_skill(self, config: SkillConfig) -> MigrationStats:
        """Migrate a skill according to its configuration."""
        if not config.path.exists():
            print(f"Error: Skill file not found: {config.path}")
            return self.stats

        parser = SkillParser(config.path)
        sections = parser.parse()

        print(f"\n{'='*60}")
        print(f"Skill: {config.name}")
        print(f"Path: {config.path}")
        print(f"Description: {config.description}")
        print(f"Total sections: {len(sections)}")
        print(f"{'='*60}\n")

        for section in sections:
            self.stats.total_sections += 1
            section_lines = len(section.content.split("\n")) if section.content else 0
            self.stats.total_lines += section_lines

            # Skip frontmatter and metadata
            if section.section_type in (SectionType.FRONTMATTER, SectionType.METADATA):
                self.stats.kept_lines += section_lines
                print(f"  KEEP: {section.title} ({section.section_type.value})")
                continue

            # Check if section should be kept
            if any(keep in section.title for keep in config.keep_sections):
                self.stats.kept_lines += section_lines
                print(f"  KEEP: {section.title}")
                continue

            # Check if section should be migrated
            if any(migrate in section.title for migrate in config.migrate_sections):
                self.stats.migrated_lines += section_lines

                if self.ingest_section(config.name, section, config):
                    self.stats.migrated_sections += 1
                    print(f"  MIGRATE: {section.title} ({section_lines} lines)")
                else:
                    self.stats.failed_sections += 1
                continue

            # Default: keep
            self.stats.kept_lines += section_lines
            print(f"  KEEP (default): {section.title}")

        return self.stats

    def compact_skill(self, config: SkillConfig) -> bool:
        """Compact a skill file by replacing migrated sections with CKS references."""
        if not config.path.exists():
            print(f"Error: Skill file not found: {config.path}")
            return False

        parser = SkillParser(config.path)
        sections = parser.parse()

        new_lines = []
        cks_references = []

        for section in sections:
            # Keep frontmatter as-is
            if section.section_type == SectionType.FRONTMATTER:
                new_lines.extend(section.content.split("\n"))
                new_lines.append("")
                continue

            # Check if section should be kept
            if any(keep in section.title for keep in config.keep_sections):
                new_lines.append(f"{'#' * section.level} {section.title}")
                new_lines.append("")
                new_lines.extend(section.content.split("\n"))
                new_lines.append("")
                continue

            # Check if section should be migrated (add reference)
            if any(migrate in section.title for migrate in config.migrate_sections):
                cks_references.append(
                    f'- **{section.title}**: `/cks "{config.name}: {section.title}"`'
                )
                continue

            # Default: keep
            new_lines.append(f"{'#' * section.level} {section.title}")
            new_lines.append("")
            new_lines.extend(section.content.split("\n"))
            new_lines.append("")

        # Add CKS reference section
        if cks_references:
            new_lines.append("## CKS: Extended Reference Documentation")
            new_lines.append("")
            new_lines.append(
                "**Detailed procedural documentation is stored in CKS.** Use `/cks` to query:"
            )
            new_lines.append("")
            for ref in cks_references:
                new_lines.append(ref)
            new_lines.append("")

        # Add integration and metadata sections (kept from original)
        for section in sections:
            if section.section_type in (
                SectionType.INTEGRATION,
                SectionType.NEURAL_CACHE,
                SectionType.METADATA,
            ):
                new_lines.append(f"{'#' * section.level} {section.title}")
                new_lines.append("")
                new_lines.extend(section.content.split("\n"))
                new_lines.append("")

        # Write compacted content
        if not self.dry_run:
            config.path.write_text("\n".join(new_lines), encoding="utf-8")
            new_line_count = len(new_lines)
            reduction_pct = 100 * (1 - new_line_count / max(self.stats.total_lines, 1))
            print(f"\nCompacted {config.path}")
            print(f"  Original: {self.stats.total_lines} lines")
            print(f"  Compact: {new_line_count} lines")
            print(f"  Reduction: {reduction_pct:.1f}%")
        else:
            print(f"\n[DRY RUN] Would compact {config.path}")
            print(f"  Would keep: {self.stats.kept_lines} lines")
            print(f"  Would migrate: {self.stats.migrated_lines} lines")

        return True

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def list_skills(skills_dir: Path) -> None:
    """List all available skills with their sizes."""
    print("\nAvailable Skills for Migration:\n")
    print(f"{'Skill':<35} {'Lines':>8} {'KB':>8} {'Description'}")
    print("-" * 100)

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file = skill_dir / "skill.md"

        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            lines = len(content.split("\n"))
            size_kb = len(content.encode("utf-8")) / 1024

            # Extract description from frontmatter
            desc = ""
            for line in content.split("\n")[:20]:
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break

            print(f"{skill_dir.name:<35} {lines:>8} {size_kb:>7.1f} {desc[:40]}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate skill content to CKS vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list
  %(prog)s --dry-run --migrate --skill testing-skills
  %(prog)s --migrate --skill testing-skills
  %(prog)s --compact --skill testing-skills
  %(prog)s --migrate --compact --skill testing-skills
  %(prog)s --migrate --all
        """,
    )

    parser.add_argument("--list", action="store_true", help="List all available skills")
    parser.add_argument("--skill", help="Specific skill to migrate")
    parser.add_argument("--all", action="store_true", help="Migrate all configured skills")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without writing"
    )
    parser.add_argument("--migrate", action="store_true", help="Migrate skill content to CKS")
    parser.add_argument("--compact", action="store_true", help="Compact skill file after migration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.list:
        list_skills(SKILLS_DIR)
        return 0

    if not args.migrate and not args.dry_run and not args.compact:
        parser.print_help()
        return 0

    # Determine which skills to process
    skills_to_process = []
    if args.all:
        for skill_name in [
            "testing-skills",
            "sharing-skills",
            "writing-skills",
            "research_internal",
            "session-handoff",
            "architecture-decision-framework",
        ]:
            config = SkillConfig.for_skill(skill_name, SKILLS_DIR)
            if config.path.exists():
                skills_to_process.append(config)
    elif args.skill:
        config = SkillConfig.for_skill(args.skill, SKILLS_DIR)
        if config.path.exists():
            skills_to_process.append(config)
        else:
            print(f"Error: Skill '{args.skill}' not found at {config.path}")
            return 1

    with SkillMigrator(dry_run=args.dry_run or not args.migrate) as migrator:
        for config in skills_to_process:
            print(f"\n{'='*60}")
            print(f"Processing: {config.name}")
            print(f"{'='*60}")

            if args.migrate or args.dry_run:
                migrator.stats = MigrationStats()  # Reset for each skill
                migrator.migrate_skill(config)

                print(f"\n{'='*60}")
                print(f"Migration Summary: {config.name}")
                print(f"{'='*60}")
                print(f"Total sections: {migrator.stats.total_sections}")
                print(f"Migrated: {migrator.stats.migrated_sections}")
                print(f"Failed: {migrator.stats.failed_sections}")
                print(f"Migrated lines: {migrator.stats.migrated_lines}")
                print(f"Kept lines: {migrator.stats.kept_lines}")

            if args.compact:
                migrator.compact_skill(config)

    return 0


if __name__ == "__main__":
    sys.exit(main())
