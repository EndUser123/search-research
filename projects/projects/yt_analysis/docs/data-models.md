# Data Models

This section defines the structure of the key data entities that YTAP will manage, how data might be structured for API payloads (if distinct from core entities), and the schemas for persistent data storage.

## Core Application Entities / Domain Objects

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

## API Payload Schemas (If distinct)

For the YTAP MVP, the data structures used in API payloads for the internal API (between the frontend UI and the backend core engine) are expected to closely mirror the definitions of the "Core Application Entities / Domain Objects" detailed above.

Specific request and response schemas for each API endpoint will be defined as part of the detailed API design process. At this stage, no complex, reusable payload structures that significantly diverge from the core entity definitions are anticipated for the MVP. This section can be expanded in the future if such distinct payload schemas become necessary.

## Database Schemas (If applicable)

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
