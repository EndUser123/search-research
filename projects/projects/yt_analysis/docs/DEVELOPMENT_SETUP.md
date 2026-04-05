# YTAP Development Setup Guide

This guide provides step-by-step instructions for setting up and running the YTAP (YouTube Transcript Analysis Project) locally for development or testing purposes.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Git:** A version control system.
    *   [Official Git Installation Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

*   **Node.js (v20.x LTS):** A JavaScript runtime environment.
    *   [Official Node.js Installation Guide](https://nodejs.org/en/download/)

*   **Python (v3.11.x):** A programming language.
    *   [Official Python Installation Guide](https://www.python.org/downloads/)

*   **Python Virtual Environment:** It is strongly recommended to use a Python virtual environment to manage project dependencies.
    *   To create a virtual environment (e.g., named `venv`):
        ```bash
        python -m venv venv
        ```
    *   To activate the virtual environment:
        *   On Windows:
            ```bash
            .\venv\Scripts\activate
            ```
        *   On macOS/Linux:
            ```bash
            source venv/bin/activate
            ```

## Cloning the Repository

To get started, clone the `ytap-monorepo` to your local machine:

```bash
git clone https://github.com/your-org/ytap-monorepo.git
cd ytap-monorepo
```
*(Note: Replace `https://github.com/your-org/ytap-monorepo.git` with the actual repository URL when available.)*

## Backend Setup (`src/backend_engine/`)

1.  Navigate to the backend directory:
    ```bash
    cd src/backend_engine/
    ```

2.  Activate your Python virtual environment (if not already active):
    *   On Windows:
        ```bash
        ..\..\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source ../../venv/bin/activate
        ```

3.  Install backend dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Frontend Setup (`src/frontend_ui/`)

1.  Navigate to the frontend directory:
    ```bash
    cd src/frontend_ui/
    ```

2.  Install frontend dependencies:
    ```bash
    npm install
    # or if using Yarn:
    # yarn install
    ```

## Environment Configuration

The project uses `.env` files for environment-specific configurations.

1.  Copy the example environment file(s):
    *   For the project root (if applicable):
        ```bash
        cp .env.example .env
        ```
    *   For the backend:
        ```bash
        cp src/backend_engine/.env.example src/backend_engine/.env
        ```
    *   For the frontend:
        ```bash
        cp src/frontend_ui/.env.example src/frontend_ui/.env.local
        ```
    *(Note: The exact location and naming of `.env.example` files will depend on Story 0.1 implementation.)*

2.  Edit the copied `.env` (or `.env.local`) files and configure the following critical environment variables:

    *   **`YT_API_KEY` (Backend):** Your YouTube Data API v3 key. This is essential for fetching YouTube video and channel data. Obtain it from the Google Cloud Console.
    *   **`NEXT_PUBLIC_API_URL` or `VITE_API_URL` (Frontend):** The URL of your running backend API. This typically points to `http://localhost:8000` during local development.
    *   *(Add other critical environment variables as defined in `docs/environment-vars.md` and `.env.example` files from Story 0.1)*

## Running the Application

To run the YTAP application locally, you will need to start both the backend and frontend development servers.

1.  **Start the Backend Development Server:**
    *   Navigate to `src/backend_engine/` and activate your virtual environment.
    *   Run the backend server command (example, actual command may vary based on framework):
        ```bash
        python main.py # or uvicorn main:app --reload
        ```
    *   The backend API will typically be accessible at: `http://localhost:8000`

2.  **Start the Frontend Development Server:**
    *   Navigate to `src/frontend_ui/`.
    *   Run the frontend server command (example, actual command may vary based on framework):
        ```bash
        npm run dev
        # or yarn dev
        ```
    *   The frontend application will typically be accessible at: `http://localhost:3000`

Once both servers are running, you can access the YTAP application in your web browser at `http://localhost:3000`.
