# Evidence Validation API

A comprehensive FastAPI-based system for standardized evidence validation with real-time checking, intelligent caching, and consistent interface for all system components.

## Features

- **Real-time Evidence Validation**: Fast evidence validation with configurable rules and async processing
- **Intelligent Caching**: Multi-layer caching with Redis and PostgreSQL for optimal performance
- **WebSocket Support**: Real-time validation updates and notifications
- **Comprehensive Adapters**: Consistent interfaces for workflow engines, CI/CD systems, databases, and more
- **High Performance**: Async-first architecture with connection pooling and optimization
- **Extensive Monitoring**: Metrics, health checks, and error tracking
- **OpenAPI Documentation**: Interactive API documentation with examples

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/example/evidence-validation-api.git
cd evidence-validation-api

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Configuration

Create a `.env` file:

```env
# Database
DATABASE__DATABASE_URL=postgresql+asyncpg://user:password@localhost/evidence_validation

# Redis
REDIS__REDIS_URL=redis://localhost:6379/0

# API
API__HOST=0.0.0.0
API__PORT=8000
API__DEBUG=false

# Security
SECURITY__JWT_SECRET_KEY=your-secret-key-change-in-production
SECURITY__CORS_ORIGINS=["http://localhost:3000", "https://yourapp.com"]
```

### Running the API

```bash
# Development
uvicorn evidence_validation_api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn evidence_validation_api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
# Build
docker build -t evidence-validation-api .

# Run
docker run -p 8000:8000 --env-file .env evidence-validation-api
```

## API Documentation

Once running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Core Concepts

### Evidence Types

The API supports various evidence types:

- `task_execution`: Task and operation execution evidence
- `api_call`: REST API and service call evidence
- `database_operation`: Database query and transaction evidence
- `file_operation`: File creation, modification, and access evidence
- `performance_metric`: System and application performance metrics
- `error_log`: Error and exception evidence
- `security_event`: Security-related events
- `audit_trail`: Audit and compliance evidence
- `test_result`: Test execution and validation evidence
- `code_analysis`: Code quality and security analysis evidence

### Validation Status

- `pending`: Validation is queued or in progress
- `in_progress`: Validation is actively being processed
- `validated`: Evidence passed all validation rules
- `rejected`: Evidence failed validation
- `failed`: Validation process failed
- `inconclusive`: Validation results are inconclusive
- `expired`: Validation result has expired

### Cache Strategies

- `no_cache`: No caching
- `short_term`: 5 minutes cache
- `medium_term`: 1 hour cache
- `long_term`: 24 hours cache
- `persistent`: 7 days cache

## Usage Examples

### Basic Evidence Validation

```python
import asyncio
import httpx

async def validate_evidence():
    evidence_request = {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "task_result": "success",
                "execution_time": 120.5,
                "output": {"status": "completed", "items_processed": 1000}
            }
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "workflow_engine",
            "source_component": "task_processor",
            "timestamp": "2024-01-15T10:30:00Z",
            "workflow_id": "workflow_123",
            "task_id": "task_456",
            "user_id": "user_789",
            "severity": "medium"
        },
        "validation_rules": ["content_integrity", "metadata_completeness"],
        "cache_strategy": "medium_term",
        "async_validation": false,
        "priority": 5
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/validate",
            json=evidence_request,
            headers={"Authorization": "Bearer your-api-key"}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Validation successful: {result['validation_result']['is_valid']}")
            print(f"Confidence score: {result['validation_result']['confidence_score']}")
        else:
            print(f"Validation failed: {response.status_code} - {response.text}")

asyncio.run(validate_evidence())
```

### Async Validation with Webhook

```python
async def validate_evidence_async():
    evidence_request = {
        "evidence": {
            "content_type": "application/json",
            "data": {"large_dataset_processing": "in_progress"}
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "data_pipeline",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        "async_validation": True,
        "webhook_url": "https://your-app.com/webhook/validation-complete",
        "timeout_seconds": 300  # 5 minutes
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/validate",
            json=evidence_request
        )

        result = response.json()
        request_id = result["request_id"]

        # Poll for status or wait for webhook
        status_response = await client.get(
            f"http://localhost:8000/validate/{request_id}/status"
        )

        status = status_response.json()
        print(f"Validation status: {status['status']}")

asyncio.run(validate_evidence())
```

### WebSocket Real-time Updates

```python
import asyncio
import websockets
import json

async def websocket_validation_updates():
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        # Subscribe to validation updates
        subscribe_message = {
            "type": "subscribe_validation",
            "request_id": "your-request-id"
        }
        await websocket.send(json.dumps(subscribe_message))

        # Listen for updates
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data["type"] == "validation_completed":
                    print(f"Validation completed: {data}")
                    break
                elif data["type"] == "validation_failed":
                    print(f"Validation failed: {data}")
                    break

            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(websocket_validation_updates())
```

## Adapters

The Evidence Validation API provides adapters for easy integration with various systems:

### Workflow Engine Integration

