# Enhanced Implementation Plan for Research Methodology Selection
## Practical Algorithms and Concrete Implementation Details

### **🚀 PHASE 1: SIMPLIFIED DEPENDENCY ANALYSIS ENGINE**

#### **1.1 Query Dependency Extraction (Week 1)**
```python
# enhanced_dependency_analyzer.py
import re
from typing import Dict, List, Set
from dataclasses import dataclass
from collections import Counter

@dataclass
class QueryDependencies:
    """Simple dependency classification without complex ML"""
    requires_code: bool = False
    requires_documentation: bool = False
    requires_academic: bool = False
    requires_ai_perspectives: bool = False
    requires_github: bool = False
    complexity_score: float = 0.0
    research_depth: str = "basic"  # basic, intermediate, advanced
    confidence: float = 0.0

class SimplifiedDependencyAnalyzer:
    def __init__(self):
        self.code_keywords = {
            'github', 'repository', 'code', 'implementation', 'example',
            'function', 'class', 'library', 'api', 'framework', 'sdk'
        }
        self.academic_keywords = {
            'paper', 'research', 'study', 'academic', 'journal', 'conference',
            'thesis', 'dissertation', 'methodology', 'analysis'
        }
        self.complexity_indicators = {
            'architecture', 'scalability', 'optimization', 'performance',
            'security', 'compliance', 'enterprise', 'production'
        }

    def analyze_dependencies(self, query: str, tsk_context: Dict = None) -> QueryDependencies:
        """Extract dependencies using keyword analysis and heuristics"""
        query_lower = query.lower()
        words = re.findall(r'\b\w+\b', query_lower)

        dependencies = QueryDependencies()

        # Basic dependency detection
        dependencies.requires_code = any(keyword in query_lower for keyword in self.code_keywords)
        dependencies.requires_github = any(word in query_lower for word in ['github', 'repo', 'repository'])
        dependencies.requires_academic = any(keyword in query_lower for keyword in self.academic_keywords)
        dependencies.requires_ai_perspectives = self._detect_ai_perspective_need(query_lower)
        dependencies.requires_documentation = any(word in query_lower for word in ['docs', 'tutorial', 'guide', 'documentation'])

        # Complexity scoring
        complexity_count = sum(1 for word in words if word in self.complexity_indicators)
        dependencies.complexity_score = min(complexity_count / len(words) if words else 0, 1.0)

        # Research depth based on complexity indicators
        if dependencies.complexity_score > 0.6:
            dependencies.research_depth = "advanced"
        elif dependencies.complexity_score > 0.3:
            dependencies.research_depth = "intermediate"

        # Confidence based on keyword clarity
        keyword_matches = sum([
            dependencies.requires_code,
            dependencies.requires_github,
            dependencies.requires_academic,
            dependencies.requires_ai_perspectives
        ])
        dependencies.confidence = keyword_matches / 4.0

        return dependencies

    def _detect_ai_perspective_need(self, query: str) -> bool:
        """Detect if multiple AI perspectives would be valuable"""
        perspective_indicators = [
            'opinion', 'perspective', 'viewpoint', 'approach', 'strategy',
            'best practice', 'comparison', 'analysis', 'evaluation'
        ]
        return any(indicator in query for indicator in perspective_indicators)
```

