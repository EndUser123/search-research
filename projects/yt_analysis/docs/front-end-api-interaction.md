# Frontend API Interaction Layer

This section describes how the YTAP frontend will communicate with the YTAP Backend API, as defined in the main YTAP Architecture Document. Our goal is to create a robust, maintainable, and easy-to-use layer for all backend interactions, as detailed in the YTAP Frontend Architecture Document.

## Client/Service Structure

* **HTTP Client Setup:**
    * We will use a dedicated HTTP client library, likely **Axios**, to manage all API requests. An instance of Axios will be configured centrally, for example, in `src/services/apiClient.ts`.
    * **Configuration MUST include:**
        * **Base URL:** Loaded from an environment variable (e.g., `process.env.NEXT_PUBLIC_API_URL` or `import.meta.env.VITE_API_URL`), which would point to the conceptual `http://localhost:PORT/api/v1/` defined in the main architecture document.
        * **Default Headers:** Such as `Content-Type: 'application/json'`.
        * **Interceptors:**
            * **Response Interceptor:** For standardized global error handling and potentially for normalizing API responses if needed. (Auth token injection previously mentioned here is removed due to no login for MVP).
    * Timeout configurations (connect and read timeouts) should also be considered for this central client.

* **Service Definitions:**
    * API interactions will be encapsulated within service modules, typically organized by resource or feature. For example:
        * `src/services/channelService.ts`: Handles CRUD operations for channels, fetching channel lists, etc.
        * `src/services/transcriptService.ts`: Handles operations related to fetching transcript status, initiating processing, etc.
        * `src/services/exportService.ts`: Handles transcript export requests.
    * **Each service function MUST:**
        * Have explicit TypeScript parameter types and a clear return type (e.g., `Promise<Channel[]>`, `Promise<VideoMetadata>`).
        * Include JSDoc/TSDoc comments explaining its purpose, parameters, return value, and any specific error handling expectations.
        * Use the configured Axios instance (`apiClient`) to make the actual HTTP requests to the correct endpoints with appropriate methods and payloads, as defined in the YTAP Backend API specification.
    * **Example (`src/services/channelService.ts`):**
        ```typescript
        import apiClient from './apiClient';
        import { Channel, ChannelCreateDto } from '@/types'; // Assuming types are defined

        /**
         * Fetches all managed channels.
         * @returns A promise that resolves to an array of Channel objects.
         */
        export const getChannels = async (): Promise<Channel[]> => {
          const response = await apiClient.get<Channel[]>('/channels');
          return response.data;
        };

        /**
         * Adds a new channel.
         * @param channelData - The data for the new channel.
         * @returns A promise that resolves to the newly created Channel object.
         */
        export const addChannel = async (channelData: ChannelCreateDto): Promise<Channel> => {
          const response = await apiClient.post<Channel>('/channels', channelData);
          return response.data;
        };
        // ... other channel-related API functions
        ```

## Error Handling & Retries (Frontend)

* **Global Error Handling:**
    * The Axios response interceptor (in `apiClient.ts`) will be the primary point for global API error handling.
    * It should inspect responses for error statuses (e.g., 4xx, 5xx).
    * For common errors (e.g., 403 Forbidden, 500 Internal Server Error), it can dispatch an action to a global UI context/slice (e.g., `AppContext`'s `addNotification` function) to display a user-friendly error message or log detailed error information. (Handling for 401 Unauthorized by redirecting to login is no longer applicable for MVP).
* **Specific Error Handling:**
    * Individual components or service calls **MAY** implement more specific error handling logic if needed (e.g., displaying inline validation messages from the backend). This should be documented in the component's specification.
* **Retry Logic:**
    * Client-side retry logic (e.g., using `axios-retry` with `apiClient`) can be implemented for failed API requests to improve resilience.
    * **Configuration MUST specify:** Max retries, retry conditions (e.g., network errors, specific idempotent 5xx errors), and retry delay (e.g., exponential backoff).
    * Retry logic **MUST** only be applied to idempotent requests (e.g., GET, PUT, DELETE).
