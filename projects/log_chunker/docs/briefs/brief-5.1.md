# Implementation Brief: Task 5.1 - CLI Refactor

**Goal**: To refactor the CLI to be "smart by default" and to use a more intuitive subcommand structure.

**Inputs**: N/A (Refactoring `cli.py`).

**Outputs**: An updated `cli.py` and changes to `log_chunker.py` (the main entry point).

**Pseudocode / Action Plan**:

1.  **Modify `cli.py`**:
    - Use `argparse`'s `add_subparsers()` to create subcommands.
    - **Default Command**: If no subcommand is given, the tool should run the full, default analysis pipeline.
    - **`analyze` subcommand**: This will be the primary command. `python log_chunker.py analyze <file>` will perform the default, full analysis.
    - **`report` subcommand**: `python log_chunker.py report <file> --type=summary` will allow users to generate a specific report type without re-running the full analysis (it will use the cached `IntelligenceReport`).
    - **`config` subcommand**: `python log_chunker.py config sample` will provide configuration-related utilities.
2.  **Modify `log_chunker.py`**:
    - The `main()` function will be updated to handle the new subcommand structure.
    - The logic for the "smart default" behavior will be implemented here. It will call the `IntelligenceEngine` and the `AdvancedReporter` with default settings.

**Key Considerations**:
- This is a major breaking change for users. The `V2_MIGRATION_GUIDE.md` is critical.
- The logic for caching the `IntelligenceReport` will need to be designed. A simple approach is to save it as a JSON file in the `reports` directory alongside the other reports.
