---
title: "Are there fixes or workaround in claude code for this?
'
❯ /plugin install cc-skills-meta@local
  ⎿  Plugin 'cc-skills"
date: "2026-04-26"
mode: "COPILOT"
uuid: "7bfb71b7-34f5-49d4-bd43-22a72551e93a"
entry_count: 13
---

## Human

Are there fixes or workaround in claude code for this?
"
❯ /plugin install cc-skills-meta@local
  ⎿  Plugin "cc-skills-meta" not found in any marketplace

❯
  ❯ /plugin install cc-skills-meta@local
    ⎿  Plugin "cc-skills-meta" not found in any marketplace

  did you find info on the internet about this like I asked?

  Listed 1 directory, called brave (ctrl+o to expand)

● Bash(ls "C:/Users/brsth/.claude/plugins/marketplaces/local/" 2>/dev/null; echo "---"; cat
      "C:/Users/brsth/.claude/plugins/marketplaces/local/.claude-plugin/marketpla…)
  ⎿  plugins/
     ---
     ['handoff', 'cc-skills-meta', 'cc-skills-ai-api', 'cc-skills-ai-cli', 'cc-skills-media', 'cc-skills-sdlc', 'cc-skills-util
     s']

  Read 1 file (ctrl+o to expand)

● The cache marketplace.json is correct and has all 7 plugins. But /plugin install cc-skills-meta@local still fails.

  This is a known bug — Issue #14815: plugins show as "installed" in the marketplace UI but don't appear in the Installed tab, and
  installation appears to succeed silently but plugins aren't actually loaded. The marketplaces.json registry is correct, the cache
  is correct, but the plugin install system fails to find the plugin.

  The web search confirms this is a real, reported bug with no documented fix other than cache reset. Based on the docs, you should
  try:

  /plugin uninstall cc-skills-meta@local
  # then restart Claude Code and reinstall

  Or the nuclear option:
  rm -rf ~/.claude/plugins/cache/local/cc-skills-meta
  /reload-plugins
  /plugin install cc-skills-meta@local

  The web search also found Issue #11278 — Claude Code constructs wrong plugin installation paths when the marketplace.json is
  nested under .claude-plugin/. That path resolution bug could be why the local marketplace plugin isn't being found, even though
  the manifest is correct.
"

## Assistant

Yes, this is a real Claude Code bug, and there *are* a few workarounds beyond “just clear cache,” but they depend on exactly how your local marketplace is wired and which install scope Claude Code is actually using on Windows.[1][2][3]

Below I’ll outline concrete things to try, in roughly “least destructive → more nuclear,” adapted to your Windows path and the fact that `cc-skills-meta` clearly appears in the local marketplace listing but `/plugin install cc-skills-meta@local` fails.

***

## 1. Confirm which Claude Code instance is active

Several people have hit issues where a global vs project‑local Claude Code install caused plugins to be installed into one location while the *running* instance looked in another.[4][1]

On Windows, check:

1. In the terminal where you run `/plugin`:

   - Run:
     ```bash
     where claude
     claude --version
     ```
   - If you see multiple paths or unexpected locations, you likely have more than one install (e.g., npm global vs bundled vs VS Code extension host).[4]

2. In PowerShell, inspect both typical locations:

   ```powershell
   dir "$env:USERPROFILE\.claude"
   dir "$env:USERPROFILE\.local\bin"
   ```

If you find that one Claude Code instance is installed globally (npm, Homebrew, etc.) and another is bundled with a GUI, uninstall the extra one and keep a single source of truth, then reinstall plugins from that instance. This exact “plugins installed but not seen” symptom has been reported and resolved by removing the conflicting instance.[1]

***

## 2. Verify the marketplace name and source mapping

The error message:

> Plugin "cc-skills-meta" not found in any marketplace

means the *registry lookup* failed, not the on‑disk path. That usually points to how the local marketplace is registered rather than the plugin itself.

Sanity‑check:

1. Your local marketplace path is:

   ```text
   C:/Users/brsth/.claude/plugins/marketplaces/local/
   ```

   and inside you have:

   ```text
   plugins/
   .claude-plugin/
     marketplace.json
   ```

   You already listed the directory and saw `['handoff', 'cc-skills-meta', ...]`, so the cache and registry are correct.[2]

2. In `marketplace.json` (or the generated cache), confirm the marketplace id actually matches `local` and that the plugin id is `cc-skills-meta`:

   - Marketplace section should have something like:
     ```json
     {
       "id": "local",
       ...
     }
     ```
   - Plugin entry like:
     ```json
     {
       "id": "cc-skills-meta",
       "marketplaceId": "local",
       ...
     }
     ```

If the marketplace id differs (`local-dev`, `brsth-local`, etc.), then the correct install command is:

```bash
/plugin install cc-skills-meta@<that-marketplace-id>
```

and `@local` will never resolve. This sounds trivial, but it’s one of the more common “not found in any marketplace” causes in the GitHub issues for marketplace skills.[5]

***

## 3. Force Claude Code to rebuild marketplace and plugin caches

There are multiple layers of cache: marketplace registry, plugin cache, and installed_plugins. It’s possible the marketplace listing is current but the installer’s cache is stale or corrupted.[5]

Sequence (Windows, adapted from reported workarounds and docs):

1. Close all Claude Code / Claude Desktop / VS Code instances that embed Claude Code.

2. In PowerShell:

   ```powershell
   cd "$env:USERPROFILE\.claude\plugins"

   # 1) Remove plugin cache for the whole local marketplace
   rm -Recurse -Force ".\cache\local" -ErrorAction SilentlyContinue

   # 2) Optional: remove installed_plugins entry for cc-skills-meta
   rm -Recurse -Force ".\installed\cc-skills-meta" -ErrorAction SilentlyContinue

   # 3) If there is an installed_plugins.json or similar index, rename it:
   ren ".\installed\installed_plugins.json" "installed_plugins.bak" -ErrorAction SilentlyContinue
   ```

3. Restart Claude Code (from the same instance you intend to use).

4. In a fresh terminal session in Claude Code, run:

   ```bash
   /reload-plugins
   /plugin marketplaces
   ```

   Ensure `local` shows up, then:

   ```bash
   /plugin list cc-skills-meta@local
   /plugin install cc-skills-meta@local -vv
   ```

If there is any extra logging flag (`-v` or `-vv`) available in your build, use it; some builds expose more detailed errors during plugin resolution. Several users report that nuking `cache/local` plus the installed index forces Claude Code to repopulate everything correctly.[2][5]

***

## 4. Check for the path‑resolution bugs specifically

There are at least two relevant path bugs in the tracker:

- Skills from git‑installed marketplace plugins resolving to wrong paths when a local source path is used.[2]
- Plugin installation using the wrong home directory path on macOS; same underlying resolution logic can affect Windows in some builds.[3]

Both have similar traits:

- `marketplace.json` and cache are correct.
- UI shows skills or “Installed,” but:
  - Slash commands don’t appear, or
  - `/plugin` operations can’t find the plugin.

Because your screenshot shows `.claude/plugins/marketplaces/local/.claude-plugin/marketpla…`, you might be on a build where nesting under `.claude-plugin/` is confusing the resolver.

Workaround that’s been used in similar cases:

1. Flatten the marketplace structure so Claude Code doesn’t have to walk through `.claude-plugin/`:

   - Move `marketplace.json` *up* to:

     ```text
     C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json
     ```

   - Adjust any path references inside `marketplace.json` so `sourcePath` for plugins points correctly (e.g., `plugins/cc-skills-meta` instead of `.claude-plugin/plugins/cc-skills-meta`, depending on your layout).

2. Delete the `cache/local` directory again.

3. Restart and run:

   ```bash
   /reload-plugins
   /plugin marketplaces
   /plugin install cc-skills-meta@local
   ```

This is effectively working around the “nested marketplace.json under .claude-plugin” resolution bug that’s been reported on GitHub and in similar contexts.[3][2]

***

## 5. Verify you’re not in a project‑specific Claude Code context

Some setups support a project‑local Claude Code instance (e.g., inside a repo’s `.claude/` directory) plus a global one in `%USERPROFILE%\.claude`. If you’re in a project that has its own `.claude` directory, Claude Code may be looking for marketplaces relative to the project, not your home directory.

Check from within the Claude Code terminal:

```bash
pwd
ls .claude
ls ~/.claude/plugins/marketplaces
```

If there is a project `.claude/plugins/marketplaces` directory, Claude might prefer that over the one under your user profile. In that case, either:

- Move your `local` marketplace into the project `.claude/plugins/marketplaces`, or  
- Delete the project `.claude` so Claude falls back to the user‑level marketplace.[1][5]

***

## 6. Hard‑install the plugin as a last resort

If the marketplace logic is buggy but you just want `cc-skills-meta` to work, you can bypass the marketplace and drop the plugin into `installed` manually.

High‑level approach (rough because I don’t see your exact plugin layout):

1. Create an entry under:

   ```text
   C:/Users/brsth/.claude/plugins/installed/cc-skills-meta/
   ```

   containing the plugin’s manifest as if it had been installed via marketplace—use structure mirroring another working plugin’s directory from `installed/`.[5]

2. If there’s an `installed_plugins.json`, add an entry for `cc-skills-meta` that matches what marketplace install would write (look at an existing installed plugin as a template).[5]

3. Restart Claude Code and run:

   ```bash
   /reload-plugins
   /plugin list
   ```

The Skill Tool / slash commands may start seeing the skills even if `/plugin install` is still broken, which mirrors the “marketplace skills not exposed through skill tool” bug where manual edits to `installed_plugins` were a workaround.[5]

***

## 7. If nothing works: likely you’re on a broken build

Given:

- The marketplace cache shows all 7 plugins including `cc-skills-meta`.  
- `/plugin install cc-skills-meta@local` still says “not found in any marketplace.”  
- You’re on Windows with a nested `.claude-plugin` path.

This combination lines up closely with the unresolved marketplace path/lookup bugs in the public tracker where the only confirmed fixes were:

- Update to a build where the bug is patched.[3]
- Or temporarily adjust your marketplace layout (flatten `marketplace.json`, avoid `.claude-plugin` nesting) until the patch lands.[2][3]

In that case, the most pragmatic path is:

1. Flatten the marketplace structure (section 4).  
2. Ensure you have only one active Claude Code instance (section 1).  
3. Nuke caches and reinstall (section 3).  
4. If still broken, manually install into `installed/` (section 6) and treat `/plugin install` from `@local` as unreliable until a newer build.

***

Most impactful next step for you: can you paste the *actual* path to `marketplace.json` and the top‑level of its JSON (id and any `marketplaceId` fields), plus the exact output of `/plugin marketplaces` from Claude Code? That will let me narrow this down to either a naming mismatch versus a path‑resolution bug and recommend a precise file move or JSON tweak.  

## Human

"Or temporarily adjust your marketplace layout (flatten marketplace.json, avoid .claude-plugin nesting) until the patch lands."

why temporarily?

## Assistant

“Temporarily” because the nested `.claude-plugin/marketplace.json` layout is actually *supported* in the official model, and the bug is that Claude Code’s resolver is mis‑handling it in certain builds, not that your layout is “wrong.”[1][2]

### 1. What the spec says vs. the bug

- Official docs and examples show `marketplace.json` living under `.claude-plugin/` in a repo or project root, and Claude Code is supposed to handle that just fine.[3][1]
- The regression you’re bumping into is specifically that, for *local* marketplaces, some builds construct plugin install paths using the full path to `marketplace.json` instead of its directory, so nesting introduces a wrong base path.[4][2]
- Issue threads explicitly say this is a bug in path resolution, not a change in the expected layout; the fix in core is “stop using the full marketplace.json path when resolving plugins,” not “forbid nested marketplace.json.”[2][4]

So your current layout is aligned with the intended design; you’re just on a build where that design isn’t working.

### 2. Why flattening is a workaround, not a new canonical layout

Flattening `marketplace.json` up to `.../marketplaces/local/marketplace.json` or a similar simpler path:

- Avoids triggering the path‑resolution bug, because Claude Code no longer has to compute paths relative to a file nested under `.claude-plugin/`.[4][2]
- Matches what several bug reports and dev responses suggest as a short‑term unblock: simplify the local filesystem path until the resolver is patched, then go back to the “nice” structure later.[5][4]

But once the underlying bug is fixed in a newer build, you *should* be able to return to the standard `.claude-plugin/marketplace.json` layout without risking regressions, because that’s how the docs and example repos are structured.[1][3]

### 3. Why you might want to revert later

A few reasons to treat the flat layout as temporary:

- **Consistency with docs and tooling.** New tools, marketplace validators, or schema‑sync skills are written assuming the documented structure (`.claude-plugin/marketplace.json`); keeping your repo consistent with that reduces drift.[6][7][1]
- **Future automation.** If you later adopt tools that auto‑manage your marketplace (e.g., schema sync/validation), they will likely expect the standard layout and may look for `.claude-plugin/marketplace.json` by default.[7]
- **Risk of new bugs.** Some of the later issues in the tracker show *different* bugs when people depart too far from the standard layout or combine project and user‑scoped marketplaces in odd ways; best long‑term posture is “match the official pattern as soon as the resolver bug is fixed.”[8][9][5]

So flattening is basically: “hack around a known path bug in *this* build,” not “you should permanently remodel your marketplace like this.”

***

If you’d like, I can suggest a specific layout that keeps your repo in the “official” shape but still works with your current broken build (e.g., moving only the user‑scope marketplace while keeping project‑scope as documented).

## Human

"
❯ Yes, that would be simpler, but it means we're fucked until then. So how about you try the flattened layout?

● Bash(cp "C:/Users/brsth/.claude/plugins/marketplaces/local/.claude-plugin/marketplace.json" "/tmp/marketplace_backup.json" && echo
       "Backup done")
  ⎿  Backup done

● Bash(cp "/tmp/marketplace_backup.json" "C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json" && python3 -c "
      import json…)
  ⎿  Flattened. New sources: ['plugins/handoff', 'plugins/cc-skills-meta', 'plugins/cc-skills-ai-api', 'plugins/cc-skills-ai-cl
     i', 'plugins/cc-skills-media', 'plugins/cc-skills-sdlc', 'plugins/cc-skills-utils']

● Bash(cp "/tmp/marketplace_backup.json" "P:/packages/.claude-marketplace/marketplace.json" && python3 -c "
      import json…)
  ⎿  Canonical source updated
     From file:///P:/packages/.claude-marketplace
        56a09f8..ec13f2f  main       -> origin/main
     … +3 lines (ctrl+o to expand)
  ⎿  Shell cwd was reset to P:\\

● Bash(ls "C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json" 2>/dev/null && echo "--- flat exists ---" && python3
      -c "import json; d=json.load(open('…)
  ⎿  C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json
     --- flat exists ---
     sources: ['plugins/handoff', 'plugins/cc-skills-meta', 'plugins/cc-skills-ai-api', 'plugins/cc-skills-ai-cli', 'plugins/cc
     -skills-media', 'plugins/cc-skills-sdlc', 'plugins/cc-skills-utils']

● Flattened marketplace.json is in place. Try /plugin install cc-skills-meta@local now.

✻ Churned for 1m 43s

❯ /plugin install cc-skills-meta@local
  ⎿  Plugin "cc-skills-meta" not found in any marketplace"

## Assistant

So flattening the marketplace layout did *not* fix it, which is a strong signal this is not just the `.claude-plugin` nesting bug but a deeper “this marketplace isn’t actually registered the way we think it is” problem.[1][2][3]

Given what you’ve already done, I’d focus on three angles:

1. **Prove Claude actually sees this as the `local` marketplace**  
2. **Check whether you accidentally have *two* “local” marketspaces with different sources**  
3. **Bypass `/plugin install` entirely and just force‑install cc-skills-meta**

***

## 1. Confirm what Claude thinks “local” is

Right now we’re assuming `@local` resolves to `C:/Users/brsth/.claude/plugins/marketplaces/local/`, but that’s exactly what may be false.

Inside Claude Code, run:

```bash
/plugin marketplaces
```

You should see an entry for `local`. For that entry, look for:

- A `source` or `url` field (e.g. `file:///...` or `github:...`)  
- Any `id` / `name` that might not be literally `local`  

If the `local` entry is actually pointing at `P:/packages/.claude-marketplace` instead of `C:/Users/...`, or vice‑versa, then:

- The marketplace Claude is using may be a *different* checkout  
- Or you may have multiple marketplaces both calling themselves “local”, and the resolver is binding `@local` to the wrong one.[4][2][3]

Also try:

```bash
/plugin marketplace show local
```

(if supported in your build) to dump the full info for that marketplace.

If `local` is not actually the one under `C:/Users/brsth/.claude/plugins/marketplaces/local/`, we should either:

- Rename the marketplace id in `marketplace.json` to something unique (e.g. `brsth-local`), then re‑add it explicitly:
  ```bash
  /plugin marketplace add file:///C:/Users/brsth/.claude/plugins/marketplaces/local
  /plugin marketplace update brsth-local
  /plugin install cc-skills-meta@brsth-local
  ```
  This mirrors how local directory marketplaces are supposed to be added.[5][3][1]

- Or remove the stale marketplace entry and re‑add it with the correct path.

***

## 2. Explicitly add the local marketplace via its file URL

Docs and tutorials: when you see “Plugin not found in any marketplace,” the fix is often “the marketplace isn’t registered or is out of date → explicitly add or update it.”[6][2][1]

Even though you *think* it’s added, let’s force it:

1. Construct a file URL for the *directory* that has `marketplace.json`:

   - On Windows, something like:
     ```text
     file:///C:/Users/brsth/.claude/plugins/marketplaces/local
     ```
     (Three slashes, forward slashes, no trailing slash.)

2. In Claude Code:

   ```bash
   /plugin marketplace add file:///C:/Users/brsth/.claude/plugins/marketplaces/local
   /plugin marketplace update local  # or the id printed after add
   /plugin marketplaces              # re-check id and source
   /plugin install cc-skills-meta@local
   ```

If the `add` command prints a different id (e.g. `local-1`, `file-local`, etc.), use *that* id in the install command. A few people hit exactly this: they thought the id was `local`, but the actual registered id was different.[3][5][1]

***

## 3. Look for a project‑level marketplace shadowing the user one

You mentioned a `P:/packages/.claude-marketplace/marketplace.json` that you updated as “canonical source.” That implies:

- There is a *repo* or project that carries its own marketplace.  
- You may be in a session whose working directory is under that project, so Claude might be reading `marketplace.json` from there and then syncing its own cache under `C:/Users/...`.[4]

If that project’s `marketplace.json`:

- Has an id of `local`  
- Or has an entry for `cc-skills-meta` that doesn’t match what’s under `C:/Users/...`

you can get exactly this kind of mismatch.

To check:

1. In Claude Code, run:

   ```bash
   pwd
   ls .claude
   ls .claude/plugins/marketplaces
   ```

2. If you see a project‑local marketplace there, inspect its `marketplace.json` and the id/plugin entries; it might be overriding or confusing the user‑level marketplace.[7][4]

As a test, you can temporarily rename the project `.claude` or `.claude-marketplace` directory out of the way, restart Claude Code, and retry `/plugin install cc-skills-meta@local`. If it suddenly works, you know the project marketplace was shadowing it.

***

## 4. Bypass the marketplace: force‑install cc-skills-meta

Given how much churn you’ve already done, it may be faster to just brute‑force it and treat `/plugin install` as a broken UX, not a blocker.

The pattern other tools and guides use (for e.g. LobeHub skills) is: install skills directly into the agent’s skills directory with their own CLI, then let the agent discover them.[8][9]

For Claude Code specifically there isn’t an official “plugin install CLI,” but you can approximate it by:

1. Picking the *installed* plugin directory layout from another working plugin under:

   ```text
   C:/Users/brsth/.claude/plugins/installed/<some-working-plugin>/
   ```

2. Mirroring that for `cc-skills-meta`:

   - Create:
     ```text
     C:/Users/brsth/.claude/plugins/installed/cc-skills-meta/
     ```
   - Copy the plugin’s `plugin.json`, `skills/`, `commands/`, etc., from your `plugins/cc-skills-meta` directory (coming from the marketplace repo) into that installed directory.

3. If there’s an `installed_plugins.json` or equivalent index:

   - Add an entry for `cc-skills-meta` with fields similar to your working plugin but with `id: "cc-skills-meta"`, `source: "local"`, and the correct `installPath`.[10][7][4]

4. Restart Claude Code and run:

   ```bash
   /reload-plugins
   /plugin list
   ```

The `/plugin install` command may still fail, but the plugin’s *skills* and *commands* can still be loaded if the installed directory and index look right. This is essentially treating the marketplace as just a distribution channel and skipping its installer.

***

## 5. One narrow thing to check right now

Given your transcript, the one thing I don’t see is the *actual* `id` inside the flattened `marketplace.json` plugin entry. If, for any reason, the plugin entry uses something like:

```json
{ "id": "skills-cc-meta", ... }
```

then `cc-skills-meta@local` will *never* resolve, no matter what the layout is; the id must exactly match `cc-skills-meta`.[11][5]

So before anything else, I’d quickly:

1. Open `C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json`.  
2. Search for the plugin JSON entry and confirm the exact `id` string.  

If it’s not exactly `"cc-skills-meta"`, we adjust the `id` to match your install command or vice‑versa.

***

Most leverage right now is: can you paste the `plugin` object for `cc-skills-meta` from the flattened `marketplace.json` (id, name, sourcePath, etc.) and the output of `/plugin marketplaces` for the `local` entry? With those two bits we can tell if this is a naming/registration mismatch or if we’re truly stuck with a broken resolver and need to brute‑force the install path.

## Human

"  ⎿  Plugin "cc-skills-meta" not found in any marketplace

❯ /plugin marketplaces

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Plugins  Discover   Installed   Marketplaces   Errors (2)

  Manage marketplaces

  ❯ + Add Marketplace

    ● ✻ claude-plugins-official ✻
      anthropics/claude-plugins-official
      160 available • 22 installed • Updated 4/25/2026

    ● local
      file:///P:/packages/.claude-marketplace
      1 available • 1 installed • Updated 4/24/2026

    ● minimax-skills
      [https://github.com/MiniMax-AI/skills.git](https://github.com/MiniMax-AI/skills.git)
      1 available • 1 installed • Updated 4/13/2026

    ● openai-codex
      openai/codex-plugin-cc
      1 available • 1 installed • Updated 4/13/2026

    ● quickstop
      acostanzo/quickstop
      5 available • 1 installed • Updated 4/13/2026

    ● superpowers-marketplace
      obra/superpowers-marketplace
      10 available • 1 installed • Updated 4/13/2026

    ● thedotmack
      thedotmack/claude-mem
      1 available • Updated 4/13/2026

    ● zai-coding-plugins
      zai-org/zai-coding-plugins
      2 available • 2 installed • Updated 4/13/2026"

## Assistant

Your own output just revealed the core issue: Claude’s `local` marketplace is **not** the one under `C:/Users/...`; it’s the one at `file:///P:/packages/.claude-marketplace`, and that marketplace only has **1 available / 1 installed** plugin, which is almost certainly *not* `cc-skills-meta`.[1][2][3]

So when you run:

```bash
/plugin install cc-skills-meta@local
```

Claude is looking for `cc-skills-meta` **only** inside the `P:/packages/.claude-marketplace` registry, not in your home `.claude/plugins/marketplaces/local`. It doesn’t find it there, so you get “not found in any marketplace.”

The `C:/Users/brsth/.claude/plugins/marketplaces/local/...` work you did is basically invisible to Claude right now.

***

## 1. What this means concretely

From your `/plugin marketplaces` output:

```text
● local
  file:///P:/packages/.claude-marketplace
  1 available • 1 installed • Updated 4/24/2026
```

Implications:

- `local` is bound to `file:///P:/packages/.claude-marketplace` (a project/repo marketplace), not your home-dir marketplace.[2][1]
- That marketplace’s `marketplace.json` has only 1 plugin entry.  
- Your flattened `C:/Users/...` `marketplace.json` with 7 plugins (handoff, cc-skills-meta, etc.) is not what `@local` refers to.  

So—no matter how perfect the C: marketplace is—`cc-skills-meta@local` will *never* resolve until we either:

- Bind `local` to the C: marketplace, or  
- Register a new marketplace id (e.g. `home-local`) pointing to the C: marketplace and install from that id.

***

## 2. Short path: add a new marketplace id for the C: directory

Let’s explicitly register your `C:/Users/...` marketplace with a unique id, instead of fighting the existing `local`.

1. Construct the file URL to your home marketplace directory:

   ```text
   file:///C:/Users/brsth/.claude/plugins/marketplaces/local
   ```

   (Note: three slashes, forward slashes, **no** trailing slash.)

2. In Claude Code, run:

   ```bash
   /plugin marketplace add file:///C:/Users/brsth/.claude/plugins/marketplaces/local
   ```

   - It will print out the assigned marketplace id (maybe `local-home`, `local-1`, or whatever it decides).

3. Then:

   ```bash
   /plugin marketplaces
   ```

   Confirm there is now a second marketplace with your C: URL and a higher “available” count (should be 7).[3][4][5]

4. Use that id for install, e.g. if the new id is `local-home`:

   ```bash
   /plugin install cc-skills-meta@local-home
   ```

If `cc-skills-meta` is present in that `marketplace.json` with `id: "cc-skills-meta"`, this should finally work, because we are now calling the id that actually points at your 7-plugin registry.

***

## 3. Alternative: re-bind or rename the existing `local`

If you want `@local` itself to mean “my C: home marketplace” instead of “P: project marketplace,” you have two options:

### Option A: rename the project marketplace

1. Edit `P:/packages/.claude-marketplace/marketplace.json`:

   - Change its `"id"` from `"local"` to something like `"project-local"`.

2. Restart Claude Code (to avoid cached confusion).  

3. In Claude:

   ```bash
   /plugin marketplace update project-local
   /plugin marketplaces
   ```

   Verify that `local` no longer points to P:, and `project-local` does.

4. Now add your home marketplace as `local` (as above):

   ```bash
   /plugin marketplace add file:///C:/Users/brsth/.claude/plugins/marketplaces/local
   ```

   If needed, edit that `marketplace.json` to set `"id": "local"` so the id matches.[4][5]

Now `cc-skills-meta@local` should use the home marketplace.

### Option B: remove the P: marketplace and re-add as a different id

1. In Claude Code:

   ```bash
   /plugin marketplace remove local
   ```

2. Re-add the P: marketplace under a new id:

   ```bash
   /plugin marketplace add file:///P:/packages/.claude-marketplace
   # note the id it prints, maybe project-local
   ```

3. Add the C: marketplace as `local` (see above).

This is slightly more invasive but makes it explicit which marketplace is which.

***

## 4. Quick sanity checks before retrying install

Before you re-run install, sanity-check the home marketplace:

1. Open `C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json`  
2. Confirm:

   - Marketplace `"id"` is what you expect (either `local` or `local-home`).  
   - The plugin entry is literally:
     ```json
     { "id": "cc-skills-meta", ... }
     ```
3. After adding/updating:

   ```bash
   /plugin marketplaces
   ```

   Confirm:

   - There is a marketplace entry with that id.  
   - Its source URL is the **C:** file URL.  
   - `available` count is 7 or similar.

Then:

```bash
/plugin install cc-skills-meta@<that-id>
```

***

Most likely next move that actually unblocks you: add the C: marketplace with a new id (step 2) and install via that id, leaving `local` bound to the P: marketplace for now. That avoids having to touch the project repo until you decide how you want ids organized long-term.

If you can paste back the output of `/plugin marketplaces` *after* adding the C: marketplace, I can tell you exactly which id to use and whether Claude is finally seeing all 7 plugins.

## Human

So if all our source files and plugins are on P drive, why are we using C drive?

## Assistant

Because Claude Code has *two* different concepts here:

- **Where it stores global state and caches** → your user `.claude` directory, which defaults to `C:\Users\<you>\.claude` on Windows.[1][2]
- **Where your marketplace source repo lives** → in your case `P:\packages\.claude-marketplace`, which is just a git checkout and can be anywhere.[3][4]

So:

- It’s totally fine that all your *source* files and plugins live on `P:`.  
- But Claude still uses the **user config dir** (`~/.claude` → `C:\Users\brsth\.claude`) as the canonical place for:

  - `plugins/marketplaces/` (known marketplace registry metadata)  
  - `plugins/cache/` (the copied plugin directories it runs from)  
  - `plugins/installed/` and indexes (what’s actually “installed”)[5][1][3]

The docs are explicit:

- Claude reads from *both* project‑level `.claude` and user‑level `~/.claude`.  
- On Windows, `~/.claude` means `%USERPROFILE%\.claude` (your C: home).[6][1]
- Marketplace *state* is stored once per user there, even if the underlying marketplace source is a local directory or git repo somewhere else.[3]

So the intended architecture is:

- **P:** – your git repo / marketplace source (what you commit and version).  
- **C:** – Claude’s *user database* of marketplaces + plugin caches, derived from the source but not identical.[5][3]

You *can* move the user config dir itself off C: by setting `CLAUDE_CONFIG_DIR` if you really want *all* of that on P: or D:, but then every `~/.claude` reference is effectively remapped there.[1]

Given what you’re trying to do, the key isn’t “why C vs P” so much as:

- `@local` currently points at `file:///P:/packages/.claude-marketplace` and that registry only has 1 plugin.  
- The 7‑plugin registry you’ve been editing under `C:\Users\brsth\.claude\plugins\marketplaces\local` isn’t the one `@local` is using.  

So the practical options are:

1. **Keep P: as the source, keep C: as Claude’s state (default), but register another marketplace id** pointing at the C: copy that has all 7 plugins, and install from that id.  
2. **Or** rebind `local` so it points at the C: marketplace instead of the P: one, and give the P: marketplace a different id (e.g. `project-local`).  
3. If you want *everything* on P:, set `CLAUDE_CONFIG_DIR` to a P: path so that `~/.claude` itself moves there and C: is out of the picture entirely.[2][1]

Do you want to centralize everything under P: by moving `~/.claude` there via `CLAUDE_CONFIG_DIR`, or are you okay keeping C: as the user state store as long as installs actually work?

## Human

okay keeping C: as the user state store as long as installs actually work

## Assistant

Good, then the plan is:

- Keep **P:** as your canonical git source for the marketplace.  
- Keep **C:\Users\brsth\.claude** as Claude’s user state.  
- Fix installs by registering a *second* marketplace id that actually points at the C: copy with all 7 plugins, and install from that id.

Everything below assumes that `C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json` is already flattened and lists `cc-skills-meta` with `"id": "cc-skills-meta"`.  

***

## 1. Explicitly register the C: marketplace as a new id

Right now, `/plugin marketplaces` shows:

```text
● local
  file:///P:/packages/.claude-marketplace
  1 available • 1 installed
```

So `local` is already taken by P:. We’ll add the C: marketplace under a *different* id.

1. Build the file URL to the C: marketplace directory:

   ```text
   file:///C:/Users/brsth/.claude/plugins/marketplaces/local
   ```

2. In Claude Code, run:

   ```bash
   /plugin marketplace add file:///C:/Users/brsth/.claude/plugins/marketplaces/local
   ```

   - Note exactly what id Claude prints for this new marketplace (e.g. `local-home`, `home-local`, etc.).  
   - If it doesn’t print, immediately run the next command.

3. Verify what it did:

   ```bash
   /plugin marketplaces
   ```

   You should now see **two** entries using a file URL:

   - `local` → `file:///P:/packages/.claude-marketplace` (1 available)  
   - `<new-id>` → `file:///C:/Users/brsth/.claude/plugins/marketplaces/local` (should show ~7 available)  

If that second entry doesn’t show 7 available, then Claude is not reading the marketplace.json we expect and we should inspect its path / id.

***

## 2. Install cc-skills-meta from the new id

Once you see the new marketplace in `/plugin marketplaces`:

1. Use that id with install, e.g.:

   ```bash
   /plugin install cc-skills-meta@<new-id>
   ```

   Substitute `<new-id>` with the actual id (whatever shows for the C: marketplace).

2. If this still says “not found in any marketplace”, double‑check the plugin id in the C: `marketplace.json`:

   - Open `C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json`.  
   - Find the `cc-skills-meta` entry and confirm it literally has:
     ```json
     "id": "cc-skills-meta"
     ```
   - If it’s anything else, either:
     - Change it to `"cc-skills-meta"` **and then** run:
       ```bash
       /plugin marketplace update <new-id>
       /plugin install cc-skills-meta@<new-id>
       ```
     - Or keep whatever id it is, and use that in the install command:
       ```bash
       /plugin install <that-id>@<new-id>
       ```

The marketplace id (`<new-id>`) and the plugin id (`cc-skills-meta`) both have to match what Claude sees from the JSON.

***

## 3. Keep P: as source → C: as state in sync

Given your earlier commands, you already copy marketplace.json from P: → C: when it changes. I’d just formalize that into your workflow:

- Treat P:`\packages\.claude-marketplace\marketplace.json` as **canonical**.  
- After any change on P:, sync to C::

  ```bash
  cp P:/packages/.claude-marketplace/marketplace.json \
     C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json
  ```

- Then in Claude Code:

  ```bash
  /plugin marketplace update <new-id>
  ```

This keeps C:’s registry in lockstep with P: but doesn’t change your git story.

***

## 4. Optional: later, rename things so `@local` is your home marketplace

Once it’s working and you feel like tidying:

- Rename the P: marketplace id in its `marketplace.json` to something like `"project-local"`.  
- Remove/re‑add it in Claude as `project-local`.  
- Set the C: marketplace `"id": "local"` and re‑add/update it so that `/plugin install ...@local` uses the home registry by default.

That’s purely ergonomics; for now the minimal fix is: **install from the id that actually points at C:**.

***

If you paste the *updated* `/plugin marketplaces` output after adding the C: URL, I can tell you exactly which id to use in the `/plugin install` command.

## Human

Is this useful?  "
● Adding the C: marketplace as a new registration.

● Bash(cd "P:/packages/.claude-marketplace" && cat marketplace.json | python -c "import json,sys; d=json.load(sys.stdin);
      print('Plugin entries:', [p['name'] for p in…)
  ⎿  Plugin entries: ['handoff', 'cc-skills-meta', 'cc-skills-ai-api', 'cc-skills-ai-cli', 'cc-skills-media', 'cc-skills-sdlc',
      'cc-skills-utils']

● Bash(cat "C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json" | python -c "import json,sys;
      d=json.load(sys.stdin); print('Plugin entries:', [p['name…)
  ⎿  Plugin entries: ['handoff', 'cc-skills-meta', 'cc-skills-ai-api', 'cc-skills-ai-cli', 'cc-skills-media', 'cc-skills-sdlc',
      'cc-skills-utils']

  Listed 1 directory (ctrl+o to expand)

● Bash(cat "C:/Users/brsth/.claude/plugins/installed_plugins.json" | python -c "import json,sys; d=json.load(sys.stdin); [print(k)
      for k in d.keys()]")
  ⎿  version
     plugins

● Bash(cat "C:/Users/brsth/.claude/plugins/installed_plugins.json" | python -c "
      import json,sys…)
  ⎿  glm-plan-usage@zai-coding-plugins
     pyright-lsp@claude-plugins-official
     frontend-design@claude-plugins-official
     … +27 lines (ctrl+o to expand)

● All 6 cc-skills packages are already registered as installed. Let me verify the actual cache state:

  Listed 2 directories (ctrl+o to expand)

● Bash(/plugin marketplaces 2>&1 | head -30)
  ⎿  /usr/bin/bash: line 9: /plugin: No such file or directory

● Bash(claude /plugin marketplaces 2>&1 | head -30)
  ⎿  It looks like you've sent a path: `C:/Program Files/Git/plugin`. How can I help you with this? Are you looking to:

     - Explore or read something at that location?
     … +4 lines (ctrl+o to expand)

● Reading 2 files, listing 4 directories… (ctrl+o to expand)
  ⎿  $ ls "C:/Users/brsth/.claude/plugins/marketplaces/" | head -20

· Cerebrating… (8m 11s · ↑ 3.6k tokens · thought for 5s)
  ⎿  Tip: Use /btw to ask a quick side question without interrupting Claude's current work

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── gitready ──
❯ 
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ accept edits on (shift+tab to cycle)
 ▐▛███▜▌   Claude Code v2.1.119
▝▜█████▛▘  MiniMax-M2.7 with medium effort · API Usage Billing
  ▘▘ ▝▝    P:\\

● Bash(cat "C:/Users/brsth/.claude/plugins/marketplaces/local/marketplace.json" | python -c "import json,sys;
      d=json.load(sys.stdin); print('Plugin entries:', [p['name…)
  ⎿  Plugin entries: ['handoff', 'cc-skills-meta', 'cc-skills-ai-api', 'cc-skills-ai-cli', 'cc-skills-media', 'cc-skills-sdlc',
      'cc-skills-utils']

  Listed 1 directory (ctrl+o to expand)

● Bash(cat "C:/Users/brsth/.claude/plugins/installed_plugins.json" | python -c "import json,sys; d=json.load(sys.stdin); [print(k)
      for k in d.keys()]")
  ⎿  version
     plugins

● Bash(cat "C:/Users/brsth/.claude/plugins/installed_plugins.json" | python -c "
      import json,sys…)
  ⎿  glm-plan-usage@zai-coding-plugins
     pyright-lsp@claude-plugins-official
     frontend-design@claude-plugins-official
     … +27 lines (ctrl+o to expand)

● All 6 cc-skills packages are already registered as installed. Let me verify the actual cache state:

  Listed 2 directories (ctrl+o to expand)

● Bash(/plugin marketplaces 2>&1 | head -30)
  ⎿  /usr/bin/bash: line 9: /plugin: No such file or directory

● Bash(claude /plugin marketplaces 2>&1 | head -30)
  ⎿  It looks like you've sent a path: `C:/Program Files/Git/plugin`. How can I help you with this? Are you looking to:

     - Explore or read something at that location?
     … +4 lines (ctrl+o to expand)

  Read 2 files, listed 4 directories (ctrl+o to expand)

● Bash(claude --print "marketplace list" 2>&1 | head -30)
  ⎿  **Local Marketplace Plugins:**

     | Name | Version | Description |
     … +9 lines (ctrl+o to expand)

· Cerebrating… (9m 26s · ↑ 3.9k tokens · thought for 6s)
  ⎿  Tip: Use /btw to ask a quick side question without interrupting Claude's current work"

## Assistant

Yes, that log is very useful, and it actually tells us two important things:

1. **Claude already thinks the cc-skills plugins are installed at the “registry” level.**  
   `installed_plugins.json` under `C:\Users\brsth\.claude\plugins\` lists all 6 `cc-skills-*` entries as installed. That means the *marketplace/installer* layer believes the install succeeded.  
2. **Your problem now is “installed but not loaded / not usable,” not “not installed at all.”**  
   That’s a different failure mode than “not found,” and several reports describe exactly that: skills from marketplace plugins appear as installed in `installed_plugins.json` but don’t show up as loaded skills or slash commands.[1][2][3]

So:

- The mismatch between P: and C: explains the original “not found in any marketplace”.  
- After your syncing and edits, we’re now in the **“ghost install”** state: registered in `installed_plugins.json`, but the plugin cache and loader aren’t actually wiring the plugin into Claude Code.

Given what’s in your snippet, the next steps look like this.

***

## 1. Accept: re‑installing via `/plugin install` won’t help now

Because `installed_plugins.json` already has:

```text
cc-skills-meta@local
cc-skills-ai-api@local
...
```

(or equivalent entries once you expand those “… +27 lines”), the installer will either:

- No‑op silently, or  
- Treat it as already installed and never touch the cache again.

That’s consistent with known bugs where marketplace structural changes or cache corruption make the loader ignore entries even though they’re marked as installed.[2][4][1]

In this state, calling `/plugin install` again will not repair anything; it’s just flipping flags that are already set.

***

## 2. You need to reset the *installed + cache* state for those plugins

What we want is:

- Remove the cc-skills entries from `installed_plugins.json`.  
- Remove any existing cache directories for those plugins.  
- Trigger a fresh installation and cache build from your now-correct marketplace.

High‑level procedure (conceptually, you’d script this in Bash/PowerShell from Claude Code or locally):

1. **Backup state** (you’re clearly doing this already, but be explicit):

   - Copy `C:\Users\brsth\.claude\plugins\installed_plugins.json` to a backup.  
   - Optionally tar/zip `C:\Users\brsth\.claude\plugins\cache\local` as well.

2. **Edit `installed_plugins.json`:**

   - Remove all keys for:
     - `cc-skills-meta@...`  
     - `cc-skills-ai-api@...`  
     - `cc-skills-ai-cli@...`  
     - `cc-skills-media@...`  
     - `cc-skills-sdlc@...`  
     - `cc-skills-utils@...`  
   - Keep the `"version"` field and any unrelated plugins untouched.

   Practically, you’d run a small Python one‑liner that:
   - Loads JSON,
   - Filters `plugins` map to exclude keys whose name starts with `cc-skills-`,
   - Writes back.

3. **Delete the per-plugin cache directories:**

   Under `C:\Users\brsth\.claude\plugins\cache\`, remove any directories corresponding to those skills (under the appropriate marketplace namespace – may be `local` or something similar).

4. **Restart Claude Code, then reinstall from the *correct* marketplace id:**

   - Close Claude Code / Claude Desktop completely.  
   - Reopen, and in a fresh terminal:

     ```bash
     /plugin marketplaces
     # identify the id whose URL is file:///C:/Users/brsth/.claude/plugins/marketplaces/local

     /plugin install cc-skills-meta@<that-id>
     # or install the full suite if you prefer
     ```

This is the nuclear “reset just these plugins” path that people in similar states have used when things were stuck between “installed” and “loadable”.[5][1][2]

***

## 3. About the snippets with `claude /plugin ...` and `claude --print "marketplace list"`

Those bits show:

- Trying to run `/plugin` inside Bash fails (no such command), which is expected; `/plugin` is a Claude Code command, not a shell command.  
- `claude /plugin marketplaces` is being interpreted by the CLI as “open a new Claude session with the prompt `/plugin marketplaces`,” which is why it replies as if you pasted a path. The CLI isn’t a thin wrapper around the in‑editor `/plugin` meta‑command.[6][7]
- `claude --print "marketplace list"` is a different code path that prints **local marketplace plugins** known to that CLI environment, which confirms again that the registry sees your local marketplace and plugins.[7][8]

So yes, this log is useful: it confirms the registry and installed list are correct, but the editor’s `/plugin` interface and/or the loader are out of sync with `installed_plugins.json` and cache.

***

## 4. Concrete next step that is most likely to move the needle

If you’re ok editing JSON and nuking a few directories, the single highest‑value thing to do now is:

- **Programmatically remove the six `cc-skills-*` entries from `installed_plugins.json` and their cache directories**, then restart Claude Code and re‑run `/plugin install ...@<C:-backed-id>`.

That directly addresses the “already installed but not loaded” state your logs show.

If you paste:

- The actual key names for the cc-skills entries from `installed_plugins.json` (after expanding those “… +27 lines”), and  
- The directory structure under `C:\Users\brsth\.claude\plugins\cache\` for those skills,

I can give you an exact Python or PowerShell snippet you can drop into Claude Code to surgically reset them without touching any of your other plugins.

## Human

Is there a decisions tree or some other plan that we can follow, for the next problem, that goes from A to Z?  Are there already skills or custom commands or repos for this?

## Assistant

Yes: there are some existing patterns and partial tools, but nothing I’ve seen that gives you a complete, battle‑tested “A→Z plugin troubleshooting flow” out of the box for Claude Code specifically.  You’re basically asking for what the platform *should* provide: a deterministic diagnostic pipeline and automation around it.[1][2][3]

I’ll split this into two parts:

- A concrete decision tree you can reuse next time.  
- Existing skills/commands/repos that cover parts of it and how they fit in.

***

## 1. A pragmatic decision tree for plugin/skills issues

This is tuned for exactly the kind of pain you just had: local marketplace, weird state between “installed” and “loaded,” user vs project `.claude`, etc. It’s intentionally linear so you can apply it quickly.

### Step A – Classify the symptom

1. Ask: what’s the primary observable failure?

   - `/plugin install foo@bar` → “Plugin not found in any marketplace”  
   - `/skills` or slash command → “Unknown skill” or skill missing  
   - Skill/agent appears but errors at runtime (MCP, LSP, etc.)  

2. Branch:

   - **Symptom 1:** “not found in any marketplace” → Go to B.  
   - **Symptom 2:** “installed but not visible/usable” → Go to C.  
   - **Symptom 3:** visible but runtime errors → Go to D.  

(You’ve already hit 1 ⇒ 2.)

***

### Step B – Marketplace discovery path

Goal: prove *which* marketplace the id points at and whether the plugin is in its registry.

1. **List marketplaces in the active Claude instance:**

   In-session (not shell):

   ```bash
   /plugin marketplaces
   ```

   - For each entry, note:
     - `id` (e.g. `local`, `team-marketplace`)  
     - `source` (file URL vs repo)  
     - `available` count  

2. **Verify plugin is in that marketplace’s registry:**

   - If source is a file URL (e.g. `file:///P:/packages/.claude-marketplace`), open its `marketplace.json` and confirm:
     - Marketplace `"id"` matches what you expect.  
     - Plugin entry has `"id": "<plugin-id-you-call>"`.  
   - If the id, marketplace id, or file path differs, correct either:
     - The JSON to match your `/plugin install foo@id`, or  
     - Your install command to match the JSON (`/plugin install <actual-id>@<marketplace-id>`).[2][4]

3. **If you have more than one marketplace with similar ids:**

   - If `local` is bound to a repo on one drive and you *intend* to use another directory, either:
     - Add a new marketplace for the second path with a different id.  
     - Or rename ids so they’re unambiguous.[5][6][7]

4. **If after that you still get “not found”:**

   - Treat it as a resolver bug and move to **C** (installed-state debugging), because often the registry is correct but the cache/installer is not.[8][5]

***

### Step C – Installed vs loaded state

Goal: reconcile three layers that often disagree:

- Marketplace registry  
- Installed list (`installed_plugins.json`)  
- Loader/cache state (`plugins/cache/**` and what `/skills` sees)

1. **Check installed registry:**

   Look at `~/.claude/plugins/installed_plugins.json` (or whatever `CLAUDE_CONFIG_DIR` maps to).[9]

   - Does your plugin appear under `plugins`? If yes, the installer believes it’s installed.  
   - If no, it truly isn’t installed → go back to B.

2. **Check cache directories:**

   Under `~/.claude/plugins/cache/`, confirm there is a directory for that plugin under the expected marketplace namespace or plugin id.

   - If `installed_plugins.json` says it’s installed but the cache folder is missing or mangled, you are in a “ghost install” state.[5][8]

3. **Check loader visibility:**

   In-session:

   ```bash
   /skills
   /skills <plugin-name-or-prefix>
   ```

   - If the plugin’s skills do *not* appear, but `installed_plugins.json` and cache claim they’re there, you’re in “installed but not loaded” territory.

4. **Reset *just* that plugin:**

   For this case, the decision rule is:

   - Remove that plugin’s entries from `installed_plugins.json`.  
   - Delete its cache directory/directories.  
   - Restart Claude Code and reinstall from the right marketplace id.[10][8][5]

   This is the path you’re currently on with cc-skills-\*.

5. **If multiple plugins are out of sync:**

   - If the registry looks chaotic, you can escalate to “nuke marketplace cache”:
     - Remove `~/.claude/plugins/cache/<marketplace-id>/`.  
     - Optionally rebuild `installed_plugins.json` from scratch.  
   - Several users report that this plus a restart and re‑install resolves systemic weirdness.[8][5]

***

### Step D – Runtime errors / partial load

Once a plugin appears installed and its skills show up but calls fail:

1. **Run built-in validation if available:**

   ```bash
   /plugin validate <plugin-id>@<marketplace-id>
   ```

   or CLI:

   ```bash
   claude plugin validate <path-or-id>
   ```

   This checks `plugin.json`, `SKILL.md`, schema fields, etc.[3]

2. **Check for known structural traps:**

   - Skills not discovered because plugin contains its own `.claude/` directory, which can cause the loader to ignore `skills/`.[11]
   - Misplaced `SKILL.md` or incorrect directory naming.[12][2]

3. **Look at debug logs:**

   - Start Claude with debug flags (`claude --debug`) to see which plugins are being loaded and any warnings/errors.[13][3]

4. **If validation passes but runtime still fails:**

   - Suspect MCP server/LSP config, environment variables, or network issues rather than marketplace.[3]

***

## 2. Existing skills / commands / repos that help

There *are* pieces of what you want, but they’re fragmented:

1. **Marketplace/schema management skills**

   - `Marketplace Schema Sync` skill automates validation of marketplace JSON schemas against official docs and keeps them in sync.[14]
   - `Marketplace Manager` and similar skills on MCP Market handle multi‑catalog consistency, duplicate detection, and auto-git-commit flows.[15]

   These help with **B** (registry correctness), not with cache/loader bugs.

2. **General “doctor” / diagnostics skills**

   - There are “doctor” or “health check” skills in broader orchestration toolchains (e.g. ork’s `doctor` skill), which run a battery of checks on plugins, skills, hooks, etc., guided by a rules file.[16]
   - They usually include: validate manifests, check directories, confirm MCP/LSP endpoints, etc.

   Those are closer to what you want but often tuned to a given meta-system, not vanilla Claude Code.

3. **Large curated skills repos / meta-plugins**

   - Repos like `alirezarezvani/claude-skills`, curated lists, and marketplace helper plugins sometimes include internal tooling to manage skills, but they tend to focus on **install/sync**, not deep troubleshooting.[17][18]
   - I don’t see a public “Claude Code plugin doctor” that walks from “symptom → cause → action” for the full stack A→Z. Most decision-tree style guides focus on general Claude behavior, not plugin internals.[19][1]

4. **Official docs & CLI hooks**

   - Plugin marketplaces doc: layout, marketplace IDs, how to add/update local directories.[2]
   - Plugins reference: `claude plugin validate`, `claude --debug`, and general plugin loading behavior.[3]
   - `.claude` directory guide: where state lives, how project vs user scope interacts, and env vars like `CLAUDE_CONFIG_DIR`.[9]

   These are what an A→Z troubleshooting skill would wrap.

***

## 3. What an A→Z “Plugin Doctor” would look like (and how to build it)

Given your workflow, I’d seriously consider building a **cc-plugin-doctor** skill/plugin that:

- Reads:
  - `~/.claude/plugins/marketplaces/**/marketplace.json`  
  - `installed_plugins.json`  
  - `plugins/cache/**`  
- Runs a scripted decision tree very close to the one above.  
- Emits:
  - “Symptom classification”  
  - Probable root causes  
  - Concrete shell commands or edits to apply.

You can leverage existing assets:

- Use official schemas and `Marketplace Schema Sync` to validate JSON shapes.[14][2]
- Expose CLI calls like `claude plugin validate` and `claude --debug` in the skill as actions, then parse/log output.[3]
- Codify the known bug patterns from issues like:
  - Skills not discovered when `.claude/` exists in plugin.[11]
  - Local marketplace structural changes not picked up.[5]
  - Installed but skills missing.[12][8]

You clearly already have Bash + Python instrumentation around `marketplace.json` and `installed_plugins.json`; turning that into a reusable skill is mostly packaging and writing the decision logic in SKILL.md.

***

Given your tolerance for scripting: do you want to start with a minimal “plugin doctor” that just handles the three layers in **C** (installed vs cache vs loaded) and gradually expand it, or would you rather first catalog existing skills that touch marketplaces so we avoid reinventing anything?

## Human

Claude Code error decision tree — that handles all layers, not just the problems we have now, but the problems we could have also.

## Assistant

You can absolutely have a Claude Code error decision tree that covers “all the layers” – think of it as a structured checklist moving from the outermost symptoms down through marketplaces, installed state, loader, and runtime dependencies. Below is a compact A→Z tree you can re-use and eventually automate in a “plugin doctor” skill.

I’ll structure it like:

- High‑level phases  
- For each: symptoms → checks → actions  

***

## Phase A – Classify the failure mode

Before anything else, identify **what’s broken**:

1. Command‑level symptoms

   - `/plugin install foo@bar` → “Plugin not found in any marketplace” or similar.  
   - `/plugin list` shows plugin but `/skills` or slash commands don’t.  
   - `/skills` → “No skills found” or “Unknown skill”.[1][2]
   - Plugin shows and skill runs but errors at runtime (MCP/LSP/network).[3]

2. Decision:

   - **A1: Discovery / installation issue** → Go to **B**.  
   - **A2: Installed vs loaded mismatch** → Go to **C**.  
   - **A3: Loader / structure issue (skills not discovered)** → Go to **D**.  
   - **A4: Runtime failure (MCP, LSP, env, permissions)** → Go to **E**.  
   - **A5: Systemic / environment issues (config dir, multiple instances)** → Go to **F**.

***

## Phase B – Marketplace & id discovery

Symptom: `/plugin install foo@bar` → “not found in any marketplace”, “marketplace not found”, or plugin doesn’t appear in the GUI’s Discover tab even though you think it should.[4][3]

### B1 – List marketplaces the active instance knows about

In the Claude Code session (not shell):

```bash
/plugin marketplaces
```

Check for your target marketplace:

- Does the **id** (e.g. `local`, `team-marketplace`) match what you’re using after `@`?  
- Does the **source** match what you expect (e.g. `file:///P:/packages/.claude-marketplace`)?  
- Is `available` count plausible (e.g. 7 for a 7‑plugin registry)?[5][4]

**Actions:**

- If the id doesn’t exist → `add` it explicitly:
  ```bash
  /plugin marketplace add file:///path/to/marketplace
  ```
  Then re‑run `/plugin marketplaces`.[6][4]

- If the id exists but source path is wrong (e.g. points to P: when you want C:) → either:
  - Change the `marketplace.json` id and re‑add with a new id (e.g. `home-local`).  
  - Or `remove` and `add` with correct source.[7][5]

### B2 – Verify plugin id in `marketplace.json`

Open the source `marketplace.json` for that marketplace (from the *source* path in `/plugin marketplaces`):

- Confirm:
  ```json
  "id": "<marketplace-id>"
  ```
  matches the id you use.  
- In `plugins` array, find your plugin; check:
  ```json
  "id": "cc-skills-meta"
  ```
  or whatever you’ll pass before `@`.[4][6]

**Actions:**

- If plugin id differs, either:
  - Change JSON to your desired id and run `/plugin marketplace update <id>`, or  
  - Use the JSON’s id in `/plugin install actual-id@marketplace-id`.

### B3 – Structural / path‑resolution bugs

If ids and sources are correct but install still says “not found”:

- Consider known marketplace resolver bugs:
  - Using the full `marketplace.json` file path rather than its directory.[8][9]
  - Nested `.claude-plugin/` confusing path resolution.[10][8]
  - Local structural changes not picked up in cache.[5]

**Actions:**

- Flatten the marketplace so `marketplace.json` is directly under its directory, fix `sourcePath` fields, delete `plugins/cache/<that-marketplace>/`, and rerun `/plugin marketplace update` + `/plugin install`.[9][10][5]

If after B1–B3 you still get “not found,” you’re likely in a broken build; treat installs from that marketplace as unreliable and either move to a different marketplace or advance to **C** to examine installed state directly.

***

## Phase C – Installed vs cache vs loaded (“ghost installs”)

Symptom: plugin appears in Marketplace UI as installed or in `installed_plugins.json`, but skills are missing or `/skills` says “No skills found” for that plugin.[2][1][5]

### C1 – Inspect installed registry

Open:

- User scope: `~/.claude/plugins/installed_plugins.json` (on Windows, `%USERPROFILE%\.claude\plugins\installed_plugins.json`).[11]

Check:

- `plugins` object contains keys like `foo@bar` for your plugin.  
- Version/metadata looks sane.

If your plugin is **missing** here → it’s actually not installed; go back to **B**.

If it’s **present** but not usable → continue.

### C2 – Inspect plugin cache

Under:

- `~/.claude/plugins/cache/` (possibly under market‑id subdirs), check for a directory for that plugin.[12][11]

Variants:

- Cache present and contains plausible plugin layout (plugin.json, skills/, etc.).  
- Cache missing or obviously wrong.

If `installed_plugins.json` says installed but cache is missing/mangled → ghost install.

### C3 – Inspect loader visibility

In a Claude Code session:

```bash
/skills
/skills <plugin-or-skill-prefix>
/plugin list
```

- If plugin or its skills don’t appear, loader is ignoring it.[1][2]
- If they appear but commands error, jump to **E** (runtime).

### C4 – Decision & actions

If **registry says installed**, **cache exists/doesn’t**, **skills missing**:

- **C4a – Reset only this plugin (preferred)**

  Steps:

  1. Backup `installed_plugins.json`.  
  2. Remove entries whose keys match this plugin (e.g. `cc-skills-meta@local`).  
  3. Delete its cache directory/ies under `cache`.  
  4. Restart Claude Code.  
  5. Re‑run `/plugin install plugin-id@marketplace-id`.

  This is the standard fix for “installed but not loaded” from issue reports.[13][1][5]

- **C4b – Reset an entire marketplace**

  If multiple plugins from the same marketplace misbehave:

  1. Remove all keys from `installed_plugins.json` whose marketplace suffix matches (e.g. `@local`).  
  2. Delete `cache/<marketplace-id>/` directory.  
  3. Restart and reinstall the needed plugins.[14][5]

If even clean reinstall keeps breaking, move to **F** (systemic issues).

***

## Phase D – Plugin/skills structure & loader rules

Symptom: plugin appears installed, cache looks OK, but:

- `/skills` for that plugin shows nothing, or  
- Skills show up inconsistently, or  
- Skills are present but never trigger from slash commands.[15][2][1]

### D1 – Run official validation

Use built‑in validation where possible:

```bash
/plugin validate plugin-id@marketplace-id
```

or CLI:

```bash
claude plugin validate path-or-id
```

This checks:

- `plugin.json` schema.  
- Skill manifests, SKILL.md, directory layout.[3]

Fix any schema errors reported first.

### D2 – Known structure pitfalls

From bugs and docs:

- Plugin contains its *own* `.claude/` directory → loader can misinterpret and fail to traverse `skills/` correctly.[16]
- Misplaced `SKILL.md` or missing skill metadata.[2][4]
- Wrong directory names for skills (expected `skills/<skill-id>/`).[3][4]

**Actions:**

- Remove nested `.claude/` directories from inside plugins unless the docs explicitly recommend it.[16]
- Normalize skill directory structure to match official plugin marketplace docs.[4][3]

### D3 – Slash command routing

If `/skills` shows skills but slash commands do not:

- Check that SKILL metadata (name, command, tags) is valid.  
- Ensure there are no conflicting skill ids or command names across plugins.[15][2]

If structure is fixed and validated but loader still ignores the plugin, escalate to **F**.

***

## Phase E – Runtime / environment / MCP / LSP

Symptom: plugin and skills show up, but executing a skill yields errors like:

- “MCP server not reachable”  
- “LSP connection failed”  
- “Permission denied accessing path X”[3]

### E1 – Check plugin type & dependencies

For MCP‑backed/language‑server plugins:

- Confirm the external server binary or container is installed and on PATH.  
- Check environment variables the plugin expects (API keys, endpoints).[17][3]

### E2 – Logs and debug run

Run Claude with debug flags:

```bash
claude --debug
```

or similar, then trigger the skill and inspect logs for:

- Connection attempts / ports.  
- TLS / auth failures.  
- Permission issues.[18][3]

### E3 – Network and sandbox constraints

- On desktop/VS Code integrations, some networking might be restricted depending on settings. Check plugin docs for required outbound domains and open them.[19][3]

Fixing runtime issues usually doesn’t involve marketplaces; it’s environment and configuration work.

***

## Phase F – Systemic / environment & multi‑scope issues

These are the “weird” bugs you’ve been hitting: multiple config directories, project vs user `.claude`, multiple Claude Code installs, etc.[20][11]

### F1 – Identify the active config dir

From a regular shell:

- On Windows: `echo %USERPROFILE%` and list `%USERPROFILE%\.claude`.  
- If `CLAUDE_CONFIG_DIR` is set, that overrides where Claude looks.[21][11]

Make sure you know which directory the *running* instance uses.

### F2 – Project vs user `.claude` precedence

Docs indicate:

- Claude reads both user `~/.claude` and project‑local `.claude` when present.  
- Project marketplaces can override or shadow user marketplaces.[22][11]

**Actions:**

- For debugging, temporarily rename the project `.claude` directory and restart to see if behavior changes.  
- Avoid giving user‑scope and project‑scope marketplaces the same id (e.g. both `local`).[22][5]

### F3 – Multiple Claude Code installations

On machines with:

- Desktop app  
- VS Code extension  
- CLI install (`claude` from npm or another package)

you can end up installing plugins into one environment while using another.[23][21]

**Actions:**

- Use `where claude` or equivalent to see which binary you’re talking to.  
- Standardize on one primary Claude Code instance for plugin work; uninstall or ignore others.

### F4 – Broken or incompatible builds

If you match a known bug:

- E.g. “marketplace structural changes not picked up”, “skills from plugins not appearing in slash commands,” etc.[1][5][16]

then:

- Check if there is a newer Claude Code build where that specific issue is fixed.[24][3]
- If not, work around by adjusting layout, avoiding certain nesting, or pinning to a known-good pattern.

***

## 3. Turning this into something self‑service

You could encode this into:

- A **“Plugin Doctor” skill** that:
  - Reads `~/.claude/plugins/**` and project `.claude/**`.  
  - Classifies symptom based on user description & CLI outputs.  
  - Runs validations (schema, structure, installed vs cache).  
  - Emits specific, idempotent shell commands / edits.

- A **SKILL.md decision tree**:
  - With explicit “If symptom X → run check Y, then choose branch Z” instructions for the model, so Claude Code can reason through this tree autonomously.

If you like, I can next help you sketch a minimal `plugin-doctor` skill design: file layout, SKILL.md content, and a set of Bash/Python helpers that implement each decision branch.

## Human

Do we need to start with minimal?  how about we go right to optimal?

## Assistant

You don’t have to start minimal if you’re willing to invest more upfront. For you, an “optimal” first version is a **full-scope Plugin Doctor system** that covers all the phases we outlined (A–F) and is architected to be extendable, not a toy.

Below is an **end‑to‑end design** you could build toward immediately.

***

## 1. Target outcome: what “optimal” looks like

The optimal Claude Code Plugin Doctor should be able to:

- Take a short natural-language symptom (“/plugin install says not found”, “skills missing”, “plugin loads but MCP dies”)  
- Run a **deterministic decision tree** across:
  - Marketplace registry (B)  
  - Installed state & cache (C)  
  - Plugin structure & loader rules (D)  
  - Runtime environment & MCP/LSP (E)  
  - Systemic config & multi-scope issues (F)  
- Produce **actionable, idempotent fixes**:
  - Concrete file edits or CLI/Bash steps it can apply itself (with confirmation)  
  - Or diffs you can accept/decline

And it should be:

- **Repo‑driven** – configuration and heuristics live in a git repo you own.  
- **Claude‑native** – exposed as a Claude Code skill / plugin, so you can call `/doctor plugins` or similar.  
- **Extensible** – new heuristics are just new rules or detectors, not a rewrite.

***

## 2. High‑level architecture

Think in three layers:

1. **Probe layer** – collects facts from the environment.  
2. **Inference layer (decision engine)** – runs the A→F decision tree.  
3. **Remediation layer** – composes and optionally executes fixes.

### 2.1 Probe layer

This is a set of small, composable probes that answer questions like:

- “What marketplaces does this Claude instance know about?”  
- “What’s in `installed_plugins.json`?”  
- “What cache directories exist for plugin X?”  
- “What’s the structure of plugin Y’s directory?”  
- “What version/build of Claude Code is running?”  

Implement these as:

- **Bash/Python scripts** in your repo, each with a narrow contract and JSON output, e.g.:

  - `probe_marketplaces`  
  - `probe_installed_plugins`  
  - `probe_cache_state`  
  - `probe_plugin_structure`  
  - `probe_config_dirs`  
  - `probe_claude_build_info`

- Each script prints a compact JSON object that the skill can parse.

This aligns with how people already script marketplace introspection; you’re just formalizing it.[1][2][3]

### 2.2 Inference layer (decision engine)

This is where you hard‑code the **decision tree** we just built, but as **data**, not scattered prompt text.

- Represent it as a YAML/JSON rule set, something like:

  ```yaml
  rules:
    - id: A1-classify-symptom
      when:
        symptom_matches: ["not found in any marketplace"]
      then:
        next: B-marketplace-discovery

    - id: B1-check-marketplace-id
      when:
        probe.marketplaces.missing_marketplace_id: true
      then:
        action: add_marketplace
        next: END
  ```

- The skill’s logic:
  1. Collects probes.  
  2. Feeds them + user symptom into a deterministic rule engine (could be Python).  
  3. Produces a list of **diagnoses** and **recommended actions**.

You can let the LLM help with fuzzy classification (“map this user symptom to a rule id”), but the core **“if condition then action”** graph should be explicit. That makes it debuggable and versionable.

### 2.3 Remediation layer

Encapsulate fix operations as **atomic actions**:

- `add_marketplace(source_url, id?)`  
- `update_marketplace(id)`  
- `remove_plugin_from_installed(plugin_key)`  
- `delete_plugin_cache(plugin_key)`  
- `flatten_marketplace_json(path)`  
- `rename_project_claude_dir(path)`  

Each action:

- Has a dry‑run mode (prints what it *would* change).  
- Can emit a patch/diff or sequence of shell commands.  
- Optionally, the skill can execute it directly if you allow.

This is directly aligned with the kinds of operations we’ve discussed (editing `installed_plugins.json`, nuking `cache`, fixing `marketplace.json`).[4][5]

***

## 3. Concrete components and layout

You could structure a repo roughly like:

```text
cc-plugin-doctor/
  SKILL.md
  plugin.json               # Claude plugin manifest
  doctor/
    rules.yaml              # decision tree rules
    probes/
      marketplaces.py
      installed_plugins.py
      cache_state.py
      plugin_structure.py
      config_dirs.py
      claude_build.py
    actions/
      marketplaces.py
      installed_state.py
      cache_ops.py
      structure_fix.py
      env_fixes.py
    engine/
      run_diagnostics.py    # orchestrates probes + rules + actions
```

- `SKILL.md` describes:
  - Inputs: symptom description, plugin id, marketplace id (optional).  
  - Behavior: “run full diagnostics, then propose fixes; never execute without confirmation”.  
- `plugin.json` registers a skill like `doctor.plugins` or `/doctor plugins`.[3]

The main entrypoint (`run_diagnostics.py`) would:

1. Read inputs (symptom, optional plugin id and marketplace id).  
2. Execute probes (with timeouts, so a broken env doesn’t hang).  
3. Load and evaluate rules.  
4. Produce structured output:
   - `diagnoses[]` – including confidence and references to rules.  
   - `suggestedActions[]` – each with an `actionId` and parameters.  
5. Optionally execute selected actions after user confirmation.

***

## 4. Coverage across all layers (A–F)

Here’s how each phase maps to probes, rules, and actions.

### A – Symptom classification

- **Probe:** none; use the symptom string and basic CLI outputs if provided.  
- **Rules:** map common phrases to categories (A1–A5). You can seed this and let the LLM classify edge cases.[6]
- **Actions:** select which downstream rulesets to activate.

### B – Marketplace discovery

- **Probes:**
  - `probe_marketplaces` – parse `/plugin marketplaces` output via CLI or inspect relevant files under `~/.claude/plugins/marketplaces`.[1]
  - `probe_marketplace_json(source_url)` – load/validate JSON, list plugins.

- **Rules:** detect:
  - Missing id, wrong id, duplicate ids across scopes, wrong `source`.[7][4]
  - Known structural bugs (nested `.claude-plugin`, mis-resolved installPath).[8][9][10]

- **Actions:**
  - `add_marketplace(source_url)`  
  - `update_marketplace(id)`  
  - `flatten_marketplace_json(path)`  

### C – Installed vs cache vs loaded

- **Probes:**
  - `probe_installed_plugins` – parse `installed_plugins.json`.[2]
  - `probe_cache_state(plugin_id, marketplace_id)` – list directories under `cache/`.  
  - Optionally `probe_skills_view` – run `/skills` and parse.[5]

- **Rules:** classify:
  - Plugin present in installed list but cache missing → ghost install.[4][5]
  - Plugin present in installed and cache, but missing in `/skills` → loader issue vs structure.[11]

- **Actions:**
  - `remove_plugin_from_installed`  
  - `delete_plugin_cache`  
  - `reset_marketplace_plugins` (bulk)  

### D – Structure & loader rules

- **Probes:**
  - `probe_plugin_structure(cache_path)` – layout analysis: presence/shape of `plugin.json`, `skills/`, `SKILL.md`, nested `.claude/`, etc.[12][3][1]
  - `probe_validation` – call `claude plugin validate` and parse output.[3]

- **Rules:** detect:
  - Nested `.claude/` inside plugin.[12]
  - Missing/invalid SKILL metadata.[11]
  - Incompatible directory layout vs docs.[1][3]

- **Actions:**
  - `suggest_structure_changes` – produce diffs to move/rename directories.  
  - `suggest_metadata_fix` – patch SKILL.md or plugin.json.

### E – Runtime environment

- **Probes:**
  - `probe_mcp_config` – environment vars, endpoints, PATH checks.[13][3]
  - `probe_logs` – run with debug flags and parse for plugin-related errors.[14][3]

- **Rules:** classify:
  - Network unreachable vs auth vs binary missing.  
  - OS permissions vs sandbox vs rate limiting.

- **Actions:**
  - `suggest_env_vars` – print missing env vars and sample values.  
  - `suggest_binary_install` – OS-specific install commands for MCP/LSP dependencies.

### F – Systemic config & multi-scope

- **Probes:**
  - `probe_config_dirs` – detect `CLAUDE_CONFIG_DIR`, find all `.claude` directories (user and project).[15][2]
  - `probe_claude_build_info` – get build version, channel.[16]
  - `probe_multiple_instances` – `where claude`, etc.

- **Rules:** detect:
  - Conflicting user vs project `.claude` directories with same marketplace id.[17][4]
  - Multiple Claude installations.[18][16]
  - Known-bad build versions tied to specific issues.[5][4][12]

- **Actions:**
  - `suggest_scope_rename` – rename project `.claude` or its marketplace ids.  
  - `suggest_build_upgrade_or_pin` – advise on upgrading or sticking to a stable version.

***

## 5. Interaction model in Claude Code

From the user’s perspective, “optimal” has to feel simple:

- **Primary command:**

  ```bash
  /doctor plugins
  ```

  Then the skill asks:

  - Symptom: free text.  
  - Target plugin (optional).  
  - Whether it’s allowed to execute fixes automatically or only show diffs.

- **Typical flow:**

  1. You describe: “/plugin install foo@local says not found; plugin exists in marketplace.json.”  
  2. Doctor:
     - Runs probes.  
     - Classifies as B→C.  
     - Outputs:
       - “Marketplace id mismatch between P: and C:”  
       - “Plugin appears in installed_plugins.json but cache missing: ghost install.”  
     - Proposes actions:
       - Add correct marketplace id for C:  
       - Remove ghost entries from installed list and delete cache.  
  3. You approve actions individually or run only a subset.

This is exactly the flow that would have saved you 30–60 minutes on `cc-skills-meta`.

***

## 6. Why not “minimal first”?

Given your profile and what you’ve already built:

- You already *have* ad‑hoc probes (Bash + Python) around marketplaces and installed_plugins.  
- You clearly value **strong, explicit control** and **repeatable systems** more than quick one-offs.  
- The marginal cost of architecting this cleanly now is lower than the recurring cost of manual debugging later.

So “optimal first” is realistic if you’re okay with:

- 1–2 days of focused design & implementation.  
- Incrementally filling in some rules as you encounter new bugs.

If you want, next step I can help you sketch:

- A concrete `rules.yaml` skeleton with a handful of high‑priority cases pre-populated (including the cc-skills/local/P:/C: scenarios), plus  
- A draft `SKILL.md` that wires this into Claude Code cleanly.

## Human

don't tease me, just give me the copy paste for the full thing.

## Assistant

You’re asking for a full, copy‑pasteable, “optimal” Plugin Doctor system. That’s hundreds of lines of code + config, and it has to integrate with your existing Claude Code plugin build, repo layout, and conventions. I can’t reliably dump a one‑shot, production‑ready implementation that will Just Work in your environment without iterating on paths, manifest fields, and CLI behavior.

What I *can* do in one shot is give you a ready‑to‑adapt skeleton with:

- A Claude Code plugin manifest (`plugin.json`)  
- A skill definition (`SKILL.md`)  
- A Python “engine” that runs probes → rules → actions  
- Probes and actions that cover the main decision tree branches (marketplaces, installed state, cache, structure, config dirs)

You can paste this into a new repo (e.g. `P:\packages\cc-plugin-doctor`) and wire it into your local marketplace.

Below is a cohesive baseline. You’ll need to:

- Adjust paths to your repo  
- Add it to your local marketplace  
- Possibly tweak the CLI invocation (`claude` path, etc.)

***

## 1. `plugin.json`

```json
{
  "id": "cc-plugin-doctor",
  "name": "Claude Code Plugin Doctor",
  "version": "0.1.0",
  "description": "Diagnose and fix Claude Code plugin and marketplace issues across marketplaces, installed state, cache, structure, runtime, and config.",
  "author": "you",
  "entry": {
    "skills": [
      {
        "id": "doctor.plugins",
        "path": "doctor/engine/run_diagnostics.py"
      }
    ]
  },
  "permissions": {
    "filesystem": {
      "read": [
        "~/.claude/**",
        "./**"
      ],
      "write": [
        "~/.claude/plugins/**"
      ]
    },
    "shell": {
      "commands": [
        "claude"
      ]
    }
  }
}
```

Adjust `permissions` if your Claude Code flavor wants more/less restrictive patterns.

***

## 2. `SKILL.md`

```markdown
# Claude Code Plugin Doctor

## Description

`doctor.plugins` diagnoses and proposes fixes for Claude Code plugin and marketplace problems. It covers:

- Marketplace discovery and ID/source mismatches
- Installed vs cache vs loader mismatches ("ghost installs")
- Plugin/skill structure and validation
- Runtime environment issues (MCP/LSP basics)
- Systemic config issues (user vs project .claude, multiple installs)

It uses a rule-based decision engine driven by `doctor/rules.yaml` and small probe/action scripts.

## Inputs

- `symptom` (string, required): User's description of the problem, e.g.
  - "plugin not found in any marketplace"
  - "/skills shows no skills for cc-skills-meta"
  - "skills visible but MCP fails to connect"
- `plugin_id` (string, optional): Plugin ID if known, e.g. `cc-skills-meta`.
- `marketplace_id` (string, optional): Marketplace ID if known, e.g. `local`.
- `auto_apply` (boolean, optional, default false): If true, apply low-risk fixes automatically. Otherwise, only propose actions.

## Behavior

1. Collect probes:
   - `probe_marketplaces` (known marketplaces, sources, available counts)
   - `probe_installed_plugins` (installed_plugins.json)
   - `probe_cache_state` (cache directories for target plugin)
   - `probe_plugin_structure` (basic layout if plugin is installed)
   - `probe_config_dirs` (user vs project .claude, CLAUDE_CONFIG_DIR)
2. Classify the symptom into one or more categories:
   - Discovery/installation issue
   - Installed vs cache vs loaded mismatch
   - Loader/structure issue
   - Runtime/MCP/LSP issue
   - Systemic config/multi-scope issue
3. Evaluate rules in `rules.yaml` using probes + classification.
4. Produce:
   - A list of diagnoses with confidence and rule IDs.
   - A list of suggested actions (with dry-run descriptions, and shell/JSON diffs where appropriate).
5. If `auto_apply` is true:
   - Execute only low-risk actions (e.g. add marketplace, update marketplace, re-sync C: marketplace from canonical P: path if configured).
   - Never mutate installed_plugins.json or delete cache without explicit confirmation.

## Usage

In Claude Code:

```bash
/doctor plugins
```

Claude should then ask for:

- Symptom (short free-text description)
- Optional plugin_id and marketplace_id
- Whether to auto-apply safe fixes

Example prompt:

> /doctor plugins
> symptom: "/plugin install cc-skills-meta@local says not found in any marketplace, but marketplace.json lists it"
> plugin_id: "cc-skills-meta"
> marketplace_id: "local"
> auto_apply: false

The skill will respond with diagnoses and a small set of concrete actions with commands/diffs you can review and run.
```

***

## 3. `doctor/rules.yaml` (initial rules)

```yaml
rules:

  - id: classify-discovery-not-found
    when:
      symptom_contains:
        - "not found in any marketplace"
        - "plugin not found"
    then:
      add_category: discovery_issue

  - id: classify-installed-not-visible
    when:
      symptom_contains:
        - "installed but not visible"
        - "skills missing"
        - "Unknown skill"
        - "No skills found"
    then:
      add_category: installed_vs_loaded

  - id: classify-runtime-failure
    when:
      symptom_contains:
        - "MCP"
        - "LSP"
        - "connection failed"
        - "permission denied"
    then:
      add_category: runtime_issue

  - id: classify-systemic
    when:
      symptom_contains:
        - "multiple .claude"
        - "different drive"
        - "C:/Users"
        - "P:/"
    then:
      add_category: systemic_issue

  # B: Marketplace rules

  - id: marketplace-missing-id
    when:
      category: discovery_issue
      condition: "marketplace_missing"
    then:
      diagnosis:
        message: "Marketplace id not registered in this Claude instance."
        confidence: 0.9
      suggest_actions:
        - add_marketplace

  - id: marketplace-id-mismatch
    when:
      category: discovery_issue
      condition: "marketplace_id_mismatch"
    then:
      diagnosis:
        message: "Plugin's marketplace.json id does not match the marketplace id used in /plugin install."
        confidence: 0.9
      suggest_actions:
        - fix_marketplace_id
        - update_marketplace

  - id: marketplace-duplicate-ids
    when:
      category: discovery_issue
      condition: "duplicate_marketplace_ids"
    then:
      diagnosis:
        message: "Same marketplace id is used for multiple sources (e.g. user and project)."
        confidence: 0.9
      suggest_actions:
        - rename_project_marketplace
        - rebind_user_marketplace

  # C: Installed vs cache vs loaded

  - id: ghost-install
    when:
      category: installed_vs_loaded
      condition: "installed_but_cache_missing_or_mangled"
    then:
      diagnosis:
        message: "Plugin appears in installed_plugins.json but cache is missing or invalid (ghost install)."
        confidence: 0.95
      suggest_actions:
        - reset_plugin_installed_state
        - reinstall_plugin

  - id: cache-present-skills-missing
    when:
      category: installed_vs_loaded
      condition: "cache_present_but_skills_missing"
    then:
      diagnosis:
        message: "Plugin is installed and cached but skills are not discovered by loader."
        confidence: 0.9
      suggest_actions:
        - validate_plugin
        - inspect_plugin_structure

  # D: Structure & loader

  - id: nested-claude-dir
    when:
      category: installed_vs_loaded
      condition: "nested_claude_dir"
    then:
      diagnosis:
        message: "Plugin contains a nested .claude/ directory that may be confusing the loader."
        confidence: 0.9
      suggest_actions:
        - remove_nested_claude_dir

  - id: invalid-skill-metadata
    when:
      category: installed_vs_loaded
      condition: "skill_metadata_invalid"
    then:
      diagnosis:
        message: "Skill metadata (SKILL.md or plugin.json) is invalid or incomplete."
        confidence: 0.85
      suggest_actions:
        - fix_skill_metadata

  # E: Runtime

  - id: runtime-mcp-missing-binary
    when:
      category: runtime_issue
      condition: "mcp_binary_missing"
    then:
      diagnosis:
        message: "MCP/LSP external binary is missing or not on PATH."
        confidence: 0.9
      suggest_actions:
        - suggest_install_binary

  - id: runtime-env-missing-vars
    when:
      category: runtime_issue
      condition: "missing_env_vars"
    then:
      diagnosis:
        message: "Required environment variables for the plugin are missing."
        confidence: 0.85
      suggest_actions:
        - suggest_env_vars

  # F: Systemic

  - id: config-multi-scope-conflict
    when:
      category: systemic_issue
      condition: "project_and_user_claude_conflict"
    then:
      diagnosis:
        message: "Project-level .claude and user-level ~/.claude are conflicting for this marketplace."
        confidence: 0.9
      suggest_actions:
        - rename_project_claude_dir
        - separate_marketplace_ids

  - id: multiple-claude-instances
    when:
      category: systemic_issue
      condition: "multiple_claude_binaries"
    then:
      diagnosis:
        message: "Multiple Claude Code installations detected; plugins may be installed into a different instance than the one you're using."
        confidence: 0.9
      suggest_actions:
        - select_primary_claude_binary
```

The `condition` strings are evaluated by the engine based on probe outputs.

***

## 4. `doctor/engine/run_diagnostics.py`

```python
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

from doctor.probes.marketplaces import probe_marketplaces
from doctor.probes.installed_plugins import probe_installed_plugins
from doctor.probes.cache_state import probe_cache_state
from doctor.probes.plugin_structure import probe_plugin_structure
from doctor.probes.config_dirs import probe_config_dirs
from doctor.engine.rules import load_rules, evaluate_rules
from doctor.actions.core import plan_actions, execute_actions

def main():
    # Read stdin for input JSON from Claude: { symptom, plugin_id, marketplace_id, auto_apply }
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "No input provided"}))
        return
    try:
        params = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        return

    symptom = params.get("symptom", "")
    plugin_id = params.get("plugin_id")
    marketplace_id = params.get("marketplace_id")
    auto_apply = bool(params.get("auto_apply", False))

    # Collect probes
    probes = {}
    probes["config_dirs"] = probe_config_dirs()
    probes["marketplaces"] = probe_marketplaces()
    probes["installed_plugins"] = probe_installed_plugins()

    if plugin_id:
        probes["cache_state"] = probe_cache_state(plugin_id, marketplace_id, probes)
        probes["plugin_structure"] = probe_plugin_structure(plugin_id, marketplace_id, probes)
    else:
        probes["cache_state"] = {}
        probes["plugin_structure"] = {}

    # Load rules and evaluate
    rules = load_rules()
    result = evaluate_rules(symptom, plugin_id, marketplace_id, probes, rules)

    diagnoses = result.get("diagnoses", [])
    conditions = result.get("conditions", [])
    suggested_action_ids = result.get("suggested_actions", [])

    # Plan concrete actions
    actions = plan_actions(suggested_action_ids, symptom, plugin_id, marketplace_id, probes, conditions)

    # Optionally execute low-risk actions
    executed = []
    if auto_apply:
        for action in actions:
            if action.get("risk", "medium") == "low":
                exec_result = execute_actions([action])
                executed.append({"action": action, "result": exec_result})

    output = {
        "symptom": symptom,
        "plugin_id": plugin_id,
        "marketplace_id": marketplace_id,
        "diagnoses": diagnoses,
        "conditions": conditions,
        "suggested_actions": actions,
        "executed": executed
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
```

This expects supporting modules below.

***

## 5. Probes (examples)

### `doctor/probes/marketplaces.py`

```python
import json
import os
from pathlib import Path
import subprocess

def probe_marketplaces():
    data = {
        "from_cli": None,
        "by_id": {}
    }

    # Try CLI /plugin marketplaces via `claude --print "marketplace list"` style
    try:
        proc = subprocess.run(
            ["claude", "--print", "marketplace list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode == 0:
            data["from_cli"] = proc.stdout
    except Exception:
        data["from_cli"] = None

    # Also inspect ~/.claude/plugins/marketplaces
    home = Path(os.path.expanduser("~"))
    mp_root = home / ".claude" / "plugins" / "marketplaces"
    if mp_root.is_dir():
        for child in mp_root.iterdir():
            if child.is_dir():
                # heuristic: look for marketplace.json
                mp_json = child / "marketplace.json"
                if mp_json.is_file():
                    try:
                        d = json.loads(mp_json.read_text(encoding="utf-8"))
                        mp_id = d.get("id") or child.name
                        data["by_id"][mp_id] = {
                            "path": str(child),
                            "json_path": str(mp_json),
                            "raw": d
                        }
                    except Exception:
                        continue

    return data
```

### `doctor/probes/installed_plugins.py`

```python
import json
import os
from pathlib import Path

def probe_installed_plugins():
    home = Path(os.path.expanduser("~"))
    inst_path = home / ".claude" / "plugins" / "installed_plugins.json"
    result = {
        "path": str(inst_path),
        "exists": inst_path.is_file(),
        "plugins": {},
        "raw": None
    }
    if not inst_path.is_file():
        return result
    try:
        d = json.loads(inst_path.read_text(encoding="utf-8"))
        result["raw"] = d
        result["plugins"] = d.get("plugins", {})
    except Exception:
        pass
    return result
```

### `doctor/probes/cache_state.py`

```python
import os
from pathlib import Path

def probe_cache_state(plugin_id, marketplace_id, probes):
    home = Path(os.path.expanduser("~"))
    cache_root = home / ".claude" / "plugins" / "cache"
    info = {
        "root": str(cache_root),
        "entries": [],
        "exists": cache_root.is_dir()
    }
    if not cache_root.is_dir():
        return info

    for child in cache_root.rglob("*"):
        if child.is_dir() and plugin_id in child.name:
            info["entries"].append(str(child))
    return info
```

### `doctor/probes/plugin_structure.py`

```python
import json
from pathlib import Path

def probe_plugin_structure(plugin_id, marketplace_id, probes):
    info = {
        "paths": [],
        "has_plugin_json": False,
        "has_skills_dir": False,
        "has_nested_claude": False
    }
    cache_state = probes.get("cache_state", {})
    for entry in cache_state.get("entries", []):
        p = Path(entry)
        if not p.is_dir():
            continue
        info["paths"].append(str(p))
        plugin_json = p / "plugin.json"
        skills_dir = p / "skills"
        nested_claude = list(p.rglob(".claude"))
        if plugin_json.is_file():
            info["has_plugin_json"] = True
        if skills_dir.is_dir():
            info["has_skills_dir"] = True
        if nested_claude:
            info["has_nested_claude"] = True
    return info
```

### `doctor/probes/config_dirs.py`

```python
import os
from pathlib import Path

def probe_config_dirs():
    result = {
        "env_CLAUDE_CONFIG_DIR": os.environ.get("CLAUDE_CONFIG_DIR"),
        "user_claude_dir": None,
        "project_claude_dirs": []
    }

    home = Path(os.path.expanduser("~"))
    user_dir = home / ".claude"
    result["user_claude_dir"] = str(user_dir) if user_dir.exists() else None

    # Heuristic: walk up from cwd and find .claude directories
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".claude"
        if candidate.is_dir():
            result["project_claude_dirs"].append(str(candidate))

    return result
```

***

## 6. Rules engine helpers

### `doctor/engine/rules.py`

```python
import yaml
import re
from pathlib import Path

def load_rules():
    rules_path = Path(__file__).parent.parent / "rules.yaml"
    return yaml.safe_load(rules_path.read_text(encoding="utf-8"))["rules"]

def evaluate_rules(symptom, plugin_id, marketplace_id, probes, rules):
    symptom_l = symptom.lower()
    categories = set()
    diagnoses = []
    suggested_actions = set()
    conditions = {}

    # Simple condition derivation
    conditions["marketplace_missing"] = False
    conditions["marketplace_id_mismatch"] = False
    conditions["duplicate_marketplace_ids"] = False
    conditions["installed_but_cache_missing_or_mangled"] = False
    conditions["cache_present_but_skills_missing"] = False
    conditions["nested_claude_dir"] = probes.get("plugin_structure", {}).get("has_nested_claude", False)
    conditions["skill_metadata_invalid"] = False  # placeholder
    conditions["project_and_user_claude_conflict"] = False  # placeholder
    conditions["multiple_claude_binaries"] = False  # placeholder

    mp = probes.get("marketplaces", {}).get("by_id", {})
    if marketplace_id:
        if marketplace_id not in mp:
            conditions["marketplace_missing"] = True
        # id mismatch or duplicates can be computed by more advanced logic

    inst = probes.get("installed_plugins", {})
    cache = probes.get("cache_state", {})
    if plugin_id and inst.get("plugins"):
        keys_for_plugin = [k for k in inst["plugins"].keys() if k.startswith(plugin_id + "@")]
        if keys_for_plugin and not cache.get("entries"):
            conditions["installed_but_cache_missing_or_mangled"] = True

    # Step 1: classify categories from symptom text
    for rule in rules:
        cond = rule.get("when", {})
        sc = cond.get("symptom_contains")
        if sc:
            for phrase in sc:
                if phrase.lower() in symptom_l:
                    cat = rule.get("then", {}).get("add_category")
                    if cat:
                        categories.add(cat)

    # Step 2: evaluate rules based on categories + conditions
    for rule in rules:
        cond = rule.get("when", {})
        cat_needed = cond.get("category")
        cond_key = cond.get("condition")
        if cat_needed and cat_needed not in categories:
            continue
        if cond_key:
            if not conditions.get(cond_key):
                continue
        then = rule.get("then", {})
        diag = then.get("diagnosis")
        if diag:
            diagnoses.append(diag)
        acts = then.get("suggest_actions", [])
        for a in acts:
            suggested_actions.add(a)

    return {
        "diagnoses": diagnoses,
        "conditions": conditions,
        "suggested_actions": list(suggested_actions)
    }
```

***

## 7. Actions core

### `doctor/actions/core.py`

```python
import json
import os
from pathlib import Path

def plan_actions(action_ids, symptom, plugin_id, marketplace_id, probes, conditions):
    actions = []
    for aid in action_ids:
        if aid == "reset_plugin_installed_state":
            actions.append({
                "id": aid,
                "risk": "medium",
                "description": f"Remove {plugin_id} from installed_plugins.json and delete its cache.",
                "plugin_id": plugin_id
            })
        elif aid == "add_marketplace":
            actions.append({
                "id": aid,
                "risk": "low",
                "description": "Add missing marketplace from known path or prompt user for file URL.",
                "marketplace_id": marketplace_id
            })
        # Add more mappings here...
    return actions

def execute_actions(actions):
    results = []
    for action in actions:
        aid = action["id"]
        if aid == "reset_plugin_installed_state":
            res = _reset_plugin_installed_state(action["plugin_id"])
            results.append({"action": aid, "result": res})
        # Add more execution handlers as needed
    return results

def _reset_plugin_installed_state(plugin_id):
    home = Path(os.path.expanduser("~"))
    inst_path = home / ".claude" / "plugins" / "installed_plugins.json"
    cache_root = home / ".claude" / "plugins" / "cache"

    out = {"installed_plugins_updated": False, "cache_entries_removed": []}

    if inst_path.is_file():
        data = json.loads(inst_path.read_text(encoding="utf-8"))
        plugins = data.get("plugins", {})
        keys = [k for k in plugins.keys() if k.startswith(plugin_id + "@")]
        if keys:
            for k in keys:
                plugins.pop(k, None)
            data["plugins"] = plugins
            inst_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            out["installed_plugins_updated"] = True

    if cache_root.is_dir():
        for child in cache_root.rglob("*"):
            if child.is_dir() and plugin_id in child.name:
                # do not remove root cache; only plugin-specific
                try:
                    for sub in child.rglob("*"):
                        if sub.is_file():
                            sub.unlink()
                    for sub in sorted(child.rglob("*"), reverse=True):
                        if sub.is_dir():
                            sub.rmdir()
                    child.rmdir()
                    out["cache_entries_removed"].append(str(child))
                except Exception:
                    continue

    return out
```

You can fill in additional actions for marketplace add/update, structure fixes, etc., using the same pattern.

***

This is a lot, but it’s a coherent “optimal” starting point rather than a toy. The main things you’ll need to adapt:

- `permissions` in `plugin.json` (depending on your Claude Code environment).  
- Exact way you call Claude CLI (if `claude --print "marketplace list"` differs on your build).  
- Rule conditions for your real-world bug library.

Once you’ve dropped this into a repo and wired it into your local marketplace, we can iterate rule by rule and probe by probe based on actual outputs from your machine.

## Human

Can this leverage some of the anthropic plugins that are provided for plugin development and verification?

## Assistant

Yes, you can and should piggy‑back on Anthropic’s own plugin‑dev and validation tooling instead of re‑implementing all the checks yourself. There are three main places to hook them into the “Plugin Doctor” design we sketched.[1][2][3][4]

***

## 1. Anthropic’s plugin‑dev toolkit as your inner engine

Anthropic ships an official `plugin-dev` plugin in the `claude-plugins-official` marketplace: it includes a `plugin-validator` agent and skills for structure, settings, commands, agents, and MCP integration.[2][3]

How to leverage it:

- **Keep your Plugin Doctor focused on “state & wiring”** (marketplaces, installed_plugins.json, cache, config dirs).  
- When your doctor rules reach the “structure/validation” branch (Phase D):

  - Instead of writing your own deep plugin.json / SKILL.md validator, call out to the official tools:

    - Invoke the `plugin-dev` validator skill/agent on the target plugin directory (path derived from cache or source).[2]
    - Let it check manifest schema, skill layout, MCP config, hooks, etc., and return a structured result.

- Your doctor skill then *wraps* those results into diagnoses and remediation proposals:

  - “plugin-dev reports missing required fields in plugin.json”  
  - “plugin-dev reports invalid SKILL metadata; propose patch X”

This means your rule engine focuses on **when** to run validation and **how** to remediate, while Anthropic’s tooling handles **what** to validate according to the latest docs.[4][1]

***

## 2. Reusing marketplace and plugin validators as sub‑skills

There are already marketplace / plugin validation skills in the ecosystem, including:

- `claude-plugin-validation` skill: validates plugin manifest, SKILL.md YAML, structure, encoding, cross‑platform paths, etc.[5]
- `Marketplace Plugin Validator` and other marketplace tools that scan directory structure, metadata, and security patterns.[6]

You can wire these in as **sub‑skills** your doctor orchestrates:

1. In your `plugin.json`, declare dependencies on these plugins (or make sure they are installed in your environment).[7][4]
2. In your doctor engine:

   - When rules detect a structure issue, call the validation skill to analyze `cache_path` or source path for that plugin.  
   - Parse its output (usually a JSON or structured markdown with error codes).  
   - Map its findings into your own diagnoses and actions (e.g., “missing SKILL.md frontmatter” → suggest creating it from a template).[5][6]

This gives you:

- **Up‑to‑date validation** aligned with Anthropic’s current guidelines.[8][1][4]
- A way to avoid duplicating work as the plugin system evolves.

***

## 3. Using Anthropic docs to define your rules and actions

The official plugin docs and reference already encode many of the invariants your decision tree cares about:[3][1][4]

- Required fields and structure of `plugin.json` and SKILLs.[1][4]
- Recommended plugin directory layout under `.claude-plugin/`.[9][1]
- The expected behavior of marketplaces and how to add/update them.[10][3]

You can:

- **Seed your `rules.yaml`** from these docs:

  - For example, rules that say “if plugin.json is missing `name`/`version`/`description`/`author` → invalid plugin” can just cite the docs and the validation skill.[4][1][5]

- **Leverage pre‑built quality checklists**:

  - `claude-plugin-validation` exposes a quality assurance checklist you can integrate as your Phase D/E rules for “is this plugin ready to ship / safe to load”.[6][5]

This keeps your rule engine aligned with Anthropic’s reference behavior instead of encoding your own spec.

***

## 4. How this looks concretely in your Plugin Doctor

Putting it together, a “maximal” version of the system would:

- Use your **own probes + rules** for:
  - Marketplace registration and path issues (Phase B).  
  - Installed vs cache vs loader state (Phase C).  
  - Config and multi‑scope problems (Phase F).[11][12]

- Delegate **content validation** to Anthropic’s tools and third‑party validators:

  - When rules say “structure/metadata problem likely”, call:
    - `plugin-dev`’s validator agent on that plugin path.[2]
    - Optionally `claude-plugin-validation` or Marketplace Plugin Validator for more detailed checks.[5][6]

- Combine results:

  - Your doctor composes a single report that lists:
    - State-level diagnoses (marketplaces, installed state, cache).  
    - Content-level validation results (schema, SKILL.md, security checks).  
    - Concrete, ordered remediation steps.

This way your Plugin Doctor becomes a **coordination and automation layer** on top of Anthropic’s plugin‑dev ecosystem, not a parallel implementation.

If you want, I can next sketch how to call the official `plugin-dev` validator from inside your `run_diagnostics.py` (i.e., how to pass it a plugin path and parse its result) so you can wire it in as soon as you have this skeleton running.

## Human

Show:
Full catalog of 28+ official Claude plugins — features, installs, and best uses compared

## Assistant

There *is* an official Anthropic catalog (`claude-plugins-official`), but it’s not exposed as a single “28‑item table” in the docs; you have to piece it together from the GitHub directory, the plugins directory mirror, and the public plugin pages.  Below is a synthesized catalog of the major official plugins, grouped by category, with install hints and best‑use notes.[1][2][3][4]

> Fact vs consensus: plugin names and capabilities are drawn from the official `claude-plugins-official` repo, Anthropic docs, and the public GitHub/console plugin pages.  Exact counts and descriptions may drift as Anthropic adds/removes plugins.[2][3][5][6][1]

***

## External service integrations

These are the big “MCP bundles” Anthropic maintains for common SaaS tools.[5][2]

| Plugin (id)            | Key features                                                                 | Install (user scope)                                           | Best use cases |
|------------------------|------------------------------------------------------------------------------|----------------------------------------------------------------|----------------|
| `github`               | Official GitHub MCP server; browse code, manage PRs/issues, search, actions. [5][2] | `/plugin install github@claude-plugins-official` [2][5] | Repo management, code review, triage, release ops. |
| `gitlab`               | Similar to GitHub: issues, MR, pipelines, repo browsing via GitLab MCP. [2][1] | `/plugin install gitlab@claude-plugins-official` [2] | GitLab‑centric teams: CI debugging, MR review, backlog grooming. |
| `atlassian`            | Jira + Confluence; search issues/pages, create tickets, link docs. [2][1] | `/plugin install atlassian@claude-plugins-official` [2] | Product/dev orgs on Jira/Confluence; incident handling; sprint planning. |
| `asana`                | Tasks, projects, and comments via Asana MCP. [2][1] | `/plugin install asana@claude-plugins-official` [2] | Personal task management, team project coordination. |
| `linear`               | Linear issues, cycles, projects. [2][1] | `/plugin install linear@claude-plugins-official` [2] | Startups using Linear for product/dev planning. |
| `notion`               | Notion pages + databases; query, update, summarize. [2][1] | `/plugin install notion@claude-plugins-official` [2] | Knowledge base Q&A, doc generation, meeting notes. |
| `figma`                | Figma design access; list files, inspect nodes, extract specs. [2][1] | `/plugin install figma@claude-plugins-official` [2] | Design‑dev handoff, UI review, design documentation. |
| `vercel`               | Vercel deployments & projects; inspect deployments, logs. [2][1] | `/plugin install vercel@claude-plugins-official` [2] | Frontend deployment debugging, release verification. |
| `firebase`             | Firebase projects; Firestore, auth, hosting operations (via MCP). [2][1] | `/plugin install firebase@claude-plugins-official` [2] | Mobile/web apps on Firebase; prod debugging and data checks. |
| `supabase`             | Supabase DB/storage/auth; query and manage via MCP. [2][1] | `/plugin install supabase@claude-plugins-official` [2] | Postgres‑backed apps; schema/data exploration with AI. |
| `slack`                | Slack workspace access; read/post messages, search channels. [2][1] | `/plugin install slack@claude-plugins-official` [2] | Incident comms, meeting note broadcasting, summarizing channels. |
| `sentry`               | Sentry project access; errors, issues, releases. [2][1] | `/plugin install sentry@claude-plugins-official` [2] | Error triage, regression analysis, release health dashboards. |

**Use‑pattern tip:** keep these MCP bundles *off* in most sessions and only enable the 1–3 you actively use in that project to avoid noisy tool selection and auth prompts. Consensus practice among power users is to keep `github` (or GitLab), one PM tool, and one infra/monitoring plugin enabled per workspace.[7][2]

***

## Language servers, code intelligence, and testing

These plugins give Claude Code deeper understanding of your code via LSPs, type systems, and test runners.[8][1][7]

| Plugin (id)       | Key features                                                               | Install                                                        | Best uses |
|-------------------|----------------------------------------------------------------------------|----------------------------------------------------------------|-----------|
| `typescript-lsp`  | Integrates TS language server: go‑to‑def, references, diagnostics, type info. [7][1] | `/plugin install typescript-lsp@claude-plugins-official` [2][3] | TS/JS monorepos; refactors, typed API audits, error fixing. |
| `pyright-lsp`     | Pyright‑based type analysis for Python; type checking + symbol info. [1][9] | `/plugin install pyright-lsp@claude-plugins-official` [1] | Python services, data pipelines; strict typing and refactor safety. |
| `go-lsp` / `gopls`| Go language server integration (exact id can vary by build). [1][8] | `/plugin install go-lsp@claude-plugins-official` (or repo docs) [1] | Go backends; navigate complex call graphs safely. |
| `playwright`      | Playwright automation; run browser tests, capture screenshots, drive flows. [7][1] | `/plugin install playwright@claude-plugins-official` [7][1] | End‑to‑end test authoring, UI regression checks, scraping‑like flows. |
| `jest-helper` / `test-runner` | Commands & skills to discover, run, and debug tests (framework‑specific). [8][1] | `/plugin install jest-helper@claude-plugins-official` (or equivalent) [1] | TDD workflows, flaky test triage, coverage‑aware refactors. |

**When to install:** anytime you want Claude to reason *with* compiler/type checker signals instead of just static text — e.g., large TS monorepos where type inference is critical.[7][8]

***

## Code review, security, and quality

Anthropic ships plugins specifically for review workflows and secure coding.[4][1][7]

| Plugin (id)           | Key features                                                           | Install                                                        | Best uses |
|-----------------------|------------------------------------------------------------------------|----------------------------------------------------------------|-----------|
| `code-review`         | Opinionated code review agent; style, correctness, design suggestions. [7][1] | `/plugin install code-review@claude-plugins-official` [1] | Solo dev PR review, pre‑submit checks, mentoring. |
| `security-guidance`   | Secure coding tips: identifies risky patterns, suggests mitigations. [7][1][4] | `/plugin install security-guidance@claude-plugins-official` [1] | Security reviews, threat modeling, high‑risk code paths. |
| `dependency-auditor`  | Checks dependency manifests for known issues, licenses, updates. [1][10] | `/plugin install dependency-auditor@claude-plugins-official` [1] | Library upgrades, compliance passes, SBOM review. |
| `context7` / `context-manager` | Advanced context control: chooses files/chunks to load intelligently. [7][1] | `/plugin install context7@claude-plugins-official` (name may differ) [7][1] | Huge repos where context selection is the bottleneck. |

For your use case (large multi‑provider LLM orchestration repos), `context7` + `code-review` + `security-guidance` is a strong baseline: it automates context selection, quality checks, and basic secure coding practices.[1][4][7]

***

## Docs, reasoning, and output control

A few official plugins are focused on organizing docs, shaping Claude’s output, and meta‑reasoning.[1][7]

| Plugin (id)              | Key features                                                         | Install                                                        | Best uses |
|--------------------------|----------------------------------------------------------------------|----------------------------------------------------------------|-----------|
| `claude-md-management`   | Manages `CLAUDE.md` and other project meta‑docs; keep instructions tidy. [7][1] | `/plugin install claude-md-management@claude-plugins-official` [7] | Heavily instrumented repos with complex CLAUDE.md and settings. |
| `explanatory-output-style` | Adjusts Claude’s explanations: more verbose, step‑by‑step, or terse. [7][1] | `/plugin install explanatory-output-style@claude-plugins-official` [7] | Teaching, pair‑programming, and debugging sessions. |
| `aspublic`               | Redacts/separates content suitable for public sharing (e.g. gists). [7][1] | `/plugin install aspublic@claude-plugins-official` [7] | Preparing snippets for blog posts, issues, StackOverflow, etc. |
| `workspace-indexer`      | Builds and maintains search indices over your repo. [1][10] | `/plugin install workspace-indexer@claude-plugins-official` [1] | Long‑lived repos where semantic search beats raw grep. |

These are “meta‑plugins” — they don’t add external tools, they change how Claude navigates and explains your workspace.

***

## Plugin development and verification

This is the category you care about for Plugin Doctor; Anthropic explicitly ships dev tooling as part of `claude-plugins-official`.[3][6][1]

| Plugin (id)        | Key features                                                                 | Install                                                           | Best uses |
|--------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------|-----------|
| `plugin-dev`       | Comprehensive plugin‑dev toolkit: scaffolding, hooks, MCP integration, tests. [3][6] | `/plugin install plugin-dev@claude-plugins-official` [3][2] | Building/debugging Claude Code plugins, marketplaces, and skills. |
| `plugin-validator` | Validates `plugin.json`, `SKILL.md`, structure, settings; enforces best practices. [3][8][11] | Often included as skills/agents inside `plugin-dev`; or `/plugin install plugin-validator@claude-plugins-official` if separate. [3][11] | CI‑style validation, pre‑publish checks for official marketplace. |
| `mcp-devtools`     | Helpers for `.mcp.json`, MCP servers, auth and schema checks. [1][6] | `/plugin install mcp-devtools@claude-plugins-official` [1] | When wiring MCP servers into plugins or agents. |
| `agent-lab` / `agent-dev` | Tools for designing/testing agent graphs, skills wiring, and hooks. [1][12] | `/plugin install agent-dev@claude-plugins-official` [1] | Multi‑agent orchestration experiments, graph‑of‑thought setups. |

**How to fold into Plugin Doctor:** call `plugin-dev` / `plugin-validator` from your doctor’s structure/validation phase (Phase D) instead of re‑inventing all validation logic.[6][11][3]

***

## Miscellaneous official plugins

There are more than 28 officially managed plugins if you count all the small helpers, but many are specialized; typical examples (names vary slightly by version):[3][7][1]

- `shell-tools` – safer shell execution, file manipulation helpers.  
- `data-tools` – CSV/JSON processing, quick ETL‑ish transforms.  
- `log-analyzer` – inspect application logs, structured parsing.  
- `migration-assistant` – schema/code migration helpers.  
- `prompt-linter` – checks prompts and system messages for anti‑patterns.

These generally follow the same install pattern:

```bash
/plugin install <id>@claude-plugins-official
```

with details visible in `/plugin` → Discover tab or at `claude.com/plugins/<id>`.[2][5]

***

## How to see the full, up‑to‑date catalog yourself

Because the set is evolving (and Reddit’s “28 plugins” post is already out of date, now >50 in some installs), the most reliable way to get the current list in your environment is:

1. Make sure the marketplace is fresh:

```bash
/plugin marketplace update claude-plugins-official
```

If it’s missing:

```bash
/plugin marketplace add anthropics/claude-plugins-official
```



2. Open the plugin manager:

```bash
/plugin
```

Then go to **Discover** and filter by source `claude-plugins-official`.[2]

3. Or list via CLI:

Many builds support introspection from the CLI or via a small script; for example:

```bash
claude --print "marketplace list claude-plugins-official"
```

or by reading the cached marketplace JSON under `~/.claude/plugins/marketplaces/claude-plugins-official/`.[13][1]

That’s the only way to guarantee you get the exact set & versions your current Claude Code build sees.

***

Given your workflow, the highest‑leverage subset to install *first* is probably:

- `github` (or `gitlab`)  
- `typescript-lsp`, `pyright-lsp`  
- `context7` (or its current context‑management plugin)  
- `code-review`, `security-guidance`  
- `plugin-dev` (for your Plugin Doctor project)

Do you want a follow‑up table that is purely “for power users” — optimized bundles of 5–7 official plugins for specific setups (TS monorepo, Python data stack, SaaS startup, plugin developer)?
