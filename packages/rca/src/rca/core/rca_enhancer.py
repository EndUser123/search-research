"""
Enhanced RCA Command

Main enhanced RCA command that integrates all Phase 2 components
with full backward compatibility and intelligent auto-integration.
"""
from __future__ import annotations

import argparse
import sys
import time

# Import Phase 1 core components
try:
    from .context_analyzer import ContextAnalyzer
    from .performance_optimizer import PerformanceOptimizer
    from .tool_selector import ToolSelector
except ImportError:
    # Fallback for direct execution
    from context_analyzer import ContextAnalyzer
    from performance_optimizer import PerformanceOptimizer
    from tool_selector import ToolSelector

# Import Phase 2 integration components
try:
    from ..integration.explore_integration import ExploreIntegration
except ImportError:
    # Fallback for direct execution
    try:
        from rca.integration.explore_integration import ExploreIntegration
    except ImportError:
        ExploreIntegration = None

# TaskMaster integration removed - pattern storage now handled by CKS


class LegacyRCACommand:
    """
    Legacy RCA command wrapper for backward compatibility
    """

    def __init__(self):
        # This would integrate with the existing /rca command
        # For now, we'll simulate the legacy functionality
        pass

    def execute_rca(self, problem_description: str, options: dict = None) -> dict:
        """
        Execute legacy RCA command

        Args:
            problem_description: Problem description to analyze
            options: Command options (strategy, cognitive, etc.)

        Returns:
            RCA analysis results

        """
        options = options or {}

        # Simulate legacy RCA execution
        strategy = options.get("strategy", "systematic")
        cognitive = options.get("cognitive", False)

        # This would call the actual rca-specialist subagent
        # For simulation, return basic results
        return {
            "findings": {
                "problem_type": "unknown",
                "analysis_performed": True,
                "strategy_used": strategy,
                "cognitive_enhancement": cognitive
            },
            "recommendations": [
                f"Analyzed using {strategy} strategy",
                "Consider additional investigation if needed"
            ],
            "legacy_execution": True,
            "execution_time_ms": 1000  # Simulated legacy execution time
        }