#### **1.2 Mode Relationship Mapping (Week 1)**
```python
# mode_relationship_mapper.py
from typing import Dict, List, Tuple
from enum import Enum

class ResearchMode(Enum):
    OCTOCODE = "octocode"
    WEB = "web"
    MULTI_MODEL = "multi-model"
    COGNITIVE = "cognitive-enhanced"

class ModeRelationshipMapper:
    def __init__(self):
        # Define how modes complement each other
        self.mode_strengths = {
            ResearchMode.OCTOCODE: {
                "primary": ["code_examples", "github_repos", "implementation"],
                "secondary": ["tutorials", "discussions"],
                "overlap": ["web"]  # Some overlap with web search
            },
            ResearchMode.WEB: {
                "primary": ["documentation", "tutorials", "news", "articles"],
                "secondary": ["academic_papers", "case_studies"],
                "overlap": ["octocode", "multi-model"]
            },
            ResearchMode.MULTI_MODEL: {
                "primary": ["diverse_perspectives", "opinions", "analysis"],
                "secondary": ["cross_validation", "comparison"],
                "overlap": ["web"]
            },
            ResearchMode.COGNITIVE: {
                "primary": ["deep_analysis", "complex_reasoning", "synthesis"],
                "secondary": ["fact_checking", "verification"],
                "overlap": ["web", "multi-model"]
            }
        }

        # Redundancy matrix (how much overlap between modes)
        self.redundancy_matrix = {
            (ResearchMode.OCTOCODE, ResearchMode.WEB): 0.3,
            (ResearchMode.MULTI_MODEL, ResearchMode.WEB): 0.4,
            (ResearchMode.MULTI_MODEL, ResearchMode.COGNITIVE): 0.2,
            (ResearchMode.COGNITIVE, ResearchMode.WEB): 0.3,
        }

    def find_optimal_combination(self, dependencies: QueryDependencies) -> List[ResearchMode]:
        """Find optimal mode combination using simple heuristics"""
        candidate_modes = []

        # Base mode selection based on dependencies
        if dependencies.requires_github or dependencies.requires_code:
            candidate_modes.append(ResearchMode.OCTOCODE)

        if dependencies.requires_academic or dependencies.requires_documentation:
            candidate_modes.append(ResearchMode.WEB)

        if dependencies.requires_ai_perspectives and dependencies.complexity_score > 0.4:
            candidate_modes.append(ResearchMode.MULTI_MODEL)

        if dependencies.complexity_score > 0.7 and dependencies.research_depth == "advanced":
            candidate_modes.append(ResearchMode.COGNITIVE)

        # Default fallback
        if not candidate_modes:
            candidate_modes.append(ResearchMode.WEB)

        # Remove redundant modes
        return self._eliminate_redundancy(candidate_modes)

    def _eliminate_redundancy(self, modes: List[ResearchMode]) -> List[ResearchMode]:
        """Remove modes with high redundancy"""
        if len(modes) <= 2:
            return modes

        # Sort by value (simplified - assume octocode and cognitive have highest value)
        mode_values = {
            ResearchMode.OCTOCODE: 4,
            ResearchMode.COGNITIVE: 3,
            ResearchMode.MULTI_MODEL: 2,
            ResearchMode.WEB: 1
        }

        # Sort by value
        modes.sort(key=lambda m: mode_values.get(m, 0), reverse=True)

        # Remove low-value modes with high redundancy
        final_modes = [modes[0]]  # Always keep highest value mode

        for mode in modes[1:]:
            redundant = False
            for existing_mode in final_modes:
                redundancy = self.redundancy_matrix.get(
                    (mode, existing_mode),
                    self.redundancy_matrix.get((existing_mode, mode), 0)
                )
                if redundancy > 0.5:  # High redundancy threshold
                    redundant = True
                    break

            if not redundant:
                final_modes.append(mode)

        return final_modes
```

### **🚀 PHASE 2: PRACTICAL OPTIMIZATION ENGINE**

