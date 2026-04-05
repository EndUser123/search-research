# Environment Variables Guide

This document outlines the approach to managing environment variables within the YTAP project.

## Overview

Environment variables are used to manage configuration settings that may vary between deployment environments (e.g., local development, future self-hosted production) or contain sensitive information like API keys.

## Management

* **Mechanism:** Environment variables for YTAP are primarily managed using `.env` files at the root of relevant project areas (e.g., backend, frontend).
* **Example Files:** A `.env.example` file **must** be provided in the repository for both the backend and frontend. This file serves as a template, listing all required environment variables without their actual values. Users will copy this to a `.env` (or `.env.local`) file and populate it with their specific values.
* **Security:** Actual `.env` files containing secrets **must** be included in the project's `.gitignore` file to prevent them from being committed to version control.
* **Loading:**
    * The backend's "Configuration Management Service" is responsible for loading, validating, and providing access to these configurations from `.env` files and other potential sources.
    * The frontend will use framework-specific mechanisms to load environment variables (e.g., prefixed variables for Next.js or Vite).

## Key Variables (Conceptual - to be detailed in `.env.example`)

* **Backend (`src/backend_engine/.env.example`):**
    * `YT_API_KEY`: The user's YouTube Data API v3 key.
    * `SQLITE_DB_PATH`: Path to the SQLite database file.
    * Other backend-specific configurations (e.g., ASR service details if applicable, logging levels).
* **Frontend (`src/frontend_ui/.env.example`):**
    * `NEXT_PUBLIC_API_URL` or `VITE_API_URL`: The base URL for the YTAP backend API (e.g., `http://localhost:8000/api/v1`).
    * Other frontend-specific configurations.

Refer to the `.env.example` files within the `src/backend_engine/` and `src/frontend_ui/` directories (once created as per Epic 0) for a complete list and description of all environment variables. The "Secrets Management" section in `docs/infra-deployment.md` and the "Configuration Management Service" description in `docs/component-view.md` also provide relevant context.
