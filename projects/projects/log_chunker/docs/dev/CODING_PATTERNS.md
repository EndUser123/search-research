# LOG_CHUNKER CODING PATTERNS
## **Mandatory Patterns for All LLM Developers**

**CRITICAL**: All enhancements MUST follow these exact patterns to ensure consistency across different LLM developers.

---

## 1. PLUGIN INTERFACE STANDARD

**ALL plugins must inherit from base classes and follow this exact structure:**

```python
# File: src/log_chunker/plugins/enhanced/example_plugin.py

"""
Example Plugin Description

Dependencies: library1, library2
Fallback: Simple implementation when dependencies unavailable
Configuration: plugin_section in ChunkingConfig
"""

from typing import List, Optional, Dict, Any
import logging

# MANDATORY: Optional dependency pattern
try:
    from advanced_library import AdvancedClass
    HAS_ADVANCED_DEPS = True
except ImportError:
    HAS_ADVANCED_DEPS = False
    AdvancedClass = None

from ..base import ChunkingPlugin  # or AnalysisPlugin
from ...data_models import ChunkInfo, LogEntry
from ...config import ChunkingConfig
from ...exceptions import PluginError, LogChunkerError

logger = logging.getLogger(__name__)

class ExamplePlugin(ChunkingPlugin):
    """Brief description of what this plugin does"""

    def __init__(self, config: ChunkingConfig, console):
        super().__init__(config, console)

        # MANDATORY: Check dependencies and setup fallback
        if not HAS_ADVANCED_DEPS:
            logger.warning(f"{self.name}: Advanced dependencies unavailable, using fallback")
            self.use_fallback = True
            return

        self.use_fallback = False
        self.advanced_feature = AdvancedClass(
            param1=config.plugin_section.param1,
            param2=config.plugin_section.param2
        )

    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """MANDATORY: Implement all abstract methods"""
        if self.use_fallback:
            return self._fallback_implementation(text, log_entries)

        try:
            return self._advanced_implementation(text, log_entries)
        except Exception as e:
            logger.error(f"{self.name}: Advanced implementation failed: {e}, using fallback")
            return self._fallback_implementation(text, log_entries)

    def _advanced_implementation(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """Implementation using advanced dependencies"""
        # Your advanced logic here
        pass

    def _fallback_implementation(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """MANDATORY: Always provide fallback that works with base dependencies"""
        # Simple implementation that works without optional dependencies
        pass

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """MANDATORY: Implement all abstract methods"""
        if self.use_fallback:
            return 0.5  # Neutral score for fallback

        # Advanced scoring logic
        return 0.8
```

---

## 2. ERROR HANDLING STANDARD

**ALL error handling MUST follow this exact pattern:**

```python
from ...exceptions import LogChunkerError, PluginError

def risky_operation(self):
    try:
        # Risky operation that might fail
        result = some_complex_operation()
        return result

    except ImportError as e:
        # Dependency issues
        self.console.print(f"[yellow]Warning in {self.name}: Missing dependency - {e}")
        raise PluginError(f"Required dependency missing: {e}") from e

    except ValueError as e:
        # Data validation issues
        self.console.print(f"[red]Error in {self.name}: Invalid data - {e}")
        raise PluginError(f"Data validation failed: {e}") from e

    except Exception as e:
        # Unexpected errors
        self.console.print(f"[red]Unexpected error in {self.name}: {e}")
        raise LogChunkerError(f"Unexpected error in {self.name}: {e}") from e
```

---

## 3. CONFIGURATION PATTERN

**ALL configuration additions must extend existing Pydantic models:**

```python
# File: src/log_chunker/config.py (ADD to existing)

from pydantic import BaseModel, Field
from typing import Optional

class SemanticClusteringConfig(BaseModel):
    """Configuration for semantic clustering plugin"""
    enabled: bool = Field(default=False, description="Enable semantic clustering")
    model_name: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    min_cluster_size: int = Field(default=5, description="Minimum cluster size for HDBSCAN")
    min_samples: int = Field(default=3, description="Minimum samples for HDBSCAN")
    cache_embeddings: bool = Field(default=True, description="Cache embeddings for performance")

# ADD to existing ChunkingConfig class:
class ChunkingConfig(BaseModel):
    # ... existing fields ...
    semantic_clustering: SemanticClusteringConfig = Field(default_factory=SemanticClusteringConfig)
```

---

## 4. RICH CONSOLE INTEGRATION

**ALL console output must use existing Rich patterns:**

```python
def process_with_progress(self, items: List[Any]):
    """Example of Rich console integration"""

    # Use existing console from initialization
    with self.console.status("[bold green]Processing items...") as status:
        total = len(items)

        for i, item in enumerate(items):
            # Update status with progress
            status.update(f"[bold green]Processing item {i+1}/{total}")

            # Process item
            result = self.process_item(item)

            # Progress logging
            if i % 100 == 0:  # Every 100 items
                self.console.print(f"✅ Processed {i+1}/{total} items")

    # Final success message
    self.console.print(f"🎉 Successfully processed {total} items", style="bold green")
```

