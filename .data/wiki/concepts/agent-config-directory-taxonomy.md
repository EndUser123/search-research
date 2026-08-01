---
title: "Agent config directory taxonomy: .agents vs .grok vs .claude vs .codex"
created: 2026-07-22
updated: 2026-07-26
source: session-2026-07-22
last_verified: 2026-07-26
tags: [agent-config, directory-convention, cross-tool, skills, agents-md, skill-md, multi-agent, taxonomy, host-setup, deduplication, symlinks]
summary: >
  The SKILL.md format is an open standard (agentskills.io). As of Jul 2026,
  the .agents/skills/ directory is the cross-agent discovery root — natively
  polled by Codex CLI, OpenCode, Grok Build, and Copilot. Only Claude Code
  does not read it (issue #66352 closed as not planned). CAUTION (added
  2026-07-26b): NO major agent CLI dedupes by resolved filesystem path —
  symlinking/junctioning a skill into multiple scan roots causes duplication
  (Codex/Copilot/Claude/Grok) or non-deterministic last-writer-wins (OpenCode,
  anomalyco/opencode#29950, #32202). Correct strategy: author under a non-
  scanned source dir (e.g. P:/packages/authored-skills/), junction to exactly
  ONE scan root per environment (~/.agents/skills/ for Grok/OpenCode/Codex/
  Copilot; ~/.claude/skills/ separately for Claude Code). Never link into
  two scan roots of the same tool.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/skill-path-resolution-gotcha
    type: refines
  - target: wiki/concepts/context-file-deduplication-agents-md-as-source
    type: related
  - target: wiki/concepts/skill-catalog
    type: related
---

## Summary

Two open standards govern AI agent configuration in 2026: **AGENTS.md** (the cross-tool instruction file, 60k+ repos) and **SKILL.md / Agent Skills** (the cross-tool skill format, agentskills.io). But neither standard mandates WHERE skills live on disk. Each tool has its own directory convention (`.claude/`, `.grok/`, `.codex/`, `.cursor/`). The `.agents/skills/` path is the emerging cross-agent convention — recognized by Copilot and the community, but not yet universally adopted.

## The two open standards

| Standard | URL | What it standardizes | What it does NOT standardize | Adoption |
|---|---|---|---|---|
| **AGENTS.md** | agents.md | A markdown file at repo root for agent instructions (build steps, tests, conventions) | Directory structure; skill format | 60k+ repos; 20+ tools (Codex, Cursor, Claude, Gemini, Devin, Aider, VS Code, etc.) |
| **Agent Skills** | agentskills.io | The SKILL.md format (frontmatter + body), directory structure within a skill | The PARENT directory where skills live | 32+ platforms |

**The gap:** the format is standardized; the location is not. This is the root cause of the path-resolution failures documented in [[skill-path-resolution-gotcha]].

## Directory taxonomy (verified per-tool)

| Directory | Scope | Who reads it | Use for |
|---|---|---|---|
| `~/.grok/skills/` | User (Grok) | Grok Build only | Grok meta-tools (/tp, /plan, /go, /handoff, /design) |
| `P:/.grok/skills/` | Workspace (Grok) | Grok Build only | Project-specific Grok overrides (being phased out) |
| `~/.claude/skills/` | User (Claude) | Claude Code only | Claude user-level skills |
| `<project>/.claude/skills/` | Project (Claude) | Claude Code only | Claude project-level skills |
| `~/.copilot/skills/` | User (Copilot) | GitHub Copilot only | Copilot user-level skills |
| **`~/.agents/skills/`** | **User (cross-tool)** | **Copilot ✅, others proposed** | **Cross-tool skills any agent can use** |
| **`<project>/.agents/skills/`** | **Project (cross-tool)** | **Copilot ✅, others proposed** | **Project-level cross-tool skills** |
| `.codex/` | Project (Codex) | Codex only | Codex config |
| `.cursor/` | Project (Cursor) | Cursor only | Cursor config |
| `.gemini/` | Project (Gemini) | Gemini CLI | Gemini config |

**Key distinction:** `.agents/` is the ONLY directory convention that is explicitly cross-tool. The rest are vendor-specific.

## The .agents/ convention (cross-tool standard as of Jul 2026)

**What `.agents/skills/` IS — natively polled by 4 of 5 major tools:**
- **Codex CLI**: scans `~/.agents/skills/**/SKILL.md` at startup alongside `~/.codex/skills/` [source: openai/codex#20637, May 2026 — quality 10/12; Medium "9 Must-Have Skills for Codex in 2026" corroborates]
- **OpenCode**: scans SIX paths natively — `.opencode/skills/`, `~/.config/opencode/skills/`, `.claude/skills/`, `~/.claude/skills/`, `.agents/skills/`, `~/.agents/skills/` [source: opencode.ai/docs/skills, retrieved 2026-07-26 — authority 12/12]
- **Grok Build**: scans `~/.agents/skills/` and `<project>/.agents/skills/` alongside `~/.grok/skills/` [OBSERVED on this host 2026-07-26: session-start skill list includes `C:\Users\brsth\.agents\skills\agent-performance-analyzer\SKILL.md`]
- **GitHub Copilot**: checks `.agents/skills/` alongside `.github/skills/` and `.claude/skills/` [source: dev.to, 10/12]
- Part of the broader `.agents/` convention: `~/.agents/instructions/`, `~/.agents/skills/`, `~/.agents/agents/` [source: GitHub #66352]

**What `.agents/skills/` is NOT:**
- **Not supported by Claude Code** (issue #66352 closed as not planned) — the lone major holdout
- **Not part of the SKILL.md spec proper** — agentskills.io standardizes the format, not the location; location convergence is happening de facto via vendor adoption, not de jure via spec
- **Case-sensitivity bug in Codex** — must be `SKILL.md` not `SKILL.MD`; Codex silently misses the skill otherwise [openai/codex#20637]

**Practical status (corrected 2026-07-26):** `.agents/skills/` is no longer "emerging" — it is the de facto cross-tool discovery root. The earlier wiki framing ("works with Copilot today, others need manual configuration") is **outdated** as of mid-2026. Codex, OpenCode, and Grok Build all read it natively.

### ⚠️ Common misdiagnosis (refuted 2026-07-26)

A 2026-07-26 OpenCode session claimed: *"P:/.agents/skills/ is just where we authored skills — it's not an authority any runtime polls by default. The only path opencode reads is ~/.config/opencode/skills/."* Both clauses are **wrong**:
1. `~/.agents/skills/` IS polled by Codex, OpenCode, Grok Build natively (see evidence above).
2. OpenCode reads SIX locations, not one. The official docs explicitly list `~/.agents/skills/<name>/SKILL.md` and `~/.claude/skills/<name>/SKILL.md`.

The session also conflated `P:/.agents/skills/` (project-scoped) with `~/.agents/skills/` (user-scoped). They are different scopes: project paths are walked from CWD; user paths are global.

## Decision rule for this host

| Skill type | Where it goes | Why |
|---|---|---|
| Grok meta-tool (/tp, /plan, /go, /handoff) | `~/.grok/skills/` | Grok-specific; only Grok reads it |
| Cross-tool skill (preflight, notebooklm) | `P:/.agents/skills/` (source) → symlink to `~/.agents/skills/` (deploy) | Single source under version control; covers Grok/OpenCode/Codex/Copilot via one symlink target |
| Project-specific tool | `P:/.grok/skills/` (deprecated) or `P:/.agents/skills/` | Depends on whether other tools need it |
| Claude-specific skill | `~/.claude/skills/` or `<project>/.claude/skills/` | Only Claude reads `.claude/skills/` natively (OpenCode also reads it as a compatibility path) |
| Cross-tool instructions | `AGENTS.md` at repo root | The standard; 20+ tools read it |

### Recommended deploy strategy (corrected 2026-07-26b — earlier single-symlink recommendation refuted)

**⚠️ The earlier recommendation (v 2026-07-26) to symlink `~/.agents/skills/` from `P:/.agents/skills/` was wrong.** [OBSERVED: empirical test in session 019f9f48 — both paths are scan roots, no tool dedupes by resolved path] Research on 2026-07-26b confirmed NO major agent CLI dedupes by resolved filesystem path. Linking a skill into multiple scan roots of the same tool triggers known bugs:

| Tool | Bug when same skill reachable via 2 scan roots | GitHub issue |
|---|---|---|
| OpenCode | Dedupes by name (shows once) but **non-deterministic** `<location>` (last-writer-wins across concurrent loads) | `anomalyco/opencode#29950`, `#32202` |
| Codex CLI | Both entries listed in `/skills` (no dedup) | `openai/codex#25324` (open), `#8169` |
| GitHub Copilot | Two subsystems register same path independently (no dedup) | `vercel-labs/skills#1200` |
| Claude Code | Same skill appears twice in autocomplete/context (no dedup; proposed `samefile()` fix not shipped) | `anthropics/claude-code#10115`, `#46833`, `#42384` |
| Grok Build | Same skill appears twice in session skill list (no dedup by name across roots) | Observed locally 2026-07-26: `verification-before-completion` appears at both `~/.agents/skills/` and `~/.grok/installed-plugins/superpowers-21e2a56d/` |

**Corrected pattern (matches the operator's existing convention):**

1. **Source under a non-scanned directory** — e.g. `P:\packages\authored-skills\<name>\` or `P:\packages\.github_repos\agent-skills\skills\<name>\`. Neither is in any tool's scan-root list, so the source files are invisible to discovery.
2. **Junction to exactly ONE scan root per tool.** Same skill can be junctioned into DIFFERENT tools' scan roots (no conflict — each tool sees one entry). Never into TWO scan roots of the SAME tool.
3. **For cross-tool reach:** junction into `~/.agents/skills/<name>` → covers Grok Build, OpenCode, Codex, Copilot in one shot. [OBSERVED] OpenCode docs at https://opencode.ai/docs/skills/ list `~/.agents/skills/` as one of six scan paths; Codex issue openai/codex#20637 confirms `~/.agents/skills/` as Codex global; Grok Build session 019f9f48 skill list includes `~/.agents/skills/agent-performance-analyzer`. Then a SEPARATE junction into `~/.claude/skills/<name>` → picks up Claude Code (and Claude Code only — OpenCode reading `~/.claude/skills/` would create a duplicate for OpenCode, so see caveat below).

```powershell
# Corrected: source OUTSIDE scan roots, junction to ONE root per tool
New-Item -ItemType Junction -Path "$env:USERPROFILE\.agents\skills\www" `
  -Target "P:\packages\authored-skills\www"

# Claude Code needs its own drop — but only if OpenCode is NOT also reading ~/.claude/skills/
# (OpenCode scans ~/.claude/skills/ as a compat path, so this would duplicate for OpenCode).
# To avoid that: set OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 in OpenCode's env,
# OR skip ~/.claude/skills/ and accept that Claude Code doesn't see the skill.
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\www" `
  -Target "P:\packages\authored-skills\www"
```

### Junction vs symlink decision (verified 2026-07-26c)

The 2026-07-26b recommendation ("junctions beat symlinks") was tested empirically against the existing 6 junctions under `~/.agents/skills/` (all created pre-2026-07-21, all healthy as of 2026-07-26c). Results by failure mode:

| Failure mode | Applies to junctions? | Applies to this host? | Evidence |
|---|---|---|---|
| **Grok Build traversal** | NO — 6/6 junctions resolve, SKILL.md reachable | NO | [OBSERVED] `agent-performance-analyzer`, `verification-before-completion`, etc. appear in current session skill list |
| **Node.js `fs.readdir`/`fs.statSync`** | NO — junctions are transparent reparse points; Node follows by default | NO | [OBSERVED] `node -e` test followed all 6 dirs, found SKILL.md in all 6 |
| **Git dereferencing** (`git add` walks INTO junction, commits files; clone loses the link) | YES | NO (junctions live at `~/.agents/skills/` which is NOT inside any git repo) | [OBSERVED via `test_git_junction.py`] `git config core.symlinks = false` on this host; `git ls-files --stage` shows dereferenced files; `git clone` produces plain dirs |
| **OneDrive/Dropbox sync** | YES — sync tools don't reliably traverse junctions; documented infinite-indexing loops | NO (OneDrive is on `D:\OneDrive`, junctions are on `C:\Users\brsth\`) | `coretechnologies.com/blog/onedrive/...` (8/12); `~/.agents/` is not synced |
| **Docker `--volume` mounts** | YES — junctions inside mounts fail with "file cannot be accessed" | NO (no Docker in current toolchain) | `docker/for-win#1205` (9/12) |
| **Drive letter change** (P: reassigned) | YES — junctions are drive-letter bound; target letter change breaks them | LOW risk (P: is workspace root, stable) | Microsoft Learn (12/12) |
| **Codex CLI symlink rejection** | **UNKNOWN for junctions** — issue tested symlinks only; closed as not planned | **UNVERIFIED** | `openai/codex#11314` (10/12): *"Codex CLI does not discover skills when .agents/skills is a symlink. Skills load correctly when .agents/skills is a real directory."* |
| **OpenCode path-resolution check** | **POSSIBLE** — security check rejects skills where resolved path "outside target directory" | **UNVERIFIED** | `upstash/context7#2361` (9/12): Windows-specific failure |

**Bottom line:**
- Junctions are **safe for Grok Build** (the primary consumer on this host) — verified operationally across 5+ days and 6 active junctions.
- Junctions are **safe for the recommended layout** (junction at `~/.agents/skills/`, source outside git/sync) — the documented failure modes don't trigger.
- Junctions are **[OBSERVED — VERIFIED 2026-07-26d]** for Codex CLI and OpenCode on Windows. Prior issues (`openai/codex#11314`, `upstash/context7#2361`) documented link-rejection in those tools but only for symlinks (Codex issue was macOS; OpenCode issue was a setup bug). Junctions specifically work in both — see "Empirical verification 2026-07-26d" below.

**Empirical verification 2026-07-26d (replaces prior "operator should run this test" guidance):**

Both tools were tested non-interactively from inside Grok Build (the claim "I cannot run this from inside Grok Build" was narrative-sufficiency closure — both CLIs have non-interactive diagnostic commands):

| Tool | Command used | Junction-reachable skills found | Duplicates |
|---|---|---|---|
| **OpenCode** | `opencode debug skill` (lists all discovered skills as JSON) | 13/13 junctions under `~/.agents/skills/` resolved | **0** (23 total skills, 23 unique names) |
| **Codex CLI** | `codex debug prompt-input` (renders model-visible prompt including `<skills_instructions>` block) | 12/12 junctions under `~/.agents/skills/` + `P:/.agents/skills/` resolved | **0** (39 total `file:` locators, 39 unique paths) |

Receipts:
- `opencode debug skill` JSON output captured to `P:/tmp/opencode_skills.json` (session 019f9f48)
- `codex debug prompt-input` JSON output captured to `P:/tmp/codex_prompt.json` (session 019f9f48)
- Parser: `P:/tmp/parse_opencode_skills.py`, `P:/tmp/parse_codex_skills.py`

**Disconfirms the prior concerns:**
- `openai/codex#11314` (Codex rejects symlinked skill dirs) does NOT apply to junctions on Windows. The issue was macOS + symlinks. Junctions traverse cleanly.
- `upstash/context7#2361` (OpenCode path-resolution security check rejects "outside target directory") does NOT fire for junction-reachable skills. The check appears to operate on installation paths, not discovery paths.

**Bottom line upgraded:** [OBSERVED — verified 2026-07-26d] junctions are **safe for all 5 environments** (Grok Build, OpenCode, Codex CLI verified empirically this session; Copilot documented; Claude Code N/A — doesn't read `.agents/skills/`). The recommended deploy strategy (source outside scan roots, one junction per tool) is empirically validated, not hypothesized.

**Falsifier:** if either Codex or OpenCode ships a resolved-path traversal check that rejects junctions, junctions stop being a viable deploy mechanism for that tool and real-directory copies (or per-tool `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` style env escapes) become necessary.

**OpenCode-specific workaround** if duplicates unavoidable: set `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` to drop the `.claude` scan root entirely.

**Falsifier:** if any of these issues ships a resolved-path dedup fix (proposed in `claude-code#46833` as `samefile()`), the "one root per tool" constraint loosens for that tool. Re-check issue status before re-introducing multi-root links.

## Conflicts in the ecosystem

**⚠️ Claude Code does not support `.agents/skills/`**
- dev.to (Mar 2026): "Claude Code uses its own `.claude/` directory structure, not `.agents/`."
- GitHub #66352 (Jun 2026): Feature request for `~/.agents/skills/` discovery — **closed as not planned**
- **Resolution:** If you want Claude Code to discover cross-tool skills, symlink or configure manually. The vendor hasn't adopted the convention.

**⚠️ No standard precedence rule**
- When a skill exists in BOTH `.claude/skills/` and `.agents/skills/`, which wins?
- GitHub #66352 proposed: project > user; tool-specific > generic. Not adopted.
- **Resolution:** avoid duplication (per [[skill-path-resolution-gotcha]]). One skill, one location.

**⚠️ Grok Build's directory model differs from the industry**
- Grok uses `~/.grok/skills/` (user) and `.grok/skills/` (workspace) — neither is `.agents/`
- The industry uses `.agents/skills/` (cross-tool) and tool-specific dirs
- **Resolution:** documented in this concept; Grok skills stay at `~/.grok/` because they're Grok-specific (not cross-tool)

## Related

- [[skill-path-resolution-gotcha]] — the failure mode this taxonomy prevents
- [[context-file-deduplication-agents-md-as-source]] — AGENTS.md as single source of truth
- [[skill-catalog]] — auto-generated index of all 970 skills across 21 directories

## Sources

- agents.md (official): https://agents.md/ — authority=3, recency=3, evidence=3, bias=3 → **12/12**
- agentskills.io specification: https://agentskills.io/specification — **12/12**
- **OpenCode Agent Skills docs (retrieved 2026-07-26): https://opencode.ai/docs/skills/** — **12/12**. Authoritative for the six-path discovery list.
- **openai/codex#20637, "Codex skill discovery silently misses global skill" (May 2026): https://github.com/openai/codex/issues/20637** — **10/12**. Confirms `~/.agents/skills/` as Codex global skills location; SKILL.md case bug.
- **anomalyco/opencode#29950, "Skill enumeration is non-deterministic when the same skill is reachable through multiple discovery roots": https://github.com/anomalyco/opencode/issues/29950** — **12/12**. Direct evidence of OpenCode's dedup failure; maintainer-assigned to kitlangton; proposed fix quoted source.
- **anomalyco/opencode#32202, "Skill duplicate roots can change available_skills across restarts" (Jun 2026): https://github.com/anomalyco/opencode/issues/32202** — **11/12**. Corroborates last-writer-wins / concurrent-load race.
- **openai/codex#25324, "Deduplicate skills by parsed frontmatter name" (open May 2026): https://github.com/openai/codex/issues/25324** — **11/12**. Explicit non-dedup statement + suggested fix.
- **openai/codex#8169, "Codex lists every skill twice on macOS" (Dec 2025): https://github.com/openai/codex/issues/8169** — **9/12**. Closed repro; confirms duplicate listing.
- **vercel-labs/skills#1200, "Copilot Chat shows each skill twice when ~/.claude/skills is symlinked to ~/.agents/skills" (open May 2026): https://github.com/vercel-labs/skills/issues/1200** — **10/12**. Root-cause: two subsystems register same path independently.
- **anthropics/claude-code#10115, "Duplicate skills when home == repo root" (Oct 2025): https://github.com/anthropics/claude-code/issues/10115** — **11/12**. Proposes `samefile()` fix; still open.
- **anthropics/claude-code#46833, "Duplicate skills in /context when multiple CLAUDE.md files resolve to same file" (Apr 2026): https://github.com/anthropics/claude-code/issues/46833** — **10/12**. Quote: *"The skill scanner should deduplicate by resolved file path (or skill directory path). Each unique SKILL.md should appear exactly once."*
- **anthropics/claude-code#42384, "Duplicate skills in slash command autocomplete menu" (Apr 2026): https://github.com/anthropics/claude-code/issues/42384** — **10/12**.
- **Node.js fs docs (retrieved 2026-07-26): https://nodejs.org/api/fs.html** — **12/12**. `fs.realpath` resolves symbolic links; Windows junctions transparent to Win32 APIs.
- **Cursor forum, "Duplicate Skills Loading Causing Context Window Waste and Confusion" (Jan 2026): https://forum.cursor.com/t/duplicate-skills-loading/150137** — **11/12**. Real-world Windows agent CLI exhibiting skill dedup failure with junction-mirrored paths.
- debs_obrien, "What Are Agent Skills?", dev.to (Mar 2026): https://dev.to/debs_obrien/what-are-agent-skills-beginners-guide-e2n — **10/12**
- GitHub #66352, "Support user-level .agents/skills/ discovery" (Jun 2026): https://github.com/anthropics/claude-code/issues/66352 — **10/12** (closed as not planned; documents Claude Code as the lone holdout for `.agents/skills/` discovery itself)
- Reddit r/ClaudeAI best-practice quote (Dec 2026): *"The trick is picking one canonical location (I keep a standalone shared-skills folder that both projects link to) so there's always one source"* — **8/12** (practitioner pattern matches corrected recommendation)
- vercel-labs/skills#1025, "Add a repair/relink command to rebuild agent symlinks from ~/.agents/skills" (Apr 2026): https://github.com/vercel-labs/skills/issues/1025 — **9/12** (confirms symlink pattern in active use; tooling emerging)

**Source diversity:** 2 official specs, 1 official vendor doc (OpenCode), 1 official runtime doc (Node.js), 9 GitHub issues across 4 tools, 2 forum/community sources. Disconfirmation pass (search for "any agent CLI that dedupes via realpath gracefully") found ZERO counterexamples — every major tool has the bug class.

**Decision context (why this concept was re-refined 2026-07-26b):** [OBSERVED] the prior refinement (2026-07-26) recommended a single-symlink pattern from `P:/.agents/skills/` to `~/.agents/skills/` claiming it would reach most environments. The operator immediately asked the right question — "does this cause duplication?" — and a follow-up /www run found that very pattern is documented as broken across OpenCode, Codex, Copilot, Claude Code, and Grok Build. The corrected strategy inverts the pattern: source OUTSIDE scan roots, junction INTO exactly one scan root per tool. This matches the operator's existing convention (six junctions from `~/.agents/skills/` into `P:/packages/...`), which was correct by design or by luck — now confirmed correct by evidence.

## Auto-related

- [[skill-catalog]]
- [[grok-build-compat-layer-marketplace-plugin-skills]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
