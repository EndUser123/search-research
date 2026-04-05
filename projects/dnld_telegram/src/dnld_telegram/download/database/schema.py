"""
Database schema for dnld_telegram

This module defines the SQLite database schema for storing channel data,
messages, media files, and download tracking with thread organization.
"""

import asyncio
import os
import sqlite3

import aiosqlite
from aiosqlitepool import SQLiteConnectionPool
from loguru import logger

# Global connection pools and lock
_connection_pools: dict[str, SQLiteConnectionPool] = {}
_pool_lock = asyncio.Lock()

# SQL Schema Definitions
SCHEMA_VERSION = 1

CREATE_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    telegram_id INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    reply_to_message_id INTEGER, -- Thread parent (NULL for thread roots)
    date TIMESTAMP NOT NULL,
    text TEXT,
    media_type TEXT,
    file_id TEXT,
    file_size INTEGER,
    filename TEXT,
    download_status TEXT DEFAULT 'pending', -- pending, downloading, completed, failed, skipped
    download_path TEXT,
    error_message TEXT,
    download_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id),
    UNIQUE(telegram_id, channel_id) -- Prevent duplicate messages per channel
);
"""

CREATE_DOWNLOAD_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    status TEXT NOT NULL, -- started, completed, failed, cancelled
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    file_size INTEGER,
    download_speed REAL, -- bytes per second
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);
"""

CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Indexes for performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_messages_channel_date ON messages(channel_id, date);",
    "CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(reply_to_message_id);",
    "CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(download_status);",
    "CREATE INDEX IF NOT EXISTS idx_messages_media ON messages(media_type) WHERE media_type IS NOT NULL;",
    "CREATE INDEX IF NOT EXISTS idx_messages_telegram_id ON messages(telegram_id);",
    "CREATE INDEX IF NOT EXISTS idx_messages_channel_telegram ON messages(channel_id, telegram_id);",
    "CREATE INDEX IF NOT EXISTS idx_download_history_message ON download_history(message_id);",
    "CREATE INDEX IF NOT EXISTS idx_channels_name ON channels(name);",
    "CREATE INDEX IF NOT EXISTS idx_channels_telegram_id ON channels(telegram_id);",
]