#### **2.1 Quality Prediction Algorithm (Week 3)**
```python
# quality_predictor.py
import math
from typing import Dict, List, Tuple

class QualityPredictor:
    def __init__(self):
        # Weight factors for different aspects
        self.weights = {
            "relevance": 0.4,
            "completeness": 0.3,
            "freshness": 0.2,
            "authority": 0.1
        }

        # Mode quality scores for different dependency types
        self.mode_quality_scores = {
            ("octocode", "code_examples"): 0.9,
            ("octocode", "github_repos"): 0.95,
            ("octocode", "documentation"): 0.6,
            ("web", "documentation"): 0.9,
            ("web", "academic_papers"): 0.8,
            ("web", "tutorials"): 0.85,
            ("multi-model", "diverse_perspectives"): 0.9,
            ("multi_model", "analysis"): 0.8,
            ("cognitive", "deep_analysis"): 0.95,
            ("cognitive", "fact_checking"): 0.85,
        }

    def predict_combination_quality(self, modes: List[ResearchMode], dependencies: QueryDependencies) -> float:
        """Predict overall quality of methodology combination"""
        if not modes:
            return 0.0

        # Calculate relevance score
        relevance = self._calculate_relevance(modes, dependencies)

        # Calculate completeness score
        completeness = self._calculate_completeness(modes, dependencies)

        # Calculate freshness score (assumed for simplicity)
        freshness = 0.8

        # Calculate authority score (assumed for simplicity)
        authority = 0.85

        # Weighted combination
        quality = (
            relevance * self.weights["relevance"] +
            completeness * self.weights["completeness"] +
            freshness * self.weights["freshness"] +
            authority * self.weights["authority"]
        )

        return min(quality, 1.0)

    def _calculate_relevance(self, modes: List[ResearchMode], dependencies: QueryDependencies) -> float:
        """Calculate how relevant the modes are to the dependencies"""
        total_relevance = 0.0
        covered_aspects = set()

        for mode in modes:
            for aspect in [
                ("code_examples", dependencies.requires_code),
                ("github_repos", dependencies.requires_github),
                ("documentation", dependencies.requires_documentation),
                ("academic_papers", dependencies.requires_academic),
                ("diverse_perspectives", dependencies.requires_ai_perspectives),
            ]:
                aspect_name, needed = aspect
                if needed and aspect_name not in covered_aspects:
                    score = self.mode_quality_scores.get((mode.value, aspect_name), 0.3)
                    total_relevance += score
                    covered_aspects.add(aspect_name)

        return total_relevance / len([a for a, n in [
            ("code_examples", dependencies.requires_code),
            ("github_repos", dependencies.requires_github),
            ("documentation", dependencies.requires_documentation),
            ("academic_papers", dependencies.requires_academic),
            ("diverse_perspectives", dependencies.requires_ai_perspectives),
        ] if n]) if any(n for a, n in [("code_examples", dependencies.requires_code), ("github_repos", dependencies.requires_github), ("documentation", dependencies.requires_documentation), ("academic_papers", dependencies.requires_academic), ("diverse_perspectives", dependencies.requires_ai_perspectives)]) else 1.0

    def _calculate_completeness(self, modes: List[ResearchMode], dependencies: QueryDependencies) -> float:
        """Calculate how completely the modes cover the dependencies"""
        if dependencies.research_depth == "basic":
            return 0.9 if len(modes) >= 1 else 0.5
        elif dependencies.research_depth == "intermediate":
            return 0.9 if len(modes) >= 2 else 0.6
        else:  # advanced
            return 0.9 if len(modes) >= 3 else 0.4
```

#### **2.2 Cost-Benefit Optimization (Week 4)**
```python
# cost_benefit_optimizer.py
from typing import Dict, List, Tuple

class CostBenefitOptimizer:
    def __init__(self):
        # Relative costs (normalized to web = 1.0)
        self.mode_costs = {
            ResearchMode.WEB: 1.0,
            ResearchMode.OCTOCODE: 1.5,  # GitHub API + web
            ResearchMode.MULTI_MODEL: 3.0,  # Multiple AI models
            ResearchMode.COGNITIVE: 2.5,  # Sequential processing
        }

        # Maximum budget (normalized)
        self.max_budget = 5.0

    def optimize_for_budget(self, candidate_modes: List[ResearchMode],
                           predicted_quality: float,
                           budget_limit: float = None) -> List[ResearchMode]:
        """Optimize mode selection within budget constraints"""
        if budget_limit is None:
            budget_limit = self.max_budget

        # Sort by cost-effectiveness (quality/cost ratio)
        modes_with_cost = [
            (mode, self.mode_costs.get(mode, 1.0))
            for mode in candidate_modes
        ]

        # Select modes within budget
        selected_modes = []
        total_cost = 0.0

        # Always include the first (highest value) mode if within budget
        if modes_with_cost:
            best_mode, best_cost = modes_with_cost[0]
            if best_cost <= budget_limit:
                selected_modes.append(best_mode)
                total_cost += best_cost

        # Add additional modes if budget allows
        for mode, cost in modes_with_cost[1:]:
            if total_cost + cost <= budget_limit:
                selected_modes.append(mode)
                total_cost += cost

        return selected_modes
```

