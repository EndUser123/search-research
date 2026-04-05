# LLM DEVELOPER IMPLEMENTATION GUIDE
## **Step-by-Step Guide for Any LLM Working on Log Chunker**

**PURPOSE**: This guide ensures any LLM developer can contribute to log_chunker enhancement with complete consistency.

---

## 🚀 GETTING STARTED

### Before Starting ANY Enhancement:

1. **Read Project Status**: Open `ENHANCEMENT_PROJECT.md` to understand current state
2. **Check Current Priority**: Review `docs/dev/ENHANCEMENT_PRIORITIES.md` for next task
3. **Study Patterns**: Read `docs/dev/CODING_PATTERNS.md` thoroughly
4. **Understand Context**: Review existing similar implementations

### Essential Files to Understand:
- `src/log_chunker/` - Core framework code
- `src/log_chunker/plugins/` - Plugin architecture
- `src/log_chunker/config.py` - Configuration system
- `src/log_chunker/data_models.py` - Data structures

---

## 📋 IMPLEMENTATION WORKFLOW

### Phase 1: Preparation
```bash
# 1. Understand current structure
ls -la src/log_chunker/
ls -la src/log_chunker/plugins/

# 2. Review existing tests
ls -la tests/

# 3. Check current configuration
cat src/log_chunker/config.py | head -20
```

### Phase 2: Implementation
1. **Create files** as specified in ENHANCEMENT_PRIORITIES.md
2. **Follow patterns** exactly as shown in CODING_PATTERNS.md
3. **Include tests** for all new functionality
4. **Update configuration** if needed

### Phase 3: Validation
1. **Test without optional dependencies**:
```bash
python -m pytest tests/ -v
python -c "from src.log_chunker import log_chunker; print('Base functionality works')"
```

2. **Test with optional dependencies** (if applicable):
```bash
pip install -r requirements-enhanced.txt
python -m pytest tests/ -v
```

3. **Run validation script**:
```bash
python scripts/validate_enhancement.py path/to/new/file.py
```

### Phase 4: Documentation
1. **Update tracking**: Mark progress in ENHANCEMENT_PROJECT.md
2. **Document changes**: Add to enhancement log
3. **Update priorities**: Mark completed items

---

## 🎯 CURRENT IMPLEMENTATION TARGET

### **NEXT TASK: Performance Optimization Engine**

**Goal**: Implement performance optimization using Polars for large file processing

**Files to Create**:
1. `src/log_chunker/engines/performance_optimizer.py`
2. `tests/unit/test_performance_optimizer.py`

**Files to Modify**:
1. `src/log_chunker/config.py` (add PerformanceOptimizationConfig)
2. `src/log_chunker/preprocessor.py` (integrate Polars)

---

## 📝 STEP-BY-STEP IMPLEMENTATION

### Step 1: Create Directory Structure
```bash
mkdir -p src/log_chunker/plugins/enhanced
touch src/log_chunker/plugins/enhanced/__init__.py
```

### Step 2: Create Optional Dependencies File
```python
# File: requirements-enhanced.txt
sentence-transformers>=2.2.0
hdbscan>=0.8.29
scikit-learn>=1.0.0
polars>=0.20.0
```

### Step 3: Extend Configuration
```python
# Add to src/log_chunker/config.py (find the ChunkingConfig class and add)

class SemanticClusteringConfig(BaseModel):
    """Configuration for semantic clustering plugin"""
    enabled: bool = Field(default=False, description="Enable semantic clustering")
    model_name: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    min_cluster_size: int = Field(default=5, description="Minimum cluster size for HDBSCAN")
    min_samples: int = Field(default=3, description="Minimum samples for HDBSCAN")
    cache_embeddings: bool = Field(default=True, description="Cache embeddings for performance")

# In the main ChunkingConfig class, add:
    semantic_clustering: SemanticClusteringConfig = Field(default_factory=SemanticClusteringConfig)
```

