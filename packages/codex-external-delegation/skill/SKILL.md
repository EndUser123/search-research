---
name: external-delegation
description: Delegate bounded low-ambiguity work to OpenCode using subscription-backed or local models, with generated packets, timeouts, artifacts, and parent verification. PI remains available only through a separate explicit invocation. Use when Codex should conserve OpenAI usage or use MiniMax, Zai, OpenCode/Zen, or llama.cpp for mechanical work.
---

# External Delegation

Codex remains the parent and owns task classification, scope, risk decisions, integration, and final judgment. Use the bridge for low-ambiguity work such as read-only exploration, extraction, classification, test execution, documentation drafts, or a tightly specified mechanical change.

Do not delegate ambiguous diagnosis, architecture, security decisions, final review, destructive actions, external mutations, or work whose result cannot be independently verified.

## Default workflow

1. Decide whether this is bounded execution or parent-owned reasoning.
2. If bounded, create a packet JSON in the current task's state directory. Do not ask the user to write the packet.
3. Default to `mode: "read_only"`, `worker: "opencode"`, an explicitly selected OpenCode model, and `thinking: "off"` where supported.
4. Include explicit `allowed_paths`, `forbidden_actions`, `output_schema.required`, and exact `verification.commands`.
5. Do not add fallback workers. If OpenCode fails, halt and return its failure evidence. PI requires a new explicit invocation with a new task ID and packet.
6. Run `node P:\packages\codex-external-delegation\bin\external-delegation.mjs run --packet <packet-path>`.
7. Inspect the normalized JSON result and raw artifacts under `.codex/state/external-delegation/<task_id>/`.
8. Independently inspect changed files and rerun verification before accepting any result.

## Safety contract

- A worker is not successful unless it returns the required structured result marker.
- Timeouts, provider failures, quota/auth failures, context overflow, missing commands, malformed output, and worker errors are distinct failure classes.
- Only read-only infrastructure failures may retry, and only once through an explicit fallback.
- Write packets require both `write_scope` and `isolated_cwd`; otherwise the bridge blocks before spawning a worker.
- Never expose API keys or auth files in a packet, prompt, artifact, or final response.

## Packet shape

```json
{
  "schema_version": "1",
  "task_id": "unique-task-id",
  "worker": "opencode",
  "model": "opencode-go/deepseek-v4-flash",
  "objective": "List all callers of the parser and return file paths with line numbers.",
  "cwd": "P:/repo",
  "mode": "read_only",
  "allowed_paths": ["src/", "tests/"],
  "forbidden_actions": ["edit files", "run network commands"],
  "output_schema": { "required": ["files", "observations"] },
  "verification": { "commands": ["rg -n parser src tests"] }
}
```

The parent must treat the worker response as candidate evidence, not truth.
