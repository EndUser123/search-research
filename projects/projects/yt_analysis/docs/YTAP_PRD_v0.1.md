# YTAP Product Requirements Document (PRD)

**Version:** 0.1 (Initial Draft)
**Date:** 2025-05-26

## 1. Goal, Objective, and Context

**Overall Goal:**
The primary goal of YTAP (YouTube Transcript Analysis Project) is to develop a personalized knowledge and insight engine. This system aims to empower you to become "smarter" by ingesting content from diverse online sources (initially YouTube transcripts) and processing it to identify common foundational knowledge alongside, critically, uncommon or differentiating learnings. By transforming this processed information into **actionable clarity and unique strategic insights**, YTAP seeks to build a curated knowledge base tailored to your specific areas of interest (e.g., Health, Wealth, Fitness, Learning). Ultimately, YTAP will equip you to make more informed decisions, deepen your understanding of various topics, enhance your analytical capabilities, and leverage these insights for tangible personal growth and achieving "above average results".

**Project Objective (for the MVP):**
The immediate objective of this project is to deliver a Minimum Viable Product (MVP) that establishes a **Reliable and Robust YouTube Transcript Ingestion & Management System** and implements **Foundational Content Organization and Basic Utility**, with a strong focus on **cost-effectiveness, particularly regarding API quota management**. This includes reliably downloading YouTube transcripts (with audio-to-text for those without, and handling restricted content), storing them, tracking processing to avoid duplicates, implementing a configurable retry mechanism, allowing categorization by your interests, and providing a basic text exporter. This MVP will serve as the critical first stage in achieving the broader vision by focusing on a dependable and efficient data pipeline and core usability, designed with a 'Modular AI Workflow' in mind.

**Context:**
YTAP is being developed to address the challenge that valuable knowledge is often scattered across numerous online platforms (like YouTube, and potentially X and Reddit in the future) and can be difficult to consume efficiently for deep, personalized learning or to identify truly unique insights. You are seeking a tool to systematically gather, process, and analyze this content to overcome perceived information suppression and to build a personalized knowledge base that supports strategic self-improvement. YTAP will draw upon relevant research, including an "Investigation into Open-Source YouTube Transcript Analysis Projects on GitHub," and learnings from a previous internal project, "YouTube Transcript Downloader," to inform its design and avoid known pitfalls, particularly around API management and data handling. The initial focus is on YouTube as the primary content source for the MVP.

## 2. Functional Requirements (MVP)

**FR1: Reliable YouTube Transcript Ingestion & Management**
* **FR1.1:** The system **shall** allow the user to add, manage, and persist a list of YouTube **channel URLs**.
* **FR1.2:** For each channel URL added, the system **shall** allow the user to associate it with one of your predefined categories (Health, Wealth, Fitness, Learning).
* **FR1.3:** This list of categorized channel URLs **shall** be saved and persist across YTAP sessions.
* **FR1.4:** The system **shall** also allow the user to input individual YouTube video URLs directly for processing.
* **FR1.5:** When processing channels, YTAP **shall** iterate through their videos, respecting other limits like `max-videos-per-channel` (from the Project Brief).
* **FR1.6:** The system **shall** maintain a record of successfully processed videos and **shall not** re-download or re-process their transcripts unless specifically instructed by a future "refresh" or "re-process" command.
* **FR1.7 (Video Metadata Storage):** The system **shall** store, for each processed video, at least the following metadata: `Video ID`, `Video Title`, `Video URL`, `Video Duration` (if readily and cost-effectively available for MVP), `Publication Date`, `Transcript Status` (e.g., downloaded, ASR_generated, failed_download, access_denied, awaiting_processing), `Transcript Source` (e.g., "YouTube direct," "ASR via YTAP"), `YTAP Processing Date`, its `Associated Channel ID`, its `User-Assigned Category`, and `Video View Count` (if readily and cost-effectively available for MVP).
* **FR1.8 (Channel Metadata Storage):** The system **shall** store, for each managed channel, at least the following metadata: `Channel ID`, `Channel Name`, `Channel URL`, its `User-Assigned Category`, its `Upload Playlist ID`, and the `Last Scanned by YTAP Date`.
* **FR1.9 (Transcript Retrieval):** For each targeted video not already successfully processed, the system **shall** first attempt to retrieve any pre-existing, publicly available transcript provided by YouTube.
* **FR1.10 (Audio-to-Text Conversion):** If a pre-existing transcript is unavailable for a targeted video (and ASR is enabled/prioritized), the system **shall** have a mechanism to download the video's audio and perform audio-to-text (ASR) conversion to generate a transcript.
* **FR1.11 (Transcript Storage):** The system **shall** store the final retrieved or ASR-generated transcript as a plain text file (UTF-8 encoded). These files should be stored in a structured manner that allows for easy association with their source video metadata.
* **FR1.12 (Handling Restricted Content):** The system **shall** attempt to process videos that might be member-only or age-restricted, to the extent technically feasible and permissible by YouTube's terms. It **shall** clearly log the outcome of such attempts and update the video's `Transcript Status` metadata accordingly.
* **FR1.13 (Retry Mechanism):** The system **shall** implement a retry mechanism for failed attempts to download video metadata, audio, or transcripts. This mechanism **shall** be configurable by the user, including an on/off toggle and potentially the number of retry attempts.
* **FR1.14 (API Quota Management & Cost-Effectiveness):** The system **shall** track estimated YouTube Data API v3 quota usage. It **shall** be designed to minimize unnecessary API calls by leveraging cached metadata and processing only new videos since the last scan for a channel to operate in a cost-effective manner.
* **FR1.15 (Automated Basic Quality Indicators):** The system **shall** attempt to identify and allow for the visual flagging of ingested transcripts that meet certain predefined basic criteria suggesting potential quality issues (e.g., transcript length below a configurable minimum word/character count, or a high percentage of recognized ASR error markers like '[inaudible]'). Exact criteria will be configurable.
* **FR1.16 (Manual Quality Flagging):** Through the MVP's UI, the system **shall** allow the user to manually apply a simple quality flag (e.g., 'Good', 'Needs Review', 'Poor ASR') or add a short note to individual transcripts.

