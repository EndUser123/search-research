#!/usr/bin/env python3
"""Coding Standards Ingestion Script.

Ingests Python and TypeScript coding standards into CKS knowledge base.

Usage:
    python -m cks.commands.ingest_coding_standards --all
    python -m cks.commands.ingest_coding_standards --language python
    python -m cks.commands.ingest_coding_standards --stats
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    from ..unified import CKS
except ImportError:
    print("❌ CKS not found. Please ensure CKS is initialized.")
    sys.exit(1)


class CodingStandardsParser:
    """Parse coding standards from markdown files."""

    @staticmethod
    def parse_markdown_table(lines: list[str]) -> list[dict[str, str]]:
        """Parse markdown table from quick reference files.

        Args:
            lines: List of file lines

        Returns:
            List of dicts with keys: number, standard, do_this, not_this, why

        """
        standards = []
        in_table = False

        for line in lines:
            # Detect table header
            if "| #" in line and "| Standard |" in line:
                in_table = True
                continue

            # Skip separator row
            if in_table and "|---" in line:
                continue

            # Parse table row
            if in_table and line.strip().startswith("|"):
                parts = [p.strip() for p in line.split("|")[1:-1]]  # Remove empty first/last
                if len(parts) >= 4 and parts[0].isdigit():
                    standards.append(
                        {
                            "number": int(parts[0]),
                            "standard": parts[1],
                            "do_this": parts[2],
                            "not_this": parts[3] if len(parts) > 3 else "",
                            "why": parts[4] if len(parts) > 4 else "",
                        }
                    )

            # End of table
            if in_table and not line.strip().startswith("|"):
                break

        return standards

    @staticmethod
    def parse_anti_patterns(lines: list[str]) -> list[str]:
        """Parse anti-patterns list from quick reference files.

        Args:
            lines: List of file lines

        Returns:
            List of anti-pattern strings

        """
        anti_patterns = []
        in_section = False
        in_code_block = False

        for line in lines:
            # Detect start of section
            if "REFUSE" in line.upper() and ("These" in line or "THESE" in line):
                in_section = True
                continue

            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Parse anti-patterns from code blocks (format: # ❌ REFUSE: pattern)
            if in_section and in_code_block:
                if "❌ REFUSE:" in line or ": REFUSE:" in line.upper():
                    # Extract pattern after "REFUSE:"
                    if "❌ REFUSE:" in line:
                        pattern = line.split("❌ REFUSE:", 1)[1].strip()
                    elif ": REFUSE:" in line:
                        pattern = line.split(": REFUSE:", 1)[1].strip()

                    # Remove comment markers and clean up
                    pattern = re.sub(r"^#\s*", "", pattern)
                    pattern = pattern.strip()

                    if pattern and not pattern.startswith("#"):
                        anti_patterns.append(pattern)

                # End of section (next heading)
                elif line.strip().startswith("#") and not line.strip().startswith("##"):
                    if anti_patterns:  # Only if we found some patterns
                        break
                elif not line.strip():
                    continue
                else:
                    # End of section (non-empty, non-comment line)
                    if anti_patterns:
                        break

            # Also parse markdown-style list items outside code blocks
            if in_section and not in_code_block:
                if line.strip().startswith(("- ", "* ")):
                    pattern = line.strip()[2:].strip()
                    # Remove markers
                    pattern = re.sub(r"^[❌#\s]*", "", pattern)
                    if pattern:
                        anti_patterns.append(pattern)
                elif line.strip().startswith("#") or "##" in line:
                    # End of section
                    if anti_patterns:
                        break
                elif not line.strip():
                    continue
                else:
                    # End of section
                    break

        return anti_patterns

    @staticmethod
    def extract_focus_area(standard: str) -> str:
        """Extract focus area from standard title."""
        standard_lower = standard.lower()

        focus_map = {
            "packaging": ["packaging", "dependency", "uv", "pyproject"],
            "linting": ["lint", "ruff", "black", "format"],
            "type-safety": ["type", "mypy", "strict"],
            "validation": ["validation", "pydantic", "schema"],
            "async": ["async", "task", "concurrency"],
            "architecture": ["architecture", "vertical", "slice"],
            "logging": ["log", "json", "struct"],
            "config": ["config", "settings", "env"],
            "runtime": ["runtime", "node", "bun", "lts"],
            "package-manager": ["package", "manager", "pnpm", "npm"],
            "testing": ["test", "vitest", "jest"],
            "imports": ["import", "esm", "commonjs"],
            "typing": ["type", "any", "unknown"],
            "backend": ["backend", "hono", "fastify", "express"],
        }

        for focus, keywords in focus_map.items():
            if any(kw in standard_lower for kw in keywords):
                return focus

        return "general"

    @staticmethod
    def extract_tools(standard: str, do_this: str) -> list[str]:
        """Extract tool names from standard."""
        text = f"{standard} {do_this}".lower()

        tools = []
        tool_keywords = {
            "uv": ["uv"],
            "ruff": ["ruff"],
            "mypy": ["mypy"],
            "pydantic": ["pydantic"],
            "asyncio": ["asyncio"],
            "pydantic-settings": ["pydantic-settings"],
            "biome": ["biome"],
            "vitest": ["vitest"],
            "zod": ["zod"],
            "hono": ["hono"],
            "fastify": ["fastify"],
            "node": ["node"],
            "bun": ["bun"],
            "pnpm": ["pnpm"],
            "github actions": ["github actions"],
        }

        for tool, keywords in tool_keywords.items():
            if any(kw in text for kw in keywords):
                tools.append(tool)

        return tools


class CodingStandardsIngestion:
    """Ingest coding standards into CKS."""

    def __init__(self) -> None:
        self.cks = CKS()
        self.parser = CodingStandardsParser()

    def ingest_python_standards(self) -> dict[str, Any]:
        """Parse and ingest Python coding standards."""
        # Navigate to project root: src/features/cks/commands -> src -> __csf -> P:
        project_root = Path(__file__).parent.parent.parent.parent
        # Coding standards are in P:\\\\.claude/commands/
        source_file = project_root.parent / ".claude/commands/code_python_2025_quick_reference.md"

        if not source_file.exists():
            return {"success": False, "error": f"Source file not found: {source_file}"}

        with open(source_file, encoding="utf-8") as f:
            lines = f.readlines()

        # Parse standards
        standards = self.parser.parse_markdown_table(lines)
        anti_patterns = self.parser.parse_anti_patterns(lines)

        results = {
            "success": True,
            "language": "python",
            "standards_ingested": 0,
            "anti_patterns_ingested": 0,
            "entries": [],
        }

        # Ingest mandatory standards
        for standard in standards:
            title = f"Python Standard #{standard['number']}: {standard['standard']}"
            content = f"""# {title}

