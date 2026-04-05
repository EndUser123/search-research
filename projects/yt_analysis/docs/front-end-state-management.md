# Frontend State Management In-Depth

This document expands on the State Management strategy for the YTAP frontend, as outlined in the YTAP Frontend Architecture Document. The primary goal for the MVP is to start simple and introduce more complexity only as needed.

## Chosen Solution

* We will primarily use **React Context API** combined with React Hooks (e.g., `useState`, `useReducer`) for managing state within the application.
* Should our state management needs grow significantly in complexity, we will consider introducing a **lightweight global state library like Zustand or Jotai**. This approach allows us to maintain simplicity for the MVP while having a clear path for evolution.

## Decision Guide for State Location

To ensure consistency and maintainability, we'll follow these guidelines for determining where state should reside:

* **Global State (React Context API / Future: Zustand/Jotai):**
    * Use for data that needs to be accessed by many unrelated components across different parts of the application (e.g., API quota information, application-wide settings or notifications).
    * Suitable for state that persists across routes or user sessions (though persistence itself might involve `localStorage` or other mechanisms accessed via the state).
    * If using `useReducer` with Context, it's good for managing complex state logic that involves multiple sub-values or transitions.
    * **MUST be used for:** Global application settings, UI theme preferences (if any), and application-wide notification states.
* **React Context API (for component subtrees):**
    * Use for state that needs to be shared down a specific branch of the component tree, but isn't truly global (e.g., state within a complex multi-step form, theme overrides for a specific section).
    * Helps avoid excessive "prop drilling."
    * **MUST be used for:** Localized shared state not suitable for prop drilling but not needed globally.
* **Local Component State (`useState`, `useReducer`):**
    * This is the **default choice** for state that is only relevant to a single component or a component and its direct children.
    * Examples: UI-specific state like form input values, open/close status of a dropdown, loading state for a specific component's data.
    * **MUST be the default choice** unless the criteria for Context API (subtree or global) are clearly met.

## Store Structure / Context Organization

With Context API, we'll organize global state by creating dedicated contexts for different domains of global data. Each context will typically have a Provider component and custom hooks for accessing its state and dispatching actions.

* **Convention:** Global contexts should be defined in `src/store/contexts/` (or potentially `src/store/` if we adopt Zustand/Jotai later and use a single store with slices). Feature-specific contexts might reside in `src/features/[featureName]/contexts/`.

* **Core Context Example: `AppContext` (e.g., in `src/store/contexts/AppContext.tsx`)**
    * **Purpose:** Manages general application state, such as global notifications or shared UI settings (e.g., API Quota status if displayed globally).
    * **State Shape (Interface/Type):**
        ```typescript
        interface AppState {
          // Example: API Quota status if displayed globally
          apiQuotaStatus?: { used: number; limit: number; resets: string };
          // Example: Global notifications
          notifications: Array<{ id: string; message: string; type: 'info' | 'error' | 'success' }>;
          // Other global UI settings or preferences if needed
        }

        interface AppContextType extends AppState {
          // Functions to update app state, e.g., addNotification, clearNotification
          addNotification: (notification: { message: string; type: 'info' | 'error' | 'success' }) => void;
          clearNotification: (id: string) => void;
          // Potentially functions to update API quota display if driven from frontend actions
          setApiQuotaStatus: (status: AppState['apiQuotaStatus']) => void;
        }
        ```
    * **Implementation:** Likely uses `useReducer` internally for state transitions and provides functions like `addNotification` that dispatch actions to the reducer.
    * **Custom Hooks (for consuming the context):**
        * `useAppState()`: Returns the current `AppState`.
        * `useAppActions()`: Returns the action functions like `addNotification`. (Or combine into a single `useAppContext()` hook).

* **Feature Context Template (e.g., `{featureName}Context` in `src/features/{featureName}/contexts/{FeatureName}Context.tsx`)**
    * **Purpose:** {To be filled out when a new feature requires its own shared state accessible within that feature's component tree.}
    * **State Shape (Interface/Type):** {To be defined by the feature.}
    * **Implementation:** {Likely `useReducer` or `useState` within the context provider.}
    * **Custom Hooks:** {e.g., `useFeatureNameState`, `useFeatureNameActions`.}

## Key Selectors (Custom Hooks for Context)

With React Context, "selectors" are effectively custom hooks that consume a context and return a specific piece of state, often memoized with `useMemo` if deriving data to prevent unnecessary re-renders.

* **`useApiQuotaStatus()` (from `AppContext`):** Returns the `apiQuotaStatus` object or `undefined`.
* **`useNotifications()` (from `AppContext`):** Returns the array of `notifications`.

## Key Actions / Reducers / Thunks (Functions within Context)

For Context API combined with `useReducer`, actions are objects dispatched to the reducer. Async operations ("thunks") are typically functions defined within the context provider (or as standalone service functions called by the context) that perform API calls and then dispatch actions to the reducer based on the outcome.

* **Core Action/Async Function Example: `fetchAndSetApiQuota()` (exposed via `AppContext`)**
    * **Purpose:** Fetches API quota status from the backend and updates the `AppContext`.
    * **Parameters:** None.
    * **Logic Flow (conceptual, within the context provider or a function it calls):**
        1.  Dispatch an action to set a loading state for quota if desired.
        2.  Call an appropriate service function (e.g., `settingsService.getApiQuotaStatus()` from `src/services/`).
        3.  On success:
            * Dispatch an action to set `apiQuotaStatus` in the `AppState`.
        4.  On error:
            * Dispatch an action to handle the error (e.g., set `apiQuotaStatus` to an error state or show a notification via `addNotification`).
* **Feature Action/Async Function Template: `{featureActionName}` (exposed via `{FeatureName}Context`)**
    * **Purpose:** {To be filled out for feature-specific async operations impacting shared feature state.}
    * **Parameters:** {Define specific parameters with types.}
    * **Logic Flow:** {To be defined by the feature, following similar patterns for API calls and dispatching actions to its local reducer.}
