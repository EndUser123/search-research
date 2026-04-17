# CSF CKS Cross-System Integration Layer

This module provides a comprehensive integration layer for the CSF Cognitive Knowledge System (CKS), enabling direct Python clients for external systems including HDMA, Serena, Chat History, and Web Content extraction.

## Architecture Overview

### Integration Components

1. **HDMA Client** - Direct Python client for static analysis pattern integration
2. **Serena Client** - Direct LSP client for multi-language code analysis
3. **Chat History Client** - Conversation pattern extraction and analysis
4. **Web Content Client** - Web content extraction using crawl4ai patterns

### Core Infrastructure

- **BaseIntegrationClient** - Abstract base class with standardized interfaces
- **IntegrationConfig** - Unified configuration management
- **IntegrationResult** - Standardized result containers
- **IntegrationFactory** - Factory for creating configured clients
- **Exception Handling** - Comprehensive error classification and handling

## Quick Start

### Basic Usage

```python
from cks.integration import IntegrationFactory

# Create all integration clients
factory = IntegrationFactory.create_development()
clients = await factory.create_all_clients()

# Initialize all clients
await factory.initialize_all_clients(clients)

# Use HDMA client for static analysis
hdma_client = clients["hdma"]
request = HDMAAnalysisRequest(
    file_paths=["src/"],
    analysis_types={"structure", "patterns"}
)
result = await hdma_client.analyze_code(request)

# Use Chat History client
chat_client = clients["chat_history"]
request = ChatHistoryRequest(
    query="debugging session",
    time_range_days=7
)
result = await chat_client.search_chat_history(request)

# Cleanup
await factory.cleanup_all_clients()
```

### Configuration

```python
from cks.integration.utils.integration_factory import IntegrationSystemConfig

# Custom configuration
config = IntegrationSystemConfig(
    global_timeout_seconds=60,
    global_retry_attempts=3,
    enable_all_clients=True,
    hdma=HDMAConfig(
        api_base_url="http://localhost:8080",
        api_key="your-api-key",
        max_concurrent_requests=5
    ),
    web_content=WebContentConfig(
        use_crawl4ai=True,
        enable_security_scanning=True,
        allowed_domains={"docs.python.org", "fastapi.tiangolo.com"}
    )
)

factory = IntegrationFactory(config)
```

### Environment Configuration

```bash
# HDMA Configuration
export HDMA_API_URL="http://localhost:8080"
export HDMA_API_KEY="your-api-key"

# Serena Configuration
export SERENA_WORKSPACE_ROOT="/path/to/workspace"

# Web Content Configuration
export ALLOWED_DOMAINS="docs.python.org,fastapi.tiangolo.com"
export BLOCKED_DOMAINS="spam.com,malicious.site"

# Global Configuration
export INTEGRATION_TIMEOUT="30"
export INTEGRATION_LOG_LEVEL="INFO"
```

## Client Documentation

### HDMA Client

**Purpose**: Static analysis pattern integration and code structure analysis

**Features**:
- Multi-language static analysis support
- Pattern recognition and extraction
- Dependency analysis
- Complexity metrics
- Security scanning for code files

**Example**:
```python
from cks.integration.clients.hdma_client import HDMAAnalysisRequest, Language

request = HDMAAnalysisRequest(
    file_paths=["src/", "lib/"],
    analysis_types={"structure", "dependencies", "patterns"},
    max_file_size_mb=10,
    exclude_patterns=["*.pyc", "node_modules/*"]
)

result = await hdma_client.analyze_code(request)
print(f"Found {len(result.data.patterns)} patterns")
print(f"Analyzed {result.data.statistics['total_files_analyzed']} files")
```

### Serena Client

**Purpose**: LSP-based multi-language code analysis and intelligent development assistance

**Features**:
- Language Server Protocol integration
- Symbol extraction and analysis
- Diagnostic information
- Definition and reference resolution
- Code completion support

**Supported Languages**:
- Python (via Pyright)
- JavaScript/TypeScript (via TypeScript Language Server)
- Additional languages configurable

**Example**:
```python
from cks.integration.clients.serena_client import SerenaAnalysisRequest, Language, LSPRequestType

request = SerenaAnalysisRequest(
    file_path="src/main.py",
    language=Language.PYTHON,
    request_types={LSPRequestType.SYMBOLS, LSPRequestType.DIAGNOSTICS}
)

result = await serena_client.analyze_code(request)
print(f"Found {len(result.data.symbols)} symbols")
print(f"Found {len(result.data.diagnostics)} issues")
```

### Chat History Client

**Purpose**: Conversation pattern extraction and temporal analysis from chat history

**Features**:
- Semantic search across conversations
- Pattern recognition (debugging, architecture, etc.)
- Temporal analysis and trend detection
- PII filtering and security
- Performance optimization with caching

**Pattern Types**:
- Question/Answer sessions
- Problem solving discussions
- Code reviews
- Architecture planning
- Debugging sessions

**Example**:
```python
from cks.integration.clients.chat_history_client import ChatHistoryRequest, ConversationPattern

request = ChatHistoryRequest(
    query="performance optimization",
    time_range_days=14,
    pattern_types={ConversationPattern.CODE_DISCUSSION},
    max_results=50
)

result = await chat_client.search_chat_history(request)
print(f"Found {len(result.data.messages)} messages")
print(f"Detected {len(result.data.patterns)} patterns")
```

