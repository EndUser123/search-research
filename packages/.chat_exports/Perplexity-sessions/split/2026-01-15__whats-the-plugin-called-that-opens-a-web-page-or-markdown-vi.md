---
title: "what's the plugin called that opens a web page or markdown viewer in claude code?"
date: "2026-01-15"
mode: "COPILOT"
uuid: "a02b8e83-9168-4fea-b774-2aa653f51bf0"
entry_count: 6
---

## Human

what's the plugin called that opens a web page or markdown viewer in claude code?

## Assistant

The plugin you are thinking of is the **`headless`** plugin from the `paddo/claude-tools` marketplace, which is used to open and render web pages (and effectively view their markdown) from Claude Code.[1]

## Plugin name

- The plugin is called **`headless`**, and it lives in the `paddo/claude-tools` plugin marketplace collection.[1]
- It is installed via the Claude plugin marketplace, e.g. `claude plugin install headless@paddo-tools`.[1]

## What it does

- The **`headless`** plugin provides a headless browser-style capability so Claude Code can load and work with an arbitrary web page.[1]
- Once installed, you can invoke it via its slash commands to grab page content in a markdown-friendly format for viewing or feeding back into Claude Code.[1]

## Human

but I can't see it in the terminal.

## Assistant

You will not see `headless` in the Claude **terminal** unless you’ve actually added the paddo marketplace and installed it, and even then it only shows up in the plugin menu and as `/headless:*` commands, not as a separate “panel” or built‑in viewer.[1][2]

## Quick checks

- Run `claude plugin marketplace list` and confirm `paddo/claude-tools` is present; if not, add it with:  
  `claude plugin marketplace add paddo/claude-tools`.[2][1]
- Then install explicitly:  
  `claude plugin install headless@paddo-tools`.[1]

## How to see/confirm it

- In a Claude Code session, use `/plugin` → “Manage & uninstall plugins” and verify that **headless** is listed as installed.[3][2]
- In the main chat input, type `/headless:` and check whether completions like `/headless:test` or `/headless:parity` appear; if they do, the plugin is active even if you do not see any new terminal UI element.[1]

## If it still doesn’t appear

- Some users have reported plugins “disappearing” from lists until a restart; fully exit Claude Code, run `claude update`, then reopen and re-run `/plugin`.[4][2]
- Also confirm you are on Claude Code 2.1.x or later, since plugin support, marketplaces, and visibility were stabilized around that release.[5][3]

If you describe exactly what you ran (`claude` version, the `plugin` commands, and where you’re looking), a more step-by-step check specific to your setup is possible.

## Human

no, I mean I can't see a rendered markdown file, or mermaid diagram, etc.

## Assistant

There is currently no built-in Claude Code “markdown/diagram viewer” panel; rendering is handled by your editor (VS Code / Cursor / Zed) or by external MCP/skills that open a browser window, not inside the Claude terminal itself.[1][2][3]

## Markdown rendering

- For plain **markdown**, use your editor’s preview: in VS Code that is the built-in Markdown Preview / “Open Preview to the Side”, which will render any `.md` file Claude creates, including tables and basic diagrams expressed as markdown.[4][1]
- Claude just writes `.md` files; viewing them is handled by the editor UI, so nothing new appears in the Claude terminal beyond the raw markdown text.[5][1]

## Mermaid diagrams

- For **Mermaid**, there are MCP servers/plugins like `claude-mermaid` that render diagrams by opening a live-preview page in your browser and auto-refreshing as you edit, instead of drawing them in the Claude panel itself.[2][6]
- The typical workflow is: ask Claude to create/update the Mermaid code in a file, then use the Mermaid MCP tool (e.g., `mermaid_preview`) to open a live-rendered diagram in your browser while you keep editing the text in your editor.[6][2]

## What you can do now

- Use the editor’s markdown preview for `.md` artifacts and let Claude keep generating/updating those files.[1][4]
- If you want rich diagram previews, install a Mermaid MCP server/plugin (such as `claude-mermaid`) so diagrams open in a browser window with live reload, which is the closest current equivalent to a “diagram viewer” for Claude Code.[2][6]

## Human

I'm pretty sure I saw a youtube video.  It opened a kind of canvas in claude code.

## Assistant

You’re almost certainly thinking of the **Claude Canvas** plugin, which opens a visual “canvas” in a split pane inside Claude Code’s terminal UI.[1][2]

