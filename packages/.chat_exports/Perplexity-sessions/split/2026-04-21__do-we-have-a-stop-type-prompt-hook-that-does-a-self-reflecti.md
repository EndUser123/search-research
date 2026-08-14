---
title: "'Do we have a stop type prompt hook that does a self-reflection step?  to make sure that we're not being obviously stupi"
date: "2026-04-21"
mode: "CONCISE"
uuid: "b1d06fd4-f2e8-49d4-bcc7-560c8ddbdb6a"
entry_count: 4
---

## Human

"Do we have a stop type prompt hook that does a self-reflection step?  to make sure that we're not being obviously stupid when we answer.
Checking the hooks directory for stop-type hooks.
Found files
Yes — Stop_self_reflection_gate.py exists. Let me read it.
ReadStop_self_reflection_gate.py
Broader structural question: Is the self-reflection gate actually wired into the Stop router and running, or is it an orphaned file?
Yes — Stop_self_reflection_gate.py exists. It's advisory-only (never blocks, always "allow": True). It scans responses for low-confidence hedging words (probably, likely, seems, etc.) within claim-like sentences and prints a console warning if found.
However, its effectiveness is limited — it only flags uncertainty markers in the response text, not reasoning quality. It won't catch confidently-wrong answers. The StopHook_reasoning_quality_gate.py and StopHook_unverified_stance.py likely cover more of what you're describing.
Want me to check if Stop_self_reflection_gate.py is registered in the Stop router?
Yes, please.
Read a file, searched code
Not in the router. Checking settings.local.json and settings.json for direct registration.
Searched code
Stop_self_reflection_gate.py is not registered anywhere — it's an orphaned file that never runs.
What is registered is a different hook: posttooluse_self_reflection_reminder.py as a PostToolUse hook in settings.json:236. That fires after tool calls, not after responses.
So: no Stop-phase self-reflection gate is currently active."


in claude code what would be some good self-reflection stop hooks?

## Assistant

Yes — the best **self-reflection stop hooks** in Claude Code are the ones that verify the answer before the turn ends, not just the ones that notice hedging words. Claude Code’s `Stop` hook fires when Claude finishes responding, and it can block stopping by exiting `2` or return structured JSON such as `{"continue": false, "reason": "..."}` to force another pass.[1][2]

## What a good Stop self-reflection hook should do

A useful Stop hook should check for failure modes that actually matter:

- Confident unsupported claims.
- Missing caveats when the answer is uncertain.
- Contradictions with earlier statements in the same response.
- Overclaiming about code, docs, or current state.
- Answers that look complete but skipped a required step.

That’s stronger than a “hedging-word detector,” which mostly catches words like “probably” or “likely” and can still miss confidently wrong answers.[2][1]

## Good patterns to implement

1. **Claim verification gate.**  
   Ask a model or script whether the response contains factual claims that are not supported by retrieved evidence, then block stopping if the answer is too speculative. Claude Code’s Stop hook is explicitly designed to let you continue the conversation when the hook says not to stop.[1][2]

2. **Uncertainty calibration gate.**  
   Require the assistant to label uncertain statements explicitly and separate facts from speculation. This is better than looking only for hedging words, because it checks whether uncertainty is *handled* rather than merely *mentioned*.[1]

3. **Completeness gate.**  
   For task-oriented work, require a checklist of requested sub-questions or deliverables and block stopping if any are missing. Community examples commonly use Stop hooks to ensure code is tested or linted before the model finishes.[3][4][5]

4. **Contradiction check.**  
   Have the hook scan for internal inconsistency, such as saying both “I checked the router” and “it is not registered” in adjacent claims, or asserting a file exists but also that it is orphaned. A Stop hook can be used to force another pass when the final answer is inconsistent or incomplete.[2][1]

5. **Evidence-backed answer gate.**  
   If the task involved web, repo, or file inspection, require that every nontrivial claim be backed by a source or by cited code/file content. Claude Code hooks support using the turn-ending stage as a quality gate, which fits this pattern well.[2][1]

## A practical implementation stack

The strongest setup is usually a **two-layer gate**:

