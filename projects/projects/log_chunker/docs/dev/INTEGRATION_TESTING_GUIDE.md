# INTEGRATION TESTING GUIDE FOR ENHANCED PLUGINS

**Purpose**: Guide for testing the interaction between enhanced plugins and ensuring they work together correctly.

## Testing Both Enhanced Plugins Together

### Prerequisites
```bash
# Install all enhanced dependencies for full testing
pip install -r requirements-enhanced.txt

# Or test fallback behavior without dependencies
# (plugins should work with graceful degradation)
```

### End-to-End Integration Test

Create a comprehensive test file: `tests/integration/test_enhanced_plugins.py`

```python
import pytest
from unittest.mock import Mock
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
from src.log_chunker.data_models import LogEntry, ChunkInfo

class TestEnhancedPluginsIntegration:

    def setup_method(self):
        """Setup for integration tests"""
        self.config = ChunkingConfig()
        self.config.semantic_clustering.enabled = True
        self.config.advanced_anomaly.enabled = True
        self.console = Mock()

    def test_both_plugins_initialize_together(self):
        """Test both enhanced plugins can initialize simultaneously"""
        semantic_plugin = SemanticClusteringPlugin()
        anomaly_plugin = AdvancedAnomalyPlugin()

        semantic_result = semantic_plugin.initialize(self.config, self.console)
        anomaly_result = anomaly_plugin.initialize(self.config, self.console)

        assert semantic_result == True
        assert anomaly_result == True

    def test_plugins_process_same_data(self):
        """Test both plugins can process the same log data"""
        # Create test log entries
        log_entries = [
            LogEntry(message="normal startup sequence initiated",
                    original_line="normal startup sequence initiated",
                    pattern="startup", language="en", line_number=1),
            LogEntry(message="critical system failure detected",
                    original_line="critical system failure detected",
                    pattern="error", language="en", line_number=2),
            LogEntry(message="normal operation resumed",
                    original_line="normal operation resumed",
                    pattern="normal", language="en", line_number=3),
        ]

        # Initialize plugins
        semantic_plugin = SemanticClusteringPlugin()
        anomaly_plugin = AdvancedAnomalyPlugin()
        semantic_plugin.initialize(self.config, self.console)
        anomaly_plugin.initialize(self.config, self.console)

        # Both plugins should handle the same data
        semantic_boundaries = semantic_plugin.find_boundaries("test", log_entries)
        anomaly_boundaries = anomaly_plugin.find_boundaries("test", log_entries)

        assert isinstance(semantic_boundaries, list)
        assert isinstance(anomaly_boundaries, list)

    def test_combined_analysis_workflow(self):
        """Test complete workflow with both plugins"""
        # Create sample chunks
        chunks = [
            ("Normal log entries here", ChunkInfo(chunk_id=1, start_line=1, end_line=5, estimated_tokens=100)),
            ("Error: critical failure", ChunkInfo(chunk_id=2, start_line=6, end_line=10, estimated_tokens=50)),
        ]

        # Initialize both plugins
        semantic_plugin = SemanticClusteringPlugin()
        anomaly_plugin = AdvancedAnomalyPlugin()
        semantic_plugin.initialize(self.config, self.console)
        anomaly_plugin.initialize(self.config, self.console)

        # Analyze chunks with both plugins
        semantic_analysis = semantic_plugin.analyze_chunks(chunks)
        anomaly_analysis = anomaly_plugin.analyze_chunks(chunks)

        # Verify analysis structure
        assert "semantic_clustering" in semantic_analysis
        assert "advanced_anomaly" in anomaly_analysis

        # Analysis should be complementary, not conflicting
        assert semantic_analysis["semantic_clustering"]["total_chunks"] == len(chunks)
        assert anomaly_analysis["advanced_anomaly"]["total_chunks"] == len(chunks)
```

### Manual Integration Testing

```bash
# Test with enhanced dependencies available
python3 -c "
from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
from src.log_chunker.config import ChunkingConfig
from unittest.mock import Mock

config = ChunkingConfig()
config.semantic_clustering.enabled = True
config.advanced_anomaly.enabled = True
console = Mock()

# Test both plugins initialize
semantic = SemanticClusteringPlugin()
anomaly = AdvancedAnomalyPlugin()

print('Semantic init:', semantic.initialize(config, console))
print('Anomaly init:', anomaly.initialize(config, console))
print('Semantic fallback:', semantic.use_fallback)
print('Anomaly fallback:', anomaly.use_fallback)
"

# Test with dependencies unavailable (fallback mode)
python3 -c "
import sys
sys.modules['sentence_transformers'] = None
sys.modules['hdbscan'] = None
sys.modules['sklearn'] = None

# Now test fallback behavior
from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
print('✅ Both plugins imported successfully in fallback mode')
"
```

## Configuration Integration Testing

### Test Configuration Loading
```python
def test_enhanced_config_integration():
    """Test that enhanced configurations load correctly"""
    config = ChunkingConfig()

    # Test semantic clustering config
    assert hasattr(config, 'semantic_clustering')
    assert config.semantic_clustering.model_name == "all-MiniLM-L6-v2"
    assert config.semantic_clustering.min_cluster_size == 5

    # Test advanced anomaly config
    assert hasattr(config, 'advanced_anomaly')
    assert config.advanced_anomaly.contamination == 0.1
    assert config.advanced_anomaly.n_estimators == 100

    # Test both can be enabled simultaneously
    config.semantic_clustering.enabled = True
    config.advanced_anomaly.enabled = True

    # Configuration should be valid
    assert config.semantic_clustering.enabled == True
    assert config.advanced_anomaly.enabled == True
```

## Performance Integration Testing

### Memory Usage Testing
```bash
# Test memory usage with both plugins active
python3 -c "
import psutil
import os
from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin

process = psutil.Process(os.getpid())
initial_memory = process.memory_info().rss / 1024 / 1024

# Initialize both plugins
# ... (initialization code)

final_memory = process.memory_info().rss / 1024 / 1024
print(f'Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB')
print(f'Memory increase: {final_memory - initial_memory:.1f}MB')
"
```

## Troubleshooting Integration Issues

### Common Issues:
1. **Memory conflicts**: Both plugins using large models simultaneously
2. **Dependency conflicts**: Different versions of scikit-learn for different features
3. **Configuration conflicts**: Incompatible parameter combinations

### Solutions:
1. **Memory management**: Use caching and model sharing where possible
2. **Dependency isolation**: Test with pinned versions in requirements-enhanced.txt
3. **Configuration validation**: Add cross-plugin configuration validation

## Validation Checklist

Before marking integration complete:

- [ ] Both plugins initialize successfully together
- [ ] Both plugins process the same log data without conflicts
- [ ] Configuration system supports both plugin configurations
- [ ] Memory usage remains reasonable with both plugins active
- [ ] Fallback modes work correctly for both plugins
- [ ] Analysis results from both plugins are complementary
- [ ] Performance remains acceptable with both plugins enabled
- [ ] No dependency conflicts between plugin requirements
