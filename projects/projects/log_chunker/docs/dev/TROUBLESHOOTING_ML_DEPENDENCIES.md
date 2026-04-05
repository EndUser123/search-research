# TROUBLESHOOTING ML DEPENDENCIES

**Purpose**: Guide for diagnosing and resolving issues with enhanced ML features and their dependencies.

## Dependency Overview

### Enhanced Features Dependencies
```
Enhanced Semantic Analysis:
├── sentence-transformers>=2.2.0
├── hdbscan>=0.8.29
├── scikit-learn>=1.0.0
└── numpy (included with above)

Advanced Anomaly Detection:
├── scikit-learn>=1.0.0
└── numpy (included with above)

Performance Optimization:
└── polars>=0.20.0
```

## Common Issues and Solutions

### 1. Import Errors

**Issue**: `ImportError: No module named 'sentence_transformers'`
```python
# Error appears in logs:
# semantic_clustering: Semantic dependencies unavailable, using fallback
```

**Solutions**:
```bash
# Option 1: Install enhanced dependencies
pip install -r requirements-enhanced.txt

# Option 2: Install specific package
pip install sentence-transformers>=2.2.0

# Option 3: Verify installation
python3 -c "import sentence_transformers; print('✅ sentence-transformers working')"

# Option 4: Check virtual environment
which python3
pip list | grep sentence
```

**Verification**:
```python
# Test that semantic clustering initializes properly
python3 -c "
from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin, HAS_SEMANTIC_DEPS
print(f'Dependencies available: {HAS_SEMANTIC_DEPS}')
"
```

### 2. Version Conflicts

**Issue**: `TypeError: 'str' object cannot be interpreted as an integer`
```
Usually indicates incompatible versions between dependencies
```

**Solutions**:
```bash
# Check installed versions
pip list | grep -E "(scikit-learn|sentence-transformers|hdbscan)"

# Force reinstall with correct versions
pip uninstall scikit-learn sentence-transformers hdbscan -y
pip install -r requirements-enhanced.txt

# Create clean environment
python3 -m venv clean_env
source clean_env/bin/activate
pip install -r requirements-enhanced.txt
```

### 3. HDBSCAN Installation Issues

**Issue**: `ERROR: Failed building wheel for hdbscan`
```
Common on systems without proper build tools
```

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential python3-dev

# macOS
xcode-select --install
brew install llvm

# Windows
# Install Microsoft Visual C++ Build Tools

# Alternative: Use conda
conda install -c conda-forge hdbscan

# Test installation
python3 -c "import hdbscan; print('✅ HDBSCAN working')"
```

### 4. Memory Issues

**Issue**: `RuntimeError: CUDA out of memory` or excessive RAM usage
```
Large transformer models can consume significant memory
```

**Solutions**:
```python
# Option 1: Use smaller model in config
{
  "semantic_clustering": {
    "model_name": "all-MiniLM-L6-v2",  # Smaller model
    "cache_embeddings": false  # Disable caching if memory constrained
  }
}

# Option 2: Reduce batch sizes
{
  "batch_size": 16,  # Reduce from default 32
  "max_workers": 2   # Reduce parallel processing
}

# Option 3: Force CPU processing
{
  "use_gpu": false
}
```

**Memory Monitoring**:
```python
# Monitor memory usage during processing
python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f}MB')
"
```

### 5. Performance Issues

**Issue**: Very slow processing with enhanced features
```
[cyan]Generating semantic embeddings...
[Takes several minutes for small files]
```

**Solutions**:
```python
# Option 1: Enable caching
{
  "semantic_clustering": {
    "cache_embeddings": true
  }
}

# Option 2: Use GPU if available
{
  "use_gpu": true
}

