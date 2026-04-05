# Vague Directive Gate - Settings.json Patch

## Add to PreToolUse section in P:\.claude\settings.json

Find this block (after session_reversion_check):
```json
      {
        "matcher": "^(Write|Edit|MultiEdit)$",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/session_reversion_check.py",
            ...
          }
        ]
      },
```

Add this immediately after:
```json
      {
        "matcher": "^(Write|Edit|MultiEdit)$",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/PreToolUse_vague_directive_gate.py",
            "timeout": 2,
            "layer": "0b_vague_directive",
            "critical": true,
            "description": "Layer 0b: BLOCK vague directives - require architecture review first (Part D)"
          }
        ]
      },
```

## Add to hook_architecture_v2.layers section

Add this new layer definition:
```json
      "0b_vague_directive": {
        "purpose": "Block vague directives that need architecture review",
        "strategy": "Detect comparative/abstract words without specific target, block and request /arch",
        "always_active": true,
        "tokens": 0,
        "version": "1.0.0",
        "rationale": "Vague directives like 'make it better' need scope definition before execution"
      },
```

## Add environment variable (optional)

In the "env" section, add:
```json
    "VAGUE_DIRECTIVE_GATE_ENABLED": "true",
```