- Layer 1: deterministic checks for obvious issues, like missing sections, banned phrases, or absent citations.
- Layer 2: a lightweight LLM critique that asks, “What is the most likely thing this answer gets wrong or omits?”

That gives you a cheap first pass and a smarter second pass. A Stop hook can then block completion only when either layer finds a serious problem.[1][2]

## Prompt to use in the hook

A solid critique prompt is something like:

- “Inspect the answer for unsupported factual claims, hidden uncertainty, contradictions, and missing required steps.”
- “Return `continue=false` only if the answer would mislead the user or fail the task.”
- “Otherwise return `continue=true` with one short improvement note.”

That fits the documented Stop-hook continuation model, where the hook can tell Claude to keep working instead of ending the turn.[2][1]

## My recommendation

If your goal is “don’t be obviously stupid,” I’d rank hooks like this:

1. **Contradiction checker.**
2. **Unsupported-claim checker.**
3. **Task-completeness checker.**
4. **Uncertainty calibration checker.**
5. **Hedging-word detector** as a weak fallback only.

The hedging detector is useful, but it should be the smallest part of the system, not the core.[1][2]

## Best next step

Build one Stop hook that runs a compact self-critique prompt over the final answer and blocks only on high-confidence problems, then add one deterministic regex pass for obvious overclaiming or missing citations. That gives you a robust self-reflection gate without turning every response into an infinite loop.[2][1]

Would you like a concrete `Stop` hook script plus a critique prompt tuned for Claude Code?

## Human

Yes, please.

## Assistant

Below is a practical **Stop-hook self-reflection gate** you can drop into Claude Code and tune. It assumes the modern hook model where `Stop` can emit structured JSON like `{"continue": false, "stopReason": "..."}` and that hooks receive JSON input on stdin.[1][2]

## Recommended design

Use one small script that does two things:

- Runs a fast deterministic check for obvious failure modes.
- Optionally asks a lightweight critique model to judge whether the response is misleading, incomplete, or overconfident.

That matches Claude Code’s hook pattern: exit 0 with structured output for normal control, or block with `continue: false` when you want another pass.[2][1]

## Example hook script

```python
#!/usr/bin/env python3
import json
import os
import re
import sys

HEDGES = [
    r"\bprobably\b", r"\blikely\b", r"\bperhaps\b", r"\bseems\b",
    r"\bappears\b", r"\bmaybe\b", r"\bmight\b", r"\bI think\b",
]
OVERCLAIM = [
    r"\balways\b", r"\bnever\b", r"\bguaranteed\b", r"\bdefinitely\b",
    r"\bobviously\b", r"\bimpossible\b", r"\bwithout exception\b",
]

def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    if payload.get("stop_hook_active"):
        sys.exit(0)

    text = payload.get("assistant_response") or payload.get("response") or raw
    t = text.lower()

    hedge_hits = sum(bool(re.search(p, t)) for p in HEDGES)
    overclaim_hits = sum(bool(re.search(p, t)) for p in OVERCLAIM)

    risky = 0
    reasons = []

    if overclaim_hits >= 2:
        risky += 2
        reasons.append("Multiple absolute/overconfident claims detected.")

    if hedge_hits >= 3 and overclaim_hits == 0:
        risky += 1
        reasons.append("Heavy uncertainty language may indicate weak grounding.")

    if re.search(r"\b(?:I checked|I verified|I confirmed)\b", t) and not re.search(r"\b(?:source|citation|file|line|doc|evidence)\b", t):
        risky += 1
        reasons.append("Verification language appears without supporting evidence.")

    if risky >= 2:
        msg = "Self-reflection gate: " + " ".join(reasons) + " Re-check claims, evidence, and completeness before stopping."
        sys.stderr.write(msg + "\n")
        print(json.dumps({"continue": False, "stopReason": msg}))
    else:
        print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
```

This is intentionally conservative: it only blocks when the response looks meaningfully risky, which reduces the chance of infinite self-reflection loops. Claude Code’s docs and community examples show that Stop hooks can be used to force continuation, but they also warn that overly aggressive gating can loop or behave unexpectedly.[3][4][2]

