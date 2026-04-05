# dnld_telegram - Code Flow and Dependency Map

Generated: 2025-08-27

## Executive Summary

This document maps the code flow and dependencies in the dnld_telegram application to help trace execution paths and identify where connection issues occur.

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Entry Points  │───▶│  Core Modules    │───▶│  Support Systems │
└─────────────────┘    └──────────────────┘    └──────────────────┘
│                      │                      │
├─ __main__.py         ├─ client.py           ├─ database/schema.py
├─ run_app.py          ├─ download.py         ├─ config/
├─ dnld_telegram.bat   ├─ enumeration.py      ├─ ui/displays/
                       ├─ file_discovery...   └─ utils/
                       └─ reverse_sync.py
```

## Critical Execution Path (Enumerate Operation)

### 1. Application Entry
```
dnld_telegram.bat
  └─ uv run python run_app.py
    └─ run_app.py imports and calls __main__.main()
      └─ dnld_telegram/download/__main__.py:main()
```

### 2. Core Initialization Flow
```python
# File: src/dnld_telegram/download/__main__.py

def main() -> None:
    # 1. Setup signal handlers (lines 107-111)
    setup_signal_handlers()

    # 2. Parse arguments and setup UI
    args = parse_args()
    console, ui_config = setup_console_and_ui(args)

    # 3. Run async main
    asyncio.run(async_main(args, console, ui_config))

async def async_main():
    # 4. Validate credentials and create client
    API_ID, API_HASH, SESSION_STRING = validate_credentials()
    client = await get_client(API_ID, API_HASH, SESSION_STRING)  # ⚠️ CRITICAL

    # 5. Process channels
    for channel_name, chat_id in channels.items():
        await process_single_channel(
            channel_name, chat_id, args, console, ui_config,
            termination_event, client, overall_stats  # ⚠️ Client passed here
        )
```

### 3. Channel Processing Flow
```python
# File: src/dnld_telegram/download/__main__.py:process_single_channel()

async def process_single_channel(..., client, ...):
    # 1. Setup directories using config system (lines 125-135)
    config_bridge = get_config_bridge()
    current_temp_download_dir = config_bridge.get_channel_temp_path(channel_name)
    current_save_directory = config_bridge.get_channel_media_path(channel_name)

    # 2. Call main operations handler
    await process_channel_operations(
        channel_name, chat_id, args, progress_display,
        current_save_directory, current_temp_download_dir,
        termination_event, client, overall_stats  # ⚠️ Client passed
    )
```

### 4. Enumerate Operation Flow
```python
# File: src/dnld_telegram/download/__main__.py:process_channel_operations()

async def process_channel_operations(..., client, ...):
    if args.enumerate:
        # 1. Call enumeration with client - THIS WORKS
        await enumerate_media_in_channel(
            client,  # ⚠️ Client used successfully here
            chat_id, args.limit, channel_name,
            is_incremental, progress_display, termination_event
        )

        # 2. Create FileDiscoveryCoordinator - FIXED to include client
        coordinator = FileDiscoveryCoordinator(
            channel_name, telegram_id=chat_id, client=client  # ⚠️ NOW includes client
        )

        # 3. Discover files - THIS IS WHERE ERROR OCCURS
        discovery = await coordinator.discover_complete_file_state()  # ⚠️ ERROR HERE
```

## Detailed Module Dependencies

### Core Client Management
```
src/dnld_telegram/download/client.py
├─ Imports:
│  ├─ telethon (TelegramClient, StringSession)
│  ├─ asyncio
│  └─ loguru.logger
│
├─ Functions:
│  ├─ validate_credentials() -> (int, str, str)
│  ├─ get_client(api_id, api_hash, session) -> TelegramClient
│  └─ [Enhanced with retry logic and connection validation]
│
└─ Used by:
   ├─ __main__.py:async_main()
   └─ test_*.py files
