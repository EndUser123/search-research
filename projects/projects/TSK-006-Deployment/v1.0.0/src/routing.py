#!/usr/bin/env python3
"""
Performance-Based Agent Routing for CSF NIP

Intelligent routing system that analyzes incoming tasks, scores available agents
based on past performance, and optimizes routing decisions over time for maximum efficiency.

Features:
- Task feature extraction with NLP and pattern analysis
- Multi-dimensional agent scoring algorithms
- Performance tracking and continuous learning
- Routing optimization with A/B testing
- Real-time adaptation and feedback loops
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import statistics
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# Add CSF NIP to path for imports
sys_path = str(Path(__file__).parent.parent.parent.parent.parent)
if sys_path not in sys.path:
    sys.path.append(sys_path)

# Try to import CSF common utilities
try:
    from csf_common import setup_logging
except ImportError:
    logging.basicConfig(level=logging.INFO)
    def setup_logging(name: str) -> logging.Logger:
        return logging.getLogger(name)

# Import existing agent systems
try:
    from ..schemas.agent_schemas import BaseAgentSchema
    from .agent_performance_optimizer import AgentPerformanceOptimizer
except ImportError:
    # Fallback if modules not available
    class AgentPerformanceOptimizer:
        def __init__(self, *args, **kwargs):
            pass
    class BaseAgentSchema:
        pass

logger = setup_logging(__name__)


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class RoutingStrategy(Enum):
    """Routing strategy options."""
    PERFORMANCE_BASED = "performance_based"
    ROUND_ROBIN = "round_robin"
    CAPABILITY_MATCH = "capability_match"
    LOAD_BALANCED = "load_balanced"
    HYBRID = "hybrid"


class AgentStatus(Enum):
    """Agent availability status."""
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"


@dataclass
class TaskFeatures:
    """Extracted features from a task description."""
    task_id: str
    description: str
    task_type: str
    complexity: TaskComplexity
    required_capabilities: list[str]
    estimated_duration: float
    priority_level: int
    domain_keywords: list[str]
    technical_keywords: list[str]
    semantic_embedding: list[float] = field(default_factory=list)
    pattern_matches: dict[str, float] = field(default_factory=dict)
    context_features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "task_type": self.task_type,
            "complexity": self.complexity.value,
            "required_capabilities": self.required_capabilities,
            "estimated_duration": self.estimated_duration,
            "priority_level": self.priority_level,
            "domain_keywords": self.domain_keywords,
            "technical_keywords": self.technical_keywords,
            "semantic_embedding": self.semantic_embedding,
            "pattern_matches": self.pattern_matches,
            "context_features": self.context_features
        }


@dataclass
class AgentProfile:
    """Agent profile with capabilities and performance data."""
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: list[str]
    status: AgentStatus
    current_load: int
    max_capacity: int
    performance_metrics: dict[str, float] = field(default_factory=dict)
    specialization_areas: list[str] = field(default_factory=list)
    historical_performance: list[dict[str, Any]] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    cost_per_task: float = 0.0
    availability_score: float = 1.0

    @property
    def load_percentage(self) -> float:
        """Calculate current load as percentage."""
        return (self.current_load / self.max_capacity) * 100 if self.max_capacity > 0 else 0

    @property
    def is_available(self) -> bool:
        """Check if agent is available for new tasks."""
        return self.status == AgentStatus.ACTIVE and self.current_load < self.max_capacity


@dataclass
class RoutingScore:
    """Routing score for an agent-task pair."""
    agent_id: str
    agent_name: str
    score: float
    confidence: float
    reasoning: list[str]
    breakdown: dict[str, float] = field(default_factory=dict)
    risk_factors: list[str] = field(default_factory=list)
    estimated_success_probability: float = 0.0
    estimated_completion_time: float = 0.0
    cost_estimate: float = 0.0


@dataclass
class RoutingDecision:
    """Complete routing decision with metadata."""
    task_id: str
    selected_agent: str
    routing_strategy: RoutingStrategy
    decision_time: float
    all_scores: list[RoutingScore]
    confidence: float
    reasoning: str
    ab_test_group: str | None = None
    expected_metrics: dict[str, float] = field(default_factory=dict)
    fallback_agents: list[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """Performance metrics for routing decisions."""
    decision_id: str
    task_id: str
    agent_id: str
    routing_score: float
    actual_execution_time: float
    actual_success: bool
    actual_quality_score: float
    user_satisfaction: float
    cost_efficiency: float
    timestamp: float

    def calculate_roi(self) -> float:
        """Calculate return on investment for this decision."""
        if self.cost_efficiency <= 0:
            return 0.0
        return (self.actual_quality_score * self.user_satisfaction) / self.cost_efficiency


class TaskFeatureExtractor:
    """Extracts features from task descriptions for routing analysis."""

    def __init__(self):
        """Initialize the feature extractor with patterns and keywords."""
        # Domain-specific keyword patterns
        self.domain_patterns = {
            "security": [
                "security", "vulnerability", "authentication", "authorization",
                "encryption", "penetration", "owasp", "audit", "compliance"
            ],
            "performance": [
                "performance", "optimization", "speed", "latency", "throughput",
                "benchmark", "profiling", "scalability", "efficiency"
            ],
            "documentation": [
                "documentation", "docs", "readme", "guide", "manual", "tutorial",
                "api docs", "user guide", "technical writing"
            ],
            "architecture": [
                "architecture", "design", "system", "structure", "pattern",
                "scalability", "microservices", "design patterns"
            ],
            "testing": [
                "testing", "test", "unit test", "integration", "e2e", "coverage",
                "pytest", "jest", "quality assurance", "qa"
            ],
            "git": [
                "git", "commit", "branch", "merge", "repository", "version control",
                "pull request", "code review", "gitflow"
            ],
            "standards": [
                "standards", "compliance", "coding standards", "best practices",
                "guidelines", "code quality", "linting", "formatting"
            ]
        }

        # Technical complexity indicators
        self.technical_indicators = {
            TaskComplexity.SIMPLE: [
                "basic", "simple", "straightforward", "quick", "easy",
                "minor", "small", "basic implementation"
            ],
            TaskComplexity.MODERATE: [
                "moderate", "medium", "standard", "typical", "regular",
                "implementation", "development", "integration"
            ],
            TaskComplexity.COMPLEX: [
                "complex", "advanced", "sophisticated", "intricate",
                "challenging", "difficult", "multi-step", "comprehensive"
            ],
            TaskComplexity.EXPERT: [
                "expert", "architectural", "mission critical", "enterprise",
                "large scale", "distributed", "high availability", "critical"
            ]
        }

        # Task type patterns
        self.task_type_patterns = {
            "analysis": [
                "analyze", "analysis", "review", "audit", "examine",
                "investigate", "evaluate", "assess"
            ],
            "implementation": [
                "implement", "build", "create", "develop", "code",
                "program", "write", "construct"
            ],
            "optimization": [
                "optimize", "improve", "enhance", "refactor", "tune",
                "performance", "efficiency", "speed up"
            ],
            "documentation": [
                "document", "write", "create docs", "generate", "manual",
                "guide", "tutorial", "readme"
            ],
            "testing": [
                "test", "testing", "qa", "validate", "verify", "check",
                "coverage", "unit test", "integration test"
            ],
            "maintenance": [
                "maintain", "update", "fix", "repair", "debug", "troubleshoot",
                "resolve", "patch"
            ]
        }

    def extract_features(self, task_description: str, task_metadata: dict | None = None) -> TaskFeatures:
        """
        Extract comprehensive features from a task description.

        Args:
            task_description: The task description text
            task_metadata: Optional additional metadata about the task

        Returns:
            TaskFeatures object with extracted features
        """
        task_id = task_metadata.get("task_id") if task_metadata else str(uuid.uuid4())

        # Normalize text
        normalized_text = task_description.lower()

        # Determine task type
        task_type = self._determine_task_type(normalized_text)

        # Determine complexity
        complexity = self._determine_complexity(normalized_text)

        # Extract required capabilities
        required_capabilities = self._extract_capabilities(normalized_text)

        # Estimate duration based on complexity and indicators
        estimated_duration = self._estimate_duration(normalized_text, complexity)

        # Determine priority level
        priority_level = task_metadata.get("priority", 3) if task_metadata else self._determine_priority(normalized_text)

        # Extract keywords
        domain_keywords = self._extract_domain_keywords(normalized_text)
        technical_keywords = self._extract_technical_keywords(normalized_text)

        # Generate semantic embedding (simplified)
        semantic_embedding = self._generate_semantic_embedding(normalized_text)

        # Find pattern matches
        pattern_matches = self._find_pattern_matches(normalized_text)

        # Extract context features
        context_features = self._extract_context_features(task_description, task_metadata or {})

        return TaskFeatures(
            task_id=task_id,
            description=task_description,
            task_type=task_type,
            complexity=complexity,
            required_capabilities=required_capabilities,
            estimated_duration=estimated_duration,
            priority_level=priority_level,
            domain_keywords=domain_keywords,
            technical_keywords=technical_keywords,
            semantic_embedding=semantic_embedding,
            pattern_matches=pattern_matches,
            context_features=context_features
        )

    def _determine_task_type(self, text: str) -> str:
        """Determine the primary task type from text."""
        type_scores = {}

        for task_type, keywords in self.task_type_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                type_scores[task_type] = score

        if not type_scores:
            return "general"

        return max(type_scores.items(), key=lambda x: x[1])[0]

    def _determine_complexity(self, text: str) -> TaskComplexity:
        """Determine task complexity from text indicators."""
        complexity_scores = {complexity: 0 for complexity in TaskComplexity}

        for complexity, indicators in self.technical_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            complexity_scores[complexity] = score

        # Additional complexity factors
        if any(word in text for word in ["enterprise", "distributed", "microservices"]):
            complexity_scores[TaskComplexity.EXPERT] += 2
        elif any(word in text for word in ["multiple", "several", "various"]):
            complexity_scores[TaskComplexity.COMPLEX] += 1
        elif "quick" in text or "simple" in text:
            complexity_scores[TaskComplexity.SIMPLE] += 1

        # Return complexity with highest score
        max_complexity = max(complexity_scores.items(), key=lambda x: x[1])
        if max_complexity[1] == 0:
            return TaskComplexity.MODERATE  # Default complexity

        return max_complexity[0]

    def _extract_capabilities(self, text: str) -> list[str]:
        """Extract required capabilities from text."""
        capabilities = []

        # Map domain keywords to capabilities
        domain_capability_map = {
            "security": ["security_analysis", "vulnerability_scanning", "compliance_checking"],
            "performance": ["performance_optimization", "profiling", "benchmarking"],
            "documentation": ["documentation_generation", "technical_writing", "api_docs"],
            "architecture": ["system_design", "architecture_review", "pattern_analysis"],
            "testing": ["test_automation", "quality_assurance", "coverage_analysis"],
            "git": ["version_control", "code_review", "repository_management"],
            "standards": ["standards_compliance", "code_quality", "best_practices"]
        }

        for domain, domain_keywords in self.domain_patterns.items():
            if any(keyword in text for keyword in domain_keywords):
                if domain in domain_capability_map:
                    capabilities.extend(domain_capability_map[domain])

        # Add general capabilities
        capabilities.extend(["analysis", "problem_solving"])

        return list(set(capabilities))  # Remove duplicates

    def _estimate_duration(self, text: str, complexity: TaskComplexity) -> float:
        """Estimate task duration in minutes."""
        base_durations = {
            TaskComplexity.SIMPLE: 15,      # 15 minutes
            TaskComplexity.MODERATE: 60,    # 1 hour
            TaskComplexity.COMPLEX: 180,    # 3 hours
            TaskComplexity.EXPERT: 480      # 8 hours
        }

        base_duration = base_durations.get(complexity, 60)

        # Adjust based on specific indicators
        if any(word in text for word in ["quick", "fast", "minor"]):
            base_duration *= 0.5
        elif any(word in text for word in ["comprehensive", "thorough", "detailed"]):
            base_duration *= 1.5
        elif any(word in text for word in ["enterprise", "large scale", "distributed"]):
            base_duration *= 2.0

        return base_duration

    def _determine_priority(self, text: str) -> int:
        """Determine priority level (1-5, 5 being highest)."""
        high_priority_words = ["urgent", "critical", "immediate", "asap", "emergency"]
        medium_priority_words = ["important", "priority", "soon", "promptly"]

        if any(word in text for word in high_priority_words):
            return 5
        elif any(word in text for word in medium_priority_words):
            return 4
        else:
            return 3  # Default priority

    def _extract_domain_keywords(self, text: str) -> list[str]:
        """Extract domain-specific keywords."""
        keywords = []

        for domain, domain_keywords in self.domain_patterns.items():
            for keyword in domain_keywords:
                if keyword in text:
                    keywords.append(keyword)

        return keywords

    def _extract_technical_keywords(self, text: str) -> list[str]:
        """Extract technical keywords and technologies."""
        # Common technical keywords
        tech_patterns = [
            r'\b(python|javascript|typescript|java|go|rust|c\+\+|c#)\b',
            r'\b(react|vue|angular|django|flask|fastapi|express)\b',
            r'\b(docker|kubernetes|aws|azure|gcp|terraform)\b',
            r'\b(redis|postgresql|mysql|mongodb|elasticsearch)\b',
            r'\b(git|github|gitlab|bitbucket)\b',
            r'\b(ubuntu|linux|windows|macos)\b',
            r'\b(api|rest|graphql|grpc|websocket)\b',
            r'\b(microservices|monolith|serverless|saas)\b'
        ]

        keywords = []
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)

        return list(set(keywords))

    def _generate_semantic_embedding(self, text: str) -> list[float]:
        """Generate a simplified semantic embedding (in real implementation, use proper NLP)."""
        # Simplified embedding based on keyword presence
        embedding_dim = 50
        embedding = [0.0] * embedding_dim

        # Hash-based embedding (simplified approach)
        words = text.split()
        for i, word in enumerate(words[:embedding_dim]):
            # Simple hash function
            hash_val = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            embedding[i % embedding_dim] = (hash_val % 100) / 100.0

        return embedding

    def _find_pattern_matches(self, text: str) -> dict[str, float]:
        """Find and score pattern matches."""
        pattern_matches = {}

        # Check for common patterns
        patterns = {
            "question_format": len(re.findall(r'\?', text)),
            "imperative_commands": len(re.findall(r'\b(implement|create|build|write|develop|add|fix)\b', text)),
            "technical_terms": len(re.findall(r'\b(api|database|server|client|system|application)\b', text)),
            "urgency_indicators": len(re.findall(r'\b(urgent|critical|immediate|asap)\b', text)),
        }

        # Normalize scores
        total_words = len(text.split())
        if total_words > 0:
            for pattern, count in patterns.items():
                pattern_matches[pattern] = count / total_words

        return pattern_matches

    def _extract_context_features(self, description: str, metadata: dict) -> dict[str, Any]:
        """Extract contextual features from description and metadata."""
        features = {}

        # Description features
        features["description_length"] = len(description)
        features["description_word_count"] = len(description.split())
        features["has_code_blocks"] = "```" in description or "`" in description
        features["has_urls"] = bool(re.findall(r'https?://', description))
        features["has_file_paths"] = bool(re.findall(r'[/\\][a-zA-Z0-9_\-./\\]+', description))

        # Metadata features
        features.update({
            "provided_priority": metadata.get("priority"),
            "estimated_effort": metadata.get("effort"),
            "required_tools": metadata.get("tools", []),
            "dependencies": metadata.get("dependencies", []),
            "deadline": metadata.get("deadline")
        })

        return features


class AgentScoringEngine:
    """Scores agents based on their suitability for specific tasks."""

    def __init__(self, performance_optimizer: AgentPerformanceOptimizer | None = None):
        """Initialize the scoring engine."""
        self.performance_optimizer = performance_optimizer
        self.scoring_weights = {
            "capability_match": 0.30,
            "performance_history": 0.25,
            "current_load": 0.15,
            "specialization": 0.15,
            "availability": 0.10,
            "cost_efficiency": 0.05
        }

        # Performance baselines for different task types
        self.performance_baselines = {
            "analysis": {"expected_time": 30, "expected_quality": 0.85},
            "implementation": {"expected_time": 120, "expected_quality": 0.90},
            "optimization": {"expected_time": 90, "expected_quality": 0.88},
            "documentation": {"expected_time": 60, "expected_quality": 0.92},
            "testing": {"expected_time": 45, "expected_quality": 0.87},
            "maintenance": {"expected_time": 75, "expected_quality": 0.83}
        }

    def score_agent(self, agent: AgentProfile, task: TaskFeatures) -> RoutingScore:
        """
        Calculate a comprehensive score for an agent-task pair.

        Args:
            agent: The agent profile to score
            task: The task features to score against

        Returns:
            RoutingScore with detailed scoring breakdown
        """
        breakdown = {}
        reasoning = []
        risk_factors = []

        # 1. Capability matching score
        capability_score, capability_reasoning = self._score_capability_match(agent, task)
        breakdown["capability_match"] = capability_score
        reasoning.extend(capability_reasoning)

        # 2. Historical performance score
        performance_score, performance_reasoning = self._score_performance_history(agent, task)
        breakdown["performance_history"] = performance_score
        reasoning.extend(performance_reasoning)

        # 3. Current load score
        load_score, load_reasoning = self._score_current_load(agent)
        breakdown["current_load"] = load_score
        reasoning.extend(load_reasoning)
        if agent.load_percentage > 80:
            risk_factors.append("High current load may impact performance")

        # 4. Specialization score
        specialization_score, specialization_reasoning = self._score_specialization(agent, task)
        breakdown["specialization"] = specialization_score
        reasoning.extend(specialization_reasoning)

        # 5. Availability score
        availability_score, availability_reasoning = self._score_availability(agent)
        breakdown["availability"] = availability_score
        reasoning.extend(availability_reasoning)

        # 6. Cost efficiency score
        cost_score, cost_reasoning = self._score_cost_efficiency(agent, task)
        breakdown["cost_efficiency"] = cost_score
        reasoning.extend(cost_reasoning)

        # Calculate weighted total score
        total_score = sum(
            score * self.scoring_weights[category]
            for category, score in breakdown.items()
        )

        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(agent, task, breakdown)

        # Estimate success probability
        success_probability = self._estimate_success_probability(agent, task, total_score)

        # Estimate completion time
        completion_time = self._estimate_completion_time(agent, task)

        # Calculate cost estimate
        cost_estimate = agent.cost_per_task * task.estimated_duration / 60

        return RoutingScore(
            agent_id=agent.agent_id,
            agent_name=agent.agent_name,
            score=total_score,
            confidence=confidence,
            reasoning=reasoning,
            breakdown=breakdown,
            risk_factors=risk_factors,
            estimated_success_probability=success_probability,
            estimated_completion_time=completion_time,
            cost_estimate=cost_estimate
        )

    def _score_capability_match(self, agent: AgentProfile, task: TaskFeatures) -> tuple[float, list[str]]:
        """Score how well agent capabilities match task requirements."""
        agent_capabilities = set(agent.capabilities)
        required_capabilities = set(task.required_capabilities)

        # Calculate capability coverage
        if not required_capabilities:
            return 1.0, ["No specific capabilities required"]

        covered_capabilities = agent_capabilities.intersection(required_capabilities)
        coverage_ratio = len(covered_capabilities) / len(required_capabilities)

        # Bonus for additional relevant capabilities
        relevant_bonus = 0.0
        reasoning = []

        # Check for domain-specific capabilities
        for domain in task.domain_keywords:
            domain_capabilities = [f"{domain}_analysis", f"{domain}_expertise"]
            domain_match = any(cap in agent_capabilities for cap in domain_capabilities)
            if domain_match:
                relevant_bonus += 0.1
                reasoning.append(f"Has relevant {domain} capabilities")

        base_score = coverage_ratio
        final_score = min(1.0, base_score + relevant_bonus)

        if coverage_ratio == 1.0:
            reasoning.append("Perfect capability match")
        elif coverage_ratio >= 0.8:
            reasoning.append("Strong capability match")
        elif coverage_ratio >= 0.6:
            reasoning.append("Moderate capability match")
        else:
            reasoning.append(f"Limited capability match ({coverage_ratio:.1%} coverage)")

        return final_score, reasoning

    def _score_performance_history(self, agent: AgentProfile, task: TaskFeatures) -> tuple[float, list[str]]:
        """Score based on agent's historical performance."""
        if not agent.historical_performance:
            return 0.5, ["No performance history available"]

        # Filter relevant performance data
        relevant_performance = [
            perf for perf in agent.historical_performance
            if self._is_performance_relevant(perf, task)
        ]

        if not relevant_performance:
            # Use overall performance metrics
            if agent.performance_metrics:
                overall_score = agent.performance_metrics.get("success_rate", 0.5)
                return overall_score, [f"Based on overall success rate: {overall_score:.1%}"]
            else:
                return 0.5, ["Limited performance data"]

        # Calculate performance score from relevant history
        success_rates = [perf.get("success_rate", 0.5) for perf in relevant_performance]
        quality_scores = [perf.get("quality_score", 0.5) for perf in relevant_performance]

        avg_success_rate = statistics.mean(success_rates)
        avg_quality_score = statistics.mean(quality_scores)

        # Weight recent performance more heavily
        weighted_scores = []
        current_time = time.time()
        for perf in relevant_performance:
            time_weight = self._calculate_time_weight(perf.get("timestamp", current_time), current_time)
            weighted_score = (perf.get("success_rate", 0.5) + perf.get("quality_score", 0.5)) / 2 * time_weight
            weighted_scores.append(weighted_score)

        if weighted_scores:
            final_score = statistics.mean(weighted_scores)
        else:
            final_score = (avg_success_rate + avg_quality_score) / 2

        reasoning = [
            f"Based on {len(relevant_performance)} relevant tasks",
            f"Average success rate: {avg_success_rate:.1%}",
            f"Average quality score: {avg_quality_score:.1%}"
        ]

        return final_score, reasoning

    def _score_current_load(self, agent: AgentProfile) -> tuple[float, list[str]]:
        """Score based on agent's current workload."""
        load_percentage = agent.load_percentage

        # Inverse scoring - lower load is better
        if load_percentage <= 20:
            score = 1.0
            reasoning = ["Very low current load"]
        elif load_percentage <= 40:
            score = 0.9
            reasoning = ["Low current load"]
        elif load_percentage <= 60:
            score = 0.7
            reasoning = ["Moderate current load"]
        elif load_percentage <= 80:
            score = 0.5
            reasoning = ["High current load"]
        else:
            score = 0.2
            reasoning = ["Very high current load"]

        return score, reasoning

    def _score_specialization(self, agent: AgentProfile, task: TaskFeatures) -> tuple[float, list[str]]:
        """Score based on agent's specialization areas."""
        if not agent.specialization_areas:
            return 0.5, ["No specific specializations"]

        # Check for matching specializations
        task_domains = set(task.domain_keywords)
        agent_specializations = set(agent.specialization_areas)

        matches = task_domains.intersection(agent_specializations)

        if not matches:
            return 0.3, ["No matching specializations"]

        # Score based on number of matches and relevance
        match_ratio = len(matches) / max(len(task_domains), 1)
        base_score = min(1.0, match_ratio * 1.5)  # Boost for specialization

        # Bonus for exact domain matches
        for domain in ["security", "performance", "architecture", "documentation"]:
            if domain in agent_specializations and domain in task_domains:
                base_score += 0.1

        reasoning = [f"Specialization matches: {', '.join(matches)}"]

        if base_score >= 0.8:
            reasoning.append("Strong specialization match")
        elif base_score >= 0.6:
            reasoning.append("Good specialization match")

        return min(1.0, base_score), reasoning

    def _score_availability(self, agent: AgentProfile) -> tuple[float, list[str]]:
        """Score based on agent availability status."""
        if agent.status == AgentStatus.ACTIVE:
            score = 1.0
            reasoning = ["Agent is active and available"]
        elif agent.status == AgentStatus.DEGRADED:
            score = 0.6
            reasoning = ["Agent is in degraded mode"]
        elif agent.status == AgentStatus.BUSY:
            score = 0.4
            reasoning = ["Agent is currently busy"]
        elif agent.status == AgentStatus.MAINTENANCE:
            score = 0.2
            reasoning = ["Agent is under maintenance"]
        else:  # OFFLINE
            score = 0.0
            reasoning = ["Agent is offline"]

        # Apply availability score modifier
        final_score = score * agent.availability_score

        return final_score, reasoning

    def _score_cost_efficiency(self, agent: AgentProfile, task: TaskFeatures) -> tuple[float, list[str]]:
        """Score based on cost efficiency."""
        if agent.cost_per_task <= 0:
            return 0.5, ["No cost information available"]

        # Calculate cost per minute
        cost_per_minute = agent.cost_per_task / 60  # Assuming per-hour rate
        total_estimated_cost = cost_per_minute * task.estimated_duration

        # Score based on cost (lower is better, but we want higher scores for efficiency)
        # This is a simplified cost scoring - in practice, you'd want market comparisons
        if total_estimated_cost <= 10:
            score = 1.0
            reasoning = [f"Very cost effective: ${total_estimated_cost:.2f} estimated"]
        elif total_estimated_cost <= 25:
            score = 0.8
            reasoning = [f"Cost effective: ${total_estimated_cost:.2f} estimated"]
        elif total_estimated_cost <= 50:
            score = 0.6
            reasoning = [f"Moderate cost: ${total_estimated_cost:.2f} estimated"]
        else:
            score = 0.4
            reasoning = [f"Higher cost: ${total_estimated_cost:.2f} estimated"]

        return score, reasoning

    def _is_performance_relevant(self, performance: dict, task: TaskFeatures) -> bool:
        """Check if performance record is relevant to current task."""
        # Check task type relevance
        if performance.get("task_type") == task.task_type:
            return True

        # Check capability overlap
        perf_capabilities = set(performance.get("capabilities_used", []))
        task_capabilities = set(task.required_capabilities)

        if perf_capabilities.intersection(task_capabilities):
            return True

        # Check time relevance (recent performance)
        perf_time = performance.get("timestamp", 0)
        current_time = time.time()
        days_diff = (current_time - perf_time) / (24 * 60 * 60)

        if days_diff <= 30:  # Recent performance
            return True

        return False

    def _calculate_time_weight(self, timestamp: float, current_time: float) -> float:
        """Calculate time-based weight for performance records."""
        age_days = (current_time - timestamp) / (24 * 60 * 60)

        # Recent performance gets higher weight
        if age_days <= 7:
            return 1.0
        elif age_days <= 30:
            return 0.8
        elif age_days <= 90:
            return 0.6
        else:
            return 0.4

    def _calculate_confidence(self, agent: AgentProfile, task: TaskFeatures, breakdown: dict[str, float]) -> float:
        """Calculate confidence in the scoring decision."""
        confidence_factors = []

        # Data availability confidence
        if len(agent.historical_performance) > 10:
            confidence_factors.append(0.9)
        elif len(agent.historical_performance) > 3:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)

        # Score variance confidence (lower variance = higher confidence)
        if breakdown:
            score_variance = statistics.stdev(breakdown.values()) if len(breakdown) > 1 else 0
            variance_confidence = max(0.3, 1.0 - score_variance)
            confidence_factors.append(variance_confidence)

        # Capability match confidence
        if set(agent.capabilities).issuperset(set(task.required_capabilities)):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)

        return statistics.mean(confidence_factors)

    def _estimate_success_probability(self, agent: AgentProfile, task: TaskFeatures, score: float) -> float:
        """Estimate probability of successful task completion."""
        base_probability = score

        # Adjust based on task complexity
        complexity_adjustments = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MODERATE: 0.0,
            TaskComplexity.COMPLEX: -0.1,
            TaskComplexity.EXPERT: -0.2
        }

        base_probability += complexity_adjustments.get(task.complexity, 0.0)

        # Adjust based on agent's historical success rate
        if agent.performance_metrics:
            historical_success = agent.performance_metrics.get("success_rate", 0.5)
            base_probability = (base_probability + historical_success) / 2

        return max(0.0, min(1.0, base_probability))

    def _estimate_completion_time(self, agent: AgentProfile, task: TaskFeatures) -> float:
        """Estimate task completion time for this agent."""
        base_time = task.estimated_duration

        # Adjust based on agent's performance speed
        if agent.performance_metrics:
            speed_factor = agent.performance_metrics.get("speed_factor", 1.0)
            base_time /= speed_factor

        # Adjust based on current load
        if agent.load_percentage > 50:
            load_factor = 1 + (agent.load_percentage - 50) / 100
            base_time *= load_factor

        return base_time


