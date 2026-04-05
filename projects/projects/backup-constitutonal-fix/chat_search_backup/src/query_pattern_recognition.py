#!/usr/bin/env python3
"""
Query Pattern Recognition and Intelligent Suggestions
Identifies repetitive query patterns and provides intelligent suggestions to reduce search time.
"""

import hashlib
import json
import logging
import re
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class QueryPattern:
    """Represents a detected query pattern"""
    pattern_id: str
    normalized_query: str
    frequency: int
    last_seen: float
    variants: list[str]
    success_metrics: dict[str, float]
    related_queries: list[str]
    suggestion_score: float


@dataclass
class QuerySuggestion:
    """Intelligent query suggestion"""
    suggestion_id: str
    suggested_query: str
    original_query: str
    confidence: float
    reasoning: str
    estimated_time_savings: float
    pattern_id: str | None = None


class QueryPatternRecognizer:
    """Recognizes patterns in search queries and provides intelligent suggestions"""

    def __init__(self, cache_dir: Path, max_patterns: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_patterns = max_patterns

        # Data files
        self.patterns_file = self.cache_dir / "query_patterns.json"
        self.history_file = self.cache_dir / "query_history.jsonl"
        self.suggestions_file = self.cache_dir / "query_suggestions.json"

        # Pattern storage
        self.patterns: dict[str, QueryPattern] = {}
        self.query_history: list[dict] = []
        self.session_queries: defaultdict = defaultdict(list)

        # Configuration
        self.min_pattern_frequency = 3
        self.similarity_threshold = 0.8
        self.suggestion_confidence_threshold = 0.6

        self.logger = logging.getLogger(__name__)
        self._load_patterns()
        self._load_history()

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching"""
        # Convert to lowercase and strip
        normalized = query.lower().strip()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Remove common filler words
        filler_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'between', 'among',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'must', 'shall', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'its', 'our', 'their'
        }

        words = [word for word in normalized.split() if word not in filler_words]
        normalized = ' '.join(words)

        return normalized

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries using Jaccard similarity"""
        set1 = set(query1.split())
        set2 = set(query2.split())

        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union)

    def _extract_intent(self, query: str) -> str:
        """Extract the primary intent from a query"""
        # Common intent patterns
        intent_patterns = {
            'search': r'\b(search|find|look for|get)\b',
            'help': r'\b(help|how to|tutorial|guide)\b',
            'fix': r'\b(fix|repair|solve|resolve|debug)\b',
            'implement': r'\b(implement|add|create|build|develop)\b',
            'explain': r'\b(explain|what is|describe|tell me about)\b',
            'error': r'\b(error|issue|problem|bug|exception)\b',
            'optimize': r'\b(optimize|improve|enhance|performance|speed)\b'
        }

        for intent, pattern in intent_patterns.items():
            if re.search(pattern, query.lower()):
                return intent

        return 'general'

    def record_query(self, query: str, session_id: str, results_count: int,
                    execution_time: float, success: bool = True):
        """Record a query for pattern analysis"""
        timestamp = time.time()
        normalized_query = self._normalize_query(query)
        intent = self._extract_intent(query)

        # Create query record
        query_record = {
            'timestamp': timestamp,
            'session_id': session_id,
            'original_query': query,
            'normalized_query': normalized_query,
            'intent': intent,
            'results_count': results_count,
            'execution_time': execution_time,
            'success': success
        }

        # Add to history
        self.query_history.append(query_record)
        self.session_queries[session_id].append(query_record)

        # Update patterns
        self._update_patterns(normalized_query, query, timestamp, results_count, execution_time, success)

        # Save to file
        self._save_query_history(query_record)

        # Cleanup old data periodically
        if len(self.query_history) % 100 == 0:
            self._cleanup_old_data()

    def _update_patterns(self, normalized_query: str, original_query: str,
                        timestamp: float, results_count: int,
                        execution_time: float, success: bool):
        """Update query patterns based on new query"""
        # Find existing similar patterns
        matching_pattern_id = None
        best_similarity = 0.0

        for pattern_id, pattern in self.patterns.items():
            similarity = self._calculate_similarity(
                normalized_query, pattern.normalized_query
            )
            if similarity > self.similarity_threshold and similarity > best_similarity:
                matching_pattern_id = pattern_id
                best_similarity = similarity

        if matching_pattern_id:
            # Update existing pattern
            pattern = self.patterns[matching_pattern_id]
            pattern.frequency += 1
            pattern.last_seen = timestamp

            # Add variant if different enough
            if original_query not in pattern.variants:
                pattern.variants.append(original_query)

            # Update success metrics
            pattern.success_metrics['total_queries'] += 1
            if success:
                pattern.success_metrics['successful_queries'] += 1
            pattern.success_metrics['avg_results'] = (
                (pattern.success_metrics['avg_results'] * (pattern.frequency - 1) + results_count)
                / pattern.frequency
            )
            pattern.success_metrics['avg_execution_time'] = (
                (pattern.success_metrics['avg_execution_time'] * (pattern.frequency - 1) + execution_time)
                / pattern.frequency
            )
        else:
            # Create new pattern
            pattern_id = hashlib.md5(f"{normalized_query}{timestamp}".encode()).hexdigest()[:12]

            pattern = QueryPattern(
                pattern_id=pattern_id,
                normalized_query=normalized_query,
                frequency=1,
                last_seen=timestamp,
                variants=[original_query],
                success_metrics={
                    'total_queries': 1,
                    'successful_queries': 1 if success else 0,
                    'avg_results': results_count,
                    'avg_execution_time': execution_time
                },
                related_queries=[],
                suggestion_score=0.0
            )

            self.patterns[pattern_id] = pattern

        # Limit pattern count
        if len(self.patterns) > self.max_patterns:
            self._prune_patterns()

    def get_intelligent_suggestions(self, current_query: str, session_id: str,
                                  limit: int = 5) -> list[QuerySuggestion]:
        """Get intelligent query suggestions based on patterns and session context"""
        normalized_query = self._normalize_query(current_query)
        suggestions = []

        # Get session context
        session_context = self.session_queries.get(session_id, [])
        recent_queries = [q['normalized_query'] for q in session_context[-10:]]

        # Pattern-based suggestions
        for pattern_id, pattern in self.patterns.items():
            if pattern.frequency >= self.min_pattern_frequency:
                similarity = self._calculate_similarity(
                    normalized_query, pattern.normalized_query
                )

                if similarity > 0.3:  # Some similarity threshold
                    # Calculate confidence
                    confidence = (
                        similarity * 0.4 +
                        (pattern.frequency / 50) * 0.3 +  # Frequency factor
                        (pattern.success_metrics['successful_queries'] /
                         max(pattern.success_metrics['total_queries'], 1)) * 0.3  # Success factor
                    )

                    if confidence > self.suggestion_confidence_threshold:
                        # Estimate time savings
                        avg_time = pattern.success_metrics['avg_execution_time']
                        estimated_savings = max(0, avg_time * 0.3)  # 30% time savings estimate

                        reasoning = self._generate_reasoning(pattern, similarity, session_context)

                        suggestion = QuerySuggestion(
                            suggestion_id=hashlib.md5(f"{pattern_id}{current_query}{time.time()}".encode()).hexdigest()[:12],
                            suggested_query=pattern.variants[0],  # Use most common variant
                            original_query=current_query,
                            confidence=confidence,
                            reasoning=reasoning,
                            estimated_time_savings=estimated_savings,
                            pattern_id=pattern_id
                        )
                        suggestions.append(suggestion)

        # Context-aware suggestions based on session
        context_suggestions = self._get_context_suggestions(
            current_query, session_context, recent_queries
        )
        suggestions.extend(context_suggestions)

        # Sort by confidence and limit
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:limit]

    def _generate_reasoning(self, pattern: QueryPattern, similarity: float,
                          session_context: list[dict]) -> str:
        """Generate reasoning for a suggestion"""
        reasons = []

        if similarity > 0.8:
            reasons.append("Very similar to previous successful queries")
        elif similarity > 0.6:
            reasons.append("Similar to common query patterns")

        if pattern.frequency > 10:
            reasons.append(f"Used {pattern.frequency} times successfully")

        success_rate = (pattern.success_metrics['successful_queries'] /
                       max(pattern.success_metrics['total_queries'], 1))
        if success_rate > 0.9:
            reasons.append("High success rate (90%+)")
        elif success_rate > 0.7:
            reasons.append("Good success rate (70%+)")

        # Check if pattern appears in current session
        session_pattern_queries = [
            q for q in session_context
            if self._calculate_similarity(
                q['normalized_query'], pattern.normalized_query
            ) > 0.8
        ]

        if session_pattern_queries:
            reasons.append("Used successfully in current session")

        return "; ".join(reasons) if reasons else "Based on usage patterns"

    def _get_context_suggestions(self, current_query: str, session_context: list[dict],
                               recent_queries: list[str]) -> list[QuerySuggestion]:
        """Get context-aware suggestions based on session history"""
        suggestions = []

        # Find related queries in session
        for query_record in session_context[-20:]:  # Last 20 queries
            similarity = self._calculate_similarity(
                current_query.lower(), query_record['normalized_query']
            )

            if similarity > 0.5 and query_record['success']:
                confidence = similarity * 0.7  # Lower confidence for context suggestions

                if confidence > self.suggestion_confidence_threshold:
                    suggestion = QuerySuggestion(
                        suggestion_id=hashlib.md5(f"context{query_record['timestamp']}{time.time()}".encode()).hexdigest()[:12],
                        suggested_query=query_record['original_query'],
                        original_query=current_query,
                        confidence=confidence,
                        reasoning=f"Successfully used in current session ({query_record['results_count']} results)",
                        estimated_time_savings=0.1  # Small time savings for context suggestions
                    )
                    suggestions.append(suggestion)

        return suggestions

    def get_repetitive_patterns(self, min_frequency: int = 5,
                              days_back: int = 7) -> list[QueryPattern]:
        """Get patterns that appear frequently and might benefit from optimization"""
        cutoff_time = time.time() - (days_back * 24 * 3600)

        repetitive_patterns = []
        for pattern in self.patterns.values():
            if (pattern.frequency >= min_frequency and
                pattern.last_seen >= cutoff_time):

                # Calculate optimization potential
                total_time = (pattern.success_metrics['avg_execution_time'] *
                             pattern.success_metrics['total_queries'])
                potential_savings = total_time * 0.3  # 30% potential savings

                pattern.suggestion_score = potential_savings
                repetitive_patterns.append(pattern)

        # Sort by potential impact
        repetitive_patterns.sort(key=lambda x: x.suggestion_score, reverse=True)
        return repetitive_patterns

    def get_optimization_recommendations(self) -> dict[str, Any]:
        """Get optimization recommendations based on pattern analysis"""
        repetitive_patterns = self.get_repetitive_patterns()

        recommendations = {
            "high_impact_patterns": [],
            "cache_optimization": [],
            "query_improvements": [],
            "estimated_time_savings": 0.0
        }

        total_savings = 0.0

        for pattern in repetitive_patterns[:10]:  # Top 10 patterns
            # High impact patterns
            recommendations["high_impact_patterns"].append({
                "pattern": pattern.normalized_query,
                "frequency": pattern.frequency,
                "avg_execution_time": pattern.success_metrics['avg_execution_time'],
                "potential_savings": pattern.suggestion_score,
                "variants": pattern.variants[:3]  # Top 3 variants
            })

            # Cache optimization suggestions
            if pattern.frequency > 10:
                recommendations["cache_optimization"].append({
                    "query_pattern": pattern.normalized_query,
                    "reason": "High frequency query pattern",
                    "recommended_ttl": "1 hour",
                    "estimated_savings": pattern.suggestion_score * 0.5
                })

            # Query improvement suggestions
            if pattern.success_metrics['avg_execution_time'] > 2.0:
                recommendations["query_improvements"].append({
                    "query_pattern": pattern.normalized_query,
                    "issue": "Slow average execution time",
                    "suggestion": "Consider adding to persistent cache or optimizing search filters",
                    "current_avg_time": pattern.success_metrics['avg_execution_time']
                })

            total_savings += pattern.suggestion_score

        recommendations["estimated_time_savings"] = total_savings

        return recommendations

    def _prune_patterns(self):
        """Remove old or low-value patterns to stay within limits"""
        if len(self.patterns) <= self.max_patterns:
            return

        # Calculate pattern value scores
        pattern_scores = []
        cutoff_time = time.time() - (30 * 24 * 3600)  # 30 days ago

        for pattern_id, pattern in self.patterns.items():
            # Score based on frequency, recency, and success rate
            age_penalty = 0.5 if pattern.last_seen < cutoff_time else 1.0
            success_rate = (pattern.success_metrics['successful_queries'] /
                           max(pattern.success_metrics['total_queries'], 1))

            score = (pattern.frequency * 0.4 +
                    success_rate * 0.3 +
                    age_penalty * 0.3)

            pattern_scores.append((pattern_id, score))

        # Sort by score and remove lowest
        pattern_scores.sort(key=lambda x: x[1])
        to_remove = len(pattern_scores) - self.max_patterns

        for pattern_id, _ in pattern_scores[:to_remove]:
            del self.patterns[pattern_id]

    def _cleanup_old_data(self):
        """Clean up old query history data"""
        cutoff_time = time.time() - (90 * 24 * 3600)  # 90 days ago

        # Remove old query records
        self.query_history = [
            record for record in self.query_history
            if record['timestamp'] > cutoff_time
        ]

        # Clean up old session data
        for session_id in list(self.session_queries.keys()):
            self.session_queries[session_id] = [
                record for record in self.session_queries[session_id]
                if record['timestamp'] > cutoff_time
            ]

            if not self.session_queries[session_id]:
                del self.session_queries[session_id]

    def _load_patterns(self):
        """Load existing patterns from file"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file) as f:
                    data = json.load(f)
                    for pattern_data in data.get('patterns', []):
                        pattern = QueryPattern(**pattern_data)
                        self.patterns[pattern.pattern_id] = pattern
                self.logger.debug(f"Loaded {len(self.patterns)} query patterns")
            except Exception as e:
                self.logger.error(f"Failed to load patterns: {e}")

    def _save_patterns(self):
        """Save patterns to file"""
        try:
            data = {
                'last_updated': time.time(),
                'patterns': [asdict(pattern) for pattern in self.patterns.values()]
            }
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save patterns: {e}")

    def _load_history(self):
        """Load query history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line.strip())
                            self.query_history.append(record)

                            # Build session index
                            session_id = record['session_id']
                            self.session_queries[session_id].append(record)

                self.logger.debug(f"Loaded {len(self.query_history)} query records")
            except Exception as e:
                self.logger.error(f"Failed to load query history: {e}")

    def _save_query_history(self, query_record: dict):
        """Append query record to history file"""
        try:
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(query_record) + '\n')

            # Save patterns periodically
            if len(self.query_history) % 10 == 0:
                self._save_patterns()

        except Exception as e:
            self.logger.error(f"Failed to save query history: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """Get pattern recognition statistics"""
        if not self.query_history:
            return {"message": "No query history available"}

        # Calculate statistics
        total_queries = len(self.query_history)
        unique_patterns = len(self.patterns)

        # Time range
        timestamps = [q['timestamp'] for q in self.query_history]
        time_range = {
            "start": min(timestamps),
            "end": max(timestamps),
            "duration_days": (max(timestamps) - min(timestamps)) / (24 * 3600)
        }

        # Top patterns
        top_patterns = sorted(
            self.patterns.values(),
            key=lambda x: x.frequency,
            reverse=True
        )[:10]

        # Success rates
        successful_queries = sum(1 for q in self.query_history if q['success'])
        success_rate = successful_queries / total_queries if total_queries > 0 else 0

        # Average execution time
        avg_execution_time = sum(q['execution_time'] for q in self.query_history) / total_queries

        return {
            "total_queries": total_queries,
            "unique_patterns": unique_patterns,
            "pattern_hit_rate": unique_patterns / total_queries if total_queries > 0 else 0,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "time_range": time_range,
            "top_patterns": [
                {
                    "query": pattern.normalized_query,
                    "frequency": pattern.frequency,
                    "avg_execution_time": pattern.success_metrics['avg_execution_time']
                }
                for pattern in top_patterns
            ],
            "sessions_analyzed": len(self.session_queries)
        }
