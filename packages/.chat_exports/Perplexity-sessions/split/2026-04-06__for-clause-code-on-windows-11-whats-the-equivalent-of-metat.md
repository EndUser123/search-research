---
title: "for clause code, on windows 11, what's the equivalent of 'meta+t'?"
date: "2026-04-06"
mode: "CONCISE"
uuid: "5c7d7741-93c8-4e10-82b1-d8d16049754d"
entry_count: 4
---

## Human

for clause code, on windows 11, what's the equivalent of 'meta+t'?

## Assistant

**In Claude Code on Windows 11, the equivalent of 'Meta+T' (Cmd+T on macOS) is also Meta+T.**[1][2]

## What It Does
Meta+T triggers `chat:thinkingToggle`, toggling extended thinking mode in the chat context.[2][1]

## Windows Key Mapping
- Meta maps to the Windows key (⊞).[2]
- Press Windows key + T. Defaults unchanged unless customized via `/keybindings`.[1]

## Customization
Run `/keybindings` to edit `~/.claude/keybindings.json` and rebind if needed (v2.1.18+).[1]

## Notes
No Windows-specific override listed; uses cross-platform Meta. Test in your terminal (e.g., Git Bash, PowerShell). Verify version with `claude --version`.[1]

## Human

Windows plus T does not change the thinking mode. All it does is make my Windows screens show other screens and stuff.

## Assistant

**Windows+T fails because Windows OS intercepts it for task switching, blocking Claude Code.**[1]

## Reliable Toggle Methods
Press **Alt+T** for `chat:thinkingToggle`—the documented cross-platform default unaffected by Win key.[2][3][1]

- Or **Tab** (older versions; check yours).[4]
- Run `/config`, select "Thinking Mode", toggle True/False (sticky).[5][6][7]

## Verify Keybindings
Run `/keybindings` to list/edit `~/.claude/keybindings.json`. Confirm `chat:thinkingToggle` binding; customize if conflicted (e.g., to Ctrl+T). Restart Claude Code after edits.[8][2]

## Terminal Tips
Use Windows Terminal/PowerShell 7+ with Node >=24.2.0 for VT mode supporting Meta properly. Avoid Git Bash if Alt issues persist.[9][10][2]

Test Alt+T now—what's your Claude Code version (`claude --version`)?[2]

## Human

In Claude Code on Windows 11, how do I switch between thinking mode and non-thinking mode, or between high-thinking mode and medium-thinking mode easily?

## Assistant

**Claude Code uses `/effort` for easy switching between low/medium/high/max thinking levels (persistent across sessions).**[1][2]

**Toggle basic thinking on/off with Alt+T (works reliably on Windows 11, avoiding Win+T conflicts).**[3][4]

## Effort Levels
Run these commands—`low`/`medium`/`high` (default) adjust adaptive thinking depth; `max` (Opus 4.6 only) maximizes it.[2][1]

| Level | Thinking Behavior | Use Case |
|-------|-------------------|----------|
| low | Minimal; skips simple tasks | Speed on basics [1] |
| medium | Moderate; skips very simple | Balanced [1] |
| high | Always deep (default) | Complex tasks [1] |
| max | Unconstrained depth | Hard problems (slow/costly) [1] |

Reset: `/effort auto`.[1]

## Toggle Shortcuts
- **Alt+T**: Basic on/off (sticky).[4][5][3]
- **Tab**: Legacy toggle (buggy in some versions).[6][3]
- Prompt triggers (per-turn): `think` (low), `think harder` (medium), `ultrathink` (high/max).[7][8]

## Windows Tips
`/config` may also toggle binary thinking (true/false). Customize via `/keybindings` if needed. Run `claude --version` for your build.[9][6]

## Human

Is it possible to have some skills use higher effort than others? Like RCA and architecture versus code, for example.

## Assistant

Yes. **Per-skill effort is supported, so you can run RCA/architecture at higher effort and routine code edits at lower effort in Claude Code.**[1][2]

## How per-skill effort works

- Each skill can declare its own **effort level** (`low`, `medium`, `high`, `max`) in the skill file, independent of the global `/effort` setting.[2][1]
- Effort controls how deeply the agent reasons when executing that skill (thinking depth, number of tool calls, verbosity), on top of adaptive thinking.[3][4]

Typical pattern for your use case:  
- **RCA / architecture skills**: set to `high` or `max` for deeper multi-step reasoning and more verification.[3][1]
- **Code-change / formatting skills**: set to `low` or `medium` for faster, cheaper actions.[1][2]

## Where to configure it (skills)

In Claude Code skills, effort is configured **inside the skill definition**, usually in YAML at the top of the skill file.[2][1]

Conceptually (structure only, not exact syntax):

```yaml
skill: rca_analysis
effort: high
# rest of skill …

skill: code_edit
effort: low
# rest of skill …
```

- The exact field name and placement follow the skill schema used by Claude Code, but the key idea is: **effort is declared per skill, not just globally.**[5][1][2]
- Once set, whenever that skill runs, it uses its configured effort level even if your global `/effort` is different.[1][2]

## How this interacts with `/effort` and thinking

- `/effort` in the chat sets a **default** for general conversations and any skills without an explicit effort.[6][3]
- A **per-skill effort** setting overrides that default for that skill’s runs.[2][1]
- Under adaptive thinking, effort acts as the ceiling/bias for how much thinking is used during that skill’s tool calls and reasoning.[4][3]

**Practical next step:** for the RCA/architecture skills you care about, open their skill files and add a high/max effort setting, and set lower effort on mundane code skills so you get deep reasoning where it matters without blowing tokens everywhere.[1][2]
