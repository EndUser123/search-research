---
title: "for stash app how can we auto tag?"
date: "2026-02-10"
mode: "CONCISE"
uuid: "ac2f46e0-4d2a-4cc2-a8b8-210bccd0d844"
entry_count: 4
---

## Human

for stash app how can we auto tag?

## Assistant

Stash app provides an Auto Tag task to automatically assign existing performers, studios, and tags to scenes, images, and galleries based on filename or filepath matches.[1]

## How It Works
Auto Tag matches multi-word names (case-insensitive) using separators like dots, hyphens, underscores, or spaces as word boundaries, but only for items already in your database—it doesn't create new ones.  
For example, "Jane.Doe.mp4" or "Jane-Doe_n.mp4" would tag "Jane Doe" if she exists, but "Maryjane-Doe.mp4" (no separator) or misspellings won't match.  
Flags like "Organized" (on media) or "Ignore Auto Tag" (on performers/tags) skip processing.

## Running Auto Tag
Access Tasks from Settings (enable advanced mode first), then run full-library Auto Tag or select directories.  
From performer/studio/tag pages, trigger selective tagging for related media.  
Pre-populate your database via scrapers or manual entry for best results.[1]

## Human

How to install and use Stash AI Tagger Plugin

## Assistant

Stash's AI Tagger plugin enables batch tagging of scenes and images using local AI models via Skier's nsfw_ai_model_server.[1][2]
It requires Python in your Stash environment and a running AI server beforehand.

## Prerequisites
Install and run Skier's nsfw_ai_model_server first (see its quickstart guide).[1]
Ensure Python matches your Stash setup (native, Docker, or venv).  
Register scenes/images in Stash with the "AI_TagMe" tag to queue them for processing.

## Installation Steps
In Stash, go to **Settings > Plugins > Available Plugins > Community (stable)**, search "AI Tagger", and install.[1]
Run **Tasks > AI Tagger > Tag Scenes** (twice) to install dependencies and create tags like AI_Tagged/AI_Errored.  
For Docker: Create a venv outside Docker, pip install requirements.txt from the plugin dir, set **Settings > System > Python Executable Path** to the venv's python, and reload plugins.

## Usage
Mark items with "AI_TagMe" tag, then run **Tasks > AI Tagger > Tag Scenes** or **Tag Images**.[1]
Success adds "AI_Tagged" plus AI-suggested tags; errors get "AI_Errored".  
Customize via config.py in `<stash-dir>/plugins/community/ai_tagger` for frame intervals or server paths.

## Human

if I select some videos or images, how can export the list so I can use it in an external player?

## Assistant

Stash lacks a built-in direct export for selected scenes or images to M3U playlists for external players, but you can use Groups for videos or the Stash Helper tool as workarounds.[1][2]

## For Videos (Scenes)
Create a Group: Select scenes, click **... > Create Group from Selection**, reorder via scene numbers or content order, then play externally via **Open With > VLC/MPV** (per scene) or use built-in player middle-click for playlists (Ctrl+middle-click adds).[3][4]
For full M3U export, use the third-party Stash Helper (GitHub: philpw99/Stash_Helper): Select/filter scenes, generate/save as .m3u with file paths, load in VLC or similar.[2]

## For Images/Galleries
No native list export; save individual images via **File > Save As** or use browser dev tools/extensions to batch-download selected thumbs/full-res from grid view.[5]
For organized lists, export gallery metadata (Performers/Galleries tabs > Export), but it yields JSON/ZIP—not player-ready.[6]

## Human

I'm on the scene tab, I selected all, but I don't see where to create group.

## Assistant

On the current Stash UI you don’t get a “Create group from selection” button directly on the Scenes tab; groups are created/managed from the Groups page and via the scene edit panel instead.[1][2]

## How to put selected scenes into a group
1. With your filter/selection active on Scenes, bulk‑edit them using the top toolbar’s **Edit** button, then in the edit dialog use the **Groups** field to add them to an existing or new group, and apply.[3]
2. Alternatively, open the **Groups** tab, create a new group with **New Group**, then edit that group and add scenes from there using the **Scenes** sub‑view and filters.[4][2]

This effectively gives you a playlist-like grouping, but the action is routed through bulk edit or the Groups page rather than a “create from selection” button on the scene grid.
