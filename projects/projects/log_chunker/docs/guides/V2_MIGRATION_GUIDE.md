'''# Log Chunker V2 Migration Guide

This guide provides instructions for migrating from v1 to v2 of the Log Chunker framework.

## Key Changes

- **CLI Structure**: The command-line interface has been refactored to use subcommands. The old, flat structure is no longer supported.
- **"Smart by Default" Philosophy**: The tool now runs a full analysis by default. The old flags for enabling specific features are now used to override the default behavior.
- **`IntelligenceReport` Caching**: The `IntelligenceReport` is now cached to disk, allowing for faster report generation.

## Migration Steps

### 1. Update CLI Usage

The old CLI commands are no longer valid. You must update your scripts to use the new subcommand structure.

**Old (v1):**
```bash
# Basic chunking
python log_chunker.py my_log.txt

# Smart analysis
python log_chunker.py my_log.txt --llm-smart-mode
```

**New (v2):**
```bash
# Full analysis (chunking, intelligence, and reporting)
python log_chunker.py analyze my_log.txt

# Generate a report from a cached analysis
python log_chunker.py report /path/to/reports/my_log_IntelligenceReport.json --type summary
```

### 2. Update Custom Plugins

If you have created custom plugins, you must update them to implement the `analyze_chunks` method. This method is now required for all plugins.

**Old (v1):**
```python
class MyCustomPlugin(BaseChunkingPlugin):
    # ...
    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        # ...
```

**New (v2):**
```python
class MyCustomPlugin(BaseChunkingPlugin):
    # ...
    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        # ...

    def analyze_chunks(self, chunks: List[Tuple[str, ChunkInfo]]) -> Dict[str, Any]:
        # Add your analysis logic here
        return {"my_custom_analysis": {"status": "ok"}}
```

### 3. Update Configuration

The `enabled_plugins` list in your configuration file should be reviewed to ensure it only contains the plugins you want to use. The `pattern` plugin is now enabled by default.
'''
