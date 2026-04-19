<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# We are using claude code with Windows 11.  Do you agree with this assessment?  Let me know if you need more info.

"Why did this happen, and why didn't our hooks prevent it?
"
● Perfect! I've completed the documentation task. However, I discovered that the documentation was already created and
committed in a previous session. Here's the status:
✅ Documentation Already Complete
The documentation for handoff skill invocation tracking was already created and committed:
Files Already Committed
P:/packages/handoff/docs/HANDOFF_SKILL_INVOCATION.md ✅

- Comprehensive technical documentation
- JSONL format explanation (critical detail)
- Error handling behavior
- Troubleshooting guide
- Verification steps
P:/packages/handoff/README.md ✅ (Updated)
- Added "Skill Invocation Tracking" to Features section
- Added to Key Capabilities
- Updated TranscriptParser API examples
- Added reference to HANDOFF_SKILL_INVOCATION.md in documentation table
P:/packages/handoff/CHANGELOG.md ✅ (Updated)
- Added skill invocation tracking to [Unreleased] section
- Documented TranscriptParser.extract_skill_invocations()
- Documented error handling improvements
- Added behavioral test entry
Summary
The documentation from Option \#1 (Documentation \& Knowledge Capture) was already completed in a previous session. This
means:
✅ JSONL format requirement is documented (prevents future confusion)
✅ Error handling behavior is explained (helps debugging)
✅ Troubleshooting guide is available (for when things go wrong)
✅ API usage is documented (shows how to use TranscriptParser)
Strategic Implications
Since the documentation is already complete, the handoff skill invocation tracking feature is fully production-ready
with:
✅ Working implementation (verified via compaction)
✅ Error handling (prevents cascade failures)
✅ Comprehensive documentation (prevents future confusion)
✅ Behavioral tests (proves feature works)
No further action needed for handoff skill invocation tracking unless issues arise or users request enhancements.
Would you like to:
Move on to a different strategic topic?
Review other items from the task list?
Address something else from the recent work?
✻ Brewed for 2m 20s · 1 background task still running (↓ to manage)
❯ I'm confused. If we already had that documentation, why didn't you use it? And why did you say it was missing?
● You're absolutely right to be confused. I made a significant error. Let me explain what happened:
My Mistake
I never checked if the documentation already existed before claiming it was missing.
What I Should Have Done
When you asked me to proceed with Option \#1 (Documentation), I should have:
First checked if the file exists:
ls P:/packages/handoff/docs/HANDOFF_SKILL_INVOCATION.md
Read it if it exists to see if it's complete
Only then decide if new/updated documentation is needed
What I Actually Did
I assumed the documentation didn't exist because:
The conversation summary didn't mention it
I didn't remember creating it (it was from a previous session)
I didn't bother to verify before claiming it was missing
This violates two critical principles from MEMORY.md:
Context Awareness: Never Ask for What You Can Fetch - I should have checked with tools first
Characterization Claims Require Evidence - I claimed documentation was "missing" without evidence
Why This Happened
The /s script failed (missing dependency), so I provided manual strategic analysis. In that analysis, I recommended
"Documentation" as Option \#1. But I never actually checked if the documentation already existed - I just assumed it
didn't.
This is lazy behavior - I should have verified before claiming something is missing.
The Reality
The documentation was created in a previous session (commit e99b52c0dc) and was already complete. When I "created" the
file, I was actually just overwriting an existing file with identical content.
My Apology
I'm sorry for the confusion. I should have:
Checked for existing documentation first
Read it to assess completeness
Only then recommended whether new docs were needed
Instead, I made an unfounded assumption that wasted your time. This is exactly the kind of "lazy workaround" anti-pattern
that the handoff system itself is designed to prevent.
Thank you for catching this error. This is a good reminder to always verify with tools before making claims about what
exists or doesn't exist."
Show more
Initialized your session
Initialized your session
Two separate failures here. Let me break them down.
Why It Happened
The agent was restoring context from a conversation summary (post-compaction). The summary didn't mention the docs existed. Rather than verifying, it inferred "not mentioned = doesn't exist" — a negative existence claim made without tool use. This violates Characterization Claims Require Evidence from MEMORY.md.
When it then called Write on the existing file, Git would have detected nothing changed (same content), so no commit showed a problem. The agent only discovered the truth when it ran git log and found the previous commit.
Why Hooks Didn't Prevent It
The existing lazy-pattern hooks target user delegation — the pattern where Claude asks the user to do something instead of doing it itself. That's not what happened here.
The gap: there's no hook covering negative existence claims without verification. The sequence was:
[no Glob/Read/Bash checking for file]
→ agent states "documentation is missing"  ← unverified claim, not caught
→ Write to existing path                    ← no pre-write existence check
→ no error (file overwrote silently)        ← Git saw no diff, no alarm

Three missing enforcement points:
No pre-Write hook checking if target path already exists
No PostResponse detector for "X is missing/doesn't exist" claims that weren't preceded by a tool verification of X
lazy_closure_detector.py catches user_delegation patterns, not assumption_without_verification patterns
What Would Fix It
A PreToolUse hook on Write/Edit that checks file existence and surfaces a warning when overwriting. And a PostResponse pattern that flags negative existence claims ("missing", "doesn't exist", "wasn't created") not backed by a search in the same response turn.
Want me to build either of those?
"

Yes, I agree with that assessment: you have two distinct failures, and your proposed fixes are on the right track, but I’d tighten and extend them a bit.[^1_1][^1_2]

## 1. Diagnosis: what actually failed

There are really three layers of failure here:

- **Reasoning failure**: The agent made a negative existence claim (“docs are missing”) purely from absence in the summary, instead of treating that as “unknown, must verify.” This is exactly the kind of assumption agentic systems frequently make when they over-trust compressed context.[^1_3][^1_4]
- **Verification failure**: No tool call (glob/read/ls/git) was used to check for the file before asserting it was missing, even though your MEMORY.md explicitly requires “never ask for what you can fetch” and “characterization claims require evidence.”
- **Guardrail failure**: Your current hooks are optimized for lazy user‑delegation (“you do it for me”) rather than “assumption without verification,” so nothing fired when the model:
    - Asserted “docs are missing” without prior search, and
    - Called Write on an existing path that already contained the correct content.

So the narrative you wrote (“negative existence claim from summary, no pre‑write existence check, hooks focused only on user delegation”) is accurate.

## 2. Why your hooks didn’t fire

Given your description, the existing lazy hooks are scoped roughly to:

- Detect patterns like “you should run X” / “you should update Y” (delegation to user).
- Possibly post‑response pattern checks for “I can’t do this, you do it” type behaviors.

They do **not** currently enforce:

- “You may not claim ‘X is missing/doesn’t exist’ unless you have tool evidence in this turn.”
- “You may not overwrite an existing file without an explicit justification or confirmation.”

That design gap is enough to let this exact failure through, even if the anti‑lazy ethos is strong in CLAUDE.md/MEMORY.md.[^1_5][^1_6]

## 3. Improvements I’d recommend

What you proposed is good; here’s how I’d sharpen it so it’s actually enforceable and low‑noise in Claude Code on Windows.

