---
title: "in codex work or code, I created a scheduled task.  How do you do that in claude desktop?"
date: "2026-07-11"
mode: "COPILOT"
uuid: "fe405c71-dced-48de-8189-09fe9b455140"
entry_count: 4
---

## Human

in codex work or code, I created a scheduled task.  How do you do that in claude desktop?

## Assistant

You create scheduled tasks in Claude Desktop through the “Scheduled” / “Routines” UI or by using the `/schedule` skill inside a Cowork/Code session; the flow is different from Codex, but conceptually the same: define a prompt, pick a cadence, and save the task.[1][2][3]

***

## Quick mapping: Codex → Claude Desktop

In Codex you likely used an “Automations” or scheduler surface where you gave the agent a name, a prompt, a folder/repo, and a schedule (hourly/daily/etc.). Claude Desktop now has an equivalent scheduled-task layer for both Code and Cowork that runs prompts on intervals, either on your machine (Desktop-local) or in the cloud (Cowork scheduled tasks). The core idea is the same: “a named routine that re-runs a prompt on a schedule,” but the entry points are different.[3][4][1]

Below I’ll split out the two main ways you can do this in Claude Desktop today.

***

## Method 1: From the Scheduled / Routines page

This is the closest analogue to “go to Codex Automations and create a scheduled job.”

1. Open Claude Desktop (Code or Cowork).
2. In the left sidebar, click:
   - “Scheduled” if you’re in Cowork, or
   - “Routines” / “Scheduled tasks” if you’re in Code, depending on your build.[5][1][3]
3. Click “New task” / “New routine” and choose:
   - “Local” if you want it to run on your desktop (Claude Code Desktop).[1]
   - “Set up manually” if you’re in Cowork’s Scheduled page.[3]

You’ll get a “Create scheduled task” form with fields like:[5][1][3]

- Name: Human-readable name, also used as an identifier.
- Description: Short summary shown in the list.
- Prompt / Instructions: What Claude should do when the task runs; write this like a normal message, including any plugins/skills via `/` if needed.[1][3]
- Model & permission mode: Pick which Claude model and mode the task uses.[2][1]
- Folder / working directory:
  - Desktop: select a trusted local folder; this becomes the task’s working directory.[1]
  - Cowork: you can choose a local folder (runs only when your machine is on) or a cloud/Core project (runs even if your PC is off).[5]
- Schedule / cadence:
  - Manual (only runs when you click “Run now”).[1]
  - Hourly, Daily (time picker), Weekdays, Weekly, etc.[3][5][1]

Save the task; it appears in your Scheduled/Routines list, and Claude will fire it on the chosen schedule as long as the relevant environment (desktop app or cloud) is available.[6][1]

***

## Method 2: Use `/schedule` inside a task/session

If you’re already in the middle of a Code or Cowork task, you can tell Claude to “turn this into a scheduled job” rather than going to the sidebar first.

For Cowork:

1. Start a Cowork task from the “Home” tab.
2. Type `/schedule` in the input while describing what you want scheduled (e.g., “Summarize new GitHub issues in this repo every weekday at 9am”).[3][5]
3. Claude will walk you through multiple-choice questions to nail down:
   - Task name and description.
   - Frequency (hourly/daily/weekly/Weekdays/manual).
   - Whether it runs locally or in the cloud, and which folder/project it should use.[5][3]
4. Confirm when it shows you the task details; Claude creates the scheduled task and adds it to the Scheduled page.[3][5]

For Code Desktop, you can similarly ask in any session:

- “Set up a daily task at 9am that runs tests in this folder.”
- “Schedule a task to run all the tests every 6 hours.”
Claude will either open the Routines/scheduled-task UI prefilled, or call the scheduler tools for you, depending on version.[7][8][1]

***

## Notes specific to Claude Code Desktop

- Local-only execution: Scheduled tasks in Claude Desktop are client-side; they only fire when the desktop app is open at the scheduled time. If you need “always on” behavior, prefer Cowork scheduled tasks configured to run in the cloud rather than desktop-only.[6]
- Task storage: For Code Desktop routines, the prompt/instructions live on disk under something like `~/.claude/scheduled-tasks/<task-name>/SKILL.md` (or under `CLAUDE_CONFIG_DIR`), with YAML frontmatter for metadata. You can edit the prompt body there and use the UI to adjust schedule/model/folder.[1]
- Ad-hoc control: You can list, edit, pause or delete tasks from the Scheduled/Routines page, and via natural language (“show my scheduled tasks”, “pause my dependency-audit task”).[3][1]
- Schedules beyond presets: For things like “every 15 minutes” or “on the first of each month,” the docs explicitly say to just express the schedule in natural language and let Claude set it, even if the UI doesn’t show that preset.[1]

***

