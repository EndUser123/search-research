---
title: "Git hook enforcement — repos and ports for Grok Build (2026-08-13)"
created: 2026-08-13
source: session-019ffd2a (/www research on git hook repos for multi-agent environments)
sources:
  - external: https://github.com/Dicklesworthstone/destructive_command_guard
  - external: https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml
  - external: https://dev.to/pickuma/gitleaks-open-source-secret-scanning-for-git-repos-in-2026-4ceb
  - external: https://www.d4b.dev/blog/2026-02-01-gitleaks-pre-commit-hook/
  - external: https://www.deployhq.com/git/faqs/ai-pre-commit-hooks-git
  - external: https://jonesrussell.github.io/blog/git-hooks-ai-agents/
  - internal: P:/.data/wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md
  - internal: P:/.data/wiki/concepts/multi-agent-destructive-git.md
  - internal: P:/.data/wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
tags: [git-hooks, enforcement, destructive-git, gitleaks, pre-commit, dcg, grok-build, multi-agent, windows]
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
summary: >
  Research identifying repos and implementations for each git-hook enforcement
  gap on this workspace. dcg (destructive_command_guard, 5746 stars, v0.10.0)
  has native Grok Build support and directly addresses the destructive-git
  enforcement gap. gitleaks' official --staged flag replaces the 127s per-file
  scan loop with a single-invocation staged-diff scan. no-commit-to-branch and
  anti-bleed wiring are one-config-entry fixes. The .githooks/ layer (shared
  via core.hooksPath) works for both hosts; the Claude PreToolUse hooks are
  dead under Grok Build (compat.claude.hooks = false) and must be replaced
  with Grok-native JSON hooks or external tools like dcg.
relations:
  - target: wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md
    type: extends
  - target: wiki/concepts/multi-agent-destructive-git.md
    type: implements-enforcement-for
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: applies
---

# Git hook enforcement — repos and ports for Grok Build

## Decision context

**The problem behind this research.** A dirty-tree triage session surfaced 758 uncommitted files from sibling sessions writing without committing. Investigation revealed the enforcement gaps: (1) destructive-git commands (`reset --hard`, `push --force`, `clean -fd`) have zero mechanical enforcement — only AGENTS.md prose; (2) the anti-bleed hook exists but is orphaned (non-standard filename, git never invokes it); (3) gitleaks pre-commit takes 127s because it spawns once per staged file in a bash loop; (4) no branch protection. The question: which repos or implementations can we adopt, and which gaps require building new?

**Key constraint.** `compat.claude.hooks = false` in config.toml — Claude Code's `PreToolUse_git_remote_check_order_guard.py` and other Claude-side hooks are dead in Grok Build sessions. Enforcement must be Grok-native (JSON hooks at `~/.grok/hooks/`) or external (git hooks via `core.hooksPath`).

## Findings: repos for each gap

### Gap 1: Destructive-git enforcement → USE dcg (adopt, not build)

