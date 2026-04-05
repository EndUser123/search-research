# --- METADATA ---
# Filename: README.md
# Version: 1.1
#
# --- CHANGELOG ---
# v1.1: Corrected setup instructions. Removed reference to a non-existent
#       config template and clarified dependency installation.
# v1.0: Initial project documentation.
# ------------------
# Vid_ReC: Video Re-encoding & Enhancement Controller

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)

Vid_ReC is a powerful, intelligent command-line tool for batch processing, re-encoding, and enhancing video files with minimal user intervention.

## Key Features

-   **Parallel Processing:** Dramatically speeds up CPU-bound encoding tasks by using multiple processor cores.
-   **Intelligent Quality (VMAF):** Automatically decides whether to keep a new file based on a superior quality-per-byte ratio.
-   **Automated Subtitle Generation:** Creates English subtitles for videos that lack them using a state-of-the-art speech-to-text model.
-   **Audio Normalization:** Ensures all output videos have a consistent, standard perceived audio loudness.
-   **Robust State Management:** Prevents re-processing of already completed files and allows for the resumption of interrupted jobs.
-   **Type-Safe Configuration:** Uses Pydantic for a clear, self-validating `config.toml`.

## Getting Started (User Guide)

To get the application up and running on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Vid_ReC
    ```

2.  **Install dependencies:**
    This project uses `pyproject.toml` to manage dependencies. Install them using `pip`.
    ```bash
    pip install .
    ```

3.  **Edit `config.toml`:**
    Open the `config.toml` file in a text editor. Set the `source` path to your video library and adjust any other settings as needed. The file is pre-configured with sensible defaults.

4.  **Run the application:**
    ```bash
    python -m src.main_processor
    ```

### Command-Line Overrides

You can override settings from your `config.toml` for a single run by using command-line arguments. Some common examples include:

-   `--source /path/to/your/videos`: Process a different directory (or a single file).
-   `--no-replace`: Prevents original files from being replaced. The new files will be left in your `temp_dir`.
-   `--language ja`: Forces the subtitle generator to assume the source language is Japanese (`ja`), overriding automatic detection.

## For Developers (Contributor Guide)

Welcome! We are excited to have you contribute. This project follows a structured, well-documented development process. To get started, please follow this path:

1.  **Set up your development environment:**
    Install the project with all development dependencies included. This will give you access to `pytest`, `ruff`, and other essential tools.
    ```bash
    pip install .[dev]
    ```

2.  **Understand the Vision:** Read the **[Project Roadmap](docs/ROADMAP.md)** to understand our high-level goals and current phase of development.

3.  **Learn the Process:** All contributions must follow the official **[Development Workflow](docs/DEV_WORKFLOW.md)**. This is the most important document for any contributor.

4.  **Understand the Architecture:** Get a high-level overview of the system's structure by reading the **[Architecture Overview](docs/ARCHITECTURE.md)**. This document serves as the primary map of the codebase and links to our **[Architectural Decision Records (ADRs)](docs/architecture/adr/)**.

5.  **Uphold Quality Standards:** Before committing, please ensure your changes align with the **[QA Checklist](docs/QA_CHECKLIST.md)**.

### Running Tests

To run the full suite of unit tests, use `pytest` (which was installed in step 1):
```bash
pytest
