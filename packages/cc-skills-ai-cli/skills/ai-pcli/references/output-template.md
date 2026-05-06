# Output Template — /ai-pcli Config Display Format

## Config Query Output

When running `/ai-pcli config`, the output follows this structure:

```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```

## Example Output

```
Active CLIs:
  Default:
    pi:ling-2.6-1t-free
    pi:kimi-k2.6
    pi:devstral-2512
  Aux / Enh:
    opencode (kimi, failover to minimax)
```

## Config Source

The config is loaded from `P:/.data/ai-pcli-recipe.json` with automatic fallback to `P:/.data/ai-cli-recipe.json` if the primary path does not exist.

## If No Config Exists

```
No saved configuration found
```

## Format Notes

- **Default CLIs**: Standalone CLI invocations (pi:, gemini, codex, etc.)
- **Aux / Enh CLIs**: Model-annotated entries (opencode with model selection and failovers)
- Empty sections are omitted from display