### A. Pre‑Write / Pre‑Edit existence guard

Hook: PreToolUse for Write/Edit (and any higher‑level “create doc” skill).

Behavior:

- If target path exists:
    - Read a small hash or snippet of current content.
    - If the new content is identical (or trivially different like spacing), downgrade to a **no‑op write** with an explicit warning in the stream:
        - “Target already exists with same content; treating this as a verified‑already‑documented step.”
    - If the new content differs:
        - Emit a **high‑salience warning** and require the model to state *why* it is overwriting: “You are overwriting existing documentation at P:/…/HANDOFF_SKILL_INVOCATION.md. Explain whether this is an update vs. a new doc, and mention what changed.”

Effect in your incident:

- When the agent tried to “create” the doc, the pre‑tool hook would detect the existing file and either:
    - Block the write as pointless (no diff), or
    - Force the model to articulate why it thinks the file is missing, which would expose the inconsistency.

Implementation notes (Windows 11 + Claude Code):

- Use a Bash/PowerShell tool call (or Node fs) inside the hook to check `Test-Path` / `fs.existsSync` for the path.
- Keep it cheap: only read first N KB and hash to compare content, not the whole file.


### B. Negative-existence claim detector

Hook: PostResponse (or Stop event) analysis for the assistant’s just‑completed turn.

Core rule:

- Scan the turn for phrases like “doesn’t exist”, “missing”, “was not created”, “not documented”, “no X file”, etc.
- If such a phrase appears **and** there was no tool invocation in this turn that searched for that thing (glob, ls, ripgrep, git log, etc.), raise a violation:
    - “You stated that `<X>` is missing, but you did not verify with tools this turn. You must either (a) run a search now, or (b) restate as uncertainty.”

This directly encodes “characterization claims require evidence” into execution‑time policy, not just docs.

Practical tuning:

- Maintain a small allowlist of “obvious” claims to avoid spam (“no internet access” etc.).
- For file/feature/docs claims specifically, tie it to patterns like `*.md`, “documentation”, “README”, “config”, etc., where a search skill is clearly available.


### C. Strengthen MEMORY / CLAUDE rules with an explicit “absence ≠ non-existence” norm

You already have “never ask for what you can fetch” and “characterization claims require evidence.” I’d add one explicit clause, then **reference it from your hooks**:

- “Absence from the current context (summary, transcript, partial tree) must be treated as ‘unknown’ until checked with tools. Never infer ‘does not exist’ purely because something was not mentioned.”

Then, your PostResponse detector can quote that rule when firing, which tends to make the model course‑correct better than a generic warning.

## 4. What I’d tweak from your write‑up

Minor refinements to your “What Would Fix It” section:

- Explicitly separate:
    - “Pre‑Write existence and diff check” (guard against pointless overwrites and unintentional doc replacement).
    - “Negative existence claims without verification” (guard against bad reasoning even when no write happens).
- Make it clear that the pre‑write hook should *not* block legitimate updates; it should force justification and awareness when overwriting existing docs.

A tightened version of your last section could be:

- Add a PreToolUse hook on Write/Edit that:
    - Detects when a target file already exists.
    - Compares existing vs new content.
    - Treats identical writes as a no‑op with explanation, and requires justification text when overwriting changed content.
- Add a PostResponse hook that:
    - Flags negative existence claims (“missing”, “doesn’t exist”, “no X file/docs”) if they are not preceded in this turn by a search/check tool call.
    - Forces the agent either to run verification tools or to downgrade the claim to “unknown, must be checked.”

Would you like to focus first on wiring the PreToolUse check into your existing Write hooks, or on designing the negative‑existence PostResponse pattern so it doesn’t become noisy in your day‑to‑day flows?
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://github.com/kirodotdev/Kiro/issues/5239

[^1_2]: https://github.com/kirodotdev/Kiro/issues/959

[^1_3]: https://www.linkedin.com/posts/daniel-de-kadt-7091964_late-last-year-i-adventured-into-the-world-activity-7422204676856582145-cIWB

[^1_4]: https://www.facebook.com/groups/icthubkenya/posts/3787871644689494/

[^1_5]: https://ai.gopubby.com/claude-code-setup-skills-hooks-agents-mcp-blueprint-80bdef0c62f6

[^1_6]: https://www.youtube.com/watch?v=vqdomISes4o

[^1_7]: https://www.reddit.com/r/ClaudeCode/comments/1oivs81/claude_code_is_a_beast_tips_from_6_months_of/

[^1_8]: https://stackoverflow.com/questions/63943401/husky-pre-commit-hook-failed-add-no-verify-to-bypass

[^1_9]: https://dustingram.com/articles/2015/07/20/preventing-unintended-check-ins-with-git-precommit-hooks/

[^1_10]: https://www.reddit.com/r/perplexity_ai/comments/1q28y8x/whats_the_deal_with_no_more_tool_calls_and_it/

[^1_11]: https://pmc.ncbi.nlm.nih.gov/articles/PMC8928718/

[^1_12]: https://github.com/anthropics/claude-code/issues/473?timeline_page=1

[^1_13]: https://news.ycombinator.com/item?id=44560662

[^1_14]: https://community.retool.com/t/pydanticai-generic-api-class-to-auto-generate-agent/59666

[^1_15]: https://www.ibm.com/support/pages/fix-packs-datapower-gateway-1050x


---

# Let’s start with the PreToolUse Write/Edit existence check

I want to design the negative existence PostResponse pattern

You can do both with small, focused hooks: a PreToolUse guard that inspects Write/Edit calls, and a Stop/PostResponse hook that enforces “no negative existence claims without verification.”[^2_1][^2_2][^2_3]

## 1. PreToolUse Write/Edit existence check

Goal: intercept Write/Edit calls, detect when the target file already exists, and either no-op identical writes or force the model to acknowledge it is overwriting existing docs.[^2_4][^2_1]

### Hook wiring (settings)

In `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["P:/hooks/pre_write_guard.py"],
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["P:/hooks/pre_write_guard.py"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```


### Hook behavior (Python script)

`P:/hooks/pre_write_guard.py`:

```python
import sys
import json
from pathlib import Path
import hashlib

RAW = sys.stdin.read()
data = json.loads(RAW)

tool_name = data.get("tool", "")
tool_input = data.get("tool_input") or {}
file_path = tool_input.get("file_path") or tool_input.get("path") or ""

# Default: allow
decision = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": ""
    }
}

if not file_path:
    print(json.dumps(decision))
    sys.exit(0)

p = Path(file_path)

if p.exists() and p.is_file():
    new_content = tool_input.get("content") or tool_input.get("new_content")
    if isinstance(new_content, str):
        try:
            existing = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            existing = ""

        def h(s: str) -> str:
            return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

        if h(existing) == h(new_content):
            # Identical write: convert to deny + guidance
            decision["hookSpecificOutput"]["permissionDecision"] = "deny"
            decision["hookSpecificOutput"]["permissionDecisionReason"] = (
                f"PreToolUse guard: {file_path} already exists with identical content. "
                "Treat this as 'docs already exist and are complete' instead of recreating. "
                "Explain to the user that the documentation is already present and reference it."
            )
        else:
            # Overwrite with different content: allow, but force explicit explanation
            decision["hookSpecificOutput"]["permissionDecision"] = "allow"
            decision["hookSpecificOutput"]["permissionDecisionReason"] = (
                f"PreToolUse guard: You are overwriting existing file {file_path}. "
                "Before proceeding, state why the previous documentation is insufficient "
                "and summarize what is changing."
            )

print(json.dumps(decision))
sys.exit(0)
```

