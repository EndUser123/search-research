# Development Workflow

**Version**: 1.0
**Status**: Active

## 1. Core Principle

This project follows a simple but strict principle: **Plan the work, then work the plan.**

The authoritative plan is maintained in the root `docs/project/PROJECT_STATUS.MD` file. All development work must correspond to a task in that plan.

## 2. AI Agent Session Workflow

This is the standard operating procedure for any AI agent session on this project.

### Step 1: Onboarding & Context Sync

At the beginning of a new session, the agent must gain full context by reviewing the following files in order:

1.  **`docs/project/PROJECT_HANDOFF.MD`**: Read the **latest entry at the top** of this file. It contains the summary of the previous session and the explicit next task to be performed.
2.  **`docs/project/PROJECT_STATUS.MD`**: Review the entire master plan to understand the current task's place in the overall project goals. The `AI Agent Onboarding` section provides a manifest of other key files.

### Step 2: Task Execution

1.  **Identify the Task**: The task is explicitly stated in the handoff log.
2.  **Consult the Brief**: If the task in `docs/project/PROJECT_STATUS.MD` links to an implementation brief in `docs/briefs/`, read that brief thoroughly before starting work.
3.  **Execute the Work**: Perform the coding, refactoring, or documentation work required to complete the task.
4.  **Update Status**: Once the task is complete, update its `Status` field in `docs/project/PROJECT_STATUS.MD` from `not-started` to `completed`.

### Step 3: Session Handoff

This is the most critical step for ensuring project continuity. It must be the **final action** of every session.

1.  **Ensure Clean State**: Verify that all files are saved and the project is in a stable, non-broken state.
2.  **Prepare Summary**: Formulate a concise summary of the work accomplished during the session.
3.  **Identify Next Step**: Clearly identify the *exact* next task ID and description from `docs/project/PROJECT_STATUS.MD`.
4.  **Append to Handoff Log**: Prepend the new `Session Handoff Summary` to the top of `docs/project/PROJECT_HANDOFF.MD`. The summary must include the session's accomplishments, confirmation of the clean workspace state, and the explicit next task.
