from __future__ import annotations

from datetime import datetime
from typing import Any
import json
import logging
import re
import statistics

from ..interfaces.analysis_interfaces import (
from .di_container import DIContainer

#!/usr/bin/env python3
"""Refactored Chat Analyzer - Clean Architecture Implementation
Follows CSF NIP standards with dependency injection and SRP.
"""



    AnalysisResult,
    ChatMessage,
    IAnalysisEngine,
    IConfigurationManager,
    IContextAnalyzer,
    ILogger,
    IMessageProcessor,
    IPatternRecognizer,
    IResultFormatter,
    IStatisticsCalculator,
    ProcessingConfig,
)


class RefactoredChatAnalyzer(IAnalysisEngine):
    """Refactored chat analyzer following clean architecture principles
    Coordinates multiple specialized components through dependency injection.
    """

    def __init__(self, container: DIContainer | None = None) -> None:
        """Initialize refactored analyzer with dependency injection.

        Args:
        ----
            container: DI container for dependency management

        """
        self.container = container or DIContainer()
        self.container.register_default_services()

        # Resolve dependencies through container
        self.message_processor = self.container.resolve(IMessageProcessor)
        self.pattern_recognizer = self.container.resolve(IPatternRecognizer)
        self.context_analyzer = self.container.resolve(IContextAnalyzer)
        self.statistics_calculator = self.container.resolve(IStatisticsCalculator)
        self.result_formatter = self.container.resolve(IResultFormatter)
        self.logger = self.container.resolve(ILogger)
        self.config_manager = self.container.resolve(IConfigurationManager)

        # Analysis state
        self._analysis_count = 0
        self._total_messages_processed = 0
        self._error_count = 0

    async def analyze(
        self, messages: list[ChatMessage], config: ProcessingConfig | None = None
    ) -> AnalysisResult:
        """Perform comprehensive chat analysis using coordinated components.

        Args:
        ----
            messages: List of chat messages to analyze
            config: Optional processing configuration

        Returns:
        -------
            AnalysisResult: Comprehensive analysis results

        """
        try:
            analysis_start_time = datetime.now()

            if self.logger:
                await self.logger.info(f"Starting analysis of {len(messages)} messages")

            # Input validation
            if not await self.validate_input(messages):
                msg = "Invalid input messages"
                raise ValueError(msg)

            # Apply processing configuration
            config = config or await self._get_default_config()

            # Initialize result structure
            result = AnalysisResult(
                summary={},
                patterns=[],
                statistics={},
                context={},
                metadata={
                    "analysis_timestamp": analysis_start_time.isoformat(),
                    "message_count": len(messages),
                    "analyzer_version": "2.0.0",
                    "architecture": "clean_architecture",
                },
            )

            # Phase 1: Message processing and normalization
            if self.logger:
                await self.logger.debug("Phase 1: Processing messages")
            processed_messages = await self._process_messages(messages, config)

            # Phase 2: Pattern recognition
            if config.enable_pattern_recognition:
                if self.logger:
                    await self.logger.debug("Phase 2: Recognizing patterns")
                result.patterns = await self._recognize_patterns(
                    processed_messages, config
                )

            # Phase 3: Context analysis
            if config.enable_context_analysis:
                if self.logger:
                    await self.logger.debug("Phase 3: Analyzing context")
                result.context = await self._analyze_context(processed_messages, config)

            # Phase 4: Statistical calculations
            if config.enable_statistics_calculation:
                if self.logger:
                    await self.logger.debug("Phase 4: Calculating statistics")
                result.statistics = await self._calculate_statistics(
                    processed_messages, config
                )

            # Phase 5: Generate summary
            if self.logger:
                await self.logger.debug("Phase 5: Generating summary")
            result.summary = await self._generate_summary(
                processed_messages, result, config
            )

            # Update metadata with analysis results
            analysis_end_time = datetime.now()
            result.metadata.update(
                {
                    "analysis_duration_seconds": (
                        analysis_end_time - analysis_start_time
                    ).total_seconds(),
                    "processed_message_count": len(processed_messages),
                    "pattern_count": len(result.patterns),
                    "success": True,
                },
            )

            # Update counters
            self._analysis_count += 1
            self._total_messages_processed += len(messages)

            if self.logger:
                await self.logger.info(
                    f"Analysis completed successfully in {result.metadata['analysis_duration_seconds']:.2f}s",
                )

            return result

        except Exception as e:
            self._error_count += 1
            error_msg = f"Analysis failed: {e}"
            if self.logger:
                await self.logger.exception(error_msg, exception=e)

            # Return error result
            return AnalysisResult(
                summary={"error": error_msg},
                patterns=[],
                statistics={},
                context={},
                metadata={
                    "analysis_timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "success": False,
                },
            )

    async def validate_input(self, messages: list[ChatMessage]) -> bool:
        """Validate input messages using message processor."""
        try:
            if not messages:
                return False

            # Validate each message
            for message in messages:
                if not await self.message_processor.validate_message(message):
                    if self.logger:
                        await self.logger.warning(
                            f"Invalid message detected: {message.id}"
                        )
                    return False

            # Check for minimum message count
            min_messages = await self.config_manager.get_setting(
                "min_messages_for_analysis", 1
            )
            if len(messages) < min_messages:
                if self.logger:
                    await self.logger.warning(
                        f"Insufficient messages: {len(messages)} < {min_messages}"
                    )
                return False

            return True

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Input validation error: {e}")
            return False

    async def get_engine_info(self) -> dict[str, Any]:
        """Get engine information and capabilities."""
        try:
            # Get component info
            components_info = {
                "message_processor": type(self.message_processor).__name__,
                "pattern_recognizer": type(self.pattern_recognizer).__name__,
                "context_analyzer": type(self.context_analyzer).__name__,
                "statistics_calculator": type(self.statistics_calculator).__name__,
                "result_formatter": type(self.result_formatter).__name__,
            }

            # Get container info
            container_info = self.container.get_service_info()

            return {
                "engine_name": "RefactoredChatAnalyzer",
                "version": "2.0.0",
                "architecture": "clean_architecture_with_dependency_injection",
                "components": components_info,
                "container_info": container_info,
                "performance_stats": {
                    "analyses_performed": self._analysis_count,
                    "total_messages_processed": self._total_messages_processed,
                    "error_count": self._error_count,
                    "success_rate": (self._analysis_count - self._error_count)
                    / max(1, self._analysis_count),
                },
                "capabilities": [
                    "message_processing_and_normalization",
                    "pattern_recognition",
                    "context_analysis",
                    "statistical_analysis",
                    "multiple_output_formats",
                    "security_validation",
                    "performance_optimization",
                ],
                "supported_formats": [
                    "json",
                    "html",
                    "markdown",
                    "plain",
                    "summary",
                    "detailed",
                ],
                "csf_nip_compliance": True,
            }

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error getting engine info: {e}")
            return {"error": str(e)}

    async def _process_messages(
        self, messages: list[ChatMessage], config: ProcessingConfig
    ) -> list[ChatMessage]:
        """Process and normalize messages using message processor component."""
        try:
            if config.cache_results:
                # Check cache first (simplified implementation)
                cached_result = await self._check_cache(messages)
                if cached_result:
                    if self.logger:
                        await self.logger.debug("Using cached processed messages")
                    return cached_result

            # Process messages
            processed_messages = await self.message_processor.normalize_messages(
                messages
            )

            # Cache results if enabled
            if config.cache_results:
                await self._cache_results(messages, processed_messages)

            return processed_messages

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error processing messages: {e}")
            # Return original messages as fallback
            return messages

    async def _recognize_patterns(
        self, messages: list[ChatMessage], config: ProcessingConfig
    ) -> list[dict[str, Any]]:
        """Recognize patterns using pattern recognizer component."""
        try:
            # Limit patterns if specified
            all_patterns = await self.pattern_recognizer.detect_patterns(messages)

            if (
                config.max_patterns_per_message
                and len(all_patterns) > config.max_patterns_per_message
            ):
                # Sort by confidence and keep top patterns
                all_patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)
                return all_patterns[: config.max_patterns_per_message]

            return all_patterns

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error recognizing patterns: {e}")
            return []

    async def _analyze_context(
        self, messages: list[ChatMessage], config: ProcessingConfig
    ) -> dict[str, Any]:
        """Analyze context using context analyzer component."""
        try:
            context = await self.context_analyzer.analyze_context(messages)

            # Extract threads if not already included
            if "threads" not in context:
                context["threads"] = await self.context_analyzer.extract_threads(
                    messages
                )

            # Analyze conversation flow if not already included
            if "conversation_flow" not in context:
                context["conversation_flow"] = (
                    await self.context_analyzer.analyze_conversation_flow(messages)
                )

            return context

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error analyzing context: {e}")
            return {"error": str(e)}

    async def _calculate_statistics(
        self, messages: list[ChatMessage], config: ProcessingConfig
    ) -> dict[str, Any]:
        """Calculate statistics using statistics calculator component."""
        try:
            # Calculate basic statistics
            basic_stats = await self.statistics_calculator.calculate_basic_stats(
                messages
            )

            # Calculate advanced statistics if needed
            if (
                hasattr(config, "enable_advanced_statistics")
                and config.enable_advanced_statistics
            ):
                advanced_stats = (
                    await self.statistics_calculator.calculate_advanced_metrics(
                        messages
                    )
                )
                basic_stats.update(advanced_stats)

            return basic_stats

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error calculating statistics: {e}")
            return {"error": str(e)}

    async def _generate_summary(
        self,
        messages: list[ChatMessage],
        result: AnalysisResult,
        config: ProcessingConfig,
    ) -> dict[str, Any]:
        """Generate comprehensive summary."""
        try:
            summary = {}

            # Basic conversation metrics
            summary.update(
                {
                    "total_messages": len(messages),
                    "unique_participants": len({msg.author for msg in messages}),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "pattern_count": len(result.patterns),
                    "analysis_success": result.metadata.get("success", False),
                },
            )

            # Add pattern summary
            if result.patterns:
                pattern_types = [p.get("type", "unknown") for p in result.patterns]
                summary["pattern_types"] = list(set(pattern_types))
                summary["pattern_distribution"] = {
                    pt: pattern_types.count(pt) for pt in set(pattern_types)
                }

            # Add statistics summary
            if result.statistics and "conversation_metrics" in result.statistics:
                summary.update(result.statistics["conversation_metrics"])

            # Add context summary
            if result.context and "conversation_overview" in result.context:
                summary.update(result.context["conversation_overview"])

            return summary

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error generating summary: {e}")
            return {"error": str(e)}

    async def _get_default_config(self) -> ProcessingConfig:
        """Get default processing configuration."""
        try:
            # Load from configuration manager if available
            if self.config_manager:
                return ProcessingConfig(
                    enable_pattern_recognition=await self.config_manager.get_setting(
                        "enable_pattern_recognition",
                        True,
                    ),
                    enable_context_analysis=await self.config_manager.get_setting(
                        "enable_context_analysis", True
                    ),
                    enable_statistics_calculation=await self.config_manager.get_setting(
                        "enable_statistics_calculation",
                        True,
                    ),
                    cache_results=await self.config_manager.get_setting(
                        "cache_results", True
                    ),
                    max_message_length=await self.config_manager.get_setting(
                        "max_message_length", 10000
                    ),
                    max_patterns_per_message=await self.config_manager.get_setting(
                        "max_patterns_per_message", 10
                    ),
                )
        except Exception as e:
            if self.logger:
                await self.logger.warning(f"Error loading config from manager: {e}")

        # Return default configuration
        return ProcessingConfig()

    async def _check_cache(
        self, messages: list[ChatMessage]
    ) -> list[ChatMessage] | None:
        """Check cache for processed messages (simplified implementation)."""
        # Placeholder for cache checking
        # In a real implementation, this would use a proper caching mechanism
        return None

    async def _cache_results(
        self,
        original_messages: list[ChatMessage],
        processed_messages: list[ChatMessage],
    ) -> None:
        """Cache processing results (simplified implementation)."""
        # Placeholder for caching
        # In a real implementation, this would store results in a cache

    # Additional convenience methods
    async def analyze_and_format(
        self,
        messages: list[ChatMessage],
        format_type: str = "json",
        config: ProcessingConfig | None = None,
    ) -> str:
        """Analyze messages and return formatted results.

        Args:
        ----
            messages: Messages to analyze
            format_type: Output format (json, html, markdown, plain, summary, detailed)
            config: Optional processing configuration

        Returns:
        -------
            str: Formatted analysis results

        """
        try:
            # Perform analysis
            result = await self.analyze(messages, config)

            # Format results
            return await self.result_formatter.format_results(result, format_type)

        except Exception as e:
            error_msg = f"Error in analyze_and_format: {e}"
            if self.logger:
                await self.logger.exception(error_msg)
            return f"Error: {error_msg}"

    async def analyze_and_export(
        self,
        messages: list[ChatMessage],
        file_path: str,
        config: ProcessingConfig | None = None,
    ) -> bool:
        """Analyze messages and export results to file.

        Args:
        ----
            messages: Messages to analyze
            file_path: Output file path
            config: Optional processing configuration

        Returns:
        -------
            bool: Success status

        """
        try:
            # Perform analysis
            result = await self.analyze(messages, config)

            # Export results
            return await self.result_formatter.export_results(result, file_path)

        except Exception as e:
            error_msg = f"Error in analyze_and_export: {e}"
            if self.logger:
                await self.logger.exception(error_msg)
            return False

    async def get_analysis_summary(
        self, messages: list[ChatMessage], config: ProcessingConfig | None = None
    ) -> str:
        """Get executive summary of analysis.

        Args:
        ----
            messages: Messages to analyze
            config: Optional processing configuration

        Returns:
        -------
            str: Executive summary

        """
        try:
            # Perform analysis
            result = await self.analyze(messages, config)

            # Create summary
            return await self.result_formatter.create_summary(result)

        except Exception as e:
            error_msg = f"Error creating summary: {e}"
            if self.logger:
                await self.logger.exception(error_msg)
            return f"Error: {error_msg}"

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.logger:
                await self.logger.info("Cleaning up analyzer resources")

            # Clear container cache
            self.container.clear_cache()

            # Reset counters
            self._analysis_count = 0
            self._total_messages_processed = 0
            self._error_count = 0

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error during cleanup: {e}")

    # Batch processing methods
    async def analyze_batch(
        self,
        message_batches: list[list[ChatMessage]],
        config: ProcessingConfig | None = None,
    ) -> list[AnalysisResult]:
        """Analyze multiple batches of messages.

        Args:
        ----
            message_batches: List of message batches to analyze
            config: Optional processing configuration

        Returns:
        -------
            List[AnalysisResult]: Results for each batch

        """
        results = []

        for i, batch in enumerate(message_batches):
            try:
                if self.logger:
                    await self.logger.debug(
                        f"Processing batch {i + 1}/{len(message_batches)}"
                    )

                result = await self.analyze(batch, config)
                results.append(result)

            except Exception as e:
                if self.logger:
                    await self.logger.exception(f"Error processing batch {i + 1}: {e}")

                # Add error result
                error_result = AnalysisResult(
                    summary={"error": str(e)},
                    patterns=[],
                    statistics={},
                    context={},
                    metadata={"batch_index": i, "error": True},
                )
                results.append(error_result)

        return results

    # Performance monitoring
    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        try:
            return {
                "total_analyses": self._analysis_count,
                "total_messages_processed": self._total_messages_processed,
                "error_count": self._error_count,
                "success_rate": (self._analysis_count - self._error_count)
                / max(1, self._analysis_count),
                "average_messages_per_analysis": self._total_messages_processed
                / max(1, self._analysis_count),
                "component_performance": {
                    "message_processor": await self._get_component_stats(
                        self.message_processor
                    ),
                    "pattern_recognizer": await self._get_component_stats(
                        self.pattern_recognizer
                    ),
                    "context_analyzer": await self._get_component_stats(
                        self.context_analyzer
                    ),
                    "statistics_calculator": await self._get_component_stats(
                        self.statistics_calculator
                    ),
                    "result_formatter": await self._get_component_stats(
                        self.result_formatter
                    ),
                },
            }

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

    async def _get_component_stats(self, component) -> dict[str, Any]:
        """Get statistics from component if available."""
        try:
            if hasattr(component, "get_processing_stats"):
                return await component.get_processing_stats()
            if hasattr(component, "get_stats"):
                return await component.get_stats()
            return {"status": "active", "type": type(component).__name__}
        except Exception:
            return {"status": "unknown", "type": type(component).__name__}
