"""
OpenAPI documentation examples for the Evidence Validation API.

This module contains comprehensive examples used in the OpenAPI/Swagger
documentation to demonstrate API usage patterns.
"""


# Example evidence validation request
EVIDENCE_VALIDATION_EXAMPLE = {
    "summary": "Validate task execution evidence",
    "description": "Example of validating evidence from a task execution",
    "value": {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "task_id": "data_processing_001",
                "task_name": "process_customer_data",
                "status": "completed",
                "execution_time": 145.7,
                "start_time": "2024-01-15T10:30:00Z",
                "end_time": "2024-01-15T10:32:25Z",
                "result": {
                    "status": "success",
                    "records_processed": 15420,
                    "records_failed": 3,
                    "output_location": "s3://processed-data/2024-01-15/customers.json",
                },
                "performance_metrics": {
                    "cpu_usage": 0.75,
                    "memory_usage": 0.62,
                    "network_io": 1024000,
                },
            },
            "content_hash": "sha256:a1b2c3d4e5f6...",
            "size_bytes": 1024,
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "data_pipeline",
            "source_component": "spark_job",
            "timestamp": "2024-01-15T10:32:30Z",
            "correlation_id": "workflow-12345",
            "workflow_id": "daily_etl_pipeline",
            "task_id": "customer_data_processing",
            "user_id": "data_engineer_001",
            "session_id": "session-abc123",
            "tags": ["etl", "customer_data", "spark"],
            "severity": "medium",
            "retention_period": "P90D",  # 90 days
            "encrypted": False,
        },
        "validation_rules": [
            "content_integrity",
            "metadata_completeness",
            "timestamp_validity",
            "performance_bounds",
        ],
        "cache_strategy": "medium_term",
        "priority": 7,
        "timeout_seconds": 60,
        "async_validation": False,
        "webhook_url": "https://webhook.example.com/validation-complete",
    },
}

# Async validation example
ASYNC_VALIDATION_EXAMPLE = {
    "summary": "Validate evidence asynchronously",
    "description": "Example of async validation for long-running processes",
    "value": {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "ml_model_training": {
                    "model_type": "random_forest",
                    "dataset": "customer_churn_v2",
                    "hyperparameters": {
                        "n_estimators": 100,
                        "max_depth": 10,
                        "random_state": 42,
                    },
                    "metrics": {
                        "accuracy": 0.892,
                        "precision": 0.887,
                        "recall": 0.901,
                        "f1_score": 0.894,
                    },
                }
            },
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "ml_platform",
            "timestamp": "2024-01-15T14:20:00Z",
            "workflow_id": "model_training_pipeline",
            "task_id": "train_churn_model_v2",
            "severity": "high",
        },
        "validation_rules": [
            "model_performance",
            "data_quality",
            "hyperparameter_validity",
        ],
        "cache_strategy": "long_term",
        "async_validation": True,
        "webhook_url": "https://ml-platform.example.com/training-complete",
        "timeout_seconds": 300,
    },
}

# Error evidence example
ERROR_EVIDENCE_EXAMPLE = {
    "summary": "Validate error log evidence",
    "description": "Example of validating error logs and failure evidence",
    "value": {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "error": {
                    "type": "ValueError",
                    "message": "Invalid input format for customer record",
                    "code": "ERR_INPUT_001",
                    "timestamp": "2024-01-15T09:45:12Z",
                    "stack_trace": 'Traceback (most recent call last):\n  File "processor.py", line 234, in process_customer\n    validate_customer_format(data)\n  File "validator.py", line 56, in validate_customer_format\n    raise ValueError(f"Invalid format: {error}")\nValueError: Invalid input format for customer record',
                    "context": {
                        "component": "data_validator",
                        "input_size": 1024,
                        "processing_stage": "validation",
                        "retry_count": 2,
                    },
                }
            },
        },
        "metadata": {
            "evidence_type": "error_log",
            "source_system": "data_processing_service",
            "source_component": "input_validator",
            "timestamp": "2024-01-15T09:45:15Z",
            "workflow_id": "data_ingestion_pipeline",
            "task_id": "validate_customer_input",
            "severity": "high",
            "tags": ["error", "validation", "input_format"],
            "user_id": "service_account_processor",
        },
        "validation_rules": [
            "error_analysis",
            "severity_assessment",
            "impact_evaluation",
        ],
        "cache_strategy": "short_term",
        "async_validation": False,
    },
}

