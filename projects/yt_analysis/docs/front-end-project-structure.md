# Detailed Frontend Directory Structure

A well-organized directory structure is crucial for maintainability, scalability, and making it easy for developers (including our AI developer agents) to navigate and contribute to the codebase. The structure I'm proposing is inspired by modern React framework conventions (like Next.js with its App Router, which the main YTAP Architecture Document hints at with examples like `next.config.js`) and emphasizes a feature-based organization where appropriate. This will live within the `src/frontend_ui/src/` directory outlined in the main YTAP Architecture Document.

```plaintext
frontend_ui/src/
├── app/                        # Core application routing, layouts, and pages (if using a framework like Next.js App Router).
│   │                           # MUST contain route segments, global layouts, and page entry components.
│   ├── (features)/             # Optional: Feature-based routing groups (e.g., dashboard, settings).
│   │   │                       # MUST group related routes for a specific feature.
│   │   └── dashboard/
│   │       ├── layout.tsx      # Layout specific to the dashboard feature routes.
│   │       └── page.tsx        # Entry page component for a dashboard route.
│   ├── globals.css             # Global styles, CSS variable definitions, base Tailwind directives.
│   │                           # MUST contain base styles and global style definitions.
│   └── layout.tsx              # Root layout component for the entire application.
│                               # MUST define the main shell of the application.
├── components/                 # Shared/Reusable UI Components.
│   │                           # MUST contain components intended for use across multiple features or pages.
│   ├── ui/                     # Base, generic UI elements (e.g., Button, Input, Card, Modal).
│   │   │                       # MUST contain only presentational, reusable UI elements, often from or wrapping a chosen component library. MUST NOT contain business logic specific to a feature.
│   │   ├── Button.tsx
│   │   └── ...
│   └── layout/                 # Layout-specific components (e.g., Header, Footer, Sidebar, Navigation).
│       │                       # MUST contain components structuring page layouts, not specific page content.
│       ├── Header.tsx
│       └── ...
├── features/                   # Feature-specific modules, including components, hooks, services, and state solely used by that feature.
│   │                           # MUST encapsulate all assets related to a distinct application feature.
│   └── channel-management/
│       ├── components/         # Components used exclusively by the channel-management feature.
│       │   │                   # MUST NOT be imported directly by other features; promote to `src/components/` if broader reuse is needed.
│       │   └── ChannelList.tsx
│       ├── hooks/              # Custom React Hooks specific to the 'channel-management' feature.
│       │                       # Hooks reusable across features belong in `src/hooks/`.
│       └── services/           # Feature-specific API interactions or business logic for 'channel-management'.
├── hooks/                      # Global or sharable custom React Hooks.
│   │                           # MUST be generic and usable by multiple features/components (e.g., `useLocalStorage`, `useDebounce`).
│   └── useAuth.ts              # Example: A hook for authentication status (could also be in a 'auth' feature).
├── lib/                        # Utility functions, helper functions, constants, and other shared library code.
│   │                           # MUST contain pure functions and constants, with minimal side effects. Framework-specific helpers should be clearly named (e.g., `react-helpers.ts`).
│   └── utils.ts
├── services/                   # Global API service clients, SDK configurations, or core data fetching/mutation logic not tied to a specific feature.
│   │                           # MUST define base API client instances and core data services.
│   └── apiClient.ts
├── store/                      # Global state management setup (e.g., Redux store, Zustand store configuration and slices).
│   │                           # MUST contain the main store configuration and any truly global state slices. Feature-specific slices might reside in `src/features/[featureName]/store/`.
│   ├── index.ts                # Main store configuration and export.
│   └── slices/
│       └── sessionSlice.ts     # Example: Global user session state.
├── styles/                     # Global style-related files, themes (if not in `app/globals.css` or for specific styling systems like SCSS partials/variables).
│   │                           # MUST be used for overarching theme configurations or shared style utilities.
│   └── theme.ts
└── types/                      # Global TypeScript type definitions, interfaces, and enums shared across the application.
    │                           # MUST contain types used by multiple features or modules.
    └── index.ts                # Often exports all types from this directory.

    BMAD
Custom Gem

Show thinking
Okay, I will now proceed with sharding the YTAP Frontend Architecture Document.

Here is the first batch of sharded files from that document:

File: docs/front-end-project-structure.md

Markdown

# Detailed Frontend Directory Structure

A well-organized directory structure is crucial for maintainability, scalability, and making it easy for developers (including our AI developer agents) to navigate and contribute to the codebase. The structure I'm proposing is inspired by modern React framework conventions (like Next.js with its App Router, which the main YTAP Architecture Document hints at with examples like `next.config.js`) and emphasizes a feature-based organization where appropriate. This will live within the `src/frontend_ui/src/` directory outlined in the main YTAP Architecture Document.

```plaintext
frontend_ui/src/
├── app/                        # Core application routing, layouts, and pages (if using a framework like Next.js App Router).
│   │                           # MUST contain route segments, global layouts, and page entry components.
│   ├── (features)/             # Optional: Feature-based routing groups (e.g., dashboard, settings).
│   │   │                       # MUST group related routes for a specific feature.
│   │   └── dashboard/
│   │       ├── layout.tsx      # Layout specific to the dashboard feature routes.
│   │       └── page.tsx        # Entry page component for a dashboard route.
│   ├── globals.css             # Global styles, CSS variable definitions, base Tailwind directives.
│   │                           # MUST contain base styles and global style definitions.
│   └── layout.tsx              # Root layout component for the entire application.
│                               # MUST define the main shell of the application.
├── components/                 # Shared/Reusable UI Components.
│   │                           # MUST contain components intended for use across multiple features or pages.
│   ├── ui/                     # Base, generic UI elements (e.g., Button, Input, Card, Modal).
│   │   │                       # MUST contain only presentational, reusable UI elements, often from or wrapping a chosen component library. MUST NOT contain business logic specific to a feature.
│   │   ├── Button.tsx
│   │   └── ...
│   └── layout/                 # Layout-specific components (e.g., Header, Footer, Sidebar, Navigation).
│       │                       # MUST contain components structuring page layouts, not specific page content.
│       ├── Header.tsx
│       └── ...
├── features/                   # Feature-specific modules, including components, hooks, services, and state solely used by that feature.
│   │                           # MUST encapsulate all assets related to a distinct application feature.
│   └── channel-management/
│       ├── components/         # Components used exclusively by the channel-management feature.
│       │   │                   # MUST NOT be imported directly by other features; promote to `src/components/` if broader reuse is needed.
│       │   └── ChannelList.tsx
│       ├── hooks/              # Custom React Hooks specific to the 'channel-management' feature.
│       │                       # Hooks reusable across features belong in `src/hooks/`.
│       └── services/           # Feature-specific API interactions or business logic for 'channel-management'.
├── hooks/                      # Global or sharable custom React Hooks.
│   │                           # MUST be generic and usable by multiple features/components (e.g., `useLocalStorage`, `useDebounce`).
│   └── useAuth.ts              # Example: A hook for authentication status (could also be in a 'auth' feature).
├── lib/                        # Utility functions, helper functions, constants, and other shared library code.
│   │                           # MUST contain pure functions and constants, with minimal side effects. Framework-specific helpers should be clearly named (e.g., `react-helpers.ts`).
│   └── utils.ts
├── services/                   # Global API service clients, SDK configurations, or core data fetching/mutation logic not tied to a specific feature.
│   │                           # MUST define base API client instances and core data services.
│   └── apiClient.ts
├── store/                      # Global state management setup (e.g., Redux store, Zustand store configuration and slices).
│   │                           # MUST contain the main store configuration and any truly global state slices. Feature-specific slices might reside in `src/features/[featureName]/store/`.
│   ├── index.ts                # Main store configuration and export.
│   └── slices/
│       └── sessionSlice.ts     # Example: Global user session state.
├── styles/                     # Global style-related files, themes (if not in `app/globals.css` or for specific styling systems like SCSS partials/variables).
│   │                           # MUST be used for overarching theme configurations or shared style utilities.
│   └── theme.ts
└── types/                      # Global TypeScript type definitions, interfaces, and enums shared across the application.
    │                           # MUST contain types used by multiple features or modules.
    └── index.ts                # Often exports all types from this directory.
