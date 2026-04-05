"""
Tool Selector for RCA Enhancement

Intelligent tool selection based on context analysis.
Provides optimal RCA tool recommendations with performance estimation.
"""
from __future__ import annotations

import time


class ToolSelector:
    """
    Intelligent tool selection based on context analysis
    """

    def __init__(self):
        self.tool_matrix = self._build_tool_matrix()
        self.performance_weights = self._build_performance_weights()

    def _build_tool_matrix(self) -> dict:
        """Build tool selection matrix for different strategies"""
        return {
            "systematic": {
                "primary": ["CHS", "CustomAnalyzer", "TreeSitter"],
                "secondary": ["FileSearch", "PatternMatcher"],
                "description": "Standard investigation with history and code analysis",
                "best_for": ["General bugs", "Crashes", "Simple issues"],
                "parallel_capable": True,
                "complexity_handling": "simple_moderate",
                "performance_weight": 1.0
            },
            "deep_scan": {
                "primary": ["TreeSitter", "HDMA", "ArchitecturalAnalyzer"],
                "secondary": ["DependencyGraph", "ComplexityMetrics", "CodeStructureMapper"],
                "description": "Code structure and architecture analysis",
                "best_for": ["Architecture issues", "Refactoring", "Structural problems"],
                "parallel_capable": False,
                "complexity_handling": "moderate_complex",
                "performance_weight": 1.2
            },
            "exploratory": {
                "primary": ["CHS", "BroadPatternSearch", "SemanticSearch"],
                "secondary": ["FileDiscovery", "ContextualSearch", "CodeDiscovery"],
                "description": "Broad search when starting point unknown",
                "best_for": ["Unknown scope", "Vague problems", "Exploratory analysis"],
                "parallel_capable": True,
                "complexity_handling": "all",
                "performance_weight": 0.8
            },
            "council": {
                "primary": ["PyRCA", "Debugpy", "CustomAnalyzer", "MultiAgentReasoning"],
                "secondary": ["ConsensusEngine", "EvidenceSynthesis", "DebateModerator"],
                "description": "Multi-agent approach for complex problems",
                "best_for": ["Complex issues", "Security problems", "Ambiguous cases"],
                "parallel_capable": False,
                "complexity_handling": "complex_only",
                "performance_weight": 1.5
            }
        }

    def _build_performance_weights(self) -> dict:
        """Build performance weights for different contexts"""
        return {
            "security": 1.5,      # Higher weight for security tools
            "performance": 1.2,   # Higher weight for performance tools
            "architectural": 1.1, # Slightly higher for architectural analysis
            "bug": 1.0,          # Standard weight for bugs
            "unknown": 0.8        # Lower weight for unknown problems
        }

    def select_optimal_tools(self, context: dict) -> dict:
        """
        Select optimal tools for RCA based on context analysis

        Args:
            context: Context analysis results from ContextAnalyzer

        Returns:
            Dictionary containing tool selection results:
            {
                'primary_strategy': str,
                'primary_tools': List[str],
                'secondary_tools': List[str],
                'optimization_level': 'standard|enhanced|maximum',
                'parallel_execution': bool,
                'estimated_performance_gain': float,
                'strategy_description': str,
                'selection_confidence': float,
                'processing_time_ms': float
            }

        """
        start_time = time.time()

        strategy = context.get("recommended_strategy", "systematic")
        problem_type = context.get("problem_type", "unknown")
        context.get("complexity_level", "moderate")

        # Get base tool configuration
        base_tools = self.tool_matrix.get(strategy, self.tool_matrix["systematic"])

        # Calculate selection confidence
        selection_confidence = self._calculate_selection_confidence(context, strategy)

        # Determine optimization level
        optimization_level = self._determine_optimization_level(context)

        # Check for parallel execution capability
        parallel_execution = self._should_execute_parallel(context, strategy)

        # Estimate performance gain
        performance_gain = self._estimate_performance_gain(context, strategy)

        # Enhance tools based on problem type
        enhanced_tools = self._enhance_tools_for_problem_type(base_tools, problem_type)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        return {
            "primary_strategy": strategy,
            "primary_tools": enhanced_tools["primary"],
            "secondary_tools": enhanced_tools.get("secondary", []),
            "optimization_level": optimization_level,
            "parallel_execution": parallel_execution,
            "estimated_performance_gain": performance_gain,
            "strategy_description": base_tools["description"],
            "selection_confidence": selection_confidence,
            "processing_time_ms": processing_time,
            "best_for_scenarios": base_tools.get("best_for", []),
            "complexity_handling": base_tools.get("complexity_handling", "unknown")
        }

    def _calculate_selection_confidence(self, context: dict, strategy: str) -> float:
        """Calculate confidence score for tool selection"""
        confidence = 0.0

        # Base confidence from context analysis (40%)
        context_confidence = context.get("confidence_score", 0.0)
        confidence += 0.4 * context_confidence

        # Strategy-appropriateness confidence (30%)
        strategy_appropriateness = self._evaluate_strategy_appropriateness(context, strategy)
        confidence += 0.3 * strategy_appropriateness

        # Problem type matching confidence (20%)
        problem_type = context.get("problem_type", "unknown")
        if problem_type != "unknown":
            confidence += 0.2

        # Complexity level confidence (10%)
        complexity_level = context.get("complexity_level", "unknown")
        if complexity_level != "unknown":
            confidence += 0.1

        return min(confidence, 1.0)

    def _evaluate_strategy_appropriateness(self, context: dict, strategy: str) -> float:
        """Evaluate how appropriate the strategy is for the context"""
        problem_type = context.get("problem_type", "unknown")
        complexity_level = context.get("complexity_level", "moderate")
        security_indicators = context.get("security_indicators", False)

        # Security problems get high appropriateness for council
        if security_indicators and strategy == "council":
            return 1.0
        if security_indicators and strategy != "council":
            return 0.3

        # Performance problems get high appropriateness for deep_scan
        if problem_type == "performance" and strategy == "deep_scan":
            return 0.9
        if problem_type == "performance" and strategy not in ["deep_scan", "systematic"]:
            return 0.4

        # Complex problems get high appropriateness for council or deep_scan
        if complexity_level == "complex" and strategy in ["council", "deep_scan"]:
            return 0.9
        if complexity_level == "complex" and strategy == "systematic":
            return 0.5

        # Simple problems get high appropriateness for systematic
        if complexity_level == "simple" and strategy == "systematic":
            return 0.9
        if complexity_level == "simple" and strategy == "council":
            return 0.4

        # Default moderate appropriateness
        return 0.7

    def _determine_optimization_level(self, context: dict) -> str:
        """Determine optimization level based on context"""
        complexity_level = context.get("complexity_level", "moderate")
        performance_indicators = context.get("performance_indicators", False)
        security_indicators = context.get("security_indicators", False)

        # Maximum optimization for complex issues or performance problems
        if complexity_level == "complex" or performance_indicators:
            return "maximum"

        # Enhanced optimization for moderate complexity or security issues
        if complexity_level == "moderate" or security_indicators:
            return "enhanced"

        # Standard optimization for simple issues
        return "standard"

    def _should_execute_parallel(self, context: dict, strategy: str) -> bool:
        """Determine if tools should be executed in parallel"""
        # Check if strategy supports parallel execution
        strategy_config = self.tool_matrix.get(strategy, {})
        if not strategy_config.get("parallel_capable", False):
            return False

        # Don't use parallel execution for security issues (sequential is safer)
        if context.get("security_indicators", False):
            return False

        # Use parallel execution for module/system scope
        scope = context.get("scope", "unknown")
        if scope in ["module", "system"]:
            return True

        # Use parallel execution for complex problems
        complexity_level = context.get("complexity_level", "moderate")
        if complexity_level == "complex":
            return True

        return False

    def _estimate_performance_gain(self, context: dict, strategy: str) -> float:
        """Estimate performance gain from intelligent tool selection"""
        base_gain = 0.1  # 10% base improvement from intelligence

        # Problem type-specific gains
        problem_type = context.get("problem_type", "unknown")
        if problem_type in self.performance_weights:
            base_gain += (self.performance_weights[problem_type] - 1.0) * 0.2

        # Complexity-based gains
        complexity_level = context.get("complexity_level", "moderate")
        if complexity_level == "complex":
            base_gain += 0.15  # Additional 15% for complex issues
        elif complexity_level == "simple":
            base_gain += 0.05  # Small gain for simple issues

        # Scope-based gains
        scope = context.get("scope", "unknown")
        if scope == "system":
            base_gain += 0.1  # Additional 10% for system scope
        elif scope == "module":
            base_gain += 0.05  # Small gain for module scope

        # Strategy-specific gains
        strategy_config = self.tool_matrix.get(strategy, {})
        strategy_weight = strategy_config.get("performance_weight", 1.0)
        base_gain += (strategy_weight - 1.0) * 0.1

        # Cap at reasonable maximum
        return min(base_gain, 0.5)  # Maximum 50% estimated gain

    def _enhance_tools_for_problem_type(self, base_tools: dict, problem_type: str) -> dict:
        """Enhance tool selection based on specific problem type"""
        enhanced_tools = {
            "primary": base_tools["primary"].copy(),
            "secondary": base_tools.get("secondary", []).copy()
        }

        # Add specialized tools for specific problem types
        if problem_type == "security":
            enhanced_tools["secondary"].extend(["SecurityScanner", "VulnerabilityAnalyzer", "ThreatModeler"])
        elif problem_type == "performance":
            enhanced_tools["secondary"].extend(["Profiler", "BottleneckAnalyzer", "ResourceMonitor"])
        elif problem_type == "architectural":
            enhanced_tools["secondary"].extend(["DesignPatternAnalyzer", "ArchitectureValidator", "CouplingAnalyzer"])

        return enhanced_tools

    def get_tool_recommendations(self, context: dict, limit: int = 5) -> list[dict]:
        """Get ranked tool recommendations for the context"""
        strategy = context.get("recommended_strategy", "systematic")
        base_tools = self.tool_matrix.get(strategy, self.tool_matrix["systematic"])

        recommendations = []

        # Add primary tools
        for tool in base_tools["primary"]:
            recommendations.append({
                "tool": tool,
                "priority": "high",
                "reason": f"Primary tool for {strategy} strategy",
                "estimated_impact": "high"
            })

        # Add secondary tools
        for tool in base_tools.get("secondary", []):
            recommendations.append({
                "tool": tool,
                "priority": "medium",
                "reason": f"Secondary tool for {strategy} strategy",
                "estimated_impact": "medium"
            })

        # Add problem-type specific tools
        problem_type = context.get("problem_type", "unknown")
        if problem_type == "security":
            recommendations.extend([
                {"tool": "SecurityScanner", "priority": "high", "reason": "Security issue detected", "estimated_impact": "high"},
                {"tool": "VulnerabilityAnalyzer", "priority": "medium", "reason": "Security vulnerability analysis", "estimated_impact": "medium"}
            ])
        elif problem_type == "performance":
            recommendations.extend([
                {"tool": "Profiler", "priority": "high", "reason": "Performance issue detected", "estimated_impact": "high"},
                {"tool": "BottleneckAnalyzer", "priority": "medium", "reason": "Bottleneck identification", "estimated_impact": "medium"}
            ])

        # Sort by priority and impact, then limit
        priority_order = {"high": 3, "medium": 2, "low": 1}
        impact_order = {"high": 3, "medium": 2, "low": 1}

        recommendations.sort(key=lambda x: (
            priority_order.get(x["priority"], 1),
            impact_order.get(x["estimated_impact"], 1)
        ), reverse=True)

        return recommendations[:limit]

    def get_strategy_comparison(self, context: dict) -> dict:
        """Get comparison of all strategies for the current context"""
        comparison = {}

        for strategy_name, strategy_config in self.tool_matrix.items():
            # Calculate appropriateness score for this strategy
            appropriateness = self._evaluate_strategy_appropriateness(context, strategy_name)
            performance_gain = self._estimate_performance_gain(context, strategy_name)

            comparison[strategy_name] = {
                "appropriateness_score": appropriateness,
                "estimated_performance_gain": performance_gain,
                "description": strategy_config["description"],
                "best_for": strategy_config.get("best_for", []),
                "parallel_capable": strategy_config.get("parallel_capable", False),
                "complexity_handling": strategy_config.get("complexity_handling", "unknown"),
                "recommended": strategy_name == context.get("recommended_strategy", "systematic")
            }

        return comparison

    def validate_tool_selection(self, selection: dict, context: dict) -> dict:
        """Validate and provide feedback on tool selection"""
        validation = {
            "is_valid": True,
            "warnings": [],
            "suggestions": [],
            "confidence_score": selection.get("selection_confidence", 0.0)
        }

        # Check for low confidence
        confidence = selection.get("selection_confidence", 0.0)
        if confidence < 0.5:
            validation["warnings"].append("Low confidence in tool selection")
            validation["suggestions"].append("Consider providing more specific problem description")

        # Check for missing tools
        primary_tools = selection.get("primary_tools", [])
        if not primary_tools:
            validation["is_valid"] = False
            validation["warnings"].append("No primary tools selected")

        # Check for strategy-context mismatch
        strategy = selection.get("primary_strategy", "")
        if strategy and not self._evaluate_strategy_appropriateness(context, strategy):
            validation["warnings"].append(f"Strategy {strategy} may not be optimal for this context")

        # Performance warnings
        performance_gain = selection.get("estimated_performance_gain", 0.0)
        if performance_gain < 0.05:
            validation["warnings"].append("Low performance improvement expected")
            validation["suggestions"].append("Consider alternative approaches for better performance")

        return validation