# Performance metrics example
PERFORMANCE_METRICS_EXAMPLE = {
    "summary": "Validate performance metrics evidence",
    "description": "Example of validating system performance metrics",
    "value": {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "system_metrics": {
                    "timestamp": "2024-01-15T12:00:00Z",
                    "cpu": {
                        "usage_percent": 45.2,
                        "load_average": [1.2, 1.5, 1.3],
                        "cores": 8,
                    },
                    "memory": {
                        "total_gb": 32.0,
                        "used_gb": 18.7,
                        "available_gb": 13.3,
                        "usage_percent": 58.4,
                    },
                    "disk": {
                        "total_gb": 500.0,
                        "used_gb": 287.5,
                        "available_gb": 212.5,
                        "usage_percent": 57.5,
                        "read_iops": 1250,
                        "write_iops": 890,
                    },
                    "network": {
                        "bytes_in": 1048576000,  # 1GB
                        "bytes_out": 524288000,  # 512MB
                        "packets_in": 150000,
                        "packets_out": 120000,
                    },
                    "application": {
                        "active_connections": 245,
                        "requests_per_second": 125.5,
                        "average_response_time_ms": 145.2,
                        "error_rate_percent": 0.12,
                    },
                }
            },
        },
        "metadata": {
            "evidence_type": "performance_metric",
            "source_system": "monitoring_system",
            "source_component": "metrics_collector",
            "timestamp": "2024-01-15T12:00:05Z",
            "tags": ["performance", "system_metrics", "monitoring"],
            "severity": "low",
        },
        "validation_rules": [
            "metric_ranges",
            "performance_standards",
            "anomaly_detection",
        ],
        "cache_strategy": "short_term",
        "async_validation": False,
    },
}

# Security event example
SECURITY_EVENT_EXAMPLE = {
    "summary": "Validate security event evidence",
    "description": "Example of validating security-related events",
    "value": {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "security_event": {
                    "event_type": "authentication_failure",
                    "severity": "medium",
                    "source_ip": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "timestamp": "2024-01-15T15:30:22Z",
                    "details": {
                        "username": "admin",
                        "failure_reason": "Invalid password",
                        "attempt_count": 3,
                        "locked_out": True,
                        "geo_location": {"country": "Unknown", "city": "Unknown"},
                    },
                    "risk_score": 0.75,
                }
            },
        },
        "metadata": {
            "evidence_type": "security_event",
            "source_system": "auth_service",
            "source_component": "authentication_handler",
            "timestamp": "2024-01-15T15:30:25Z",
            "severity": "high",
            "tags": ["security", "authentication", "failure"],
            "retention_period": "P365D",  # 1 year for security events
        },
        "validation_rules": [
            "security_policy_compliance",
            "risk_assessment",
            "incident_procedure",
        ],
        "cache_strategy": "long_term",
        "async_validation": False,
    },
}

# Validation response examples
VALIDATION_RESPONSE_SUCCESS = {
    "summary": "Successful validation response",
    "description": "Example response for successful evidence validation",
    "value": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "evidence_id": "660f9500-f39c-52e5-b827-557766551111",
        "validation_result": {
            "is_valid": True,
            "confidence_score": 0.967,
            "validation_status": "validated",
            "validated_at": "2024-01-15T10:32:32.123Z",
            "validator_id": "content_integrity_validator",
            "validation_rules": [
                "content_integrity",
                "metadata_completeness",
                "timestamp_validity",
            ],
            "violations": [],
            "warnings": [
                "Performance metrics indicate higher than usual CPU usage",
                "Consider monitoring memory usage trends",
            ],
            "recommendations": [
                "Set up alerts for CPU usage above 80%",
                "Schedule regular performance reviews",
            ],
            "metadata": {
                "evidence_type": "task_execution",
                "source_system": "data_pipeline",
                "validation_timestamp": "2024-01-15T10:32:32.123Z",
                "processing_stage": "completed",
            },
        },
        "processing_time_ms": 245.67,
        "cached_result": False,
        "api_version": "1.0",
        "timestamp": "2024-01-15T10:32:32.456Z",
    },
}

