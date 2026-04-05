# AI Coder's Guide to Excellent Command-Line Interface (CLI) User Experience

This guide provides best practices for designing user-friendly and efficient Command-Line Interfaces (CLIs), specifically tailored for an AI coder. By following these guidelines, you can create CLIs that are intuitive, powerful, and a pleasure to use.

## 1. General Principles

**The Problem:** CLIs can be intimidating and difficult to use if not designed with the user in mind.

**The Solution:** Design CLIs with a human-first approach, prioritizing consistency, simplicity, and efficiency.

*   **Human-first design:** Design CLIs primarily for human users, even if they can be used by other programs.
*   **Consistency:** Adhere to established conventions and maintain consistency in command structure, naming, and input/output across the application.
*   **Simplicity:** Create small, simple programs with clean interfaces that can be combined for larger systems.
*   **Efficiency:** Enable users to perform tasks quickly and with minimal effort.

## 2. Command Design

**The Problem:** Poorly designed commands can be confusing and hard to remember.

**The Solution:** Design commands that are clear, intuitive, and easy to use.

*   **Clear Naming Conventions:** Use a single form and "VERB-NOUN" format for command names (e.g., `git clone`, `npm install`).
*   **Flags over Arguments:** Prefer using flags to label arguments (e.g., `forge deploy --environment production`) instead of relying on argument order.
*   **Short-form Aliases:** Provide short-form aliases for commonly used flags (e.g., `-v` for `--verbose`), but minimize their number and avoid using them differently from common usage in other CLIs.
*   **Enum-style Flags:** Use enum-style flags (flags that assume a value) over Boolean flags for better clarity and easier tab completion.
*   **Minimize Commands:** Limit the total number of commands and avoid introducing new verbs unnecessarily.
*   **Options as Parameters:** Options should provide parameters to commands, rather than specifying actions themselves.

## 3. User Feedback and Guidance

**The Problem:** Users can get lost or frustrated if they don't receive clear feedback and guidance.

**The Solution:** Provide comprehensive help, clear error messages, and visual feedback.

*   **Comprehensive Help:** Include a `--help` command that provides a complete list of commands, subcommands, and their descriptions.
*   **Human-readable Error Messages:** Craft clear, concise, and human-readable error messages that explain what went wrong and, if possible, suggest how to fix it.
*   **Visual Progress Indicators:** For long-running tasks, show progress visually using progress bars, spinners, or by breaking tasks into meaningful steps.
*   **Reaction for Every Action:** Provide clear feedback for every user action, indicating the current system status.
*   **Suggest Next Steps:** Guide users by suggesting commands they can run next, especially when several commands form a workflow.
*   **Prompt for Missing Information:** Instead of throwing an error, prompt the user for any outstanding required information, especially for interactive commands.
*   **Input Validation:** Validate user input as soon as possible and provide useful error messages for incorrect or invalid values.

## 4. Discoverability and Onboarding

**The Problem:** New users may struggle to get started with a CLI if it's not easy to discover its functionality.

**The Solution:** Make functionality discoverable and provide an easy onboarding experience.

*   **Ease of Discovery:** Make functionality discoverable through comprehensive help texts, examples, and suggestions.
*   **Instructive Onboarding:** Nudge users towards the commands they are most likely to use first.
*   **Interactive Modes:** Implement interactive usage modes to prompt users for necessary input, which can be particularly helpful for new users.

## 5. Output and Readability

**The Problem:** Unformatted or cluttered output can be difficult to read and understand.

**The Solution:** Design output that is easy to read and interpret.

*   **Support Skim-readers:** Break information into digestible chunks, use text formatting (bold headings, lists), and icons to emphasize important information.
*   **Use Colors Judiciously:** Use colors to attract attention and improve readability, but reserve yellow and red for warnings and errors.
*   **Consistent Input/Output:** Maintain consistency in inputs and outputs across the application.
*   **Streams:** Design CLIs to work well with text streams, allowing users to pipe output to other tools like `grep` or `awk`.

## 6. Safety and Robustness

**The Problem:** Destructive commands or unexpected behavior can lead to data loss or system instability.

**The Solution:** Implement safety measures and ensure robustness.

*   **Provide an Easy Way Out:** Ensure users can easily stop tasks (e.g., with `^C`).
*   **Bypass Prompt Option:** Provide a bypass option (e.g., `--output` flag) for prompts to allow scripting.
*   **Avoid Implicit Steps:** Make every action transparent to the user and avoid implicit steps that might override existing configurations without warning.
*   **Exit Codes:** Use exit codes correctly (0 for success, non-zero for failure) to allow other programs and scripts to interact with your tool reliably.
*   **`--dry-run` Option:** Where available, use a `--dry-run` option to test commands before execution, especially for destructive operations.
*   **Be Mindful of Destructive Commands:** Always be aware of the current directory and double-check arguments, especially for commands that can delete or modify files.
