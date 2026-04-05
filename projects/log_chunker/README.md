# Advanced Log Chunking Framework

A comprehensive, plugin-based system for intelligent log analysis and chunking, optimized for LLM processing.

**For development guidelines, please see the [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md).**

## Features

* 🔌 **Plugin Architecture**: Extensible chunking strategies
* 🧠 **ML-Powered**: Semantic clustering, advanced anomaly detection, perplexity, and temporal analysis
* 🚀 **High Performance**: Async processing with GPU acceleration
* 📊 **Rich Reporting**: Beautiful terminal output and comprehensive reports
* 🔄 **Smart Deduplication**: Fuzzy matching and pattern normalization
* ⚙️ **Configurable**: Extensive configuration options
* 💡 **Auto-Optimization**: Automatically analyzes logs and applies optimal settings by default
* 🤖 **Smart Analysis**: Error deduplication, correlation detection, anomaly highlighting, and timeline intelligence
* 📈 **Multi-Report Generation**: Generates all complementary report formats by default for comprehensive LLM analysis
* 🎯 **LLM Optimization**: Ultra-compact, summary, error-focused, and comprehensive report types

## Usage

### Analyzing a Log File

To perform a full analysis of a log file, use the `analyze` command:

```bash
# Run the full analysis pipeline (chunking, intelligence, and reporting)
python log_chunker.py analyze my_log.txt

# Specify an output directory for reports
python log_chunker.py analyze my_log.txt --reports-dir /path/to/reports
```

### Generating a Report

To generate a specific report from a cached `IntelligenceReport.json` file, use the `report` command:

```bash
# Generate a summary report from a cached analysis
python log_chunker.py report /path/to/reports/my_log_IntelligenceReport.json --type summary
```

### Managing Configuration

To generate a sample configuration file, use the `config sample` command:

```bash
# Generate a sample config file
python log_chunker.py config sample
```

## Architecture

For a structured, machine-readable definition of the project's layout, scripts, and dependencies, see `PROJECT-CONFIG.yaml`.

```
log_chunker.py          # Main entry point with cross-directory execution support
├── config.py           # Configuration models
├── data_models.py      # Data structures
├── preprocessor.py     # Log preprocessing
├── chunking_engine.py  # Main chunking logic
├── plugin_manager.py   # Plugin system
├── reporter.py         # Multi-format report generation with smart analysis
├── intelligence_engine.py # Core analysis engine
├── cli.py              # Comprehensive command line interface
├── adaptive_config.py  # Content analysis and adaptive configuration
├── plugin_template.py  # Plugin template generation
└── plugins/
    ├── base.py        # Plugin base classes
    ├── semantic.py    # Semantic chunking
    └── other_plugins.py # Additional plugins
```

## Plugins

### Built-in Plugins

* **Semantic**: Uses sentence transformers for meaning-based boundaries
* **Perplexity**: Leverages LLM uncertainty for logical breaks
* **Temporal**: Detects time-based anomalies and patterns
* **Conversation**: Speaker-aware chunking for chat logs
* **Pattern**: Advanced regex and structural pattern detection

### Creating Custom Plugins

```bash
# Generate plugin template
python log_chunker.py create-plugin my_custom_chunker

# Use custom plugin
python log_chunker.py analyze logs.txt --plugin my_custom_chunker_plugin.py
```

## Configuration

### Sample Configuration

```bash
# Generate sample config
python log_chunker.py config sample
```

### Key Settings

* `target_tokens`: Target tokens per chunk (default: 100,000)
* `overlap_ratio`: Overlap between chunks (default: 0.15)
* `enable_deduplication`: Smart log deduplication (default: True)
* `enabled_plugins`: List of active plugins
* `semantic_threshold`: Semantic similarity threshold (default: 0.3)
* `plugin_weights`: Define influence of each plugin on boundary merging.
* `log_parsing_patterns`: Regex patterns for parsing log lines.
* `advanced_detection_patterns`: Regex patterns for categorizing log content.
* `perplexity_context_window`: Number of preceding sentences for perplexity calculation.

## Examples

### Conversation Log Analysis

