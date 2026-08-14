---
title: "provide an operational guide based on the transcript, to implement the ideas, in claude code on windows 11."
date: "2026-06-19"
mode: "COPILOT"
uuid: "5f8a3fdd-9e73-47e4-83ad-2756ee8759bc"
entry_count: 1
---

## Human

provide an operational guide based on the transcript, to implement the ideas, in claude code on windows 11.

## Assistant

Yes — but one important correction first: the video demonstrates the core idea correctly, while the current Claude Code docs indicate that for `UserPromptSubmit` you should use `additionalContext` to inject or transform prompt context, rather than relying on arbitrary stdout text as the primary mechanism. `UserPromptSubmit` hooks receive the submitted `prompt`, and hooks are configured in `settings.json`; the docs explicitly say prompt-stage hooks can add context with `additionalContext`.[1][2][3]

## What the video shows

The transcript’s pattern is: parse JSON from stdin, extract the prompt, build a rewritten version, log both original and modified forms, and emit the modified content so Claude uses the enhanced prompt path. The example prefixes the user’s input with “tell me a joke on …”, so a bare input like “finance” becomes a more specific instruction and yields the intended style of answer.[1]

Operationally, the durable idea is not “always rewrite to a joke,” but “insert a deterministic transformation layer before Claude sees the final effective instruction.” That is useful for hidden context injection, standardization, guardrails, sanitization, and prompt normalization.[2][1]

## Recommended design

On Windows 11, implement this as a small Node or Python hook script plus a project-local `.claude/settings.json`. Project-local settings are the right default when you want repo-specific behavior that is versionable and shareable with a team; user-wide settings exist too, but are better for personal defaults.[3][4]

Use a narrow, explicit transformation policy:
- Read hook payload from stdin as JSON.
- Extract `prompt`.
- Apply deterministic rewrite rules, for example prepend coding standards, expand shorthand intents, or attach hidden project context.
- Return `additionalContext` for Claude, and separately append an audit log entry with original and transformed prompt.
- Fail closed only when necessary; otherwise prefer no-op pass-through on parse errors.[4][2][3][1]

## Windows 11 layout

A practical repo layout on Windows is:
- `.claude/settings.json`
- `.claude/hooks/user-prompt-submit.mjs`
- `.claude/logs/prompt-audit.jsonl`

This is preferable to stuffing shell one-liners into settings because Windows quoting is brittle, JSON escaping is annoying, and a real script is easier to test and secure. Hooks run with your user permissions, so treat them like production code and validate all input before using it.[3][4]

Example `settings.json` shape, adapted to the documented hooks model:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/user-prompt-submit.mjs"
          }
        ]
      }
    ]
  }
}
```

That structure matches the documented hook configuration model in Claude Code, where hooks are declared by event name and each event contains one or more command hooks.[4][3]

## Node implementation

Below is a Windows-friendly Node version that follows the transcript’s spirit but aligns with the current docs by returning structured JSON with `additionalContext`. The exact output contract can evolve across Claude Code versions, so verify against the installed version’s docs if behavior differs.[2][3]

```js
// .claude/hooks/user-prompt-submit.mjs
import fs from "node:fs";
import path from "node:path";

const readStdin = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
};

const ensureDir = (dir) => {
  fs.mkdirSync(dir, { recursive: true });
};

const normalizePrompt = (prompt) => {
  const p = (prompt || "").trim();
  if (!p) return { original: "", rewritten: "", additionalContext: "" };

  let additionalContext = "";
  let rewritten = p;

  if (/^(fix|debug|investigate)\b/i.test(p)) {
    additionalContext += [
      "Work systematically.",
      "Inspect existing code paths before proposing changes.",
      "Prefer minimal modifications.",
      "State assumptions, edge cases, and uncertainty explicitly."
    ].join(" ");
  }

  if (/^(make|write|create)\b/i.test(p) && /\b(feature|hook|plugin|script)\b/i.test(p)) {
    additionalContext += " Prefer project-local implementation, Windows 11 compatibility, and concise TypeScript or Python examples unless another language is already established.";
  }

  return { original: p, rewritten, additionalContext: additionalContext.trim() };
};

try {
  const raw = await readStdin();
  const input = JSON.parse(raw);
  const prompt = typeof input.prompt === "string" ? input.prompt : "";

  const result = normalizePrompt(prompt);

  const logDir = path.resolve(".claude/logs");
  ensureDir(logDir);
  fs.appendFileSync(
    path.join(logDir, "prompt-audit.jsonl"),
    JSON.stringify({
      ts: new Date().toISOString(),
      session_id: input.session_id ?? null,
      cwd: input.cwd ?? process.cwd(),
      original: result.original,
      rewritten: result.rewritten,
      additionalContext: result.additionalContext
    }) + "\n",
    "utf8"
  );

  process.stdout.write(
    JSON.stringify({
      continue: true,
      suppressOutput: true,
      additionalContext: result.additionalContext
    })
  );
} catch (err) {
  process.stdout.write(
    JSON.stringify({
      continue: true,
      suppressOutput: true
    })
  );
}
```

This implementation keeps the user-visible prompt unchanged, injects hidden operational guidance, and writes an audit trail with original plus derived context, which is the cleanest translation of the video’s “original + modified” logging idea into the current documented hook model.[1][2][3]

## Python implementation

If you prefer Python on Windows:

```python
# .claude/hooks/user_prompt_submit.py
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import sys
import re