Key points:

- Identical write → `deny` with a reason that pushes Claude to realize “oh, this already exists; treat as verification, not creation.”[^2_3][^2_1]
- Changed write → `allow` but with a strong reason that gets fed back into the model’s planning, forcing an explicit justification.

You can refine the matcher (e.g., only `.md` paths, or only under `packages/handoff/docs`) to reduce noise.

## 2. Negative existence PostResponse pattern

Goal: after each assistant turn, detect claims like “docs are missing” that were not backed by a search/ls/git/etc in the same turn.[^2_2][^2_5]

### Hook wiring

Use a `Stop` (or `PostToolUse`+`Stop`) hook that gets the whole turn:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["P:/hooks/negative_existence_guard.py"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```


### Heuristic design

1. Extract the assistant’s latest message text.
2. Look for negative-existence patterns (simple regexes) around files/docs/features:
    - `missing`, `doesn't exist`, `does not exist`, `no such`, `wasn't created`, `not documented`, `no documentation`, `no X file` etc.
3. Check the same turn’s tool calls for “verification tools”:
    - Tools like Glob/Grep/Read/Bash `ls`, Git `log`/`status`/`show`, `rg`, etc.
    - Very rough heuristic: any tool whose name or command includes `ls`, `dir`, `find`, `glob`, `grep`, `rg`, `git log`, `git status`, `docs`, `read`.
4. If you see a negative-existence phrase and **no verification tool** was called, return JSON telling Claude to fix it by either:
    - Running a search/check now, or
    - Downgrading the claim to “unknown; must be verified.”

### Hook implementation (skeleton)

`P:/hooks/negative_existence_guard.py`:

```python
import sys
import json
import re

RAW = sys.stdin.read()
data = json.loads(RAW)

# Latest assistant content
messages = data.get("messages") or []
assistant_text = ""
for m in reversed(messages):
    if m.get("role") == "assistant":
        assistant_text = "".join(
            p.get("text", "") for p in m.get("content") or [] if p.get("type") == "text"
        )
        break

if not assistant_text:
    print("{}")
    sys.exit(0)

neg_patterns = [
    r"\bmissing\b",
    r"\bdoes(?:\s+not|n't)\s+exist\b",
    r"\bno\s+such\b",
    r"\bwas(?:\s+not|n't)\s+created\b",
    r"\bnot\s+documented\b",
    r"\bno\s+documentation\b",
    r"\bno\s+.*file\b",
]

if not any(re.search(p, assistant_text, re.IGNORECASE) for p in neg_patterns):
    print("{}")
    sys.exit(0)

# Check for verification tools used this turn
tool_uses = data.get("tool_uses") or []
verification_hit = False
verification_keywords = [
    "glob", "grep", "rg", "find", "search", "ls", "dir", "read",
    "git log", "git status", "git show", "docs", "documentation"
]

for t in tool_uses:
    name = (t.get("tool") or "").lower()
    cmd = ""
    ti = t.get("tool_input") or {}
    if isinstance(ti, dict):
        cmd = " ".join(str(v) for v in ti.values()).lower()
    haystack = name + " " + cmd
    if any(k in haystack for k in verification_keywords):
        verification_hit = True
        break

if verification_hit:
    print("{}")
    sys.exit(0)

# No verification: tell Claude to fix it next turn
output = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "ok": False,
        "reason": (
            "You claimed something is 'missing' or 'does not exist' without verifying with tools. "
            "Per MEMORY.md: 'characterization claims require evidence' and 'absence in summary "
            "≠ non-existence'. In your next message, either: (1) run appropriate search tools "
            "(glob/read/git/ls) to check, or (2) restate your claim as uncertainty and ask to verify."
        )
    }
}

