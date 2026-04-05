# Plugin System Migration Guide

## Phase 2.1: Plugin System Unification

**Status:** COMPLETE  
**Date:** 2026-01-05  
**Priority:** HIGH

## Overview

The yt-fts project had two incompatible display plugin systems that have been unified:

1. **New System:** `yt_fts.display/` - Modern, extensible plugin architecture
2. **Legacy System:** `yt_fts.ui.plugins/` - Deprecated, batch-download-only plugins

This migration consolidates both systems under the new `display/` API while maintaining backward compatibility through adapters.

## Changes Made

### 1. Deprecation Warnings Added

**File:** `src/yt_fts/ui/plugins/__init__.py`

- Added module-level deprecation warning
- All functions now emit deprecation warnings
- Clear migration path documented in warnings

```python
# Old import (now deprecated)
from yt_fts.ui.plugins import create_plugin

# Warning emitted:
# DeprecationWarning: The yt_fts.ui.plugins module is deprecated.
# Use yt_fts.display instead.
```

### 2. Batch Downloader Updated

**File:** `src/yt_fts/download/batch_downloader.py`

- Updated to use new `display/` system with `PluginContext`
- Graceful fallback to legacy system with deprecation warning
- Maintains backward compatibility

```python
# New approach
from yt_fts.display import PluginContext, create_plugin

context = PluginContext(
    command="download",
    console=self.console,
    options={"verbose": True},
)
plugin = create_plugin("default", context)
```

### 3. Legacy Adapter Auto-Registration

**File:** `src/yt_fts/display/discovery.py`

- Legacy plugins automatically wrapped in `LegacyDisplayPluginAdapter`
- Registered as `legacy_*` plugin names
- Suppresses deprecation warnings during internal loading

Available legacy adapters:
- `legacy_default`
- `legacy_compact`
- `legacy_detailed`
- `legacy_minimal`
- `legacy_table`
- `legacy_progress`

### 4. Display Module Exports

**File:** `src/yt_fts/display/__init__.py`

Added exports:
- `load_builtin_plugins()` - Load all built-in plugins
- `get_registry()` - Access global registry

## Migration Guide for Plugin Authors

### Creating New Plugins

**Old way (deprecated):**

```python
# src/yt_fts/ui/plugins/my_plugin.py
from .base import DisplayPlugin

class MyDisplayPlugin(DisplayPlugin):
    def __init__(self, console=None, verbose=True):
        self.console = console or Console()
        self.verbose = verbose
    
    def display_channel_header(self, channel_info):
        # Implementation
        pass
```

**New way (recommended):**

```python
# src/yt_fts/display/plugins/my_plugin.py
from ..base import DisplayPlugin, PluginContext

class MyDisplayPlugin(DisplayPlugin):
    # Specify which commands this plugin supports
    supported_commands = ["download", "search"]
    
    def __init__(self, context: PluginContext):
        super().__init__(context)
        # Access console via context
        # Access options via self.options
    
    def get_name(self) -> str:
        return "my_plugin"
    
    def display_channel_header(self, channel_info):
        # Implementation
        pass
    
    def display_search_results(self, results):
        # Can now support search commands too!
        pass
```

### Registering Custom Plugins

**Old way (deprecated):**

```python
from yt_fts.ui.plugins import register_plugin
from my_module import MyPlugin

register_plugin("my_plugin", MyPlugin)
```

**New way (recommended):**

```python
from yt_fts.display import register_plugin
from my_module import MyPlugin

register_plugin("my_plugin", MyPlugin)
```

### Using Plugins in Code

**Old way (deprecated):**

```python
from yt_fts.ui.plugins import create_plugin

plugin = create_plugin("default", console=my_console, verbose=True)
```

**New way (recommended):**

```python
from yt_fts.display import PluginContext, create_plugin

context = PluginContext(
    command="download",  # or "search", "import", "status", etc.
    console=my_console,
    options={"verbose": True, "custom_option": "value"},
)
plugin = create_plugin("default", context)
```

## Key API Differences

| Feature | Old System (`ui.plugins`) | New System (`display`) |
|---------|---------------------------|------------------------|
| **Base Class** | `ui.plugins.base.DisplayPlugin` | `display.base.DisplayPlugin` |
| **Initialization** | `__init__(console, verbose)` | `__init__(context: PluginContext)` |
| **Context** | No context object | `PluginContext` with command info |
| **Multi-Command** | Batch download only | Supports all commands |
| **Configuration** | Constructor parameters only | `configure()` method + context options |
| **Generic Display** | Not supported | `display()` method for custom data |
| **Error Methods** | Not supported | `error()`, `warning()`, `info()` helpers |

## Backward Compatibility

### Legacy Plugins Still Work

Existing legacy plugins continue to work without modification:

```python
# This still works, but emits deprecation warning
from yt_fts.ui.plugins import create_plugin
plugin = create_plugin("detailed", console=my_console)
```

### Legacy Adapters Available

All legacy plugins are available as `legacy_*` in the new system:

```python
from yt_fts.display import PluginContext, create_plugin

context = PluginContext(command="download", console=my_console)

# Use legacy plugin through adapter (no deprecation warning)
plugin = create_plugin("legacy_detailed", context)
```

## Testing

All tests pass with the new unified system:

```bash
# Run plugin integration tests
pytest tests/integration/test_plugin_adapter_integration.py -v
# Result: 47 passed

# Run plugin security tests  
pytest tests/test_plugin_discovery_security.py -v
# Result: 16 passed
```

## Migration Checklist

For plugin authors migrating to the new system:

- [ ] Update base class import from `ui.plugins.base` to `display.base`
- [ ] Change `__init__` signature to accept `PluginContext`
- [ ] Implement `get_name()` method
- [ ] Add `supported_commands` list (or leave empty for all commands)
- [ ] Update `__init__` to call `super().__init__(context)`
- [ ] Replace `self.console` initialization with `self.console = context.console`
- [ ] Replace `self.verbose` with `self.options.get("verbose", True)`
- [ ] Update registration to use `yt_fts.display.register_plugin`
- [ ] Update plugin instantiation to use `PluginContext`
- [ ] Add support for additional commands if applicable
- [ ] Test with both new and legacy usage patterns

## Timeline

- **Phase 1 (Current):** Deprecation warnings added, legacy adapters available
- **Phase 2 (Future):** Legacy imports emit warnings but still work
- **Phase 3 (Future):** Legacy system removed, only new system available

## References

- **Refactor Plan:** `docs/refactor_plan_prioritized.md` Phase 2.1
- **New API:** `src/yt_fts/display/base.py`
- **Legacy Adapter:** `src/yt_fts/display/legacy_adapter.py`
- **Plugin Registry:** `src/yt_fts/display/registry.py`
- **Integration Tests:** `tests/integration/test_plugin_adapter_integration.py`

## Support

For questions or issues during migration:

1. Check the integration tests for examples
2. Review existing plugin implementations in `src/yt_fts/display/plugins/`
3. Examine the legacy adapter for compatibility patterns
4. Consult the refactor plan for design decisions

## Summary

The plugin system unification is **COMPLETE** with:

- ✅ Deprecation warnings added to legacy system
- ✅ Batch downloader updated to use new system
- ✅ Legacy plugins auto-registered as adapters
- ✅ All 63 tests passing
- ✅ Backward compatibility maintained
- ✅ Clear migration path documented

No immediate action required for existing code. The legacy system will continue to work with deprecation warnings, giving time for gradual migration.
