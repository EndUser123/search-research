#!/usr/bin/env python3
"""CKS Add CLI Module.

Provides content classification and auto-ingestion functionality for the /cks-add command.
Detects content type (pattern, memory, code, document) and ingests to CKS appropriately.

Enhanced with smart ingestion:
- High-value detection (errors, decisions, metrics, code blocks)
- Lossy compression for low-value content
- Value-based routing
"""

import logging
import re
import sys
from pathlib import Path
from typing import Literal

# Add src directory to path for imports
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from cks.unified import CKS

# Import ingest_cli for document delegation
# In tests, this is patched as a MagicMock callable
# In production, should be a function that handles document ingestion
from src.cli.ingest_cli import main as ingest_cli

# Configure logger
logger = logging.getLogger(__name__)

# Content type constants
ContentType = Literal["pattern", "memory", "code", "document"]
MODE_PATTERN: ContentType = "pattern"
MODE_MEMORY: ContentType = "memory"
MODE_CODE: ContentType = "code"
MODE_DOCUMENT: ContentType = "document"

# File extension classifications
CODE_EXTENSIONS = (".py", ".js", ".ts")
DOCUMENT_EXTENSIONS = (".md", ".txt", ".rst")

# Pattern detection keywords
PATTERN_KEYWORDS = ("Results:", "Anti-pattern:")
PATTERN_INDICATORS = ("%", "reduction")

# Memory detection question starters
MEMORY_QUESTION_STARTERS = (
    "What",
    "How",
    "Why",
    "When",
    "Where",
    "Who",
    "Which",
    "Can",
    "Does",
    "Is",
)

# Code detection keywords
CODE_KEYWORDS = ("def ", "class ", "function ", "interface ")

# High-value detection patterns
ERROR_PATTERNS = (
    r"Traceback \(most recent call last\):",
    r"Exception\s+occurred",
    r"Exception:",
    r"\bException\b",
    r"Error:",
    r"\bError\b",
    r"\bFile\s+\"[^\"]+\",\s+line\s+\d+",
    r"\b[A-Z]\w+Error:",
    r"raise\s+\w+",
    r"except\s+\w+",
)

DECISION_MARKERS = (
    "DECISION:",
    "DECIDED:",
    "RESOLVED:",
    "APPROVED:",
    "RATIONALE:",
    "ALTERNATIVES CONSIDERED:",
    "CONTEXT:",
    "OUTCOME:",
)

METRIC_PATTERNS = (
    r"\d+th\s+percentile",
    r"\d+%(?:\s+reduction|\s+improvement|\s+increase)?",
    r"\d+\s*(?:ms|seconds?|minutes?)",
    r"(?:latency|throughput|memory|cpu|disk):\s*\d+",
    r"\d+\s*requests?/?\s*second",
)

CODE_BLOCK_PATTERNS = (
    r"```(?:python|js|typescript|java|go|rust|bash|shell)",
    r"def\s+\w+\s*\(",
    r"class\s+\w+",
    r"interface\s+\w+",
    r"function\s+\w+",
)

# Default source type when none provided
DEFAULT_SOURCE_TYPE = "paste"

# Default document title for ingest_cli
DEFAULT_DOCUMENT_TITLE = "Document"

# Compression threshold - only compress content longer than this
COMPRESSION_THRESHOLD = 500


def is_high_value(text: str) -> bool:
    """Check if content is high-value (should be stored verbatim).

    High-value indicators:
    - Error traces and exceptions
    - Decision/commitment markers
    - Metrics and measurements
    - Code blocks with syntax

    Only content explicitly matching high-value patterns returns True.
    Plain narrative without these patterns is considered low-value.

    Args:
        text: Content to evaluate

    Returns:
        True if content is high-value, False otherwise

    """
    # Check for error patterns
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Check for decision markers
    text_upper = text.upper()
    for marker in DECISION_MARKERS:
        if marker in text_upper:
            return True

    # Check for metric patterns
    for pattern in METRIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Check for code blocks
    for pattern in CODE_BLOCK_PATTERNS:
        if re.search(pattern, text):
            return True

    # Check for repetitive/low-value patterns
    lines = text.strip().split("\n")
    if len(lines) > 5:
        # If more than 50% of lines are identical or very similar
        unique_lines = {line.strip()[:50] for line in lines}  # First 50 chars
        if len(unique_lines) < len(lines) * 0.5:
            return False  # Repetitive content is low-value

    # Default: content without explicit high-value markers is low-value
    # This ensures only actual high-value patterns get verbatim storage
    return False