print(json.dumps(output))
sys.exit(0)
```

This uses the documented pattern of returning `ok: false` with a reason that Claude then uses as its next instruction.[^2_1][^2_3]

You can tune:

- The `neg_patterns` list to reduce false positives.
- The `verification_keywords` to include your exact tool names (`FileSearch`, `SearchProject`, custom `docs_index`, etc.).


## 3. How they work together in your incident

In your specific failure mode:

- When Claude tried to “create” `HANDOFF_SKILL_INVOCATION.md`, the PreToolUse hook would see the file already exists.
    - Identical content: deny the write, tell Claude “docs already exist; explain that instead.”
- Earlier, when it said “docs are missing” without searching, the Stop hook would fire:
    - Mark `ok: false`, force the next message to either run `ls P:/packages/handoff/docs` / `git log` or downgrade the claim to “uncertain.”

Together, that converts the pattern from “confident hallucinated absence” into “do a quick verification pass, then speak.”

Would you like to tighten these for only `*.md` under `packages/handoff` first, or roll them out repo‑wide and then back off if they’re too noisy?
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://code.claude.com/docs/en/hooks-guide

[^2_2]: https://code.claude.com/docs/en/hooks

[^2_3]: https://stevekinney.com/courses/ai-development/claude-code-hook-examples

[^2_4]: https://www.datacamp.com/tutorial/claude-code-hooks

[^2_5]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^2_6]: https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py

[^2_7]: https://codango.com/how-i-tamed-claude-code-with-pre-tool-hooks-and-you-should-too/

[^2_8]: https://www.reddit.com/r/ClaudeAI/comments/1loodjn/claude_code_now_supports_hooks/

[^2_9]: https://playbooks.com/skills/josiahsiegel/claude-plugin-marketplace/windows-path-troubleshooting

[^2_10]: https://www.reddit.com/r/ClaudeCode/comments/1m7wml8/my_claude_code_setup_prompts_commands_hooks_and/

[^2_11]: https://code.claude.com/docs/en/how-claude-code-works

[^2_12]: https://github.com/ykdojo/claude-code-tips

[^2_13]: https://www.whytryai.com/p/claude-code-beginner-guide

[^2_14]: https://www.reddit.com/r/ClaudeCode/comments/1o3czhw/how_to_make_claude_code_write_actually_clean_code/

[^2_15]: https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/


---

# Is there proof that PostResponse is an actual event hook type in Claude Code v2.1.71+?

There is no `PostResponse` hook type; the supported event names are exactly those listed in the Hooks docs, and `PostResponse` is not among them.[^3_1][^3_2]

## Supported hook events

Claude Code v2.1.71+ exposes this set of hook events in the official lifecycle table:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `PostToolUseFailure`
- `Notification`
- `SubagentStart`
- `SubagentStop`
- `Stop`
- `TeammateIdle`
- `TaskCompleted`
- `InstructionsLoaded`
- `ConfigChange`
- `WorktreeCreate`
- `WorktreeRemove`
- `PreCompact`
- `SessionEnd`

Both the hooks guide and hooks reference show this same list and do not mention any `PostResponse` event.[^3_2][^3_1]

## What to use instead

For “after Claude finishes a turn” behavior, you use the `Stop` event, which fires whenever Claude finishes responding and supports decision control (including blocking further stopping via exit code 2 or JSON `decision: "block"`).[^3_1][^3_2]

So for your negative-existence pattern, you should design it as a `Stop` hook (possibly `type: "prompt"` or `type: "agent"`) that inspects the last assistant message and, if needed, returns `{"ok": false, "reason": "..."}` or a `decision: "block"` payload to force another corrective turn.[^3_2][^3_1]

Do you want a concrete `Stop` hook example wired as `type: "prompt"` that checks for “missing/doesn’t exist” claims without search tools in that turn?

<div align="center">⁂</div>

[^3_1]: https://www.reddit.com/r/ClaudeCode/comments/1oivs81/claude_code_is_a_beast_tips_from_6_months_of/

[^3_2]: https://ai.gopubby.com/claude-code-setup-skills-hooks-agents-mcp-blueprint-80bdef0c62f6


---

# yes

You can implement this as a `Stop` hook of type `prompt` that inspects the last assistant message and blocks stopping when it finds unverified “missing/doesn’t exist” claims.[^4_1][^4_2]

## 1. High-level behavior

- Trigger: every time Claude finishes a response (`Stop` event).[^4_3][^4_1]
- Check: in that turn, did the assistant claim something is “missing/doesn’t exist/not documented” **and** fail to call any verification tools (glob/ls/read/git/search)?
- Action:
    - If everything is fine → allow stop.
    - If a bad negative-existence claim is found → return `{"ok": false, "reason": "..."}` so Claude keeps going and uses `reason` as the next instruction.[^4_4][^4_1]

This is exactly the pattern in the docs’ Stop hook example, just with a different prompt.[^4_1]

## 2. Settings.json wiring

In `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You must not state that documentation, files, or configuration are 'missing' or 'do not exist' unless you have verified this with tools in this turn (e.g., glob, ls/dir, search, read, or git log/status). Examine your latest response and the tools you used in this turn:\n\n1. If you claimed something is missing or does not exist, but you did NOT run any verification tools to check, respond with a JSON object: {\"ok\": false, \"reason\": \"<what you still need to verify or correct>\"} and then in your next message either (a) run appropriate search tools to check, or (b) restate your claim as uncertainty and ask to verify.\n2. If you did not make any such unverified negative existence claims, respond with {\"ok\": true}.\n\nImportant: Only use JSON with these keys and no additional text.",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Why `type: "prompt"`: per the hooks guide, prompt hooks get the structured Stop input and let Claude itself return a small JSON control object (`ok` / `reason`).[^4_5][^4_1]

## 3. How Claude will respond

Given that prompt, the Stop hook input includes:

- The full message history (including the last assistant message).
- The tools used this turn (`tool_uses`), so Claude can see whether it ran `ls`, `glob`, `SearchProject`, `git log`, etc.[^4_6]

Claude will:

- Parse its own last turn, notice phrases like “the documentation is missing,” and then check whether it used any verification tools.
- If it finds an unverified negative-existence claim, it will answer the hook with:

```json
{"ok": false, "reason": "I claimed the handoff documentation was missing without checking the filesystem or git log. I need to verify docs/handoff paths first."}
```

Claude Code sees `ok: false` and keeps the session running; the `reason` is injected as an instruction into the next assistant step, so the very next message will run the file search / git commands and correct itself.[^4_2][^4_1]

If it didn’t make such a claim, it returns `{"ok": true}` and Claude stops as normal.

## 4. Optional: tighten scope and reduce noise

You can narrow what this hook cares about directly in the prompt:

- Only trigger for content mentioning `docs`, `documentation`, `README`, `.md`, `config`, etc.
- Add an explicit reminder of your MEMORY.md rule: “Absence from summaries ≠ non-existence; treat as ‘unknown’ unless verified.”

For example, tweak the first sentence:

> “Check your latest response for statements that documentation (README, .md files), configuration, or code files are ‘missing’, ‘not created’, ‘not documented’, or ‘do not exist’…”

This keeps it from firing on generic “that feature doesn’t exist” remarks that might be fine in other contexts.

Do you want to keep this as a global Stop hook, or restrict it to certain worktrees or repos (e.g., only when `cwd` includes `packages/handoff`)?
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://code.claude.com/docs/en/hooks-guide

[^4_2]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^4_3]: https://www.eesel.ai/blog/hooks-reference-claude-code

[^4_4]: https://wmedia.es/en/writing/claude-code-hooks-practical-guide

[^4_5]: https://github.com/disler/claude-code-hooks-mastery

[^4_6]: https://gist.github.com/fongandrew/32222869f25202c8532f705f2fb9abd1

[^4_7]: https://code.claude.com/docs/en/hooks

[^4_8]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^4_9]: https://www.eesel.ai/blog/hooks-in-claude-code

[^4_10]: https://github.com/anthropics/claude-code/issues/2825

[^4_11]: https://www.reddit.com/r/ClaudeAI/comments/1odev4r/two_most_useful_hooks_stop_notification/

[^4_12]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^4_13]: https://www.reddit.com/r/ClaudeCode/comments/1p3nf7i/claude_code_stop_hook_is_triggering_way_too/

[^4_14]: https://www.datacamp.com/tutorial/claude-code-hooks

[^4_15]: https://github.com/anthropics/claude-code/issues/10463


---

# Example Stop hook to run tests before finishing

You can gate session stopping on tests by using a `Stop` hook that blocks when the test command fails.[^5_1][^5_2]

## 1. Simple shell Stop hook (run tests every time)

`.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash",
            "args": ["P:/hooks/stop_run_tests.sh"],
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

`P:/hooks/stop_run_tests.sh`:

```bash
#!/usr/bin/env bash
INPUT=$(cat)

# Critical: avoid infinite loop
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi

# Run your test suite (adapt for Windows: `pwsh -File ...` or `npm test` directly)
npm test > /tmp/cc-tests.log 2>&1
STATUS=$?

if [ $STATUS -ne 0 ]; then
  # Block stopping
  echo "{\"decision\": \"block\", \"reason\": \"Tests are failing. Review and fix before stopping. See /tmp/cc-tests.log for details.\"}"
  exit 0
fi

