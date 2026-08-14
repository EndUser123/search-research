---
title: "what repos for claude code support this solution direction?
'What do you think of this? Look at P:/.claude/hooks to unde"
date: "2026-02-18"
mode: "COPILOT"
uuid: "19e4587d-20e4-4f87-821e-94418e787817"
entry_count: 11
---

## Human

what repos for claude code support this solution direction?
"What do you think of this? Look at P:/.claude/hooks to understand the context.
"
• I verified the stale patterns are gone from skills. I’ll summarize: this run is mostly a skill-command/path drift issue
plus offline model fetch behavior, not a contract-hook deadlock now.
• Yes, this specific transcript is mostly not the old hook deadlock.
What happened in that run:
Skill(search) loaded correctly.
Then the agent chose bad/stale execution paths:
python -m knowledge.systems.chs.cli (module does not exist)
then fallback commands that can fail/hang depending on environment/model availability.
So this is primarily skill execution instruction drift + backend runtime behavior, not contract gating.
Updated /search skill with explicit canonical command and fallback:
P:/.claude/skills/search/SKILL.md
Updated /chs skill to valid CHS CLI fallback and corrected stale src.modules... references:
Key enforcement added in /search skill:
Explicitly forbids inventing knowledge.systems.chs.cli
Directs first command to:
cd "P:/__csf" && python src/cli/nip/search_enhanced.py "{{query}}" --limit 10
CHS fallback:
cd "P:/__csf/src" && python -m knowledge.systems.chs.v2.scripts.chs_cli "{{query}}" --limit 20
If you want, next I can add a PreToolUse deny rule for known-bad module strings (knowledge.systems.chs.cli,
src.modules.analysis...) so this gets blocked immediately with a corrective message instead of wasting turns.
› Is there a less friction way to do this?
› ❯ proceed with task #1096
● Now let me refactor /q SKILL.md to reflect the new strategic quality purpose. First, let me
read it again to prepare the rewrite:
● Read 1 file (ctrl+o to expand)
● Now let me create the refactored SKILL.md for /q:
● Write(.claude\skills\q\SKILL.md)
⎿  Error: PreToolUse:Write hook error: [python P:/.claude/hooks/__lib/hook_runner.py
attempts).
BOOTSTRAP-FIRST GUARD: stop retrying substantive tools.
Your next command must be a contract bootstrap command, for example:
python P:/.claude/hooks/repositories/bootstrap_contract.py --task "<task>"
After bootstrap succeeds, retry your original command.
scope.session_id=b1de8495-73e3-4df3-8598-b68578c19853
… +3 lines (ctrl+o to see all)
● I need to bootstrap a contract for the write operation:
• Yes.
Lowest-friction setup is:
Keep hooks strict on safety.
Reduce “policy in prose” by moving execution choices into one resolver.
Let hooks auto-correct obvious stale commands instead of hard-blocking.
Practical version for your case:
Add a single canonical command resolver for search
One function returns the exact command for /search and /chs based on environment.
Skills call resolver output, not hand-written shell snippets.
If command matches known stale patterns (knowledge.systems.chs.cli, src.modules...), rewrite to canonical command and
continue.
Only block when rewrite is impossible.
Use capability probes once per session
Cache: daemon up/down, model available/offline, backend health.
Then route automatically:
daemon path
offline-safe CHS CLI
unified search fallback
Keep contract handshake automatic
On Skill(...) success, auto-seed session+terminal contract (already done).
No manual bootstrap prompts during normal slash workflows.
Make failures actionable, not punitive
Error message should say “I rewrote X to Y” or “Run this exact command,” not generic gate text.
If you want, I can implement step 2 next (auto-rewrite for stale CHS/search command patterns) so this class of failures
disappears without extra user intervention.
• I’ll fix this by adding an auto-bootstrap path in the contract enforcer: when the user gives explicit implementation
intent (like “proceed with task #1096”), it seeds a scoped contract and allows the write, instead of forcing manual
bootstrap.
• Running Get-Content -Path P:/.claude/hooks/PreToolUse_authorization_gate.py -TotalCount 320
• Running Get-Content -Path P:/.claude/hooks/PreToolUse/contract_enforcer.py -TotalCount 620
• Ran if (Get-Command rg -ErrorAction SilentlyContinue) { rg -n "def get_last_user_message|def has_explicit_authorization|
│ explicit authorization|proceed|implement" P:/.claude/hooks/PreToolUse_authorization_gate.py P:/.claude/hooks/
│ PreToolUse/contract_enforcer.py }
└ P:/.claude/hooks/PreToolUse_authorization_gate.py:10:- CC interprets as "proceed with execution"
P:/.claude/hooks/PreToolUse_authorization_gate.py:94: r"\bproceed\b",
… +13 lines
P:/.claude/hooks/PreToolUse/contract_enforcer.py:507: "Please establish a contract before
proceeding. "
■ Conversation interrupted - tell the model what to do differently. Something went wrong? Hit /feedback to report the
issue.
› I didn't say I want.
• Correct. You didn’t ask me to implement that change.
I’ll stop making behavioral changes unless you explicitly approve. In this last step I only inspected files; I did not
patch anything after your message.
If you want, I can do one of these with no assumptions:
Diagnose-only: explain exactly why proceed with task #1096 still hit contract block.
Minimal fix proposal only (no edits), for your approval.
No hook changes, just exact bootstrap command flow for this session.
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
› You seem very tactical about it. Is there a greater principle that is being ignored?
• - User intent is the primary source of truth to minimize friction.
Design for least surprise by ensuring behavior matches user expectations.
Maintain monotonic trust to avoid regressions and unexpected states.
Enable graceful degradation to preserve functionality under failure.
Favor composability and a single source of execution truth to reduce complexity.
Differentiate policy from mechanism clearly to allow flexible control.
Prefer fail-safe over fail-closed when possible, ensuring recoverability.
Emphasize local-first determinism to handle concurrency and stale data without strict TTL dependence.
• Yes. The bigger principle being missed is:
Governance should enforce user intent, not replace it.
What’s been happening is tactical gate layering without a clear intent hierarchy. That causes tools to obey local rules
while violating the global goal.
The principles to restore:
Intent supremacy: explicit user directives should satisfy policy automatically.
Single source of truth: one canonical execution path per command (/search, /chs), no improvised alternates.
Graceful enforcement: block unsafe actions, but auto-repair predictable issues instead of deadlocking.
Deterministic scope: session+terminal identity must be stable across hooks; no fallback ambiguity.
Policy coherence: gates must compose (skill gate + contract gate), not conflict.
Trust monotonicity: once user authorizes a task, the system should become easier to execute that task, not harder.
So yes, the ignored principle is architectural: prioritizing local guard behavior over end-to-end intent fidelity.
› how should we optimally refactor to support the principle?
• Optimal refactor: move from “many gates” to an intent-first policy pipeline.
Establish a single Intent Ledger
Write once at UserPromptSubmit: {session_id, terminal_id, command, task_id, explicit_user_authorized, timestamp,
nonce}.
All hooks read the same record. No per-hook session parsing drift.
No TTL. Clear by explicit completion/override events only.
Define strict policy precedence (one engine)
User explicit intent
Safety invariants (destructive ops, path constraints)
Workflow requirements (skill-first, contract)
Convenience heuristics
Encode this in one policy_engine.py; hooks call it, not custom logic.
Unify scope identity
One shared resolve_scope() used by every hook.
Deterministic keys: session_id + terminal_id.
Fail closed on missing identity; never silent bypass.
Convert contract gate to intent-derived authorization
If ledger says user explicitly authorized task execution, auto-materialize scoped contract.
Contract remains required, but it’s generated from intent, not manual bootstrap friction.
Add canonical command resolver
/search, /chs, etc. resolve through one source of truth.
Disallow ad-hoc module paths.
Optional auto-rewrite for known stale commands before blocking.
Add recovery-before-block
For deterministic errors (stale command, missing contract with explicit intent), auto-repair once.
Block only if repair fails or safety invariant violated.
Make observability first-class
Structured decision log per tool call: input_intent, applied_rules, rewrite, decision, reason_code.
This is what lets you debug “why blocked” in one glance.
Remove duplicate routers / dead hooks
One active PostToolUse path.
Archive or delete unused variants and stale docs immediately.
Acceptance tests (must-pass)
/search ... then first substantive tool succeeds without manual bootstrap.
Explicit “proceed with task #N” allows writes in same scope.
Cross-terminal isolation: contract in terminal A does not leak to B.
Stale command string is rewritten to canonical path or blocked with exact fix.
Missing scope identity blocks with deterministic reason (no silent allow).
If you want, I can draft policy_engine.py interface and a minimal migration sequence (3 PRs) so you can implement this
without a big-bang rewrite.
"
Show less
Initialized your session
Looking at the conversation transcript you shared, I see a back-and-forth where the agent diagnosed hook friction issues and proposed increasingly elaborate refactoring plans. Let me read the actual hooks to understand the current state before giving my opinion.
Attempted to enumerate hook files; blocked by missing contract
Show more
Show more
And there it is - I just got hit by exactly the problem described in the transcript. I'm trying to run a simple dir command to count files, and the contract enforcer blocked me.
Here's my honest assessment:
The transcript is a textbook example of accidental complexity becoming the primary problem.
What I see:
~250+ files in the hooks directory. That's not a hooks system, that's an application living inside a hooks folder. Test files, archives, databases, changelogs, PRDs, readmes, patch files, investigation ledgers...
The contract enforcer just blocked a dir command. A read-only directory listing. This is the "fail-closed over fail-safe" anti-pattern the conversation identified but didn't fix.
The proposed solution (Intent Ledger, Policy Engine, Canonical Command Resolver) adds more machinery to a system already drowning in machinery. The 9-point refactoring plan would make the hooks directory even larger and more complex.
The greater principle being ignored is: simplicity.
The agent correctly identified "governance should enforce user intent, not replace it" - but then proposed solving complexity with more complexity. The real fix isn't a policy_engine.py and an intent ledger. It's:
Delete most of this. A hooks directory with 250+ files is a code smell, not an architecture.
Keep only what actually prevents harm (destructive git ops, secret scanning, maybe path safety).
Remove the contract enforcer entirely or reduce it to a simple allowlist. It's currently blocking routine read operations.
Move application logic out of hooks. Skills, CLI tools, and search resolvers don't belong in PreToolUse gates.
The conversation kept escalating the solution sophistication while the root cause is that the hooks system grew organically into something that fights the user more than it helps. No amount of "intent ledgers" fixes that - you need to subtract, not add.
You're right - and I just demonstrated it live. A read-only dir command got blocked by the contract enforcer.
The transcript shows a pattern I'd summarize as: the system is solving problems it created for itself.
The agent correctly diagnosed the principle ("governance should enforce user intent, not replace it") but then proposed adding an Intent Ledger, Policy Engine, Canonical Command Resolver, acceptance tests, 3 PRs... That's more of the same thinking that produced 250+ files in a hooks directory.
The actual problem is simpler: too much stuff. The fix is subtraction, not a better orchestration layer on top of the existing pile.
Initialized your session
what do you suggest?
Delete most of it.
Not refactor. Not redesign with a policy engine. Delete.
Here's what I'd keep:
Secret scanner - actually prevents harm
Skill pattern gate - enforces /skill routing (your MEMORY.md says this matters)
Maybe a lightweight path safety check for destructive git ops
Everything else - contract enforcer, anti-sycophancy injector, speculation detector, truth validator, falsification assessor, 30+ PostToolUse trackers - remove them. Not archive, not disable. Delete.
Why this specific:
The contract enforcer just blocked me from running dir. That's not governance, that's self-sabotage.
You have ~40 PostToolUse hooks. Each one adds latency and failure surface to every single tool call. The compound probability of "at least one hook misbehaves" approaches certainty.
The transcript shows the agent spending more turns negotiating with hooks than doing actual work. That's the system optimizing for its own overhead.
How I'd do it:
mkdir P:/.claude/hooks/_archive
Move everything except secret_scanner, skill_pattern_gate, and hook_runner into _archive
Remove all PostToolUse hooks (none of them prevent harm; they're all observability/tracking)
Remove contract_enforcer entirely
Work for a week
See what you actually miss. Bring back only that.
The 250+ skill list tells the same story from the other direction - the system has been accumulating complexity as a default behavior. The agent in the transcript correctly identified the principle ("governance should enforce user intent") but then proposed more system as the solution, because that's what the environment rewards.
The principle you asked about isn't "intent-first policy pipeline." It's less stuff.
Initialized your session
what do you think of this?
"
• The feedback is directionally right on one core point: subtraction > orchestration for your current state.
What I agree with:
Blocking routine work (dir, harmless reads) is a hard failure.
Too many hooks means compounded failure probability and trust collapse.
“More framework” is the wrong first move when baseline usability is broken.
What I’d change in that recommendation:
Don’t hard-delete everything at once.
Do a controlled minimum-safe baseline first, then re-add only proven value.
Optimal path:
Freeze new hook additions.
Keep only:
destructive-command safety
path safety
required skill routing (if you want this behavior)
Put all other enforcement hooks in disabled/ (not active), not deleted.
Remove contract enforcement from read-only operations immediately.
Track 1 week of real usage:
block rate
false blocks
task completion latency
Re-enable hooks only if they show measurable net benefit.
So: the principle in that feedback is correct. The best implementation is a staged simplification, not another
architectural layer and not a big-bang purge."
I do want the skill enforcement because it's super frustrating when the LLM doesn't use skills properly.
Show more
The agent gave you a diplomatic "both sides" answer. Let me be direct about what I think of it.
"Don't hard-delete, put in disabled/" — This is how you got here. The system accumulated because nothing ever actually gets removed, it gets archived, disabled, moved aside "just in case." A disabled/ folder is a _archive/ folder is a graveyard that never gets cleaned.
"Track 1 week of real usage" — You don't need a week of metrics to know the contract enforcer blocking dir is broken. You already have the data: it's in the transcript you showed me.
"Staged simplification" — Sounds reasonable, but in practice "staged" means "we'll get to phase 2 eventually" and you never do because phase 1 is working well enough and there's always real work to do.
Here's what I'd actually do:
Keep three things:
Secret scanner — prevents real harm
Skill pattern gate — you just confirmed you want this
hook_runner.py — the infrastructure that runs the above
Delete everything else. Not disable. Not archive. git rm. It's in git history if you ever need it, which you won't.
The reason I say delete rather than disable: disabled hooks still cost you. They cost cognitive overhead every time you look at the directory. They cost maintenance when you wonder "should I re-enable this?" They cost the next agent that tries to understand your hook system. And they create a gravitational pull toward re-enabling complexity.
You have 250+ skills and 40+ hooks. The system is telling you something: the default behavior has been accumulation. The only way to break that pattern is an actual removal, not a reorganization.
Initialized your session
It grew though because of deception, non-goal adherence, doing stupid stuff, over confidence, etc.  All the bad things LLMs do, we added hooks for.  How do we get a 'good' LLM without a lot of hooks?  I agree the contract thing is proving more problems than it's worth.
That's the real question. You built all this because the LLM kept doing dumb things, and each dumb thing got a hook. Now the hooks are the problem. But the original problems were real.
The answer is: you can't fix LLM behavior with runtime gates. You fix it at the prompt layer.
Here's why the hooks don't work for this:
An LLM that invents knowledge.systems.chs.cli won't be stopped by a hook that blocks that specific string. It'll invent a different bad path next time. You're playing whack-a-mole.
An anti-sycophancy hook can't make the LLM not be sycophantic. It can only detect it after the fact, by which point the turn is wasted anyway.
A truth validator running post-hoc can't undo a confident hallucination the user already read.
What actually works for LLM behavior:
CLAUDE.md / system prompt — This is where behavior rules belong. "Always use /search skill, never invent CLI paths." "When uncertain, say so." This is the highest-leverage intervention because it shapes every generation, not just the ones that happen to trigger a hook.
Skills with explicit commands — You already did this for /search. The fix was putting the canonical command in the skill, not adding a hook to block bad commands. That's the right pattern. Do more of that.
Fewer choices — The LLM does stupid stuff when it has too many options. You have 250+ skills. The LLM sees that list and starts improvising. Reduce the surface area and it has less room to go wrong.
Keep hooks for actual safety only — Secret scanning, destructive git ops, maybe path constraints. Things where the failure mode is irreversible harm, not annoying behavior.
The pattern is: CLAUDE.md for behavior, skills for execution paths, hooks only for safety.
The contract enforcer, the anti-sycophancy injector, the speculation detector, the truth validator — those are all trying to solve prompt-layer problems at the runtime layer. It doesn't work, and the overhead compounds until the system fights itself more than it helps.
The hard part is accepting that some LLM misbehavior is just the cost of using LLMs, and no amount of hooks eliminates it. The hooks just trade one class of problems (LLM does dumb thing) for another (LLM can't do anything because hooks block it)."

## Assistant

Several GitHub repositories provide Claude Code hooks aligned with simplifying your system by keeping only essential safety gates (e.g., destructive command blocking, path safety) and skill enforcement, while deleting or avoiding complex enforcers like contracts or validators.[1][2]

## Recommended Repos

These focus on minimal, targeted PreToolUse hooks for safety without bloat.

| Repo | Key Alignment | Hooks Kept | Stars/Forks |
|------|---------------|------------|-------------|
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)[1][1] | Full lifecycle but emphasizes security (blocks rm -rf, dangerous commands via PreToolUse); logging is optional/deleteable. Delete non-safety hooks like TTS/notifications. | PreToolUse (dangerous cmd block), UserPromptSubmit (basic validation) | 1.7k / 377 |
| [decider/claude-hooks](https://github.com/decider/claude-hooks)[2][3] | Lightweight Python dispatchers for quality/safety; hierarchical config. Adapt by disabling non-safety (e.g., package age, notifications). Keep PreToolUse for path/destructive blocks. | PreToolUse (validation/block), PostToolUse (optional) | 49 / 2 |
| [kenryu42/claude-code-safety-net](https://github.com/kenryu42/claude-code-safety-net)[4] | Pure safety net for git/filesystem destruction prevention. Minimal—no contracts or behavior gates. | PreToolUse (destructive git/fs blocks) | 1k / 42 |

## Adaptation Steps
- Install via their setup scripts into `.claude/hooks/`.[3][1]
- Retain only PreToolUse for secret scanning/skill patterns/destructive ops (your priorities).[5]
- Delete extras (e.g., PostToolUse trackers, notifications) as proposed—git history preserves them.[6]
- Pair with prompt-based behavior fixes in CLAUDE.md (e.g., "Always use /search skill, never invent CLI"). No repos contradict this; they reinforce runtime safety only.[7]

This matches your "delete most, keep safety + skills" direction without adding policy engines or ledgers.[8]

## Human

We are really dealing with bad LLM behavior, not filesystem safety.

## Assistant

Hooks can't reliably fix core LLM issues like hallucinations, deception, or laziness—they detect post-facto but compound friction as you've seen.[1][2][3]

## Prompt-Layer Fixes
Strong system prompts in CLAUDE.md enforce behavior upfront, shaping every generation without runtime overhead.[4][5][6]
- Use XML tags: `<investigate_before_answering>Never speculate; read files first</investigate_before_answering>` to curb hallucinations.[3]
- Anti-laziness: "Think step-by-step; verify before claiming done; use /search skill explicitly."[7]
- Skill enforcement: "For searches, invoke /search; never invent CLI paths like knowledge.systems.chs.cli."

## Repo Support
These repos target LLM behavior via prompts/skills/verification, not heavy hooks—aligning with your simplification.[2][8]

| Repo/List | Behavior Focus | Approach | Why Fits |
|-----------|----------------|----------|----------|
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)[8] | Hallucinations, skill misuse | Curated skills/orchestrators for verification (e.g., verify_cot, MCP verification skill) | No hooks bloat; prompt-first patterns like chain-of-thought verification.[9] |
| [smykla-labs/klaudiush](https://github.com/smykla-labs/klaudiush)[2][10] | Lazy execution, false claims | PreToolUse validation dispatcher (git/commit checks, no ad-hoc blocks) | Minimal; focuses on workflow verification, not anti-sycophancy gates.[1] |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)[11] | Overconfidence, assumptions | Context injection/prompt validation in UserPromptSubmit | Selective use: Keep prompt enhancers, delete others; pairs with CLAUDE.md.[4] |

## Implementation
- Start with CLAUDE.md rewrite incorporating Anthropic best practices (no "be thorough" for modern models).[3]
- Add 1-2 verification skills (e.g., /verify for self-checks).[2]
- Test: New session per task to avoid history-induced laziness.[5]
This trades hooks for prompts/skills, reducing your 250+ files while targeting root LLM flaws.

## Human

Best practices for CLAUDE.md to fix laziness

## Assistant

Claude Code laziness stems from context rot, not model flaws—fix via aggressive CLAUDE.md structure and session management.[1][2][3]

## Core Principles
Drop old anti-laziness phrases like "think carefully" or "do not be lazy"—they backfire on modern Claude models.[2]
Use XML tags for clear instructions, state injection for persistence, and /clear between tasks to reset polluted history.[3][4][1]
Enforce verification loops and skill use to prevent shortcuts.[5]

## Sample CLAUDE.md Template
```
<role>
You are a precise code executor. Follow user intent exactly. Use skills first (/search, /verify).
</role>

<rules>
- Investigate before answering: Read files, run ls/dir before assuming.
- No placeholders: Code must run without errors.
- Verify before claiming done: Test, then confirm.
- New session per major task: Use /clear after subtasks.
- Skills mandatory: /search for queries; never invent CLI.
</rules>

<state_injection>
{{PROJECT_STATE}}  <!-- Inject snapshot XML here: active plan, constraints -->
</state_injection>

<output_format>
Wrap reasoning in <reasoning>, code in <code>, verification in <verify>.
</output_format>
```
This combats laziness by forcing evidence-chaining and fresh context.[6][7][1]

## Usage Workflow
- Snapshot state (plan/constraints) as XML before /clear; inject on new chat.[4][1]
- Separate analysis/execution sessions: Plan in one, implement in fresh.[8]
- Prompt raw data for bugs: "fix" + logs/screenshots, no explanations.[9]
Test shows 90% effectiveness from manual new chats alone.[1][3]

## Human

Scripts or tools like cmp for automating session resets

## Assistant

PowerShell scripts and CLI wrappers automate Claude Code session resets via `/clear`, `--continue`, or restarts, preventing laziness from context buildup.[1][2][3]

## Key Tools/Commands
Native CLI flags like `claude --continue` resume last session without full reset; `claude --resume` picks from list.[2][3]
`/clear` inside sessions resets context while keeping permissions (stored in `.claude/settings.local.json`).[4][5]
SessionStart hooks auto-inject state post-reset (e.g., project XML).[6][7]

## PowerShell Scripts
Adapt these for your Windows 11/PowerShell 7 workflow (task-based resets, state snapshots).

```powershell
# reset-session.ps1: /clear + state inject + new task
param($TaskId, $StateFile="P:/state.xml")
# Send /clear to current Claude Code session (assumes PID or named pipe)
claude --resume | Out-Null  # Or kill/restart if hung [web:71]
echo "<state><task>$TaskId</task><context>$(Get-Content $StateFile)</context></state>" | claude
Write-Output "Reset for task $TaskId"
```

```powershell
# daemon-task.ps1: Auto-reset per task (daemon watches)
while ($true) {
    $nextTask = Get-Content "P:/tasks/next.txt"  # Your task queue
    pwsh reset-session.ps1 $nextTask
    # Kill old session PID if needed: Stop-Process -Id (Get-Process claude | Select -First 1).Id
    Start-Sleep 60  # Task complete
}
```

```powershell
# multi-terminal.ps1: Your 6+ terminals (worktree isolation)
foreach ($worktree in git worktree list) {
    Push-Location $worktree.Path
    claude --clear-equivalent  # Custom: /clear via expect-like or hook
    Pop-Location
}
```

## Automation Patterns
- **Daemon watcher**: Monitors token count via statusline hooks; auto `/clear` + reinject.[8][6]
- **Hook integration**: SessionStart hook runs `pwsh inject-state.ps1` post-`/clear`.[7]
- **Queue driver**: Tasks in file; script does reset → prompt → verify → next.[9]
Run via your multi-terminal setup: `Invoke-Expression` in each for parallelism.[2]

## Human

Prompting techniques to reduce Claude hallucinations

## Assistant

Claude hallucinations drop 70-90% with structured prompting that forces verification and speculation tagging.[1][2][3]

## Core Techniques
Use XML tags for self-audits, explicit "say I don't know" permission, and chain-of-verification (CoV) to expose gaps before final output.[4][5][1]
Avoid "be accurate"—it pressures; say "take time, accuracy > speed."[2]
Instruct "investigate before answering" for code/files.[3][6]

## CLAUDE.md Snippet
```
<anti_hallucination>
- Permission: Say "I don't know" or [UNKNOWN] freely if uncertain.
- Verify: Read files/search before claims. Tag [INFERENCE]/[SPECULATION].
- CoV: <reasoning> steps → <verification> checks → <final>.
- No general knowledge unless prompted.
</anti_hallucination>
```

## Prompt Examples
| Technique | Example Prompt | Effect [1][7] |
|-----------|----------------|-------------------------|
| Permission to Refuse | "If unsure, say 'I don't know'. Base only on provided info." | Cuts fabrications 80% [4] |
| Chain-of-Verification | "1. List facts. 2. Verify each. 3. Flag gaps." | Reveals logic flaws [8][5] |
| Tagging Speculation | "Tag [KNOWN], [INFERRED], [UNKNOWN]." | Self-correction loops [9] |
| Investigate First | "Before code: ls/dir files, /search docs." | File hallucinations down [6][10] |
| Step-Back | "Step back: What assumptions? Verify." | Reduces overconfidence [7] |

Combine in skills like /verify for your workflows; test via best-of-N reruns.[11][1]

## Human

Real-world tests of investigate before answering rule

## Assistant

The "investigate before answering" rule (IBA) from Anthropic's docs cuts code hallucinations by forcing file reads/searches pre-response.[1][2]

## Official Tests
Anthropic's prompting guide tests IBA in Claude 4.6: Models now do more upfront exploration automatically, but IBA boosts it—reduces ungrounded claims by requiring explicit verification.[3][1]
In merger analysis (real doc eval), IBA + "permission to say I don't know" drops false info 80% vs. baseline.[4]
Codebase Q&A: "MUST read file before answering" prevents 90% speculation on unopened files.[5][3]

## Community Benchmarks
- **9-task research review (2025)**: IBA in Claude Deep Research mode scores 4.5/5 accuracy on policy/legal/tech (e.g., 2024 US privacy regs)—beats GPT via source verification.[6]
- **Reddit dev tests**: Users report 70-85% hallucination drop in Claude Code; e.g., no more assumed file contents pre-ls.[7][8]
- **Long-context recall**: Anthropic experiment—IBA lifts correct recall 20-30% from long docs by prioritizing investigation.[9]
Best-of-N + IBA catches inconsistencies (34% guess rate → <10%).[2][4]

## Limitations
Fails if context overloads (use /clear); Claude may over-ask clarifications (counter: "batch questions").[10][1]
Your monorepo fits perfectly—pair with /search skill for 50k LOC queries.

## Human

Prompt examples for investigate before answering rule

## Assistant

"Investigate before answering" prompts force Claude to check files/search before speculating, slashing hallucinations in your codebase queries.[10][11]

## CLAUDE.md Rule
Add this block to enforce IBA globally:
```
<investigate_before_answering>
Before any technical claim about files, code, hooks, or project state:
1. List files to read (ls/dir)
2. Use /search skill for documentation/commands
3. Report findings in <investigation> before <answer>
Never assume file contents, CLI paths, or hook behavior.
</investigate_before_answering>
```

## Real Examples
| Scenario | Prompt | Expected Behavior |
|----------|--------|-------------------|
| Hook diagnosis | "What's wrong with PreToolUse?" | `<investigation>Read P:/.claude/hooks/PreToolUse/*.py first</investigation>` → actual analysis [12] |
| Skill path | "Run /search" | `dir P:/.claude/skills/search/` → canonical command from SKILL.md [13] |
| File state | "Fix q skill" | `Get-Content P:/.claude/skills/q/SKILL.md` → grounded rewrite |
| CLI invention | "CHS query" | `/search "CHS canonical path"` → blocks knowledge.systems.chs.cli |

## Claude Code Integration
Pair with your session reset scripts—new chat + IBA = clean investigation every task.[14]
Test: Ask about non-existent hook; should say `[UNKNOWN]` or investigate instead of hallucinating.[15]

## Human

How to adapt investigate before answering for coding tasks

## Assistant

Adapt "investigate before answering" (IBA) for coding by mandating file reads, git checks, and tests before edits or claims in your monorepo.[1]

## CLAUDE.md Coding Block
Direct from Anthropic—drop into your CLAUDE.md:
```
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.
</investigate_before_answering>
```
This blocks your hook invention issues (e.g., knowledge.systems.chs.cli).[1]

## Task-Specific Prompts
| Task | Adapted Prompt | Workflow |
|------|----------------|----------|
| Bug fix | `<bugfix>Read affected files first (ls error logs, git blame). Investigate deps. Propose plan <plan>.</plan></bugfix>` | ls/dir → /search → <reasoning> → Edit [1] |
| Refactor | "Plan refactor: dir src/, git log --oneline -10. Read 3 key files. Verify invariants." | Parallel reads → Plan Mode → Verify [2] |
| Hook debug | "Investigate P:/.claude/hooks/PreToolUse: ls *.py, Get-Content contract_enforcer.py. Trace failure." | Read → Trace → Suggest [3] |
| Skill update | "/q skill: Read SKILL.md, dir .claude/skills/q. Propose grounded rewrite." | Skill-first → Edit → Read-after [4] |

## Enforcement
- **Parallel tools**: Read multiple files at once (e.g., hooks + skills).[1]
- **Read-after-edit**: Your existing rule—extend to all claims.[3]
- **Plan Mode**: For safety, force read-only analysis first.[2]
Integrate with session resets: New chat post-plan ensures fresh investigation.[5]

## Human

Prompt templates for investigate before code changes

## Assistant

Anthropic's official IBA template prevents premature edits by forcing reads/plans first—perfect for your hooks/skills safety.[1]

## Core CLAUDE.md Template
```
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.
</investigate_before_answering>

<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed to make changes. When the user's intent is ambiguous, default to providing information, doing research, and providing recommendations rather than taking action. Only proceed with edits, modifications, or implementations when the user explicitly requests them.
</do_not_act_before_instructions>
```
Paste directly—reduces screw-ups from eager changes.[2][1]

## Task Templates
| Change Type | Template | Key Steps |
|-------------|----------|-----------|
| Bugfix | "Fix [bug]: 1. ls/dir logs/files. 2. git blame. 3. Plan <plan>. 4. Edit only after verify." | Read → Plan → Test → Edit [3] |
| Refactor | "Refactor [module]: First, characterization tests (lock behavior). Read deps. Small diffs." | Tests first → Investigate → Commit [3] |
| Hook update | "Update PreToolUse: Read *.py. Trace flow. Propose <diff> before Write." | ls/Get-Content → Plan → Edit [4] |
| Skill rewrite | "/q SKILL.md: Read current, dir skills/. Plan strategic changes <plan>." | Read → /search → Rewrite [5] |

## Workflow
1. Prompt plan: Forces parallel reads (e.g., 3 hooks at once).[1]
2. User approve: "Proceed?" → Edit.
3. Post-edit: Read-after-verify (your rule).[5]
This fits your multi-terminal: One for investigate, one for execute.

## Human

what are the other anthropic best practices for prompting and hooking?

## Assistant

Anthropic's 2026 prompting best practices emphasize XML structure, few-shot examples, and tool-first action, while hooks focus on safety at commit-time (not write-time).[1][2][3]

## Prompting Practices
Use clear audience/objective, verification/citations, and <default_to_action> for proactive edits—avoids your laziness.[4][1]

| Practice | Description | Template/Example |
|----------|-------------|------------------|
| XML Tags | Boundaries for roles/rules/examples | `<role>Executor</role><rules>Verify first</rules>` [1] |
| Few-Shot | 1-3 input/output pairs | Good/bad edits [5] |
| State Audience/Objective | "For hooks refactor: Minimize changes, verify deps" | Constraints upfront [4] |
| Verification Chains | "Extract claims → Cite → Audit" | Anti-hallucination [6] |
| Prefill Outputs | Start JSON/report | Claude completes [6] |

## Hooks Practices
Hooks enforce determinism: Validate at Stop/PreToolUse, never block writes (frustrates LLM).[2][3]

| Hook Type | Best Use | Exit Codes |
|-----------|----------|------------|
| UserPromptSubmit | Clarify ambiguous prompts, inject context | Block if unsafe [7] |
| PreToolUse | Destructive cmd scan (git rm), skill route | decision: block [2] |
| Stop | Commit validation (syntax, tests pass) | continue: false [3] |
| SessionStart | State inject (your XML snapshot) | Log only [8] |

Security: Quote vars, absolute paths, no .. traversal.[2]
Your simplification aligns: Keep PreToolUse safety + skill gate; delete rest.[3]

## Human

what repos follow the prompting and hooking ideas optimally?

## Assistant

These repos exemplify Anthropic's prompting (XML, verification, few-shot) and hooks (safety at PreToolUse/Stop, minimal bloat) for Claude Code.[1][2][3]

## Top Repos

| Repo | Prompting Focus | Hooks Focus | Why Optimal |
|------|-----------------|-------------|-------------|
| [awattar/claude-code-best-practices](https://github.com/awattar/claude-code-best-practices)[1] | XML/IBA, context engineering, few-shot for code | PreToolUse validation, Stop commit checks | Distills docs for real workflows; no bloat [4] |
| [ThamJiaHe/claude-prompt-engineering-guide](https://github.com/ThamJiaHe/claude-prompt-engineering-guide)[5] | Official practices + Claude 4.x tests (verification chains) | N/A (prompts only) | Synthesizes Anthropic guide; enterprise-ready [6] |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)[2] | Prompt optimizer via UserPromptSubmit | Full lifecycle (8 events), error handling | Comprehensive but modular—delete extras [7] |
| [decider/claude-hooks](https://github.com/decider/claude-hooks)[8] | Hierarchical CLAUDE.md integration | Quality validation (package age, clean code) | Lightweight Python; fits your simplification [9] |
| [johnpsasser/claude-code-prompt-optimizer](https://github.com/johnpsasser/claude-code-prompt-optimizer)[10] | AI-optimized prompts (<optimize> tag) | UserPromptSubmit enhancer | Auto-applies best practices [3] |

## Alignment Notes
- Prompts: All use <tags>, investigate-first, <default_to_action>—fixes your laziness/hallucinations.[3]
- Hooks: PreToolUse for blocks (destructive cmds), not contracts; aligns with "delete most."[9][11]
Fork awattar for your monorepo baseline.
