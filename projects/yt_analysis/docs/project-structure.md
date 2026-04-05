# Project Structure

As YTAP will be developed within a Monorepo structure, the following high-level project directory layout is proposed. This structure aims to provide a clear organization for the backend (Python), frontend (JavaScript), shared components (if any), documentation, tests, and other essential project assets. The detailed internal structure of the `frontend_ui/` directory will be further defined in the dedicated Frontend Architecture Document.

```plaintext
ytap-monorepo/
├── .github/                    # CI/CD workflows (e.g., GitHub Actions) (Future consideration)
├── .vscode/                    # Optional: VSCode specific settings (e.g., linter, formatter configs)
├── docs/                       # All project documentation
│   ├── YTAP_Project_Brief_v1.0.md
│   ├── YTAP_PRD_v0.1.md
│   ├── YTAP_Architecture_Doc_v0.1.1.md
│   ├── YTAP_UI_UX_Spec_v0.1_draft.md
│   ├── YTAP_Frontend_Architecture_Document_v0.1.md
│   └── (other supporting docs, diagrams, etc.)
├── scripts/                    # Utility or helper scripts (e.g., for setup, data tasks, build)
├── src/                        # Main application source code
│   ├── backend_engine/         # Python-based backend core engine, services, and API
│   │   ├── main.py             # Main entry point or application factory for the backend
│   │   ├── api/                # API endpoints (e.g., FastAPI/Flask routes) exposed to the frontend
│   │   ├── components/         # Core backend modules/components as defined in Component View
│   │   │   ├── channel_management/
│   │   │   ├── transcript_ingestion/
│   │   │   ├── content_organization/
│   │   │   ├── data_export/
│   │   │   └── api_quota/
│   │   ├── persistence/        # Data persistence logic (e.g., Repository implementations for SQLite, file access)
│   │   ├── services/           # Business logic services (orchestrating persistence and components)
│   │   ├── config/             # Backend configuration loading and management
│   │   └── utils/              # Shared backend utility functions and classes
│   ├── frontend_ui/            # JavaScript-based GUI/Web UI application
│   │   ├── public/             # Static assets for the UI
│   │   ├── src/                # UI source code (components, views, state management, etc.)
│   │   ├── package.json        # JS project manifest and dependencies
│   │   └── (other JS framework specific files/folders, e.g., vite.config.js, next.config.js)
│   └── shared_types/           # Optional: TypeScript/Python type definitions shared between frontend and backend (e.g., API payload structures)
├── tests/                      # Automated tests
│   ├── backend/                # Unit and integration tests for the backend_engine
│   └── frontend/               # Unit and component tests for the frontend_ui (details in FE Arch Doc)
├── .env.example                # Example environment variables file for backend and potentially frontend build
├── .gitignore                  # Specifies intentionally untracked files that Git should ignore
├── Dockerfile                  # Potential Docker configuration for self-hosting YTAP (MVP/Future - Deferred for MVP)
└── README.md                   # Top-level project overview, setup instructions, and basic usage

Key Directory Descriptions (Initial Overview)
/docs/: Contains all project planning and design documentation, including the Project Brief, PRD, this Architecture Document, UI/UX Specification, Frontend Architecture Document, etc.
/scripts/: For utility scripts that might assist with development, build processes, or operational tasks (e.g., database setup, initial data seeding if any).
/src/: The main directory for all application source code.
/src/backend_engine/: Houses all Python code for YTAP's core logic, including API definitions, service modules for each major function (ingestion, organization, export), data persistence layer (repositories), and utility functions.
/src/frontend_ui/: Contains all source code for the JavaScript-based GUI/Web User Interface. The detailed internal structure of this directory will be further defined in the Frontend Architecture Document.
/src/shared_types/: (Optional) If there's a need for strongly typed data structures shared between the Python backend and JavaScript frontend (e.g., for API request/response payloads), they could reside here.
/tests/: Home for all automated tests, with subdirectories mirroring the /src/ structure to separate backend and frontend tests.
.env.example: Provides a template for developers to create their local .env file, which will contain environment-specific configurations and sensitive keys.
README.md: The primary entry point for understanding the project, with instructions on setup, basic usage, and contribution guidelines.