**FR2: Foundational Content Organization**
* **FR2.1:** The system **shall** allow the user to define and manage a list of personal interest categories (initially Health, Wealth, Fitness, Learning).
* **FR2.2:** The system **shall** enable the user to associate each ingested transcript (or its source channel, as per FR1.2) with one or more of these defined categories.
* **FR2.3:** The system **shall** provide a way for the user to list, view, or retrieve transcripts based on their assigned category or categories.
* **FR2.4:** When a user views a specific category within the MVP UI, the system **shall** display basic summary statistics for that category (e.g., number of associated channels, total number of transcripts it contains) and list the channels assigned to it.

**FR3: Basic Data Utility (Text Exporter)**
* **FR3.1:** The system **shall** provide a mechanism for the user to select one or more ingested transcripts for export.
* **FR3.2:** The selection for export **shall** support choosing individual transcripts and/or all transcripts belonging to a specified category (as defined in FR2.3).
* **FR3.3:** The exported transcripts **shall** be provided in a plain text format (e.g., `.txt` files, UTF-8 encoded), ensuring they are readily usable in external tools or for input into other Large Language Models (LLMs).
* **FR3.4 (Revised):** The content of the exported files for the MVP **shall** be the transcript text as processed and stored by YTAP. The exporter **shall** provide an *optional* mechanism for basic profanity filtering and an *optional* mechanism for basic filler-word removal.
* **FR3.5:** The optional basic profanity filter **shall** operate based on a configurable, predefined list of terms.
* **FR3.6:** The optional basic filler word removal **shall** operate based on a configurable, predefined list of terms.
* **FR3.7:** Comprehensive grammar correction and more advanced text optimization for export are designated as Phase 2 features.

**FR_MVP.Val1 (Input Validation):** The system **shall** perform validation on key user-provided inputs (e.g., format of YouTube channel URLs, paths for export directories). If validation fails, the system **shall** provide clear, user-friendly error messages through the GUI/Web UI, guiding the user to correct the input.

## 3. Non-Functional Requirements (MVP)

**NFR1: Reliability**
* **NFR1.1:** The MVP system **shall** operate with high stability during its core operations (ingestion of YouTube transcripts including ASR, categorization, and export via the GUI/Web UI), minimizing crashes or data corruption under typical usage.
* **NFR1.2:** The configurable retry mechanism (defined in FR1.13) **shall** be effective in recovering from a significant percentage of common transient errors (e.g., temporary network issues) encountered during video/transcript processing.
* **NFR1.3:** Data persistence for channel lists, category assignments, transcript status metadata, and downloaded transcript files **shall** be robust, ensuring no unintended loss of this information between user sessions under normal operating conditions.

**NFR2: Performance & Cost-Effectiveness**
* **NFR2.1:** The system **shall** be optimized to minimize YouTube Data API v3 quota consumption. This will be achieved through efficient caching of previously fetched data, processing only new content by default for existing channels (as per FR1.6, FR1.8, FR1.14), and avoiding unnecessary API calls, directly supporting the primary goal of operating "without extra costs".
* **NFR2.2:** The GUI/Web UI for the MVP **shall** offer responsive interaction for core tasks such as adding/managing channels, assigning categories, initiating processing, viewing status updates, and initiating exports, without causing undue waiting times for the user on a typical personal computer.
* **NFR2.3:** While specific benchmarks are TBD for the MVP, the processing time for an average-sized YouTube channel (e.g., 50-100 videos) **shall** be reasonable and not excessively long, with clear progress indication.

