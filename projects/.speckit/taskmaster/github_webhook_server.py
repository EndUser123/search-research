#!/usr/bin/env python3
"""
GitHub Webhook Server for TaskMaster Integration
Handles GitHub events and converts them to automated task creation
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, web

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class GitHubEvent:
    """GitHub webhook event data structure"""

    event_type: str
    action: str | None
    payload: dict[str, Any]
    repository: dict[str, Any]
    sender: dict[str, Any]
    timestamp: str

    @property
    def repo_name(self) -> str:
        return self.repository.get("full_name", "unknown")

    @property
    def repo_url(self) -> str:
        return self.repository.get("html_url", "")

    @property
    def branch(self) -> str:
        """Extract branch name from event payload"""
        if self.event_type == "push":
            return self.payload.get("ref", "").replace("refs/heads/", "")
        elif self.event_type == "pull_request":
            return self.payload.get("pull_request", {}).get("head", {}).get("ref", "")
        return "unknown"


@dataclass
class TaskCreationRequest:
    """Request structure for automated task creation"""

    title: str
    description: str
    task_type: str
    priority: str
    phase: str
    source: str
    metadata: dict[str, Any]
    acceptance_criteria: list[str]
    tags: list[str]
    estimated_duration: int | None = None
    parent_task_id: str | None = None


class GitHubWebhookServer:
    """Main webhook server for GitHub integration"""

    def __init__(
        self,
        webhook_secret: str,
        github_token: str,
        db_path: Path = Path("P:/.speckit/taskmaster/tasks.db"),
        host: str = "localhost",
        port: int = 8080,
    ):
        self.webhook_secret = webhook_secret
        self.github_token = github_token
        self.db_path = db_path
        self.host = host
        self.port = port
        self.app = web.Application()
        self.session: ClientSession | None = None

        # Rate limiting
        self.rate_limits = {}
        self.request_timestamps = []

        # Event handlers
        self.event_handlers = {
            "pull_request": self.handle_pull_request,
            "push": self.handle_push,
            "issues": self.handle_issues,
            "issue_comment": self.handle_issue_comment,
        }

        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_post("/webhook/github", self.handle_webhook)
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/status", self.status_check)

    async def start(self):
        """Start the webhook server"""
        self.session = ClientSession()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"GitHub webhook server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the webhook server"""
        if self.session:
            await self.session.close()
        logger.info("GitHub webhook server stopped")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not signature:
            logger.warning("No signature provided")
            return False

        try:
            expected_signature = (
                "sha256="
                + hmac.new(
                    self.webhook_secret.encode("utf-8"), payload, hashlib.sha256
                ).hexdigest()
            )

            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    def check_rate_limit(
        self, repo_name: str, max_requests: int = 100, window_minutes: int = 5
    ) -> bool:
        """Check if repository has exceeded rate limit"""
        now = time.time()
        window_start = now - (window_minutes * 60)

        # Clean old timestamps
        self.request_timestamps = [
            t for t in self.request_timestamps if t > window_start
        ]

        # Count requests in current window
        recent_requests = len([t for t in self.request_timestamps if t > window_start])

        if recent_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for {repo_name}")
            return False

        self.request_timestamps.append(now)
        return True

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Main webhook handler"""
        try:
            # Extract signature
            signature = request.headers.get("X-Hub-Signature-256", "")
            event_type = request.headers.get("X-GitHub-Event", "")

            # Verify signature
            payload = await request.read()
            if not self.verify_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return web.Response(status=401, text="Invalid signature")

            # Parse payload
            try:
                payload_data = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                return web.Response(status=400, text="Invalid JSON")

            # Create event object
            event = GitHubEvent(
                event_type=event_type,
                action=payload_data.get("action"),
                payload=payload_data,
                repository=payload_data.get("repository", {}),
                sender=payload_data.get("sender", {}),
                timestamp=datetime.now().isoformat(),
            )

            # Check rate limiting
            if not self.check_rate_limit(event.repo_name):
                return web.Response(status=429, text="Rate limit exceeded")

            # Route to appropriate handler
            handler = self.event_handlers.get(event_type)
            if handler:
                await handler(event)
                return web.Response(status=200, text="Event processed")
            else:
                logger.info(f"No handler for event type: {event_type}")
                return web.Response(status=200, text="Event received but not processed")

        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return web.Response(status=500, text="Internal server error")

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.Response(status=200, text="OK")

    async def status_check(self, request: web.Request) -> web.Response:
        """Detailed status check"""
        status = {
            "server": "running",
            "timestamp": datetime.now().isoformat(),
            "rate_limit_current": len(self.request_timestamps),
            "handlers": list(self.event_handlers.keys()),
        }
        return web.Response(status=200, text=json.dumps(status))

    async def handle_pull_request(self, event: GitHubEvent):
        """Handle pull request events"""
        action = event.action
        pr = event.payload.get("pull_request", {})

        if action in ["opened", "ready_for_review", "reopened"]:
            await self.process_pr_for_task_creation(event, pr)
        elif action in ["closed", "merged"]:
            await self.process_pr_closure(event, pr)

    async def handle_push(self, event: GitHubEvent):
        """Handle push events"""
        commits = event.payload.get("commits", [])
        branch = event.branch

        for commit in commits:
            await self.process_commit_for_task_creation(event, commit, branch)
            await self.link_commit_to_existing_tasks(event, commit)

    async def handle_issues(self, event: GitHubEvent):
        """Handle issue events"""
        action = event.action
        issue = event.payload.get("issue", {})

        if action == "opened":
            await self.process_issue_for_task_creation(event, issue)

    async def handle_issue_comment(self, event: GitHubEvent):
        """Handle issue comment events for task triggers"""
        comment = event.payload.get("comment", {})
        issue = event.payload.get("issue", {})

        # Check for task creation keywords
        if self.contains_task_trigger(comment.get("body", "")):
            await self.process_comment_for_task_creation(event, issue, comment)

    def contains_task_trigger(self, text: str) -> bool:
        """Check if text contains task creation triggers"""
        triggers = [
            "/task-create",
            "/tsk.new",
            "/add-task",
            "create task",
            "add task",
            "new task",
            "TODO:",
            "TASK:",
            "FIXME:",
        ]
        return any(trigger.lower() in text.lower() for trigger in triggers)

    async def process_pr_for_task_creation(
        self, event: GitHubEvent, pr: dict[str, Any]
    ):
        """Process pull request for automated task creation"""
        try:
            # Extract task information from PR
            title = pr.get("title", "")
            description = pr.get("body", "")
            author = pr.get("user", {}).get("login", "github-user")

            # Analyze PR for task implications
            task_request = await self.analyze_pr_for_task(pr, event)

            if task_request:
                # Create task in database
                task_id = await self.create_task_from_request(task_request, event)
                logger.info(f"Created task {task_id} from PR {pr.get('number')}")

                # Add comment to PR about task creation
                await self.add_pr_comment(pr, f"🤖 Automated task created: #{task_id}")

        except Exception as e:
            logger.error(f"Error processing PR for task creation: {e}", exc_info=True)

    async def analyze_pr_for_task(
        self, pr: dict[str, Any], event: GitHubEvent
    ) -> TaskCreationRequest | None:
        """Analyze PR and generate task creation request"""
        title = pr.get("title", "")
        description = pr.get("body", "")
        labels = [label.get("name", "") for label in pr.get("labels", [])]

        # Determine task type based on PR content
        task_type = self.determine_task_type(title, description, labels)

        # Determine priority based on labels and content
        priority = self.determine_priority(labels, title, description)

        # Extract acceptance criteria from PR description
        acceptance_criteria = self.extract_acceptance_criteria(description)

        # Generate tags
        tags = ["github", "pr", "automated"] + [f"label:{label}" for label in labels]

        # Determine phase based on PR content
        phase = self.determine_phase(title, description, labels)

        metadata = {
            "github_pr_number": pr.get("number"),
            "github_pr_url": pr.get("html_url", ""),
            "github_author": pr.get("user", {}).get("login", ""),
            "github_repo": event.repo_name,
            "github_branch": event.branch,
            "github_labels": labels,
            "creation_source": "github_pr",
            "original_title": title,
            "original_description": description,
        }

        return TaskCreationRequest(
            title=f"PR Review: {title}",
            description=f"Automated task created from GitHub PR:\n\n{description}",
            task_type=task_type,
            priority=priority,
            phase=phase,
            source="github_webhook",
            metadata=metadata,
            acceptance_criteria=acceptance_criteria,
            tags=tags,
            estimated_duration=self.estimate_duration(task_type, priority, description),
        )

    def determine_task_type(
        self, title: str, description: str, labels: list[str]
    ) -> str:
        """Determine task type from PR content"""
        text = (title + " " + description).lower()

        type_mapping = {
            "bug": ["bug", "fix", "error", "issue", "problem"],
            "feature": ["feature", "enhancement", "new", "add"],
            "refactor": ["refactor", "cleanup", "improve", "optimize"],
            "documentation": ["docs", "documentation", "readme", "guide"],
            "testing": ["test", "testing", "coverage", "spec"],
            "ci/cd": ["ci", "cd", "deploy", "pipeline", "workflow"],
            "security": ["security", "vulnerability", "auth", "permission"],
            "performance": ["performance", "speed", "latency", "optimization"],
        }

        # Check labels first
        for label in labels:
            label_lower = label.lower()
            for task_type, keywords in type_mapping.items():
                if any(keyword in label_lower for keyword in keywords):
                    return task_type

        # Then check title and description
        for task_type, keywords in type_mapping.items():
            if any(keyword in text for keyword in keywords):
                return task_type

        return "development"  # default

    def determine_priority(
        self, labels: list[str], title: str, description: str
    ) -> str:
        """Determine task priority from content"""
        # Check labels for priority indicators
        priority_labels = {
            "critical": ["critical", "urgent", "blocker", "high-priority"],
            "high": ["high", "important", "priority"],
            "medium": ["medium", "normal"],
            "low": ["low", "minor", "nice-to-have"],
        }

        for label in labels:
            label_lower = label.lower()
            for priority, keywords in priority_labels.items():
                if any(keyword in label_lower for keyword in keywords):
                    return priority

        # Check title for urgency indicators
        text = (title + " " + description).lower()
        urgency_indicators = {
            "critical": ["critical", "urgent", "asap", "emergency", "security"],
            "high": ["important", "high priority", "soon", "breaks"],
            "low": ["minor", "nice to have", "later", "eventually"],
        }

        for priority, keywords in urgency_indicators.items():
            if any(keyword in text for keyword in keywords):
                return priority

        return "medium"  # default

    def determine_phase(self, title: str, description: str, labels: list[str]) -> str:
        """Determine task phase from content"""
        text = (title + " " + description).lower()

        phase_mapping = {
            "planning": ["plan", "design", "spec", "requirement"],
            "development": ["implement", "develop", "code", "build"],
            "testing": ["test", "qa", "verify", "validate"],
            "deployment": ["deploy", "release", "publish", "ship"],
            "maintenance": ["maintain", "update", "fix", "patch"],
        }

        # Check labels
        for label in labels:
            label_lower = label.lower()
            for phase, keywords in phase_mapping.items():
                if any(keyword in label_lower for keyword in keywords):
                    return phase

        # Check text
        for phase, keywords in phase_mapping.items():
            if any(keyword in text for keyword in keywords):
                return phase

        return "development"  # default

    def extract_acceptance_criteria(self, description: str) -> list[str]:
        """Extract acceptance criteria from PR description"""
        criteria = []

        # Look for common acceptance criteria patterns
        patterns = [
            r"(?i)acceptance criteria:?\s*\n?(.*?)(?:\n\n|\Z)",
            r"(?i)criteria:?\s*\n?(.*?)(?:\n\n|\Z)",
            r"(?i)requirements:?\s*\n?(.*?)(?:\n\n|\Z)",
            r"(?i)checklist:?\s*\n?(.*?)(?:\n\n|\Z)",
        ]

        # Simple extraction - look for bullet points or numbered lists
        lines = description.split("\n")
        in_criteria_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if we're entering a criteria section
            if any(
                keyword in line.lower()
                for keyword in [
                    "acceptance criteria:",
                    "criteria:",
                    "requirements:",
                    "checklist:",
                ]
            ):
                in_criteria_section = True
                continue

            # Extract bullet points or numbered items in criteria section
            if in_criteria_section and (
                line.startswith("-")
                or line.startswith("*")
                or (line[0].isdigit() and "." in line)
            ):
                criteria.append(line.lstrip("-* ").strip())
            elif (
                in_criteria_section
                and not line.startswith("-")
                and not line.startswith("*")
                and not (line[0].isdigit() and "." in line)
            ):
                # End of criteria section
                in_criteria_section = False

        return criteria

    def estimate_duration(
        self, task_type: str, priority: str, description: str
    ) -> int | None:
        """Estimate task duration in hours based on type, priority, and complexity"""
        base_durations = {
            "bug": {"low": 2, "medium": 4, "high": 8, "critical": 16},
            "feature": {"low": 8, "medium": 16, "high": 32, "critical": 64},
            "refactor": {"low": 4, "medium": 8, "high": 16, "critical": 32},
            "documentation": {"low": 2, "medium": 4, "high": 8, "critical": 16},
            "testing": {"low": 4, "medium": 8, "high": 16, "critical": 32},
            "ci/cd": {"low": 4, "medium": 8, "high": 16, "critical": 24},
            "security": {"low": 8, "medium": 16, "high": 32, "critical": 48},
            "performance": {"low": 8, "medium": 16, "high": 32, "critical": 64},
            "development": {"low": 4, "medium": 8, "high": 16, "critical": 32},
        }

        base_duration = base_durations.get(task_type, {}).get(priority, 8)

        # Adjust based on description complexity
        complexity_factor = 1.0
        desc_length = len(description)
        if desc_length > 2000:
            complexity_factor = 1.5
        elif desc_length > 1000:
            complexity_factor = 1.2

        return int(base_duration * complexity_factor)

    async def create_task_from_request(
        self, request: TaskCreationRequest, event: GitHubEvent
    ) -> str:
        """Create task in database from request"""
        try:
            # Import database access layer
            import sys

            sys.path.append(str(Path(__file__).parent))
            from db import get_dal

            dal = get_dal()

            # Generate unique task ID
            task_id = f"gh-{int(time.time())}-{hash(request.title) % 10000:04d}"

            # Prepare task data
            task_data = {
                "id": task_id,
                "tsk_id": await self.get_active_tsk_id(),
                "title": request.title,
                "description": request.description,
                "status": "todo",
                "priority": request.priority,
                "phase": request.phase,
                "task_type": request.task_type,
                "assigned_to": None,
                "estimated_duration": request.estimated_duration,
                "actual_duration": None,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "last_activity": datetime.now().isoformat(),
                "source": request.source,
                "parent_task_id": request.parent_task_id,
                "tags": json.dumps(request.tags),
                "acceptance_criteria": json.dumps(request.acceptance_criteria),
                "verification_status": json.dumps(
                    {
                        "github_created": True,
                        "cwo12_validated": False,
                        "automated": True,
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
                    {"github_linked": True, "auto_update": True}
                ),
                "automation_metadata": json.dumps(request.metadata),
                "completion_triggers": json.dumps([]),
                "auto_closure_confirmed": False,
                "closure_verification_required": True,
            }

            # Insert task
            dal.add_task(task_data)

            logger.info(f"Created task {task_id} from GitHub event")
            return task_id

        except Exception as e:
            logger.error(f"Error creating task from request: {e}", exc_info=True)
            raise

    async def get_active_tsk_id(self) -> str:
        """Get active TSK ID or create a default one"""
        try:
            import sys

            sys.path.append(str(Path(__file__).parent))
            from db import get_dal

            dal = get_dal()
            active_tsk = dal.get_active_tsk()

            if active_tsk:
                return active_tsk["id"]
            else:
                # Create a default TSK for GitHub tasks
                tsk_id = f"gh-{datetime.now().strftime('%Y%m%d')}"
                # Note: TSK creation would need to be implemented
                logger.warning("No active TSK found, using default")
                return tsk_id

        except Exception as e:
            logger.error(f"Error getting active TSK ID: {e}")
            return "default-tsk"

    async def add_pr_comment(self, pr: dict[str, Any], message: str):
        """Add comment to GitHub PR"""
        try:
            if not self.session:
                return

            comments_url = pr.get("comments_url")
            if not comments_url:
                return

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            payload = {"body": message}

            async with self.session.post(
                comments_url, headers=headers, json=payload
            ) as response:
                if response.status == 201:
                    logger.info(f"Added comment to PR #{pr.get('number')}")
                else:
                    logger.warning(f"Failed to add PR comment: {response.status}")

        except Exception as e:
            logger.error(f"Error adding PR comment: {e}")

    async def process_pr_closure(self, event: GitHubEvent, pr: dict[str, Any]):
        """Process PR closure for task completion"""
        try:
            # Find tasks linked to this PR
            pr_number = pr.get("number")
            repo_name = event.repo_name

            # Update related tasks
            await self.update_tasks_for_pr_closure(
                pr_number, repo_name, pr.get("merged", False)
            )

        except Exception as e:
            logger.error(f"Error processing PR closure: {e}", exc_info=True)

    async def process_commit_for_task_creation(
        self, event: GitHubEvent, commit: dict[str, Any], branch: str
    ):
        """Process commit for task creation"""
        try:
            message = commit.get("message", "")
            author = commit.get("author", {}).get("name", "unknown")

            # Check if commit contains task creation keywords
            if self.contains_task_trigger(message):
                task_request = await self.analyze_commit_for_task(commit, event, branch)
                if task_request:
                    task_id = await self.create_task_from_request(task_request, event)
                    logger.info(
                        f"Created task {task_id} from commit {commit.get('id', '')[:8]}"
                    )

        except Exception as e:
            logger.error(
                f"Error processing commit for task creation: {e}", exc_info=True
            )

    async def analyze_commit_for_task(
        self, commit: dict[str, Any], event: GitHubEvent, branch: str
    ) -> TaskCreationRequest | None:
        """Analyze commit and generate task creation request"""
        message = commit.get("message", "")
        author = commit.get("author", {}).get("name", "unknown")
        commit_hash = commit.get("id", "")[:8]

        # Extract task information from commit message
        lines = message.split("\n")
        title = lines[0] if lines else message
        description = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # Determine task characteristics
        task_type = self.determine_task_type(title, description, [])
        priority = self.determine_priority([], title, description)
        phase = self.determine_phase(title, description, [])

        metadata = {
            "github_commit_hash": commit.get("id", ""),
            "github_commit_url": commit.get("url", ""),
            "github_author": author,
            "github_repo": event.repo_name,
            "github_branch": branch,
            "creation_source": "github_commit",
            "original_message": message,
        }

        return TaskCreationRequest(
            title=f"Commit Task: {title}",
            description=f"Automated task created from commit:\n\n{description or message}",
            task_type=task_type,
            priority=priority,
            phase=phase,
            source="github_webhook",
            metadata=metadata,
            acceptance_criteria=[],
            tags=["github", "commit", "automated"],
            estimated_duration=4,  # Default for commit tasks
        )

    async def link_commit_to_existing_tasks(
        self, event: GitHubEvent, commit: dict[str, Any]
    ):
        """Link commit to existing tasks for evidence collection"""
        try:
            # This would link commits to existing tasks
            # Implementation would depend on specific linking requirements
            pass
        except Exception as e:
            logger.error(f"Error linking commit to tasks: {e}", exc_info=True)

    async def process_issue_for_task_creation(
        self, event: GitHubEvent, issue: dict[str, Any]
    ):
        """Process GitHub issue for task creation"""
        try:
            title = issue.get("title", "")
            description = issue.get("body", "")
            labels = [label.get("name", "") for label in issue.get("labels", [])]

            task_request = await self.analyze_issue_for_task(issue, event)
            if task_request:
                task_id = await self.create_task_from_request(task_request, event)
                logger.info(f"Created task {task_id} from issue #{issue.get('number')}")

        except Exception as e:
            logger.error(
                f"Error processing issue for task creation: {e}", exc_info=True
            )

    async def analyze_issue_for_task(
        self, issue: dict[str, Any], event: GitHubEvent
    ) -> TaskCreationRequest | None:
        """Analyze GitHub issue and generate task creation request"""
        title = issue.get("title", "")
        description = issue.get("body", "")
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        task_type = self.determine_task_type(title, description, labels)
        priority = self.determine_priority(labels, title, description)
        phase = "planning"  # Issues are typically planning phase

        metadata = {
            "github_issue_number": issue.get("number"),
            "github_issue_url": issue.get("html_url", ""),
            "github_author": issue.get("user", {}).get("login", ""),
            "github_repo": event.repo_name,
            "github_labels": labels,
            "creation_source": "github_issue",
            "original_title": title,
            "original_description": description,
        }

        return TaskCreationRequest(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            phase=phase,
            source="github_webhook",
            metadata=metadata,
            acceptance_criteria=self.extract_acceptance_criteria(description),
            tags=["github", "issue", "automated"]
            + [f"label:{label}" for label in labels],
            estimated_duration=self.estimate_duration(task_type, priority, description),
        )

    async def process_comment_for_task_creation(
        self, event: GitHubEvent, issue: dict[str, Any], comment: dict[str, Any]
    ):
        """Process issue comment for task creation"""
        try:
            comment_body = comment.get("body", "")
            author = comment.get("user", {}).get("login", "unknown")

            # Extract task details from comment
            task_request = await self.analyze_comment_for_task(comment, issue, event)
            if task_request:
                task_id = await self.create_task_from_request(task_request, event)
                logger.info(f"Created task {task_id} from comment by {author}")

        except Exception as e:
            logger.error(
                f"Error processing comment for task creation: {e}", exc_info=True
            )

    async def analyze_comment_for_task(
        self, comment: dict[str, Any], issue: dict[str, Any], event: GitHubEvent
    ) -> TaskCreationRequest | None:
        """Analyze issue comment and generate task creation request"""
        comment_body = comment.get("body", "")
        issue_title = issue.get("title", "")

        # Extract task details from comment
        task_details = self.extract_task_details_from_comment(comment_body)

        metadata = {
            "github_issue_number": issue.get("number"),
            "github_issue_url": issue.get("html_url", ""),
            "github_comment_id": comment.get("id"),
            "github_author": comment.get("user", {}).get("login", ""),
            "github_repo": event.repo_name,
            "creation_source": "github_comment",
            "original_comment": comment_body,
        }

        return TaskCreationRequest(
            title=task_details.get(
                "title", f"Task from comment on #{issue.get('number')}"
            ),
            description=task_details.get("description", comment_body),
            task_type=task_details.get("type", "development"),
            priority=task_details.get("priority", "medium"),
            phase=task_details.get("phase", "development"),
            source="github_webhook",
            metadata=metadata,
            acceptance_criteria=task_details.get("acceptance_criteria", []),
            tags=["github", "comment", "automated"],
            estimated_duration=task_details.get("duration", 8),
        )

    def extract_task_details_from_comment(self, comment_body: str) -> dict[str, Any]:
        """Extract structured task details from comment"""
        details = {
            "title": "",
            "description": comment_body,
            "type": "development",
            "priority": "medium",
            "phase": "development",
            "acceptance_criteria": [],
            "duration": 8,
        }

        lines = comment_body.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for structured task syntax
            if line.lower().startswith("title:"):
                details["title"] = line[6:].strip()
            elif line.lower().startswith("type:"):
                details["type"] = line[5:].strip()
            elif line.lower().startswith("priority:"):
                details["priority"] = line[9:].strip()
            elif line.lower().startswith("phase:"):
                details["phase"] = line[6:].strip()
            elif line.lower().startswith("duration:"):
                try:
                    details["duration"] = int(line[9:].strip())
                except ValueError:
                    pass
            elif line.lower().startswith("acceptance criteria:"):
                current_section = "acceptance_criteria"
            elif current_section == "acceptance_criteria" and (
                line.startswith("-") or line.startswith("*")
            ):
                details["acceptance_criteria"].append(line.lstrip("-* ").strip())
            elif (
                current_section
                and not line.startswith("-")
                and not line.startswith("*")
            ):
                current_section = None

        # Use first line as title if no explicit title
        if not details["title"] and lines:
            details["title"] = lines[0].strip()

        return details

    async def update_tasks_for_pr_closure(
        self, pr_number: int, repo_name: str, merged: bool
    ):
        """Update tasks when PR is closed"""
        try:
            # This would update task status based on PR closure
            # Implementation would query for tasks linked to this PR and update their status
            status = "completed" if merged else "cancelled"
            logger.info(
                f"Updating tasks for PR #{pr_number} closure (merged: {merged})"
            )

        except Exception as e:
            logger.error(f"Error updating tasks for PR closure: {e}", exc_info=True)


# Main execution
async def main():
    """Main execution function"""
    import os

    # Configuration
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "your-secret-key")
    github_token = os.getenv("GITHUB_TOKEN", "your-github-token")

    server = GitHubWebhookServer(
        webhook_secret=webhook_secret, github_token=github_token
    )

    try:
        await server.start()
        logger.info("GitHub webhook server is running...")

        # Keep server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
