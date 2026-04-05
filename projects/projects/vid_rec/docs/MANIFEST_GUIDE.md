# Vid_ReC Manifest File Guide

## 1. Purpose

The `dev/vidrec_manifest.json` file is the central index for the `Vid_ReC` project. Its purpose is to provide a single, machine-readable "table of contents" for all essential, version-controlled project artifacts.

This file is used to:
-   Bootstrap the AI Architect's context at the beginning of a work session.
-   Provide a scalable way to reference project components without needing to read every file.
-   Enforce a consistent and logical project structure.

## 2. Schema Definition

The manifest follows a key-value structure, grouping related artifacts under logical top-level keys.

| Key | Type | Description |
| :--- | :--- | :--- |
| `projectName` | String | The official, human-readable name of the project. |
| `projectDescription`| String | A one-sentence summary of the project's purpose. |
| `project_definition`| Object | Contains paths to files that define the project's identity and dependencies. |
| `source_code` | Object | Contains paths to the main application source code. |
| `workflow_artifacts`| Object | Contains paths to operational files used by our development process itself. |
| `documentation` | Object | Contains paths to human-readable documentation and guides. |
| `testing` | Object | Contains paths to the testing suite. |

### 2.1. `project_definition` Schema

| Key | Type | Description |
| :--- | :--- | :--- |
| `build_definition` | String | Path to the `pyproject.toml` file. |
| `main_configuration`| String | Path to the main user-facing `config.toml` file. |
| `readme` | String | Path to the project's `README.md`. |

### 2.2. `source_code` Schema

| Key | Type | Description |
| :--- | :--- | :--- |
| `source_directory`| String | Path to the root source directory (e.g., `src/`). |

### 2.3. `workflow_artifacts` Schema

| Key | Type | Description |
| :--- | :--- | :--- |
| `state_file` | String | Path to the JSON file tracking task status (`dev/vidrec_state.json`). |
| `manifest_file` | String | Path to this manifest file itself (`dev/vidrec_manifest.json`). |
| `architect_prompt_template` | String | Path to the YAML template for initializing the AI Architect (`dev/prompt_template.yaml`). |

### 2.4. `documentation` Schema

| Key | Type | Description |
| :--- | :--- | :--- |
| `project_roadmap` | String | Path to the high-level strategic roadmap. |
| `DEV_WORKFLOW` | String | Path to the guide explaining the contribution process. |
| `qa_checklist` | String | Path to the pre-commit quality assurance checklist. |
| `manifest_guide` | String | Path to this guide document itself. |
| `architecture_dir` | String | Path to the directory containing architecture diagrams and descriptions. |
| `adr_dir` | String | Path to the directory containing Architectural Decision Records. |

### 2.5. `testing` Schema

| Key | Type | Description |
| :--- | :--- | :--- |
| `test_directory` | String | Path to the root testing directory (e.g., `tests/`). |
