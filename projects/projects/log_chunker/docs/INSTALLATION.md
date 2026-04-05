# Installation Guide

## Prerequisites

### Python Requirements
- **Python 3.8+** (recommended: 3.9+)
- **pip** package manager
- **git** for version control

### System Requirements
- **RAM**: 4GB minimum, 8GB+ recommended for large files
- **Storage**: 1GB free space for dependencies and cache
- **GPU**: Optional CUDA-capable GPU for ML acceleration

## Installation Methods

### 1. Quick Installation (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd log_chunker

# Install core dependencies
pip install -r requirements.txt

# Validate installation
python log_chunker.py validate
```

### 2. Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd log_chunker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Run validation
python log_chunker.py validate
```

### 3. Minimal Installation (Core Features Only)

If you want to avoid heavy ML dependencies:

```bash
# Install only core dependencies
pip install rich>=13.0.0 pydantic>=2.0.0 numpy>=1.21.0 loguru>=0.7.0

# This will disable semantic and perplexity plugins but maintain:
# - Pattern-based chunking
# - Temporal analysis
# - Conversation chunking
# - Multi-report generation
```

## Dependency Categories

### Core Dependencies (Required)
```
rich>=13.0.0          # Terminal UI and formatting
pydantic>=2.0.0        # Configuration validation
numpy>=1.21.0          # Numerical operations
loguru>=0.7.0          # Logging
```

### ML Dependencies (Optional - Advanced Features)
```
torch>=2.0.0                    # PyTorch for neural models
transformers>=4.30.0            # Hugging Face models
sentence-transformers>=2.2.0    # Semantic embedding models
scikit-learn>=1.3.0            # Machine learning utilities
scipy>=1.10.0                  # Scientific computing
```

### Text Processing Dependencies (Optional - Enhanced Features)
```
langdetect>=1.0.9              # Language detection
fuzzywuzzy>=0.18.0             # Fuzzy string matching
python-levenshtein>=0.12.0     # Fast edit distance
```

## GPU Support Setup

### CUDA Setup (Optional)
For GPU acceleration of semantic analysis:

```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### CPU-Only Mode
The framework automatically falls back to CPU processing if GPU is unavailable.

## Configuration

### Initial Setup
```bash
# Generate sample configuration
python log_chunker.py sample-config

# Customize settings in sample_config.json
# Then use: python log_chunker.py logs.txt --config sample_config.json
```

### Environment Variables
```bash
# Optional: Set default token limits
export LOG_CHUNKER_DEFAULT_TOKENS=50000

# Optional: Set default output directory
export LOG_CHUNKER_OUTPUT_DIR=/path/to/output
```

## Verification

### Basic Functionality Test
```bash
# Test with sample data
echo "2024-01-01 10:00:00 INFO Starting application
2024-01-01 10:00:01 ERROR Connection failed
2024-01-01 10:00:02 INFO Retrying connection" > test.log

python log_chunker.py test.log
```

### Advanced Features Test
```bash
# Test semantic analysis (requires ML dependencies)
python log_chunker.py test.log --enable-semantic --llm-smart-mode
```

## Troubleshooting Installation

### Common Issues

#### ImportError: No module named 'torch'
```bash
# Install ML dependencies
pip install torch>=2.0.0 transformers>=4.30.0 sentence-transformers>=2.2.0
```

#### CUDA out of memory
```bash
# Use CPU-only mode
python log_chunker.py logs.txt --no-gpu
```

#### Permission denied errors
```bash
# Install in user directory
pip install --user -r requirements.txt
```

#### Package conflicts
```bash
# Create clean virtual environment
python -m venv fresh_env
source fresh_env/bin/activate  # or fresh_env\Scripts\activate on Windows
pip install -r requirements.txt
```

### Dependency Resolution
If you encounter dependency conflicts:

1. **Check Python version**: Ensure Python 3.8+
2. **Update pip**: `pip install --upgrade pip`
3. **Clean install**: Remove and recreate virtual environment
4. **Minimal install**: Use core dependencies only first

## Platform-Specific Notes

### Windows
- Use Command Prompt or PowerShell
- Backslashes in paths: `python log_chunker.py C:\path\to\logs.txt`
- GPU support requires CUDA toolkit installation

### macOS
- May need Xcode command line tools: `xcode-select --install`
- Use forward slashes in paths: `python log_chunker.py /path/to/logs.txt`

### Linux
- May need build tools: `sudo apt-get install build-essential`
- GPU support requires NVIDIA drivers and CUDA

## Next Steps

After successful installation:

1. **Read the [User Guide](docs/USER_GUIDE.md)** for basic usage
2. **Try examples** in the [Examples Guide](docs/EXAMPLES.md)
3. **Check [Configuration Reference](docs/CONFIGURATION.md)** for advanced settings
4. **See [Developer Guide](docs/DEVELOPER_GUIDE.md)** for customization

## Support

If you encounter issues:

1. Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Review [Common Issues](docs/FAQ.md)
3. Check existing [GitHub Issues](issues-link)
4. Create a new issue with installation details
