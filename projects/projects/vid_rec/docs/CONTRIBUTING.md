# Contributing to Vid_ReC

Thank you for your interest in contributing to Vid_ReC! This guide outlines the process for setting up your development environment and submitting changes.

## 1. Setting Up the Development Environment

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Vid_ReC
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS / Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies in editable mode:**
    This command installs the project's dependencies and also installs the project itself in a way that allows you to edit the code directly.
    ```bash
    pip install -e .
    ```

## 2. Code Style and Linting

This project uses `black` for code formatting and `ruff` for linting to ensure a consistent code style.

Before committing any changes, please run these tools from the project's root directory:

```bash
# Auto-format all code with black
black src/

# Run the linter with ruff
ruff check src/
3. Submitting a Change
Create a new branch: Create a descriptive branch name for your feature or bugfix.


git checkout -b feature/my-new-feature
Make your changes: Implement your feature or bugfix.

Commit your work: Write a clear and concise commit message.


git add .
git commit -m "feat: Add new feature for X"
Push to your fork and create a Pull Request: Push your branch to your fork on the remote repository and open a Pull Request against the main branch of the original repository. Please provide a clear description of the changes in the Pull Request.