**NFR3: Usability**
* **NFR3.1:** The MVP's primary user interface **shall** be a simple, intuitive, and user-friendly GUI or Web UI, designed to be aesthetically pleasing and prioritizing clarity for core MVP tasks.
* **NFR3.2:** All user inputs through the GUI/Web UI **shall** be validated (as per FR_MVP.Val1), and any errors **shall** be communicated via clear, helpful, and non-technical messages that guide the user towards correction.
* **NFR3.3:** The system **shall** provide clear and timely visual feedback through the GUI/Web UI regarding its current status, the progress of ongoing operations (like downloads or ASR processing), and the outcomes of user actions (e.g., successful export, category assignment).

**NFR4: Maintainability**
* **NFR4.1:** The MVP codebase **shall** be well-organized, adhering to relevant best practices for Python (and JavaScript, if applicable for the UI), and include clear comments for any complex logic. This is to facilitate understanding, future enhancements by yourself or others, and efficient bug fixing, aligning with the preference for "maintainable and no complexity without a reason".
* **NFR4.2:** The system **shall** be designed adhering to the "Modular AI Workflow" guiding principle, ensuring components are loosely coupled where appropriate to support future development, including the potential addition of a CLI or other analytical modules.

**NFR5: Security (MVP Context)**
* **NFR5.1:** Any API keys (e.g., for YouTube Data API v3) or other potentially sensitive configuration data required by YTAP **shall** be managed securely (e.g., through user-managed `.env` files or appropriate secure storage if a different configuration method is chosen) and must not be hardcoded into the application or exposed in standard logs or UI displays.

**NFR6: Scalability (MVP Context)**
* **NFR6.1:** The MVP system **shall** be capable of comfortably managing a personal library consisting of, for example, up to a few dozen actively tracked channels and an accumulation of several thousand video transcripts over time, without significant degradation in the performance of its core MVP functions (ingestion, categorization, basic retrieval/export, and UI responsiveness).

## 4. User Interaction and Design Goals

This section outlines the high-level vision and goals for the User Experience (UX) and design of the YTAP MVP's primary graphical user interface (GUI) or Web UI. It serves as an initial guide for subsequent detailed design work.

* **Overall Vision & Experience:**
    * The UI **shall** strive for a **clean, intuitive, and modern aesthetic** that is straightforward and pleasing to use for the defined MVP tasks.
    * The user experience **shall** feel **reliable and responsive**. The system must provide clear, unambiguous feedback to the user regarding its status, ongoing processes (like ingestion or export), and the results of their actions.
    * While YTAP will manage and present data, the interface should prioritize clarity and ease of understanding over dense, overly technical displays.

* **Key Interaction Paradigms (Conceptual for MVP):**
    * **Simplified Navigation:** A simple and obvious primary navigation structure (e.g., a sidebar or top menu) to access core sections like channel management, categorized content views, and export functionalities.
    * **Form-Based Inputs:** Adding new channels or defining/editing categories will likely utilize simple, clearly labeled forms.
    * **List & Table Displays:** Information such as lists of channels, transcripts within categories, and status reports will be presented in well-organized lists or tables, with basic sorting capabilities where appropriate for MVP (e.g., by channel name, date added).
    * **Direct Action Controls:** Key actions like "Add Channel," "Start Processing," "Assign Category," or "Export Selected" will be triggered by clearly identifiable buttons or controls.
    * **Visual Feedback:** The UI **shall** provide visual cues for system activity, such as progress indicators for downloads or processing, and clear success or error notifications.

* **Core Screens/Views (Conceptual for MVP):**
    * **Channel Management View:** A primary area to list all configured channels, their assigned categories, basic statistics (e.g., number of videos, last scanned date), and controls to add new channels or initiate processing for selected channels.
    * **Category Explorer View:** A view allowing the user to select one of their defined categories (Health, Wealth, etc.) and see a list of associated transcripts, along with basic statistics for that category (e.g., number of items).
    * **Transcript Export View/Modal:** A simple interface enabling the user to select transcripts (perhaps by category or individually from a list) and initiate the basic export process.
    * **(Potential) Basic Settings View:** A minimal area if needed for any MVP-level UI-configurable settings (e.g., managing the API key if not solely .env, toggling the retry mechanism).

* **Accessibility Aspirations (High-Level for MVP):**
    * The UI **shall** aim for basic web accessibility, including readable default font sizes, sufficient color contrast for text and important UI elements, and ensuring essential functions can be navigated using a keyboard.

* **Branding Considerations (High-Level for MVP):**
    * No specific branding (logos, color schemes) is defined for the MVP. The focus will be on a clean, professional, and uncluttered appearance using a standard, modern design palette.

