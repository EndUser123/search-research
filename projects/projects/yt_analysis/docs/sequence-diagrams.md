# Core Workflow / Sequence Diagrams

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

```mermaid
sequenceDiagram
    actor User
    participant UI as YTAP UI (GUI/Web App)
    participant Backend as Backend Core Engine
    participant ChanVidService as Channel & Video Metadata Service
    participant ExtYouTubeAPI as YouTube Data API v3
    participant Persistence as Data Persistence Layer


    User->>+UI: 1. Navigate to Channels Mgt & Click "+ Add Channel"
    UI-->>User: 2. Display "Add Channel" form (URL, Categories)
    User->>+UI: 3. Enter Channel URL & Categories, Submit form
    UI->>+Backend: 4. API Request: POST /api/v1/channels (Channel URL, Categories)
    Backend->>+ChanVidService: 5a. processAddChannelRequest(data)
    ChanVidService->>ChanVidService: 5b. Validate input (URL format, categories)

    alt Input Invalid
        ChanVidService-->>Backend: Validation Error
        Backend-->>UI: Error Response (e.g., 400 Bad Request)
        UI-->>User: Display validation error message
    else Input Valid
        opt Fetch Initial Channel Details from YouTube
            ChanVidService->>+ExtYouTubeAPI: 5c. GET /channels (to get official Channel Name/ID)
            ExtYouTubeAPI-->>ChanVidService: Channel Details (Name, ID)
        end

        ChanVidService->>+Persistence: 5d. Save New Channel(ChannelInfo, Categories, DateAdded)
        Persistence-->>ChanVidService: Confirm Save

        ChanVidService-->>Backend: 6a. Channel Added Successfully (with details)
        Backend-->>UI: 6b. Success Response (e.g., 201 Created, full Channel Details)
        UI-->>User: 7. Display "Channel Added" success message & Update Channel List in UI
    end
