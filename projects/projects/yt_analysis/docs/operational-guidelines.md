# Operational Guidelines

This document consolidates key operational aspects of the YTAP project, including logging, security, testing, and coding standards.

## Development Environment & Shell Configuration

-   **Terminal Environment:** All terminal commands generated for this project **MUST** be compatible with **PowerShell**.
-   **Syntax Requirement:** Ensure all commands use PowerShell syntax. For example:
    -   To set environment variables, use `$env:VAR_NAME="value"` or `Set-Variable -Name "VAR_NAME" -Value "value"`. Do not use `export VAR_NAME=value`.
    -   Use PowerShell-specific cmdlets where appropriate (e.g., `Get-ChildItem` instead of `ls`, `Copy-Item` instead of `cp`).
-   This is a mandatory project standard.

## Logging Strategy (Backend - Python)

* **Library:** The backend (Python/FastAPI) **shall** use Python's built-in `logging` module.
* **Format:**
    * Logs **should** be structured, preferably in JSON format, for easier parsing and potential future integration with log management systems, even if only outputting to console/file in MVP. Each log entry **must** include at least:
        * Timestamp (ISO 8601 format).
        * Log level (e.g., INFO, ERROR).
        * Logger name (e.g., module path).
        * Log message.
    * A plain text format with similar information is acceptable as a fallback for local console readability if JSON proves cumbersome for direct viewing in MVP.
* **Log Levels:** Standard Python log levels will be used:
    * `DEBUG`: Detailed information, typically of interest only when diagnosing problems.
    * `INFO`: Confirmation that things are working as expected (e.g., service startup, major operations initiated/completed).
    * `WARNING`: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., 'disk space low'). The software is still working as expected. (Used for API quota warnings, recoverable errors during ingestion).
    * `ERROR`: Due to a more serious problem, the software has not been able to perform some function (e.g., failed ASR, unhandled exception in an API call).
    * `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running.
* **Output:**
    * For MVP local execution, logs **shall** primarily be written to `stdout` (console).
    * Consider providing a configuration option (e.g., via `.env` or a settings file) to also write logs to a rotating file (e.g., `ytap.log`) in the application's data directory.
* **Contextual Information:** Where relevant, log messages should include contextual information such as Video ID, Channel ID, or specific parameters related to an operation, ensuring no sensitive data (like API keys) is logged.
* **Frontend Logging:** Frontend logging will primarily be to the browser's developer console for debugging purposes. No centralized logging from the frontend is planned for MVP.

## Security Architecture (Backend/Overall Focus)

This section complements the "Frontend Security Considerations" in the YTAP Frontend Architecture Document. It focuses on backend and overall application security for the local MVP.

* **Input Validation & Sanitization (Backend):**
    * All data received by the backend API from the frontend or other sources **MUST** be strictly validated against expected schemas and constraints. If FastAPI is used, Pydantic models will serve this purpose for request bodies and query parameters.
    * Paths for file system operations (e.g., storing transcripts) **MUST** be validated and sanitized to prevent directory traversal attacks or writing to unintended locations. Operations should be restricted to designated base directories.
* **Secrets Management:**
    * As stated in "Infrastructure and Deployment Overview > Certificates and Secrets Management" (see `docs/infra-deployment.md`), sensitive secrets like the YouTube Data API v3 key **MUST** be managed via environment variables (loaded from `.env` files by the backend) and **MUST NOT** be hardcoded or committed to version control.
* **API Security (Internal Backend API):**
    * The internal API between the frontend and backend is intended for local communication (`http://localhost:...`) for the MVP and does not implement authentication/authorization. Access is controlled by the user's access to their local machine.
    * If the application were to be self-hosted and exposed to a network, robust authentication (e.g., API keys, JWT) and HTTPS **MUST** be implemented for this API, likely via a reverse proxy.
* **External API Interactions (Backend to YouTube, etc.):**
    * All calls made by the backend to external services (e.g., YouTube Data API) **MUST** use HTTPS.
* **Dependency Security (Backend):**
    * Python dependencies **MUST** be regularly scanned for known vulnerabilities (e.g., using `pip-audit` or integrating Snyk/Dependabot alerts with the repository). High/critical vulnerabilities **MUST** be addressed.
* **File System Operations:**
    * Transcript files should be stored in a designated data directory. Ensure this directory does not have execute permissions if not needed.
    * Be cautious with filenames derived from external sources; sanitize them before use.
* **Error Handling:**
    * Detailed error messages or stack traces **MUST NOT** be exposed directly to the frontend API responses if they contain sensitive internal information. Generic error messages with logged details server-side are preferred.
* **Principle of Least Privilege:**
    * While less critical for a local single-user app, if the application were deployed in a shared environment, any processes or service accounts it uses would need to operate with the minimum necessary permissions.

## Testing Strategy Notes

* The overall testing tools are defined in `docs/tech-stack.md` (e.g., Pytest for backend, Jest with React Testing Library for frontend, Playwright for E2E).
* A detailed Frontend Testing Strategy is available in the YTAP Frontend Architecture Document (see `docs/front-end-testing-strategy.md` once sharded).
* An explicit, consolidated "Overall Testing Strategy" section detailing backend unit/integration test approaches, mocking strategies for backend, and combined test coverage targets was not drafted as part of YTAP Architecture Document v0.1.1. These aspects will be implicitly covered by adherence to standard testing practices for FastAPI/Python and the testing tool choices. Test generation and practices will be part of individual story development.

## Coding Standards Notes

* Explicit, detailed coding standards (e.g., specific naming conventions beyond framework norms, file structure rules beyond the project layout, detailed language feature usage policies) were not itemized as a standalone section in YTAP Architecture Document v0.1.1.
* Code quality and consistency will be primarily enforced through:
    * The selected linting and formatting tools (Ruff for Python backend; ESLint and Prettier for TypeScript/JavaScript frontend) as defined in `docs/tech-stack.md`. Configuration for these tools will define the enforceable style.
    * Adherence to the "Project Structure" defined in `docs/project-structure.md`.
    * Following standard best practices and idiomatic conventions for the chosen languages and frameworks (Python/FastAPI, TypeScript/React).
    * The "Template for Component Specification" in the Frontend Architecture Document provides detailed structure for frontend components.

## Error Handling Strategy Notes

* A dedicated, comprehensive "Error Handling Strategy" section covering all aspects (e.g., custom error type hierarchies, specific patterns for business logic errors, transaction management for errors) was not drafted as a standalone section in YTAP Architecture Document v0.1.1.
* Error handling aspects are addressed within:
    * The "API Interaction Layer" of the Frontend Architecture Document (global and specific error handling for frontend API calls).
    * The "Security Architecture (Backend/Overall Focus)" section above (regarding not exposing sensitive error details).
    * The "Logging Strategy" section above (for logging errors).
    * Individual component and service design will need to incorporate robust error handling appropriate to their context.