**Category:** Mandatory
**Standard Number:** {standard['number']}

## DO THIS
{standard['do_this']}

## NOT THIS
{standard['not_this']}

## Why
{standard['why']}

## Quick Reference
```bash
# Correct approach
{standard['do_this']}
```

This is a mandatory Python 2025 coding standard. Following this standard ensures:
- Better code quality
- Improved performance
- Modern best practices
- Team consistency
"""

            focus_area = self.parser.extract_focus_area(standard["standard"])
            tools = self.parser.extract_tools(standard["standard"], standard["do_this"])

            metadata = {
                "language": "python",
                "category": "mandatory",
                "standard_number": standard["number"],
                "focus_area": focus_area,
                "tools": tools,
                "source_file": "code_python_2025_quick_reference.md",
            }

            tags = ["python", "2025-standards", "mandatory", focus_area, *tools]

            entry_id = self.cks.ingest_pattern(
                title=title,
                content=content,
                metadata=metadata,
                tags=tags,
            )

            results["standards_ingested"] += 1
            results["entries"].append({"id": entry_id, "title": title, "type": "standard"})
            print(f"  ✅ Ingested: {title}")

        # Ingest anti-patterns
        for anti_pattern in anti_patterns:
            title = f"Python Anti-Pattern: {anti_pattern}"
            content = f"""# {title}