* **Target Devices/Platforms for UI:**
    * The YTAP MVP's GUI/Web UI will be designed and optimized primarily for use on **desktop web browsers**. Responsive design for smaller screens (e.g., tablet, mobile) is not a priority for the MVP.

## 5. Technical Assumptions

This section captures high-level technical guidance, preferences, and existing knowledge to inform the Architect during the system design phase for YTAP.

* **Core Technologies:**
    * The project will primarily utilize **Python** and **JavaScript**.
    * The technology stack of the previous "YouTube Transcript Downloader" project (which included Python, SQLite, `yt-dlp`, `youtube-transcript-api`, and `rich`) should be considered as a relevant reference for foundational components.
    * No other specific preferences for libraries or frameworks (beyond Python/JS) have been stated at this time. Specific choices for UI frameworks (e.g., Streamlit, or a stack like FastAPI/React, as mentioned in the GitHub projects research) and other key libraries will be determined by the Architect, guided by the project's requirements and user preferences for simplicity and maintainability.
    * The user has also expressed a strong interest in **n8n.io** for workflow automation, particularly for data ingestion from multiple sources (YouTube, Reddit, X) and for orchestrating text processing pipelines. The Architect should evaluate the practicality and benefits of incorporating a self-hosted n8n instance for these purposes, starting with its potential role in the MVP's YouTube ingestion or for Phase 2 multi-source ingestion.
    * A long-term goal is to incorporate **Minimal Lossy Text Simplification (MLTS)** to enhance text clarity for analysis. Initial exploration of MLTS, potentially via LLM prompting, could be considered for Phase 2. This would build upon the basic text cleaning options planned for the MVP's exporter.

* **Starter Templates & Other External APIs:**
    * No specific starter project templates have been identified by the user at this stage.
    * Beyond the primary content sources (YouTube, and planned X/Reddit), it is currently unknown if other external APIs will be needed for the MVP's core functionality.

* **Hosting Platforms or Cloud Services:**
    * There is a strong user preference **not to utilize managed hosting or cloud platform services** for YTAP. The system, including any GUI/Web UI components, should therefore be designed to run locally or be self-hostable. Specific deployment considerations adhering to this preference will be determined during the architectural design phase.

* **Repository & Service Architecture:**
    * **Repository Structure:** An initial preference has been expressed for a **Monorepo** structure, with the thought that it might be easier to manage for this project. This will be a key consideration for the Architect, who will make a final recommendation based on best practices and project requirements.
    * **High-Level Service Architecture:** While no specific service architecture (e.g., Monolith, Microservices, Serverless) is prescribed at this stage, the overriding design principle **must** be to create a system that is **simple, modular, and maintainable**. This aligns with and reinforces the "Modular AI Workflow" guiding principle established for YTAP. The Architect will propose an architecture that embodies these qualities.

## 6. Epic Overview