class PerformanceTracker:
    """Tracks and analyzes routing performance over time."""

    def __init__(self, db_path: str = "data/routing_performance.db"):
        """Initialize the performance tracker."""
        self.db_path = db_path
        self._initialize_database()

        # Performance metrics cache
        self.metrics_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def _initialize_database(self):
        """Initialize the performance tracking database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT UNIQUE NOT NULL,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    task_type TEXT,
                    task_complexity TEXT,
                    routing_score REAL,
                    confidence REAL,
                    routing_strategy TEXT,
                    decision_time REAL,
                    timestamp REAL,
                    expected_metrics TEXT,
                    fallback_agents TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL,
                    actual_execution_time REAL,
                    actual_success BOOLEAN,
                    actual_quality_score REAL,
                    user_satisfaction REAL,
                    cost_efficiency REAL,
                    timestamp REAL,
                    feedback_text TEXT,
                    FOREIGN KEY (decision_id) REFERENCES routing_decisions (decision_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    total_tasks INTEGER,
                    successful_tasks INTEGER,
                    average_execution_time REAL,
                    average_quality_score REAL,
                    total_cost REAL,
                    timestamp REAL,
                    UNIQUE(agent_id, date)
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_routing_decisions_task_id ON routing_decisions(task_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_routing_decisions_agent_id ON routing_decisions(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_outcomes_decision_id ON performance_outcomes(decision_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_id ON agent_performance_trends(agent_id)")

    def record_routing_decision(self, decision: RoutingDecision) -> bool:
        """Record a routing decision for tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO routing_decisions
                    (decision_id, task_id, agent_id, task_type, task_complexity,
                     routing_score, confidence, routing_strategy, decision_time,
                     timestamp, expected_metrics, fallback_agents)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision.task_id,  # Use task_id as decision_id for uniqueness
                    decision.task_id,
                    decision.selected_agent,
                    "",  # task_type - would be populated from task features
                    "",  # task_complexity - would be populated from task features
                    decision.confidence,
                    decision.confidence,
                    decision.routing_strategy.value,
                    decision.decision_time,
                    time.time(),
                    json.dumps(decision.expected_metrics),
                    json.dumps(decision.fallback_agents)
                ))

            logger.debug(f"Recorded routing decision: {decision.task_id} -> {decision.selected_agent}")
            return True

        except Exception as e:
            logger.error(f"Failed to record routing decision: {e}")
            return False

    def record_performance_outcome(self, decision_id: str, outcome: PerformanceMetrics) -> bool:
        """Record the actual performance outcome of a routing decision."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_outcomes
                    (decision_id, actual_execution_time, actual_success, actual_quality_score,
                     user_satisfaction, cost_efficiency, timestamp, feedback_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision_id,
                    outcome.actual_execution_time,
                    outcome.actual_success,
                    outcome.actual_quality_score,
                    outcome.user_satisfaction,
                    outcome.cost_efficiency,
                    outcome.timestamp,
                    ""  # feedback_text - optional
                ))

            # Update agent performance trends
            self._update_agent_performance_trends(outcome.agent_id, outcome)

            # Invalidate cache
            self.metrics_cache.clear()

            logger.debug(f"Recorded performance outcome for decision: {decision_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record performance outcome: {e}")
            return False

    def _update_agent_performance_trends(self, agent_id: str, outcome: PerformanceMetrics):
        """Update daily performance trends for an agent."""
        date = datetime.fromtimestamp(outcome.timestamp).date()

        with sqlite3.connect(self.db_path) as conn:
            # Check if record exists for today
            cursor = conn.execute("""
                SELECT total_tasks, successful_tasks, average_execution_time,
                       average_quality_score, total_cost
                FROM agent_performance_trends
                WHERE agent_id = ? AND date = ?
            """, (agent_id, date))

            existing = cursor.fetchone()

            if existing:
                # Update existing record
                total_tasks, successful_tasks, avg_exec_time, avg_quality, total_cost = existing
                new_total_tasks = total_tasks + 1
                new_successful_tasks = successful_tasks + (1 if outcome.actual_success else 0)
                new_avg_exec_time = (avg_exec_time * total_tasks + outcome.actual_execution_time) / new_total_tasks
                new_avg_quality = (avg_quality * total_tasks + outcome.actual_quality_score) / new_total_tasks
                new_total_cost = total_cost + (outcome.actual_execution_time * outcome.cost_efficiency)

                conn.execute("""
                    UPDATE agent_performance_trends
                    SET total_tasks = ?, successful_tasks = ?, average_execution_time = ?,
                        average_quality_score = ?, total_cost = ?, timestamp = ?
                    WHERE agent_id = ? AND date = ?
                """, (new_total_tasks, new_successful_tasks, new_avg_exec_time,
                      new_avg_quality, new_total_cost, time.time(), agent_id, date))
            else:
                # Insert new record
                conn.execute("""
                    INSERT INTO agent_performance_trends
                    (agent_id, date, total_tasks, successful_tasks, average_execution_time,
                     average_quality_score, total_cost, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (agent_id, date, 1, 1 if outcome.actual_success else 0,
                      outcome.actual_execution_time, outcome.actual_quality_score,
                      outcome.actual_execution_time * outcome.cost_efficiency, time.time()))

    def get_agent_performance_summary(self, agent_id: str, days: int = 30) -> dict[str, Any]:
        """Get performance summary for an agent."""
        cache_key = f"agent_summary_{agent_id}_{days}"

        # Check cache
        if cache_key in self.metrics_cache:
            cached_time, cached_data = self.metrics_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        cutoff_date = datetime.now().date() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Get daily performance data
            cursor = conn.execute("""
                SELECT date, total_tasks, successful_tasks, average_execution_time,
                       average_quality_score, total_cost
                FROM agent_performance_trends
                WHERE agent_id = ? AND date >= ?
                ORDER BY date DESC
            """, (agent_id, cutoff_date))

            daily_data = cursor.fetchall()

            if not daily_data:
                return {"error": "No performance data available"}

            # Calculate aggregates
            total_tasks = sum(row[1] for row in daily_data)
            total_successful = sum(row[2] for row in daily_data)
            success_rate = total_successful / total_tasks if total_tasks > 0 else 0

            avg_execution_times = [row[3] for row in daily_data if row[3] > 0]
            avg_execution_time = statistics.mean(avg_execution_times) if avg_execution_times else 0

            avg_quality_scores = [row[4] for row in daily_data if row[4] > 0]
            avg_quality_score = statistics.mean(avg_quality_scores) if avg_quality_scores else 0

            total_cost = sum(row[5] for row in daily_data)
            cost_per_task = total_cost / total_tasks if total_tasks > 0 else 0

            # Calculate trend
            if len(daily_data) >= 7:
                recent_success_rates = [row[2] / row[1] for row in daily_data[:7] if row[1] > 0]
                trend = "improving" if len(recent_success_rates) > 0 and recent_success_rates[0] > recent_success_rates[-1] else "stable"
            else:
                trend = "insufficient_data"

            summary = {
                "agent_id": agent_id,
                "period_days": days,
                "total_tasks": total_tasks,
                "successful_tasks": total_successful,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "average_quality_score": avg_quality_score,
                "total_cost": total_cost,
                "cost_per_task": cost_per_task,
                "trend": trend,
                "data_points": len(daily_data)
            }

            # Cache the result
            self.metrics_cache[cache_key] = (time.time(), summary)

            return summary

    def get_routing_performance_metrics(self, days: int = 30) -> dict[str, Any]:
        """Get overall routing performance metrics."""
        cache_key = f"routing_metrics_{days}"

        # Check cache
        if cache_key in self.metrics_cache:
            cached_time, cached_data = self.metrics_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        with sqlite3.connect(self.db_path) as conn:
            # Get routing decisions with outcomes
            cursor = conn.execute("""
                SELECT rd.routing_score, rd.confidence, rd.routing_strategy,
                       po.actual_success, po.actual_quality_score, po.user_satisfaction,
                       po.cost_efficiency, po.actual_execution_time
                FROM routing_decisions rd
                LEFT JOIN performance_outcomes po ON rd.decision_id = po.decision_id
                WHERE rd.timestamp >= ?
            """, (cutoff_time,))

            results = cursor.fetchall()

            if not results:
                return {"error": "No routing data available"}

            # Separate decisions with and without outcomes
            decisions_with_outcomes = [row for row in results if row[3] is not None]  # actual_success not None
            total_decisions = len(results)

            if not decisions_with_outcomes:
                return {
                    "total_decisions": total_decisions,
                    "decisions_with_outcomes": 0,
                    "pending_decisions": total_decisions,
                    "error": "No completed decisions available"
                }

            # Calculate metrics
            success_count = sum(1 for row in decisions_with_outcomes if row[3])  # actual_success
            success_rate = success_count / len(decisions_with_outcomes)

            quality_scores = [row[4] for row in decisions_with_outcomes if row[4] is not None]
            avg_quality_score = statistics.mean(quality_scores) if quality_scores else 0

            satisfaction_scores = [row[5] for row in decisions_with_outcomes if row[5] is not None]
            avg_satisfaction = statistics.mean(satisfaction_scores) if satisfaction_scores else 0

            cost_efficiencies = [row[6] for row in decisions_with_outcomes if row[6] is not None]
            avg_cost_efficiency = statistics.mean(cost_efficiencies) if cost_efficiencies else 0

            execution_times = [row[7] for row in decisions_with_outcomes if row[7] is not None]
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0

            routing_scores = [row[0] for row in results if row[0] is not None]
            avg_routing_score = statistics.mean(routing_scores) if routing_scores else 0

            confidences = [row[1] for row in results if row[1] is not None]
            avg_confidence = statistics.mean(confidences) if confidences else 0

            # Strategy breakdown
            strategies = defaultdict(int)
            for row in results:
                strategy = row[2] or "unknown"
                strategies[strategy] += 1

            metrics = {
                "period_days": days,
                "total_decisions": total_decisions,
                "decisions_with_outcomes": len(decisions_with_outcomes),
                "pending_decisions": total_decisions - len(decisions_with_outcomes),
                "success_rate": success_rate,
                "average_quality_score": avg_quality_score,
                "average_user_satisfaction": avg_satisfaction,
                "average_cost_efficiency": avg_cost_efficiency,
                "average_execution_time": avg_execution_time,
                "average_routing_score": avg_routing_score,
                "average_confidence": avg_confidence,
                "strategy_breakdown": dict(strategies)
            }

            # Cache the result
            self.metrics_cache[cache_key] = (time.time(), metrics)

            return metrics


