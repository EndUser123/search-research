"""HyDE (Hypothetical Document Embeddings) multi-chapter generation.

This module provides multi-chapter HyDE generation, which creates multiple
hypothetical documents from different predefined aspects (Technical Implementation,
Best Practices, Security, Performance, etc.) for comprehensive query enhancement.

HYDE-C-001: Chapter Generation Configuration
HydeChapterConfig dataclass configures chapter generation with num_chapters,
detail_level, and enable_diversity parameters.

HYDE-C-002: Chapter Data Structure
HydeChapter dataclass stores chapter title, content, and search_focus.

HYDE-C-003: Chapter Generation Function
generate_hyde_chapters() creates multiple chapters from predefined aspects.
"""

from dataclasses import dataclass

# Valid detail levels for chapter generation
_VALID_DETAIL_LEVELS = ("low", "medium", "high")

# Predefined aspects for chapter generation
_PREDEFINED_ASPECTS = [
    "Introduction and Overview",
    "Technical Implementation",
    "Best Practices",
    "Common Challenges",
    "Advanced Techniques",
    "Security Considerations",
    "Performance Optimization",
    "Testing Strategies",
    "Deployment Patterns",
    "Monitoring and Observability",
]


@dataclass
class HydeChapterConfig:
    """Configuration for HyDE chapter generation.

    Attributes:
        num_chapters: Number of chapters to generate.
        detail_level: Level of detail (low, medium, high).
        enable_diversity: Whether to ensure diversity across chapters.
    """

    num_chapters: int = 3
    detail_level: str = "medium"
    enable_diversity: bool = True


@dataclass
class HydeChapter:
    """A single HyDE chapter.

    Attributes:
        title: The chapter title.
        content: The chapter content.
        search_focus: The search focus for this chapter.
    """

    title: str
    content: str
    search_focus: str


def _generate_chapter_content(query: str, aspect: str, detail_level: str) -> str:
    """Generate content for a chapter.

    Args:
        query: The query string.
        aspect: The aspect name.
        detail_level: The detail level.

    Returns:
        Generated content string.
    """
    base_content = f"Content about {aspect} for query: {query}."

    if detail_level == "low":
        return base_content
    elif detail_level == "medium":
        return base_content + " This includes detailed explanations and examples."
    else:  # high
        return (
            base_content
            + " This includes comprehensive explanations, multiple examples, best practices, and in-depth analysis."
        )


def generate_hyde_chapters(
    query: str,
    num_chapters: int = 3,
    detail_level: str = "medium",
    enable_diversity: bool = True,
) -> list[HydeChapter]:
    """Generate HyDE chapters covering different aspects of a query.

    HYDE-C-003: Creates multiple hypothetical documents from predefined aspects.

    Args:
        query: The query string.
        num_chapters: Number of chapters to generate.
        detail_level: Level of detail (low, medium, high).
        enable_diversity: Whether to ensure diversity.

    Returns:
        List of HydeChapter objects.

    Raises:
        ValueError: If query is empty or invalid arguments provided.

    Examples:
        >>> chapters = generate_hyde_chapters("FastAPI patterns", num_chapters=3)
        >>> len(chapters)
        3
        >>> chapters[0].title
        'Introduction and Overview'
    """
    if not query or query.strip() == "":
        raise ValueError("Query cannot be empty")

    valid_detail_levels = list(_VALID_DETAIL_LEVELS)
    if detail_level not in valid_detail_levels:
        raise ValueError(f"Invalid detail_level: {detail_level}. Must be one of {valid_detail_levels}")

    if num_chapters <= 0:
        raise ValueError("num_chapters must be greater than 0")

    chapters = []

    for i in range(min(num_chapters, len(_PREDEFINED_ASPECTS))):
        aspect = _PREDEFINED_ASPECTS[i]
        content = _generate_chapter_content(query, aspect, detail_level)

        chapter = HydeChapter(
            title=aspect,
            content=content,
            search_focus=aspect.lower(),
        )
        chapters.append(chapter)

    return chapters
