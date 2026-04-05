#!/usr/bin/env python3
"""
PRD Parser for TaskMaster - Enhanced Version

Improved version with better pattern matching and edge case handling.

Author: Claude Code
Version: 1.2.0
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PRDRequirement:
    """A requirement extracted from a PRD."""
    id: str  # FR-XXX or NF-XXX
    sub_id: str | None  # .Y for sub-requirements
    title: str
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    acceptance_criteria: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    line_number: int = 0
    raw_text: str = ""  # Full raw text for context
    status: str = "pending"


@dataclass
class ParsedPRD:
    """Result of parsing a PRD file."""
    prd_name: str
    metadata: dict[str, Any]
    functional_requirements: list[PRDRequirement]
    non_functional_requirements: list[PRDRequirement]
    total_requirements: int
    parse_time: datetime = field(default_factory=datetime.now)
    source_file: str = ""
    raw_content: str = ""

    @property
    def version(self) -> str | None:
        """Get PRD version from metadata."""
        return self.metadata.get("version")

    @property
    def title(self) -> str | None:
        """Get PRD title from metadata."""
        return self.metadata.get("title") or self.prd_name

    def get_requirement_by_id(self, req_id: str) -> PRDRequirement | None:
        """Get a requirement by its ID."""
        all_reqs = self.functional_requirements + self.non_functional_requirements
        for req in all_reqs:
            if req.id == req_id:
                return req
        return None

    def get_requirements_by_category(self, category: str) -> list[PRDRequirement]:
        """Get all requirements matching a category."""
        all_reqs = self.functional_requirements + self.non_functional_requirements
        return [r for r in all_reqs if r.category == category]


class PRDValidationError(Exception):
    """Raised when PRD validation fails."""


class PRDParser:
    """
    Parser for PRD.md files with FR-XXX/NF-XXX format.

    Extracts requirements from PRD files and structures them for database storage.

    Supports multiple PRD formats:
    1. #### **FR-1:** Title (header format - yt_sync style)
    2. - **FR-1:** Title (list format)
    3. Checkbox-based requirements with [x]/[ ]
    4. - **ID:** FR-001 (vid_dup_ai style with separate ID field)
    """

    def __init__(self, base_path: str | None = None):
        """Initialize the PRD parser.

        Args:
            base_path: Base path for resolving relative PRD file paths
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logger = logging.getLogger(__name__)

        # Parse statistics
        self.parse_stats = {
            "prd_files_parsed": 0,
            "requirements_extracted": 0,
            "functional_count": 0,
            "non_functional_count": 0,
            "parse_errors": 0,
            "validation_errors": 0,
        }

    def parse_prd_file(self, prd_path: str) -> ParsedPRD:
        """Parse a PRD.md file and extract requirements.

        Args:
            prd_path: Path to the PRD file

        Returns:
            ParsedPRD object with extracted requirements

        Raises:
            PRDValidationError: If PRD validation fails
        """
        prd_file = Path(prd_path)
        if not prd_file.is_absolute():
            prd_file = self.base_path / prd_path

        if not prd_file.exists():
            raise PRDValidationError(f"PRD file not found: {prd_path}")

        self.logger.info(f"Parsing PRD file: {prd_file}")

        # Read content
        with open(prd_file, encoding='utf-8') as f:
            raw_content = f.read()

        # Extract frontmatter and content
        frontmatter, content = self._extract_frontmatter(prd_file, raw_content)

        # Extract PRD name from metadata or filename
        prd_name = frontmatter.get("prd_name", frontmatter.get("name", prd_file.stem))

        # Validate PRD structure (non-blocking - warnings only)
        validation_errors = self._validate_prd_structure(content)
        if validation_errors:
            self.logger.warning(f"PRD validation warnings: {validation_errors}")
            self.parse_stats["validation_errors"] += len(validation_errors)

        # Extract requirements using multiple patterns
        all_requirements = self._extract_all_requirements(content)

        # Separate by type
        functional_reqs = [r for r in all_requirements if r.id.startswith('FR')]
        non_functional_reqs = [r for r in all_requirements if r.id.startswith('NF') or r.id.startswith('NFR')]

        # Parse result
        parsed_prd = ParsedPRD(
            prd_name=prd_name,
            metadata=frontmatter,
            functional_requirements=functional_reqs,
            non_functional_requirements=non_functional_reqs,
            total_requirements=len(all_requirements),
            source_file=str(prd_file),
            raw_content=raw_content,
        )

        # Update statistics
        self.parse_stats["prd_files_parsed"] += 1
        self.parse_stats["requirements_extracted"] += parsed_prd.total_requirements
        self.parse_stats["functional_count"] += len(functional_reqs)
        self.parse_stats["non_functional_count"] += len(non_functional_reqs)

        self.logger.info(
            f"Parsed {parsed_prd.total_requirements} requirements from {prd_name} "
            f"({len(functional_reqs)} FR, {len(non_functional_reqs)} NF)"
        )

        return parsed_prd

    def _extract_frontmatter(self, file_path: Path, content: str) -> tuple[dict[str, Any], str]:
        """Extract YAML frontmatter from markdown file.

        Args:
            file_path: Path to the markdown file
            content: Raw file content

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        try:
            # Look for YAML frontmatter
            if content.startswith("---\n"):
                # Find the end of frontmatter
                end_idx = content.find("\n---\n", 4)
                if end_idx == -1:
                    # Try alternative pattern
                    end_idx = content.find("\n---", 4)

                if end_idx != -1:
                    frontmatter_str = content[4:end_idx]
                    content_body = content[end_idx + 5:]

                    try:
                        frontmatter = yaml.safe_load(frontmatter_str) or {}
                        return frontmatter, content_body
                    except yaml.YAMLError as e:
                        self.logger.warning(f"Failed to parse YAML in {file_path}: {e}")
                        return {}, content

            # No frontmatter found
            return {}, content

        except Exception as e:
            self.logger.error(f"Error reading frontmatter from {file_path}: {e}")
            return {}, content

    def _validate_prd_structure(self, content: str) -> list[str]:
        """Validate PRD structure and return list of errors.

        Args:
            content: PRD content without frontmatter

        Returns:
            List of validation error messages
        """
        errors = []

        # Check for requirements section
        has_requirements = (
            "## Requirements" in content or
            "## Functional Requirements" in content or
            "# Requirements" in content or
            "## Feature Requirements" in content or
            "### Core Feature Requirements" in content
        )
        if not has_requirements:
            errors.append("Missing Requirements section")

        # Check for at least one requirement pattern
        has_req_pattern = bool(self._find_any_requirement(content))
        if not has_req_pattern:
            errors.append("No requirements found (expected format: **FR-XXX:** Title or **NFR-XXX:** Title)")

        return errors

    def _find_any_requirement(self, content: str) -> str | None:
        """Find any requirement-like pattern in content.

        Returns:
            First match found or None
        """
        # Look for FR-1:, FR-1:, NFR-1:, NF-1: patterns
        patterns = [
            r'[A-Z]+FR-\d+:',
            r'[A-Z]+FR-\d+',
            r'FR\d+:',
            r'NFR\d+:',
        ]
        for pat in patterns:
            m = re.search(pat, content)
            if m:
                return m.group(0)
        return None

    def _extract_all_requirements(self, content: str) -> list[PRDRequirement]:
        """Extract requirements using all available patterns.

        Args:
            content: PRD content

        Returns:
            List of PRDRequirement objects
        """
        requirements = []
        seen_ids = set()

        # Method 1: Parse line by line for requirement headers
        # This is more robust than complex regex
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if line contains a requirement header
            req_match = self._match_requirement_line(line)
            if req_match:
                req_id, title = req_match

                # Clean up ID (remove trailing colon, etc)
                req_id = req_id.rstrip(':').strip()

                # Skip duplicates
                if req_id not in seen_ids:
                    seen_ids.add(req_id)

                    # Get line number
                    line_number = i + 1

                    # Extract description from following lines
                    description = self._extract_description_from_lines(lines, i + 1)

                    # Get surrounding context
                    context_start = max(0, i - 3)
                    context_end = min(len(lines), i + 15)
                    context = '\n'.join(lines[context_start:context_end])

                    # Extract acceptance criteria from context
                    acceptance_criteria = self._extract_acceptance_criteria(context)

                    # Extract success metrics from context
                    success_metrics = self._extract_success_metrics(context)

                    # Determine category
                    category = self._infer_category(context, title)

                    requirement = PRDRequirement(
                        id=req_id,
                        sub_id=None,
                        title=title,
                        description=description,
                        category=category,
                        acceptance_criteria=acceptance_criteria,
                        success_metrics=success_metrics,
                        line_number=line_number,
                        raw_text=line,
                    )
                    requirements.append(requirement)

            i += 1

        return requirements

    def _match_requirement_line(self, line: str) -> tuple[str, str] | None:
        """Check if a line contains a requirement and return (id, title).

        Args:
            line: The line to check

        Returns:
            Tuple of (requirement_id, title) or None
        """
        # Pattern 1: #### **FR-1: Title** (header format - yt_sync style)
        # Matches: **FR-1: Title** where both ID and title are wrapped in **
        # Use non-greedy match with space after colon to avoid over-matching
        m = re.search(r'\*\*FR-(\d+):\s*(.+?)\*\*', line)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            # Remove leading : if title starts with it
            title = title.lstrip(':').strip()
            # Limit title length to avoid capturing entire paragraphs
            if len(title) > 200:
                title = title[:200].rsplit(' ', 1)[0]  # Truncate at word boundary
            return f'FR-{num}', title

        # Pattern 2: #### **NFR-1: Title** (non-functional header format)
        m = re.search(r'\*\*NFR-(\d+):\s*(.+?)\*\*', line)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            title = title.lstrip(':').strip()
            if len(title) > 200:
                title = title[:200].rsplit(' ', 1)[0]
            return f'NFR-{num}', title

        # Pattern 3: #### **NF-1: Title** (alternative non-functional format)
        m = re.search(r'\*\*NF-(\d+):\s*(.+?)\*\*', line)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            title = title.lstrip(':').strip()
            if len(title) > 200:
                title = title[:200].rsplit(' ', 1)[0]
            return f'NF-{num}', title

        # Pattern 3.5: #### **FR-1** Title (no colon after ID)
        m = re.search(r'\*\*(FR|NFR|NF)-(\d+)\*\*\s*(.+)', line)
        if m:
            req_type = m.group(1)
            num = m.group(2)
            title = m.group(3).strip()
            # Remove leading : if present
            title = title.lstrip(':').strip()
            if len(title) > 200:
                title = title[:200].rsplit(' ', 1)[0]
            return f'{req_type}-{num}', title

        # Pattern 4: *   **NFR-1:** Title: Description (inline format)
        # Matches when the entire requirement is on one line with description
        # This requires limiting title length to avoid capturing whole paragraphs
        m = re.search(r'\*\*(?:FR|NFR|NF)-(\d+):\*\*\s*(.{5,200}?)(?:\n|$)', line)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            # Try to extract just the title (before the colon if present)
            if ':' in title:
                title_parts = title.split(':', 1)
                title = title_parts[0].strip()
            return f'{self._get_req_type(line)}-{num}', title

        # Pattern 5: FR-1: Title (without bold)
        m = re.search(r'(?:FR|NFR|NF)-(\d+):\s*([^\n]{5,200})', line)
        if m and not line.strip().startswith('#'):
            num = m.group(1)
            title = m.group(2).strip()
            if ':' in title:
                title = title.split(':', 1)[0].strip()
            return f'{self._get_req_type(line)}-{num}', title

        # Pattern 6: - **ID:** FR-001 (vid_dup_ai style with separate ID field)
        # Look for lines with - **ID:** FR-XXX or - **ID:** NFR-XXX
        m = re.search(r'-\s+\*\*ID:\*\*\s*(FR|NFR|NF)-(\d+)', line)
        if m:
            req_type = m.group(1)
            num = m.group(2)
            # Return the ID but with placeholder title, will be filled from next lines
            return f'{req_type}-{num}', f"{req_type}-{num}"

        return None

    def _get_req_type(self, line: str) -> str:
        """Extract requirement type (FR/NFR/NF) from line."""
        m = re.search(r'(FR|NFR|NF)-\d+', line)
        if m:
            return m.group(1)
        return 'FR'  # Default to FR

    def _extract_description_from_lines(self, lines: list[str], start_idx: int) -> str:
        """Extract description from lines following a requirement.

        Args:
            lines: All lines in the document
            start_idx: Index to start looking

        Returns:
            Extracted description text
        """
        description_lines = []
        max_lines = 10
        bullets = ['*', '-', '•']

        for i in range(start_idx, min(len(lines), start_idx + max_lines)):
            line = lines[i].strip()

            # Stop at next requirement header
            if self._match_requirement_line(line):
                break

            # Stop at next major section
            if line.startswith('#'):
                break

            # Skip empty lines and just bullets
            if not line or line.split()[0] if line.split() else '' in bullets:
                continue

            # Skip if it looks like a list item without context
            if line.startswith('-') or line.startswith('*'):
                continue

            description_lines.append(line)

            # Limit description length
            if len(' '.join(description_lines)) > 500:
                break

        return ' '.join(description_lines)[:500] if description_lines else ""

    def _extract_acceptance_criteria(self, context: str) -> list[str]:
        """Extract acceptance criteria from context."""
        pattern = re.compile(r'[-\*]\s+AC[\.:]\s*(.+?)(?=\n|$)', re.MULTILINE)
        return pattern.findall(context)

    def _extract_success_metrics(self, context: str) -> list[str]:
        """Extract success metrics from context."""
        pattern = re.compile(r'[-\*]\s+Metric[\.:]\s*(.+?)(?=\n|$)', re.MULTILINE)
        return pattern.findall(context)

    def _infer_category(self, context: str, title: str) -> str | None:
        """Infer requirement category from context and title.

        Args:
            context: Surrounding text context
            title: Requirement title

        Returns:
            Inferred category or None
        """
        context_lower = context.lower()
        title_lower = title.lower()

        # Category keywords - ordered by priority (more specific first)
        category_keywords = [
            ("API", ["api", "endpoint", "rest", "graphql", "http"]),
            ("Authentication", ["authentication", "login", "auth", "security", "permission"]),
            ("Data", ["database", "storage", "persistence", "data", "cache"]),
            ("User Interface", ["ui", "user interface", "display", "screen", "view", "cli"]),
            ("Performance", ["performance", "speed", "latency", "throughput"]),
            ("Testing", ["test", "coverage", "unit test"]),
            ("Configuration", ["config", "setting", "option"]),
        ]

        # Prepare words
        title_words = set(title_lower.replace('-', ' ').replace('_', ' ').split())
        context_words = set(context_lower.replace('-', ' ').replace('_', ' ').split())

        # First pass: check title only (highest priority)
        for category, keywords in category_keywords:
            for keyword in keywords:
                if keyword in title_words:
                    return category

        # Second pass: check context only if no title match
        for category, keywords in category_keywords:
            for keyword in keywords:
                if keyword in context_words:
                    return category

        return None


    def get_statistics(self) -> dict[str, Any]:
        """Get parser statistics.

        Returns:
            Dictionary with parser statistics
        """
        return self.parse_stats.copy()

    def reset_statistics(self) -> None:
        """Reset parse statistics."""
        self.parse_stats = {
            "prd_files_parsed": 0,
            "requirements_extracted": 0,
            "functional_count": 0,
            "non_functional_count": 0,
            "parse_errors": 0,
            "validation_errors": 0,
        }


# Convenience functions

def parse_prd(prd_path: str, base_path: str | None = None) -> ParsedPRD:
    """
    Parse a PRD file using default parser.

    Args:
        prd_path: Path to PRD file
        base_path: Optional base path for relative paths

    Returns:
        ParsedPRD object
    """
    parser = PRDParser(base_path)
    return parser.parse_prd_file(prd_path)


def extract_requirement_ids(prd_path: str) -> list[str]:
    """
    Quick extraction of all requirement IDs from a PRD.

    Args:
        prd_path: Path to PRD file

    Returns:
        List of requirement IDs (e.g., ['FR-1', 'FR-2', 'NFR-1'])
    """
    parser = PRDParser()
    prd = parser.parse_prd_file(prd_path)

    fr_ids = [r.id for r in prd.functional_requirements]
    nfr_ids = [r.id for r in prd.non_functional_requirements]

    return fr_ids + nfr_ids


# Example usage
if __name__ == "__main__":

    # Test parser on a sample PRD
    parser = PRDParser()

    # Example: Parse yt_sync PRD
    test_prd_path = r"/p/projects/yt_sync/docs/PRD.md"

    try:
        parsed_prd = parser.parse_prd_file(test_prd_path)

        print(f"PRD Name: {parsed_prd.prd_name}")
        print(f"Total Requirements: {parsed_prd.total_requirements}")
        print(f"Functional: {len(parsed_prd.functional_requirements)}")
        print(f"Non-Functional: {len(parsed_prd.non_functional_requirements)}")

        # Print first 5 functional requirements
        print("\nFirst 5 Functional Requirements:")
        for req in parsed_prd.functional_requirements[:5]:
            print(f"  {req.id}: {req.title}")

        # Print statistics
        print("\nParser Statistics:")
        for key, value in parser.get_statistics().items():
            print(f"  {key}: {value}")

    except PRDValidationError as e:
        print(f"PRD validation error: {e}")
    except FileNotFoundError:
        print(f"Test PRD not found at: {test_prd_path}")
        print("Usage: python parser.py <path_to_prd>")
