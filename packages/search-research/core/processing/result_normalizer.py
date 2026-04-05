"""Provider result normalization for unified schema.

This module provides the ResultNormalizer which converts raw provider results
into a unified NormalizedResult schema, enabling cross-provider operations
like deduplication, quality scoring, and gap analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse


class SourceType(Enum):
    """Source type classification for results."""
    DOCS = "docs"
    ACADEMIC = "academic"
    COMMUNITY = "community"
    NEWS = "news"
    VENDOR = "vendor"
    VIDEO = "video"
    BLOG = "blog"
    UNKNOWN = "unknown"


@dataclass
class NormalizedResult:
    """Unified result schema from any provider.

    Attributes:
        title: Result title
        snippet: Content snippet or summary
        url: Result URL
        domain: Extracted domain (lowercase)
        source_type: Detected source type (docs, academic, etc.)
        provider: Original provider name
        published_at: Publication date if available
        metadata: Additional metadata (trust_score, original_score, etc.)
    """
    title: str
    snippet: str
    url: str
    domain: str
    source_type: SourceType
    provider: str
    published_at: datetime | None = None
    metadata: dict = field(default_factory=dict)


class ResultNormalizer:
    """Normalize provider results to unified schema."""

    # Domain trust scores for authoritative sources
    DOMAIN_TRUST = {
        "docs.python.org": 0.95,
        "developer.mozilla.org": 0.95,
        "python.org": 0.90,
        "arxiv.org": 0.90,
        "ieee.org": 0.90,
        "acm.org": 0.90,
        "github.com": 0.80,
        "stackoverflow.com": 0.75,
        "reddit.com": 0.60,
        "medium.com": 0.50,
    }

    # Source type detection patterns
    VIDEO_PATTERNS = ["youtube.com", "vimeo.com", "video."]
    ACADEMIC_PATTERNS = ["arxiv.org", "ieee.org", "acm.org", "springer.com", "sciencedirect.com"]
    COMMUNITY_PATTERNS = ["reddit.com", "stackoverflow.com", "github.com", "discord.com"]
    NEWS_PATTERNS = ["news", "bbc.com", "cnn.com", "reuters.com", "apnews.com", "npr.org"]
    DOCS_PATTERNS = ["docs.", "documentation", "/docs/", "/doc/"]
    VENDOR_PATTERNS = ["cloud.google.com", "aws.amazon.com", "azure.microsoft.com", "developer.vmware.com"]
    BLOG_PATTERNS = ["/blog/", "medium.com", "dev.to", "hashnode.dev", "substack.com"]

    def __init__(self) -> None:
        """Initialize normalizer with domain trust scores."""
        self.domain_trust = self.DOMAIN_TRUST.copy()

    def normalize(self, raw_result: dict, provider: str) -> NormalizedResult:
        """Convert raw provider result to normalized schema.

        Args:
            raw_result: Dictionary with keys: url, title, content/snippet
            provider: Provider name (tavily, serper, brave, etc.)

        Returns:
            NormalizedResult with unified schema
        """
        # Extract URL and domain
        url = raw_result.get("url", "")
        domain = self._extract_domain(url)

        # Detect source type
        source_type = self._detect_source_type(url, domain, raw_result)

        # Extract published date
        published_at = self._extract_date(raw_result)

        # Build metadata
        metadata = {
            "trust_score": self.domain_trust.get(domain, 0.5),
            "original_score": raw_result.get("score", 0.5),
        }

        return NormalizedResult(
            title=raw_result.get("title", ""),
            snippet=raw_result.get("content", raw_result.get("snippet", "")),
            url=url,
            domain=domain,
            source_type=source_type,
            provider=provider,
            published_at=published_at,
            metadata=metadata,
        )

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: URL string

        Returns:
            Lowercase domain or empty string
        """
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""

    def _detect_source_type(self, url: str, domain: str, raw_result: dict) -> SourceType:
        """Detect source type from URL patterns and content.

        Args:
            url: Result URL
            domain: Extracted domain
            raw_result: Original result dict

        Returns:
            Detected SourceType
        """
        url_lower = url.lower() if url else ""

        # Video detection
        if any(pattern in url_lower for pattern in self.VIDEO_PATTERNS):
            return SourceType.VIDEO

        # Academic detection
        if any(pattern in url_lower for pattern in self.ACADEMIC_PATTERNS):
            return SourceType.ACADEMIC
        snippet = raw_result.get("snippet", "")
        if snippet and "filetype:pdf" in snippet.lower():
            return SourceType.ACADEMIC

        # Community detection
        if any(pattern in url_lower for pattern in self.COMMUNITY_PATTERNS):
            return SourceType.COMMUNITY

        # News detection
        if any(pattern in url_lower or pattern in domain for pattern in self.NEWS_PATTERNS):
            return SourceType.NEWS

        # Docs detection
        if any(pattern in url_lower for pattern in self.DOCS_PATTERNS):
            return SourceType.DOCS

        # Vendor detection
        if any(pattern in url_lower for pattern in self.VENDOR_PATTERNS):
            return SourceType.VENDOR

        # Blog detection
        if any(pattern in url_lower for pattern in self.BLOG_PATTERNS):
            return SourceType.BLOG

        return SourceType.UNKNOWN

    def _extract_date(self, raw_result: dict) -> datetime | None:
        """Extract publish date from result metadata.

        Args:
            raw_result: Original result dict

        Returns:
            Datetime if found, None otherwise
        """
        # Try common date fields
        date_fields = ["published_at", "date", "publish_date", "timestamp", "pubDate", "datePublished"]

        for field in date_fields:
            if field not in raw_result:
                continue
            date_value = raw_result[field]
            if date_value is None:
                continue
            try:
                if isinstance(date_value, datetime):
                    return date_value
                if isinstance(date_value, str):
                    # Try ISO format
                    return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                if isinstance(date_value, (int, float)):
                    # Unix timestamp
                    return datetime.fromtimestamp(date_value)
            except Exception:
                continue

        return None

    def normalize_batch(self, raw_results: list[dict], provider: str) -> list[NormalizedResult]:
        """Normalize a batch of results from a provider.

        Args:
            raw_results: List of raw result dicts
            provider: Provider name

        Returns:
            List of NormalizedResult objects
        """
        return [self.normalize(r, provider) for r in raw_results]