# Triggers for updated_at timestamp
CREATE_TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS update_channels_timestamp
    AFTER UPDATE ON channels
    BEGIN
        UPDATE channels SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS update_messages_timestamp
    AFTER UPDATE ON messages
    BEGIN
        UPDATE messages SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """,
]


def get_database_path(channel_name: str) -> str:
    """Get the database file path for a channel."""
    from ..config.paths import get_channel_path

    # Create databases directory
    db_dir = get_channel_path(channel_name)
    db_dir.mkdir(parents=True, exist_ok=True)

    return str(db_dir / "telegram_data.db")


def initialize_database(channel_name: str) -> str:
    """
    Initialize SQLite database for a channel with full schema.

    Args:
        channel_name: Name of the channel

    Returns:
        Path to the created database file
    """
    db_path = get_database_path(channel_name)

    try:
        with sqlite3.connect(db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON;")

            # Create tables
            conn.execute(CREATE_CHANNELS_TABLE)
            conn.execute(CREATE_MESSAGES_TABLE)
            conn.execute(CREATE_DOWNLOAD_HISTORY_TABLE)
            conn.execute(CREATE_SCHEMA_VERSION_TABLE)

            # Create indexes
            for index_sql in CREATE_INDEXES:
                conn.execute(index_sql)

            # Create triggers
            for trigger_sql in CREATE_TRIGGERS:
                conn.execute(trigger_sql)

            # Record schema version
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,),
            )

            conn.commit()
            logger.info(
                f"Database initialized for channel '{channel_name}' at {db_path}"
            )

    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database for channel '{channel_name}': {e}")
        raise

    return db_path


def get_database_size_gb(channel_name: str) -> float:
    """
    Get the size of a channel's database in GB.

    Args:
        channel_name: Name of the channel

    Returns:
        Database size in GB
    """
    db_path = get_database_path(channel_name)
    if not os.path.exists(db_path):
        return 0.0

    try:
        size_bytes = os.path.getsize(db_path)
        return size_bytes / (1024**3)  # Convert to GB
    except OSError:
        return 0.0


def calculate_optimal_sqlite_settings(size_gb: float) -> dict:
    """
    Calculate optimal SQLite settings based on database size.

    Args:
        size_gb: Database size in GB

    Returns:
        Dictionary with optimal SQLite settings
    """
    settings = {}

    # Cache size: 20MB per GB, max 2GB cache for very large databases
    if size_gb > 50:
        cache_mb = min(2048, int(size_gb * 20))
        settings["cache_size"] = -cache_mb * 1024  # Negative means KB
    else:
        settings["cache_size"] = -64 * 1024  # Default 64MB cache

    # Memory map size: 10% of DB size as memory map, max 4GB
    if size_gb > 10:
        mmap_gb = min(4, size_gb * 0.1)
        settings["mmap_size"] = int(mmap_gb * 1024 * 1024 * 1024)
    else:
        settings["mmap_size"] = 0  # Disable memory mapping for smaller DBs

    # Busy timeout scaling: longer for larger databases (enhanced for 50GB+ channels)
    if size_gb > 50:
        settings["busy_timeout"] = 60000  # 60 seconds for very large databases
    elif size_gb > 20:
        settings["busy_timeout"] = 30000  # 30 seconds for large databases
    elif size_gb > 5:
        settings["busy_timeout"] = 20000  # 20 seconds for medium databases
    else:
        settings["busy_timeout"] = 10000  # 10 seconds (default)

    # Connection pool size recommendation (for future implementation)
    settings["recommended_pool_size"] = min(10, max(2, int(size_gb / 5)))

    return settings


class _ConnectionContextManager:
    """
    Async context manager that provides optimized database connections from the pool.
    """

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self._pool_connection = None

    async def __aenter__(self):
        """Acquire connection from pool and apply optimizations."""
        from loguru import logger

        try:
            logger.debug(
                f"🔍 Acquiring database connection for channel: {self.channel_name}"
            )

            async with _pool_lock:
                if self.channel_name not in _connection_pools:
                    logger.debug(
                        f"🔧 Initializing new connection pool for: {self.channel_name}"
                    )
                    await initialize_channel_pool(self.channel_name)

            pool = _connection_pools[self.channel_name]
            logger.debug(f"✅ Got connection pool for: {self.channel_name}")

            # CRITICAL DEBUG: Add more detailed logging before pool connection
            logger.debug(f"🔍 Pool object type: {type(pool)}")
            logger.debug(
                f"🔍 Pool state before connection: {getattr(pool, '_pool_size', 'unknown')}"
            )

            # Use the pool's context manager to get a connection
            self._pool_connection = pool.connection()
            logger.debug("🔌 Acquiring connection from pool...")
            logger.debug(
                f"🔍 Pool connection object type: {type(self._pool_connection)}"
            )

            # This is where the error occurs - let's add maximum debugging
            logger.debug("🔍 About to call __aenter__ on pool connection...")
            conn = await self._pool_connection.__aenter__()
            logger.debug(
                f"✅ Connection acquired successfully for: {self.channel_name}"
            )

        except Exception as e:
            logger.error(f"❌ Database connection failed for {self.channel_name}: {e}")
            logger.error(
                f"📍 Connection pools available: {list(_connection_pools.keys())}"
            )
            logger.error(f"📍 Pool connection object: {self._pool_connection}")
            logger.error(f"📍 Pool object: {pool}")
            logger.error(f"📍 Exception type: {type(e).__name__}")
            logger.error(f"📍 Exception details: {str(e)}")

            # Check if this is the Telethon "no active connection" error being misattributed
            if "no active connection" in str(e).lower():
                logger.error(
                    "🚨 This appears to be a Telethon client error, not a database error!"
                )
                logger.error(
                    "🚨 The client may have disconnected during database operations"
                )

                # Add stack trace to understand where this error comes from
                import traceback

                logger.error(f"📍 Full stack trace:\n{traceback.format_exc()}")

            raise

        # Apply optimal settings based on database size
        size_gb = get_database_size_gb(self.channel_name)
        optimal_settings = calculate_optimal_sqlite_settings(size_gb)

        await conn.execute(f"PRAGMA busy_timeout = {optimal_settings['busy_timeout']};")
        await conn.execute(f"PRAGMA cache_size = {optimal_settings['cache_size']};")

        if optimal_settings["mmap_size"] > 0:
            await conn.execute(f"PRAGMA mmap_size = {optimal_settings['mmap_size']};")

        if size_gb > 20:
            logger.info(
                f"Applied large database optimizations for {self.channel_name}: "
                f"{size_gb:.1f}GB, cache={-optimal_settings['cache_size'] // 1024}MB, "
                f"timeout={optimal_settings['busy_timeout'] / 1000}s"
            )

        # Force WAL checkpoint to prevent lock issues from large WAL files
        try:
            await conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        except aiosqlite.Error:
            # If checkpoint fails, continue anyway - it's not critical
            pass

        return conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release connection back to pool."""
        if self._pool_connection:
            await self._pool_connection.__aexit__(exc_type, exc_val, exc_tb)