### Web Content Client

**Purpose**: Web content extraction and processing with security validation

**Features**:
- crawl4ai integration for content extraction
- Security scanning and threat detection
- Content filtering and sanitization
- Domain whitelist/blacklist support
- Batch processing and performance optimization

**Security Features**:
- Malicious content detection
- Domain validation
- Content sanitization
- Rate limiting
- Sandboxed processing

**Example**:
```python
from cks.integration.clients.web_content_client import WebContentRequest, ContentType

request = WebContentRequest(
    urls=["https://docs.python.org/3/", "https://fastapi.tiangolo.com/"],
    content_types={ContentType.DOCUMENTATION, ContentType.API_DOCS},
    max_content_length=1000000,  # 1MB
    allowed_domains={"docs.python.org", "fastapi.tiangolo.com"}
)

result = await web_client.extract_content(request)
print(f"Extracted {len(result.data.contents)} pages")
print(f"Security summary: {result.data.security_summary}")
```

## Error Handling

### Exception Hierarchy

```
IntegrationException (Base)
├── AuthenticationException
├── AuthorizationException
├── NetworkException
├── TimeoutException
├── RateLimitException
├── ValidationException
├── ConfigurationException
├── SecurityException
├── ConstitutionalException
└── DependencyException
```

### Error Handling Best Practices

```python
try:
    result = await client.analyze_code(request)
    if result.success:
        print("Analysis successful")
        process_result(result.data)
    else:
        print(f"Analysis failed: {result.error}")
        # Handle specific error types
        if "rate limit" in result.error.lower():
            await asyncio.sleep(60)  # Wait before retry
except AuthenticationException:
    print("Authentication failed - check API credentials")
except NetworkException:
    print("Network error - check connectivity")
except ConstitutionalException:
    print("Constitutional violation detected")
```

## Configuration Options

### Global Settings

- `global_timeout_seconds`: Operation timeout (default: 30)
- `global_retry_attempts`: Retry attempts (default: 3)
- `global_retry_delay_seconds`: Retry delay (default: 1.0)
- `enable_all_clients`: Enable all clients (default: True)
- `log_level`: Logging level (default: "INFO")

### Client-Specific Settings

Each client has specific configuration options detailed in their respective documentation.

## Security Considerations

### Content Security

- **Input Validation**: All external content is validated before processing
- **Threat Detection**: Malicious content patterns are detected and blocked
- **Domain Filtering**: Whitelist/blacklist enforcement for web content
- **PII Protection**: Personal information filtering in chat history

### API Security

- **Credential Management**: Secure API key handling
- **Rate Limiting**: Configurable rate limits to prevent abuse
- **Access Control**: Role-based access to sensitive operations
- **Audit Logging**: Comprehensive logging of all operations

## Performance Optimization

### Caching

- **Result Caching**: Intelligent caching of analysis results
- **Configuration Caching**: Cached configuration for repeated use
- **Connection Pooling**: Reused connections for HTTP clients
- **Memory Management**: Efficient memory usage with cleanup

### Concurrency

- **Async Processing**: Full async/await support for high throughput
- **Batch Operations**: Efficient processing of multiple items
- **Resource Limits**: Configurable concurrency limits
- **Timeout Management**: Proper timeout handling

## Testing

### Running Tests

```bash
# Run all tests
pytest src/features/cks/integration/tests/ -v

# Run specific client tests
pytest src/features/cks/integration/tests/test_hdma_client.py -v

# Run with coverage
pytest src/features/cks/integration/tests/ --cov=src/features/cks/integration --cov-report=html

# Run performance tests
pytest src/features/cks/integration/tests/ -m performance

# Run security tests
pytest src/features/cks/integration/tests/ -m security
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component workflows
- **Security Tests**: Vulnerability and compliance testing
- **Performance Tests**: Scalability and efficiency
- **Mock Tests**: Testing with external dependencies mocked

## Constitutional Compliance

This integration layer follows CSF constitutional requirements:

- **Solo Developer Optimization**: Simple interfaces and sensible defaults
- **Evidence-Based Operations**: Comprehensive logging and validation
- **Force Multiplier**: Automated analysis and pattern extraction
- **Security Requirements**: Built-in security validation and threat detection
- **Performance Standards**: Efficient processing with optimization

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install aiohttp beautifulsoup4 crawl4ai-cu110
   ```

2. **Authentication Failures**: Check API credentials and endpoints
3. **Timeout Issues**: Increase timeout values for slow systems
4. **Memory Usage**: Monitor memory usage with large datasets
5. **Rate Limiting**: Implement proper rate limiting for external APIs

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for specific clients
factory = IntegrationFactory.create_development()
factory.config.log_level = "DEBUG"
```

### Health Checks

```python
# Check health of all clients
health_results = await factory.health_check_all_clients(clients)

for name, health in health_results.items():
    print(f"{name}: {health.status.value}")
    if not health.is_healthy:
        print(f"  Error: {health.error_message}")
```

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest src/features/cks/integration/tests/`
4. Ensure constitutional compliance: `python scripts/validate.py`

### Code Standards

- Follow PEP 8 with 79-character line limit
- Comprehensive docstrings for all functions
- Type hints for all parameters and return values
- Constitutional compliance validation
- Comprehensive test coverage

## License

This integration layer is part of the CSF project and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test cases for usage examples
3. Enable debug logging for detailed error information
4. Check constitutional compliance requirements
