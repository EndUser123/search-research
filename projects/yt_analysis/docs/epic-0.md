# Epic 0: Project Initialization & Foundation

* **Goal:** To establish a fully configured, standardized, and automated development environment for the YTAP project, enabling consistent code quality and efficient subsequent development of application features.

* **User Stories (Technical Enabling Stories):**

    * **Story 0.1: Establish Core Project Repository & Structure**
        * **User Story:** As a YTAP developer, I want a standardized monorepo initialized with the defined backend (`src/backend_engine/`) and frontend (`src/frontend_ui/`) directory structures, including basic configuration files (`package.json`, `pyproject.toml`/`requirements.txt`), so that all subsequent development has a consistent and organized foundation.
        * **Acceptance Criteria (ACs):**
            1.  A new Git repository named `ytap-monorepo` (or similar agreed-upon name) is initialized on a version control platform (e.g., GitHub).
            2.  The repository can be successfully cloned to a local development environment.
            3.  The root directory `ytap-monorepo/` is present.
            4.  The core project directory structure as defined in the YTAP Architecture Document (Project Structure section) is created within the repository. This MUST include at least:
                * `docs/`
                * `scripts/`
                * `src/`
                    * `src/backend_engine/`
                    * `src/frontend_ui/`
                * `tests/`
                    * `tests/backend/`
                    * `tests/frontend/`
            5.  A basic `package.json` file is created and committed at `src/frontend_ui/package.json` (e.g., initialized via `npm init -y` or `yarn init -y`), ready for a React/TypeScript project.
            6.  A basic Python project configuration file is created and committed for the backend within `src/backend_engine/` (e.g., an empty `requirements.txt` or a `pyproject.toml` suitable for Python 3.11+).
            7.  A root `.gitignore` file is created and committed, configured with common ignore patterns for Node.js (e.g., `node_modules/`, `*.log`, build outputs like `dist/`, `.next/`, `.parcel-cache/`, `coverage/`) and Python (e.g., `__pycache__/`, `*.pyc`, virtual environment folders like `venv/`, `.env`, `*.sqlite3`) projects.
            8.  All these initial project structure elements and configuration files are committed to the main branch of the Git repository with a descriptive initial commit message (e.g., "Initial project structure and configuration for YTAP monorepo").

    * **Story 0.2: Implement Initial README and Comprehensive Development Setup Guide**
        * **User Story:** As a YTAP developer, I want a root `README.md` file with a concise project overview and a `docs/DEVELOPMENT_SETUP.md` file with clear, step-by-step local setup instructions, so that anyone (including myself in the future or other contributors) can easily get the project running locally for development or testing.
        * **Acceptance Criteria (ACs):**
            1.  A `README.md` file is created and committed at the root of the `ytap-monorepo/`.
            2.  The `README.md` file contains at least the following sections:
                * **Project Title:** "YTAP (YouTube Transcript Analysis Project)".
                * **Description:** A brief (1-2 paragraph) overview of the project's purpose and goals, derived from the YTAP PRD's "Goal, Objective, and Context" section.
                * **Getting Started / Development Setup:** A section that clearly links to the `docs/DEVELOPMENT_SETUP.md` file for detailed setup instructions.
                * **(Optional but Recommended) Placeholders for:** "Usage" (how to use the application once running), "Features" (high-level list), and "Contributing" (guidelines for future contributions).
            3.  A `DEVELOPMENT_SETUP.md` file is created and committed within the `docs/` directory.
            4.  The `DEVELOPMENT_SETUP.md` file provides clear, accurate, and step-by-step instructions for a developer to set up and run the YTAP project locally. This guide MUST cover:
                * **Prerequisites:**
                    * Links to official installation guides for Git.
                    * Instructions for installing the specific version of Node.js (e.g., 20.x LTS) as defined in the YTAP Architecture Document.
                    * Instructions for installing the specific version of Python (e.g., 3.11.x) as defined in the YTAP Architecture Document.
                    * Strong recommendation and basic instructions for setting up and using a Python virtual environment (e.g., `venv`).
                * **Cloning the Repository:** Command to clone the `ytap-monorepo`.
                * **Backend Setup (`src/backend_engine/`):**
                    * Steps to navigate to the `src/backend_engine/` directory.
                    * Instructions for creating/activating the Python virtual environment.
                    * Command to install backend dependencies (e.g., `pip install -r requirements.txt`).
                * **Frontend Setup (`src/frontend_ui/`):**
                    * Steps to navigate to the `src/frontend_ui/` directory.
                    * Command to install frontend dependencies (e.g., `npm install` or `yarn install`).
                * **Environment Configuration:**
                    * Clear instructions on how to copy the `.env.example` file(s) (for backend and frontend, as defined in ARD and Frontend Architecture Document) to `.env` (or `.env.local`).
                    * A list and explanation of all critical environment variables that MUST be configured by the developer for the application to run (e.g., `YT_API_KEY` for the backend, `NEXT_PUBLIC_API_URL` or `VITE_API_URL` for the frontend).
                * **Running the Application:**
                    * The command(s) to start the backend development server.
                    * The command(s) to start the frontend development server.
                    * The expected local URLs (e.g., `http://localhost:3000` for frontend, `http://localhost:8000` for backend API) where the application components can be accessed.
            5.  The instructions within `docs/DEVELOPMENT_SETUP.md` are validated by at least one other team member or by following them precisely in a clean environment to ensure they result in a successfully running local development instance of YTAP (both backend and frontend components operational).
            6.  Both `README.md` and `docs/DEVELOPMENT_SETUP.md` are well-formatted and easy to read.

    * **Story 0.3: Integrate Linting, Formatting, and Basic CI Workflow**
        * **User Story:** As a YTAP developer, I want automated linting (Ruff for Python, ESLint for TypeScript) and formatting (Prettier for frontend) configured with project-standard rules, along with a basic Continuous Integration (CI) pipeline using GitHub Actions that runs these checks on every push/pull request, so that code quality, style consistency, and early issue detection are maintained from the project's inception.
        * **Acceptance Criteria (ACs):**
            1.  Ruff is configured for the Python backend (`src/backend_engine/`) with a sensible default ruleset and a corresponding configuration file (e.g., in `pyproject.toml` or `ruff.toml`) is committed.
            2.  ESLint (with necessary plugins for TypeScript, React, and Accessibility) and Prettier are configured for the TypeScript frontend (`src/frontend_ui/`) with sensible default rulesets, and their configuration files (e.g., `.eslintrc.js`, `.prettierrc.js`, `.prettierignore`) are committed.
            3.  The frontend's `package.json` includes script commands (e.g., `lint`, `lint:fix`, `format`, `format:check`) to execute ESLint and Prettier.
            4.  The backend project includes accessible commands or script configurations (e.g., in `pyproject.toml` for task runners like `poe`, or a `Makefile`) to execute Ruff for linting (including auto-fix) and formatting.
            5.  A GitHub Actions workflow file (e.g., located in `.github/workflows/ci.yml`) is created and configured to trigger automatically on pushes to the main development branch and on all pull requests targeting it.
            6.  The CI workflow successfully executes the following steps in isolated jobs or sequential steps:
                * Checks out the repository code.
                * Sets up the Node.js environment (version as per ARD).
                * Installs frontend dependencies.
                * Runs frontend linting and formatting checks (e.g., `npm run lint:check`, `npm run format:check`). The CI job MUST fail if these checks do not pass.
                * Sets up the Python environment (version as per ARD).
                * Installs backend dependencies.
                * Runs backend linting and formatting checks (e.g., `ruff check .`, `ruff format --check .`). The CI job MUST fail if these checks do not pass.
            7.  The status of the CI workflow (pass/fail for each check) is clearly reported on pull requests within the Git hosting platform interface.

    * **Story 0.4: Initialize Core Testing Frameworks with Placeholder Tests**
        * **User Story:** As a YTAP developer, I want Pytest (for the backend) and Jest with React Testing Library (for the frontend) installed and configured, each with a minimal sample passing test, so that a foundational structure for automated testing is established and validated early in the project lifecycle, and the CI pipeline can execute these tests.
        * **Acceptance Criteria (ACs):**
            1.  Pytest is added as a development dependency and correctly configured for the Python backend (`src/backend_engine/`).
            2.  A sample (placeholder) passing Pytest test file (e.g., `tests/backend/test_initial.py`) is created and committed, containing at least one simple assertion (e.g., `assert True`).
            3.  Jest and React Testing Library (RTL) are added as development dependencies and correctly configured for the React/TypeScript frontend (`src/frontend_ui/`), including any necessary Jest setup files (e.g., `jest.config.js`, `jest.setup.js`).
            4.  A sample (placeholder) passing Jest/RTL component test file (e.g., located at `src/frontend_ui/src/components/ui/ExampleComponent.test.tsx` or `src/frontend_ui/src/app/App.test.tsx`) is created and committed, testing a very simple component or asserting a basic render.
            5.  The frontend's `package.json` includes a script command (e.g., `test`) that executes all Jest tests and displays results, including coverage reports if configured.
            6.  The backend project includes an accessible command (e.g., via `pyproject.toml` task runners or `Makefile`) to execute all Pytest tests and display results, including coverage reports if configured.
            7.  The CI workflow defined in Story 0.3 is updated to include dedicated steps/jobs to:
                * Execute all frontend tests (e.g., `npm test`). The CI job MUST fail if any frontend tests fail.
                * Execute all backend tests (e.g., `pytest`). The CI job MUST fail if any backend tests fail.
