# Architecture Design Record for dnld_telegram

This document records significant architectural decisions made during the development of the dnld_telegram system, a Telegram media downloader application.

## 1. Overall Architecture

- **Decision:** The system will adopt a modular, asynchronous architecture with pluggable UI components.
- **Rationale:** This approach promotes modularity, maintainability, and allows for easy extension of UI options while leveraging Python's async capabilities for I/O operations.
- **Alternatives Considered:** Monolithic synchronous architecture (rejected due to performance concerns with I/O operations).

## 2. Technology Stack

- **Decision:**
    - **Core:** Python 3.9+ with asyncio for asynchronous operations
    - **Telegram Client:** Telethon library for Telegram API interaction
    - **UI Components:** Multiple options (tqdm, rich, textual, alive-progress) with factory pattern
    - **Configuration:** python-dotenv for environment management
    - **Logging:** loguru for enhanced logging capabilities
- **Rationale:** These technologies were chosen for their performance, community support, and suitability for the specific requirements of a Telegram downloader.
- **Alternatives Considered:**
    - Telegram Client: pyrogram, telegram-bot-api
    - UI Libraries: Single UI approach vs. pluggable architecture

## 3. Progress Display Architecture

- **Decision:** Implement a factory pattern with abstract base classes for multiple progress display implementations.
- **Rationale:** This allows users to choose from different UI experiences while maintaining a consistent interface. The factory pattern enables easy addition of new display modes.
- **Alternatives Considered:** Single progress display implementation (rejected due to limited user choice and flexibility).

## 4. File Management and Storage

- **Decision:** Use a two-tier directory structure with temporary and final storage locations.
- **Rationale:** Temporary directories allow for safe download operations and cleanup, while final directories organize content by channel. This approach prevents data loss during interrupted downloads.
- **Alternatives Considered:** Direct download to final location (rejected due to risk of partial files).

## 5. Concurrency Management

- **Decision:** Implement configurable concurrent downloads with asyncio semaphore control.
- **Rationale:** This prevents overwhelming the Telegram API while allowing users to optimize performance based on their connection and system capabilities.
- **Alternatives Considered:** Fixed concurrency limits (rejected due to lack of flexibility).

## 6. Configuration Management

- **Decision:** Support both environment variables and TOML configuration files with fallback mechanisms.
- **Rationale:** Environment variables provide security for credentials, while TOML files offer structured configuration for complex setups. The fallback mechanism ensures usability in different environments.
- **Alternatives Considered:** Single configuration method (rejected due to limited deployment flexibility).

## 7. Error Handling and Graceful Termination

- **Decision:** Implement global termination events and proper resource cleanup with signal handlers.
- **Rationale:** This ensures that long-running operations can be safely interrupted while preserving data integrity and cleaning up temporary resources.
- **Alternatives Considered:** Force termination (rejected due to potential data corruption and resource leaks).

## 8. Logging Architecture

- **Decision:** Use loguru with both console and file handlers, supporting rich formatting when available.
- **Rationale:** Loguru provides enhanced logging capabilities with minimal configuration, while supporting graceful degradation when rich formatting is not available.
- **Alternatives Considered:** Standard library logging (rejected due to limited features and formatting capabilities).

## 9. Plugin Architecture

- **Decision:** Implement plugin system for extensible functionality (e.g., enumeration strategies).
- **Rationale:** This allows for future extension of features without modifying core code, promoting maintainability and feature evolution.
- **Alternatives Considered:** Monolithic feature implementation (rejected due to reduced maintainability).

## 10. Testing Strategy

- **Decision:** Implement unit tests for core components and integration tests for download workflows.
- **Rationale:** This ensures reliability of critical operations while allowing for safe refactoring and feature additions.
- **Alternatives Considered:** Manual testing only (rejected due to scalability and reliability concerns).

## 11. TQDM Progress Bar Design

- **Decision:** Use TQDM with dynamic positioning, combined speed calculation, automatic refresh mechanisms, and configurable UI behavior via UIConfig.
- **Rationale:** TQDM provides clean terminal output with real-time feedback while being resilient to terminal disruption. Dynamic positioning adapts to concurrent download settings; configurable options allow environment-appropriate output (emoji vs ASCII, alignment), and combined speed calculation gives meaningful overall throughput.
- **Implementation Details:**
  - Individual file bars positioned at 0 to max_concurrent-1; main bar positioned at max_concurrent (dynamic)
  - Automatic refresh to recover from scrolling; throttled updates to reduce flicker
  - Time format: "elapsed_time_e, remaining_time_r" (comma-separated)
  - Main bar shows combined MB/s speed from active downloads
  - Lazy loading: progress bars only appear when download progress occurs
  - Unique internal keys (filename#1, filename#2) prevent duplicate filename conflicts; original filenames preserved for display
  - Description formatting: dynamic file-type icon selected by extension with ASCII fallback; configurable name truncation/padding
  - Separator formatting: enforce "n / total"; fixed-width padding applied to elapsed/remaining/rate to keep dividers aligned across bars
  - Resize handling: dynamic_ncols enabled; minimal desc changes and throttled refresh to limit jitter
- **UIConfig Options (relevant to TQDM):**
  - `icons_on` (bool): enable/disable icons in descriptions
  - `ascii_only` (bool): force ASCII tags (e.g., [VID], [IMG]) instead of emoji
  - `align_stats` (bool): enable fixed-width padding for stats fields
  - `max_name_width` (int): truncate/pad file display name to this width
- **Alternatives Considered:**
  - Fixed positioning (rejected due to spacing issues)
  - Rich Layout-based display (rejected to maintain TQDM simplicity)
  - Time remaining estimates on main bar (rejected as misleading)

## 12. Telegram API Error Handling Architecture

- **Decision:** Implement structured error categorization with type-specific retry logic and graceful shutdown handling.
- **Rationale:** Telegram API has predictable error patterns that benefit from specialized handling. Structured approach reduces log noise and improves reliability.
- **Implementation Details:**
  - Error categories: disconnection, rate_limit, protocol, media, unknown
  - Retry strategies: protocol (1 retry, 1s delay), rate_limit (3 retries, exponential backoff), media (1 retry, 2s delay)
  - Graceful shutdown: suppress disconnection and protocol errors during termination
  - Centralized error handling through TelegramErrorHandler class
- **Alternatives Considered:**
  - Generic retry for all errors (rejected due to inappropriate handling of different error types)
  - No error categorization (rejected due to log noise and poor UX)
