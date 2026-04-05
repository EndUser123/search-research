# ADR-20260326-intelligence-stream-gemini-url-passthrough

**Status:** Accepted
**Date:** 2026-03-26
**Context:** Redesign `csf-analyze` to pass YouTube URLs directly to Gemini 3.1 via `google.genai` SDK `Part.from_uri()`, replacing the broken Phase 1 approach of reading local text files as prompts to the `gemini` CLI subprocess.

---

### Decision

Replace the `subprocess.run(["gemini", "-p", ...])` pattern in `bin/csf-analyze` with the `google.genai` Python SDK, using `Part.from_uri(file_uri=yt_url, mime_type="video/mp4")` to pass YouTube URLs directly to Gemini for analysis.

---

### Rationale

The Phase 1 `csf-analyze` implementation (bin/csf-analyze:17-66) reads a local `.mp4` path, extracts text content, sends it as a prompt to the `gemini` CLI subprocess, then double-parses the JSON response. This is architecturally wrong — it does not let Gemini consume the YouTube URL directly.

The user explicitly specified: "We're supposed to [let Gemini 3.1 consume YouTube directly]. I told you that's what I wanted."

The correct approach uses the `google.genai` SDK `Part.from_uri()` method which passes the YouTube URL directly to Gemini's video understanding endpoint. Gemini fetches the video content server-side, avoiding local file downloads entirely for public videos.

---

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | `google.genai` SDK + `Part.from_uri()` | Direct URL passthrough, no local downloads, server-side fetch | Preview-only (8hr/day free tier), public videos only | N/A |
| Alt A | Keep `gemini` CLI + text extraction from local files | Works today, no new dep | Does NOT do URL passthrough — fundamentally wrong per user intent | Violates user requirement |
| Alt B | `gemini` CLI with `--video-url` flag | No SDK dependency | No such flag exists in current `gemini` CLI | Doesn't exist |
| Alt C | yt-dlp download → local file → SDK `Part.from_data()` | Works for private/unavailable videos | Downloads video files, slower, more storage | Trade-off for private videos — fallback, not primary path |

---

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| **Correctness** | Gemini gets raw video content via URL passthrough, not degraded text transcript | None |
| **Performance Efficiency** | No local file I/O, no transcript extraction step | API latency depends on video length |
| **Reliability** | Single API call with structured SDK | Requires internet connectivity to Google's servers |
| **Maintainability** | Replaces 30-line subprocess + JSON-parse hack with 10-line SDK call | New dependency (`google-genai`) |
| **Availability** | Preview free tier (8hr/day) — sufficient for solo dev | Rate limiting on free tier |

---

### Multi-Terminal Safety

- **Safe**: Each terminal runs `csf-analyze` independently. No shared state is written by the analyze step — output goes to terminal-isolated `.logs/analyses/{video_id}_{tid}.json` via `resolve_tid()`.
- CKS ingest (via `append_to_cks()`) uses `get_cks()` context manager which handles multi-terminal isolation at the CKS layer.
- **No shared mutable files** introduced by this change.

---

### Edge Case Considerations

- **Private/unavailable videos**: Gemini URL passthrough fails with `400 InvalidArgument` for private or region-locked videos. **Mitigation**: Catch `google.api_core.exceptions.InvalidArgument`, fall back to `csf-ingest` download + `Part.from_data()` with local file. Log via `log_action("analysis_url_fallback", {"video_id": video_id})`.
- **Free tier rate limit**: 8hr/day on URL passthrough. **Mitigation**: Track usage; if quota exhausted, fall back to `csf-ingest` path or wait. Log via `log_action("analysis_quota_exhausted", {"video_id": video_id})`.
- **Non-YouTube URLs**: `Part.from_uri()` accepts any direct media URL. **Behavior**: Accept any URL, delegate to Gemini's server-side fetch. Validate URL scheme (`http`/`https`) before calling SDK.
- **Video duration**: Very long videos may exceed Gemini's context window. **Behavior**: Gemini returns truncated analysis. No mitigation — inherent API limitation.
- **API key**: `google.genai` SDK reads `GOOGLE_API_KEY` env var. **Requirement**: User must have `GOOGLE_API_KEY` set in environment.
- **Concurrent terminals**: Independent API calls per terminal, no shared state. Safe.
- **Process crash mid-operation**: Analysis output written atomically to `.logs/analyses/` after successful API call. No partial state.

---

### Implementation

#### Contract: `analyze_video(video_id: str, video_url: str) -> dict`

```python
from google import genai
from google.genai.types import Part
from google.api_core.exceptions import InvalidArgument

def analyze_video(video_id: str, video_url: str) -> dict:
    """Analyze a video by URL using Gemini 3.1 URL passthrough.

    Args:
        video_id: YouTube video ID
        video_url: Full YouTube URL (e.g. https://www.youtube.com/watch?v=...)

    Returns:
        dict with keys: video_id, summary, key_points, topics, raw_response

    Raises:
        RuntimeError: if API key missing or quota exhausted
        ValueError: if URL scheme is not http/https
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set — required for URL passthrough analysis")

    # Validate URL scheme
    parsed = urlparse(video_url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-001",  # auto-selected if None
            contents=[
                Part.from_uri(file_uri=video_url, mime_type="video/mp4"),
                "Analyze this video and extract: title, summary (2-3 sentences), "
                "5 key topics, and 3 bullet points for a technical audience. "
                "Return valid JSON with keys: title, summary, key_topics (list), "
                "key_points (list of 3 strings).",
            ],
        )
        # Parse response.text as JSON
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"content": response.text, "video_id": video_id}
    except InvalidArgument as e:
        # Private/unavailable video — propagate as fallback signal
        raise RuntimeError(f"Video unavailable for URL passthrough: {e}")
```

#### File Changes

| File | Change |
|------|--------|
| `requirements.txt` | Add `google-genai>=0.8.0` |
| `bin/csf-analyze` | Replace subprocess `gemini -p` with SDK `client.models.generate_content()` + `Part.from_uri()`. Accept both `--url <youtube_url>` and `--input <local_file>` (for fallback path). |
| `config/intelligence_stream.yaml` | Add `gemini: { model: gemini-3.5-flash-001, api_key_env: GOOGLE_API_KEY }` |

#### Testing Approach

1. **Unit**: Mock `genai.Client` — verify `Part.from_uri()` call with correct URL + `mime_type="video/mp4"`
2. **Integration**: Call with a known public YouTube URL, verify JSON response structure
3. **Fallback**: Mock `InvalidArgument` from SDK — verify local-file fallback path is triggered
4. **Regression**: Existing `--input` path (local file fallback) continues to work

#### Rollback

Revert `bin/csf-analyze` to `subprocess.run(["gemini", "-p", ...])` approach (Phase 1 broken implementation). Remove `google-genai` from `requirements.txt`. Rollback is low-risk — behavior degrades to Phase 1 broken state, not data loss.

---

### Consequences

- **Positive**: `csf-analyze` finally does what the user originally requested — YouTube URL → Gemini 3.1 direct passthrough. No local downloads needed for public videos.
- **Negative**: New dependency (`google-genai`). Free-tier rate limit (8hr/day) requires fallback path for heavy use. Private videos still need `csf-ingest` download fallback.