### Step 4: Implement Plugin (Copy This Exact Template)
```python
# File: src/log_chunker/plugins/enhanced/semantic_clustering.py

"""
Semantic Clustering Plugin using sentence-transformers and HDBSCAN

Dependencies: sentence-transformers, hdbscan
Fallback: Uses simple keyword clustering if dependencies unavailable
Configuration: semantic_clustering section in config
"""

from typing import List, Optional, Dict, Any
import logging

# Standard optional dependency pattern
try:
    from sentence_transformers import SentenceTransformer
    import hdbscan
    import numpy as np
    HAS_SEMANTIC_DEPS = True
except ImportError:
    HAS_SEMANTIC_DEPS = False
    SentenceTransformer = None
    hdbscan = None
    np = None

from ..base import ChunkingPlugin
from ...data_models import ChunkInfo, LogEntry
from ...config import ChunkingConfig
from ...exceptions import PluginError, LogChunkerError

logger = logging.getLogger(__name__)

class SemanticClusteringPlugin(ChunkingPlugin):
    """Enhanced semantic clustering using transformer embeddings and HDBSCAN"""

    def __init__(self, config: ChunkingConfig, console):
        super().__init__(config, console)

        if not HAS_SEMANTIC_DEPS:
            logger.warning(f"{self.name}: Semantic dependencies unavailable, using fallback")
            self.console.print("[yellow]Semantic clustering dependencies not found, using fallback")
            self.use_fallback = True
            return

        self.use_fallback = False

        # Initialize semantic model
        try:
            self.model = SentenceTransformer(config.semantic_clustering.model_name)
            self.clusterer = hdbscan.HDBSCAN(
                min_cluster_size=config.semantic_clustering.min_cluster_size,
                min_samples=config.semantic_clustering.min_samples,
                metric='euclidean'
            )
            self.console.print(f"[green]✅ Semantic clustering initialized with {config.semantic_clustering.model_name}")
        except Exception as e:
            logger.error(f"{self.name}: Failed to initialize semantic components: {e}")
            self.use_fallback = True

    def find_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """Find boundaries using semantic similarity"""
        if self.use_fallback:
            return self._fallback_boundaries(text, log_entries)

        try:
            return self._semantic_boundaries(text, log_entries)
        except Exception as e:
            logger.error(f"{self.name}: Semantic clustering failed: {e}, using fallback")
            self.console.print(f"[yellow]Semantic analysis failed, using fallback: {e}")
            return self._fallback_boundaries(text, log_entries)

    def _semantic_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """Implementation using semantic embeddings and HDBSCAN"""
        if len(log_entries) < 2:
            return []

        # Extract messages for embedding
        messages = [entry.message for entry in log_entries]

        # Generate embeddings
        self.console.print("[cyan]Generating semantic embeddings...")
        embeddings = self.model.encode(messages, show_progress_bar=False)

        # Perform clustering
        self.console.print("[cyan]Performing HDBSCAN clustering...")
        cluster_labels = self.clusterer.fit_predict(embeddings)

        # Find cluster boundaries
        boundaries = []
        if len(cluster_labels) > 0:
            current_cluster = cluster_labels[0]

            for i, label in enumerate(cluster_labels[1:], 1):
                if label != current_cluster:
                    if log_entries[i].line_number is not None:
                        boundaries.append(log_entries[i].line_number)
                    current_cluster = label

        self.console.print(f"[green]Found {len(boundaries)} semantic boundaries")
        return boundaries

    def _fallback_boundaries(self, text: str, log_entries: List[LogEntry]) -> List[int]:
        """Fallback using simple keyword similarity"""
        boundaries = []

        if len(log_entries) < 2:
            return boundaries

        # Simple keyword-based clustering fallback
        prev_keywords = set()

        for i, entry in enumerate(log_entries):
            # Extract simple keywords
            words = entry.message.lower().split()
            keywords = set(word for word in words if len(word) > 3)

            if i > 0:
                # Calculate Jaccard similarity
                intersection = prev_keywords.intersection(keywords)
                union = prev_keywords.union(keywords)
                similarity = len(intersection) / len(union) if union else 0

                # If similarity is low, create boundary
                if similarity < 0.3 and entry.line_number is not None:
                    boundaries.append(entry.line_number)

            prev_keywords = keywords

        return boundaries

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score based on semantic coherence"""
        if self.use_fallback:
            return 0.5  # Neutral score for fallback

        try:
            # Simple coherence scoring
            lines = chunk.strip().split('\n')
            if len(lines) < 2:
                return 0.7

            # Get embeddings for all lines
            embeddings = self.model.encode(lines, show_progress_bar=False)

            # Calculate average pairwise similarity
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i+1, len(embeddings)):
                    sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    similarities.append(sim)

            return float(np.mean(similarities)) if similarities else 0.5

        except Exception as e:
            logger.error(f"{self.name}: Scoring failed: {e}")
            return 0.5
```

