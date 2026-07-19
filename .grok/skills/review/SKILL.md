---
name: review
description: >
  Intelligent code/package review with verified findings on disk. Auto-infers
  target (local diff, branch, PR, or package path) and lenses (correctness,
  integrity, maintainability, security, architecture). Always writes a run_dir
  + FINDINGS.md; severity≥risk findings must be verified against source before
  labeled verified. Use for /review, code review, critical review, package audit,
  PR review, "review my changes", or when /go routes a review-only task here.
when-to-use: >
  /review, code review, critical review, audit package, review PR, review branch,
  review my changes, maintainability review
argument-hint: "[plain language | --local | --branch <name> | --pr <n|url> | --package <path> | --lite | --durable | --focus <lens> | --second-opinion | --adversarial | --plan | --session-aware]"
effort: high
metadata:
  short-description: "Verified findings on disk (intelligent)"
---

# /review — Intelligent verified findings

You are the **review orchestrator**. Prefer **plain language**. Infer target and
lenses; do **not** make the user memorize flags. Bias toward **more** depth when
unsure (user preference), except with `--lite`.

**Product rule:** Review is not complete until findings are **on disk** and
non-nit findings have a **verification** status. Chat is a pointer to the artifact.

## Why paid products charge (what we copy)

Anthropic **Claude Code Review** (Team/Enterprise, research preview) and **OpenAI
Codex Code Review** charge because depth is expensive tokens + multi-step work.
Public docs/claims worth copying (not the price tag):

| Paid product pattern | Why it is “worth money” | Copy into this skill |
|---|---|---|
| **Multi-agent parallel specialists** | Different bug classes; better coverage than one pass | Step 4 specialists by lens |
| **Separate verification step** | Drops false positives before human sees them | Step 5 mandatory verify |
| **Full-repo context, not diff-only** | Catches regressions / call-site breaks | Read surrounding code + AGENTS |
| **High-signal only (logic bugs)** | Style nits burn trust and budget | Correctness first; cap nits |
| **Severity + pre-existing tag** | Separates new vs old bugs | `introduced_by_change` field |
| **Inline PR comments + summary** | Actionable in GitHub UI | Step 7 optional PR post |
| **Repo policy file** (`REVIEW.md` / AGENTS.md) | Team-specific rules without re-prompting | Step 0.5 load policy |
| **Structured JSON + confidence** (Codex) | Machine-postable, filterable | `findings.json` schema |
| **Overall correctness verdict + confidence** | Explicit ship/no-ship signal | FINDINGS.md verdict block |
| **Human stays merge authority** | Never auto-approve PR | Never “LGTM merge” |

We **cannot** copy Anthropic’s managed GitHub App fleet or their trained review
models. We **can** copy the **pipeline contract**: parallel find → verify →
dedupe/rank → durable artifact → optional inline comments.

**Honest limits:** Solo Grok runs use your subscription tokens, not a $15–25
managed bill line-item; quality depends on following verify rules, not marketing.

```text
/review                              # intelligent: dirty tree → local; else ask
/review critical review yt-is        # package + wide lenses
/review my changes                   # local
/review --pr 42                      # PR
/review --lite                       # correctness only, smaller
/review --durable                    # also copy FINDINGS into package docs/ops
/review --second-opinion             # optional external multi-model critique (BYOK)
# optional: --focus maintainability|integrity|security|architecture|correctness
```

---

## Step 0 — Run directory (always first; multi-terminal isolated)

**Canonical root: `P:/.artifacts/`** (workspace convention for ignored, per-run agent
output). Aligns with existing patterns like `.claude/.artifacts/{TERMINAL_ID}/…`
and `P:/.artifacts/research/runs/…`.

**Do not** put packets, specialists, critics, or draft FINDINGS under:

- shared `P:/tmp/grok-review/…` without terminal isolation (legacy; migrate away)
- fixed global folders (e.g. `P:/tmp/grok-review/multi-model-critique/`)
- package `docs/` until the durable step (Step 6)

