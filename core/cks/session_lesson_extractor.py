#!/usr/bin/env python3
"""Session Lesson Extractor for CKS

Analyzes Claude Code session transcripts and extracts lessons/learnings
to store in the Constitutional Knowledge System.

Usage:
    from cks.session_lesson_extractor import extract_session_lessons

    lessons = extract_session_lessons(session_file_path)
    for lesson in lessons:
        lesson.store()
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add src directory to path for imports
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from cks.unified import CKS

logger = logging.getLogger(__name__)


@dataclass
class ExtractedLesson:
    """A lesson extracted from a session transcript."""

    entry_type: str  # "learning", "insight", "correction", "pattern"
    title: str
    content: str
    metadata: dict[str, Any]
    source_file: str
    extracted_at: str

    def store(self, cks: CKS) -> str:
        """Store this lesson in CKS."""
        metadata = {
            **self.metadata,
            "source_file": self.source_file,
            "extracted_at": self.extracted_at,
            "extraction_method": "session_lesson_extractor",
        }

        if self.entry_type == "learning":
            return cks.ingest_learning(
                title=self.title,
                content=self.content,
                **metadata,
            )
        if self.entry_type == "insight":
            return cks.ingest_insight(
                title=self.title,
                content=self.content,
                **metadata,
            )
        if self.entry_type == "correction":
            return cks.ingest_correction(
                title=self.title,
                content=self.content,
                **metadata,
            )
        if self.entry_type == "pattern":
            return cks.ingest_pattern(
                title=self.title,
                content=self.content,
                **metadata,
            )
        # Fallback to memory
        return cks.ingest_memory(
            question=self.title,
            answer=self.content,
            **metadata,
        )


class SessionLessonExtractor:
    """Extract lessons from Claude Code session transcripts.

    Detects and categorizes:
    - Learnings: New information gained (e.g., "Serper is 20-30x cheaper")
    - Insights: Realizations (e.g., "Hook timing mismatch caused loop")
    - Corrections: Mistakes and fixes
    - Patterns: Repeating solutions (e.g., "Windows cmd /c wrapper")
    """

    # Learning patterns: things we learned that should be remembered
    LEARNING_PATTERNS = [
        r"(?:learned|discovered|found|realized|note|remember)[:\s]+(.+?)(?:\.|$)",
        r"(?:serper|serpapi|tavily|brave|exa)[\s]+is\s+(?:\d+x\s+)?(?:cheaper|faster|better)(.+?)(?:\.|$)",
        r"(?:verif?ied|confirmed)[\s]+(.+?)(?:\.|$)",
        r"(?:claim|statement)[\s]+(.+?)[:\s]+(?:true|correct|accurate)",
        r"(?:free tier[:\s]+.+?)(?:\.|$)",
    ]

    # Insight patterns: realizations and "aha" moments
    INSIGHT_PATTERNS = [
        r"(?:realized|noticed|observed)[\s]+(.+?)(?:\.|$)",
        r"(?:issue|problem|error)[\s+was[:\s]+(?:caused|due to)[\s]+(.+?)(?:\.|$)",
        r"(?:root cause|reason|because)[\s]+(?:was|is)[:\s]+(.+?)(?:\.|$)",
    ]

    # Correction patterns: mistakes and their fixes
    CORRECTION_PATTERNS = [
        r"(?:fixed|corrected|resolved)[\s]+(.+?)[:\s]+by\s+(.+?)(?:\.|$)",
        r"(?:mistake|error|bug|issue)[\s]+(.+?)[:\s]+(.+?)(?:\.|$)",
        r"(?:wrong|incorrect|broken)[\s]+(.+?)[:\s]+(.+?)(?:\.|$)",
    ]

    # Pattern patterns: reusable solutions
    PATTERN_PATTERNS = [
        r"(?:use|need|require)[:\s]+(.+?)(?:\.|$)",
        r"(?:windows|cmd|npx|wrapper|script|bash|shell)[:\s]+(.+?)(?:\.|$)",
        r"(?:solution|fix|workaround)[:\s]+(.+?)(?:\.|$)",
        r"(?:pattern|approach|method|strategy)[:\s]+(.+?)(?:\.|$)",
        r"(?:config|configuration|settings)[:\s]+(.+?)(?:\.|$)",
    ]

    # Sections to look for in the transcript
    SECTION_HEADERS = [
        "summary",
        "conclusions",
        "lessons learned",
        "findings",
        "results",
        "recommendations",
        "action items",
        "next steps",
    ]

    def __init__(self):
        self.cks = CKS()

    def extract_session(self, session_file: Path | str) -> list[ExtractedLesson]:
        """Extract lessons from a Claude Code session transcript.

        Args:
            session_file: Path to the session JSONL file

        Returns:
            List of extracted lessons

        """
        session_file = Path(session_file)

        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            return []

        lessons = []
        transcript = self._read_transcript(session_file)

        # Extract from sections first
        lessons.extend(self._extract_from_sections(transcript, session_file))

        # Then scan for patterns in the full transcript
        lessons.extend(self._extract_from_patterns(transcript, session_file))

        return lessons

    def _read_transcript(self, session_file: Path) -> str:
        """Read and parse session transcript from JSONL file."""
        messages = []

        for line in session_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    # Try multiple content field names
                    content = (
                        data.get("content", "")
                        or data.get("summary", "")
                        or data.get("text", "")
                        or data.get("message", "")
                    )
                    if content:
                        # Add type prefix if available for context
                        entry_type = data.get("type", "")
                        if entry_type and entry_type != "summary":
                            messages.append(f"[{entry_type}] {content}")
                        else:
                            messages.append(content)
                elif isinstance(data, list):
                    # Content might be a list of blocks
                    for block in data:
                        if isinstance(block, dict) and "text" in block:
                            messages.append(block["text"])
                        elif isinstance(block, str):
                            messages.append(block)
            except json.JSONDecodeError:
                # Skip invalid lines
                continue

        return "\n".join(messages)

    def _extract_from_sections(
        self,
        transcript: str,
        session_file: Path,
    ) -> list[ExtractedLesson]:
        """Extract lessons from formal sections (Summary, Conclusions, etc.)."""
        lessons = []
        current_section = None
        section_content = []

        lines = transcript.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for section headers
            if line.startswith("##") and any(
                header in line.lower() for header in self.SECTION_HEADERS
            ):
                # Save previous section
                if current_section and section_content:
                    lessons.extend(
                        self._parse_section_content(
                            "\n".join(section_content),
                            current_section,
                            session_file,
                        ),
                    )

                # Start new section
                current_section = line.lstrip("#").strip()
                section_content = []
            elif current_section:
                section_content.append(line)

            i += 1

        # Don't forget the last section
        if current_section and section_content:
            lessons.extend(
                self._parse_section_content(
                    "\n".join(section_content),
                    current_section,
                    session_file,
                ),
            )

        return lessons

    def _extract_from_patterns(
        self,
        transcript: str,
        session_file: Path,
    ) -> list[ExtractedLesson]:
        """Extract lessons by scanning for patterns."""
        lessons = []
        seen = set()  # Deduplicate by content hash

        # Try each pattern type
        pattern_groups = [
            (self.LEARNING_PATTERNS, "learning"),
            (self.INSIGHT_PATTERNS, "insight"),
            (self.CORRECTION_PATTERNS, "correction"),
            (self.PATTERN_PATTERNS, "pattern"),
        ]

        for patterns, entry_type in pattern_groups:
            for pattern in patterns:
                matches = re.finditer(pattern, transcript, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    content = match.group(0).strip()
                    if len(content) < 20:  # Skip very short matches
                        continue

                    # Deduplicate
                    content_hash = hash(content.lower())
                    if content_hash in seen:
                        continue
                    seen.add(content_hash)

                    lessons.append(
                        ExtractedLesson(
                            entry_type=entry_type,
                            title=self._generate_title(content, entry_type),
                            content=content,
                            metadata={
                                "match_pattern": pattern,
                                "extraction_type": "pattern_match",
                            },
                            source_file=str(session_file.name),
                            extracted_at=datetime.now(tz=UTC).isoformat(),
                        ),
                    )

        return lessons

    def _parse_section_content(
        self,
        content: str,
        section_type: str,
        session_file: Path,
    ) -> list[ExtractedLesson]:
        """Parse section content and create appropriate lessons."""
        lessons = []
        lines = content.strip().split("\n")

        # Clean up the content (remove bullet points, numbering, etc.)
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Remove list markers
            line = re.sub(r"^[\-\*\+•]\s+", "", line)
            line = re.sub(r"^\d+[\.\)]\s+", "", line)
            if line:
                cleaned_lines.append(line)

        cleaned_content = "\n".join(cleaned_lines)

        # Categorize based on section type
        section_lower = section_type.lower()
        if any(h in section_lower for h in ["summary", "conclusions", "lessons learned"]):
            # Split into individual lessons
            lesson_texts = self._split_into_lessons(cleaned_content)
            for lesson_text in lesson_texts:
                lessons.append(
                    ExtractedLesson(
                        entry_type="learning",
                        title=self._generate_title(lesson_text, "learning", section_type),
                        content=lesson_text,
                        metadata={"section": section_type},
                        source_file=str(session_file.name),
                        extracted_at=datetime.now(tz=UTC).isoformat(),
                    ),
                )
        elif any(h in section_lower for h in ["findings", "results"]):
            lessons.append(
                ExtractedLesson(
                    entry_type="insight",
                    title=f"{section_type} from session",
                    content=cleaned_content,
                    metadata={"section": section_type},
                    source_file=str(session_file.name),
                    extracted_at=datetime.now(tz=UTC).isoformat(),
                ),
            )
        elif any(h in section_lower for h in ["action items", "next steps", "recommendations"]):
            lessons.append(
                ExtractedLesson(
                    entry_type="pattern",
                    title=f"{section_type} from session",
                    content=cleaned_content,
                    metadata={"section": section_type},
                    source_file=str(session_file.name),
                    extracted_at=datetime.now(tz=UTC).isoformat(),
                ),
            )

        return lessons

    def _split_into_lessons(self, content: str) -> list[str]:
        """Split section content into individual lessons."""
        lessons = []
        current_lesson = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                if current_lesson:
                    lessons.append(" ".join(current_lesson))
                    current_lesson = []
            elif line[0].isupper() and len(line) < 50 and not line.endswith("."):
                # Likely a new lesson (starts with capital letter, short)
                if current_lesson:
                    lessons.append(" ".join(current_lesson))
                current_lesson = [line]
            else:
                current_lesson.append(line)

        if current_lesson:
            lessons.append(" ".join(current_lesson))

        return [l for l in lessons if len(l) > 30]

    def _generate_title(
        self,
        content: str,
        entry_type: str,
        context: str = "",
    ) -> str:
        """Generate a title for the extracted lesson."""
        # Take first ~50 chars and make it a title
        title = content[:50].strip()
        if len(title) < 30:
            title = content.split(".")[0].strip()[:60]

        # Add type prefix
        type_prefix = {
            "learning": "Learning",
            "insight": "Insight",
            "correction": "Correction",
            "pattern": "Pattern",
        }.get(entry_type, "Note")

        if context and context not in title:
            return f"{type_prefix}: {title}"

        return f"{type_prefix}: {title}"

    def extract_and_store(
        self,
        session_file: Path | str,
    ) -> dict[str, Any]:
        """Extract lessons from session and store them in CKS.

        Args:
            session_file: Path to the session JSONL file

        Returns:
            Dictionary with extraction results

        """
        session_file = Path(session_file)

        print(f"\n📖 Extracting lessons from: {session_file.name}")
        print("=" * 50)

        lessons = self.extract_session(session_file)

        if not lessons:
            print("✓ No lessons found in this session")
            return {
                "session_file": str(session_file),
                "lessons_extracted": 0,
                "lessons_stored": 0,
            }

        results = {
            "session_file": str(session_file),
            "lessons_extracted": len(lessons),
            "lessons_stored": 0,
            "by_type": {},
            "errors": [],
        }

        for lesson in lessons:
            try:
                entry_id = lesson.store(self.cks)
                results["lessons_stored"] += 1
                results["by_type"][lesson.entry_type] = (
                    results["by_type"].get(lesson.entry_type, 0) + 1
                )
                print(f"  ✓ [{lesson.entry_type}] {lesson.title[:60]}...")
            except Exception as e:
                results["errors"].append(str(e))
                print(f"  ✗ Failed to store: {lesson.title[:60]}...")

        print()
        print("📊 Results:")
        print(f"  Extracted: {results['lessons_extracted']}")
        print(f"  Stored: {results['lessons_stored']}")
        if results["by_type"]:
            print("  By type:")
            for entry_type, count in results["by_type"].items():
                print(f"    - {entry_type}: {count}")

        return results


def find_current_session() -> Path | None:
    """Find the current Claude Code session transcript file.

    The current session can be found by:
    1. Checking CLAUDE_SESSION_ID environment variable
    2. Looking for the most recent session in the projects directory

    Returns:
        Path to the current session JSONL file, or None if not found

    """
    # Try environment variable first
    session_id = os.environ.get("CLAUDE_SESSION_ID")
    if session_id:
        # Look in projects directory
        projects_dir = Path("C:/Users/brsth/.claude/projects")
        if projects_dir.exists():
            session_file = projects_dir / f"{session_id}.jsonl"
            if session_file.exists():
                return session_file

    # Fallback: find most recently modified session
    projects_dir = Path("C:/Users/brsth/.claude/projects")
    if projects_dir.exists():
        session_files = list(projects_dir.glob("*.jsonl"))
        if session_files:
            return max(session_files, key=lambda p: p.stat().st_mtime)

    return None


def extract_session_lessons(session_file: Path | str | None = None) -> dict[str, Any]:
    """Convenience function to extract and store lessons from current session.

    Args:
        session_file: Path to session file (auto-detects if None)

    Returns:
        Dictionary with extraction results

    """
    if session_file is None:
        session_file = find_current_session()

    if session_file is None:
        return {
            "error": "No session file found",
            "session_file": None,
            "lessons_extracted": 0,
            "lessons_stored": 0,
        }

    extractor = SessionLessonExtractor()
    return extractor.extract_and_store(session_file)


# Quick CLI interface
def main():
    """CLI entry point for session extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract lessons from Claude Code session and store in CKS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "session_file",
        nargs="?",
        type=str,
        help="Path to session JSONL file (auto-detects if not provided)",
    )

    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect current session (default behavior)",
    )

    args = parser.parse_args()

    if args.auto_detect or not args.session_file:
        session_file = find_current_session()
        if not session_file:
            print("❌ No session file found")
            print("\nHint: Ensure CLAUDE_SESSION_ID is set or run from project directory")
            return
    else:
        session_file = Path(args.session_file)

    # Extract and store
    results = extract_session_lessons(session_file)

    # Show summary
    print()
    if "error" in results:
        print(f"❌ {results['error']}")
    else:
        print("✓ Session extraction complete")
        if results.get("lessons_stored", 0) > 0:
            print()
            print("Search your lessons with:")
            print("  python -m cks.cks_cli query lessons")
            print('  /cks "session learnings"')


if __name__ == "__main__":
    main()
