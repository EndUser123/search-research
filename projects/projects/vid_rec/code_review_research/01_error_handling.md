# AI Coder's Guide to Robust Error Handling

This guide provides best practices for handling errors in Python, specifically tailored for an AI coder. By following these guidelines, you can write more robust, reliable, and maintainable code.

## 1. Be Specific When Catching Exceptions

**The Problem:** Using a bare `except:` clause catches all exceptions, including system-exiting ones like `SystemExit` and `KeyboardInterrupt`. This can hide bugs and make it difficult to debug problems.

**The Solution:** Always catch specific exceptions that you can handle meaningfully. This allows you to handle different errors differently and prevents you from unintentionally hiding bugs.

**Example:**

```python
# Bad Practice: Catches too broadly
try:
    value = int("abc")
except:
    print("An error occurred.")

# Good Practice: Catches specific error
try:
    value = int("abc")
except ValueError as e:
    print(f"Invalid input: {e}")

# Good Practice: Catches multiple specific errors
def divide(a, b):
    try:
        return a / b
    except (ZeroDivisionError, TypeError) as e:
        print(f"Cannot perform division: {e}")
        return None
```

## 2. Keep `try` Blocks Small

**The Problem:** Large `try` blocks make it difficult to identify the source of an error and handle it appropriately.

**The Solution:** Your `try` blocks should only contain the specific lines of code that might raise an exception. This makes it easier to pinpoint the source of an error and handle it in a targeted way.

**Example:**

```python
# Bad Practice: Too much code in one try block
try:
    data = read_file("data.txt")
    processed_data = process(data)
    save_to_database(processed_data)
except Exception as e:
    print(f"An error occurred during file operations or processing: {e}")

# Good Practice: Granular try blocks
try:
    data = read_file("data.txt")
except FileNotFoundError as e:
    print(f"Error reading file: {e}")
    data = None

if data:
    try:
        processed_data = process(data)
    except ProcessingError as e: # Assuming ProcessingError is a custom exception
        print(f"Error processing data: {e}")
        processed_data = None

if processed_data:
    try:
        save_to_database(processed_data)
    except DatabaseError as e: # Assuming DatabaseError is a custom exception
        print(f"Error saving to database: {e}")
```

## 3. Use the `finally` Block for Cleanup

**The Problem:** Resources like files, network connections, or database connections need to be closed or released, even if an error occurs during their use.

**The Solution:** The `finally` block is always executed, regardless of whether an exception was raised. This makes it the perfect place for cleanup code, ensuring resources are properly managed.

**Example:**

```python
f = None
try:
    f = open("my_file.txt", "r")
    content = f.read()
    print(content)
except FileNotFoundError:
    print("File not found.")
finally:
    if f:
        print("Closing the file.")
        f.close()

# Even better: Use 'with' statement for automatic resource management
try:
    with open("another_file.txt", "r") as f:
        content = f.read()
        print(content)
except FileNotFoundError:
    print("Another file not found.")
# No finally block needed here, 'with' handles closing automatically
```

## 4. Create Custom Exceptions and Hierarchies

**The Problem:** Application-specific errors may not be well-represented by built-in exceptions, leading to generic error messages and less clear error handling logic. A flat structure of custom exceptions can also become unmanageable.

**The Solution:** Create your own custom exception classes to make your error handling more semantic and improve code readability. For complex applications, organize these custom exceptions into a hierarchy to allow for more granular or broader catching.

**Example:**

```python
# Base custom exception for the application
class MyAppError(Exception):
    """Base exception for Vid_ReC application errors."""
    pass

# Specific exceptions inheriting from the base
class ConfigurationError(MyAppError):
    """Raised when there's an issue with application configuration."""
    pass

class ProcessingError(MyAppError):
    """Raised when a video processing step fails."""
    pass

class SubtitleGenerationError(ProcessingError):
    """Raised when subtitle generation encounters an issue."""
    pass

def load_settings(config_path):
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")
    # ... load logic

def generate_subtitles(video_file):
    if not video_file.exists():
        raise SubtitleGenerationError(f"Video file not found: {video_file}")
    # ... subtitle generation logic

# How to catch them
try:
    load_settings("non_existent.toml")
except ConfigurationError as e:
    print(f"Caught a configuration specific error: {e}")
except MyAppError as e:
    print(f"Caught a general application error: {e}")
```

## 5. Preserve the Original Traceback

**The Problem:** When you catch an exception and raise a new one (e.g., to provide a more user-friendly message or to transform the error type), you can inadvertently lose the original stack trace. This makes debugging significantly harder as the context of the initial error is lost.

**The Solution:** Use `raise NewException from OriginalException` to chain the exceptions. This preserves the original stack trace, providing a complete history of how the error propagated.

**Example:**

```python
def fetch_data_from_api(url):
    try:
        # Simulate a network error
        raise ConnectionError("Failed to connect to API endpoint.")
    except ConnectionError as e:
        # Re-raise with more context, preserving the original traceback
        raise ValueError(f"Could not retrieve data from {url}") from e

def process_report():
    try:
        fetch_data_from_api("http://example.com/api/data")
    except ValueError as e:
        print(f"Report generation failed: {e}")
        # The 'from ConnectionError' part is preserved and visible in the traceback
        import traceback
        traceback.print_exc()
```

## 6. Implement Proper Logging

**The Problem:** Simply printing error messages to the console is not sufficient for production applications. It lacks context, severity levels, and persistence, making debugging and monitoring challenging.

**The Solution:** Use Python's robust `logging` module to record exceptions and other events. This allows you to capture detailed information, including stack traces, timestamps, and context, for later analysis and debugging.

**Example:**

```python
import logging

# Configure basic logging (in a real app, use a more sophisticated setup)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_ratio(numerator, denominator):
    try:
        result = numerator / denominator
        return result
    except ZeroDivisionError as e:
        # Log the exception with exc_info=True to include traceback
        logging.error("Attempted to divide by zero.", exc_info=True)
        return None
    except TypeError as e:
        logging.error("Invalid types for calculation.", exc_info=True)
        return None

calculate_ratio(10, 0)
calculate_ratio(10, "a")
```

**Why this is better:**
*   **Context:** Log messages can include variables, timestamps, and logger names.
*   **Severity Levels:** You can categorize messages (DEBUG, INFO, WARNING, ERROR, CRITICAL) and filter them.
*   **Persistence:** Logs can be written to files, sent to remote servers, or integrated with monitoring systems.
*   **Tracebacks:** `exc_info=True` automatically adds the full traceback to the log entry, which is crucial for debugging.