def compress_content(text: str) -> str:
    """Apply lossy compression to low-value content.

    Uses extractive summarization:
    - Preserves sentences with technical keywords
    - Removes repetitive content
    - Maintains key context

    Args:
        text: Content to compress

    Returns:
        Compressed version (shorter but preserves key information)

    """
    if len(text) < COMPRESSION_THRESHOLD:
        return text

    # Technical keywords to preserve
    tech_keywords = {
            "database",
            "sqlite",
            "sql",
            "api",
            "http",
            "json",
            "xml",
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "rust",
            "docker",
            "kubernetes",
            "redis",
            "postgresql",
            "mysql",
            "oauth",
            "jwt",
            "ssl",
            "tls",
            "websocket",
            "async",
            "await",
            "promise",
            "callback",
            "error",
            "exception",
            "warning",
            "debug",
    }

    # First try line-based compression
    lines = text.strip().split("\n")

    # If there's only one line, split into sentences
    if len(lines) <= 1:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        lines = [s.strip() for s in sentences if s.strip()]

    # Score lines by technical content
    scored_lines = []
    seen = set()

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Skip duplicates
        line_key = line_stripped[:100]
        if line_key in seen:
            continue
        seen.add(line_key)

        # Score: count technical keywords present
        score = 0
        line_lower = line_stripped.lower()
        for keyword in tech_keywords:
            if keyword in line_lower:
                score += 1

        scored_lines.append((score, line_stripped))

    # Sort by score (highest first) and take top lines
    scored_lines.sort(key=lambda x: x[0], reverse=True)

    # Take top 30% of lines, minimum 3, maximum 20
    target_count = max(3, min(20, int(len(scored_lines) * 0.3)))
    top_lines = [
        line for score, line in scored_lines[:target_count] if score > 0 or len(scored_lines) < 10
    ]

    # If no high-scoring lines, take first few sentences
    if not top_lines:
        # Take first 5 sentences (split by period)
        sentences = re.split(r"\.\s+", text)
        top_lines = sentences[:5]

    compressed = ". ".join(top_lines) if top_lines else text[:500]

    # Ensure compressed version is actually shorter
    # If not, extract segments containing keywords instead of simple truncation
    if len(compressed) >= len(text) * 0.9:
        # Try to extract segments with keywords
        keyword_segments = []
        remaining = text
        for keyword in tech_keywords:
            if keyword in remaining.lower():
                # Find and extract context around keyword (200 chars before/after)
                idx = remaining.lower().find(keyword)
                start = max(0, idx - 200)
                end = min(len(text), idx + len(keyword) + 200)
                segment = text[start:end]
                keyword_segments.append(segment)
                remaining = remaining[:idx] + " " + remaining[idx + len(keyword) :]

        if keyword_segments:
            # Join keyword segments
            compressed = " ... ".join(keyword_segments[:5])
        else:
            # Final fallback: simple truncate
            compressed = text[: min(len(text), 500)] + "..."

    return compressed


