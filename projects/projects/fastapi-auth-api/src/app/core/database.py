"""
Database configuration and connection management for FastAPI authentication API.

Test Case ID: TC-DATABASE-001
Priority: High
Test Type: Database Configuration

Purpose:
Provide database connection management, session handling, and async operations
with proper connection pooling and error handling.

Algorithm Approach: Async SQLAlchemy with connection pooling
Time Complexity: O(1) - Connection management
Space Complexity: O(n) - Connection pool where n is pool size

Security Considerations:
- Connection security
- SQL injection prevention
- Connection pooling limits
- Error handling without information leakage
- Transaction management
"""

import asyncio
import logging
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

from .config import settings
from .exceptions import ConfigurationError, DatabaseError

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database engine and session factory
engine: object | None = None
async_session_maker: async_sessionmaker | None = None


def create_database_url() -> str:
    """
    Create database URL with proper driver and security settings.

    Algorithm Approach: URL construction with security validation
    Time Complexity: O(1) - String operations
    Space Complexity: O(1) - URL string

    Security Considerations:
    - Driver security selection
    - SSL enforcement for production
    - Connection parameter validation
    - Credential protection

    Returns:
    str: Complete database connection URL

    Raises:
    ConfigurationError: If database configuration is invalid
    """
    database_url = settings.DATABASE_URL

    # Convert sync URL to async if needed
    if database_url.startswith("sqlite:///"):
        # SQLite with async support
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif database_url.startswith("postgresql://"):
        # PostgreSQL with async driver
        return database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("mysql://"):
        # MySQL with async driver
        return database_url.replace("mysql://", "mysql+aiomysql://")
    else:
        # Assume URL is already async-compatible
        return database_url


def create_engine_kwargs() -> dict:
    """
    Create engine keyword arguments based on database type and settings.

    Algorithm Approach: Conditional configuration based on database type
    Time Complexity: O(1) - Configuration creation
    Space Complexity: O(1) - Configuration dictionary

    Security Considerations:
    - SSL configuration for production databases
    - Connection pooling limits
    - Pool timeout configuration
    - Connection security parameters

    Returns:
    dict: Engine configuration kwargs
    """
    database_url = create_database_url()
    kwargs = {}

    if database_url.startswith("sqlite+aiosqlite://"):
        # SQLite configuration
        kwargs.update(
            {
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,  # Connection timeout
                },
                "echo": settings.DEBUG,  # Enable query logging in debug
            }
        )
    elif database_url.startswith("postgresql+asyncpg://"):
        # PostgreSQL configuration
        kwargs.update(
            {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": 30,
                "pool_recycle": 3600,  # Recycle connections after 1 hour
                "echo": settings.DEBUG,
            }
        )

        # SSL configuration for production
        if settings.is_production:
            kwargs["connect_args"] = {"ssl": ssl.create_default_context()}

    elif database_url.startswith("mysql+aiomysql://"):
        # MySQL configuration
        kwargs.update(
            {
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "echo": settings.DEBUG,
            }
        )

        # SSL configuration for production
        if settings.is_production:
            kwargs["connect_args"] = {"ssl": {"check_hostname": False, "ssl": True}}

    else:
        # Default configuration
        kwargs.update(
            {
                "pool_size": min(settings.DATABASE_POOL_SIZE, 10),
                "max_overflow": min(settings.DATABASE_MAX_OVERFLOW, 20),
                "echo": settings.DEBUG,
            }
        )

    return kwargs


async def initialize_database() -> None:
    """
    Initialize database engine and session maker.

    Algorithm Approach: Async engine initialization with proper error handling
    Time Complexity: O(1) - Engine creation
    Space Complexity: O(1) - Engine object creation

    Security Considerations:
    - Connection validation
    - Error handling without credential exposure
    - Proper resource cleanup

    Raises:
    ConfigurationError: If database initialization fails
    """
    global engine, async_session_maker

    try:
        database_url = create_database_url()
        engine_kwargs = create_engine_kwargs()

        logger.info(
            f"Initializing database connection to: {database_url.split('://')[0]}://[REDACTED]"
        )

        # Create async engine
        engine = create_async_engine(database_url, **engine_kwargs)

        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        # Test database connection
        await test_database_connection()

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise ConfigurationError(f"Failed to initialize database: {str(e)}")


async def test_database_connection() -> None:
    """
    Test database connection health.

    Algorithm Approach: Simple connection test with error handling
    Time Complexity: O(1) - Connection attempt
    Space Complexity: O(1) - Connection object

    Security Considerations:
    - Connection validation without exposing credentials
    - Proper error logging
    - Timeout handling

    Raises:
    DatabaseError: If connection test fails
    """
    if not engine:
        raise ConfigurationError("Database engine not initialized")

    try:
        async with engine.begin() as connection:
            # Simple connection test
            if connection.dialect.name == "sqlite":
                await connection.execute("SELECT 1")
            else:
                await connection.execute("SELECT 1")

        logger.debug("Database connection test successful")

    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        raise DatabaseError(f"Database connection failed: {str(e)}")


