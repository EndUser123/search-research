---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-02-25"
mode: "COPILOT"
uuid: "7a939a47-b6c1-4c73-964e-168b8597c145"
entry_count: 1
---

## Human

You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and obvious filler. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works or makes decisions in this domain.[2][1]

Produce a rewritten version of the thread that:

- Keeps every distinct **insight, workflow, configuration, or regimen**, including:
  - Specific sequences of actions, steps, or protocols people follow.
  - Concrete parameter choices (doses, thresholds, settings, schedules, frequencies, tools).[1]
  - Integration details between {artifacts_1}, {artifacts_2}, and {artifacts_3} (e.g., how they are chained or orchestrated).
- Preserves all mentions of **key artifacts** and what people actually do with them:
  - {artifact_type_1}: e.g., tools, agents, drugs, components.
  - {artifact_type_2}: e.g., files, documents, guidelines, protocols.
  - {artifact_type_3}: e.g., automations, policies, hooks, governance mechanisms.
- Removes repeated restatements of the same idea unless a repetition adds a new nuance, constraint, or failure mode.

After the rewrite, add a section called **“Operational patterns and setups”** where you explicitly list:

- **Multi‑entity flows**
  - How multiple {entities} are used together (e.g., “I use {artifact_A} and {artifact_B}, then have {artifact_C} consolidate and apply changes”).[1]
- **Automation patterns**
  - Any described triggers, scheduled runs, pipelines, or hooks that react to events or phases.
  - Any rules that determine when something is reviewer‑only vs allowed to auto‑modify.[3][1]
- **Guardrail artifacts**
  - Named documents, configs, or policies (e.g., {guardrail_doc_1}, {guardrail_doc_2}) and the key rules or principles they encode.
  - How those guardrails are enforced in practice (checks, reviews, blocking conditions).

Add a final section **“Practical recommendations”** that distills the most useful advice into concrete steps another practitioner in this domain could implement, for example:

- “Set up {artifact_or_system} with {N} parallel {entities} and one consolidator that merges and applies decisions.”
- “Add a hook or rule that blocks {undesired_pattern} unless {explicit_condition} is met.”
- “Configure {tool_or_policy} to act as a reviewer/critic only, not an automatic changer, for high‑risk operations.”[1]
- “Centralize principles in a single {guardrail_doc} and reference it in every {process_stage} where decisions are made.”

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow, configuration, regimen, or recommendation from the conversation that could alter how someone operates in this domain.[1]

***

To use it, just fill:

- {domain} → “technical”, “clinical evidence”, “policy”, etc.  
- {artifacts_*}, {entities}, {guardrail_doc_*}, {tool_or_policy}, {undesired_pattern}, {process_stage} with your domain‑specific terms.

## Assistant

## Rewritten thread (technical remote-control workflows)

### Core capability: remote control for Claude Code

- Claude Code now supports **remote control**: you can run Claude Code locally (or on a server) and control that exact session from your phone or another device via the Claude app or Claude web UI.[1, {ts:8}]
- Once remote control is enabled, any messages you send in the Claude app’s “Code” tab go to the selected running Claude Code session and appear in your local terminal as if you typed them yourself.[1, {ts:91}]
- This replaces older setups like tmux + Tailscale + mobile terminal apps (e.g., Terminus); those still work but are more fiddly for permission handling and setup.[1, {ts:20}]

### Basic local setup and usage

- Start in the folder you want Claude Code to manage (e.g., a “RayOS” folder that holds all your personal/operational files).[1, {ts:31}]
- Run `claude rc` or `claude remote-control` to start a remote-controllable Claude Code session.[1, {ts:44}]
- The **first run** requires enabling a secure connection from your machine to Anthropic’s servers; a prompt appears in the terminal to enable remote control.[1, {ts:54}]
- To use elevated capabilities without prompts, you can instead run `claude dangerously skip permissions`, then use `/remote-control` inside that session to enable remote control just for that session.[1, {ts:68}][1, {ts:54}]
- To enable remote control **for all future sessions**, run `/config`, search for “remote control”, set “enable remote control for all sessions” to `true`, then save (Escape to exit).[1, {ts:80}]