def get_connection(channel_name: str):
    """
    Get an async context manager for a database connection from the connection pool.
    Usage: async with get_connection(channel_name) as conn:
    """
    return _ConnectionContextManager(channel_name)


async def get_connection_pool(channel_name: str):
    """
    Get the connection pool for a specific channel.
    Initializes the pool if it doesn't exist.
    """
    async with _pool_lock:
        if channel_name not in _connection_pools:
            await initialize_channel_pool(channel_name)
        return _connection_pools[channel_name]


async def initialize_channel_pool(channel_name: str):
    """
    Initialize a connection pool for a specific channel with enhanced recovery.
    """
    from loguru import logger

    try:
        logger.debug(f"🚀 Initializing connection pool for: {channel_name}")
        db_path = get_database_path(channel_name)

        # Initialize database if it doesn't exist
        if not os.path.exists(db_path):
            logger.debug(f"📁 Database doesn't exist, creating: {db_path}")
            # CRITICAL FIX: Wrap blocking operation in thread executor
            await asyncio.to_thread(initialize_database, channel_name)
            logger.debug(f"✅ Database created: {db_path}")

        async def connection_factory():
            """Factory function to create robust database connections."""
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.debug(
                        f"🔌 Creating database connection (attempt {attempt + 1}/{max_retries})"
                    )

                    # Use more robust connection parameters with connection pooling fixes
                    conn = await aiosqlite.connect(
                        db_path,
                        timeout=30.0,  # Longer timeout
                        isolation_level=None,  # Auto-commit mode
                        check_same_thread=False,  # Allow cross-thread access
                    )

                    # Enable dictionary-like row access
                    conn.row_factory = aiosqlite.Row

                    # Apply conservative SQLite settings for stability
                    await conn.execute("PRAGMA journal_mode = WAL")
                    await conn.execute("PRAGMA synchronous = NORMAL")
                    await conn.execute("PRAGMA temp_store = MEMORY")
                    await conn.execute("PRAGMA foreign_keys = ON")
                    await conn.execute(
                        "PRAGMA busy_timeout = 30000"
                    )  # 30 second timeout

                    # CRITICAL: Ensure connection remains active for pooling
                    await conn.execute(
                        "PRAGMA optimize"
                    )  # Prepare connection for optimal use

                    # Test connection health with proper error handling
                    try:
                        cursor = await conn.execute("SELECT 1")
                        result = await cursor.fetchone()
                        await cursor.close()
                        if not result:
                            raise Exception("Connection test failed - no result")
                    except Exception as test_error:
                        await conn.close()
                        raise Exception(f"Connection health test failed: {test_error}")

                    logger.debug(
                        "✅ Database connection established and tested successfully"
                    )
                    return conn

                except Exception as e:
                    logger.warning(f"⚠️ Connection attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error(
                            f"❌ All {max_retries} connection attempts failed for {db_path}"
                        )
                        raise
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

        # EMERGENCY FIX: Bypass aiosqlitepool entirely due to health check failures
        # Use direct connection factory instead of pooling
        class _SimplestDirectPool:
            """Ultra-simple direct connection pool that avoids all threading issues"""

            def __init__(self, db_path):
                self.db_path = db_path

            def connection(self):
                """Return a simple direct connection context manager"""
                return _SimplestDirectConnection(self.db_path)

            def get_connection(self):
                """Return a simple direct connection context manager (compatibility)"""
                return _SimplestDirectConnection(self.db_path)

        class _SimplestDirectConnection:
            """Ultra-simple async context manager for direct aiosqlite connections"""

            def __init__(self, db_path):
                self.db_path = db_path
                self._connection = None

            async def __aenter__(self):
                # Create a completely fresh aiosqlite connection each time
                import aiosqlite

                self._connection = await aiosqlite.connect(
                    self.db_path,
                    timeout=30.0,
                    isolation_level=None,  # Auto-commit mode
                    check_same_thread=False,  # Allow cross-thread access
                )

                # Enable dictionary-like row access
                self._connection.row_factory = aiosqlite.Row

                # Apply basic SQLite settings
                await self._connection.execute("PRAGMA journal_mode = WAL")
                await self._connection.execute("PRAGMA synchronous = NORMAL")
                await self._connection.execute("PRAGMA foreign_keys = ON")

                return self._connection

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if self._connection:
                    try:
                        await self._connection.close()
                    except Exception as e:
                        logger.warning(f"Error closing connection: {e}")
                    finally:
                        self._connection = None
                return False

        pool = _SimplestDirectPool(db_path)
        _connection_pools[channel_name] = pool
        logger.info(
            f"✅ Initialized SIMPLE DIRECT connections for channel: {channel_name}"
        )

    except Exception as e:
        logger.error(f"❌ Failed to initialize connection pool for {channel_name}: {e}")
        # Clean up partial state
        if channel_name in _connection_pools:
            del _connection_pools[channel_name]
        raise


