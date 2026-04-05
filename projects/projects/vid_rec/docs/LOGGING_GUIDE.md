# Enhanced Logging Guide for Vid_ReC

## 1. Introduction and Purpose

**Why Enhance Logging?**
Effective logging is crucial for debugging, performance monitoring, and understanding application behavior, especially in complex systems like Vid_ReC. The current logging system, based on `structlog` as per `ADR-007_Structured_Logging_with_structlog.md`, provides a solid foundation with structured JSON output to `vidrec.json`. However, there is a partial drift in comprehensive context binding and detailed event logging, which limits the logs' utility as a queryable dataset for tracing job lifecycles and system events.

**Objective**: This guide aims to enhance the logging system by incorporating best practices that maximize the utility of logs for developers, ensuring traceability, detailed insights, and actionable data without unnecessary overhead. As per project requirements, log rotation and retention policies (since logs are overwritten on each run) and security considerations (not applicable to this app) are excluded from this enhancement plan.

## 2. Key Best Practices for Enhanced Logging

Below are the prioritized best practices tailored for Vid_ReC, focusing on maximizing the utility of `vidrec.json`.

### 2.1 Comprehensive Context Binding
- **Why**: Binding context to every log entry (e.g., `file_name`, `worker_id`, `job_id`, `run_id`) ensures that each message can be traced back to its source, crucial for debugging in a multi-process environment.
- **Where**: Across all modules, especially in `processing_job.py`, `main_processor.py`, and `state_manager.py`, where job-specific operations occur.
- **How**: Use `structlog.contextvars` to bind metadata to logs before emitting messages.
- **Benefit**: Enables precise querying of logs for specific jobs or operations.

### 2.2 Structured and Hierarchical Logging
- **Why**: Organizing logs by category or subsystem (e.g., `ui`, `processing`) makes filtering and analysis easier.
- **Where**: In all log-emitting modules to tag logs with their origin or purpose.
- **How**: Add a `category` field to log entries via `structlog` processors or manual binding.
- **Benefit**: Groups related logs for better analysis and debugging.

### 2.3 Detailed Job Lifecycle Logging
- **Why**: Logging every significant event in a job's lifecycle (start, progress, completion, errors) provides a complete audit trail.
- **Where**: Primarily in `processing_job.py` and `main_processor.py`.
- **How**: Emit log messages at key lifecycle points with detailed metadata.
- **Benefit**: Facilitates tracking job progress and diagnosing failures.

### 2.4 Performance Metrics Logging
- **Why**: Capturing metrics like processing time helps identify bottlenecks.
- **Where**: In performance-critical sections of `main_processor.py` and `subtitle_generator.py`.
- **How**: Use timing decorators or manual logging to record execution durations.
- **Benefit**: Supports optimization efforts by highlighting slow operations.

### 2.5 Error and Exception Logging with Stack Traces
- **Why**: Detailed error logs with stack traces speed up root cause analysis.
- **Where**: Wherever exceptions are caught or errors are handled across the codebase.
- **How**: Leverage `structlog.processors.format_exc_info` and `structlog.processors.dict_tracebacks` for comprehensive error data.
- **Benefit**: Reduces debugging time by providing full context of errors.

### 2.6 Log Levels and Granularity
- **Why**: Appropriate log levels prevent clutter and ensure important information stands out.
- **Where**: Across all modules, adjusting levels based on event significance.
- **How**: Set log levels (DEBUG, INFO, WARNING, ERROR) to match the importance of messages.
- **Benefit**: Keeps logs focused and actionable.

### 2.7 User-Centric Logging for UI Feedback
- **Why**: Logging user interactions aids in understanding user behavior and improving UX.
- **Where**: In `ui_dashboard.py` and related UI components.
- **How**: Use the existing `DashboardLogHandler` to capture UI events with specific tags.
- **Benefit**: Provides insights into user experience issues.

### 2.8 Tooling for Log Analysis
- **Why**: Consistent JSON structure enables integration with analysis tools like `jq` or ELK Stack.
- **Where**: In the configuration of `logger.py` to maintain JSON format in `vidrec.json`.
- **How**: Ensure log structure remains consistent and document the schema for external tools.
- **Benefit**: Allows advanced querying and visualization of log data.

## 3. Implementation Roadmap and Suggested Tasks

Below are actionable tasks to implement these best practices, prioritized by impact and feasibility.

