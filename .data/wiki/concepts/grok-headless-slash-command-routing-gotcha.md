---
title: "Grok Build headless mode treats slash commands as prompts, not TUI commands"
created: 2026-08-06
source: session-20260806
tags: [grok-build, headless-mode, slash-commands, gotcha, cli-behavior, routing]
summary: >
  When using `grok --single "/usage"` (headless mode), slash commands are
  sent to the model as prompts rather than executed as native TUI commands.
  The model interprets the command and may route to a matching skill instead
  of the intended native function. This makes scripting TUI slash commands
  from headless mode unreliable — the `--verbatim` flag may help but is
  unverified for this use case.
agent: grok
host: grok
cognitive_load: 2
verification: empirically-tested
sources:
  - https://docs.x.ai/developers/rate-limits (xAI, accessed 2026-08-06)
relations:
  - target: wiki/concepts/grok-build-grpc-web-billing-endpoint.md
    type: complements
  - target: wiki/concepts/provider-quota-usage-api-reference.md
    type: extends
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: related
---

# Grok Build headless mode treats slash commands as prompts

## Decision context

The operator asked whether `grok --single "/usage"` could be used to
programmatically query Grok Build's weekly quota from a script (e.g., from
`fleet_quota.py`). Initial research incorrectly concluded that `/usage`
was "not script-callable." The operator pushed back: why not use headless
mode? Testing revealed that headless mode does accept the command, but it
doesn't execute it the way the interactive TUI does.

## The finding

**[FACT]** In interactive mode, `/usage` is intercepted by the TUI before
reaching the model — it executes the native billing display.

**[FACT]** In headless mode (`grok --single` / `--prompt-json` / `--prompt-file`),
the input is sent to the model as a prompt. The model then interprets
`/usage` as a user request and routes to whatever skill it finds matching.

**[FACT]** When tested with `grok --single "/usage" --output-format json`,
the model found the GLM Coding Plan `usage-query` skill in the session
catalog and ran that instead — returning GLM quota data, not Grok weekly
quota. This happened with both the default model (GLM-5.2) and
`--model grok-4.5`.

The `--verbatim` flag ("send the prompt exactly as given") exists and may
prevent model interpretation, but this is **[UNTESTED]** for slash-command
invocation.

## Why this matters

This affects any attempt to script Grok Build's interactive slash commands
from CI, cron, or other scripts. The commands look scriptable (they accept
JSON output format, work non-interactively), but they route through the
model's skill-matching logic rather than the TUI's command dispatcher.

For quota specifically, the workaround was to bypass `/usage` entirely and
query the gRPC-web billing endpoint directly (see
[[grok-build-grpc-web-billing-endpoint]]). But the broader pattern affects
all TUI slash commands in headless mode — `/status`, `/privacy`,
`/settings`, etc. This complements [[provider-quota-usage-api-reference]]
which documents the programmatic quota query paths but didn't cover the
headless-mode scripting gotcha.

## What this means for our workspace

- **Don't script TUI slash commands via `grok --single`.** The model
  interprets them, which produces unreliable routing.
- **For quota queries:** use the direct gRPC-web endpoint approach in
  `check_grok()`, not `grok --single "/usage"`.
- **For other TUI commands:** investigate whether they have a direct CLI
  subcommand equivalent (e.g., `grok doctor`, `grok models`) before
  attempting to script them via headless mode. The
  [[execution-path-based-model-routing-grok-build]] concept covers the
  routing architecture but doesn't address the headless-mode command
  dispatch difference.
- **The `--verbatim` flag** deserves testing — it may bypass model
  interpretation and enable native command execution. Unverified.

## Falsifier

This finding is wrong if:
1. A future Grok Build update intercepts slash commands in headless mode
   before sending them to the model (then headless `/usage` would work)
2. The `--verbatim` flag is confirmed to execute native commands (then the
   pattern is `grok --single --verbatim "/usage"`)
3. xAI exposes a direct CLI subcommand for usage (e.g., `grok usage`)

## Sources

- [xAI FAQ: Usage & Limits](https://docs.x.ai/grok/faq) (xAI, accessed 2026-08-06) — documents the `/usage` slash command for interactive use
- [Grok Build headless mode docs](~/.grok/docs/user-guide/14-headless-mode.md) — documents `--single` flag behavior

## Receipts

- **Live test:** `grok --single "/usage" --model grok-4.5 --output-format json` — session 019fd698, 2026-08-06. Response routed to GLM `usage-query` skill, returned GLM quota data. Model thinking: "The user is asking for `/usage`. Looking at the available skills..."
- **`/usage` docs:** `~/.grok/docs/user-guide/04-slash-commands.md:404-410` — "View credit usage or manage billing"
- **`--single` docs:** `~/.grok/docs/user-guide/14-headless-mode.md:9` — "Passing a prompt non-interactively triggers headless mode"

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[model-tool-calling-capability-matrix]]
- [[grok-build-workflows-rhai-orchestration]]
- [[quantization-and-memory-optimization-for-local-ai-models]]