### **🚀 PHASE 3: MULTI-MODE ORCHESTRATION**

#### **3.1 Parallel Execution Coordinator (Week 5)**
```python
# multi_mode_orchestrator.py
import asyncio
from typing import Dict, List, Any, Callable
from concurrent.futures import ThreadPoolExecutor

class MultiModeOrchestrator:
    def __init__(self):
        self.mode_executors = {
            ResearchMode.OCTOCODE: self._execute_octocode,
            ResearchMode.WEB: self._execute_web,
            ResearchMode.MULTI_MODEL: self._execute_multi_model,
            ResearchMode.COGNITIVE: self._execute_cognitive,
        }

        # Execution dependencies (some modes depend on others)
        self.execution_dependencies = {
            ResearchMode.COGNITIVE: [],  # Can run independently
            ResearchMode.MULTI_MODEL: [],
            ResearchMode.OCTOCODE: [],
            ResearchMode.WEB: [],
        }

    async def execute_research(self, query: str, modes: List[ResearchMode],
                             tsk_context: Dict = None) -> Dict[str, Any]:
        """Coordinate parallel execution across multiple modes"""
        if not modes:
            return {"error": "No research modes specified"}

        # Create execution plan
        execution_plan = self._create_execution_plan(modes)

        # Execute stages in parallel where possible
        results = {}

        for stage, stage_modes in execution_plan.items():
            stage_tasks = []

            for mode in stage_modes:
                task = asyncio.create_task(
                    self._execute_mode(mode, query, tsk_context)
                )
                stage_tasks.append((mode, task))

            # Wait for all modes in this stage to complete
            for mode, task in stage_tasks:
                try:
                    result = await task
                    results[mode.value] = result
                except Exception as e:
                    results[mode.value] = {"error": str(e)}

        # Synthesize results
        synthesized_results = self._synthesize_results(results, query)

        return {
            "individual_results": results,
            "synthesized_results": synthesized_results,
            "modes_used": [m.value for m in modes],
            "execution_summary": self._create_execution_summary(results)
        }

    def _create_execution_plan(self, modes: List[ResearchMode]) -> Dict[int, List[ResearchMode]]:
        """Create execution plan considering dependencies"""
        # For now, all modes can execute in parallel (stage 0)
        return {0: modes}

    async def _execute_mode(self, mode: ResearchMode, query: str,
                          tsk_context: Dict = None) -> Dict[str, Any]:
        """Execute a single research mode"""
        executor = self.mode_executors.get(mode)
        if not executor:
            raise ValueError(f"No executor for mode: {mode}")

        return await executor(query, tsk_context)

    async def _execute_octocode(self, query: str, tsk_context: Dict = None) -> Dict[str, Any]:
        """Execute octocode research (placeholder for actual implementation)"""
        # This would integrate with the enhanced octocode engine
        return {
            "mode": "octocode",
            "sources": ["github", "web"],
            "results": [],  # Would contain actual research results
            "confidence": 0.85
        }

    async def _execute_web(self, query: str, tsk_context: Dict = None) -> Dict[str, Any]:
        """Execute web search (placeholder for actual implementation)"""
        # This would integrate with tavily or other web search engines
        return {
            "mode": "web",
            "sources": ["web_search"],
            "results": [],  # Would contain actual search results
            "confidence": 0.80
        }

    async def _execute_multi_model(self, query: str, tsk_context: Dict = None) -> Dict[str, Any]:
        """Execute multi-model research (placeholder for actual implementation)"""
        # This would integrate with multiple AI models
        return {
            "mode": "multi-model",
            "sources": ["ai_model_1", "ai_model_2", "ai_model_3"],
            "results": [],  # Would contain actual AI model responses
            "confidence": 0.75
        }

    async def _execute_cognitive(self, query: str, tsk_context: Dict = None) -> Dict[str, Any]:
        """Execute cognitive pipeline (placeholder for actual implementation)"""
        # This would integrate with the enhanced cognitive pipeline
        return {
            "mode": "cognitive-enhanced",
            "sources": ["ai_deep_analysis"],
            "results": [],  # Would contain cognitive analysis results
            "confidence": 0.90
        }

    def _synthesize_results(self, results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Synthesize results from multiple modes"""
        synthesized = {
            "query": query,
            "total_sources": sum(len(r.get("sources", [])) for r in results.values() if isinstance(r, dict)),
            "overall_confidence": 0.0,
            "mode_contributions": {},
            "consensus_points": [],  # Points where multiple modes agree
            "unique_insights": [],   # Unique insights from each mode
            "recommendations": []    # Synthesized recommendations
        }

        # Calculate overall confidence
        confidences = [r.get("confidence", 0.0) for r in results.values()
                      if isinstance(r, dict) and "confidence" in r]
        if confidences:
            synthesized["overall_confidence"] = sum(confidences) / len(confidences)

        # Mode contributions summary
        for mode, result in results.items():
            if isinstance(result, dict):
                synthesized["mode_contributions"][mode] = {
                    "sources": len(result.get("sources", [])),
                    "confidence": result.get("confidence", 0.0)
                }

        return synthesized

    def _create_execution_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of execution results"""
        total_sources = 0
        successful_modes = 0
        total_confidence = 0.0

        for result in results.values():
            if isinstance(result, dict):
                total_sources += len(result.get("sources", []))
                if "confidence" in result:
                    successful_modes += 1
                    total_confidence += result.get("confidence", 0.0)

        return {
            "modes_attempted": len(results),
            "modes_successful": successful_modes,
            "total_sources_found": total_sources,
            "average_confidence": total_confidence / successful_modes if successful_modes > 0 else 0.0
        }
```