### Phone / remote device control flow

- Install and log into the Claude app on your phone, then go to the **Code** tab on the left.[1, {ts:91}]
- Locate the running remote-controllable session by name and select it; this links your phone’s chat interface to that terminal session.[1, {ts:91}]
- Example usage: from the phone, send instructions like “Go to my Google Drive folder, find the raw MP4 file, and edit it with the video editor skill.”[1, {ts:106}]
- The terminal session then executes your instructions, using your existing Claude Code configuration, skills, and MCP servers, including those that depend on local file mounts (e.g., local Google Drive).[1, {ts:115}][1, {ts:171}]
- You can start multiple sessions locally (e.g., one for video editing, another for coding projects) and remote-control each from your phone, switching between sessions as needed.[1, {ts:127}][1, {ts:136}]

### Permissions and security considerations

- **Dangerously skip permissions** gives Claude Code more power to act without prompting but increases risk, especially if the session has network access and tools that can modify files or execute arbitrary commands.[1, {ts:221}]
- Safer alternative: run without dangerously skip permissions and approve permissions from your phone whenever Claude Code needs to perform sensitive operations, making it less fiddly than older remote-terminal solutions.[1, {ts:158}][1, {ts:146}]
- Remote control uses a **secure connection via Anthropic servers**; your local session appears as a “remote session” on other devices, including via the Claude web interface.[1, {ts:234}][1, {ts:246}]
- For **isolation**, you can:
  - Run Claude Code on a **remote server** (e.g., Hetzner) and allow dangerously skip permissions there, so any prompt-injection damage is limited to that server.[1, {ts:258}][1, {ts:352}]
  - Use **Claude Code sandboxing** with strong limits on which tools and hosts are allowed.[1, {ts:378}][1, {ts:365}]
  - Add a **network proxy** and restrict traffic by domain, while still allowing the Anthropic API so remote control keeps working.[1, {ts:441}][1, {ts:456}]

### Remote server deployment workflow (Hetzner example)

- In Hetzner:
  - Create a new server, choosing the cheapest tier (around 3.49 €/month) and a region like Germany.[1, {ts:280}]
  - Add your SSH key and name the server (e.g., “Claude Code”).[1, {ts:280}]
- SSH into the server and:
  - Run the Claude Code install command.[1, {ts:297}]
  - Apply a provided shell fix command if needed for bash compatibility.[1, {ts:297}]
  - Run `claude` to start Claude Code and sign in with your Anthropic subscription.[1, {ts:310}][1, {ts:297}]
- Use `tmux`:
  - Start `tmux` on the server.[1, {ts:310}]
  - Inside tmux, run `claude`, accept the terms, and run `/remote-control` to enable remote control in that session.[1, {ts:324}][1, {ts:310}]
  - Detach from tmux (e.g., `Ctrl+B` then `:` then `detach`) so the session continues running in the background while you disconnect from SSH.[1, {ts:324}]
- From your phone (or another machine), open the Claude app, go to Code, select the server-backed remote session, and issue tasks such as “search online and tell me about Claude Code.”[1, {ts:339}][1, {ts:324}]
- You can install MCP servers on this remote server so it can run background research tasks, generate reports, and stay online without depending on your local machine.[1, {ts:352}][1, {ts:339}]

### Sandboxed research environment with settings.local

- Create a dedicated **sandbox folder** for research sessions.[1, {ts:365}]
- In that folder, create or edit `settings.local.json` with keys such as:
  - `sandbox.enabled: true`[1, {ts:378}]
  - `permissions.defaultMode: "don't ask"` (so allowed actions don’t prompt for approval).[1, {ts:378}]
  - A list of **allowed websites** for research.[1, {ts:378}]
  - A list of **denied tools**, including editing/writing tools and bash tools, to prevent file modification and shell access.[1, {ts:390}][1, {ts:378}]
