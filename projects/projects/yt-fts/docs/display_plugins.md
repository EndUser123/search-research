# Display Plugin Guide

This guide explains how to create and use display plugins for yt-fts.

## Overview

Display plugins allow you to customize how yt-fts outputs information for different commands:
- `search` - Full-text and vector search results
- `download` / `batch-download` - Download progress and results
- `import` - Channel import operations
- `status` - System status information
- `list` - Listing operations (channels, videos, etc.)

## Plugin Interface

All display plugins must inherit from `DisplayPlugin` and implement the required methods:

```python
from yt_fts.display import DisplayPlugin, PluginContext, register_plugin

class MyDisplayPlugin(DisplayPlugin):
    """My custom display plugin."""

    # Specify which commands this plugin supports
    # Empty list = supports all commands
    supported_commands = ["search", "download"]

    def __init__(self, context: PluginContext):
        """Initialize with plugin context."""
        super().__init__(context)
        # Access context.command, context.console, context.options

    def get_name(self) -> str:
        """Return the plugin name."""
        return "my_plugin"

    def configure(self, options: dict) -> None:
        """Configure plugin with options."""
        super().configure(options)
        # Handle custom options

    # Implement command-specific methods
    def display_search_results(self, results: dict) -> None:
        """Display search results."""
        pass

    def display_channel_header(self, channel_info: dict) -> None:
        """Display channel processing header."""
        pass

    # ... other methods
```

## Plugin Context

The `PluginContext` provides:

- `command`: The command name (e.g., "search", "download")
- `console`: Rich `Console` instance for output
- `options`: Dictionary of command-specific options
- `config_dir`: Path to configuration directory
- `db_path`: Path to database file

## Required Methods

### Core Methods

| Method | Purpose |
|--------|---------|
| `get_name()` | Return plugin name (snake_case) |
| `configure(options)` | Configure plugin with options |

### Command-Specific Methods

| Method | Command | Purpose |
|--------|---------|---------|
| `display_search_results(results)` | search | Display search results |
| `display_channel_header(info)` | download | Show channel header |
| `display_rss_status(info)` | download | Show RSS check results |
| `display_download_result(info)` | download | Show download result |
| `display_batch_summary(info)` | download | Show batch summary |
| `display_status(info)` | status | Show system status |
| `display_import_progress(info)` | import | Show import progress |
| `display_import_result(info)` | import | Show import result |

### Generic Methods

| Method | Purpose |
|--------|---------|
| `display(data)` | Generic display fallback |
| `error(message)` | Display error message |
| `warning(message)` | Display warning message |
| `info(message)` | Display info message |
| `cleanup()` | Cleanup resources |

## Installation

### Built-in Plugins

Built-in plugins are automatically available:
- `default` - Clean Rich-formatted output (default)
- `compact` - Minimal, machine-friendly output
- `json` - Machine-readable JSON output

### User Plugins

Place user plugins in `~/.config/yt-fts/plugins/`:

```
~/.config/yt-fts/plugins/
├── my_plugin.py
└── another_plugin/
    └── __init__.py
```

Plugins are automatically discovered at runtime.

### Manual Registration

Register a plugin programmatically:

```python
from yt_fts.display import register_plugin
from my_module import MyCustomPlugin

register_plugin("custom", MyCustomPlugin)
```

## Usage

### Command Line

Use the `--display-plugin` option:

```bash
# Use compact output for search
yt-fts search "query" --display-plugin compact

# Use JSON output for batch downloads
yt-fts batch-download channels.txt --display-plugin json

# Use custom plugin
yt-fts search "query" --display-plugin my_plugin
```

### Python API

```python
from rich.console import Console
from yt_fts.display import create_plugin, PluginContext

# Create plugin context
context = PluginContext(
    command="search",
    console=Console(),
    options={"limit": 10}
)

# Create plugin instance
plugin = create_plugin("default", context)

# Use plugin
plugin.display_search_results({
    "query": "test",
    "matches": [...],
    "total_matches": 5
})
```

## Example Plugins

### Custom Search Plugin

```python
from typing import Any
from yt_fts.display import DisplayPlugin, PluginContext

class MarkdownSearchPlugin(DisplayPlugin):
    """Output search results as Markdown."""

    supported_commands = ["search"]

    def get_name(self) -> str:
        return "markdown_search"

    def display_search_results(self, results: dict[str, Any]) -> None:
        query = results.get("query", "")
        matches = results.get("matches", [])

        self.console.print(f"# Search Results for: {query}\n")

        for quote in matches:
            channel = quote.get("channel_name", "Unknown")
            video = quote.get("video_title", "")
            text = quote.get("text", "")
            link = quote.get("link", "")

            self.console.print(f"## {video}")
            self.console.print(f"*{channel}*\n")
            self.console.print(f"> {text}\n")
            self.console.print(f"[Link]({link})\n")
```

### Custom Progress Plugin

```python
from typing import Any
from yt_fts.display import DisplayPlugin, PluginContext

class EmojiDownloadPlugin(DisplayPlugin):
    """Use emojis for download status."""

    supported_commands = ["download", "batch-download"]

    def get_name(self) -> str:
        return "emoji"

    def display_channel_header(self, channel_info: dict) -> None:
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]

        self.console.print(f"📺 [{index}/{total}] {name}")

    def display_download_result(self, result_info: dict) -> None:
        if result_info["success"]:
            count = result_info.get("videos_count", 0)
            self.console.print(f"✅ Downloaded {count} videos")
        else:
            self.console.print(f"❌ Failed: {result_info.get('error', 'Unknown')}")
```

## Plugin Discovery

Plugins are discovered from:

1. Built-in plugins (always available)
2. `~/.config/yt-fts/plugins/*.py` (user plugins)
3. `~/.config/yt-fts/plugins/*/__init__.py` (plugin packages)

### Auto-Registration

Plugins with a class inheriting `DisplayPlugin` are automatically registered.

The plugin name is derived from the class name (CamelCase -> snake_case):

- `MyCustomPlugin` -> `my_custom`
- `JSONOutput` -> `json_output`

Override with `plugin_name` class attribute:

```python
class MyPlugin(DisplayPlugin):
    plugin_name = "my_custom_name"
    # ...
```

## Best Practices

1. **Use Rich formatting**: Leverage `context.console` for styled output
2. **Handle encoding issues**: Use fallback console for Windows encoding errors
3. **Keep output focused**: Only show relevant information
4. **Document options**: Clearly document any custom configuration options
5. **Test across commands**: Ensure plugin works with all supported commands

## Migrating from Legacy Plugins

Legacy plugins in `yt_fts.ui.plugins` are automatically wrapped and available with the `legacy_` prefix:

- `default` -> `legacy_default`
- `compact` -> `legacy_compact`
- `detailed` -> `legacy_detailed`
- `minimal` -> `legacy_minimal`
- `progress` -> `legacy_progress`
- `table` -> `legacy_table`

To migrate a legacy plugin:

1. Change import from `yt_fts.ui.plugins.base` to `yt_fts.display.base`
2. Update method signatures to use new `DisplayPlugin` base class
3. Implement `get_name()` method
4. Add `supported_commands` class attribute
5. Update context usage (use `context.options` instead of instance variables)