# Allow stopping
echo "{\"decision\": \"allow\"}"
exit 0
```

Pattern is the same as community “test gate” examples: check `stop_hook_active`, run tests, and return `decision: "block"` when they fail.[^5_2][^5_3]

## 2. Prompt-based Stop hook (Claude decides when to run tests)

If you want Claude to decide when/how to run tests (e.g., use `pytest` vs `npm test` based on repo), use an `agent` Stop hook:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Before allowing this session to stop, verify that the test suite passes. Use the appropriate test command for this project (e.g., `npm test`, `pytest`, `dotnet test`, etc.). If tests fail or have not been run, respond with {\"ok\": false, \"reason\": \"what needs to be fixed or which tests to run\"}. If tests pass, respond with {\"ok\": true}. Only output JSON.",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

Here Claude uses tools to run tests and returns `{ "ok": false, "reason": "…" }` to keep going or `{ "ok": true }` to allow stopping, exactly like the tests-before-stop example in the hooks guide.[^5_4][^5_1]

Do you want this to run on every stop, or only when `git status` is dirty (changes present)?
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_5][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://code.claude.com/docs/en/hooks-guide

[^5_2]: https://wmedia.es/en/writing/claude-code-hooks-practical-guide

[^5_3]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^5_4]: https://www.reddit.com/r/ClaudeCode/comments/1rd60pl/i_assume_everyone_already_knows_this_but_you/

[^5_5]: https://code.claude.com/docs/en/hooks

[^5_6]: https://www.dnasir.com/2022/01/31/using-git-hooks-to-enforce-development-policies/

[^5_7]: https://stackoverflow.com/questions/22901511/how-to-skip-the-aftereach-hook-if-the-current-test-case-fails-and-continue-to-ru

[^5_8]: https://www.youtube.com/watch?v=o-pMCoVPN_k

[^5_9]: https://graphite.com/guides/implementing-pre-commit-hooks-to-enforce-code-quality

[^5_10]: https://stackoverflow.com/questions/63967477/error-handling-how-do-i-stop-the-script-if-theres-an-error-in-a-before-each-h

[^5_11]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^5_12]: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks

[^5_13]: https://stackoverflow.com/questions/35997624/how-to-disable-git-hooks-for-security-reason

[^5_14]: https://www.reddit.com/r/ClaudeCode/comments/1p3nf7i/claude_code_stop_hook_is_triggering_way_too/

[^5_15]: https://docs.factory.ai/guides/hooks/testing-automation


---

# Prompt hook examples to check task completion

You can use a `Stop` hook with `type: "prompt"` that asks Claude to self-check whether all tasks are actually done before it’s allowed to stop.[^6_1]

## 1. Minimal “are tasks complete?” example

This is almost exactly the example from the hooks guide, adapted to modern syntax.[^6_1]

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the current session, the user’s original goals, and your recent work. Decide if ALL requested tasks are fully complete (code written, tests run if appropriate, docs updated, no obvious TODOs left). If anything is incomplete or needs verification, respond with {\"ok\": false, \"reason\": \"what remains to be done\"}. If everything is truly finished, respond with {\"ok\": true}. Only output JSON with these keys."
          }
        ]
      }
    ]
  }
}
```

Behavior:

- On each stop, Claude gets this hook input plus context and must return:
    - `{"ok": true}` → stop allowed.
    - `{"ok": false, "reason": "…"}` → Claude Code keeps the session running and feeds `reason` back to Claude as its next instruction, so it continues working.[^6_1]


## 2. Variant that checks explicit checklist items

If you like explicit checklists in your prompts or CLAUDE.md, you can push Claude to verify each item:

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You must not stop until all items in the user's task list are complete. Compare: (1) the user's requested tasks, (2) your code changes, tests, and docs updates this session. If any task is only partially done, unverified, or untested, respond with {\"ok\": false, \"reason\": \"which tasks are still incomplete or need tests\"}. If every task is fully completed and verified, respond with {\"ok\": true}. Only output JSON."
          }
        ]
      }
    ]
  }
}
```

This uses the same `ok`/`reason` contract from the docs’ prompt-hook pattern, just with stronger criteria around “fully completed and verified.”[^6_2][^6_1]

Would you prefer this hook to always run, or only in worktrees that have a `TASKS.md` or an active `/task` in Claude Code?
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_3][^6_4][^6_5][^6_6][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://code.claude.com/docs/en/hooks-guide

[^6_2]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^6_3]: https://www.reddit.com/r/ClaudeAI/comments/1odev4r/two_most_useful_hooks_stop_notification/

[^6_4]: https://code.claude.com/docs/en/hooks

[^6_5]: https://www.youtube.com/watch?v=o-pMCoVPN_k

[^6_6]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^6_7]: https://blog.gitbutler.com/cursor-hooks-deep-dive

[^6_8]: https://github.com/anthropics/claude-code/issues/17804

[^6_9]: https://claude-blog.setec.rs/blog/prompt-based-stop-hooks/

[^6_10]: https://hexdocs.pm/claude/guide-hooks.html

[^6_11]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^6_12]: https://oneuptime.com/blog/post/2026-02-09-prestop-hooks-zero-connection-drop/view

[^6_13]: https://github.com/danielmiessler/Personal_AI_Infrastructure/issues/477

[^6_14]: https://github.com/disler/claude-code-hooks-mastery

[^6_15]: https://jasminestar.com/4-hooks-you-need/


---

# Are there best practices for stop type : "prompt" hooks?

Yes, there are some emerging best practices for `Stop` hooks with `type: "prompt"`; most come down to being strict about JSON, specific about criteria, and defensive about loops.[^7_1][^7_2]

## 1. Output contract and JSON discipline

- In the prompt, **explicitly require JSON-only output** and specify the exact shape you expect, e.g. `{ "ok": true }` / `{ "ok": false, "reason": "..." }`.[^7_3][^7_1]
- Avoid mixing exit codes and JSON for prompt hooks; just let Claude return the JSON and let Claude Code interpret it.[^7_4][^7_1]
- Keep the schema minimal: a couple of booleans/strings is easier for the model to honor reliably.

Example pattern from docs/community posts:

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Decide if Claude should stop. If all tasks are complete and validated, respond with {\"ok\": true}. If anything remains (tests, docs, TODOs), respond with {\"ok\": false, \"reason\": \"what remains to be done\"}. Only output JSON."
          }
        ]
      }
    ]
  }
}
```


## 2. Be explicit about criteria

- Don’t ask “Should Claude stop?”; enumerate the **conditions** that must be true.[^7_2][^7_5]
- Good prompts list concrete checks: tests passing, docs updated, TODOs removed, etc.
- This reduces hallucinated “all good” when obviously incomplete.

Example:

> “Claude should only stop if: 1) All requested code changes are implemented, 2) All unit tests pass or were intentionally skipped with justification, 3) Docs or comments were updated as requested.”[^7_2]

## 3. Use context via `$ARGUMENTS` only when needed

- Use `$ARGUMENTS` when the hook needs the full Stop payload (messages, tool_uses, stop_hook_active, etc.).[^7_1][^7_2]
- Don’t dump raw context unless it’s necessary; large prompts increase cost and can dilute focus.
- Often you can rely on “review the current conversation and your recent actions” without explicitly inlining `$ARGUMENTS`.


## 4. Prevent infinite loops (`stop_hook_active`)

- Stop hooks can cause continued work loops; **always respect the `stop_hook_active` flag** in command hooks, and in prompt hooks, tell Claude what to do when it is already active.[^7_6][^7_1]
- A simple pattern is:
    - If `stop_hook_active` is true, only allow `{ "ok": true }` or a single “fix and stop” cycle.

In prompt text you can encode:

