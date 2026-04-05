"""
/Explore Command Integration

Integration with enhanced /explore command capabilities for intelligent
tool selection, performance optimization, and specialized analysis.
"""
from __future__ import annotations


class ExploreIntegration:
    """
    Integration with enhanced /explore command capabilities
    """

    def __init__(self):
        self.explore_commands = self._load_explore_commands()
        self.performance_cache = {}
        self.command_registry = self._build_command_registry()

    def _load_explore_commands(self) -> dict:
        """Load available /explore commands"""
        # This would integrate with the actual /explore command registry
        return {
            # File analysis commands
            "file_search": {
                "available": True,
                "performance_factor": 1.0,
                "category": "file_analysis",
                "description": "Advanced file search with pattern matching"
            },
            "semantic_search": {
                "available": True,
                "performance_factor": 1.2,
                "category": "file_analysis",
                "description": "Semantic search in code content"
            },
            "dependency_analysis": {
                "available": True,
                "performance_factor": 1.3,
                "category": "architecture",
                "description": "Comprehensive dependency graph analysis"
            },
            "architecture_analysis": {
                "available": True,
                "performance_factor": 1.4,
                "category": "architecture",
                "description": "System architecture analysis"
            },

            # Performance analysis commands
            "performance_profiling": {
                "available": True,
                "performance_factor": 1.2,
                "category": "performance",
                "description": "Detailed performance profiling"
            },
            "bottleneck_analysis": {
                "available": True,
                "performance_factor": 1.3,
                "category": "performance",
                "description": "System bottleneck identification"
            },
            "resource_usage": {
                "available": True,
                "performance_factor": 1.1,
                "category": "performance",
                "description": "Resource usage analysis"
            },

            # Security analysis commands
            "security_scan": {
                "available": True,
                "performance_factor": 1.4,
                "category": "security",
                "description": "Comprehensive security vulnerability scan"
            },
            "vulnerability_check": {
                "available": True,
                "performance_factor": 1.3,
                "category": "security",
                "description": "Vulnerability assessment"
            },
            "audit_trail": {
                "available": True,
                "performance_factor": 1.1,
                "category": "security",
                "description": "Security audit trail analysis"
            },

            # Code analysis commands
            "code_structure_mapper": {
                "available": True,
                "performance_factor": 1.2,
                "category": "code_analysis",
                "description": "Code structure visualization"
            },
            "design_pattern_check": {
                "available": True,
                "performance_factor": 1.1,
                "category": "code_analysis",
                "description": "Design pattern validation"
            },
            "complexity_metrics": {
                "available": True,
                "performance_factor": 1.2,
                "category": "code_analysis",
                "description": "Code complexity analysis"
            }
        }

    def _build_command_registry(self) -> dict:
        """Build comprehensive command registry with optimization hints"""
        registry = {}

        for command_id, command_info in self.explore_commands.items():
            if command_info["available"]:
                registry[command_id] = {
                    "id": command_id,
                    "category": command_info["category"],
                    "performance_factor": command_info["performance_factor"],
                    "description": command_info["description"],
                    "optimal_for": self._get_optimal_use_cases(command_id),
                    "complementary": self._get_complementary_commands(command_id)
                }

        return registry

    def _get_optimal_use_cases(self, command_id: str) -> list[str]:
        """Get optimal use cases for a command"""
        use_cases = {
            "file_search": ["unknown_scope", "file_discovery", "pattern_matching"],
            "semantic_search": ["content_analysis", "semantic_matching", "code_understanding"],
            "dependency_analysis": ["architectural_issues", "refactoring", "impact_analysis"],
            "architecture_analysis": ["system_design", "structure_analysis", "scalability_issues"],
            "performance_profiling": ["performance_bottlenecks", "optimization", "resource_analysis"],
            "bottleneck_analysis": ["performance_issues", "system_analysis", "optimization"],
            "resource_usage": ["resource_optimization", "performance_tuning", "capacity_planning"],
            "security_scan": ["security_vulnerabilities", "compliance", "threat_assessment"],
            "vulnerability_check": ["security_analysis", "vulnerability_assessment", "code_review"],
            "audit_trail": ["forensics", "compliance", "security_analysis"],
            "code_structure_mapper": ["architecture_understanding", "refactoring", "code_review"],
            "design_pattern_check": ["architecture_review", "design_validation", "best_practices"],
            "complexity_metrics": ["code_quality", "maintainability", "refactoring_planning"]
        }
        return use_cases.get(command_id, ["general_analysis"])

    def _get_complementary_commands(self, command_id: str) -> list[str]:
        """Get commands that complement this command"""
        complementary = {
            "file_search": ["semantic_search", "dependency_analysis"],
            "semantic_search": ["file_search", "code_structure_mapper"],
            "dependency_analysis": ["architecture_analysis", "code_structure_mapper"],
            "architecture_analysis": ["dependency_analysis", "design_pattern_check"],
            "performance_profiling": ["bottleneck_analysis", "resource_usage"],
            "bottleneck_analysis": ["performance_profiling", "dependency_analysis"],
            "resource_usage": ["performance_profiling", "bottleneck_analysis"],
            "security_scan": ["vulnerability_check", "audit_trail"],
            "vulnerability_check": ["security_scan", "dependency_analysis"],
            "audit_trail": ["security_scan", "vulnerability_check"],
            "code_structure_mapper": ["dependency_analysis", "design_pattern_check"],
            "design_pattern_check": ["code_structure_mapper", "architecture_analysis"],
            "complexity_metrics": ["code_structure_mapper", "dependency_analysis"]
        }
        return complementary.get(command_id, [])

    def enhance_tool_selection(self, tool_selection: dict, context: dict) -> dict:
        """
        Enhance tool selection using /explore capabilities

        Args:
            tool_selection: Current tool selection from ToolSelector
            context: Context analysis from ContextAnalyzer

        Returns:
            Enhanced tool selection with explore integration

        """
        enhancements = {}

        # Add context-specific explore commands
        context_commands = self._get_context_commands(context)
        if context_commands:
            enhancements["explore_commands"] = context_commands

        # Add performance optimization hints
        perf_hints = self._get_performance_hints(context)
        if perf_hints:
            enhancements["performance_hints"] = perf_hints

        # Add specialized analysis tools
        specialized_tools = self._get_specialized_tools(context)
        if specialized_tools:
            enhancements["specialized_tools"] = specialized_tools

        # Add optimization recommendations
        optimization_recs = self._get_optimization_recommendations(tool_selection, context)
        if optimization_recs:
            enhancements["optimization_recommendations"] = optimization_recs

        return enhancements

    def _get_context_commands(self, context: dict) -> list[str]:
        """Get relevant /explore commands for context"""
        commands = []
        problem_type = context.get("problem_type", "unknown")
        complexity_level = context.get("complexity_level", "moderate")
        scope = context.get("scope", "unknown")

        # Problem type-specific commands
        if problem_type == "security":
            commands.extend(["security_scan", "vulnerability_check", "audit_trail"])
        elif problem_type == "performance":
            commands.extend(["performance_profiling", "bottleneck_analysis", "resource_usage"])
        elif problem_type == "architectural":
            commands.extend(["architecture_analysis", "dependency_analysis", "design_pattern_check"])

        # Complexity-specific commands
        if complexity_level == "complex":
            commands.extend(["dependency_analysis", "architecture_analysis", "complexity_metrics"])
        elif complexity_level == "simple":
            commands.extend(["file_search", "semantic_search"])

        # Scope-specific commands
        if scope == "system":
            commands.extend(["architecture_analysis", "dependency_analysis"])
        elif scope == "module":
            commands.extend(["code_structure_mapper", "design_pattern_check"])

        # Remove duplicates while maintaining order
        return list(dict.fromkeys(commands))

    def _get_performance_hints(self, context: dict) -> list[str]:
        """Get performance optimization hints"""
        hints = []
        problem_type = context.get("problem_type", "unknown")
        complexity_level = context.get("complexity_level", "moderate")
        scope = context.get("scope", "unknown")

        # Scope-based hints
        if scope == "system":
            hints.append("use_parallel_processing")
        elif scope == "module":
            hints.append("optimize_tool_ordering")

        # Complexity-based hints
        if complexity_level == "complex":
            hints.append("enable_advanced_caching")
            hints.append("use_intelligent_pruning")
        elif complexity_level == "simple":
            hints.append("use_fast_path_execution")

        # Problem type-based hints
        if problem_type == "performance":
            hints.append("prioritize_performance_tools")
        elif problem_type == "security":
            hints.append("use_sequential_execution_for_safety")

        return hints

    def _get_specialized_tools(self, context: dict) -> list[str]:
        """Get specialized tools for context"""
        tools = []
        problem_type = context.get("problem_type", "unknown")
        security_indicators = context.get("security_indicators", False)
        performance_indicators = context.get("performance_indicators", False)

        # Problem type-specific tools
        if problem_type == "security" or security_indicators:
            tools.extend([
                "security_scanner", "threat_modeler", "compliance_checker",
                "vulnerability_analyzer", "security_pattern_matcher"
            ])

        if problem_type == "performance" or performance_indicators:
            tools.extend([
                "performance_profiler", "bottleneck_analyzer", "resource_monitor",
                "performance_pattern_detector", "optimization_recommender"
            ])

        if problem_type == "architectural":
            tools.extend([
                "architecture_validator", "design_pattern_analyzer", "coupling_analyzer",
                "scalability_assessor", "technical_debt_analyzer"
            ])

        return list(dict.fromkeys(tools))  # Remove duplicates

    def _get_optimization_recommendations(self, tool_selection: dict, context: dict) -> list[str]:
        """Get optimization recommendations based on tools and context"""
        recommendations = []
        primary_tools = tool_selection.get("primary_tools", [])
        secondary_tools = tool_selection.get("secondary_tools", [])

        # Tool combination optimization
        if "TreeSitter" in primary_tools and "HDMA" in primary_tools:
            recommendations.append("use_tree_sitter_first_for_syntax_then_hdma_for_semantics")

        if "CHS" in primary_tools and "semantic_search" in secondary_tools:
            recommendations.append("combine_chs_history_with_semantic_search")

        # Performance optimization recommendations
        if len(primary_tools) > 2:
            recommendations.append("consider_parallel_execution_for_independent_tools")

        if context.get("complexity_level") == "complex":
            recommendations.append("use_progressive_analysis_starting_broad_then_narrow")

        # Resource optimization recommendations
        if context.get("scope") == "system":
            recommendations.append("use_targeted_analysis_instead_of_full_system_scan")

        return recommendations

    def has_direct_api(self, context: dict) -> bool:
        """Check if /explore has direct API for this context"""
        relevant_commands = self._get_context_commands(context)
        return any(
            cmd in self.explore_commands and self.explore_commands[cmd]["available"]
            for cmd in relevant_commands
        )

    def get_command_performance_factor(self, command: str) -> float:
        """Get performance factor for a command"""
        if command in self.explore_commands:
            return self.explore_commands[command]["performance_factor"]
        return 1.0

    def optimize_command_sequence(self, commands: list[str], context: dict) -> list[str]:
        """Optimize command execution sequence"""
        if not commands:
            return commands

        # Get command information
        command_info = {}
        for cmd in commands:
            if cmd in self.command_registry:
                command_info[cmd] = self.command_registry[cmd]

        # Sort by performance factor (higher = more impactful first)
        sorted_commands = sorted(
            commands,
            key=lambda cmd: command_info.get(cmd, {}).get("performance_factor", 1.0),
            reverse=True
        )

        # Apply context-specific ordering
        if context.get("security_indicators", False):
            # Security commands first
            security_commands = [cmd for cmd in sorted_commands
                               if command_info.get(cmd, {}).get("category") == "security"]
            other_commands = [cmd for cmd in sorted_commands if cmd not in security_commands]
            return security_commands + other_commands

        if context.get("performance_indicators", False):
            # Performance commands first
            perf_commands = [cmd for cmd in sorted_commands
                            if command_info.get(cmd, {}).get("category") == "performance"]
            other_commands = [cmd for cmd in sorted_commands if cmd not in perf_commands]
            return perf_commands + other_commands

        return sorted_commands

    def get_command_recommendations(self, context: dict, limit: int = 10) -> list[dict]:
        """Get ranked command recommendations for context"""
        recommendations = []
        all_commands = list(self.command_registry.keys())

        for command in all_commands:
            cmd_info = self.command_registry[command]
            relevance_score = self._calculate_command_relevance(command, context)

            if relevance_score > 0.1:  # Minimum relevance threshold
                recommendations.append({
                    "command": command,
                    "description": cmd_info["description"],
                    "category": cmd_info["category"],
                    "relevance_score": relevance_score,
                    "performance_factor": cmd_info["performance_factor"],
                    "optimal_for": cmd_info["optimal_for"]
                })

        # Sort by relevance score and performance factor
        recommendations.sort(
            key=lambda x: (x["relevance_score"], x["performance_factor"]),
            reverse=True
        )

        return recommendations[:limit]

    def _calculate_command_relevance(self, command: str, context: dict) -> float:
        """Calculate relevance score for command in context"""
        if command not in self.command_registry:
            return 0.0

        cmd_info = self.command_registry[command]
        relevance = 0.0

        # Problem type relevance
        problem_type = context.get("problem_type", "unknown")
        category_relevance = {
            "security": {"security": 1.0, "performance": 0.3, "code_analysis": 0.5},
            "performance": {"performance": 1.0, "security": 0.2, "architecture": 0.6},
            "architecture": {"architecture": 1.0, "code_analysis": 0.8, "performance": 0.5},
            "code_analysis": {"code_analysis": 1.0, "architecture": 0.7, "security": 0.4},
            "file_analysis": {"file_analysis": 1.0, "code_analysis": 0.8}
        }

        cmd_category = cmd_info["category"]
        if cmd_category in category_relevance and problem_type in category_relevance[cmd_category]:
            relevance += category_relevance[cmd_category][problem_type] * 0.4

        # Complexity relevance
        complexity_level = context.get("complexity_level", "moderate")
        if complexity_level == "complex" and cmd_info["performance_factor"] > 1.2:
            relevance += 0.3
        elif complexity_level == "simple" and cmd_info["performance_factor"] <= 1.2:
            relevance += 0.2

        # Scope relevance
        scope = context.get("scope", "unknown")
        if (scope == "system" and cmd_category in ["architecture", "performance"]) or (scope == "specific_file" and cmd_category in ["file_analysis", "code_analysis"]):
            relevance += 0.2

        return min(relevance, 1.0)

    def get_integration_summary(self) -> dict:
        """Get summary of explore integration capabilities"""
        return {
            "total_commands": len(self.explore_commands),
            "available_commands": sum(1 for cmd in self.explore_commands.values()
                                   if cmd["available"]),
            "categories": list({cmd["category"] for cmd in self.explore_commands.values()
                                if cmd["available"]}),
            "performance_factors": {cmd: info["performance_factor"]
                                 for cmd, info in self.explore_commands.items()
                                 if info["available"]},
            "command_registry_size": len(self.command_registry),
            "integration_capabilities": {
                "tool_selection_enhancement": True,
                "performance_optimization": True,
                "specialized_analysis": True,
                "context_aware_recommendations": True,
                "direct_api_support": True
            }
        }