## Stronger critique prompt

If you want the hook to use an LLM instead of only regex, use a short prompt like this:

```text
You are a Stop-hook self-critique gate for Claude Code.

Task:
Evaluate the assistant response for:
1. Unsupported factual claims.
2. Contradictions or internal inconsistency.
3. Missing required steps or incomplete answer.
4. Overconfidence where uncertainty is warranted.
5. Claims that should be caveated but are not.

Return ONLY valid JSON:
{
  "continue": true|false,
  "stopReason": "short explanation",
  "risk": "low|medium|high",
  "issues": ["..."]
}

Rules:
- Return continue=false only if the response is likely misleading, incomplete, or materially wrong.
- Do not block for style issues alone.
- Prefer false negatives over false positives.
- If the response is acceptable, return continue=true.
```

That prompt is aligned with the documented structured-output model for hooks and with the practical goal of a late-turn quality gate, not a stylistic nag.[1][2]

## Better version for your workflow

Given your repo/tooling style, I would make the gate **evidence-aware** rather than generic:

- If the answer contains claims about code state, require file/line evidence.
- If the answer contains “I checked” language, require a concrete artifact or citation.
- If the answer is advisory, require an explicit uncertainty label.
- If the answer is task-completion oriented, require checklist completion.

That is more useful than a generic “don’t sound dumb” rule, because it catches the real failure modes: false certainty, missing evidence, and incomplete work. Claude Code’s Stop hook can enforce that last-mile quality control as part of the turn-ending lifecycle.[2][1]

## Wiring suggestion

For reliability, keep the gating logic in two layers:

1. **Deterministic prefilter** in Python.
2. **Optional critique model** only when the prefilter sees risk.

That way the hook stays fast and cheap most of the time, while still catching answers that are confidently wrong or incomplete. Stop hooks are powerful, but the docs and issue reports suggest you should keep the logic simple enough to avoid JSON/schema mistakes and unintended blocking.[5][6][1]

## Practical starting threshold

A good default is:

- `continue=true` for low-risk answers.
- `continue=false` only when there are at least two serious signals, or one severe signal.
- Severities: unsupported factual claim, contradiction, missing requested deliverable, or overconfident verification language without evidence.

That keeps the hook from becoming a perfectionist loop machine while still improving answer quality in the places that matter most.[7][3][2]

Would you like me to turn this into a Claude Code `settings.json` hook entry plus a repo-ready script path layout?

## Human

How about we let Claude Code figure out where to put them and what to call them and how to register them.  Remember, I'm on Windows 11 and if it applies, I want to be immune to fail data, be multi-terminal isolated, and be immune to workflow interruption caused by compact events.

## Assistant

Yes — if you want Claude Code to decide **where hook files live, what they’re called, and how they’re registered**, the best approach is to give it a **policy/spec**, not fixed filenames. Put the policy in your personal Claude instructions or a bootstrap note, and tell it to choose paths that respect Claude Code’s config precedence: user settings at `~/.claude/settings.json`, shared project settings at `.claude/settings.json`, and personal-per-project overrides at `.claude/settings.local.json`, where local scope overrides project and user scope.[1][2]

## Best placement policy

For your constraints, I would tell Claude Code to follow these rules:

- Put **personal, machine-specific, Windows-specific, and interruption-hardening hooks** in `~/.claude/` so they apply everywhere on your Windows 11 machine.[2][1]
- Put **team-shared, repo-relevant hooks** in `.claude/` inside the project so they can be versioned with the repo.[1][2]
- Put **experimental or repo-local personal overrides** in `.claude/settings.local.json` so they do not leak into git and can safely differ per terminal/project.[2][1]

That gives you the right separation for multi-terminal work: project-safe shared defaults in repo config, and personal resilience features in user or local scope so one project does not accidentally contaminate another.[1][2]

## What to tell Claude Code

Give Claude Code a directive like this:

