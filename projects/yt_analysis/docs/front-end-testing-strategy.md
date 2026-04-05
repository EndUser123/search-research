# Frontend Testing Strategy

This section elaborates on the "Overall Testing Strategy" from the main YTAP Architecture Document, focusing on frontend-specific aspects for YTAP, as detailed in the YTAP Frontend Architecture Document.

* **Link to Main Overall Testing Strategy:** Please refer to the main `YTAP_Architecture_Doc_v0.1.1.md` for the overarching testing principles and tool selections (such as Jest, React Testing Library, and Playwright).

## Component Testing

* **Scope:** Testing individual UI components in isolation. This includes validating their rendering with various props, interactions, and basic state changes.
* **Tools:** We will use **Jest** as the test runner and **React Testing Library (RTL)** for rendering components and simulating user interactions.
* **Focus:**
    * Correct rendering with different sets of props.
    * User interactions (e.g., clicks, input changes) using RTL's `userEvent` or `fireEvent`.
    * Verification of event emissions or callback invocations.
    * Basic internal state changes that affect rendering or behavior.
    * **Snapshot testing MUST be used sparingly** and only with clear justification. Prefer explicit assertions.
* **Location:** Test files (e.g., `MyComponent.test.tsx`) **MUST** be co-located with their corresponding component files.

## Feature/Flow Testing (UI Integration)

* **Scope:** Testing how multiple components interact to fulfill a small user flow or feature within a single page or a closely related set of views. This may involve mocking API calls or global state management.
* **Tools:** The same tools as component testing (**Jest** and **React Testing Library**) will be used, but tests will involve more complex setups, including mock providers for routing, state (e.g., `AppContext`), or API calls (e.g., using Mock Service Worker - MSW).
* **Focus:**
    * Data flow between interconnected components.
    * Conditional rendering based on interactions across multiple components.
    * Navigation or view changes within a limited feature scope.
    * Integration with mocked services/state to simulate real application behavior.

## End-to-End (E2E) UI Testing Tools & Scope

* **Tools:** We will use **Playwright** for E2E testing.
* **Scope (Frontend Focus):** For the YTAP MVP, E2E tests **MUST** cover the following key user journeys (at a minimum):
    1.  **Channel Management:** Successfully adding a new YouTube channel URL, assigning it a category, and verifying it appears correctly in the list of managed channels.
    2.  **Content Exploration:** Navigating to the "Content Explorer," selecting a category, and verifying that a list of (mocked or sample) transcripts/videos is displayed.
    3.  **Transcript Export:** Selecting one or more transcripts (or a category) for export, choosing any optional cleaning options, initiating the export, and verifying the UI feedback for the export process.
    4.  **Settings Management:** Navigating to the settings page, changing a simple setting (e.g., toggling the retry mechanism if this is a UI-controlled setting), and verifying the UI reflects the change.
* **Test Data Management for UI E2E Tests:**
    * Primary reliance on **API Mocking** (e.g., using Mock Service Worker - MSW) to intercept API calls and return predefined responses for consistent E2E tests.