**Epic 1: Core Transcript Ingestion, Processing, and Management**
* **Goal:** To establish a reliable and robust system for ingesting YouTube video content (including transcript fetching, audio-to-text conversion for videos without transcripts, handling restricted content), processing it, storing the transcripts and associated metadata, and implementing essential operational features like a configurable retry mechanism, basic quality indicators, and API quota management. This epic forms the foundational data pipeline for YTAP.
* **User Stories:**
    * **Story 1.1: Manage and Categorize Source YouTube Channels**
        * **Story:** As the primary user of YTAP, I want to be able to add, view, categorize, and save a list of YouTube channel URLs so that YTAP has a persistent and organized set of sources to process for transcript ingestion according to my defined interests.
        * **Acceptance Criteria (ACs):**
            1.  Through the YTAP GUI/Web UI, I can add a new YouTube channel by providing its URL.
            2.  When adding a channel, I can associate it with one or more of my predefined personal interest categories (initially Health, Wealth, Fitness, Learning).
            3.  The system performs basic validation on the format of the entered YouTube channel URL and provides clear feedback via the UI if the format appears invalid.
            4.  Added channels, along with their assigned categories and the date they were added to YTAP, are saved and persist across YTAP sessions.
            5.  Through the UI, I can view a list of all saved channels, displaying their URL, assigned categories, and any basic channel metadata that YTAP stores upon adding (e.g., Channel Name, if fetched, and date added).
            6.  Through the UI, I can remove a channel from the saved list.
            7.  *(Consider for MVP or early follow-up):* Through the UI, I can edit the categories associated with an already saved channel.
    * **Story 1.2: Discover Videos and Fetch Metadata from Channels**
        * **Story:** As the primary user of YTAP, I want the system to scan my saved YouTube channels for videos, retrieve and store essential metadata for any new videos found since the last scan, so that YTAP has an up-to-date inventory of videos to consider for transcript processing, while efficiently managing API quota.
        * **Acceptance Criteria (ACs):**
            1.  When channel processing is initiated (e.g., via the GUI/Web UI), YTAP uses the YouTube Data API v3 to list videos from the specified channel(s) (likely via their `Upload Playlist ID`).
            2.  For each channel, the system primarily fetches metadata only for videos published *since* the channel's "Last Scanned by YTAP Date" to identify new content and minimize API calls.
            3.  The system respects the `max-videos-per-channel` configuration when fetching new videos from a channel during a single processing run.
            4.  For each new video identified that hasn't been successfully processed before, the system retrieves and stores its essential metadata. This includes at least: `Video ID`, `Video Title`, `Video URL`, `Publication Date`, and where readily and cost-effectively available for MVP, `Video Duration` and `Video View Count`.
            5.  The system updates the "Last Scanned by YTAP Date" for the channel in its metadata store upon successful completion of the video discovery scan for that channel.
            6.  The system accurately tracks estimated YouTube Data API v3 quota usage during this metadata fetching process.
            7.  If the API response for a video during metadata retrieval indicates it might be restricted (e.g., private, deleted, requiring login, age-restricted), this initial status is noted in the video's metadata record.
            8.  The user receives feedback via the UI regarding the video discovery process (e.g., "Scanning channel X...", "Found Y new videos for channel X").
    * **Story 1.3: Acquire and Store Video Transcripts**
        * **Story:** As the primary user of YTAP, I want the system to attempt to retrieve or generate a transcript for each newly identified and pending video, and then store this transcript, so that the textual content of the videos is captured and available for my review and subsequent YTAP features.
        * **Acceptance Criteria (ACs):**
            1.  For each video identified in Story 1.2 as needing transcript processing, YTAP **shall** first attempt to download any pre-existing, publicly available transcript (e.g., using the YouTube Transcript API).
            2.  If a pre-existing transcript is successfully downloaded:
                a.  It **shall** be stored as a plain text file in the designated structured storage.
                b.  The video's metadata record **shall** be updated with a status like 'transcript_downloaded_direct' and the `Transcript Source` set to 'YouTube_direct'.
            3.  If a pre-existing transcript is *not* found or cannot be downloaded (and ASR is enabled for the MVP), the video **shall** be queued for Audio-to-Text (ASR) conversion.
            4.  The ASR process **shall** involve downloading the audio of the video, converting the audio to text, and then storing the resulting text as a transcript file.
            5.  If ASR processing is successful:
                a.  The generated transcript **shall** be stored as a plain text file.
                b.  The video's metadata record **shall** be updated with a status like 'transcript_ASR_completed' and the `Transcript Source` set to 'ASR_YTAP'.
            6.  The system **shall** handle errors encountered during transcript download attempts or ASR processing (e.g., video becomes unavailable, ASR service failure, content is for members-only and cannot be accessed). Such errors will be logged, and the video's status in the metadata will be updated accordingly (e.g., 'transcript_download_failed', 'ASR_failed', 'access_denied').
            7.  The configurable retry mechanism (defined in FR1.13) **shall** be applied to eligible download or ASR processing failures.
            8.  The system **shall** attempt to identify basic quality indicators for the acquired transcript (e.g., very short length, high ratio of ASR error markers if detectable) and make these indicators visible or flaggable in the UI.
            9.  The user **shall** be able to see the updated status of transcript acquisition for each video via the GUI/Web UI (e.g., 'downloading', 'ASR in progress', 'completed', 'failed').
    * **Story 1.4: View Operational Status and API Quota**
        * **Story:** As the primary user of YTAP, I want to be able to easily view the overall operational status of my YTAP system, including the processing progress for my channels and videos, and the current YouTube Data API v3 quota usage, so that I can understand what YTAP is doing, monitor its resource consumption, and be aware of any potential issues or limitations.
        * **Acceptance Criteria (ACs):**
            1.  The YTAP GUI/Web UI **shall** provide a main dashboard or overview section displaying a summary of managed channels.
            2.  For each managed channel listed, the UI **shall** display key status information, such as its name, assigned category, total videos known to YTAP, number of videos successfully processed (transcript acquired), number of videos pending processing, and number of videos that encountered errors.
            3.  The UI **shall** allow me to drill down (or view details for) a specific channel to see a list of its associated videos and their individual transcript processing statuses (e.g., 'pending_download', 'metadata_fetched', 'ASR_in_progress', 'transcript_complete', 'download_failed', 'restricted_content', 'quality_flagged').
            4.  If batch processing is active, the UI **shall** provide a clear indication of overall progress (e.g., "Processing X of Y videos/channels").
            5.  The YTAP GUI/Web UI **shall** display the current estimated YouTube Data API v3 quota status, including (if available from the API tracking mechanism) metrics like quota points used today, quota points remaining, and when the quota is expected to reset.
            6.  The UI **shall** clearly indicate the current state (enabled/disabled) of the configurable retry mechanism.
            7.  The UI **shall** provide easy access to view logs or a summary of critical errors if they occur during processing.
    * **Story 1.5: Process a Directly Provided Individual Video URL**
        * **Story:** As the primary user of YTAP, I want to be able to submit a single YouTube video URL directly through the UI for immediate transcript processing and categorization, so I can quickly ingest specific videos of interest that are not part of my regularly monitored channels.
        * **Acceptance Criteria (ACs):**
            1.  The YTAP GUI/Web UI provides a clear option to submit an individual YouTube video URL.
            2.  Upon submission, the system validates the URL format.
            3.  The system processes the individual video through the same pipeline as channel videos: metadata fetching, transcript acquisition (direct or ASR), storage, and status updates.
            4.  I can associate the individually processed video with one or more of my predefined categories.
            5.  The processed video and its transcript appear in the relevant category views and are available for export.
    * **Story 1.6: Manually Apply Quality Flags to Transcripts**
        * **Story:** As the primary user of YTAP, after reviewing an ingested transcript via the UI, I want to be able to manually apply a quality flag (e.g., 'Good', 'Needs Review', 'Poor ASR') and optionally add a short note, so I can record my personal assessment of the transcript's quality for future reference and filtering.
        * **Acceptance Criteria (ACs):**
            1.  When viewing a transcript or its metadata in the UI, an option is available to apply/edit a manual quality flag.
            2.  The system provides a predefined, editable list of quality flag options (e.g., 'Good', 'Needs Review', 'Poor ASR', 'Excellent').
            3.  The system allows me to add a short text note associated with the quality flag for a specific transcript.
            4.  The applied quality flag and note are saved with the video's metadata and are visible when viewing the transcript or its details.
            5.  *(Phase 2 consideration):* The system should allow filtering or searching based on these manual quality flags in the future.

