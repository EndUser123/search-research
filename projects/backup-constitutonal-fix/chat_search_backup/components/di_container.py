from __future__ import annotations

from datetime import date
from enum import auto
from typing import Any
import logging
import re
import statistics
import threading

from ..interfaces.analysis_interfaces import (
from abc import ABC
import inspect

#!/usr/bin/env python3
"""Dependency Injection Container for Chat Analysis Components
Following CSF NIP clean architecture principles.
"""


    IAnalysisEngine,
    ICacheManager,
    IConfigurationManager,
    IContextAnalyzer,
    ILogger,
    IMessageProcessor,
    IPatternRecognizer,
    IResultFormatter,
    IStatisticsCalculator,
)


class ServiceRegistrationError(Exception):
    """Service registration error."""


class DIContainer:
    """Dependency Injection Container for Chat Analysis Components.

    Manages service lifecycles and dependencies according to CSF NIP standards
    """

    def __init__(self) -> None:
        self._services: dict[type, Any] = {}
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, callable] = {}
        self._instances: dict[type, Any] = {}
        self._lock = threading.RLock()
        self._auto_wire = True

    def register_transient(self, interface: type, implementation: type) -> None:
        """Register transient service (new instance per request)."""
        with self._lock:
            if not issubclass(implementation, interface):
                msg = f"Implementation {implementation.__name__} must implement {interface.__name__}"
                raise ServiceRegistrationError(
                    msg,
                )
            self._services[interface] = implementation

    def register_singleton(self, interface: type, implementation: type) -> None:
        """Register singleton service (shared instance)."""
        with self._lock:
            if not issubclass(implementation, interface):
                msg = f"Implementation {implementation.__name__} must implement {interface.__name__}"
                raise ServiceRegistrationError(
                    msg,
                )
            self._services[interface] = implementation

    def register_factory(self, interface: type, factory: callable) -> None:
        """Register factory function for service creation."""
        with self._lock:
            self._factories[interface] = factory

    def resolve(self, interface: type) -> Any:
        """Resolve service instance with auto-wiring."""
        with self._lock:
            # Check if we have an existing instance
            if interface in self._instances:
                return self._instances[interface]

            # Create new instance based on registration type
            if interface in self._singletons:
                # Singleton - create once and reuse
                if interface not in self._singletons:
                    self._singletons[interface] = self._create_instance(interface)
                instance = self._singletons[interface]
                self._instances[interface] = instance

            elif interface in self._factories:
                # Factory-based creation
                factory = self._factories[interface]
                instance = factory(container=self)
                self._instances[interface] = instance

            elif interface in self._services:
                # Transient - create new instance each time
                instance = self._create_instance(interface)

            else:
                available_services = list(self._services.keys()) + list(
                    self._factories.keys()
                )
                msg = (
                    f"Service {interface.__name__} not registered. "
                    f"Available: {[s.__name__ for s in available_services]}"
                )
                raise ServiceRegistrationError(
                    msg,
                )

            # Auto-wire dependencies if enabled
            if self._auto_wire:
                self._auto_wire_dependencies(instance)

            return instance

    def _create_instance(self, interface: type) -> Any:
        """Create instance with dependency injection."""
        implementation = self._services.get(interface)
        if not implementation:
            msg = f"No implementation registered for {interface.__name__}"
            raise ServiceRegistrationError(msg)

        # Check if implementation needs container parameter
        sig = inspect.signature(implementation.__init__)

        if "container" in sig.parameters:
            # Pass container to constructor for dependency injection
            return implementation(container=self)
        # Create with default constructor
        return implementation()

    def _auto_wire_dependencies(self, instance: Any) -> None:
        """Automatically wire dependencies for service instance."""
        # Get constructor signature
        sig = inspect.signature(instance.__init__)

        for param_name, param in sig.parameters.items():
            if param_name in ["self", "args", "kwargs"]:
                continue

            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                continue

            # Check if parameter type is a registered interface
            if isinstance(param_type, type) and issubclass(param_type, ABC):
                try:
                    dependency = self.resolve(param_type)
                    # Set dependency using reflection
                    setattr(instance, param_name, dependency)
                except ServiceRegistrationError:
                    # Dependency not available, leave as None
                    pass

    def register_default_services(self) -> None:
        """Register default service implementations for CSF NIP compliance."""
        try:
            # Import concrete implementations
            from .context_analyzer import ContextAnalyzer
            from .message_processor import MessageProcessor
            from .pattern_recognizer import PatternRecognizer
            from .result_formatter import ResultFormatter
            from .statistics_calculator import StatisticsCalculator

            # Register core analysis components
            self.register_singleton(IMessageProcessor, MessageProcessor)
            self.register_singleton(IPatternRecognizer, PatternRecognizer)
            self.register_singleton(IContextAnalyzer, ContextAnalyzer)
            self.register_singleton(IStatisticsCalculator, StatisticsCalculator)
            self.register_singleton(IResultFormatter, ResultFormatter)
            self.register_singleton(IConfigurationManager, ConfigurationManager)

            # Register utility components
            self.register_singleton(ICacheManager, CacheManager)
            self.register_singleton(ILogger, Logger)

        except Exception:
            pass

    def get_service_info(self) -> dict[str, Any]:
        """Get information about registered services."""
        with self._lock:
            return {
                "registered_services": len(self._services),
                "singletons": len(self._singletons),
                "factories": len(self._factories),
                "active_instances": len(self._instances),
                "auto_wire_enabled": self._auto_wire,
                "available_interfaces": [
                    interface.__name__ for interface in self._services
                ],
            }

    def clear_cache(self) -> None:
        """Clear all cached instances."""
        with self._lock:
            self._instances.clear()

    def set_auto_wire(self, enabled: bool) -> None:
        """Enable or disable auto-wiring."""
        self._auto_wire = enabled


