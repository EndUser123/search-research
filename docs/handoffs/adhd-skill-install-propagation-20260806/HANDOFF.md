---
thread_id: adhd-skill-20260806
parent_handoff_path: none
current_session_id: 019fd81d-3012-7762-ab3f-71ac0c992a8b
current_terminal_id: grok-adhd-019fd81d
produced_at: 2026-08-06T07:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: a5b3210d4ec1eb315c33ec50116e8841fec1666f
---

# /adhd skill install + Rule 7 propagation

## Objective

Install and test the i-have-adhd output-style skill on Grok Build, evaluate which of its 10 ADHD-friendly rules are evidence-supported, and propagate the genuinely missing ones into existing skills.

## What now works

- `/adhd` is installed at `~/.grok/skills/adhd/` and invocable next session
- Rule 7 ("make wins visible") is embedded in `/close`, `/handoff`, and `/go`
- SessionStart hook reminds operator that `/adhd` exists
- Clone space convention documented in the wiki

## Status

OPEN — skill installed and 3 skills patched. Testing across live sessions is the remaining work.

## Key decisions

### Decision 1: Opt-in skill, not AGENTS.md or hook

**Choice:** Install as opt-in skill (`/adhd`), not as AGENTS.md rules or a SessionStart hook.

**Selection criterion:** instruction budget compliance.

**Why:** AGENTS.md is already 122K bytes (~30K tokens, ~200+ rules) — past IFScale's "uniform abandonment" threshold (arXiv:2507.11538). Adding rules degrades ALL existing rules. SessionStart hooks are passive on Grok Build (stdout ignored, file:///10-hooks.md:303), so the Claude Code hook-injection pattern doesn't transfer.

**Steelman (rejected):** AGENTS.md always-on block. Stronger per-rule enforcement via system-prompt priority (arXiv:2502.12197). Rejected because every added rule degrades every existing rule in the budget.

**Falsifier:** Grok Build adds a SessionStart context-injection mechanism (not stdout) — hook approach becomes viable and always-on could work.

### Decision 2: Rule 9 rejected

**Choice:** Do not enforce "cap lists at 5 items."

**Why:** ADHD research says working memory is 3-4 items (not 5). And AGENTS.md says "Completeness over curation — list every item with positive ROI." Rule 9 loses on both axes. Resolution: chunk (top 3-4 as "do now"), don't cap.

### Decision 3: Rule 7 propagated to three skills

**Choice:** Only "make wins visible" was propagated. Rules 1 (lead with action), 5 (restate state), 10 (no preamble) were evaluated and found already covered by existing skill output formats.

**Why:** The /tp critique collapsed the 15-edit proposal to 3 edits. Most "ADHD-friendly" rules are already the default output shape (verdict-first, numbered lists, status restated via todo_write).

## Evidence

- IFScale benchmark (arXiv:2507.11538): 20 models tested, best at 68% accuracy at 500 instructions. Our ~200+ rules are in "uniform abandonment" regime.
- Multi-turn decay (arXiv:2505.06120): 39% performance drop across turns. Opt-in injection is less reliable but doesn't compete for system-prompt budget.
- System prompt robustness (arXiv:2502.12197): system prompts have trained priority; user-injected rules don't.
- ADHD rule audit: 5 of 10 rules evidence-supported. Rule 9 contradicted (3-4 items not 5). Rules 8, 10 are style preferences without ADHD-specific evidence.
- AGENTS.md size: 122,727 bytes verified this session via `(Get-Item).Length`.

## Next steps

1. **Test `/adhd` across 3-5 sessions** covering different work types (execution, research, review, planning). Observe which rules actually help vs. feel forced.
2. **After testing, evaluate:** does the operator notice when `/adhd` is active? Do the rules that help match the 5 the research validated (1, 2, 4, 5, 6)?
3. **If Rule 5 (restate state) proves valuable**, consider adding it to `/go` phase progress lines (currently shows phase name only — could add "step X of Y" explicitly).
4. **Wiki concept** at `[[i-have-adhd-skill-implementation-research]]` is the durable reference. Update it after testing.

## Files touched

