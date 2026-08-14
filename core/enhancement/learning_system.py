"""
Learning System for Research Methodology Selection
Simple feedback collection and pattern recognition using JSON storage
"""

import json
import os
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, cast


@dataclass
class ResearchFeedback:
    """Feedback from a research session"""
    research_id: str
    query: str
    modes_used: list[str]
    predicted_quality: float
    actual_quality_rating: float  # 1-5 scale from user
    helpful_aspects: list[str]
    improvement_suggestions: list[str]
    sources_helpful: list[str]
    sources_missing: list[str]
    timestamp: datetime
    session_duration: float  # seconds
    user_expertise_level: str  # beginner, intermediate, expert
    research_domain: str

@dataclass
class PatternInsight:
    """Insight derived from pattern analysis"""
    pattern_type: str
    confidence: float
    recommendation: str
    supporting_evidence: list[str]
    last_updated: datetime

class LearningSystem:
    """Simple learning system with feedback collection and pattern recognition"""

    def __init__(self, feedback_file: str = "research_feedback.json"):
        self.feedback_file = feedback_file
        self.feedback_history: list[ResearchFeedback] = []
        self.patterns: dict[str, PatternInsight] = {}
        self.query_patterns: dict[str, dict] = {}
        self.mode_performance: dict[str, dict] = {}

        self._load_feedback()
        self._analyze_patterns()

    def _load_feedback(self) -> None:
        """Load feedback history from JSON file"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, encoding='utf-8') as f:
                    data = json.load(f)

                self.feedback_history = [
                    ResearchFeedback(
                        research_id=item['research_id'],
                        query=item['query'],
                        modes_used=item['modes_used'],
                        predicted_quality=item['predicted_quality'],
                        actual_quality_rating=item['actual_quality_rating'],
                        helpful_aspects=item['helpful_aspects'],
                        improvement_suggestions=item['improvement_suggestions'],
                        sources_helpful=item['sources_helpful'],
                        sources_missing=item['sources_missing'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        session_duration=item['session_duration'],
                        user_expertise_level=item['user_expertise_level'],
                        research_domain=item['research_domain']
                    )
                    for item in data
                ]
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Warning: Could not load feedback file: {e}")
                self.feedback_history = []

    def _save_feedback(self) -> None:
        """Save feedback history to JSON file"""
        try:
            # Create directory if it doesn't exist
            feedback_dir = os.path.dirname(self.feedback_file)
            if feedback_dir:
                os.makedirs(feedback_dir, exist_ok=True)

            data = []
            for feedback in self.feedback_history:
                feedback_dict = asdict(feedback)
                feedback_dict['timestamp'] = feedback.timestamp.isoformat()
                data.append(feedback_dict)

            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save feedback file: {e}")

    def collect_feedback(self, research_id: str, query: str, modes_used: list[str],
                        predicted_quality: float, actual_quality_rating: float,
                        helpful_aspects: list[str] | None = None,
                        improvement_suggestions: list[str] | None = None,
                        sources_helpful: list[str] | None = None,
                        sources_missing: list[str] | None = None,
                        session_duration: float = 0.0,
                        user_expertise_level: str = "intermediate",
                        research_domain: str = "general") -> None:
        """Collect user feedback for learning"""

        feedback = ResearchFeedback(
            research_id=research_id,
            query=query,
            modes_used=modes_used,
            predicted_quality=predicted_quality,
            actual_quality_rating=actual_quality_rating,
            helpful_aspects=helpful_aspects or [],
            improvement_suggestions=improvement_suggestions or [],
            sources_helpful=sources_helpful or [],
            sources_missing=sources_missing or [],
            timestamp=datetime.now(),
            session_duration=session_duration,
            user_expertise_level=user_expertise_level,
            research_domain=research_domain
        )

        self.feedback_history.append(feedback)
        self._save_feedback()
        self._analyze_patterns()

    def _analyze_patterns(self) -> None:
        """Analyze feedback patterns for learning insights"""
        if len(self.feedback_history) < 5:  # Need minimum data for meaningful patterns
            return

        # Analyze mode combination success patterns
        self._analyze_mode_combinations()

        # Analyze query patterns
        self._analyze_query_patterns()

        # Analyze domain-specific patterns
        self._analyze_domain_patterns()

        # Analyze expertise-specific patterns
        self._analyze_expertise_patterns()

    def _analyze_mode_combinations(self) -> None:
        """Analyze which mode combinations work best"""
        mode_combo_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "ratings": [], "quality_errors": []})  # type: ignore[assignment]

        for feedback in self.feedback_history:
            combo_key = '+'.join(sorted(feedback.modes_used))
            stats = mode_combo_stats[combo_key]

            stats["count"] += 1  # type: ignore[operator]
            stats["ratings"].append(feedback.actual_quality_rating)  # type: ignore[arg-type]

            # Track prediction accuracy
            quality_error = abs(feedback.predicted_quality - (feedback.actual_quality_rating / 5.0))
            stats["quality_errors"].append(quality_error)  # type: ignore[arg-type]

        # Calculate performance metrics for each combination
        self.mode_performance = {}
        for combo_key, stats in mode_combo_stats.items():
            if stats["count"] >= 3:  # Minimum samples for reliability
                avg_rating = statistics.mean(stats["ratings"])  # type: ignore[arg-type]
                avg_error = statistics.mean(stats["quality_errors"])  # type: ignore[arg-type]

                self.mode_performance[combo_key] = {
                    "avg_rating": avg_rating,
                    "avg_error": avg_error,
                    "sample_size": stats["count"],
                    "reliability": min(stats["count"] / 10.0, 1.0),  # More samples = more reliable
                    "recommendation_score": avg_rating * (1.0 - avg_error)  # Higher rating + lower accuracy error
                }

    def _analyze_query_patterns(self) -> None:
        """Analyze patterns in query types and successful methodologies"""
        query_patterns: dict[str, dict[str, dict[str, Any]]] = defaultdict(lambda: defaultdict(lambda: {"count": 0, "ratings": []}))  # type: ignore[assignment]

        for feedback in self.feedback_history:
            # Extract keywords from query
            query_words = self._extract_keywords(feedback.query)

            for word in query_words:
                if len(word) > 3:  # Only consider meaningful words
                    combo_key = '+'.join(sorted(feedback.modes_used))

                    query_patterns[word][combo_key]["count"] += 1  # type: ignore[operator]
                    query_patterns[word][combo_key]["ratings"].append(feedback.actual_quality_rating)  # type: ignore[arg-type]

        # Calculate best mode combinations for each keyword
        self.query_patterns = {}
        for keyword, combos in query_patterns.items():
            best_combos = []

            for combo_key, stats in combos.items():
                if stats["count"] >= 2:  # Minimum samples
                    avg_rating = statistics.mean(stats["ratings"])  # type: ignore[arg-type]
                    best_combos.append((combo_key, avg_rating, stats["count"]))

            # Sort by rating, then by sample size
            best_combos.sort(key=lambda x: (x[1], x[2]), reverse=True)

            if best_combos:
                self.query_patterns[keyword] = {
                    "best_combination": best_combos[0][0],
                    "avg_rating": best_combos[0][1],
                    "sample_size": best_combos[0][2],
                    "alternatives": best_combos[1:3],  # Top 2 alternatives
                    "confidence": min(best_combos[0][2] / 5.0, 1.0)  # Confidence based on sample size
                }

    def _analyze_domain_patterns(self) -> None:
        """Analyze domain-specific patterns"""
        domain_patterns: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))  # type: ignore[assignment]

        for feedback in self.feedback_history:
            domain = feedback.research_domain
            combo_key = '+'.join(sorted(feedback.modes_used))
            domain_patterns[domain][combo_key].append(feedback.actual_quality_rating)

        # Store domain insights
        for domain, combos in domain_patterns.items():
            domain_insights: list[dict[str, Any]] = []
            for combo_key, ratings in combos.items():
                if len(ratings) >= 2:
                    avg_rating = statistics.mean(ratings)
                    domain_insights.append({
                        "combination": combo_key,
                        "avg_rating": avg_rating,
                        "sample_size": len(ratings)
                    })

            domain_insights.sort(key=lambda x: x["avg_rating"], reverse=True)  # type: ignore[arg-type]

            if domain_insights:
                pattern_key = f"domain_{domain}"
                self.patterns[pattern_key] = PatternInsight(  # type: ignore[assignment]
                    pattern_type="domain_specific",
                    confidence=min(domain_insights[0]["sample_size"] / 5.0, 1.0),
                    recommendation=f"For {domain} queries, use {domain_insights[0]['combination']}",
                    supporting_evidence=[
                        f"Average rating: {domain_insights[0]['avg_rating']:.1f}/5.0 "
                        f"based on {domain_insights[0]['sample_size']} samples"
                    ],
                    last_updated=datetime.now()
                )

    def _analyze_expertise_patterns(self) -> None:
        """Analyze patterns based on user expertise level"""
        expertise_patterns: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))  # type: ignore[assignment]

        for feedback in self.feedback_history:
            expertise = feedback.user_expertise_level
            combo_key = '+'.join(sorted(feedback.modes_used))
            expertise_patterns[expertise][combo_key].append(feedback.actual_quality_rating)

        # Store expertise insights
        for expertise, combos in expertise_patterns.items():
            expertise_insights: list[dict[str, Any]] = []
            for combo_key, ratings in combos.items():
                if len(ratings) >= 2:
                    avg_rating = statistics.mean(ratings)
                    expertise_insights.append({
                        "combination": combo_key,
                        "avg_rating": avg_rating,
                        "sample_size": len(ratings)
                    })

            expertise_insights.sort(key=lambda x: x["avg_rating"], reverse=True)  # type: ignore[arg-type]

            if expertise_insights:
                pattern_key = f"expertise_{expertise}"
                self.patterns[pattern_key] = PatternInsight(  # type: ignore[assignment]
                    pattern_type="expertise_specific",
                    confidence=min(expertise_insights[0]["sample_size"] / 5.0, 1.0),
                    recommendation=f"For {expertise} users, use {expertise_insights[0]['combination']}",
                    supporting_evidence=[
                        f"Average rating: {expertise_insights[0]['avg_rating']:.1f}/5.0 "
                        f"based on {expertise_insights[0]['sample_size']} samples"
                    ],
                    last_updated=datetime.now()
                )

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract meaningful keywords from query"""
        import re
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b\w+\b', query.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'how', 'what', 'when', 'where', 'why', 'can', 'could', 'would', 'should'}
        return [word for word in words if word not in stop_words and len(word) > 2]

    def get_pattern_based_recommendation(self, query: str, candidate_modes: list[str],
                                       domain: str | None = None, expertise: str | None = None) -> dict | None:
        """Get recommendation based on learned patterns"""
        if not self.patterns and not self.query_patterns:
            return None

        # Check for keyword-based recommendations
        query_words = self._extract_keywords(query)
        keyword_matches = []

        for word in query_words:
            if word in self.query_patterns:
                pattern = self.query_patterns[word]
                # Check if the recommended combination uses available modes
                rec_modes = pattern["best_combination"].split('+')
                if any(mode in candidate_modes for mode in rec_modes):
                    keyword_matches.append({
                        "type": "keyword",
                        "keyword": word,
                        "recommendation": pattern["best_combination"],
                        "confidence": pattern["confidence"],
                        "avg_rating": pattern["avg_rating"],
                        "sample_size": pattern["sample_size"]
                    })

        # Check for domain-based recommendations
        domain_match: dict[str, Any] | None = None
        if domain and f"domain_{domain}" in self.patterns:
            domain_pattern: PatternInsight = self.patterns[f"domain_{domain}"]  # type: ignore[assignment]
            # Extract combination from recommendation text
            rec_text = domain_pattern.recommendation
            if "use " in rec_text:
                rec_combo = rec_text.split("use ")[1].strip()
                domain_match = {
                    "type": "domain",
                    "domain": domain,
                    "recommendation": rec_combo,
                    "confidence": domain_pattern.confidence,
                    "evidence": domain_pattern.supporting_evidence
                }

        # Check for expertise-based recommendations
        expertise_match: dict[str, Any] | None = None
        if expertise and f"expertise_{expertise}" in self.patterns:
            expertise_pattern: PatternInsight = self.patterns[f"expertise_{expertise}"]  # type: ignore[assignment]
            rec_text = expertise_pattern.recommendation
            if "use " in rec_text:
                rec_combo = rec_text.split("use ")[1].strip()
                expertise_match = {
                    "type": "expertise",
                    "expertise": expertise,
                    "recommendation": rec_combo,
                    "confidence": expertise_pattern.confidence,
                    "evidence": expertise_pattern.supporting_evidence
                }

        # Combine recommendations with confidence weighting
        all_recommendations = keyword_matches
        if domain_match:
            all_recommendations.append(domain_match)
        if expertise_match:
            all_recommendations.append(expertise_match)

        if not all_recommendations:
            return None

        # Select best recommendation based on confidence and evidence
        best_rec = max(all_recommendations, key=lambda x: x["confidence"])

        return {
            "recommended_combination": best_rec["recommendation"],
            "confidence": best_rec["confidence"],
            "reasoning": f"Based on {best_rec['type']} pattern analysis",
            "evidence": best_rec.get("evidence", []),
            "sample_size": best_rec.get("sample_size", 0),
            "pattern_type": best_rec["type"]
        }

    def get_mode_performance_stats(self) -> dict[str, dict]:
        """Get performance statistics for different mode combinations"""
        return self.mode_performance.copy()

    def get_recent_feedback(self, days: int = 30) -> list[ResearchFeedback]:
        """Get feedback from recent days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            feedback for feedback in self.feedback_history
            if feedback.timestamp >= cutoff_date
        ]

    def get_learning_summary(self) -> dict[str, Any]:
        """Get summary of learning system insights"""
        if not self.feedback_history:
            return {"status": "No feedback data available"}

        total_feedback = len(self.feedback_history)
        recent_feedback = len(self.get_recent_feedback(30))
        avg_rating = statistics.mean(f.actual_quality_rating for f in self.feedback_history)

        return {
            "total_feedback_sessions": total_feedback,
            "recent_feedback_sessions": recent_feedback,
            "average_user_rating": avg_rating,
            "patterns_identified": len(self.patterns),
            "query_patterns_learned": len(self.query_patterns),
            "mode_combinations_analyzed": len(self.mode_performance),
            "learning_active": recent_feedback > 0,
            "last_pattern_update": max(
                (p.last_updated for p in self.patterns.values()),
                default=datetime.now()
            ).isoformat()
        }

    def export_patterns(self, filename: str | None = None) -> str:
        """Export learned patterns for analysis or backup"""
        if filename is None:
            filename = f"research_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_feedback_samples": len(self.feedback_history),
            "mode_performance": self.mode_performance,
            "query_patterns": self.query_patterns,
            "patterns": {
                key: asdict(pattern) for key, pattern in self.patterns.items()
            },
            "learning_summary": self.get_learning_summary()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filename

# Test cases
if __name__ == "__main__":
    # Create test learning system
    learning_system = LearningSystem("test_feedback.json")

    # Simulate some feedback data
    test_feedback = [
        {
            "query": "react hooks implementation example",
            "modes": ["octocode"],
            "predicted_quality": 0.85,
            "actual_rating": 4.2,
            "helpful": ["code examples", "github repos"],
            "domain": "technical",
            "expertise": "intermediate"
        },
        {
            "query": "microservices security best practices",
            "modes": ["octocode", "web", "multi-model"],
            "predicted_quality": 0.92,
            "actual_rating": 4.7,
            "helpful": ["diverse perspectives", "comprehensive coverage"],
            "domain": "technical",
            "expertise": "expert"
        },
        {
            "query": "machine learning academic papers",
            "modes": ["web"],
            "predicted_quality": 0.78,
            "actual_rating": 3.8,
            "missing": ["more recent papers", "comprehensive analysis"],
            "domain": "academic",
            "expertise": "expert"
        },
        {
            "query": "docker tutorial beginner",
            "modes": ["web", "octocode"],
            "predicted_quality": 0.88,
            "actual_rating": 4.5,
            "helpful": ["step by step guide", "practical examples"],
            "domain": "technical",
            "expertise": "beginner"
        },
        {
            "query": "react hooks implementation example",
            "modes": ["octocode", "web"],
            "predicted_quality": 0.90,
            "actual_rating": 4.6,
            "helpful": ["comprehensive coverage", "multiple examples"],
            "domain": "technical",
            "expertise": "intermediate"
        }
    ]

    # Add test feedback
    for i, feedback_data in enumerate(test_feedback):
        learning_system.collect_feedback(
            research_id=f"test_{i}",
            query=cast(str, feedback_data["query"]),
            modes_used=cast(list[str], feedback_data["modes"]),
            predicted_quality=cast(float, feedback_data["predicted_quality"]),
            actual_quality_rating=cast(float, feedback_data["actual_rating"]),
            helpful_aspects=cast(list[str] | None, feedback_data.get("helpful")),
            improvement_suggestions=cast(list[str] | None, feedback_data.get("missing")),
            user_expertise_level=cast(str, feedback_data["expertise"]),
            research_domain=cast(str, feedback_data["domain"])
        )

    print("=== Learning System Test ===")

    # Test pattern-based recommendations
    test_queries = [
        ("react hooks example", ["octocode", "web"], "technical", "intermediate"),
        ("microservices security patterns", ["octocode", "web", "multi-model"], "technical", "expert"),
        ("docker tutorial", ["web", "octocode"], "technical", "beginner")
    ]

    for query, candidate_modes, domain, expertise in test_queries:
        recommendation = learning_system.get_pattern_based_recommendation(
            query, candidate_modes, domain, expertise
        )

        print(f"\nQuery: {query}")
        if recommendation:
            print(f"Recommended: {recommendation['recommended_combination']}")
            print(f"Confidence: {recommendation['confidence']:.2f}")
            print(f"Reasoning: {recommendation['reasoning']}")
        else:
            print("No pattern-based recommendation available")

    # Show learning summary
    summary = learning_system.get_learning_summary()
    print("\n=== Learning Summary ===")
    print(f"Total feedback sessions: {summary['total_feedback_sessions']}")
    print(f"Average user rating: {summary['average_user_rating']:.2f}/5.0")
    print(f"Patterns identified: {summary['patterns_identified']}")
    print(f"Query patterns learned: {summary['query_patterns_learned']}")
    print(f"Mode combinations analyzed: {summary['mode_combinations_analyzed']}")

    # Show mode performance
    print("\n=== Mode Performance ===")
    mode_stats = learning_system.get_mode_performance_stats()
    for combo, stats in mode_stats.items():
        print(f"{combo}: {stats['avg_rating']:.1f}/5.0 "
              f"(error: {stats['avg_error']:.2f}, samples: {stats['sample_size']})")

    # Export patterns
    export_file = learning_system.export_patterns("test_patterns.json")
    print(f"\nPatterns exported to: {export_file}")

    # Cleanup test file
    try:
        os.remove("test_feedback.json")
        os.remove("test_patterns.json")
    except FileNotFoundError:
        pass
