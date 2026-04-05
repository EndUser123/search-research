# User Guide

A comprehensive guide to using the Advanced Log Chunking Framework for intelligent log analysis and LLM preprocessing.

## Quick Start

### Basic Usage
```bash
# Analyze any log file with optimal settings
python log_chunker.py your_logs.txt

# This automatically:
# - Analyzes content and applies optimal configuration
# - Generates all report formats for comprehensive analysis
# - Uses intelligent chunking with multiple strategies
# - Cleans up temporary files
```

### First Run Example
```bash
# Create a test log file
echo "2024-01-15 10:00:00 INFO Application started
2024-01-15 10:00:01 ERROR Database connection failed
2024-01-15 10:00:02 WARN Retrying connection (attempt 1/3)
2024-01-15 10:00:03 INFO Database connection established
2024-01-15 10:00:04 INFO Processing 1000 records" > sample.log

# Process with framework
python log_chunker.py sample.log
```

## Core Concepts

### What is Log Chunking?
Log chunking intelligently divides large log files into semantically coherent segments that:
- Preserve contextual relationships between related log entries
- Fit within LLM token limits for analysis
- Maintain temporal and causal relationships
- Optimize for downstream processing

### Multi-Strategy Approach
The framework uses multiple chunking strategies simultaneously:

- **Semantic Chunking**: Groups related content by meaning
- **Temporal Analysis**: Identifies time-based boundaries
- **Pattern Recognition**: Detects structural boundaries
- **Conversation Awareness**: Handles chat logs and dialogue

## Report Types Generated

By default, the framework generates 4 complementary report formats:

### 1. Standard Report (50K tokens)
- **File**: `*_llm_optimized.md`
- **Purpose**: Comprehensive analysis with all high-quality chunks
- **Best for**: Detailed investigation, root cause analysis

### 2. Ultra-Compact Report (10K tokens)
- **File**: `*_llm_ultra.md`
- **Purpose**: Error-focused, minimal formatting for fast processing
- **Best for**: Quick error overview, emergency analysis

### 3. Executive Summary (15K tokens)
- **File**: `*_llm_summary.md`
- **Purpose**: Key findings and critical issues overview
- **Best for**: Management reporting, incident summaries

### 4. Error-Only Standard (30K tokens)
- **File**: `*_llm_errors_only.md`
- **Purpose**: Full formatting but errors/warnings only
- **Best for**: Troubleshooting, error pattern analysis

### 5. Smart Analysis Report (when enabled)
- **File**: `*_smart_analysis.md` or `*_smart_analysis.json`
- **Purpose**: Advanced pattern detection, correlations, anomalies
- **Best for**: Deep investigation, pattern discovery

## Command-Line Usage

### Basic Commands

```bash
# Basic processing with all defaults
python log_chunker.py logs.txt

# Analyze content without processing
python log_chunker.py analyze logs.txt

# Generate single report format instead of all
python log_chunker.py logs.txt --llm-single-report --llm-ultra-compact

# Keep temporary files for inspection
python log_chunker.py logs.txt --keep-chunks
```

### Smart Analysis Features

```bash
# Enable all smart analysis features
python log_chunker.py logs.txt --llm-smart-mode

# Enable specific smart features
python log_chunker.py logs.txt --llm-dedupe-errors --llm-correlate --llm-timeline

# Generate structured JSON for programmatic use
python log_chunker.py logs.txt --llm-json --llm-smart-mode
```

### Configuration Control

```bash
# Disable auto-optimization (get prompted for changes)
python log_chunker.py logs.txt --no-auto-optimize

# Use custom configuration file
python log_chunker.py logs.txt --config my_settings.json

# Generate sample configuration
python log_chunker.py sample-config
```

### Plugin Control

```bash
# Enable specific plugins only
python log_chunker.py logs.txt --enable-semantic --enable-temporal

# Disable specific plugins
python log_chunker.py logs.txt --disable-pattern

# Disable all plugins (minimal processing)
python log_chunker.py logs.txt --disable-all-plugins
```

### Performance Tuning

```bash
# High-performance processing
python log_chunker.py logs.txt --target-tokens 75000 --batch-size 32 --max-workers 8

# Disable GPU (force CPU processing)
python log_chunker.py logs.txt --no-gpu

# Minimal resource usage
python log_chunker.py logs.txt --batch-size 4 --max-workers 2
```

## Understanding Output

### Directory Structure
After processing, you'll see:
```
reports/
├── your_logs_metadata.json          # Complete processing metadata
├── your_logs_report.md              # Human-readable summary
├── your_logs_llm_optimized.md       # Standard LLM report (50K)
├── your_logs_llm_ultra.md           # Ultra-compact report (10K)
├── your_logs_llm_summary.md         # Executive summary (15K)
├── your_logs_llm_errors_only.md     # Error-focused report (30K)
└── your_logs_smart_analysis.md      # Smart analysis (if enabled)
```

**Note**: When running `log_chunker.py` in a compatible terminal (e.g., one supporting Rich output), the paths to the generated report files will be displayed as clickable links, allowing for quick access to the reports.

### Reading Reports

#### Standard Report Format
```markdown
# Log Analysis: your_logs
Generated: 2024-01-15 10:30:15
Total Original Chunks: 45
Preprocessing: 1,250 → 1,180 lines

## Key Insights
- Unique patterns detected: 23
- Processing plugins: semantic, temporal, pattern

## Selected High-Quality Log Chunks

### Chunk 1 (Quality: 0.87)
**Method**: multi_plugin | **Patterns**: error, database, timeout

```
[Log content here]
```
```

