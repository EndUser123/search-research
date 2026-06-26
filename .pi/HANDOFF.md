# Handoff — Pi risk-policy session

## State at handoff

Five packages installed via `pi install` (user-global, in `~/.pi/agent/`):

1. **`P:\.pi\pi-risk-policy`** — risk classification + verification gates
2. **`git:github.com/nicobailon/pi-web-access`** — Exa / Perplexity / Gemini Web search + content extraction
3. **`git:github.com/DietrichGebert/ponytail`** — code-review skill (already installed, unrelated)
4. **`npm:pi-review`** (akuzmenko, MIT, v1.1.4) — `/review` command: starts a new branch from the current conversation and runs a maintainer-style review of available work. 0 runtime deps.
5. **`npm:pi-simplify`** (mdevy, MIT, v0.2.2) — `/simplify` command: reviews recently changed code (via `git diff`) for clarity, consistency, maintainability. 0 runtime deps. Ships compiled JS, not source.

Plus one global extension at **`~/.pi/agent/extensions/extra-search.ts`** — Brave / Tavily / Serper as pi tools (complements pi-web-access).

## Single source of truth: `P:/.env`

All API keys live in `P:/.env`. The Windows registry (`HKCU\Environment`) and PowerShell profile have been **cleaned of API keys** — they keep only system config (PATH, TEMP, GOPATH, etc.). PowerShell profile auto-sources `P:/.env` on shell start.

To read keys in a pi extension, use the `loadDotEnv` helper from `extra-search.ts` (copy the function — it's ~25 lines, strips quotes, skips comments, doesn't overwrite existing `process.env`).

If a non-pi tool needs an API key in a plain bash/PowerShell session, source `P:/.env` first. The pattern is `set -a; source /p/.env; set +a` for bash.

## Risk-policy package

`P:\.pi\pi-risk-policy\` — see `README.md` for scope. Phase 2 items (filesystem new-file checks, fake-done detection, catch-22 regression guard) are explicitly out of scope. Don't add them without a separate scope decision.

Key files:
- `extensions/risk-classifier.ts` — `classifyRisk`, `isVerificationCommand`, `mergeConfig`, `DEFAULT_CONFIG`
- `extensions/verification-state.ts` — `canClaimDone`, `missingRequirements`
- `extensions/risk-policy-extension.ts` — entrypoint; maps spec hooks → real pi events
- `tests/risk-policy.test.ts` — 65 unit + integration tests

`tsc --noEmit` is clean, **72/72 tests pass**. Run with `npm test` (after `npm install`) or `npx tsx --test tests/*.test.ts`.

The classifier's `DEFAULT_CONFIG.productionKeywords` deliberately excludes `"auth"` so `Refactor src/auth.ts` classifies as MED (per the README's classification note). If stricter auth handling is needed, add a co-signal rule, don't blanket-add the keyword.

## Verified behaviors

- LOW (`Update docs/README.md`) → LOW, banner + footer marker
- MED (`Refactor src/auth.ts`) → MED
- HIGH (`Modify infra/deploy.yml for production`) → HIGH
- HIGH (`deploy to production`) → HIGH (PRODUCTION_KEYWORD)
- Verification commands: `pytest`, `npm test`, `npm run test`, `npm run lint`, `ruff check`, `mypy`, `cargo test` are detected via `isVerificationCommand`
- Override mid-task preserves verification state (the fix this session made; do not regress)
- JSONL audit log written to `.pi/risk-log.jsonl` in the project cwd when project trust allows

## Pending / known gaps

- **State doesn't survive `/reload`.** In-memory `RiskStateStore` only. The `todo.ts` example shows the reconstruction pattern; not implemented here.
- **`pi-subagents` decision scheduled for June 30, 2026.** A Windows scheduled task `pi-subagents-review` will pop a reminder. Reassess then: only install if a real friction case emerged in the past week.
- **`agent_end` is mitigation, not enforcement.** It fires *after* the assistant message is finalized. The model can still say "done" prematurely; `before_agent_start` injects a reminder on the next turn.
- **Last-verification exit code is approximated.** Pi's `BashToolDetails` doesn't carry the exit code. `extractBashExitCode` parses it from the error message text (`"exited with code N"`); falls back to 1 when unparseable. The boolean `verificationPassed` is correct; the numeric `lastVerificationExitCode` may be 0/1 even when the real code was different.

## Things you shouldn't do without asking

- Modify `P:/.env` to add a key without first checking that `.env` doesn't already have it under a different name (case/underscore variants — we've already resolved GitHub, Mistral, and Z.AI).
- Add pi packages speculatively. The user values small surface; the bar is "real, recurring friction."
- Reintroduce "registry wins" semantics in any new loader. P:/.env is canonical. The "process.env wins over .env" rule is fine (lets explicit-override work); "registry wins over .env" caused the morning's bug.

## File locations quick-ref

```
P:/.env                                         # canonical API keys
P:/.pi/HANDOFF.md                               # this file
P:/.pi/pi-risk-policy/                          # the risk-policy package
  ├── README.md
  ├── extensions/
  │   ├── risk-policy-extension.ts               # entrypoint
  │   ├── risk-classifier.ts
  │   ├── risk-policy.ts
  │   ├── risk-state.ts
  │   ├── risk-ui.ts
  │   ├── risk-commands.ts
  │   ├── risk-tools.ts
  │   ├── risk-log.ts
  │   ├── risk-types.ts
  │   ├── path-extractor.ts
  │   ├── verification-state.ts
  │   └── bash-result.ts
  ├── skills/{medium-risk-implementation,high-risk-change-control}/SKILL.md
  ├── prompt-templates/risk-review.md
  └── tests/risk-policy.test.ts                  # 65 tests

~/.pi/agent/extensions/extra-search.ts          # Brave/Tavily/Serper + dotenv loader
~/.pi/agent/settings.json                        # pi list output lives here
~/.pi/agent/git/github.com/nicobailon/pi-web-access/   # the web access package
~/.pi/agent/npm/node_modules/pi-review/          # /review command package
~/.pi/agent/npm/node_modules/pi-simplify/        # /simplify command package
```

## Verification command (run before claiming anything works)

```bash
cd /p/.pi/pi-risk-policy && npx tsc --noEmit && npx tsx --test tests/*.test.ts
```

Both must exit 0 and pass 74 tests respectively (was 72; +2 for the SAFE_TEXT_EXTENSIONS classifier rule). If they don't, fix before claiming health.

## New commands available in pi

- `/review` — start a new branch from the current conversation and run a maintainer-style review of the available work
- `/simplify` — review recently changed code (via `git diff`) for clarity, consistency, maintainability
- `/reflect <file>` — read recent pi sessions, compare against a target markdown file, apply surgical edits to close gaps between actual behavior and the target. Default target is `AGENTS.md`. Auto-commits to git. `/reflect-stats` shows correction-rate trends + rule-recidivism.
- `/advisor` — pick a reviewer model. Once selected, the `advisor` tool is enabled and the model can hand the current conversation branch to the reviewer before acting. Off by default.
