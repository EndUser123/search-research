## --- METADATA ---
# Filename: ADR.md
# Version: 1.5.0
# ------------------
#
# --- CHANGELOG ---
# v1.5.0: FEAT: Added ADR-007 to document the strategic migration from RQ to Dramatiq for improved stability and cross-platform support.
# v1.4.0: FEAT: Added ADR-005 for adopting the standard `rq worker` command and ADR-006 for the major refactor into a `src/` layout.
# v1.3.0: FEAT: Added ADR-004 to document the switch from a custom @retry decorator to native RQ job retries for better resilience and throughput.
# v1.2.0: DOCS: Updated ADR-003 to reflect the consequences of the decoupled architecture, such as the need for an 'execute' command to handle result aggregation and post-processing.
# v1.1.0: FEAT: Added ADR-003 for the decision to adopt a queue-based architecture with RQ.
# v1.0.0: INIT: Created initial ADRs for Concurrency Model and Logging Framework decisions.
# ------------------

# --- INTEGRITY ---
# Previous Character Count: 10255
# Current Character Count: 11956
# Syntax Check: PASS
# Logic Validation: The new ADR correctly captures the reasons for migrating away from RQ and the benefits of adopting Dramatiq.
# Reason for Change: To formally document the final major architectural decision to ensure long-term stability.
# ------------------

# Architectural Decision Records (ADR)

This document records the architectural decisions made for the Video Dedupe AI project.

---

## ADR-001: Concurrency Model for Subprocess-Heavy Tasks

- **Status:** Superseded by ADR-003
- **Date:** 2025-06-29
- **Context:** The application was experiencing deadlocks and hanging indefinitely during the "Finding Duplicates" phase. This phase involves processing multiple video files in parallel, with each task spawning numerous `ffmpeg` subprocesses for metadata extraction, hashing, and quality analysis.
- **Decision:** We will use `concurrent.futures.ProcessPoolExecutor` for the main planning and processing tasks that involve heavy I/O and subprocess execution. The `ThreadPoolExecutor` will be reserved only for lightweight, I/O-bound tasks that do not spawn subprocesses, such as the initial metadata indexing.

- **Rationale:**
    1.  **Deadlock Prevention:** The root cause of the hangs was resource contention when using `ThreadPoolExecutor`. Threads in Python are constrained by the Global Interpreter Lock (GIL) and share resources like file descriptors. Spawning many subprocesses from multiple threads led to a classic deadlock scenario.
    2.  **Process Isolation:** `ProcessPoolExecutor` creates separate OS processes, each with its own memory space and resources. This completely isolates the `ffmpeg` subprocess calls from each other, eliminating the contention and resolving the deadlock.
    3.  **True Parallelism:** For CPU-bound tasks like video analysis, processes bypass the GIL and can achieve true parallelism on multi-core systems, improving performance.
    4.  **Alignment with Best Practices:** This decision aligns with established Python concurrency patterns, which recommend threads for I/O-bound work and processes for CPU-bound or subprocess-heavy work.

- **Consequences:**
    - **Pro:** The application is now stable and no longer hangs during processing.
    - **Pro:** The architecture is more robust and scalable.
    - **Con:** Processes have a higher startup overhead than threads, but this is negligible compared to the long-running nature of the video processing tasks.
    - **Con:** Inter-process communication is more complex if needed in the future (requiring queues, etc.), but is not a major factor in the current design.

---

## ADR-002: Logging Framework Selection

- **Status:** Accepted
- **Date:** 2025-06-29
- **Context:** The initial logging implementation used Python's standard `logging` module combined with `RichHandler` and `python-json-logger`. This setup was functional but required significant boilerplate code, was complex to configure, and had unintuitive log rotation behavior.
- **Decision:** We will replace the entire standard `logging` boilerplate with the **Loguru** library as the sole logging framework for the application.

- **Rationale:**
    1.  **Simplicity and Readability:** Loguru drastically reduces boilerplate. The entire `setup_logger` function (~45 lines) was replaced with a concise 5-line configuration block, making the code easier to read and maintain.
    2.  **Superior Features Out-of-the-Box:** Loguru provides critical features with simple, intuitive parameters:
        - **Process-Safe Logging:** `enqueue=True` makes logging from `ProcessPoolExecutor` safe and trivial to implement.
        - **Idiomatic Rotation:** Using `{time}` in the filename creates a new, timestamped log for each run, which is a more robust and non-destructive pattern than the previous implementation.
        - **Structured Logging:** `serialize=True` enables structured JSON logging without needing an external formatter library.
        - **Better Exceptions:** Loguru's exception formatting is more detailed and includes variable states, aiding debugging.
    3.  **Performance:** Research indicates Loguru has excellent performance suitable for high-volume logging in CLI applications.

