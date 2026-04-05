# AI Coder's Guide to Effective Configuration Management

This guide provides best practices for managing configuration in Python, specifically tailored for an AI coder. By following these guidelines, you can build more scalable, maintainable, and secure applications.

## 1. Separate Configuration from Code

**The Problem:** Hardcoding configuration values in your code makes it difficult to change settings across different environments without modifying the code itself. This violates the "Config" principle of the [12-Factor App methodology](https://12factor.net/config), which states that config should be strictly separated from code.

**The Solution:** Externalize your configuration into files or environment variables. This simplifies updates, improves maintainability, and allows for easy deployment across different environments without code changes.

*   **Common file formats:**
    *   **.env files:** Used for storing environment variables, especially for local development. Libraries like `python-dotenv` can load these.
    *   **YAML (.yml) or JSON (.json):** Human-readable and support nested structures, suitable for complex configurations. Libraries like `PyYAML` or Python's built-in `json` module can parse these.
    *   **TOML (.toml):** A clear, human-friendly configuration file format that is easy to parse. The `tomlkit` library is excellent for this.
    *   **INI files (.ini):** Python's built-in `configparser` module can handle this format, which is good for simple, flat key-value pairs.

## 2. Handle Different Environments

**The Problem:** Applications typically run in multiple environments (development, testing, production), each with its own configuration (e.g., database credentials, API endpoints). Managing these manually can lead to errors and inconsistencies.

**The Solution:** Use one of these strategies to manage multiple environments effectively, ensuring the correct configuration is loaded for each deployment.

*   **Environment-specific files:** Use separate configuration files for each environment (e.g., `config.dev.yaml`, `config.prod.yaml`). Your application can then load the appropriate file based on an environment variable (e.g., `APP_ENV=production`).
*   **Hierarchical configuration:** Define a base configuration with common values and override specific settings for each environment. This reduces duplication and makes it clear which settings are environment-specific.
*   **Use environment variables:** Store environment-specific values directly in the execution environment. This is a common and highly recommended practice for containerized applications (e.g., with Docker) and cloud deployments.

## 3. Manage Secrets Securely

**The Problem:** Storing sensitive information like API keys, passwords, or database credentials directly in your source code or in unencrypted configuration files committed to version control is a major security risk.

**The Solution:** Implement robust secret management practices to protect sensitive data from unauthorized access.

*   **Environment variables:** Load secrets from environment variables at runtime. This is a simple and effective way to keep secrets out of your codebase.
*   **.env files:** Store secrets in a `.env` file for local development and ensure this file is listed in your `.gitignore` to prevent accidental commits.
*   **Cloud-based secret managers:** For production environments, use dedicated services like AWS Secrets Manager, Google Secret Manager, or Azure Key Vault. These services provide secure storage, access control, and auditing for your secrets.
*   **Encrypted configuration files:** Tools like Mozilla SOPS can encrypt secrets within your configuration files, allowing you to safely commit them to version control while keeping them encrypted at rest.

## 4. Use Validation and Typing

**The Problem:** Invalid or incorrectly typed configuration values can lead to runtime errors, unexpected behavior, and difficult-to-debug issues.

**The Solution:** Use validation and static typing to ensure your configuration is valid, correctly structured, and adheres to expected data types.

*   **Pydantic:** This library is highly recommended for modern Python configuration management. It allows you to define your configuration as a typed class (a `BaseModel`), providing powerful data validation, type casting, and default values. Pydantic's `BaseSettings` can automatically read settings from environment variables and `.env` files.
    ```python
    from pydantic import BaseModel, Field
    from pathlib import Path

    class PathsConfig(BaseModel):
        source: Path = Field(..., description="The root directory.")
        temp_dir: Path = Field(default=Path("/tmp/videos"), description="Temp dir.")

    class AppConfig(BaseModel):
        paths: PathsConfig
        log_level: str = "INFO"

    # Example usage:
    # config_data = {"paths": {"source": "/data/videos"}, "log_level": "DEBUG"}
    # app_config = AppConfig(**config_data)
    # print(app_config.paths.source)
    ```
*   **Dataclasses:** Python's built-in `dataclasses` can be used to create structured configuration objects, which is a cleaner approach than using raw dictionaries with string keys. While they don't offer built-in validation like Pydantic, they improve readability and provide type hints.