## Minimal Codex → Claude translation

Given you already had a Codex scheduled automation, the closest Claude Desktop/Cowork equivalent is:

- Take the Codex automation prompt and paste it into the “Prompt/Instructions” field of a new Claude scheduled task.
- Select the same repo/folder you used in Codex as the working directory.
- Pick the same cadence (hourly/daily/weekly/etc.).
- If you want “always-on” behavior like Codex cloud automations, configure it as a Cowork scheduled task running in the cloud project instead of a pure desktop routine.[4][5][3]

A concrete next step: open Claude Desktop, go to the “Scheduled” / “Routines” tab, and recreate one of your Codex automations by pasting its existing instructions and matching the schedule and folder; once that’s working, you can move other automations over the same way.[5][3][1]

What kind of Codex task did you schedule (e.g., repo checks, CI monitoring, content scraping)?  

## Human

What do you suggest for a library of automated routines?

## Assistant

I’d suggest treating your automated routines as a **small control plane**, not a pile of one-off scheduled prompts. For your workflow, the best library is one that separates event-driven hooks, scheduled monitoring, and reusable prompt/spec templates, because you already prefer low-friction automation over “remember to run this” behavior.[1][2]

## Recommended structure

Use three layers:

- **Hooks** for session-bound automation, like startup health checks, context injection, environment validation, and “what changed since last time?” surfacing.
- **Scheduled tasks** for time-based work, like hourly CI checks, daily repo triage, weekly dependency audits, and recurring research/report generation.[1][2][3]
- **Routine specs** as a prompt/template library, so each automation has a stable contract: trigger, inputs, tools allowed, output schema, failure handling, and where results go.

That split matters because many teams misuse schedules for things that should be hooks, or vice versa. In your case, startup checks belong in hooks, while “look outside the current session and produce a recurring artifact” belongs in scheduled tasks.[3]

## Best routine categories

I’d build the library around 6 routine families:

- **Repo hygiene**: daily issue triage, stale PR review, label suggestions, changelog draft, TODO debt scan.[2][1]
- **Build and release monitoring**: hourly CI failure summaries, deploy regression checks, release-readiness audits, flaky-test watchlists.[1]
- **Dependency and security**: weekly dependency audits, advisory summarization, upgrade batching, license drift review.[2]
- **Architecture and quality**: ADR drift detection, contract/schema health checks, plugin/hook regression scans, verification coverage gaps.
- **Knowledge capture**: weekly transcript summarization, GOAL.md/state rollups, lessons-learned extraction, recurring research digests.
- **Ops and environment**: local model/router health checks, token/cost anomaly scans, tool/server availability summaries.

These categories fit your existing bias toward routing, verification, and minimizing manual ceremony.

## What to prioritize

Start with the routines that have all 4 properties: frequent, annoying, structured, and decision-supportive. Based on your background, these are the highest-ROI first candidates:

| Routine | Trigger | Why it’s high ROI |
|---|---|---|
| CI failure summary | Hourly | Repetitive, time-sensitive, easy to structure into a concise brief.[1] |
| GitHub issue triage | Daily | Ongoing backlog pressure; Claude docs explicitly position scheduled tasks for recurring code-review style work.[2][1] |
| Dependency audit | Weekly | Predictable cadence, bounded scope, naturally produces a report artifact.[2] |
| Session startup health | SessionStart hook | Better as hook than schedule because it should surface only when you begin work. |
| GOAL / state rollup | End-of-session or daily | Matches your interest in automated state tracking and phase shifts. |

I would **not** start with broad “research everything” routines. Claude scheduled tasks work best when the scope is narrow, explicit, and tied to a concrete output.[3]

## Library design rules

Each routine should live as a reusable spec with fields like:

- Name.
- Purpose.
- Trigger type: hook, schedule, or manual.
- Working directory / repo scope.
- Input sources: GitHub, CI logs, files, plugins, local folder.
- Output contract: markdown, JSON, checklist, patch suggestion, issue comment draft.
- Escalation rule: when to notify, when to stay silent.
- Verification rule: what counts as success/failure.[3]

A good naming convention would be:

- `startup.contract-health`
- `repo.issue-triage.daily`
- `ci.failures.hourly`
- `deps.audit.weekly`
- `goal.rollup.daily`
- `router.health.startup`

That makes the library sortable by domain and trigger, and easier to port between Claude hooks, Claude scheduled tasks, and any future orchestrator layer.

## Suggested default stack

For your setup, I’d use this default policy:

- Put **session-coupled checks** in hooks, especially startup advisory, schema health, router/local-model readiness, and context injection.
- Put **recurring external-state scans** in Claude scheduled tasks, especially CI, issues, dependencies, and recurring research/reporting.[1][2][3]
- Keep a **template library** in version control, ideally near your Claude skills/commands, so each routine can be regenerated or migrated without rewriting from scratch.[4]