# Option 3: Reduce model complexity
{
  "semantic_clustering": {
    "min_cluster_size": 10,  # Larger clusters, faster processing
    "model_name": "all-MiniLM-L6-v2"  # Fastest model
  },
  "advanced_anomaly": {
    "n_estimators": 50  # Fewer trees, faster processing
  }
}
```

## Diagnostic Commands

### Complete Dependency Check
```python
# File: scripts/check_dependencies.py
def check_all_dependencies():
    """Comprehensive dependency check for enhanced features"""

    print("🔍 Checking Enhanced ML Dependencies")
    print("=" * 40)

    # Check semantic clustering dependencies
    try:
        import sentence_transformers
        import hdbscan
        import sklearn
        print("✅ Semantic Clustering: All dependencies available")
        print(f"   sentence-transformers: {sentence_transformers.__version__}")
        print(f"   hdbscan: {hdbscan.__version__}")
        print(f"   scikit-learn: {sklearn.__version__}")
    except ImportError as e:
        print(f"❌ Semantic Clustering: Missing dependency - {e}")

    # Check anomaly detection dependencies
    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.feature_extraction.text import TfidfVectorizer
        print("✅ Advanced Anomaly Detection: All dependencies available")
    except ImportError as e:
        print(f"❌ Advanced Anomaly Detection: Missing dependency - {e}")

    # Check plugin initialization
    try:
        from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
        from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
        from src.log_chunker.config import ChunkingConfig
        from unittest.mock import Mock

        config = ChunkingConfig()
        console = Mock()

        semantic = SemanticClusteringPlugin()
        anomaly = AdvancedAnomalyPlugin()

        semantic_init = semantic.initialize(config, console)
        anomaly_init = anomaly.initialize(config, console)

        print(f"✅ Plugin Initialization:")
        print(f"   Semantic Clustering: {'Success' if semantic_init else 'Failed'}")
        print(f"   Advanced Anomaly: {'Success' if anomaly_init else 'Failed'}")
        print(f"   Semantic Fallback: {semantic.use_fallback}")
        print(f"   Anomaly Fallback: {anomaly.use_fallback}")

    except Exception as e:
        print(f"❌ Plugin Initialization Failed: {e}")

if __name__ == "__main__":
    check_all_dependencies()
```

### Run Diagnostic
```bash
python3 scripts/check_dependencies.py
```

## Fallback Behavior Testing

### Test Fallback Modes
```python
# Test semantic clustering fallback
python3 -c "
import sys
# Simulate missing dependencies
sys.modules['sentence_transformers'] = None
sys.modules['hdbscan'] = None

from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
plugin = SemanticClusteringPlugin()
print('✅ Semantic clustering fallback mode working')
"

# Test anomaly detection fallback
python3 -c "
import sys
# Simulate missing dependencies
sys.modules['sklearn'] = None

from src.log_chunker.plugins.enhanced.advanced_anomaly import AdvancedAnomalyPlugin
plugin = AdvancedAnomalyPlugin()
print('✅ Anomaly detection fallback mode working')
"
```

## Environment-Specific Solutions

### Docker Environment
```dockerfile
# Dockerfile for enhanced features
FROM python:3.9-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-enhanced.txt .
RUN pip install -r requirements-enhanced.txt

# Test installation
RUN python3 -c "import sentence_transformers, hdbscan, sklearn; print('✅ All dependencies installed')"
```

### Virtual Environment
```bash
# Create isolated environment for enhanced features
python3 -m venv enhanced_env
source enhanced_env/bin/activate

# Install with specific versions
pip install --upgrade pip
pip install -r requirements-enhanced.txt

# Verify installation
python3 -c "
from src.log_chunker.plugins.enhanced.semantic_clustering import HAS_SEMANTIC_DEPS
from src.log_chunker.plugins.enhanced.advanced_anomaly import HAS_SKLEARN_DEPS
print(f'Semantic deps: {HAS_SEMANTIC_DEPS}')
print(f'Anomaly deps: {HAS_SKLEARN_DEPS}')
"
```

## Getting Help

### Debug Information Collection
```bash
# Collect comprehensive debug info
python3 -c "
import sys
print('Python version:', sys.version)
print('Python path:', sys.path)

import platform
print('Platform:', platform.platform())
print('Architecture:', platform.architecture())

try:
    import sentence_transformers
    print('sentence-transformers:', sentence_transformers.__version__)
except ImportError:
    print('sentence-transformers: NOT INSTALLED')

try:
    import hdbscan
    print('hdbscan:', hdbscan.__version__)
except ImportError:
    print('hdbscan: NOT INSTALLED')

try:
    import sklearn
    print('scikit-learn:', sklearn.__version__)
except ImportError:
    print('scikit-learn: NOT INSTALLED')
"
```

### Performance Profiling
```bash
# Profile plugin performance
python3 -c "
import time
from src.log_chunker.plugins.enhanced.semantic_clustering import SemanticClusteringPlugin
from src.log_chunker.config import ChunkingConfig
from unittest.mock import Mock

start = time.time()
plugin = SemanticClusteringPlugin()
config = ChunkingConfig()
console = Mock()
plugin.initialize(config, console)
end = time.time()

print(f'Plugin initialization time: {end - start:.2f} seconds')
print(f'Using fallback: {plugin.use_fallback}')
"
```

**When to Contact Support**:
- Persistent installation failures after following all solutions
- Memory errors that can't be resolved with configuration changes
- Performance issues not resolved by optimization suggestions
- Dependency conflicts that can't be resolved with clean installation
