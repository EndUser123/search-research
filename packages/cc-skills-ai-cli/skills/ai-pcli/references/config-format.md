# Config Format — /ai-pcli Recipe File

Config file: `P:/.data/ai-pcli-recipe.json` (falls back to `P:/.data/ai-cli-recipe.json`)

## Full Structure

```json
{
  "default": { "clis": [...] },
  "aux": { "clis": [...] },
  "clis": [...],
  "opencode_models": [...]
}
```

## Groups

### `default.clis` — Primary CLI invocations

Run unconditionally. Each entry is a CLI identifier string:

```json
"default": { "clis": [
  { "name": "pi:kimi-k2.6" },
  { "name": "pi:devstral-2512" },
  { "name": "gemini" }
]}
```

Valid prefixes: `pi:` (pi CLI), bare `gemini`/`codex`/`opencode` (native CLI).

### `aux.clis` — Model-annotated CLIs

For CLIs with per-model selection. Currently used for `opencode`:

```json
"aux": { "clis": [
  { "name": "opencode", "model": "kimi", "failover": "minimax" }
]}
```

Fields:
- `name` — CLI name (must be `opencode` for aux entries)
- `model` — primary model alias
- `failover` — fallback model alias

### `default.clis[n].tags` — Model strength hints

Optional tags that describe model strengths for quality scoring:

```json
{ "name": "pi:kimi-k2.6", "tags": ["analytical", "concise"] }
{ "name": "pi:devstral-2512", "tags": ["creative", "thorough"] }
{ "name": "gemini", "tags": ["code", "architecture"] }
```

Available tags (case-insensitive):
- `analytical` — Structured, evidence-based reasoning
- `concise` — Short, focused responses
- `creative` — Novel approaches, brainstorming
- `thorough` — Detailed, comprehensive analysis
- `code` — Code generation and review expertise
- `architecture` — System design and architecture
- `documentation` — Doc writing and explanation
- `debug` — Debugging and troubleshooting
- `planning` — Planning and strategy

Tags are used for task-type-aware quality weighting (improvement #2).

### Legacy flat format

Old config files use `clis` (string list) and `opencode_models` (string list). These are still read and flattened into `default`/`aux` for display compatibility.

## Saving Config

`/ai-pcli config save <args>` (if implemented) writes the structured format. Direct file editing also works — the format is self-explanatory.

## Display Mapping

```
default.clis[n].name  →  Default: <name>
aux.clis[n]           →  Aux / Enh: <name> (<model>, failover to <failover>)
```