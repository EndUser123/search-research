---
title: "Is there such a thing as a best practice unified error framework for python?"
date: "2025-12-23"
mode: "COPILOT"
uuid: "892d1bb6-9aae-44c5-8f23-a8674294ec7d"
entry_count: 5
---

## Human

Is there such a thing as a best practice unified error framework for python?

## Assistant

The short answer is **no**, there is no single, universally adopted "standard library" for error handling in Python that works like Log4j does for logging.

However, in professional, institutional-grade Python development, a "unified error framework" is a standard **architectural pattern** that you are expected to implement. Senior engineers typically build this by combining 2–3 specific tools.

Depending on your philosophy, you should adopt one of the following three approaches.

### 1. The "Enterprise Standard" Architecture (Best Practice)
This is the most common pattern for robust backend services (Django, FastAPI, Flask, or Scripts). It unifies errors by enforcing a strict hierarchy and a single "translation layer" at the edge of your application.

**The Recipe:**
*   **The Base:** Create a `AppError` (or `BaseError`) class that inherits from `Exception`.
*   **The Structure:** All custom exceptions must inherit from this base and define:
    *   `message`: A human-readable description.
    *   `code`: A machine-readable string/enum (e.g., `USER_NOT_FOUND`, `PAYMENT_FAILED`) for frontend logic.
    *   `payload`: A dictionary of extra context (e.g., `{"user_id": 5}`).
*   **The Trap:** A global exception handler (middleware in web apps, or a decorator in scripts) that catches `AppError`, extracts the `code`/`payload`, and formats the final output (JSON response or log entry).

**Recommended Libraries to Build This:**
*   **Web API Standard:** Implement **RFC 7807 (Problem Details)**.
    *   *Library:* **`python-httpproblem`** or framework-specific tools like **`drf-standardized-errors`** (Django) or **`fastapi-problem`**.
*   **Logging:** Use **`structlog`** or **`loguru`**. These are essential because they allow you to bind context (like `request_id`) at the start of a process, so when an error fires deep in the stack, that context is automatically attached to the error log.

### 2. The "Functional" Framework (The `dry-python` approach)
If you prefer a strict framework that forces developers to handle errors (preventing runtime crashes), this is the rising alternative. It mimics Rust/Haskell by treating errors as *values* rather than *exceptions*.

*   **The Framework:** **`dry-python/returns`**
*   **How it works:** Instead of raising exceptions, functions return a `Result` container (`Success(value)` or `Failure(error)`).
*   **Why use it:** It creates a "railway oriented programming" flow where errors are passed down the track safely. It completely unifies error handling because you *cannot* access a value without checking if it's an error first.

### 3. The "Validation-First" Framework
For applications heavy on data processing (ETL, Data Science), error handling often centers on "why is this data bad?" rather than "why did the code crash?"

*   **The Framework:** **`Pydantic`**
*   **How it works:** While known for validation, Pydantic is often used as the unified error framework. You define strict schemas for inputs *and* outputs. If anything deviates, Pydantic raises a standard `ValidationError` with a highly structured JSON detailing exactly where and why it failed.

### Summary Recommendation

| If you are building... | Use this Unified Framework Strategy |
| :--- | :--- |
| **REST APIs (FastAPI/Flask)** | **RFC 7807 Pattern**: Use a global exception handler to catch custom exceptions and convert them to "Problem Details" JSON. |
| **Mission Critical Logic** | **Functional Pattern**: Use `dry-python/returns` to force developers to handle every failure case explicitly. |
| **Data Pipelines / CLI** | **Structured Logging Pattern**: Use `structlog` to bind context + a root `try/except` block that catches `AppError` and pretty-prints the result. |

### Example: The "Enterprise Standard" Implementation
If you just want the "best practice" code snippet to copy-paste, this is the pattern used in high-scale Python systems:

