# 📥 dnld_telegram - Async Optimized Telegram Media Downloader

## 🎯 Overview
Enhanced Telegram media downloader with production-ready async optimizations, comprehensive error handling, and robust testing framework. This tool allows you to download media files from specific Telegram channels using the Telethon library with advanced async patterns and enterprise-grade reliability.

## 🔧 Prerequisites
1. **Python 3.11+** - Compatible Python version as specified in pyproject.toml
2. **Telegram API credentials** - API ID and API Hash from [Telegram](https://my.telegram.org/)
3. **Telegram session string** - Authentication token for accessing your account
4. **uv package manager** - Modern Python package manager (`pip install uv`)

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/your-org/dnld_telegram.git
cd dnld_telegram

# Install dependencies using uv (recommended)
uv pip install -r requirements.txt

# Or using traditional pip
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the project root with your Telegram credentials:

```env
# Telegram API Configuration
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_SESSION_STRING=your_session_string_here

# Channel Configuration (JSON format)
TELEGRAM_CHANNELS={"jcexclusive": -1002436706028, "koreannarchive": -1001518888395}

# Storage Configuration
STORAGE_BASE_PATH=./downloads
MAX_CONCURRENT_DOWNLOADS=2
```

### 3. Basic Usage

**Primary Command (Recommended):**
```bash
# Standard download command with UI selection
# Run from the project root (C:\_Python\_Projects\)
C:\_Python\_Projects\dnld_telegram\.venv\Scripts\dnld_telegram.exe --ui A

# Alternative UI option
PS C:\_Python\_Projects\dnld_telegram> .\dnld_telegram --ui B
```

**Alternative Commands (Advanced Usage):**
```bash
# Download from all configured channels
uv run --active python -m src.download

# Download from a specific channel
uv run --active python -m src.download --channel jcexclusive

# Download with specific options
uv run --active python -m src.download --channel jcexclusive --media-type video --limit 10

# Show database sharding status for all channels
uv run --active python -m src.download --show-sharding-status

**Note on `uv run` and UI Modes:**
While `uv run` is convenient, interactive UI modes (like `--ui A` or `--ui B`) or long-running operations executed via `uv run` might appear to "hang" in some terminal environments or when executed by automated agents. If a command seems unresponsive, consider using non-interactive options (e.g., `--help`, `--show-sharding-status`) for testing, or running the executable directly with its full path.
```

## 📋 Available Commands

### Main Operations
```bash
# Download from all channels (default behavior)
uv run --active python -m src.download

# Download from specific channel
uv run --active python -m src.download --channel CHANNEL_NAME

# Continue downloading unfinished media
uv run --active python -m src.download --continue

# Scan for existing files in temp directory
uv run --active python -m src.download --scan-existing

# Scan and organize existing files
uv run --active python -m src.download --scan-and-organize
```

### Enumeration Without Downloading
```bash
# Enumerate all media in a channel without downloading
uv run --active python -m src.download --channel CHANNEL_NAME --enumerate full

# Enumerate new media only (incremental)
uv run --active python -m src.download --channel CHANNEL_NAME --enumerate inc
```

### Status and Information
```bash
# Show database sharding status for all channels
uv run --active python -m src.download --show-sharding-status

# Show help with all available options
uv run --active python -m src.download --help
```

## ⚙️ Advanced Configuration Options

### Media Type Filtering
```bash
# Download only specific types of media
uv run --active python -m src.download --media-type video    # Videos only
uv run --active python -m src.download --media-type image    # Images only
uv run --active python -m src.download --media-type audio    # Audio files only
uv run --active python -m src.download --media-type all      # All media (default)
```

### Performance Tuning
```bash
# Adjust concurrent downloads
uv run --active python -m src.download --concurrent-downloads 1  # Single download
uv run --active python -m src.download --concurrent-downloads 4  # Four concurrent downloads

# Set operation timeout
uv run --active python -m src.download --timeout 3600  # 1 hour timeout
```

### User Interface Options

**Recommended Approach:**
```bash
# Standard command with UI modes
.\dnld_telegram --ui A
.\dnld_telegram --ui B
```

**Alternative (Advanced):**
```bash
# Different UI modes for various environments
uv run --active python -m src.download --ui tqdm     # Progress bars (default)
uv run --active python -m src.download --ui simple   # Basic text output
uv run --active python -m src.download --ui rich     # Rich formatting
uv run --active python -m src.download --ui quiet    # Minimal output
```

### Logging Levels
```bash
# Set logging verbosity
uv run --active python -m src.download --log-level DEBUG    # Most verbose
uv run --active python -m src.download --log-level INFO     # Standard info
uv run --active python -m src.download --log-level WARNING  # Warnings and errors (default)
uv run --active python -m src.download --log-level ERROR    # Errors only
```

## 🧪 Testing Framework

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_enhanced_async_compliance.py

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Run tests in parallel
uv run pytest -n auto
```

### Testing Guidelines
The project follows comprehensive testing practices:
- **Isolate external dependencies** using mocking or dependency injection
- **Follow TDD workflow**: RED → GREEN → REFACTOR for each feature
- **Test error paths** and exception handling
- **Use parametrized tests** for multiple scenarios

See [TESTING_GUIDELINES.md](coordination/TESTING_GUIDELINES.md) for detailed strategies.

## 🛡️ Error Handling & Recovery

### Built-in Resilience Patterns
1. **Circuit Breaker** - Prevents cascading failures
2. **Retry with Backoff** - Handles transient failures gracefully
3. **Dead Letter Queue** - Manages persistently failing operations
4. **Graceful Degradation** - Continues operation during partial failures

### Error Recovery Features
- **Automatic Stall Detection** - Detects and recovers from stalled operations
- **Process Management** - Cleans up orphaned processes
- **Database Recovery** - Recovers from database locking issues
- **Network Resilience** - Handles connection interruptions

## 📊 Monitoring & Observability

### Health Checks
```bash
# Check system health
uv run --active python -m src.download --show-sharding-status
```

### Metrics Collection
The system collects and reports:
- **Download Statistics**: Files downloaded, bytes transferred
- **Performance Metrics**: Speed, concurrency utilization
- **Error Rates**: Failure counts and types
- **Resource Usage**: Memory, CPU, network

## 🔒 Security & Privacy

### Data Protection
- **Local Storage**: All data stored locally, never transmitted
- **Encrypted Sessions**: Telegram session strings are encrypted at rest
- **API Credential Security**: Credentials stored in secure `.env` file
- **No Third-Party Services**: No external dependencies for core functionality

### Best Practices
- Keep your API credentials and session string secure
- Never commit credentials or session files to version control
- Use strong file permissions for sensitive files
- Regularly rotate your Telegram API credentials

## 🚨 Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify your session string is valid
2. **Download Failures**: Check channel permissions and network connectivity
3. **Database Locking**: Restart the application to clear stale locks
4. **Missing Channels**: Ensure channels are properly defined in your `.env` file

### Debugging Commands
```bash
# Enable debug logging
uv run --active python -m src.download --log-level DEBUG

# Check for stalled processes
uv run --active python -m src.download --show-sharding-status

# Force cleanup of temporary files
uv run --active python -m src.download --scan-existing

### Command Hanging/Long Execution
If `dnld_telegram` commands appear to hang or run for an unexpectedly long time, especially when using interactive UI modes or long-running operations:
1.  **Use Non-Interactive Commands for Testing:** For basic verification, prefer commands like `--help` or `--show-sharding-status`, which are designed to exit quickly.
2.  **Run Executable Directly:** Instead of `uv run`, execute the `dnld_telegram` executable directly from its virtual environment's `Scripts` directory:
    ```bash
    C:\_Python\_Projects\dnld_telegram\.venv\Scripts\dnld_telegram.exe [options]
    ```
3.  **Consider a Timeout Wrapper:** For automated environments, use a timeout wrapper script (e.g., `timeout_executor.py` from `__dev/ai_tools/scripts/`) to enforce a maximum execution time.
    ```bash
    python C:\_Python\_Projects\__dev\ai_tools\scripts\timeout_executor.py --command "C:\_Python\_Projects\dnld_telegram\.venv\Scripts\dnld_telegram.exe --ui A" --timeout 120 --working-dir "C:\_Python\_Projects\"
    ```

```

## 📁 Project Structure
```
dnld_telegram/
├── src/                   # Source code
│   └── download/          # Main download functionality
│       ├── database/      # Database storage and management
│       ├── config/        # Configuration management
│       ├── monitoring/    # Health checks and metrics
│       └── resilience/    # Error handling and recovery
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance benchmarks
├── coordination/          # Task coordination files
├── docs/                  # Documentation
├── logs/                  # Log files
├── temp/                  # Temporary files
└── downloads/             # Downloaded media (configurable)
```

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Develop** following TDD principles (RED → GREEN → REFACTOR)
4. **Test** your changes (`uv run pytest`)
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to branch (`git push origin feature/amazing-feature`)
7. **Open** Pull Request

### Code Standards
- Follow PEP 8 Python style guide
- Write comprehensive tests for new features
- Document all public APIs
- Use type hints for function signatures
- Maintain backward compatibility when possible

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- [Loguru](https://github.com/Delgan/loguru) - Enhanced logging
- [Rich](https://github.com/Textualize/rich) - Rich text formatting
- [Pytest](https://github.com/pytest-dev/pytest) - Testing framework
---
**Built with ❤️ for the Telegram community** 🚀