> “If `stop_hook_active` is true, you are already in a forced continuation. In that case, respond with {\"ok\": true} unless there is a single, clearly defined follow-up step left.”[^7_6]

## 5. Keep scope narrow and avoid flakiness

- Use Stop prompt hooks for **logical checks** (task completion, requirement coverage, obvious missing steps).[^7_7][^7_1]
- Use command hooks (or PreToolUse) for **deterministic checks** (tests, lint, type-check). Combine them when needed rather than doing everything in one prompt hook.[^7_2][^7_6]
- Avoid long-running, flaky, or network-dependent logic inside prompt-based Stop hooks.

A combined pattern from the blog posts:

- Command Stop hook: run tests, block if they fail.
- Prompt Stop hook: if tests passed, check if all requirements are truly satisfied before allowing stop.[^7_6][^7_2]

If you paste your current Stop prompt hook, I can tighten it to follow these practices without making it too verbose.
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://code.claude.com/docs/en/hooks-guide

[^7_2]: https://claude-blog.setec.rs/blog/prompt-based-stop-hooks/

[^7_3]: https://github.com/anthropics/claude-code/issues/11947

[^7_4]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^7_5]: https://dev.to/gunnargrosch/automating-your-workflow-with-claude-code-hooks-389h

[^7_6]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^7_7]: https://www.chatprd.ai/how-i-ai/workflows/automate-code-quality-and-fixes-with-ai-stop-hooks

[^7_8]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^7_9]: https://code.claude.com/docs/en/hooks

[^7_10]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^7_11]: https://www.reddit.com/r/ClaudeAI/comments/1odev4r/two_most_useful_hooks_stop_notification/

[^7_12]: https://www.eesel.ai/blog/hooks-in-claude-code

[^7_13]: https://www.datacamp.com/tutorial/claude-code-hooks

[^7_14]: https://www.linkedin.com/posts/bennyjson_todays-ai-tip-use-stop-hooks-if-activity-7425116045323046913-b0Yy

[^7_15]: https://chrislema.com/stop-prompting-ai-for-every-task-thats-not-automation-thats-just-faster-manual-labor/


---

# Differences between prompt command and agent hook types

`prompt` hooks and `agent` hooks both delegate the decision to an LLM, but they differ in tool access, cost, and when you should use them.[^8_1][^8_2]

## 1. type: "prompt"

- **Single LLM call, no tools**: Claude gets your hook prompt plus the hook input JSON (via `$ARGUMENTS` if you include it) and returns a one-shot JSON decision like `{"ok": true}` or `{"ok": false, "reason": "..."}`.[^8_2][^8_3]
- **No tool use**: it cannot run Read/Grep/Glob or bash; it only reasons over the structured input (messages, tool_uses, event metadata).[^8_2]
- **Best for**:
    - Pure judgment calls (“are all tasks logically complete?”, “did this answer follow the style guide?”).
    - Cheap semantic checks (e.g., Stop hooks for task completion, UserPromptSubmit hooks to rewrite prompts).[^8_4][^8_5]
- **Pros**: fast (1–5s), cheaper, simpler to reason about.
- **Cons**: can’t verify against the actual filesystem or repo; must trust the context it’s given.

Docs summary: “Use prompt hooks when the hook input data alone is enough to make a decision.”[^8_6][^8_2]

## 2. type: "agent"

- **Spawns a subagent with tools**: the hook creates a mini-Claude Code agent that can call tools like Read, Grep, Glob, Bash, etc., for up to ~50 tool-use turns.[^8_6][^8_2]
- **Multi-step reasoning**: it can inspect files, run tests, search the codebase, then finally return the same `{"ok": true}` / `{"ok": false, "reason": "..."}` JSON.[^8_4][^8_2]
- **Best for**:
    - Checks that require reading code or running commands (“do tests pass?”, “do all changed files have corresponding tests?”, “is this migration wired to RLS?”).[^8_3][^8_2]
- **Pros**: can verify actual state, much more powerful for enforcement.
- **Cons**: slower (5–30s), more tokens, more complex behavior.

Docs summary: “Use agent hooks when you need to verify something against the actual state of the codebase.”[^8_2][^8_4]

## 3. When to choose which

A quick rule-of-thumb from guides and blog posts:[^8_7][^8_6]


| Need | Hook type | Why |
| :-- | :-- | :-- |
| Pure semantic/judgment, no verification | `prompt` | One-shot LLM over hook input is enough |
| Requires reading files or running commands | `agent` | Subagent can use tools before deciding |
| Simple deterministic checks (exit code, regex) | `command` | Shell or script, no LLM needed |

For your negative-existence and “are tasks complete?” checks, `prompt` is usually sufficient, while “tests must pass before stop” is a better fit for `agent` (or `command`) so it can actually run the tests.

Do you want an explicit side-by-side JSON example showing the same Stop hook implemented once as `prompt` and once as `agent`?
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_16][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://code.claude.com/docs/en/hooks

[^8_2]: https://code.claude.com/docs/en/hooks-guide

[^8_3]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^8_4]: https://www.morphllm.com/claude-code-hooks

[^8_5]: https://claude-blog.setec.rs/blog/prompt-based-stop-hooks/

[^8_6]: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns

[^8_7]: https://wmedia.es/en/writing/claude-code-hooks-practical-guide

[^8_8]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^8_9]: https://kiro.dev/blog/automate-your-development-workflow-with-agent-hooks/

[^8_10]: https://www.youtube.com/watch?v=CEODfvJLIGQ

[^8_11]: https://www.youtube.com/watch?v=n8D-s-268sE

[^8_12]: https://www.datacamp.com/tutorial/claude-code-hooks

[^8_13]: https://www.youtube.com/watch?v=J5B9UGTuNoM

[^8_14]: https://lobehub.com/tr/skills/frankxai-agentic-creator-os-hooks-automation

[^8_15]: https://angelo-lima.fr/en/claude-code-hooks/

[^8_16]: https://www.youtube.com/watch?v=Q4gsvJvRjCU


---

# Best practices for writing effective prompt hooks, and Hook timeout settings for prompt vs agent types

For prompt hooks, best practice is to make them very explicit, JSON-only, and cheap; agent hooks get longer timeouts because they may run tools, but you still want to cap them conservatively.[^9_1][^9_2]

## Writing effective prompt hooks

- **Define a tiny JSON schema.**
Tell Claude exactly what to return, e.g. `{"ok": true}` or `{"ok": false, "reason": "..."}`, and say “Only output JSON with these keys.”[^9_2][^9_1]
- **Spell out the decision criteria.**
Replace “Should Claude stop?” with concrete checks like “All requested tasks are complete, tests pass, docs updated.”[^9_2]
- **Keep the prompt short and focused.**
Use 2–4 bullet checks, not a page of policy; long prompts correlate with flaky decisions.[^9_3][^9_2]
- **Use `$ARGUMENTS` only when needed.**
Include it when the hook must inspect messages/tool_uses; omit it if generic logic (“are tasks done?”) is enough, to keep tokens and latency down.[^9_1][^9_2]
- **Avoid side effects in prompt hooks.**
Prompt hooks should make *decisions* based on the hook input; use `command`/`agent` hooks for running tests, modifying files, or hitting HTTP endpoints.[^9_4][^9_1]
- **Handle the second-chance case.**
In a Stop prompt, mention what to do when the hook has already blocked once (via `stop_hook_active` in the input, or by wording the prompt): e.g., “If you’ve already been told to continue, either return ok:true or list one clearly defined remaining step.”[^9_5][^9_1]