async def close_all_connection_pools():
    """
    Gracefully close all active connection pools.
    """
    async with _pool_lock:
        for channel_name, pool in list(_connection_pools.items()):
            try:
                await pool.close()
                logger.info(f"Closed connection pool for channel: {channel_name}")
                del _connection_pools[channel_name]
            except Exception as e:
                logger.warning(f"Error closing pool for {channel_name}: {e}")


async def ensure_channel_exists(
    channel_name: str, telegram_id: int, description: str | None = None
) -> int:
    """
    Ensure a channel exists in the database and return its ID.

    Args:
        channel_name: Name of the channel
        telegram_id: Telegram channel ID
        description: Optional channel description

    Returns:
        Channel ID in the database
    """
    logger.debug(
        f"ensure_channel_exists called with channel_name='{channel_name}', telegram_id={telegram_id}"
    )
    async with get_connection(channel_name) as conn:
        # Try to get existing channel
        cursor = await conn.execute(
            "SELECT id FROM channels WHERE name = ? OR telegram_id = ?",
            (channel_name, telegram_id),
        )
        row = await cursor.fetchone()

        if row:
            # Update if needed
            logger.debug(f"Channel exists with id={row['id']}, updating...")
            await conn.execute(
                "UPDATE channels SET name = ?, telegram_id = ?, description = ? WHERE id = ?",
                (channel_name, telegram_id, description, row["id"]),
            )
            await conn.commit()
            logger.debug("Channel updated successfully")
            return row["id"]
        else:
            # Create new channel
            logger.debug("Creating new channel...")
            cursor = await conn.execute(
                "INSERT INTO channels (name, telegram_id, description) VALUES (?, ?, ?)",
                (channel_name, telegram_id, description),
            )
            new_id = cursor.lastrowid
            if new_id is None:
                raise RuntimeError(
                    f"Failed to create channel '{channel_name}' - INSERT returned no ID"
                )
            await conn.commit()
            logger.debug(f"Channel created with id={new_id}")
            return new_id


def check_database_health(channel_name: str) -> dict:
    """
    Check database health and return statistics.

    Args:
        channel_name: Name of the channel

    Returns:
        Dictionary with database statistics
    """
    try:
        with get_connection(channel_name) as conn:
            stats = {}

            # Get table counts
            tables = ["channels", "messages", "download_history"]
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()["count"]

            # Get database file size
            db_path = get_database_path(channel_name)
            if os.path.exists(db_path):
                stats["file_size_mb"] = os.path.getsize(db_path) / (1024 * 1024)

            # Get schema version
            cursor = conn.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            )
            row = cursor.fetchone()
            stats["schema_version"] = row["version"] if row else 0

            return stats

    except sqlite3.Error as e:
        logger.error(f"Database health check failed for '{channel_name}': {e}")
        return {"error": str(e)}
