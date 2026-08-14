"""Synthesis processor for combining and summarizing search results.

Migrated from research_skill.processors.synthesis (2025-03-08).
"""

import re
from typing import Any

# Graph-of-Thought analysis integration
try:
    from ..processing.got_analysis import GotAnalyzer
    HAS_GOT = True
except ImportError:
    HAS_GOT = False

# Constants for summary generation
_DEFAULT_TOP_RESULTS = 5
_SENTENCES_PER_RESULT = 2
_SUMMARY_SENTENCES = 3
_MIN_SENTENCE_LENGTH = 10
_MIN_INSIGHT_LENGTH = 10
_BULLETS_PER_RESULT = 2
_LONG_SENTENCE_MIN_LENGTH = 15

# Keywords that indicate important content
_INSIGHT_KEYWORDS = [
    'key', 'important', 'essential', 'critical',
    'should', 'must', 'best', 'practice',
]

class SynthesisProcessor:
    """Processor for synthesizing search results.

    Combines, summarizes, and extracts insights from search results.
    """

    def __init__(
        self,
        max_summary_length: int = 500,
        max_insights: int = 5,
    ):
        """Initialize the synthesis processor.

        Args:
            max_summary_length: Maximum length for generated summaries.
            max_insights: Maximum number of key insights to extract.
        """
        self.max_summary_length = max_summary_length
        self.max_insights = max_insights

    def combine_results(
        self,
        results: list,
        query: str = "",
    ) -> str:
        """Combine multiple search results into a single text.

        Args:
            results: List of search results.
            query: The original query (for context).

        Returns:
            Combined content as a string.
        """
        if not results:
            return ""

        # Sort by score descending
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        sections = []
        for result in sorted_results:
            # Add title and content
            title = result.title or "Untitled"
            content = result.content or ""
            url = result.url or ""

            section = f"## {title}\n\n"
            if content:
                section += f"{content}\n\n"
            if url:
                section += f"Source: {url}\n"

            sections.append(section)

        combined = "\n".join(sections)
        return combined

    def generate_summary(
        self,
        results: list,
        max_length: int | None = None,
    ) -> str:
        """Generate a summary from search results.

        Args:
            results: List of search results.
            max_length: Maximum length for the summary.

        Returns:
            Generated summary as a string.
        """
        if not results:
            return ""

        if max_length is None:
            max_length = self.max_summary_length

        # Sort by score and extract top content
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        # Collect key sentences from top results
        sentences = []
        for result in sorted_results[:_DEFAULT_TOP_RESULTS]:  # Use top 5 results
            if result.content:
                # Split into sentences and add first few
                content_sentences = re.split(
                    r'[.!?]+', result.content
                )
                for sent in content_sentences[:_SENTENCES_PER_RESULT]:
                    sent = sent.strip()
                    if sent and len(sent) > _MIN_SENTENCE_LENGTH:
                        sentences.append(sent)

        # Build summary
        if not sentences:
            return "No summary available."

        summary = " ".join(sentences[:_SUMMARY_SENTENCES])  # Use up to 3 sentences

        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."

        return summary

    def extract_key_insights(
        self,
        results: list,
        max_insights: int | None = None,
    ) -> list[str]:
        """Extract key insights from search results.

        Args:
            results: List of search results.
            max_insights: Maximum number of insights to extract.

        Returns:
            List of insight strings.
        """
        if not results:
            return []

        if max_insights is None:
            max_insights = self.max_insights

        insights = []

        # Sort by score descending
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        # Extract insights from top results
        for result in sorted_results:
            if len(insights) >= max_insights:
                break

            if result.content:
                # Look for bullet points, numbered lists, or key sentences
                content = result.content

                # Try to find bullet points
                bullets = re.findall(r'^[\s]*[-*]\s+(.+)$', content, re.MULTILINE)
                if bullets:
                    for bullet in bullets[:_SENTENCES_PER_RESULT]:
                        if len(bullet) > _MIN_INSIGHT_LENGTH:
                            insights.append(bullet)
                            if len(insights) >= max_insights:
                                break

                # If no bullets, extract key sentences
                if len(insights) < max_insights:
                    sentences = re.split(r'[.!?]+', content)
                    for sent in sentences:
                        sent = sent.strip()
                        # Look for sentences with key indicators
                        if any(keyword in sent.lower() for keyword in _INSIGHT_KEYWORDS):
                            if len(sent) > _LONG_SENTENCE_MIN_LENGTH and sent not in insights:
                                insights.append(sent)
                                if len(insights) >= max_insights:
                                    break

        # If still not enough, add first sentences from top results
        if len(insights) < max_insights:
            for result in sorted_results:
                if len(insights) >= max_insights:
                    break
                if result.content:
                    first_sent = result.content.split('.')[0]
                    if len(first_sent) > _LONG_SENTENCE_MIN_LENGTH and first_sent not in insights:
                        insights.append(first_sent)

        return insights[:max_insights]

    def synthesize_with_fetched(
        self,
        results: list,
        query: str = "",
    ) -> str:
        """Synthesize results using fetched full content when available.

        Args:
            results: List of search results (may have fetched content).
            query: The original query.

        Returns:
            Synthesized content.
        """
        if not results:
            return ""

        sections = []

        for result in results:
            # Use fetched full content if available
            if hasattr(result, 'fetched') and result.fetched:
                full_content = result.metadata.get("full_content", "")
                if full_content:
                    sections.append(f"## {result.title}\n\n{full_content}")
                else:
                    sections.append(f"## {result.title}\n\n{result.content}")
            else:
                sections.append(f"## {result.title}\n\n{result.content}")

        return "\n\n".join(sections)

    def synthesize_structured(
        self,
        results: list,
        query: str = "",
    ) -> dict[str, Any]:
        """Generate structured synthesis with sections.

        Args:
            results: List of search results.
            query: The original query.

        Returns:
            Dictionary with structured synthesis.
        """
        if not results:
            return {"summary": "", "insights": [], "sources": []}

        summary = self.generate_summary(results)
        insights = self.extract_key_insights(results)

        # Extract sources
        sources = [
            {"url": r.url, "title": r.title, "source": r.source}
            for r in results if r.url
        ]

        return {
            "summary": summary,
            "insights": insights,
            "sources": sources,
            "overview": summary,
        }



    def synthesize_with_got(
        self,
        results: list,
        query: str = '',
    ) -> dict[str, Any]:
        """Synthesize results with Graph-of-Thought analysis.
        
        Args:
            results: List of search results.
            query: The original query.
            
        Returns:
            Dictionary with GoT-enhanced synthesis including clusters and relationships.
        """
        if not results:
            return {
                'summary': '',
                'insights': [],
                'sources': [],
                'got_analysis': {},
                'got_formatted': ''
            }
        
        # Run GoT analysis if available
        got_analysis = {}
        if HAS_GOT:
            analyzer = GotAnalyzer()
            got_analysis = analyzer.analyze_results(results)
        
        # Get standard synthesis
        summary = self.generate_summary(results)
        insights = self.extract_key_insights(results)
        sources = [
            {'url': r.url, 'title': r.title, 'source': r.source}
            for r in results if r.url
        ]
        
        # Format with GoT metadata
        got_formatted = ''
        if got_analysis and HAS_GOT:
            analyzer = GotAnalyzer()
            got_formatted = analyzer.format_results_with_got(results, got_analysis)
        
        return {
            'summary': summary,
            'insights': insights,
            'sources': sources,
            'got_analysis': got_analysis,
            'got_formatted': got_formatted,
            'overview': summary,
        }

    def synthesize_with_citations(
        self,
        results: list,
        query: str = "",
    ) -> str:
        """Synthesize with source citations.

        Args:
            results: List of search results.
            query: The original query.

        Returns:
            Synthesized content with citations.
        """
        if not results:
            return ""

        sections = []
        for i, result in enumerate(results, 1):
            citation = f"[{i}]"
            title = result.title or "Untitled"
            content = result.content or ""
            source = result.source or "unknown"
            url = result.url or ""

            section = f"{citation} **{title}**\n"
            section += f"{content}\n"
            section += f"Source: {source}"
            if url:
                section += f" ({url})"

            sections.append(section)

        return "\n\n".join(sections)