def normalize_prompt(prompt: str):
    p = (prompt or "").strip()
    if not p:
        return {"original": "", "rewritten": "", "additionalContext": ""}

    additional = []
    if re.match(r"^(fix|debug|investigate)\b", p, re.I):
        additional.extend([
            "Work systematically.",
            "Inspect existing code paths before proposing changes.",
            "Prefer minimal modifications.",
            "State assumptions, edge cases, and uncertainty explicitly."
        ])

    if re.match(r"^(make|write|create)\b", p, re.I) and re.search(r"\b(feature|hook|plugin|script)\b", p, re.I):
        additional.append("Prefer project-local implementation, Windows 11 compatibility, and concise TypeScript or Python examples unless another language is already established.")

    return {
        "original": p,
        "rewritten": p,
        "additionalContext": " ".join(additional).strip()
    }

def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        prompt = data.get("prompt", "")
        result = normalize_prompt(prompt)

        log_dir = Path(".claude/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "prompt-audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_id": data.get("session_id"),
                "cwd": data.get("cwd", os.getcwd()),
                "original": result["original"],
                "rewritten": result["rewritten"],
                "additionalContext": result["additionalContext"]
            }) + "\n")

        sys.stdout.write(json.dumps({
            "continue": True,
            "suppressOutput": True,
            "additionalContext": result["additionalContext"]
        }))
    except Exception:
        sys.stdout.write(json.dumps({
            "continue": True,
            "suppressOutput": True
        }))

if __name__ == "__main__":
    main()
```

Use this in settings with a command such as `python .claude/hooks/user_prompt_submit.py`. The design is the same: deterministic transform, structured output, and append-only audit logging.[3][4]

## High-value rewrite patterns

The transcript uses a toy “tell me a joke” prefix, but in real Claude Code workflows the best prompt rewrites are these:

- Standards injection: append hidden instructions like “use existing patterns, avoid broad refactors, run targeted validation first.” This is exactly the class of “enforce coding standards” and “improve prompt clarity” use case described in the video summary.[1]
- Context injection: add repo-specific rules, architecture constraints, forbidden paths, test commands, or coding conventions without forcing the human to retype them every time. The docs describe `additionalContext` specifically for this type of prompt-stage augmentation.[2][3]
- Sanitization: detect obvious secrets, tokens, or pasted credentials and block or redact before the request proceeds. The video description calls out sanitizing sensitive input as a use case, and general hook guidance recommends validating and sanitizing hook input.[4][1]
- Intent expansion: rewrite vague prompts such as “fix this” into a hidden structure: inspect first, identify root cause, propose smallest change, explain tradeoffs. This preserves user ergonomics while improving consistency.[1]

## Windows 11 specifics

On Windows 11, avoid depending on Bash syntax unless you know Claude Code is running under Git Bash, WSL, or a Unix-like shell. A direct `node ...mjs` or `python ...py` command is more robust across PowerShell and standard Windows environments.[4]

Also keep paths repo-relative and avoid shell interpolation where possible. The general hook guidance warns to validate JSON input, quote variables, and use explicit paths because hooks execute with your user permissions and are not sandboxed.[4]

## Safe rollout

Start with observe-only mode:
1. Log original prompt plus computed `additionalContext`.
2. Return no blocking behavior.
3. Verify a week of prompts.
4. Add only one rewrite family at a time, for example debugging prompts first.

That rollout is safer than immediate hard enforcement because prompt rewrites can create hidden behavior that is hard to notice when they go wrong. Confidence is high that logging plus additive context injection is the least risky starting point; confidence is medium on any more aggressive “full rewrite” strategy because version-specific hook output semantics may vary.[2][3][1][4]

## Practical policy

For your style of Claude Code usage on Windows 11, I would implement this first policy:

- On `UserPromptSubmit`, if the prompt looks like debugging, architecture, or implementation work, inject:
  - inspect existing files and flows first
  - prefer minimal necessary changes
  - reuse existing code before creating new abstractions
  - state assumptions and uncertainty
  - give concrete next steps

That policy directly operationalizes the behavior you want from Claude Code without forcing you to type it every turn, and it stays close to the transcript’s core mechanism: intercept prompt, derive enhanced intent, and feed Claude the improved version behind the scenes.[2][1]

Would you like a second version tailored specifically to your Claude Code plugin/skills workflow, including rules for hooks, skills, and multi-terminal safety?