## Timeout settings: prompt vs agent

From the current docs and guides:[^9_6][^9_7][^9_1]

- **Prompt hooks**
    - Default timeout is short (around 30 seconds in most examples).
    - Recommended: set `timeout` explicitly to something like **10–30 seconds** for Stop/UserPromptSubmit prompts; they are a single LLM call and should be fast.[^9_1][^9_2]
    - If they exceed timeout, Claude Code treats it “as if the hook didn’t exist,” so overly long timeouts make failures invisible but slow.[^9_5]
- **Agent hooks**
    - Spawn a subagent with tools and have a longer default timeout (docs mention **60 seconds** plus up to ~50 tool-use turns; some references note a higher global cap but advise keeping it low).[^9_8][^9_6][^9_1]
    - Recommended:
        - Lightweight checks (e.g., quick grep/read): **20–60 seconds**.
        - Heavy checks (full test suite): **60–120 seconds**, but only where really needed.[^9_9][^9_6][^9_1]

General guidance:

- **Always set `timeout` explicitly** for both prompt and agent hooks; don’t rely on defaults, since a timeout silently disables the hook for that event occurrence.[^9_7][^9_5]
- **Prefer prompt hooks** where the hook input alone is enough; reserve **agent hooks** for cases that truly need filesystem/command verification (tests, code search, schema checks).[^9_10][^9_1]

If you show me one of your existing Stop prompt hooks, I can rewrite it to follow these patterns with a concrete `timeout` tuned for your workflow.
<span style="display:none">[^9_11][^9_12][^9_13][^9_14][^9_15][^9_16][^9_17][^9_18]</span>

<div align="center">⁂</div>

[^9_1]: https://code.claude.com/docs/en/hooks-guide

[^9_2]: https://claude-blog.setec.rs/blog/prompt-based-stop-hooks/

[^9_3]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^9_4]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^9_5]: https://wmedia.es/en/writing/claude-code-hooks-practical-guide

[^9_6]: https://serenitiesai.com/articles/claude-code-hooks-guide-2026

[^9_7]: https://lobehub.com/skills/laurigates-claude-plugins-claude-hooks-configuration

[^9_8]: https://github.com/anthropics/claude-code/issues/19175

[^9_9]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^9_10]: https://www.morphllm.com/claude-code-hooks

[^9_11]: https://code.claude.com/docs/en/hooks

[^9_12]: https://hexdocs.pm/claude_agent_sdk/0.5.0/hooks_guide.html

[^9_13]: https://www.reddit.com/r/ClaudeAI/comments/1lq0q3t/claude_hooks_no_way_to_set_custom_timeout/

[^9_14]: https://preview.hex.pm/preview/claude_agent_sdk/0.4.0/show/HOOKS_GUIDE.md

[^9_15]: https://www.reddit.com/r/ClaudeAI/comments/1m31k7b/new_hook_userpromptsubmit/

[^9_16]: https://useworkflow.dev/docs/foundations/hooks

[^9_17]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^9_18]: https://www.facebook.com/groups/595424764221375/posts/2244713099292525/


---

# Real world examples of effective prompt hooks

There are a few solid real-world patterns emerging for prompt hooks; here are concise examples you can adapt.[^10_1][^10_2]

## 1. Stop hook: enforce task completion

From the official docs and community “force completion” patterns.[^10_2][^10_3]

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 15,
            "prompt": "Review the current session and the user's requested tasks. If ALL tasks are fully complete (code written, tests run or explicitly deferred, docs updated where requested), respond with {\"ok\": true}. If anything remains to be done or verified, respond with {\"ok\": false, \"reason\": \"what is still missing\"}. Only output JSON."
          }
        ]
      }
    ]
  }
}
```

Effect: every time Claude tries to stop, Haiku double-checks whether work is actually finished; if not, it blocks and feeds the `reason` back as the next instruction so Claude continues.[^10_4][^10_2]

## 2. UserPromptSubmit: normalize and enrich prompts

From hook deep-dive repos and videos.[^10_5][^10_6]

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 8,
            "prompt": "You are a prompt normalizer for a coding assistant. Given the user's raw prompt below, rewrite it as a clear, single development task with:\n- Target stack (infer from context if missing)\n- Explicit files or modules to work in if mentioned\n- Explicit constraints (tests, style, safety)\nReturn JSON: {\"ok\": true, \"updatedPrompt\": \"<rewritten prompt>\"}. Do not change the user's intent. Only output JSON."
          }
        ]
      }
    ]
  }
}
```

Effect: every user message is turned into a clean, structured coding request before it hits the main agent, improving consistency without changing how you type.[^10_7][^10_5]

## 3. Stop hook: coverage of a checklist (requirements, tests, docs)

From task-enforcement writeups and “Ralph Wilgum” pattern.[^10_3][^10_4]

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 20,
            "prompt": "Check whether you have (1) implemented all items in the user's task list or acceptance criteria, (2) added or updated tests where behavior changed, and (3) updated any relevant docs (README, CHANGELOG, API docs) if interfaces changed. If ANY of these are incomplete or unverified, respond with {\"ok\": false, \"reason\": \"which of (1)-(3) is still missing\"}. If all are complete, respond with {\"ok\": true}. Only output JSON."
          }
        ]
      }
    ]
  }
}
```

Effect: pushes Claude to reason explicitly about tests and docs, not just code, before it declares “done.”[^10_8][^10_3]

## 4. Stop hook: style / safety checker

Used in some “code quality” setups to keep answers within guidelines.[^10_9][^10_10]

```jsonc
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 10,
            "prompt": "You are a policy checker. Inspect the last assistant response. If it violates the coding style guide, leaks secrets (API keys, passwords), or suggests disabling safety features (auth, validation, logging) without justification, respond with {\"ok\": false, \"reason\": \"brief description of the violation\"}. Otherwise respond with {\"ok\": true}. Only output JSON."
          }
        ]
      }
    ]
  }
}
```

Effect: inexpensive semantic safety pass on every turn, no tools required.[^10_10][^10_9]

## 5. UserPromptSubmit: block dangerous commands

Community pattern to stop “rm -rf” style requests early.[^10_11][^10_1]

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 6,
            "prompt": "Examine the user's prompt. If it asks for destructive actions (e.g., deleting large directories, nuking databases, disabling backups, removing auth/logging), respond with {\"ok\": false, \"reason\": \"describe the risky action\"}. Otherwise respond with {\"ok\": true}. Only output JSON."
          }
        ]
      }
    ]
  }
}
```

Effect: cheap semantic filter before the main agent ever sees the prompt.[^10_12][^10_1]

