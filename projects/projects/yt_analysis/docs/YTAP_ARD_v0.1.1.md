Okay, excellent. I'm glad those sections meet your approval.

With these additions and the earlier updates, the YTAP Architecture Document (which I'll version as 0.1.1 to reflect these changes as of June 4, 2025) is now substantially complete for this phase of planning. It provides a comprehensive technical blueprint for the MVP.

Here is the complete YTAP Architecture Document (Version 0.1.1) for your records:

````markdown
# YTAP Architecture Document

**Version:** 0.1.1
**Date:** 2025-06-04

## Introduction / Preamble

This document outlines the overall project architecture for YTAP (YouTube Transcript Analysis Project). It details the design of its backend systems, core processing engine for content ingestion (including transcript fetching and Audio-to-Text conversion), data management strategies (for transcripts and associated metadata), and any shared services or non-User Interface (UI) specific concerns. Its primary goal is to serve as the guiding architectural blueprint for YTAP's development, ensuring consistency, maintainability, and adherence to chosen patterns, technologies, and the "Modular AI Workflow" guiding principle. It aims to provide a clear technical foundation for building a system capable of reliably ingesting content from various sources, enabling foundational organization, supporting basic utility functions like export, and ultimately supporting your goal of becoming "smarter" by identifying actionable insights.

**Relationship to Frontend Architecture:**
Given that the YTAP MVP includes a "simple, user-friendly GUI or Web UI" as its primary interface, a separate **Frontend Architecture Document** will be developed (likely by Jane, our Design Architect, in consultation with the development team). That document will detail the frontend-specific design, such as the chosen UI framework (e.g., React), component structure, state management approach, and interaction with backend APIs. The Frontend Architecture Document **must** be used in conjunction with this main YTAP Architecture Document. Core technology stack choices documented herein (particularly in the "Definitive Tech Stack Selections" section) are considered definitive for the entire YTAP project, including any frontend components, unless explicitly stated otherwise.

## Table of Contents
_{ Placeholder - To be populated as the document is built out }_
- [Introduction / Preamble](#introduction--preamble)
- [Table of Contents](#table-of-contents)
- [Technical Summary](#technical-summary)
- [High-Level Overview](#high-level-overview)
- [Architectural / Design Patterns Adopted](#architectural--design-patterns-adopted)
- [Component View](#component-view)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Data Models](#data-models)
- [Core Workflow / Sequence Diagrams](#core-workflow--sequence-diagrams)
- [Definitive Tech Stack Selections](#definitive-tech-stack-selections)
- [Infrastructure and Deployment Overview](#infrastructure-and-deployment-overview)
- [Database Migrations](#database-migrations)
- [Logging Strategy (Backend - Python)](#logging-strategy-backend---python)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Security Architecture (Backend/Overall Focus)](#security-architecture-backendoverall-focus)
- [Disaster Recovery (DR)](#disaster-recovery-dr)
- [Scalability and Performance Design (Backend/Overall Focus)](#scalability-and-performance-design-backendoverall-focus)
- [Developer Onboarding](#developer-onboarding)
- [Decision Log](#decision-log)
- [Key Reference Documents](#key-reference-documents)
- [Change Log](#change-log)

## Technical Summary

The YTAP (YouTube Transcript Analysis Project) system is architected to function as a personalized knowledge and insight engine, with its Minimum Viable Product (MVP) focused on establishing a **reliable and robust YouTube transcript ingestion and management pipeline**, implementing **foundational content organization**, and providing **basic data export utility** via a simple, user-friendly GUI/Web UI. The architecture will be guided by key Non-Functional Requirements including high reliability, cost-effectiveness (particularly in YouTube Data API v3 quota management), usability of the desktop web UI, and overall system maintainability.

Key logical components envisioned for the MVP include:
* A **Data Ingestion Module** responsible for fetching YouTube channel/video metadata, retrieving existing transcripts, performing Audio-to-Text (ASR) conversion for videos without transcripts, handling restricted content scenarios, and managing a configurable retry mechanism.
* A **Data Storage Layer** for persisting raw transcript text (likely as files) and structured metadata (for channels, videos, categories, processing status, quality flags; SQLite is a consideration for metadata storage).
* A **Content Organization Module** to manage user-defined categories and associate transcripts with them.
* A **Data Export Module** providing basic text export functionality with optional simple cleaning.
* A **GUI/Web User Interface** serving as the primary interaction point for the MVP on desktop browsers.

The technology stack will primarily leverage **Python** for backend processing and the core engine, and **JavaScript** for the frontend GUI/Web UI. An initial preference for a **Monorepo** structure has been noted. A critical architectural principle is adherence to a **simple, modular, and maintainable design**, aligning with the "Modular AI Workflow" guiding principle. The system is intended to be **locally runnable or self-hostable**, without reliance on managed cloud platform services. The potential use of a self-hosted **n8n.io** instance for workflow automation, particularly for data ingestion, will be evaluated during the detailed design phase. The architecture will aim for extensibility to support future features like advanced analytics, additional content sources, Minimal Lossy Text Simplification (MLTS), and semantic search capabilities.

## High-Level Overview

For the YTAP MVP, the system will be designed using a **Modular Monolith** architectural style. This approach is chosen to effectively balance the project's requirements for simplicity, maintainability, and a self-hostable/local deployment model with the need for clear internal structure and future extensibility, aligning with the "Modular AI Workflow" guiding principle. While YTAP will be developed as a single application for ease of deployment and management in its initial phase, its internal design will emphasize distinct modules (e.g., data ingestion, content organization, data export, UI interaction layer) with well-defined interfaces to ensure logical separation of concerns and facilitate future development or potential refactoring.

The project will utilize a **Monorepo** structure for version control and codebase management, as per the initial user preference. This will consolidate all related code for the backend (Python), frontend GUI/Web UI (JavaScript-based), any potential future CLI, and associated documentation within a single repository.

At a conceptual level, the primary user interaction and data flow for the MVP is envisioned as follows:
1.  The **User** interacts with the **GUI/Web UI** (designed for desktop web browsers) to perform actions such as adding/managing YouTube channels, assigning categories, initiating transcript processing, viewing ingested content, and triggering exports.
2.  These UI actions will typically send requests to a **Backend Core Engine** (primarily Python-based).
3.  The **Backend Core Engine** is responsible for:
    * Orchestrating the data ingestion pipeline: fetching channel/video metadata from YouTube, retrieving existing transcripts, managing Audio-to-Text (ASR) conversion processes for videos without transcripts, implementing retry logic for failed operations, and monitoring API quota usage.
    * Interacting with the **Data Storage Layer** to persist and retrieve channel information, video metadata, transcript status, user-defined categories (likely using SQLite for structured metadata), and the transcript text files themselves.
    * Applying categorization logic to ingested content.
    * Handling data export requests, including any optional basic text cleaning (profanity/filler word removal).
4.  The Backend Core Engine will provide data and status updates back to the GUI/Web UI for display to the user (e.g., progress of ingestion, lists of categorized transcripts, results of export operations).

*(A high-level system context or interaction diagram, likely using Mermaid, will be developed and inserted here later in the design process, once the primary components and their interfaces are more formally defined in the "Component View" section.)*

## Architectural / Design Patterns Adopted

The YTAP architecture will incorporate several key high-level design patterns to ensure a robust, maintainable, and scalable system, aligning with our "Modular Monolith" architectural style and the principles of simplicity and modularity previously established.

* **Pattern 1: Modular Design**
    * _Description:_ The system will be constructed as a collection of cohesive, loosely-coupled modules, each with well-defined responsibilities and clear interfaces (e.g., a module for data ingestion, another for content organization, a separate one for the data export functionality, and a distinct layer for UI interaction). This directly implements the "Modular Monolith" architectural style and supports the "Modular AI Workflow" guiding principle.
    * _Rationale/Reference:_ This pattern enhances maintainability by isolating the impact of changes within specific modules. It improves testability, as modules can often be tested independently. It promotes a strong separation of concerns, leading to a more organized and understandable codebase, which is crucial for long-term development and scalability of features.

* **Pattern 2: Repository Pattern (for Data Access)**
    * _Description:_ All logic for accessing and persisting data (such as channel metadata, video information, transcript status in the SQLite database, and transcript text files) will be encapsulated within Repository components. These repositories will provide a clean abstraction layer between the core application/business logic and the underlying data storage mechanisms.
    * _Rationale/Reference:_ This pattern decouples the core application logic from the specifics of how data is stored and retrieved. This significantly improves testability (as repositories can be easily mocked or replaced with fakes during testing) and makes the system more flexible, allowing changes to data storage technologies (e.g., moving from file system to a different storage for transcripts, or changing database systems) with minimal impact on the rest of the application. It also centralizes data access logic, making it easier to manage and optimize.

* **Pattern 3: Dependency Injection (DI)**
    * _Description:_ Dependencies between different modules and components within YTAP (e.g., a service needing a specific repository, or a UI controller needing a backend service) will be managed using the Dependency Injection pattern. Instead of components creating their own dependencies internally, these dependencies will be "injected" from an external source (e.g., a DI container or manually during component construction).
    * _Rationale/Reference:_ DI promotes loose coupling between components, which is fundamental for a modular and maintainable system. It greatly enhances testability by allowing dependencies to be easily replaced with mock objects or test doubles. This also increases the flexibility of the system, as components can be reconfigured or their dependencies swapped out with less effort.

## Component View

Based on the Modular Monolith architectural style chosen for YTAP, the system will be structured into several key logical components (or internal modules). These components are designed to have clear responsibilities and interact through well-defined interfaces, promoting modularity, maintainability, and testability. The primary interaction flow involves the User Interface communicating with a Backend Core Engine, which itself is composed of several specialized service modules.

The major logical components for the YTAP MVP are envisioned as follows:

* **1. YTAP User Interface (GUI/Web Application)**
    * **Description:** The primary interface for all user interaction with YTAP, designed as a desktop web browser application. It will encompass the views and user flows defined in the UI/UX Specification (e.g., Dashboard, Channels Management, Content Explorer, Exporter, Settings).
    * **Responsibilities:**
        * Presenting information, status, and data to the user in a clear, user-friendly manner.
        * Capturing user input for all operations (e.g., adding channel URLs, selecting categories, initiating processing, configuring settings, triggering exports).
        * Communicating user requests and data to the Backend Core Engine, likely via a defined API (e.g., a RESTful or similar HTTP-based API exposed by the backend).
        * Displaying feedback, progress, and results from backend operations.
    * **Key Collaborators:** Backend Core Engine (specifically, its API interface).

* **2. Backend Core Engine (Modular Monolith - Python-based)**
    * **Description:** The central processing and application logic hub of YTAP, implemented primarily in Python. It orchestrates all backend operations and manages the core business logic. It will be internally structured into the following distinct service modules:
        * **2a. Channel & Video Metadata Service:**
            * **Responsibilities:** Managing the persistent list of user-defined YouTube channels and their associated categories. Discovering new videos within these channels by interacting with the YouTube Data API v3. Fetching, parsing, and updating video metadata. Collaborating with the Data Persistence Layer for storage and retrieval.
            * **Key Collaborators:** YouTube Data API v3 Client, Data Persistence Layer, API Quota Management Service.
        * **2b. Transcript Ingestion Service:**
            * **Responsibilities:** Orchestrating the retrieval of existing transcripts from YouTube. Managing and invoking Audio-to-Text (ASR) conversion processes for videos lacking pre-existing transcripts. Implementing and managing the configurable retry mechanism for failed ingestion attempts. Performing basic automated quality indication on ingested transcripts. Storing final transcripts via the Data Persistence Layer.
            * **Key Collaborators:** YouTube Transcript Fetching Utilities (e.g., youtube-transcript-api, yt-dlp), ASR Technology/Service (to be defined), Data Persistence Layer, Retry Mechanism Component.
        * **2c. Content Organization Service:**
            * **Responsibilities:** Managing user-defined interest categories (create, rename, delete, list). Handling the association of ingested transcripts/videos with these categories. Providing capabilities to query or filter content based on categories for display or export.
            * **Key Collaborators:** Data Persistence Layer.
        * **2d. Data Export Service:**
            * **Responsibilities:** Handling user requests to export selected transcripts (individually or by category). Applying optional basic text cleaning (profanity filtering, filler word removal) based on user selection and configurable lists. Preparing transcript data in the specified plain text format.
            * **Key Collaborators:** Data Persistence Layer, Text Cleaning Utilities.
        * **2e. API Quota Management Service:**
            * **Responsibilities:** Tracking estimated usage of the YouTube Data API v3 quota. Providing quota status information.
            * **Key Collaborators:** Channel & Video Metadata Service, User Interface (for status display).
        * **2f. Configuration Management Service:**
            * **Responsibilities:** Loading, validating, and providing access to all application configurations (from `.env` files, potential YAML files, and user-configurable settings via the UI). Managing settings like the retry mechanism toggle, API keys, category definitions, and quality indicator thresholds.
            * **Key Collaborators:** All other backend modules, User Interface (for settings management).

* **3. Data Persistence Layer (Implementing Repository Pattern)**
    * **Description:** This layer is responsible for all direct interactions with the physical data stores, abstracting the data storage mechanisms from the service modules. It will implement the Repository Pattern.
    * **Responsibilities:**
        * Storing and retrieving structured metadata related to channels, videos, categories, processing statuses, and quality flags (likely utilizing SQLite repositories, as per Technical Assumptions).
        * Storing and retrieving transcript text files from the designated file system location.
        * Managing database connections, schema (migrations if needed), and ensuring data integrity at the storage level.
    * **Key Collaborators:** All Backend Core Engine service modules that require data persistence or retrieval.

*(A component diagram illustrating these components and their primary interactions will be added here later in the design process, once these responsibilities and interfaces are further refined.)*

## Project Structure

As YTAP will be developed within a Monorepo structure, the following high-level project directory layout is proposed. This structure aims to provide a clear organization for the backend (Python), frontend (JavaScript), shared components (if any), documentation, tests, and other essential project assets. The detailed internal structure of the `frontend_ui/` directory will be further defined in the dedicated Frontend Architecture Document.

```plaintext
ytap-monorepo/
├── .github/                    # CI/CD workflows (e.g., GitHub Actions) (Future consideration)
├── .vscode/                    # Optional: VSCode specific settings (e.g., linter, formatter configs)
├── docs/                       # All project documentation
│   ├── YTAP_Project_Brief_v1.0.md
│   ├── YTAP_PRD_v0.1.md
│   ├── YTAP_Architecture_Doc_v0.1.1.md (this document)
│   ├── YTAP_UI_UX_Spec_v0.1_draft.md
│   ├── YTAP_Frontend_Architecture_Document_v0.1.md
│   └── (other supporting docs, diagrams, etc.)
├── scripts/                    # Utility or helper scripts (e.g., for setup, data tasks, build)
├── src/                        # Main application source code
│   ├── backend_engine/         # Python-based backend core engine, services, and API
│   │   ├── main.py             # Main entry point or application factory for the backend
│   │   ├── api/                # API endpoints (e.g., FastAPI/Flask routes) exposed to the frontend
│   │   ├── components/         # Core backend modules/components as defined in Component View
│   │   │   ├── channel_management/
│   │   │   ├── transcript_ingestion/
│   │   │   ├── content_organization/
│   │   │   ├── data_export/
│   │   │   └── api_quota/
│   │   ├── persistence/        # Data persistence logic (e.g., Repository implementations for SQLite, file access)
│   │   ├── services/           # Business logic services (orchestrating persistence and components)
│   │   ├── config/             # Backend configuration loading and management
│   │   └── utils/              # Shared backend utility functions and classes
│   ├── frontend_ui/            # JavaScript-based GUI/Web UI application
│   │   ├── public/             # Static assets for the UI
│   │   ├── src/                # UI source code (components, views, state management, etc.)
│   │   ├── package.json        # JS project manifest and dependencies
│   │   └── (other JS framework specific files/folders, e.g., vite.config.js, next.config.js)
│   └── shared_types/           # Optional: TypeScript/Python type definitions shared between frontend and backend (e.g., API payload structures)
├── tests/                      # Automated tests
│   ├── backend/                # Unit and integration tests for the backend_engine
│   └── frontend/               # Unit and component tests for the frontend_ui (details in FE Arch Doc)
├── .env.example                # Example environment variables file for backend and potentially frontend build
├── .gitignore                  # Specifies intentionally untracked files that Git should ignore
├── Dockerfile                  # Potential Docker configuration for self-hosting YTAP (MVP/Future - Deferred for MVP)
└── README.md                   # Top-level project overview, setup instructions, and basic usage
````

### Key Directory Descriptions (Initial Overview)

  * **`/docs/`**: Contains all project planning and design documentation, including the Project Brief, PRD, this Architecture Document, UI/UX Specification, Frontend Architecture Document, etc.
  * **`/scripts/`**: For utility scripts that might assist with development, build processes, or operational tasks (e.g., database setup, initial data seeding if any).
  * **`/src/`**: The main directory for all application source code.
      * **`/src/backend_engine/`**: Houses all Python code for YTAP's core logic, including API definitions, service modules for each major function (ingestion, organization, export), data persistence layer (repositories), and utility functions.
      * **`/src/frontend_ui/`**: Contains all source code for the JavaScript-based GUI/Web User Interface. The detailed internal structure of this directory will be further defined in the Frontend Architecture Document.
      * **`/src/shared_types/`**: (Optional) If there's a need for strongly typed data structures shared between the Python backend and JavaScript frontend (e.g., for API request/response payloads), they could reside here.
  * **`/tests/`**: Home for all automated tests, with subdirectories mirroring the `/src/` structure to separate backend and frontend tests.
  * **`.env.example`**: Provides a template for developers to create their local `.env` file, which will contain environment-specific configurations and sensitive keys.
  * **`README.md`**: The primary entry point for understanding the project, with instructions on setup, basic usage, and contribution guidelines.

## API Reference

This section details the external Application Programming Interfaces (APIs) that YTAP will consume and any internal APIs it will provide to facilitate communication between its components.

### External APIs Consumed

**1. YouTube Data API v3**

  * **Purpose:** To fetch official channel metadata (e.g., channel name, upload playlist ID) and video metadata (e.g., video ID, title, publication date, duration, view counts) for content to be processed by YTAP. This API is essential for discovering videos and gathering authoritative context before transcript ingestion.
  * **Base URL(s):** `https://www.googleapis.com/youtube/v3/`
  * **Authentication:** Requires an API Key obtained from Google Cloud Console. This key will be managed securely by the user (e.g., via an `.env` file) and used for all requests.
  * **Key Endpoints Used (Conceptual for MVP):**
      * `GET /channels`: To retrieve channel details using channel ID or username (e.g., for `part=id,snippet,contentDetails` to get upload playlist ID).
      * `GET /playlistItems`: To list videos within a channel's upload playlist (e.g., for `part=snippet,contentDetails` to get video IDs and publication dates).
      * `GET /videos`: To fetch detailed information for specific video IDs (e.g., for `part=snippet,contentDetails,statistics` to get title, duration, view counts).
  * **Rate Limits:** Subject to YouTube Data API v3 quota limits (typically 10,000 units per day per project by default). YTAP is designed to minimize API calls and track estimated consumption to operate within these limits. The user is responsible for monitoring their own quota.
  * **Link to Official Docs:** [https://developers.google.com/youtube/v3/docs](https://developers.google.com/youtube/v3/docs)

**2. YouTube Transcript Service (via `youtube-transcript-api` library)**

  * **Purpose:** To retrieve pre-existing, publicly available text transcripts for YouTube videos. This is the primary method for obtaining transcripts when they are directly provided by YouTube.
  * **Base URL(s):** Not directly applicable as URLs are handled internally by the `youtube-transcript-api` Python library, which interacts with YouTube's unofficial transcript fetching mechanisms.
  * **Authentication:** Generally not required for publicly available transcripts on public videos.
  * **Key Endpoints Used:** Abstracted by the `youtube-transcript-api` library.
  * **Rate Limits:** Not officially documented by YouTube for this access method. The library itself may have some internal handling for retries, but excessive use could lead to IP-based throttling or temporary blocks by YouTube.
  * **Link to Official Docs:** N/A (as it's an unofficial API accessed by a third-party library). For the library: e.g., [https://pypi.org/project/youtube-transcript-api/](https://pypi.org/project/youtube-transcript-api/)

**3. `yt-dlp` (CLI utility / Python wrapper)**

  * **Purpose:** 1. To serve as a secondary method for attempting to download alternative pre-existing transcript file formats (e.g., .vtt, .srt) if the `youtube-transcript-api` fails or does not find a transcript. These files would then require parsing to plain text.
    2\. To download the audio track of YouTube videos when Audio-to-Text (ASR) conversion is necessary.
  * **Base URL(s):** N/A (interacts directly with YouTube content delivery networks).
  * **Authentication:** Generally not required for public videos. May require cookies for some restricted content, but this is an advanced use case likely outside MVP scope for direct transcript/audio download.
  * **Key Endpoints Used:** N/A (command-line tool interaction).
  * **Rate Limits:** Subject to YouTube's general traffic management; excessive use from a single IP could lead to throttling or blocks.
  * **Link to Official Docs:** [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)

**4. Audio-to-Text (ASR) Service/Library (To Be Determined by Architect)**

  * **Purpose:** To generate transcripts from video audio when pre-existing transcripts are not available or retrievable through other means.
  * **Base URL(s):** To be determined. The architectural design will prioritize local libraries or self-hostable models if feasible, to align with the "no managed cloud services" preference. If an external API-based service is considered, this section will be updated.
  * **Authentication:** TBD based on chosen solution.
  * **Key Endpoints Used:** TBD.
  * **Rate Limits:** TBD.
  * **Link to Official Docs:** TBD.

### Internal APIs Provided (If Applicable)

**1. YTAP Backend API (for Frontend UI Communication)**

  * **Purpose:** To serve as the communication interface between the YTAP Frontend UI (JavaScript-based web application) and the YTAP Backend Core Engine (Python-based). The UI will use this API to send user requests (e.g., add/manage channels, initiate processing, request data for display like channel/video lists and statuses, configure settings, trigger export operations) and to receive data, status updates, and results from the backend.
  * **Base URL(s) (Conceptual):** A local server address, e.g., `http://localhost:PORT/api/v1/`. The specific port and path structure will be defined during detailed design.
  * **Authentication/Authorization (MVP):** For the MVP, which is designed as a local/self-hosted personal tool without user login, complex authentication mechanisms between the locally running frontend and backend are not necessary. Access control will primarily be managed by the user's access to their own machine where YTAP is running.
  * **Endpoints (Conceptual - to be detailed during design):** The API will need to expose endpoints to support all functionalities defined in the PRD that require frontend-backend interaction. This will include, but not be limited to, endpoints for:
      * Managing channels (CRUD operations - Create, Read, Update, Delete).
      * Managing categories (CRUD operations).
      * Initiating and querying the status of processing tasks (e.g., transcript ingestion for channels/videos).
      * Retrieving lists of channels, videos, and transcripts, with filtering capabilities (e.g., by category, status).
      * Retrieving dashboard/status information, including API quota details.
      * Triggering transcript export operations and configuring associated cleaning options.
      * Managing application settings (e.g., retry toggle, quality flag criteria).
        *(A more detailed API specification, potentially using OpenAPI/Swagger, will be developed as part of the detailed backend and frontend design if the API complexity warrants it.)*

## Data Models

This section defines the structure of the key data entities that YTAP will manage, how data might be structured for API payloads (if distinct from core entities), and the schemas for persistent data storage.

### Core Application Entities / Domain Objects

These are the main objects or concepts that the YTAP application will work with directly. For the MVP, the following core entities are identified:

**1. Channel**

  * **Description:** Represents a YouTube channel that the user has added to YTAP for monitoring and transcript ingestion.
  * **Key Attributes (Conceptual Schema):**
    ```typescript
    interface Channel {
      channelId: string;          // Unique YouTube Channel ID (Primary Key for storage)
      channelName?: string;        // Official name of the channel (fetched via API)
      channelUrl: string;           // User-provided URL for the channel
      assignedCategories: string[]; // List of category names assigned by the user
      uploadPlaylistId?: string;   // YouTube playlist ID for the channel's uploads (for fetching videos)
      lastScannedDate?: Date;      // Timestamp of when YTAP last scanned this channel for new videos
      dateAddedToYTAP: Date;      // Timestamp of when this channel was added to YTAP by the user
    }
    ```
  * **Validation Rules (Conceptual):**
      * `channelId`: Must conform to YouTube's channel ID format.
      * `channelUrl`: Must be a valid YouTube channel URL. Input will be validated.
      * `assignedCategories`: Must reference valid, user-defined categories.

**2. Video**

  * **Description:** Represents an individual YouTube video processed or managed by YTAP, belonging to a tracked Channel.
  * **Key Attributes (Conceptual Schema):**
    ```typescript
    interface Video {
      videoId: string;            // Unique YouTube Video ID (Primary Key for storage)
      channelId: string;          // Foreign Key linking to the Channel entity
      videoTitle?: string;         // Official title of the video
      videoUrl: string;             // Direct URL to the YouTube video
      publicationDate?: Date;      // Date the video was published on YouTube
      duration?: string;           // Video duration (e.g., "PT10M5S" or formatted)
      viewCount?: number;          // Number of views (if fetched)
      transcriptStatus: string;   // e.g., 'pending_download', 'transcript_available', 'asr_needed', 'asr_in_progress', 'asr_completed', 'download_failed', 'asr_failed', 'restricted_access', 'processed'
      transcriptSource?: string;   // e.g., 'YouTube_direct', 'ASR_YTAP', 'yt-dlp_file'
      transcriptFilePath?: string; // Local path to the stored transcript text file
      automatedQualityIndicators?: string[]; // List of flags like 'short_transcript', 'high_asr_errors'
      manualQualityFlag?: string;  // User-applied flag e.g., 'Good', 'Needs Review'
      manualQualityNote?: string;  // User's note on quality
      dateAddedToYTAP: Date;      // Timestamp of when this video record was first created in YTAP
      lastProcessedDate: Date;    // Timestamp of when YTAP last processed/updated this video's transcript/status
      assignedCategories: string[]; // Categories inherited from the channel, potentially overridable
    }
    ```
  * **Validation Rules (Conceptual):**
      * `videoId`: Must conform to YouTube's video ID format.
      * `videoUrl`: Must be a valid YouTube video URL.

**3. Category**

  * **Description:** Represents a user-defined interest category (e.g., Health, Wealth, Fitness, Learning) used to organize channels and transcripts.
  * **Key Attributes (Conceptual Schema):**
    ```typescript
    interface Category {
      categoryName: string;       // Unique name of the category (Primary Key for storage)
      date_created: Date;        // When the category was defined by the user.
    }
    ```
  * **Validation Rules (Conceptual):**
      * `categoryName`: Must be unique, non-empty.

**4. TranscriptContent (Conceptual Object for holding transcript text)**

  * **Description:** Represents the actual textual content of a transcript. While stored as a file, the application might load it into an object for processing or display.
  * **Key Attributes (Conceptual Schema):**
    ```typescript
    interface TranscriptContent {
      videoId: string;            // Links to the Video entity
      rawText: string;            // The raw transcript text as initially ingested
      cleanedText?: string;        // Text after optional basic cleaning (for exporter)
    }
    ```

### API Payload Schemas (If distinct)

For the YTAP MVP, the data structures used in API payloads for the internal API (between the frontend UI and the backend core engine) are expected to closely mirror the definitions of the "Core Application Entities / Domain Objects" detailed above.

Specific request and response schemas for each API endpoint will be defined as part of the detailed API design process. At this stage, no complex, reusable payload structures that significantly diverge from the core entity definitions are anticipated for the MVP. This section can be expanded in the future if such distinct payload schemas become necessary.

### Database Schemas (If applicable)

The YTAP MVP will utilize an SQLite database for storing structured metadata. Transcript textual content will be stored as individual files on the local file system, with paths referenced in the database. The following conceptual table structures are proposed:

**1. `Channels` Table**

  * **Purpose:** Stores information about each YouTube channel added by the user.
  * **Conceptual Schema (SQLite):**
      * `channel_id` (TEXT, PRIMARY KEY) - Unique YouTube Channel ID.
      * `channel_name` (TEXT, NULLABLE) - Official name of the channel.
      * `channel_url` (TEXT, NOT NULL) - User-provided URL for the channel.
      * `assigned_categories` (TEXT, NOT NULL) - JSON string or comma-separated list of category names (e.g., '["Health", "Learning"]'). For MVP simplicity, a text field is proposed; a separate join table could be a future enhancement for more complex querying.
      * `upload_playlist_id` (TEXT, NULLABLE) - YouTube playlist ID for the channel's uploads.
      * `last_scanned_date` (DATETIME, NULLABLE) - Timestamp of when YTAP last scanned this channel.
      * `date_added_to_ytap` (DATETIME, NOT NULL) - Timestamp of when the channel was added to YTAP.
      * *Indexes likely on `channel_id` (automatic for PK).*

**2. `Videos` Table**

  * **Purpose:** Stores metadata and status information for each individual YouTube video processed by YTAP.
  * **Conceptual Schema (SQLite):**
      * `video_id` (TEXT, PRIMARY KEY) - Unique YouTube Video ID.
      * `channel_id` (TEXT, NOT NULL, FOREIGN KEY referencing `Channels(channel_id)`) - Links to the source channel.
      * `video_title` (TEXT, NULLABLE) - Official title of the video.
      * `video_url` (TEXT, NOT NULL) - Direct URL to the YouTube video.
      * `publication_date` (DATETIME, NULLABLE) - Date the video was published.
      * `duration` (TEXT, NULLABLE) - Video duration (e.g., formatted string or seconds).
      * `view_count` (INTEGER, NULLABLE) - Number of views (if fetched).
      * `transcript_status` (TEXT, NOT NULL) - Current processing status (e.g., 'pending\_download', 'transcript\_available', 'asr\_completed', 'download\_failed').
      * `transcript_source` (TEXT, NULLABLE) - How the transcript was obtained (e.g., 'YouTube\_direct', 'ASR\_YTAP', 'yt-dlp\_file').
      * `transcript_file_path` (TEXT, NULLABLE) - Relative or absolute path to the stored transcript text file.
      * `automated_quality_indicators` (TEXT, NULLABLE) - JSON string or comma-separated list of flags (e.g., '["short\_transcript"]').
      * `manual_quality_flag` (TEXT, NULLABLE) - User-applied flag (e.g., 'Good', 'Needs Review').
      * `manual_quality_note` (TEXT, NULLABLE) - User's note on quality.
      * `date_added_to_ytap` (DATETIME, NOT NULL) - Timestamp when this video record was created.
      * `last_processed_date` (DATETIME, NOT NULL) - Timestamp when this video's transcript/status was last updated by YTAP.
      * `assigned_categories` (TEXT, NOT NULL) - JSON string or comma-separated list of category names (usually inherited from the channel).
      * *Indexes likely on `video_id` (PK), `channel_id`, `transcript_status`, `publication_date`, `assigned_categories`.*

**3. `Categories` Table**

  * **Purpose:** Stores the list of user-defined personal interest categories.
  * **Conceptual Schema (SQLite):**
      * `category_name` (TEXT, PRIMARY KEY) - Unique name of the category (e.g., "Health", "Wealth").
      * `date_created` (DATETIME, NOT NULL) - When the category was defined by the user.
      * *Relationships to Channels/Videos are primarily managed via the `assigned_categories` text fields in the `Channels` and `Videos` tables for MVP simplicity.*

**Transcript File Storage:**

  * As per PRD FR1.11, transcript text will be stored as individual UTF-8 encoded plain text files.
  * The `transcript_file_path` in the `Videos` table will point to these files.
  * A consistent directory structure for these files (e.g., `<base_transcript_dir>/<category_name>/<channel_name>/<video_id>.txt`) will be defined.

## Core Workflow / Sequence Diagrams

This section illustrates key or complex workflows using Mermaid sequence diagrams.

**Workflow: User Adds a New YouTube Channel**

1.  **User Action:** The User navigates to the "Channels Management" view in the UI and clicks the "+ Add New Channel" button.
2.  **UI Presents Form:** The User Interface displays a form prompting for the YouTube Channel URL and allowing selection of one or more categories.
3.  **User Submits Data:** The User enters the required information and submits the form.
4.  **UI Request to Backend:** The User Interface sends an API request (e.g., a POST request to an `/api/v1/channels` endpoint) to the Backend Core Engine, containing the channel URL and selected categories.
5.  **Backend Processing (Channel & Video Metadata Service):**
      * The Backend Core Engine routes the request to the Channel & Video Metadata Service.
      * The Service validates the input (e.g., URL format, valid categories).
      * *(Optional, but likely for better UX):* The Service might make a quick call to the YouTube Data API v3 to fetch basic channel details (like the official Channel Name and Channel ID, if the input was a vanity URL) to store along with the user-provided URL. This would also verify the channel exists. API quota usage would be tracked.
      * The Service instructs the Data Persistence Layer to save the new channel information (Channel ID, User URL, Official Name, Assigned Categories, Date Added).
6.  **Backend Response to UI:** The Backend Core Engine sends a response back to the User Interface indicating success (and perhaps returning the newly saved channel details, including any fetched metadata like the Channel Name) or failure (with an error message).
7.  **UI Updates:** The User Interface displays a success message to the User and updates the list of managed channels to include the newly added channel.

<!-- end list -->

```mermaid
sequenceDiagram
    actor User
    participant UI as YTAP UI (GUI/Web App)
    participant Backend as Backend Core Engine
    participant ChanVidService as Channel & Video Metadata Service
    participant ExtYouTubeAPI as YouTube Data API v3
    participant Persistence as Data Persistence Layer

    User->>+UI: 1. Navigate to Channels Mgt & Click "+ Add Channel"
    UI-->>-User: 2. Display "Add Channel" form (URL, Categories)
    User->>+UI: 3. Enter Channel URL & Categories, Submit form
    UI->>+Backend: 4. API Request: POST /api/v1/channels (Channel URL, Categories)
    Backend->>+ChanVidService: 5a. processAddChannelRequest(data)
    ChanVidService->>ChanVidService: 5b. Validate input (URL format, categories)

    alt Input Invalid
        ChanVidService-->>Backend: Validation Error
        Backend-->>UI: Error Response (e.g., 400 Bad Request)
        UI-->>-User: Display validation error message
    else Input Valid
        opt Fetch Initial Channel Details from YouTube
            ChanVidService->>+ExtYouTubeAPI: 5c. GET /channels (to get official Channel Name/ID)
            ExtYouTubeAPI-->>-ChanVidService: Channel Details (Name, ID)
        end

        ChanVidService->>+Persistence: 5d. Save New Channel(ChannelInfo, Categories, DateAdded)
        Persistence-->>-ChanVidService: Confirm Save

        ChanVidService-->>Backend: 6a. Channel Added Successfully (with details)
        Backend-->>UI: 6b. Success Response (e.g., 201 Created, full Channel Details)
        UI-->>-User: 7. Display "Channel Added" success message & Update Channel List in UI
    end
```

*(More sequence diagrams for other key MVP workflows, such as "Transcript Ingestion Process" and "Exporting Transcripts," will be added as detailed design progresses or if specific complexities need to be visualized.)*

## Definitive Tech Stack Selections

This table is the **single source of truth** for all technology selections. Other architecture documents (e.g., Frontend Architecture) must refer to these choices and elaborate on their specific application rather than re-defining them.

| Category | Technology | Version / Details | Description / Purpose | Justification (Optional) |
| :--- | :--- | :--- | :--- | :--- |
| **Languages** | Python | **3.11.x** (or newer stable, e.g., 3.12.x at project start) | Primary language for backend core engine, services, and API. | Modern features, performance improvements, broad library support, good for web backends and data processing. |
| | TypeScript | **Latest stable at project start (e.g., 5.x)** | Primary language for frontend GUI/Web UI development. | Superset of JavaScript, provides type safety, improved maintainability for larger JavaScript projects. |
| **Runtime** | Python Interpreter | Matches Python language version (e.g., 3.11.x+) | Execution environment for all backend Python code. | Standard for Python applications. |
| | Node.js | **20.x (LTS at project start, or newer LTS)** | JavaScript runtime for frontend development tooling, build processes, and local dev server. | Standard for modern frontend JavaScript/TypeScript development; LTS ensures stability and long-term support. |
| **Frameworks** | FastAPI | **Latest stable at project start (e.g., 0.10x.x+)** | Python framework for building the backend API for YTAP. | Modern, high-performance, excellent for APIs with Python type hints, supports async, aligns with modular principles. |
| | React | **Latest stable at project start (e.g., 18.x)** | JavaScript/TypeScript library for building the frontend GUI/Web UI. | Popular, robust, large ecosystem, component-based, suitable for creating interactive and user-friendly interfaces. |
| **Databases** | SQLite | **Bundled with Python 3.11+ (e.g., 3.39.x+)** | Primary datastore for structured metadata (channels, videos, categories, status, etc.). | Simple, file-based, serverless, no separate setup needed, good for local/self-hosted applications, previously used. |
| | File System | **N/A (OS-level)** | Storage for raw transcript text files. | Direct and simple storage for text blobs; paths will be referenced in the SQLite database. |
| **Cloud Platform** | Local / Self-Hosted | **N/A** | YTAP is designed to run on the user's local machine or a self-managed server. | Aligns with user preference for control, no external dependencies on cloud providers for core operation, cost management. |
| **Cloud Services** | None for MVP / N/A | **N/A** | No specific managed cloud provider services will be used for core MVP functionality. | Aligns with the local/self-hosted preference and simplifies MVP deployment. External APIs are listed separately. |
| **Infrastructure** | Local Machine Environment | **N/A (User's OS: Windows, macOS, Linux)** | YTAP MVP will run directly on the user's OS using the specified Python & Node.js runtimes. | Aligns with self-hosted focus and simplicity for MVP. Docker containerization is deferred to post-MVP consideration. |
| **UI Libraries** | Modern React Component Library | **To be selected during Frontend Architecture phase; Latest stable version.** \<br/\>(e.g., Material UI, Ant Design, Chakra UI, or Tailwind CSS based sets like Headless UI, Shadcn/UI) | Provide pre-built, customizable UI components for the React-based frontend, ensuring a consistent, modern, and user-friendly interface. | Accelerates development, ensures a professional look/feel, promotes UI consistency. Selection guided by UI/UX goals ("simple," "pretty," "modern," "user-friendly") and ease of integration with React. |
| **State Management (Frontend)** | React Context API / Lightweight Library | **N/A (for Context API) / Latest stable (if library chosen, e.g., Zustand, Jotai)** | Manage frontend application state for the React UI. | Start with React's built-in Context API for simple global/shared state. Consider a lightweight library if more complex global state management needs clearly emerge during MVP development, prioritizing simplicity. |
| **Testing** | `pytest` | **Latest stable at project start** | Python testing framework for backend unit, integration, and API tests. | Popular, powerful, flexible, rich plugin ecosystem, concise syntax, excellent for testing FastAPI applications. |
| | Jest | **Latest stable at project start** | JavaScript testing framework for frontend (React) unit and component integration tests. | Widely adopted in the React ecosystem, good for snapshot testing, mocking, and asynchronous code. |
| | React Testing Library (RTL) | **Latest stable at project start (used with Jest)** | Utilities for testing React components in a user-centric way, focusing on behavior rather than implementation details. | Encourages good testing practices, improves test resilience to refactoring, well-integrated with Jest. |
| | Playwright | **Latest stable at project start** | End-to-End (E2E) testing framework for the frontend GUI/Web UI, simulating real user interactions in the browser. | Modern, fast, reliable, excellent cross-browser support (though MVP targets Chrome), good for testing full user flows. |
| **CI/CD** | GitHub Actions (or similar Git-based CI service) | N/A (uses cloud service features / latest syntax) | **Continuous Integration (CI) for MVP:** Automate code linting and execution of unit/component tests for backend (Python) and frontend (TypeScript/React) upon code pushes. | Improves code quality, catches regressions early, supports maintainability and the "must always work" principle with manageable setup. Continuous Deployment (CD) is deferred for MVP. |
| **Other Tools** | Ruff | **Latest stable at project start** | Fast Python linter and formatter (can replace Black, Flake8, isort). | Modern, extremely performant, consolidates multiple Python formatting/linting tools, improving developer experience. |
| | Prettier | **Latest stable at project start** | Opinionated code formatter for TypeScript/JavaScript and other frontend assets. | Ensures consistent code style across the frontend codebase, widely adopted. |
| | ESLint | **Latest stable at project start (with TS/React plugins)** | Pluggable linting utility for JavaScript and TypeScript to identify problematic patterns and enforce coding standards. | Highly configurable, industry standard for JS/TS projects, helps maintain code quality and catch errors early. |
| | n8n.io | **Latest stable (self-hosted)** | Workflow automation tool. To be evaluated for data ingestion pipelines and orchestration tasks. | User interest expressed. Potential to simplify complex data collection and processing workflows. Evaluation needed for MVP fit. |
| | yt-dlp | **Latest stable** | Command-line utility (or Python wrapper) for downloading YouTube videos/audio and transcripts. | Robust and versatile for YouTube content interaction; key for transcript acquisition fallback and ASR audio sourcing. |

## Infrastructure and Deployment Overview

This section details how YTAP is intended to be deployed and managed, focusing on its infrastructure for a self-hostable application, and how sensitive data like API keys and certificates are handled.

### Certificates and Secrets Management

  * **Secrets Management (e.g., API Keys):**

      * All sensitive secrets, such as the YouTube Data API v3 key, **shall** be managed by the user through environment variables, typically loaded from a `.env` file located in the project's root directory.
      * The application **shall not** store API keys or other secrets directly in its codebase or configuration files committed to version control.
      * The `.env` file itself **must** be included in the project's `.gitignore` file to prevent accidental commits. An `.env.example` file will provide a template for users.
      * This approach aligns with NFR5.1 and ensures user control over their sensitive credentials.

  * **Certificates (SSL/TLS for Web UI - MVP Context):**

      * For the MVP, which is designed primarily for local execution on the user's desktop machine and accessed via `http://localhost:<port>`, the implementation of HTTPS with SSL/TLS certificates for the local YTAP web server is **not a requirement**.
      * If the user chooses to self-host YTAP on a server and access it across a network or expose it in a way that requires HTTPS (a post-MVP consideration), the setup and management of SSL/TLS certificates (e.g., using a reverse proxy like Nginx or Caddy with Let's Encrypt) will be the user's responsibility or part of that specific advanced deployment scenario. YTAP's core application for MVP will not bundle or require direct SSL certificate management.

## Database Migrations

  * **MVP Strategy:** For the YTAP MVP, using SQLite as the metadata store, a formal, automated database migration tool (e.g., Alembic) is considered out of scope due to the anticipated stability of the initial schema and the local nature of the application.
  * **Initial Schema Creation:** The database schema, as defined in the "Data Models \> Database Schemas" section, will be created initially by:
      * Scripts executed upon application startup if the database file doesn't exist.
      * Or, if an ORM like SQLAlchemy is implicitly used with FastAPI (a common pattern, though not explicitly in the tech stack yet), the ORM's schema creation capabilities (e.g., `metadata.create_all()`) will be used.
  * **Schema Changes during MVP Development:**
      * Minor changes to the SQLite schema during the MVP development phase will likely be handled by:
        1.  Updating the schema definition in the code/SQL scripts.
        2.  For development environments, potentially dropping and recreating the database. This is acceptable as long as no critical, persistent user data needs to be preserved between schema changes during early development.
        3.  If minimal data preservation is needed, simple SQL `ALTER TABLE` scripts might be manually applied.
  * **Post-MVP:** If the project evolves to use a more complex database system or if schema changes become frequent and data preservation is critical, a proper database migration tool (e.g., Alembic for Python/SQLAlchemy environments) would be introduced.

## Logging Strategy (Backend - Python)

  * **Library:** The backend (Python/FastAPI) **shall** use Python's built-in `logging` module.
  * **Format:**
      * Logs **should** be structured, preferably in JSON format, for easier parsing and potential future integration with log management systems, even if only outputting to console/file in MVP. Each log entry **must** include at least:
          * Timestamp (ISO 8601 format).
          * Log level (e.g., INFO, ERROR).
          * Logger name (e.g., module path).
          * Log message.
      * A plain text format with similar information is acceptable as a fallback for local console readability if JSON proves cumbersome for direct viewing in MVP.
  * **Log Levels:** Standard Python log levels will be used:
      * `DEBUG`: Detailed information, typically of interest only when diagnosing problems.
      * `INFO`: Confirmation that things are working as expected (e.g., service startup, major operations initiated/completed).
      * `WARNING`: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., 'disk space low'). The software is still working as expected. (Used for API quota warnings, recoverable errors during ingestion).
      * `ERROR`: Due to a more serious problem, the software has not been able to perform some function (e.g., failed ASR, unhandled exception in an API call).
      * `CRITICAL`: A serious error, indicating that the program itself may be unable to continue running.
  * **Output:**
      * For MVP local execution, logs **shall** primarily be written to `stdout` (console).
      * Consider providing a configuration option (e.g., via `.env` or a settings file) to also write logs to a rotating file (e.g., `ytap.log`) in the application's data directory.
  * **Contextual Information:** Where relevant, log messages should include contextual information such as Video ID, Channel ID, or specific parameters related to an operation, ensuring no sensitive data (like API keys) is logged.
  * **Frontend Logging:** Frontend logging will primarily be to the browser's developer console for debugging purposes. No centralized logging from the frontend is planned for MVP.

## Monitoring and Alerting

Given YTAP's MVP nature as a local, self-hosted application:

  * **Monitoring:**
      * **Application Logs:** Primary monitoring will be through direct observation of application console logs (and log files, if implemented) for errors, warnings, and operational status.
      * **API Quota Usage:** The "API Quota Management Service" will provide internal monitoring and status display of YouTube Data API v3 quota usage through the UI.
      * **System Resources:** Basic operating system tools (Task Manager, Activity Monitor, `top`/`htop`) can be used by the user to monitor CPU, memory, and disk usage if performance issues are suspected.
      * **File System:** Users may need to monitor disk space if ingesting a very large number of transcripts and audio files.
  * **Alerting:**
      * No automated alerting system is planned for the local MVP.
      * Alerts will be implicit:
          * User observing error messages or unexpected behavior in the UI.
          * User observing `ERROR` or `CRITICAL` messages in the application logs.
          * The application failing to start or perform core functions.

## Security Architecture (Backend/Overall Focus)

This section complements the "Frontend Security Considerations" in the YTAP Frontend Architecture Document. It focuses on backend and overall application security for the local MVP.

  * **Input Validation & Sanitization (Backend):**
      * All data received by the backend API from the frontend or other sources **MUST** be strictly validated against expected schemas and constraints. If FastAPI is used, Pydantic models will serve this purpose for request bodies and query parameters.
      * Paths for file system operations (e.g., storing transcripts) **MUST** be validated and sanitized to prevent directory traversal attacks or writing to unintended locations. Operations should be restricted to designated base directories.
  * **Secrets Management:**
      * As stated in "Infrastructure and Deployment Overview \> Certificates and Secrets Management", sensitive secrets like the YouTube Data API v3 key **MUST** be managed via environment variables (loaded from `.env` files by the backend) and **MUST NOT** be hardcoded or committed to version control.
  * **API Security (Internal Backend API):**
      * The internal API between the frontend and backend is intended for local communication (`http://localhost:...`) for the MVP and does not implement authentication/authorization. Access is controlled by the user's access to their local machine.
      * If the application were to be self-hosted and exposed to a network, robust authentication (e.g., API keys, JWT) and HTTPS **MUST** be implemented for this API, likely via a reverse proxy.
  * **External API Interactions (Backend to YouTube, etc.):**
      * All calls made by the backend to external services (e.g., YouTube Data API) **MUST** use HTTPS.
  * **Dependency Security (Backend):**
      * Python dependencies **MUST** be regularly scanned for known vulnerabilities (e.g., using `pip-audit` or integrating Snyk/Dependabot alerts with the repository). High/critical vulnerabilities **MUST** be addressed.
  * **File System Operations:**
      * Transcript files should be stored in a designated data directory. Ensure this directory does not have execute permissions if not needed.
      * Be cautious with filenames derived from external sources; sanitize them before use.
  * **Error Handling:**
      * Detailed error messages or stack traces **MUST NOT** be exposed directly to the frontend API responses if they contain sensitive internal information. Generic error messages with logged details server-side are preferred.
  * **Principle of Least Privilege:**
      * While less critical for a local single-user app, if the application were deployed in a shared environment, any processes or service accounts it uses would need to operate with the minimum necessary permissions.

## Disaster Recovery (DR)

For the YTAP MVP, designed as a local/self-hosted application, disaster recovery is primarily the responsibility of the user managing their local environment.

  * **Data Backup:**
      * **Critical Data:** The primary data includes the SQLite database file (containing metadata for channels, videos, categories, etc.) and the stored transcript text files.
      * **User Responsibility:** The user is responsible for regularly backing up these files to a separate storage location (e.g., external hard drive, cloud storage). Standard file backup procedures for their operating system should be followed.
  * **Application Recovery:**
      * **Source Code:** The application source code will be managed in a Git repository. In case of local disk failure, the code can be re-cloned from the remote repository (e.g., GitHub).
      * **Setup:** The application can be re-installed and set up by following the `DEVELOPMENT_SETUP.md` guide (to be created as per Epic 0).
      * **Configuration:** Environment variables (e.g., API keys in `.env`) would need to be restored by the user from their own secure backups/records.
  * **Recovery Time Objective (RTO) / Recovery Point Objective (RPO):**
      * For the MVP, these are not formally defined. RPO depends on the user's backup frequency. RTO depends on the time taken to re-setup the application and restore data.

## Scalability and Performance Design (Backend/Overall Focus)

The YTAP MVP is designed primarily for single-user, local operation. Scalability for multiple concurrent users or extremely large datasets is a post-MVP concern. However, initial design choices promote good performance for the intended use case.

  * **Performance (MVP):**
      * **Efficient API Usage:** The "API Quota Management Service" and strategies like processing only new videos for a channel are designed to minimize YouTube Data API v3 calls and operate cost-effectively.
      * **Backend Framework:** FastAPI is chosen for its high performance.
      * **ASR Processing:** The choice of ASR technology (to be determined) should consider local models if possible, to avoid external API latencies and costs for bulk processing. If ASR is resource-intensive, it may be a background or batch process.
      * **Database Operations:** SQLite is efficient for single-user local access. Database queries will be designed to be efficient. The Repository Pattern helps centralize and optimize data access.
      * **Transcript Storage:** Storing transcripts as individual files is simple and performant for retrieval of individual documents.
  * **Scalability (Post-MVP Considerations):**
      * **Modular Monolith:** The chosen "Modular Monolith" architecture allows for future scalability. If specific components (e.g., ASR processing, data analysis) become bottlenecks or require independent scaling, they can potentially be refactored into separate services.
      * **Database:** For multi-user or larger-scale scenarios, SQLite would likely be replaced with a more robust client-server database (e.g., PostgreSQL).
      * **Task Queues:** CPU-intensive tasks like ASR or bulk data processing could be offloaded to a task queue (e.g., Celery with Redis/RabbitMQ) for asynchronous processing in a scaled-up version.
      * **Stateless Services:** If backend services are designed to be stateless, they are easier to scale horizontally behind a load balancer.

## Developer Onboarding

The primary resource for developer onboarding will be the **`docs/DEVELOPMENT_SETUP.md`** document (to be created as part of Epic 0, Story 0.2). This document will provide comprehensive instructions for setting up the local development environment.

Additional key documents for understanding the project include:

  * This YTAP Architecture Document (`YTAP_Architecture_Doc_v0.1.1.md`)
  * YTAP Product Requirements Document (`YTAP_PRD_v0.1.md`)
  * YTAP UI/UX Specification (`YTAP_UI_UX_Spec_v0.1_draft.md`)
  * YTAP Frontend Architecture Document (`YTAP_Frontend_Architecture_Document_v0.1.md`)

Adherence to coding standards and patterns defined within these documents will be expected.

## Decision Log

*(This section should be maintained throughout the project to track key architectural decisions, alternatives considered, and the rationale behind the final choices.)*

| Date       | Decision                                                                      | Rationale                                                                                                                     | Alternatives Considered          | Stakeholders     |
| :--------- | :---------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------- | :------------------------------- | :--------------- |
| 2025-06-03 | Adopt Modular Monolith architecture with a Monorepo structure.              | Simplicity for MVP, local deployment, clear internal structure, future extensibility. User preference.      | Microservices, Polyrepo          | User, Fred       |
| 2025-06-03 | Tech Stack: Python/FastAPI (Backend), TypeScript/React (Frontend), SQLite.    | Alignment with project needs, performance, developer familiarity, local hosting.                      | Django, Node/Express, PostgreSQL | User, Fred       |
| 2025-06-04 | No user login/authentication for MVP.                                         | Simplifies MVP development significantly for a local, single-user tool.                                                       | User authentication system       | User, Jane, Fred |

## Key Reference Documents

  * YTAP Project Brief (`YTAP_Project_Brief_v1.0.md`)
  * YTAP Product Requirements Document (`YTAP_PRD_v0.1.md`)
  * YTAP Architecture Document (this document, `YTAP_Architecture_Doc_v0.1.1.md`)
  * YTAP UI/UX Specification (`YTAP_UI_UX_Spec_v0.1_draft.md`)
  * YTAP Frontend Architecture Document (`YTAP_Frontend_Architecture_Document_v0.1.md`)
  * `docs/DEVELOPMENT_SETUP.md` (to be created as part of Epic 0)

## Change Log

| Date       | Version | Description                                                                                                | Author           |
| :--------- | :------ | :--------------------------------------------------------------------------------------------------------- | :--------------- |
| 2025-06-03 | 0.1     | Initial draft including Intro, Summary, Overview, Patterns, Components, Project Structure, API Ref, Data Models, Core Workflow, Definitive Tech Stack, Infra/Deployment (Secrets). | Fred (Architect) |
| 2025-06-04 | 0.1.1   | Completed remaining operational sections (DB Migrations, Logging, Monitoring, Security Arch, DR, Scalability, Dev Onboarding, Decision Log, Key Refs, Change Log). Revised due to "no login" decision. | Fred (Architect) |