class EnhancedRCACommand:
    """
    Enhanced RCA command with intelligent auto-integration
    """

    def __init__(self):
        # Initialize Phase 1 core components
        self.context_analyzer = ContextAnalyzer()
        self.tool_selector = ToolSelector()
        self.performance_optimizer = PerformanceOptimizer()

        # Initialize Phase 2 integration components (optional)
        self.explore_integration = ExploreIntegration() if ExploreIntegration else None

        # Initialize legacy adapter for backward compatibility
        self.legacy_rca = LegacyRCACommand()

        # Feature flags for controlled rollout
        self.feature_flags = self._load_feature_flags()

    def _load_feature_flags(self) -> dict:
        """Load feature flags for controlled rollout"""
        return {
            "enable_context_analysis": True,
            "enable_tool_selection": True,
            "enable_explore_integration": False,  # Phase 2 feature
            "enable_performance_optimization": True,
            "enable_legacy_fallback": True,
            "enable_enhancement_feedback": True
        }

    def execute_rca(self, problem_description: str, options: dict = None) -> dict:
        """
        Execute enhanced RCA with intelligent auto-integration

        Args:
            problem_description: Description of the problem to analyze
            options: Optional command-line options

        Returns:
            Enhanced RCA analysis results

        """
        options = options or {}
        start_time = time.time()

        # Check for legacy mode
        if options.get("legacy_mode"):
            return self._execute_legacy_rca(problem_description, options)

        # Check for Phase 2 feature availability
        phase2_available = (self.feature_flags["enable_explore_integration"] and
                          self.explore_integration is not None)

        if not phase2_available:
            return self._execute_phase1_enhanced_rca(problem_description, options)

        # Full Phase 2 enhanced execution
        return self._execute_phase2_enhanced_rca(problem_description, options)

    def _execute_phase2_enhanced_rca(self, problem_description: str, options: dict) -> dict:
        """Execute RCA with full Phase 2 enhancements"""
        enhancements_applied = []

        try:
            # Step 1: Context Analysis (Intelligence Layer)
            context = self.context_analyzer.analyze_context(problem_description)
            enhancements_applied.append("context_analysis")

            # Step 2: Tool Selection with Explore Integration (Intelligence Layer)
            tool_selection = self.tool_selector.select_optimal_tools(context)
            enhancements_applied.append("intelligent_tool_selection")

            # Step 3: Explore Integration Enhancement (Integration Layer)
            if self.explore_integration:
                explore_enhancements = self.explore_integration.enhance_tool_selection(tool_selection, context)
                if explore_enhancements:
                    tool_selection.update(explore_enhancements)
                    enhancements_applied.append("explore_integration")

            # Step 4: Performance Optimization with Explore Insights (Intelligence Layer)
            optimization = self.performance_optimizer.optimize_execution(tool_selection, context)
            if optimization["optimizations_applied"]:
                enhancements_applied.extend(optimization["optimizations_applied"])

            # Step 5: Execute RCA with Enhanced Capabilities (Execution Layer)
            rca_result = self._execute_enhanced_rca_analysis(
                problem_description, context, tool_selection, optimization, None
            )

            # Calculate total execution time
            total_time = (time.time() - start_time) * 1000

            # Return enhanced results
            result = {
                "session_id": None,  # TaskMaster removed - use CKS for pattern storage
                "findings": rca_result["findings"],
                "recommendations": rca_result["recommendations"],
                "enhancements_applied": list(set(enhancements_applied)),  # Remove duplicates
                "context_analysis": context,
                "tool_selection": tool_selection,
                "performance_optimization": optimization,
                "execution_time_ms": total_time,
                "phase": "phase2_enhanced"
            }

            # Add enhancement feedback if enabled
            if self.feature_flags["enable_enhancement_feedback"]:
                result["enhancement_summary"] = self._generate_enhancement_summary(result)

            return result

        except Exception as e:
            # Fallback to Phase 1 if Phase 2 fails
            if self.feature_flags["enable_legacy_fallback"]:
                return self._execute_phase1_enhanced_rca(problem_description, options)
            raise e

    def _execute_phase1_enhanced_rca(self, problem_description: str, options: dict) -> dict:
        """Execute RCA with Phase 1 enhancements only"""
        enhancements_applied = []
        start_time = time.time()

        try:
            # Step 1: Context Analysis
            context = self.context_analyzer.analyze_context(problem_description)
            enhancements_applied.append("context_analysis")

            # Step 2: Tool Selection
            tool_selection = self.tool_selector.select_optimal_tools(context)
            enhancements_applied.append("intelligent_tool_selection")

            # Step 3: Performance Optimization
            optimization = self.performance_optimizer.optimize_execution(tool_selection, context)
            if optimization["optimizations_applied"]:
                enhancements_applied.extend(optimization["optimizations_applied"])

            # Step 4: Execute Enhanced RCA (without Phase 2 integrations)
            rca_result = self._execute_enhanced_rca_analysis(
                problem_description, context, tool_selection, optimization, None
            )

            # Calculate total execution time
            total_time = (time.time() - start_time) * 1000

            return {
                "session_id": None,
                "findings": rca_result["findings"],
                "recommendations": rca_result["recommendations"],
                "enhancements_applied": list(set(enhancements_applied)),
                "context_analysis": context,
                "tool_selection": tool_selection,
                "performance_optimization": optimization,
                "execution_time_ms": total_time,
                "phase": "phase1_enhanced"
            }

        except Exception as e:
            # Fallback to legacy if Phase 1 fails
            if self.feature_flags["enable_legacy_fallback"]:
                return self._execute_legacy_rca(problem_description, options)
            raise e

    def _execute_legacy_rca(self, problem_description: str, options: dict) -> dict:
        """Execute legacy RCA for backward compatibility"""
        enhancements_applied = ["legacy_fallback"]
        start_time = time.time()

        try:
            # Execute legacy RCA
            legacy_result = self.legacy_rca.execute_rca(problem_description, options)

            # Calculate total execution time
            total_time = (time.time() - start_time) * 1000

            return {
                "session_id": None,
                "findings": legacy_result["findings"],
                "recommendations": legacy_result["recommendations"],
                "enhancements_applied": enhancements_applied,
                "context_analysis": None,
                "tool_selection": None,
                "performance_optimization": None,
                "execution_time_ms": total_time,
                "phase": "legacy",
                "fallback_reason": "Phase enhancement unavailable or failed"
            }

        except Exception as e:
            raise RuntimeError(f"Legacy RCA execution also failed: {e}")

    def _execute_enhanced_rca_analysis(self, problem_description: str, context: dict,
                                    tool_selection: dict, optimization: dict,
                                    session_id: str | None) -> dict:
        """
        Execute RCA analysis with enhanced capabilities

        This would integrate with the actual rca-specialist subagent
        with enhanced tool selection and optimization
        """
        # Extract strategy from tool selection
        strategy = tool_selection.get("primary_strategy", "systematic")

        # Apply optimizations
        if optimization.get("parallel_execution"):
            strategy += "_parallel"

        if optimization.get("optimizations_applied"):
            strategy += "_optimized"

        # Calculate execution time based on performance improvement
        performance_improvement = optimization.get("estimated_time_reduction", 0.0)
        base_time = 1000  # Base legacy execution time (1 second)
        execution_time = base_time * (1 - performance_improvement)

        # Generate enhanced findings based on context and tools
        findings = {
            "problem_type": context.get("problem_type", "unknown"),
            "complexity_level": context.get("complexity_level", "moderate"),
            "scope": context.get("scope", "unknown"),
            "strategy_used": strategy,
            "tools_applied": tool_selection.get("primary_tools", []),
            "optimizations_applied": optimization.get("optimizations_applied", []),
            "performance_improvement": performance_improvement,
            "analysis_confidence": context.get("confidence_score", 0.5),
            "security_concerns": context.get("security_indicators", False),
            "performance_issues": context.get("performance_indicators", False),
            "execution_time_ms": execution_time
        }

        # Generate enhanced recommendations
        recommendations = self._generate_enhanced_recommendations(
            context, tool_selection, optimization
        )

        return {
            "findings": findings,
            "recommendations": recommendations,
            "execution_summary": f"Enhanced RCA analysis completed using {strategy} strategy"
        }

    def _generate_enhanced_recommendations(self, context: dict, tool_selection: dict,
                                         optimization: dict) -> list[str]:
        """Generate enhanced recommendations based on context and analysis"""
        recommendations = []

        problem_type = context.get("problem_type", "unknown")
        complexity_level = context.get("complexity_level", "moderate")
        strategy = tool_selection.get("primary_strategy", "systematic")

        # Base strategy recommendation
        recommendations.append(f"Analysis performed using {strategy} strategy")

        # Problem type-specific recommendations
        if problem_type == "security":
            recommendations.extend([
                "Conduct comprehensive security vulnerability assessment",
                "Review authentication and authorization mechanisms",
                "Implement security best practices and monitoring"
            ])
        elif problem_type == "performance":
            recommendations.extend([
                "Profile application to identify performance bottlenecks",
                "Optimize database queries and caching strategies",
                "Consider architectural improvements for scalability"
            ])
        elif problem_type == "architectural":
            recommendations.extend([
                "Review system architecture for design patterns",
                "Consider refactoring to improve maintainability",
                "Evaluate scalability and extensibility requirements"
            ])

        # Complexity-specific recommendations
        if complexity_level == "complex":
            recommendations.append("Break down complex problem into smaller, manageable components")
        elif complexity_level == "simple":
            recommendations.append("Apply targeted fix with minimal system impact")

        # Optimization-specific recommendations
        if optimization.get("optimizations_applied"):
            recommendations.append("Performance optimizations were applied during analysis")
            if optimization.get("cache_hit_rate", 0) > 0.5:
                recommendations.append("Consider enabling persistent caching for similar issues")

        # Tool-specific recommendations
        primary_tools = tool_selection.get("primary_tools", [])
        if "TreeSitter" in primary_tools:
            recommendations.append("Consider code structure improvements based on TreeSitter analysis")
        if "HDMA" in primary_tools:
            recommendations.append("Review architectural patterns and design decisions")

        return recommendations

    def _generate_enhancement_summary(self, result: dict) -> dict:
        """Generate summary of enhancements applied"""
        summary = {
            "total_enhancements": len(result.get("enhancements_applied", [])),
            "performance_improvement": 0.0,
            "intelligence_applied": False,
            "integration_applied": False,
            "user_experience_impact": "transparent"
        }

        enhancements = result.get("enhancements_applied", [])

        # Calculate performance improvement
        optimization = result.get("performance_optimization", {})
        if optimization:
            summary["performance_improvement"] = optimization.get("estimated_time_reduction", 0.0) * 100

        # Check for intelligence applied
        if any("context_analysis" in e or "intelligent_tool_selection" in e for e in enhancements):
            summary["intelligence_applied"] = True

        # Check for integration applied
        if any("explore_integration" in e for e in enhancements):
            summary["integration_applied"] = True

        return summary

    def parse_command_line_args(self, args: list[str] = None) -> dict:
        """
        Parse command line arguments for enhanced /rca command

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Parsed arguments dictionary

        """
        if args is None:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(add_help=False)

        # Existing options (maintained for backward compatibility)
        parser.add_argument("--strategy", choices=["systematic", "deep_scan", "exploratory", "council"])
        parser.add_argument("--cognitive", action="store_true")
        parser.add_argument("--no-cognitive", action="store_true")
        parser.add_argument("--thinking-modes", type=str)

        # New enhancement options
        parser.add_argument("--legacy-mode", action="store_true",
                           help="Disable all enhancements, use legacy RCA only")
        parser.add_argument("--show-enhancements", action="store_true",
                           help="Show applied enhancements and their impact")
        parser.add_argument("--performance-mode", choices=["standard", "enhanced", "maximum"],
                           default="enhanced", help="Performance optimization level")

        # Phase 2 specific options
        parser.add_argument("--no-explore", action="store_true",
                           help="Disable /explore command integration")

        known_args, unknown_args = parser.parse_known_args(args)

        return {
            "strategy": known_args.strategy,
            "cognitive": known_args.cognitive,
            "no_cognitive": known_args.no_cognitive,
            "thinking_modes": known_args.thinking_modes,
            "legacy_mode": known_args.legacy_mode,
            "show_enhancements": known_args.show_enhancements,
            "performance_mode": known_args.performance_mode,
            "no_explore": known_args.no_explore,
            "unknown_args": unknown_args
        }

    def display_rca_results(self, result: dict, options: dict):
        """
        Display RCA results with enhancement information

        Args:
            result: RCA analysis results
            options: Display options

        """
        print("\n🔍 Enhanced RCA Analysis Results")

        # Display findings
        findings = result.get("findings", {})
        print("\n📋 Analysis Findings:")
        print(f"  • Problem Type: {findings.get('problem_type', 'Unknown')}")
        print(f"  • Complexity Level: {findings.get('complexity_level', 'Unknown')}")
        print(f"  • Strategy Used: {findings.get('strategy_used', 'Unknown')}")
        print(f"  • Analysis Confidence: {findings.get('analysis_confidence', 0):.0%}")

        if findings.get("security_concerns"):
            print("  ⚠️  Security Concerns Detected")
        if findings.get("performance_issues"):
            print("  ⚡ Performance Issues Identified")

        # Display recommendations
        recommendations = result.get("recommendations", [])
        print(f"\n💡 Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

        # Display enhancement information if requested
        if options.get("show_enhancements"):
            self._display_enhancement_info(result)

        # Display performance metrics
        self._display_performance_info(result)

    def _display_enhancement_info(self, result: dict):
        """Display enhancement information"""
        print("\n🚀 Applied Enhancements:")
        enhancements = result.get("enhancements_applied", [])
        if enhancements:
            for enhancement in enhancements:
                print(f"  ✅ {enhancement}")
        else:
            print("  • No enhancements applied (legacy mode)")

        # Display enhancement summary if available
        if "enhancement_summary" in result:
            summary = result["enhancement_summary"]
            print("\n📊 Enhancement Summary:")
            print(f"  • Total Enhancements: {summary['total_enhancements']}")
            print(f"  • Performance Improvement: {summary['performance_improvement']:.1f}%")
            print(f"  • Intelligence Applied: {'Yes' if summary['intelligence_applied'] else 'No'}")
            print(f"  • Integration Applied: {'Yes' if summary['integration_applied'] else 'No'}")

    def _display_performance_info(self, result: dict):
        """Display performance information"""
        execution_time = result.get("execution_time_ms", 0)
        print("\n⏱️  Performance Metrics:")
        print(f"  • Total Execution Time: {execution_time:.0f}ms")

        optimization = result.get("performance_optimization", {})
        if optimization:
            print(f"  • Optimizations Applied: {len(optimization.get('optimizations_applied', []))}")
            print(f"  • Estimated Time Reduction: {optimization.get('estimated_time_reduction', 0):.1%}")
            print(f"  • Cache Hit Rate: {optimization.get('cache_hit_rate', 0):.1%}")

    def get_feature_status(self) -> dict:
        """Get current feature status"""
        return {
            "feature_flags": self.feature_flags.copy(),
            "phase1_available": all([
                self.feature_flags["enable_context_analysis"],
                self.feature_flags["enable_tool_selection"],
                self.feature_flags["enable_performance_optimization"]
            ]),
            "phase2_available": self.feature_flags["enable_explore_integration"],
            "explore_integration": (
                self.explore_integration.get_integration_summary() if self.explore_integration else {}
            ),
            "pattern_integration": "CKS (see cks_pattern_integration.py)"
        }


# Main entry point for enhanced /rca command
def main():
    """Main entry point for enhanced /rca command"""
    enhanced_rca = EnhancedRCACommand()

    # Parse command line arguments
    options = enhanced_rca.parse_command_line_args()

    # Get problem description from args or stdin
    if options["unknown_args"]:
        problem_description = " ".join(options["unknown_args"])
    else:
        problem_description = sys.stdin.read().strip()

    if not problem_description:
        print("Error: No problem description provided")
        sys.exit(1)

    # Execute enhanced RCA
    try:
        result = enhanced_rca.execute_rca(problem_description, options)
        enhanced_rca.display_rca_results(result, options)
    except Exception as e:
        print(f"Error: RCA analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
