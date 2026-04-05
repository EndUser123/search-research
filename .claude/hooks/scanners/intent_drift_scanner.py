#!/usr/bin/env python3
"""
Intent Drift Detection Scanner
==============================

Detects when model actions drift from the original user intent.

Based on patterns from Voyager agent:
https://github.com/MinecraftYuan/Voyager

Features:
- Computes drift score between original intent and current action
- Tracks intent trajectory across session
- Warns when drift exceeds threshold

Prevents scope creep by validating that actions align with stated goals.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from .base_scanner import BaseScanner, ScanResult, ScanStatus

# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
class IntentDriftScanner(BaseScanner):
    """
    Intent drift detection scanner.

    Tracks original user intent and validates that subsequent actions
    remain aligned with that intent.
    """

    # Default drift threshold (0.0 = aligned, 1.0 = completely drifted)
    DEFAULT_THRESHOLD = 0.6

    # Session state file
    STATE_FILE = PROJECT_ROOT / ".claude" / "session_data" / "intent_state.json"

    # Action types that indicate scope expansion
    SCOPE_EXPANSION_PATTERNS = [
        r"also\s+(?:create|implement|build|add)\s+",
        r"(?:additionally|meanwhile|furthermore|besides)\s*,",
        r"(?:while\s+we're\s+at\s+it|since\s+we're\s+here)",
        r"(?:might\s+(?:as\s+well|also)|could\s+also)\s+",
        r"(?:let's\s+also|we\s+should\s+also)\s+",
    ]

    # Goal action verbs for classification
    GOAL_ACTIONS = {
        "fix": ["fix", "repair", "correct", "patch", "resolve"],
        "implement": ["implement", "build", "create", "add", "develop"],
        "refactor": ["refactor", "restructure", "reorganize", "clean"],
        "analyze": ["analyze", "review", "examine", "investigate", "check"],
        "optimize": ["optimize", "improve", "enhance", "speed up"],
        "remove": ["remove", "delete", "eliminate", "get rid of"],
        "test": ["test", "verify", "validate", "check"],
        "document": ["document", "write docs", "comment"],
    }

    def __init__(self, enabled: bool = True, threshold: float = DEFAULT_THRESHOLD):
        """
        Initialize intent drift scanner.

        Args:
            enabled: Whether scanner is active
            threshold: Drift score threshold (0.0 to 1.0)
        """
        super().__init__(enabled)
        self.threshold = threshold
        self._intent_state = self._load_state()

    def scan(self, text: str, context: dict = None) -> ScanResult:
        """
        Scan response for intent drift.

        Args:
            text: The text to scan (usually model response)
            context: Optional context (original prompt, current goal, etc.)

        Returns:
            ScanResult with validation outcome
        """
        if not self.enabled:
            return ScanResult(ScanStatus.SKIP, self.name)

        # Get current goal from context or state
        current_goal = self._get_current_goal(context)

        if not current_goal:
            # No goal set yet, skip drift detection
            return ScanResult(ScanStatus.SKIP, self.name, reason="No goal set for drift detection")

        # Extract action from response
        response_action = self._extract_action(text)

        if not response_action:
            return ScanResult(ScanStatus.PASS, self.name)

        # Compute drift score
        drift_score = self._compute_drift(current_goal, response_action, text)

        # Update state with current action
        self._update_action_history(response_action, drift_score)

        if drift_score > self.threshold:
            return ScanResult(
                status=ScanStatus.FAIL,
                scanner_name=self.name,
                matched_text=response_action.get("text", "")[:50],
                reason=f"Intent drift detected (score: {drift_score:.2f}, threshold: {self.threshold:.2f})",
                severity="MEDIUM",
                suggestion=(
                    f"Original goal: {current_goal.get('text', 'unknown')}\n"
                    f"Current action: {response_action.get('text', 'unknown')}\n"
                    f"Stay focused on the stated objective."
                ),
            )

        return ScanResult(ScanStatus.PASS, self.name)

    def _get_current_goal(self, context: dict = None) -> dict | None:
        """Get the current/primary goal from context or state."""
        # First check context
        if context:
            if "primary_goal" in context:
                return {"text": context["primary_goal"], "source": "context"}
            if "goal" in context:
                return {"text": context["goal"], "source": "context"}

        # Check session state
        if self._intent_state:
            if "primary_goal" in self._intent_state:
                return {
                    "text": self._intent_state["primary_goal"],
                    "source": "session_state",
                }

        return None

    def _extract_action(self, text: str) -> dict | None:
        """
        Extract action description from response text.

        Returns dict with keys: text, action_type, scope
        """
        # Look for statements about what was done or is being done
        action_patterns = [
            r"(?:I've|I have|I)\s+(?:created|implemented|built|added|written)\s+([^.\n]{10,100})",
            r"(?:Creating|Implementing|Building|Adding|Writing)\s+([^.\n]{10,100})",
            r"(?:Now\s+)?(?:I'll|I will)\s+(?:create|implement|build|add|write)\s+([^.\n]{10,100})",
        ]

        for pattern in action_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                action_text = match.group(0)
                action_type = self._classify_action(action_text)
                return {"text": action_text, "action_type": action_type}

        return None

    def _classify_action(self, action_text: str) -> str:
        """Classify action type (fix, implement, refactor, etc.)."""
        action_lower = action_text.lower()

        for action_type, verbs in self.GOAL_ACTIONS.items():
            if any(verb in action_lower for verb in verbs):
                return action_type

        return "unknown"

    def _compute_drift(self, goal: dict, action: dict, response_text: str) -> float:
        """
        Compute drift score between goal and action.

        Returns:
            Float from 0.0 (aligned) to 1.0 (completely drifted)
        """
        goal_text = goal.get("text", "").lower()
        action_text = action.get("text", "").lower()
        goal_type = self._classify_action(goal_text)
        action_type = action.get("action_type", "unknown")

        # Base drift from action type mismatch
        type_drift = 0.0
        if goal_type != "unknown" and action_type != "unknown":
            if goal_type != action_type:
                # Determine how different the action types are
                compatible_actions = {
                    "fix": ["refactor", "test"],
                    "implement": ["refactor", "test"],
                    "refactor": ["optimize"],
                    "optimize": ["refactor"],
                    "test": ["fix", "implement"],
                }

                if action_type not in compatible_actions.get(goal_type, []):
                    type_drift = 0.5  # Significant mismatch

        # Check for scope expansion patterns
        scope_drift = 0.0
        for pattern in self.SCOPE_EXPANSION_PATTERNS:
            if re.search(pattern, response_text, re.IGNORECASE):
                scope_drift = 0.3
                break

        # Check for specific keyword mismatches
        goal_keywords = self._extract_keywords(goal_text)
        action_keywords = self._extract_keywords(action_text)

        # If action introduces completely new topics not in goal
        new_topic_drift = 0.0
        if action_keywords - goal_keywords:
            # At least some new topics
            new_topic_ratio = len(action_keywords - goal_keywords) / max(len(action_keywords), 1)
            new_topic_drift = min(new_topic_ratio * 0.4, 0.5)

        # Combined drift score
        drift = type_drift + scope_drift + new_topic_drift
        return min(drift, 1.0)  # Cap at 1.0

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "should", "could", "may", "might", "can", "this",
            "that", "these", "those", "i", "you", "we", "they", "it",
        }

        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return set(words) - stop_words

    def _update_action_history(self, action: dict, drift_score: float) -> None:
        """Update the action history in session state."""
        if not self._intent_state:
            self._intent_state = {}

        if "action_history" not in self._intent_state:
            self._intent_state["action_history"] = []

        self._intent_state["action_history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "drift_score": drift_score,
        })

        # Keep only last 50 actions
        if len(self._intent_state["action_history"]) > 50:
            self._intent_state["action_history"] = self._intent_state["action_history"][-50:]

        self._save_state()

    def set_primary_goal(self, goal_text: str) -> None:
        """Set the primary goal for drift detection."""
        if not self._intent_state:
            self._intent_state = {}

        self._intent_state["primary_goal"] = goal_text
        self._intent_state["goal_set_at"] = datetime.now().isoformat()
        self._save_state()

    def _load_state(self) -> dict | None:
        """Load intent state from file."""
        try:
            if self.STATE_FILE.exists():
                return json.loads(self.STATE_FILE.read_text())
        except Exception:
            pass
        return {}

    def _save_state(self) -> None:
        """Save intent state to file."""
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.STATE_FILE.write_text(json.dumps(self._intent_state, indent=2))
        except Exception:
            pass

    def get_drift_summary(self) -> dict:
        """Get summary of drift detection history."""
        if not self._intent_state:
            return {"status": "No intent state"}

        action_history = self._intent_state.get("action_history", [])

        if not action_history:
            return {
                "primary_goal": self._intent_state.get("primary_goal", "Not set"),
                "actions_tracked": 0,
                "average_drift": 0.0,
            }

        drifts = [a.get("drift_score", 0.0) for a in action_history]
        return {
            "primary_goal": self._intent_state.get("primary_goal", "Not set"),
            "actions_tracked": len(action_history),
            "average_drift": sum(drifts) / len(drifts) if drifts else 0.0,
            "max_drift": max(drifts) if drifts else 0.0,
            "recent_actions": [
                {
                    "action": a.get("action", {}).get("text", "")[:50],
                    "drift": a.get("drift_score", 0.0),
                    "timestamp": a.get("timestamp", ""),
                }
                for a in action_history[-5:]  # Last 5 actions
            ],
        }
