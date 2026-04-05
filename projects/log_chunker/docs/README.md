# Documentation Directory

Welcome to the Advanced Log Chunking Framework documentation. This directory contains comprehensive guides for users, developers, and administrators.

## Quick Navigation

### For New Users
- **[Installation Guide](INSTALLATION.md)** - Get started with the framework
- **[User Guide](USER_GUIDE.md)** - Complete usage guide with examples
- **[Configuration Reference](CONFIGURATION.md)** - Detailed configuration options

### For Developers
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Architecture and development setup
- **[API Documentation](API.md)** - Complete API reference
- **[Plugin Development](PLUGIN_DEVELOPMENT.md)** - Creating custom plugins

### For System Administrators
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Performance Tuning](PERFORMANCE.md)** - Optimization guidelines
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

### Reference Materials
- **[Examples](EXAMPLES.md)** - Real-world usage examples
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[Features & Architecture](FEATURES_AND_ARCHITECTURE.md)** - Technical deep dive

## Documentation Structure

```
docs/
├── README.md                    # This file - navigation hub
├── INSTALLATION.md              # Installation and setup
├── USER_GUIDE.md               # Complete user manual
├── DEVELOPER_GUIDE.md          # Development documentation
├── API.md                      # API reference
├── CONFIGURATION.md            # Configuration reference
├── FEATURES_AND_ARCHITECTURE.md # Technical architecture
├── PLUGIN_DEVELOPMENT.md       # Plugin creation guide
├── EXAMPLES.md                 # Usage examples
├── TROUBLESHOOTING.md          # Common issues
├── FAQ.md                      # Frequently asked questions
├── PERFORMANCE.md              # Performance optimization
├── DEPLOYMENT.md               # Production deployment
├── SECURITY.md                 # Security considerations
├── CHANGELOG.md                # Version history
└── assets/                     # Images and diagrams
    ├── architecture.png
    ├── workflow.png
    └── examples/
```

## Getting Started

### 5-Minute Quick Start

1. **Install the framework**:
   ```bash
   pip install -r requirements.txt
   python log_chunker.py validate
   ```

2. **Process your first log file**:
   ```bash
   python log_chunker.py your_logs.txt
   ```

3. **Check the results**:
   ```bash
   ls reports/  # See generated report files
   ```

That's it! The framework automatically optimizes settings and generates comprehensive reports.

### First Steps by Role

#### **I'm a User** - I want to analyze log files
→ Start with **[User Guide](USER_GUIDE.md)**

Key sections:
- [Quick Start](USER_GUIDE.md#quick-start)
- [Command-Line Usage](USER_GUIDE.md#command-line-usage)
- [Understanding Output](USER_GUIDE.md#understanding-output)

#### **I'm a Developer** - I want to integrate or extend the framework
→ Start with **[Developer Guide](DEVELOPER_GUIDE.md)**

Key sections:
- [Development Setup](DEVELOPER_GUIDE.md#development-setup)
- [Plugin Development](DEVELOPER_GUIDE.md#plugin-development)
- [API Reference](API.md)

#### **I'm a System Administrator** - I want to deploy this in production
→ Start with **[Installation Guide](INSTALLATION.md)** then **[Deployment Guide](DEPLOYMENT.md)**

Key sections:
- [System Requirements](INSTALLATION.md#system-requirements)
- [Configuration Management](CONFIGURATION.md)
- [Performance Tuning](PERFORMANCE.md)

## What This Framework Does

The Advanced Log Chunking Framework intelligently divides large log files into semantically coherent segments optimized for:

- **LLM Analysis** - Chunks fit within token limits while preserving context
- **Pattern Recognition** - Identifies errors, correlations, and anomalies
- **Multi-Format Output** - Generates reports optimized for different use cases
- **Smart Analysis** - Advanced pattern detection and relationship mapping

### Key Features

- 🔌 **Plugin Architecture** - Extensible chunking strategies
- 🧠 **ML-Powered Analysis** - Semantic and pattern-based chunking
- 🚀 **High Performance** - GPU acceleration and async processing
- 📊 **Rich Reporting** - Multiple report formats for different needs
- 🤖 **Smart Analysis** - Error deduplication, correlation detection, anomaly highlighting
- 💡 **Auto-Optimization** - Analyzes content and applies optimal settings
- 📈 **Multi-Report Generation** - Comprehensive analysis formats by default

## Support and Community

### Getting Help

1. **Check the documentation** - Most questions are answered here
2. **Review [FAQ](FAQ.md)** - Common questions and solutions
3. **Check [Troubleshooting Guide](TROUBLESHOOTING.md)** - Known issues and fixes
4. **Search existing issues** - [GitHub Issues](issues-link)
5. **Create a new issue** - Provide logs and configuration details

### Contributing

We welcome contributions! See the [Developer Guide](DEVELOPER_GUIDE.md#contributing) for:

- Code style guidelines
- Testing requirements
- Pull request process
- Development setup

### Documentation Feedback

Found an error or want to improve the documentation?

- **Small fixes**: Edit the file directly and submit a PR
- **Large changes**: Open an issue to discuss first
- **New sections**: Check the [documentation template](TEMPLATE.md)

## Version Information

- **Framework Version**: 1.0.0
- **Documentation Version**: 1.0.0
- **Last Updated**: 2024-01-15
- **Python Compatibility**: 3.8+

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Need immediate help?** Check the [User Guide Quick Start](USER_GUIDE.md#quick-start) for the fastest path to processing your first log file.
