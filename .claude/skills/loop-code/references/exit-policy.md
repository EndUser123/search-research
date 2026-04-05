# Exit Policy Configuration

Exit conditions are configured in `.claude/loop/config.yaml`:

```yaml
version: 1
enforcement:
  enabled: true                         # Full policy (default)
                                        # false = Minimal policy (EXIT_SIGNAL + indicators only)
exit_policy:
  min_completion_indicators: 2          # Minimum iterations (default: 2)
  require_exit_signal: true             # Require EXIT_SIGNAL in RALPH_STATUS
  require_all_tasks_complete: true      # Require all tasks marked complete
  require_verification_pass: false      # Require verification to pass
verification:
  enabled: true                         # Practical verification (default)
                                        # false = Disabled
  lookback_turns: 10                    # Chat lookback window for concerns
  fuzzy_match_threshold: 0.8           # Requirement matching threshold (0.0-1.0)
plans:
  default_plan: plan.md
  allow_per_terminal_plan: false
logging:
  decision_log: .claude/loop/logs/decision.log
  verifier_log: .claude/loop/logs/verifier.log
```

## Enforcement Modes (TASK-018)

- **`enforcement.enabled: true`** (default): Full policy enforcement
  - All exit policy flags are evaluated (EXIT_SIGNAL, task completion, verification)
  - Stricter quality control before exit
  - Use for production workflows requiring complete verification

- **`enforcement.enabled: false`**: Minimal policy enforcement
  - Only requires `completion_indicators >= min` + `EXIT_SIGNAL: true`
  - Ignores `require_all_tasks_complete` and `require_verification_pass`
  - Use for rapid prototyping or experimental development
  - Faster iteration cycle with fewer exit requirements

## Setting EXIT_SIGNAL

The LLM adds this to the plan file's RALPH_STATUS block when it believes all work is complete:

```markdown
## RALPH_STATUS

- EXIT_SIGNAL: true
- completion_indicators: 3
- current_task: TASK-005
```

## Practical Verification

When `verification.enabled: true` (default), the loop uses practical verification instead of formal PRD verification.

### Plan Requirement Extraction

- Parses these sections from plan.md (in order of priority):
  - `## Acceptance Criteria`
  - `## Success Metrics`
  - `## Constraints`
- Extracts bullet list items as requirements
- Example:
  ```markdown
  ## Acceptance Criteria
  - [ ] User can authenticate with email/password
  - [ ] Password hashing uses bcrypt
  - [ ] Login endpoint returns JWT token
  ```

### Requirement Verification

- Checks each completed task against plan requirements
- Uses 80% fuzzy matching threshold to match tasks to requirements
- Tracks which requirements are satisfied by completed tasks
- Exit blocked if any requirements unmatched

### Chat Concern Extraction

- Extracts a bounded structured excerpt from the last `lookback_turns` turns -- keyword matches only (issue/blocker/correction counts), not raw transcript content. The raw transcript MUST NOT be loaded into the loop orchestrator's context; only the extracted concern list (a short JSON array) is returned.
- Looks for user-reported issues:
  - "This is wrong" -> issue
  - "Not working" -> issue
  - "Blocked by" -> blocker
  - "Fix this" -> correction
- Exit blocked if any unresolved concerns found

### Configuration

```yaml
verification:
  enabled: true                        # Practical verification (default)
  lookback_turns: 10                   # Chat lookback window
  fuzzy_match_threshold: 0.8          # Requirement matching threshold
```

### Policy-based exit flexibility

- `min_completion_indicators`: Prevents premature exit on simple tasks
- `require_exit_signal`: LLM's explicit judgment that plan is complete
- `require_all_tasks_complete`: Ensures all tasks are marked done
- `require_verification_pass`: Requires successful verification run
- All enabled conditions must be met for exit (AND logic)

## Exit Conditions Reference

| Condition | Purpose | Set By | Config Flag | Enforcement Mode |
|-----------|---------|--------|-------------|------------------|
| `completion_indicators >= min` | Heuristic completion | Auto-incremented | Always required | Both |
| `EXIT_SIGNAL: true` | Explicit LLM judgment | LLM in RALPH_STATUS | `require_exit_signal` | Both |
| All tasks complete | Ensure all tasks done | Checkbox completion | `require_all_tasks_complete` | Enabled only |
| Verification passed | Verification required | Verifier skill | `require_verification_pass` | Enabled only |

**Exit logic**: ALL enabled conditions must be true (AND logic).

**Enforcement modes**:
- **`enforcement.enabled: true`**: All conditions apply (full policy)
- **`enforcement.enabled: false`**: Only `completion_indicators >= min` + `EXIT_SIGNAL: true` (minimal policy)

**Example scenarios**:
- If `completion_indicators = 0` and `EXIT_SIGNAL: true` -> Continue (min not met)
- If `completion_indicators = 5` and `EXIT_SIGNAL: false` -> Continue (signal not set)
- If all tasks complete but `verification_status.passed = false` -> Continue (enforcement enabled, verification required and failed)
- If `enforcement.enabled: false`, incomplete tasks, but `EXIT_SIGNAL: true` -> Exit (minimal policy, ignores task completion)
- If all conditions met -> Exit (all enabled conditions satisfied)