### Step 5: Create Tests
```python
# File: tests/unit/test_semantic_clustering.py

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.config import ChunkingConfig
from src.log_chunker.data_models import LogEntry, ChunkInfo

class TestSemanticClusteringPlugin:

    def setup_method(self):
        """Setup for each test"""
        self.config = ChunkingConfig()
        self.console = Mock()

    def test_initialization_without_dependencies(self):
        """Test plugin falls back gracefully without dependencies"""
        with patch('src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS', False):
            plugin = SemanticClusteringPlugin(self.config, self.console)
            assert plugin.use_fallback

    def test_fallback_implementation_works(self):
        """Test fallback provides basic functionality"""
        with patch('src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS', False):
            plugin = SemanticClusteringPlugin(self.config, self.console)

            log_entries = [
                LogEntry(message="auth failed user john", original_line="auth failed user john",
                        pattern="auth", language="en", line_number=1),
                LogEntry(message="database connection timeout", original_line="database connection timeout",
                        pattern="db", language="en", line_number=2),
                LogEntry(message="auth failed user jane", original_line="auth failed user jane",
                        pattern="auth", language="en", line_number=3)
            ]

            boundaries = plugin.find_boundaries("test text", log_entries)
            assert isinstance(boundaries, list)

    def test_score_chunk_fallback(self):
        """Test chunk scoring works with fallback"""
        with patch('src.log_chunker.plugins.enhanced.semantic_clustering.HAS_SEMANTIC_DEPS', False):
            plugin = SemanticClusteringPlugin(self.config, self.console)

            chunk_info = ChunkInfo(chunk_id=1, start_line=1, end_line=5, estimated_tokens=100)
            score = plugin.score_chunk("test chunk content", chunk_info)

            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
```

### Step 6: Update Plugin Manager (if needed)
Check if the plugin manager automatically discovers plugins in the enhanced/ directory. If not, update it to include the new plugin.

---

## ✅ VALIDATION CHECKLIST

**Before marking task complete, verify ALL items:**

### Functionality Tests:
- [ ] Plugin initializes without optional dependencies (fallback mode)
- [ ] Plugin initializes with optional dependencies (full mode)
- [ ] find_boundaries() returns valid line numbers
- [ ] score_chunk() returns float between 0.0 and 1.0
- [ ] Error handling works correctly
- [ ] Rich console integration displays properly

### Code Quality:
- [ ] Follows CODING_PATTERNS.md exactly
- [ ] Includes comprehensive docstrings
- [ ] Has proper type hints
- [ ] Uses established error handling patterns
- [ ] Maintains backward compatibility

### Integration:
- [ ] Works with existing test suite
- [ ] Integrates with current plugin manager
- [ ] Configuration system updated correctly
- [ ] No breaking changes to existing functionality

---

## 🔄 HANDOFF PROCESS

### When Completing This Task:

1. **Update Project Status**:
   - Mark task as complete in `ENHANCEMENT_PROJECT.md`
   - Update "COMPLETED ENHANCEMENTS" section
   - Move to next priority in `ENHANCEMENT_PRIORITIES.md`

2. **Provide Handoff Notes**:
   - Document any challenges encountered
   - Note any deviations from the plan
   - Specify what the next LLM should focus on

3. **Quality Assurance**:
   - Run full test suite: `python -m pytest tests/ -v`
   - Test both dependency scenarios
   - Verify Rich console output looks correct

### For Next LLM Developer:
- The next task will be "Advanced Anomaly Detection" from Tier 1
- Follow the same implementation pattern
- Build on the foundation established by this semantic clustering plugin

---

## 🆘 TROUBLESHOOTING

### Common Issues:

**Import Errors**:
- Verify the plugin path is correct
- Check `__init__.py` files exist in all directories
- Ensure PYTHONPATH includes the src directory

**Configuration Errors**:
- Verify Pydantic model syntax is correct
- Check that new config is added to main ChunkingConfig class
- Test configuration loading with simple script

**Plugin Not Loading**:
- Check plugin manager discovery mechanism
- Verify plugin follows exact interface requirements
- Test plugin instantiation manually

**Rich Console Issues**:
- Use existing console patterns from other plugins
- Test console output in isolation
- Verify Rich markup syntax is correct

---

**Remember**: When in doubt, copy existing patterns exactly. Consistency is more important than optimization at this stage.
