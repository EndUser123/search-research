"""CKS Query Expansion Module.

Expands queries using synonyms, abbreviations, domain knowledge,
and semantic relationships to improve search recall.
"""

import re
from functools import lru_cache
from typing import Any


# Type definitions for entity terms structure
class EntityData(dict[str, Any]):
    """Entity-specific terminology data structure.

    Expected keys:
        - synonyms: dict[str, list[str]] - term to synonym mappings
        - related_concepts: list[str] - related concept strings
    """

    synonyms: dict[str, list[str]]
    related_concepts: list[str]


class QueryExpander:
    """Expands queries using multiple strategies:
    - Synonym expansion
    - Abbreviation expansion
    - Entity-specific terms
    - Domain knowledge.
    """

    def __init__(self) -> None:
        """Initialize query expander with synonym and abbreviation mappings.

        Pre-compiles regex patterns for performance to avoid N+1 compilation
        on every query expansion.
        """
        self.synonyms = self._load_synonyms()
        self.abbreviations = self._load_abbreviations()
        self.entity_terms = self._load_entity_terms()

        # Pre-compile regex patterns for performance (avoid N+1 compilation)
        self._synonym_patterns: dict[str, re.Pattern[str]] = {}
        for term in self.synonyms:
            if "-" in term:
                self._synonym_patterns[term] = re.compile(
                    r"(?<!\w)" + re.escape(term) + r"(?!\w)",
                    re.IGNORECASE,
                )
            else:
                self._synonym_patterns[term] = re.compile(
                    r"\b" + re.escape(term) + r"\b",
                    re.IGNORECASE,
                )

        self._abbreviation_patterns: dict[str, re.Pattern[str]] = {}
        for abbrev in self.abbreviations:
            self._abbreviation_patterns[abbrev] = re.compile(
                r"\b" + re.escape(abbrev) + r"\b",
            )

        # Pre-compile entity-specific patterns (PERF-001 fix: N+1 pattern compilation)
        self._entity_patterns: dict[str, dict[str, re.Pattern[str]]] = {}
        for entity_slug, entity_data in self.entity_terms.items():
            self._entity_patterns[entity_slug] = {}
            for term in entity_data.get("synonyms", {}).keys():
                self._entity_patterns[entity_slug][term] = re.compile(
                    r"\b" + re.escape(term) + r"\b",
                    re.IGNORECASE,
                )

    def expand_query(
        self,
        query: str,
        entity_slug: str | None = None,
        max_variations: int = 5,
    ) -> list[str]:
        """Generate query variations for better matching.

        Args:
            query: Original search query
            entity_slug: Optional entity to load terms from
            max_variations: Maximum number of variations to return

        Returns:
            List of query variations including original

        """
        variations = {query.lower()}

        # 1. Synonym expansion
        synonym_vars = self._expand_synonyms(query)
        variations.update(synonym_vars)

        # 2. Abbreviation expansion
        abbreviation_vars = self._expand_abbreviations(query)
        variations.update(abbreviation_vars)

        # 3. Entity-specific terms
        if entity_slug and entity_slug in self.entity_terms:
            entity_vars = self._expand_with_entity_terms(query, entity_slug)
            variations.update(entity_vars)

        # 4. Domain-specific expansions
        domain_vars = self._expand_domain_terms(query)
        variations.update(domain_vars)

        # Convert to list with deterministic ordering: prioritize original query,
        # then sort remaining variations by length (shorter first) then alphabetically
        variation_list = list(variations)
        if query.lower() in variation_list:
            variation_list.remove(query.lower())
        result = [query.lower()] + sorted(variation_list, key=lambda x: (len(x), x))
        return result[:max_variations]

    def _expand_synonyms(self, query: str) -> set[str]:
        """Expand query using synonym mappings with word boundary matching."""
        variations: set[str] = set()
        query_lower = query.lower()

        # Use pre-compiled patterns for performance
        for term, synonyms in self.synonyms.items():
            pattern = self._synonym_patterns[term]
            if pattern.search(query_lower):
                for synonym in synonyms:
                    variations.add(pattern.sub(synonym, query_lower))

        return variations

    def _expand_abbreviations(self, query: str) -> set[str]:
        """Expand abbreviations to full terms."""
        variations: set[str] = set()
        query_lower = query.lower()

        # Use pre-compiled patterns for performance
        for abbrev, full_term in self.abbreviations.items():
            pattern = self._abbreviation_patterns[abbrev]
            if pattern.search(query_lower):
                variations.add(pattern.sub(full_term, query_lower))

        return variations

    def _expand_with_entity_terms(self, query: str, entity_slug: str) -> set[str]:
        """Expand query with entity-specific terminology.

        Uses pre-compiled patterns from __init__ for performance (PERF-001 fix).
        """
        variations: set[str] = set()

        if entity_slug not in self.entity_terms:
            return variations

        entity_data = self.entity_terms[entity_slug]
        query_lower = query.lower()

        # Use pre-compiled patterns for performance (PERF-001 fix)
        entity_patterns = self._entity_patterns.get(entity_slug, {})
        for term, synonyms in entity_data.get("synonyms", {}).items():
            pattern = entity_patterns.get(term)
            if pattern and pattern.search(query_lower):
                for synonym in synonyms:
                    variations.add(pattern.sub(synonym, query_lower))

        # Add related concepts
        for concept in entity_data.get("related_concepts", []):
            variations.add(f"{query} {concept}")

        return variations

    def _expand_domain_terms(self, query: str) -> set[str]:
        """Expand query with domain knowledge."""
        variations = set()

        # Database-related expansions
        if re.search(r"\bdb\b", query, re.IGNORECASE):
            variations.update(
                {
                    query.replace("db", "database"),
                    "database management",
                    "data storage",
                    "data persistence",
                }
            )

        # Authentication-related
        if re.search(r"\bauth\b", query, re.IGNORECASE):
            variations.update(
                {
                    query.replace("auth", "authentication"),
                    "user authentication",
                    "login system",
                    "identity verification",
                }
            )

        # Code-related
        if re.search(r"\bcode\b", query, re.IGNORECASE):
            variations.update(
                {
                    "source code",
                    "programming code",
                    "implementation",
                    "codebase",
                }
            )

        # Error-related
        if re.search(r"\berror\b", query, re.IGNORECASE):
            variations.update(
                {
                    query.replace("error", "exception"),
                    "bug fix",
                    "issue resolution",
                    "error handling",
                }
            )

        return variations

    def _load_synonyms(self) -> dict[str, list[str]]:
        """Load synonym mappings for technical terms.

        Note: Includes reverse mappings for async/concurrency terminology
        to map formal terms to common terms that work better with embedding models.
        """
        return {
            "db": ["database", "data store", "persistence layer"],
            "auth": ["authentication", "login", "identity verification", "access control"],
            "timeout": ["time limit", "expiration", "deadline exceeded"],
            "api": ["interface", "endpoint", "service contract"],
            "fix": ["repair", "resolve", "patch", "correction", "solution"],
            "bug": ["error", "issue", "defect", "problem", "fault"],
            "test": ["validation", "verification", "quality check", "assertion"],
            "deploy": ["release", "ship", "rollout", "launch", "production"],
            "config": ["configuration", "settings", "preferences", "options"],
            "cache": ["storage", "buffer", "memoization", "optimization"],
            "log": ["record", "audit trail", "history", "tracking"],
            "async": ["asynchronous", "non-blocking", "parallel"],
            "sync": ["synchronous", "blocking", "sequential"],
            "parse": ["interpret", "read", "decode", "analyze"],
            "render": ["display", "draw", "paint", "visualize"],
            # Reverse mappings: formal terms → common terms for better embeddings
            "asynchronous": ["async"],
            "coroutine": ["async"],
            "non-blocking": ["async"],
            "concurrent": ["parallel"],
            "parallelism": ["parallel"],
            # Priority 1: Additional async/concurrency terminology
            "await": ["async"],
            "future": ["async"],
            "promise": ["async"],
            "callback": ["async"],
            "multiprocess": ["parallel"],
            "thread": ["parallel"],
            "worker": ["parallel"],
            "pool": ["parallel"],
        }

    def _load_abbreviations(self) -> dict[str, str]:
        """Load common abbreviation mappings."""
        return {
            "hyde": "hypothetical document embeddings",
            "octocode": "github repository search",
            "cks": "Constitutional Knowledge System",
            "bert": "Bidirectional Encoder Representations from Transformers",
            "rca": "Root cause analysis",
            "rag": "Retrieval-Augmented Generation",
            "db": "database",
            "auth": "authentication",
            "api": "application programming interface",
            "ui": "user interface",
            "ux": "user experience",
            "http": "hypertext transfer protocol",
            "https": "hypertext transfer protocol secure",
            "sql": "structured query language",
            "nosql": "not only sql",
            "json": "javascript object notation",
            "xml": "extensible markup language",
            "yaml": "yaml ain't markup language",
            "csv": "comma separated values",
            "cli": "command line interface",
            "gui": "graphical user interface",
            "ide": "integrated development environment",
            "vcs": "version control system",
            "ci/cd": "continuous integration continuous deployment",
            "cpu": "central processing unit",
            "gpu": "graphics processing unit",
            "ram": "random access memory",
            "ssd": "solid state drive",
            "hdd": "hard disk drive",
            "os": "operating system",
            "dns": "domain name system",
            "ip": "internet protocol",
            "tcp": "transmission control protocol",
            "udp": "user datagram protocol",
            "jwt": "json web token",
            "oidc": "openid connect",
            "oauth": "open authorization",
            "rest": "representational state transfer",
            "graphql": "graph query language",
            "soap": "simple object access protocol",
            "rpc": "remote procedure call",
            "grpc": "google remote procedure call",
            "moe": "mixture of experts",
            "mos": "mixture of specialists",
        }

    def _load_entity_terms(self) -> dict[str, dict[str, Any]]:
        """Load entity-specific terminology."""
        return {
            "cks": {
                "synonyms": {
                    "cks": ["constitutional knowledge system", "knowledge system"],
                    "entry": ["memory", "knowledge item", "record"],
                    "search": ["query", "retrieve", "lookup", "find"],
                },
                "related_concepts": [
                    "semantic search",
                    "vector embeddings",
                    "entity filtering",
                    "multi-signal ranking",
                ],
            },
            "taskmaster": {
                "synonyms": {
                    "task": ["assignment", "work item", "ticket", "issue"],
                    "naming": ["identifier", "convention", "format"],
                },
                "related_concepts": [
                    "TSK format",
                    "task tracking",
                ],
            },
            "desktop-commander": {
                "synonyms": {
                    "window": ["pane", "tile", "frame"],
                    "focus": ["active", "selected", "current"],
                },
                "related_concepts": [
                    "spiral tiling",
                    "window management",
                ],
            },
            "nse": {
                "synonyms": {
                    "recommendation": ["suggestion", "advice", "guidance"],
                    "engine": ["system", "module", "component"],
                },
                "related_concepts": [
                    "collaborative filtering",
                    "personalization",
                ],
            },
            "cwo12": {
                "synonyms": {
                    "workflow": ["process", "pipeline", "procedure"],
                    "step": ["stage", "phase", "task"],
                },
                "related_concepts": [
                    "task decomposition",
                    "quality gates",
                ],
            },
        }


# Thread-safe singleton using @lru_cache (maxsize=1) for performance
@lru_cache(maxsize=1)
def _get_default_expander() -> QueryExpander:
    """Return cached QueryExpander instance (thread-safe singleton).

    Uses @lru_cache(maxsize=1) for thread-safe lazy initialization.
    The lru_cache decorator ensures only one instance is created and
    provides thread safety through internal locking.
    """
    return QueryExpander()


def get_query_suggestions(query: str, limit: int = 5) -> list[str]:
    """Get query suggestions for autocomplete.

    Args:
        query: Partial query string
        limit: Maximum suggestions to return

    Returns:
        List of suggested query completions

    """
    expander = _get_default_expander()
    return expander.expand_query(query, max_variations=limit)


# Convenience function for integration
def expand_query_if_enabled(query: str, enabled: bool = True, **kwargs: Any) -> list[str]:
    """Expand query only if the feature is enabled.

    Args:
        query: Search query
        enabled: Whether to expand (default: True)
        **kwargs: Additional arguments for QueryExpander.expand_query

    Returns:
        List of query variations

    """
    if not enabled:
        return [query]

    expander = _get_default_expander()
    return expander.expand_query(query, **kwargs)
