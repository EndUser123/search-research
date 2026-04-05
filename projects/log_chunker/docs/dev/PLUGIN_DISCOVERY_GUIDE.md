# PLUGIN DISCOVERY AND LOADING GUIDE

**Purpose**: Understanding how the plugin system discovers and loads enhanced plugins automatically.

## Plugin Discovery Architecture

### Current Plugin Structure
```
src/log_chunker/plugins/
├── __init__.py
├── base.py                    # Base plugin classes and protocols
├── boundary_detection.py     # Core boundary detection
├── semantic.py               # Original semantic plugin
├── temporal.py               # Temporal analysis
├── conversation.py           # Conversation analysis
├── pattern.py               # Pattern-based detection
├── security_analysis.py     # Security analysis
└── enhanced/                 # NEW: Enhanced ML plugins
    ├── __init__.py
    ├── semantic_clustering.py    # Enhanced semantic analysis
    └── advanced_anomaly.py      # Advanced anomaly detection
```

## Plugin Loading Mechanism

### Current Loading System
Based on the existing codebase, plugins are loaded via:

1. **Manual Plugin Registration**: Plugins are explicitly imported and registered
2. **Configuration-Based Enabling**: `enabled_plugins` list in configuration
3. **Plugin Manager**: Central plugin management system

### Enhanced Plugin Integration

**For future LLM developers**: You need to ensure new enhanced plugins are properly integrated into the plugin loading system.

#### Step 1: Check Plugin Manager
```python
# Find the plugin manager (likely in main processing file)
# Look for files that import plugins and manage their lifecycle
```

#### Step 2: Registration Pattern
Based on existing patterns, enhanced plugins need to be:

1. **Imported**: Added to import statements
2. **Registered**: Added to plugin registry/manager
3. **Configured**: Added to default `enabled_plugins` list

### Plugin Loading Verification

#### Test Plugin Discovery
```python
# File: scripts/test_plugin_discovery.py
def test_plugin_discovery():
    """Test that enhanced plugins are discovered correctly"""

    # Test 1: Import discovery
    try:
        from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
        from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
        print("✅ Enhanced plugins can be imported")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Plugin attributes
    semantic = SemanticClusteringPlugin()
    anomaly = AdvancedAnomalyPlugin()

    required_attrs = ['name', 'version', 'dependencies']
    for plugin, plugin_name in [(semantic, 'semantic'), (anomaly, 'anomaly')]:
        for attr in required_attrs:
            if not hasattr(plugin, attr):
                print(f"❌ {plugin_name} missing attribute: {attr}")
                return False
        print(f"✅ {plugin_name} has required attributes")

    # Test 3: Plugin methods
    required_methods = ['initialize', 'find_boundaries', 'score_chunk', 'analyze_chunks']
    for plugin, plugin_name in [(semantic, 'semantic'), (anomaly, 'anomaly')]:
        for method in required_methods:
            if not hasattr(plugin, method):
                print(f"❌ {plugin_name} missing method: {method}")
                return False
        print(f"✅ {plugin_name} has required methods")

    return True

if __name__ == "__main__":
    success = test_plugin_discovery()
    print(f"\nPlugin discovery test: {'PASSED' if success else 'FAILED'}")
```

## Integration Requirements

### For Next LLM Developer: Plugin Manager Integration

**CRITICAL**: The enhanced plugins are created but may not be automatically loaded by the main system. You need to:

#### 1. Find the Plugin Manager
```bash
# Search for plugin management code
grep -r "enabled_plugins\|plugin.*manager\|import.*plugin" src/log_chunker/ --include="*.py"
```

#### 2. Add Enhanced Plugins to Loading System
Look for patterns like:
```python
# Likely in main processing file or plugin manager
from plugins.semantic import SemanticPlugin
from plugins.temporal import TemporalPlugin
# ADD THESE:
from plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
```

#### 3. Update Plugin Registry
Look for plugin registration patterns:
```python
# Likely plugin registry
AVAILABLE_PLUGINS = {
    'semantic': SemanticPlugin,
    'temporal': TemporalPlugin,
    # ADD THESE:
    'semantic_clustering': SemanticClusteringPlugin,
    'advanced_anomaly': AdvancedAnomalyPlugin,
}
```

#### 4. Update Default Configuration
```python
# In config.py or similar
enabled_plugins: List[str] = Field(
    default_factory=lambda: [
        'semantic', 'temporal', 'conversation', 'pattern', 'security_analysis',
        # ADD THESE:
        'semantic_clustering', 'advanced_anomaly'
    ]
)
```

### Plugin Initialization Order

**Important**: Enhanced plugins should initialize after basic plugins to ensure proper dependency handling.

```python
# Recommended initialization order:
initialization_order = [
    'pattern',           # Basic pattern detection first
    'temporal',          # Temporal analysis
    'conversation',      # Conversation analysis
    'semantic',          # Original semantic (may be replaced)
    'security_analysis', # Security analysis
    'semantic_clustering',  # Enhanced semantic (requires ML dependencies)
    'advanced_anomaly',     # Advanced anomaly (requires ML dependencies)
]
```

