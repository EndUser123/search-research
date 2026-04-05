# Frontend Routing Strategy

This section details how users navigate through the YTAP application, which libraries will be used, how routes are defined, and route protection considerations, as specified in the YTAP Frontend Architecture Document.

## Routing Library

* The specific routing library will largely depend on the React meta-framework we ultimately use (e.g., Next.js comes with its own App Router or Pages Router, while a Vite + React setup would typically use a library like **React Router**).
* Given the directory structure previously discussed (with an `app/` directory), we are leaning towards a solution like **Next.js App Router**. If a simpler Vite + React setup is chosen, **React Router (latest version)** would be the choice.

## Route Definitions

The following table outlines the main routes envisioned for the YTAP MVP, based on the UI/UX Specification and PRD. The `Component/Page` paths assume a Next.js App Router-like structure within `frontend_ui/src/app/`.

| Path Pattern              | Component/Page (`frontend_ui/src/app/...`)   | Protection      | Notes                                                                                                |
| :------------------------ | :------------------------------------------- | :-------------- | :--------------------------------------------------------------------------------------------------- |
| `/`                       | `page.tsx` (Dashboard/Home)                  | Public          | Main landing page, showing an overview.                                                              |
| `/channels`               | `channels/page.tsx`                          | Public          | View for managing YouTube channels (add, view list, categorize).         |
| `/content`                | `content/page.tsx`                           | Public          | Main view for Content Explorer, likely showing categories.                 |
| `/content/[categoryName]` | `content/[categoryName]/page.tsx`            | Public          | View displaying transcripts/videos for a specific category. Parameter: `categoryName` (string).        |
| `/export`                 | `export/page.tsx`                            | Public          | View/modal for the Exporter Tool.                               |
| `/settings`               | `settings/page.tsx`                          | Public          | View for application settings (API key, retry toggle, category management). |

*(Note: The `/login` route and "Authenticated" protection status were removed as per user clarification that no login is needed for the MVP).*

## Route Guards / Protection

* Given that the MVP does not require user login, traditional authentication guards are not necessary. Access control is implicit by the user running the application locally.
* **Future Consideration:** If a self-hosted version with multiple users or restricted access were to be developed post-MVP, mechanisms for authentication and authorization would need to be implemented here.
