# Epic 1: Core Transcript Ingestion, Processing, and Management

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
