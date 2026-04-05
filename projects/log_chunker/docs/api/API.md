
# API Documentation

Complete API reference for the Advanced Log Chunking Framework.

---

## [DRAFT] Development Process & Risk Mitigation

### Strategic Risks & Solutions

#### 1. The "Crystal Ball" Problem (Strategic Risk)

- **Issue**: The IntelligenceReport data model is defined early, but its completeness is only proven when used in later phases (Reporting, Plugins, CLI). Late discoveries may require major refactoring.
- **Solution**: Add a Cross-Phase Validation Gate at the end of Phase 5: "Validate Data Model Finality." This task reviews the IntelligenceReport against all consuming features to ensure completeness before final testing.

#### 2. The "Ghost of Code Past" Problem (Technical Debt Risk)

- **Issue**: New components (IntelligenceEngine, SemanticTagger) may leave legacy analysis logic in files like reporter.py, creating dead code and technical debt.
- **Solution**: Add explicit "Refactor and Cleanup" tasks in the plan. For example, after refactoring reporter.py to use IntelligenceReport, add: "Remove old analysis logic from reporter.py."

#### 3. The "Black Box" Problem (Quality Risk)

- **Issue**: No objective way to measure the quality of intelligence produced. Subjective quality risks persist even if all tests pass.
- **Solution**:
    1. **Golden Dataset**: Manually create a perfect IntelligenceReport.json for a sample log (e.g., rovodev.log) as ground truth.
    2. **Evaluation Script**: Add scripts/evaluate_quality.py to compare generated IntelligenceReport.json against the golden file, checking for key patterns and clustering.
    3. **Testing Integration**: Make this evaluation script a required part of final testing (Phase 6), turning subjective quality into an objective, repeatable test.

---

## Table of Contents