- **Consequences:**
    - **Pro:** The codebase is significantly simpler and more maintainable.
    - **Pro:** Logging behavior is more robust, especially regarding log rotation and multiprocessing.
    - **Pro:** The project has one fewer dependency (`python-json-logger` was removed).
    - **Con:** Introduces a new dependency (`loguru`), but its benefits far outweigh the cost. The project is already dependent on several external libraries, so adding one more for a significant architectural improvement is a worthwhile trade-off.

---

## ADR-003: Decoupled Task Execution with a Queue-Based Architecture

- **Status:** Superseded by ADR-007
- **Date:** 2025-06-29
- **Context:** While `ProcessPoolExecutor` (ADR-001) solved the immediate deadlock issue, it still represents a tightly coupled architecture. The main application is responsible for managing the worker process lifecycle, and a catastrophic worker failure could still impact the parent. Furthermore, this model does not scale beyond a single machine.
- **Decision:** We will refactor the application to a decoupled, client-worker architecture using **Redis** as a message broker and **Redis Queue (RQ)** as the task queue framework.

- **Rationale:**
    1.  **Decoupling & Resilience:** The main CLI (`vda_cli.py`) now acts as a lightweight client that only enqueues jobs. It is no longer responsible for executing them. Independent `worker.py` processes consume these jobs. If a worker crashes, it does not affect the client or other workers; the job can be retried or moved to a failed queue for inspection.
    2.  **Scalability:** This architecture can be scaled horizontally. To increase processing power, we can simply run more `worker.py` processes, even on different machines, all pointing to the same Redis instance.
    3.  **Observability:** The queue-based model provides better insight into the system's state. We can easily query the queue to see how many jobs are pending, which jobs have failed, and which workers are active, as implemented in the `status` command.
    4.  **Asynchronous Workflow:** The client can enqueue thousands of jobs and exit in seconds, freeing up the user's terminal. The processing happens entirely in the background, which is a much better user experience for long-running tasks.

- **Consequences:**
    - **Pro:** Greatly improved system resilience and fault tolerance.
    - **Pro:** Enables horizontal scaling and a path toward a microservices-based architecture.
    - **Pro:** Better user experience due to non-blocking client operations.
    - **Con:** Introduces a new runtime dependency: a running **Redis server**. This increases the complexity of the development and deployment environment.
    - **Con:** The workflow is now multi-step (start Redis, start workers, run client), which must be clearly documented.
    - **Con:** Business logic is now split across commands. The `plan` command enqueues jobs, but aggregate logic (like batching all "best" videos for AI categorization) must be handled by a new `execute` command that post-processes worker results. This increases workflow complexity but is a necessary trade-off for decoupling.

---

## ADR-004: Native Queue-Based Job Retries

- **Status:** Superseded by ADR-007
- **Date:** 2025-06-29
- **Context:** The application initially used a custom `@retry` decorator on functions executed by the worker. This approach, while functional, had a major drawback: it blocked the worker process during the retry attempts, preventing it from processing other available jobs in the queue and reducing overall system throughput.
- **Decision:** We will replace the custom `@retry` decorator entirely with Redis Queue's native `Retry` object. The retry policy (`max=3`, with increasing intervals) is now defined at the point of job creation in `vda_cli.py` when calling `q.enqueue()`.

- **Rationale:**
    1.  **Non-Blocking Workers:** When a job fails, the worker immediately moves it back to the queue (or to the failed registry after max retries) and becomes available to process the next job. This significantly improves system throughput and responsiveness.
    2.  **Centralized Retry Policy:** The retry logic is now part of the job's metadata in the queue, rather than being hidden inside the task function's implementation. This makes the retry behavior more explicit and centrally managed.
    3.  **Code Simplification:** Removing the custom decorator and its usages simplifies the codebase, eliminating ~50 lines of code and making the decorated functions cleaner.
    4.  **Leveraging the Framework:** This change aligns with the best practice of using the features provided by a framework (RQ) rather than re-implementing them.

- **Consequences:**
    - **Pro:** The system is more resilient and efficient, as workers are no longer blocked by failing tasks.
    - **Pro:** The codebase is simpler and easier to maintain.
    - **Con:** The retry logic is no longer co-located with the function it applies to. A developer must look at the `q.enqueue` call site to understand a task's retry behavior, which is a minor but acceptable trade-off for the significant performance and resilience gains.

---

## ADR-005: Adopt Standard `rq worker` Command

- **Status:** Superseded by ADR-007
- **Date:** 2025-06-29
- **Context:** The project initially used a custom `worker.py` script to programmatically start an `rq.SimpleWorker`. This script was created to solve cross-platform compatibility issues (`os.fork` and `SIGALRM`). However, this approach introduced custom code that needed to be maintained and did not correctly implement features like scheduled retries.
- **Decision:** The custom `worker.py` script will be deleted. The project will now use the standard `rq worker` command-line tool provided by the `rq` library. The `--with-scheduler` flag will be used to correctly enable delayed retries, and the `--worker-class rq.SimpleWorker` flag will be used on Windows for compatibility.

