"""
Voice Notifications Configuration Module
Manages configuration loading with intelligent filtering settings
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class VoiceConfig:
    """Voice engine configuration"""
    preferred_voice: str = "Microsoft David Desktop"
    fallback_voice: str = "Microsoft Zira Desktop"
    volume: int = 85
    rate: int = -1
    async_speech: bool = True

@dataclass
class NotificationTypeConfig:
    """Configuration for a specific notification type"""
    enabled: bool = True
    template: str = ""
    priority: str = "normal"
    max_frequency_per_hour: int = 10
    session_timeout_minutes: int = 30
    requires_user_interaction: bool = False

@dataclass
class IntelligentFilterConfig:
    """Intelligent filtering configuration"""
    enabled: bool = True
    session_isolation: bool = True
    behavioral_filtering: bool = True
    frequency_limits: bool = True
    context_analysis: bool = True
    learning_enabled: bool = True
    filter_strength: float = 0.7  # 0.0 to 1.0
    session_timeout_minutes: int = 30
    max_notifications_per_hour: int = 20
    max_notifications_per_session: int = 50
    exempt_high_priority: bool = True
    learning_rate: float = 0.1
    decay_rate: float = 0.05

@dataclass
class PerformanceConfig:
    """Performance monitoring configuration"""
    target_delivery_ms: int = 500
    parallel_execution: bool = True
    max_concurrent_notifications: int = 3
    enable_metrics: bool = True
    performance_log_file: str | None = None
    alert_on_slow_delivery: bool = True
    slow_delivery_threshold_ms: int = 1000

@dataclass
class LoggingConfig:
    """Logging configuration"""
    enabled: bool = True
    log_file: str = "P:/hooks/voice_notification.log"
    log_level: str = "info"
    max_log_size_mb: int = 10
    include_performance_metrics: bool = True
    include_filter_decisions: bool = True

@dataclass
class IntegrationConfig:
    """Integration configuration"""
    hook_script_path: str = "P:/hooks/voice-notification.ps1"
    power_shell_required: bool = True
    speech_synthesis_required: bool = True
    use_pyttsx3_engine: bool = True
    fallback_to_powershell: bool = True

@dataclass
class VoiceNotificationSystemConfig:
    """Complete voice notification system configuration"""
    enabled: bool = True

    # Sub-configurations
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    notifications: dict[str, NotificationTypeConfig] = field(default_factory=dict)
    intelligent_filter: IntelligentFilterConfig = field(default_factory=IntelligentFilterConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)

    # Legacy support
    concurrent_sessions: dict[str, Any] = field(default_factory=dict)
    fallback: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default notification types if not provided"""
        if not self.notifications:
            self.notifications = {
                "task_complete": NotificationTypeConfig(
                    template="Task Complete: {task_name}",
                    priority="normal"
                ),
                "review_complete": NotificationTypeConfig(
                    template="Review Complete: {task_name}",
                    priority="normal"
                ),
                "question": NotificationTypeConfig(
                    template="Question about: {task_name}",
                    priority="high"
                ),
                "plan_ready": NotificationTypeConfig(
                    template="Plan Ready: {task_name}",
                    priority="normal"
                ),
                "error": NotificationTypeConfig(
                    template="Error occurred: {task_name}",
                    priority="high",
                    requires_user_interaction=True
                ),
                "warning": NotificationTypeConfig(
                    template="Warning: {task_name}",
                    priority="normal"
                ),
                "info": NotificationTypeConfig(
                    template="Information: {task_name}",
                    priority="low"
                )
            }

