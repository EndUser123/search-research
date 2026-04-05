# ai-cli Output Template

## Config Query Output

When user queries "config", display saved configuration **directly to stdout** in tree format using box-drawing characters:

```
Active CLIs:
  Default:
    <cli>
    <cli>
      └── <model>
      └── <failover>
    ...
  Aux / Enh:
    <cli>
      ├── <model>
      │   ├── <failover1>
      │   └── <failover2>
    ...

Or if no saved config:
```
No saved configuration found
```

**Rules:**
- Use box-drawing characters: `├──`, `└──`, `│`
- CLI names at top level
- Models are children of CLI (indented with `│   `)
- Failover options are nested under model (indented with `│   │   `)
- Position-based connectors: `├──` for non-last, `└──` for last
- Single-child items that are last in group: no continuation bar
- 4-space indent for tree levels
- No labels like "[Config]"
- No surrounding boxes or borders
- No mixed stderr/stdout
