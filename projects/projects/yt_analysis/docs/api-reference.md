# API Reference

This section details the external Application Programming Interfaces (APIs) that YTAP will consume and any internal APIs it will provide to facilitate communication between its components.

## External APIs Consumed

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
    2. To download the audio track of YouTube videos when Audio-to-Text (ASR) conversion is necessary.
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

## Internal APIs Provided (If Applicable)

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
