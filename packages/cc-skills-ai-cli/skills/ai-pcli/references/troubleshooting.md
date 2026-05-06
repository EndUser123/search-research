# Troubleshooting — /ai-pcli Common Issues

## Empty Output Sections

**Symptom:** All 8 model sections appear but content is blank.
**Cause:** stderr from pi CLI contains "Warning: No models match pattern..." which was incorrectly treated as an error, clearing the output buffer.
**Fix:** The `Warning:` sentinel was added to the PTY noise filter in `parallel_llm.py`. Update to the latest skill version.

## Config Not Found

**Symptom:** `/ai-pcli config` shows "No saved configuration found"
**Cause:** Config file is at `P:/.data/ai-pcli-recipe.json`. Falls back to `ai-cli-recipe.json` if primary missing.
**Fix:** Run `/ai-pcli config save` (or the save workflow in your setup) to populate the config file.

## Timeout Errors

**Symptom:** Command times out before models return output.
**Cause:** Context file is large. Default is 180s base + 1s per MB.
**Fix:** Use `--timeout N` to increase. E.g., `--timeout 600` for a 10MB context.

## Model Not Found (pi)

**Symptom:** pi CLI reports "No models match pattern"
**Cause:** Model name may need resolution. Check alias mapping in `ai_cli.py` `_resolve_model_alias()`.
**Fix:** Use `--pi-model <model>` with exact model name from `pi --list-models`.

## All CLIs Fail

**Symptom:** Every model reports failure.
**Cause:** Network issue, API credentials expired, or rate limiting.
**Fix:** Check individual CLI health (`gemini-cli --version`, `codex --version`, etc.) and verify API keys are set.

## Partial Failures (Expected Behavior)

**Symptom:** Some CLIs succeed, others fail.
**This is normal.** Individual failures don't abort others. The aggregated output shows which CLIs succeeded/failed.

## File Context Not Loaded

**Symptom:** CLIs respond without referencing the file content.
**Cause:** Used piped stdin instead of `--context FILE`.
**Fix:** Always use `--context P:\path\to\file.ext` — piped stdin is ignored when auto-context is detected.