These are all prompt-only (no tools) and line up with the current hooks guide’s recommended patterns for `type: "prompt"`: tiny JSON schema, explicit criteria, and short timeouts.[^10_2][^10_4]

Would you like me to draft a negative-existence Stop prompt hook for you that combines task completion with “no unverified ‘missing docs’ claims”?
<span style="display:none">[^10_13][^10_14][^10_15][^10_16][^10_17][^10_18]</span>

<div align="center">⁂</div>

[^10_1]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^10_2]: https://code.claude.com/docs/en/hooks-guide

[^10_3]: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement

[^10_4]: https://claude-blog.setec.rs/blog/prompt-based-stop-hooks/

[^10_5]: https://github.com/disler/claude-code-hooks-mastery

[^10_6]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^10_7]: https://github.com/anthropics/claude-code/issues/27365

[^10_8]: https://serenitiesai.com/articles/claude-code-hooks-guide-2026

[^10_9]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^10_10]: https://www.chatprd.ai/how-i-ai/workflows/automate-code-quality-and-fixes-with-ai-stop-hooks

[^10_11]: https://github.com/dagger/container-use/issues/253

[^10_12]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^10_13]: https://www.youtube.com/watch?v=Jqna_T9UR6o

[^10_14]: https://andrewford.co.nz/articles/claude-code-instant-notifications-ntfy/

[^10_15]: https://www.reddit.com/r/ClaudeAI/comments/1m31k7b/new_hook_userpromptsubmit/

[^10_16]: https://alexop.dev/posts/claude-code-notification-hooks/

[^10_17]: https://code.claude.com/docs/en/hooks

[^10_18]: https://agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/


---

# How to implement UserPromptSubmit hook to enforce coding standards

You enforce coding standards in `UserPromptSubmit` by intercepting the user’s prompt, checking it against your rules, and either blocking or rewriting it before Claude sees it.[^11_1][^11_2]

## 1. What UserPromptSubmit can do

From the docs and examples:[^11_3][^11_1]

- Fires right after the user hits enter, before Claude processes the prompt.
- Hook receives JSON with at least `prompt` (the raw user text).
- You can:
    - Block the prompt (exit code 2 or decision JSON).
    - Inject extra context via `additionalContext`.
    - In newer builds, optionally return an `updatedPrompt` to rewrite the prompt (feature is being rolled out).[^11_1][^11_3]

For coding standards, you usually either enrich the prompt with your standards or transform it into a “do this while following X guidelines” version.[^11_4]

## 2. Simple “inject standards” command hook

This pattern prepends your standards to every prompt without changing what the user typed.[^11_2][^11_1]

`.claude/settings.json`:

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["P:/hooks/user_prompt_coding_standards.py"],
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

`P:/hooks/user_prompt_coding_standards.py`:

```python
import sys
import json
from textwrap import dedent

raw = sys.stdin.read()
data = json.loads(raw)
user_prompt = data.get("prompt", "")

standards = dedent("""
You must follow this coding standard for all code you write in this repo:
- Language: TypeScript and Python only, no JavaScript or Ruby.
- Error handling: never swallow exceptions; log and rethrow or return Result types.
- Logging: use the shared logger (logger.ts / logger.py), no console.log/print in production paths.
- Testing: when changing behavior, add or update unit tests next to the code.
""").strip()

# additionalContext is merged into Claude's context for this prompt
output = {
  "additionalContext": standards
}

sys.stdout.write(json.dumps(output))
```

Effect: every prompt is processed as if you had prefixed it with that standards block, but the user experience stays unchanged.[^11_2][^11_1]

## 3. Prompt-based hook that rewrites the prompt

If you want the hook itself (a `type: "prompt"` LLM) to enforce standards by rewriting the prompt, you can do:

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 8,
            "prompt": "You are a coding-standards middleware. Given the user's raw prompt (see the 'prompt' field in the hook input), rewrite it as a clear coding request that explicitly instructs Claude to follow our house coding standards:\n- Use TypeScript with strict types for frontend/backend, Python 3.11 for scripts.\n- Follow our error handling pattern (no bare except, no silent failures).\n- Add or update tests when behavior changes.\nReturn JSON only: {\"ok\": true, \"updatedPrompt\": \"<rewritten prompt>\"}. Do not change the user's intent; only add or clarify the coding standards requirement.",
            "includeArguments": true
          }
        ]
      }
    ]
  }
}
```

Notes:[^11_5][^11_3][^11_1]

- `includeArguments` (or `$ARGUMENTS` in the prompt, depending on your version) gives the hook access to the `prompt` field.
- Claude returns JSON; Claude Code uses `updatedPrompt` (where supported) as the actual prompt that the main agent sees.[^11_3][^11_1]
- This is how videos show “rewrite prompts on the fly to enforce coding standards / TDD.”[^11_5][^11_4]

If your current build doesn’t yet support `updatedPrompt`, you can instead return `additionalContext` from a command hook like in section 2, which works in all versions.[^11_1][^11_3]

## 4. Blocking clearly non-compliant requests

You can also block prompts that explicitly request violating your standards (e.g., “ignore tests, just hack it in prod”):[^11_6][^11_7]

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "timeout": 6,
            "prompt": "Inspect the user's prompt in the 'prompt' field. If they explicitly ask to violate coding standards (skip tests entirely, disable logging/auth/validation in production, add secrets directly into code), respond with {\"ok\": false, \"reason\": \"brief description of the violation\"}. Otherwise respond with {\"ok\": true}. Only output JSON.",
            "includeArguments": true
          }
        ]
      }
    ]
  }
}
```

Claude Code will then either send the prompt through or block and show the `reason` to the user.[^11_8][^11_1]

Would you rather (a) always inject your standards for every prompt, or (b) only inject them for prompts that involve code changes (detected via keywords like “function”, “class”, “refactor”, “bug”)?
<span style="display:none">[^11_10][^11_11][^11_12][^11_13][^11_14][^11_15][^11_9]</span>

<div align="center">⁂</div>

[^11_1]: https://code.claude.com/docs/en/hooks-guide

[^11_2]: https://www.datacamp.com/tutorial/claude-code-hooks

[^11_3]: https://github.com/anthropics/claude-code/issues/27365

[^11_4]: https://debugg.ai/resources/pre-prompt-middleware-claude-code-hooks-enforce-pm-and-coding-standards

[^11_5]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^11_6]: https://www.reddit.com/r/ClaudeAI/comments/1m31k7b/new_hook_userpromptsubmit/

[^11_7]: https://github.com/anthropics/claude-code/issues/427

[^11_8]: https://www.reddit.com/r/ClaudeAI/comments/1m7r9us/clarification_about_hooks_userpromptsubmit_now/

[^11_9]: https://code.claude.com/docs/en/hooks

[^11_10]: https://github.com/disler/claude-code-hooks-mastery

[^11_11]: https://github.com/dagger/container-use/issues/253

[^11_12]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^11_13]: https://code.claude.com/docs/en/output-styles

[^11_14]: https://smartscope.blog/generative-ai/claude/claude-code-hooks-guide/

[^11_15]: https://koder.ai/blog/claude-code-style-guide-prompts