- Start a Claude Code session in that folder (`claude rc`), then select the appropriate sandboxed session in the Claude app under the research environment.[1, {ts:390}]
- Example: ask it to “go on arXiv and find the latest AI papers and summarize 5 that look interesting,” which it performs without prompting because those URLs and operations are allowed.[1, {ts:404}][1, {ts:390}]
- If you instruct it to fetch a blocked URL (e.g., `masterclaudecode.com`), WebFetch in the sandbox will refuse; because bash tools are disabled, it cannot bypass restrictions with `curl`.[1, {ts:416}][1, {ts:428}][1, {ts:404}]

### Proxy-based network guardrail

- To further tighten security, configure a **proxy** and route Claude Code’s network access through it.[1, {ts:428}][1, {ts:441}]
- In your sandbox configuration:
  - Disable WebFetch and WebSearch tools, since they would bypass the proxy.[1, {ts:441}][1, {ts:428}]
  - Set up an HTTP proxy port in the config (e.g., `network.httpProxyPort: <port>`).[1, {ts:441}]
- Implement a simple proxy script (e.g., `proxy.js` with Node) that:
  - Allows only whitelisted domains, including `api.anthropic.com` so remote control and API calls still function.[1, {ts:456}][1, {ts:441}]
  - Blocks all other outbound HTTP requests, logging them as blocked.[1, {ts:472}][1, {ts:441}]
- Run the proxy with `node proxy.js`, then start Claude Code with `claude rc dangerously skip permissions`, ensuring its traffic is routed through the proxy.[1, {ts:472}][1, {ts:456}]
- Test behavior:
  - Accessing a blocked domain (e.g., your personal domain) should fail, with the proxy logging the HTTP GET as blocked.[1, {ts:472}]
  - Accessing an allowed domain (e.g., `masterclaudecode.com`) should succeed and show as passed via the proxy.[1, {ts:484}][1, {ts:472}]
- This pattern supports research agents running with dangerously skip permissions but constrained to a specific set of websites and with many permissions blocked, making harmful actions harder.[1, {ts:508}][1, {ts:495}]

### Remote control vs OpenClaw and tmux setups

- Compared to older tmux + Tailscale + Terminus setups, the new remote control flow centralizes permission prompts and configuration, making it easier to approve actions from your phone rather than manually interacting with a remote terminal.[1, {ts:20}][1, {ts:158}]
- Compared to OpenClaw:
  - OpenClaw can proactively run on schedules (e.g., search online on a cron and push notifications), whereas Claude Code remote control is **passive**: you issue a command, it runs for a while, then waits.[1, {ts:519}][1, {ts:508}]
  - Claude Code remote control leverages your existing Claude Code configuration (skills, MCP servers, project-specific setups) and your Claude subscription instead of external orchestrators.[1, {ts:171}][1, {ts:569}]
- There is an explicit desire for features similar to OpenClaw, such as:
  - Hooks that can schedule or trigger actions automatically.
  - Integration between Claude Code hooks and phone notifications.[1, {ts:531}][1, {ts:519}]
- Commented workflow idea: use OpenClaw as an orchestrator with access to an “agent 0” and run both in a sandbox environment; consider using OpenClaw on one model/subscription (e.g., ChatGPT Codex 5.3 with prepaid credits) and connect it to remote sessions with Claude Code to combine strengths.[1]

### Practical personal workflow examples

- Managing an entire life/operations system (e.g., “RayOS” folder) through Claude Code, and now being able to manipulate that system from the phone: drafting emails, downloading files, video editing, and other tasks with the same local file access and MCP configuration.[1, {ts:569}][1, {ts:31}]
- Using Claude Code to perform about **95%** of video editing via a dedicated “video editor” skill, with manual cleanup for the remaining 5%.[1, {ts:115}][1, {ts:127}]
- Keeping Claude Code sessions running constantly (locally or on a server), and from the phone:
  - Triggering **plan mode** and MCP servers like Exa for background research while away from the computer.[1, {ts:187}][1, {ts:171}]
  - Answering plan-mode questions from the phone to continue work during breaks like lunch.[1, {ts:199}][1, {ts:212}]