```bash
python log_chunker.py chat.txt --enable-conversation --enable-temporal
```

### High-Performance Processing

```bash
python log_chunker.py huge_log.txt --batch-size 64 --max-workers 8
```

### Disable Deduplication

```bash
python log_chunker.py logs.txt --no-dedup --fuzzy-threshold 95
```

## Output

The framework generates:
* `chunks/`: Individual chunk files (automatically cleaned up unless `--keep-chunks`)
* `reports/`: Final analysis outputs including:
  * `metadata.json`: Comprehensive metadata
  * `report.md`: Markdown summary report
  * `*_llm_optimized.md`: Standard LLM-optimized format (50K tokens)
  * `*_llm_ultra.md`: Ultra-compact format (10K tokens, error-focused)
  * `*_llm_summary.md`: Executive summary format (15K tokens)
  * `*_llm_errors_only.md`: Error-focused standard format (30K tokens)
  * `*_smart_analysis.md/json`: Smart analysis with deduplication, correlations, anomalies

## Performance

* **GPU Acceleration**: Automatic detection and usage
* **Async Processing**: Non-blocking I/O operations
* **Batch Processing**: Configurable batch sizes
* **Memory Efficient**: Streaming for large files

## Dependencies

### Core (Required)

- rich >= 13.0.0
* pydantic >= 2.0.0
* numpy >= 1.21.0

### Optional (Enhanced Features)

- torch >= 2.0.0
* transformers >= 4.30.0
* sentence-transformers >= 2.2.0
* scikit-learn >= 1.3.0
* scipy >= 1.10.0
* langdetect >= 1.0.9
* fuzzywuzzy >= 0.18.0

## Smart Analysis Features

### Error Deduplication (`--llm-dedupe-errors`)
- Merges identical error patterns and shows frequencies
- Normalizes variable parts (timestamps, IDs, paths) for pattern recognition
- Confidence scoring based on occurrence frequency

### Correlation Analysis (`--llm-correlate`)
- Groups related errors that happen together within time windows
- Detects cause-and-effect relationships in error sequences
- Time-based correlation analysis with configurable windows

### Anomaly Detection (`--llm-anomaly-focus`)
- Highlights unusual patterns vs routine events
- **NEW**: ML-powered Isolation Forest anomaly detection with TF-IDF features
- Frequency-based fallback for high occurrence rates
- Error burst detection for multiple simultaneous issues

### Timeline Intelligence (`--llm-timeline`)
- Chronological format showing cause/effect chains
- Automatic timestamp extraction and event classification
- Causality linking for error-to-restart sequences

### Advanced Options
- `--llm-confidence`: Add confidence scores for all findings
- `--llm-cross-reference`: Cross-reference mapping between related errors
- `--llm-guided-prompts`: Embed analysis questions in reports
- `--llm-json`: Generate structured JSON format
- `--llm-smart-mode`: Enable all smart optimizations automatically

## Multi-Report Strategy

By default, the framework generates complementary analysis formats for comprehensive LLM analysis:

1. **Standard (50K tokens)**: Comprehensive analysis with all high-quality chunks
2. **Ultra-Compact (10K tokens)**: Error-focused with minimal formatting for fast processing
3. **Executive Summary (15K tokens)**: Key findings and critical issues overview
4. **Error-Only Standard (30K tokens)**: Full formatting but errors/warnings only

Use `--llm-single-report` with specific flags (like `--llm-ultra-compact`) to generate only one format instead.

## Installation

### Basic Installation

The log chunker works with standard Python dependencies:

```bash
pip install -r requirements.txt
```

### Enhanced ML Features

For advanced semantic clustering and anomaly detection capabilities, install the enhanced dependencies:

```bash
pip install -r requirements-enhanced.txt
```

**Enhanced features include**:
- **Semantic Clustering**: Uses sentence-transformers and HDBSCAN for intelligent content grouping
- **Advanced Anomaly Detection**: Isolation Forest with TF-IDF features for sophisticated anomaly identification

**Note**: All enhanced features include automatic fallback modes that work without the optional dependencies, ensuring the framework always functions regardless of your environment.

## License

MIT License - see LICENSE file for details.