async def create_tables() -> None:
    """
    Create all database tables.

    Algorithm Approach: Async table creation with proper ordering
    Time Complexity: O(n) - Where n is number of tables
    Space Complexity: O(1) - No additional memory usage

    Security Considerations:
    - Table creation validation
    - Migration safety
    - Error handling

    Raises:
    DatabaseError: If table creation fails
    """
    if not engine:
        raise ConfigurationError("Database engine not initialized")

    try:
        async with engine.begin() as connection:
            # Import all models to ensure they're registered

            # Create tables
            await connection.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Table creation failed: {str(e)}")
        raise DatabaseError(f"Failed to create tables: {str(e)}")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.

    Algorithm Approach: Context manager for session lifecycle
    Time Complexity: O(1) - Session creation
    Space Complexity: O(1) - Session object

    Security Considerations:
    - Automatic session cleanup
    - Transaction rollback on error
    - Connection pool management

    Yields:
    AsyncSession: Database session

    Raises:
    ConfigurationError: If session maker not initialized
    """
    if not async_session_maker:
        raise ConfigurationError("Database session maker not initialized")

    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def close_database() -> None:
    """
    Close database connections and cleanup resources.

    Algorithm Approach: Graceful shutdown with resource cleanup
    Time Complexity: O(1) - Connection closure
    Space Complexity: O(1) - Resource cleanup

    Security Considerations:
    - Proper connection cleanup
    - Resource leak prevention
    - Graceful shutdown handling
    """
    global engine, async_session_maker

    try:
        if engine:
            await engine.dispose()
            engine = None
            async_session_maker = None

        logger.info("Database connections closed successfully")

    except Exception as e:
        logger.error(f"Database cleanup error: {str(e)}")


def add_database_event_listeners() -> None:
    """
    Add event listeners for database operations monitoring.

    Algorithm Approach: Event listener registration
    Time Complexity: O(1) - Listener registration
    Space Complexity: O(1) - Listener objects

    Security Considerations:
    - Query logging for security monitoring
    - Performance monitoring
    - Error tracking
    """
    if not engine:
        return

    @event.listens_for(engine.sync_engine, "before_execute")
    def receive_before_execute(
        conn, clauseelement, multiparams, params, execution_options
    ):
        if settings.DEBUG:
            logger.debug(f"Executing SQL: {clauseelement}")

    @event.listens_for(engine.sync_engine, "after_execute")
    def receive_after_execute(
        conn, clauseelement, multiparams, params, execution_options, result
    ):
        if settings.DEBUG:
            logger.debug(f"SQL executed successfully: {clauseelement}")

    @event.listens_for(engine.sync_engine, "handle_error")
    def receive_handle_error(exception_context):
        logger.error(f"Database error: {exception_context.original_exception}")


class DatabaseHealthChecker:
    """
    Database health checking utility.

    Design Pattern: Health checker with periodic validation
    Provides database connectivity monitoring and health reporting.

    Security Considerations:
    - Non-destructive health checks
    - Error logging without credential exposure
    - Performance monitoring
    """

    def __init__(self):
        """Initialize health checker."""
        self.last_check_time = None
        self.is_healthy = False

    async def check_health(self) -> dict:
        """
        Check database health and return status.

        Algorithm Approach: Connection test with response time measurement
        Time Complexity: O(1) - Connection test
        Space Complexity: O(1) - Status dictionary

        Security Considerations:
        - Non-intrusive health check
        - Response time measurement
        - Error classification

        Returns:
        dict: Health check results
        """
        health_result = {
            "database": "unhealthy",
            "response_time_ms": None,
            "error": None,
            "timestamp": None,
        }

        if not engine:
            health_result["error"] = "Database engine not initialized"
            return health_result

        try:
            import time

            start_time = time.time()

            async with engine.begin() as connection:
                await connection.execute("SELECT 1")

            response_time = (time.time() - start_time) * 1000

            health_result.update(
                {
                    "database": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "timestamp": start_time,
                }
            )

            self.is_healthy = True
            self.last_check_time = start_time

        except Exception as e:
            health_result["error"] = str(e)
            self.is_healthy = False

        return health_result

    async def wait_for_connection(self, timeout_seconds: int = 30) -> bool:
        """
        Wait for database connection to be available.

        Algorithm Approach: Retry mechanism with exponential backoff
        Time Complexity: O(n) - Where n is retry attempts
        Space Complexity: O(1) - Constant space

        Security Considerations:
        - Configurable timeout
        - Exponential backoff for resource protection
        - Clean error handling

        Args:
        timeout_seconds: Maximum time to wait

        Returns:
        bool: True if connection successful
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                await test_database_connection()
                return True
            except Exception:
                wait_time = min(
                    2 ** int(time.time() - start_time), 5
                )  # Exponential backoff, max 5s
                await asyncio.sleep(wait_time)

        return False


# Global health checker instance
health_checker = DatabaseHealthChecker()


# Dependency for FastAPI
async def get_db():
    """
    FastAPI dependency for getting database session.

    Returns:
    AsyncSession: Database session
    """
    async for session in get_db_session():
        yield session