- `~/.grok/skills/adhd/SKILL.md` (installed)
- `~/.grok/hooks/adhd-skill-reminder.json` (SessionStart reminder)
- `~/.grok/skills/close/SKILL.md` (Rule 7: "What now works" in Completed section)
- `~/.grok/skills/handoff/SKILL.md` (Rule 7: "Lead the body with what now works")
- `~/.grok/skills/go/SKILL.md` (Rule 7: phase lines show what each wave produced)
- `P:/packages/.github_repos/i-have-adhd/` (cloned reference)
- `P:/.data/wiki/concepts/external-repo-clone-space-convention.md` (new)
- `P:/.data/wiki/concepts/i-have-adhd-skill-implementation-research.md` (new, validated)

## Commits

- `~/.grok`: `f7c57bd` — feat: install /adhd skill + add 'make wins visible'
- `~/.grok`: `571b8c5` — fix: 4 review findings (hook matcher, H1, Rule 9 override, bold)
- `P:/`: `c683e9f` — wiki: update /adhd implementation decision
- `P:/`: `6f0fe1a` — wiki: document clone space convention
- `P:/`: `f8528c7` — docs: dream + handoff
- `P:/`: `9806912` — wiki: add review fixes + upstream-override pattern to /adhd concept

## Suggested skills

- `/check` after next `/adhd` invocation to verify rule compliance
- `/tp` after testing to challenge which rules actually helped

---

## Revision 1 — 2026-08-06T20:00Z (session 019fd81d)

**Trigger:** auto-update — review fixes shipped after original handoff was written.

**What changed since the original:**
- `/review` ran (subagent, 33 tool calls). 6 findings: 3 gaps, 3 suggestions, 0 bugs.
- 4 of 6 findings fixed:
  - Hook matcher `startup` → `startup|resume` (F-01: resumed sessions now get the reminder)
  - SKILL.md H1 `# i-have-adhd` → `# adhd` (F-02: matches frontmatter name)
  - Rule 9 workspace override added inline (F-03: AGENTS.md completeness wins over cap-at-5)
  - Handoff stance bullet de-bolded (F-06: consistency with neighbors)
- 2 suggestions deferred:
  - F-04: hook uses inline `python -c` (works, brittle — extract to script later)
  - F-05: Go phase placeholders could leak literally (low risk)
- Wiki concept updated with review fixes + upstream-override pattern
- `/check` passed: 15/15 items verified

**Updated evidence:**
- Review artifact: `P:/.artifacts/grok-review/019fd81d-adhd-session/findings.md`
- Check state: `P:/.artifacts/grok-check/019fd81d-3012-7762-ab3f-71ac0c992a8b/check-state.md`

**Status update:** unchanged — OPEN. Skill installed, review fixes shipped, testing across sessions is still the remaining work.

**New open items:**
- F-05 (go placeholders): shorten `<one line: ...>` to `<findings>` style when editing `/go` next

---

## Revision 2 — 2026-08-06T20:30Z (session 019fd81d)

**Trigger:** auto-update — F-04 resolved, second check + review pass complete.

**What changed since Revision 1:**
- F-04 resolved: extracted hook `python -c` to `hooks/scripts/adhd_skill_reminder.py` (commit `19b59a3`). ruff check passed.
- Second `/check` passed: 18/18 items verified (includes hook script execution + ruff)
- Second `/review` passed: no new findings. 5 of 6 original findings resolved; F-05 remains deferred (low-risk suggestion).
- `/tp do?` + `/tp improve` completed: 8 improvement items surfaced (2 efficiency, 2 effectiveness, 2 insightfulness, 2 thought-partnership). All behavioral — no executable code changes beyond F-04.
- Wiki concept updated to mark F-04 resolved.

**Final commit inventory:**
- `~/.grok`: `f7c57bd` (install), `571b8c5` (4 review fixes), `19b59a3` (hook script extraction)
- `P:/`: `c683e9f`, `6f0fe1a`, `f8528c7`, `9806912`, `d1b5b11`, `190dbb6` (wiki, handoff, dream, clone convention)

**Status update:** unchanged — OPEN. All implementation and review work complete. Remaining work is testing across sessions (next session) and F-05 (low priority).
- `/wiki` to update the implementation concept after testing results come in