- “Choose hook file names and locations automatically.”
- “Prefer `~/.claude/hooks/` for user-global resilience hooks.”
- “Prefer `.claude/hooks/` for repo-scoped workflow hooks.”
- “Register them in the narrowest scope that satisfies the purpose.”
- “Do not assume Linux paths; generate Windows-safe paths and commands.”
- “Preserve terminal isolation by avoiding shared mutable temp files unless they are session-keyed.”
- “Preserve compact-event resilience by using `PreCompact` plus `SessionStart` with compact-aware restoration when needed.”

This works because Claude Code supports multiple scopes and hook lifecycle events including `stop`, `pre_compact`, and `session_start`, and session-start hooks can be used to restore context after compaction or resume events.[3][4]

## Hooks that fit your constraints

For your three explicit goals, I would ask Claude Code to create these classes of hooks:

| Goal | Hook type | What it should do |
|---|---|---|
| Fail-data immunity | `Stop` + `PostToolUse` | Refuse unsupported claims, require evidence markers, and persist critical findings before stop. [5][6] |
| Multi-terminal isolation | `SessionStart` + per-session state | Use terminal/session-specific state files keyed by session ID, cwd, or terminal identifier so concurrent terminals do not overwrite each other. Hook systems expose session/project context in event payloads, which supports this pattern. [3] |
| Compact interruption immunity | `PreCompact` + `SessionStart` with compact matcher | Save authoritative working state before compaction, then re-inject or restore it immediately after compaction/resume. Community guidance specifically uses `SessionStart` with compact-aware matching for this purpose. [4][3] |

That combination is much stronger than a single self-reflection stop hook, because it protects not just answer quality but continuity of work across interruptions.[4][3]

## Recommended operating model

I would have Claude Code implement a **three-layer resilience system**:

1. **Stop self-reflection gate** for final-answer sanity checking.[5][6]
2. **PreCompact state snapshot** that writes an authoritative mini-state file before compaction. `pre_compact` is a recognized lifecycle event in hook ecosystems built around Claude Code.[3]
3. **SessionStart restore hook** that detects resume/compact startup and reloads the latest authoritative state into context. Community examples show `SessionStart` can add restoration context after compaction.[4]

This is the architecture most aligned with your stated priorities, because “being less stupid” is only one part of the problem; the larger problem is preserving correctness under interruption and concurrent terminal usage.[3][4]

## Windows-specific guidance

Because you are on Windows 11, tell Claude Code to prefer one of these patterns:

- Python hook entrypoints, because Python scripts are more portable across Windows shells than bash-heavy hooks. Windows compatibility concerns matter in practice when hook commands are shell-invoked.[1]
- If shell wrappers are needed, generate PowerShell-compatible wrappers rather than assuming `/bin/bash`.
- Normalize paths and avoid assumptions about `/tmp`; use project-local or user-local directories under `.claude/` or `~/.claude/`.
- Use atomic writes and session-keyed filenames so one terminal does not clobber another terminal’s state.

Those choices are not directly mandated by the docs, but they follow from the documented multi-scope configuration model and from your Windows/multi-terminal constraints. **FACT:** scope separation exists. **SPECULATION, high confidence:** Python-first hooks plus session-keyed files are the safest implementation style for your environment.[2][1]

## Concrete spec you can paste

Use this as your instruction to Claude Code:

```text
Design and install Claude Code hooks automatically.

Requirements:
- You decide filenames, directories, and registration points.
- Use the narrowest correct scope:
  - ~/.claude/ for my personal machine-wide hooks
  - .claude/ for repo-shared hooks
  - .claude/settings.local.json for my personal repo-local overrides
- I am on Windows 11, so generated commands and paths must be Windows-safe.
- Prefer Python hook scripts over bash unless there is a strong reason otherwise.
- I want:
  1) a Stop self-reflection gate that catches unsupported claims, contradictions, and incomplete answers
  2) compact-event resilience using a PreCompact snapshot and SessionStart restoration path
  3) multi-terminal isolation using session-keyed state so concurrent terminals do not overwrite each other
  4) immunity to fail-data by persisting authoritative working state before risky transitions
- Avoid orphaned hook files: after creating anything, verify it is actually registered in the effective settings.
- After installation, show me:
  - where each file was placed
  - which settings file registered it
  - which scope won by precedence
  - how terminal isolation is achieved
  - how compact recovery is achieved
```

