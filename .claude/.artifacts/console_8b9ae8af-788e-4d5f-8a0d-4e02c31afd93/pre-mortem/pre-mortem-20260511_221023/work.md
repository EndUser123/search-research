Enhance /wiki SKILL.md v1.3.0 for YouTube transcript ingestion:
- YouTube URL auto-detection (youtube.com/@, youtube.com/channel, youtu.be, youtube.com/watch)
- yt-is pipeline: csf-source add (if new) -> csf-source fetch (yt-dlp -> Selenium escalation)
- Gemini CLI failover when transcripts.sqlite shows no_transcript
- Pre-phase manifest script with --source yt-is flag targeting transcript files
- Enhanced subagent prompt: pillar_scores (4x1-5), cognitive_load, EVIDENCE_GAP flags, verbatim extraction
- One wiki page per video (Option A per user decision)
- URL handler: YouTube -> csf-source -> manifest -> subagents -> QMD
- Non-YouTube URLs -> /crawl (unchanged)
Target: P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/SKILL.md