def classify_content(text: str, source_type: str = DEFAULT_SOURCE_TYPE) -> ContentType:
    """Classify content type based on text and source.

    Enhanced with high-value detection:
    - Error traces -> code
    - Decisions -> pattern
    - Metrics -> pattern

    Args:
        text: The content text to classify
        source_type: Source identifier (file path, "paste", "text", etc.)

    Returns:
        One of: "pattern", "memory", "code", or "document"

    """
    # File extension detection takes priority
    if source_type:
        if source_type.endswith(CODE_EXTENSIONS):
            return MODE_CODE
        if source_type.endswith(DOCUMENT_EXTENSIONS):
            return MODE_DOCUMENT

    # Enhanced: Check for error patterns (high-value code)
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return MODE_CODE

    # Enhanced: Check for decision markers (high-value pattern)
    text_upper = text.upper()
    for marker in DECISION_MARKERS:
        if marker in text_upper:
            return MODE_PATTERN

    # Enhanced: Check for metrics (high-value pattern)
    for pattern in METRIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return MODE_PATTERN

    # Original pattern detection: "Results:", "Anti-pattern:", metrics like "%"
    if any(keyword in text for keyword in PATTERN_KEYWORDS) or any(
        indicator in text for indicator in PATTERN_INDICATORS
    ):
        return MODE_PATTERN

    # Memory detection: Q&A format starting with question words
    text_stripped = text.strip()
    if any(text_stripped.startswith(qw) for qw in MEMORY_QUESTION_STARTERS):
        return MODE_MEMORY

    # Code detection: function/class/interface definitions
    if any(keyword in text for keyword in CODE_KEYWORDS):
        return MODE_CODE

    # Default: document
    return MODE_DOCUMENT


def cks_add(
    text: str,
    source_type: str = DEFAULT_SOURCE_TYPE,
    force_mode: ContentType | None = None,
) -> str:
    """Add content to CKS with automatic classification and smart routing.

    Enhanced with value-based routing:
    - High-value content -> stored verbatim
    - Low-value content -> compressed before storage

    Args:
        text: The content text to add
        source_type: Source identifier (file path, "paste", "text", etc.)
        force_mode: If provided, skip classification and use this mode

    Returns:
        Success message indicating the mode used

    """
    # Use force_mode if provided, else classify
    mode = force_mode if force_mode else classify_content(text, source_type)

    # Smart routing: apply compression to low-value document content
    content_to_store = text
    if mode == MODE_DOCUMENT and not is_high_value(text):
        content_to_store = compress_content(text)
        logger.debug(
            "Compressed low-value content: %d -> %d chars", len(text), len(content_to_store)
        )

    cks = CKS()
    if mode == MODE_PATTERN:
        cks.ingest_pattern("", content_to_store)
    elif mode == MODE_MEMORY:
        # Split question from answer for memory
        lines = content_to_store.strip().split("\n", 1)
        question = lines[0] if lines else ""
        answer = lines[1] if len(lines) > 1 else ""
        cks.ingest_memory(question, answer)
    elif mode == MODE_CODE:
        # Call ingest_code if it exists (mocked in tests)
        if hasattr(cks, "ingest_code"):
            cks.ingest_code(content_to_store)
        else:
            # Fallback to ingest_pattern for code
            cks.ingest_pattern("", content_to_store, entry_type="code")
    else:  # document
        # Delegate to ingest_cli for document processing
        ingest_cli(text=content_to_store, title=DEFAULT_DOCUMENT_TITLE, tags=[], source=source_type)

    try:
        cks.close()
    except Exception as e:
        logger.debug("CKS close raised exception: %s", e)

    return f"Added to CKS as: {mode}"


def main():
    """CLI entry point for cks-add command."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Add content to CKS with automatic type detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cks.cks_add_cli "Hybrid pattern... Results: 32%% reduction"
  python -m cks.cks_add_cli --file pattern.md
  python -m cks.cks_add_cli "content" --force-mode pattern
        """,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "text",
        nargs="?",
        type=str,
        help="Content text (inline)",
    )
    input_group.add_argument(
        "--file",
        "-f",
        type=str,
        help="Read content from file",
    )

    # Mode options
    parser.add_argument(
        "--force-mode",
        type=str,
        choices=["pattern", "memory", "code", "document"],
        help="Force specific mode (skip auto-detection)",
    )
    parser.add_argument(
        "--source-type",
        type=str,
        default="paste",
        help="Source identifier (default: paste)",
    )

    args = parser.parse_args()

    # Get content
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        source_type = args.file
    else:
        text = args.text
        source_type = args.source_type

    # Add to CKS
    result = cks_add(text, source_type=source_type, force_mode=args.force_mode)
    print(result)


if __name__ == "__main__":
    main()