- Using remote sessions to perform coding tasks, such as “make the macOS release bump up the minor version,” while away from the keyboard.[1, {ts:146}][1, {ts:136}]

***

## Operational patterns and setups

### Multi-entity flows

- **Phone → Claude app → Local Claude Code session**
  - Local machine runs `claude rc` or `claude dangerously skip permissions` in a target folder.[1, {ts:44}][1, {ts:68}]
  - User connects from the Claude mobile app (Code tab) to that specific session and sends commands (e.g., find files, run skills, edit video).[1, {ts:106}][1, {ts:91}]
  - Claude Code executes using locally configured skills, MCP servers, and file mappings.[1, {ts:171}][1, {ts:115}]
- **Phone → Claude app → Remote server (tmux) → Claude Code**
  - Remote server (Hetzner) runs tmux with a persistent `claude` session with `/remote-control` enabled.[1, {ts:310}][1, {ts:324}]
  - Claude app links to this session; user issues commands like online research or report generation.[1, {ts:339}]
  - MCP servers are installed on the remote machine, enabling continuous tasks and reports while isolating risk away from the local machine.[1, {ts:352}][1, {ts:339}]
- **Sandbox folder → settings.local → Claude Code remote control**
  - A dedicated project folder contains `settings.local.json` that enables sandboxing and configures allowed hosts and denied tools.[1, {ts:365}][1, {ts:378}]
  - Starting `claude rc` in that folder yields a sandboxed session accessible via remote control; user issues research prompts from the phone, receiving summaries on allowed hosts only.[1, {ts:404}][1, {ts:390}]
- **Proxy → Claude Code → External Internet**
  - Claude Code network traffic is routed through an HTTP proxy defined in settings; the proxy script enforces domain-level allow/deny rules.[1, {ts:456}][1, {ts:441}]
  - WebFetch and WebSearch are disabled in config, so network usage must go through `curl` or similar tools, which are themselves constrained by the proxy.[1, {ts:428}][1, {ts:441}]
- **Third-party orchestrator (OpenClaw) → agents → Claude Code (comment)**  
  - A commenter describes a setup where OpenClaw is given access to an “agent 0” and both run in a sandboxed environment; this orchestrator could, in theory, still be used while also running remote Claude Code sessions, potentially combining different subscriptions and models.[1]

### Automation patterns

- **Persistent sessions via tmux**
  - On remote servers, tmux keeps Claude Code running after SSH disconnect; remote control sessions remain available to phone and web clients.[1, {ts:324}][1, {ts:310}]
- **Background research agent**
  - On a remote server with MCP servers configured, Claude Code can perform ongoing research, generate reports, and handle web tasks without requiring your local machine to stay on.[1, {ts:339}][1, {ts:352}]
- **Plan mode from phone**
  - Using `/plan` (plan mode) with MCP servers like Exa, the user can initiate a planning workflow from the terminal and then answer interactive questions from the phone, effectively continuing planning work while mobile.[1, {ts:187}][1, {ts:199}][1, {ts:171}]
- **Potential future automated hooks**
  - Suggested but not yet implemented: hooks tied to notifications or scheduled tasks similar to OpenClaw, including:
    - Cron-like triggers to start tasks automatically.
    - Hooks that send notifications from Claude Code directly to the phone rather than only to the desktop (currently, desktop notifications can be built with AppleScript).[1, {ts:531}][1, {ts:519}]

### Guardrail artifacts

- **`settings.local.json` (sandbox guardrail config)**
  - Encodes rules such as:
    - `sandbox.enabled: true`.[1, {ts:378}]
    - `permissions.defaultMode: "don't ask"` for allowed operations.[1, {ts:378}]
    - Explicit lists of allowed websites for research, blocked editing/writing tools, and disabled bash tools.[1, {ts:390}][1, {ts:378}]
  - Practically enforced by:
    - Claude Code refusing WebFetch requests to disallowed hosts (e.g., blocking `masterclaudecode.com`).[1, {ts:416}][1, {ts:404}]
    - No bash access, so the model can’t circumvent the block by invoking `curl`.[1, {ts:416}][1, {ts:428}]
