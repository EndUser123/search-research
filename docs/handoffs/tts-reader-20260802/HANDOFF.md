---
thread_id: tts-reader-20260802
parent_handoff_path: none
current_session_id: 019fbf77-8fe7-7070-bccd-e12f5d1807d8
current_terminal_id: grok
produced_at: 2026-08-02T19:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 89fc5af3995f4dba448be0280eefa44248875358
---

# Handoff: Local TTS Reader (Parler-TTS)

## Objective

Local text-to-speech reading tool for PDFs and text files with voice selection and emotion control, running fully offline with no cloud calls. Installed and working but has follow-up opportunities.

## Status
OPEN — tool works, follow-up items are enhancement opportunities

## What's done

- Parler-TTS installed in Python 3.12 venv at `P:/packages/tts-reader/venv/`
- `speak.py` — text/PDF reader with 34 named voices, 8 emotions, custom voice descriptions
- `sample_voices.py` — batch voice sample generator
- `speak.cmd` shortcut on PATH at `P:/scripts/speak.cmd`
- 8 voice samples generated at `P:/packages/tts-reader/samples/`
- Tested end-to-end: 4.3s audio generated in 5s on RTX 5070
- Wiki concept: `P:/.data/wiki/concepts/private-uncensored-text-to-speech.md` (28+ TTS models profiled)
- /www ledger: `P:/.data/www-ledger/private-uncensored-text-to-speech.md`

**Usage:** `speak "file.txt" --voice jon --emotion excited --output output.wav`

## What's open

### Enhancement: emotion quality comparison
The 8 emotion presets (excited, calm, sad, angry, whispering, husky, breathy, neutral) are text-description-based. Quality varies. A systematic comparison (generate same text with all 8 emotions, listen-test) would help users pick.

### Enhancement: PDF reading quality
Long-form narration has known pronunciation issues with Kokoro (espeak-ng phoneme fix needed). Parler-TTS has similar issues with unusual words. A text-normalization pre-processing step (expand abbreviations, handle numbers) would improve quality.

### Enhancement: voice cloning
Parler-TTS doesn't support voice cloning. If cloning is needed, the wiki research identified Qwen3-TTS (3s cloning, Apache 2.0) and OpenVoice v2 (1-5s, MIT) as the best options. Would need separate installation.

### Enhancement: audiobook export
Currently outputs WAV. MP3/M4B with chapter markers (for audiobook use) would require ffmpeg post-processing.

## Key files

- `P:/packages/tts-reader/speak.py` — main script
- `P:/packages/tts-reader/sample_voices.py` — voice sampler
- `P:/packages/tts-reader/venv/` — Python 3.12 venv (NOT system Python 3.14 — tokenizers build fails on 3.14)
- `P:/scripts/speak.cmd` — PATH shortcut
- `C:/Users/brsth/.grok/skills/model-quota/scripts/fleet_quota.py` — Perplexity quota (unrelated but committed in same session)

## Read-first list

- `P:/.data/wiki/concepts/private-uncensored-text-to-speech.md` — TTS model research (28+ models, license tiers, voice cloning capabilities)
- `P:/.data/wiki/concepts/tool-fallbacks.md` — now includes `speak` as local TTS tool

## Dependencies

- **Requires:** nothing — tool is installed and working
- **Blocks:** nothing
- **Non-blocking to:** epistemic knowledge system, tool-failure lifecycle

## Falsifier

This handoff is obsolete if Parler-TTS is superseded by a better model or if the operator switches to a different TTS engine (Kokoro, Qwen3-TTS, etc.). The wiki concept documents alternatives.
