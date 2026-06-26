---
name: high-risk-change-control
description: Change-control workflow for HIGH-risk tasks (plan + verify + manual apply). Use when the active risk tier is HIGH — touches infra, auth, secrets, production deploys, or destructive operations.
---

# High-Risk Change Control

The active risk tier is **HIGH** — plan + verification + manual approval required.

## Workflow

1. **Produce a detailed plan.** List every file, command, system, and blast radius. Note the rollback path. Record it with `risk_progress(action="plan", text=...)` or `/risk-plan`.

2. **Summarize affected systems and risks.** Before editing, write a short paragraph naming the systems touched, the data sensitivity class, and the failure modes. Keep it factual.

3. **Do not auto-apply final destructive or production changes.** When the only path forward is `rm -rf`, `kubectl apply`, `terraform apply`, `git push --force`, or a production deploy, stop after staging the change and tell the user what remains. The policy is `manualApplyOnly: true`.

4. **Run required verification.** Run the verification commands appropriate for the change. The extension observes `bash` results automatically. You can also call `risk_progress(action="verification", passed=..., command=..., exitCode=...)`.

5. **Summarize the diff.** Once verification passes, record a concise diff summary with `risk_progress(action="diff_summary", text=...)` or `/risk-diff`.

6. **Wait for manual approval.** The user runs `/risk-approve` to confirm the change is ready to land. Until that fires, `manualApprovalRecorded` stays `false` and `canClaimDone("HIGH", ...)` returns `false`. Do not claim final completion before approval.

## Guardrails

- Avoid `sudo` and broad `chmod 777`.
- Prefer dry-run flags when the tool offers them.
- Pin versions and names; do not invent new dependencies in the same change.
- Stop and re-plan if scope grows during execution.