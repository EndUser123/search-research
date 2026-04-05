"""
Performance Optimizer for RCA Enhancement

Intelligent performance optimization for RCA execution with caching,
parallel execution, and direct API integration capabilities.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any


class AnalysisCache:
    """
    Thread-safe LRU cache for analysis results with TTL support
    """

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
        self.hit_count = 0
        self.miss_count = 0

    def _generate_cache_key(self, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, str):
            key_data = data
        else:
            key_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True

        age_seconds = (datetime.now() - self.timestamps[key]).total_seconds()
        return age_seconds > self.ttl_seconds

    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = datetime.now()
        expired_keys = []

        for key, timestamp in self.timestamps.items():
            age_seconds = (current_time - timestamp).total_seconds()
            if age_seconds > self.ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)

    def get(self, key_data: Any) -> Any | None:
        """Get value from cache"""
        with self.lock:
            key = self._generate_cache_key(key_data)

            # Check if entry exists and is not expired
            if key in self.cache and not self._is_expired(key):
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self.hit_count += 1
                return self.cache[key]

            self.miss_count += 1

            # Cleanup expired entries periodically
            if self.miss_count % 100 == 0:
                self._cleanup_expired()

            return None

    def put(self, key_data: Any, value: Any):
        """Put value into cache"""
        with self.lock:
            key = self._generate_cache_key(key_data)

            # Remove oldest if cache is full
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key, None)

            self.cache[key] = value
            self.timestamps[key] = datetime.now()

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hit_count = 0
            self.miss_count = 0

    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / total_requests if total_requests > 0 else 0.0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": self.get_hit_rate(),
            "cache_size": len(self.cache),
            "max_size": self.max_size
        }


class ParallelExecutor:
    """
    Thread-safe parallel execution manager for RCA tools
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.execution_history = []

    def can_execute_parallel(self, tools: list[str], context: dict) -> bool:
        """Determine if tools can be executed in parallel"""
        # Don't use parallel execution for security issues
        if context.get("security_indicators", False):
            return False

        # Check if tools support parallel execution
        parallel_incompatible = ["PyRCA", "Debugpy", "MultiAgentReasoning"]  # Sequential tools
        if any(tool in parallel_incompatible for tool in tools):
            return False

        # Use parallel execution for multiple tools
        return len(tools) > 1

    def create_execution_plan(self, tools: dict, context: dict) -> list[dict]:
        """Create optimized execution plan"""
        plan = []
        tool_sequence = []

        # Add primary tools
        for tool in tools.get("primary_tools", []):
            tool_sequence.append({"tool": tool, "priority": "high", "phase": 1})

        # Add secondary tools
        for tool in tools.get("secondary_tools", []):
            tool_sequence.append({"tool": tool, "priority": "medium", "phase": 2})

        # Organize into parallel groups
        if tools.get("parallel_execution", False):
            plan = self._create_parallel_plan(tool_sequence, context)
        else:
            plan = self._create_sequential_plan(tool_sequence, context)

        return plan

    def _create_parallel_plan(self, tool_sequence: list[dict], context: dict) -> list[dict]:
        """Create parallel execution plan"""
        plan = []
        current_group = []
        current_phase = 1

        for tool_info in tool_sequence:
            # Start new group for different phase or incompatible tools
            if (tool_info["phase"] != current_phase or
                not self._are_tools_compatible(current_group + [tool_info])):

                if current_group:
                    plan.append({
                        "type": "parallel",
                        "tools": current_group.copy(),
                        "estimated_time": self._estimate_group_time(current_group)
                    })
                    current_group = []

                current_phase = tool_info["phase"]

            current_group.append(tool_info)

        # Add final group
        if current_group:
            plan.append({
                "type": "parallel" if len(current_group) > 1 else "sequential",
                "tools": current_group.copy(),
                "estimated_time": self._estimate_group_time(current_group)
            })

        return plan

    def _create_sequential_plan(self, tool_sequence: list[dict], context: dict) -> list[dict]:
        """Create sequential execution plan"""
        plan = []

        for tool_info in tool_sequence:
            plan.append({
                "type": "sequential",
                "tools": [tool_info],
                "estimated_time": self._estimate_tool_time(tool_info["tool"], context)
            })

        return plan

    def _are_tools_compatible(self, tools: list[dict]) -> bool:
        """Check if tools can be executed together in parallel"""
        tool_names = [tool["tool"] for tool in tools]

        # Tools that require exclusive access
        exclusive_tools = ["PyRCA", "Debugpy", "DatabaseConnection"]
        if any(tool in exclusive_tools for tool in tool_names):
            return False

        # Tools that modify shared state
        state_modifying = ["FileWriter", "DatabaseWriter", "CacheUpdater"]
        if len([tool for tool in tool_names if tool in state_modifying]) > 1:
            return False

        return True

    def _estimate_group_time(self, tools: list[dict]) -> float:
        """Estimate execution time for a group of tools"""
        if not tools:
            return 0.0

        # For parallel execution, use the maximum time
        base_times = {
            "CHS": 0.5, "CustomAnalyzer": 1.0, "TreeSitter": 0.8,
            "FileSearch": 0.3, "PatternMatcher": 0.4, "HDMA": 1.5,
            "ArchitecturalAnalyzer": 2.0, "SemanticSearch": 0.6,
            "SecurityScanner": 1.2, "Profiler": 0.9, "Debugger": 1.8
        }

        max_time = 0.0
        for tool_info in tools:
            tool_time = base_times.get(tool_info["tool"], 1.0)
            # Adjust for priority
            if tool_info.get("priority") == "high":
                tool_time *= 1.2
            max_time = max(max_time, tool_time)

        return max_time

    def _estimate_tool_time(self, tool: str, context: dict) -> float:
        """Estimate execution time for a single tool"""
        base_times = {
            "CHS": 0.5, "CustomAnalyzer": 1.0, "TreeSitter": 0.8,
            "FileSearch": 0.3, "PatternMatcher": 0.4, "HDMA": 1.5,
            "ArchitecturalAnalyzer": 2.0, "SemanticSearch": 0.6,
            "SecurityScanner": 1.2, "Profiler": 0.9, "Debugger": 1.8
        }

        base_time = base_times.get(tool, 1.0)

        # Adjust for context complexity
        complexity_multiplier = {
            "simple": 0.8,
            "moderate": 1.0,
            "complex": 1.5
        }.get(context.get("complexity_level", "moderate"), 1.0)

        return base_time * complexity_multiplier


