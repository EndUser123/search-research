---
title: "In obsidian, I'm trying to view the knowledge graph, but it keeps going to a blank screen."
date: "2026-04-09"
mode: "COPILOT"
uuid: "f7f8d74a-0e15-4f01-8636-2a032becfede"
entry_count: 6
---

## Human

In obsidian, I'm trying to view the knowledge graph, but it keeps going to a blank screen.

## Assistant

The blank knowledge graph screen in Obsidian is typically a GPU rendering issue, and the fix depends on your operating system. Here are the primary solutions, ordered by likelihood of success:

## Check graph filters first

Open the graph settings (gear icon at the top corner) and verify no filter is accidentally set that's hiding all nodes. This is sometimes introduced when importing templates.[1]

## Clear GPU cache (most common fix)

**Linux/Mac:** Delete the GPU cache folder, then restart Obsidian:[2]
- **Linux:** `~/.config/obsidian/GPUCache`
- **Mac:** `~/Library/Application Support/obsidian/GPUCache`
- **Windows:** Navigate to `AppData\Local\obsidian` and delete the `GPUCache` folder

After deletion, reopen Obsidian and the graph should render.[3]

## Disable and re-enable hardware acceleration

In Obsidian settings → About, toggle hardware acceleration off, test the graph, then toggle it back on. This temporarily works around GPU driver conflicts but isn't sustainable for large vaults since CPU-only rendering is resource-intensive.[3]

## Repair settings folder (nuclear option)

If caching doesn't work, close Obsidian and rename `~/.obsidian/settings` to `~/.obsidian/settings.backup`, then restart Obsidian to regenerate settings with defaults. You'll lose custom preferences but often fixes rendering bugs.[4]

## Root cause

This is fundamentally a GPU driver incompatibility with PixiJS, the rendering library Obsidian uses for graph visualization. It frequently occurs after OS or driver updates, particularly on Linux systems. Reinstalling Obsidian from the official site sometimes resolves it if your installed version is outdated.[5][2]

What operating system are you running, and have you recently updated your GPU drivers or OS?

## Human

I'm on windows 11 and I don't see a gear icon.

## Assistant

On Windows 11, the graph settings access differs slightly. Here are the correct approaches:

## Open graph settings via command palette

Press `Ctrl+P` to open the command palette, then search for "graph" and select "Open graph view". Once the graph view is open, look for a **three-dot menu icon (⋯)** or **settings icon** in the top-right corner of the graph panel itself, not the main window toolbar.[1]

## Alternative: Access via sidebar

Click the graph icon in the left sidebar (it looks like a network diagram). The graph panel will open at the bottom or side. The settings control should be in the top-right of that panel.

## Clear GPU cache on Windows 11 (primary fix)

Since you don't see settings controls, start with the GPU cache clear—this is the most common Windows fix for blank graph screens:

1. Close Obsidian completely
2. Open File Explorer and navigate to: `C:\Users\[YourUsername]\AppData\Local\obsidian`
3. Delete the `GPUCache` folder (AppData is hidden by default; enable "View → Hidden items" in File Explorer if needed)
4. Restart Obsidian

This should resolve the blank screen issue [][].

If the graph still doesn't appear after clearing cache, try disabling hardware acceleration: Settings → About → toggle "Hardware acceleration" off, restart Obsidian, check if the graph renders, then toggle it back on.

Does clearing the GPU cache resolve it, or is the graph still blank after restart?

## Human

That folder doesn't exist.

## Assistant

If the `GPUCache` folder doesn't exist, the issue is likely different. Let's diagnose further.

## Verify the graph view is actually opening

First, confirm the graph view itself is loading:

1. Press `Ctrl+P` (command palette)
2. Type "graph" and select "Open graph view"
3. Does a panel open at all, or does it remain completely blank/black?

If nothing opens or it's entirely black, this points to a rendering initialization failure rather than a cache issue.

## Check your vault structure