**Epic 2: Foundational Content Organization & Basic Export Utility**
* **Goal:** To enable the user to organize the ingested transcripts using personal interest categories (initially Health, Wealth, Fitness, Learning), view basic statistics about these categories, and export the raw or lightly cleaned transcript data for external use, all through a simple, user-friendly GUI/Web UI. This epic focuses on making the collected data manageable and useful.
* **User Stories:**
    * **Story 2.1: Manage Personal Interest Categories**
        * **Story:** As the primary user of YTAP, I want to define and manage my personal interest categories (e.g., Health, Wealth, Fitness, Learning) via the UI, so that I have a flexible system for organizing all ingested content according to my needs.
        * *(Key ACs would cover: UI to create new categories, view existing categories, potentially edit/delete categories; initial categories are pre-defined or easily added; changes are persisted [derived from FR2.1]).*
    * **Story 2.2: Associate Content with Categories**
        * **Story:** As the primary user of YTAP, I want to easily associate ingested transcripts (either at the channel level during setup or for individual transcripts later) with one or more of my defined interest categories through the UI, so that my content library is accurately organized.
        * *(Key ACs would cover: UI mechanisms for assigning/changing category tags for channels and/or individual transcripts; associations are saved [derived from FR1.2, FR2.2]).*
    * **Story 2.3: View and Navigate Content by Category**
        * **Story:** As the primary user of YTAP, I want to be able to view my ingested transcripts grouped or filtered by my defined categories within the UI, and see basic summary statistics for each category, so I can easily navigate, access, and understand the scope of my curated content library.
        * *(Key ACs would cover: UI displays list of categories; selecting a category shows associated transcripts; basic stats like channel count and transcript count per category are displayed [derived from FR2.3, FR2.4]).*
    * **Story 2.4: Export Transcripts**
        * **Story:** As the primary user of YTAP, I want to select one or more transcripts (either individually or by category) via the UI and export them as plain text files, so that I can easily use this data with external tools, for offline review, or input into other LLMs.
        * *(Key ACs would cover: UI for selecting individual transcripts or all transcripts in a category for export; files exported in .txt format, UTF-8 encoded; output is the raw/ingested transcript text by default [derived from FR3.1, FR3.2, FR3.3, FR3.4]).*
    * **Story 2.5: Apply Optional Basic Cleaning During Export**
        * **Story:** As the primary user of YTAP, when exporting transcripts, I want the option via the UI to apply basic profanity filtering and/or basic filler word removal, so that the exported text can be cleaner and potentially more optimized for token usage in external LLM applications.
        * *(Key ACs would cover: UI provides clear options/toggles to enable/disable profanity filter and filler word removal before export; filters use configurable, predefined lists; if enabled, exported text reflects these changes, otherwise raw text is exported; comprehensive grammar correction is explicitly out of scope for this feature [derived from FR3.4 (Revised), FR3.5, FR3.6, FR3.7]).*