```python
# 1. THE UNIFIED BASE
class AppError(Exception):
    """Base class for all application errors."""
    def __init__(self, message, code="INTERNAL_ERROR", context=None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

# 2. SPECIFIC ERRORS (Inherit from Base)
class ResourceNotFoundError(AppError):
    def __init__(self, resource_id):
        super().__init__(f"Resource {resource_id} not found", code="NOT_FOUND", context={"id": resource_id})

# 3. THE UNIFIED HANDLER (The "Framework" part)
def global_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # Unified Logging
            logger.error(f"Logic Failure: {e.message}", code=e.code, context=e.context)
            # Unified Response
            return {"error": True, "code": e.code, "message": str(e)}
        except Exception as e:
            # Catch-all for unexpected crashes
            logger.exception("System Crash")
            return {"error": True, "code": "SYSTEM_CRASH", "message": "An unexpected error occurred."}
    return wrapper
```

## Human

How is this related to dual sink logging?

## Assistant

**Dual sink logging** is the implementation strategy that makes a unified error framework useful in the real world.

While your **Unified Error Framework** defines *what* happens (creating a standardized `AppError` object with a code, message, and context), **Dual Sink Logging** defines *where* that information goes and *how* it looks when it gets there.

In professional Python environments, "Dual Sink" typically refers to splitting your log stream into two distinct formats:
1.  **The Machine Sink (JSON):** For your log aggregator (Datadog, Splunk, ELK). It needs the raw data structure for querying.
2.  **The Human Sink (Pretty-Print):** For your terminal (stdout) during local development. It needs colors and readability.

### The Relationship: Payload vs. Transport

Think of the **Unified Error Framework** as the package, and **Dual Sink Logging** as the delivery trucks.

*   **The Framework's Job:** To ensure that every error exception contains a consistent "payload" of data (e.g., `error_code`, `user_id`, `request_id`, `traceback`).
*   **The Logging's Job:** To unpack that payload differently depending on the destination.
    *   **Sink A (Machine):** Serializes the entire payload into a single JSON line so you can query `status:500 AND code:PAYMENT_FAIL`.
    *   **Sink B (Human):** Extracts just the `message` and `traceback`, colors them red, and prints them to the console so a human can debug immediately.

### Why They Are Often Confused
They are often confused because libraries like **`structlog`** and **`loguru`** handle *both* tasks simultaneously. They allow you to structure the data (framework) and route it to different outputs (dual sink) in the same configuration block.

### Implementation Pattern

Here is how you connect the `AppError` framework we defined earlier to a Dual Sink system using **`loguru`** (which is generally preferred over `structlog` for this specific "dual sink" ease-of-use).

```python
import sys
from loguru import logger

# 1. DEFINE THE SINKS
# Sink A: Machine-Readable JSON (Standard Output) -> Goes to Datadog/Splunk
logger.add(
    sys.stdout, 
    format="{message}", 
    serialize=True,  # <--- MAGIC: Converts the log record to JSON
    level="INFO",
    filter=lambda record: record["extra"].get("sink") == "machine"
)

# Sink B: Human-Readable Text (Standard Error) -> Goes to Developer Console
logger.add(
    sys.stderr, 
    format="<green>{time}</green> | <level>{level}</level> | <cyan>{message}</cyan>", 
    level="DEBUG",
    serialize=False, # <--- Keeps it pretty text
    filter=lambda record: record["extra"].get("sink") != "machine" # Avoid duplicating JSON logs here
)

# 2. THE UNIFIED FRAMEWORK CONNECTION
# The error handler we built earlier now just feeds the logger
def global_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            # The Framework provides the structured data
            error_context = {
                "error_code": e.code,
                "user_context": e.context,
                "exception_type": type(e).__name__
            }
            
            # The Logger (Dual Sink) handles the routing
            
            # 1. Send deep data to the Machine Sink
            logger.bind(payload=error_context, sink="machine").error("Structured Error Event")
            
            # 2. Send readable alert to the Human Sink
            logger.error(f"Failed: {e.message} (Code: {e.code})")
            
            # Return standardized API response
            return {"error": True, "code": e.code, "message": str(e)}
    return wrapper
```

### Strategic Value
If you only have the **Unified Framework** but print to a simple text log, you lose the ability to filter logs by `error_code`. If you only have **Dual Sink Logging** but no framework, your JSON logs will be messy and inconsistent (some have `user_id`, others have `uid`, others have nothing).

