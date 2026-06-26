---
name: medium-risk-implementation
description: Implementation workflow for MED-risk tasks (plan + verify required). Use when the active risk tier is MED and the task touches application code or unknown scope.
---

# Medium-Risk Implementation

The active risk tier is **MED** — plan + verification required.

## Workflow

1. **Plan first.** Before editing anything, write a short numbered plan listing the files you intend to touch and why. Call `risk_progress(action="plan", text=...)` or run `/risk-plan` to record it. The plan is what makes verification meaningful.

2. **Edit in scope.** Stay inside the planned files. If you discover you need to touch something else, update the plan before editing.

3. **Verify before claiming done.** Run the project's verification command (`pytest`, `npm run test`, etc.). The `risk-policy` extension observes bash tool results and records verification automatically. You can also call `risk_progress(action="verification", passed=..., command=..., exitCode=...)` to record a verification explicitly.

4. **Report state honestly.** If verification did not run, say `pending verification`. Do not say `done`. Use `get_active_risk_policy` to confirm the current verification state if unsure.

## When to escalate

Promote to HIGH if any of the following appears during the task:

- Production keywords (`deploy`, `prod`, `secret`, `credential`, `auth`) start to dominate.
- A path under `infra/`, `auth/`, `security/`, `secrets/`, `.github/workflows/` is needed.
- A destructive command (`rm -rf`, `kubectl`, `terraform apply`, etc.) becomes necessary.

If escalation is needed, call `evaluate_change_risk(paths=..., commands=...)` to reclassify before proceeding.