## Configuration Integration

### Plugin Weights Update
```python
# Ensure enhanced plugins have appropriate weights
plugin_weights: Dict[str, float] = Field(
    default_factory=lambda: {
        'semantic': 1.0,
        'perplexity': 1.2,
        'temporal': 0.8,
        'conversation': 1.1,
        'pattern': 0.9,
        'security_analysis': 1.3,
        # ADD THESE:
        'semantic_clustering': 1.5,  # Higher weight for advanced semantic
        'advanced_anomaly': 1.4,     # High weight for anomaly detection
    }
)
```

### Plugin Dependencies Handling
```python
# Plugin manager should handle optional dependencies
def load_plugin_safely(plugin_class, config, console):
    """Safely load plugin with dependency checking"""
    try:
        plugin = plugin_class()
        success = plugin.initialize(config, console)
        if success and hasattr(plugin, 'use_fallback'):
            if plugin.use_fallback:
                console.print(f"[yellow]{plugin.name}: Using fallback mode")
            else:
                console.print(f"[green]{plugin.name}: Full ML mode active")
        return plugin if success else None
    except Exception as e:
        console.print(f"[red]{plugin_class.__name__}: Failed to load - {e}")
        return None
```

## Testing Plugin Integration

### Complete Integration Test
```python
def test_complete_plugin_integration():
    """Test that enhanced plugins integrate with the complete system"""

    # Test 1: Configuration loading
    config = ChunkingConfig()
    assert hasattr(config, 'semantic_clustering')
    assert hasattr(config, 'advanced_anomaly')

    # Test 2: Plugin loading (this will fail until plugin manager is updated)
    # This test should be implemented once plugin manager integration is complete

    # Test 3: End-to-end processing
    # This test should verify that enhanced plugins are used in actual log processing

    print("Plugin integration test framework ready")
    print("NOTE: Complete integration requires plugin manager updates")
```

## Migration Guide for Existing Plugins

### Replacing Original Semantic Plugin
If the enhanced semantic clustering should replace the original semantic plugin:

```python
# Option 1: Deprecate original
enabled_plugins: List[str] = [
    'temporal', 'conversation', 'pattern', 'security_analysis',
    'semantic_clustering',  # Replaces 'semantic'
    'advanced_anomaly'
]

# Option 2: Keep both
enabled_plugins: List[str] = [
    'semantic',           # Original for compatibility
    'temporal', 'conversation', 'pattern', 'security_analysis',
    'semantic_clustering',  # Enhanced version
    'advanced_anomaly'
]
```

## Debugging Plugin Loading

### Plugin Loading Debug Script
```python
# File: scripts/debug_plugin_loading.py
def debug_plugin_loading():
    """Debug plugin loading issues"""

    print("🔍 Debugging Plugin Loading")
    print("=" * 30)

    # Check imports
    plugins_to_check = [
        ('semantic_clustering', 'src.log_chunker.plugins.enhanced.semantic_clustering', 'SemanticClusteringPlugin'),
        ('advanced_anomaly', 'src.log_chunker.plugins.enhanced.advanced_anomaly', 'AdvancedAnomalyPlugin'),
    ]

    for name, module_path, class_name in plugins_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            plugin_class = getattr(module, class_name)
            print(f"✅ {name}: Import successful")

            # Test instantiation
            plugin = plugin_class()
            print(f"✅ {name}: Instantiation successful")

        except ImportError as e:
            print(f"❌ {name}: Import failed - {e}")
        except Exception as e:
            print(f"❌ {name}: Instantiation failed - {e}")

    # Check configuration
    try:
        from src.log_chunker.config import ChunkingConfig
        config = ChunkingConfig()
        print(f"✅ Configuration: semantic_clustering exists = {hasattr(config, 'semantic_clustering')}")
        print(f"✅ Configuration: advanced_anomaly exists = {hasattr(config, 'advanced_anomaly')}")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")

if __name__ == "__main__":
    debug_plugin_loading()
```

## Next Steps for Future LLM

**IMMEDIATE ACTION REQUIRED**: The enhanced plugins are implemented but not integrated into the main plugin loading system. The next LLM developer should:

1. **Find the plugin manager** (search for plugin loading code)
2. **Add enhanced plugins to imports** in the main processing files
3. **Update plugin registry** to include enhanced plugins
4. **Update default configuration** to enable enhanced plugins
5. **Test complete integration** with actual log processing
6. **Update plugin weights** for optimal boundary fusion

**Search commands to find plugin manager**:
```bash
grep -r "from.*plugins" src/log_chunker/ --include="*.py"
grep -r "enabled_plugins" src/log_chunker/ --include="*.py"
grep -r "plugin.*manager\|PluginManager" src/log_chunker/ --include="*.py"
```
