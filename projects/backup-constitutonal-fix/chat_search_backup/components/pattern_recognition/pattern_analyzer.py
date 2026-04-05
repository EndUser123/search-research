from __future__ import annotations

from collections import Counter, defaultdict
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any
import logging
import os
import re
import sys

import numpy as np

from ...domain_models.chat_models import (
from ..interfaces.chat_interfaces import IPatternRecognizer

#!/usr/bin/env python3
"""Advanced Pattern Recognition System for CHS
Sophisticated pattern detection in conversations with decision trail analysis.
"""



# Add CSF NIP paths


sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)

    ChatMessage,
    ConversationContext,
    ConversationPattern,
)


class PatternType(Enum):
    """Types of conversation patterns."""

    PROBLEM_SOLUTION = "problem_solution"
    DECISION_MAKING = "decision_making"
    WORKFLOW = "workflow"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    TROUBLESHOOTING = "troubleshooting"
    PLANNING = "planning"
    CODE_REVIEW = "code_review"
    CONTEXT_SWITCH = "context_switch"
    TECHNICAL_DISCUSSION = "technical_discussion"
    QUESTION_ANSWER = "question_answer"


@dataclass
class DecisionPoint:
    """Represents a decision point in conversation."""

    timestamp: int
    decision_type: str
    options_considered: list[str]
    chosen_option: str | None
    rationale: str | None
    participants: list[str]
    confidence: float
    outcome_tracked: bool = False


@dataclass
class WorkflowStep:
    """Represents a step in a conversation workflow."""

    step_id: str
    action: str
    timestamp: int
    duration: int | None
    tools_mentioned: list[str]
    dependencies: list[str]
    success_indicators: list[str]


