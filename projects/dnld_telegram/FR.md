# Functional Requirements for dnld_telegram

This document outlines the functional requirements for the dnld_telegram system, a Telegram media downloader application.

## 1. Authentication and Configuration

- **FR1.1:** The system SHALL allow users to configure Telegram API credentials (API ID, API Hash) via environment variables or .env file.
- **FR1.2:** The system SHALL support session string generation and storage for Telegram authentication.
- **FR1.3:** The system SHALL validate Telegram API credentials before establishing connections.
- **FR1.4:** The system SHALL allow users to configure multiple Telegram channels for download operations via configuration files.

## 2. Channel Management

- **FR2.1:** The system SHALL allow users to specify which Telegram channels to download from.
- **FR2.2:** The system SHALL enumerate media files available in specified Telegram channels.
- **FR2.3:** The system SHALL support both full and incremental enumeration of channel media.
- **FR2.4:** The system SHALL maintain channel-specific download directories and metadata.

## 3. Media Download Operations

- **FR3.1:** The system SHALL download media files from specified Telegram channels.
- **FR3.2:** The system SHALL support downloading all media from a channel.
- **FR3.3:** The system SHALL support downloading specific messages by message ID.
- **FR3.4:** The system SHALL support limiting the number of messages processed during download operations.
- **FR3.5:** The system SHALL handle various media types (videos, images, documents) from Telegram.

## 4. File Management and Organization

- **FR4.1:** The system SHALL organize downloaded files into channel-specific directories.
- **FR4.2:** The system SHALL maintain temporary download directories for in-progress downloads.
- **FR4.3:** The system SHALL scan existing files in temporary directories.
- **FR4.4:** The system SHALL organize and move existing files from temporary to final directories.

## 5. Progress Tracking and Monitoring

- **FR5.1:** The system SHALL provide real-time progress tracking for download operations.
- **FR5.2:** The system SHALL support multiple progress display modes (tqdm, simple, alive, textual, rich, etc.).
- **FR5.3:** The system SHALL display concurrent download progress when enabled.
- **FR5.4:** The system SHALL log download operations and progress information.
- **FR5.5:** TQDM progress bars SHALL show elapsed/remaining time in "XXXe, XXXr" format (not "XXXe<XXXr").
- **FR5.6:** Main progress bar SHALL show combined download speed in MB/s from all active downloads.
- **FR5.7:** Individual file progress bars SHALL be positioned dynamically based on max concurrent setting.
- **FR5.8:** Progress display SHALL recover from terminal scrolling disruption through automatic refresh.
- **FR5.9:** Main progress bar SHALL show only elapsed time without misleading time-remaining estimates.
- **FR5.10:** Individual download progress bars SHALL only appear when actual download progress occurs (lazy loading).
- **FR5.11:** The system SHALL handle duplicate filenames in concurrent downloads without progress bar conflicts or overwrites.

## 6. Error Handling and Graceful Termination

- **FR6.1:** The system SHALL handle network interruptions gracefully during downloads.
- **FR6.2:** The system SHALL support graceful termination via Ctrl+C with proper cleanup.
- **FR6.3:** The system SHALL retry failed downloads with exponential backoff.
- **FR6.4:** The system SHALL provide informative error messages for common failure scenarios.
- **FR6.5:** The system SHALL categorize Telegram API errors (disconnection, rate_limit, protocol, media) for appropriate handling.
- **FR6.6:** The system SHALL suppress disconnection errors during graceful shutdown to prevent log spam.
- **FR6.7:** The system SHALL implement smart retry logic based on error type with appropriate delays.
- **FR6.8:** The system SHALL handle protocol errors with single retry and rate limits with exponential backoff.

## 7. Concurrency and Performance

- **FR7.1:** The system SHALL support configurable concurrent downloads.
- **FR7.2:** The system SHALL limit concurrent downloads to prevent overwhelming the Telegram API.
- **FR7.3:** The system SHALL manage system resources efficiently during long-running operations.