**You need both:** The Framework standardizes the *keys*, and Dual Sink logging standardizes the *format*.

## Human

Anything else I need to know about dual sink logging before I give the above chat history to a llm to implement?

## Assistant

Before you hand this off to an LLM, there are **five "gotchas"** you must explicitly include in your prompt. If you don't, the LLM will likely generate code that looks correct but fails in production (silent failures, missing logs, or data leaks).

### 1. The "Interception" Trap (Critical)
**The Problem:** The code snippet I gave you earlier only handles *your* logs. It does **not** capture logs from libraries you use (like `django`, `flask`, `requests`, `sqlalchemy`). These libraries use the standard `logging` module. If you don't "intercept" them, they will bypass your beautiful JSON sink and print unstructured garbage to `stderr`, breaking your log parser.

**The Fix:** You must tell the LLM to implement an `InterceptHandler`.
*   **Prompt Instruction:** "Ensure the `loguru` configuration includes a custom `InterceptHandler` class that routes standard library `logging` messages into the `loguru` sinks. It should forcibly take over the root logger."

### 2. The JSON Serialization Crash
**The Problem:** Your `AppError` payload might contain objects that standard JSON parsers hate (e.g., `datetime` objects, `UUIDs`, `Decimal` types from DBs, or Pydantic models). If you try to log `context={"user_id": uuid4()}`, the logger will crash your application with a `TypeError`.

**The Fix:** You need a serialization function that converts these types to strings before logging.
*   **Prompt Instruction:** "The JSON sink must use a custom serialization function (or `rotation` serializer) that handles non-JSON-serializable types like `datetime`, `UUID`, and `Pydantic` models gracefully without crashing."

### 3. Sensitive Data Redaction (PII)
**The Problem:** A "Unified Framework" creates a single funnel for all errors. If a developer accidentally logs a user object `context={"user": user_model}`, and that model includes a `password_hash` or `email`, you are now leaking PII into your logs at scale.

**The Fix:** You need a filter/processor that scans for sensitive keys.
*   **Prompt Instruction:** "Implement a 'redaction filter' in the logger that recursively scans the `extra/context` dictionary and masks values for keys like `password`, `token`, `secret`, or `auth` before they reach the sink."

### 4. Async Context Propagation
**The Problem:** If you are using FastAPI or any async framework, simple context binding often fails. If Request A binds `user_id=5`, Request B might accidentally inherit it if you aren't using `contextvars` correctly. `loguru` handles this relatively well, but it's brittle if not explicit.

**The Fix:**
*   **Prompt Instruction:** "Ensure the context binding implementation is safe for `asyncio` and `contextvars`, so that concurrent requests do not leak context to each other."

### 5. Environment Switching (Not just Filtering)
**The Problem:** The previous example *filtered* logs (sending some to JSON, some to text). In reality, you never want "Human Readable" text logs in Production (it wastes CPU/Disk), and you rarely want "JSON" logs in Local Dev (hard to read).

**The Fix:**
*   **Prompt Instruction:** "Use an environment variable (e.g., `LOG_FORMAT=JSON` vs `LOG_FORMAT=HUMAN`) to completely disable the unused sink, rather than just filtering messages. We don't want to pay the serialization cost for a sink we aren't using."

### Suggested "System Prompt" Addition
When you prompt the LLM, add this block to ensure it covers these bases:

> **"Implementation Constraints:**
> 1.  **Interception:** Must route standard library `logging` (requests, sqlalchemy) through this system.
> 2.  **Safety:** Must include a serializer that handles `UUID`/`datetime` and a PII masker for keys like 'password'.
> 3.  **Performance:** Configure sinks conditionally based on an environment variable (`ENV=LOCAL` vs `PROD`) so we don't double-log in production.
> 4.  **Async:** Ensure `contextvars` compatibility for FastAPI request ID tracking."

## Human

Any nuances regarding asyncio?

## Assistant

Yes, `asyncio` introduces a subtle but critical "gotcha" involving **Task Groups** (used in `anyio`, Starlette, and newer Python versions) and **Context Variable Propagation**.