That instruction is precise enough to let Claude Code choose names and locations intelligently, while still forcing verification so you do not end up with another orphaned hook. Scope precedence and the existence of compact/session lifecycle hooks are documented, so this spec is grounded rather than hand-wavy.[4][3][2][1]

## One caution

Do **not** ask Claude Code to put everything in one global settings file by default. That is convenient, but it weakens isolation and makes project behavior less predictable when multiple repos need different hook policies. The documented precedence model exists specifically so you can separate user-global defaults from project-shared and local overrides.[2][1]

## My recommendation

Your default policy should be:

- **Global in `~/.claude/`**: compact-resilience framework, session-isolation primitives, Windows-safe utility hooks.[1][2]
- **Project in `.claude/`**: repo-specific quality gates and task-completion hooks.[2][1]
- **Local override in `.claude/settings.local.json`**: experiments, stronger personal gates, temporary tuning.[1][2]

That gives you the best mix of portability, resilience, and isolation for a Windows 11 multi-terminal workflow with compaction interruptions.[3][4][1]

If you want, I can next write the **exact master instruction/policy prompt** you should give Claude Code so it installs this whole hook architecture by itself.

## Human

"Authoritative working state before risky transitions" , we should define this.

## Assistant

Working definition, tuned for your use case:

> **Authoritative working state** is the *single, minimal, source-of-truth summary* of what’s currently true about the work, such that if everything else (chat, scratch reasoning, partial edits) vanished, you could *reconstruct the session correctly* from that state alone.  

> **Before risky transitions** means *right before events that can corrupt, lose, or desync context* — especially Claude Code compaction, session end, or cross-terminal handoff.[1][2][3][4]

I’ll break that into something operational.

***

## 1. What is “authoritative working state”?

In Claude Code + repo terms, **authoritative working state** is *not* “whatever’s in the last 200 messages of the chat.” It’s a deliberately maintained artifact (or small set of artifacts) with these properties:

1. **Single source of truth**  
   - One clearly designated place (or a small, well-defined set) that Claude and you both treat as the canonical record.  
   - Typical implementations in the wild use a file like `docs/session-state.md` or a JSON/YAML state file that hooks read/write.[5][4]

2. **Enough to reconstruct the session**  
   It must capture at least:
   - Current **task / subtask** and its status.  
   - **Key decisions & rationale** (why we chose path A over B).  
   - **Files touched + their current role** (what changed, where the main logic lives).  
   - **Invariants and constraints** (assumptions we must not violate).  
   - **Next concrete actions** (the next 1–3 steps).  
   This matches patterns used by PreCompact/SessionStart state files described in community guides.[2][4][1]

3. **Stable vs. volatile separation**  
   - Stable: decisions, target architecture, accepted interfaces, contract shapes, key invariants.  
   - Volatile: individual prompts, partial thoughts, one-off scratch code.  
   The authoritative state only needs *stable* facts; volatile noise can be regenerated. This distinction is what people lean on when they build session-state documents that survive compaction.[4][1]

4. **Machine-usable**  
   - Structured enough (headings, bullets, or fields) that hooks and Claude can both read and update it deterministically.  
   - E.g., a fixed template in `session-state.md` with sections like “Current Task”, “Decisions”, “Files”, “Next Steps”, which a PreCompact hook can explicitly remind Claude to update.[5][4]

5. **Repo-aware + session-aware**  
   - Tied to repo and, for you, ideally also terminal/session (e.g., `docs/session-state.<session-id>.md`), so multiple simultaneous sessions don’t trample each other. Hook guides show patterns where project and session context are included in the hook payload and used to select the right state file.[4][5]

So: **“authoritative working state” is your intentional `session-state` artifact(s), not the conversation log.**  

***

## 2. What counts as a “risky transition”?

From Claude Code’s lifecycle and community patterns, the risky transitions are the ones where **context can shrink, disappear, or diverge**:[3][1][2][5][4]