Confidence: **high** on the structure, **medium** on exact routine order because the right first 3 depends on whether your biggest pain today is repo triage, CI monitoring, or state tracking.[2]

Concrete next step: create just 5 library entries first — `startup.contract-health`, `ci.failures.hourly`, `repo.issue-triage.daily`, `deps.audit.weekly`, and `goal.rollup.daily` — and force each one to have an explicit output schema plus a “stay silent unless actionable” rule.[3]

Would you like me to draft that as a concrete folder structure plus 10 routine spec templates you can drop into Claude?

## Human

what about for non-code life stuff?

## Assistant

For non-code life, think of Claude as a **standing personal ops team**: recurring briefings, planning, cleanup, and reviews that run on a schedule so you only handle the decisions, not the prep.[1][2][3]

***

## Core non-code categories

These are the highest-leverage families of routines people actually use in Cowork and similar setups:[2][3][4][1]

- **Information digestion**
  - Daily briefings from email, calendar, Slack/Discord, and feeds.
  - Weekly “what changed?” reports on finances, subscriptions, or health metrics.
  - Recurring research on topics you care about (AI, markets, travel, etc.).[5][1][2]

- **Planning and prioritization**
  - Weekly review that looks at your calendar, reminders, and goals and proposes a prioritized plan.[4]
  - Next-week planning every Sunday, aligning tasks with goals and constraints.
  - Monthly “goal alignment” audit (are you doing what you said you care about?).[6][4]

- **Digital housekeeping**
  - Folder cleanup: sort downloads or a “to-file” directory into named subfolders.[3][1]
  - Note and doc grooming: consolidate scattered notes into structured summaries.
  - Subscription/expense scan from bank exports or statements.[7][3]

- **Personal logistics**
  - Travel price tracking (flights/lodging on routes you care about).[3]
  - Meal planning and grocery list generation based on recurring constraints (time, budget, diet).[8][6]
  - Appointment management assistance: drafting emails, rescheduling templates, compiling questions for doctors or advisors.[9][6]

- **Reflection and habit support**
  - Daily or weekly journaling prompts with summary + themes.[8]
  - “Mini check-in” systems that nudge you with short questions and log your answers.[8]
  - Mood or energy tracking from simple logs, with patterns surfaced weekly.[8]

***

## Concrete example routines

Here are a few specific routines you could wire in Cowork scheduled tasks (or any comparable system):[10][1][2]

1. **Morning briefing (weekday)**
   - Inputs: email, calendar, a “tasks” doc or reminders.
   - Output: one markdown report saved to `~/Life/Briefings/{date}.md`.
   - Cadence: weekdays at 7:30am.
   - Content: today’s events, prep notes, three highest-priority tasks, any urgent emails to answer.[1][2][10]

2. **Weekly life review (Friday)**
   - Inputs: calendar, goal doc, time-tracking or simple task log.
   - Output: `~/Life/Reviews/week-{date}.md` with sections for wins, misses, drift vs goals, and 3 adjustments.[2][4]
   - Cadence: weekly.
   - Purpose: keep your actual behavior aligned with your stated goals without you manually collating data.[4]

3. **Inbox triage assistant (daily)**
   - Inputs: email snapshot or export.
   - Output: prioritized list of threads, suggested replies for the top N, and a “ignore/archive” list.[6][1]
   - Cadence: daily.
   - Boundaries: draft only; you still send, to retain control.

4. **Files and notes cleanup (weekly)**
   - Inputs: `~/Downloads` or `~/Inbox` folder; notes app exports or a “scratchpad” doc.[11][3]
   - Output: organized subfolders, an index file of what changed, and a “needs human decision” list.
   - Cadence: weekly.
   - Goal: keep digital clutter under control with minimal attention.

5. **Meal and shopping planner (weekly)**
   - Inputs: pantry/fridge inventory snapshot, budget and diet constraints.[6][8]
   - Output: `~/Life/Meals/week-{date}.md` plus `~/Life/Groceries/list-{date}.md`.
   - Cadence: weekly.
   - Benefit: offload menu design and list-making; you only edit and execute.

***

## Design principles for “life” routines

Given your bias toward hooks and contracts, I’d design non-code routines with almost the same rigor as your coding ones:[1][2]

- **Explicit output contracts**: each routine must define where it writes (path, filename pattern, format) and what sections it always includes (e.g., “TODOs”, “Risks”, “Decisions to make”).[1][2]
- **Action-first briefs**: lead with “3 things to do or decide”, not just summaries; Claude is preparing the decision surface, you act.[12][10]
- **Silent-when-no-signal**: routines should produce a minimal “nothing important changed” line if there’s truly nothing, not noise.[13][12]
- **Cadence matched to change rate**: daily for volatile streams (inbox, calendar), weekly for goals and habits, monthly for big-picture life direction.[13][2]
- **Separation of concerns**: one routine per theme (briefing, review, cleanup, planning) so each stays predictable and testable.[2]