class PerformanceOptimizer:
    """
    Performance optimization for RCA execution
    """

    def __init__(self, cache_size: int = 1000, cache_ttl_hours: int = 24):
        self.cache = AnalysisCache(cache_size, cache_ttl_hours)
        self.parallel_executor = ParallelExecutor()
        self.optimization_history = []
        self.performance_metrics = {
            "optimizations_applied": 0,
            "cache_hits": 0,
            "parallel_executions": 0,
            "total_time_saved": 0.0
        }

    def optimize_execution(self, tools: dict, context: dict) -> dict:
        """
        Optimize RCA execution based on tools and context

        Args:
            tools: Tool selection results from ToolSelector
            context: Context analysis results from ContextAnalyzer

        Returns:
            Dictionary containing optimization results:
            {
                'execution_plan': List[Dict],
                'optimizations_applied': List[str],
                'estimated_time_reduction': float,
                'cache_hit_rate': float,
                'parallel_execution': bool,
                'processing_time_ms': float
            }

        """
        start_time = time.time()

        optimizations = []
        time_reduction = 0.0

        # Step 1: Check for cached results
        cache_key = {
            "tools": tools,
            "context": context
        }
        cached_plan = self.cache.get(cache_key)

        if cached_plan:
            optimizations.append("cache_optimization")
            self.performance_metrics["cache_hits"] += 1
            execution_plan = cached_plan
            time_reduction += 0.3  # 30% time reduction from cache
        else:
            # Step 2: Create optimized execution plan
            execution_plan = self.parallel_executor.create_execution_plan(tools, context)

            # Step 3: Apply performance optimizations
            plan_optimizations, plan_time_reduction = self._apply_plan_optimizations(execution_plan, context)
            optimizations.extend(plan_optimizations)
            time_reduction += plan_time_reduction

            # Cache the optimized plan
            self.cache.put(cache_key, execution_plan)

        # Step 4: Check for parallel execution opportunities
        if tools.get("parallel_execution", False):
            parallel_tools = [step for step in execution_plan if step.get("type") == "parallel"]
            if parallel_tools:
                optimizations.append("parallel_execution")
                self.performance_metrics["parallel_executions"] += 1
                time_reduction += 0.2  # Additional 20% reduction from parallel

        # Step 5: Apply context-specific optimizations
        context_optimizations, context_time_reduction = self._apply_context_optimizations(
            execution_plan, context
        )
        optimizations.extend(context_optimizations)
        time_reduction += context_time_reduction

        # Step 6: Apply intelligent pruning if needed
        if self._should_prune_tools(execution_plan, context):
            pruned_plan, pruning_reduction = self._intelligent_pruning(execution_plan, context)
            execution_plan = pruned_plan
            optimizations.append("intelligent_pruning")
            time_reduction += pruning_reduction

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Update metrics
        self.performance_metrics["optimizations_applied"] += len(optimizations)
        self.performance_metrics["total_time_saved"] += time_reduction

        # Store optimization history
        self.optimization_history.append({
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "optimizations": optimizations,
            "time_reduction": time_reduction,
            "cache_hit_rate": self.cache.get_hit_rate()
        })

        return {
            "execution_plan": execution_plan,
            "optimizations_applied": list(set(optimizations)),  # Remove duplicates
            "estimated_time_reduction": min(time_reduction, 0.6),  # Cap at 60% reduction
            "cache_hit_rate": self.cache.get_hit_rate(),
            "cache_stats": self.cache.get_stats(),
            "parallel_execution": tools.get("parallel_execution", False),
            "processing_time_ms": processing_time,
            "estimated_total_time": self._estimate_total_time(execution_plan),
            "performance_metrics": self.performance_metrics.copy()
        }

    def _apply_plan_optimizations(self, plan: list[dict], context: dict) -> tuple[list[str], float]:
        """Apply optimizations to execution plan"""
        optimizations = []
        time_reduction = 0.0

        # Optimize tool ordering
        optimized_plan = self._optimize_tool_ordering(plan, context)
        if optimized_plan != plan:
            optimizations.append("tool_ordering_optimization")
            time_reduction += 0.1  # 10% reduction from better ordering

        # Remove redundant tools
        pruned_plan, reduction = self._remove_redundant_tools(plan, context)
        if len(pruned_plan) < len(plan):
            optimizations.append("redundancy_elimination")
            time_reduction += reduction

        return optimizations, time_reduction

    def _apply_context_optimizations(self, plan: list[dict], context: dict) -> tuple[list[str], float]:
        """Apply context-specific optimizations"""
        optimizations = []
        time_reduction = 0.0

        # Performance context optimizations
        if context.get("performance_indicators", False):
            optimizations.append("performance_focus")
            time_reduction += 0.1  # Prioritize performance tools

        # Security context optimizations
        if context.get("security_indicators", False):
            optimizations.append("security_sequential_execution")
            # No time reduction, but improved security

        # Complexity-based optimizations
        complexity = context.get("complexity_level", "moderate")
        if complexity == "simple":
            optimizations.append("simple_execution_plan")
            time_reduction += 0.15  # Simple plans can be faster

        return optimizations, time_reduction

    def _optimize_tool_ordering(self, plan: list[dict], context: dict) -> list[dict]:
        """Optimize tool ordering for maximum efficiency"""
        # Priority order: high priority tools first, then fast tools
        def sort_key(step):
            tool_priority = {"high": 3, "medium": 2, "low": 1}
            tool_speed = {"CHS": 1, "FileSearch": 1, "TreeSitter": 2, "CustomAnalyzer": 3}

            if step.get("type") == "parallel" and step.get("tools"):
                # For parallel groups, use the highest priority/slowest tool
                main_tool = step["tools"][0]
                priority = tool_priority.get(main_tool.get("priority", "medium"), 2)
                speed = tool_speed.get(main_tool.get("tool", "CustomAnalyzer"), 3)
            # For sequential steps, use priority then speed
            elif step.get("tools"):
                tool = step["tools"][0]
                priority = tool_priority.get(tool.get("priority", "medium"), 2)
                speed = tool_speed.get(tool.get("tool", "CustomAnalyzer"), 3)
            else:
                priority = 2
                speed = 3

            return (-priority, speed)  # Negative for descending priority

        return sorted(plan, key=sort_key)

    def _remove_redundant_tools(self, plan: list[dict], context: dict) -> tuple[list[dict], float]:
        """Remove redundant tools from execution plan"""
        # Define tool redundancy relationships
        redundant_pairs = [
            ("FileSearch", "SemanticSearch"),  # Semantic search includes file search
            ("PatternMatcher", "SemanticSearch"),  # Semantic search includes pattern matching
            ("CodeStructureMapper", "ArchitecturalAnalyzer"),  # Architectural analyzer includes structure mapping
        ]

        pruned_plan = []
        tools_used = set()
        time_reduction = 0.0

        for step in plan:
            if step.get("type") == "parallel" and step.get("tools"):
                # Filter redundant tools in parallel steps
                filtered_tools = []
                for tool_info in step["tools"]:
                    tool_name = tool_info.get("tool", "")
                    is_redundant = False

                    for primary, redundant in redundant_pairs:
                        if tool_name == redundant and primary in tools_used:
                            is_redundant = True
                            time_reduction += 0.05  # 5% reduction per redundant tool
                            break

                    if not is_redundant:
                        filtered_tools.append(tool_info)
                        tools_used.add(tool_name)

                if filtered_tools:
                    step["tools"] = filtered_tools
                    pruned_plan.append(step)
            else:
                pruned_plan.append(step)
                if step.get("tools"):
                    tools_used.add(step["tools"][0].get("tool", ""))

        return pruned_plan, time_reduction

    def _should_prune_tools(self, plan: list[dict], context: dict) -> bool:
        """Determine if tools should be pruned for efficiency"""
        complexity = context.get("complexity_level", "moderate")
        tool_count = sum(len(step.get("tools", [])) for step in plan)

        return (
            complexity == "simple" and
            tool_count > 3 and
            not context.get("security_indicators", False)
        )

    def _intelligent_pruning(self, plan: list[dict], context: dict) -> tuple[list[dict], float]:
        """Intelligently prune tools while maintaining effectiveness"""
        pruned_plan = []
        time_reduction = 0.0

        # Keep all high-priority tools
        # Selectively keep medium-priority tools based on context
        # Remove low-priority tools for simple problems

        for step in plan:
            if step.get("type") == "parallel" and step.get("tools"):
                filtered_tools = []
                for tool_info in step["tools"]:
                    priority = tool_info.get("priority", "medium")
                    tool_name = tool_info.get("tool", "")

                    # Keep high-priority tools always
                    if priority == "high" or (priority == "medium" and self._is_tool_relevant(tool_name, context)):
                        filtered_tools.append(tool_info)
                    # Skip low-priority tools for simple problems
                    elif priority == "low" and context.get("complexity_level") == "simple":
                        time_reduction += 0.05  # 5% reduction per pruned tool
                        continue
                    else:
                        filtered_tools.append(tool_info)

                if filtered_tools:
                    step["tools"] = filtered_tools
                    pruned_plan.append(step)
            else:
                pruned_plan.append(step)

        return pruned_plan, time_reduction

    def _is_tool_relevant(self, tool: str, context: dict) -> bool:
        """Check if tool is relevant for the current context"""
        problem_type = context.get("problem_type", "unknown")
        performance_indicators = context.get("performance_indicators", False)
        security_indicators = context.get("security_indicators", False)

        # Context-tool relevance mapping
        relevance_map = {
            "performance": ["Profiler", "BottleneckAnalyzer", "ResourceMonitor"],
            "security": ["SecurityScanner", "VulnerabilityAnalyzer", "ThreatModeler"],
            "architectural": ["ArchitecturalAnalyzer", "DesignPatternAnalyzer", "DependencyGraph"]
        }

        if problem_type in relevance_map:
            return tool in relevance_map[problem_type]

        if performance_indicators and tool in ["Profiler", "BottleneckAnalyzer"]:
            return True

        if security_indicators and tool in ["SecurityScanner", "VulnerabilityAnalyzer"]:
            return True

        return True  # Default to relevant

    def _estimate_total_time(self, plan: list[dict]) -> float:
        """Estimate total execution time for the plan"""
        total_time = 0.0

        for step in plan:
            step_time = step.get("estimated_time", 1.0)
            if step.get("type") == "parallel":
                # Parallel steps: use the maximum time (tools run concurrently)
                total_time += step_time
            else:
                # Sequential steps: add all times
                total_time += step_time

        return total_time

    def get_optimization_summary(self) -> dict:
        """Get summary of optimization performance"""
        return {
            "total_optimizations": self.performance_metrics["optimizations_applied"],
            "cache_hit_rate": self.cache.get_hit_rate(),
            "parallel_executions": self.performance_metrics["parallel_executions"],
            "total_time_saved": self.performance_metrics["total_time_saved"],
            "average_time_saved_per_optimization": (
                self.performance_metrics["total_time_saved"] /
                max(self.performance_metrics["optimizations_applied"], 1)
            ),
            "cache_stats": self.cache.get_stats(),
            "recent_optimizations": self.optimization_history[-10:] if self.optimization_history else []
        }

    def clear_cache(self):
        """Clear all cached optimization results"""
        self.cache.clear()

    def reset_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            "optimizations_applied": 0,
            "cache_hits": 0,
            "parallel_executions": 0,
            "total_time_saved": 0.0
        }
        self.optimization_history.clear()
