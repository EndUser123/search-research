# SPECS.md

Canonical specifications for yt-fts implementation. All code generation and modification must reference these specs.

## Display Format Specifications

### Batch Download Channel Display Template

**Canonical format:**
```
N. * CHANNEL_NAME [index/total]
   ⎿ db: X total | Y cc, Z no cc | W pl | V subs
   ⎿ RSS: status message
   ⎿ yt-api: status message
   ⎿ yt-dlp: status message
   ⎿ net: final result
```

**Rules:**
- Prefix: `⎿` (U+23BF, LEFT WHITE CORNER BRACKET) - NOT `-`
- Indent: 3 spaces before `⎿`
- Service names: Capitalized (RSS, yt-api, yt-dlp, net, whisper)
- Format: `   ⎿ SERVICE: message`

**Database Stats Format:**
```
   ⎿ db: X total | Y cc, Z no cc | W pl | V subs
```
- `X total` - Total videos in database for this channel
- `Y cc` - Videos with closed captions/subtitles
- `Z no cc` - Videos without subtitles
- `W pl` - Playlist count (when available)
- `V subs` - Subtitle entries in database

**Status Line Examples:**
- `   ⎿ RSS: 0 new video(s) found`
- `   ⎿ RSS: new channel, switching to yt-api for full scan`
- `   ⎿ yt-api: ✓ 50 videos metadata updated`
- `   ⎿ yt-dlp: fetching playlist metadata...`
- `   ⎿ net: + 142 new | took 2.3m`
- `   ⎿ net: all videos already in database`

**Do NOT:**
- Use `-` (dash) as status prefix
- Normalize `⎿` to ASCII in output functions
- Use lowercase service names (rss, yt-api, net)
- Add extra spaces or alter the indent pattern

See ARCHITECTURE.md "Batch Download Channel Display Template" for full documentation with examples.

## CHANGELOG Entry Format

When adding entries to CHANGELOG.md:
1. Use `[Unreleased]` for work in progress
2. Use `[VERSION] - YYYY-MM-DD` format for releases
3. Sections: Added, Changed, Deprecated, Removed, Fixed, Security
4. Format bullets as: `**Component**: Description`
5. Reference relevant specs when format-changing
6. Group related changes under sub-bullets with `-` prefix

**Example:**
```markdown
## [1.10.8] - 2026-01-19
### Added
- **Display Format**: Channel block output now uses ⎿ prefix
  - Changed from `-` to `⎿` (U+23BF) for status lines
  - Capitalized service names: RSS, yt-api, yt-dlp, net
  - See SPECS.md "Display Format Specifications"
```

## Code Generation Requirements

When generating display-related code:
1. Read SPECS.md "Display Format Specifications" first
2. Use `⎿` not `-` for status prefixes
3. Match the exact format shown above
4. DO NOT normalize `⎿` to ASCII in any output function
5. DO NOT add `⎿: "-"` to character replacement mappings

## Related Documentation

- ARCHITECTURE.md - System design, data flows, technical decisions
- PRD.md - Product requirements, roadmap
- README.md - User guide, installation, features
- CHANGELOG.md - Version history
