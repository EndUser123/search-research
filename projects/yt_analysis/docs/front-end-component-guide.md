# Frontend Component Guide

This document details the approach to component breakdown, naming conventions, and the standard template for specifying UI components for the YTAP project, as defined in the YTAP Frontend Architecture Document.

## Component Naming & Organization

* **Component Naming Convention:** We will use **PascalCase for both React component names and their corresponding filenames** (e.g., a component named `UserProfileCard` will be in a file named `UserProfileCard.tsx`). All component files MUST follow this convention.
* **Organization (File System):**
    * Globally reusable, purely presentational UI elements (e.g., generic Button, Input, Card wrappers) will reside in `src/components/ui/`.
    * Shared layout components (e.g., Header, Sidebar) will be in `src/components/layout/`.
    * Components specific to a feature and not intended for global reuse will be co-located within their feature directory (e.g., `src/features/channel-management/components/`).
    * Refer to `docs/front-end-project-structure.md` for the complete directory layout.

## Template for Component Specification

For each significant UI component identified from the UI/UX Specification and design files (once available), the following details MUST be provided by the agent defining the component (e.g., PO, SM, or Design Architect during further detailing). The level of detail MUST be sufficient for an AI agent or developer to implement it with minimal ambiguity.

### Component: `{ComponentName}` (e.g., `ChannelRow`, `TranscriptView`)

* **Purpose:** {Briefly describe what this component does and its role in the UI. MUST be clear and concise.}
* **Source File(s):** {e.g., `src/features/channel-management/components/ChannelRow.tsx`. MUST be the exact path within the defined project structure.}
* **Visual Reference:** {Link to specific Figma frame/component (if available), or Storybook page, or a clear description from the UI/UX Specification. REQUIRED.}
* **Props (Properties):**
    {List each prop the component accepts. For each prop, all columns in the table MUST be filled.}
    | Prop Name      | Type                                                                           | Required? | Default Value | Description                                                                                                                                  |
    | :------------- | :----------------------------------------------------------------------------- | :-------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------------- |
    | `exampleProp`  | `string`                                                                       | Yes       | N/A           | Example: The title text to display. MUST be a non-empty string.                                                                              |
    | `optionalProp` | `number \| null`                                                               | No        | `null`        | Example: An optional count.                                                                                                                  |
    | `{anotherProp}`| `{Specific primitive, imported type, or inline interface/type definition}`     | {Yes/No}  | {If any}      | {MUST clearly state the prop's purpose and any constraints, e.g., 'Must be a positive integer.'}                                           |
* **Internal State (if any):**
    {Describe any significant internal state the component manages. Only list state that is *not* derived from props or global state. If state is complex, consider if it should be managed by a custom hook or global state solution instead.}
    | State Variable  | Type      | Initial Value | Description                                                                    |
    | :-------------- | :-------- | :------------ | :----------------------------------------------------------------------------- |
    | `isLoading`     | `boolean` | `false`       | Tracks if data for the component is loading.                                   |
    | `{anotherState}`| `{type}`  | `{value}`     | {Description of state variable and its purpose.}                               |
* **Key UI Elements / Structure:**
    {Provide a pseudo-HTML or JSX-like structure representing the component's DOM. Include key conditional rendering logic if applicable. **This structure dictates the primary output for the AI agent.**}
    ```html
    <div> <span class="{styles.channelName}">{channel.name}</span>
      {/* Additional elements and conditional logic based on props/state */}
    </div>
    ```
* **Events Handled / Emitted:**
    * **Handles:** {e.g., `onClick` on a delete button (triggers `onDeleteChannel` prop).}
    * **Emits:** {If the component emits custom events/callbacks not covered by props, describe them with their exact signature. e.g., `onChannelSelect: (payload: { channelId: string; }) => void`}
* **Actions Triggered (Side Effects):**
    * **State Management:** {e.g., "Dispatches `featureSlice.actions.setSomeState(newState)` from `src/features/featureName/store/featureSlice.ts`. Action payload MUST match the defined action creator."}
    * **API Calls:** {Specify which service/function from the "API Interaction Layer" is called. e.g., "Calls `channelService.fetchChannelDetails(channelId)` from `src/services/channelService.ts` on mount. Request payload: `{ channelId }`. Success response populates internal state `channelDetails`. Error response dispatches `uiSlice.actions.showErrorToast({ message: 'Failed to load channel details' })`."}
* **Styling Notes:**
    * {MUST reference specific Design System component names (e.g., "Uses `<Button variant='primary'>` from chosen UI library") OR specify Tailwind CSS classes / CSS module class names to be applied (e.g., "Container uses `p-4 bg-white rounded-lg shadow-md`. Title uses `text-xl font-semibold`.") OR specify SCSS custom component classes to be applied. Any dynamic styling logic based on props or state MUST be described. If Tailwind CSS is used, list primary utility classes or `@apply` directives for custom component classes. AI Agent should prioritize direct utility class usage for simple cases and propose reusable component classes/React components for complex styling patterns.}
* **Accessibility Notes:**
    * {MUST list specific ARIA attributes and their values (e.g., `aria-label="Channel row for [channel name]"`, `role="listitem"`), required keyboard navigation behavior (e.g., "Row is focusable. Enter key triggers selection."), and any focus management requirements.}

---
_This template is crucial for any new component definition and MUST be used consistently._
---

## Foundational/Shared Components

Many basic UI elements (Buttons, Inputs, Modals, etc.) will likely be provided by the "Modern React Component Library" chosen for YTAP. However, thin wrapper components (e.g., `<YtapButton>`, `<YtapModal>`) might be created around these library components to:
* Enforce YTAP-specific styling variations or defaults.
* Encapsulate common YTAP-specific behaviors or prop transformations.
* Simplify usage and maintain consistency across the application.

The decision to create such wrappers will be made as needed during development. If created, they **MUST** also be specified using the "Template for Component Specification" above and placed in `src/components/ui/` or `src/components/layout/` as appropriate.