### **🚀 PHASE 4: SIMPLE LEARNING SYSTEM**

#### **4.1 Feedback Collection System (Week 7)**
```python
# learning_system.py
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ResearchFeedback:
    query: str
    modes_used: List[str]
    predicted_quality: float
    user_rating: float  # 1-5 scale
    helpful_aspects: List[str]
    improvement_suggestions: List[str]
    timestamp: datetime

class LearningSystem:
    def __init__(self, feedback_file: str = "research_feedback.json"):
        self.feedback_file = feedback_file
        self.feedback_history: List[ResearchFeedback] = []
        self.patterns: Dict[str, Dict] = {}

        self._load_feedback()
        self._analyze_patterns()

    def _load_feedback(self):
        """Load feedback history from file"""
        try:
            with open(self.feedback_file, 'r') as f:
                data = json.load(f)
                self.feedback_history = [
                    ResearchFeedback(
                        query=item['query'],
                        modes_used=item['modes_used'],
                        predicted_quality=item['predicted_quality'],
                        user_rating=item['user_rating'],
                        helpful_aspects=item['helpful_aspects'],
                        improvement_suggestions=item['improvement_suggestions'],
                        timestamp=datetime.fromisoformat(item['timestamp'])
                    )
                    for item in data
                ]
        except FileNotFoundError:
            self.feedback_history = []

    def _save_feedback(self):
        """Save feedback history to file"""
        data = [asdict(feedback) for feedback in self.feedback_history]
        data = [
            {
                **item,
                'timestamp': item['timestamp'].isoformat()
            }
            for item in data
        ]

        with open(self.feedback_file, 'w') as f:
            json.dump(data, f, indent=2)

    def collect_feedback(self, query: str, modes_used: List[str],
                        predicted_quality: float, user_rating: float,
                        helpful_aspects: List[str] = None,
                        improvement_suggestions: List[str] = None) -> None:
        """Collect user feedback for learning"""
        feedback = ResearchFeedback(
            query=query,
            modes_used=modes_used,
            predicted_quality=predicted_quality,
            user_rating=user_rating,
            helpful_aspects=helpful_aspects or [],
            improvement_suggestions=improvement_suggestions or [],
            timestamp=datetime.now()
        )

        self.feedback_history.append(feedback)
        self._save_feedback()
        self._analyze_patterns()

    def _analyze_patterns(self):
        """Analyze feedback patterns for learning"""
        if not self.feedback_history:
            return

        # Analyze which mode combinations work best
        mode_combo_success = {}

        for feedback in self.feedback_history:
            combo_key = '+'.join(sorted(feedback.modes_used))

            if combo_key not in mode_combo_success:
                mode_combo_success[combo_key] = {
                    'count': 0,
                    'total_rating': 0.0,
                    'avg_rating': 0.0
                }

            mode_combo_success[combo_key]['count'] += 1
            mode_combo_success[combo_key]['total_rating'] += feedback.user_rating
            mode_combo_success[combo_key]['avg_rating'] = (
                mode_combo_success[combo_key]['total_rating'] /
                mode_combo_success[combo_key]['count']
            )

        # Store patterns for future recommendations
        self.patterns['mode_combo_success'] = mode_combo_success

        # Analyze query patterns
        query_patterns = {}

        for feedback in self.feedback_history:
            # Simple keyword extraction for pattern analysis
            query_words = set(feedback.query.lower().split())

            for word in query_words:
                if len(word) > 3:  # Only consider meaningful words
                    if word not in query_patterns:
                        query_patterns[word] = {
                            'best_modes': {},
                            'count': 0
                        }

                    query_patterns[word]['count'] += 1

                    combo_key = '+'.join(sorted(feedback.modes_used))
                    if combo_key not in query_patterns[word]['best_modes']:
                        query_patterns[word]['best_modes'][combo_key] = {
                            'count': 0,
                            'total_rating': 0.0,
                            'avg_rating': 0.0
                        }

                    query_patterns[word]['best_modes'][combo_key]['count'] += 1
                    query_patterns[word]['best_modes'][combo_key]['total_rating'] += feedback.user_rating
                    query_patterns[word]['best_modes'][combo_key]['avg_rating'] = (
                        query_patterns[word]['best_modes'][combo_key]['total_rating'] /
                        query_patterns[word]['best_modes'][combo_key]['count']
                    )

        self.patterns['query_patterns'] = query_patterns

    def get_pattern_based_recommendation(self, query: str,
                                       candidate_modes: List[str]) -> Optional[List[str]]:
        """Get recommendation based on learned patterns"""
        if not self.patterns:
            return None

        query_words = set(query.lower().split())
        recommendations = []

        # Look for matching query patterns
        for word in query_words:
            if len(word) > 3 and word in self.patterns.get('query_patterns', {}):
                word_patterns = self.patterns['query_patterns'][word]['best_modes']

                # Find the best performing mode combination
                best_combo = max(word_patterns.items(),
                               key=lambda x: x[1]['avg_rating'] if x[1]['count'] >= 3 else 0)

                if best_combo[1]['count'] >= 3:  # Minimum threshold
                    best_modes = best_combo[0].split('+')
                    if any(mode in candidate_modes for mode in best_modes):
                        recommendations.append(best_modes)

        if recommendations:
            # Return the most common recommendation
            from collections import Counter
            recommendation_counts = Counter(tuple(r) for r in recommendations)
            return list(recommendation_counts.most_common(1)[0][0])

        return None
```