# Default service implementations (to be overridden by specific implementations)


class AnalysisEngine(IAnalysisEngine):
    """Default analysis engine implementation."""

    def __init__(self, container=None) -> None:
        self.container = container
        if container:
            self.message_processor = container.resolve(IMessageProcessor)
            self.pattern_recognizer = container.resolve(IPatternRecognizer)
            self.context_analyzer = container.resolve(IContextAnalyzer)
            self.statistics_calculator = container.resolve(IStatisticsCalculator)
            self.result_formatter = container.resolve(IResultFormatter)

    async def analyze(self, messages, config=None) -> None:
        # Implementation to be provided
        pass

    async def validate_input(self, messages):
        return len(messages) > 0

    async def get_engine_info(self):
        return {"version": "1.0.0", "components": 6}


class MessageProcessor(IMessageProcessor):
    """Default message processor implementation."""

    async def process_message(self, message):
        # Implementation to be provided
        return message

    async def normalize_messages(self, messages):
        return [await self.process_message(msg) for msg in messages]

    async def validate_message(self, message):
        return bool(message and message.content and message.author)


class PatternRecognizer(IPatternRecognizer):
    """Default pattern recognizer implementation."""

    async def detect_patterns(self, messages):
        # Implementation to be provided
        return []

    async def classify_intent(self, message) -> str:
        return "general"

    async def get_pattern_confidence(self, pattern, message) -> float:
        return 0.5


class ContextAnalyzer(IContextAnalyzer):
    """Default context analyzer implementation."""

    async def analyze_context(self, messages):
        return {"thread_count": 1}

    async def extract_threads(self, messages):
        return []

    async def analyze_conversation_flow(self, messages):
        return {"flow_type": "linear"}


class StatisticsCalculator(IStatisticsCalculator):
    """Default statistics calculator implementation."""

    async def calculate_basic_stats(self, messages):
        return {"total_messages": len(messages)}

    async def calculate_advanced_metrics(self, messages):
        return {}

    async def get_trends(self, messages):
        return {}


class ResultFormatter(IResultFormatter):
    """Default result formatter implementation."""

    async def format_results(self, result, format_type):
        return str(result)

    async def export_results(self, result, file_path) -> bool:
        return False

    async def create_summary(self, result) -> str:
        return f"Analysis completed with {len(result.patterns)} patterns"


class ConfigurationManager(IConfigurationManager):
    """Default configuration manager implementation."""

    def __init__(self) -> None:
        self._config = {}

    async def load_config(self, config_path):
        return self._config

    async def get_setting(self, key, default=None):
        return self._config.get(key, default)

    async def update_setting(self, key, value) -> bool:
        self._config[key] = value
        return True

    async def validate_config(self, config) -> bool:
        return True


class CacheManager(ICacheManager):
    """Default cache manager implementation."""

    def __init__(self) -> None:
        self._cache = {}

    async def get(self, key):
        return self._cache.get(key)

    async def put(self, key, value, ttl=3600) -> None:
        self._cache[key] = value

    async def invalidate(self, key):
        return self._cache.pop(key, None) is not None

    async def clear(self) -> None:
        self._cache.clear()


class Logger(ILogger):
    """Default logger implementation."""

    async def info(self, message, **kwargs) -> None:
        pass

    async def error(self, message, **kwargs) -> None:
        pass

    async def debug(self, message, **kwargs) -> None:
        pass

    async def warning(self, message, **kwargs) -> None:
        pass
