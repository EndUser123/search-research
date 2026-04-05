# Vid_ReC QA Checklist

Before committing a new feature or significant bugfix, perform these checks.

#### **Phase 1: Planning & Design**

*   `[ ]` **Define User Story / Value:** (As a [user], I want [action], so that [benefit]). What is the goal?
*   `[ ]` **Identify Dependencies:** What external libraries or internal modules are involved?
*   `[ ]` **Anticipate Failure Modes:** What could go wrong? (e.g., API call fails, file not found, invalid data, out of disk space). The implementation plan must handle these.

#### **Phase 2: Implementation & Code Quality**

*   `[ ]` **Logging:** Does every major action, decision point, and error path log useful information?
*   `[ ]` **Configuration:** If the feature needs a setting, is it added to `config.py` with a sensible default?
*   `[ ]` **State Management:** Does the `state_manager` correctly record the outcome (e.g., success, failure, new intermediate states)?

#### **Phase 3: Verification**

*   `[ ]` **The "Clean Slate" Test:** Does the feature work correctly for a file that has never been processed?
*   `[ ]` **The "Resumption" Test:** If the script is stopped mid-process, does it correctly resume or re-process on the next run?
*   `[ ]` **The "Already Done" Test:** Does the feature correctly skip files that are already fully processed?
