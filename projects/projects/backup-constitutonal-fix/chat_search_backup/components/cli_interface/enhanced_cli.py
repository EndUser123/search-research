from __future__ import annotations

import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from ...domain_models.chat_models import AnalysisSession, SearchRanking, SearchResult
from ..interfaces.chat_interfaces import ICLIProcessor

#!/usr/bin/env python3
"""Enhanced CLI Interface for CHS
Natural language processing with intelligent query understanding and response generation.
"""




# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)



class NaturalLanguageProcessor:
    """Process natural language queries with intent classification."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()

    def _load_intent_patterns(self) -> dict[str, list[str]]:
        """Load intent classification patterns."""
        return {
            "search": [
                r"find|search|look for|show me|get me|what about",
                r"where is|when did|how to|why did|who mentioned",
                r"any.*about|tell me about|information about",
            ],
            "analyze": [
                r"analyze|analysis|pattern|trend|summary",
                r"what.*patterns|how.*changed|statistics|metrics",
                r"conversation analysis|chat analysis|discussion analysis",
            ],
            "compare": [
                r"compare|difference|versus|vs|better|worse",
                r"which.*better|what.*difference|contrast",
            ],
            "export": [
                r"export|save|download|output|file",
                r"create.*file|generate.*report|save.*results",
            ],
            "help": [
                r"help|how to|what can|what do|how do",
                r"instructions|tutorial|guide|explain",
            ],
            "status": [
                r"status|health|performance|statistics",
                r"how.*doing|current.*state|system.*info",
            ],
        }

    def _load_entity_patterns(self) -> dict[str, str]:
        """Load entity extraction patterns."""
        return {
            "time_period": r"(today|yesterday|this week|last week|this month|last month|recent|lately)",
            "context": r"(project|technical|general|debugging|planning|research)",
            "time_range": r"(last (\d+) (days|weeks|months)|between (\d{4}-\d{2}-\d{2}) and (\d{4}-\d{2}-\d{2}))",
            "format": r"(json|markdown|csv|text|table)",
            "limit": r"(top (\d+)|first (\d+)|limit (\d+)|only (\d+))",
            "ranking": r"(by relevance|by recency|by frequency|most relevant|most recent)",
            "technical_terms": r"(python|docker|kubernetes|api|database|git|test|deploy)",
        }

    def parse_natural_language_query(self, query: str) -> dict[str, Any]:
        """Parse natural language query into structured format."""
        query.lower()

        # Classify intent
        intent = self.classify_intent(query)

        # Extract entities
        entities = self.extract_entities(query)

        # Extract core search terms
        search_terms = self.extract_search_terms(query)

        # Determine query complexity
        complexity = self.assess_query_complexity(query, entities)

        # Generate query structure
        parsed_query = {
            "original_query": query,
            "intent": intent,
            "search_terms": search_terms,
            "entities": entities,
            "complexity": complexity,
            "filters": self.build_filters_from_entities(entities),
            "output_preferences": self.extract_output_preferences(query),
            "confidence": self.calculate_parse_confidence(
                intent, entities, search_terms
            ),
        }

        self.logger.info(
            f"Parsed query with intent '{intent}' and confidence {parsed_query['confidence']:.2f}"
        )
        return parsed_query

    def classify_intent(self, query: str) -> str:
        """Classify user intent from query."""
        query_lower = query.lower()
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            intent_scores[intent] = score

        # Return intent with highest score, default to 'search'
        if max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        return "search"

    def extract_entities(self, query: str) -> dict[str, Any]:
        """Extract entities from natural language query."""
        entities = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches

        # Extract quoted phrases as search terms
        quoted_phrases = re.findall(r'"([^"]+)"', query)
        if quoted_phrases:
            entities["quoted_phrases"] = quoted_phrases

        # Extract code references
        code_refs = re.findall(r"`([^`]+)`", query)
        if code_refs:
            entities["code_references"] = code_refs

        return entities

    def extract_search_terms(self, query: str) -> list[str]:
        """Extract core search terms from query."""
        # Remove intent words and stop words
        stop_words = {
            "find",
            "search",
            "show",
            "get",
            "me",
            "about",
            "what",
            "how",
            "when",
            "where",
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "to",
            "are",
            "as",
            "was",
            "were",
            "will",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
        }

        # Extract quoted phrases first
        quoted_terms = re.findall(r'"([^"]+)"', query)

        # Extract code references
        code_terms = re.findall(r"`([^`]+)`", query)

        # Clean query and extract remaining terms
        clean_query = re.sub(
            r'"[^"]+"|`[^`]+`', "", query
        )  # Remove quoted and code content
        clean_query = re.sub(
            r"[^\w\s]", " ", clean_query
        )  # Replace punctuation with spaces

        words = clean_query.lower().split()
        filtered_words = [
            word for word in words if word not in stop_words and len(word) > 2
        ]

        # Combine all terms
        all_terms = quoted_terms + code_terms + filtered_words

        return list(set(all_terms))  # Remove duplicates

    def assess_query_complexity(self, query: str, entities: dict[str, Any]) -> str:
        """Assess query complexity."""
        complexity_score = 0

        # Length factor
        if len(query) > 100:
            complexity_score += 2
        elif len(query) > 50:
            complexity_score += 1

        # Entity factor
        complexity_score += len(entities)

        # Multiple entities increase complexity
        if len(entities) > 3:
            complexity_score += 2
        elif len(entities) > 1:
            complexity_score += 1

        # Complex patterns
        if re.search(r"\b(and|or|but|while|if|when)\b", query.lower()):
            complexity_score += 1

        if complexity_score >= 4:
            return "complex"
        if complexity_score >= 2:
            return "moderate"
        return "simple"

    def build_filters_from_entities(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Build search filters from extracted entities."""
        filters = {}

        # Time period filter
        if "time_period" in entities:
            time_period = entities["time_period"][0].lower()
            if time_period == "today":
                filters["session_filter"] = "today"
            elif time_period == "yesterday":
                filters["session_filter"] = "yesterday"
            elif "week" in time_period:
                filters["session_filter"] = "week"
            elif "month" in time_period:
                filters["session_filter"] = "month"
            elif time_period in ["recent", "lately"]:
                filters["session_filter"] = "week"

        # Context filter
        if "context" in entities:
            context = entities["context"][0].lower()
            filters["context_filter"] = context

        # Time range filter
        if "time_range" in entities:
            # Parse complex time ranges
            time_range = entities["time_range"][0]
            if isinstance(time_range, tuple):
                if len(time_range) == 3 and time_range[1].isdigit():
                    # "last X days/weeks/months"
                    filters["time_range"] = {
                        "type": "relative",
                        "value": int(time_range[1]),
                        "unit": time_range[2],
                    }
                elif len(time_range) >= 5:
                    # "between date and date"
                    filters["time_range"] = {
                        "type": "absolute",
                        "start": time_range[3],
                        "end": time_range[4],
                    }

        # Format preference
        if "format" in entities:
            filters["output_format"] = entities["format"][0]

        # Limit preference
        if "limit" in entities:
            limit_match = entities["limit"][0]
            if isinstance(limit_match, tuple):
                for value in limit_match:
                    if value.isdigit():
                        filters["limit"] = int(value)
                        break

        # Ranking preference
        if "ranking" in entities:
            ranking = entities["ranking"][0].lower()
            if "relevance" in ranking:
                filters["ranking"] = SearchRanking.RELEVANCE
            elif "recent" in ranking:
                filters["ranking"] = SearchRanking.RECENCY
            elif "frequency" in ranking:
                filters["ranking"] = SearchRanking.FREQUENCY

        return filters

    def extract_output_preferences(self, query: str) -> dict[str, Any]:
        """Extract output format preferences."""
        preferences = {}

        # Look for explicit format requests
        format_indicators = {
            "table": r"\btable\b",
            "list": r"\blist\b",
            "detailed": r"\bdetailed\b|\bverbose\b",
            "summary": r"\bsummary\b|\bbrief\b",
            "examples": r"\bexample[s]?\b|\bsample[s]?\b",
        }

        for format_type, pattern in format_indicators.items():
            if re.search(pattern, query.lower()):
                preferences[format_type] = True

        return preferences

    def calculate_parse_confidence(
        self, intent: str, entities: dict[str, Any], search_terms: list[str]
    ) -> float:
        """Calculate confidence in parse quality."""
        confidence = 0.5  # Base confidence

        # Intent clarity
        if intent != "search":  # Specific intents are more confident
            confidence += 0.2

        # Entity extraction success
        confidence += min(0.3, len(entities) * 0.1)

        # Search term quality
        confidence += min(0.2, len(search_terms) * 0.05)

        # Bonus for quoted terms
        quoted_terms = len([term for term in search_terms if " " in term])
        confidence += min(0.1, quoted_terms * 0.05)

        return min(1.0, confidence)