VALIDATION_RESPONSE_PENDING = {
    "summary": "Async validation pending response",
    "description": "Example response for async validation that is still processing",
    "value": {
        "request_id": "770g0600-g49d-63f6-c938-668877662222",
        "evidence_id": "880h1700-h59e-74g7-d049-779988773333",
        "validation_result": {
            "is_valid": False,
            "confidence_score": 0.0,
            "validation_status": "pending",
            "validated_at": "2024-01-15T14:20:05.789Z",
            "validation_rules": [],
            "violations": [],
            "warnings": [],
            "recommendations": [],
            "metadata": {"async": True, "estimated_completion": "2024-01-15T14:25:00Z"},
        },
        "processing_time_ms": 12.34,
        "cached_result": False,
        "api_version": "1.0",
        "timestamp": "2024-01-15T14:20:05.890Z",
    },
}

VALIDATION_RESPONSE_FAILED = {
    "summary": "Failed validation response",
    "description": "Example response for failed evidence validation",
    "value": {
        "request_id": "990i1800-i69f-85g8-e159-889999884444",
        "evidence_id": "001j2900-j79g-96h9-f260-990001995555",
        "validation_result": {
            "is_valid": False,
            "confidence_score": 0.0,
            "validation_status": "rejected",
            "validated_at": "2024-01-15T09:45:18.234Z",
            "validator_id": "error_analysis_validator",
            "validation_rules": ["error_analysis", "severity_assessment"],
            "violations": [
                "Error contains sensitive information in stack trace",
                "Missing required error context information",
                "Error severity classification may be incorrect",
            ],
            "warnings": [
                "Error occurred during critical processing stage",
                "Similar errors have been detected recently",
            ],
            "recommendations": [
                "Sanitize stack traces before logging",
                "Include more contextual information in error logs",
                "Review error classification thresholds",
            ],
            "metadata": {
                "evidence_type": "error_log",
                "source_system": "data_processing_service",
                "error_category": "validation_error",
                "impact_level": "medium",
            },
        },
        "processing_time_ms": 89.12,
        "cached_result": False,
        "api_version": "1.0",
        "timestamp": "2024-01-15T09:45:18.567Z",
    },
}

# Status response examples
VALIDATION_STATUS_RESPONSE = {
    "summary": "Validation status response",
    "description": "Example response for validation status check",
    "value": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "validation_result": {
            "is_valid": True,
            "validation_status": "validated",
            "confidence_score": 0.967,
            "validated_at": "2024-01-15T10:32:32.123Z",
        },
    },
}

VALIDATION_STATUS_IN_PROGRESS = {
    "summary": "Validation in progress status",
    "description": "Example response for validation that is still in progress",
    "value": {
        "request_id": "770g0600-g49d-63f6-c938-668877662222",
        "status": "in_progress",
        "task_done": False,
        "task_cancelled": False,
        "progress": {
            "percentage": 45,
            "current_stage": "content_validation",
            "estimated_remaining_seconds": 120,
        },
    },
}

# Metrics response example
METRICS_RESPONSE = {
    "summary": "System metrics response",
    "description": "Example response for system metrics",
    "value": {
        "total_validations": 15420,
        "cache_hits": 12034,
        "cache_misses": 3386,
        "validation_errors": 23,
        "average_processing_time": 167.89,
        "active_validations": 5,
        "max_concurrent_validations": 100,
        "timestamp": "2024-01-15T16:00:00.000Z",
        "cache_hit_rate": 0.780,
        "success_rate": 0.9985,
        "performance": {
            "p50_processing_time": 145.2,
            "p95_processing_time": 289.7,
            "p99_processing_time": 445.3,
        },
    },
}

