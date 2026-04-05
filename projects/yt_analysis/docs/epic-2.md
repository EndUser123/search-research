# Epic 2: Foundational Content Organization & Basic Export Utility

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