## What Claude Canvas is

- **Claude Canvas** is a plugin/skill that gives Claude Code a graphical canvas layer, letting it spawn visual panels (for layouts, dashboards, etc.) alongside the text terminal.[2][1]
- In demos, it’s used to show things like flight layouts, agendas, or custom UIs that Claude controls, which is probably the YouTube video you saw.[3][1]

## How it appears in Claude Code

- When installed, canvas views open in a **split pane** inside your terminal (TUI-style), not as a normal VS Code webview, which is why it looks like “a canvas in Claude Code” rather than an editor preview.[2]
- You trigger it via a plugin/skill command (e.g., a `/canvas`-style command or a specific skill) and Claude then updates that canvas while you interact in the main pane.[1][2]

## Markdown / diagrams on the canvas

- Claude Canvas itself is more of a **general visual dashboard** layer; some demos show it rendering structured content or UI-like layouts, but not a generic “markdown preview” identical to VS Code’s.[1][2]
- For pure markdown/mermaid rendering, you still typically rely on the editor preview or specialized plugins (like Mermaid preview skills), but Canvas can be used to build custom visualizations driven by Claude.[4][5][1]

If you want, next step can be: walk through the exact install and invocation commands for Claude Canvas on your setup so you can reproduce what you saw in that video.

## Human

How do I enable Claude Canvas in Claude Code

## Assistant

Claude Canvas is an external plugin/skill you add via a plugin marketplace, then invoke from Claude Code; it is not enabled by default.[1][2]

## 1. Prerequisites

- Make sure you are on a Claude Code build that supports `/plugin` and marketplaces (2.0.7x+ / 2.1+).[3]
- Install **bun** and **tmux** (Canvas uses them to spawn split panes for the canvas views).[1]

## 2. Add the marketplace that hosts Claude Canvas

The typical pattern (as shown in recent videos) is:

- Use `/plugin marketplace add <marketplace-url-or-alias>` to add the marketplace that includes **`claude-canvas`**.[4][1]
- After adding, run `/plugin marketplace list` and confirm the marketplace that lists **`claude-canvas`** is visible.[2][4]

(If the video you watched linked a specific marketplace URL, use that exact URL/alias; Canvas is usually listed as `claude-canvas` with a description like “gives Claude Code its own display/external monitor”. )[4][2]

## 3. Install Claude Canvas

- In a Claude Code session, run a plugin install command similar to:  
  `/plugin install claude-canvas`  
  or, if namespaced, `/plugin install claude-canvas@<marketplace-id>`.[2][1]
- Choose user or workspace scope when prompted; user-scope is enough for personal use.[1]

You can verify installation with `/plugin` → “Manage & uninstall plugins” and checking that **Claude Canvas** appears in the list.[1]

## 4. Use Claude Canvas from Claude Code

- With tmux and bun set up, open Claude Code in your terminal and start a session as usual (`claude`).[1]
- Use the Canvas command the plugin exposes (in the video it’s a canvas-related command that Claude suggests once the plugin is installed) and Claude will spawn a **split pane** where the canvas UI lives.[1]
- That canvas pane is where you can ask Claude to show layouts, dashboards, or effectively “rendered” views while you keep chatting in the main pane.[5][1]

If you paste the exact command line the video shows (or a link to that video), a concrete, copy‑pasteable set of commands for your environment (Windows + WSL + tmux, etc.) can be tailored to match it.

## Human

does it work on windows 11?

## Assistant

Claude Canvas itself does **not** work on native Windows terminals; it requires a Unix‑style environment and tmux, and the author explicitly calls out Windows as a limitation.[1][2]

## What this means on Windows 11

- The Canvas plugin spawns extra panes using **tmux**, which is why it only works reliably on Linux/macOS terminals right now.[2][1]
- In the demo video, the creator says the smoother UX “won’t work for Windows,” so running it directly in Windows Terminal or cmd/PowerShell is not supported.[1]

## Possible workaround

- You *can* still use Claude Code on Windows by running it inside **WSL (Ubuntu)** and installing tmux there; that gives you a Linux terminal where Canvas can run, even though the host OS is Windows 11.[3][4]
- The workflow is: install WSL + Ubuntu, install tmux and bun inside WSL, run `claude` from the WSL shell, then install and use Claude Canvas from that environment.[4][3][2]
