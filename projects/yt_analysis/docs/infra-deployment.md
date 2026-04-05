# Infrastructure and Deployment Overview

This section details how YTAP is intended to be deployed and managed, focusing on its infrastructure for a self-hostable application, and how sensitive data like API keys and certificates are handled.

## Certificates and Secrets Management

* **Secrets Management (e.g., API Keys):**
    * All sensitive secrets, such as the YouTube Data API v3 key, **shall** be managed by the user through environment variables, typically loaded from a `.env` file located in the project's root directory.
    * The application **shall not** store API keys or other secrets directly in its codebase or configuration files committed to version control.
    * The `.env` file itself **must** be included in the project's `.gitignore` file to prevent accidental commits. An `.env.example` file will provide a template for users.
    * This approach aligns with NFR5.1 and ensures user control over their sensitive credentials.

* **Certificates (SSL/TLS for Web UI - MVP Context):**
    * For the MVP, which is designed primarily for local execution on the user's desktop machine and accessed via `http://localhost:<port>`, the implementation of HTTPS with SSL/TLS certificates for the local YTAP web server is **not a requirement**.
    * If the user chooses to self-host YTAP on a server and access it across a network or expose it in a way that requires HTTPS (a post-MVP consideration), the setup and management of SSL/TLS certificates (e.g., using a reverse proxy like Nginx or Caddy with Let's Encrypt) will be the user's responsibility or part of that specific advanced deployment scenario. YTAP's core application for MVP will not bundle or require direct SSL certificate management.
