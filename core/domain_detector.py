"""Domain detection for query-context-aware constraint surfacing.

Provides DomainClassification with domain tags derived from query content
and intent type. Used to look up constraint entries in CKS that are tagged
with matching domain keywords.

Architecture:
    Query -> IntentClassification -> DomainClassification -> DomainConstraintBackend
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

# ============================================================================
# Domain keywords - maps domain name to triggering keywords
# These are matched against the lowercased query text.
# Order matters: more specific domains should come before general ones.
# ============================================================================

DOMAIN_KEYWORDS: Final[dict[str, list[str]]] = {
    "hook": [
        "hooks.json",
        "pretooluse",
        "posttooluse",
        "stop hook",
        "userpromptsubmit",
        "sessionstart",
        "precompact",
        "stop_hook",
        "hook_runner",
        "hook_system",
        "hook dispatch",
    ],
    "plugin": [
        ".claude-plugin",
        "plugin.json",
        "marketplace",
        "plugin development",
        "cc-model-router",
        "skill-guard",
        "snapshot plugin",
        "bifrost",
    ],
    "constraint": [
        "settings.json",
        "router.py",
        "domain_tags",
        "constraint entry",
        "domain constraint",
        "constraint surfacing",
        "constraint injection",
        "constraint knowledge",
        "proactive constraint",
    ],
    "cks": [
        "cks",
        "knowledge system",
        "decision entry",
        "memory entry",
        "pattern entry",
        "ingest ",
    ],
    "architecture": [
        "architecture",
        "design decision",
        "adr",
        "architectural",
        "system design",
        "component design",
    ],
    "sdcc": [
        "sdlc",
        "tdd",
        "test-driven",
        "testing",
        "test coverage",
        "ci/cd",
        "deployment",
    ],
    "search": [
        "/search",
        "backend",
        "search backend",
        "query router",
        "fts5",
        "semantic search",
        "hybrid search",
    ],
    "refactor": [
        "refactor",
        "rearchitect",
        "redesign",
        "restructure",
        "debt",
        "technical debt",
        "rewrite",
    ],
    "verification": [
        "verify",
        "validate",
        "test",
        "check",
        "audit",
        "inspect",
        "assertion",
        "proof",
    ],
}

# Maximum domains to return per query (prevents overly broad matches)
MAX_DOMAINS_PER_QUERY: Final[int] = 5

# Minimum keyword matches required to claim a domain (prevents noise)
MIN_KEYWORD_MATCHES: Final[int] = 1


@dataclass
class DomainClassification:
    """Result of domain detection from a query.

    Attributes:
        domains: List of matched domain names (e.g. ["hook", "plugin"])
        confidence: Confidence score 0-1 based on keyword density
        matched_keywords: List of (domain, keyword) tuples that matched
    """

    domains: list[str] = field(default_factory=list)
    confidence: float = 0.0
    matched_keywords: list[tuple[str, str]] = field(default_factory=list)

    @property
    def has_constraints(self) -> bool:
        """True if any matched domain is a constraint-carrying domain."""
        return bool(self.domains)


def detect_domain(query: str, intent_type: str | None = None) -> DomainClassification:
    """Detect domain tags from a query string and optional intent type.

    Args:
        query: The search query string
        intent_type: Optional IntentType value to influence domain scoring

    Returns:
        DomainClassification with matched domains and confidence

    Examples:
        >>> dc = detect_domain("hooks.json bug in plugin registration")
        >>> dc.domains
        ["hook", "plugin", "constraint"]

        >>> dc = detect_domain("CKS decision entry for architecture")
        >>> dc.domains
        ["cks", "architecture"]
    """
    if not query or not query.strip():
        return DomainClassification()

    query_lower = query.lower()
    matched_domains: dict[str, int] = {}  # domain -> match count
    all_matched: list[tuple[str, str]] = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        domain_matches = 0
        for kw in keywords:
            if kw.lower() in query_lower:
                domain_matches += 1
                all_matched.append((domain, kw))

        if domain_matches >= MIN_KEYWORD_MATCHES:
            matched_domains[domain] = domain_matches

    # Build ordered domain list (higher match count = higher priority)
    sorted_domains = sorted(
        matched_domains.keys(),
        key=lambda d: matched_domains[d],
        reverse=True,
    )

    # Cap at MAX_DOMAINS_PER_QUERY
    capped_domains = sorted_domains[:MAX_DOMAINS_PER_QUERY]

    # Confidence: base 0.5 + 0.1 per domain + bonus for constraint domain
    # Constraint domain match gets a boost since constraints are high-value
    base_confidence = 0.5
    domain_bonus = len(capped_domains) * 0.1
    constraint_bonus = 0.15 if "constraint" in capped_domains else 0.0
    confidence = min(0.95, base_confidence + domain_bonus + constraint_bonus)

    return DomainClassification(
        domains=capped_domains,
        confidence=round(confidence, 2),
        matched_keywords=all_matched,
    )
