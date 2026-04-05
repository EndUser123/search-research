# Vid_ReC Development Workflow

**Objective:** To provide a clear, repeatable process for all work on the Vid_ReC project, ensuring alignment with our plan and quality standards.

### Roles & Responsibilities
This workflow is a partnership between two distinct roles:
* **The Developer (Human):** The final authority and validator.
* **The Architect (LLM):** The thinking partner and planner.

### Project Layout
The project is organized into three main root directories:
* `src/`: Contains all the application's Python source code.
* `dev/`: Contains operational artifacts for the development process itself (e.g., the state file, manifest, and prompt templates).
* `docs/`: Contains all human-readable documentation, guides, and architectural diagrams.

### Core Principles
1.  **Single Source of Truth:** All work is tracked in `dev/vidrec_state.json`.
2.  **Task-Driven Development:** All code changes must be associated with a specific task ID.
3.  **Atomic Commits:** Source code and documentation/state changes must be committed together.

### The Standard Operational Loop

**Step 1: Initiate a Session**
-   Start a new session with the Architect by providing the master prompt template from `dev/prompt_template.yaml`, populated with the project manifest and all relevant source files.
-   The Architect will analyze the state and report the next recommended task.

**Step 2: Plan the Task**
-   Collaborate with the Architect to define the plan for the selected task.
-   This will typically involve the Architect proposing changes to `dev/vidrec_state.json` (e.g., updating milestones), which you must approve before proceeding.

**Step 3: Execute the Task**
-   Implement the code changes as planned.
-   Follow the project's `docs/QA_CHECKLIST.md` before finalizing your work.

**Step 4: Commit a Complete Unit of Work**
-   Once implementation is complete and has passed local testing, stage all related changes. This **must** include:
    -   The source code you modified.
    -   The updated `dev/vidrec_state.json` file.
    -   Any new documentation (like ADRs) created for the task.
-   Commit the changes with a message that includes the task ID (e.g., "feat(vmaf): Add quality-based decision logic - Closes #3.1").

**Step 5: Conduct Post-Task Architectural Review**
-   After a task is complete and committed, the Architect will conduct a formal review before the next task is chosen. This ensures we continuously evaluate our technical choices.
-   This review will answer four key questions:
    1.  **Component Analysis:** What core components, libraries, or architectural patterns were directly affected by the completed task?
    2.  **Impact Assessment:** Did the change improve or degrade the performance and stability of these components? Were the trade-offs acceptable and aligned with our goals?
    3.  **Opportunity Analysis:** Is there a known or emerging alternative technology for any of the affected components that might offer a significant improvement in performance, stability, or maintainability?
    4.  **Recommendation:** Based on the analysis, what is the immediate next step?
        -   **A) Proceed:** The current technology is sound. Proceed with the next task on the roadmap.
        -   **B) Investigate:** A promising alternative exists. Create a new, time-boxed **[Research]** task to investigate further.
        -   **C) Pivot:** The alternative is so compelling that we should consider making it our next priority, likely resulting in a new ADR.
-   The result of this review will be presented to the Developer to inform the decision on what to do next.