# Performance monitoring for tool selector
class ToolSelectorMetrics:
    """Metrics collection for tool selector performance"""

    def __init__(self):
        self.selection_count = 0
        self.total_processing_time = 0.0
        self.strategy_usage = {}
        self.problem_type_accuracy = {}

    def record_selection(self, selection_result: dict, context: dict):
        """Record metrics for tool selection"""
        self.selection_count += 1
        self.total_processing_time += selection_result["processing_time_ms"]

        # Track strategy usage
        strategy = selection_result.get("primary_strategy", "unknown")
        if strategy not in self.strategy_usage:
            self.strategy_usage[strategy] = 0
        self.strategy_usage[strategy] += 1

        # Track problem type vs strategy correlation
        problem_type = context.get("problem_type", "unknown")
        key = f"{problem_type}_{strategy}"
        if key not in self.problem_type_accuracy:
            self.problem_type_accuracy[key] = 0
        self.problem_type_accuracy[key] += 1

    def get_average_processing_time(self) -> float:
        """Get average processing time in milliseconds"""
        if self.selection_count == 0:
            return 0.0
        return self.total_processing_time / self.selection_count

    def get_strategy_distribution(self) -> dict:
        """Get distribution of strategy usage"""
        total = sum(self.strategy_usage.values())
        if total == 0:
            return {}

        return {strategy: count / total for strategy, count in self.strategy_usage.items()}

    def get_most_used_strategy(self) -> str:
        """Get the most commonly used strategy"""
        if not self.strategy_usage:
            return "unknown"

        return max(self.strategy_usage, key=self.strategy_usage.get)
