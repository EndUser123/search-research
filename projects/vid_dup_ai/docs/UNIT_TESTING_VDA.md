# Testing Strategy for Video Dedupe AI

## 1. Introduction and Objectives
This document outlines a practical and robust testing strategy for the **Video Dedupe AI** script. The primary objective is to adapt principles from the advanced "AI Testing Guide" to ensure the script is reliable, correct, and maintainable. This strategy serves as a blueprint for both developers and automated testing frameworks.

## 2. Core Testing Principles and Framework
This section defines the foundational rules that govern all test cases to ensure consistency and quality.

- **Testing Framework:** All tests will be implemented using **`pytest`** for its powerful features in test discovery, execution, and fixtures.
- **Test Structure (AAA Pattern):** For maximum clarity and maintainability, every test will strictly follow the **Arrange-Act-Assert** pattern:
    - **Arrange:** Set up all preconditions, including mock objects and data structures.
    - **Act:** Execute the specific function or method under test.
    - **Assert:** Verify that the outcome matches the expected result.
- **Dependency Isolation (Mocking):** To ensure tests are fast, reliable, and run in isolation, all external dependencies **must** be mocked using **`pytest-mock`**. This includes:
    - File system operations (`os`, `shutil`).
    - External programs (`ffmpeg`).
    - Network-aware libraries (`transformers`, `torch`).

## 3. Unit Testing Plan
Unit tests are designed to verify the smallest pieces of the application in complete isolation.

### 3.1. Test Cases for `VideoProcessor`
| Method / Function               | Test Scenario                                                                                               | Priority |
|---------------------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `get_video_metadata`            | **Given** a mocked `ffmpeg.probe` result, **assert** that the correct metadata dictionary is returned.              | High     |
| `get_video_metadata`            | **When** `ffmpeg.probe` raises an error, **assert** that the function returns `None`.                               | High     |
| `get_quality_metric_score`      | **Mock** the `FfmpegQualityMetrics` class and **assert** that the average score is correctly extracted.               | Medium   |

### 3.2. Test Cases for `OperationPlanner`
| Method / Function               | Test Scenario                                                                                               | Priority |
|---------------------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `_find_potential_matches`       | **Using** a mock `videos_index`, **test** that matches are correctly found based on fuzzy name and duration.      | High     |
| `_select_best_video` (Quality)  | **Given** a list of mock videos, **assert** that the one with the highest `composite_score` is chosen.            | High     |
| `_select_best_video` (Size)     | **Given** a list where all quality scores are equal, **assert** that the smallest video is chosen.                  | High     |

### 3.3. Test Cases for `ConfigManager`
| Method / Function               | Test Scenario                                                                                               | Priority |
|---------------------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `get_config`                    | **Test** that command-line arguments correctly override settings from a mocked `config.ini` file.             | Medium   |

### 3.4. Test Cases for `main` Module (Security)
| Method / Function               | Test Scenario                                                                                               | Priority |
|---------------------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `normalize_and_validate_path`   | **Given** a path with `../`, **assert** that a `PermissionError` is raised.                                       | Critical |
| `normalize_and_validate_path`   | **Given** a valid path, **assert** that the correct absolute path is returned.                                    | High     |

## 4. Integration Testing Plan
Integration tests verify that different components of the script collaborate correctly. These tests are critical for validating the logic flow between classes.

| Feature / Flow                 | Test Scenario                                                                                                   | Mocks Required                 | Priority |
|--------------------------------|-----------------------------------------------------------------------------------------------------------------|--------------------------------|----------|
| **End-to-End Planning**        | **Test** the main `plan_operations` method. **Mock** `VideoProcessor` methods and **assert** a correct plan is generated.     | `VideoProcessor`, `os.walk`, `ffmpeg` | High     |
| **Graceful Dependency Failure**| **Simulate** `torch` not installed, pass `--categorize`, and **assert** the script exits gracefully.                    | `check_dependency` function      | High     |
| **`rich` UI Fallback**         | **Test** `setup_logger`: 1. With `rich` available, **assert** `RichHandler` is used. 2. Without, **assert** `StreamHandler`. | `RICH_AVAILABLE` flag          | Medium   |

## 5. Manual Testing Prerequisite (Pre-flight Check)
Before initiating the automated testing suite, a complete run-through of the **Manual Testing Plan** (`MANUAL_TESTING.md`) is mandatory. This pre-flight check ensures that the end-to-end user experience is validated and helps catch high-level regressions that isolated tests might miss.