**Category:** Anti-Pattern (REFUSE These)
**Language:** Python

## Why This Is Problematic
This pattern violates Python 2025 coding standards and should be avoided.

## Correct Alternative
Refer to the relevant mandatory Python standard for the correct approach.

## Impact
- Code quality issues
- Potential bugs
- Maintainability problems
- Performance degradation

Search for this pattern in your codebase and replace with the recommended alternative.
"""

            metadata = {
                "language": "python",
                "category": "avoid",
                "focus_area": "anti-pattern",
                "source_file": "code_python_2025_quick_reference.md",
            }

            tags = ["python", "anti-pattern", "2025-standards", "avoid"]

            entry_id = self.cks.ingest_pattern(
                title=title,
                content=content,
                metadata=metadata,
                tags=tags,
            )

            results["anti_patterns_ingested"] += 1
            results["entries"].append({"id": entry_id, "title": title, "type": "anti-pattern"})
            print(f"  ✅ Ingested: {title}")

        return results

    def ingest_typescript_standards(self) -> dict[str, Any]:
        """Parse and ingest TypeScript coding standards."""
        # Navigate to project root: src/features/cks/commands -> src -> __csf -> P:
        project_root = Path(__file__).parent.parent.parent.parent
        # Coding standards are in P:\\\\.claude/commands/
        source_file = project_root.parent / ".claude/commands/code_ts_2025_quick_reference.md"

        if not source_file.exists():
            return {"success": False, "error": f"Source file not found: {source_file}"}

        with open(source_file, encoding="utf-8") as f:
            lines = f.readlines()

        # Parse standards
        standards = self.parser.parse_markdown_table(lines)
        anti_patterns = self.parser.parse_anti_patterns(lines)

        results = {
            "success": True,
            "language": "typescript",
            "standards_ingested": 0,
            "anti_patterns_ingested": 0,
            "entries": [],
        }

        # Ingest mandatory standards
        for standard in standards:
            title = f"TypeScript Standard #{standard['number']}: {standard['standard']}"
            content = f"""# {title}

**Category:** Mandatory
**Standard Number:** {standard['number']}

## DO THIS
{standard['do_this']}

## NOT THIS
{standard['not_this']}

## Why
{standard['why']}

## Quick Reference
```bash
# Correct approach
{standard['do_this']}
```

This is a mandatory TypeScript 2025 coding standard. Following this standard ensures:
- Type safety
- Better performance
- Modern tooling
- Consistency across projects
"""

            focus_area = self.parser.extract_focus_area(standard["standard"])
            tools = self.parser.extract_tools(standard["standard"], standard["do_this"])

            metadata = {
                "language": "typescript",
                "category": "mandatory",
                "standard_number": standard["number"],
                "focus_area": focus_area,
                "tools": tools,
                "source_file": "code_ts_2025_quick_reference.md",
            }

            tags = ["typescript", "2025-standards", "mandatory", focus_area, *tools]

            entry_id = self.cks.ingest_pattern(
                title=title,
                content=content,
                metadata=metadata,
                tags=tags,
            )

            results["standards_ingested"] += 1
            results["entries"].append({"id": entry_id, "title": title, "type": "standard"})
            print(f"  ✅ Ingested: {title}")

        # Ingest anti-patterns
        for anti_pattern in anti_patterns:
            title = f"TypeScript Anti-Pattern: {anti_pattern}"
            content = f"""# {title}

**Category:** Anti-Pattern (REFUSE These)
**Language:** TypeScript

## Why This Is Problematic
This pattern violates TypeScript 2025 coding standards and should be avoided.

## Correct Alternative
Refer to the relevant mandatory TypeScript standard for the correct approach.

## Impact
- Type safety issues
- Runtime errors
- Maintainability problems
- Poor developer experience