The standard `contextvars` module propagates context *downwards* into tasks correctly. However, a specific edge case occurs with **Task Inheritance** when using libraries like **`loguru`** or **`structlog`**.

### The "Task Context Copy" Nuance

When you spawn a new task in asyncio (e.g., `asyncio.create_task(my_func())`), Python automatically copies the current `contextvars` context into the new task. This works perfectly 95% of the time.

**The Problem:**
If you set a context variable (like `request_id`) **inside** a middleware or a function *after* the task has started, that change does **not** propagate "up" to the parent, nor does it propagate "sideways" to other tasks that were already spawned.

More importantly, if you use a library that abstracts task creation (like `anyio.create_task_group()` or certain `background_tasks` in FastAPI), the context binding might behave unexpectedly depending on *when* the binding happens relative to the task creation.

### Implementation Nuance: The "Reset Token" Pattern

For `loguru` specifically, `logger.contextualize()` is context-manager based and safe. But if you try to manually bind context globally in an async middleware without using the context manager, you might leak memory or context.

**What you must tell the LLM:**

1.  **Prefer `contextualize()` over `bind()` for scopes:**
    When entering a request middleware, use `with logger.contextualize(request_id=...)` rather than `logger = logger.bind(...)`. The context manager ensures the context is cleaned up when the request exits, preventing "context pollution" where Request B inherits Request A's data because they shared an event loop thread.

2.  **Explicit Context Copying for Background Tasks:**
    If you fire a "fire-and-forget" background task (e.g., sending an email after a response) using `asyncio.create_task`, tell the LLM to verify that the logging context is explicitly copied if using older Python versions or specific frameworks.
    *   *Note:* Python 3.7+ does this automatically for `asyncio.create_task`.
    *   *However:* If you use `threading` inside an async application (e.g., for CPU-bound work), the context is **LOST**. You must manually copy it.

### Specific Prompt Addition for Asyncio

Add this to your prompt to cover the "threaded worker" edge case (common in real-world async apps):

> "**Async/Thread Safety:**
> - Ensure the configuration handles `contextvars` correctly for `asyncio` tasks.
> - **Critical:** If the implementation includes any offloading to threads (e.g., `run_in_executor`), include a helper function or decorator that manually copies the `contextvars` context into the thread, otherwise logs inside the thread will lose the `trace_id`."

**Example of the helper the LLM should generate:**
```python
import contextvars
import functools
import asyncio

def to_thread(func):
    """Decorator that runs a sync function in a thread with context copied."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = contextvars.copy_context()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, ctx.run, functools.partial(func, *args, **kwargs))
    return wrapper
```

## Human

Anything else I should regarding any of the above before we implement?

## Assistant

Yes. There are **three final critical items** that will determine whether your implementation is "production-grade" or "breaks at scale."

## 1. Log Rotation & Disk Space (The Silent Killer)

**The Problem:** If you're writing JSON logs to a file sink (common in production), without proper rotation, your disk will fill up silently. The logger won't crash—it will just stop writing. Meanwhile, your application keeps running, and you have **zero visibility** into what's happening.

**The Issue:**
- Text logs are human-readable but *incompressible*. A 1GB text log is still 1GB.
- JSON logs are denser but still uncompressed. A 1GB JSON log is still 1GB.
- If you have 10 concurrent workers each logging 50MB/hour, you need 500MB/hour of disk. On a 10GB partition, you're full in 20 hours.

**What to Tell the LLM:**
> "Configure log rotation on **both sinks** (not just one). Use `loguru`'s `rotation` parameter (e.g., `rotation="500 MB"` or `rotation="00:00"` for daily rotation). If writing to a file, include `retention` (e.g., `retention="7 days"`) to auto-delete old logs. **Critical:** Verify that rotation doesn't cause a race condition in async code—if one coroutine is writing while another is rotating, you need proper file locking."

**Red Flag:** If the LLM generates code with file sinks but no `rotation` parameter, send it back.

***

## 2. The "Correlation ID" (Request Tracing) Blueprint