1. [Core Classes](#core-classes)
2. [Configuration](#configuration)
3. [Data Models](#data-models)
4. [Plugin Interface](#plugin-interface)
5. [Analysis Classes](#analysis-classes)
6. [Utility Functions](#utility-functions)
7. [Command Line Interface](#command-line-interface)

## Core Classes

### AdvancedChunkingEngine

Main processing engine that orchestrates the chunking pipeline.

```python
class AdvancedChunkingEngine:
    def __init__(self, config: ChunkingConfig, console: Optional[Console] = None)
    def chunk_text(self, text: str) -> ChunkingResult
    def cleanup(self) -> None
```

#### Methods

**`__init__(config: ChunkingConfig, console: Optional[Console] = None)`**

- **Purpose**: Initialize the chunking engine with configuration
- **Parameters**:
  - `config`: ChunkingConfig object with all settings
  - `console`: Optional Rich console for display output
- **Raises**: `ConfigurationError` if config is invalid

**`chunk_text(text: str) -> ChunkingResult`**

- **Purpose**: Process text and generate chunks with analysis
- **Parameters**:
  - `text`: Input text to be chunked
- **Returns**: ChunkingResult with chunks and metadata
- **Raises**: `ProcessingError` if chunking fails

**`cleanup() -> None`**

- **Purpose**: Clean up resources and temporary files
- **Parameters**: None
- **Returns**: None

#### Example Usage

```python
from chunking_engine import AdvancedChunkingEngine
from config import ChunkingConfig

# Create configuration
config = ChunkingConfig(
    target_tokens=50000,
    enabled_plugins=["semantic", "temporal"]
)

# Initialize engine
engine = AdvancedChunkingEngine(config)

# Process text
with open("logs.txt", "r") as f:
    text = f.read()

result = engine.chunk_text(text)

# Access results
print(f"Generated {len(result.chunks)} chunks")
print(f"Processing time: {result.total_processing_time:.2f}s")

# Cleanup
engine.cleanup()
```

### PluginManager

Manages loading and coordination of chunking plugins.

```python
class PluginManager:
    def __init__(self, config: ChunkingConfig, console: Console)
    def analyze(self, result: ChunkingResult, **options) -> IntelligenceReport:
    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> Dict[str, List[int]]
    def merge_boundaries(self, all_boundaries: Dict[str, List[int]]) -> List[int]
```

#### Methods

**`load_external_plugin(plugin_path: str) -> None`**
analysis = analyzer.analyze(

- **Parameters**:
  - `plugin_path`: Path to Python file containing plugin class
- **Raises**: `PluginError` if loading fails

**`find_boundaries(text: str, log_entries: List[LogEntry]) -> Dict[str, List[int]]`**

- **Purpose**: Execute all active plugins to find chunk boundaries
- **Parameters**:
  - `text`: Input text to analyze
  - `log_entries`: Parsed log entries with metadata
- **Returns**: Dictionary mapping plugin names to boundary lists

  # Access analysis results

    error_patterns = analysis.error_patterns
    correlations = analysis.correlations
    anomalies = analysis.anomalies
    timeline = analysis.timeline
- **Returns**: Final merged boundary positions

### IntelligenceEngine

The `IntelligenceEngine` is the core analysis component. Its primary role is to take the raw log entries and produce a comprehensive `IntelligenceReport`.

```python
class IntelligenceEngine:
    def __init__(self, config: ChunkingConfig):
        # Initializes the engine with the necessary configuration.
        pass

    def analyze(self, log_entries: List[LogEntry]) -> IntelligenceReport:
        # The main analysis method. It orchestrates the various analysis
        # sub-modules (deduplication, correlation, etc.) and returns a
        # single, structured IntelligenceReport object.
        pass
```

#### Methods

**`analyze(log_entries: List[LogEntry]) -> IntelligenceReport`**

-   **Purpose**: To perform a comprehensive analysis of the provided log entries. This method is the single entry point for all intelligence-gathering operations.
-   **Parameters**:
    -   `log_entries`: A list of `LogEntry` objects representing the parsed log file.
-   **Returns**: An `IntelligenceReport` object containing the complete analysis, including error patterns, correlations, anomalies, and more.

#### Example Usage

```python
from intelligence_engine import IntelligenceEngine
from data_models import IntelligenceReport

# Assume 'log_entries' is a list of LogEntry objects
# and 'config' is a valid ChunkingConfig instance.

engine = IntelligenceEngine(config)
report: IntelligenceReport = engine.analyze(log_entries)

# Now you can access the structured analysis results
print(f"Found {len(report.error_patterns)} unique error patterns.")
for cluster in report.semantic_clusters:
    print(f"Cluster '{cluster.label}': {len(cluster.chunk_ids)} chunks")

```

### AdvancedReporter

Multi-format report generation with LLM optimization.

```python
class AdvancedReporter:
    def __init__(self, console: Optional[Console] = None)
    def display_chunking_results(self, result: ChunkingResult) -> None
    def save_detailed_report(self, result: ChunkingResult, chunks_dir: Path,
                           reports_dir: Path, base_name: str, **options) -> None
```

#### Methods

**`save_detailed_report(result: ChunkingResult, chunks_dir: Path, reports_dir: Path, base_name: str, **options) -> None`**

- **Purpose**: Generate comprehensive reports in multiple formats
- **Parameters**:
  - `result`: ChunkingResult to report on
  - `chunks_dir`: Directory for temporary chunk files
  - `reports_dir`: Directory for final reports
  - `base_name`: Base filename for reports
  - `llm_token_limit`: int = 50000 - Token limit for standard report
  - `llm_ultra_compact`: bool = False - Generate ultra-compact report
  - `llm_error_only`: bool = False - Generate error-only report
  - `llm_summary_mode`: bool = False - Generate summary report
  - `llm_multi_report`: bool = False - Generate all report formats
  - Additional smart analysis options

## Configuration

### ChunkingConfig

Main configuration class using Pydantic for validation.

```python
@dataclass
class ChunkingConfig(BaseModel):
    # Core chunking parameters
    target_tokens: int = Field(100000, gt=0, description="Target tokens per chunk")
    max_tokens: int = Field(150000, gt=0, description="Maximum tokens per chunk")
    overlap_ratio: float = Field(0.15, ge=0, le=1, description="Overlap ratio between chunks")

    # Plugin configuration
    enabled_plugins: List[str] = Field(default_factory=lambda: ["semantic", "temporal", "pattern"])
    plugin_weights: Dict[str, float] = Field(default_factory=dict)

    # ML model settings
    semantic_model: str = Field("all-MiniLM-L6-v2", description="Sentence transformer model")
    semantic_threshold: float = Field(0.3, ge=0, le=1, description="Semantic similarity threshold")
    perplexity_model: str = Field("gpt2", description="Perplexity calculation model")
    perplexity_threshold: float = Field(50.0, gt=0, description="Perplexity threshold")

    # Preprocessing settings
    enable_deduplication: bool = Field(True, description="Enable intelligent deduplication")
    dedup_threshold: int = Field(5, ge=1, description="Minimum occurrences for deduplication")
    fuzzy_threshold: int = Field(85, ge=0, le=100, description="Fuzzy matching threshold")

    # Performance settings
    batch_size: int = Field(8, ge=1, description="Batch size for processing")
    max_workers: Optional[int] = Field(None, description="Maximum parallel workers")
    use_gpu: bool = Field(True, description="Enable GPU acceleration")

    # Output settings
    save_metadata: bool = Field(True, description="Save processing metadata")
    rich_display: bool = Field(True, description="Enable rich terminal display")
```

#### Configuration Examples

**Basic Configuration**

```python
config = ChunkingConfig(
    target_tokens=75000,
    enabled_plugins=["semantic", "pattern"],
    semantic_threshold=0.25
)
```

**High-Performance Configuration**

```python
config = ChunkingConfig(
    target_tokens=50000,
    batch_size=16,
    max_workers=8,
    use_gpu=True,
    enabled_plugins=["semantic", "temporal", "pattern"]
)
```

**Memory-Optimized Configuration**

```python
config = ChunkingConfig(
    target_tokens=25000,
    batch_size=4,
    max_workers=2,
    use_gpu=False,
    enabled_plugins=["pattern"]  # Minimal plugins
)
```

#### Configuration Validation

The configuration uses Pydantic validators for automatic validation:

```python
from config import ChunkingConfig
from pydantic import ValidationError

try:
    config = ChunkingConfig(
        target_tokens=-1000  # Invalid: must be positive
    )
except ValidationError as e:
    print(f"Configuration error: {e}")
```

## Data Models

### ChunkingResult

Contains complete results from the chunking process.

```python
@dataclass
class ChunkingResult:
    chunks: List[Tuple[str, ChunkInfo]]           # List of (text, metadata) tuples
    preprocessing_stats: Dict[str, Any]           # Preprocessing statistics
    plugin_stats: Dict[str, Dict[str, Any]]      # Per-plugin performance stats
    quality_metrics: Dict[str, float]            # Overall quality metrics
    config_used: ChunkingConfig                  # Configuration used for processing
    total_processing_time: float                 # Total processing time in seconds
```

#### Accessing Results

```python
result = engine.chunk_text(text)

# Access chunks
for chunk_text, chunk_info in result.chunks:
    print(f"Chunk {chunk_info.chunk_id}: {chunk_info.estimated_tokens} tokens")
    print(f"Quality: {chunk_info.quality_score:.2f}")

# Access statistics
print(f"Original lines: {result.preprocessing_stats['original_lines']}")
print(f"Processing time: {result.total_processing_time:.2f}s")
print(f"Average quality: {result.quality_metrics['avg_quality_score']:.2f}")
```

### ChunkInfo

Metadata for individual chunks.

```python
@dataclass
class ChunkInfo:
    chunk_id: int                                 # Unique chunk identifier
    start_pos: int                               # Start position in original text
    end_pos: int                                 # End position in original text
    estimated_tokens: int                       # Estimated token count
    actual_tokens: Optional[int]                # Actual token count (if calculated)
    original_lines: int                         # Number of original lines
    overlap_with_previous_chars: int            # Overlap with previous chunk
    overlap_with_next_chars: int               # Overlap with next chunk
    method_used: str                           # Chunking method used
    plugin_scores: Dict[str, float]            # Per-plugin boundary scores
    boundaries_found: List[int]                # Boundary positions found
    deduplicated_lines: int                    # Lines removed by deduplication
    compression_ratio: float                   # Compression achieved
    semantic_coherence: Optional[float]        # Semantic coherence score
    temporal_anomalies: List[str]              # Temporal anomalies detected
    detected_patterns: List[str]               # Patterns detected in chunk
    quality_score: float                       # Overall quality score (0.0-1.0)
```

### LogEntry

Represents a parsed log entry with metadata.

```python
@dataclass
class LogEntry:
    line_number: int                            # Original line number
    timestamp: Optional[datetime]               # Parsed timestamp
    level: Optional[str]                       # Log level (INFO, ERROR, etc.)
    message: str                               # Log message content
    source: Optional[str]                      # Source/logger name
    metadata: Dict[str, Any]                   # Additional metadata
```

### Smart Analysis Data Models

#### ErrorPattern

```python
@dataclass
class ErrorPattern:
    pattern: str                               # Normalized error pattern
    message_template: str                      # Human-readable template
    occurrences: int                          # Number of occurrences
    timestamps: List[str]                     # Occurrence timestamps
    severity: str                             # Error severity level
    chunks: List[Tuple[str, ChunkInfo]]       # Associated chunks
    confidence: float                         # Confidence score (0.0-1.0)
```

#### CorrelationGroup

```python
@dataclass
class CorrelationGroup:
    name: str                                 # Correlation description
    error_patterns: List[str]                 # Related error patterns
    time_window: str                          # Time window for correlation
    frequency: int                            # Co-occurrence frequency
    confidence: float                         # Confidence score (0.0-1.0)
```

#### AnomalyDetection

```python
@dataclass
class AnomalyDetection:
    event: str                                # Anomalous event description
    anomaly_type: str                         # Type of anomaly
    description: str                          # Detailed description
    confidence: float                         # Confidence score (0.0-1.0)
    normal_baseline: str                      # Normal behavior baseline
```

#### TimelineEvent

```python
@dataclass
class TimelineEvent:
    timestamp: Optional[datetime]             # Event timestamp
    event_type: str                          # Type of event
    description: str                         # Event description
    related_chunks: List[int]                # Related chunk IDs
    confidence: float                        # Confidence score (0.0-1.0)
    causality_links: List[int]               # Causally linked event indices
```

## Plugin Interface

### BaseChunkingPlugin

Abstract base class for all chunking plugins.

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from rich.console import Console

class BaseChunkingPlugin(ABC):
    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.config: Optional[ChunkingConfig] = None
        self.console: Optional[Console] = None

    @abstractmethod
    def initialize(self, config: ChunkingConfig, console: Console) -> bool:
        """Initialize plugin with configuration and console"""
        pass

    @abstractmethod
    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """Find potential chunk boundaries in text"""
        pass

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score chunk quality (0.0-1.0)"""
        return 0.5  # Default neutral score

    @abstractmethod
    def analyze_chunks(self, chunks: List[Tuple[str, ChunkInfo]]) -> Dict[str, Any]:
        """Perform detailed analysis on generated chunks.

        Returns:
            Dictionary containing structured analysis data.
            Keys should be unique to the plugin to avoid conflicts.
        """
        return {}

    def cleanup(self) -> None:
        """Clean up plugin resources"""
        pass
```

### Plugin Implementation Example

```python
from plugins.base import BaseChunkingPlugin
import re

class CustomPatternPlugin(BaseChunkingPlugin):
    def __init__(self):
        super().__init__()
        self.name = "custom_pattern"
        self.description = "Custom pattern-based chunking"
        self.patterns = []

    def initialize(self, config: ChunkingConfig, console: Console) -> bool:
        self.config = config
        self.console = console

        # Load custom patterns from config
        self.patterns = getattr(config, 'custom_patterns', [
            r'^\[ERROR\]',
            r'^\[FATAL\]',
            r'^=+\s+\w+\s+=+$'  # Section headers
        ])

        if console:
            console.print(f"[green]Initialized {self.name} with {len(self.patterns)} patterns[/green]")

        return True

    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        boundaries = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            for pattern in self.patterns:
                if re.search(pattern, line):
                    boundaries.append(i)
                    break

        return boundaries

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        # Score based on pattern matches
        pattern_matches = sum(1 for line in chunk.split('\n')
                            for pattern in self.patterns
                            if re.search(pattern, line))

        # Higher score for chunks with more pattern matches
        max_possible_matches = len(chunk.split('\n'))
        return min(0.5 + (pattern_matches / max_possible_matches), 1.0)
```

## Analysis Classes

### AdaptiveChunker

Analyzes content and recommends optimal configuration.

```python
class AdaptiveChunker:
    def analyze_and_recommend(self, text: str) -> ContentAnalysis
    def _classify_content_type(self, text: str) -> Tuple[str, float]
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> ChunkingConfig
```

#### Methods

**`analyze_and_recommend(text: str) -> ContentAnalysis`**

- **Purpose**: Analyze content and generate configuration recommendations
- **Parameters**:
  - `text`: Sample text to analyze (typically first 50KB)
- **Returns**: ContentAnalysis with detected type and recommended config

#### Example Usage

```python
from adaptive_config import AdaptiveChunker

chunker = AdaptiveChunker()
analysis = chunker.analyze_and_recommend(sample_text)

print(f"Detected content type: {analysis.content_type}")
print(f"Confidence: {analysis.confidence:.1%}")
print(f"Recommended target tokens: {analysis.recommended_config.target_tokens}")
```

### ContentAnalysis

Results from adaptive content analysis.

```python
@dataclass
class ContentAnalysis:
    content_type: str                         # Detected content type
    confidence: float                        # Detection confidence (0.0-1.0)
    characteristics: Dict[str, Any]          # Content characteristics
    recommended_config: ChunkingConfig       # Recommended configuration
    reasoning: List[str]                     # Human-readable reasoning
```

## Utility Functions

### Configuration Utilities

```python
def load_config_from_file(config_path: str) -> ChunkingConfig:
    """Load configuration from JSON file"""

def create_config_from_args(args: argparse.Namespace) -> ChunkingConfig:
    """Create configuration from CLI arguments"""

def merge_configs(base: ChunkingConfig, override: ChunkingConfig) -> ChunkingConfig:
    """Merge two configurations with override taking precedence"""
```

### Text Processing Utilities

```python
def estimate_tokens(text: str, method: str = "simple") -> int:
    """Estimate token count for text"""

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""

def extract_timestamps(text: str) -> List[datetime]:
    """Extract timestamps from text"""
```

### Validation Utilities

```python
def validate_file_path(path: str) -> bool:
    """Validate that file path exists and is readable"""

def validate_output_directory(path: str) -> bool:
    """Validate that output directory is writable"""

def validate_plugin_file(path: str) -> bool:
    """Validate that plugin file contains valid plugin class"""
```

## Command Line Interface

### Main CLI Function

```python
def main() -> int:
    """Main entry point for CLI"""
    parser = create_cli_parser()
    args = parser.parse_args()

    # Process arguments and execute
    return process_command(args)
```

### CLI Parser

```python
def create_cli_parser() -> argparse.ArgumentParser:
    """Create comprehensive CLI argument parser"""

    parser = argparse.ArgumentParser(
        description='Advanced Log Chunking Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add all command line arguments
    # See cli.py for complete implementation

    return parser
```

### Command Functions

```python
def process_log_file(args: argparse.Namespace, config: ChunkingConfig,
                    console: Optional[Console]) -> int:
    """Main log processing pipeline"""

def analyze_content_only(file_path: str) -> None:
    """Analyze content without chunking"""

def validate_installation() -> bool:
    """Validate framework installation"""

def create_sample_config() -> None:
    """Create sample configuration file"""
```

## Error Handling

### Exception Hierarchy

```python
class LogChunkerError(Exception):
    """Base exception for all log chunker errors"""

class ConfigurationError(LogChunkerError):
    """Configuration validation and loading errors"""

class PluginError(LogChunkerError):
    """Plugin loading and execution errors"""

class ProcessingError(LogChunkerError):
    """Text processing and chunking errors"""

class ValidationError(LogChunkerError):
    """Input validation errors"""
```

### Error Handling Patterns

```python
try:
    result = engine.chunk_text(text)
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    return 1
except PluginError as e:
    logger.warning(f"Plugin error: {e}")
    # Continue with available plugins
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    return 1
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    return 1
```

## Performance Considerations

### Memory Usage

- **ChunkingResult**: Stores all chunks in memory
- **Plugin caches**: May consume significant memory for large texts
- **ML models**: Transformer models require GPU/CPU memory

### Processing Speed

- **Semantic analysis**: Requires ML model inference (can be slow)
- **Pattern matching**: Fast regex-based processing
- **Boundary fusion**: Linear time complexity
- **Report generation**: I/O bound operation

### Optimization Tips

1. **Use appropriate batch sizes** for your hardware
2. **Enable GPU acceleration** when available
3. **Disable unused plugins** to reduce overhead
4. **Use streaming** for very large files (future feature)
5. **Cache model outputs** when processing similar content

## Integration Examples

### Programmatic Usage

```python
from chunking_engine import ChunkingEngine
from intelligence_engine import IntelligenceEngine
from config import ChunkingConfig
from reporter import Reporter

# Setup
config = ChunkingConfig(target_tokens=50000, enabled_plugins=["semantic", "pattern"])
intelligence_engine = IntelligenceEngine(config)
engine = ChunkingEngine(config)
reporter = Reporter(config)

# Process
chunks = engine.chunk_file("application.log", intelligence_engine)
report = intelligence_engine.analyze(chunks, "application.log")

# Generate reports
from pathlib import Path
reporter.save_intelligence_report(report, Path("reports"))

# Cleanup
engine.cleanup()
```

### Custom Plugin Integration

```python
# Load custom plugin
engine.plugin_manager.load_external_plugin("my_custom_plugin.py")

# Use with specific configuration
config = ChunkingConfig(
    enabled_plugins=["my_custom", "semantic"],
    plugin_weights={"my_custom": 0.7, "semantic": 0.3}
)
```

### Batch Processing

```python
import glob
from pathlib import Path

config = ChunkingConfig(target_tokens=25000)  # Smaller chunks for batch processing
engine = AdvancedChunkingEngine(config)

for log_file in glob.glob("logs/*.log"):
    print(f"Processing {log_file}")

    with open(log_file, "r") as f:
        text = f.read()

    result = engine.chunk_text(text)

    # Save results
    base_name = Path(log_file).stem
    reporter.save_detailed_report(result, Path("chunks"), Path("reports"), base_name)

engine.cleanup()
```
