"""
FastAPI application for standardized evidence validation API.

This module provides the main FastAPI application with:
- RESTful endpoints for evidence validation
- WebSocket support for real-time updates
- Comprehensive middleware and error handling
- OpenAPI documentation with examples
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models.database import get_database_manager, init_database
from .models.schemas import (
    EvidenceRequest,
    EvidenceResponse,
    SystemStatus,
    WebSocketMessage,
)
from .services.validation_service import EvidenceValidationService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get(__name__)

# Global variables
validation_service: EvidenceValidationService | None = None
websocket_connections: set[WebSocket] = set()
app_start_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting evidence validation API...")

    try:
        # Initialize database
        db_url = "postgresql+asyncpg://user:password@localhost/evidence_validation"
        await init_database(db_url)

        # Initialize validation service
        global validation_service
        db_manager = get_database_manager()
        redis_url = "redis://localhost:6379"
        validation_service = EvidenceValidationService(
            db_manager=db_manager,
            redis_url=redis_url,
            default_timeout=30,
            max_concurrent_validations=100,
        )
        await validation_service.initialize()

        logger.info("Evidence validation API started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down evidence validation API...")

    try:
        if validation_service:
            await validation_service.shutdown()

        logger.info("Evidence validation API shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Evidence Validation API",
    description="""
    Standardized Evidence Validation API with real-time checking,
    intelligent caching, and consistent interface for all system components.

    ## Features

    * **Real-time Validation**: Fast evidence validation with configurable rules
    * **Intelligent Caching**: Multi-layer caching with Redis and PostgreSQL
    * **Async Processing**: Background validation with webhook callbacks
    * **WebSocket Support**: Real-time validation updates
    * **Comprehensive Monitoring**: Metrics, health checks, and error tracking
    * **OpenAPI Documentation**: Interactive API documentation with examples
    """,
    version="1.0.0")
    contact={
        "name": "Evidence Validation Team",
        "email": "team@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Get current user from authentication token."""
    # This is a placeholder - implement proper authentication
    if credentials is None:
        return {"user_id": "anonymous", "permissions": []}

    # TODO: Validate JWT token and extract user info
    return {"user_id": "demo_user", "permissions": ["validate_evidence"]}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID and logging middleware."""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        request_id=request_id,
    )

    start_time = datetime.utcnow()
    response = await call_next(request)

    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time_ms=round(process_time, 2),
        request_id=request_id,
    )

    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/", response_model=dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Evidence Validation API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Health check endpoint."""
    uptime_seconds = (datetime.utcnow() - app_start_time).total_seconds()

    status_info = {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "active_validations": 0,
        "queue_size": 0,
        "cache_stats": {},
        "database_status": "unknown",
        "redis_status": "unknown",
        "last_health_check": datetime.utcnow(),
    }

    # Get service metrics if available
    if validation_service:
        try:
            metrics = await validation_service.get_metrics()
            status_info.update(
                {
                    "active_validations": metrics.get("active_validations", 0),
                    "queue_size": metrics.get("queue_size", 0),
                    "cache_stats": {
                        "cache_hits": metrics.get("cache_hits", 0),
                        "cache_misses": metrics.get("cache_misses", 0),
                        "hit_rate": (
                            metrics.get("cache_hits", 0)
                            / max(
                                1,
                                metrics.get("cache_hits", 0)
                                + metrics.get("cache_misses", 0),
                            )
                        ),
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")

    return SystemStatus(**status_info)


@app.post("/validate", response_model=EvidenceResponse)
async def validate_evidence(
    request: EvidenceRequest,
    background_tasks: BackgroundTasks,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Validate evidence with real-time checking and caching.

    ## Example Request

    ```json
    {
        "evidence": {
            "content_type": "application/json",
            "data": {
                "task_result": "success",
                "execution_time": 120.5,
                "output": {"status": "completed"}
            },
            "content_hash": "sha256_hash_here"
        },
        "metadata": {
            "evidence_type": "task_execution",
            "source_system": "workflow_engine",
            "timestamp": "2024-01-15T10:30:00Z",
            "severity": "medium"
        },
        "validation_rules": ["content_integrity", "metadata_completeness"],
        "cache_strategy": "medium_term",
        "async_validation": false
    }
    ```
    """
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")

    # Check permissions
    if "validate_evidence" not in current_user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        # Validate evidence
        response = await validation_service.validate_evidence(request)

        # Broadcast update via WebSocket if not async
        if not request.async_validation:
            await broadcast_websocket_message(
                {
                    "type": "validation_completed",
                    "request_id": str(response.request_id),
                    "evidence_id": str(response.evidence_id),
                    "is_valid": response.validation_result.is_valid,
                    "status": response.validation_result.validation_status,
                }
            )

        return response

    except Exception as e:
        logger.error(f"Evidence validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.get("/validate/{request_id}/status")
async def get_validation_status(
    request_id: UUID, current_user: dict[str, Any] = Depends(get_current_user)
):
    """Get status of an ongoing validation request."""
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")

    try:
        status = await validation_service.get_validation_status(request_id)

        if not status:
            raise HTTPException(status_code=404, detail="Validation request not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get validation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.delete("/validate/{request_id}")
async def cancel_validation(
    request_id: UUID, current_user: dict[str, Any] = Depends(get_current_user)
):
    """Cancel an ongoing validation request."""
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")

    # Check permissions
    if "cancel_validation" not in current_user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        cancelled = await validation_service.cancel_validation(request_id)

        if not cancelled:
            raise HTTPException(
                status_code=404,
                detail="Validation request not found or already completed",
            )

        # Broadcast cancellation
        await broadcast_websocket_message(
            {
                "type": "validation_cancelled",
                "request_id": str(request_id),
            }
        )

        return {"message": "Validation cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel validation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel validation: {str(e)}"
        )


@app.get("/metrics")
async def get_metrics(current_user: dict[str, Any] = Depends(get_current_user)):
    """Get validation service metrics."""
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")

    # Check permissions
    if "view_metrics" not in current_user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        metrics = await validation_service.get_metrics()
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time validation updates."""
    await websocket.accept()
    websocket_connections.add(websocket)

    try:
        logger.info(f"WebSocket connection established: {websocket.client}")

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                # Parse message
                message = WebSocketMessage.model_validate_json(data)

                # Handle different message types
                if message.message_type == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    )
                elif message.message_type == "subscribe_validation":
                    # Client wants to subscribe to validation updates
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "subscribed",
                                "request_id": str(message.request_id)
                                if message.request_id
                                else None,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    )

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_connections.discard(websocket)


async def broadcast_websocket_message(message: dict[str, Any]):
    """Broadcast message to all connected WebSocket clients."""
    if not websocket_connections:
        return

    message["timestamp"] = datetime.utcnow().isoformat()
    message_str = json.dumps(message)

    # Create tasks for all connections
    tasks = []
    for (
        websocket
    ) in websocket_connections.copy():  # Copy to avoid modification during iteration
        try:
            tasks.append(websocket.send_text(message_str))
        except Exception:
            # Remove broken connections
            websocket_connections.discard(websocket)

    # Send messages concurrently
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


@app.post("/webhook/validation-completed")
async def webhook_validation_completed(
    webhook_data: dict[str, Any], background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for async validation completion notifications.

    This endpoint can be called by external services to notify
    about validation completion.
    """
    try:
        request_id = webhook_data.get("request_id")
        if not request_id:
            raise HTTPException(
                status_code=400, detail="Missing request_id in webhook data"
            )

        # Broadcast to WebSocket clients
        await broadcast_websocket_message(
            {
                "type": "validation_completed_webhook",
                "request_id": request_id,
                "data": webhook_data,
            }
        )

        return {"status": "received", "request_id": request_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )


# Utility functions
def create_error_response(
    status_code: int,
    error_code: str,
    error_message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Create standardized error response."""
    content = {
        "error": error_message,
        "error_code": error_code,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if details:
        content["details"] = details

    return JSONResponse(status_code=status_code, content=content)


# Import json for WebSocket message handling
import json

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "evidence_validation_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
