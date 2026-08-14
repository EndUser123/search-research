---
title: "using codex cli, how do we get json output from a non-interactive prompt?"
date: "2026-01-20"
mode: "COPILOT"
uuid: "74cf637e-06c6-47e8-bd30-64d6ad1d71ff"
entry_count: 2
---

## Human

using codex cli, how do we get json output from a non-interactive prompt?

## Assistant

**Use `codex exec` for non-interactive prompts in Codex CLI.** The `--json` flag outputs a JSON Lines (JSONL) stream of events to stdout, while `--output-schema` enforces structured JSON for the final response.[1][2]

## Basic JSON Output
Run `codex exec --json "your prompt here"` to stream events like thread starts, agent messages, and completions as newline-delimited JSON objects. Progress shows on stderr by default. Pipe to tools like `jq` for parsing: `codex exec --json "summarize repo" | jq`. [1][1]

## Structured JSON Response
Define a JSON Schema file (e.g., schema.json) and use `--output-schema ./schema.json -o output.json "extract metadata"`. Codex validates and writes the conforming final response to the file and stdout. This ensures parseable output matching your schema.[2][1]

## Key Flags
- `--json` or `--experimental-json`: JSONL event stream (instead of formatted text).[2]
- `--output-last-message -o path`: Saves final message (text or structured).[2]
- Combine with `--full-auto` for automation without approvals.[1]

## Human

does that flag actually exist?  Do you have any examples?

## Assistant

I apologize for the earlier response—I overstated the feature parity. The `--json` flag **does exist** in the official Codex CLI reference, but looking at the actual documentation and GitHub discussion, the implementation and behavior differ from what I initially suggested.

**Yes, `--json` exists:** Use it with `codex exec` to output newline-delimited JSON events instead of formatted text. The documentation lists it as:[1]

```
--json, --experimental-json (boolean)
Print newline-delimited JSON events instead of formatted text.
```

**Real-world usage:** From GitHub issues, users have confirmed `--json` produces an event stream of JSON objects. There's also a newer `--experimental-json` flag mentioned as coming to replace `--json`.[2][3]

**Combined with output options:** For non-interactive use, pair `--json` with `--output-last-message -o <path>` to capture the final response, and optionally `--output-schema <path>` to enforce structured JSON validation against a schema file.[1]

**Basic example:**
```bash
codex exec --json --output-last-message output.json "your prompt here"
```

**However, caveats exist:** The feature request on GitHub shows users want better control over where the JSON gets written and how the complete trajectory is serialized—currently logs go to `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl`. There's ongoing discussion about a `--json-log` flag for more explicit control, but that appears to still be proposed rather than implemented.[2]

So: the `--json` flag is real and documented, but the structured output story is still evolving. For your automation use case, `codex exec --json` streams events to stdout while `--output-last-message` captures the final state to a file.