### Task 1: Implement Comprehensive Context Binding
- **Objective**: Ensure all log messages include critical context.
- **Where**: Start with `processing_job.py` and `main_processor.py`.
- **Code Example**:
  ```python
  import structlog
  from structlog.contextvars import bind_contextvars

  log = structlog.get_logger("vidrec.processing")
  # Bind context at the start of a job
  bind_contextvars(file_name="example.mp4", worker_id=1, job_id="job-123")
  log.info("Starting job processing")
  ```
- **Action**: Review and update all log-emitting functions to bind context before logging. Add a utility function in `utils.py` to standardize context binding for jobs.

### Task 2: Add Hierarchical Categories to Logs
- **Objective**: Organize logs by subsystem for better filtering.
- **Where**: Update `logger.py` to include a category processor.
- **Code Example**:
  ```python
  # In logger.py, add to shared_processors
  def add_category(_, __, event_dict):
      event_dict["category"] = event_dict.get("category", "general")
      return event_dict
  shared_processors.append(add_category)
  ```
- **Action**: Modify log calls in modules to specify a category, e.g., `log.info("UI event", category="ui")`.

### Task 3: Log Job Lifecycle Events
- **Objective**: Capture detailed events for each job.
- **Where**: In `processing_job.py`.
- **Code Example**:
  ```python
  log.info("Job started", job_id=job_id, file_name=file_name)
  # During processing
  log.info("Processing subtitle", progress="50%", job_id=job_id)
  log.info("Job completed", duration=elapsed_time, job_id=job_id)
  ```
- **Action**: Add log statements at key points in job processing with relevant metadata.

### Task 4: Include Performance Metrics
- **Objective**: Log execution times for critical operations.
- **Where**: In `subtitle_generator.py`.
- **Code Example**:
  ```python
  import time
  start_time = time.time()
  # Perform operation
  elapsed = time.time() - start_time
  log.info("Subtitle generation completed", duration=elapsed, file_name=file_name)
  ```
- **Action**: Identify performance-critical functions and add timing logs.

### Task 5: Ensure Detailed Error Logging
- **Objective**: Capture full error details.
- **Where**: In exception handling blocks across the codebase.
- **Code Example**:
  ```python
  try:
      # Risky operation
      process_file()
  except Exception as e:
      log.error("Processing failed", error=str(e), exc_info=True, file_name=file_name)
  ```
- **Action**: Audit exception handling to ensure `exc_info=True` is used for detailed stack traces.

### Task 6: Adjust Log Levels for Granularity
- **Objective**: Use appropriate log levels.
- **Where**: Review all log statements.
- **Code Example**:
  ```python
  log.debug("Detailed debug info for developers", variable=value)  # Detailed diagnostics
  log.info("Significant event occurred", event="startup")  # Key events
  log.warning("Non-critical issue detected", issue="missing config")
  ```
- **Action**: Adjust log levels to match event importance, reducing noise in INFO level.

### Task 7: Enhance UI-Centric Logging
- **Objective**: Log user interactions for UX analysis.
- **Where**: In `ui_dashboard.py`.
- **Code Example**:
  ```python
  log.info("User clicked process button", category="ui", action="process_start")
  ```
- **Action**: Add logs for key user interactions using the `DashboardLogHandler`.

### Task 8: Document Log Structure for Analysis Tools
- **Objective**: Support log analysis with consistent structure.
- **Where**: In project documentation or `logger.py` comments.
- **Code Example**:
  ```markdown
  # Log Schema for vidrec.json
  - event: Main message or event description (string)
  - logger: Source logger name (string)
  - level: Log level (string: info, error, etc.)
  - timestamp: ISO timestamp (string)
  - category: Subsystem or module category (string)
  - job_id, file_name, worker_id: Context variables (optional)
  ```
- **Action**: Create a log schema document or comment in `logger.py` for reference.

## 4. Conclusion

By implementing these best practices, the logging system in Vid_ReC will become a powerful tool for debugging, monitoring, and improving the application. The focus on context binding, detailed lifecycle logging, and structured categorization will address the current drift from the ADR and ensure logs are maximally useful without adding unnecessary complexity.

**Next Steps**: Start with Tasks 1 and 3 (context binding and job lifecycle logging) as they have the highest impact on traceability. Once these are in place, proceed to performance metrics and UI logging to further enhance insights.