# Health check response example
HEALTH_CHECK_RESPONSE = {
    "summary": "Health check response",
    "description": "Example response for health check endpoint",
    "value": {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": 86400.45,
        "active_validations": 3,
        "queue_size": 7,
        "cache_stats": {"cache_hits": 5021, "cache_misses": 1323, "hit_rate": 0.791},
        "database_status": "connected",
        "redis_status": "connected",
        "last_health_check": "2024-01-15T16:00:05.000Z",
        "components": {
            "validation_service": "healthy",
            "database": "healthy",
            "redis": "healthy",
            "websocket_server": "healthy",
        },
    },
}

# WebSocket message examples
WEBSOCKET_PING_MESSAGE = {
    "summary": "WebSocket ping message",
    "description": "Example ping message for WebSocket connection",
    "value": {"message_type": "ping", "timestamp": "2024-01-15T16:00:00.000Z"},
}

WEBSOCKET_PONG_MESSAGE = {
    "summary": "WebSocket pong response",
    "description": "Example pong response from WebSocket server",
    "value": {"message_type": "pong", "timestamp": "2024-01-15T16:00:00.123Z"},
}

WEBSOCKET_SUBSCRIBE_MESSAGE = {
    "summary": "WebSocket subscription message",
    "description": "Example message to subscribe to validation updates",
    "value": {
        "message_type": "subscribe_validation",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-15T16:00:00.000Z",
    },
}

WEBSOCKET_VALIDATION_COMPLETED = {
    "summary": "WebSocket validation completed notification",
    "description": "Example message when validation is completed",
    "value": {
        "message_type": "validation_completed",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "evidence_id": "660f9500-f39c-52e5-b827-557766551111",
        "status": "validated",
        "is_valid": True,
        "confidence_score": 0.967,
        "timestamp": "2024-01-15T16:00:05.789Z",
    },
}

WEBSOCKET_VALIDATION_FAILED = {
    "summary": "WebSocket validation failed notification",
    "description": "Example message when validation fails",
    "value": {
        "message_type": "validation_failed",
        "request_id": "990i1800-i69f-85g8-e159-889999884444",
        "evidence_id": "001j2900-j79g-96h9-f260-990001995555",
        "status": "rejected",
        "is_valid": False,
        "violations": ["Missing required metadata fields"],
        "timestamp": "2024-01-15T16:00:05.789Z",
    },
}

# Error response examples
ERROR_RESPONSE_VALIDATION_FAILED = {
    "summary": "Validation service error",
    "description": "Example error response when validation fails",
    "value": {
        "error": "Evidence validation failed: Content integrity check failed",
        "error_code": "VALIDATION_FAILED",
        "status_code": 422,
        "timestamp": "2024-01-15T16:00:00.000Z",
        "request_id": "112k3900-k39l-07i0-g270-001112990666",
    },
}

ERROR_RESPONSE_SERVICE_UNAVAILABLE = {
    "summary": "Service unavailable error",
    "description": "Example error response when validation service is unavailable",
    "value": {
        "error": "Validation service not available",
        "error_code": "SERVICE_UNAVAILABLE",
        "status_code": 503,
        "timestamp": "2024-01-15T16:00:00.000Z",
    },
}

ERROR_RESPONSE_RATE_LIMITED = {
    "summary": "Rate limit exceeded error",
    "description": "Example error response when rate limit is exceeded",
    "value": {
        "error": "Rate limit exceeded. Maximum 100 requests per minute allowed.",
        "error_code": "RATE_LIMIT_EXCEEDED",
        "status_code": 429,
        "timestamp": "2024-01-15T16:00:00.000Z",
        "retry_after": 60,
    },
}

# Webhook payload examples
WEBHOOK_VALIDATION_COMPLETED_PAYLOAD = {
    "summary": "Webhook validation completed payload",
    "description": "Example payload sent to webhook when validation completes",
    "value": {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "validation_result": {
            "is_valid": True,
            "confidence_score": 0.967,
            "validation_status": "validated",
            "violations": [],
            "warnings": ["Consider monitoring performance trends"],
            "validated_at": "2024-01-15T16:00:05.789Z",
        },
        "timestamp": "2024-01-15T16:00:06.000Z",
        "processing_time_ms": 167.89,
    },
}