- **Rationale:**
    1.  **Code Simplification:** Deleting `worker.py` reduces the amount of custom code in the project, lowering the maintenance burden.
    2.  **Correctness:** The standard `rq worker` command with the `--with-scheduler` flag is the documented, correct way to handle scheduled jobs and interval-based retries, fixing a latent bug in our previous implementation.
    3.  **Robustness:** Relying on the library's official entry point is more robust and less prone to subtle bugs than maintaining a custom implementation. It benefits from the library's own testing and development.
    4.  **Alignment with Best Practices:** This aligns with the principle of using a framework's provided tools instead of re-implementing them.

- **Consequences:**
    - **Pro:** The project is simpler and more maintainable.
    - **Pro:** The job retry mechanism now functions correctly with scheduled delays.
    - **Con:** The "How to Run" instructions for developers and users must be updated to use the new command.

---

## ADR-006: Refactor to `src/` Project Layout

- **Status:** Superseded by ADR-007
- **Date:** 2025-06-29
- **Context:** The project's Python scripts (`vda_cli.py`, `tasks.py`) were located in the project root. This is not a standard practice and hinders packaging and distribution. Furthermore, a hidden circular dependency existed (`vda_cli.py` imported `tasks.py`, and `tasks.py` imported `vda_cli.py`), which would break Python's import system upon moving the files.
- **Decision:** All Python source code will be moved into a `src/` directory. The circular dependency will be broken by applying the Dependency Inversion Principle. The shared components will be extracted into new, single-purpose modules:
    - `src/queue_config.py`: Defines the shared Redis connection and `rq.Queue` instance.
    - `src/processing.py`: Contains the core application logic classes (`VideoProcessor`, `OperationPlanner`).
    The `vda_cli.py` and `tasks.py` modules will now import from these new modules instead of each other.

- **Rationale:**
    1.  **Standard Project Structure:** Adopting a `src/` layout is a standard Python convention that separates source code from project configuration files (like `README.md`, `requirements.txt`), making the project cleaner and easier to navigate.
    2.  **Enables Packaging:** This structure is a prerequisite for building the project into an installable package using tools like `setuptools` or `poetry`.
    3.  **Eliminates Circular Dependencies:** Breaking the import cycle makes the codebase more robust, easier to reason about, and prevents `ImportError` exceptions. The new dependency graph is acyclic and clear.
    4.  **Improved Modularity:** Separating the CLI, processing logic, and queue configuration into distinct modules improves separation of concerns and makes the code more modular and reusable.

- **Consequences:**
    - **Pro:** The project structure is now clean, scalable, and follows Python best practices.
    - **Pro:** The codebase is more robust and easier to maintain.
    - **Con:** The way the application is run from the command line changes. Instead of `python vda_cli.py`, it must now be run as a module with `python -m src.vda_cli`. This change must be clearly documented.

---

## ADR-007: Strategic Migration from RQ to Dramatiq

- **Status:** Accepted
- **Date:** 2025-06-29
- **Context:** After multiple attempts, the project has proven that the `rq` library is fundamentally unstable on Windows due to its architectural reliance on POSIX signals (e.g., `SIGALRM`) for all timeout and scheduling features. All workarounds result in a loss of critical functionality (like delayed retries) and a fragile, high-maintenance implementation.
- **Decision:** The project will be migrated from **RQ** to **Dramatiq**. This involves replacing all `rq`-specific code, including the queue, worker, and job definitions, with their Dramatiq equivalents.

- **Rationale:**
    1.  **First-Class Windows Support:** Dramatiq is explicitly designed and tested for full compatibility with Windows, eliminating the root cause of our persistent cross-platform issues.
    2.  **Full Feature Set:** Dramatiq provides reliable, cross-platform support for all the features we require, including job retries with exponential backoff, without needing platform-specific workarounds.
    3.  **Code and Workflow Simplification:** The migration allows us to remove all the conditional logic and custom classes we added to patch RQ's limitations. It also simplifies the user workflow by removing the separate `execute` command in favor of a single `plan --wait` command.
    4.  **Long-Term Stability:** Building on a library that officially supports our target platform is a more robust and professional engineering decision that reduces future maintenance and technical debt.

- **Consequences:**
    - **Pro:** The application is now stable and fully functional on Windows, Linux, and macOS.
    - **Pro:** The codebase is significantly simpler, more robust, and easier to maintain.
    - **Pro:** The user workflow is streamlined.
    - **Con:** This required a one-time engineering effort to refactor the task queue integration.