1. **Auto-compaction events**  
   - Claude Code fires `PreCompact` right before it compacts the conversation.[1][3][5]
   - After compaction, lots of “what did we decide 40 messages ago?” vanishes unless it was externalized.  
   - Community patterns explicitly treat PreCompact as “critical moment: persist state now.”[2][1][4]

2. **Session end / terminal close / IDE restart**  
   - Hooks like `SessionEnd` and `SessionStart` are commonly used as bookends to ensure that what matters is written down before a session is gone and re-loaded later.[4]
   - For you this includes “I just kill this terminal” and “Claude Desktop restarts” scenarios.

3. **Cross-terminal or cross-session handoff**  
   - When you pick up work on the same repo from a different Claude session or terminal, the in-session chat history is effectively a different universe.  
   - If state isn’t in a shared artifact, the two universes diverge.

4. **Major branch/structural transitions**  
   - Examples: switching Git branches, restructuring directory layout, major refactor, or swapping architectures.  
   - If the state file doesn’t capture “we changed the world in this way,” subsequent compaction or resumes will act as if both worlds exist simultaneously.

5. **High-risk operations where errors are expensive**  
   - E.g., mass edits, schema changes, deleting files.  
   - You may also want to mark these as “risky transitions” so that self-reflection + state persistence happen *before* they execute.

So a hook-level definition:

> A **risky transition** is any lifecycle point where Claude Code’s internal context can be compacted, discarded, or forked (PreCompact, SessionEnd, cross-session resume), *or* where the project state undergoes large, hard-to-undo changes (branch switches, mass edits).

***

## 3. Putting the definition into a spec for hooks

If you want hooks to operationalize this, you can define it like this in your policy:

**Definition block for Claude Code:**

```text
“Authoritative working state”:
A minimal, canonical state artifact (or small set of artifacts) per project and session that contains:
- Current task and subtask
- Key decisions and their rationale
- List of relevant files and what role they play
- Known invariants / constraints that must not be violated
- Next 1–3 concrete actions

It must be sufficient to reconstruct the session’s intent and direction after:
- full context compaction
- IDE / terminal restart
- cross-session or cross-terminal handoff

The authoritative state lives in structured files (e.g., docs/session-state[.<session>].md)
that both hooks and Claude can read and update.

“Risky transitions”:
Any event where context can be lost or desynchronized, including:
- PreCompact (before Claude Code auto-compaction)
- SessionEnd (before session termination)
- Cross-session or cross-terminal handoff
- Major branch changes or large-scale refactors
- Other high-impact operations designated by hooks

Policy:
- Before each risky transition, ensure the authoritative working state is updated
  to accurately reflect the current reality.
- Hooks may remind, require, or enforce this depending on severity.
```

This lines up with how PreCompact, SessionStart, and SessionEnd hooks are used in practice: as trigger points to validate or update `session-state.md` or similar canonical files.[3][1][2][5][4]

***

## 4. How self-reflection + authoritative state interact

Given that definition, the “don’t be obviously stupid” Stop-hook and the state hooks should split responsibilities:

- **Stop self-reflection hook**  
  - Check *the answer* for unsupported claims, contradictions, missing steps.  
  - Optionally check that the authoritative state file is at least mentioned/consistent when the answer modifies global decisions.  

- **PreCompact / SessionEnd hooks**  
  - Check *the session* for “has the authoritative state been updated to match what just happened?”  
  - If not, either:
    - emit warnings/reminders (advisory mode), or  
    - block compaction/termination until a small update is written (strong mode).[1][4]

That keeps the responsibilities clean: Stop = answer quality; PreCompact/Session = continuity and resilience.

***

## 5. Sanity check against the ecosystem

- Hooks docs: show that `PreCompact` fires before compaction and can be used to update shared state files.[6][3][5]
- Community guides: use `docs/session-state.md` + PreCompact/SessionStart to preserve context and remind Claude to maintain it.[2][1][4]
- Therefore, defining “authoritative working state” as “the state that those hooks are responsible for keeping honest” is consistent with how the ecosystem already treats session state.

***

If you like this, next step is to formalize a **tiny schema** for `session-state` (sections/fields) so hooks and prompts can treat it as data instead of prose. Want to define that schema next?
