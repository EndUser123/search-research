"""
Voice Notifications System
Intelligent voice notification system with parallel execution and performance monitoring

This package provides:
- Intelligent notification filtering without explicit user feedback
- Parallel task execution for concurrent notifications
- Performance monitoring with <500ms delivery targets
- Constitutional compliance with clear error messages
- Windows-only implementation with pyttsx3 and PowerShell support

Main Components:
- VoiceNotificationOrchestrator: Core system orchestrator
- IntelligentNotificationFilter: Context-aware filtering
- VoiceNotificationHookIntegration: Claude hook integration
- Performance monitoring and alerting

Usage:
    from voice_notifications import VoiceNotificationOrchestrator

    orchestrator = VoiceNotificationOrchestrator()
    await orchestrator.start()

    result = await orchestrator.trigger_notification(
        notification_type="task_complete",
        task_name="My Task",
        session_id="session123"
    )
"""

from .config.config_manager import (
    ConfigManager,
    IntegrationConfig,
    IntelligentFilterConfig,
    LoggingConfig,
    NotificationTypeConfig,
    PerformanceConfig,
    VoiceConfig,
    VoiceNotificationSystemConfig,
)
from .core.notification_orchestrator import (
    DeliveryResult,
    DeliveryStatus,
    NotificationRequest,
    PerformanceMetrics,
    VoiceEngine,
    VoiceNotificationOrchestrator,
)
from .filters.intelligent_filter import (
    BehavioralProfile,
    FilterDecision,
    FilterResult,
    IntelligentNotificationFilter,
    NotificationContext,
    SessionMetrics,
)
from .hooks.claude_integration import (
    VoiceNotificationHookIntegration,
    get_hook_integration,
)
from .monitoring.performance_monitor import (
    DeliveryPerformanceSnapshot,
    PerformanceAlert,
    PerformanceThresholds,
    SystemResourceSnapshot,
    VoiceNotificationPerformanceMonitor,
)

__version__ = "1.0.0"
__author__ = "Claude Voice Notifications System"

# Convenience functions for easy access
async def create_orchestrator(config_path=None):
    """Create and start a voice notification orchestrator"""
    orchestrator = VoiceNotificationOrchestrator(config_path)
    await orchestrator.start()
    return orchestrator

def trigger_notification_sync(notification_type, task_name="", session_id="default", **kwargs):
    """Synchronous convenience function for triggering notifications"""
    integration = get_hook_integration()
    return integration.trigger_notification_sync(
        notification_type, task_name, session_id, **kwargs
    )

def get_system_metrics():
    """Get current system metrics"""
    integration = get_hook_integration()
    return integration.get_system_metrics()

# Export main components
__all__ = [
    # Core orchestrator
    'VoiceNotificationOrchestrator',
    'NotificationRequest',
    'DeliveryResult',
    'DeliveryStatus',
    'VoiceEngine',
    'PerformanceMetrics',

    # Intelligent filtering
    'IntelligentNotificationFilter',
    'NotificationContext',
    'FilterDecision',
    'FilterResult',
    'SessionMetrics',
    'BehavioralProfile',

    # Configuration
    'ConfigManager',
    'VoiceNotificationSystemConfig',
    'VoiceConfig',
    'NotificationTypeConfig',
    'IntelligentFilterConfig',
    'PerformanceConfig',
    'LoggingConfig',
    'IntegrationConfig',

    # Performance monitoring
    'VoiceNotificationPerformanceMonitor',
    'PerformanceThresholds',
    'DeliveryPerformanceSnapshot',
    'SystemResourceSnapshot',
    'PerformanceAlert',

    # Hook integration
    'VoiceNotificationHookIntegration',
    'get_hook_integration',

    # Convenience functions
    'create_orchestrator',
    'trigger_notification_sync',
    'get_system_metrics'
]