```

### Database Layer
```
src/dnld_telegram/download/database/schema.py
├─ Imports:
│  ├─ aiosqlite, aiosqlitepool
│  ├─ asyncio, sqlite3
│  └─ config.paths (get_channel_path)
│
├─ Key Components:
│  ├─ _connection_pools: dict[str, SQLiteConnectionPool]
│  ├─ _ConnectionContextManager (async context manager)
│  ├─ get_connection(channel_name) -> _ConnectionContextManager
│  ├─ initialize_channel_pool(channel_name)
│  └─ ensure_channel_exists(channel_name, telegram_id, description)
│
├─ Error Pattern:
│  └─ ValueError: "no active connection" caught in __aenter__() method
│     ├─ Identified as Telethon client error being misattributed
│     └─ Stack trace added for debugging
│
└─ Used by:
   ├─ file_discovery_coordinator.py:_get_database_files()
   ├─ enumeration.py (for storing messages)
   └─ reverse_sync.py
```

### File Discovery Coordinator
```
src/dnld_telegram/download/file_discovery_coordinator.py
├─ Imports:
│  ├─ database.schema (get_connection)
│  ├─ config.paths (get_channel_path, get_channel_media_path)
│  └─ json, logging, pathlib
│
├─ Class: FileDiscoveryCoordinator
│  ├─ __init__(channel_name, telegram_id=None, client=None)  # ⚠️ FIXED
│  ├─ discover_complete_file_state() -> FileDiscoveryResult
│  │  ├─ _scan_filesystem()
│  │  ├─ _get_database_files()  # ⚠️ Uses database connection
│  │  ├─ _match_files()
│  │  ├─ _should_reverse_sync()
│  │  └─ _estimate_downloadable_from_telegram()
│  └─ coordinate_sync_operations()
│
└─ Used by:
   └─ __main__.py:process_channel_operations() (lines 248, 315)
```

### Enumeration Plugin
```
src/dnld_telegram/download/plugins/enumeration.py
├─ Imports:
│  ├─ telethon (Message, types)
│  ├─ database.schema (get_connection, ensure_channel_exists)
│  ├─ client (ensure_client_connected)  # ⚠️ Connection management
│  └─ asyncio, datetime
│
├─ Key Functions:
│  ├─ enumerate_media_in_channel(client, chat_id, ...)  # ⚠️ WORKS
│  ├─ ensure_client_connected(client, operation_name)
│  │  ├─ Exponential backoff retry logic
│  │  ├─ Connection health checks
│  │  └─ Robust error recovery
│  └─ MediaMessagesDict (result container)
│
└─ Used by:
   └─ __main__.py:process_channel_operations()
```

## Critical Error Location Analysis

### Primary Issue: Database Connection Error in FileDiscoveryCoordinator

**Error Location**: `src/dnld_telegram/download/database/schema.py:271`
```python
# _ConnectionContextManager.__aenter__()
except Exception as e:
    logger.error(f"❌ Database connection failed for {self.channel_name}: {e}")
    # Exception type: ValueError
    # Exception details: no active connection
```

**Root Cause Analysis**:
1. **Error Type**: `ValueError: no active connection`
2. **Source**: This is a **Telethon client error**, not a database error
3. **Propagation**: The Telethon error propagates through the async call stack and gets caught by the database connection error handler
4. **Timing**: Occurs during `FileDiscoveryCoordinator.discover_complete_file_state()`

### Call Stack Analysis
```
__main__.py:process_channel_operations()
  └─ coordinator.discover_complete_file_state()  # file_discovery_coordinator.py:62
    └─ self._get_database_files()  # file_discovery_coordinator.py:76
      └─ async with get_connection(channel_name)  # database/schema.py:200
        └─ _ConnectionContextManager.__aenter__()  # database/schema.py:243
          └─ pool.connection().__aenter__()  # aiosqlitepool
            └─ ValueError: no active connection  # ⚠️ TELETHON ERROR