**The Problem:** You've built a beautiful dual-sink system, but if you can't link logs together across service boundaries, it's useless at scale. When a request flows through Middleware → Service A → Service B → Database, each component logs independently. Without a correlation ID (also called `request_id` or `trace_id`), you can't reconstruct the request journey.

**The Architecture:**
- A correlation ID is generated once (in your API gateway or middleware) and propagated through the request lifecycle.
- It must survive across:
  - Synchronous function calls (easy)
  - Async task spawning (requires contextvars, which we covered)
  - HTTP calls to downstream services (must be passed in headers)
  - Database calls (must be logged alongside queries)

**What to Tell the LLM:**
> "Generate a `request_id` in the middleware (e.g., `uuid.uuid4()`) and bind it to the logger context using `logger.contextualize(request_id=request_id)`. When making downstream HTTP calls (e.g., with `httpx` or `aiohttp`), ensure the middleware automatically injects the `request_id` into the `X-Request-ID` header. For database operations, if using SQLAlchemy, include a hook that logs query start/end with the `request_id` automatically."

**Example Pattern the LLM should generate:**
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    with logger.contextualize(request_id=request_id):
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Red Flag:** If the code doesn't generate a correlation ID or doesn't propagate it to downstream calls, it's incomplete.

***

## 3. Performance Impact & Sampling Strategy

**The Problem:** Dual sink logging with JSON serialization is **CPU-bound**. If you're logging every database query, every HTTP call, and every error, you can reduce your throughput by 10–30% depending on log volume. In high-frequency systems (>1000 RPS), this is unacceptable.

**The Real Issue:**
- JSON serialization is slower than text printing.
- If you're binding large objects to context (e.g., full `request.body`, full `response.json()`), each serialization is expensive.
- At 1000 RPS with 5 logs per request, you're doing 5000 serializations/second. Python's `json.dumps()` can't keep up without careful optimization.

**The Solution: Sampling**
Production systems typically use **log sampling** for high-volume events:
- Log 100% of **errors and warnings**.
- Log 1% of **debug and info** (or sample based on slow requests).

**What to Tell the LLM:**
> "Implement a sampling filter in the logger that allows different sample rates for different levels. For example: log 100% of `ERROR`, `CRITICAL`, and `WARNING` messages, but only 5% of `INFO` and `DEBUG`. Additionally, provide a 'slow request' override: if a request takes >1 second, force log all statements for that request even if normally sampled. Use a `sample_rate` variable in the context to pass this down the call stack."

**Example the LLM should generate:**
```python
import random

def sampling_filter(record):
    """Log 100% of errors, 5% of info."""
    if record["level"].no >= 30:  # WARNING and above
        return True
    sample_rate = record["extra"].get("sample_rate", 0.05)
    return random.random() < sample_rate

logger.add(json_sink, filter=sampling_filter, level="INFO")
```

**Red Flag:** If the code logs everything at 1000 RPS without sampling, production will either be slow or the logs will be useless (too many entries to search).

***

## Summary: The Three Items to Verify Before Implementation

| Item | Check | Red Flag |
|------|-------|----------|
| **Log Rotation** | Is `rotation` and `retention` configured on file sinks? | No `rotation` parameter, or it's only on one sink |
| **Correlation ID** | Is a `request_id` generated, bound to context, and propagated to downstream calls? | No correlation ID or no header injection |
| **Sampling** | Is there a sampling strategy for high-volume logs? | Logs 100% of INFO/DEBUG at scale (will be slow) |

**Final Prompt Addition:**

> "**Production Requirements:**
> 1. Configure log rotation with `rotation='500 MB'` and `retention='7 days'` to prevent disk overflow.
> 2. Implement a correlation ID (`request_id`) that's generated in middleware, bound to logger context, and propagated via HTTP headers to downstream services.
> 3. Implement log sampling: 100% for ERROR+ levels, 5% for INFO/DEBUG, with a fast-path override if a request exceeds 1 second (force 100% logging for that request).
> 4. Provide clear documentation showing how to query correlated logs in a log aggregator (e.g., `request_id:abc123`)."

If the LLM doesn't address all three, it's missing critical production hardening.