A truly blank graph can also occur if:
- Your vault has **no notes yet** (graph needs at least one file to render)
- All notes are in a folder that's somehow excluded from the graph
- Your vault path contains special characters that break the rendering

Create a simple test note (`Test.md` with some content) in the root of your vault and reopen the graph to see if it appears.

## Verify Obsidian version and reinstall if needed

An outdated or corrupted Obsidian installation can cause rendering failures:

1. Check Settings → About for your current version
2. Visit [obsidian.md](https://obsidian.md) and download the latest Windows installer
3. Close Obsidian, run the installer, and restart

## Check for plugin interference

Disable all community plugins temporarily:
1. Settings → Community plugins → Disable all
2. Reopen the graph view

If the graph appears after disabling plugins, re-enable them one by one to identify the culprit.

What happens when you open the graph view—does any panel appear at all, or is it completely unresponsive?

## Human

The GraphView starts to open and then it says something about indexing and then the whole screen, well the whole window goes blank and then you can't even close the window because there's no X button.

## Assistant

This is a critical indexing crash—the graph view is triggering an infinite loop or hang during vault indexing, freezing the entire window. This is a known issue with Obsidian on Windows 11 when the vault has structural problems or indexing corruption.

## Force close and rebuild index

1. **Force close Obsidian:** Press `Alt+F4` or use Task Manager (`Ctrl+Shift+Esc`) to kill the Obsidian process
2. **Delete the index cache:** Navigate to `C:\Users\[YourUsername]\.obsidian` (the dot folder is hidden—enable "View → Hidden items" in File Explorer)
3. Inside `.obsidian`, delete the `cache.json` file (this forces Obsidian to rebuild its index from scratch)
4. Restart Obsidian and **wait for indexing to complete** before opening graph view—watch the bottom-left status bar for "Indexing complete"

## If that fails: reset vault metadata

If the crash persists:

1. Close Obsidian
2. In `C:\Users\[YourUsername]\.obsidian`, rename the entire folder to `.obsidian.backup`
3. Restart Obsidian—it will regenerate `.obsidian` with fresh settings and caches
4. Wait for full indexing, then test the graph view

**Warning:** This resets all Obsidian settings, themes, and plugin configurations to defaults, but preserves your actual notes.

## Nuclear option: Check for corrupted notes

If indexing still hangs, a specific note file may be corrupted:

1. Close Obsidian
2. Move all `.md` files temporarily to a backup folder (outside the vault)
3. Restart Obsidian—indexing should be instant with no files
4. Test graph (it will be empty but should load)
5. If graph loads, move files back **one folder at a time** and retest to isolate the problematic note

The indexing hang suggests either vault corruption or a note with malformed YAML frontmatter that breaks the parser.[1][2]

Try deleting `cache.json` first and report back—does Obsidian index successfully this time, or does it still hang when you open graph view?

## Human

when I open obsidian it opens the workspace.  I navigated away from the graph, and after a second or two it still went to a blank window.

## Assistant

This changes the diagnosis significantly—the crash is happening **automatically in the background**, not just when you manually open graph view. This indicates Obsidian is trying to render the graph view in a cached workspace pane even though you've navigated away from it.

## Disable graph view in workspace layout

The graph view is persisting in your saved workspace and auto-loading:

1. **Force close Obsidian** (`Alt+F4` or Task Manager)
2. Navigate to `C:\Users\[YourUsername]\.obsidian` (enable hidden files if needed)
3. Open `workspace.json` in a text editor (Notepad or VS Code)
4. Search for `"type": "graph"` 
5. Delete the entire graph pane object (usually looks like a large block containing graph settings)
6. Save the file
7. Restart Obsidian

This removes the graph view from your saved workspace layout so it won't auto-load on startup.

## Alternative: Reset workspace completely

If editing `workspace.json` seems risky, close Obsidian and rename `workspace.json` to `workspace.json.backup`. Obsidian will generate a fresh workspace on restart with default panes only.

## Verify indexing completes

After either fix, watch the bottom-left status bar when Obsidian opens—confirm "Indexing complete" appears before attempting anything else. If indexing hangs or the window goes blank anyway, the issue is vault corruption (cache corruption or malformed note), not the workspace layout.

After fixing the workspace, does Obsidian stay responsive and not crash to a blank screen?

## Human

This is what is says, this is the version that blank windows:
"{
  "main": {
    "id": "b7a4279cd2eb0a27",
    "type": "split",
    "children": [
      {
        "id": "4c63766654680e16",
        "type": "tabs",
        "children": [
          {
            "id": "aaeca2b75b450158",
            "type": "leaf",
            "state": {
              "type": "markdown",
              "state": {
                "file": "2026-04-09.md",
                "mode": "source",
                "source": false
              },
              "icon": "lucide-file",
              "title": "2026-04-09"
            }
          }
        ]
      }
    ],
    "direction": "vertical"
  },
  "left": {
    "id": "71553ea140309acb",
    "type": "split",
    "children": [
      {
        "id": "45dba5d67326b8e5",
        "type": "tabs",
        "children": [
          {
            "id": "fd85c77a110a6513",
            "type": "leaf",
            "state": {
              "type": "file-explorer",
              "state": {
                "sortOrder": "alphabetical",
                "autoReveal": false
              },
              "icon": "lucide-folder-closed",
              "title": "Files"
            }
          },
          {
            "id": "4163fa32d480884b",
            "type": "leaf",
            "state": {
              "type": "search",
              "state": {
                "query": "",
                "matchingCase": false,
                "explainSearch": false,
                "collapseAll": false,
                "extraContext": false,
                "sortOrder": "alphabetical"
              },
              "icon": "lucide-search",
              "title": "Search"
            }
          },
          {
            "id": "6a9e2e839bc4f312",
            "type": "leaf",
            "state": {
              "type": "bookmarks",
              "state": {},
              "icon": "lucide-bookmark",
              "title": "Bookmarks"
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 300
  },
  "right": {
    "id": "b52137f2db25e158",
    "type": "split",
    "children": [
      {
        "id": "dd9800b82cca2862",
        "type": "tabs",
        "children": [
          {
            "id": "e3e74ec471333b54",
            "type": "leaf",
            "state": {
              "type": "backlink",
              "state": {
                "collapseAll": false,
                "extraContext": false,
                "sortOrder": "alphabetical",
                "showSearch": false,
                "searchQuery": "",
                "backlinkCollapsed": false,
                "unlinkedCollapsed": true
              },
              "icon": "links-coming-in",
              "title": "Backlinks"
            }
          },
          {
            "id": "583ac12f74e4f699",
            "type": "leaf",
            "state": {
              "type": "outgoing-link",
              "state": {
                "linksCollapsed": false,
                "unlinkedCollapsed": true
              },
              "icon": "links-going-out",
              "title": "Outgoing links"
            }
          },
          {
            "id": "5aef3aac3a160311",
            "type": "leaf",
            "state": {
              "type": "tag",
              "state": {
                "sortOrder": "frequency",
                "useHierarchy": true,
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-tags",
              "title": "Tags"
            }
          },
          {
            "id": "90121bfbd89cdb89",
            "type": "leaf",
            "state": {
              "type": "all-properties",
              "state": {
                "sortOrder": "frequency",
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-archive",
              "title": "All properties"
            }
          },
          {
            "id": "51b94b543dfffb01",
            "type": "leaf",
            "state": {
              "type": "outline",
              "state": {
                "followCursor": false,
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-list",
              "title": "Outline"
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 300,
    "collapsed": true
  },
  "left-ribbon": {
    "hiddenItems": {
      "switcher:Open quick switcher": false,
      "graph:Open graph view": false,
      "canvas:Create new canvas": false,
      "daily-notes:Open today's daily note": false,
      "templates:Insert template": false,
      "command-palette:Open command palette": false,
      "bases:Create new base": false
    }
  },
  "active": "aaeca2b75b450158",
  "lastOpenFiles": [
    "2026-04-09.md",
    "wiki/concepts/you-can-see-that-I-keep-asking-the-LLM-for-what-ca.md",
    "wiki/concepts/You-can-see-from-this-chat-that-when-the-LLM-imple.md",
    "wiki/concepts/You-can-see-from-this-chat-that-when-the-LLM-imple-(2).md",
    "wiki/concepts/You-can-see-from-this-chat-that-when-the-LLM-imple-(1).md",
    "wiki/concepts/Which-plan-is-better__LLM_1___Here-is-a-draft-plan.md",
    "wiki/concepts/Which-plan-is-better__LLM_1___Here-is-a-draft-plan-(1).md",
    "wiki/concepts/whats-the-optimal-workflow-for-coding_-explore,.md",
    "wiki/concepts/What-repos-implment-the-ideas-in-this-chat-history.md",
    "wiki/concepts/What-repos-implment-the-ideas-in-this-chat-history-(1).md",
    "wiki/concepts/what-repos-for-claude-code-support-this-solution-d.md",
    "wiki/investigations/what-problems-and-opportunities-do-you-see-in-this.md",
    "wiki/investigations/what-problems-and-opportunities-do-you-see-in-this-(1).md",
    "wiki/investigations/What-problem-is-being-shown-in-the-chat-history,-a.md",
    "wiki/investigations/What-problem-is-being-shown-in-the-chat-history,-a-(2).md",
    "wiki/investigations/What-problem-is-being-shown-in-the-chat-history,-a-(1).md",
    "wiki/entities/What-is-_-remember-claude-plugins-official.md",
    "wiki/concepts/What-domains-are-being-expressed-in-these-decompos.md",
    "wiki/concepts/What-do-you-think-the-optimal-solution-to-the-demo.md",
    "wiki/investigations/What-do-you-think-about-this___-Problem-Descripti.md",
    "wiki/concepts/what-are-the-current-gemini-rate-limits-per-day-fo.md",
    "wiki/concepts/what-are-the-current-gemini-rate-limits-per-day-fo-(2).md",
    "wiki/concepts/please-make-a-clickable-url-list-for-all-the-video.md",
    "wiki/concepts/Please-look-up-github-repos-for-claude-code-for-ra.md",
    "wiki/concepts/Please-look-at-the-review-bundle-and-analyze-the-p.md",
    "wiki/concepts/please-create-your-improved-version-of-the-operati.RESTORED_DRAFT.md",
    "wiki/investigations"
  ]
}"

## Assistant

Good news—this workspace file looks **completely normal** with no graph view panes. The blank screen crash is happening for a different reason.

The issue is likely **vault indexing corruption** combined with your vault size. Your `lastOpenFiles` shows you have a large wiki structure with many nested notes. When Obsidian tries to rebuild the index on startup (especially after the previous crash), it's hitting a parsing error on one of those files.

## Immediate fix: Rebuild the index from scratch

1. **Close Obsidian completely** (`Alt+F4`)
2. Navigate to `C:\Users\[YourUsername]\.obsidian`
3. Delete **only** `cache.json` (not the entire folder)
4. Restart Obsidian
5. **Wait at least 2-3 minutes** without interacting—let indexing complete fully. Watch the status bar at bottom-left for "Indexing complete"

If it still crashes during indexing, a specific note file is corrupted.

## If indexing still hangs/crashes:

Isolate the corrupted file:

1. Close Obsidian
2. Move `wiki/concepts` folder to a temporary backup location outside your vault
3. Restart Obsidian—indexing should be instant now
4. If it stays stable, move the folder back **one subfolder at a time** (or individual files) to find which one breaks it

Once you identify the problematic `.md` file, open it in Notepad and check for:
- Malformed YAML frontmatter (unclosed quotes, missing colons)
- Null bytes or corruption
- Invalid characters in the filename itself

The blank window crash during indexing is always vault corruption, not a workspace layout issue. Your workspace.json is clean.

Does Obsidian stay responsive after clearing cache.json and waiting for indexing to complete?