class ResponseFormatter:
    """Format search results and analysis for display."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def format_results(
        self,
        results: list[SearchResult],
        format_type: str = "text",
        preferences: dict[str, Any] | None = None,
    ) -> str:
        """Format search results for display."""
        if not results:
            return "No results found."

        preferences = preferences or {}

        if format_type == "json":
            return self._format_json(results, preferences)
        if format_type == "markdown":
            return self._format_markdown(results, preferences)
        if format_type == "table" or preferences.get("table"):
            return self._format_table(results, preferences)
        if preferences.get("list"):
            return self._format_list(results, preferences)
        if preferences.get("detailed"):
            return self._format_detailed(results, preferences)
        if preferences.get("summary"):
            return self._format_summary(results, preferences)
        return self._format_text(results, preferences)

    def _format_text(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results as plain text."""
        output = f"Found {len(results)} results:\n\n"

        for i, result in enumerate(results, 1):
            timestamp = datetime.fromtimestamp(
                result.message.timestamp / 1000
            ).strftime("%Y-%m-%d %H:%M")
            context = result.message.context.value
            project = result.message.project_name or "General"

            output += (
                f"{i}. [{timestamp}] ({context}) Score: {result.relevance_score:.2f}\n"
            )
            output += f"   Project: {project}\n"

            if result.matched_terms:
                output += f"   Matched: {', '.join(result.matched_terms[:5])}\n"

            # Content preview
            content = result.message.content
            if len(content) > 200:
                content = content[:200] + "..."
            output += f"   {content}\n\n"

        return output

    def _format_json(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results as JSON."""
        results_data = []
        for result in results:
            result_data = {
                "rank": results.index(result) + 1,
                "message": result.message.to_dict(),
                "relevance_score": result.relevance_score,
                "matched_terms": result.matched_terms,
                "semantic_similarity": result.semantic_similarity,
                "temporal_relevance": result.temporal_relevance,
                "confidence": result.confidence_score,
            }
            results_data.append(result_data)

        return json.dumps(
            {
                "total_results": len(results),
                "generated_at": datetime.now().isoformat(),
                "results": results_data,
            },
            indent=2,
            ensure_ascii=False,
        )

    def _format_markdown(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results as Markdown."""
        output = "# Search Results\n\n"
        output += f"**Found:** {len(results)} results  \n"
        output += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for i, result in enumerate(results, 1):
            timestamp = datetime.fromtimestamp(
                result.message.timestamp / 1000
            ).strftime("%Y-%m-%d %H:%M")
            context = result.message.context.value
            project = result.message.project_name or "General"

            output += f"## {i}. Score: {result.relevance_score:.2f}\n\n"
            output += f"**Time:** {timestamp}  \n"
            output += f"**Context:** {context}  \n"
            output += f"**Project:** {project}  \n"

            if result.matched_terms:
                output += f"**Matched:** {', '.join(result.matched_terms[:5])}  \n"

            output += f"**Content:**\n{result.message.content}\n\n"
            output += "---\n\n"

        return output

    def _format_table(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results as table."""
        if not results:
            return "No results to display in table format."

        # Calculate column widths
        max_time_width = 16
        max_context_width = 12
        max_score_width = 8
        max_content_width = 50

        rows = []
        for result in results:
            timestamp = datetime.fromtimestamp(
                result.message.timestamp / 1000
            ).strftime("%m-%d %H:%M")
            content = result.message.content.replace("\n", " ")[:max_content_width]
            if len(result.message.content) > max_content_width:
                content += "..."

            rows.append(
                [
                    timestamp,
                    result.message.context.value[:max_context_width],
                    f"{result.relevance_score:.2f}",
                    content,
                ],
            )

        # Build table
        header = ["Time", "Context", "Score", "Content"]
        widths = [max_time_width, max_context_width, max_score_width, max_content_width]

        # Header row
        output = (
            "│ "
            + " │ ".join(header[i].ljust(widths[i]) for i in range(len(header)))
            + " │\n"
        )

        # Separator
        output += (
            "├─" + "─┼─".join("─" * widths[i] for i in range(len(widths))) + "─┤\n"
        )

        # Data rows
        for row in rows:
            output += (
                "│ "
                + " │ ".join(str(row[i]).ljust(widths[i]) for i in range(len(row)))
                + " │\n"
            )

        return output

    def _format_list(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results as simple list."""
        output = f"Search Results ({len(results)} items):\n\n"

        for i, result in enumerate(results, 1):
            timestamp = datetime.fromtimestamp(
                result.message.timestamp / 1000
            ).strftime("%m-%d %H:%M")
            content_preview = result.message.content.replace("\n", " ")[:100]
            if len(result.message.content) > 100:
                content_preview += "..."

            output += f"{i}. [{timestamp}] {content_preview} (Score: {result.relevance_score:.2f})\n"

        return output

    def _format_detailed(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results with detailed information."""
        output = f"Detailed Search Results ({len(results)} items):\n\n"

        for i, result in enumerate(results, 1):
            timestamp = datetime.fromtimestamp(
                result.message.timestamp / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")

            output += f"{'=' * 60}\n"
            output += f"Result {i} - Score: {result.relevance_score:.3f}\n"
            output += f"{'=' * 60}\n\n"

            output += f"Timestamp: {timestamp}\n"
            output += f"Context: {result.message.context.value}\n"
            output += f"Project: {result.message.project_name or 'N/A'}\n"
            output += f"Message Type: {result.message.message_type.value}\n"
            output += f"Intensity: {result.message.intensity_score:.2f}\n"

            if result.matched_terms:
                output += f"Matched Terms: {', '.join(result.matched_terms)}\n"

            semantic_tags = result.message.semantic_tags
            if semantic_tags:
                output += f"Semantic Tags: {', '.join(result.semantic_tags)}\n"

            output += f"Semantic Similarity: {result.semantic_similarity:.3f}\n"
            output += f"Temporal Relevance: {result.temporal_relevance:.3f}\n"
            output += f"Confidence: {result.confidence_score:.3f}\n\n"

            output += f"Content:\n{result.message.content}\n\n"

            if result.evidence_sources:
                output += f"Evidence Sources: {', '.join(result.evidence_sources)}\n\n"

        return output

    def _format_summary(
        self, results: list[SearchResult], preferences: dict[str, Any]
    ) -> str:
        """Format results as summary."""
        if not results:
            return "No results found."

        # Analyze results for summary
        contexts = Counter([r.message.context.value for r in results])
        projects = Counter([r.message.project_name or "General" for r in results])
        avg_score = np.mean([r.relevance_score for r in results])

        # Time range
        timestamps = [r.message.timestamp for r in results]
        earliest = datetime.fromtimestamp(min(timestamps) / 1000)
        latest = datetime.fromtimestamp(max(timestamps) / 1000)

        output = f"Search Summary ({len(results)} results)\n"
        output += f"{'=' * 40}\n\n"
        output += f"Time Range: {earliest.strftime('%Y-%m-%d %H:%M')} to {latest.strftime('%Y-%m-%d %H:%M')}\n"
        output += f"Average Score: {avg_score:.2f}\n\n"

        output += "Context Distribution:\n"
        for context, count in contexts.most_common():
            output += f"  {context}: {count} ({count / len(results) * 100:.1f}%)\n"

        output += "\nProject Distribution:\n"
        for project, count in projects.most_common(5):
            output += f"  {project}: {count}\n"

        # Top matches
        output += "\nTop 3 Results:\n"
        for i, result in enumerate(results[:3], 1):
            timestamp = datetime.fromtimestamp(
                result.message.timestamp / 1000
            ).strftime("%m-%d %H:%M")
            content_preview = result.message.content.replace("\n", " ")[:80]
            if len(result.message.content) > 80:
                content_preview += "..."

            output += f"  {i}. [{timestamp}] {content_preview} (Score: {result.relevance_score:.2f})\n"

        return output

    def generate_summary(self, session: AnalysisSession) -> str:
        """Generate summary of analysis session."""
        summary = "# Analysis Session Summary\n\n"
        summary += f"**Query:** {session.query}\n"
        summary += f"**Session ID:** {session.session_id}\n"
        summary += f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if session.completed_at:
            summary += (
                f"**Completed:** {session.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            summary += f"**Processing Time:** {session.processing_time_ms}ms\n"

        summary += f"**Cache Hit:** {'Yes' if session.cache_hit else 'No'}\n\n"

        # Results summary
        if session.results:
            summary += "## Results Summary\n\n"
            summary += f"**Total Results:** {len(session.results)}\n"
            summary += f"**Average Score:** {np.mean([r.relevance_score for r in session.results]):.3f}\n"

            # Context distribution
            contexts = Counter([r.message.context.value for r in session.results])
            summary += f"**Contexts:** {', '.join(f'{ctx}({count})' for ctx, count in contexts.most_common())}\n\n"

        # Patterns summary
        if session.patterns:
            summary += "## Patterns Found\n\n"
            for pattern in session.patterns[:5]:  # Top 5 patterns
                summary += f"- **{pattern.pattern_type}**: {pattern.description} "
                summary += f"(Confidence: {pattern.confidence:.2f}, Frequency: {pattern.frequency})\n"
            summary += "\n"

        # Temporal insights
        if session.temporal_metrics:
            summary += "## Temporal Insights\n\n"
            avg_intensity = np.mean(
                [m.intensity_average for m in session.temporal_metrics]
            )
            total_messages = sum(m.message_count for m in session.temporal_metrics)
            summary += f"**Average Intensity:** {avg_intensity:.3f}\n"
            summary += f"**Total Messages:** {total_messages}\n"
            summary += f"**Time Buckets:** {len(session.temporal_metrics)}\n\n"

        # Knowledge graph insights
        if session.knowledge_graph:
            graph = session.knowledge_graph
            summary += "## Knowledge Graph\n\n"
            summary += f"**Nodes:** {graph.node_count}\n"
            summary += f"**Edges:** {graph.edge_count}\n"
            summary += f"**Clusters:** {graph.cluster_count}\n"
            summary += f"**Modularity:** {graph.modularity:.3f}\n\n"

        # User feedback
        if session.user_feedback:
            summary += "## User Feedback\n\n"
            summary += f"{session.user_feedback}\n\n"

        # Evidence and confidence
        summary += "## Evidence & Validation\n\n"
        summary += f"**Confidence Score:** {session.confidence_score:.3f}\n"
        summary += f"**Validation Status:** {session.validation_status}\n"

        if session.evidence_collected:
            summary += (
                f"**Evidence Sources:** {len(session.evidence_collected)} categories\n"
            )

        return summary


class QueryOptimizer:
    """Optimize and improve user queries."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def suggest_query_improvements(
        self, query: str, context: dict[str, Any]
    ) -> list[str]:
        """Suggest improvements to user query."""
        suggestions = []

        # Check for common issues
        query_lower = query.lower()

        # Too short query
        if len(query.strip()) < 5:
            suggestions.append(
                "Consider adding more specific terms to narrow down results"
            )

        # No time filter specified
        if not any(
            indicator in query_lower
            for indicator in ["today", "yesterday", "week", "month", "recent"]
        ):
            suggestions.append(
                "Add a time filter (e.g., 'this week', 'yesterday') for more relevant results"
            )

        # No context specified
        if not any(
            indicator in query_lower
            for indicator in ["project", "technical", "general", "debugging"]
        ):
            suggestions.append(
                "Specify context (e.g., 'technical discussions', 'project work') for better filtering"
            )

        # Suggest quotes for exact phrases
        if " " in query and '"' not in query:
            suggestions.append(
                'Use quotes around phrases for exact matches: "exact phrase"'
            )

        # Suggest technical terms
        if (
            any(term in query_lower for term in ["problem", "issue", "error"])
            and "debugging" not in query_lower
        ):
            suggestions.append("Try adding 'debugging' context for technical issues")

        # Suggest format specification
        if (
            "table" not in query_lower
            and "list" not in query_lower
            and "json" not in query_lower
        ):
            suggestions.append(
                "Add format preference: 'show as table' or 'export as json'"
            )

        # Suggest ranking method
        if (
            "relevant" not in query_lower
            and "recent" not in query_lower
            and "frequent" not in query_lower
        ):
            suggestions.append(
                "Specify ranking: 'most relevant', 'most recent', or 'most frequent'"
            )

        # Check recent context for suggestions
        if "recent_searches" in context:
            recent_terms = [
                search.get("terms", []) for search in context["recent_searches"][-3:]
            ]
            all_recent_terms = [term for terms in recent_terms for term in terms]
            if all_recent_terms:
                suggestions.append(
                    f"Related recent terms: {', '.join(set(all_recent_terms)[:3])}"
                )

        return suggestions

    def expand_query(self, query: str, entities: dict[str, Any]) -> list[str]:
        """Expand query with related terms."""
        expansions = []

        # Technical term expansions
        technical_expansions = {
            "docker": ["container", "image", "kubernetes", "deployment"],
            "python": ["script", "function", "class", "module", "package"],
            "database": ["sql", "query", "table", "index", "migration"],
            "api": ["rest", "endpoint", "service", "request", "response"],
            "git": ["commit", "branch", "merge", "pull", "push"],
            "test": ["testing", "unit", "integration", "coverage", "mock"],
        }

        search_terms = entities.get("search_terms", [])
        for term in search_terms:
            term_lower = term.lower()
            if term_lower in technical_expansions:
                expansions.extend(technical_expansions[term_lower])

        # Context-based expansions
        if "context" in entities:
            context = entities["context"][0].lower()
            if context == "technical":
                expansions.extend(["code", "implement", "develop", "programming"])
            elif context == "debugging":
                expansions.extend(["error", "fix", "debug", "troubleshoot", "issue"])
            elif context == "project":
                expansions.extend(["milestone", "deadline", "feature", "requirement"])

        # Remove duplicates and limit
        return list(set(expansions))[:5]


class EnhancedCLIProcessor(ICLIProcessor):
    """Enhanced CLI processor with natural language capabilities."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.nlp = NaturalLanguageProcessor()
        self.formatter = ResponseFormatter()
        self.optimizer = QueryOptimizer()

    def parse_natural_language_query(self, query: str) -> dict[str, Any]:
        """Parse natural language query into structured format."""
        return self.nlp.parse_natural_language_query(query)

    def classify_intent(self, query: str) -> str:
        """Classify user intent from query."""
        return self.nlp.classify_intent(query)

    def extract_entities(self, query: str) -> dict[str, Any]:
        """Extract entities from natural language query."""
        return self.nlp.extract_entities(query)

    def suggest_query_improvements(
        self, query: str, context: dict[str, Any]
    ) -> list[str]:
        """Suggest improvements to user query."""
        return self.optimizer.suggest_query_improvements(query, context)

    def format_results(
        self, results: list[SearchResult], format_type: str = "text"
    ) -> str:
        """Format search results for display."""
        return self.formatter.format_results(results, format_type)

    def generate_summary(self, session: AnalysisSession) -> str:
        """Generate summary of analysis session."""
        return self.formatter.generate_summary(session)