## 7. Key Reference Documents
* **YTAP Project Brief (Version 1.0, dated 2025-05-24):** The foundational document you created with Mary, our Analyst, which outlines the initial project vision, goals, scope, target audience, and context that informed this PRD.
* **YTAP Product Requirements Document (this document, current Version 0.1 - Draft):** This PRD, which we are currently developing, detailing the functional requirements, non-functional requirements, user interaction goals, technical assumptions, and epic/story breakdown for the MVP and beyond.
*(Future documents like Architecture Document, UI/UX Specification will be added here).*

## 8. Out of Scope Ideas Post MVP

The following features and capabilities, while part of the broader vision for YTAP, are considered out of scope for the initial Minimum Viable Product (MVP) and are planned for subsequent development phases:

**Targeted for Phase 2 (Immediately following the MVP):**
* **Expanded Content Ingestion:**
    * Integrating content from other platforms such as **X (formerly Twitter) and Reddit**.
    * Integration and expansion of **n8n.io** for advanced workflow automation and multi-source data ingestion.
* **Core Analytical Capabilities:**
    * Developing a **Common Pattern Analyzer**.
    * Implementing the **Uncommon Insight Detector / Outlier Detection** feature.
    * Adding a **Comparative Analysis Engine**.
    * Creating an initial version of a **"Why it Works" Extractor**.
    * Incorporating a **Sentiment/Popularity Tracker**.
    * Beginning development of an **Actionable Synthesis Module** (initial version).
    * Implementation of **Minimal Lossy Text Simplification (MLTS)** - initial version (potentially via LLM prompting).
* **Enhanced User Interaction & Utility:**
    * Building a **Personalized Query Interface** for more advanced questioning.
    * Adding **Keyword Identification** for transcripts.
    * Implementing support for **Hierarchical Grouping** in content organization.
    * Enhancing the **Text Exporter** with features like light editing (e.g., removing profanity, redundant words) to optimize token usage for external LLMs.
    * Developing a **Command-Line Interface (CLI)** as an alternative way to interact with YTAP.
    * **Semantic Search capability (potentially using Vector RAG)**.

**Targeted for Future (Longer-term, more ambitious capabilities):**
* **Advanced Content Ingestion:**
    * Integrating **Deep Research Results** from Markdown files or other structured text sources.
* **Sophisticated Analysis & Synthesis:**
    * Developing an advanced **Evidence Ranker/Validator**.
    * Creating a more advanced and nuanced **Actionable Synthesis Module**.
    * Further enhancements to all Phase 2 analytical capabilities.
    * Advanced **Minimal Lossy Text Simplification (MLTS)** capabilities / Dedicated MLTS model integration.
* **Comprehensive Grammar Correction** for the Text Exporter.

## 9. Change Log
| Change        | Date       | Version              | Description                                         | Author         |
|---------------|------------|----------------------|-----------------------------------------------------|----------------|
| Initial Draft | 2025-05-26 | 0.1 (PRD Sections 1-9) | First draft of PRD sections 1 through 9 completed. | John (PM) / User |

---
## Prompt for Design Architect (UI/UX Specification Mode)

**Objective:** To develop a detailed UI/UX Specification for the YTAP MVP, which will feature a simple, user-friendly GUI or Web UI as its primary interface, designed for a desktop web browser environment.
**Mode:** UI/UX Specification Mode
**Input:** This completed YTAP Product Requirements Document (PRD Version 0.1), paying close attention to Section 2 (Functional Requirements for MVP), Section 3 (Non-Functional Requirements, especially NFR3: Usability), and Section 4 (User Interaction and Design Goals).
**Key Tasks for Design Architect (Jane):**
1.  Review the YTAP PRD, particularly the MVP goals (e.g., reliable ingestion, categorization, export), the user interactions implied by the Functional Requirements (e.g., adding channels, viewing category stats, selecting for export), and the high-level "User Interaction and Design Goals" (Section 4 of this PRD).
2.  Collaboratively define detailed user flows for the MVP features, ensuring they are intuitive and align with the "simple, user-friendly" NFR.
3.  Develop wireframes (low-fidelity) or mockups (conceptual) for the core screens/views identified (e.g., Channel Management View, Category Explorer View, Transcript Export View/Modal, and any potential Basic Settings View).
4.  Specify detailed usability requirements and ensure basic web accessibility principles (as noted in Section 4 of this PRD) are incorporated into the design concepts.
5.  Populate or create a `front-end-spec-tmpl.txt` (or equivalent UI/UX Specification document) detailing these designs, flows, and interaction patterns.
6.  Ensure this PRD is updated with a reference to the completed UI/UX Specification, or that key UI/UX decisions are integrated back if appropriate, to provide a comprehensive foundation for Fred (Architect) and subsequent development.
Please guide the user through this process to detail the UI/UX for the YTAP MVP, keeping in mind their preference for "something pretty, but it must always work".