class ABRoutingTester:
    """A/B testing framework for routing strategies."""

    def __init__(self, performance_tracker: PerformanceTracker):
        """Initialize the A/B testing framework."""
        self.performance_tracker = performance_tracker
        self.test_configurations = {}
        self.active_tests = {}

    def create_ab_test(
        self,
        test_name: str,
        strategy_a: RoutingStrategy,
        strategy_b: RoutingStrategy,
        traffic_split: float = 0.5,
        min_sample_size: int = 100,
        confidence_level: float = 0.95
    ) -> bool:
        """Create a new A/B test for routing strategies."""
        try:
            test_id = str(uuid.uuid4())

            self.test_configurations[test_id] = {
                "test_name": test_name,
                "strategy_a": strategy_a,
                "strategy_b": strategy_b,
                "traffic_split": traffic_split,
                "min_sample_size": min_sample_size,
                "confidence_level": confidence_level,
                "created_at": time.time(),
                "status": "active"
            }

            self.active_tests[test_name] = test_id

            logger.info(f"Created A/B test '{test_name}': {strategy_a.value} vs {strategy_b.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            return False

    def assign_test_group(self, test_name: str, task_id: str) -> str | None:
        """Assign a task to a test group (A or B)."""
        if test_name not in self.active_tests:
            return None

        test_id = self.active_tests[test_name]
        test_config = self.test_configurations[test_id]

        if test_config["status"] != "active":
            return None

        # Use consistent hashing for assignment
        hash_value = int(hashlib.md5(f"{test_id}_{task_id}".encode()).hexdigest()[:8], 16)

        if (hash_value % 100) < (test_config["traffic_split"] * 100):
            return "A"
        else:
            return "B"

    def get_test_strategy(self, test_name: str, group: str) -> RoutingStrategy | None:
        """Get the routing strategy for a test group."""
        if test_name not in self.active_tests:
            return None

        test_id = self.active_tests[test_name]
        test_config = self.test_configurations[test_id]

        if group == "A":
            return test_config["strategy_a"]
        elif group == "B":
            return test_config["strategy_b"]
        else:
            return None

    def analyze_test_results(self, test_name: str) -> dict[str, Any]:
        """Analyze A/B test results and determine statistical significance."""
        if test_name not in self.active_tests:
            return {"error": "Test not found"}

        test_id = self.active_tests[test_name]
        test_config = self.test_configurations[test_id]

        # Get performance data for both strategies
        strategy_a_results = self._get_strategy_results(test_config["strategy_a"])
        strategy_b_results = self._get_strategy_results(test_config["strategy_b"])

        if not strategy_a_results or not strategy_b_results:
            return {"error": "Insufficient data for analysis"}

        # Calculate metrics
        a_success_rate = strategy_a_results["success_rate"]
        b_success_rate = strategy_b_results["success_rate"]
        a_sample_size = strategy_a_results["sample_size"]
        b_sample_size = strategy_b_results["sample_size"]

        # Perform statistical test (simplified chi-square test)
        p_value = self._calculate_statistical_significance(
            a_success_rate, b_success_rate, a_sample_size, b_sample_size
        )

        # Determine winner
        if p_value < (1 - test_config["confidence_level"]):
            if a_success_rate > b_success_rate:
                winner = "A"
                improvement = ((a_success_rate - b_success_rate) / b_success_rate) * 100
            else:
                winner = "B"
                improvement = ((b_success_rate - a_success_rate) / a_success_rate) * 100
            is_significant = True
        else:
            winner = "inconclusive"
            improvement = 0
            is_significant = False

        results = {
            "test_name": test_name,
            "strategy_a": test_config["strategy_a"].value,
            "strategy_b": test_config["strategy_b"].value,
            "strategy_a_metrics": strategy_a_results,
            "strategy_b_metrics": strategy_b_results,
            "winner": winner,
            "improvement_percentage": improvement,
            "p_value": p_value,
            "is_statistically_significant": is_significant,
            "confidence_level": test_config["confidence_level"],
            "min_sample_size_reached": min(a_sample_size, b_sample_size) >= test_config["min_sample_size"]
        }

        return results

    def _get_strategy_results(self, strategy: RoutingStrategy) -> dict[str, Any] | None:
        """Get performance results for a specific routing strategy."""
        # This would query the performance tracker for results by strategy
        # For now, return a placeholder
        return {
            "success_rate": 0.85,
            "sample_size": 150,
            "average_quality": 0.88,
            "average_execution_time": 120
        }

    def _calculate_statistical_significance(
        self,
        rate_a: float,
        rate_b: float,
        n_a: int,
        n_b: int
    ) -> float:
        """Calculate p-value for statistical significance testing."""
        # Simplified calculation - in practice, use proper statistical tests
        if n_a == 0 or n_b == 0:
            return 1.0

        pooled_rate = ((rate_a * n_a) + (rate_b * n_b)) / (n_a + n_b)

        if pooled_rate == 0 or pooled_rate == 1:
            return 1.0

        standard_error = ((pooled_rate * (1 - pooled_rate)) * (1/n_a + 1/n_b)) ** 0.5

        if standard_error == 0:
            return 1.0

        z_score = abs(rate_a - rate_b) / standard_error

        # Simplified p-value calculation (would use proper statistical tables)
        if z_score > 2.58:
            return 0.01
        elif z_score > 1.96:
            return 0.05
        elif z_score > 1.64:
            return 0.10
        else:
            return 0.50


class PerformanceBasedRouter:
    """Main routing engine that integrates all components."""

    def __init__(self, config: dict | None = None):
        """Initialize the performance-based router."""
        self.config = config or {}

        # Initialize components
        self.feature_extractor = TaskFeatureExtractor()
        self.performance_optimizer = AgentPerformanceOptimizer()
        self.scoring_engine = AgentScoringEngine(self.performance_optimizer)
        self.performance_tracker = PerformanceTracker(
            self.config.get("performance_db_path", "data/routing_performance.db")
        )
        self.ab_tester = ABRoutingTester(self.performance_tracker)

        # Agent registry
        self.agents: dict[str, AgentProfile] = {}

        # Routing configuration
        self.default_strategy = RoutingStrategy.PERFORMANCE_BASED
        self.fallback_enabled = True
        self.max_fallback_agents = 3

        # Performance thresholds
        self.min_confidence_threshold = 0.6
        self.min_score_threshold = 0.4

        logger.info("Performance-Based Router initialized")

    def register_agent(self, agent_profile: AgentProfile) -> bool:
        """Register an agent with the routing system."""
        try:
            self.agents[agent_profile.agent_id] = agent_profile
            logger.debug(f"Registered agent: {agent_profile.agent_name} ({agent_profile.agent_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {agent_profile.agent_id}: {e}")
            return False

    def route_task(
        self,
        task_description: str,
        task_metadata: dict | None = None,
        preferred_strategy: RoutingStrategy | None = None
    ) -> RoutingDecision:
        """
        Route a task to the most suitable agent.

        Args:
            task_description: Description of the task to be routed
            task_metadata: Additional metadata about the task
            preferred_strategy: Preferred routing strategy (optional)

        Returns:
            RoutingDecision with selected agent and reasoning
        """
        start_time = time.time()

        # Extract task features
        task_features = self.feature_extractor.extract_features(task_description, task_metadata)

        # Determine routing strategy
        routing_strategy = preferred_strategy or self._determine_routing_strategy(task_features)

        # Check for A/B tests
        ab_test_group = None
        for test_name in self.ab_tester.active_tests:
            group = self.ab_tester.assign_test_group(test_name, task_features.task_id)
            if group:
                ab_test_group = group
                test_strategy = self.ab_tester.get_test_strategy(test_name, group)
                if test_strategy:
                    routing_strategy = test_strategy
                break

        # Get available agents
        available_agents = self._get_available_agents(task_features)

        if not available_agents:
            return self._create_no_agents_decision(task_features, routing_strategy, start_time)

        # Score all available agents
        agent_scores = []
        for agent in available_agents:
            score = self.scoring_engine.score_agent(agent, task_features)
            agent_scores.append(score)

        # Sort by score (descending)
        agent_scores.sort(key=lambda x: x.score, reverse=True)

        # Select best agent
        selected_score = agent_scores[0]

        # Apply confidence threshold
        if selected_score.confidence < self.min_confidence_threshold or selected_score.score < self.min_score_threshold:
            if self.fallback_enabled and len(agent_scores) > 1:
                # Try next best agent
                selected_score = agent_scores[1]
                logger.warning(f"Primary agent below threshold, using fallback agent: {selected_score.agent_name}")

        # Prepare fallback agents
        fallback_agents = [score.agent_id for score in agent_scores[1:self.max_fallback_agents + 1]]

        # Create routing decision
        decision = RoutingDecision(
            task_id=task_features.task_id,
            selected_agent=selected_score.agent_id,
            routing_strategy=routing_strategy,
            decision_time=time.time() - start_time,
            all_scores=agent_scores,
            confidence=selected_score.confidence,
            reasoning=self._generate_reasoning(selected_score, task_features),
            ab_test_group=ab_test_group,
            expected_metrics={
                "success_probability": selected_score.estimated_success_probability,
                "estimated_duration": selected_score.estimated_completion_time,
                "estimated_cost": selected_score.cost_estimate
            },
            fallback_agents=fallback_agents
        )

        # Record the routing decision
        self.performance_tracker.record_routing_decision(decision)

        logger.info(f"Routed task {task_features.task_id} to {selected_score.agent_name} (score: {selected_score.score:.2f})")

        return decision

    def record_task_completion(
        self,
        task_id: str,
        execution_time: float,
        success: bool,
        quality_score: float = 0.0,
        user_satisfaction: float = 0.0,
        cost_efficiency: float = 1.0
    ) -> bool:
        """Record the completion of a routed task."""
        try:
            # Find the routing decision
            # In a real implementation, you'd query the database for the decision_id
            decision_id = task_id  # Simplified - using task_id as decision_id

            # Get agent ID from the decision
            selected_agent = None
            for agent_id, agent in self.agents.items():
                if agent.agent_name == selected_agent:
                    selected_agent = agent_id
                    break

            if not selected_agent:
                logger.warning(f"Could not find agent for task {task_id}")
                return False

            # Create performance metrics
            metrics = PerformanceMetrics(
                decision_id=decision_id,
                task_id=task_id,
                agent_id=selected_agent,
                routing_score=0.0,  # Would be retrieved from decision
                actual_execution_time=execution_time,
                actual_success=success,
                actual_quality_score=quality_score,
                user_satisfaction=user_satisfaction,
                cost_efficiency=cost_efficiency,
                timestamp=time.time()
            )

            # Record the outcome
            success = self.performance_tracker.record_performance_outcome(decision_id, metrics)

            if success:
                logger.debug(f"Recorded completion for task {task_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to record task completion: {e}")
            return False

    def get_routing_performance_report(self, days: int = 30) -> dict[str, Any]:
        """Generate a comprehensive routing performance report."""
        # Get overall metrics
        overall_metrics = self.performance_tracker.get_routing_performance_metrics(days)

        # Get agent-specific summaries
        agent_summaries = {}
        for agent_id in self.agents:
            summary = self.performance_tracker.get_agent_performance_summary(agent_id, days)
            if "error" not in summary:
                agent_summaries[agent_id] = summary

        # Get A/B test results
        ab_test_results = {}
        for test_name in self.ab_tester.active_tests:
            results = self.ab_tester.analyze_test_results(test_name)
            if "error" not in results:
                ab_test_results[test_name] = results

        # Generate recommendations
        recommendations = self._generate_performance_recommendations(overall_metrics, agent_summaries)

        report = {
            "report_metadata": {
                "generated_at": time.time(),
                "period_days": days,
                "total_agents": len(self.agents),
                "active_ab_tests": len(self.ab_tester.active_tests)
            },
            "overall_metrics": overall_metrics,
            "agent_performance": agent_summaries,
            "ab_test_results": ab_test_results,
            "recommendations": recommendations,
            "routing_config": {
                "default_strategy": self.default_strategy.value,
                "min_confidence_threshold": self.min_confidence_threshold,
                "min_score_threshold": self.min_score_threshold,
                "fallback_enabled": self.fallback_enabled
            }
        }

        return report

    def _determine_routing_strategy(self, task_features: TaskFeatures) -> RoutingStrategy:
        """Determine the best routing strategy for a given task."""
        # Strategy selection logic based on task characteristics
        if task_features.complexity == TaskComplexity.EXPERT:
            return RoutingStrategy.PERFORMANCE_BASED
        elif task_features.priority_level >= 4:
            return RoutingStrategy.PERFORMANCE_BASED
        elif len(task_features.required_capabilities) == 1:
            return RoutingStrategy.CAPABILITY_MATCH
        elif self._should_load_balance():
            return RoutingStrategy.LOAD_BALANCED
        else:
            return self.default_strategy

    def _get_available_agents(self, task_features: TaskFeatures) -> list[AgentProfile]:
        """Get list of agents available for this task."""
        available_agents = []

        for agent in self.agents.values():
            # Check basic availability
            if not agent.is_available:
                continue

            # Check capability match
            agent_capabilities = set(agent.capabilities)
            required_capabilities = set(task_features.required_capabilities)

            if not required_capabilities or agent_capabilities.intersection(required_capabilities):
                available_agents.append(agent)

        return available_agents

    def _create_no_agents_decision(
        self,
        task_features: TaskFeatures,
        strategy: RoutingStrategy,
        start_time: float
    ) -> RoutingDecision:
        """Create a decision when no agents are available."""
        return RoutingDecision(
            task_id=task_features.task_id,
            selected_agent="none",
            routing_strategy=strategy,
            decision_time=time.time() - start_time,
            all_scores=[],
            confidence=0.0,
            reasoning="No suitable agents available",
            expected_metrics={}
        )

    def _generate_reasoning(self, score: RoutingScore, task_features: TaskFeatures) -> str:
        """Generate human-readable reasoning for the routing decision."""
        reasoning_parts = []

        # Top contributing factors
        top_factors = sorted(score.breakdown.items(), key=lambda x: x[1], reverse=True)[:3]

        for factor, value in top_factors:
            if factor == "capability_match" and value >= 0.8:
                reasoning_parts.append("Strong capability match")
            elif factor == "performance_history" and value >= 0.8:
                reasoning_parts.append("Excellent historical performance")
            elif factor == "current_load" and value >= 0.8:
                reasoning_parts.append("Low current workload")
            elif factor == "specialization" and value >= 0.7:
                reasoning_parts.append("Relevant specialization")

        if not reasoning_parts:
            reasoning_parts.append("Best available match")

        # Add confidence level
        if score.confidence >= 0.8:
            reasoning_parts.append("High confidence routing")
        elif score.confidence >= 0.6:
            reasoning_parts.append("Moderate confidence routing")
        else:
            reasoning_parts.append("Lower confidence routing")

        return "; ".join(reasoning_parts)

    def _should_load_balance(self) -> bool:
        """Check if load balancing should be used."""
        # Check if any agents are overloaded
        overloaded_agents = [
            agent for agent in self.agents.values()
            if agent.load_percentage > 70
        ]

        return len(overloaded_agents) > len(self.agents) * 0.3

    def _generate_performance_recommendations(
        self,
        overall_metrics: dict,
        agent_summaries: dict
    ) -> list[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if overall_metrics.get("success_rate", 0) < 0.8:
            recommendations.append("Consider reviewing agent selection criteria - success rate below 80%")

        if overall_metrics.get("average_confidence", 0) < 0.7:
            recommendations.append("Improve data quality to increase routing confidence")

        # Find underperforming agents
        for agent_id, summary in agent_summaries.items():
            if summary.get("success_rate", 0) < 0.7:
                recommendations.append(f"Agent {agent_id} shows low success rate - consider retraining or replacement")

        if overall_metrics.get("average_execution_time", 0) > 300:
            recommendations.append("Consider optimizing task allocation to reduce average execution time")

        if len(recommendations) == 0:
            recommendations.append("Routing performance is within acceptable ranges")

        return recommendations


# Global router instance for easy access
router = PerformanceBasedRouter()

# Convenience functions
def register_agent(agent_profile: AgentProfile) -> bool:
    """Register an agent with the global router."""
    return router.register_agent(agent_profile)

def route_task(
    task_description: str,
    task_metadata: dict | None = None,
    strategy: RoutingStrategy | None = None
) -> RoutingDecision:
    """Route a task using the global router."""
    return router.route_task(task_description, task_metadata, strategy)

def record_task_completion(
    task_id: str,
    execution_time: float,
    success: bool,
    quality_score: float = 0.0,
    user_satisfaction: float = 0.0,
    cost_efficiency: float = 1.0
) -> bool:
    """Record task completion using the global router."""
    return router.record_task_completion(task_id, execution_time, success, quality_score, user_satisfaction, cost_efficiency)

def get_performance_report(days: int = 30) -> dict[str, Any]:
    """Get performance report from the global router."""
    return router.get_routing_performance_report(days)


if __name__ == "__main__":
    # Demo the performance-based routing system
    def demo():
        print("Performance-Based Agent Routing Demo")
        print("=" * 50)

        # Create sample agents
        agents = [
            AgentProfile(
                agent_id="agent_001",
                agent_name="Security Specialist",
                agent_type="security",
                capabilities=["security_analysis", "vulnerability_scanning", "compliance_checking", "penetration_testing"],
                status=AgentStatus.ACTIVE,
                current_load=2,
                max_capacity=10,
                performance_metrics={"success_rate": 0.92, "speed_factor": 1.1},
                specialization_areas=["security", "owasp", "compliance"],
                cost_per_task=100.0
            ),
            AgentProfile(
                agent_id="agent_002",
                agent_name="Python Developer",
                agent_type="development",
                capabilities=["python_development", "api_design", "database_integration", "testing"],
                status=AgentStatus.ACTIVE,
                current_load=5,
                max_capacity=10,
                performance_metrics={"success_rate": 0.88, "speed_factor": 1.2},
                specialization_areas=["python", "fastapi", "django"],
                cost_per_task=80.0
            ),
            AgentProfile(
                agent_id="agent_003",
                agent_name="Documentation Expert",
                agent_type="documentation",
                capabilities=["technical_writing", "api_documentation", "user_guides", "tutorial_creation"],
                status=AgentStatus.ACTIVE,
                current_load=1,
                max_capacity=8,
                performance_metrics={"success_rate": 0.95, "speed_factor": 0.9},
                specialization_areas=["documentation", "technical_writing"],
                cost_per_task=60.0
            )
        ]

        # Register agents
        for agent in agents:
            register_agent(agent)
            print(f"Registered agent: {agent.agent_name}")

        print("\nRouting sample tasks...")

        # Sample tasks
        sample_tasks = [
            {
                "description": "Implement secure authentication with JWT tokens and OWASP compliance",
                "metadata": {"priority": 4, "task_id": "task_001"}
            },
            {
                "description": "Create comprehensive API documentation for FastAPI service",
                "metadata": {"priority": 2, "task_id": "task_002"}
            },
            {
                "description": "Quick bug fix for simple validation issue",
                "metadata": {"priority": 3, "task_id": "task_003"}
            }
        ]

        # Route tasks
        for task in sample_tasks:
            decision = route_task(task["description"], task["metadata"])

            print(f"\nTask: {task['description'][:60]}...")
            print(f"  Selected Agent: {decision.selected_agent}")
            print(f"  Routing Strategy: {decision.routing_strategy.value}")
            print(f"  Confidence: {decision.confidence:.2f}")
            print(f"  Score: {decision.all_scores[0].score if decision.all_scores else 0:.2f}")
            print(f"  Reasoning: {decision.reasoning}")

            if decision.expected_metrics:
                print(f"  Expected Duration: {decision.expected_metrics.get('estimated_duration', 0):.1f} minutes")
                print(f"  Success Probability: {decision.expected_metrics.get('success_probability', 0):.1%}")

        # Simulate task completion
        print("\nRecording task completions...")

        record_task_completion("task_001", 45.0, True, 0.9, 0.85, 1.2)
        record_task_completion("task_002", 30.0, True, 0.95, 0.92, 0.8)
        record_task_completion("task_003", 15.0, True, 0.88, 0.9, 1.0)

        # Generate performance report
        print("\nGenerating performance report...")
        report = get_performance_report(days=1)

        print("Overall Metrics:")
        if "overall_metrics" in report:
            metrics = report["overall_metrics"]
            print(f"  Total Decisions: {metrics.get('total_decisions', 0)}")
            print(f"  Success Rate: {metrics.get('success_rate', 0):.1%}")
            print(f"  Average Quality: {metrics.get('average_quality_score', 0):.2f}")
            print(f"  Average Confidence: {metrics.get('average_confidence', 0):.2f}")

        print("\nDemo completed successfully!")

    demo()
