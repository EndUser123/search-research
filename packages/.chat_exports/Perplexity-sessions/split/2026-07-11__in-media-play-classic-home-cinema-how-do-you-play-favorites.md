---
title: "in media play classic home cinema, how do you play favorites?"
date: "2026-07-11"
mode: "COPILOT"
uuid: "ba43db2d-b681-43cd-a671-3abaf9841615"
entry_count: 1
---

## Human

in media play classic home cinema, how do you play favorites?

## Assistant

You play favorites in Media Player Classic Home Cinema (MPC‑HC) from the main menu: once you’ve added items as favorites, you access them via the Favorites menu and click the entry you want to start playback.[1][2]

## What “favorites” are in MPC‑HC

In MPC‑HC, “Favorites” are saved references to either complete files or specific timestamps inside a file (bookmarks).[2][3]
They are stored either in the registry under `HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files` or in `MPlayerC.ini` if you use portable mode with “Store settings to .ini file” enabled.[4][5][2]

## Adding something to favorites

To be able to play favorites, you must first add them:

- Open a video or audio file in MPC‑HC.[6][3]
- Use the menu option to add to favorites: typically `Navigate → Favorites → Add to Favorites` for the current file, or “Add to favorites” for a specific position if you’re using bookmarks. The UI wording can vary by build, but it’s under the Navigate/Favorites menu.[7][1]

For bookmarks at specific times, MPC‑HC stores the time offset so choosing the favorite later will seek to that moment in the file.[2]

## Playing favorites (files or bookmarked points)

Once you have favorites defined:

- Open MPC‑HC with no file or any file loaded.[6]
- Go to the menu bar and choose `Navigate → Favorites`, or the `Favorites` menu, then click the desired favorite entry; MPC‑HC will (re)load the file and jump to the saved time if it’s a bookmark.[1][2]

One quirk reported by users is that selecting a favorite will reload the video even if that same file is already playing, because the favorite acts as a “load + seek” operation.[1][2]

## Where favorites live (for backup/transfer)

If you’re also interested in moving favorites between machines or installs:

- Normal install (settings in registry): favorites are under `HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Favorites\Files`. You can export that key and import it on another machine.[5][4][2]
- Portable install (`Store settings to .ini file`): favorites are in the `[Favorites]` section of `MPlayerC.ini` in the MPC‑HC directory. Copying that file carries your favorites with it.[4][5]

Are you trying to play simple file favorites, or timestamp bookmarks inside long videos (e.g., scenes/chapters)?
