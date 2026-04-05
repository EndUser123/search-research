"""Configuration models for the chunking framework."""

import multiprocessing as mp  # Used in max_workers validator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

# Try to import pydantic, fallback to dataclass if not available
try:
    from pydantic import BaseModel, Field, ValidationInfo, field_validator

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object

    def Field(default, **kwargs):
        return default

    def field_validator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


if HAS_PYDANTIC:

    class SemanticClusteringConfig(BaseModel):
        """Configuration for semantic clustering plugin"""

        enabled: bool = Field(default=False, description="Enable semantic clustering")
        model_name: str = Field(
            default="all-MiniLM-L6-v2", description="Sentence transformer model"
        )
        min_cluster_size: int = Field(
            default=5, description="Minimum cluster size for HDBSCAN"
        )
        min_samples: int = Field(default=3, description="Minimum samples for HDBSCAN")
        cache_embeddings: bool = Field(
            default=True, description="Cache embeddings for performance"
        )

    class AdvancedAnomalyConfig(BaseModel):
        """Configuration for advanced anomaly detection plugin"""

        enabled: bool = Field(
            default=False, description="Enable advanced anomaly detection"
        )
        contamination: float = Field(
            default=0.1, ge=0.01, le=0.5, description="Expected proportion of anomalies"
        )
        n_estimators: int = Field(
            default=100, gt=0, description="Number of trees in isolation forest"
        )
        max_samples: str = Field(
            default="auto", description="Number of samples to draw from X"
        )
        random_state: int = Field(
            default=42, description="Random state for reproducibility"
        )

    class ChunkingConfig(BaseModel):
        """Main configuration for chunking pipeline"""

        # Basic chunking parameters
        target_tokens: int = Field(
            100000,
            gt=0,
            description="Target number of tokens per chunk. The framework aims to create chunks close to this size.",
        )
        max_tokens: int = Field(
            120000,
            gt=0,
            description="Maximum allowed tokens per chunk. If a chunk exceeds this, it will be forcibly split.",
        )
        overlap_ratio: float = Field(
            0.15,
            ge=0,
            le=1,
            description="Ratio of overlap between consecutive chunks (0.0 to 1.0). Useful for preserving context at boundaries.",
        )

        # Tokenizer settings
        tokenizer_type: str = Field(
            "gemini",
            description="Type of tokenizer used for rough token estimation (e.g., 'gemini', 'openai'). Affects token/char ratio.",
        )
        tokens_per_char: float = Field(
            0.25,
            gt=0,
            description="Estimated tokens per character for rough token counting. Adjust based on content language and type.",
        )

        # Deduplication settings
        enable_deduplication: bool = Field(
            True,
            description="Enable smart log deduplication to reduce redundant log entries.",
        )
        dedup_threshold: int = Field(
            5,
            ge=1,
            description="Minimum number of identical/fuzzy log lines before they are summarized into a single entry.",
        )
        fuzzy_threshold: int = Field(
            85,
            ge=0,
            le=100,
            description="Similarity threshold (0-100) for fuzzy deduplication. Higher means stricter matching.",
        )
        time_window_minutes: int = Field(
            60,
            ge=1,
            description="Time window in minutes within which similar entries are grouped for deduplication.",
        )

        # Semantic chunking
        enable_semantic: bool = Field(
            True,
            description="Enable the Semantic chunking plugin, which identifies boundaries based on meaning changes.",
        )
        enable_semantic_clustering: bool = Field(
            True,
            description="Enable semantic clustering of chunks to group related content.",
        )
        semantic_model: str = Field(
            "all-MiniLM-L6-v2",
            description="Sentence Transformer model name (e.g., 'all-MiniLM-L6-v2') for semantic analysis. Impacts performance and quality.",
        )
        semantic_threshold: float = Field(
            0.3,
            ge=0,
            le=1,
            description="Semantic similarity threshold (0-1) for boundaries. Lower value results in more splits (more granular chunks).",
        )
        min_cluster_size: int = Field(
            2,
            gt=0,
            description="Minimum size of clusters for semantic chunking (HDBSCAN). Smaller values create more, smaller clusters.",
        )
        min_samples: int = Field(
            1,
            ge=0,
            description="Minimum number of samples in a neighborhood for a point to be considered as a core point (HDBSCAN). Affects cluster density.",
        )

        # Perplexity chunking
        enable_perplexity: bool = Field(
            False,
            description="Enable the Perplexity chunking plugin, using LLM uncertainty for logical breaks. Requires transformers and torch.",
        )
        perplexity_model: str = Field(
            "microsoft/DialoGPT-medium",
            description="Causal language model (e.g., 'microsoft/DialoGPT-medium') for perplexity calculations.",
        )
        perplexity_threshold: float = Field(
            0.15,
            ge=0,
            le=1,
            description="Perplexity change threshold (0-1) indicating a boundary. Lower value results in more splits.",
        )
        perplexity_context_window: int = Field(
            3,
            gt=0,
            description="Number of preceding sentences to consider for perplexity context. Higher values provide more context but are slower.",
        )

        # Temporal analysis
        enable_temporal: bool = Field(
            True,
            description="Enable the Temporal chunking plugin, detecting boundaries based on time-based anomalies.",
        )
        temporal_std_threshold: float = Field(
            2.0,
            gt=0,
            description="Standard deviation threshold for detecting anomalous time gaps in log timestamps. Higher value means stricter anomaly detection.",
        )

        # Conversation analysis
        enable_conversation: bool = Field(
            True,
            description="Enable the Conversation chunking plugin, specialized for chat logs (speaker changes, turn-taking).",
        )
        speaker_change_weight: float = Field(
            1.5,
            gt=0,
            description="Weight assigned to speaker changes in conversation chunking. Influences boundary fusion severity.",
        )

        # Log parsing and pattern detection patterns
        log_parsing_patterns: list[str] = Field(
            default_factory=lambda: [
                r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,. ]\d{3})\s*-\s*([^\s]+)\s*-\s*([A-Z]+)\s*-\s*(.+)",
                r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+([^:]+):\s*(.+)",
                r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*([A-Z]+):\s*(.+)",
                r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.]\d{3}Z?)\s*\[([A-Z]+)\]\s*([^\s]+)\s*-\s*(.+)",
            ],
            description="List of regex patterns used by the preprocessor to parse common log line formats (extracting timestamp, level, logger, message).",
        )
        advanced_detection_patterns: dict[str, list[str]] = Field(
            default_factory=lambda: {
                "error_start": [
                    r"(ERROR|FATAL|EXCEPTION|TRACEBACK)",
                    r"^\s*(at |Traceback|Exception|Error:)",
                    r"Caused by:",
                    r"Stack trace:",
                ],
                "section_start": [
                    r"^=+\s*$",
                    r"^-+\s*$",
                    r"^\*+\s*$",
                    r"^\#+\s+",
                    r"Starting|Initializing|Beginning|Stopping|Shutting down",
                ],
                "code_block": [
                    r"```",
                    r"^\s*(def |class |import |from )",
                    r"^\s*(function|var |const |let )",
                    r"^\s*(public|private|protected)\s+(class|interface)",
                ],
                "network_activity": [
                    r"(GET|POST|PUT|DELETE|PATCH)\s+/",
                    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
                    r"HTTP/\d\.\d\s+\d{3}",
                    r"(tcp|udp|http|https)://",
                ],
                "sql_query": [r"(SELECT|INSERT|UPDATE|DELETE)\s+FROM", r"JOIN\s+"],
                "kubernetes": [r"(pod|namespace|deployment|service)/", r"kubelet"],
                "docker": [r"(container|image|volume|daemon|dockerd):"],
                "uuid": [
                    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
                ],
                "email": [r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"],
                "url": [r"https?://[^\s]+"],
                "file_path": [r"(?:[a-zA-Z]:)?[/\\](?:[^/\\]+[/\\])*[^/\\]+"],
            },
            description="Dictionary of regex patterns for advanced content classification (e.g., 'error_start', 'code_block').",
        )

        # Enhanced Semantic Analysis Configuration
        semantic_clustering: "SemanticClusteringConfig" = Field(
            default_factory=lambda: SemanticClusteringConfig()
        )

        # Advanced Anomaly Detection Configuration
        advanced_anomaly: "AdvancedAnomalyConfig" = Field(
            default_factory=lambda: AdvancedAnomalyConfig()
        )

        # Performance settings
        batch_size: int = Field(
            32,
            gt=0,
            description="Batch size for ML model inference and other batched operations. Larger batches improve GPU utilization but consume more VRAM.",
        )
        max_workers: int | None = Field(
            None,
            description="Maximum CPU workers for multiprocessing. Optimal value depends on CPU cores and workload. Defaults to min(CPU count, 8).",
        )
        use_gpu: bool = Field(
            True,
            description="Enable GPU usage if a CUDA-capable device is available and required libraries are installed. Set to False to force CPU processing.",
        )

        # Plugin settings
        enabled_plugins: list[str] = Field(
            default_factory=lambda: [
                "semantic",
                "temporal",
                "conversation",
                "pattern",
                "security_analysis",
                "semantic_clustering",
                "advanced_anomaly",
            ],
            description="List of plugin names to enable for chunk boundary detection. Available: 'semantic', 'perplexity', 'temporal', 'conversation', 'pattern', 'security_analysis', 'semantic_clustering', 'advanced_anomaly'.",
        )
        plugin_weights: dict[str, float] = Field(
            default_factory=lambda: {
                "semantic": 1.0,
                "perplexity": 1.2,  # Perplexity is often a strong indicator
                "temporal": 0.8,
                "conversation": 1.1,
                "pattern": 0.9,
                "security_analysis": 1.3,  # Security events are important for boundaries
                "semantic_clustering": 1.5,  # Enhanced semantic analysis with ML
                "advanced_anomaly": 1.4,  # Advanced anomaly detection with ML
                # Add custom plugin weights here if you define custom plugins
            },
            description="Weights for each plugin's boundary suggestions during fusion. A higher weight means that plugin's suggestions have more influence on the final chunk boundaries.",
        )

        # Output settings
        save_metadata: bool = Field(
            True,
            description="Save comprehensive metadata (metadata.json) and individual chunk files to the output directory.",
        )
        rich_display: bool = Field(
            True,
            description="Enable rich terminal output using the 'rich' library for enhanced readability.",
        )

        # Adaptive configuration settings
        no_adaptive: bool = Field(
            False,
            description="Disable adaptive configuration suggestions for the current run.",
        )
        auto_optimize: bool = Field(
            False,
            description="Automatically apply optimized configuration recommended by adaptive analysis without prompting the user.",
        )

        @field_validator("max_tokens")
        def max_tokens_greater_than_target(cls, v: int, info: "ValidationInfo") -> int:
            """Validate that max_tokens is greater than target_tokens."""
            if "target_tokens" in info.data and v <= info.data["target_tokens"]:
                raise ValueError("max_tokens must be greater than target_tokens")
            return v

        @field_validator("max_workers")
        def validate_max_workers(cls, v: int | None) -> int:
            """Validate max_workers, setting a default based on CPU count if None."""
            if v is None:
                return min(
                    mp.cpu_count(), 8
                )  # Default to CPU count, capped at 8 to avoid excessive context switching
            return max(1, v)  # Ensure at least 1 worker, and use provided value

else:

    @dataclass
    class SemanticClusteringConfig:
        """Configuration for semantic clustering plugin (fallback without pydantic)"""

        enabled: bool = False
        model_name: str = "all-MiniLM-L6-v2"
        min_cluster_size: int = 5
        min_samples: int = 3
        cache_embeddings: bool = True

    @dataclass
    class AdvancedAnomalyConfig:
        """Configuration for advanced anomaly detection plugin (fallback without pydantic)"""

        enabled: bool = False
        contamination: float = 0.1
        n_estimators: int = 100
        max_samples: str = "auto"
        random_state: int = 42

    @dataclass
    class ChunkingConfig:
        """Main configuration for chunking pipeline (fallback without pydantic)"""

        # Basic chunking parameters
        target_tokens: int = 100000
        max_tokens: int = 120000
        overlap_ratio: float = 0.15

        # Tokenizer settings
        tokenizer_type: str = "gemini"
        tokens_per_char: float = 0.25

        # Deduplication settings
        enable_deduplication: bool = True
        dedup_threshold: int = 5
        fuzzy_threshold: int = 85
        time_window_minutes: int = 60

        # Semantic chunking
        enable_semantic: bool = True
        enable_semantic_clustering: bool = True
        semantic_model: str = "all-MiniLM-L6-v2"
        semantic_threshold: float = 0.3
        min_cluster_size: int = 2
        min_samples: int = 1

        # Perplexity chunking
        enable_perplexity: bool = False
        perplexity_model: str = "microsoft/DialoGPT-medium"
        perplexity_threshold: float = 0.15
        perplexity_context_window: int = 3

        # Temporal analysis
        enable_temporal: bool = True
        temporal_std_threshold: float = 2.0

        # Conversation analysis
        enable_conversation: bool = True
        speaker_change_weight: float = 1.5

        # Log parsing patterns
        log_parsing_patterns: list[str] = field(
            default_factory=lambda: [
                r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,. ]\d{3})\s*-\s*([^\s]+)\s*-\s*([A-Z]+)\s*-\s*(.+)",
                r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+([^:]+):\s*(.+)",
                r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*([A-Z]+):\s*(.+)",
                r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.]\d{3}Z?)\s*\[([A-Z]+)\]\s*([^\s]+)\s*-\s*(.+)",
            ]
        )

        advanced_detection_patterns: dict[str, list[str]] = field(
            default_factory=lambda: {
                "error_start": [
                    r"(ERROR|FATAL|EXCEPTION|TRACEBACK)",
                    r"^\s*(at |Traceback|Exception|Error:)",
                    r"Caused by:",
                    r"Stack trace:",
                ],
                "section_start": [
                    r"^=+\s*$",
                    r"^-+\s*$",
                    r"^\*+\s*$",
                    r"^\#+\s+",
                    r"Starting|Initializing|Beginning|Stopping|Shutting down",
                ],
            }
        )

        # Performance settings
        batch_size: int = 32
        max_workers: int | None = None
        use_gpu: bool = True

        # Plugin settings
        enabled_plugins: list[str] = field(
            default_factory=lambda: [
                "semantic",
                "temporal",
                "conversation",
                "pattern",
                "security_analysis",
                "semantic_clustering",
                "advanced_anomaly",
            ]
        )
        plugin_weights: dict[str, float] = field(
            default_factory=lambda: {
                "semantic": 1.0,
                "perplexity": 1.2,
                "temporal": 0.8,
                "conversation": 1.1,
                "pattern": 0.9,
                "security_analysis": 1.3,
                "semantic_clustering": 1.5,
                "advanced_anomaly": 1.4,
            }
        )

        # Output settings
        save_metadata: bool = True
        rich_display: bool = True

        # Adaptive configuration settings
        no_adaptive: bool = False
        auto_optimize: bool = False

        # Enhanced Semantic Analysis Configuration
        semantic_clustering: SemanticClusteringConfig = field(
            default_factory=SemanticClusteringConfig
        )

        # Advanced Anomaly Detection Configuration
        advanced_anomaly: AdvancedAnomalyConfig = field(
            default_factory=AdvancedAnomalyConfig
        )

        def __post_init__(self):
            """Validate config after initialization."""
            if self.max_tokens <= self.target_tokens:
                raise ValueError("max_tokens must be greater than target_tokens")
            if self.max_workers is None:
                self.max_workers = min(mp.cpu_count(), 8)


# Avoid circular import by using TYPE_CHECKING
if TYPE_CHECKING:
    from .adaptive_config import ContentAnalysis

    ChunkingConfig.__annotations__["analysis_results"] = Optional["ContentAnalysis"]