**Repo:** [Dicklesworthstone/destructive_command_guard](https://github.com/Dicklesworthstone/destructive_command_guard) (dcg)

**Why dcg is the right choice:**
- **Native Grok Build support.** `dcg install --grok` writes `~/.grok/hooks/dcg.json` with a PreToolUse/Bash matcher. Grok internally aliases "Bash" to `run_terminal_cmd`, so one rule covers all shell commands. dcg detects Grok at runtime from `GROK_SESSION_ID` / `GROK_HOOK_EVENT` / `GROK_WORKSPACE_ROOT` env vars and outputs Grok's JSON contract: `{"decision":"deny","reason":...}`.
- **Windows-native.** Two default-on packs on Windows: `windows.filesystem` (blocks `Remove-Item -Recurse -Force`, `del /s`, `rd /s`, `format`) and `windows.system` (blocks `vssadmin delete shadows`, `diskpart`). PowerShell installer available (`install.ps1`).
- **Maturity.** 5746 stars, v0.10.0, created 2026-01-07, last pushed 2026-08-11 (2 days before research). Rust binary, sub-millisecond latency, 50+ security packs.
- **Heredoc/inline-script scanning.** Catches `python -c "os.remove(...)"` and `bash -c "git reset --hard"` — the exact bypass pattern an agent might use.
- **Smart context detection.** Won't block `grep "rm -rf"` (data) but will block `rm -rf /` (execution).
- **Bypass mechanism.** `DCG_BYPASS=1` for single-command escape, `dcg allowlist add` for permanent exceptions.

**Disposition:** ADOPT. Do not build new — dcg already covers this gap with native Grok support, Windows packs, and active maintenance. [UNTESTED — not yet installed on this workspace]

**Rejected alternatives:**
- Building a custom `PreToolUse_destructive_git_guard.py` — would be a inferior reimplementation of dcg's 50+ packs, heredoc scanning, and context detection
- `git-safe` (dev.to/boucle2026) — simpler but Claude-only, no Grok support, no Windows packs
- `agent-guardrails` (roboticforce) — terraform/k8s/cloud focused, not git/filesystem
- `tool-guardian` (github/awesome-copilot) — Copilot-only

### Gap 2: Gitleaks performance (127s → <5s) → USE official --staged flag (adapt config)

**Root cause of slowness.** The current `.githooks/pre-commit` runs gitleaks in a bash while-loop, spawning the binary once per staged file: `while IFS= read -r f; do gitleaks detect --source "$f"...`. 416 files = 416 process spawns = 127 seconds.

**The fix.** Gitleaks' official pre-commit hook file (`.pre-commit-hooks.yaml` on master) uses:
```
entry: gitleaks git --pre-commit --redact --staged --verbose
pass_filenames: false
```

This scans the staged git diff (`git diff --cached`) in a SINGLE invocation. No per-file loop. The `--staged` flag is the key — it tells gitleaks to scan only what's about to be committed, not the whole working tree or git history.

**Disposition:** ADAPT. Replace the per-file while-loop in `.githooks/pre-commit` Section 2 with a single `gitleaks git --pre-commit --redact --staged --verbose` call. This also fixes the path-allowlist issue — since gitleaks scans the staged diff (not individual files), path-based allowlists in `gitleaks.toml` match correctly because file paths survive in the finding output. [UNTESTED — not yet applied to this workspace]

**Evidence:** multi-source — official `.pre-commit-hooks.yaml`, dev.to article ("run it with --staged and it checks what git diff --cached is about to commit"), d4b.dev article, gitleaks issue #1522 documenting the old whole-history scan problem.

**Note:** the gitleaks.toml stale comment (lines 11-13, "path allowlists do NOT work") was correct when the hook used stdin scanning but is wrong now that the hook scans per-file or staged diff. If we keep the per-file loop (instead of switching to --staged), path allowlists already work. If we switch to --staged, they also work. Either way, the comment is stale.

### Gap 3: Anti-bleed hook orphaned → FOLD into pre-commit (build fix)

**Problem.** `P:/.githooks/anti-bleed-hook` has sound logic (block ≥5 files or ≥3 top-level dirs) but a non-standard filename git never invokes. Nothing calls it.

**Fix.** Fold its logic into `.githooks/pre-commit` as Section 0 (before gitleaks). The override mechanism (`ANTI_BLEED_OVERRIDE=1 git commit --no-verify`) already exists.

**Disposition:** BUILD FIX — 10-line addition to the existing pre-commit hook. No repo needed.

### Gap 4: Branch protection → USE no-commit-to-branch (config entry)

**The built-in solution.** `pre-commit-hooks` (already in `.pre-commit-config.yaml`) ships `no-commit-to-branch`. One config entry:
```yaml
- id: no-commit-to-branch
  args: ["--branch", "main"]
```

**Disposition:** ADAPT — one entry in the existing `.pre-commit-config.yaml`. [UNTESTED]

### Gap 5: Gitleaks path allowlist for wiki sources → BUILD NEW (gitleaks.toml edit)

**Problem.** `.data/wiki/sources/` contains scraped public docs (Cohere S3 presigned URLs) and YouTube transcripts (educational API-key discussions). Gitleaks flags these as `aws-access-token`, `generic-api-key`, `jwt` — all false positives.

**Fix.** Add a `[allowlist]` section to `gitleaks.toml`:
```toml
[allowlist]
description = "Wiki sources — scraped public docs + public transcripts"
paths = ['''\.data/wiki/sources/.*''']
```

**Disposition:** BUILD NEW — but the config lives under `P:/.claude/**` (permission-denied). Either the operator edits it, or we create a repo-root `.gitleaksignore` (which we CAN write) with per-finding fingerprints. The path allowlist is the cleaner solution if the permission issue is resolved.

### Gap 6: .gitignore for caches → BUILD NEW (config entry)

**Problem.** `.pnpm-store/`, `.logs/`, `.continue/` show as untracked — regenerable caches that shouldn't be tracked.

**Fix.** Add to `.gitignore`.

**Disposition:** BUILD NEW — one-line entries.

## Host invariant check

| Recommendation | Invariant | Status |
|---|---|---|
| dcg | Multi-terminal isolation (each session is independent) | ✅ dcg is stateless per-invocation; no shared state files |
| dcg | Windows paths use forward slashes | ✅ dcg normalizes paths internally |
| dcg | `Remove-Item -Recurse -Force` already deny-ruled in config.toml | ⚠️ Defense in depth — dcg adds a second layer. Potential false positive if agent needs to remove a directory. Bypass: `DCG_BYPASS=1` |
| gitleaks --staged | Windows Git Bash compatibility | ⚠️ [UNTESTED] — gitleaks issue #1532 notes edge cases in blob-/tree-less repos |
| no-commit-to-branch | We commit directly to main by standing policy | ⚠️ CONFLICT — our AGENTS.md says "commit to working branch" but the operator pushes directly to main. This hook would block the workflow. Skip unless the workflow changes. |

## Decision contract

<decision-contract>
schema_version: 1

decision_contract:
  required: true
  reason: consequential_implementation_decision

decision:
  state: CANDIDATE_IDENTIFIED
  proposed_action: REUSE

outcome_without_mechanism: "Block AI agents from executing destructive git/filesystem commands, fix pre-commit performance, and enforce commit hygiene — without relying on prose rules that don't fire under session pressure."

discovery:
  direct_alternatives:
    - candidate: dcg (destructive_command_guard)
      receipt: https://github.com/Dicklesworthstone/destructive_command_guard
      disposition: reuse
      reason: native Grok support, Windows packs, 5746 stars, v0.10.0, active maintenance
    - candidate: gitleaks --staged (official pre-commit hook)
      receipt: https://github.com/gitleaks/gitleaks/blob/master/.pre-commit-hooks.yaml
      disposition: reuse
      reason: single-invocation staged-diff scan replaces 127s per-file loop
    - candidate: no-commit-to-branch (pre-commit-hooks built-in)
      receipt: https://www.deployhq.com/git/faqs/ai-pre-commit-hooks-git
      disposition: reject
      reason: conflicts with our direct-to-main commit workflow
  adjacent_alternatives:
    - candidate: git-safe
      receipt: https://dev.to/boucle2026/git-safe-stop-claude-code-from-force-pushing-your-branch-115f
      disposition: reject
      reason: Claude-only, no Grok support, no Windows packs
    - candidate: agent-guardrails
      receipt: https://github.com/roboticforce/agent-guardrails
      disposition: reject
      reason: terraform/k8s/cloud focused, not git/filesystem
  capability_reuse:
    - capability: destructive-command-blocking
      candidate: dcg
      receipt: https://github.com/Dicklesworthstone/destructive_command_guard
  workspace_existing:
    - candidate: anti-bleed-hook
      receipt: P:/.githooks/anti-bleed-hook
    - candidate: .githooks/pre-commit (gitleaks per-file)
      receipt: P:/.githooks/pre-commit

best_reuse_candidate:
  candidate: dcg
  receipt: https://github.com/Dicklesworthstone/destructive_command_guard
  disposition: REUSE

search_falsifier:
  killer_counterexample: "A simpler built-in mechanism that already blocks destructive git on Grok Build without installing a third-party binary"
  search_executed: true
  receipts:
    - "Searched 6 backends for 'destructive command guard AI agent git hook' — dcg dominated with 5-backend agreement"
    - "Wiki [[grok-build-stop-hook-patterns-and-feedback-mechanism]] already documented dcg as the only real Grok Build implementation (2026-07-27)"

decision_reversing_unknowns:
  - id: dcg-windows-compat
    status: RESOLVED
    falsification: "Install dcg on this Windows host, run dcg test 'git reset --hard', confirm it blocks; run dcg test 'git status', confirm it passes"
    resolution: "dcg v0.10.0 installed on Windows. Binary verified: blocks git reset --hard (exit 0 + JSON deny), blocks git push --force, allows git status. GAP FOUND: dcg does not parse Grok's camelCase input format (toolName/toolInput vs tool_name/tool_input). Wrapper script (dcg_grok_wrapper.py) written to translate. Wrapper verified: deny with exit 2 for destructive, allow with exit 0 for safe. Grok loads hooks at session start only — dcg hook active starting next session."
  - id: gitleaks-staged-windows
    status: RESOLVED
    falsification: "Replace the per-file loop in .githooks/pre-commit with gitleaks git --pre-commit --staged, commit 416 files, confirm it completes in <10s"
    resolution: "418-file wiki commit (785b49c) scanned in seconds (not backgrounded). Verified with controlled test: high-entropy fake API key (sk-ant-api03-..., entropy 5.30) correctly blocked by pre-commit hook via gitleaks git --pre-commit --staged. Low-entropy key (all A's, entropy ~0) correctly rejected by entropy filter — not a gitleaks failure."

evidence_requirements:
  - claim: "dcg has native Grok Build support"
    evidence_required: [document, source_code]
    evidence_present: [document]
    discriminates_competing_explanations: false
  - claim: "gitleaks --staged scans only the staged diff in one invocation"
    evidence_required: [document, source_code]
    evidence_present: [document]
    discriminates_competing_explanations: true
</decision-contract>

## Implementation priority

| Priority | Action | Mechanism | Effort |
|---|---|---|---|
| 1 (CRITICAL) | Install dcg with Grok + Windows packs | `dcg install --grok` | 5 min |
| 2 (HIGH) | Fix gitleaks: switch to `--staged` single-invocation | Edit `.githooks/pre-commit` Section 2 | 10 min |
| 3 (HIGH) | Fold anti-bleed logic into pre-commit Section 0 | Edit `.githooks/pre-commit` | 5 min |
| 4 (MEDIUM) | Add gitleaks path allowlist for `.data/wiki/sources/` | Edit `gitleaks.toml` (needs permission) or `.gitleaksignore` | 5 min |
| 5 (LOW) | Add `.gitignore` entries for caches | Edit `.gitignore` | 2 min |
| SKIP | no-commit-to-branch | Conflicts with direct-to-main workflow | — |