#### Smart Analysis Report
```markdown
# Smart Analysis: your_logs

## 🔍 Deduplicated Error Patterns

### 🔴 Pattern 1: Critical
**Occurrences**: 15×
**Confidence**: 85%
**Template**: `Database connection timeout after [NUMBER] seconds`

## 🔗 Error Correlations

### Correlation 1: Database timeout → Service restart
**Frequency**: 8 co-occurrences
**Confidence**: 92%
```

### Metadata File
The `*_metadata.json` contains complete processing information:
```json
{
  "chunks": [...],
  "preprocessing_stats": {
    "original_lines": 1250,
    "processed_lines": 1180,
    "compression_ratio": 0.94
  },
  "plugin_stats": {
    "semantic": {"boundaries_found": 23, "avg_chunk_score": 0.78}
  },
  "quality_metrics": {
    "avg_chunk_size": 2340,
    "avg_quality_score": 0.81
  }
}
```

## Advanced Usage

### Custom Configuration

Create `my_config.json`:
```json
{
  "target_tokens": 75000,
  "overlap_ratio": 0.2,
  "enabled_plugins": ["semantic", "temporal", "pattern"],
  "semantic_threshold": 0.25,
  "dedup_threshold": 3,
  "fuzzy_threshold": 90,
  "semantic_clustering": {
    "enabled": true,
    "model_name": "all-MiniLM-L6-v2",
    "min_cluster_size": 5,
    "min_samples": 3,
    "cache_embeddings": true
  },
  "advanced_anomaly": {
    "enabled": true,
    "contamination": 0.1,
    "n_estimators": 100,
    "max_samples": "auto",
    "random_state": 42
  }
}
```

### Enhanced ML Features Configuration

**Semantic Clustering** (requires `sentence-transformers`, `hdbscan`):
- `enabled`: Enable advanced semantic clustering
- `model_name`: Sentence transformer model (default: "all-MiniLM-L6-v2")
- `min_cluster_size`: Minimum HDBSCAN cluster size
- `min_samples`: Minimum samples for core points
- `cache_embeddings`: Cache embeddings for performance

**Advanced Anomaly Detection** (requires `scikit-learn`):
- `enabled`: Enable ML-powered anomaly detection
- `contamination`: Expected proportion of anomalies (0.1 = 10%)
- `n_estimators`: Number of isolation trees
- `max_samples`: Samples per tree ("auto" for optimal)
- `random_state`: Seed for reproducible results

**Note**: Both features automatically fall back to simpler algorithms when dependencies are unavailable.

Use with: `python log_chunker.py logs.txt --config my_config.json`

### Batch Processing

```bash
# Process multiple files
for file in *.log; do
    python log_chunker.py "$file" --output-dir "chunks_$file" --reports-dir "reports_$file"
done
```

### Integration with Other Tools

#### Pipe Output to LLM Analysis
```bash
# Generate ultra-compact for quick analysis
python log_chunker.py logs.txt --llm-single-report --llm-ultra-compact
cat reports/logs_llm_ultra.md | your_llm_tool
```

#### Extract JSON for Processing
```bash
# Generate structured JSON
python log_chunker.py logs.txt --llm-json --llm-smart-mode
python process_analysis.py reports/logs_smart_analysis.json
```

## Troubleshooting Common Issues

### Large Files
```bash
# For very large files (>100MB)
python log_chunker.py huge.log --batch-size 8 --max-workers 4 --target-tokens 25000
```

### Memory Issues
```bash
# Reduce memory usage
python log_chunker.py logs.txt --no-gpu --batch-size 4 --disable-all-plugins
```

### Encoding Issues
The framework automatically handles UTF-8 and Latin-1 encoding. For other encodings:
```bash
# Convert to UTF-8 first
iconv -f ISO-8859-1 -t UTF-8 logs.txt > logs_utf8.txt
python log_chunker.py logs_utf8.txt
```

### No Output Generated
Check for:
- File permissions on output directories
- Sufficient disk space
- Input file format (binary files not supported)

## Best Practices

### For Different Log Types

#### Application Logs
```bash
python log_chunker.py app.log --enable-semantic --enable-temporal --llm-smart-mode
```

#### Chat/Conversation Logs
```bash
python log_chunker.py chat.log --enable-conversation --enable-semantic
```

#### Mixed Documentation
```bash
python log_chunker.py docs.txt --enable-semantic --target-tokens 50000
```

#### Error Investigation
```bash
python log_chunker.py error.log --llm-smart-mode --llm-dedupe-errors --llm-correlate
```

### For LLM Analysis

1. **Use appropriate report type** for your analysis needs
2. **Enable smart analysis** for pattern detection
3. **Check quality scores** in metadata for chunk reliability
4. **Use guided prompts** from smart analysis reports

### Performance Optimization

1. **Start with defaults** - they're optimized for most cases
2. **Use GPU acceleration** when available for semantic analysis
3. **Adjust batch size** based on available memory
4. **Profile large files** with `analyze` command first

## Next Steps

- **[Configuration Reference](CONFIGURATION.md)** - Detailed configuration options
- **[API Documentation](API.md)** - For programmatic usage
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Creating custom plugins
- **[Examples](EXAMPLES.md)** - Real-world usage examples
