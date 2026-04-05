# Evidence Validation API Usage Examples

This document provides comprehensive examples of how to integrate and use the Evidence Validation API with various systems and programming languages.

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Python Integration](#python-integration)
3. [JavaScript/Node.js Integration](#javascriptnodejs-integration)
4. [Workflow System Integration](#workflow-system-integration)
5. [CI/CD Pipeline Integration](#cicd-pipeline-integration)
6. [Database Integration](#database-integration)
7. [WebSocket Integration](#websocket-integration)
8. [Advanced Patterns](#advanced-patterns)
9. [Error Handling](#error-handling)
10. [Performance Optimization](#performance-optimization)

## Quick Start Examples

### Basic REST API Call

```bash
curl -X POST "http://localhost:8000/validate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "evidence": {
      "content_type": "application/json",
      "data": {
        "task_result": "success",
        "execution_time": 120.5
      }
    },
    "metadata": {
      "evidence_type": "task_execution",
      "source_system": "my_system",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "validation_rules": ["content_integrity"],
    "cache_strategy": "medium_term"
  }'
```

### Python Quick Example

```python
import requests

response = requests.post(
    "http://localhost:8000/validate",
    headers={"Authorization": "Bearer your-api-key"},
    json={
        "evidence": {
            "content_type": "application/json",
            "data": {"result": "success"}
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "my_app",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Valid: {result['validation_result']['is_valid']}")
    print(f"Score: {result['validation_result']['confidence_score']}")
```

## Python Integration

### Using the Adapters

```python
from evidence_validation_api.adapters.workflow import WorkflowEngineAdapter
from evidence_validation_api.adapters.data import DatabaseAdapter
import asyncio

async def workflow_integration_example():
    # Initialize workflow adapter
    workflow_adapter = WorkflowEngineAdapter(
        workflow_engine="airflow",
        base_url="http://localhost:8000",
        api_key="your-api-key"
    )

    # Validate task execution
    result = await workflow_adapter.validate_task_execution(
        task_id="process_customer_data",
        dag_id="daily_etl",
        task_result={"records_processed": 50000, "status": "completed"},
        execution_time=245.7,
        logs="Task completed successfully"
    )

    print(f"Task validation: {result.validation_result.is_valid}")
    print(f"Confidence: {result.validation_result.confidence_score}")

    await workflow_adapter.close()

async def database_integration_example():
    # Initialize database adapter
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

    await db_adapter.close()

# Run examples
asyncio.run(workflow_integration_example())
asyncio.run(database_integration_example())
```

### Custom Adapter Implementation

```python
from evidence_validation_api.adapters.base import HTTPAdapter
from evidence_validation_api.models.schemas import EvidenceType, CacheStrategy

class CustomSystemAdapter:
    """Custom adapter for a proprietary system."""

    def __init__(self, system_name: str, api_url: str, api_key: str = None):
        self.http_adapter = HTTPAdapter(
            component_name=f"{system_name}_adapter",
            component_version="1.0.0",
            base_url=api_url,
            api_key=api_key
        )

    async def validate_custom_operation(self, operation_data: dict):
        """Validate a custom system operation."""
        return await self.http_adapter.validate_evidence(
            evidence_data=operation_data,
            evidence_type=EvidenceType.TASK_EXECUTION,
            metadata={
                "operation_type": "custom_processing",
                "system_version": "2.1.0",
                "tags": ["custom", "processing"]
            },
            validation_rules=["content_integrity", "custom_rules"],
            cache_strategy=CacheStrategy.MEDIUM_TERM
        )

    async def close(self):
        await self.http_adapter.close()

# Usage
adapter = CustomSystemAdapter("my_system", "http://localhost:8000")
result = await adapter.validate_custom_operation({
    "operation_id": "op_123",
    "status": "completed",
    "output": {"processed_items": 1000}
})
```

### Batch Processing

```python
import asyncio
from typing import List, Dict

async def batch_validate_evidence(evidence_items: List[Dict]):
    """Validate multiple evidence items concurrently."""
    adapter = WorkflowEngineAdapter("airflow", "http://localhost:8000")

    # Create validation tasks
    tasks = []
    for item in evidence_items:
        task = adapter.validate_task_execution(
            task_id=item["task_id"],
            dag_id=item["dag_id"],
            task_result=item["result"],
            execution_time=item.get("execution_time", 0)
        )
        tasks.append(task)

    # Execute all validations concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    print(f"Successful validations: {len(successful)}")
    print(f"Failed validations: {len(failed)}")

    await adapter.close()

    return successful, failed

# Usage
evidence_items = [
    {
        "task_id": "task_1",
        "dag_id": "dag_1",
        "result": {"status": "success"},
        "execution_time": 120
    },
    {
        "task_id": "task_2",
        "dag_id": "dag_1",
        "result": {"status": "completed"},
        "execution_time": 89
    }
]

successful, failed = await batch_validate_evidence(evidence_items)
```

## JavaScript/Node.js Integration

### Basic HTTP Client

```javascript
const axios = require('axios');

class EvidenceValidationClient {
    constructor(baseURL, apiKey) {
        this.baseURL = baseURL;
        this.apiKey = apiKey;
        this.client = axios.create({
            baseURL: baseURL,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            }
        });
    }

    async validateEvidence(evidenceRequest) {
        try {
            const response = await this.client.post('/validate', evidenceRequest);
            return response.data;
        } catch (error) {
            console.error('Validation failed:', error.response?.data || error.message);
            throw error;
        }
    }

    async getValidationStatus(requestId) {
        try {
            const response = await this.client.get(`/validate/${requestId}/status`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    async cancelValidation(requestId) {
        try {
            await this.client.delete(`/validate/${requestId}`);
            return true;
        } catch (error) {
            if (error.response?.status === 404) {
                return false;
            }
            throw error;
        }
    }
}

// Usage
const client = new EvidenceValidationClient('http://localhost:8000', 'your-api-key');

async function example() {
    const evidenceRequest = {
        evidence: {
            content_type: "application/json",
            data: {
                operation: "user_login",
                user_id: "user123",
                timestamp: new Date().toISOString(),
                success: true
            }
        },
        metadata: {
            evidence_type: "task_execution",
            source_system: "auth_service",
            timestamp: new Date().toISOString()
        },
        validation_rules: ["content_integrity"],
        cache_strategy: "medium_term"
    };

    const result = await client.validateEvidence(evidenceRequest);
    console.log('Validation result:', result.validation_result);
}

example().catch(console.error);
```

### WebSocket Integration

```javascript
const WebSocket = require('ws');

class EvidenceValidationWebSocket {
    constructor(url, apiKey) {
        this.url = url;
        this.apiKey = apiKey;
        this.ws = null;
        this.subscriptions = new Map();
    }

    connect() {
        return new Promise((resolve, reject) => {
            const headers = this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {};

            this.ws = new WebSocket(this.url, { headers });

            this.ws.on('open', () => {
                console.log('WebSocket connected');
                resolve();
            });

            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            });

            this.ws.on('close', () => {
                console.log('WebSocket disconnected');
            });
        });
    }

    handleMessage(message) {
        const { type, request_id } = message;

        if (type === 'validation_completed' || type === 'validation_failed') {
            const callback = this.subscriptions.get(request_id);
            if (callback) {
                callback(message);
                this.subscriptions.delete(request_id);
            }
        }
    }

    subscribeToValidation(requestId, callback) {
        this.subscriptions.set(requestId, callback);

        const message = {
            type: 'subscribe_validation',
            request_id: requestId,
            timestamp: new Date().toISOString()
        };

        this.ws.send(JSON.stringify(message));
    }

    sendPing() {
        const message = {
            type: 'ping',
            timestamp: new Date().toISOString()
        };
        this.ws.send(JSON.stringify(message));
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
async function websocketExample() {
    const wsClient = new EvidenceValidationWebSocket('ws://localhost:8000/ws');

    await wsClient.connect();

    // Subscribe to validation updates
    const requestId = 'some-request-id';
    wsClient.subscribeToValidation(requestId, (message) => {
        console.log('Validation update:', message);
    });

    // Send periodic pings
    setInterval(() => wsClient.sendPing(), 30000);
}

websocketExample().catch(console.error);
```

### Express.js Integration

```javascript
const express = require('express');
const axios = require('axios');

class EvidenceValidationMiddleware {
    constructor(validationAPIURL, apiKey) {
        this.validationAPIURL = validationAPIURL;
        this.apiKey = apiKey;
    }

    async validateEvidence(req, res, next) {
        try {
            // Extract evidence from request
            const evidence = this.extractEvidenceFromRequest(req);

            if (!evidence) {
                return next(); // No evidence to validate
            }

            // Create validation request
            const validationRequest = {
                evidence: {
                    content_type: "application/json",
                    data: evidence
                },
                metadata: {
                    evidence_type: "api_call",
                    source_system: "express_app",
                    timestamp: new Date().toISOString(),
                    user_id: req.user?.id,
                    session_id: req.sessionID
                },
                validation_rules: ["content_integrity"],
                cache_strategy: "short_term"
            };

            // Validate evidence
            const response = await axios.post(
                `${this.validationAPIURL}/validate`,
                validationRequest,
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 5000
                }
            );

            // Attach validation result to request
            req.validationResult = response.data;

            // Optionally reject invalid evidence
            if (!response.data.validation_result.is_valid) {
                return res.status(400).json({
                    error: 'Invalid evidence',
                    violations: response.data.validation_result.violations
                });
            }

            next();
        } catch (error) {
            console.error('Evidence validation failed:', error);
            // Continue without blocking the request
            next();
        }
    }

    extractEvidenceFromRequest(req) {
        // Custom logic to extract evidence from request
        return {
            method: req.method,
            url: req.originalUrl,
            user_agent: req.get('User-Agent'),
            ip_address: req.ip,
            request_body: req.body,
            query_params: req.query,
            timestamp: new Date().toISOString()
        };
    }
}

// Express app setup
const app = express();
const evidenceMiddleware = new EvidenceValidationMiddleware(
    'http://localhost:8000',
    'your-api-key'
);

app.use(express.json());

// Apply validation middleware to specific routes
app.post('/api/process',
    evidenceMiddleware.validateEvidence.bind(evidenceMiddleware),
    (req, res) => {
        res.json({
            success: true,
            validation_result: req.validationResult
        });
    }
);

app.listen(3000, () => {
    console.log('Express app running on port 3000');
});
```

## Workflow System Integration

### Apache Airflow Integration

```python
from airflow.decorators import dag, task
from airflow.models.dagrun import DagRun
from datetime import datetime, timedelta
from evidence_validation_api.adapters.workflow import WorkflowEngineAdapter
import asyncio

class AirflowEvidenceValidator:
    def __init__(self, validation_api_url: str, api_key: str = None):
        self.adapter = WorkflowEngineAdapter("airflow", validation_api_url, api_key)

    async def validate_task_execution(self, task_instance, execution_result):
        """Validate Airflow task execution evidence."""
        return await self.adapter.validate_task_execution(
            task_id=task_instance.task_id,
            dag_id=task_instance.dag_id,
            execution_date=task_instance.execution_date,
            task_result=execution_result,
            task_logs=task_instance.log_url,
            execution_time=task_instance.duration.total_seconds() if task_instance.duration else None
        )

    async def close(self):
        await self.adapter.close()

# Airflow DAG with evidence validation
@dag(
    dag_id='data_pipeline_with_validation',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def data_pipeline_dag():
    validator = AirflowEvidenceValidator('http://localhost:8000', 'your-api-key')

    @task
    def extract_data():
        # Extract data logic
        return {"records_extracted": 10000, "source": "database"}

    @task
    def transform_data(data):
        # Transform data logic
        return {"records_transformed": 9500, "transformations": 5}

    @task
    def load_data(data):
        # Load data logic
        return {"records_loaded": 9500, "destination": "data_warehouse"}

    @task
    def validate_evidence(extraction_result, transformation_result, load_result):
        """Validate all task executions."""
        async def run_validations():
            await validator.validate_task_execution(
                task_id="extract_data",
                dag_id="data_pipeline_with_validation",
                execution_date=datetime.now(),
                task_result=extraction_result
            )

            await validator.validate_task_execution(
                task_id="transform_data",
                dag_id="data_pipeline_with_validation",
                execution_date=datetime.now(),
                task_result=transformation_result
            )

            await validator.validate_task_execution(
                task_id="load_data",
                dag_id="data_pipeline_with_validation",
                execution_date=datetime.now(),
                task_result=load_result
            )

        return asyncio.run(run_validations())

    # Define task dependencies
    extraction_result = extract_data()
    transformation_result = transform_data(extraction_result)
    load_result = load_data(transformation_result)
    validate_evidence(extraction_result, transformation_result, load_result)

data_pipeline_dag()
```

### Prefect Integration

```python
from prefect import flow, task, get_run_logger
from evidence_validation_api.adapters.workflow import WorkflowEngineAdapter
import asyncio

class PrefectEvidenceValidator:
    def __init__(self, validation_api_url: str):
        self.adapter = WorkflowEngineAdapter("prefect", validation_api_url)

    async def validate_task_execution(self, task_run, result):
        """Validate Prefect task execution evidence."""
        logger = get_run_logger()

        try:
            validation_result = await self.adapter.validate_task_execution(
                task_id=task_run.name,
                dag_id=task_run.flow_run.name,
                task_result=result,
                execution_time=task_run.total_run_seconds,
                logs=str(logger)
            )

            logger.info(f"Task validation completed: {validation_result.validation_result.is_valid}")
            return validation_result

        except Exception as e:
            logger.error(f"Task validation failed: {e}")
            return None

    async def close(self):
        await self.adapter.close()

validator = PrefectEvidenceValidator('http://localhost:8000')

@task
async def process_data_with_validation(data):
    """Process data with automatic evidence validation."""
    # Process data
    result = {"processed_items": len(data), "status": "success"}

    # Validate evidence
    task_run = await process_data_with_validation.get_run()
    validation_result = await validator.validate_task_execution(task_run, result)

    if validation_result and not validation_result.validation_result.is_valid:
        raise Exception(f"Evidence validation failed: {validation_result.validation_result.violations}")

    return result

@flow(name="data-processing-flow")
async def data_processing_flow(input_data):
    """Data processing flow with evidence validation."""
    results = []

    for batch in input_data:
        result = await process_data_with_validation(batch)
        results.append(result)

    await validator.close()
    return results

# Usage
if __name__ == "__main__":
    input_data = [{"id": i, "value": f"data_{i}"} for i in range(100)]
    asyncio.run(data_processing_flow(input_data))
```

## CI/CD Pipeline Integration

### GitHub Actions

```yaml
name: Evidence Validation CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-validate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install httpx

    - name: Run tests with evidence validation
      run: |
        python -c "
import asyncio
import httpx
import json
from datetime import datetime, timezone

async def validate_test_evidence():
    evidence_request = {
        'evidence': {
            'content_type': 'application/json',
            'data': {
                'test_type': 'unit_tests',
                'framework': 'pytest',
                'tests_run': 150,
                'tests_passed': 147,
                'tests_failed': 3,
                'coverage': 87.5
            }
        },
        'metadata': {
            'evidence_type': 'test_result',
            'source_system': 'github_actions',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'workflow_id': os.getenv('GITHUB_WORKFLOW'),
            'run_id': os.getenv('GITHUB_RUN_ID'),
            'repository': os.getenv('GITHUB_REPOSITORY'),
            'branch': os.getenv('GITHUB_REF_NAME')
        },
        'validation_rules': ['test_quality_metrics', 'coverage_standards'],
        'cache_strategy': 'short_term'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://validation-api:8000/validate',
            json=evidence_request,
            headers={'Authorization': f'Bearer {os.getenv(\"VALIDATION_API_KEY\")}'}
        )

        result = response.json()
        print(f'Validation result: {result[\"validation_result\"][\"is_valid\"]}')

        if not result['validation_result']['is_valid']:
            print(f'Violations: {result[\"validation_result\"][\"violations\"]}')
            exit(1)

asyncio.run(validate_test_evidence())
"
      env:
        VALIDATION_API_KEY: ${{ secrets.VALIDATION_API_KEY }}

    - name: Build application
      run: |
        python setup.py build

    - name: Validate build artifacts
      run: |
        python -c "
import asyncio
import httpx
import os
import hashlib

async def validate_build_artifacts():
    artifacts = []

    # Collect build artifacts
    for root, dirs, files in os.walk('dist/'):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                content = f.read()
                artifacts.append({
                    'path': file_path,
                    'size': len(content),
                    'hash': hashlib.sha256(content).hexdigest()
                })

    for artifact in artifacts:
        evidence_request = {
            'evidence': {
                'content_type': 'application/json',
                'data': artifact
            },
            'metadata': {
                'evidence_type': 'file_operation',
                'source_system': 'github_actions',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'tags': ['build', 'artifact', os.getenv('GITHUB_SHA')]
            },
            'validation_rules': ['file_integrity', 'size_validation'],
            'cache_strategy': 'medium_term'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://validation-api:8000/validate',
                json=evidence_request,
                headers={'Authorization': f'Bearer {os.getenv(\"VALIDATION_API_KEY\")}'}
            )

            result = response.json()
            print(f'Artifact {artifact[\"path\"]}: {result[\"validation_result\"][\"is_valid\"]}')

asyncio.run(validate_build_artifacts())
"
      env:
        VALIDATION_API_KEY: ${{ secrets.VALIDATION_API_KEY }}
```

### GitLab CI

```yaml
stages:
  - validate
  - build
  - test

variables:
  VALIDATION_API_URL: "http://validation-api:8000"
  VALIDATION_API_KEY: "$VALIDATION_API_KEY"

validate_code:
  stage: validate
  script:
    - |
      python3 << EOF
import httpx
import json
import os
from datetime import datetime, timezone

async def validate_pipeline_evidence():
    evidence_request = {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "pipeline_id": os.getenv("CI_PIPELINE_ID"),
                "job_id": os.getenv("CI_JOB_ID"),
                "stage": os.getenv("CI_JOB_STAGE"),
                "project": os.getenv("CI_PROJECT_NAME"),
                "branch": os.getenv("CI_COMMIT_REF_NAME"),
                "commit": os.getenv("CI_COMMIT_SHA")
            }
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "gitlab_ci",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tags": ["pipeline", os.getenv("CI_JOB_STAGE")]
        },
        "validation_rules": ["pipeline_integrity"],
        "cache_strategy": "short_term"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "$VALIDATION_API_URL/validate",
            json=evidence_request,
            headers={"Authorization": f"Bearer $VALIDATION_API_KEY"}
        )

        result = response.json()
        print(f"Pipeline validation: {result['validation_result']['is_valid']}")

        if not result['validation_result']['is_valid']:
            print(f"Violations: {result['validation_result']['violations']}")
            exit(1)

import asyncio
asyncio.run(validate_pipeline_evidence())
EOF
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Database Integration

### SQLAlchemy Integration

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from evidence_validation_api.adapters.data import DatabaseAdapter
import asyncio
import json

class DatabaseEvidenceValidator:
    def __init__(self, validation_api_url: str, database_url: str):
        self.adapter = DatabaseAdapter("sqlalchemy", validation_api_url)
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession)

    async def validate_query_event(self, connection, cursor, statement, parameters, context, executemany):
        """Validate SQL query execution."""
        if context and hasattr(context, 'execution_time'):
            evidence_data = {
                "query": str(statement),
                "parameters": str(parameters),
                "execution_time": context.execution_time,
                "rows_affected": cursor.rowcount if cursor else 0
            }

            await self.adapter.validate_query_execution(
                query=str(statement),
                database_name="app_db",
                execution_time=context.execution_time,
                rows_affected=cursor.rowcount if cursor else 0,
                user=context.get("user", "system")
            )

    async def setup_validation_listeners(self):
        """Set up SQLAlchemy event listeners for evidence validation."""
        event.listen(self.engine.sync_engine, "before_cursor_execute", self.validate_query_event)

    async def close(self):
        await self.adapter.close()
        await self.engine.dispose()

# Usage example
async def database_with_validation():
    validator = DatabaseEvidenceValidator(
        "http://localhost:8000",
        "postgresql+asyncpg://user:password@localhost/app_db"
    )

    await validator.setup_validation_listeners()

    # Use database with automatic validation
    async with validator.SessionLocal() as session:
        # Queries will be automatically validated
        result = await session.execute(
            "SELECT COUNT(*) FROM users WHERE active = true"
        )
        count = result.scalar()
        print(f"Active users: {count}")

    await validator.close()

asyncio.run(database_with_validation())
```

## WebSocket Integration

### Python WebSocket Client

```python
import asyncio
import json
import websockets
from typing import Dict, Callable, Optional

class EvidenceValidationWebSocketClient:
    def __init__(self, url: str, api_key: str = None):
        self.url = url
        self.api_key = api_key
        self.websocket = None
        self.callbacks: Dict[str, Callable] = {}
        self.is_connected = False

    async def connect(self):
        """Connect to the WebSocket server."""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        self.websocket = await websockets.connect(
            self.url,
            extra_headers=headers,
            ping_interval=20,
            ping_timeout=10
        )
        self.is_connected = True

        # Start message listener
        asyncio.create_task(self._listen_for_messages())

    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()

    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.is_connected = False

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'pong':
                return  # Handle ping/pong automatically

            # Call registered callbacks
            if message_type in self.callbacks:
                await self.callbacks[message_type](data)

        except json.JSONDecodeError:
            print(f"Invalid JSON received: {message}")
        except Exception as e:
            print(f"Error handling message: {e}")

    def on(self, message_type: str, callback: Callable):
        """Register a callback for a specific message type."""
        self.callbacks[message_type] = callback

    async def send_message(self, message: Dict):
        """Send a message to the WebSocket server."""
        if self.websocket and self.is_connected:
            await self.websocket.send(json.dumps(message))

    async def ping(self):
        """Send a ping message."""
        await self.send_message({
            'type': 'ping',
            'timestamp': '2024-01-15T10:30:00Z'
        })

    async def subscribe_to_validation(self, request_id: str):
        """Subscribe to validation updates for a specific request."""
        await self.send_message({
            'type': 'subscribe_validation',
            'request_id': request_id,
            'timestamp': '2024-01-15T10:30:00Z'
        })

# Usage example
async def websocket_validation_example():
    client = EvidenceValidationWebSocketClient(
        "ws://localhost:8000/ws",
        "your-api-key"
    )

    await client.connect()

    # Register callbacks
    async def on_validation_completed(data):
        print(f"Validation completed: {data['request_id']}")
        print(f"Is valid: {data['is_valid']}")

    async def on_validation_failed(data):
        print(f"Validation failed: {data['request_id']}")
        print(f"Violations: {data['violations']}")

    client.on('validation_completed', on_validation_completed)
    client.on('validation_failed', on_validation_failed)

    # Submit validation request
    import httpx
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            "http://localhost:8000/validate",
            json={
                "evidence": {
                    "content_type": "application/json",
                    "data": {"test": "data"}
                },
                "metadata": {
                    "evidence_type": "task_execution",
                    "source_system": "test_system",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "async_validation": True
            },
            headers={"Authorization": "Bearer your-api-key"}
        )

        request_data = response.json()
        request_id = request_data["request_id"]

    # Subscribe to validation updates
    await client.subscribe_to_validation(request_id)

    # Keep connection alive
    try:
        while client.is_connected:
            await client.ping()
            await asyncio.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()

asyncio.run(websocket_validation_example())
```

## Advanced Patterns

### Validation Pipeline with Dependencies

```python
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ValidationStage(Enum):
    CONTENT_INTEGRITY = "content_integrity"
    SECURITY_CHECK = "security_check"
    COMPLIANCE_CHECK = "compliance_check"
    PERFORMANCE_ANALYSIS = "performance_analysis"

@dataclass
class ValidationStep:
    stage: ValidationStage
    depends_on: List[ValidationStage]
    rules: List[str]
    required: bool = True

class EvidenceValidationPipeline:
    def __init__(self, adapter):
        self.adapter = adapter
        self.steps = [
            ValidationStep(
                ValidationStage.CONTENT_INTEGRITY,
                [],
                ["content_integrity"]
            ),
            ValidationStep(
                ValidationStage.SECURITY_CHECK,
                [ValidationStage.CONTENT_INTEGRITY],
                ["security_validation"]
            ),
            ValidationStep(
                ValidationStage.COMPLIANCE_CHECK,
                [ValidationStage.CONTENT_INTEGRITY],
                ["compliance_rules"]
            ),
            ValidationStep(
                ValidationStage.PERFORMANCE_ANALYSIS,
                [ValidationStage.CONTENT_INTEGRITY],
                ["performance_metrics"]
            )
        ]

    async def run_pipeline(self, evidence_request: Dict[str, Any]) -> Dict[str, Any]:
        """Run validation pipeline with dependencies."""
        results = {}
        completed_stages = set()

        for step in self.steps:
            # Wait for dependencies
            if not all(dep in completed_stages for dep in step.depends_on):
                continue

            try:
                # Create request for this stage
                stage_request = evidence_request.copy()
                stage_request["validation_rules"] = step.rules

                # Run validation
                result = await self.adapter.validate_evidence(
                    evidence_data=stage_request["evidence"]["data"],
                    evidence_type=EvidenceType.TASK_EXECUTION,
                    metadata=stage_request["metadata"],
                    validation_rules=step.rules
                )

                results[step.stage.value] = result

                if step.required and not result.validation_result.is_valid:
                    # Stop pipeline for required failures
                    break

                completed_stages.add(step.stage)

            except Exception as e:
                if step.required:
                    raise e
                results[step.stage.value] = {"error": str(e)}
                completed_stages.add(step.stage)

        return results

# Usage
pipeline = EvidenceValidationPipeline(adapter)
results = await pipeline.run_pipeline(evidence_request_dict)
```

### Retry Mechanism with Backoff

```python
import asyncio
import random
from typing import Callable, Any

class ValidationRetryManager:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if attempt == self.max_retries:
                    break

                # Calculate delay
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )

                # Add jitter
                if self.jitter:
                    delay *= (0.5 + random.random() * 0.5)

                print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)

        raise last_exception

# Usage
retry_manager = ValidationRetryManager(max_retries=3)

async def validate_with_retry(adapter, evidence_request):
    return await retry_manager.execute_with_retry(
        adapter.validate_evidence,
        evidence_data=evidence_request["evidence"]["data"],
        evidence_type=EvidenceType.TASK_EXECUTION,
        metadata=evidence_request["metadata"]
    )
```

## Error Handling

### Comprehensive Error Handling

```python
import asyncio
import httpx
from typing import Optional, Dict, Any
from enum import Enum

class ValidationErrorCode(Enum):
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"

class ValidationError(Exception):
    def __init__(
        self,
        code: ValidationErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code.value}: {message}")

class RobustEvidenceValidator:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def validate_evidence(
        self,
        evidence_request: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Validate evidence with comprehensive error handling."""
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.post("/validate", json=evidence_request)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise ValidationError(
                        ValidationErrorCode.AUTHENTICATION_ERROR,
                        "Invalid API key or authentication failed"
                    )
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise ValidationError(
                        ValidationErrorCode.RATE_LIMIT_ERROR,
                        f"Rate limit exceeded, retry after {retry_after} seconds",
                        {"retry_after": retry_after}
                    )
                elif response.status_code >= 500:
                    raise ValidationError(
                        ValidationErrorCode.SERVER_ERROR,
                        f"Server error: {response.status_code}",
                        {"status_code": response.status_code, "response": response.text}
                    )
                else:
                    raise ValidationError(
                        ValidationErrorCode.VALIDATION_ERROR,
                        f"Validation failed: {response.text}",
                        {"status_code": response.status_code}
                    )

            except httpx.TimeoutException:
                last_error = ValidationError(
                    ValidationErrorCode.TIMEOUT_ERROR,
                    f"Request timeout after {self.timeout} seconds"
                )
            except httpx.NetworkError as e:
                last_error = ValidationError(
                    ValidationErrorCode.NETWORK_ERROR,
                    f"Network error: {str(e)}"
                )
            except ValidationError:
                # Re-raise validation errors immediately
                raise
            except Exception as e:
                last_error = ValidationError(
                    ValidationErrorCode.VALIDATION_ERROR,
                    f"Unexpected error: {str(e)}"
                )

            if attempt < max_retries:
                # Exponential backoff
                delay = min(2 ** attempt, 30)
                print(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                await asyncio.sleep(delay)

        # All retries failed
        raise last_error

# Usage
async def robust_validation_example():
    evidence_request = {
        "evidence": {
            "content_type": "application/json",
            "data": {"test": "data"}
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "test_system",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }

    try:
        async with RobustEvidenceValidator(
            "http://localhost:8000",
            "your-api-key",
            timeout=30.0
        ) as validator:

            result = await validator.validate_evidence(evidence_request, max_retries=3)
            print(f"Validation successful: {result['validation_result']['is_valid']}")

    except ValidationError as e:
        print(f"Validation failed: {e}")

        if e.code == ValidationErrorCode.RATE_LIMIT_ERROR:
            retry_after = e.details.get("retry_after", 60)
            print(f"Retry after {retry_after} seconds")
        elif e.code == ValidationErrorCode.AUTHENTICATION_ERROR:
            print("Check your API key")
        elif e.code == ValidationErrorCode.TIMEOUT_ERROR:
            print("Request timed out, try reducing evidence size")

asyncio.run(robust_validation_example())
```

## Performance Optimization

### Connection Pooling and Batch Processing

```python
import asyncio
import httpx
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import json

class HighPerformanceEvidenceValidator:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        max_connections: int = 20,
        batch_size: int = 50
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.max_connections = max_connections
        self.batch_size = batch_size
        self.client = None

    async def __aenter__(self):
        # Create HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            limits=httpx.Limits(
                max_keepalive_connections=self.max_connections,
                max_connections=self.max_connections * 2
            ),
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def validate_batch(
        self,
        evidence_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate multiple evidence requests in batches."""
        results = []

        # Process requests in batches
        for i in range(0, len(evidence_requests), self.batch_size):
            batch = evidence_requests[i:i + self.batch_size]

            # Create concurrent tasks for batch
            tasks = [
                self._validate_single(request)
                for request in batch
            ]

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    # Handle errors
                    results.append({
                        "error": str(result),
                        "success": False
                    })
                else:
                    results.append({
                        "result": result,
                        "success": True
                    })

        return results

    async def _validate_single(self, evidence_request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single evidence request."""
        try:
            response = await self.client.post("/validate", json=evidence_request)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Validation failed: {e}")

    async def validate_stream(
        self,
        evidence_stream: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate evidence stream with controlled concurrency."""
        semaphore = asyncio.Semaphore(self.max_connections)

        async def validate_with_semaphore(request):
            async with semaphore:
                return await self._validate_single(request)

        # Create all tasks
        tasks = [
            validate_with_semaphore(request)
            for request in evidence_stream
        ]

        # Execute with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            result if not isinstance(result, Exception)
            else {"error": str(result), "success": False}
            for result in results
        ]

# Usage example
async def high_performance_example():
    # Generate test data
    evidence_requests = [
        {
            "evidence": {
                "content_type": "application/json",
                "data": {"task_id": f"task_{i}", "result": "success"}
            },
            "metadata": {
                "evidence_type": "task_execution",
                "source_system": "perf_test",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        for i in range(1000)  # 1000 requests
    ]

    async with HighPerformanceEvidenceValidator(
        "http://localhost:8000",
        "your-api-key",
        max_connections=50,
        batch_size=25
    ) as validator:

        # Batch processing
        print("Starting batch validation...")
        batch_results = await validator.validate_batch(evidence_requests)

        successful = sum(1 for r in batch_results if r.get("success", False))
        print(f"Batch validation completed: {successful}/{len(batch_results)} successful")

        # Stream processing
        print("Starting stream validation...")
        stream_results = await validator.validate_stream(evidence_requests)

        successful = sum(1 for r in stream_results if r.get("success", False))
        print(f"Stream validation completed: {successful}/{len(stream_results)} successful")

asyncio.run(high_performance_example())
```

This comprehensive documentation provides practical examples for integrating the Evidence Validation API with various systems, programming languages, and use cases. Each example includes error handling, performance considerations, and best practices for production usage.
