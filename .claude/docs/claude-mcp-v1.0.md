# Claude Code MCP Guide

**v1.0 | April 2026 | Reference**

---

## CHANGELOG

| Aspect | Notes |
|--------|-------|
| v1.0 (Apr 2026) | Initial release — mirrors structure of claude-agents-v1.0.md for parity |
| MCP server growth | 100 → 5,000+ servers (Nov 2024 → Oct 2025, 50x) |
| Downloads growth | 100k → 8 million in same period |
| Remote MCP servers | 4x growth since May 2025 (enterprise signal) |
| Skills + MCP ecosystem | Document automation, TDD workflows, real-time revenue data integration |
| v1.1 additions | MCP server reliability/error handling, skill composition/chaining, local-first patterns, testing/debugging, when not to use MCP, cross-reference to claude-agents-v1.0.md |

---

## TABLE OF CONTENTS

1. [Core MCP Concepts](#core-mcp-concepts)
2. [MCP Server Architecture](#mcp-server-architecture)
3. [Skills as the Integration Layer](#skills-as-the-integration-layer)
4. [Plugin Structure with MCP](#plugin-structure-with-mcp)
5. [MCP Server Discovery](#mcp-server-discovery)
6. [Authentication & Security](#authentication--security)
7. [MCP Server Reliability & Error Handling](#mcp-server-reliability--error-handling)
8. [Skill Composition & Chaining](#skill-composition--chaining)
9. [Local-First & Solo Dev Patterns](#local-first--solo-dev-patterns)
10. [Best Practices](#best-practices)
11. [Anti-Patterns](#anti-patterns)
12. [Pattern Catalog](#pattern-catalog)
13. [Skill + MCP Integration Workflow](#skill--mcp-integration-workflow)
14. [Top MCP Servers by ROI](#top-mcp-servers-by-roi)
15. [Testing & Debugging](#testing--debugging)
16. [When Not to Use MCP](#when-not-to-use-mcp)
17. [Cross-Reference: claude-agents-v1.0.md](#cross-reference-claude-agents-v10md)
18. [Sources](#sources)

---

## CORE MCP CONCEPTS

The Model Context Protocol (MCP) is Anthropic's standard for connecting Claude to external data sources and tools. Unlike REST APIs that require custom code per integration, MCP exposes a standardized interface that Claude understands natively.

### What MCP provides

| Capability | Description |
|-----------|-------------|
| **Tool exposure** | External APIs become native Claude tools |
| **Resource access** | Databases, files, APIs exposed as structured resources |
| **Standardized interface** | One protocol, many servers — no custom code per integration |
| **Protocol abstraction** | When backend APIs change, the MCP interface stays valid |
| **Vendor-backed servers** | GitHub, Stripe, Salesforce, Figma invest in remote servers — enterprise demand proven |

### MCP vs REST API

| Dimension | REST API | MCP |
|-----------|----------|-----|
| **Per-integration code** | Custom code per API | Standardized interface |
| **API drift handling** | Break when APIs change | Interface stable across API versions |
| **Tool discovery** | Manual documentation | Native tool exposure to Claude |
| **Composite integrations** | Multiple REST calls, manual orchestration | Single protocol, multi-server access |
| **Setup effort** | High (per-API wrapper) | Low (one protocol, many servers) |

### MCP growth signals

- **5,000+ MCP servers** as of October 2025 (50x growth in 11 months)
- **8 million downloads** (vs 100k a year prior)
- **Remote servers up 4x** since May 2025 — companies only invest in remote infrastructure when demand is proven
- **70% of MCP consumers** have 2–7 MCP servers configured
- **180k+ monthly searches** for MCP servers collectively

---

## MCP SERVER ARCHITECTURE

### Transport types

| Transport | Use Case | Example |
|-----------|----------|---------|
| **stdio** | Local commands, CLI tools | `mcp add npx --transport stdio` |
| **SSE** | Server-sent events, local servers | `mcp add --transport sse http://localhost:3000` |
| **HTTP** | Remote vendor servers | `mcp add --transport http stripe https://mcp.stripe.com` |
| **WebSocket** | Real-time bidirectional | Real-time notifications, live data |

### Server configuration

```bash
# Add a remote MCP server
claude mcp add --transport http stripe https://mcp.stripe.com

# Add a local MCP server
claude mcp add --transport stdio my-local-server

# List configured servers
claude mcp list

# Remove a server
claude mcp remove stripe
```

### Bundled servers (plugin structure)

MCP servers can be bundled directly within a plugin using `.mcp.json`:

```json
{
  "mcpServers": [
    {
      "name": "github",
      "transport": "http",
      "url": "https://mcp.github.com"
    },
    {
      "name": "stripe",
      "transport": "http",
      "url": "https://mcp.stripe.com"
    }
  ]
}
```

When teammates clone the repo, they're prompted to install these servers automatically — no manual setup needed.

---

## SKILLS AS THE INTEGRATION LAYER

The **optimal pattern** is Skills as the orchestration wrapper with MCP as the tool backend:

```
Skill (SKILL.md) → orchestrates → MCP Server (tool backend)
```

### What each layer does

| Layer | Responsibility |
|-------|----------------|
| **Skill** | Encodes workflow, decision logic, context triggers (when to fire) |
| **MCP server** | Exposes external tools/data as structured resources Claude can call natively |

### Skills auto-fire via context triggers

The `description` field in SKILL.md frontmatter with specific context cues tells Claude when to activate:

```yaml
---
name: monthly-revenue-report
description: Generates monthly revenue report from Stripe using ARR, MRR, and churn metrics.
  Use when user asks for revenue report, monthly metrics, or mentions "Stripe data",
  "revenue numbers", or "ARR calculations".
---
```

**Trigger patterns that work:**
- Domain-specific phrases: `"Stripe data"`, `"churn analysis"`, `"pricing model"`
- Workflow context: `"automate this weekly task"`, `"build a daily digest"`
- Tool names: `"GitHub PR"`, `"Salesforce pipeline"`, `"HubSpot contacts"`

**Trigger anti-patterns — too vague:**
- `"help with data"` — fires constantly, noisy
- `"analysis"` — fires on every analytical query
- `"automation"` — too generic

### Skill → MCP binding

Skills call MCP tools by their canonical name:

```
1. Skill activates (context trigger matches)
2. Skill reads its workflow from SKILL.md
3. Skill invokes MCP tool (e.g., stripe.get_charges)
4. MCP server returns structured data
5. Skill processes and formats output
```

### The `mcp-builder` skill

The canonical skill for building MCP integrations is `mcp-builder` (from `anthropics/skills`):

- Scaffolds tool naming conventions
- Defines lifecycle management
- Handles auth scoping patterns
- Creates proper `.mcp.json` structure

```bash
# Install anthropics/skills to get mcp-builder
/plugin install example-skills@anthropic-agent-skills
```

### MCP tool description quality (high-leverage improvement)

A UCLA/NTU peer-reviewed study of 10,831 MCP servers found that **73% have repeated generic tool names** and 3,449 have wrong parameter meanings. Well-described tools achieve a **260% selection probability improvement** in multi-server scenarios.

**For skill authors building custom MCP integrations:**

| Quality dimension | Generic description | High-quality description |
|-------------------|---------------------|------------------------|
| **Tool name** | `search` | `stripe_search_customers_by_email` |
| **Parameters** | `query: string` | `query: { email: string, limit?: 1-100 }` |
| **Description** | `Search the database` | `Search Stripe customers by email address. Returns customer ID, name, email, and subscription status.` |
| **Error cases** | not documented | Documents failure modes: NO_RESULTS, RATE_LIMITED, INVALID_EMAIL |

**The result of poor descriptions:** When tool descriptions are generic, Claude may hallucinate plausible tool responses instead of reporting that a tool call failed. This is the most dangerous silent failure mode in MCP skill workflows.

### Tool poisoning and prompt injection risk

MCP tool descriptions enter the agent's context window as **trusted content**. Attackers can exploit this via:

1. **Tool poisoning** (demonstrated April 2025): Malicious MCP server publishes with misleading tool descriptions that cause the agent to take unintended actions
2. **Prompt injection via tool results**: MCP server returns crafted tool results that instruct the agent to perform attacker-chosen actions
3. **GitHub MCP prompt injection** (May 2025, 14k-star repo): Real-world exploit demonstrated on popular MCP server

**Mitigations:**

| Threat | Mitigation |
|--------|------------|
| Tool poisoning | Use only first-party servers from verified publishers. Audit third-party descriptions before use. |
| Prompt injection via results | Treat MCP tool results as untrusted input. Skills should not pass tool output directly into system prompts without sanitization. |
| Sensitive deployments | Consider a sanitizing MCP gateway proxy that audits tool descriptions and results |
| Supply chain risk | Review `.mcp.json` additions like any other dependency. Don't auto-add untrusted servers. |

**Red flag**: A newly-added MCP server that requests broad filesystem or network access but has generic or minimal tool descriptions. Legitimate servers describe their access scope clearly.

---

## PLUGIN STRUCTURE WITH MCP

A plugin that integrates MCP servers follows this structure:

```
plugin-name/
├── plugin.json              # Plugin manifest
├── .mcp.json                # MCP server definitions (auto-installed on clone)
├── skills/
│   ├── SKILL.md             # Workflow skill
│   └── references/          # Supporting docs
├── agents/                  # (optional) Subagent definitions
└── hooks/                   # (optional) Enforcement hooks
```

### plugin.json with MCP config

```json
{
  "name": "revenue-ops",
  "version": "1.0.0",
  "description": "Revenue operations integration for Stripe, Salesforce, Slack",
  "mcpServers": [
    {
      "name": "stripe",
      "transport": "http",
      "url": "https://mcp.stripe.com"
    },
    {
      "name": "salesforce",
      "transport": "http",
      "url": "https://mcp.salesforce.com"
    },
    {
      "name": "slack",
      "transport": "http",
      "url": "https://mcp.slack.com"
    }
  ],
  "skills": [
    "skills/revenue-report/SKILL.md",
    "skills/churn-detection/SKILL.md"
  ]
}
```

### Permission scoping

MCP servers should follow least-privilege scoping in `plugin.json`:

```json
{
  "permissions": {
    "mcpServers": {
      "stripe": ["read:charges", "read:subscriptions", "read:customers"],
      "github": ["read:repos", "write:issues"]
    }
  }
}
```

---

## MCP SERVER DISCOVERY

### Discovery platforms

| Platform | Count | Notes |
|---------|-------|-------|
| [MCP Market](https://mcpmarket.com) | 5,000+ servers | Searchable, categorized |
| [Awesome MCP Servers](https://mcpservers.org) | 5,000+ servers | Categorized directory |
| [SkillsMP](https://skillsmp.com) | 2,300+ skills | AI-ranked |
| [SkillHub](https://skillhub.club) | 7,000+ skills | Multi-agent compatible |
| [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) | 3.4k stars | Master directory |

### Most-searched MCP servers (highest ROI signals)

| Rank | Server | Monthly Searches | Primary Use |
|------|--------|-----------------|-------------|
| 1 | Figma MCP | 23k | Design system enforcement, component discovery |
| 2 | Playwright MCP | 35k | Browser automation, testing |
| 3 | GitHub MCP | 17k | PR review, issue triage, repo analysis |
| 4 | Stripe MCP | High | Revenue data, billing, churn |
| 5 | Salesforce MCP | High | Pipeline, deal analysis, forecasting |
| 6 | Slack MCP | High | Alerts, digests, async triggers |
| 7 | Context7 | 13k | Documentation retrieval for any tech stack |

---

## AUTHENTICATION & SECURITY

### Token management

| Auth Type | Pattern |
|-----------|--------|
| **Static token** | Environment variable (`STRIPE_API_KEY`) — set once, referenced in `.mcp.json` |
| **OAuth** | OAuth flow handled by MCP server — skill receives scoped token |
| **Token rotation** | Use secret manager (not plain text in `.mcp.json`) |

### Security principles

1. **Least privilege by default** — scope MCP server permissions to the minimum tools needed
2. **Token never in source** — use environment variables or secret manager
3. **Bundled servers require review** — servers in `.mcp.json` should be reviewed like any dependency
4. **Remote server verification** — verify server URL matches official vendor endpoint before adding

### Auth flow example (OAuth)

```
1. User runs skill that requires Salesforce MCP
2. Skill redirects to OAuth provider
3. User authenticates in browser
4. OAuth token stored locally (not in .mcp.json)
5. MCP server uses token for scoped API access
```

---

## BEST PRACTICES

1. **Wrap MCP in Skills** — raw MCP tool calls require the user to know what to ask. Skills encode the context when to ask, making the workflow discoverable.

2. **Use `mcp-builder` to scaffold** — start with the official skill for creating MCP integrations rather than hand-rolling structure.

3. **Context triggers over explicit invocation** — put specific phrases in the skill `description` so Claude auto-activates the skill without the user saying "use the X skill."

4. **Version `.mcp.json` in git** — MCP configurations belong in version control like any other config. This ensures team consistency.

5. **Bundle servers with plugins** — put MCP server definitions in the plugin's `.mcp.json` so setup is automatic on repo clone.

6. **Scope permissions tightly** — don't give an MCP server more access than the skill needs. A read-only skill shouldn't have write-capable MCP tools.

7. **Use remote servers for vendor tools** — GitHub, Stripe, Salesforce remote servers are maintained by the vendor. Prefer these over self-hosted for vendor tools.

8. **Skills should be business-logic centric, not tool-centric** — the skill encodes what to do with the data; MCP handles how to get the data.

9. **Fan-out over per-API skills** — one skill can orchestrate multiple MCP servers (Stripe + Slack for a daily revenue digest). Avoid creating a skill per MCP server.

10. **Use verification-before-completion** — apply a quality gate before shipping skill + MCP integrations (see the `superpowers` skill for this pattern).

---

## ANTI-PATTERNS

| Anti-pattern | Why it's bad | Better approach |
|-------------|--------------|-----------------|
| MCP without a skill wrapper | User must know exact MCP tool name and syntax | Wrap in a skill with context triggers |
| One MCP server per skill | Proliferates skills unnecessarily | One skill orchestrates multiple MCP servers |
| Unscoped MCP permissions | Expands attack surface | Scope to minimum required tools |
| API key in `.mcp.json` | Token visible in source, wrong repo | Environment variables or secret manager |
| No version control on `.mcp.json` | MCP config drifts across team | Git-tracked, reviewed like code |
| Skills that are just MCP proxies | No business logic encoded | Skill should have workflow beyond "call this tool" |
| Self-hosted for vendor tools | Maintenance burden vs vendor-maintained remote | Use vendor remote servers |
| Generic tool descriptions | 73% of MCP servers have this problem — causes wrong tool selection, 260% selection probability reduction | Use specific parameter shapes and action verbs: `stripe_search_customers_by_email` not `search` |
| Accepting tool output without validation | MCP tool results enter context as trusted content — prompt injection risk | Sanitize tool outputs before passing to system prompts; never echo raw tool output into code generation |
| Adding MCP servers without description audit | Tool poisoning (April 2025) and prompt injection via tool results (May 2025, 14k-star repo) are real | Review `.mcp.json` additions like dependency upgrades; reject servers with generic/misleading descriptions |

---

## PATTERN CATALOG

### Pattern 1: Revenue Report Skill

```
Trigger: "monthly revenue report" | "revenue metrics" | "ARR"
Skill: monthly-revenue-report
  → Stripe MCP (get charges, last 30 days)
  → Calculate MRR, ARR, churn rate, new vs expansion
  → xlsx skill (generate Excel)
  → Slack MCP (post summary to #revenue-ops)
```

**Outcome**: 8-hour monthly task → 15-minute automated task.

### Pattern 2: Churn Detection Skill

```
Trigger: "at-risk accounts" | "churn alert" | "flag accounts"
Skill: churn-detection
  → Salesforce MCP (pipeline data, contract dates)
  → Analytics DB MCP (product usage metrics)
  → Apply internal at-risk scoring logic
  → Slack MCP (daily prioritized alert to CSM team)
```

**Outcome**: Weekly 30-hour manual review → automated overnight daily check. Annual savings: ~$117k recovered capacity per CSM team.

### Pattern 3: Competitive Intelligence Skill

```
Trigger: "competitor analysis" | "monitor competitors" | "ad intelligence"
Skill: competitive-intel
  → Playwright MCP (scrape competitor pricing pages)
  → competitive-ads-extractor skill (VoltAgent)
  → content-research-writer skill (summarize with citations)
  → Slack MCP (daily digest to growth team)
```

**Outcome**: Weekly 5-hour task → automated daily with better coverage.

### Pattern 4: Multi-Agent MCP Orchestration

```
Lead agent:
  → Spawn teammates for parallel MCP data fetching
  → Teammate A: GitHub MCP (PR review metrics)
  → Teammate B: Stripe MCP (revenue trends)
  → Teammate C: Salesforce MCP (pipeline velocity)
  → Lead synthesizes and writes analysis
```

**Use when**: Three or more independent data streams feed a single decision.

### Pattern 5: TDD + MCP Validation

```
Skill: verification-before-completion
  → MCP tools collect runtime data
  → superpowers TDD workflow runs validation checks
  → Pass → post results via Slack MCP
  → Fail → surface issues with evidence for fix
```

**Use when**: MCP integration needs quality gate before shipping to team.

---

## SKILL + MCP INTEGRATION WORKFLOW

### Week 1: Foundation Setup

```bash
# Add core marketplaces
/plugin marketplace add anthropics/skills
/plugin marketplace add obra/superpowers-marketplace
/plugin marketplace add wong2/awesome-mcp-servers

# Install core skill bundles
/plugin install example-skills@anthropic-agent-skills
/plugin install superpowers@superpowers-marketplace

# Add MCP servers
claude mcp add --transport http stripe https://mcp.stripe.com
claude mcp add --transport http salesforce https://mcp.salesforce.com
claude mcp add --transport http slack https://mcp.slack.com
claude mcp add --transport http github https://mcp.github.com

# Verify
claude mcp list
```

### Week 2: Build First Custom Skill

```bash
# Use skill-creator (from anthropics/skills) to scaffold
# Ask: "Use skill-creator to build a skill that generates our monthly revenue report from Stripe data"

# Skill-creator guides through:
# 1. Understanding task with examples
# 2. Planning reusable components (scripts, references)
# 3. Writing SKILL.md with proper trigger phrases
# 4. Testing and iteration
```

### Week 3: Bundle with Plugin

Add to repo's `.claude/settings.json`:

```json
{
  "plugins": [
    {
      "source": "anthropics/skills",
      "plugins": ["example-skills@anthropic-agent-skills"]
    }
  ],
  "skills": [
    ".claude/skills/monthly-revenue-report",
    ".claude/skills/churn-detection"
  ]
}
```

When teammates clone, they're prompted to install all skills + MCP servers automatically.

### Week 4: Measure & Iterate

Track:
- Hours saved per skill per week
- Error rate (skills that fail vs. succeed)
- Time to build new skills (should decrease with familiarity)
- MCP server availability (vendor remote servers should be up)

---

## TOP MCP SERVERS BY ROI

### Revenue/Finance

| MCP Server | What it does | Time saved |
|-----------|-------------|-----------|
| **Stripe MCP** | Charge data, subscriptions, revenue metrics | 8 hrs/month |
| **Salesforce MCP** | Pipeline, deal analysis, forecasting | 10 hrs/week |
| **HubSpot MCP** | Contacts, deal stages, marketing attribution | 5 hrs/week |

### Development

| MCP Server | What it does | Time saved |
|-----------|-------------|-----------|
| **GitHub MCP** | PR review, issue triage, repo analysis | 3-5 hrs/week |
| **Playwright MCP** | Browser automation, testing | 4-6 hrs/week |
| **Context7** | Documentation retrieval for any tech stack | 2-3 hrs/week |

### Operations

| MCP Server | What it does | Time saved |
|-----------|-------------|-----------|
| **Slack MCP** | Alerts, digests, async notifications | 2-4 hrs/week |
| **Figma MCP** | Design system enforcement, component discovery | 3-5 hrs/week |
| **Notion MCP** | Wiki search, document retrieval | 2-3 hrs/week |

---

## MCP SERVER RELIABILITY & ERROR HANDLING

Remote vendor MCP servers go down. Skills that assume availability and don't handle errors gracefully produce worse outcomes than not using MCP at all.

### Failure modes

| Failure Mode | What happens | Impact |
|-------------|--------------|--------|
| **Remote server timeout** | Tool call hangs >30s | Skill appears stuck |
| **Server returns error** | MCP returns error object | Skill must handle gracefully |
| **Server partially available** | Some tools work, others fail | Silent partial results |
| **Auth token expired** | 401/403 on tool call | Skill fails without clear message |
| **Rate limit hit** | 429 Too Many Requests | Skill retries incorrectly or not at all |

### Retry and backoff pattern

Skills that call MCP tools should implement retry with exponential backoff:

```python
async def call_mcp_with_retry(mcp_tool, max_retries=3, base_delay=2):
    for attempt in range(max_retries):
        try:
            result = await mcp_tool()
            return result
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

### Graceful degradation

When an MCP server is unavailable, the skill should fail with a clear message — not silently skip the step:

```
❌ Silent failure: "Revenue report generated" (but Stripe data missing, report is incomplete)
✅ Graceful failure: "Revenue report failed: Stripe MCP server returned 503.
  Last successful data: 2026-04-20. Retry after vendor resolves the outage."
```

### Health check pattern

For critical workflows, check MCP server availability before executing:

```bash
# Pre-flight health check
claude mcp list | grep stripe || echo "STRIPE_MCP_DOWN"
```

### Permission error handling

When a skill encounters a permission denied error from an MCP tool:

1. Surface the error with the specific tool name and permission that was denied
2. Explain what scope is needed and how to grant it
3. Do not retry silently — the permission won't change on retry

---

## SKILL COMPOSITION & CHAINING

### Can a skill invoke another skill?

Yes. Skills can reference and delegate to other skills in the same plugin or from the skills ecosystem. The invoking skill passes context explicitly.

### Skill chain data flow

```
Skill A (orchestrator)
  → calls MCP tool (gets raw data)
  → passes structured output to Skill B
  → Skill B processes further or formats output
  → returns final result to user or upstream skill
```

**Key rule**: Each skill in the chain should be independently testable and have a clear input/output contract.

### Error propagation across skill chains

When Skill A invokes Skill B and Skill B fails:

- Skill A should capture the failure with Skill B's error message
- Skill A surfaces the failure — does not silently continue
- Skill A reports which step failed and what the inputs were

### Composite skill pattern

A composite skill bundles multiple skills under one trigger:

```yaml
---
name: daily-revenue-digest
description: Daily revenue snapshot. Use when user asks for "daily digest",
  "revenue snapshot", or "today's numbers".
---
# Delegates to:
#   - stripe-metrics (MCP call + calculation)
#   - sales-report-formatter (formatting)
#   - slack-alert (notification)
```

### Anti-pattern: skill-per-MCP-server proliferation

Creating one skill per MCP server creates navigation overhead and no composability. Instead, bundle related MCP tools under one workflow skill.

---

## LOCAL-FIRST & SOLO DEV PATTERNS

### Prioritize stdio and local SSE

For solo dev workflows, local transports are simpler and faster:

| Transport | Setup effort | Latency | Best for |
|-----------|--------------|---------|---------|
| **stdio** | Low (local CLI tool) | Near-zero | Local commands, git, npm |
| **SSE** | Medium (local server) | Low | Local databases, dev APIs |
| **HTTP** | Higher (vendor remote) | Higher | Vendor tools (Stripe, GitHub) |

**Solo dev guidance**: Start with stdio. Move to HTTP only when the MCP server is remote-only (Stripe, Salesforce, etc.).

### Token management for solo dev

For local development, environment variables in `.env` are sufficient:

```bash
# .env (not committed to git)
STRIPE_API_KEY=sk_live_xxx
SALESFORCE_TOKEN=sf_token_xxx
```

Reference in `.mcp.json` as `${env:STRIPE_API_KEY}` — never hardcode tokens.

### Local MCP server health checks

For stdio-based MCP servers, verify the command exists before running:

```bash
# Verify before building workflow
which npx && npx --yes @modelcontextprotocol/server-filesystem --version
```

### Solo dev testing without vendor APIs

Use mock MCP servers for testing without hitting real APIs:

- Stub the MCP tool response in the skill's test script
- Use `claude mcp add --transport stdio mock-server ./mock_server.py` for local mock
- Run integration tests against the mock, not the real vendor

---

## TESTING & DEBUGGING

### How to test a skill + MCP integration end-to-end

1. **Unit test the skill logic** — mock MCP tool responses, test the workflow
2. **Integration test with real MCP** — if local/stdio, test against real server
3. **End-to-end test** — run the full skill trigger and verify output

### Debugging when skill fires but MCP call fails

```bash
# Step 1: Verify MCP server is configured
claude mcp list

# Step 2: Test MCP tool directly
# Ask: "What tools does the Stripe MCP expose?"
# Then: "Call stripe.get_charges with limit=3"

# Step 3: Check skill invocation
# Add debug output in skill: echo "SKILL INVOKED with context: $CONTEXT"

# Step 4: Inspect MCP tool responses
# Run skill with verbose logging to capture MCP tool input/output
```

### Inspecting available MCP tools at runtime

```bash
# List all available MCP tools
claude mcp list

# Test a specific MCP tool directly
# (via natural language in main conversation)
"Call stripe.list_customers with limit=5"
```

### Stub MCP for local development

```json
// local-mock-stripe.json — stub for development
{
  "name": "stripe-stub",
  "transport": "stdio",
  "command": "node",
  "args": ["./mock-servers/stripe-stub.js"]
}
```

---

## WHEN NOT TO USE MCP

MCP is not always the right answer. Know when to reach for something simpler.

| Scenario | Why MCP is wrong | Better approach |
|----------|-----------------|-----------------|
| **Simple CLI command** | MCP adds protocol overhead for a one-liner | `Bash` tool directly |
| **Latency-sensitive workflow** | MCP roundtrip overhead (~50ms) matters | Direct API call |
| **One-time data fetch** | Skill + MCP is overkill | `Bash curl` or inline script |
| **Tool not available as MCP** | Can't wait for MCP server to be built | REST call via `Bash` or `httpx` |
| **Very simple API** | MCP is over-engineering | `Bash curl` or skill with direct HTTP call |

**Rule of thumb**: If the task is a one-liner that doesn't need to be repeated or shared, don't build a skill + MCP for it.

---

## CROSS-REFERENCE: CLAUDE-AGENTS-V1.0.MD

The [claude-agents-v1.0.md](claude-agents-v1.0.md) companion document covers agent patterns that complement MCP workflows.

### Where they overlap

| Topic | MCP Guide covers | Agents Guide adds |
|-------|------------------|------------------|
| Multi-agent orchestration | Pattern 4 (intro only) | Full team architecture, mailbox, task list |
| Tool restrictions | Least-privilege MCP scoping | Agent permission modes, allowlist vs sandboxing |
| Plan mode | Mentioned in workflow | Full plan mode patterns, approval criteria |
| Token budgeting | Not covered | Agent teams context window management |
| Subagent delegation | Skill-to-skill chaining | Subagent vs agent team decision tree |

### Key cross-reference rules

1. **Skill + MCP + Agent teams**: Use skill for workflow orchestration, MCP for tool backend, agent team for parallel multi-stream work
2. **MCP tool restrictions** map to agent `tools` allowlist — same principle (least privilege)
3. **Background MCP calls** align with background agent spawning — both are non-blocking

### Reading order

For a new integration project:
1. Read [claude-mcp-v1.0.md](claude-mcp-v1.0.md) to understand MCP + skill integration
2. Read [claude-agents-v1.0.md](claude-agents-v1.0.md) when scaling to multi-agent workflows
3. Reference [claude-hooks-v3.1.md](claude-hooks-v3.1.md) for enforcement hooks that validate MCP tool calls

---

## SOURCES

- [The Complete Guide to Claude Code Skills and MCP Servers](https://www.linkedin.com/pulse/complete-guide-claude-code-skills-mcp-servers-real-revenue-raza-xsl2f) — Hassan Raza, Jan 2026
- [MCP Integration Skill](https://mcpmarket.com/tools/skills/mcp-integration-1) — Tool naming, lifecycle management, OAuth patterns (46k stars)
- [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) — 3.4k stars, 5,000+ servers
- [anthropics/skills](https://github.com/anthropics/skills) — 43.5k stars, official skill library
- [VoltAgent/awesome-claude-skills](https://github.com/VoltAgent/awesome-claude-skills) — 2.5k stars, curated skill collections
- [MCP Market](https://mcpmarket.com) — Searchable server directory
- [Awesome MCP Servers](https://mcpservers.org) — Categorized MCP server directory