- **Proxy script (`proxy.js`) and network policy**
  - Acts as a network guardrail:
    - Allows traffic only to whitelisted domains such as `api.anthropic.com` and specific research sites.[1, {ts:456}][1, {ts:441}]
    - Logs and blocks HTTP GET requests to any other domain.[1, {ts:472}][1, {ts:441}]
  - Enforced in practice because Claude Code’s network access flows through this proxy when configured, and WebFetch/WebSearch are disabled to prevent bypass.[1, {ts:428}][1, {ts:441}]
- **Server-level isolation**
  - Using a cheap remote server (e.g., Hetzner) as an execution environment is itself a guardrail: any prompt-induced harmful actions are contained to that server’s filesystem and network environment.[1, {ts:280}][1, {ts:352}]
- **Permission modes**
  - Choosing between standard permissions (with prompts) and `dangerously skip permissions` acts as a policy decision:
    - For local machines, avoid permanently using dangerously skip permissions due to higher risk, especially with internet access.[1, {ts:221}]
    - For remote, isolated servers, dangerously skip permissions can be acceptable, especially when combined with sandboxing and proxies.[1, {ts:495}][1, {ts:258}]

***

## Practical recommendations

- **Set up a persistent remote Claude Code server**
  - Provision a low-cost VM (e.g., Hetzner 3.49 €/month) named for Claude Code.[1, {ts:280}]
  - Install Claude Code, fix shell issues if prompted, sign in with your Anthropic subscription.[1, {ts:297}][1, {ts:310}]
  - Run `tmux`, start `claude`, enable `/remote-control`, then detach, so the session is always available to your phone.[1, {ts:310}][1, {ts:324}]
- **Use a three-tier model: local, remote, sandbox**
  - Local machine: run `claude rc` in key folders (e.g., “RayOS”), avoiding dangerously skip permissions by default and approving sensitive actions from phone or desktop.[1, {ts:31}][1, {ts:221}]
  - Remote server: allow `claude rc dangerously skip permissions` for heavy automation and research, but combine with strict sandbox and proxy rules.[1, {ts:258}][1, {ts:495}]
  - Sandbox folders: create dedicated research directories with `settings.local.json` limiting hosts and tools.[1, {ts:365}][1, {ts:378}]
- **Add hooks/rules for high-risk operations**
  - Treat filesystem modifications and shell access as high-risk:
    - Disable bash tools and editing/writing tools in sandbox configs where you only need read-only research.[1, {ts:390}][1, {ts:378}]
    - Reserve dangerously skip permissions only for isolated remote environments or strongly proxied sandboxes.[1, {ts:495}][1, {ts:221}]
  - Block web access by default, then explicitly whitelist only required sites via `settings.local.json` and proxy rules.[1, {ts:441}][1, {ts:378}]
- **Centralize guardrail logic**
  - Use `settings.local.json` as a **local guardrail doc** per environment, encoding:
    - What tools are allowed.
    - Which sites can be fetched.
    - Default permission behavior.[1, {ts:378}]
  - Reference this file in every workflow by always launching `claude rc` from the correct folder so you automatically inherit the right guardrails.[1, {ts:365}][1, {ts:390}]
- **Optimize remote work patterns**
  - Keep critical Claude Code sessions (e.g., for your “life OS” folder, video editing, or ongoing research) running and remote-controllable; from your phone you can:
    - Trigger plan mode and answer prompts during downtime.[1, {ts:199}][1, {ts:171}]
    - Kick off long-running tasks (video editing, research reports) while away.[1, {ts:115}][1, {ts:339}]
  - Where you previously used tmux + Tailscale + mobile terminals, consider migrating to the built-in remote control for simpler permission approval and tighter integration with your existing Claude Code skills and MCP setup.[1, {ts:158}][1, {ts:20}]
