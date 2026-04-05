# ADR-008: Use SQLAlchemy with SQLite for Domain Models

## Status
Accepted

## Context

The project initially lacked a defined persistence layer and Object-Relational Mapper (ORM) for its core domain models (e.g., User, Order, Product). While `src/state_manager.py` utilized SQLite for internal application state, there was no clear strategy for managing and persisting application-specific data.

To enable features requiring data storage and retrieval, such as user management, order processing, and product catalog, a decision on the database and ORM stack is required.

## Decision

We will adopt **SQLite** as the database and **SQLAlchemy** as the ORM for managing the application's domain models.

## Consequences

### Positive

*   **Simplicity and Portability:** SQLite is a lightweight, file-based database, eliminating the need for a separate database server. This simplifies development, deployment, and testing, making the application highly portable.
*   **Familiarity:** The project already uses SQLite for `state_manager`, leveraging existing knowledge within the codebase.
*   **Robust ORM:** SQLAlchemy is a mature, powerful, and flexible ORM that provides a Pythonic way to interact with relational databases. It supports complex queries, relationships, and schema migrations (though explicit migration tools like Alembic would be needed for production-grade schema evolution).
*   **Testability:** SQLAlchemy's session management allows for easy setup of transactional tests, ensuring isolated and repeatable test runs.
*   **Scalability Path:** While SQLite is suitable for many small to medium-sized applications, SQLAlchemy provides a consistent API that allows for easier migration to more robust database systems (e.g., PostgreSQL, MySQL) if future scalability requirements demand it.

### Negative

*   **No Built-in Concurrency for Writes:** SQLite has limitations with concurrent write operations. While SQLAlchemy helps manage connections, heavy concurrent writes might still lead to performance bottlenecks or `database is locked` errors. For this application's expected usage (primarily single-user or limited concurrent operations), this is not anticipated to be a significant issue.
*   **Schema Migrations:** While SQLAlchemy defines models, managing schema changes (e.g., adding columns, altering tables) in a production environment typically requires a dedicated migration tool like Alembic, which adds an additional layer of complexity.
*   **Learning Curve:** Developers new to SQLAlchemy may face a learning curve due to its comprehensive feature set and flexible API.

### Neutral

*   **File-based Database:** The database will be stored as a file (`sql_app.db` by default), which needs to be managed (e.g., backed up) like any other application file.

## Alternatives Considered

*   **No ORM (Raw SQL):** While offering maximum control, raw SQL would increase development time, introduce more boilerplate, and make the codebase harder to maintain and evolve.
*   **Other ORMs (e.g., Peewee, PonyORM):** While simpler for some use cases, SQLAlchemy's widespread adoption, comprehensive features, and robust community support make it a more future-proof choice for a growing application.
*   **PostgreSQL/MySQL:** These are more robust client-server databases suitable for high-concurrency and large-scale applications. However, they introduce additional setup and management overhead (installing and running a database server), which is unnecessary for the current scope of this CLI tool.
