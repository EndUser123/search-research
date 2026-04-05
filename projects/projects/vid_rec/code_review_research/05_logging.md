# AI Coder's Guide to Effective Logging

This guide provides best practices for logging in Python, specifically tailored for an AI coder. By following these guidelines, you can write more debuggable, maintainable, and observable applications.

## 1. Use the `logging` Module

**The Problem:** Using `print()` statements for logging is inflexible, difficult to control, and lacks features like severity levels, handlers, and formatters.

**The Solution:** Always use Python's built-in `logging` module. It provides a robust and configurable way to track events in your code, offering fine-grained control over what, where, and how logs are recorded.

## 2. Avoid the Root Logger

**The Problem:** Using the root logger (`logging.getLogger()`) makes it difficult to control log settings for different parts of your application independently. All messages from the root logger propagate to its handlers, leading to less granular control.

**The Solution:** Create a specific logger for each module or logical component of your application. This allows for more granular control over logging levels, handlers, and propagation, making it easier to manage and debug specific parts of your system.

```python
# In my_module.py
import logging
logger = logging.getLogger(__name__) # Creates a logger named 'my_module'

logger.info("This is an informational message from my_module.")
```

## 3. Centralize Logging Configuration

**The Problem:** Inconsistent logging configuration across your application makes it difficult to manage, update, and ensure all parts of your system are logging correctly.

**The Solution:** Centralize your logging configuration in a dedicated module or file that is loaded once at application startup. You can configure logging using Python code, a configuration file (e.g., `.ini`, `.yaml`), or a dictionary (`logging.config.dictConfig`).

**Example (using `dictConfig`):**

```python
# In a dedicated logging_config.py file
import logging.config
import os

def setup_logging(log_level="INFO", log_file="app.log"):
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_file,
                'maxBytes': 10485760, # 10 MB
                'backupCount': 5,
                'formatter': 'json'
            }
        },
        'loggers': {
            '': { # Root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True
            },
            'my_app.database': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False # Prevent messages from going to root logger
            }
        }
    }
    logging.config.dictConfig(logging_config)

# In your main application file
# from logging_config import setup_logging
# setup_logging(log_level="DEBUG", log_file="logs/debug.log")
# logger = logging.getLogger(__name__)
# logger.debug("Logging is configured!")
```

## 4. Use Appropriate Log Levels

**The Problem:** Using the wrong log level can make it difficult to filter, prioritize, and understand your logs, leading to information overload or missed critical events.

**The Solution:** Use the appropriate log level for each message to accurately reflect its severity and importance.

*   **DEBUG:** Detailed information, typically of interest only when diagnosing problems (e.g., variable values, function entry/exit).
*   **INFO:** Confirmation that things are working as expected (e.g., application startup, successful operation).
*   **WARNING:** An indication that something unexpected happened, or a problem might occur in the future, but the application can still proceed (e.g., deprecated feature used, minor configuration issue).
*   **ERROR:** Due to a more serious problem, the software has not been able to perform some function (e.g., failed API call, invalid input that prevents processing).
*   **CRITICAL:** A serious error, indicating that the program itself may be unable to continue running or data integrity is at risk (e.g., database connection lost, unhandled exception leading to crash).

## 5. Write Meaningful and Structured Log Messages

**The Problem:** Vague, unstructured log messages make it difficult to understand the application's state, especially when analyzing large volumes of logs or using automated parsing tools.

**The Solution:** Write descriptive and structured log messages. Structured logging involves logging data as key-value pairs (e.g., JSON), making logs easily parsable by machines and more informative for humans.

**Example (using `structlog` for structured logging):**

