#!/usr/bin/env python3
"""
Main GitHub Integration Orchestrator for TaskMaster
Coordinates all components of the GitHub webhook integration system
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from commit_analyzer import CommitAnalyzer
from error_handling_retry import ErrorHandlingRetryManager
from github_webhook_server import GitHubWebhookServer
from pr_analysis_engine import PRAnalysisEngine
from task_automation_engine import (
    TaskAutomationEngine,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("P:/.speckit/taskmaster/github_integration.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class GitHubIntegrationOrchestrator:
    """Main orchestrator for GitHub integration components"""

    def __init__(self):
        # Configuration
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "your-secret-key")
        self.github_token = os.getenv("GITHUB_TOKEN", "your-github-token")
        self.db_path = Path("P:/.speckit/taskmaster/tasks.db")
        self.host = os.getenv("WEBHOOK_HOST", "localhost")
        self.port = int(os.getenv("WEBHOOK_PORT", "8080"))

        # Initialize components
        self.error_manager = ErrorHandlingRetryManager(self.db_path)
        self.webhook_server = None
        self.pr_analyzer = None
        self.commit_analyzer = None
        self.automation_engine = None

        # Statistics
        self.stats = {
            "start_time": None,
            "events_processed": 0,
            "tasks_created": 0,
            "errors_handled": 0,
            "last_activity": None,
        }

    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing GitHub Integration Orchestrator")

            # Initialize webhook server
            self.webhook_server = GitHubWebhookServer(
                webhook_secret=self.webhook_secret,
                github_token=self.github_token,
                db_path=self.db_path,
                host=self.host,
                port=self.port,
            )

            # Initialize analyzers
            self.pr_analyzer = PRAnalysisEngine(self.github_token)
            self.commit_analyzer = CommitAnalyzer(self.github_token)

            # Initialize automation engine
            self.automation_engine = TaskAutomationEngine(self.db_path)

            # Update webhook server to use orchestrator for event processing
            self._update_webhook_server_handlers()

            self.stats["start_time"] = asyncio.get_event_loop().time()

            logger.info("GitHub Integration Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            raise

    def _update_webhook_server_handlers(self):
        """Update webhook server event handlers to use orchestrator"""
        # Replace the webhook server's event handlers with orchestrator methods
        original_handlers = self.webhook_server.event_handlers

        async def enhanced_pr_handler(event):
            """Enhanced PR handler with orchestrator coordination"""
            await self.process_pull_request_event(event)

        async def enhanced_push_handler(event):
            """Enhanced push handler with orchestrator coordination"""
            await self.process_push_event(event)

        async def enhanced_issues_handler(event):
            """Enhanced issues handler with orchestrator coordination"""
            await self.process_issues_event(event)

        async def enhanced_comment_handler(event):
            """Enhanced comment handler with orchestrator coordination"""
            await self.process_comment_event(event)

        # Update handlers
        self.webhook_server.event_handlers.update(
            {
                "pull_request": enhanced_pr_handler,
                "push": enhanced_push_handler,
                "issues": enhanced_issues_handler,
                "issue_comment": enhanced_comment_handler,
            }
        )

    async def start(self):
        """Start the integration system"""
        try:
            await self.initialize()

            # Start webhook server
            await self.webhook_server.start()

            logger.info(
                f"GitHub Integration started successfully on {self.host}:{self.port}"
            )
            logger.info(
                f"Webhook endpoint: http://{self.host}:{self.port}/webhook/github"
            )
            logger.info(
                f"Health check: http://{self.host}:{self.port}/health"
            )
            logger.info(
                f"Status check: http://{self.host}:{self.port}/status"
            )

            # Keep the service running
            await self._run_service_loop()

        except Exception as e:
            logger.error(f"Failed to start integration: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the integration system"""
        try:
            logger.info("Stopping GitHub Integration Orchestrator")

            # Stop components
            if self.webhook_server:
                await self.webhook_server.stop()

            if self.pr_analyzer:
                await self.pr_analyzer.close()

            if self.commit_analyzer:
                await self.commit_analyzer.close()

            # Generate final report
            await self._generate_final_report()

            logger.info("GitHub Integration Orchestrator stopped")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

    async def _run_service_loop(self):
        """Main service loop"""
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute

                # Perform periodic maintenance
                await self._perform_maintenance()

                # Log statistics periodically
                if (
                    self.stats["events_processed"] > 0
                    and self.stats["events_processed"] % 100 == 0
                ):
                    await self._log_statistics()

        except asyncio.CancelledError:
            logger.info("Service loop cancelled")
        except Exception as e:
            logger.error(f"Error in service loop: {e}", exc_info=True)

    async def process_pull_request_event(self, event):
        """Process pull request events with full integration"""
        try:
            self.stats["events_processed"] += 1
            self.stats["last_activity"] = asyncio.get_event_loop().time()

            logger.info(
                f"Processing PR event: {event.action} for #{event.payload.get('pull_request', {}).get('number', 'unknown')}"
            )

            # Analyze PR with comprehensive engine
            pr_analysis = await self.error_manager.execute_with_retry(
                self.pr_analyzer.analyze_pr,
                "github_api",
                event.payload.get("pull_request", {}),
                event.repo_name,
            )

            if pr_analysis:
                logger.info(
                    f"PR analysis completed: {len(pr_analysis.task_suggestions)} task suggestions"
                )

                # Convert analysis results to task creation requests
                event_data = {
                    "event_type": "pull_request",
                    "payload": event.payload,
                    "analysis_result": pr_analysis,
                }

                # Process through automation engine
                created_tasks = await self.error_manager.execute_with_retry(
                    self.automation_engine.process_github_event,
                    "task_creation",
                    event_data,
                )

                self.stats["tasks_created"] += len(created_tasks)
                logger.info(f"Created {len(created_tasks)} tasks from PR analysis")

        except Exception as e:
            self.stats["errors_handled"] += 1
            logger.error(f"Error processing PR event: {e}", exc_info=True)

    async def process_push_event(self, event):
        """Process push events with commit analysis"""
        try:
            self.stats["events_processed"] += 1
            self.stats["last_activity"] = asyncio.get_event_loop().time()

            commits = event.payload.get("commits", [])
            logger.info(f"Processing push event with {len(commits)} commits")

            for commit in commits:
                # Analyze commit for task creation and linking
                commit_analysis = await self.error_manager.execute_with_retry(
                    self.commit_analyzer.analyze_commit,
                    "github_api",
                    commit,
                    event.repo_name,
                )

                if commit_analysis:
                    # Create tasks from commit analysis
                    for task_request in commit_analysis.task_creation_requests:
                        event_data = {
                            "event_type": "push",
                            "payload": event.payload,
                            "task_request": task_request,
                            "commit_analysis": commit_analysis,
                        }

                        try:
                            created_tasks = await self.error_manager.execute_with_retry(
                                self.automation_engine.process_github_event,
                                "task_creation",
                                event_data,
                            )
                            self.stats["tasks_created"] += len(created_tasks)

                        except Exception as e:
                            logger.error(f"Error creating task from commit: {e}")

                    # Handle task linking requests
                    for link_request in commit_analysis.task_linking_requests:
                        await self._process_task_linking(link_request, commit_analysis)

                    # Handle task status updates
                    for status_update in commit_analysis.task_status_updates:
                        await self._process_status_update(
                            status_update, commit_analysis
                        )

        except Exception as e:
            self.stats["errors_handled"] += 1
            logger.error(f"Error processing push event: {e}", exc_info=True)

    async def process_issues_event(self, event):
        """Process issues events"""
        try:
            self.stats["events_processed"] += 1
            self.stats["last_activity"] = asyncio.get_event_loop().time()

            logger.info(
                f"Processing issues event: {event.action} for #{event.payload.get('issue', {}).get('number', 'unknown')}"
            )

            # Process through automation engine
            event_data = {"event_type": "issues", "payload": event.payload}

            created_tasks = await self.error_manager.execute_with_retry(
                self.automation_engine.process_github_event, "task_creation", event_data
            )

            self.stats["tasks_created"] += len(created_tasks)
            logger.info(f"Created {len(created_tasks)} tasks from issue")

        except Exception as e:
            self.stats["errors_handled"] += 1
            logger.error(f"Error processing issues event: {e}", exc_info=True)

    async def process_comment_event(self, event):
        """Process issue comment events for task triggers"""
        try:
            self.stats["events_processed"] += 1
            self.stats["last_activity"] = asyncio.get_event_loop().time()

            comment = event.payload.get("comment", {})
            issue = event.payload.get("issue", {})

            logger.info(
                f"Processing comment event on issue #{issue.get('number', 'unknown')}"
            )

            # Check for task creation triggers in comment
            comment_body = comment.get("body", "")
            if self._contains_task_trigger(comment_body):
                # Process through automation engine
                event_data = {"event_type": "issue_comment", "payload": event.payload}

                created_tasks = await self.error_manager.execute_with_retry(
                    self.automation_engine.process_github_event,
                    "task_creation",
                    event_data,
                )

                self.stats["tasks_created"] += len(created_tasks)
                logger.info(f"Created {len(created_tasks)} tasks from comment")

        except Exception as e:
            self.stats["errors_handled"] += 1
            logger.error(f"Error processing comment event: {e}", exc_info=True)

    def _contains_task_trigger(self, text: str) -> bool:
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

    async def _process_task_linking(
        self, link_request: dict[str, Any], commit_analysis
    ):
        """Process task linking request from commit"""
        try:
            # This would link commits to existing tasks
            # Implementation would depend on specific linking requirements
            logger.info(
                f"Processing task link: {link_request.get('task_id')} -> {link_request.get('commit_hash')}"
            )
        except Exception as e:
            logger.error(f"Error processing task link: {e}")

    async def _process_status_update(
        self, status_update: dict[str, Any], commit_analysis
    ):
        """Process task status update from commit"""
        try:
            # This would update task status based on commit analysis
            logger.info(
                f"Processing status update: {status_update.get('status')} for commit {status_update.get('commit_hash')}"
            )
        except Exception as e:
            logger.error(f"Error processing status update: {e}")

    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        try:
            # Clear old errors
            self.error_manager.clear_old_errors(days=7)

            # Update metrics
            # Additional maintenance tasks can be added here

        except Exception as e:
            logger.error(f"Error during maintenance: {e}")

    async def _log_statistics(self):
        """Log current statistics"""
        try:
            runtime = asyncio.get_event_loop().time() - self.stats["start_time"]
            runtime_hours = runtime / 3600

            logger.info(
                f"Statistics - Runtime: {runtime_hours:.1f}h, "
                f"Events: {self.stats['events_processed']}, "
                f"Tasks Created: {self.stats['tasks_created']}, "
                f"Errors Handled: {self.stats['errors_handled']}"
            )

            # Get error statistics
            error_stats = self.error_manager.get_error_statistics()
            logger.info(
                f"Error Statistics - Success Rate: {error_stats['success_rate']:.1f}%, "
                f"Total Errors: {error_stats['total_errors']}"
            )

        except Exception as e:
            logger.error(f"Error logging statistics: {e}")

    async def _generate_final_report(self):
        """Generate final report on shutdown"""
        try:
            runtime = asyncio.get_event_loop().time() - self.stats["start_time"]
            runtime_hours = runtime / 3600

            logger.info("=== GitHub Integration Final Report ===")
            logger.info(f"Total Runtime: {runtime_hours:.2f} hours")
            logger.info(f"Events Processed: {self.stats['events_processed']}")
            logger.info(f"Tasks Created: {self.stats['tasks_created']}")
            logger.info(f"Errors Handled: {self.stats['errors_handled']}")

            if self.stats["events_processed"] > 0:
                logger.info(
                    f"Average Events per Hour: {self.stats['events_processed'] / runtime_hours:.1f}"
                )
            if self.stats["tasks_created"] > 0:
                logger.info(
                    f"Task Creation Rate: {self.stats['tasks_created'] / self.stats['events_processed'] * 100:.1f}%"
                )

            # Error statistics
            error_stats = self.error_manager.get_error_statistics()
            logger.info(f"Overall Success Rate: {error_stats['success_rate']:.1f}%")
            logger.info(
                f"Average Response Time: {error_stats['average_response_time']:.2f}s"
            )

            # Health status
            health = self.error_manager.get_health_status()
            logger.info(f"Final Health Status: {health['status']}")

            logger.info("=== End Report ===")

        except Exception as e:
            logger.error(f"Error generating final report: {e}")

    def get_integration_status(self) -> dict[str, Any]:
        """Get comprehensive integration status"""
        return {
            "orchestrator": {
                "runtime_hours": (
                    (
                        (asyncio.get_event_loop().time() - self.stats["start_time"])
                        / 3600
                    )
                    if self.stats["start_time"]
                    else 0
                ),
                "events_processed": self.stats["events_processed"],
                "tasks_created": self.stats["tasks_created"],
                "errors_handled": self.stats["errors_handled"],
                "last_activity": self.stats["last_activity"],
            },
            "components": {
                "webhook_server": "running" if self.webhook_server else "stopped",
                "pr_analyzer": "running" if self.pr_analyzer else "stopped",
                "commit_analyzer": "running" if self.commit_analyzer else "stopped",
                "automation_engine": "running" if self.automation_engine else "stopped",
            },
            "error_handling": self.error_manager.get_error_statistics(),
            "health": self.error_manager.get_health_status(),
            "automation": (
                self.automation_engine.get_automation_statistics()
                if self.automation_engine
                else {}
            ),
        }


# Main execution function
async def main():
    """Main entry point"""
    orchestrator = GitHubIntegrationOrchestrator()

    try:
        # Set up signal handlers for graceful shutdown
        import signal

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(orchestrator.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start the integration
        await orchestrator.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    # Check environment variables
    required_vars = ["GITHUB_WEBHOOK_SECRET", "GITHUB_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set the following environment variables:")
        for var in missing_vars:
            logger.error(f"  {var}")
        sys.exit(1)

    # Run the orchestrator
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application terminated with error: {e}")
        sys.exit(1)
