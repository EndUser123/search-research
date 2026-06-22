---
name: council-decide
description: Single-model fallback execution
version: 1.0.0
---

# /council-decide - Single-Model Fallback

Execute single-model execution bypassing council deliberation.

## Usage

```
/council-decide <prompt>
```

## Behavior

- Bypasses council entirely
- Uses first available model
- Useful for quick answers or when council is unavailable

## Examples

```
/council-decide What is 2+2?
```

## Output

Direct model response without council metadata.