***

## Where to start

High-confidence starting set, keeping it minimal but impactful:[2][3][1]

- Weekday **morning briefing**.
- Weekly **life review**.
- Weekly **files/notes cleanup**.
- Weekly **meal + grocery planner**.
- Optional: a nightly **brain-dump organizer** that turns freeform notes into structured tasks and ideas.[10][8]

Concrete next step: pick **one** of those (morning briefing or weekly review), draft a short prompt that makes the output genuinely useful for you, run it once manually in Cowork, then call `/schedule` and set the cadence.[1][2]

Which non-code area feels most worth automating first for you—information digestion (briefings), planning/review, or digital housekeeping?

## Human

Please group all your shceduled task ideas into domains, and bullet point list them.  We don't need an explaination for them, unless you think a 5 year old (that can read) wouldn't understand them.

## Assistant

Here’s a domain-based library of scheduled-task ideas.

***

## Information & Reading

- Daily news summary  
- Daily “AI / tech” update  
- Weekly long-article reading list  
- Weekly “what changed in the world I care about” report  
- Weekly YouTube/watchlist recommendations, based on your interests  
- Weekly “saved links” digest (from bookmarks or a notes file)  

***

## Email, Messages & Communication

- Daily email triage (top messages to answer today)  
- Daily “draft replies” for important emails  
- Weekly inbox cleanup suggestions (newsletters, promos, spam)  
- Weekly “follow-up” list (messages you forgot to answer)  
- Weekly “unsubscribe suggestions” list  

***

## Calendar, Time & Planning

- Morning briefing for today’s calendar and tasks  
- End-of-day summary (“what you did today”)  
- Weekly plan for next week  
- Weekly check for double-bookings and conflicts  
- Monthly “big events coming soon” reminder  

***

## Tasks, Projects & Goals

- Daily “top 3 things to do today” list  
- Weekly review of tasks: done, stuck, postponed  
- Weekly “project status” summary for ongoing work  
- Monthly goal review: progress vs. plan  
- Monthly “new goals ideas” brainstorm  

***

## Money, Bills & Shopping

- Weekly expense summary (from a CSV or export)  
- Weekly list of big or unusual expenses  
- Monthly budget check (spend vs. target)  
- Monthly subscription list (things you pay for every month)  
- Monthly “subscriptions to cancel or review” suggestions  
- Weekly grocery shopping list  
- Weekly meal plan with matching grocery list  

***

## Health, Habits & Self-Care

- Daily habit checklist (sleep, steps, water, etc.)  
- Weekly habit summary (which habits you kept or broke)  
- Weekly exercise log summary  
- Weekly “energy/mood patterns” summary (from a simple log)  
- Weekly suggestions for self-care ideas (walks, breaks, fun)  

***

## Learning & Research

- Weekly “topics to study” list based on your interests  
- Weekly summary of new papers/articles on a topic  
- Weekly skill-practice plan (e.g., coding, language, music)  
- Monthly “learning log” (what you read/watched/practiced)  

***

## Files, Notes & Digital Housekeeping

- Weekly cleanup of Downloads folder (group by type)  
- Weekly sort of a “to file” folder into subfolders  
- Weekly cleanup of screenshots (keep/delete suggestions)  
- Weekly consolidation of scattered notes into one summary file  
- Weekly tagging or labeling of notes (e.g., “ideas”, “tasks”, “references”)  

***

## Life Logistics & Errands

- Weekly errands list (things to do outside the house)  
- Weekly “household chores” checklist  
- Weekly fridge/pantry check (what to use soon, what’s missing)  
- Monthly home maintenance reminders (filters, batteries, etc.)  
- Monthly “people to catch up with” list  

***

## Travel & Fun

- Weekly flight/price watch for specific trips  
- Monthly “trip ideas” list (weekend, day trips, longer trips)  
- Weekly local events summary (concerts, shows, meetups)  
- Monthly “fun things to try” list (new places, activities)  

***

## Reflection, Journaling & Memory

- Daily journaling prompt  
- Weekly reflection summary (highlights, lowlights, lessons)  
- Weekly “gratitude list” builder  
- Monthly memory log (best moments of the month)  

***

## Meta / System Support

- Weekly “automation health” report (which routines are useful, noisy, or broken)  
- Weekly list of new routine ideas based on your recent week  
- Monthly “declutter automations” pass (suggest routines to pause or delete)  

If you tell me which 2–3 domains matter most right now, I can turn these into a concrete starter set with names and file paths.