```

### Why This is a Telethon Issue
1. **Database operations don't use Telethon** - SQLite connections are independent
2. **Error message pattern** - "no active connection" is Telethon's specific error message
3. **Async context pollution** - Telethon client state affects async context manager execution
4. **Timing correlation** - Error occurs immediately after successful enumeration operation

## Configuration System

### Configuration Loading Chain
```
src/dnld_telegram/download/config/
├─ integration.py
│  └─ get_config_bridge() -> ConfigBridge
│     ├─ Loads app.toml (application settings)
│     ├─ Loads channels.toml (channel mappings)
│     └─ Provides path resolution methods
│
├─ paths.py
│  ├─ get_channel_path(channel_name) -> Path
│  ├─ get_channel_media_path(channel_name) -> Path
│  └─ get_channel_temp_path(channel_name) -> Path
│
└─ channels_toml_loader.py
   └─ load_channels() -> dict[str, int]
```

### Path Resolution Flow
```
Root Config: C:\_Python\_Projects\dnld_telegram\config.toml
channels_base = "E:/dnld_media/telegram/channels"

Channel Paths:
├─ Channel Dir: E:/dnld_media/telegram/channels/{channel_name}/
├─ Media Dir:   E:/dnld_media/telegram/channels/{channel_name}/_media/
├─ Temp Dir:    E:/dnld_media/telegram/channels/{channel_name}/_temp/
└─ Database:    E:/dnld_media/telegram/channels/{channel_name}/telegram_data.db
```

## UI System Dependencies

### Display Factory Pattern
```
src/dnld_telegram/ui/
├─ factory.py
│  └─ create_progress_display(ui_type) -> ProgressDisplay
│
├─ displays/
│  ├─ rich_display.py (default)
│  ├─ alive_display.py (--ui A)
│  ├─ simple_display.py (--ui simple)
│  └─ textual_display.py (--ui textual)
│
└─ protocols.py
   └─ ProgressDisplay (interface definition)
```

## Fix Implementation Summary

### Changes Made
1. **FileDiscoveryCoordinator Constructor**:
   - Added `client: Optional[Any] = None` parameter
   - Stores client reference for potential future use

2. **Main Application Updates**:
   - Updated both coordinator instantiations in `__main__.py` to pass client
   - Lines 248 and 315 now include `client=client` parameter

3. **Database Error Handling**:
   - Added stack trace logging for "no active connection" errors
   - Enhanced debugging to identify Telethon vs database errors

### Current Status
- ✅ Client is now passed to FileDiscoveryCoordinator
- ❓ Error still occurring - needs further investigation
- 🔍 Stack trace should reveal actual error source

## Recommendations for Further Investigation

1. **Add Client Health Check**:
   - Verify client connection before FileDiscoveryCoordinator operations
   - Add explicit client.is_connected() checks

2. **Isolate Database Operations**:
   - Test database operations completely independent of Telethon client
   - Verify connection pool functionality separately

3. **AsyncIO Context Analysis**:
   - Investigate if Telethon client affects asyncio event loop context
   - Check for async context manager conflicts

4. **Connection Lifecycle Management**:
   - Add explicit client connection management in FileDiscoveryCoordinator
   - Implement connection verification before database operations

## File Cross-Reference

### Import Hierarchy
```
__main__.py
├─ client.py (get_client, validate_credentials)
├─ plugins/enumeration.py (enumerate_media_in_channel)
├─ file_discovery_coordinator.py (FileDiscoveryCoordinator)
├─ download.py (get_messages_to_download)
├─ ui/factory.py (create_progress_display)
└─ config/integration.py (get_config_bridge)

file_discovery_coordinator.py
├─ database/schema.py (get_connection)
├─ config/paths.py (get_channel_path, get_channel_media_path)
└─ reverse_sync.py (sync_channel_database_with_filesystem)

database/schema.py
├─ aiosqlite, aiosqlitepool
├─ config/paths.py (get_channel_path)
└─ asyncio.Lock() for connection pool management
```

### Critical Files for "no active connection" Error
1. `src/dnld_telegram/download/__main__.py` - Main execution flow
2. `src/dnld_telegram/download/file_discovery_coordinator.py` - Error trigger point
3. `src/dnld_telegram/download/database/schema.py` - Error catch location
4. `src/dnld_telegram/download/client.py` - Client management
5. `src/dnld_telegram/download/plugins/enumeration.py` - Working client usage example

---

*This dependency map should help trace the exact code flow and identify where the Telethon "no active connection" error is propagating through the database connection system.*
