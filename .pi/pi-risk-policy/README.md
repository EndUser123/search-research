# pi-risk-policy

Automatic, visible, risk-based control for a solo director using Pi as an AI coder.

Classifies every task into `LOW`, `MED`, or `HIGH` based on what you said and
what you're about to touch, shows that classification in the UI, and gates
"done" on deterministic verification rules.

Three discrete tiers. One classifier. One policy table. No probabilistic
scoring, no hidden weights.

## Release scope

This release implements the **core risk-policy contract** only:

- Deterministic task classification into `LOW`, `MED`, and `HIGH`
- Visible risk state in the PI UI (footer marker + editor banner)
- Manual override support (`/risk-override`, `/risk-reset`)
- Verification-state tracking and `canClaimDone(...)` gating
- Risk logging (JSONL audit log under `.pi/risk-log.jsonl` when project trust allows)
- End-to-end validation for the `LOW` path
- Checklist-backed unit tests for classifier and failure-recording behavior

### Not in this release (Phase 2)

The following checklist items are **intentionally out of scope** for the
current package. They require separate interception, state, and enforcement
subsystems rather than small extensions to the classifier-and-policy design:

- Filesystem-aware new-file and dependency-resolution handling
- Assistant-message fake-done detection with on-disk artifact verification
- Regression guard / catch-22 failure-threshold logic

If you need any of those, treat them as future work, not as regressions.

### Classification note

The default classifier treats clearly production-sensitive paths and
keywords as `HIGH`. To avoid over-escalating ordinary application-code
work, `auth` is **not** included in `DEFAULT_CONFIG.productionKeywords`
for the current release.

That means a prompt like `Refactor src/auth.ts` classifies as `MED`
unless it also carries a stronger `HIGH` signal such as:

- A match on `highPaths` (e.g. an `auth/`, `infra/`, `secrets/` path)
- A match on `highCommandPatterns` (e.g. `kubectl`, `terraform apply`)
- A production-sensitive keyword such as `prod`, `production`, `deploy`, `secret`, or `credential`

If stricter auth-related escalation is needed later, add it as a narrower
co-signal rule rather than as a broad standalone keyword.

## Install

```bash
pi install /path/to/pi-risk-policy
```

Or via the npm/git URL once published.

## What you get

### Visible tier

The active tier shows in the Pi footer (`R:LOW` / `R:MED` / `R:HIGH`) and as a
banner above the editor. The banner shows the policy label and the reasons
that put you at this tier. HIGH additionally fires a non-blocking toast.

### Tiers

| Tier | Triggered by | Controls |
|------|--------------|----------|
| **LOW** | Only `docs/`, `tests/`, `examples/`, `fixtures/`, or `*.md` paths | Fast path |
| **MED** | App code, unknown scope | Plan + verify required |
| **HIGH** | `infra/`, `auth/`, `security/`, `secrets/`, `.github/workflows/`, destructive commands, or production keywords | Plan + verify + manual approval; manual-apply only |

See [POLICY_BY_TIER](./extensions/risk-policy.ts) for the full table.

### Slash commands

| Command | Purpose |
|---------|---------|
| `/risk` | Current tier, reasons, matched rules, policy, verification state |
| `/risk-why` | Latest assessment plus recent log entries |
| `/risk-override low\|med\|high` | Force a tier until `/risk-reset` |
| `/risk-reset` | Clear manual override |
| `/risk-approve` | HIGH only — record manual approval |
| `/risk-plan [text]` | Record plan (MED/HIGH) |
| `/risk-diff [text]` | Record diff summary (HIGH) |

### Tools the model can call

- `get_active_risk_policy` — returns current assessment, policy, verification
- `evaluate_change_risk(paths?, commands?, prompt?)` — re-classify with extra context
- `risk_progress(action="plan"|"diff_summary"|"verification", ...)` — record progress

### Skills

- `medium-risk-implementation` — workflow for MED tasks (plan + verify)
- `high-risk-change-control` — workflow for HIGH tasks (plan + verify + manual approval)

Load with `/skill:medium-risk-implementation` or `/skill:high-risk-change-control`.

### Prompt template

`/risk-review` renders a concise review block from the active assessment.

### Audit log

Every classification, override, and verification update writes a JSONL record
to `.pi/risk-log.jsonl` in the project (when project trust is granted).
Falls back silently when the directory is not writable.

## Repo-local config

Drop a `.pi/risk-policy.json` in your project root to override the default
config arrays (path lists, command patterns, keywords, verification commands):

```json
{
  "lowPaths": ["docs/", "tests/", "specs/"],
  "highPaths": ["infra/", "auth/", "secrets/", ".github/workflows/", "deploy/"],
  "highCommandPatterns": ["kubectl", "terraform apply", "rm -rf"],
  "productionKeywords": ["prod", "production", "secret", "credential"],
  "verificationCommands": {
    "default": ["pytest -q"],
    "typescript": ["npm test", "npm run lint"],
    "rust": ["cargo test"]
  }
}
```

Arrays are replaced wholesale — they do not merge with defaults. The file is
only read after the project is trusted (`ctx.isProjectTrusted()`).

## Development

```bash
npm install
npm test
```

Tests cover:

- `classifyRisk` — low-path, med-default, high-path, high-command, keyword-high, override, path normalization
- `extractCandidatePaths` — slash paths, dotfile dirs, bare filenames, URL exclusion, dedup
- `canClaimDone` / `missingRequirements` — every tier
- `mergeConfig` — array replacement and verification-command additive merge
- `isVerificationCommand` — `pytest`, `npm test`, `npm run lint`, `mypy`, `cargo test`
- `POLICY_BY_TIER` — control surface

## Layout

```
pi-risk-policy/
├── package.json
├── README.md
├── tsconfig.json
├── extensions/
│   ├── risk-policy-extension.ts   # runtime entrypoint
│   ├── risk-classifier.ts         # classifyRisk, isVerificationCommand, mergeConfig
│   ├── risk-policy.ts             # POLICY_BY_TIER
│   ├── risk-state.ts              # RiskStateStore
│   ├── risk-ui.ts                 # banner / status / widget helpers
│   ├── risk-commands.ts           # /risk, /risk-override, ...
│   ├── risk-tools.ts              # get_active_risk_policy, evaluate_change_risk, risk_progress
│   ├── risk-log.ts                # JSONL audit log
│   ├── risk-types.ts              # shared types
│   ├── path-extractor.ts          # extractCandidatePaths
│   └── verification-state.ts      # canClaimDone, missingRequirements
├── skills/
│   ├── medium-risk-implementation/SKILL.md
│   └── high-risk-change-control/SKILL.md
├── prompt-templates/
│   └── risk-review.md
└── tests/
    └── risk-policy.test.ts
```

## Non-goals

- Claude-Code-style hook chains
- Probabilistic / ML-based risk scoring
- OS-level sandboxing or real shell isolation
- Team approval workflows or multi-user RBAC
- Complex workflow DAGs
- Filesystem-aware new-file and dependency-resolution handling (see **Release scope → Phase 2**)
- Assistant-message fake-done detection with on-disk artifact verification (see **Release scope → Phase 2**)
- Regression guard / catch-22 failure-threshold logic (see **Release scope → Phase 2**)

Pi is not a sandbox and does not treat trust as a security boundary. Risk
classification is an input-loading guard and a UI affordance, not a
privilege boundary. Real isolation belongs outside this package.