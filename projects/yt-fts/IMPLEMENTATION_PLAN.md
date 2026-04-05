# IMPLEMENTATION PLAN

## Overview
Add comprehensive edge case handling to batch_download flow to prevent data loss,
silent corruption, and improve reliability.

## Architecture
1. New module: resource_checks.py (memory, disk, HTTP utilities)
2. Enhanced error handling in batch_downloader.py
3. Pre-flight checks before processing
4. Specific exception handlers for different error types

## Changes Required
- Create resource_checks.py module
- Add pre-flight checks in batch_download()
- Enhance error handling in channel processing loop
- Add transaction rollback patterns
- Add cursor verification

## Data Flow
1. Pre-flight: Check memory, disk, DB integrity
2. Per-channel: Check resources, handle specific errors
3. Post-download: Verify integrity, cleanup resources

## Error Handling
- Distinguish DNS vs Timeout vs Connection errors
- Specific HTTP code responses
- Resource exhaustion checks
- Transaction atomicity

## Test Strategy
- Unit tests for resource checks
- Integration test for full flow
- Manual verification with --dry-run

## Standards
- Python 2025+ standards
- Dual-sink logging (file + console)
- Thread-safe operations
