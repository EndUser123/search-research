from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

#!/usr/bin/env python3
"""Analysis Interface Definitions for Chat History System
Clean architecture interfaces following CSF NIP standards.
"""




@dataclass
class ChatMessage:
    """Core message data structure."""

    id: str
    content: str
    timestamp: str
    author: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Analysis result data structure."""

    summary: dict[str, Any]
    patterns: list[dict[str, Any]]
    statistics: dict[str, Any]
    context: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingConfig:
    """Configuration for analysis processing."""

    enable_pattern_recognition: bool = True
    enable_context_analysis: bool = True
    enable_statistics_calculation: bool = True
    cache_results: bool = True
    max_message_length: int = 10000
    max_patterns_per_message: int = 10


class IAnalysisEngine(ABC):
    """Core analysis engine interface following SRP."""

    @abstractmethod
    async def analyze(
        self, messages: list[ChatMessage], config: ProcessingConfig | None = None
    ) -> AnalysisResult:
        """Perform comprehensive chat analysis."""

    @abstractmethod
    async def validate_input(self, messages: list[ChatMessage]) -> bool:
        """Validate input messages."""

    @abstractmethod
    async def get_engine_info(self) -> dict[str, Any]:
        """Get engine information and capabilities."""


class IMessageProcessor(ABC):
    """Message processing interface following SRP."""

    @abstractmethod
    async def process_message(self, message: ChatMessage) -> ChatMessage:
        """Process individual message."""

    @abstractmethod
    async def normalize_messages(
        self, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        """Normalize message format."""

    @abstractmethod
    async def validate_message(self, message: ChatMessage) -> bool:
        """Validate message format."""


class IPatternRecognizer(ABC):
    """Pattern recognition interface following SRP."""

    @abstractmethod
    async def detect_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect conversation patterns."""

    @abstractmethod
    async def classify_intent(self, message: ChatMessage) -> str:
        """Classify message intent."""

    @abstractmethod
    async def get_pattern_confidence(self, pattern: str, message: ChatMessage) -> float:
        """Get confidence score for pattern detection."""


class IContextAnalyzer(ABC):
    """Context analysis interface following SRP."""

    @abstractmethod
    async def analyze_context(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Analyze conversation context."""

    @abstractmethod
    async def extract_threads(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Extract conversation threads."""

    @abstractmethod
    async def analyze_conversation_flow(
        self, messages: list[ChatMessage]
    ) -> dict[str, Any]:
        """Analyze conversation flow and dynamics."""


class IStatisticsCalculator(ABC):
    """Statistics calculation interface following SRP."""

    @abstractmethod
    async def calculate_basic_stats(
        self, messages: list[ChatMessage]
    ) -> dict[str, Any]:
        """Calculate basic statistics."""

    @abstractmethod
    async def calculate_advanced_metrics(
        self, messages: list[ChatMessage]
    ) -> dict[str, Any]:
        """Calculate advanced metrics."""

    @abstractmethod
    async def get_trends(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Calculate trends over time."""


class IResultFormatter(ABC):
    """Result formatting interface following SRP."""

    @abstractmethod
    async def format_results(self, result: AnalysisResult, format_type: str) -> str:
        """Format analysis results."""

    @abstractmethod
    async def export_results(self, result: AnalysisResult, file_path: str) -> bool:
        """Export results to file."""

    @abstractmethod
    async def create_summary(self, result: AnalysisResult) -> str:
        """Create executive summary."""


class IConfigurationManager(ABC):
    """Configuration management interface following SRP."""

    @abstractmethod
    async def load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration."""

    @abstractmethod
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get specific setting."""

    @abstractmethod
    async def update_setting(self, key: str, value: Any) -> bool:
        """Update specific setting."""

    @abstractmethod
    async def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate configuration."""


class ICacheManager(ABC):
    """Cache management interface."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get cached item."""

    @abstractmethod
    async def put(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Put item in cache."""

    @abstractmethod
    async def invalidate(self, key: str) -> bool:
        """Invalidate cached item."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache."""


class ILogger(ABC):
    """Logging interface."""

    @abstractmethod
    async def info(self, message: str, **kwargs) -> None:
        """Log info message."""

    @abstractmethod
    async def error(self, message: str, **kwargs) -> None:
        """Log error message."""

    @abstractmethod
    async def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""

    @abstractmethod
    async def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
