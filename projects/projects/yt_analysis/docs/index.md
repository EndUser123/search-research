# YTAP Project Documentation Index

This document serves as a central index for all key planning, design, and operational documents related to the YTAP (YouTube Transcript Analysis Project).

## I. Core Planning & Requirements Documents

### [YTAP Project Brief (v1.0)](YTAP_Project_Brief_v1.0.md)
Outlines the initial vision, goals, target audience, and high-level scope for the YTAP project.

### [YTAP Product Requirements Document (PRD) (v0.1)](YTAP_PRD_v0.1.md)
Details the functional and non-functional requirements for the YTAP MVP, including user interaction goals, technical assumptions, and an overview of project epics. *(Note: Detailed Epics are sharded below).*

### [YTAP UI/UX Specification (v0.1 - Draft)](YTAP_UI_UX_Spec_v0.1_draft.md)
Defines the user experience goals, information architecture, user flows (conceptual), and visual design specifications for the YTAP user interface.

## II. Architecture & Design Documents

### [YTAP Architecture Document (v0.1.1)](YTAP_Architecture_Doc_v0.1.1.md)
The main technical blueprint for YTAP, covering backend systems, shared services, overall architectural patterns, and core technology choices. *(Note: Key sections are sharded below for easier access).*

### [YTAP Frontend Architecture Document (v0.1)](YTAP_Frontend_Architecture_Document_v0.1.md)
Details the technical architecture specifically for the YTAP frontend, including framework application, component strategy, state management, API interaction, and testing. *(Note: Key sections are sharded below).*

### Architectural Granules:

#### [API Reference](api-reference.md)
Details external APIs consumed by YTAP and internal APIs it provides, including endpoints and authentication methods.

#### [Data Models](data-models.md)
Defines core application entities, API payload schemas, and database schemas for YTAP.

#### [Project Structure (Overall)](project-structure.md)
Outlines the monorepo project directory layout for backend, frontend, docs, tests, and other assets.

#### [Definitive Tech Stack Selections](tech-stack.md)
The single source of truth for all technology choices (languages, frameworks, databases, tools) for the YTAP project.

#### [Component View & Design Patterns (Backend/System)](component-view.md)
Describes the major logical backend components/services, their responsibilities, interactions, and the high-level architectural design patterns adopted.

#### [Core Workflows / Sequence Diagrams](sequence-diagrams.md)
Illustrates key system workflows and interactions using Mermaid sequence diagrams.

#### [Infrastructure, Deployment, and Secrets Management](infra-deployment.md)
Details how YTAP is intended to be deployed (focusing on local MVP), and how sensitive data like API keys are managed.

### Frontend Architectural Granules:

#### [Frontend Project Structure](front-end-project-structure.md)
Provides the detailed frontend application's folder structure within `frontend_ui/src/`.

#### [Frontend Styling Approach and Guide](front-end-style-guide.md)
Outlines the styling approach, guiding principles, and conceptual visual elements for the YTAP frontend.

#### [Frontend Component Guide](front-end-component-guide.md)
Details component naming, organization, and the standard template for specifying UI components.

#### [Frontend State Management In-Depth](front-end-state-management.md)
Expands on the chosen state management solution (Context API, etc.), decision guides, store structure, and patterns for selectors/actions.

#### [Frontend API Interaction Layer](front-end-api-interaction.md)
Describes how the frontend communicates with backend APIs, including HTTP client setup, service definitions, and error handling.

#### [Frontend Routing Strategy](front-end-routing-strategy.md)
Details navigation, routing library considerations, route definitions, and protection mechanisms.

#### [Frontend Testing Strategy](front-end-testing-strategy.md)
Elaborates on component testing, UI integration/flow testing, and E2E UI testing scope and tools for the frontend.

## III. Operational & Implementation Guides

#### [Environment Variables Guide](environment-vars.md)
Outlines the approach to managing environment variables using `.env` files for backend and frontend configurations.

#### [Operational Guidelines (Backend/System)](operational-guidelines.md)
Consolidates backend logging strategy, security architecture, and notes on testing and coding standards.

#### [Frontend Coding Standards](front-end-coding-standards.md)
Summarizes key coding standards and conventions for the YTAP frontend, focusing on TypeScript, React, linting/formatting, naming, and project structure adherence.

#### [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)
*(To be created as per Epic 0, Story 0.2)* - Will provide step-by-step instructions for setting up the local development environment for YTAP.

## IV. Project Epics (from PRD)

### [Epic 0: Project Initialization & Foundation](epic-0.md)
Focuses on establishing the core project repository, development environment, CI/CD pipeline, and testing frameworks.

### [Epic 1: Core Transcript Ingestion, Processing, and Management](epic-1.md)
Covers the system's ability to ingest YouTube video content, fetch/generate transcripts, store them with metadata, and manage API quotas.

### [Epic 2: Foundational Content Organization & Basic Export Utility](epic-2.md)
Details features for organizing ingested transcripts by user-defined categories and exporting transcript data.

## V. Other Key Documents

### [Key Reference Documents (from ARD)](key-references.md)
A list of key documents referenced within or complementing the main YTAP Architecture Document.