---
## Initial Architect Prompt

Based on the YTAP Product Requirements Document (PRD v0.1), particularly the defined MVP scope (Functional Requirements Section 2, Non-Functional Requirements Section 3, User Interaction Goals Section 4, and Technical Assumptions Section 5), the following technical guidance and constraints are provided to kickstart the architecture design process for YTAP:

### Technical Infrastructure

* **Repository & Service Architecture Decision:** An initial user preference is for a **Monorepo**. The service architecture **must** be **simple, modular, and maintainable**, aligning with the "Modular AI Workflow" guiding principle established for YTAP. The MVP includes a GUI/Web UI as the primary interface.
* **Starter Project/Template:** None specified by the user. Architect to recommend if an appropriate one exists that aligns with other technical preferences.
* **Hosting/Cloud Provider:** There is a strong user preference **not to utilize managed hosting or cloud platform services**. YTAP, including its GUI/Web UI, should be designed to run locally or be self-hostable.
* **Frontend Platform:** The MVP requires a **simple, user-friendly GUI or Web UI designed for desktop web browsers**. The Design Architect (Jane) will further detail UI/UX specifications. Preferred technologies include JavaScript. Architect to propose specific frameworks in consultation with Design Architect, keeping simplicity and maintainability in mind.
* **Backend Platform:** The primary preferred language is **Python**. Specific frameworks are to be determined by the Architect, focusing on simplicity, maintainability, support for the defined functional requirements (including ASR capabilities), and adherence to NFRs (Section 3).
* **Database Requirements:**
    * The system needs to persist: a list of categorized YouTube channels (including channel ID, name, URL, category, upload playlist ID, last scanned date); video metadata (video ID, title, URL, duration, pub date, transcript status, source, processing date, view count, associated channel, category); and potentially manual quality flags/notes per transcript.
    * Transcripts themselves will be stored as plain text files.
    * SQLite was used for metadata in a previous similar project and can be considered for its simplicity and local nature, aligning with the "no hosting services" preference. Architect to confirm suitability or propose alternatives.

### Technical Constraints & Key MVP Functionality
* Must adhere to all defined Functional Requirements (FRs) for the MVP.
* The architecture must enable adherence to all defined Non-Functional Requirements (NFRs), especially NFR1 (Reliability), NFR2 (Performance & Cost-Effectiveness - particularly minimizing YouTube API quota usage), NFR3 (Usability of the GUI/Web UI), and NFR4 (Maintainability).
* The system must support audio-to-text (ASR) conversion for videos without pre-existing transcripts (MVP requirement). Architect to propose or evaluate ASR technology options considering local execution preference.
* A configurable retry mechanism for failed ingestion tasks is required for MVP.
* Basic automated and manual quality flagging for transcripts is part of MVP.
* A basic text exporter with optional simple cleaning (profanity, filler words) is required for MVP.
* Input validation for user-provided data via the UI is required.

### Deployment Considerations
* Deployment strategy must align with the "no managed hosting/cloud services" preference. Focus should be on ease of local setup and operation for a technical user, or straightforward self-hosting of any web components.
* Consider packaging or distribution for a desktop application environment if appropriate for the chosen UI technology.

### Local Development & Testing Requirements
* The system must be easily runnable and testable in a local development environment for all its components.
* Architect to propose suitable testing strategies (unit, integration, potentially E2E for UI) aligning with chosen technologies and the need for reliability.

### Other Technical Considerations
* The "Modular AI Workflow" is a critical guiding principle. The architecture should enable YTAP to function as a component in a larger analytical workflow, potentially integrating with or exporting data to other tools in a flexible manner.
* Leverage insights, lessons learned, and potentially reusable patterns from the previous "YouTube Transcript Downloader" project documentation (referenced in YTAP PRD Section 7) where applicable, particularly regarding API interaction, caching, and error handling.
* The primary user has a technical background.
* **Workflow Automation & Advanced Text Processing:** The user is highly interested in **n8n.io** for workflow automation, especially for multi-source data ingestion (Phase 2+) and orchestrating processing tasks. The Architect should evaluate its suitability for YTAP, considering a self-hosted deployment model and its potential role even in aspects of the MVP's YouTube ingestion if beneficial. Additionally, the architecture should eventually support advanced text pre-processing capabilities like **Minimal Lossy Text Simplification (MLTS)** (targeted for Phase 2, potentially via LLM prompting initially) to improve input quality for downstream analytical functions.
* **Future RAG Support:** The Architect should consider data storage and organization strategies that could facilitate the future implementation of semantic search capabilities, potentially using Retrieval Augmented Generation (RAG) techniques (a Phase 2/Future goal).
