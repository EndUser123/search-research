# prompt-enhancer

## Purpose

Manual slash-command invocation of the prompt enhancement engine. Provides interactive prompt clarification when invoked directly.

## Usage

```
/prompt-enhancer fix it
/prompt-enhancer delete the database
/prompt-enhancer make this better
```

## How it works

Delegates to `prompt_enhancer.enhance()` with the provided prompt argument. The callable module performs ambiguity triage and returns an `EnhancementResult`. When invoked via slash command, the skill prints the `additionalContext` string to stdout so it appears in the transcript.

For automatic hook-based enhancement, the `prompt_enhancer_hook.py` hook (registered in `settings.json`) handles all incoming prompts.
