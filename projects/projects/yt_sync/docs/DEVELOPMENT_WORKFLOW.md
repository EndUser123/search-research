# Project Development Workflow

**Objective:** To provide a clear, repeatable process for all contributors to select, execute, and complete tasks, ensuring alignment with our strategic roadmap and quality standards.

### Core Principles
1.  **Single Source of Truth:** All work is tracked in `dev/tracking/tracking_dev.json` or `dev\tracking_test.json`. If a task isn't in these files, it isn't officially part of the plan.
2.  **Task-Driven Development:** All code changes must be associated with a specific task ID. "Cowboy coding" without a tracked task is prohibited.
3.  **Plan Before Execution:** For any non-trivial task, a plan should be proposed or linked within the task's comments or `related_links` before implementation begins.

### The Standard Operational Loop

This is the primary workflow for any developer or architect contributing to the project.

**Step 1: Review the Strategic State**
-   Before starting any work, review the active tasks in both tracking files (`dev/tracking/tracking_dev.json` and `dev\tracking_test.json`).
-   Understand the current `In Progress` tasks to avoid conflicting work.
-   Consult `roadmap.md` to understand the objectives of the current phase.

**Step 2: Select a Task**
-   Select a task that is in the `Not Started` state.
-   Prioritize tasks based on their `priority` field ("Critical" > "High" > "Medium" > "Low").
-   Ensure all tasks listed in the `dependencies` array are `Completed` or `Verified`.
-   If the task seems unclear, use the `comments` section to ask for clarification.

**Step 3: Begin Work & Update Status**
-   Once you have selected a task, your first action is to **update its status to `In Progress`** in the relevant JSON file.
-   Add a `comment` to the task announcing that you have started work. This prevents other developers from picking up the same task.
-   Example Comment: `{"author": "Developer A", "timestamp": "...", "text": "Beginning implementation."}`

**Step 4: Execute the Task**
-   Follow all relevant project standards as defined in:
    -   `docs/architecture/coding_standards.md`
    -   `docs/testing/unit_testing_guide_v5.md`
-   If the task involves creating a new feature or making a significant change, follow the `docs/testing/qa-checklist.md`.
-   If the task has a detailed plan in the `test-plans/` directory, follow it.

**Step 5: Complete Work & Update Status**
-   Once your implementation is complete and has passed local testing, update the task's status to `Completed`.
-   Add a final `comment` summarizing the work done.
-   For bug fixes, the comment should reference the specific fix.
-   For new features, the comment should point to the new code and tests.
-   Commit your changes with a message that includes the task ID (e.g., "feat(auditor): Refactor to SRP - Closes YT-SYNC-8-3").
