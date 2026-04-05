# ADR-008: Log File Overwrite Behavior

-   **Status:** Accepted
-   **Date:** 2025-06-27
-   **Deciders:** Project Team

## Context and Problem Statement

The application generates structured JSON logs to a file (`logs/vidrec.json`) for debugging and run analysis. A decision is required on how this log file should behave across multiple application runs. The primary options are:

1.  **Append/Rotate:** Append new logs to the existing file and rotate it when it reaches a certain size or age.
2.  **Overwrite:** Truncate and overwrite the log file completely on each new application run.

The initial implementation used a `TimedRotatingFileHandler`, which appends logs. This led to confusion, as logs from multiple runs were mixed, making it difficult to analyze the most recent execution. It also created the potential for unbounded disk space usage.

## Decision

The application's primary log file, `logs/vidrec.json`, **MUST** be overwritten at the start of each execution.

This is implemented in `src/logger.py` by configuring the `'file'` handler as follows:

```python
'handlers': {
    'file': {
        'class': 'logging.FileHandler',
        'mode': 'w',  # 'w' for write/overwrite
        'formatter': 'json_formatter',
        'filename': log_file,
        'encoding': 'utf-8',
    },
    # ... other handlers
}