**Isolation key = terminal first** (concurrent tabs/windows). Session id is recorded
for provenance/join when env provides it — **never invent** either id.

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$slug = "review"   # package name or "local"/"pr-N" after target known
# Isolation identity (first non-empty wins; never invent a fake UUID)
$term = $env:CLAUDE_TERMINAL_ID
if (-not $term) { $term = $env:WT_SESSION }
if (-not $term) { $term = $env:TERMINAL_ID }
if (-not $term) { $term = "noterm" }
$termClean = ($term -replace '[^a-zA-Z0-9_-]','')
$termSafe = if ($termClean.Length -le 36) { $termClean } else { $termClean.Substring(0, 36) }
$sess = $env:GROK_SESSION_ID
if (-not $sess) { $sess = $env:CLAUDE_SESSION_ID }
if (-not $sess) { $sess = "nosess" }
# Layout: .artifacts / <terminal> / grok-review / <slug> / <ts>
# → immune to other terminals; all packets co-located with this run
$runDir = "P:\.artifacts\$termSafe\grok-review\$slug\$ts"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
# specialists/, critics/, packets/ are created LAZILY when first populated.
# For focused reviews (no specialists, no critics, no proposal packet) these
# subdirs are never created. See Step 3.5 (focused tier) and Step 6 artifact
# control for when each subdir is justified by a downstream consumer.
$runDir
```

Write `$runDir/_run.json` (isolation + freshness anchors):

```json
{
  "status": "in-progress",
  "started_at": "<iso>",
  "skill": "review",
  "terminal_id": "<from env or noterm>",
  "session_id": "<from env or nosess — never invented>",
  "head": "<git rev-parse --short HEAD or n/a>",
  "target": "<mode:summary>",
  "run_dir": "<absolute runDir>",
  "artifacts_root": "P:/.artifacts"
}
```

Paths (absolute; **entire run lives under this `run_dir`** — packets are not a
separate root):

| Path | Role |
|---|---|
| `$runDir/findings.json` | Structured findings (source of truth for the run) |
| `$runDir/FINDINGS.md` | Human report for the run |
| `$runDir/specialists/*.json` | Per-lens outputs (deep/package: agent-authored) |
| `$runDir/specialists/_manifest.json` | Spawn log |
| `$runDir/packets/*.md` | Path-only handoff briefs (proposal, verify, critic brief) |
| `$runDir/critics/<model>.md` | Multi-model critic outputs for **this** run only |
| `$runDir/diff.patch` | local/branch/PR |
| `$durablePath` | Optional package `docs/operations/` copy (Step 6) — not the working run |

**Why terminal-scoped `.artifacts` (not only `tmp`):** multi-terminal isolation matches
hook/skill state (`{terminal_id}` trees); ignored by git; survives casual `tmp`
wipes; one root for path-only child prompts.

**Session id:** store in `_run.json` and packet front-matter for joinability. Prefer
**not** as the sole path segment when missing (Grok often has `noterm`/`nosess`);
terminal alone + timestamp is enough isolation. If both exist:
`…/<termSafe>/grok-review/<slug>/<ts>/` remains the path; session is metadata.

### Stale-data immunity (hard)

| Rule | Why |
|---|---|
| **Never read another run_dir’s specialists/critics/packets as live input** unless the user names that path **and** `_run.json.head` matches current `HEAD` (or user waives) | Avoids yesterday’s tree |
| **Never write** to a terminal folder that is not **this** process’s resolved `$termSafe` | Cross-terminal clobber |
| **Never reuse** fixed filenames outside `run_dir` | Cross-session clobber |
| Child writes **only** under this `run_dir` | Sibling agents cannot land in another tab’s tree |
| Prior durable reviews (`docs/operations/…`) = **prior ledger only** | Stale narrative vs live code |
| New `/review` → **new** `run_dir`; do not append into `status=complete` runs | Two reviews merged by accident |
| Record `head` at start; mid-run HEAD change → `head_drift` in `_run.json` before done | Verify against wrong tree |

### Path-only handoff (hard — no inline dossier paste)

**Anti-pattern (forbidden):** Pasting full proposals, full findings JSON, or multi-page
briefs into `spawn_subagent` / `grok -p` prompts.

**Required pattern:**

1. Write full text once under `$runDir/packets/` (e.g. `PROPOSAL.md`, `VERIFY.md`)
   with front-matter: `run_dir`, `head`, `started_at`, `terminal_id`, `session_id`.
2. Child prompt = **absolute paths + short instructions only**, e.g.:

```text
Read these files (do not rely on chat memory):
- P:/.artifacts/<term>/grok-review/<slug>/<ts>/packets/PROPOSAL.md  (sections A–C; follow E)
- P:/.artifacts/<term>/grok-review/<slug>/<ts>/FINDINGS.md  (optional: header + Recommended)
Write your review ONLY to:
- P:/.artifacts/<term>/grok-review/<slug>/<ts>/critics/<model-id>.md
End with REVIEWER: <model-id>
```

3. Transcript pointer: path + **line range or headings**, not transcript body in prompt.
4. Verify agents: paths to `specialists/*.json` under **this** `run_dir` + re-open source
   at current HEAD — never inline JSON bodies.

Multi-model critics (`minimax-m3`, `glm-5-2`, …): BYOK env if needed; path-only
prompts; write only under`$runDir/critics/`.

---

## Step 0.4 — Resume state (terminal-scoped, anti-confusion)

Before collecting evidence, **read the terminal-scoped state file** if it
exists, to understand where this terminal's prior work left off:

```powershell
$term = $env:CLAUDE_TERMINAL_ID
if (-not $term) { $term = $env:WT_SESSION }
if (-not $term) { $term = "noterm" }
$termClean = ($term -replace '[^a-zA-Z0-9_-]','')
$termSafe = if ($termClean.Length -le 36) { $termClean } else { $termClean.Substring(0, 36) }
$stateFile = "P:/.artifacts/$termSafe/yt-is-state.md"   # or <pkg>-state.md
if (Test-Path $stateFile) { Read it; treat Backlog / Last verify as prior context. }
```

If state file HEAD matches current `git rev-parse HEAD` AND last update is
recent, trust it. Otherwise treat as history and update at end of this run.

**Never read another terminal's state file.** Cross-terminal reads are forbidden
by the `.artifacts/<term>/...` root convention.

---

## Step 0.5 — Load review policy (Claude REVIEW.md + Codex AGENTS pattern)

Before specialists run, load **highest-priority** policy text and inject into
every specialist and the verify pass. **Do not require a root-level `REVIEW.md`**
(keep monorepo roots clean).

| File (first found wins for review rules; then merge AGENTS notes) | Role |
|---|---|
| Package `docs/operations/REVIEW.md` or package `.grok/REVIEW.md` | Package-local review rules |
| Repo `P:/.grok/REVIEW.md` (or `<repo>/.grok/REVIEW.md`) | Workspace review policy |
| `~/.grok/REVIEW.md` | User-global fallback |
| Package / repo `AGENTS.md` | Project conventions; new violations → at most `nit` unless REVIEW policy escalates |
| `CLAUDE.md` if present | Same as AGENTS for compat |

**Optional legacy:** only if a package or tool still has root `REVIEW.md`, honor it
for that package — do **not** create root `REVIEW.md` for this monorepo.

If a `REVIEW.md` is found, treat it as **highest priority** for what to flag and at
what severity (same idea as Anthropic’s REVIEW.md injection).

**Default high-signal bar (when REVIEW.md silent):** Prefer **correctness**
bugs that would break production: logic errors, security, broken edge cases,
subtle regressions. Cap inline **nits** at **5**; put the rest as a count in
the summary (“plus N similar nits”). Do not re-report pure lint/format if CI
already enforces it.

---

## Step 1 — Infer target (intelligent)

Parse flags if present; otherwise **infer** from user text + git state.

| Signal | Target `MODE` |
|---|---|
| `--pr` / GitHub PR URL / `#123` as PR | `pr` |
| `--branch <name>` / "branch X" | `branch` |
| `--local` / "my changes" / "this diff" | `local` |
| `--package <path>` / "critical review yt-is" / path under `packages/` | `package` |
| Existing path that is a directory with code | `package` |
| Empty + dirty worktree | `local` |
| Empty + clean worktree | ask once: local vs package path |

**Package resolution examples:** `yt-is` → `P:\packages\yt-is` if it exists.

### Focused default for single-primary-file targets

When the inferred target resolves to a directory, do not automatically treat it as a multi-file package. Apply this rule:

> If the directory contains exactly one obvious primary review artifact (for example, one `SKILL.md`, one `README.md`, one `AGENTS.md`, one `.md` policy file) and the directory has no peer executable modules, hooks, persistence layers, or tests that interact with that primary artifact, **the target is that single file** and the **default depth is `focused`**, not `package`. The directory is consulted only to discover the primary artifact, not as a multi-file audit surface.

The single file is reviewed. Supporting files in the same directory (backups, sibling READMEs, examples) may be inspected when they are referenced by the primary artifact, but they do not change the tier.

Do **not** upgrade to `package` merely because the user supplied a directory. Do not infer deep scope from the directory shape alone. A directory with one primary file is a focused review by default.

Emit:

```text
REVIEW: target=<mode>:<summary> confidence=<high|medium|low>
lenses: <list>
depth: <focused|lite|standard|deep>
tier_reason: <why this depth>
run_dir: <absolute>
```

`tier_reason` is required when the depth is `deep` or when escalation occurs (see Step 3.5); it states the triggering criterion.

---

## Step 2 — Infer lenses (not all-on)

**Always on:** `correctness` + disk artifact + verify pass for severity ≥ risk.

| Signal | Add lenses |
|---|---|
| Default PR / local / "code review" | (+ light architecture if multi-file) |
| maintainability / spaghetti / code-judo / `code-review` alias | `maintainability` |
| security / auth / injection / XSS | `security` |
| critical review / audit / integrity / concurrency / package | `integrity`, `concurrency`, `authority` |
| architecture / control plane / god module | `architecture` |
| thorough / ultrathink / deep | expand (bias more) |
| `--lite` | **only** `correctness` |
| `--focus X` | force that lens on (still keep correctness) |

Do **not** enable every lens every time unless package/critical/thorough.

---

## Step 2.5 -- H1-think for lens selection (ensure nothing missed)

Before spawning specialists, reason about which lenses **could apply** to this
target. The goal is NOT to remove lenses but to ensure none is missed.

Check:
1. Does the diff touch SQLite / shared state? If yes, ensure **integrity** + **concurrency** are both in the lens list.
2. Does the diff touch auth / credentials / cookies? If yes, ensure **security** is included.
3. Does the diff touch multiple callers of a shared API? If yes, ensure **correctness** (call-site breaks) + **architecture** (coupling) are included.
4. Does the diff touch god modules (>1000 lines)? If yes, ensure **maintainability** is included.

**Never remove a lens that could apply.** All applicable lenses run at full depth.
The think step only ADDS lenses; it never subtracts.

When `--adversarial` is on, also add a post-merge adversarial critic pass (Step 5.6).

When `--plan` is on, write the lens plan to `$runDir/packets/LENS-PLAN.md` before
specialists run. User reviews the plan; review pauses until approved or 60s timeout.

**Session-aware (default ON when state file HEAD matches):** if
`P:/.artifacts/<term>/<pkg>-state.md` exists and its HEAD matches current
`git rev-parse HEAD`, inject the session claims (from state file Backlog +
Last verify) into each specialist prompt as **hints** — "the author claimed X."
Specialists still verify against code, but they know what to check. This bridges
`/check` and `/review` without merging them. Use `--no-session-aware` to disable.

---

## Step 3 — Collect evidence

### MODE=local | branch | pr

Collect a unified diff into `$runDir/diff.patch` (same intent as classic review):

- **local:** staged + unstaged + untracked (size-gate: >10MB abort; >1MB confirm)
- **branch:** merge-base with origin/main or origin/master vs target
- **pr:** `gh pr diff` + metadata (requires `gh auth`)

If diff empty: write FINDINGS.md "No changes to review", set `_run.json` complete, stop.

### MODE=package

No full-tree dump. Read:

1. Package `AGENTS.md` / `CLAUDE.md` / `HANDOFF.md` if present  
2. Entry points (README, `bin/`, main modules)  
3. Focused greps for risks implied by lenses  

Optional: light discovery script if ownership unclear — do not load multi-MB JSON whole-file.

---

## Step 3.5 — Depth gate + prior ledger (anti-fast-fake)

After target/lenses are set, record:

| depth | When |
|---|---|
| `focused` | default for single-primary-file targets (see Step 1.5); or `--focused` |
| `lite` | `--lite` only |
| `standard` | default local/branch/PR |
| `deep` | explicit user request OR ≥1 escalation criterion below |

### Escalation criteria (any one is sufficient; record the trigger)

1. User explicitly requested deep, exhaustive, release-grade, or multi-specialist review.
2. The target contains multiple materially interacting executable or policy files.
3. A focused pass found at least two interacting high-impact defects whose combined effect cannot be assessed locally.
4. Independent specialist review is required by an existing safety, release, or governance contract.
5. The decision requires release-grade assurance or irreversible / high-consequence action.
6. The focused review cannot establish a defensible verdict within its evidence budget.

Do **not** escalate merely because: the target is expressed as a directory, several lenses are available, specialists can be spawned, more artifacts could be generated, the review is described as "critical" or "rigorous," or the reviewer can think of additional low-severity findings.

When escalation occurs, write the triggering criterion to `_run.json` field `escalation_trigger`. When no criterion fires and depth stays at the default, record `escalation_trigger: "not_applicable"`.

### Sufficiency stop (apply before each expansion step)

> Stop expanding the review once enough verified evidence exists to support one of: `PASS`, `PASS_WITH_LIMITATIONS`, `NEEDS_TARGETED_FIX`, or `DEEP_REVIEW_JUSTIFIED`. The review must not add lenses, specialists, verification passes, or artifacts after the likely verdict and recommended next action would remain unchanged.

Apply these four questions before each expansion:

1. Is there already a verified blocking or high-impact defect sufficient to determine the verdict?
2. Would another lens or specialist plausibly change the verdict or next action?
3. Is the remaining uncertainty material to the user's decision?
4. Is the expected value of another review step greater than its latency and complexity cost?

If the answer to question 2 or 3 is no, stop. Record in `_run.json`:

- `stop_reason`: short label (e.g. `sufficient_evidence`, `escalation_justified`, `continued_for_completeness`).
- `decision_supported`: `true | false`.
- `additional_review_expected_to_change_decision`: `true | false`.

**Prior ledger (do not skip discovery):** If
`docs/operations/critical-review-*.md` or `review-*-grok.md` exists under the
package, list paths as **prior**. Specialists must **not** receive the full prior
text (avoids rewrite-the-same-review). Parent later merges
`confirmed | closed | new | residual` against prior IDs.

---

## Step 4 — Specialist pass (ENFORCED multi-agent)

### Spawn minimums (tier-driven; not a marker of quality by itself)

| depth / mode | Min `spawn_subagent` calls | Notes |
|---|---|---|
| `focused` | **0** | one reviewer (parent); specialists only if the sufficiency-stop question 2 answer is yes |
| `lite` | **1** | correctness only OK |
| `standard` | **2** | e.g. correctness + one extra lens; parallel preferred |
| `deep` or MODE=`package` (with recorded escalation trigger) | **2–4** (minimum **2**) | parallel `explore` / read-only; one lens per agent preferred |

**Specialist-control rule.** Specialists are not a marker of quality. For focused reviews the default is **zero** specialists; the parent is the reviewer. Permit one specialist only when it supplies a genuinely independent capability or lens likely to change the decision (sufficiency-stop question 2). Require a stated specialist question; do not split generic correctness and maintainability into separate specialists when one reviewer covers both; do not spawn specialists merely to satisfy a deep-review template. Two or more specialists require deep-review justification and a recorded `escalation_trigger`.

**PROCESS FAIL** if `depth=deep` or `MODE=package` and fewer than **2** real
subagent spawns complete successfully:

```text
REVIEW PROCESS FAIL: deep/package requires ≥2 specialist subagents; got N
status: incomplete
```

Write `_run.json` with `"status": "process_fail"`, `"reason": "no_specialists"`.
**Do not** emit `REVIEW DONE` with a success verdict. You may still leave a short
`FINDINGS.md` explaining the process failure.

### Parent must NOT author specialist JSON

- **Forbidden:** orchestrator invents `$runDir/specialists/*.json` from memory or
  prior reviews without a corresponding subagent that used tools on the tree.
- **Required:** each specialist file is produced by a child agent (child writes
  the file, or parent copies **only** the child's tool-backed output into that
  path after the child returns).
- Write `$runDir/specialists/_manifest.json`:

```json
{
  "depth": "deep",
  "spawned": [
    { "lens": "integrity", "subagent_id": "<id>", "subagent_type": "explore" },
    { "lens": "concurrency", "subagent_id": "<id>", "subagent_type": "explore" }
  ],
  "parent_authored_specialist_json": false
}
```

If `parent_authored_specialist_json` would be true for deep/package → **PROCESS FAIL**.

### Blind hunt vs prior

Specialist prompts may include: package path, lenses, REVIEW.md / AGENTS
excerpts, entrypoint hints. **Do not** paste the full prior findings ledger.
Ask them to find defects with tools; prior is for parent merge only.

### Specialist prompts (high-signal, Codex-style, path-only)

Prefer writing a short packet `$runDir/packets/SPECIALIST-<lens>.md` when the brief
is long; otherwise keep the spawn prompt under ~30 lines and **always** pass
absolute write paths.

Every specialist prompt must include:

> You are reviewing a proposed change (or package) made by another engineer.
> Focus on issues that impact **correctness, performance, security, maintainability**.
> Flag **only actionable** issues. Prefer severe issues; avoid nit-level comments
> unless they block understanding. Cite **exact file and line** using tools;
> incorrect citations will be rejected. Do not approve or merge.
> Package/target path: `<absolute>`. Diff (if any): `<absolute run_dir/diff.patch>`.
> Write findings JSON only to: `<absolute path to specialists/<lens>.json>`
> under **this** run_dir (do not write elsewhere).
> Your final message must include that path. Do not set verification fields.
> If you cannot write files, return full JSON in the final message for parent copy
> into that exact path only.

For **diff modes**, also: *only flag issues introduced by this change* unless
tagging `introduced_by_change: false` (pre-existing).

Finding object shape:

```json
{
  "id": "INT-001",
  "severity": "bug",
  "priority": 0,
  "location": "path/to/file.py:123",
  "line_range": { "start": 123, "end": 130 },
  "title": "one line max 80 chars",
  "detail": "2-3 sentences",
  "evidence": "quote or tool observation",
  "fix": "concrete correction",
  "confidence_score": 0.0,
  "introduced_by_change": true,
  "claim_type": "static-shape"
}
```

| Field | Notes |
|---|---|
| `severity` | `bug` \| `risk` \| `suggestion` \| `nit` |
| `priority` | 0 most severe … 3 least |
| `confidence_score` | 0–1 |
| `introduced_by_change` | `false` = pre-existing |

Personas: prepend `~/.grok/personas/sdlc-critic.toml` when available.

---

## Step 5 — Verify pass (mandatory — prefer independent)

**This is the step that justifies expensive reviews.**

### Independence

| Mode | Allowed |
|---|---|
| **Preferred** | Spawn a **new** read-only subagent (`[critic] verify`) that did **not** author specialist findings; pass only **absolute paths** under this `run_dir` (`specialists/*.json`, optional `packets/VERIFY.md`) + instruction to re-read source at current HEAD — **never paste specialist JSON bodies** |
| **Allowed with disclosure** | Parent verifies with tools, but only if specialists were real subagents; set `verify: self` in REVIEW DONE |
| **Forbidden for deep/package success** | Parent invents findings and parent “verifies” them without subagents (`verify: self` + 0 specialists) |
| **Forbidden** | Verifying against specialist files from a **different** `run_dir` / terminal / older HEAD without explicit user resume + head check |

If verify is self on deep/package, still allowed **only when** `_manifest.json`
shows ≥2 spawned agents; disclosure is mandatory.

For **each** finding with severity `bug` or `risk`:

1. Open `location` / line_range (or grep if line moved).  
2. Confirm the defect is real against **actual code behavior**, not naming.  
3. For behavior claims: prefer a small test, mental execution with evidence, or
   mark `unverified` — do not invent runtime results.  
4. Set `verification` and optionally adjust `confidence_score`:

| Value | Meaning |
|---|---|
| `verified` | Re-checked against source this run; confidence typically ≥ 0.6 to surface as Important |
| `unverified` | Could not confirm; keep but flag `[unverified]` — do **not** suppress |
| `non_reproducible` | Source contradicts the claim; **drop** from primary list → Suppressed |

**Drop or demote to nit** if confidence_score < 0.5 after verify, unless severity
is clear `bug` with hard evidence.

`suggestion` / `nit`: verify when cheap; else may stay `unverified`. Cap posted
nits at 5.

**Hard rules:**

- Never label `verified` without a tool-backed re-check in this run.  
- Never auto-approve a PR.  
- Dedupe by (file, line band, title similarity).  
- Merge with prior ledger: `confirmed | closed | new | residual`.

Claim types: `existence`/`scope-completeness` → broad search; `static-shape` →
read; `behavior` → test or honest `unverified`.

---

## Step 5.5 — Optional external second opinion (BYOK multi-model)

**Default: OFF.** Use only when:

- User passed `--second-opinion` / said "second opinion" / "multi-model critique", **or**
- `depth=deep` **and** user has previously asked for external critics this session, **or**
- Critiquing a **proposal/plan packet** (not re-finding bugs with a second tool tour)

**Not for:** lite reviews, mechanical specialist fan-out (keep primary model), or every `/review`.

### Mechanics (path-only, soft-fail)

1. After FINDINGS exist (or when reviewing a plan): write  
   `$runDir/packets/SECOND-OPINION.md` with:
   - front-matter: `run_dir`, `head`, `terminal_id`, `session_id`, `started_at`
   - what to critique (link paths only): `FINDINGS.md` summary + recommended actions, or `packets/PROPOSAL.md`
   - critic instructions (verdict ship/revise/reject, dangers, one falsifier)
2. Child prompt = **paths only** (never paste FINDINGS body).
3. Invoke **1–2** external models when configured (e.g. `minimax-m3`, `glm-5-2` via
   `spawn_subagent` model=… or `grok -m …`). Load BYOK from env / `P:/.env` if needed
   (`MINIMAX_API_KEY`, `ZAI_CODING_KEY` / `ZAI_API_KEY`) — **do not print secrets**.
4. Write outputs only to `$runDir/critics/<model-id>.md`.
5. **Soft skip on auth/failure:** if 401 or model unavailable, record in `_run.json`:
   `"second_opinion": "skipped", "reason": "auth_or_unavailable"` — do **not**
   fail the whole review. Primary verify + FINDINGS still complete.
6. Parent synthesizes agreement/disagreement briefly in FINDINGS.md section
   **“External second opinion”** (or chat if findings already sealed — prefer edit FINDINGS).

**Never** invent session IDs for critic metadata. **Never** use another terminal’s
`critics/` tree.

---

## Step 5.6 -- Adversarial critic (opt-in: `--adversarial`)

After merge + verify, spawn a **red-team critic** subagent that argues AGAINST
the merged findings:

> You are an adversarial reviewer. The review team found N findings. Your job:
> identify what class of bug they ALL missed. Do not re-find the same bugs.
> Look for: blind spots shared by all specialists, missing lenses, assumptions
> that all specialists made, edge cases none tested.
> Write your findings to: `$runDir/critics/adversarial.md`
> End with: BLIND_SPOTS_FOUND: N

Parent adds any new blind-spot findings to `findings.json` with
`source: adversarial_critic` and `severity` set conservatively.

This pass finds **systematic gaps**, not individual bugs. It is the "red team"
layer copied from `/red-team` and Claude Code Review's multi-perspective approach.

---

## Step 6 — Write FINDINGS.md + findings.json (mandatory)

### findings.json (Codex-compatible core)

```json
{
  "findings": [ /* merged verified+unverified, no non_reproducible */ ],
  "suppressed": [ /* non_reproducible with reason */ ],
  "overall_correctness": "patch is correct | patch is incorrect | package needs_attention | package critical | n/a",
  "overall_explanation": "1-3 sentences",
  "overall_confidence_score": 0.0,
  "severity_counts": { "bug": 0, "risk": 0, "suggestion": 0, "nit": 0, "pre_existing": 0 }
}
```

For **diff** modes map: any remaining `bug` with `introduced_by_change: true`
and `verification: verified` → lean **patch is incorrect** unless trivial/docs-only.

### FINDINGS.md

1. Meta: target, lenses, run_dir, HEAD/sha, time, policy files loaded  
2. One-line tally: `bugs: N, risks: M, nits: K (capped)` — lead with  
   **“No blocking issues”** when bugs=0  
3. Summary (2–4 sentences) + verdict: `healthy` | `needs_attention` | `critical`  
4. Findings by severity (bug → risk → suggestion → nit); tag pre-existing  
5. Each: id, location, detail, evidence, fix, **verification**, confidence  
6. Suppressed (non_reproducible)  
7. Claim ledger (required for package/critical)  
8. Recommended next actions — if package has `docs/operations/root-cause-program.md`,
   point implementers there; finding IDs are acceptance cases, not the sole backlog  
9. External second opinion (if Step 5.5 ran): paths to `critics/*.md` + 3-bullet synthesis  

### Artifact production control

Before preserving any artifact, identify its consumer. If no consumer exists, do not generate it by default.

| Tier | Required artifacts | Conditional artifacts (only if a consumer exists) |
|------|-------------------|--------------------------------------------------|
| `focused` | `findings.json`, `_run.json` (and `FINDINGS.md` when the user wants a human-readable report) | none by default |
| `lite` | `findings.json`, `_run.json`, `FINDINGS.md` | none by default |
| `standard` | `findings.json`, `FINDINGS.md`, `_run.json`, `specialists/_manifest.json` | `specialists/<lens>.json` per specialist; `packets/PROPOSAL.md` only if consumed |
| `deep` or MODE=`package` | `findings.json`, `FINDINGS.md`, `_run.json`, `specialists/_manifest.json`, `specialists/<lens>.json` per specialist | `packets/PROPOSAL.md`, `critics/<model>.md` only if explicitly requested or recorded `second_opinion` consumer |

Do not auto-create `specialists/`, `critics/`, or `packets/` subdirectories at run start (Step 0); create them lazily on first write. Do not compute hashes for every intermediate artifact; hash only the artifacts that downstream consumers need to verify integrity for (`findings.json`, `FINDINGS.md`, durable copies).

### Durable copy

When `--durable` **or** MODE=package **or** user said "save findings" / "write to docs":

- If package path known:  
  `<package>/docs/operations/review-YYYY-MM-DD-grok.md`  
  (timestamped if same day exists; **do not silently overwrite** a hand-maintained
  `critical-review-*.md` ledger — link to it as prior instead)  
- Else: leave only under the run’s `P:/.artifacts/<term>/grok-review/...` and tell the user.

---

## Step 7 — PR posting (optional — GitHub App substitute)

If MODE=pr and user wants GitHub comments (or `--comment`): after FINDINGS.md
exists, post a **PENDING** review via `gh api` using only findings with
`verification: verified` (or high-confidence unverified if user insists), and
only lines present on the **RIGHT** side of the diff.

- Never set merge-blocking check conclusion as required for merge.  
- Failure must not delete FINDINGS.md.  
- Prefer PENDING (user submits) over auto-submit.

---

## Step 8 — Final report to user

### Pre-flight for success claim

Before `REVIEW DONE`, check:

1. `findings.json` exists and is non-empty (focused, lite, standard, deep all require this).
2. If `depth=deep` or `MODE=package` (or `depth=standard` with ≥1 specialist): `_manifest.json` has `spawned.length >= 2` (or the documented count for that tier) and `parent_authored_specialist_json == false`.
3. `verify` is `independent` or `self` (self only with #2 satisfied).
4. `new_findings_vs_prior` line is present when a prior ledger was found.
5. `_run.json` includes `stop_reason`, `decision_supported`, `escalation_trigger`, `additional_review_expected_to_change_decision`.
6. Artifacts produced match the tier's required set from Step 6 (artifact production control); no extras without a recorded consumer.

If #2 fails → emit **`REVIEW PROCESS FAIL`** only (see Step 4).

### Success template

```text
REVIEW DONE
target: ...
lenses: ...
depth: focused|lite|standard|deep
tier_reason: <why this depth>
specialists: N spawned (ids: ... | lenses: ...) | n/a (focused)
verify: independent|self|n/a (focused)
stop_reason: <sufficient_evidence|escalation_justified|continued_for_completeness|...>
decision_supported: true|false
additional_review_expected_to_change_decision: true|false
second_opinion: skipped|ran (models: …) | n/a
new_findings_vs_prior: N new / M confirmed / K closed / R residual (or n/a)
verdict: healthy|needs_attention|critical
overall_correctness: ...
findings: N verified, M unverified, K suppressed
artifact: <absolute FINDINGS.md> | n/a (focused without human report)
json: <absolute findings.json>
manifest: <absolute specialists/_manifest.json> | n/a
durable: <path or n/a>
next: ...
```

**Do not** claim review complete without `artifact:` path.  
**Do not** claim deep/package success with `specialists: 0`.

Update `_run.json` to include `status`, `verdict`, `specialists_spawned`,
`verify_mode`, `parent_authored_specialist_json`.

### Recommended next (skill handoff)

Always emit one explicit **next-skill suggestion** based on verdict:

| Verdict | Recommended next |
|---------|------------------|
| `critical` with verified bugs | `/go` to fix by contract (C1/C2/...) — open with the closed-contract ledger |
| `needs_attention` | `/check` to confirm fix targets; then `/go` to fix |
| `healthy` | `/check` to confirm no regressions; merge |
| `REVIEW PROCESS FAIL` | Re-run with at least 2 specialists; respect path-only handoff |

Spell out the literal command. Example:

```text
Recommended next: /check "critical findings on trust-floor/phase-1" then
/go "implement C3 durable merge policy"
```

### Update state file (terminal-scoped)

At `REVIEW DONE`, **update the terminal-scoped state file** so the next session
can resume without confusion:

```powershell
$term = $env:CLAUDE_TERMINAL_ID
if (-not $term) { $term = $env:WT_SESSION }
if (-not $term) { $term = "noterm" }
$termClean = ($term -replace '[^a-zA-Z0-9_-]','')
$termSafe = if ($termClean.Length -le 36) { $termClean } else { $termClean.Substring(0, 36) }
$stateFile = "P:/.artifacts/$termSafe/yt-is-state.md"
# Refresh: updated, branch, worktree, head, last_review_verdict, last_review_artifact
# Update Backlog table: add any new findings / close under contract IDs.
```

If the file doesn't exist, create it. If HEAD has drifted, record `head_drift`.

---

## Maintainability lens (absorbs code-review)

When `maintainability` is active, enforce:

- No unjustified growth of files past ~1000 lines  
- No spaghetti special-case branching in shared paths  
- Prefer delete complexity / code-judo over rearranging mess  
- Flag wrong-layer logic and thin wrappers  

Do not flood with nits when structural issues exist.

---

## Rules

1. Plain language is enough; infer target + lenses.  
2. Read-only on product code (only write run_dir / durable findings / optional PR pending).  
3. No fake `verified`.  
4. **Default to focused**, not deep. Bias more depth only when an escalation criterion fires (Step 3.5).  
5. Empty diff / empty package → short FINDINGS + stop.  
6. One clarifying question max (target only).  
7. This skill **overrides** bundled `/review` when loaded from repo `.grok/skills/review`.  
8. **Deep/package: ≥2 real subagent specialists or PROCESS FAIL.** Focused: 0 specialists by default; 1 permitted only with a stated question.  
9. **Parent must not invent specialist JSON** for deep/package.  
10. **Disclose `verify: self` vs `independent`.**  
11. Prior ledger informs merge only; specialists hunt blind.  
12. **Path-only handoffs:** write packets under `$runDir/packets/`; child prompts get paths, not dossier paste.  
13. **Multi-terminal isolation:** `run_dir` includes terminal segment; no shared fixed critique dirs.  
14. **Stale-data immunity:** never treat another run_dir’s outputs as live without user resume + HEAD match; new `/review` → new `run_dir`.  
15. **Never invent** session/terminal IDs for isolation metadata; use env or `noterm`/`nosess`.  
16. **External second opinion is opt-in** (or deep+explicit); soft-skip on BYOK/401; path-only packets.
17. **H1-think for lens selection:** ensure no applicable lens is missed; never remove lenses.
18. **Adversarial mode** (`--adversarial`): post-merge red-team critic finds systematic blind spots.
19. **Session-aware** (default ON when HEAD matches): inject session claims as hints for specialists; `--no-session-aware` disables.
20. **Sufficiency stop:** before adding a specialist, lens, verification pass, or artifact, ask whether the result would change the verdict or next action; if no, stop. Record `stop_reason`, `decision_supported`, `additional_review_expected_to_change_decision` in `_run.json`.
21. **Artifact control:** do not generate an artifact unless a downstream consumer needs it. Match artifact set to tier (Step 6). Create `specialists/`, `critics/`, `packets/` lazily, not at run start.

---

## Examples

| User | Behavior |
|---|---|
| `/review` (dirty) | local + standard ≥2 agents if multi-file else lite≥1 |
| `/review yt-is` | package + deep → **≥2 subagents** + durable + prior merge |
| `/review --focus maintainability` | local/PR + maintainability lens + spawn min by depth |
| `/review --lite my changes` | local correctness; 1 agent OK |
| `/review --second-opinion` | after FINDINGS: path-only multi-model critics under `run_dir/critics/` |
| `/go critical review foo` | `/go` loads **this** skill; same deep rules |
| `/review --adversarial` | standard + post-merge red-team critic for blind spots |
| `/review --plan` | produce lens plan packet; pause for user approval before specialists |
| `/review --session-aware` | force inject session claims as hints (default ON when HEAD matches) |
