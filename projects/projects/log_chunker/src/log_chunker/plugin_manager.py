"""Plugin manager for chunking strategies."""

import importlib.util
import inspect
import logging
from collections import defaultdict
from typing import Any

from rich.console import Console

from .config import ChunkingConfig
from .data_models import ChunkInfo, LogEntry
from .plugins.base import BaseChunkingPlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages chunking plugins"""

    def __init__(self, config: ChunkingConfig, console: Console = None):
        self.config = config
        self.plugins = {}
        self.console = console or self._create_default_console()
        self._load_core_plugins()

    def _create_default_console(self):
        """Create a default console if none provided"""
        return Console()

    def _load_core_plugins(self):
        """Load core plugins with enhanced validation"""
        core_plugins = {
            # 'semantic': SemanticChunkingPlugin, # Loaded dynamically below
        }

        # Import other plugins dynamically to avoid import errors
        try:
            from .plugins.semantic import SemanticChunkingPlugin

            core_plugins["semantic"] = SemanticChunkingPlugin
        except ImportError:
            logger.warning("Semantic plugin not available")
        try:
            from .plugins.other_plugins import TemporalChunkingPlugin

            core_plugins["temporal"] = TemporalChunkingPlugin
        except ImportError:
            logger.warning("Temporal plugin not available")

        try:
            from .plugins.other_plugins import ConversationChunkingPlugin

            core_plugins["conversation"] = ConversationChunkingPlugin
        except ImportError:
            logger.warning("Conversation plugin not available")

        try:
            from .plugins.other_plugins import PatternChunkingPlugin

            core_plugins["pattern"] = PatternChunkingPlugin
        except ImportError:
            logger.warning("Pattern plugin not available")

        try:
            from .plugins.other_plugins import PerplexityChunkingPlugin

            core_plugins["perplexity"] = PerplexityChunkingPlugin
        except ImportError:
            logger.warning("Perplexity plugin not available")

        try:
            from .plugins.security_analysis import SecurityAnalysisPlugin

            core_plugins["security_analysis"] = SecurityAnalysisPlugin
        except ImportError:
            logger.warning("Security analysis plugin not available")

        # Enhanced ML plugins with optional dependencies
        try:
            from .plugins.enhanced.semantic_clustering import SemanticClusteringPlugin

            core_plugins["semantic_clustering"] = SemanticClusteringPlugin
        except ImportError:
            logger.warning("Enhanced semantic clustering plugin not available")

        try:
            from .plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin

            core_plugins["advanced_anomaly"] = AdvancedAnomalyPlugin
        except ImportError:
            logger.warning("Advanced anomaly detection plugin not available")

        for name, plugin_class in core_plugins.items():
            if name in self.config.enabled_plugins:
                try:
                    plugin = plugin_class()

                    # Validate plugin capabilities
                    if not self._validate_plugin_interface_internal(plugin, name):
                        logger.warning(
                            f"Plugin {name} does not implement required interface"
                        )
                        continue

                    if plugin.initialize(self.config, self.console):
                        self.plugins[name] = plugin
                        capabilities = self._detect_plugin_capabilities(plugin)
                        logger.info(
                            f"Loaded plugin: {name} with capabilities: {capabilities}"
                        )
                    else:
                        logger.warning(f"Failed to initialize plugin: {name}")
                except Exception as e:
                    logger.error(f"Error loading plugin {name}: {e}")

    def load_external_plugin(self, plugin_path: str):
        """Load external plugin from file"""
        try:
            spec = importlib.util.spec_from_file_location(
                "external_plugin", plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseChunkingPlugin)
                    and obj != BaseChunkingPlugin
                ):
                    plugin = obj()
                    if plugin.initialize(self.config, self.console):
                        self.plugins[plugin.name] = plugin
                        logger.info(f"Loaded external plugin: {plugin.name}")

        except Exception as e:
            logger.error(f"Failed to load external plugin {plugin_path}: {e}")

    def find_boundaries(
        self, text: str, log_entries: list[LogEntry]
    ) -> dict[str, list[int]]:
        """Find boundaries using all active plugins"""
        all_boundaries = {}

        for name, plugin in self.plugins.items():
            try:
                boundaries = plugin.find_boundaries(text, log_entries)
                all_boundaries[name] = boundaries
                logger.debug(f"Plugin {name} found {len(boundaries)} boundaries")
            except Exception as e:
                logger.error(f"Error in plugin {name}: {e}")
                all_boundaries[name] = []

        return all_boundaries

    def score_chunks(self, chunks: list[tuple]) -> None:
        """Score chunks using all active plugins"""
        for chunk_text, info in chunks:
            plugin_scores = {}

            for name, plugin in self.plugins.items():
                try:
                    score = plugin.score_chunk(chunk_text, info)
                    plugin_scores[name] = score
                except Exception as e:
                    logger.error(f"Error scoring chunk with plugin {name}: {e}")
                    plugin_scores[name] = 0.0

            info.plugin_scores = plugin_scores
            total_score = 0.0
            total_weight = 0.0
            for name, score in plugin_scores.items():
                weight = self.config.plugin_weights.get(name, 1.0)
                total_score += score * weight
                total_weight += weight

            info.quality_score = total_score / total_weight if total_weight > 0 else 0.0

    def merge_boundaries(
        self, boundary_dict: dict[str, list[int]], log_entries: list[LogEntry]
    ) -> list[int]:
        """Intelligently merge boundaries from multiple plugins"""
        all_boundaries = set([0])  # Always include start

        # Collect weighted boundaries
        boundary_scores = defaultdict(float)

        for plugin_name, boundaries in boundary_dict.items():
            weight = self.config.plugin_weights.get(
                plugin_name, 1.0
            )  # Use configurable weights
            for boundary in boundaries:
                boundary_scores[boundary] += weight

        # Select boundaries above threshold
        threshold = len(self.plugins) * 0.3  # 30% of plugins must agree

        for boundary, score in boundary_scores.items():
            if score >= threshold and 0 <= boundary < len(log_entries):
                all_boundaries.add(boundary)

        # Add end boundary
        all_boundaries.add(len(log_entries))

        return sorted(list(all_boundaries))

    def run_analysis_plugins(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> dict[str, Any]:
        """Run analysis plugins on generated chunks and merge results.

        Args:
            chunks: List of (chunk_text, chunk_info) tuples

        Returns:
            Dictionary containing merged analysis results from all plugins
        """
        merged_analysis = {}
        analysis_plugins = [
            name
            for name, plugin in self.plugins.items()
            if hasattr(plugin, "analyze_chunks") and callable(plugin.analyze_chunks)
        ]

        if not analysis_plugins:
            logger.info("No plugins support analysis capability")
            return merged_analysis

        logger.info(
            f"Running analysis with {len(analysis_plugins)} plugins: {', '.join(analysis_plugins)}"
        )

        for name, plugin in self.plugins.items():
            if name not in analysis_plugins:
                continue

            try:
                logger.debug(f"Running analysis plugin: {name}")
                plugin_analysis = plugin.analyze_chunks(chunks)

                if plugin_analysis:
                    # Namespace the plugin results to avoid conflicts
                    merged_analysis[name] = plugin_analysis
                    analysis_keys = list(plugin_analysis.keys())
                    logger.info(
                        f"Plugin {name} contributed analysis data: {analysis_keys}"
                    )
                else:
                    logger.debug(f"Plugin {name} returned no analysis data")

            except NotImplementedError:
                logger.warning(
                    f"Plugin {name} has not implemented analyze_chunks method"
                )
                merged_analysis[name] = {"status": "not_implemented"}
            except Exception as e:
                logger.error(f"Error running analysis in plugin {name}: {e}")
                # Continue with other plugins even if one fails
                merged_analysis[name] = {"error": str(e), "status": "failed"}

        logger.info(
            f"Plugin analysis complete. {len(merged_analysis)} plugins contributed data."
        )
        return merged_analysis

    def register_plugin(self, name: str, plugin: BaseChunkingPlugin):
        """Register a plugin instance."""
        if self.validate_plugin_interface(plugin):
            self.plugins[name] = plugin
            logger.info(f"Successfully registered plugin: {name}")
        else:
            logger.error(f"Failed to register plugin {name} due to interface mismatch.")

    def validate_plugin_interface(self, plugin: BaseChunkingPlugin) -> bool:
        """Validate that a plugin instance has the required methods."""
        required_methods = ["find_boundaries", "score_chunk", "analyze_chunks"]
        missing_methods = []
        for method in required_methods:
            if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
                missing_methods.append(method)

        if missing_methods:
            logger.error(
                f"Plugin validation failed. Missing methods: {', '.join(missing_methods)}"
            )
            return False
        return True

    def _validate_plugin_interface_internal(self, plugin, plugin_name: str) -> bool:
        """Validate that plugin implements required interface methods."""
        required_methods = ["find_boundaries", "score_chunk", "analyze_chunks"]

        for method_name in required_methods:
            if not hasattr(plugin, method_name):
                logger.error(
                    f"Plugin {plugin_name} missing required method: {method_name}"
                )
                return False

            if not callable(getattr(plugin, method_name)):
                logger.error(
                    f"Plugin {plugin_name} method {method_name} is not callable"
                )
                return False

        return True

    def _detect_plugin_capabilities(self, plugin) -> list[str]:
        """Detect what capabilities a plugin supports."""
        capabilities = []

        # Check for chunking capability
        if hasattr(plugin, "find_boundaries") and callable(plugin.find_boundaries):
            capabilities.append("chunking")

        # Check for scoring capability
        if hasattr(plugin, "score_chunk") and callable(plugin.score_chunk):
            capabilities.append("scoring")

        # Check for analysis capability
        if hasattr(plugin, "analyze_chunks") and callable(plugin.analyze_chunks):
            capabilities.append("analysis")

        return capabilities

    def get_enabled_plugins(self):
        """Get dictionary of enabled plugins."""
        if hasattr(self.config, "enabled_plugins") and self.config.enabled_plugins:
            return {
                name: plugin
                for name, plugin in self.plugins.items()
                if name in self.config.enabled_plugins
            }
        return self.plugins

    def cleanup(self):
        """Cleanup all plugins"""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin: {e}")