class ConfigManager:
    """Manages voice notification system configuration with validation"""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else Path("P:/hooks/voice-notification-config.json")
        self.config: VoiceNotificationSystemConfig = VoiceNotificationSystemConfig()
        self.last_modified: datetime | None = None
        self.load_config()

    def load_config(self) -> bool:
        """
        Load configuration from file with validation
        Returns True if successful, False otherwise
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self.config = VoiceNotificationSystemConfig()
                self._save_config()
                return True

            with open(self.config_path, encoding='utf-8') as f:
                data = json.load(f)

            # Validate and migrate configuration
            validated_config = self._validate_and_migrate(data)

            # Create configuration object
            self.config = self._dict_to_config(validated_config)
            self.last_modified = datetime.now()

            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {self.config_path}: {e}")
            self.config = VoiceNotificationSystemConfig()
            return False
        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
            self.config = VoiceNotificationSystemConfig()
            return False

    def _validate_and_migrate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate configuration data and migrate from legacy format
        """
        if not isinstance(data, dict):
            raise ValueError("Configuration must be a dictionary")

        # Initialize result with defaults
        result = {
            "enabled": data.get("enabled", True),
            "voice": {},
            "notifications": {},
            "intelligent_filter": {},
            "performance": {},
            "logging": {},
            "integration": {},
            "concurrent_sessions": data.get("concurrent_sessions", {}),
            "fallback": data.get("fallback", {})
        }

        # Validate voice settings
        voice_data = data.get("voice", {})
        result["voice"] = {
            "preferred_voice": voice_data.get("preferred_voice", "Microsoft David Desktop"),
            "fallback_voice": voice_data.get("fallback_voice", "Microsoft Zira Desktop"),
            "volume": self._validate_int_range(voice_data.get("volume", 85), 0, 100, "volume"),
            "rate": voice_data.get("rate", -1),
            "async_speech": voice_data.get("async_speech", True)
        }

        # Validate notifications
        notifications_data = data.get("notifications", {})
        default_notifications = {
            "task_complete": {"template": "Task Complete: {task_name}", "priority": "normal"},
            "review_complete": {"template": "Review Complete: {task_name}", "priority": "normal"},
            "question": {"template": "Question about: {task_name}", "priority": "high"},
            "plan_ready": {"template": "Plan Ready: {task_name}", "priority": "normal"}
        }

        for notif_type, default_config in default_notifications.items():
            notif_data = notifications_data.get(notif_type, default_config)
            result["notifications"][notif_type] = {
                "enabled": notif_data.get("enabled", True),
                "template": notif_data.get("template", default_config["template"]),
                "priority": self._validate_priority(notif_data.get("priority", default_config["priority"])),
                "max_frequency_per_hour": self._validate_int_range(
                    notif_data.get("max_frequency_per_hour", 10), 1, 100, "max_frequency_per_hour"
                ),
                "session_timeout_minutes": self._validate_int_range(
                    notif_data.get("session_timeout_minutes", 30), 1, 1440, "session_timeout_minutes"
                ),
                "requires_user_interaction": notif_data.get("requires_user_interaction", False)
            }

        # Validate intelligent filter settings
        filter_data = data.get("intelligent_filter", {})
        result["intelligent_filter"] = {
            "enabled": filter_data.get("enabled", True),
            "session_isolation": filter_data.get("session_isolation", True),
            "behavioral_filtering": filter_data.get("behavioral_filtering", True),
            "frequency_limits": filter_data.get("frequency_limits", True),
            "context_analysis": filter_data.get("context_analysis", True),
            "learning_enabled": filter_data.get("learning_enabled", True),
            "filter_strength": self._validate_float_range(filter_data.get("filter_strength", 0.7), 0.0, 1.0, "filter_strength"),
            "session_timeout_minutes": self._validate_int_range(
                filter_data.get("session_timeout_minutes", 30), 1, 1440, "session_timeout_minutes"
            ),
            "max_notifications_per_hour": self._validate_int_range(
                filter_data.get("max_notifications_per_hour", 20), 1, 1000, "max_notifications_per_hour"
            ),
            "max_notifications_per_session": self._validate_int_range(
                filter_data.get("max_notifications_per_session", 50), 1, 1000, "max_notifications_per_session"
            ),
            "exempt_high_priority": filter_data.get("exempt_high_priority", True),
            "learning_rate": self._validate_float_range(filter_data.get("learning_rate", 0.1), 0.0, 1.0, "learning_rate"),
            "decay_rate": self._validate_float_range(filter_data.get("decay_rate", 0.05), 0.0, 1.0, "decay_rate")
        }

        # Validate performance settings
        perf_data = data.get("performance", {})
        result["performance"] = {
            "target_delivery_ms": self._validate_int_range(perf_data.get("target_delivery_ms", 500), 50, 10000, "target_delivery_ms"),
            "parallel_execution": perf_data.get("parallel_execution", True),
            "max_concurrent_notifications": self._validate_int_range(
                perf_data.get("max_concurrent_notifications", 3), 1, 10, "max_concurrent_notifications"
            ),
            "enable_metrics": perf_data.get("enable_metrics", True),
            "performance_log_file": perf_data.get("performance_log_file"),
            "alert_on_slow_delivery": perf_data.get("alert_on_slow_delivery", True),
            "slow_delivery_threshold_ms": self._validate_int_range(
                perf_data.get("slow_delivery_threshold_ms", 1000), 100, 10000, "slow_delivery_threshold_ms"
            )
        }

        # Validate logging settings
        logging_data = data.get("logging", {})
        result["logging"] = {
            "enabled": logging_data.get("enabled", True),
            "log_file": logging_data.get("log_file", "P:/hooks/voice_notification.log"),
            "log_level": self._validate_log_level(logging_data.get("log_level", "info")),
            "max_log_size_mb": self._validate_int_range(logging_data.get("max_log_size_mb", 10), 1, 1000, "max_log_size_mb"),
            "include_performance_metrics": logging_data.get("include_performance_metrics", True),
            "include_filter_decisions": logging_data.get("include_filter_decisions", True)
        }

        # Validate integration settings
        integration_data = data.get("integration", {})
        result["integration"] = {
            "hook_script_path": integration_data.get("hook_script_path", "P:/hooks/voice-notification.ps1"),
            "power_shell_required": integration_data.get("power_shell_required", True),
            "speech_synthesis_required": integration_data.get("speech_synthesis_required", True),
            "use_pyttsx3_engine": integration_data.get("use_pyttsx3_engine", True),
            "fallback_to_powershell": integration_data.get("fallback_to_powershell", True)
        }

        return result

    def _validate_int_range(self, value: Any, min_val: int, max_val: int, field_name: str) -> int:
        """Validate integer value is within range"""
        try:
            int_value = int(value)
            if not min_val <= int_value <= max_val:
                logger.warning(f"{field_name} value {int_value} out of range [{min_val}, {max_val}], using default")
                # Return a reasonable default based on field
                defaults = {
                    "volume": 85, "rate": -1, "max_frequency_per_hour": 10,
                    "session_timeout_minutes": 30, "target_delivery_ms": 500,
                    "max_concurrent_notifications": 3, "slow_delivery_threshold_ms": 1000,
                    "max_notifications_per_hour": 20, "max_notifications_per_session": 50
                }
                return defaults.get(field_name, min_val)
            return int_value
        except (ValueError, TypeError):
            logger.warning(f"Invalid {field_name} value: {value}, using default")
            defaults = {
                "volume": 85, "rate": -1, "max_frequency_per_hour": 10,
                "session_timeout_minutes": 30, "target_delivery_ms": 500,
                "max_concurrent_notifications": 3, "slow_delivery_threshold_ms": 1000,
                "max_notifications_per_hour": 20, "max_notifications_per_session": 50
            }
            return defaults.get(field_name, min_val)

    def _validate_float_range(self, value: Any, min_val: float, max_val: float, field_name: str) -> float:
        """Validate float value is within range"""
        try:
            float_value = float(value)
            if not min_val <= float_value <= max_val:
                logger.warning(f"{field_name} value {float_value} out of range [{min_val}, {max_val}], using default")
                defaults = {"filter_strength": 0.7, "learning_rate": 0.1, "decay_rate": 0.05}
                return defaults.get(field_name, (min_val + max_val) / 2)
            return float_value
        except (ValueError, TypeError):
            logger.warning(f"Invalid {field_name} value: {value}, using default")
            defaults = {"filter_strength": 0.7, "learning_rate": 0.1, "decay_rate": 0.05}
            return defaults.get(field_name, (min_val + max_val) / 2)

    def _validate_priority(self, value: Any) -> str:
        """Validate priority value"""
        valid_priorities = ["low", "normal", "high", "critical"]
        if isinstance(value, str) and value.lower() in valid_priorities:
            return value.lower()
        logger.warning(f"Invalid priority value: {value}, using 'normal'")
        return "normal"

    def _validate_log_level(self, value: Any) -> str:
        """Validate log level value"""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if isinstance(value, str) and value.lower() in valid_levels:
            return value.lower()
        logger.warning(f"Invalid log level: {value}, using 'info'")
        return "info"

    def _dict_to_config(self, data: dict[str, Any]) -> VoiceNotificationSystemConfig:
        """Convert dictionary to configuration object"""
        # Convert voice settings
        voice_data = data.get("voice", {})
        voice = VoiceConfig(**voice_data)

        # Convert notifications
        notifications = {}
        for notif_type, notif_data in data.get("notifications", {}).items():
            notifications[notif_type] = NotificationTypeConfig(**notif_data)

        # Convert intelligent filter
        filter_data = data.get("intelligent_filter", {})
        intelligent_filter = IntelligentFilterConfig(**filter_data)

        # Convert performance
        perf_data = data.get("performance", {})
        performance = PerformanceConfig(**perf_data)

        # Convert logging
        logging_data = data.get("logging", {})
        logging_config = LoggingConfig(**logging_data)

        # Convert integration
        integration_data = data.get("integration", {})
        integration = IntegrationConfig(**integration_data)

        return VoiceNotificationSystemConfig(
            enabled=data.get("enabled", True),
            voice=voice,
            notifications=notifications,
            intelligent_filter=intelligent_filter,
            performance=performance,
            logging=logging_config,
            integration=integration,
            concurrent_sessions=data.get("concurrent_sessions", {}),
            fallback=data.get("fallback", {})
        )

    def save_config(self) -> bool:
        """
        Save current configuration to file
        Returns True if successful, False otherwise
        """
        try:
            # Convert configuration to dictionary
            config_dict = asdict(self.config)

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.last_modified = datetime.now()
            logger.info(f"Configuration saved to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving config to {self.config_path}: {e}")
            return False

    def _save_config(self) -> bool:
        """Internal method to save default configuration"""
        return self.save_config()

    def reload_config(self) -> bool:
        """Reload configuration from file"""
        return self.load_config()

    def get_notification_config(self, notification_type: str) -> NotificationTypeConfig | None:
        """Get configuration for a specific notification type"""
        return self.config.notifications.get(notification_type)

    def is_notification_enabled(self, notification_type: str) -> bool:
        """Check if a notification type is enabled"""
        if not self.config.enabled:
            return False

        notif_config = self.get_notification_config(notification_type)
        return notif_config.enabled if notif_config else False

    def update_setting(self, path: str, value: Any) -> bool:
        """
        Update a specific configuration setting using dot notation
        Example: update_setting("voice.volume", 90)
        """
        try:
            parts = path.split('.')
            config_obj = self.config

            # Navigate to the correct object
            for part in parts[:-1]:
                config_obj = getattr(config_obj, part)

            # Set the value
            setattr(config_obj, parts[-1], value)

            # Validate and save
            return self.save_config()

        except Exception as e:
            logger.error(f"Error updating setting {path}: {e}")
            return False