Search for this pattern in your codebase and replace with the recommended alternative.
"""

            metadata = {
                "language": "typescript",
                "category": "avoid",
                "focus_area": "anti-pattern",
                "source_file": "code_ts_2025_quick_reference.md",
            }

            tags = ["typescript", "anti-pattern", "2025-standards", "avoid"]

            entry_id = self.cks.ingest_pattern(
                title=title,
                content=content,
                metadata=metadata,
                tags=tags,
            )

            results["anti_patterns_ingested"] += 1
            results["entries"].append({"id": entry_id, "title": title, "type": "anti-pattern"})
            print(f"  ✅ Ingested: {title}")

        return results

    def show_stats(self) -> None:
        """Show statistics on ingested standards."""
        print("\n📊 Coding Standards Statistics")
        print("=" * 60)

        # Search for all coding standard patterns using title-based search
        python_results = self.cks.search("Python Standard", entry_type="pattern", limit=100)
        ts_results = self.cks.search("TypeScript Standard", entry_type="pattern", limit=100)

        # Count mandatory vs anti-patterns based on title
        python_standards = [p for p in python_results if "Python Standard #" in p.get("title", "")]
        python_anti_patterns = [p for p in python_results if "Anti-Pattern" in p.get("title", "")]

        ts_standards = [p for p in ts_results if "TypeScript Standard #" in p.get("title", "")]
        ts_anti_patterns = [p for p in ts_results if "Anti-Pattern" in p.get("title", "")]

        print("\n🐍 Python Standards:")
        print(f"  Mandatory: {len(python_standards)}")
        print(f"  Anti-patterns: {len(python_anti_patterns)}")
        print(f"  Total: {len(python_standards) + len(python_anti_patterns)}")

        print("\n📘 TypeScript Standards:")
        print(f"  Mandatory: {len(ts_standards)}")
        print(f"  Anti-patterns: {len(ts_anti_patterns)}")
        print(f"  Total: {len(ts_standards) + len(ts_anti_patterns)}")

        total = (
            len(python_standards)
            + len(python_anti_patterns)
            + len(ts_standards)
            + len(ts_anti_patterns)
        )
        print(f"\n📈 Total Standards: {total}")

        # Show sample standards
        if python_standards:
            print("\n🐍 Python Standards Sample:")
            for p in python_standards[:5]:
                print(f"  - {p.get('title', '')}")

        if ts_standards:
            print("\n📘 TypeScript Standards Sample:")
            for p in ts_standards[:5]:
                print(f"  - {p.get('title', '')}")


def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Ingest coding standards into CKS knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                    Ingest all coding standards
  %(prog)s --language python        Ingest only Python standards
  %(prog)s --language typescript    Ingest only TypeScript standards
  %(prog)s --stats                  Show statistics
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest all coding standards (Python + TypeScript)",
    )
    parser.add_argument(
        "--language",
        choices=["python", "typescript"],
        help="Ingest standards for specific language",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics on ingested standards",
    )

    args = parser.parse_args()

    ingestion = CodingStandardsIngestion()

    try:
        if args.stats:
            ingestion.show_stats()

        elif args.all or args.language:
            if args.all or args.language == "python":
                print("\n🐍 Ingesting Python Coding Standards...")
                print("=" * 60)
                result = ingestion.ingest_python_standards()
                if result["success"]:
                    print("\n✅ Python ingestion complete:")
                    print(f"   Standards: {result['standards_ingested']}")
                    print(f"   Anti-patterns: {result['anti_patterns_ingested']}")
                else:
                    print(f"\n❌ Python ingestion failed: {result.get('error')}")
                    sys.exit(1)

            if args.all or args.language == "typescript":
                print("\n📘 Ingesting TypeScript Coding Standards...")
                print("=" * 60)
                result = ingestion.ingest_typescript_standards()
                if result["success"]:
                    print("\n✅ TypeScript ingestion complete:")
                    print(f"   Standards: {result['standards_ingested']}")
                    print(f"   Anti-patterns: {result['anti_patterns_ingested']}")
                else:
                    print(f"\n❌ TypeScript ingestion failed: {result.get('error')}")
                    sys.exit(1)

            if args.all:
                print("\n" + "=" * 60)
                ingestion.show_stats()

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
