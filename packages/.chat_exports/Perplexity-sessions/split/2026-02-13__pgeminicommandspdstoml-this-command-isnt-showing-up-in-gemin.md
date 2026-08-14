---
title: "P:\\.gemini\\commands\\pds.toml, this command isn't showing up in gemini cli.  what am i doing wrong?"
date: "2026-02-13"
mode: "COPILOT"
uuid: "b99c98a7-f06b-4da9-b641-832cc489a7f1"
entry_count: 1
---

## Human

P:\\.gemini\\commands\\pds.toml, this command isn't showing up in gemini cli.  what am i doing wrong?

## Assistant

On Windows, Gemini CLI only loads custom commands from a very specific `.gemini\commands` directory and the command name comes from the file path, so a small mismatch in location or naming will make it disappear.[1][2][3]

## Things to check

1. **Correct directory (user‑ vs project‑scoped)**  
   - User‑scoped: `C:\Users\<You>\.gemini\commands\pds.toml`.[4][1]
   - Project‑scoped: `<your project>\.gemini\commands\pds.toml` (relative to the directory where you run `gemini`).[1]
   Your path `P:\.gemini\commands\pds.toml` will **only** be seen if you are running `gemini` from `P:\` (or a subdirectory) and that `.gemini` is your project‑level config.[3][1]

2. **How the command is named**  
   - The slash command name is derived from the file’s relative path inside `commands`.  
   - For `...\.gemini\commands\pds.toml`, the command should appear as `/pds` in the CLI.[2][5][3]

3. **Minimal TOML schema**  
   - Your file must at least define:  
     ```toml
     description = "Smart Engineering Mega-Skill - Unified orchestrator for native /arch, /tdd, and /rca skills"
     prompt = "You are the Smart PDS Orchestrator. You have been activated to handle: {{args}}. Follow the gemini-pds skill rules."
     ```  
   - `description` and `prompt` are valid fields; this is enough for a basic command, so the content itself looks fine.[6][5][2]

4. **Restart and environment**  
   - Fully close and reopen the Gemini CLI session after creating the file so it rescans commands.[7][8]
   - If you changed the config directory via `GEMINI_CONFIG_DIR` or similar, make sure `.gemini\commands` lives under that directory instead of your home drive.[4]

5. **Version / install quirk**  
   - Some older `npm -g @google/gemini-cli` builds had issues loading custom commands; building from the repo or updating to the latest version fixes it.[8][7]

## Quick sanity checklist for your setup

- If you want `/pds` available **everywhere**: move `pds.toml` to `C:\Users\<You>\.gemini\commands\pds.toml`, then restart CLI and try `/pds`.[5][1][4]
- If you want it only for a given project on `P:\`: ensure your shell’s current directory is that project (e.g. `P:\myproj`), and that `P:\myproj\.gemini\commands\pds.toml` exists, then restart and try `/pds`.[3][1]

If you paste your exact working directory when you run `gemini` plus where `.gemini\commands\pds.toml` sits relative to that, I can pinpoint the exact mismatch.