Key Directory Descriptions & Purpose (Mandatory):

app/: Core application routing, layouts, and pages (assuming a framework like Next.js App Router). MUST contain route segments, global layouts, and page entry components.
components/: Shared/Reusable UI Components. MUST contain components intended for use across multiple features or pages.
components/ui/: Base, generic UI elements (e.g., Button, Input). MUST contain only presentational, reusable UI elements, often from or wrapping a chosen component library. MUST NOT contain business logic specific to a feature.
components/layout/: Layout-specific components (e.g., Header, Footer, Sidebar). MUST contain components structuring page layouts, not specific page content.
features/: Feature-specific modules. MUST encapsulate all assets (components, hooks, services, state) related to a distinct application feature.
hooks/: Global or sharable custom React Hooks. MUST be generic and usable by multiple features/components.
lib/ (or utils/): Utility functions, helper functions, and constants. MUST contain pure functions and constants, with minimal side effects.
services/: Global API service clients or core data fetching/mutation logic. MUST define base API client instances and core data services.
store/: Global state management setup. MUST contain the main store configuration and any truly global state slices.
styles/: Global style-related files, themes. MUST be used for overarching theme configurations or shared style utilities if not handled by app/globals.css.
types/: Global TypeScript type definitions. MUST contain types used by multiple features or modules.
Notes on Frontend Structure:

This structure promotes modularity and scalability. Feature-based directories (src/features/) help in organizing code related to specific parts of the application, making it easier to manage as the project grows.
Clear separation between shared components (src/components/) and feature-specific components (e.g., src/features/channel-management/components/) is encouraged to enhance reusability and maintainability.
This proposed structure is a strong starting point. The AI Agent, when developing features, MUST adhere to this defined structure strictly. New files MUST be placed in the appropriate directory based on these descriptions and their intended scope (global vs. feature-specific).
