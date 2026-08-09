---
title: "Claude Code Video Editing Automation"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, video]
summary: >
  A method for automating video editing workflows using Claude Code to process raw footage into finished content with minimal human intervention, leveraging a folder-based system that monitors for new files and generates edited output.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8b807d28-b283-4de3-a369-4ff5e065ac92" (WL: Claude Code Repos & Tools, synced 2026-07-27)
  - "NotebookLM source 300f2770-ac18-488a-aa9f-3fdf90783e40" (Studio 2.9.0 Release AND Context Studio!, synced 2026-07-27)
  - "NotebookLM source 40639e57-f390-4b45-be9a-af7e71d260dc" (How I Fully Automated Video Editing (Claude Code), synced 2026-07-27)
  - "NotebookLM source 450045d2-0f2b-4d9e-b53f-353fdb50d841" (Claude Code Cut 20 Hours of Video Editing Down to Zero!, synced 2026-07-27)
  - "NotebookLM source 6d2de472-3204-4f01-a07b-261a4798cd0e" (Guard The Leaf Channel Update | My Channel Moving Forward, synced 2026-07-27)
  - "NotebookLM source 83fa46c1-52bc-4601-b492-730f41a9f0f5" (How I Fully Automated My Video Editing (Claude Code), synced 2026-07-27)
  - "NotebookLM source 936ef2e8-04db-42fe-ab3e-81b3de89fd02" (Make Claude code your video editor, synced 2026-07-27)
  - "NotebookLM source aca18095-75ff-4190-b22c-60adfb503be0" (How To: Edit Video with Claude Code, synced 2026-07-27)
  - "NotebookLM source b2152567-48be-45ce-9153-6191f71f0fe2" (How I Fully Automated My Video Editing (Claude Code), synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: claude-code-video-editing-automation
    - level: notebook
      id: 8b807d28-b283-4de3-a369-4ff5e065ac92
      title: WL: Claude Code Repos & Tools
      url: https://notebooklm.google.com/notebook/8b807d28-b283-4de3-a369-4ff5e065ac92
    - level: cluster
      id: 3
      name: video-claude-code
relations:
  - target: wiki/concepts/video-post-production-workflows.md
    type: related
  - target: wiki/concepts/ai-assisted-content-creation.md
    type: related
  - target: wiki/concepts/automated-media-asset-management.md
    type: related
---

# Claude Code Video Editing Automation

## Decision context

**Definition:** A method for automating video editing workflows using Claude Code to process raw footage into finished content with minimal human intervention, leveraging a folder-based system that monitors for new files and generates edited output.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *WL: Claude Code Repos & Tools*, clustered into the "video-claude-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Raw footage is placed in an input folder, and an automated routine scans for new files, processes them, and saves edited results to an output folder.
- Claude Code performs automated cuts by detecting and removing dead spaces, trimming unnecessary portions of footage.
- The system generates motion graphics and dynamic visuals to enhance video quality and engagement.
- Subtitles and captions are added automatically, with customizable styling including font, color, and branding elements.
- Audio analysis enables automatic insertion of sound effects that match the video content.
- Automatic B-roll generation creates supplementary footage that complements the main content.
- The Buttercut tool (available at buttercot.io) provides Claude Code skills for footage analysis and rough cut generation in YAML format, along with a Ruby library for converting outputs to Final Cut Pro XML and Adobe Premiere formats.
- The automated workflow reduces video editing time from 15-20 hours per week to effectively zero hours of manual work.
- Output can be configured for platform-specific formats including Instagram Reels, YouTube Shorts, and TikTok videos.

## Verifiable values

| Name | Value |
|---|---|
| Potential weekly time savings | `15 to 20 hours` |
| Editing cost per video | `over $200 (using traditional editors)` |
| Weeks to find suitable editor | `multiple weeks` |
| Automation software | `Claude Code with Buttercut extension` |

## Related concepts

- video-post-production-workflows — Video post-production workflows
- ai-assisted-content-creation — AI-assisted content creation
- automated-media-asset-management — Automated media asset management
- context-studio — Context Studio

## Citations (from contributing transcripts)

- **Claim:** The workflow uses a folder-based approach where raw video files are placed in an input directory and an automated routine processes them to an output folder.
  - Source: Claude Code Cut 20 Hours of Video Editing Down to Zero! (`450045d2-0f2b-4d9e-b53f-353fdb50d841`)
  - Context: we're just going to have a folder where you can dump all of your raw video files in every single morning we'll just have a routine that runs it'll look through that folder for any new additions it's going to edit all of the videos in there and then just save them to a new output folder
- **Claim:** Claude Code performs automated cuts by trimming out dead spaces and making precise editing decisions.
  - Source: How I Fully Automated Video Editing (Claude Code) (`40639e57-f390-4b45-be9a-af7e71d260dc`)
  - Context: it makes all the cuts it trims out all the dead space and it even adds really dope motion graphics
- **Claim:** The system adds customizable subtitles and captions with brand styling options.
  - Source: How I Fully Automated Video Editing (Claude Code) (`40639e57-f390-4b45-be9a-af7e71d260dc`)
  - Context: it does subtitles too like these at the bottom of the screen right here and this caption is my brand kit the font and color that I want
- **Claim:** Audio analysis enables automatic sound effect insertion and B-roll generation.
  - Source: How I Fully Automated Video Editing (Claude Code) (`40639e57-f390-4b45-be9a-af7e71d260dc`)
  - Context: CL code listens to your video and it will add sound effects for you automatically but if you want to go one step further Claude will actually generate automatic B-rolls for you that make sense for your video
- **Claim:** Buttercut provides Claude Code skills for analyzing footage and a Ruby library for generating Final Cut Pro and Adobe Premiere XML files.
  - Source: How To: Edit Video with Claude Code (`aca18095-75ff-4190-b22c-60adfb503be0`)
  - Context: Buttercut is basically two pieces it's a bunch of clawed code skills that you can use to analyze your footage and generate rough cuts in YAML form and then it's a Ruby library that can actually generate XML for Final Cut Pro and Adobe Premiere
- **Claim:** The automated workflow reduces editing time from 15-20 hours per week to zero.
  - Source: Claude Code Cut 20 Hours of Video Editing Down to Zero! (`450045d2-0f2b-4d9e-b53f-353fdb50d841`)
  - Context: if you're spending 15 to 20 hours a week editing your videos that's 15 to 20 hours that you're not spending making new content
- **Claim:** Output is configured for short-form video platforms.
  - Source: Claude Code Cut 20 Hours of Video Editing Down to Zero! (`450045d2-0f2b-4d9e-b53f-353fdb50d841`)
  - Context: edit it completely down into a ready to post clip for Instagram reels YouTube shorts or Tik Tok videos

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8b807d28-b283-4de3-a369-4ff5e065ac92`
(cluster `video-claude-code`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [WL: Claude Code Repos & Tools](https://notebooklm.google.com/notebook/8b807d28-b283-4de3-a369-4ff5e065ac92)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