# Performance monitoring for explore integration
class ExploreIntegrationMetrics:
    """Metrics collection for explore integration performance"""

    def __init__(self):
        self.enhancement_count = 0
        self.total_processing_time = 0.0
        self.command_usage = {}
        self.context_analysis_accuracy = {}

    def record_enhancement(self, enhancement_result: dict, context: dict):
        """Record metrics for enhancement operation"""
        self.enhancement_count += 1
        self.total_processing_time += enhancement_result.get("processing_time_ms", 0)

        # Track command usage
        if "explore_commands" in enhancement_result:
            for command in enhancement_result["explore_commands"]:
                if command not in self.command_usage:
                    self.command_usage[command] = 0
                self.command_usage[command] += 1

        # Track context analysis accuracy (if ground truth available)
        # This would be updated based on user feedback or validation

    def get_average_processing_time(self) -> float:
        """Get average processing time in milliseconds"""
        if self.enhancement_count == 0:
            return 0.0
        return self.total_processing_time / self.enhancement_count

    def get_most_used_commands(self, limit: int = 5) -> list[tuple[str, int]]:
        """Get most commonly used commands"""
        sorted_commands = sorted(self.command_usage.items(),
                                key=lambda x: x[1],
                                reverse=True)
        return sorted_commands[:limit]

    def get_command_distribution(self) -> dict[str, float]:
        """Get distribution of command usage"""
        total_usage = sum(self.command_usage.values())
        if total_usage == 0:
            return {}

        return {cmd: count / total_usage for cmd, count in self.command_usage.items()}
