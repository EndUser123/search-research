---
thread_id: www-proactive-trigger-design
current_session_id: 019f91d3-2741-7f83-af68-211796180474
parent_handoff_path: none
assignee: grok
status: OPEN
created: 2026-07-24
---

# /www Proactive Trigger Design — implementation packet

## Problem

`/www` currently only fires when the user explicitly types `/www`. The skill
has no proactive triggers — no mechanism to suggest research at decision
points where external knowledge would change the outcome. This session proved
the cost: 5 Textual best-practice violations shipped because no `/www` run
happened before coding.

## Design (resolved via /tp this session)

**3 mandatory triggers** (structural enforcement in `/go` and `/refactor`):

| Trigger | Enforcement | Blast radius if skipped |
|---------|-------------|------------------------|
| New library/dependency in code being written | `/go` H3 wiki query already checks; if wiki empty, skill says "no wiki knowledge — consider `/www` before proceeding" and pauses | Entire codebase adopts wrong patterns |
| Destructive operation being added (`shutil.move`, `os.remove`, `drop`, `delete`) | `/go` H1 think-pack item: "does this code perform irreversible operations? If yes, research failure modes first" | Data loss |
| Version upgrade (library major version bump) | `/go` architectural profile alternatives gate; add version-compatibility check step | Entire app silently breaks |

**5 advisory triggers** (suggestions in `/www` SKILL.md):

1. Competitive analysis (before building a feature, research how others do it)
2. Domain knowledge gap (agent makes claims without wiki backing)
3. Pattern research before refactor (`/refactor` already does its own discovery)
4. Repeated failure investigation (same error class 2+ times)
5. Pre-commit verification research (patterns match current best practices?)

**1 scheduled trigger:**

- Wiki staleness audit: quarterly `/www` run on "what's changed in [topic] since [concept date]"

## Two deliverables

### Deliverable 1: Add trigger conditions to `/www` SKILL.md

Add a "Proactive triggers" section listing all 9 triggers with enforcement
level (mandatory/advisory/scheduled) and the skill/step that enforces each.
This is a documentation change — the mandatory triggers are enforced by
existing skills (`/go` H3, H1, architectural profile), not by new hooks.

File: `~/.grok/skills/www/SKILL.md`

### Deliverable 2: Wiki health audit script

`P:/.data/wiki/scripts/wiki_health_audit.py` (~100 lines) that reports:

- **Staleness**: concepts older than 6 months whose `sources:` reference
  library/tool versions (flag for re-research)
- **Coverage gaps**: domains referenced in AGENTS.md/skills that have no
  wiki concept (flag for `/www` research)
- **Orphaned ledgers**: `/www` ledgers whose wiki concept path no longer exists
- **Untriggered research**: libraries used in `P:\packages\` imports that
  have no wiki concept (scan `import` statements, cross-reference wiki)

Run quarterly or before major work.

## What was NOT decided

- Whether the mandatory triggers should be hooks (structural enforcement at
  the tool level) or skill steps (behavioral enforcement in the LLM's
  reasoning). The `/tp` discussion resolved that hooks are stronger but
  the immediate implementation is skill-level. Hook enforcement is a
  future enhancement.
- Whether the wiki health audit script should auto-create `/www` tasks
  for stale concepts or just report. Design assumes report-only; operator
  decides what to act on.

## Key files to read cold

- `~/.grok/skills/go/SKILL.md` — H3 Discover Pack (already has wiki query step we added)
- `~/.grok/skills/www/SKILL.md` — where proactive triggers section goes
- `P:/.data/wiki/concepts/advisory-vs-mandatory-triggers.md` — the principle
- `P:/.data/wiki/concepts/textual-tui-best-practices.md` — proof of cost when triggers don't fire

## Acceptance criteria

- `/www` SKILL.md has a "Proactive triggers" section with all 9 triggers
- Each mandatory trigger names the enforcing skill and step
- `wiki_health_audit.py` runs and produces a report
- Report includes at least: staleness, coverage gaps, orphaned ledgers
