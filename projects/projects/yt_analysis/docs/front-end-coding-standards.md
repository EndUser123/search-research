# Frontend Coding Standards

This document outlines key coding standards and conventions for the YTAP frontend. While a comprehensive, standalone coding standard document was not explicitly detailed in the YTAP Frontend Architecture Document v0.1, the following guidelines, derived from it and the main YTAP Architecture Document, MUST be followed.

## General Principles

* **Language:** All frontend code **MUST** be written in **TypeScript** (latest stable version, e.g., 5.x). Leverage TypeScript's type safety features and avoid `any` where possible.
* **Framework:** Adhere to **React** (latest stable version, e.g., 18.x) best practices and idiomatic patterns.
* **Clarity and Readability:** Code should be clear, concise, and easy to understand. Add comments to explain complex logic, not obvious statements.

## Linting and Formatting

* **Tools:**
    * **ESLint** (with necessary plugins for TypeScript, React, and Accessibility) **MUST** be used for identifying problematic patterns and enforcing coding standards.
    * **Prettier** **MUST** be used for opinionated code formatting to ensure a consistent code style across the codebase.
* **Configuration:** Default project configurations for these tools (e.g., `.eslintrc.js`, `.prettierrc.js`) will define the specific rules and MUST be adhered to.
* **CI Integration:** Linting and formatting checks **MUST** be part of the CI pipeline and fail the build if checks do not pass, as specified in "Epic 0: Story 0.3" of the PRD.

## Naming Conventions

* **Components & Files:** Use **PascalCase** for React component names and their corresponding filenames (e.g., `UserProfileCard.tsx`).
* **Variables & Functions:** Use camelCase (e.g., `currentUser`, `fetchChannelData`).
* **Types & Interfaces:** Use PascalCase (e.g., `interface ChannelMetadata`).
* **Constants:** Use UPPER_SNAKE_CASE (e.g., `const MAX_RETRIES = 3`).

## Project Structure

* All code **MUST** adhere to the **Detailed Frontend Directory Structure** defined in `docs/front-end-project-structure.md` (derived from the YTAP Frontend Architecture Document). Files must be placed in their designated directories based on their purpose and scope.

## Component Design

* Follow the **"Template for Component Specification"** for defining new components, as detailed in `docs/front-end-component-guide.md` (derived from the YTAP Frontend Architecture Document).
* Emphasize modularity, reusability, and separation of concerns.

## Other Key Practices

* **Imports:** Use ES Module syntax (`import`/`export`) exclusively. Organize imports (e.g., standard library, third-party, then local modules).
* **Accessibility (AX):** Adhere to the guidelines in `docs/accessibility-ax-implementation-details.md` (derived from YTAP Frontend Architecture Document).
* **Security:** Follow the practices outlined in `docs/frontend-security-considerations.md` (derived from YTAP Frontend Architecture Document).

This document serves as a high-level guide. More specific conventions may be adopted by the development team as the project progresses, provided they align with these foundational principles.
