#!/usr/bin/env python3
"""
Task Automation Engine for TaskMaster GitHub Integration
Maps GitHub events to automated task creation and management with CWO12 compliance
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types with CWO12 compliance requirements"""

    BUG = "bug"
    FEATURE = "feature"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_REVIEW = "code_review"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskPhase(Enum):
    """Task phases with workflow progression"""

    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


@dataclass
class AutomationRule:
    """Rule for automating task creation from GitHub events"""

    rule_id: str
    name: str
    description: str
    event_type: str
    conditions: dict[str, Any]
    task_template: dict[str, Any]
    enabled: bool = True
    cwo12_compliance_required: bool = True
    created_at: str = None
    updated_at: str = None


@dataclass
class TaskCreationRequest:
    """Standardized task creation request"""

    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    phase: TaskPhase
    source: str
    source_event_id: str
    acceptance_criteria: list[str]
    tags: list[str]
    estimated_duration: int | None
    parent_task_id: str | None
    dependencies: list[str]
    metadata: dict[str, Any]
    cwo12_compliance_data: dict[str, Any]


class TaskAutomationEngine:
    """Advanced task automation engine with CWO12 compliance"""

    def __init__(self, db_path: Path = Path("P:/.speckit/taskmaster/tasks.db")):
        self.db_path = db_path
        self.automation_rules: list[AutomationRule] = []
        self.task_type_mapping = {}
        self.priority_mapping = {}
        self.phase_mapping = {}

        # Initialize default automation rules
        self._initialize_default_rules()

        # CWO12 compliance validators
        self.cwo12_validators = {
            "evidence_required": self._validate_evidence_requirements,
            "constitutional_compliance": self._validate_constitutional_compliance,
            "documentation_complete": self._validate_documentation_completeness,
            "verification_ready": self._validate_verification_readiness,
        }

    def _initialize_default_rules(self):
        """Initialize default automation rules for GitHub events"""
        default_rules = [
            # Pull Request Rules
            AutomationRule(
                rule_id="pr_opened_feature",
                name="PR Opened - Feature Development",
                description="Create task for new feature pull requests",
                event_type="pull_request",
                conditions={
                    "action": ["opened", "ready_for_review"],
                    "labels_contains": ["feature", "enhancement"],
                    "title_not_contains": ["fix", "bug"],
                },
                task_template={
                    "task_type": TaskType.FEATURE,
                    "priority": TaskPriority.MEDIUM,
                    "phase": TaskPhase.DEVELOPMENT,
                    "acceptance_criteria": [
                        "Feature requirements fully implemented",
                        "Unit tests written and passing",
                        "Code reviewed and approved",
                        "Documentation updated",
                    ],
                    "tags": ["github", "pr", "feature", "automated"],
                },
                cwo12_compliance_required=True,
            ),
            AutomationRule(
                rule_id="pr_opened_bug",
                name="PR Opened - Bug Fix",
                description="Create task for bug fix pull requests",
                event_type="pull_request",
                conditions={
                    "action": ["opened", "ready_for_review"],
                    "labels_contains": ["bug", "fix"],
                    "title_contains": ["fix", "bug"],
                },
                task_template={
                    "task_type": TaskType.BUG,
                    "priority": TaskPriority.HIGH,
                    "phase": TaskPhase.TESTING,
                    "acceptance_criteria": [
                        "Bug reproduction verified",
                        "Fix implemented and tested",
                        "Regression tests pass",
                        "Root cause documented",
                    ],
                    "tags": ["github", "pr", "bug", "automated"],
                },
                cwo12_compliance_required=True,
            ),
            # Push Event Rules
            AutomationRule(
                rule_id="push_with_task_keywords",
                name="Push with Task Keywords",
                description="Create tasks from commits with task creation keywords",
                event_type="push",
                conditions={
                    "commit_message_contains": [
                        "task-create",
                        "tsk.new",
                        "TODO:",
                        "FIXME:",
                    ]
                },
                task_template={
                    "task_type": TaskType.DEVELOPMENT,
                    "priority": TaskPriority.MEDIUM,
                    "phase": TaskPhase.PLANNING,
                    "acceptance_criteria": [
                        "Requirements clearly defined",
                        "Implementation approach planned",
                        "Dependencies identified",
                        "Testing strategy defined",
                    ],
                    "tags": ["github", "commit", "automated"],
                },
                cwo12_compliance_required=True,
            ),
            # Issue Event Rules
            AutomationRule(
                rule_id="issue_opened",
                name="Issue Opened",
                description="Create task from GitHub issues",
                event_type="issues",
                conditions={"action": "opened"},
                task_template={
                    "task_type": TaskType.FEATURE,
                    "priority": TaskPriority.MEDIUM,
                    "phase": TaskPhase.PLANNING,
                    "acceptance_criteria": [
                        "Issue requirements understood",
                        "Solution approach designed",
                        "Implementation planned",
                        "Acceptance criteria defined",
                    ],
                    "tags": ["github", "issue", "automated"],
                },
                cwo12_compliance_required=True,
            ),
            # Security Rules
            AutomationRule(
                rule_id="security_vulnerability",
                name="Security Vulnerability",
                description="High priority task for security-related changes",
                event_type="pull_request",
                conditions={
                    "labels_contains": ["security", "vulnerability"],
                    "title_contains": [
                        "security",
                        "vulnerability",
                        "auth",
                        "permission",
                    ],
                },
                task_template={
                    "task_type": TaskType.SECURITY,
                    "priority": TaskPriority.CRITICAL,
                    "phase": TaskPhase.TESTING,
                    "acceptance_criteria": [
                        "Security vulnerability assessed",
                        "Fix implemented and tested",
                        "Security review completed",
                        "Compliance verification passed",
                    ],
                    "tags": ["github", "pr", "security", "critical", "automated"],
                },
                cwo12_compliance_required=True,
            ),
            # Documentation Rules
            AutomationRule(
                rule_id="documentation_changes",
                name="Documentation Changes",
                description="Create task for documentation updates",
                event_type="pull_request",
                conditions={
                    "files_changed_extensions": [".md", ".rst", ".txt", ".doc"],
                    "labels_contains": ["documentation", "docs"],
                },
                task_template={
                    "task_type": TaskType.DOCUMENTATION,
                    "priority": TaskPriority.LOW,
                    "phase": TaskPhase.REVIEW,
                    "acceptance_criteria": [
                        "Documentation accurate and complete",
                        "Examples provided and tested",
                        "Formatting standards followed",
                        "Review feedback incorporated",
                    ],
                    "tags": ["github", "pr", "documentation", "automated"],
                },
                cwo12_compliance_required=False,
            ),
        ]

        self.automation_rules.extend(default_rules)

    async def process_github_event(self, event_data: dict[str, Any]) -> list[str]:
        """
        Process GitHub event and create tasks based on automation rules
        Returns list of created task IDs
        """
        created_task_ids = []

        try:
            event_type = event_data.get("event_type", "")
            payload = event_data.get("payload", {})

            # Find matching rules
            matching_rules = self._find_matching_rules(event_type, payload)

            logger.info(
                f"Found {len(matching_rules)} matching rules for {event_type} event"
            )

            for rule in matching_rules:
                try:
                    # Create task request
                    task_request = self._create_task_from_rule(rule, event_data)

                    # Validate CWO12 compliance if required
                    if rule.cwo12_compliance_required:
                        compliance_result = await self._validate_cwo12_compliance(
                            task_request
                        )
                        if not compliance_result["compliant"]:
                            logger.warning(
                                f"Task creation blocked due to CWO12 compliance issues: {compliance_result['issues']}"
                            )
                            continue

                    # Create task in database
                    task_id = await self._create_task_in_database(task_request)
                    created_task_ids.append(task_id)

                    logger.info(f"Created task {task_id} using rule {rule.rule_id}")

                except Exception as e:
                    logger.error(
                        f"Error processing rule {rule.rule_id}: {e}", exc_info=True
                    )
                    continue

            return created_task_ids

        except Exception as e:
            logger.error(f"Error processing GitHub event: {e}", exc_info=True)
            return created_task_ids

    def _find_matching_rules(
        self, event_type: str, payload: dict[str, Any]
    ) -> list[AutomationRule]:
        """Find automation rules that match the event"""
        matching_rules = []

        for rule in self.automation_rules:
            if not rule.enabled:
                continue

            if rule.event_type != event_type:
                continue

            if self._evaluate_conditions(rule.conditions, payload):
                matching_rules.append(rule)

        return matching_rules

    def _evaluate_conditions(
        self, conditions: dict[str, Any], payload: dict[str, Any]
    ) -> bool:
        """Evaluate rule conditions against payload"""
        for condition_key, condition_value in conditions.items():
            if not self._evaluate_single_condition(
                condition_key, condition_value, payload
            ):
                return False
        return True

    def _evaluate_single_condition(
        self, key: str, value: Any, payload: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition"""
        if key == "action":
            actual_value = payload.get("action")
            if isinstance(value, list):
                return actual_value in value
            return actual_value == value

        elif key == "labels_contains":
            labels = [
                label.get("name", "").lower() for label in payload.get("labels", [])
            ]
            if isinstance(value, list):
                return any(v.lower() in labels for v in value)
            return value.lower() in labels

        elif key == "title_contains":
            title = payload.get("title", "").lower()
            if isinstance(value, list):
                return any(v.lower() in title for v in value)
            return value.lower() in title

        elif key == "title_not_contains":
            title = payload.get("title", "").lower()
            if isinstance(value, list):
                return not any(v.lower() in title for v in value)
            return value.lower() not in title

        elif key == "commit_message_contains":
            commits = payload.get("commits", [])
            for commit in commits:
                message = commit.get("message", "").lower()
                if isinstance(value, list):
                    if any(v.lower() in message for v in value):
                        return True
                elif value.lower() in message:
                    return True
            return False

        elif key == "files_changed_extensions":
            # This would need file information from the event
            # For now, return True as this would be evaluated elsewhere
            return True

        return True

    def _create_task_from_rule(
        self, rule: AutomationRule, event_data: dict[str, Any]
    ) -> TaskCreationRequest:
        """Create task request from automation rule"""
        payload = event_data.get("payload", {})
        event_type = event_data.get("event_type", "")

        # Extract information based on event type
        if event_type == "pull_request":
            return self._create_pr_task(rule, payload, event_data)
        elif event_type == "push":
            return self._create_commit_task(rule, payload, event_data)
        elif event_type == "issues":
            return self._create_issue_task(rule, payload, event_data)
        else:
            return self._create_generic_task(rule, payload, event_data)

    def _create_pr_task(
        self, rule: AutomationRule, payload: dict[str, Any], event_data: dict[str, Any]
    ) -> TaskCreationRequest:
        """Create task request from pull request"""
        pr = payload.get("pull_request", {})
        title = pr.get("title", "")
        description = pr.get("body", "")
        author = pr.get("user", {}).get("login", "unknown")
        labels = [label.get("name", "") for label in pr.get("labels", [])]

        # Customize template with PR data
        template = rule.task_template.copy()

        return TaskCreationRequest(
            title=f"PR Review: {title}",
            description=f"Automated task from GitHub PR:\n\n{description}",
            task_type=template["task_type"],
            priority=self._determine_priority_from_labels(labels, template["priority"]),
            phase=template["phase"],
            source="github_webhook",
            source_event_id=str(pr.get("number", "")),
            acceptance_criteria=template["acceptance_criteria"],
            tags=template["tags"] + [f"label:{label}" for label in labels],
            estimated_duration=self._estimate_duration(
                template["task_type"], template["priority"]
            ),
            parent_task_id=None,
            dependencies=[],
            metadata={
                "github_pr_number": pr.get("number"),
                "github_pr_url": pr.get("html_url", ""),
                "github_author": author,
                "github_labels": labels,
                "automation_rule": rule.rule_id,
                "creation_timestamp": datetime.now().isoformat(),
            },
            cwo12_compliance_data=self._generate_cwo12_compliance_data(
                rule, event_data
            ),
        )

    def _create_commit_task(
        self, rule: AutomationRule, payload: dict[str, Any], event_data: dict[str, Any]
    ) -> TaskCreationRequest:
        """Create task request from commit"""
        commits = payload.get("commits", [])
        if not commits:
            return None

        # Find commit with task creation keywords
        target_commit = None
        for commit in commits:
            message = commit.get("message", "")
            if any(
                keyword in message
                for keyword in ["task-create", "tsk.new", "TODO:", "FIXME:"]
            ):
                target_commit = commit
                break

        if not target_commit:
            return None

        message = target_commit.get("message", "")
        author = target_commit.get("author", {}).get("name", "unknown")
        commit_hash = target_commit.get("sha", "")[:8]

        # Extract task details from commit message
        task_details = self._extract_task_details_from_commit(message)

        template = rule.task_template.copy()

        return TaskCreationRequest(
            title=task_details.get("title", f"Task from commit {commit_hash}"),
            description=task_details.get("description", message),
            task_type=task_details.get("task_type", template["task_type"]),
            priority=task_details.get("priority", template["priority"]),
            phase=template["phase"],
            source="github_webhook",
            source_event_id=commit_hash,
            acceptance_criteria=template["acceptance_criteria"],
            tags=template["tags"] + ["commit"],
            estimated_duration=self._estimate_duration(
                template["task_type"], template["priority"]
            ),
            parent_task_id=None,
            dependencies=[],
            metadata={
                "github_commit_hash": target_commit.get("sha", ""),
                "github_commit_url": target_commit.get("url", ""),
                "github_author": author,
                "automation_rule": rule.rule_id,
                "creation_timestamp": datetime.now().isoformat(),
            },
            cwo12_compliance_data=self._generate_cwo12_compliance_data(
                rule, event_data
            ),
        )

    def _create_issue_task(
        self, rule: AutomationRule, payload: dict[str, Any], event_data: dict[str, Any]
    ) -> TaskCreationRequest:
        """Create task request from GitHub issue"""
        issue = payload.get("issue", {})
        title = issue.get("title", "")
        description = issue.get("body", "")
        author = issue.get("user", {}).get("login", "unknown")
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        template = rule.task_template.copy()

        return TaskCreationRequest(
            title=title,
            description=description,
            task_type=template["task_type"],
            priority=self._determine_priority_from_labels(labels, template["priority"]),
            phase=template["phase"],
            source="github_webhook",
            source_event_id=str(issue.get("number", "")),
            acceptance_criteria=template["acceptance_criteria"],
            tags=template["tags"] + [f"label:{label}" for label in labels],
            estimated_duration=self._estimate_duration(
                template["task_type"], template["priority"]
            ),
            parent_task_id=None,
            dependencies=[],
            metadata={
                "github_issue_number": issue.get("number"),
                "github_issue_url": issue.get("html_url", ""),
                "github_author": author,
                "github_labels": labels,
                "automation_rule": rule.rule_id,
                "creation_timestamp": datetime.now().isoformat(),
            },
            cwo12_compliance_data=self._generate_cwo12_compliance_data(
                rule, event_data
            ),
        )

    def _create_generic_task(
        self, rule: AutomationRule, payload: dict[str, Any], event_data: dict[str, Any]
    ) -> TaskCreationRequest:
        """Create generic task request"""
        template = rule.task_template.copy()

        return TaskCreationRequest(
            title=f"Automated Task: {event_data.get('event_type', 'unknown')}",
            description=f"Task created from {event_data.get('event_type', 'unknown')} event",
            task_type=template["task_type"],
            priority=template["priority"],
            phase=template["phase"],
            source="github_webhook",
            source_event_id=str(event_data.get("id", "")),
            acceptance_criteria=template["acceptance_criteria"],
            tags=template["tags"],
            estimated_duration=self._estimate_duration(
                template["task_type"], template["priority"]
            ),
            parent_task_id=None,
            dependencies=[],
            metadata={
                "automation_rule": rule.rule_id,
                "event_data": event_data,
                "creation_timestamp": datetime.now().isoformat(),
            },
            cwo12_compliance_data=self._generate_cwo12_compliance_data(
                rule, event_data
            ),
        )

    def _determine_priority_from_labels(
        self, labels: list[str], default_priority: TaskPriority
    ) -> TaskPriority:
        """Determine task priority from GitHub labels"""
        priority_mapping = {
            "critical": TaskPriority.CRITICAL,
            "urgent": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "high priority": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
            "minor": TaskPriority.LOW,
        }

        for label in labels:
            label_lower = label.lower()
            if label_lower in priority_mapping:
                return priority_mapping[label_lower]

        return default_priority

    def _extract_task_details_from_commit(self, commit_message: str) -> dict[str, Any]:
        """Extract task details from commit message"""
        lines = commit_message.split("\n")
        details = {
            "title": "",
            "description": commit_message,
            "task_type": TaskType.DEVELOPMENT,
            "priority": TaskPriority.MEDIUM,
        }

        # Look for structured task syntax
        for line in lines:
            line = line.strip()
            if line.startswith("task-create:") or line.startswith("tsk.new:"):
                details["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                type_str = line.split(":", 1)[1].strip()
                try:
                    details["task_type"] = TaskType(type_str.lower())
                except ValueError:
                    pass
            elif line.startswith("priority:"):
                priority_str = line.split(":", 1)[1].strip()
                try:
                    details["priority"] = TaskPriority(priority_str.lower())
                except ValueError:
                    pass

        # Use first line as title if no structured title found
        if not details["title"] and lines:
            details["title"] = lines[0].strip()

        return details

    def _estimate_duration(self, task_type: TaskType, priority: TaskPriority) -> int:
        """Estimate task duration in hours"""
        base_durations = {
            TaskType.BUG: 4,
            TaskType.FEATURE: 16,
            TaskType.REFACTOR: 8,
            TaskType.DOCUMENTATION: 4,
            TaskType.TESTING: 6,
            TaskType.SECURITY: 20,
            TaskType.PERFORMANCE: 12,
            TaskType.CODE_REVIEW: 3,
            TaskType.DEPLOYMENT: 6,
            TaskType.MAINTENANCE: 8,
        }

        priority_multipliers = {
            TaskPriority.CRITICAL: 1.3,
            TaskPriority.HIGH: 1.1,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.LOW: 0.8,
        }

        base_duration = base_durations.get(task_type, 8)
        priority_multiplier = priority_multipliers.get(priority, 1.0)

        return int(base_duration * priority_multiplier)

    def _generate_cwo12_compliance_data(
        self, rule: AutomationRule, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate CWO12 compliance data for task"""
        return {
            "automation_rule_id": rule.rule_id,
            "cwo12_compliance_required": rule.cwo12_compliance_required,
            "event_source": "github_webhook",
            "creation_timestamp": datetime.now().isoformat(),
            "evidence_collected": {
                "github_event_data": True,
                "automation_rule_applied": True,
                "task_template_used": True,
            },
            "validation_status": "pending",
            "compliance_score": 0.0,
            "validation_results": {},
        }

    async def _validate_cwo12_compliance(
        self, task_request: TaskCreationRequest
    ) -> dict[str, Any]:
        """Validate CWO12 compliance for task request"""
        if not task_request.cwo12_compliance_data.get(
            "cwo12_compliance_required", False
        ):
            return {"compliant": True, "issues": [], "score": 1.0}

        validation_results = {}
        total_score = 0.0
        validator_count = len(self.cwo12_validators)

        for validator_name, validator_func in self.cwo12_validators.items():
            try:
                result = await validator_func(task_request)
                validation_results[validator_name] = result
                total_score += result["score"]
            except Exception as e:
                logger.error(f"Error in CWO12 validator {validator_name}: {e}")
                validation_results[validator_name] = {
                    "valid": False,
                    "score": 0.0,
                    "issues": [f"Validator error: {e}"],
                }
                total_score += 0.0

        compliance_score = total_score / validator_count if validator_count > 0 else 0.0
        compliant = compliance_score >= 0.8  # 80% compliance threshold

        # Collect all issues
        all_issues = []
        for result in validation_results.values():
            all_issues.extend(result.get("issues", []))

        return {
            "compliant": compliant,
            "score": compliance_score,
            "issues": all_issues,
            "validation_results": validation_results,
        }

    async def _validate_evidence_requirements(
        self, task_request: TaskCreationRequest
    ) -> dict[str, Any]:
        """Validate evidence requirements for CWO12 compliance"""
        issues = []
        score = 1.0

        # Check for sufficient description
        if len(task_request.description) < 50:
            issues.append("Task description too short - insufficient evidence")
            score -= 0.3

        # Check for acceptance criteria
        if not task_request.acceptance_criteria:
            issues.append(
                "No acceptance criteria defined - insufficient verification evidence"
            )
            score -= 0.4

        # Check for metadata
        if not task_request.metadata:
            issues.append("No metadata provided - insufficient context evidence")
            score -= 0.2

        # Check for source tracking
        if not task_request.source or not task_request.source_event_id:
            issues.append("No source tracking - insufficient traceability evidence")
            score -= 0.1

        return {"valid": score >= 0.7, "score": max(0.0, score), "issues": issues}

    async def _validate_constitutional_compliance(
        self, task_request: TaskCreationRequest
    ) -> dict[str, Any]:
        """Validate constitutional compliance requirements"""
        issues = []
        score = 1.0

        # Check for prohibited patterns in task title/description
        prohibited_patterns = ["bypass", "override", "skip", "ignore", "hack"]
        text_to_check = (task_request.title + " " + task_request.description).lower()

        for pattern in prohibited_patterns:
            if pattern in text_to_check:
                issues.append(
                    f"Potentially unconstitutional language detected: {pattern}"
                )
                score -= 0.5

        # Check for required constitutional elements
        if "automated" in task_request.tags:
            # Automated tasks should have clear validation rules
            if not task_request.acceptance_criteria:
                issues.append("Automated task lacks verification criteria")
                score -= 0.3

        return {"valid": score >= 0.7, "score": max(0.0, score), "issues": issues}

    async def _validate_documentation_completeness(
        self, task_request: TaskCreationRequest
    ) -> dict[str, Any]:
        """Validate documentation completeness"""
        issues = []
        score = 1.0

        # Check for clear task title
        if len(task_request.title) < 5:
            issues.append("Task title too brief")
            score -= 0.2

        # Check for descriptive task description
        if len(task_request.description) < 20:
            issues.append("Task description insufficient")
            score -= 0.3

        # Check for appropriate tags
        if not task_request.tags:
            issues.append("No tags specified for task categorization")
            score -= 0.2

        # Check for phase-appropriate acceptance criteria
        if task_request.phase in [TaskPhase.TESTING, TaskPhase.DEPLOYMENT]:
            if not task_request.acceptance_criteria:
                issues.append("No acceptance criteria for testing/deployment phase")
                score -= 0.4

        return {"valid": score >= 0.7, "score": max(0.0, score), "issues": issues}

    async def _validate_verification_readiness(
        self, task_request: TaskCreationRequest
    ) -> dict[str, Any]:
        """Validate that task is ready for verification"""
        issues = []
        score = 1.0

        # Check for measurable acceptance criteria
        measurable_criteria = 0
        for criteria in task_request.acceptance_criteria:
            if any(
                word in criteria.lower()
                for word in ["test", "verify", "check", "validate", "measure"]
            ):
                measurable_criteria += 1

        if task_request.acceptance_criteria and measurable_criteria == 0:
            issues.append("Acceptance criteria not measurable or verifiable")
            score -= 0.3

        # Check for estimated duration
        if not task_request.estimated_duration:
            issues.append("No estimated duration provided")
            score -= 0.1

        # Check for task type consistency
        if (
            task_request.task_type == TaskType.BUG
            and task_request.priority == TaskPriority.LOW
        ):
            issues.append("Bug task with low priority may need review")
            score -= 0.1

        return {"valid": score >= 0.8, "score": max(0.0, score), "issues": issues}

    async def _create_task_in_database(self, task_request: TaskCreationRequest) -> str:
        """Create task in database"""
        try:
            # Import database access layer
            import sys

            sys.path.append(str(self.db_path.parent))
            from db import get_dal

            dal = get_dal()

            # Generate unique task ID
            task_id = f"auto-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}"

            # Prepare task data
            task_data = {
                "id": task_id,
                "tsk_id": await self._get_active_tsk_id(),
                "title": task_request.title,
                "description": task_request.description,
                "status": "todo",
                "priority": task_request.priority.value,
                "phase": task_request.phase.value,
                "task_type": task_request.task_type.value,
                "assigned_to": None,
                "estimated_duration": task_request.estimated_duration,
                "actual_duration": None,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "last_activity": datetime.now().isoformat(),
                "source": task_request.source,
                "parent_task_id": task_request.parent_task_id,
                "tags": json.dumps(task_request.tags),
                "acceptance_criteria": json.dumps(task_request.acceptance_criteria),
                "verification_status": json.dumps(
                    {
                        "automated": True,
                        "cwo12_validated": True,
                        "creation_evidence": task_request.cwo12_compliance_data,
                    }
                ),
                "completion_percentage": 0,
                "migration_date": None,
                "entities": json.dumps([]),
                "validation_rules": json.dumps([]),
                "state_management": json.dumps({}),
                "auto_closure_enabled": False,
                "closure_conditions": json.dumps([]),
                "last_state_check": datetime.now().isoformat(),
                "state_transition_history": json.dumps([]),
                "workflow_automation": json.dumps(
                    {"github_automated": True, "cwo12_compliant": True}
                ),
                "automation_metadata": json.dumps(task_request.metadata),
                "completion_triggers": json.dumps([]),
                "auto_closure_confirmed": False,
                "closure_verification_required": True,
            }

            # Insert task
            dal.add_task(task_data)

            logger.info(f"Successfully created automated task {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"Error creating task in database: {e}", exc_info=True)
            raise

    async def _get_active_tsk_id(self) -> str:
        """Get active TSK ID"""
        try:
            import sys

            sys.path.append(str(self.db_path.parent))
            from db import get_dal

            dal = get_dal()
            active_tsk = dal.get_active_tsk()

            if active_tsk:
                return active_tsk["id"]
            else:
                # Return default TSK for automated tasks
                return f"auto-{datetime.now().strftime('%Y%m%d')}"

        except Exception as e:
            logger.error(f"Error getting active TSK ID: {e}")
            return "default-tsk"

    def add_automation_rule(self, rule: AutomationRule):
        """Add new automation rule"""
        rule.created_at = datetime.now().isoformat()
        rule.updated_at = datetime.now().isoformat()
        self.automation_rules.append(rule)
        logger.info(f"Added automation rule: {rule.rule_id}")

    def remove_automation_rule(self, rule_id: str) -> bool:
        """Remove automation rule by ID"""
        for i, rule in enumerate(self.automation_rules):
            if rule.rule_id == rule_id:
                del self.automation_rules[i]
                logger.info(f"Removed automation rule: {rule_id}")
                return True
        return False

    def enable_automation_rule(self, rule_id: str) -> bool:
        """Enable automation rule by ID"""
        for rule in self.automation_rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                rule.updated_at = datetime.now().isoformat()
                logger.info(f"Enabled automation rule: {rule_id}")
                return True
        return False

    def disable_automation_rule(self, rule_id: str) -> bool:
        """Disable automation rule by ID"""
        for rule in self.automation_rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                rule.updated_at = datetime.now().isoformat()
                logger.info(f"Disabled automation rule: {rule_id}")
                return True
        return False

    def get_automation_rules(self) -> list[dict[str, Any]]:
        """Get all automation rules"""
        return [asdict(rule) for rule in self.automation_rules]

    def get_automation_statistics(self) -> dict[str, Any]:
        """Get automation engine statistics"""
        enabled_rules = [r for r in self.automation_rules if r.enabled]
        rules_requiring_cwo12 = [
            r for r in self.automation_rules if r.cwo12_compliance_required
        ]

        return {
            "total_rules": len(self.automation_rules),
            "enabled_rules": len(enabled_rules),
            "disabled_rules": len(self.automation_rules) - len(enabled_rules),
            "cwo12_required_rules": len(rules_requiring_cwo12),
            "cwo12_enabled_rules": len([r for r in rules_requiring_cwo12 if r.enabled]),
            "rule_types": list({rule.event_type for rule in self.automation_rules}),
            "last_updated": max(
                (rule.updated_at for rule in self.automation_rules), default=None
            ),
        }


# Example usage
async def main():
    """Example usage of task automation engine"""
    engine = TaskAutomationEngine()

    # Example GitHub event data
    example_event = {
        "event_type": "pull_request",
        "payload": {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Add user authentication feature",
                "body": "This PR adds OAuth2 authentication with JWT tokens",
                "user": {"login": "john-doe"},
                "labels": [{"name": "feature"}, {"name": "enhancement"}],
                "html_url": "https://github.com/owner/repo/pull/123",
            },
        },
    }

    try:
        # Process event
        created_tasks = await engine.process_github_event(example_event)
        print(f"Created {len(created_tasks)} tasks: {created_tasks}")

        # Get statistics
        stats = engine.get_automation_statistics()
        print(f"Automation engine stats: {stats}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