class ConversationFlowAnalyzer:
    """Analyze conversation flow patterns."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.transition_patterns = defaultdict(int)
        self.context_indicators = self._load_context_indicators()

    def _load_context_indicators(self) -> dict[str, list[str]]:
        """Load indicators for different conversation contexts."""
        return {
            ConversationContext.PROJECT.value: [
                "project",
                "milestone",
                "deadline",
                "deliverable",
                "sprint",
                "iteration",
                "feature",
                "user story",
                "acceptance criteria",
                "scope",
                "requirements",
            ],
            ConversationContext.TECHNICAL.value: [
                "code",
                "function",
                "class",
                "method",
                "algorithm",
                "architecture",
                "database",
                "api",
                "service",
                "module",
                "library",
                "framework",
            ],
            ConversationContext.RESEARCH.value: [
                "research",
                "investigate",
                "explore",
                "analyze",
                "study",
                "review",
                "documentation",
                "article",
                "paper",
                "resource",
                "reference",
            ],
            ConversationContext.DEBUGGING.value: [
                "error",
                "bug",
                "issue",
                "problem",
                "debug",
                "fix",
                "troubleshoot",
                "exception",
                "crash",
                "failure",
                "broken",
                "not working",
            ],
            ConversationContext.PLANNING.value: [
                "plan",
                "schedule",
                "timeline",
                "roadmap",
                "strategy",
                "approach",
                "design",
                "architecture",
                "proposal",
                "outline",
                "structure",
            ],
        }

    def analyze_conversation_flows(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Analyze conversation flow patterns."""
        if len(messages) < 2:
            return []

        flows = []

        # Analyze message transitions
        transitions = self._analyze_transitions(messages)

        # Identify conversation states
        states = self._identify_conversation_states(messages)

        # Detect flow patterns
        flow_patterns = self._detect_flow_patterns(messages, transitions, states)

        flows.extend(flow_patterns)

        # Analyze flow efficiency
        efficiency_analysis = self._analyze_flow_efficiency(messages, transitions)
        flows.append(efficiency_analysis)

        return flows

    def _analyze_transitions(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Analyze transitions between messages."""
        transitions = []

        for i in range(1, len(messages)):
            prev_msg = messages[i - 1]
            curr_msg = messages[i]

            transition = {
                "from_context": prev_msg.context.value,
                "to_context": curr_msg.context.value,
                "time_gap": (curr_msg.timestamp - prev_msg.timestamp)
                / 1000
                / 60,  # minutes
                "content_similarity": self._calculate_content_similarity(
                    prev_msg.content, curr_msg.content
                ),
                "topic_continuity": self._calculate_topic_continuity(
                    prev_msg, curr_msg
                ),
                "question_answer_pair": self._is_question_answer_pair(
                    prev_msg, curr_msg
                ),
            }

            transitions.append(transition)

        return transitions

    def _identify_conversation_states(self, messages: list[ChatMessage]) -> list[str]:
        """Identify conversation states."""
        states = []

        for message in messages:
            content_lower = message.content.lower()

            # Define state indicators
            if any(
                indicator in content_lower
                for indicator in ["help", "stuck", "problem", "error"]
            ):
                states.append("problem_state")
            elif any(
                indicator in content_lower
                for indicator in ["try", "attempt", "let me", "how about"]
            ):
                states.append("exploration_state")
            elif any(
                indicator in content_lower
                for indicator in ["fixed", "solved", "worked", "success"]
            ):
                states.append("solution_state")
            elif any(
                indicator in content_lower
                for indicator in ["decided", "choose", "go with", "final"]
            ):
                states.append("decision_state")
            elif any(
                indicator in content_lower
                for indicator in ["question", "why", "how", "what"]
            ):
                states.append("question_state")
            else:
                states.append("discussion_state")

        return states

    def _detect_flow_patterns(
        self,
        messages: list[ChatMessage],
        transitions: list[dict[str, Any]],
        states: list[str],
    ) -> list[dict[str, Any]]:
        """Detect specific flow patterns."""
        patterns = []

        # Problem-Solution flow
        problem_solution_patterns = self._detect_problem_solution_flows(
            states, transitions
        )
        patterns.extend(problem_solution_patterns)

        # Decision-Making flow
        decision_patterns = self._detect_decision_flows(states, transitions)
        patterns.extend(decision_patterns)

        # Exploratory flow
        exploration_patterns = self._detect_exploration_flows(states, transitions)
        patterns.extend(exploration_patterns)

        return patterns

    def _detect_problem_solution_flows(
        self,
        states: list[str],
        transitions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect problem-solution flow patterns."""
        patterns = []

        i = 0
        while i < len(states):
            if states[i] == "problem_state":
                # Look for solution state
                j = i + 1
                while j < len(states) and states[j] != "solution_state":
                    j += 1

                if j < len(states):
                    # Calculate flow metrics
                    flow_duration = sum(t["time_gap"] for t in transitions[i:j])
                    steps_taken = j - i

                    pattern = {
                        "type": "problem_solution_flow",
                        "start_index": i,
                        "end_index": j,
                        "duration_minutes": flow_duration,
                        "steps_count": steps_taken,
                        "efficiency": (
                            "high"
                            if steps_taken < 5
                            else "medium" if steps_taken < 10 else "low"
                        ),
                        "transitions": transitions[i:j],
                    }
                    patterns.append(pattern)
                    i = j
                else:
                    i += 1
            else:
                i += 1

        return patterns

    def _detect_decision_flows(
        self, states: list[str], transitions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Detect decision-making flow patterns."""
        patterns = []

        for i, state in enumerate(states):
            if state == "decision_state":
                # Look back to find decision context
                start_idx = max(0, i - 5)
                preceding_states = states[start_idx:i]

                # Analyze decision context
                decision_context = self._analyze_decision_context(
                    preceding_states, transitions[start_idx:i]
                )

                pattern = {
                    "type": "decision_flow",
                    "decision_index": i,
                    "context_start": start_idx,
                    "preceding_states": preceding_states,
                    "decision_context": decision_context,
                    "confidence": decision_context.get("confidence", 0.5),
                }
                patterns.append(pattern)

        return patterns

    def _detect_exploration_flows(
        self, states: list[str], transitions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Detect exploratory flow patterns."""
        patterns = []

        i = 0
        while i < len(states):
            if states[i] == "exploration_state":
                # Count consecutive exploration states
                j = i
                while j < len(states) and states[j] == "exploration_state":
                    j += 1

                if j - i > 1:  # At least 2 consecutive exploration states
                    exploration_depth = j - i
                    avg_time_gap = (
                        np.mean([t["time_gap"] for t in transitions[i : j - 1]])
                        if j > i + 1
                        else 0
                    )

                    pattern = {
                        "type": "exploration_flow",
                        "start_index": i,
                        "end_index": j,
                        "depth": exploration_depth,
                        "avg_time_gap_minutes": avg_time_gap,
                        "thoroughness": (
                            "deep"
                            if exploration_depth > 5
                            else "moderate" if exploration_depth > 2 else "shallow"
                        ),
                    }
                    patterns.append(pattern)
                    i = j
                else:
                    i += 1
            else:
                i += 1

        return patterns

    def _analyze_flow_efficiency(
        self,
        messages: list[ChatMessage],
        transitions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze overall flow efficiency."""
        if not transitions:
            return {"type": "efficiency_analysis", "error": "No transitions to analyze"}

        # Calculate metrics
        avg_time_gap = np.mean([t["time_gap"] for t in transitions])
        avg_similarity = np.mean([t["content_similarity"] for t in transitions])
        context_changes = sum(
            1 for t in transitions if t["from_context"] != t["to_context"]
        )
        qa_pairs = sum(1 for t in transitions if t["question_answer_pair"])

        total_duration = sum(t["time_gap"] for t in transitions)
        efficiency_score = self._calculate_efficiency_score(
            avg_time_gap,
            avg_similarity,
            context_changes,
            qa_pairs,
            len(transitions),
        )

        return {
            "type": "efficiency_analysis",
            "total_duration_minutes": total_duration,
            "avg_time_gap_minutes": avg_time_gap,
            "avg_content_similarity": avg_similarity,
            "context_switches": context_changes,
            "question_answer_pairs": qa_pairs,
            "total_transitions": len(transitions),
            "efficiency_score": efficiency_score,
            "efficiency_rating": self._get_efficiency_rating(efficiency_score),
        }

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity between two messages."""
        words1 = set(re.findall(r"\b\w+\b", content1.lower()))
        words2 = set(re.findall(r"\b\w+\b", content2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _calculate_topic_continuity(
        self, msg1: ChatMessage, msg2: ChatMessage
    ) -> float:
        """Calculate topic continuity between messages."""
        topics1 = set(msg1.semantic_tags)
        topics2 = set(msg2.semantic_tags)

        if not topics1 or not topics2:
            return 0.0

        intersection = len(topics1.intersection(topics2))
        union = len(topics1.union(topics2))

        return intersection / union if union > 0 else 0.0

    def _is_question_answer_pair(self, msg1: ChatMessage, msg2: ChatMessage) -> bool:
        """Check if messages form a question-answer pair."""
        has_question = "?" in msg1.content or any(
            word in msg1.content.lower()
            for word in ["what", "how", "why", "when", "where", "which"]
        )

        has_answer = (
            any(
                word in msg2.content.lower()
                for word in ["because", "since", "due to", "answer", "solution"]
            )
            or len(msg2.content) > len(msg1.content) * 1.5
        )

        return has_question and has_answer

    def _analyze_decision_context(
        self,
        preceding_states: list[str],
        transitions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze context around a decision."""
        if not preceding_states:
            return {"confidence": 0.0, "context_type": "unknown"}

        # Count state types
        state_counts = Counter(preceding_states)

        # Determine decision context
        if state_counts["exploration_state"] > 0:
            context_type = "exploratory_decision"
            confidence = min(0.8, 0.3 + state_counts["exploration_state"] * 0.2)
        elif state_counts["problem_state"] > 0:
            context_type = "problem_solving_decision"
            confidence = min(0.9, 0.4 + state_counts["problem_state"] * 0.3)
        else:
            context_type = "routine_decision"
            confidence = 0.5

        return {
            "context_type": context_type,
            "confidence": confidence,
            "preceding_states": state_counts,
            "avg_transition_time": (
                np.mean([t["time_gap"] for t in transitions]) if transitions else 0
            ),
        }

    def _calculate_efficiency_score(
        self,
        avg_time_gap: float,
        avg_similarity: float,
        context_changes: int,
        qa_pairs: int,
        total_transitions: int,
    ) -> float:
        """Calculate overall flow efficiency score."""
        # Normalize metrics
        time_score = max(0, 1 - avg_time_gap / 60)  # Prefer shorter gaps
        similarity_score = avg_similarity  # Higher similarity is better
        context_score = max(
            0, 1 - context_changes / total_transitions
        )  # Fewer context changes
        qa_score = min(1, qa_pairs / (total_transitions / 2))  # Some Q&A is good

        # Weighted average
        return (
            time_score * 0.3
            + similarity_score * 0.3
            + context_score * 0.2
            + qa_score * 0.2
        )

    def _get_efficiency_rating(self, score: float) -> str:
        """Get efficiency rating from score."""
        if score >= 0.8:
            return "excellent"
        if score >= 0.6:
            return "good"
        if score >= 0.4:
            return "fair"
        return "poor"


class DecisionTrailAnalyzer:
    """Analyze decision-making trails in conversations."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.decision_indicators = self._load_decision_indicators()

    def _load_decision_indicators(self) -> dict[str, list[str]]:
        """Load decision-making indicators."""
        return {
            "options": [
                "option",
                "choice",
                "alternative",
                "either",
                "or",
                "versus",
                "vs",
            ],
            "decision_words": [
                "decided",
                "choose",
                "selected",
                "went with",
                "prefer",
                "final",
            ],
            "rationale": ["because", "since", "due to", "reason", "why", "justify"],
            "consideration": [
                "consider",
                "think about",
                "evaluate",
                "weigh",
                "compare",
            ],
        }

    def analyze_decision_trails(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Analyze decision-making trails."""
        decision_points = []
        decision_trails = []

        # Identify decision points
        for i, message in enumerate(messages):
            decision_point = self._identify_decision_point(message, messages, i)
            if decision_point:
                decision_points.append(decision_point)

        # Build decision trails
        for decision_point in decision_points:
            trail = self._build_decision_trail(
                decision_point, messages, decision_points
            )
            decision_trails.append(trail)

        self.logger.info(f"Analyzed {len(decision_trails)} decision trails")
        return decision_trails

    def _identify_decision_point(
        self,
        message: ChatMessage,
        all_messages: list[ChatMessage],
        index: int,
    ) -> DecisionPoint | None:
        """Identify if a message represents a decision point."""
        content_lower = message.content.lower()

        # Check for decision indicators
        decision_score = 0
        options_considered = []

        for category, indicators in self.decision_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in content_lower)
            if category == "decision_words" and matches > 0:
                decision_score += 3
            elif category == "options" and matches > 0:
                decision_score += 2
                # Extract options
                options_considered = self._extract_options(message.content)
            elif category == "rationale" and matches > 0:
                decision_score += 1

        if decision_score >= 2:  # Threshold for decision point
            return DecisionPoint(
                timestamp=message.timestamp,
                decision_type=self._classify_decision_type(message.content),
                options_considered=options_considered,
                chosen_option=self._extract_chosen_option(message.content),
                rationale=self._extract_rationale(message.content),
                participants=["user"],  # Simplified
                confidence=min(1.0, decision_score / 4),
            )

        return None

    def _extract_options(self, content: str) -> list[str]:
        """Extract options from decision text."""
        options = []

        # Look for patterns like "option A vs option B" or "choose X or Y"
        option_patterns = [
            r"(\w+)\s+(?:vs|versus|or)\s+(\w+)",
            r"(?:choose|select|pick)\s+(?:between|among)?\s*(.+?)(?:\s+or\s+|$)",
            r"option\s*[:\-]?\s*(.+?)(?:\s+or\s+|$)",
        ]

        for pattern in option_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    options.extend([m.strip() for m in match if m.strip()])
                else:
                    options.append(match.strip())

        return list(set(options))  # Remove duplicates

    def _extract_chosen_option(self, content: str) -> str | None:
        """Extract the chosen option from decision text."""
        chosen_patterns = [
            r"(?:chose|selected|went with|decided on)\s+(\w+)",
            r"(?:going with|using|implementing)\s+(\w+)",
        ]

        for pattern in chosen_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_rationale(self, content: str) -> str | None:
        """Extract rationale for decision."""
        rationale_patterns = [
            r"(?:because|since|due to|as)\s+([^,.!?]+)",
            r"reason[:\-]?\s*([^,.!?]+)",
            r"why[:\-]?\s*([^,.!?]+)",
        ]

        for pattern in rationale_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _classify_decision_type(self, content: str) -> str:
        """Classify the type of decision."""
        content_lower = content.lower()

        if any(
            word in content_lower
            for word in ["technical", "architecture", "design", "implementation"]
        ):
            return "technical"
        if any(
            word in content_lower
            for word in ["timeline", "schedule", "deadline", "priority"]
        ):
            return "temporal"
        if any(
            word in content_lower
            for word in ["tool", "library", "framework", "technology"]
        ):
            return "technology"
        if any(
            word in content_lower
            for word in ["process", "workflow", "approach", "method"]
        ):
            return "process"
        return "general"

    def _build_decision_trail(
        self,
        decision_point: DecisionPoint,
        messages: list[ChatMessage],
        all_decisions: list[DecisionPoint],
    ) -> dict[str, Any]:
        """Build trail leading to decision."""
        # Find messages leading to this decision
        decision_time = decision_point.timestamp
        trail_messages = []

        for message in messages:
            if message.timestamp < decision_time:
                trail_messages.append(message)

        # Analyze trail characteristics
        trail_duration = (
            decision_time - trail_messages[0].timestamp if trail_messages else 0
        )
        exploration_depth = len(
            [
                m
                for m in trail_messages
                if any(
                    word in m.content.lower()
                    for word in ["explore", "try", "consider", "option"]
                )
            ],
        )

        return {
            "decision_point": decision_point,
            "trail_messages_count": len(trail_messages),
            "trail_duration_minutes": trail_duration / 1000 / 60,
            "exploration_depth": exploration_depth,
            "context_switches": self._count_context_switches(trail_messages),
            "decision_quality": self._assess_decision_quality(
                decision_point, trail_messages
            ),
        }

    def _count_context_switches(self, messages: list[ChatMessage]) -> int:
        """Count context switches in trail."""
        if len(messages) < 2:
            return 0

        switches = 0
        for i in range(1, len(messages)):
            if messages[i].context != messages[i - 1].context:
                switches += 1

        return switches

    def _assess_decision_quality(
        self,
        decision_point: DecisionPoint,
        trail_messages: list[ChatMessage],
    ) -> dict[str, Any]:
        """Assess quality of decision."""
        quality_factors = {
            "has_options": len(decision_point.options_considered) > 0,
            "has_rationale": decision_point.rationale is not None,
            "thoroughness": len(trail_messages),
            "confidence": decision_point.confidence,
        }

        # Calculate overall quality score
        score = 0
        if quality_factors["has_options"]:
            score += 0.3
        if quality_factors["has_rationale"]:
            score += 0.3
        if quality_factors["thoroughness"] > 5:
            score += 0.2
        elif quality_factors["thoroughness"] > 2:
            score += 0.1
        score += quality_factors["confidence"] * 0.2

        return {
            "factors": quality_factors,
            "score": min(1.0, score),
            "rating": "high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
        }


class WorkflowAnalyzer:
    """Analyze workflow patterns in conversations."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.workflow_patterns = self._load_workflow_patterns()

    def _load_workflow_patterns(self) -> dict[str, list[str]]:
        """Load workflow pattern indicators."""
        return {
            "development": [
                "code",
                "implement",
                "develop",
                "program",
                "script",
                "function",
            ],
            "testing": ["test", "verify", "validate", "check", "debug", "troubleshoot"],
            "deployment": ["deploy", "release", "publish", "ship", "push", "merge"],
            "documentation": [
                "document",
                "write",
                "explain",
                "describe",
                "comment",
                "readme",
            ],
            "planning": ["plan", "design", "architect", "specify", "define", "outline"],
            "review": ["review", "audit", "inspect", "examine", "analyze", "evaluate"],
        }

    def identify_workflow_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Identify workflow patterns in conversations."""
        workflows = []

        # Segment messages into workflow sessions
        workflow_sessions = self._segment_workflow_sessions(messages)

        for session in workflow_sessions:
            workflow_pattern = self._analyze_workflow_session(session)
            workflows.append(workflow_pattern)

        # Identify workflow types
        for workflow in workflows:
            workflow["type"] = self._classify_workflow_type(workflow["messages"])
            workflow["efficiency"] = self._calculate_workflow_efficiency(
                workflow["messages"]
            )

        self.logger.info(f"Identified {len(workflows)} workflow patterns")
        return workflows

    def _segment_workflow_sessions(
        self, messages: list[ChatMessage]
    ) -> list[list[ChatMessage]]:
        """Segment messages into workflow sessions."""
        if not messages:
            return []

        sessions = []
        current_session = [messages[0]]

        for i in range(1, len(messages)):
            current_msg = messages[i]
            prev_msg = messages[i - 1]

            # Check for session break (context switch or long time gap)
            time_gap = (
                (current_msg.timestamp - prev_msg.timestamp) / 1000 / 60
            )  # minutes

            if (
                current_msg.context != prev_msg.context
                or time_gap > 30
                or self._is_workflow_boundary(current_msg.content, prev_msg.content)
            ):
                # Start new session
                sessions.append(current_session)
                current_session = [current_msg]
            else:
                current_session.append(current_msg)

        if current_session:
            sessions.append(current_session)

        return sessions

    def _is_workflow_boundary(self, current_content: str, prev_content: str) -> bool:
        """Check if there's a workflow boundary between messages."""
        boundary_indicators = [
            "next step",
            "now let's",
            "moving on",
            "finally",
            "in conclusion",
            "summary",
            "recap",
            "done",
            "finished",
            "complete",
        ]

        return any(
            indicator in current_content.lower() for indicator in boundary_indicators
        )

    def _analyze_workflow_session(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Analyze a single workflow session."""
        if not messages:
            return {}

        # Calculate session metrics
        duration = (
            (messages[-1].timestamp - messages[0].timestamp) / 1000 / 60
        )  # minutes
        message_frequency = len(messages) / max(duration, 1)

        # Identify activities
        activities = self._identify_activities(messages)

        return {
            "messages": messages,
            "duration_minutes": duration,
            "message_count": len(messages),
            "message_frequency": message_frequency,
            "activities": activities,
            "start_time": messages[0].timestamp,
            "end_time": messages[-1].timestamp,
            "context": messages[0].context.value,
        }

    def _identify_activities(self, messages: list[ChatMessage]) -> list[str]:
        """Identify activities in workflow session."""
        activities = []

        for message in messages:
            content_lower = message.content.lower()

            for activity, indicators in self.workflow_patterns.items():
                if any(indicator in content_lower for indicator in indicators):
                    activities.append(activity)
                    break

        return list(set(activities))

    def _classify_workflow_type(self, messages: list[ChatMessage]) -> str:
        """Classify workflow type."""
        activities = self._identify_activities(messages)

        if not activities:
            return "general"

        activity_counts = Counter(activities)
        dominant_activity = activity_counts.most_common(1)[0][0]

        # Check for multi-activity workflows
        if len(activity_counts) > 1:
            return f"multi_activity_{dominant_activity}"
        return dominant_activity

    def _calculate_workflow_efficiency(
        self, messages: list[ChatMessage]
    ) -> dict[str, Any]:
        """Calculate workflow efficiency metrics."""
        if len(messages) < 2:
            return {"score": 0.5, "rating": "insufficient_data"}

        # Calculate metrics
        time_gaps = []
        for i in range(1, len(messages)):
            gap = (messages[i].timestamp - messages[i - 1].timestamp) / 1000 / 60
            time_gaps.append(gap)

        avg_time_gap = np.mean(time_gaps)
        time_consistency = (
            1 - (np.std(time_gaps) / avg_time_gap) if avg_time_gap > 0 else 0
        )

        # Activity diversity
        activities = self._identify_activities(messages)
        diversity = len(set(activities)) / len(activities) if activities else 0

        # Completion indicators
        completion_words = [
            "done",
            "finished",
            "complete",
            "success",
            "working",
            "solved",
        ]
        has_completion = any(
            word in msg.content.lower() for msg in messages for word in completion_words
        )

        # Calculate efficiency score
        time_score = max(0, 1 - avg_time_gap / 20)  # Prefer shorter gaps
        consistency_score = time_consistency
        diversity_score = diversity
        completion_score = 0.8 if has_completion else 0.4

        efficiency_score = (
            time_score * 0.3
            + consistency_score * 0.3
            + diversity_score * 0.2
            + completion_score * 0.2
        )

        return {
            "score": efficiency_score,
            "rating": self._get_efficiency_rating(efficiency_score),
            "avg_time_gap": avg_time_gap,
            "time_consistency": consistency_score,
            "activity_diversity": diversity,
            "has_completion": has_completion,
        }

    def _get_efficiency_rating(self, score: float) -> str:
        """Get efficiency rating from score."""
        if score >= 0.8:
            return "highly_efficient"
        if score >= 0.6:
            return "efficient"
        if score >= 0.4:
            return "moderate"
        return "inefficient"


class EnhancedPatternRecognizer(IPatternRecognizer):
    """Enhanced pattern recognizer with comprehensive analysis capabilities."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.flow_analyzer = ConversationFlowAnalyzer()
        self.decision_analyzer = DecisionTrailAnalyzer()
        self.workflow_analyzer = WorkflowAnalyzer()

    def identify_conversation_patterns(
        self, messages: list[ChatMessage]
    ) -> list[ConversationPattern]:
        """Identify conversation patterns."""
        patterns = []

        # Flow patterns
        flow_patterns = self.flow_analyzer.analyze_conversation_flows(messages)
        for flow_pattern in flow_patterns:
            pattern = ConversationPattern(
                pattern_type=flow_pattern.get("type", "unknown"),
                description=flow_pattern.get("type", "Unknown flow pattern"),
                frequency=1,  # Each pattern occurs once in this context
                confidence=0.7,
                time_span_days=1,  # Simplified
                sample_messages=[],
                evidence_entries=[msg.id for msg in messages],
                processing_metadata=flow_pattern,
            )
            patterns.append(pattern)

        # Decision patterns
        decision_trails = self.decision_analyzer.analyze_decision_trails(messages)
        for trail in decision_trails:
            pattern = ConversationPattern(
                pattern_type="decision_trail",
                description=f"Decision-making process: {trail['decision_point'].decision_type}",
                frequency=1,
                confidence=trail["decision_quality"]["score"],
                time_span_days=1,
                sample_messages=[
                    trail["decision_point"].rationale or "No rationale provided"
                ],
                evidence_entries=[msg.id for msg in messages],
                processing_metadata=trail,
            )
            patterns.append(pattern)

        # Workflow patterns
        workflow_patterns = self.workflow_analyzer.identify_workflow_patterns(messages)
        for workflow in workflow_patterns:
            pattern = ConversationPattern(
                pattern_type="workflow",
                description=f"Workflow: {workflow['type']} (efficiency: {workflow['efficiency']['rating']})",
                frequency=1,
                confidence=workflow["efficiency"]["score"],
                time_span_days=1,
                sample_messages=[workflow["type"]],
                evidence_entries=[msg.id for msg in workflow["messages"]],
                processing_metadata=workflow,
            )
            patterns.append(pattern)

        self.logger.info(f"Identified {len(patterns)} conversation patterns")
        return patterns

    def analyze_decision_trails(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Analyze decision-making trails."""
        return self.decision_analyzer.analyze_decision_trails(messages)

    def detect_problem_solution_pairs(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect problem-solution patterns."""
        problem_solution_pairs = []

        # Identify problem indicators
        problem_indicators = [
            "error",
            "issue",
            "problem",
            "bug",
            "broken",
            "not working",
            "stuck",
        ]
        solution_indicators = [
            "fixed",
            "solved",
            "resolved",
            "working",
            "success",
            "solution",
        ]

        for i, message in enumerate(messages):
            content_lower = message.content.lower()

            # Check if message contains a problem
            if any(indicator in content_lower for indicator in problem_indicators):
                # Look for solution in following messages
                for j in range(i + 1, min(i + 10, len(messages))):
                    later_content = messages[j].content.lower()
                    if any(
                        indicator in later_content for indicator in solution_indicators
                    ):
                        pair = {
                            "problem_message": message,
                            "solution_message": messages[j],
                            "resolution_time": (
                                messages[j].timestamp - message.timestamp
                            )
                            / 1000
                            / 60,
                            "messages_between": j - i - 1,
                            "problem_type": self._classify_problem_type(
                                message.content
                            ),
                            "solution_type": self._classify_solution_type(
                                messages[j].content
                            ),
                        }
                        problem_solution_pairs.append(pair)
                        break

        return problem_solution_pairs

    def identify_workflow_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Identify workflow patterns."""
        return self.workflow_analyzer.identify_workflow_patterns(messages)

    def analyze_conversation_flows(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Analyze conversation flow patterns."""
        return self.flow_analyzer.analyze_conversation_flows(messages)

    def detect_context_switches(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect context switches in conversations."""
        context_switches = []

        for i in range(1, len(messages)):
            if messages[i].context != messages[i - 1].context:
                switch = {
                    "from_context": messages[i - 1].context.value,
                    "to_context": messages[i].context.value,
                    "timestamp": messages[i].timestamp,
                    "time_gap": (messages[i].timestamp - messages[i - 1].timestamp)
                    / 1000
                    / 60,
                    "trigger_message": messages[i].content[:100],
                    "switch_type": self._classify_context_switch(
                        messages[i - 1], messages[i]
                    ),
                }
                context_switches.append(switch)

        return context_switches

    def calculate_pattern_confidence(
        self, pattern: ConversationPattern, evidence: list[ChatMessage]
    ) -> float:
        """Calculate confidence score for pattern."""
        if not evidence:
            return 0.0

        # Base confidence from pattern
        base_confidence = pattern.confidence

        # Evidence strength (number of supporting messages)
        evidence_strength = min(1.0, len(evidence) / 10)

        # Temporal consistency (how closely grouped in time)
        if len(evidence) > 1:
            timestamps = [msg.timestamp for msg in evidence]
            time_span = max(timestamps) - min(timestamps)
            temporal_consistency = max(
                0, 1 - time_span / (7 * 24 * 60 * 60 * 1000)
            )  # Decay over a week
        else:
            temporal_consistency = 0.5

        # Content similarity
        if len(evidence) > 1:
            similarities = []
            for i in range(len(evidence)):
                for j in range(i + 1, len(evidence)):
                    similarity = self.flow_analyzer._calculate_content_similarity(
                        evidence[i].content,
                        evidence[j].content,
                    )
                    similarities.append(similarity)
            content_similarity = np.mean(similarities) if similarities else 0.5
        else:
            content_similarity = 0.5

        # Weighted combination
        final_confidence = (
            base_confidence * 0.4
            + evidence_strength * 0.3
            + temporal_consistency * 0.2
            + content_similarity * 0.1
        )

        return min(1.0, final_confidence)

    def _classify_problem_type(self, content: str) -> str:
        """Classify problem type."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["error", "exception", "traceback"]):
            return "error"
        if any(word in content_lower for word in ["slow", "performance", "optimize"]):
            return "performance"
        if any(
            word in content_lower for word in ["design", "architecture", "structure"]
        ):
            return "design"
        if any(word in content_lower for word in ["logic", "algorithm", "approach"]):
            return "logic"
        return "general"

    def _classify_solution_type(self, content: str) -> str:
        """Classify solution type."""
        content_lower = content.lower()

        if any(word in content_lower for word in ["fix", "patch", "change"]):
            return "fix"
        if any(word in content_lower for word in ["refactor", "improve", "optimize"]):
            return "improvement"
        if any(word in content_lower for word in ["workaround", "alternative"]):
            return "workaround"
        if any(word in content_lower for word in ["reimplement", "rewrite"]):
            return "rewrite"
        return "general"

    def _classify_context_switch(
        self, from_msg: ChatMessage, to_msg: ChatMessage
    ) -> str:
        """Classify type of context switch."""
        # Problem -> Solution
        if from_msg.context == ConversationContext.DEBUGGING and to_msg.context in [
            ConversationContext.TECHNICAL,
            ConversationContext.PROJECT,
        ]:
            return "problem_to_solution"

        # Planning -> Implementation
        if (
            from_msg.context == ConversationContext.PLANNING
            and to_msg.context == ConversationContext.TECHNICAL
        ):
            return "planning_to_implementation"

        # Discussion -> Decision
        if from_msg.context == ConversationContext.GENERAL and to_msg.context in [
            ConversationContext.PROJECT,
            ConversationContext.TECHNICAL,
        ]:
            return "discussion_to_action"

        # Technical break
        if (
            from_msg.context == ConversationContext.TECHNICAL
            and to_msg.context == ConversationContext.GENERAL
        ):
            return "technical_break"

        return "context_switch"