```python
import structlog

# Assuming structlog is configured (e.g., via setup_logging in a real app)
log = structlog.get_logger(__name__)

def process_order(order_id, item_count, customer_id):
    try:
        if item_count <= 0:
            log.warning("Attempted to process order with no items", order_id=order_id, item_count=item_count)
            return False
        # Simulate processing
        log.info("Processing order", order_id=order_id, item_count=item_count, customer_id=customer_id)
        # ... actual processing logic ...
        log.info("Order processed successfully", order_id=order_id, status="completed")
        return True
    except Exception as e:
        log.error("Failed to process order", order_id=order_id, error=str(e), exc_info=True)
        return False

process_order("ORD-123", 5, "CUST-ABC")
process_order("ORD-456", 0, "CUST-DEF")
```

**Why this is better:**
*   **Machine Readability:** Structured logs (like JSON) can be easily ingested and queried by log management systems (e.g., ELK Stack, Splunk, Datadog).
*   **Contextual Information:** Key-value pairs provide immediate context without needing to parse complex strings.
*   **Searchability:** You can easily search and filter logs based on specific keys (e.g., `order_id="ORD-123"`).
*   **Consistency:** Encourages consistent logging practices across the codebase.

## 6. Don't Log Sensitive Information

**The Problem:** Logging sensitive data like passwords, API keys, personal identifiable information (PII), or financial details is a major security risk and can lead to data breaches and compliance violations.

**The Solution:** Be extremely careful not to log sensitive data. Implement masking or redaction for any sensitive information that might inadvertently appear in logs.

*   **Masking/Redaction:** Replace sensitive parts of data with asterisks or other placeholders (e.g., `password="********"`).
*   **Avoid Logging Raw Input:** Never log raw user input that might contain sensitive data.
*   **Review Log Content:** Regularly review your log content, especially in development and staging environments, to ensure no sensitive data is being logged.

## 7. Handle Exceptions Gracefully

**The Problem:** Unhandled exceptions can crash your application, lead to unexpected behavior, and make it difficult to debug without sufficient context.

**The Solution:** When an exception occurs, log it with a traceback to provide as much context as possible for debugging. This allows you to diagnose issues without exposing internal details to end-users.

```python
import logging

logger = logging.getLogger(__name__)

def divide_numbers(a, b):
    try:
        result = a / b
        return result
    except ZeroDivisionError as e:
        # Log the exception with exc_info=True to include the full traceback
        logger.error("Attempted to divide by zero.", exc_info=True)
        return None
    except TypeError as e:
        logger.error("Invalid types for division operation.", exc_info=True)
        return None

divide_numbers(10, 0)
divide_numbers(10, "two")
```

## 8. Use Log Rotation

**The Problem:** Log files can grow indefinitely, consuming excessive disk space and making them difficult to manage, transfer, and analyze.

**The Solution:** Use log rotation to prevent log files from growing too large. The `logging.handlers` module provides handlers like `RotatingFileHandler` (rotates based on file size) and `TimedRotatingFileHandler` (rotates based on time intervals).

**Example:**

```python
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Rotate log file after 10MB, keep 5 backup files
handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("This message will go into the rotating log file.")
```

## 9. Configure Loggers for Different Environments

**The Problem:** You may want different logging configurations for development, testing, and production environments (e.g., more verbose logging in dev, less in prod, different output destinations).

**The Solution:** Manage different logging configurations using environment variables, configuration files, or conditional logic within your logging setup. This allows you to tailor logging behavior without changing application code.

**Example:**

```python
import os
import logging.config

def get_logging_config(env):
    if env == "production":
        return {
            'version': 1,
            'handlers': {'console': {'class': 'logging.StreamHandler', 'level': 'INFO'}},
            'root': {'handlers': ['console'], 'level': 'INFO'}
        }
    else: # Development/Testing
        return {
            'version': 1,
            'handlers': {'console': {'class': 'logging.StreamHandler', 'level': 'DEBUG'}},
            'root': {'handlers': ['console'], 'level': 'DEBUG'}
        }

# In your main application file
# ENV = os.getenv("APP_ENV", "development")
# logging_config = get_logging_config(ENV)
# logging.config.dictConfig(logging_config)
# logger = logging.getLogger(__name__)
# logger.debug("This is a debug message (visible in dev).")
# logger.info("This is an info message (visible in dev and prod).")
```
