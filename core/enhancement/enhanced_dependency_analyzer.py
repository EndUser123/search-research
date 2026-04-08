"""
Enhanced Dependency Analyzer for Research Methodology Selection
Simplified, practical approach using keyword analysis and heuristics
"""

import re
from dataclasses import dataclass
from enum import Enum


class ResearchDepth(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class QueryDependencies:
    """Simple dependency classification without complex ML"""
    requires_code: bool = False
    requires_documentation: bool = False
    requires_academic: bool = False
    requires_ai_perspectives: bool = False
    requires_github: bool = False
    requires_tutorials: bool = False
    requires_examples: bool = False
    complexity_score: float = 0.0
    research_depth: ResearchDepth = ResearchDepth.BASIC
    confidence: float = 0.0
    primary_indicators: list[str] | None = None

    def __post_init__(self) -> None:
        if self.primary_indicators is None:
            self.primary_indicators = []

class SimplifiedDependencyAnalyzer:
    """Analyze research queries to determine optimal methodology requirements"""

    def __init__(self) -> None:
        # Keyword sets for different dependency types
        self.code_keywords = {
            'github', 'repository', 'repo', 'code', 'implementation', 'example',
            'function', 'class', 'library', 'api', 'framework', 'sdk', 'package',
            'module', 'script', 'programming', 'development', 'debug'
        }

        self.documentation_keywords = {
            'docs', 'documentation', 'guide', 'tutorial', 'howto', 'manual',
            'readme', 'getting started', 'setup', 'installation', 'configuration'
        }

        self.academic_keywords = {
            'paper', 'research', 'study', 'academic', 'journal', 'conference',
            'thesis', 'dissertation', 'methodology', 'analysis', 'survey',
            'literature review', 'peer reviewed', 'citation'
        }

        self.ai_perspective_keywords = {
            'opinion', 'perspective', 'viewpoint', 'approach', 'strategy',
            'best practice', 'comparison', 'evaluation', 'analysis', 'recommendation',
            'pros and cons', 'advantages', 'disadvantages', 'alternatives'
        }

        self.complexity_indicators = {
            'architecture', 'scalability', 'optimization', 'performance',
            'security', 'compliance', 'enterprise', 'production', 'distributed',
            'microservices', 'design patterns', 'best practices', 'complex'
        }

        self.github_specific = {
            'github', 'repo', 'repository', 'pull request', 'pr', 'issue',
            'commit', 'branch', 'fork', 'clone', 'open source'
        }

        self.example_indicators = {
            'example', 'demo', 'sample', 'illustration', 'case study',
            'walkthrough', 'tutorial', 'how to', 'step by step'
        }

    def analyze_dependencies(self, query: str, tsk_context: dict | None = None) -> QueryDependencies:
        """Extract dependencies using keyword analysis and heuristics"""
        query_lower = query.lower()
        words = re.findall(r'\b\w+\b', query_lower)

        dependencies = QueryDependencies()
        dependency_scores = {}

        # Basic dependency detection with scoring
        dependencies.requires_code, code_score = self._check_keyword_match(query_lower, self.code_keywords)
        dependency_scores['code'] = code_score

        dependencies.requires_github, github_score = self._check_keyword_match(query_lower, self.github_specific)
        dependency_scores['github'] = github_score

        dependencies.requires_documentation, doc_score = self._check_keyword_match(query_lower, self.documentation_keywords)
        dependency_scores['documentation'] = doc_score

        dependencies.requires_academic, academic_score = self._check_keyword_match(query_lower, self.academic_keywords)
        dependency_scores['academic'] = academic_score

        dependencies.requires_ai_perspectives, ai_score = self._check_keyword_match(query_lower, self.ai_perspective_keywords)
        dependency_scores['ai_perspectives'] = ai_score

        dependencies.requires_tutorials, tutorial_score = self._check_keyword_match(query_lower, self.example_indicators)
        dependency_scores['tutorials'] = tutorial_score

        dependencies.requires_examples = dependencies.requires_code or dependencies.requires_tutorials

        # Calculate complexity score
        complexity_count = sum(1 for word in words if word in self.complexity_indicators)
        dependencies.complexity_score = min(complexity_count / max(len(words), 1), 1.0)

        # Determine research depth
        if dependencies.complexity_score > 0.6:
            dependencies.research_depth = ResearchDepth.ADVANCED
        elif dependencies.complexity_score > 0.3:
            dependencies.research_depth = ResearchDepth.INTERMEDIATE
        else:
            dependencies.research_depth = ResearchDepth.BASIC

        # Calculate confidence based on keyword clarity
        keyword_matches = sum([
            dependencies.requires_code,
            dependencies.requires_github,
            dependencies.requires_academic,
            dependencies.requires_ai_perspectives,
            dependencies.requires_documentation
        ])
        dependencies.confidence = min(keyword_matches / 5.0 + (dependencies.complexity_score * 0.2), 1.0)

        # Track primary indicators for debugging
        for indicator in words:
            if dependencies.primary_indicators is None:
                dependencies.primary_indicators = []
            if indicator in self.code_keywords or indicator in self.github_specific:
                dependencies.primary_indicators.append(f"code:{indicator}")
            elif indicator in self.academic_keywords:
                dependencies.primary_indicators.append(f"academic:{indicator}")
            elif indicator in self.ai_perspective_keywords:
                dependencies.primary_indicators.append(f"ai_perspective:{indicator}")
            elif indicator in self.documentation_keywords or indicator in self.example_indicators:
                dependencies.primary_indicators.append(f"documentation:{indicator}")

        # Consider TSK context if provided
        if tsk_context:
            self._apply_context_analysis(dependencies, tsk_context)

        return dependencies

    def _check_keyword_match(self, query: str, keywords: set[str]) -> tuple[bool, float]:
        """Check if any keywords match and return match status with score"""
        matches = [kw for kw in keywords if kw in query]
        if not matches:
            return False, 0.0

        # Score based on number of matches and query complexity
        score = min(len(matches) / 3.0, 1.0)  # Cap at 1.0
        return True, score

    def _apply_context_analysis(self, dependencies: QueryDependencies, tsk_context: dict) -> None:
        """Apply context-based adjustments to dependencies"""
        # If TSK indicates technical domain, boost code requirements
        if tsk_context.get('domain_type') == 'technical':
            dependencies.requires_code = True
            dependencies.confidence += 0.1

        # If TSK indicates academic/research domain, boost academic requirements
        if tsk_context.get('domain_type') == 'academic':
            dependencies.requires_academic = True
            dependencies.confidence += 0.1

        # If TSK complexity is high, boost research depth
        if tsk_context.get('complexity', 0) > 0.7:
            if dependencies.research_depth == ResearchDepth.BASIC:
                dependencies.research_depth = ResearchDepth.INTERMEDIATE
            elif dependencies.research_depth == ResearchDepth.INTERMEDIATE:
                dependencies.research_depth = ResearchDepth.ADVANCED

    def get_dependency_summary(self, dependencies: QueryDependencies) -> dict:
        """Get a summary of dependencies for debugging and analysis"""
        return {
            "primary_requirements": [
                req for req, val in [
                    ("code", dependencies.requires_code),
                    ("github", dependencies.requires_github),
                    ("academic", dependencies.requires_academic),
                    ("ai_perspectives", dependencies.requires_ai_perspectives),
                    ("documentation", dependencies.requires_documentation),
                    ("tutorials", dependencies.requires_tutorials),
                    ("examples", dependencies.requires_examples)
                ] if val
            ],
            "complexity_score": dependencies.complexity_score,
            "research_depth": dependencies.research_depth.value,
            "confidence": dependencies.confidence,
            "indicators": (dependencies.primary_indicators or [])[:10]  # Limit to first 10 for readability
        }

# Test cases and validation
if __name__ == "__main__":
    analyzer = SimplifiedDependencyAnalyzer()

    test_queries = [
        "react hooks implementation example",
        "github repository microservices architecture",
        "machine learning research papers comparison",
        "best practices for API security",
        "academic study on distributed systems scalability",
        "how to implement oauth2 with jwt tokens",
        "docker production deployment strategies",
        "typescript typescript generic types tutorial"
    ]

    print("=== Dependency Analysis Test Cases ===")
    for query in test_queries:
        deps = analyzer.analyze_dependencies(query)
        summary = analyzer.get_dependency_summary(deps)

        print(f"\nQuery: {query}")
        print(f"Requirements: {', '.join(summary['primary_requirements'])}")
        print(f"Complexity: {summary['complexity_score']:.2f}")
        print(f"Depth: {summary['research_depth']}")
        print(f"Confidence: {summary['confidence']:.2f}")
        if summary['indicators']:
            print(f"Key Indicators: {', '.join(summary['indicators'][:3])}")