### **🚀 INTEGRATION WITH ENHANCED RESEARCH ENGINE**

#### **5.1 Enhanced Research Engine Integration**
```python
# enhanced_research_engine.py
from typing import Dict, List, Any, Optional

class EnhancedResearchEngine:
    def __init__(self):
        self.dependency_analyzer = SimplifiedDependencyAnalyzer()
        self.mode_mapper = ModeRelationshipMapper()
        self.quality_predictor = QualityPredictor()
        self.cost_optimizer = CostBenefitOptimizer()
        self.orchestrator = MultiModeOrchestrator()
        self.learning_system = LearningSystem()

    async def research(self, query: str, mode: str = "auto",
                      budget_limit: float = None, tsk_context: Dict = None) -> Dict[str, Any]:
        """Enhanced research with intelligent methodology selection"""

        if mode == "auto":
            # Use intelligent methodology selection
            return await self._intelligent_research(query, budget_limit, tsk_context)
        else:
            # Use specified mode
            return await self._single_mode_research(query, mode, tsk_context)

    async def _intelligent_research(self, query: str, budget_limit: float,
                                  tsk_context: Dict) -> Dict[str, Any]:
        """Intelligent research with methodology selection"""

        # Step 1: Analyze dependencies
        dependencies = self.dependency_analyzer.analyze_dependencies(query, tsk_context)

        # Step 2: Find optimal mode combination
        candidate_modes = self.mode_mapper.find_optimal_combination(dependencies)

        # Step 3: Predict quality
        predicted_quality = self.quality_predictor.predict_combination_quality(
            candidate_modes, dependencies
        )

        # Step 4: Get pattern-based recommendation if available
        pattern_recommendation = self.learning_system.get_pattern_based_recommendation(
            query, [m.value for m in candidate_modes]
        )

        if pattern_recommendation:
            # Override with learned recommendation
            candidate_modes = [ResearchMode(m) for m in pattern_recommendation if m in [rm.value for rm in ResearchMode]]

        # Step 5: Optimize for budget
        if budget_limit:
            candidate_modes = self.cost_optimizer.optimize_for_budget(
                candidate_modes, predicted_quality, budget_limit
            )

        # Step 6: Execute research
        results = await self.orchestrator.execute_research(
            query, candidate_modes, tsk_context
        )

        # Step 7: Add metadata for learning
        results["methodology_metadata"] = {
            "dependencies": dependencies.__dict__,
            "candidate_modes": [m.value for m in candidate_modes],
            "predicted_quality": predicted_quality,
            "pattern_recommendation": pattern_recommendation
        }

        return results

    async def _single_mode_research(self, query: str, mode: str,
                                  tsk_context: Dict) -> Dict[str, Any]:
        """Single mode research execution"""
        research_mode = ResearchMode(mode)

        results = await self.orchestrator.execute_research(
            query, [research_mode], tsk_context
        )

        # Add metadata for learning
        results["methodology_metadata"] = {
            "dependencies": {},
            "candidate_modes": [mode],
            "predicted_quality": 0.8,  # Default assumption
            "pattern_recommendation": None
        }

        return results

    def provide_feedback(self, research_id: str, user_rating: float,
                        helpful_aspects: List[str] = None,
                        improvement_suggestions: List[str] = None) -> None:
        """Provide feedback for learning (would need to store research metadata)"""
        # This would integrate with the learning system
        # Implementation would require storing research metadata during execution
        pass
```

## **🎯 ENHANCED IMPLEMENTATION SUMMARY**

### **Key Improvements Made:**

#### **1. Simplified Dependency Analysis**
- **Keyword-based detection** instead of complex ML
- **Simple scoring system** for complexity and confidence
- **Concrete implementation** with specific algorithms

#### **2. Practical Optimization Engine**
- **Heuristic-based mode selection** with clear rules
- **Redundancy elimination** using configurable thresholds
- **Budget-aware optimization** with cost-benefit analysis

#### **3. Scalable Multi-Mode Orchestration**
- **Parallel execution** with dependency resolution
- **Result synthesis** with confidence weighting
- **Error handling** and fallback mechanisms

#### **4. Simple Learning System**
- **Feedback collection** with structured data
- **Pattern recognition** using keyword matching
- **Recommendation engine** based on historical success

#### **5. Clear Integration Path**
- **Enhanced auto mode** replacing rule-based selection
- **Backward compatibility** with existing research modes
- **Metadata collection** for continuous improvement

This enhanced implementation provides a practical, scalable approach that starts simple and can be enhanced over time while delivering immediate value through intelligent methodology selection.