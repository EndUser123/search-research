# YT-Sync Project: Coding Standards
**Version**: 2.2
**Last Updated**: 2025-06-22

## 1. Introduction

### 1.1. Purpose
This document establishes the official coding standards for the `yt-sync` project. Its purpose is to ensure code quality, consistency, and maintainability across the entire codebase.

### 1.2. Scope
These standards apply to all code written for this project, including application logic, tests, and utility scripts. All contributions, whether from human developers or AI assistants, must adhere to these guidelines.

### 1.3. Guiding Philosophy
- **Clarity over Cleverness**: Code should be easy to read and understand. Avoid overly complex or obscure constructs when a simpler, more direct solution exists.
- **Don't Repeat Yourself (DRY)**: Avoid duplicating code. Use functions, classes, and modules to create reusable components.
- **Fail-Fast**: As defined in **ADR 005**, services should validate inputs and configuration as early as possible and fail with clear, actionable error messages.

---

## 2. Standard Source Code Header

As defined in **ADR 006**, all Python source files (`.py`) in the `yt_sync/` directory must begin with a standardized header block. The AI Architect is responsible for populating and maintaining this block for each file.

```python
# --- METADATA ---
# Filename: yt_sync/main_processor.py
# Version: 1.16
#
# --- CHANGELOG ---
# v1.16: Refactored scan phase progress bar to show file counts for better observability.
# v1.15: Added a guard to the subtitle callback to prevent progress overflow (e.g., 1203/962), ensuring stable time estimates.
# v1.14: Reinstated stable hierarchical subtitle progress bar and fixed final summary logic.
# v1.13: Reverted subtitle progress to a single, robust bar to fix terminal rendering bugs.
# v1.12: Correctly initialize subtitle child task with total=None to prevent freeze.
#
# --- INTEGRITY ---
# Previous Character Count: 11628
# Current Character Count: 11985
# Reason for Shrinkage: null
# ------------------
#
# --- ARCHITECT'S OATH (PRE-FLIGHT CHECK) ---
# Self-check to prevent failures.
# 1. Context Continuity: Review prior instructions/code ensuring no requirements/context forgotten.
# 2. Error Prevention: Identify/address common errors (input validation, exception handling, edge cases).
# 3. API Verification: Verify API calls against docs to prevent signature mismatches/runtime errors.
# 4. Data Integrity: Ensure no data/logic from files/steps lost or altered without instruction.
# 5. Reasoning Transparency: Explain reasoning, choices, and assumptions.
# -------------------------------------------
```

### 2.1. Header Field Explanations

* **METADATA**:
    * `Filename`: The full path to the file from the project root.
    * `Version`: A semantic version number for the file itself, incremented with significant changes.
* **CHANGELOG**:
    * A brief, reverse-chronological log of the most recent, significant changes to the file.
* **INTEGRITY**:
    * `Previous Character Count`: The character count of the file *before* the proposed change.
    * `Current Character Count`: The character count of the file *after* the proposed change.
    * `Reason for Shrinkage`: If the character count decreases, provide a brief justification. Use `null` otherwise.
* **ARCHITECT'S OATH**:
    * A mandatory pre-flight checklist for the AI Architect to mentally complete before generating any file.

---

## 3. Python Language Standards

### 3.1. Formatting & Encoding

* **PEP 8 Compliance**: All Python code must strictly follow the [PEP 8](https://peps.python.org/pep-0008/) style guide.
* **Character Encoding**: All text and source code files must be saved with UTF-8 encoding.
* **Indentation**:
    * Use 4 standard ASCII spaces (`\x20`) per indentation level.
    * Never use tabs or non-standard whitespace.

### 3.2. Naming Conventions

* Follow PEP 8 naming conventions (`snake_case` for functions and variables, `PascalCase` for classes).
* Use descriptive, unambiguous names. For example, `discoverer` is better than `disc`.
* Avoid single-letter variable names except for simple loop counters (e.g., `i`, `k`, `v`).

### 3.3. Docstrings and Comments

* All public modules, functions, classes, and methods must have docstrings explaining their purpose.
* Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings) format for docstrings.
* Use inline comments (`#`) to explain complex logic, algorithms, or workarounds.

### 3.4. Error Handling

* Follow the **Fail-Fast Principle** as defined in ADR 005.
* Use specific, custom exceptions for application-level errors, inheriting from a base `YTSyncError` class.
* Avoid broad `except Exception:` clauses. Catch specific exceptions whenever possible.