---

## 5. ASYNC PATTERN (For I/O Operations)

**ALL I/O operations should use async patterns where possible:**

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncCapablePlugin(ChunkingPlugin):

    async def process_large_file(self, file_path: str):
        """Example async I/O operation"""

        # CPU-bound work in thread pool
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                self._cpu_intensive_work,
                file_path
            )

        return result

    def _cpu_intensive_work(self, file_path: str):
        """CPU-intensive work that runs in thread pool"""
        # Your processing logic here
        pass
```

---

## 6. FILE STRUCTURE CONVENTIONS

**ALL enhancement files must follow this structure:**

```
src/log_chunker/
├── plugins/
│   ├── enhanced/                    # NEW enhanced plugins go here
│   │   ├── __init__.py
│   │   ├── semantic_clustering.py  # Example enhancement
│   │   └── advanced_anomaly.py     # Example enhancement
│   └── base.py                     # Existing base classes
├── engines/                        # NEW processing engines
│   ├── __init__.py
│   └── ml_pipeline.py
├── integrations/                   # NEW external integrations
│   ├── __init__.py
│   ├── database/
│   └── ml_models/
└── utils/                          # Utility functions
    ├── performance.py              # Performance utilities
    └── validation.py               # Enhanced validation
```

---

## 7. TESTING PATTERNS

**ALL enhancements must include tests following this pattern:**

```python
# File: tests/unit/test_enhanced_semantic_clustering.py

import pytest
from unittest.mock import Mock, patch

from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import LogEntry

class TestSemanticClusteringPlugin:

    def setup_method(self):
        """Setup for each test"""
        self.config = ChunkingConfig()
        self.console = Mock()

    def test_initialization_with_dependencies(self):
        """Test plugin initializes correctly with dependencies"""
        with patch('src.log_chunker.plugins.enhanced.semantic_clustering.HAS_ADVANCED_DEPS', True):
            plugin = SemanticClusteringPlugin(self.config, self.console)
            assert not plugin.use_fallback

    def test_initialization_without_dependencies(self):
        """Test plugin falls back gracefully without dependencies"""
        with patch('src.log_chunker.plugins.enhanced.semantic_clustering.HAS_ADVANCED_DEPS', False):
            plugin = SemanticClusteringPlugin(self.config, self.console)
            assert plugin.use_fallback

    def test_fallback_implementation_works(self):
        """Test fallback provides basic functionality"""
        with patch('src.log_chunker.plugins.enhanced.semantic_clustering.HAS_ADVANCED_DEPS', False):
            plugin = SemanticClusteringPlugin(self.config, self.console)

            log_entries = [
                LogEntry(message="test1", original_line="test1", pattern="test", language="en"),
                LogEntry(message="test2", original_line="test2", pattern="test", language="en")
            ]

            boundaries = plugin.find_boundaries("test text", log_entries)
            assert isinstance(boundaries, list)
```

---

## 8. DOCUMENTATION REQUIREMENTS

**ALL enhancements must include:**

1. **Docstring Format**:
```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of what the function does.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2

    Returns:
        Dict containing result data

    Raises:
        PluginError: When specific conditions fail
        LogChunkerError: When unexpected errors occur

    Example:
        >>> plugin = ExamplePlugin(config, console)
        >>> result = plugin.complex_function("test", 42)
        >>> print(result["status"])
        "success"
    """
```

2. **Module Documentation**:
```python
"""
Module: semantic_clustering.py

Purpose: Provides advanced semantic clustering using sentence transformers and HDBSCAN.

Dependencies:
    - sentence-transformers: For generating semantic embeddings
    - hdbscan: For hierarchical density-based clustering

Fallback: Uses simple keyword-based clustering when dependencies unavailable.

Configuration:
    - semantic_clustering.enabled: Enable this plugin
    - semantic_clustering.model_name: Transformer model to use
    - semantic_clustering.min_cluster_size: Minimum cluster size
"""
```

---

## MANDATORY CHECKLIST FOR ALL ENHANCEMENTS

**Before submitting any enhancement, verify:**

- [ ] Follows exact plugin interface pattern
- [ ] Implements proper optional dependency handling
- [ ] Provides fallback implementation
- [ ] Uses standard error handling patterns
- [ ] Integrates with Rich console correctly
- [ ] Includes comprehensive tests
- [ ] Has proper documentation
- [ ] Works with base dependencies only
- [ ] Works with enhanced dependencies
- [ ] Maintains backward compatibility

**Any enhancement not following these patterns will be rejected and must be rewritten.**
