"""
Auto-Research Trigger for RCA/Debug Workflow

Detects when external research is needed for debugging by identifying:
1. External library references in errors
2. Knowledge staleness indicators
3. Version/deprecation keywords

This is Option A (heuristic-based) - simple, fast, covers ~80% of cases.
Phase 2 will add Option B (CKS caching) for smart doc storage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

# Fast-moving libraries that change frequently
# These are high-probability candidates for stale knowledge
# Note: Include both hyphen and underscore variants
FAST_MOVING_LIBRARIES = {
    # Python web/frameworks
    "fastapi",
    "django",
    "flask",
    "starlette",
    "aiohttp",
    "httpx",
    # ML/AI
    "torch",
    "tensorflow",
    "keras",
    "scikit-learn",
    "numpy",
    "pandas",
    "openai",
    "anthropic",
    "langchain",
    "llama-index",
    "chromadb",
    # Data/processing
    "pydantic",
    "sqlalchemy",
    "alembic",
    "pytest",
    "uvicorn",
    # YouTube/download tools (common in yt-fts context)
    "yt-dlp",
    "yt_dlp",
    "ytdl",
    "youtube-dl",
    "youtube_dl",
    # CLI tools
    "click",
    "typer",
    "rich",
    # Async/concurrency
    "asyncio",
    "trio",
    "curio",
    # HTTP/API
    "requests",
    "urllib3",  # Cloud services
    "boto3",
    "botocore",
    "azure",
    "google-cloud",
}

# Trigger keywords that suggest version/deprecation issues
STALENESS_KEYWORDS = [
    "deprecated",
    "removed in",
    "changed in",
    "version",
    "not available",
    "no attribute",
    "module has no",
    "unexpected keyword",
    "type annotation",
]


@dataclass
class ResearchTrigger:
    """Result of research trigger analysis."""

    should_research: bool
    confidence: float  # 0.0 to 1.0
    libraries: list[str]
    reason: str
    keywords_found: list[str]


def extract_library_names(text: str) -> list[str]:
    """
    Extract potential library names from error text.

    Looks for:
    - Module names in import errors
    - Package names in AttributeError
    - Known library names

    Returns:
        List of detected library names (lowercase)

    """
    libraries = []
    # Normalize: treat underscores and hyphens the same
    text_normalized = text.lower().replace("_", "-")

    # Direct matches against known libraries
    for lib in FAST_MOVING_LIBRARIES:
        lib_normalized = lib.replace("_", "-")
        if lib_normalized in text_normalized:
            libraries.append(lib_normalized)

    # Extract from ImportError patterns
    # "No module named 'package'" or "cannot import name 'X' from 'Y'"
    import_patterns = [
        r"No module named '([a-zA-Z0-9_-]+)'",
        r"cannot import name '([a-zA-Z0-9_-]+)'",
        r"from '([a-zA-Z0-9_.-]+)'",
        r"ModuleNotFoundError: No module named '([a-zA-Z0-9_.-]+)'",
    ]

    for pattern in import_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Split on dots and take first part (main package)
            pkg = match.split(".")[0].split("-")[0].lower()
            if len(pkg) >= 3:  # Filter out short matches
                libraries.append(pkg)

    # Extract from AttributeError patterns
    # "module 'X' has no attribute 'Y'"
    attr_pattern = r"module '([a-zA-Z0-9_]+)' has no attribute"
    matches = re.findall(attr_pattern, text)
    libraries.extend(m.lower() for m in matches)

    return list(set(libraries))


def should_trigger_research(problem_description: str) -> ResearchTrigger:
    """
    Determine if external research is needed for this problem.

    Args:
        problem_description: The error or problem description

    Returns:
        ResearchTrigger with decision and reasoning

    """
    text = problem_description.lower()
    libraries = extract_library_names(problem_description)
    keywords_found = [kw for kw in STALENESS_KEYWORDS if kw in text]

    # Calculate confidence based on signals
    confidence = 0.0
    reasons = []

    # Signal 1: External library detected
    if libraries:
        confidence += 0.4
        reasons.append(f"External libraries: {', '.join(libraries)}")

    # Signal 2: Fast-moving library (higher weight)
    # Normalize for checking
    fast_moving_libs_normalized = {
        lib.replace("_", "-") for lib in FAST_MOVING_LIBRARIES
    }
    fast_moving = [
        lib for lib in libraries if lib.replace("_", "-") in fast_moving_libs_normalized
    ]
    if fast_moving:
        confidence += 0.3
        reasons.append(f"Fast-moving libs detected: {', '.join(fast_moving)}")

    # Signal 3: Staleness keywords
    if keywords_found:
        confidence += 0.2
        reasons.append(f"Staleness keywords: {', '.join(keywords_found)}")

    # Signal 4: Version/deprecation specific keywords (stronger signal)
    if any(kw in text for kw in ["deprecated", "removed in", "changed in"]):
        confidence += 0.3  # Increased from 0.1 - these are strong signals
        reasons.append("Version change detected")

    # Cap confidence at 1.0
    confidence = min(1.0, confidence)

    # Decision threshold: 0.5 (moderate confidence)
    should_research = confidence >= 0.5

    # Build reason string
    if not reasons:
        reason = "No clear research triggers detected"
    else:
        reason = "; ".join(reasons)

    return ResearchTrigger(
        should_research=should_research,
        confidence=confidence,
        libraries=libraries,
        reason=reason,
        keywords_found=keywords_found,
    )


def build_research_query(libraries: list[str], problem_description: str) -> str:
    """
    Build a web search query for library research.

    Args:
        libraries: List of library names detected
        problem_description: Original problem text

    Returns:
        Search query string

    """
    if not libraries:
        # Fallback: search the problem description
        return f'"{problem_description[:100]}"'

    # Primary library
    primary_lib = libraries[0]

    # Extract error type
    error_type = "error"
    error_patterns = [
        (r"AttributeError", "AttributeError"),
        (r"ImportError", "ImportError"),
        (r"TypeError", "TypeError"),
        (r"ValueError", "ValueError"),
        (r"ModuleNotFoundError", "module not found"),
    ]
    for pattern, name in error_patterns:
        if re.search(pattern, problem_description, re.IGNORECASE):
            error_type = name
            break

    # Build query: "{library} {error_type} {current_year} documentation"
    current_year = datetime.now().year
    return f"{primary_lib} {error_type} {current_year} documentation"


# CLI-style test function
def _test() -> None:
    """Run built-in tests."""
    test_cases = [
        (
            "AttributeError: 'NoneType' object has no attribute 'x'",
            False,
            "internal code",
        ),
        ("yt-dlp option '--format' not available", True, "yt-dlp is fast-moving"),
        (
            "ImportError: cannot import name 'BaseRequest' from 'fastapi'",
            True,
            "fastapi detected",
        ),
        (
            "DeprecationWarning: 'old_method' removed in version 2.0",
            True,
            "deprecation keyword",
        ),
        ("my_function() returns None instead of list", False, "no library refs"),
    ]

    print("Auto-Research Trigger Tests")
    print("=" * 60)

    for problem, expected, note in test_cases:
        result = should_trigger_research(problem)
        status = "✓" if result.should_research == expected else "✗"
        print(f"{status} {expected}: {note}")
        print(f"   Input: {problem[:60]}...")
        print(f"   Confidence: {result.confidence:.2f}, Libraries: {result.libraries}")
        print()


if __name__ == "__main__":
    _test()
