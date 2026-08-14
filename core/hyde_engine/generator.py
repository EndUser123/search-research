"""HyDE Generator - Core hypothetical document generation logic.

This module implements the core HyDE generation algorithm without external
dependencies. It uses template-based generation with query analysis to create
hypothetical documents that capture the semantic intent of queries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# Query Analysis
# =============================================================================


@dataclass(frozen=True)
class QueryIntent:
    """Represents the analyzed intent of a query."""

    category: str  # 'how', 'what', 'why', 'when', 'where', 'who', 'list', 'compare'
    domain: str  # 'technical', 'general', 'code', 'debugging'
    complexity: str  # 'simple', 'medium', 'complex'
    keywords: tuple[str, ...]
    entities: tuple[str, ...]
    has_code_context: bool


class QueryAnalyzer:
    """Analyzes queries to determine intent and extract key information."""

    # Intent patterns
    _HOW_PATTERNS = (
        r"\bhow\s+(?:do|can|to|would|might|should|does)\b",
        r"\bhow\s+(?:do|can|to)\s+I\b",
        r"\bimplement\b",
        r"\bcreate\b",
        r"\bbuild\b",
        r"\bwrite\b",
        r"\bdevelop\b",
    )

    _WHAT_PATTERNS = (
        r"\bwhat\s+(?:is|are|was|were|does|do)\b",
        r"\bdefine\b",
        r"\bexplain\b",
        r"\bdescribe\b",
        r"\bmeaning\b",
    )

    _WHY_PATTERNS = (
        r"\bwhy\s+(?:do|does|did|is|are|was|were)\b",
        r"\breason\s+for\b",
        r"\bcause\s+of\b",
        r"\bpurpose\s+of\b",
    )

    _WHEN_PATTERNS = (
        r"\bwhen\s+(?:do|does|did|should|can)\b",
        r"\bappropriate\s+time\b",
        r"\bbest\s+time\b",
    )

    _LIST_PATTERNS = (
        r"\blist\b",
        r"\bshow\s+(?:me|all|the)\b",
        r"\bfind\b",
        r"\bsearch\b",
        r"\bexamples?\b",
        r"\btypes?\s+of\b",
    )

    _COMPARE_PATTERNS = (
        r"\bcompare\b",
        r"\bdifference\b",
        r"\bvs\b\.?",
        r"\bversus\b",
        r"\bbetter\b",
        r"\bbest\b",
        r"\bpros?\s+and\s+cons?\b",
    )

    _DEBUG_PATTERNS = (
        r"\berror\b",
        r"\bbug\b",
        r"\bfix\b",
        r"\bissue\b",
        r"\bproblem\b",
        r"\bdebug\b",
        r"\btroubleshoot\b",
        r"\bnot\s+working\b",
        r"\bfailed\b",
        r"\bexception\b",
    )

    # Technical domain indicators
    _CODE_KEYWORDS = (
        "function",
        "class",
        "method",
        "variable",
        "import",
        "module",
        "api",
        "endpoint",
        "query",
        "database",
        "schema",
        "algorithm",
        "data structure",
        "design pattern",
        "async",
        "sync",
        "thread",
        "process",
        "memory",
        "performance",
        "optimization",
    )

    _LANGUAGE_KEYWORDS = (
        "python",
        "javascript",
        "java",
        "rust",
        "go",
        "typescript",
        "cpp",
        "c++",
        "c#",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "sql",
        "html",
        "css",
        "bash",
        "shell",
        "yaml",
        "json",
        "xml",
    )

    __slots__ = ()

    @classmethod
    def analyze(cls, query: str) -> QueryIntent:
        """Analyze a query to determine its intent and characteristics.

        Args:
            query: The search query to analyze

        Returns:
            QueryIntent object with categorized intent
        """
        query_lower = query.lower()

        # Determine category
        category = cls._determine_category(query_lower)

        # Determine domain
        domain = cls._determine_domain(query_lower)

        # Determine complexity
        complexity = cls._determine_complexity(query)

        # Extract keywords (meaningful words, 3+ chars)
        keywords = tuple(
            w.strip(".,!?;:()[]{}\"'").lower()
            for w in query.split()
            if len(w.strip(".,!?;:()[]{}\"'")) >= 3
        )

        # Extract entities (capitalized words, technical terms)
        entities = cls._extract_entities(query)

        # Check for code context
        has_code_context = cls._has_code_context(query)

        return QueryIntent(
            category=category,
            domain=domain,
            complexity=complexity,
            keywords=keywords,
            entities=entities,
            has_code_context=has_code_context,
        )

    @classmethod
    def _determine_category(cls, query: str) -> str:
        """Determine the query category."""
        if cls._matches_any(query, cls._DEBUG_PATTERNS):
            return "debugging"

        if cls._matches_any(query, cls._COMPARE_PATTERNS):
            return "compare"

        if cls._matches_any(query, cls._HOW_PATTERNS):
            return "how"

        if cls._matches_any(query, cls._WHAT_PATTERNS):
            return "what"

        if cls._matches_any(query, cls._WHY_PATTERNS):
            return "why"

        if cls._matches_any(query, cls._WHEN_PATTERNS):
            return "when"

        if cls._matches_any(query, cls._LIST_PATTERNS):
            return "list"

        return "general"

    @classmethod
    def _determine_domain(cls, query: str) -> str:
        """Determine the query domain."""
        if cls._matches_any(query, cls._DEBUG_PATTERNS):
            return "debugging"

        # Check for programming language keywords
        if any(lang in query for lang in cls._LANGUAGE_KEYWORDS):
            return "code"

        # Check for technical keywords
        if any(kw in query for kw in cls._CODE_KEYWORDS):
            return "technical"

        return "general"

    @classmethod
    def _determine_complexity(cls, query: str) -> str:
        """Determine query complexity based on length and structure."""
        word_count = len(query.split())
        has_conjunctions = any(
            word in query.lower() for word in ("and", "or", "but", "however", "although", "because")
        )
        has_subordination = (
            len(re.findall(r"\b(?:when|while|after|before|if|unless)\b", query.lower())) > 0
        )

        if word_count > 15 or (has_conjunctions and has_subordination):
            return "complex"
        if word_count > 8 or has_conjunctions:
            return "medium"
        return "simple"

    @classmethod
    def _extract_entities(cls, query: str) -> tuple[str, ...]:
        """Extract named entities from the query."""
        # Capitalized words (excluding first word)
        capitalized = tuple(
            m.group()
            for m in re.finditer(r"\b[A-Z][a-z]+\b", query)
            if m.start() > 0  # Not at start
        )

        # Quoted strings
        quoted = tuple(m.group(1) for m in re.finditer(r'"([^"]+)"', query))

        # Code-like identifiers
        identifiers = tuple(
            m.group()
            for m in re.finditer(r"\b[a-z_][a-z0-9_]*\b", query.lower())
            if "_" in m.group() or any(c.isdigit() for c in m.group())
        )

        return tuple(set(capitalized + quoted + identifiers))

    @classmethod
    def _has_code_context(cls, query: str) -> bool:
        """Check if query references code."""
        code_indicators = (
            "()",
            "=>",
            "def ",
            "class ",
            "import ",
            "from ",
            "function(",
            ".py",
            ".js",
        )
        return any(indicator in query for indicator in code_indicators)

    @classmethod
    def _matches_any(cls, text: str, patterns: tuple[str, ...]) -> bool:
        """Check if text matches any of the given patterns."""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


# =============================================================================
# Document Templates
# =============================================================================


@dataclass(slots=True)
class DocumentTemplate:
    """Template for generating hypothetical documents."""

    intent: QueryIntent
    context: str = ""

    def generate_content(self, query: str) -> str:
        """Generate hypothetical document content based on query intent."""
        category = self.intent.category
        domain = self.intent.domain

        # Route to specialized generator
        if category == "debugging":
            return self._debug_template(query)
        if category == "how":
            return self._how_template(query, domain)
        if category == "what":
            return self._what_template(query, domain)
        if category == "why":
            return self._why_template(query)
        if category == "compare":
            return self._compare_template(query)
        if category == "list":
            return self._list_template(query, domain)

        return self._general_template(query)

    def _how_template(self, query: str, domain: str) -> str:
        """Generate 'how-to' style content."""
        topic = self._extract_topic(query)

        if domain == "code":
            return (
                f"To {topic.lower()}, you can use the following approach:\n\n"
                f"1. First, prepare the necessary dependencies and imports.\n"
                f"2. Define the main function or class that handles the core logic.\n"
                f"3. Implement the required methods with proper error handling.\n"
                f"4. Add configuration options and parameters for flexibility.\n"
                f"5. Test the implementation with various input scenarios.\n\n"
                f"Common considerations include performance optimization, "
                f"edge case handling, and code maintainability."
            )

        return (
            f"To {topic.lower()}, follow these steps:\n\n"
            f"First, understand the requirements and gather necessary information. "
            f"Then, choose the appropriate approach based on your specific use case. "
            f"Implement the solution incrementally, testing each component before proceeding. "
            f"Finally, validate the results and make adjustments as needed.\n\n"
            f"Key factors to consider include efficiency, scalability, and maintainability."
        )

    def _what_template(self, query: str, domain: str) -> str:
        """Generate definition/explanation style content."""
        topic = self._extract_topic(query)

        if domain == "code":
            return (
                f"{topic} is a programming concept that provides specific functionality "
                f"within software development. It serves as a fundamental building block "
                f"for implementing various features and algorithms.\n\n"
                f"The main characteristics include modularity, reusability, and "
                f"well-defined interfaces. Common use cases involve data processing, "
                f"application logic, and system integration."
            )

        return (
            f"{topic} refers to a concept or entity that serves a specific purpose "
            f"within its domain. It encompasses key principles and practices that "
            f"guide its application and usage.\n\n"
            f"Understanding {topic.lower()} involves recognizing its core features, "
            f"benefits, and typical use cases. It is commonly applied in scenarios "
            f"where specific requirements must be met efficiently and effectively."
        )

    def _why_template(self, query: str) -> str:
        """Generate explanation of reasons/purposes."""
        topic = self._extract_topic(query)

        return (
            f"The reason for {topic.lower()} stems from specific requirements "
            f"and constraints. This approach addresses particular challenges "
            f"while optimizing for key factors such as performance, maintainability, "
            f"or user experience.\n\n"
            f"Primary benefits include improved efficiency, reduced complexity, "
            f"and better alignment with best practices. The decision is typically "
            f"based on empirical evidence, established patterns, and specific "
            f"contextual needs."
        )

    def _debug_template(self, query: str) -> str:
        """Generate debugging/troubleshooting content."""
        return (
            "To resolve this issue, first identify the root cause by examining "
            "error messages, stack traces, and system logs. Common causes include "
            "incorrect configuration, resource constraints, or logic errors.\n\n"
            "Troubleshooting steps:\n"
            "1. Verify all dependencies and imports are correctly configured.\n"
            "2. Check for typos in variable names and function calls.\n"
            "3. Ensure proper error handling and exception management.\n"
            "4. Review recent changes that might have introduced the issue.\n"
            "5. Test with simplified inputs to isolate the problem.\n\n"
            "If the issue persists, consider consulting documentation, "
            "checking for known issues, or seeking community support."
        )

    def _compare_template(self, query: str) -> str:
        """Generate comparison content."""
        return (
            "When comparing these options, key differences include:\n\n"
            "Performance: Option A typically offers better performance for "
            "large-scale operations, while Option B excels in smaller, "
            "frequent tasks.\n\n"
            "Complexity: Option A has a steeper learning curve but provides "
            "more flexibility. Option B is simpler to implement but may "
            "require workarounds for advanced use cases.\n\n"
            "Ecosystem: Option A has a more mature ecosystem with extensive "
            "libraries and community support. Option B is newer but has "
            "growing adoption.\n\n"
            "Choose based on your specific requirements: performance needs, "
            "team expertise, and long-term maintenance considerations."
        )

    def _list_template(self, query: str, domain: str) -> str:
        """Generate listing/categorization content."""
        topic = self._extract_topic(query)

        if domain == "code":
            return (
                f"Common examples of {topic.lower()} include:\n\n"
                f"1. Basic implementations demonstrating core functionality\n"
                f"2. Advanced patterns for specific use cases\n"
                f"3. Integration examples with popular libraries\n"
                f"4. Performance-optimized variants\n"
                f"5. Edge case handling approaches\n\n"
                f"Each example serves different purposes and should be chosen "
                f"based on the specific requirements of your application."
            )

        return (
            f"Examples of {topic.lower()} include:\n\n"
            f"- Standard approaches that work in most scenarios\n"
            f"- Specialized variants for particular use cases\n"
            f"- Optimized versions for performance-critical situations\n"
            f"- Alternative methods that offer different trade-offs\n\n"
            f"The choice depends on factors such as scale, complexity, "
            f"and specific requirements of your situation."
        )

    def _general_template(self, query: str) -> str:
        """Generate general-purpose content."""
        topic = self._extract_topic(query)

        return (
            f"Regarding {topic.lower()}, this topic encompasses several key aspects "
            f"that are important to understand. The core concepts involve fundamental "
            f"principles that guide its application and usage.\n\n"
            f"Key points to consider include the underlying mechanisms, common use "
            f"cases, and best practices for implementation. Understanding these "
            f"aspects helps in making informed decisions and applying the knowledge "
            f"effectively in practical situations."
        )

    def _extract_topic(self, query: str) -> str:
        """Extract the main topic from the query."""
        # Remove question words and get the core phrase
        topic = query

        # Strip leading question words
        for prefix in ("How do I ", "How to ", "What is ", "What are ", "Why ", "When "):
            if topic.startswith(prefix):
                topic = topic[len(prefix) :]
                break

        # Clean up
        topic = topic.strip()
        topic = re.sub(r"\?$", "", topic)  # Remove trailing question mark
        topic = topic[:1].upper() + topic[1:] if topic else "This topic"

        return topic


# =============================================================================
# HyDE Generator
# =============================================================================


@dataclass(slots=True)
class HyDEGenerator:
    """Generates hypothetical documents for semantic search enhancement."""

    _analyzer: QueryAnalyzer = field(default_factory=QueryAnalyzer)
    _template_cache: dict[str, DocumentTemplate] = field(default_factory=dict)

    def generate(
        self,
        query: str,
        context: str = "",
        max_length: int = 500,
    ) -> str:
        """Generate a hypothetical document for the given query.

        Args:
            query: The search query
            context: Additional context to incorporate
            max_length: Maximum length of generated document

        Returns:
            Generated hypothetical document text
        """
        # Analyze query intent
        intent = self._analyzer.analyze(query)

        # Create template
        cache_key = f"{intent.category}:{intent.domain}:{intent.complexity}"
        if cache_key not in self._template_cache:
            self._template_cache[cache_key] = DocumentTemplate(intent=intent, context=context)

        template = self._template_cache[cache_key]

        # Generate content
        content = template.generate_content(query)

        # Add context if provided
        if context:
            content = f"Context: {context}\n\n{content}"

        # Truncate if necessary
        if len(content) > max_length:
            content = content[:max_length].rsplit(" ", 1)[0] + "..."

        return content

    def batch_generate(
        self,
        queries: list[str],
        context: str = "",
    ) -> list[str]:
        """Generate hypothetical documents for multiple queries.

        Args:
            queries: List of search queries
            context: Additional context for all queries

        Returns:
            List of generated documents
        """
        return [self.generate(q, context) for q in queries]


# =============================================================================
# Public API Functions
# =============================================================================

# Global generator instance
_default_generator: HyDEGenerator | None = None


def get_default_generator() -> HyDEGenerator:
    """Get or create the default HyDE generator instance."""
    global _default_generator
    if _default_generator is None:
        _default_generator = HyDEGenerator()
    return _default_generator


def generate_hyde(
    query: str,
    context: str = "",
    max_length: int = 500,
) -> str:
    """Generate a hypothetical document for semantic search enhancement.

    This function creates a hypothetical "ideal answer" document that captures
    the semantic intent of the query. The generated document can be embedded
    and used for retrieval instead of the raw query, often improving relevance.

    Args:
        query: The search query to generate a hypothetical document for
        context: Optional additional context to guide generation
        max_length: Maximum length of the generated document in characters

    Returns:
        A hypothetical document that represents an ideal answer to the query

    Example:
        >>> hyde = generate_hyde("How do I implement memoization in Python?")
        >>> print(hyde)
        To implement memoization in Python, you can use the following approach...

    Note:
        The generation uses template-based methods without external dependencies.
        For production use with actual embeddings, integrate with your preferred
        embedding model.
    """
    if not query or not query.strip():
        return ""

    generator = get_default_generator()
    return generator.generate(query, context, max_length)
