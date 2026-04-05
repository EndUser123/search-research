"""
Claude Hook Integration for Voice Notifications
Updated with intelligent filtering and parallel execution support
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add the voice notifications module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..core.notification_orchestrator import VoiceNotificationOrchestrator

logger = logging.getLogger(__name__)

class VoiceNotificationHookIntegration:
    """
    Integration layer between Claude hooks and the voice notification system
    Provides intelligent filtering, parallel execution, and performance monitoring
    """

    def __init__(self, config_path: str | None = None):
        # Initialize the orchestrator
        self.orchestrator = VoiceNotificationOrchestrator(config_path)
        self.config_manager = self.orchestrator.config_manager

        # Start the orchestrator
        self._startup_complete = False
        self._start_orchestrator()

        # Hook session tracking
        self.session_start_time = datetime.now()
        self.hook_session_id = os.getenv("CLAUDE_SESSION_ID", f"hook_{int(time.time())}")

        logger.info(f"Voice Notification Hook Integration initialized with session: {self.hook_session_id}")

    def _start_orchestrator(self) -> None:
        """Start the notification orchestrator"""
        try:
            # Run in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start orchestrator
            loop.run_until_complete(self.orchestrator.start())
            self._startup_complete = True

            logger.info("Notification orchestrator started successfully")

        except Exception as e:
            logger.error(f"Failed to start notification orchestrator: {e}")
            self._startup_complete = False

    async def trigger_notification(
        self,
        notification_type: str,
        task_name: str = "",
        session_id: str | None = None,
        priority: str = "normal",
        tool_name: str | None = None,
        context: dict[str, Any] | None = None
    ) -> bool:
        """
        Trigger a voice notification with intelligent filtering
        Returns True if notification was queued successfully
        """
        try:
            if not self._startup_complete:
                logger.warning("Orchestrator not started, skipping notification")
                return False

            # Use provided session ID or fallback to hook session
            effective_session_id = session_id or self.hook_session_id

            # Trigger notification through orchestrator
            result = await self.orchestrator.trigger_notification(
                notification_type=notification_type,
                task_name=task_name,
                session_id=effective_session_id,
                priority=priority,
                tool_name=tool_name,
                context=context
            )

            return result.status.value != "failed"

        except Exception as e:
            logger.error(f"Error triggering notification: {e}")
            return False

    def trigger_notification_sync(
        self,
        notification_type: str,
        task_name: str = "",
        session_id: str | None = None,
        priority: str = "normal",
        tool_name: str | None = None,
        context: dict[str, Any] | None = None
    ) -> bool:
        """
        Synchronous wrapper for trigger_notification
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.trigger_notification(
                notification_type, task_name, session_id, priority, tool_name, context
            )
        )

    def parse_hook_input(self) -> dict[str, Any]:
        """Parse hook input from stdin or environment"""
        hook_data = {}

        # Try to read from stdin (JSON format from Claude)
        try:
            if not sys.stdin.isatty():
                input_data = sys.stdin.read().strip()
                if input_data:
                    hook_data = json.loads(input_data)
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not parse stdin input: {e}")

        # Get session ID from environment if available
        session_id = os.getenv("CLAUDE_SESSION_ID", "")
        if session_id:
            hook_data["session_id"] = session_id

        # Add hook session metadata
        hook_data["hook_session_id"] = self.hook_session_id
        hook_data["hook_start_time"] = self.session_start_time.isoformat()

        return hook_data

    def determine_notification_type(self, tool_name: str, action: str, hook_type: str) -> str | None:
        """
        Enhanced notification type determination with more context awareness
        """
        tool_name_lower = tool_name.lower() if tool_name else ""
        action_lower = action.lower() if action else ""

        # Special hook type handling
        if hook_type == "SessionStart":
            return "task_complete"
        elif hook_type == "SessionEnd":
            return "task_complete"
        elif hook_type == "Stop":
            return "task_complete"

        # Task completion indicators
        if any(keyword in tool_name_lower for keyword in ["complete", "done", "finish", "implement"]):
            return "task_complete"

        # Review completion indicators
        if any(keyword in tool_name_lower for keyword in ["review", "analyze", "audit"]):
            return "review_complete"

        # Plan ready indicators
        if any(keyword in tool_name_lower for keyword in ["plan", "strategy", "design"]):
            return "plan_ready"

        # Question indicators
        if any(keyword in action_lower for keyword in ["question", "clarify", "ask"]):
            return "question"

        # Error indicators
        if any(keyword in tool_name_lower for keyword in ["error", "fail", "exception"]):
            return "error"

        # Warning indicators
        if any(keyword in tool_name_lower for keyword in ["warning", "caution", "alert"]):
            return "warning"

        return None

    def extract_priority(self, tool_name: str, context: dict[str, Any]) -> str:
        """Extract notification priority from tool name and context"""
        tool_name_lower = tool_name.lower() if tool_name else ""

        # High priority indicators
        high_priority_keywords = ["error", "fail", "exception", "urgent", "critical"]
        if any(keyword in tool_name_lower for keyword in high_priority_keywords):
            return "high"

        # Check context for priority information
        if isinstance(context, dict):
            priority = context.get("priority")
            if priority in ["low", "normal", "high", "critical"]:
                return priority

            # Check for error information in context
            if context.get("error") or context.get("exception"):
                return "high"

        return "normal"

    def handle_session_start(self, hook_data: dict[str, Any]) -> None:
        """Handle SessionStart hook"""
        session_id = hook_data.get("session_id", self.hook_session_id)
        self.trigger_notification_sync(
            "task_complete",
            f"Session started ({session_id[:8]}...)",
            session_id,
            priority="normal",
            tool_name="SessionStart"
        )

    def handle_session_end(self, hook_data: dict[str, Any]) -> None:
        """Handle SessionEnd hook"""
        session_id = hook_data.get("session_id", self.hook_session_id)
        self.trigger_notification_sync(
            "task_complete",
            f"Session ended ({session_id[:8]}...)",
            session_id,
            priority="normal",
            tool_name="SessionEnd"
        )

    def handle_post_tool_use(self, hook_data: dict[str, Any]) -> None:
        """Handle PostToolUse hook with enhanced context analysis"""
        tool_name = hook_data.get("tool_name", "")
        action = hook_data.get("action", "")
        session_id = hook_data.get("session_id", self.hook_session_id)

        # Determine notification type
        notification_type = self.determine_notification_type(tool_name, action, "PostToolUse")

        if not notification_type:
            return  # No notification needed

        # Extract task context
        task_context = ""
        if hook_data.get("context"):
            task_context = hook_data["context"]
        elif tool_name:
            task_context = tool_name

        # Extract priority
        priority = self.extract_priority(tool_name, hook_data)

        # Prepare additional context
        context_data = {
            "hook_type": "PostToolUse",
            "action": action,
            "original_context": hook_data.get("context"),
            "hook_timestamp": datetime.now().isoformat()
        }

        # Trigger notification
        self.trigger_notification_sync(
            notification_type,
            task_context,
            session_id,
            priority=priority,
            tool_name=tool_name,
            context=context_data
        )

    def handle_stop(self, hook_data: dict[str, Any]) -> None:
        """Handle Stop hook"""
        session_id = hook_data.get("session_id", self.hook_session_id)
        self.trigger_notification_sync(
            "task_complete",
            "Claude session stopped",
            session_id,
            priority="normal",
            tool_name="Stop"
        )

    def handle_pre_tool_use(self, hook_data: dict[str, Any]) -> None:
        """Handle PreToolUse hook"""
        # Could trigger question notifications if tool asks for clarification
        action = hook_data.get("action", "")
        if "question" in action.lower() or "clarify" in action.lower():
            session_id = hook_data.get("session_id", self.hook_session_id)
            self.trigger_notification_sync(
                "question",
                f"Question about: {hook_data.get('tool_name', 'unknown tool')}",
                session_id,
                priority="high",
                tool_name=hook_data.get("tool_name", ""),
                context={"hook_type": "PreToolUse"}
            )

    def get_system_metrics(self) -> dict[str, Any]:
        """Get current system metrics for monitoring"""
        try:
            if self._startup_complete:
                return self.orchestrator.get_metrics()
            else:
                return {
                    "status": "not_started",
                    "error": "Orchestrator not initialized"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def shutdown(self) -> None:
        """Shutdown the voice notification system"""
        try:
            if self._startup_complete:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.orchestrator.stop())
            logger.info("Voice notification system shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global instance for hook integration
_hook_integration: VoiceNotificationHookIntegration | None = None

def get_hook_integration() -> VoiceNotificationHookIntegration:
    """Get or create the global hook integration instance"""
    global _hook_integration
    if _hook_integration is None:
        _hook_integration = VoiceNotificationHookIntegration()
    return _hook_integration

def main():
    """Main hook handler"""
    if len(sys.argv) < 2:
        print("Usage: voice_notifications.py <hook_type> [additional_args]")
        return

    hook_type = sys.argv[1]

    try:
        # Get hook integration instance
        hook_integration = get_hook_integration()

        # Parse hook input data
        hook_data = hook_integration.parse_hook_input()

        # Handle different hook types
        if hook_type == "SessionStart":
            hook_integration.handle_session_start(hook_data)

        elif hook_type == "SessionEnd":
            hook_integration.handle_session_end(hook_data)

        elif hook_type == "PostToolUse":
            hook_integration.handle_post_tool_use(hook_data)

        elif hook_type == "Stop":
            hook_integration.handle_stop(hook_data)

        elif hook_type == "PreToolUse":
            hook_integration.handle_pre_tool_use(hook_data)

        else:
            logger.info(f"Unknown hook type: {hook_type}")

    except Exception as e:
        logger.error(f"Error in hook handler: {e}")

if __name__ == "__main__":
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        main()

    except UnicodeEncodeError:
        print("Warning: Unicode encoding issue occurred, but system completed basic functionality")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        # Cleanup
        if _hook_integration:
            _hook_integration.shutdown()