```python
from evidence_validation_api.adapters.workflow import WorkflowEngineAdapter

# Initialize adapter
adapter = WorkflowEngineAdapter(
    workflow_engine="airflow",
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Validate task execution
result = await adapter.validate_task_execution(
    task_id="process_data_123",
    dag_id="data_pipeline_v2",
    task_result={"status": "success", "records_processed": 50000},
    execution_time=245.7,
    logs="Task completed successfully"
)

print(f"Task validation: {result.validation_result.is_valid}")
```

### Database Integration

```python
from evidence_validation_api.adapters.data import DatabaseAdapter

# Initialize adapter
db_adapter = DatabaseAdapter(
    database_type="postgresql",
    base_url="http://localhost:8000"
)

# Validate query execution
result = await db_adapter.validate_query_execution(
    query="UPDATE users SET last_login = NOW() WHERE active = true",
    database_name="app_db",
    execution_time=12.3,
    rows_affected=1250
)

print(f"Query validation: {result.validation_result.is_valid}")
```

### CI/CD Integration

```python
from evidence_validation_api.adapters.cicd import CIPlatformAdapter

# Initialize adapter
ci_adapter = CIPlatformAdapter(
    ci_platform="github_actions",
    base_url="http://localhost:8000"
)

# Connect for real-time updates
await ci_adapter.connect()

# Validate build execution
result = await ci_adapter.validate_build_execution(
    build_id="build-456",
    project_name="my-app",
    branch="main",
    commit_hash="abc123def",
    status="success",
    start_time=datetime.now(),
    build_number="789"
)
```

## Configuration

### Database Configuration

```python
# PostgreSQL (recommended for production)
DATABASE__DATABASE_URL=postgresql+asyncpg://user:password@localhost/evidence_validation

# SQLite (for development/testing)
DATABASE__DATABASE_URL=sqlite+aiosqlite:///./evidence_validation.db
```

### Redis Configuration

```python
# Local Redis
REDIS__REDIS_URL=redis://localhost:6379/0

# Redis with authentication
REDIS__REDIS_URL=redis://:password@localhost:6379/0

# Redis Cluster
REDIS__REDIS_URL=redis://redis-cluster:6379/0
```

### Validation Settings

```python
# Performance tuning
VALIDATION__MAX_CONCURRENT_VALIDATIONS=100
VALIDATION__DEFAULT_TIMEOUT=30
VALIDATION__MAX_QUEUE_SIZE=1000

# Cache settings
VALIDATION__DEFAULT_CACHE_STRATEGY=medium_term
VALIDATION__CACHE_TTL_SHORT=300      # 5 minutes
VALIDATION__CACHE_TTL_MEDIUM=3600   # 1 hour
VALIDATION__CACHE_TTL_LONG=86400     # 24 hours
```

## Monitoring and Metrics

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "active_validations": 5,
  "queue_size": 12,
  "cache_stats": {
    "cache_hits": 1250,
    "cache_misses": 340,
    "hit_rate": 0.786
  },
  "database_status": "connected",
  "redis_status": "connected",
  "last_health_check": "2024-01-15T11:30:00.123Z"
}
```

### Metrics

```bash
curl http://localhost:8000/metrics
```

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Fast unit tests
pytest -m integration             # Integration tests
pytest -m "not slow"              # Exclude slow tests
pytest -m redis                   # Tests requiring Redis

# Run with coverage
pytest --cov=evidence_validation_api --cov-report=html

# Run specific test file
pytest tests/test_validation_service.py
```

## Performance Considerations

### Caching Strategy

- Use `medium_term` cache for most validation requests
- Use `short_term` cache for real-time metrics
- Use `long_term` cache for compliance evidence
- Use `no_cache` for one-time validations

### Async vs Sync

- Use `async_validation=True` for long-running validations
- Use sync validation for quick, critical validations
- Set appropriate timeout values based on evidence complexity

### Batch Processing

```python
# Process multiple evidence items concurrently
import asyncio
from evidence_validation_api.adapters.workflow import WorkflowEngineAdapter

adapter = WorkflowEngineAdapter("airflow", "http://localhost:8000")

tasks = [
    adapter.validate_task_execution(f"task_{i}", f"dag_{i}", {"result": i})
    for i in range(100)
]

results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Security

### Authentication

```python
# Using JWT token
headers = {"Authorization": "Bearer your-jwt-token"}

# Using API key
headers = {"X-API-Key": "your-api-key"}

response = await client.post(
    "http://localhost:8000/validate",
    json=evidence_request,
    headers=headers
)
```

### Evidence Encryption

```python
evidence_request = {
    "metadata": {
        "evidence_type": "task_execution",
        "source_system": "secure_system",
        "encrypted": True  # Mark evidence as encrypted
    }
}
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis is running
   redis-cli ping

   # Verify connection string
   redis-cli -u redis://localhost:6379/0 ping
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   psql postgresql://user:password@localhost/evidence_validation
   ```

3. **Validation Timeouts**
   ```python
   # Increase timeout for complex validations
   evidence_request["timeout_seconds"] = 120  # 2 minutes
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in environment
LOG_LEVEL=DEBUG uvicorn evidence_validation_api.main:app --reload
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: https://evidence-validation-api.readthedocs.io
- **Issues**: https://github.com/example/evidence-validation-api/issues
- **Discussions**: https://github.com/example/evidence-validation-api/discussions

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
