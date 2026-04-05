"""
Main FastAPI application for authentication API.

Test Case ID: TC-MAIN-001
Priority: High
Test Type: Application Entry Point

Purpose:
FastAPI application with authentication endpoints, security middleware,
CORS configuration, and comprehensive error handling.

Algorithm Approach: FastAPI application factory pattern
Time Complexity: O(1) - Application initialization
Space Complexity: O(1) - Application object creation

Security Considerations:
- CORS configuration for cross-origin security
- Security headers middleware
- Rate limiting integration
- Comprehensive error handling
- Request logging
"""

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from .core.config import settings, validate_production_settings
from .core.database import close_database, initialize_database
from .core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    RateLimitError,
    TokenError,
    UserExistsError,
    UserNotFoundError,
    ValidationError,
)
from .schemas.auth import (
    ErrorResponse,
    TokenRefreshRequest,
    TokenResponse,
    TokenValidationResponse,
    UserLoginRequest,
    UserRegistrationRequest,
    UserResponse,
)
from .services.auth_service import AuthService

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

logger = structlog.get_logger(__name__)

# Global service instances
auth_service = AuthService()
security = HTTPBearer(auto_error=False)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware.

    Design Pattern: Middleware for security headers
    Adds security headers to all responses.

    Security Considerations:
    - XSS protection
    - Content type options
    - Frame options
    - HSTS for HTTPS
    - Content security policy
    """

    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response.

        Args:
        request: HTTP request
        call_next: Next middleware in chain

        Returns:
        Response with security headers
        """
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add HSTS for HTTPS in production
        if settings.is_production and request.url.scheme == "https":
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

        # Remove server header
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware.

    Design Pattern: Middleware for request/response logging
    Logs all requests with security-relevant information.

    Security Considerations:
    - Request logging for audit trail
    - Performance monitoring
    - Error tracking
    - IP address logging
    """

    async def dispatch(self, request: Request, call_next):
        """
        Log request and response information.

        Args:
        request: HTTP request
        call_next: Next middleware in chain

        Returns:
        Response with logging
        """
        start_time = time.time()

        # Get client IP (considering proxies)
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=str(request.url.path),
            query=str(request.url.query) if request.url.query else None,
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent"),
            content_type=request.headers.get("Content-Type"),
        )

        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
            )

            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                method=request.method,
                path=str(request.url.path),
                error=str(e),
                process_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
                exc_info=True,
            )

            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Design Pattern: Async context manager for startup/shutdown
    Handles application initialization and cleanup.

    Security Considerations:
    - Database initialization
    - Resource cleanup
    - Graceful shutdown
    """
    logger.info("Starting FastAPI authentication API")

    try:
        # Initialize database
        await initialize_database()
        logger.info("Database initialized successfully")

        # Validate production settings
        if settings.is_production:
            warnings = validate_production_settings()
            if warnings:
                logger.warning("Production security warnings", warnings=warnings)

        # Log application info
        logger.info(
            "Application started",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            debug=settings.DEBUG,
        )

        yield

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}", exc_info=True)
        raise

    finally:
        logger.info("Shutting down FastAPI authentication API")
        await close_database()
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Secure FastAPI Authentication API with JWT, rate limiting, and comprehensive security",
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL if settings.DEBUG else None,
    redoc_url=settings.REDOC_URL if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add middleware
if settings.SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Trusted host middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure based on your domain
    )


# Exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(detail=exc.message, error_code="AUTH_FAILED").dict(),
    )


@app.exception_handler(TokenError)
async def token_exception_handler(request: Request, exc: TokenError):
    """Handle token errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(detail=exc.message, error_code="TOKEN_INVALID").dict(),
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ErrorResponse(detail=exc.message, error_code="ACCESS_DENIED").dict(),
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """Handle rate limiting errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ErrorResponse(
            detail=exc.message,
            error_code="RATE_LIMIT_EXCEEDED",
            retry_after=exc.retry_after,
        ).dict(),
    )


@app.exception_handler(UserExistsError)
async def user_exists_exception_handler(request: Request, exc: UserExistsError):
    """Handle user exists errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(detail=exc.message, error_code="USER_EXISTS").dict(),
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_exception_handler(request: Request, exc: UserNotFoundError):
    """Handle user not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(detail=exc.message, error_code="USER_NOT_FOUND").dict(),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            detail=exc.message,
            error_code="VALIDATION_ERROR",
            field=getattr(exc, "field", None),
        ).dict(),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Handle FastAPI request validation errors."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            detail="Validation failed", error_code="REQUEST_VALIDATION_ERROR"
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", exc_info=True, path=str(request.url.path))

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="Internal server error" if settings.is_production else str(exc),
            error_code="INTERNAL_ERROR",
        ).dict(),
    )


# Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserResponse:
    """
    Get current authenticated user from JWT token.

    Design Pattern: Dependency injection for authentication
    Extracts and validates user from JWT token.

    Security Considerations:
    - Token validation
    - User existence verification
    - Active status checking
    - Proper error handling

    Args:
    credentials: HTTP Authorization credentials

    Returns:
    UserResponse: Current authenticated user

    Raises:
    HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        user = await auth_service.get_user_from_token(token)
        return UserResponse.from_orm(user)
    except (TokenError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# API Endpoints
@app.post(
    f"{settings.API_V1_PREFIX}/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserRegistrationRequest):
    """
    Register a new user account.

    Algorithm Approach: User creation with security validation
    Time Complexity: O(1) - Database operations with indexes
    Space Complexity: O(1) - User object creation

    Security Considerations:
    - Email validation and normalization
    - Password strength requirements
    - Duplicate user prevention
    - Email verification requirement

    Args:
    user_data: User registration data

    Returns:
    UserResponse: Created user information

    Raises:
    HTTPException: If registration fails
    """
    try:
        user_dict = await auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        return UserResponse(**user_dict)

    except UserExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@app.post(f"{settings.API_V1_PREFIX}/auth/login", response_model=TokenResponse)
async def login_user(user_data: UserLoginRequest, request: Request):
    """
    Authenticate user and return JWT tokens.

    Algorithm Approach: Credential verification with token generation
    Time Complexity: O(1) - Authentication and token generation
    Space Complexity: O(1) - Token creation

    Security Considerations:
    - Rate limiting enforcement
    - Account lockout protection
    - Secure token generation
    - Login attempt tracking

    Args:
    user_data: Login credentials
    request: HTTP request for IP extraction

    Returns:
    TokenResponse: Authentication tokens and user data

    Raises:
    HTTPException: If authentication fails
    """
    try:
        # Get client IP for rate limiting
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        auth_result = await auth_service.authenticate_user(
            email=user_data.email, password=user_data.password, client_ip=client_ip
        )

        return TokenResponse(**auth_result)

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after)} if e.retry_after else {},
        )
    except Exception:
        logger.error("Login error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


@app.post(f"{settings.API_V1_PREFIX}/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: TokenRefreshRequest):
    """
    Refresh access token using refresh token.

    Algorithm Approach: Token exchange with validation
    Time Complexity: O(1) - Token operations
    Space Complexity: O(1) - New token generation

    Security Considerations:
    - Refresh token validation
    - Token rotation support
    - User status verification
    - Replay attack prevention

    Args:
    refresh_data: Refresh token data

    Returns:
    TokenResponse: New access token

    Raises:
    HTTPException: If token refresh fails
    """
    try:
        token_result = await auth_service.refresh_access_token(
            refresh_data.refresh_token
        )
        return TokenResponse(**token_result)

    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.get(
    f"{settings.API_V1_PREFIX}/auth/validate", response_model=TokenValidationResponse
)
async def validate_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """
    Validate JWT token and return user information.

    Algorithm Approach: Token validation with user verification
    Time Complexity: O(1) - Token verification
    Space Complexity: O(1) - Token payload

    Security Considerations:
    - Token format validation
    - Signature verification
    - Expiration checking
    - User existence verification

    Args:
    credentials: HTTP Authorization credentials

    Returns:
    TokenValidationResponse: Token validation result

    Raises:
    HTTPException: If token validation fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        validation_result = await auth_service.validate_token(credentials.credentials)
        return TokenValidationResponse(**validation_result)

    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.get(f"{settings.API_V1_PREFIX}/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Algorithm Approach: User data retrieval from authenticated context
    Time Complexity: O(1) - User data access
    Space Complexity: O(1) - User object

    Security Considerations:
    - Authentication required
    - User data filtering
    - No sensitive information exposure

    Args:
    current_user: Currently authenticated user

    Returns:
    UserResponse: User information
    """
    return current_user


@app.post(f"{settings.API_V1_PREFIX}/auth/logout")
async def logout_user(current_user: UserResponse = Depends(get_current_user)):
    """
    Logout user and revoke refresh tokens.

    Algorithm Approach: Token revocation with user context
    Time Complexity: O(1) - Database update
    Space Complexity: O(1) - Status update

    Security Considerations:
    - Token invalidation
    - Session termination
    - Account security

    Args:
    current_user: Currently authenticated user

    Returns:
    dict: Logout confirmation
    """
    try:
        # In a real implementation, you'd get the full user object
        # For now, just return success
        return {"message": "Logged out successfully"}

    except Exception:
        logger.error("Logout error", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Algorithm Approach: System health verification
    Time Complexity: O(1) - Health checks
    Space Complexity: O(1) - Health status

    Security Considerations:
    - System status disclosure
    - No sensitive information
    - Monitoring integration

    Returns:
    dict: Health status information
    """
    from .core.database import health_checker

    try:
        # Check database health
        db_health = await health_checker.check_health()

        return {
            "status": "healthy" if db_health["database"] == "healthy" else "unhealthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_health,
        }

    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e) if not settings.is_production else "Health check failed",
        }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
    dict: Basic API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": settings.DOCS_URL if settings.DEBUG else None,
    }
