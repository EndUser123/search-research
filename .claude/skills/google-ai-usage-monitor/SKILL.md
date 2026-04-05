---
name: google-ai-usage-monitor
version: 1.0.0
status: "stable"
category: monitoring
description: Monitor Google AI Studio (Gemini API) usage, rate limits, and quota consumption with automated alerts.
author: xiaoyaner
---

# Google AI Usage Monitor Skill

Monitor Google AI Studio usage to prevent quota exhaustion and optimize API consumption.

## Supported Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| RPM | Requests Per Minute (peak) | > 80% of limit |
| TPM | Tokens Per Minute (peak) | > 80% of limit |
| RPD | Requests Per Day | > 80% of limit |

## Rate Limits by Tier

| Tier | Typical Limits |
|------|---------------|
| Free | 2 RPM, 32K TPM, 50 RPD |
| Pay-as-you-go | 10-15 RPM, 100K+ TPM, 500+ RPD |
| Paid Tier 1 | 20 RPM, 100K TPM, 250 RPD (varies by model) |

Note: Actual limits vary by model and can be viewed at the usage dashboard.

## Usage Dashboard

### URL
```
https://aistudio.google.com/usage?project={PROJECT_ID}&timeRange=last-28-days&tab=rate-limit
```

### Key Elements to Extract
- **Project name**: Which GCP project
- **Tier**: Free / Pay-as-you-go / Paid tier X
- **Models table**: Each row contains model name, category, RPM, TPM, RPD
- **Time range**: Default 28 days

## Browser Automation

### Open Usage Page
```javascript
// Using OpenClaw browser tool
browser action=open targetUrl="https://aistudio.google.com/usage?project=YOUR_PROJECT_ID&timeRange=last-28-days&tab=rate-limit" profile=openclaw
```

### Wait for Data Load
The page loads data asynchronously. Wait for:
1. Project dropdown shows project name (not "Loading...")
2. Rate limits table has data rows

### Parse Table Data
Look for table rows with pattern:
```
Model Name | Category | X / Y | X / Y | X / Y | View in charts
```

Where `X / Y` represents `used / limit`.

## Report Format

### Discord Message Template

```markdown
## 📊 Google AI Studio 用量报告

**项目**: {project_name}
**付费等级**: {tier}
**统计周期**: 过去 28 天

---

### {Model Name}
| 指标 | 用量 | 限额 | 使用率 |
|------|------|------|--------|
| RPM | {rpm_used} | {rpm_limit} | {rpm_pct}% |
| TPM | {tpm_used} | {tpm_limit} | {tpm_pct}% |
| RPD | {rpd_used} | {rpd_limit} | {rpd_pct}% |

---

{status_emoji} **状态**: {status_text}

*检查时间: {timestamp}*
```

### Status Levels

| Usage % | Status | Emoji | Action |
|---------|--------|-------|--------|
| < 50% | 正常 | ✅ | Continue normally |
| 50-80% | 需关注 | ⚠️ | Monitor more frequently |
| > 80% | 风险预警 | 🚨 | Alert user, consider rate limiting |

## Alert Rules

### When to Alert User

1. **Any metric > 80%**: Immediate alert with @mention
2. **Any metric > 50%**: Include warning note in report
3. **API errors (429)**: Track rate limit hits

### Alert Message Template

```markdown
🚨 **Google AI 配额预警**

<@USER_ID> 以下指标接近限额：

- **{model}** {metric}: {used}/{limit} ({pct}%)

建议：
- 减少 API 调用频率
- 考虑升级付费等级
- 检查是否有异常调用
```

## Cron Job Setup

### Daily Check (Recommended)

```json
{
  "name": "Google AI 用量检查",
  "schedule": {
    "kind": "cron",
    "expr": "0 20 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "检查 Google AI Studio 用量并发送报告到指定 Discord 频道"
  },
  "delivery": {
    "mode": "announce",
    "channel": "discord",
    "to": "CHANNEL_ID"
  }
}
```

## Integration with OpenClaw

### Configuration

Add to `TOOLS.md`:

```markdown
## Google AI Studio

- **Project ID**: gen-lang-client-XXXXXXXXXX
- **Dashboard**: https://aistudio.google.com/usage
- **Discord Channel**: #google-ai (CHANNEL_ID)
- **Check Schedule**: Daily 20:00
```

### Heartbeat Integration

Add to `HEARTBEAT.md`:

```markdown
## Google AI Monitoring
- Check usage if last check > 24 hours
- Alert if any metric > 80%
```

## Troubleshooting

### Page Not Loading

1. Check if logged into correct Google account
2. Verify project ID is correct
3. Wait longer for async data load (5-10 seconds)

### Data Shows "Loading..."

The project dropdown may take time to populate. Retry snapshot after a few seconds.

### Metrics Not Updating

Google notes: "Usage data may take up to 15 minutes to update."

## References

- [Google AI Studio Usage Dashboard](https://aistudio.google.com/usage)
- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Billing Documentation](https://ai.google.dev/gemini-api/docs/billing)
- [Cloud Monitoring for Gemini](https://firebase.google.com/docs/ai-logic/monitoring)

---

## Gemini Model Quota — Empirical Findings (March 2026)

Tested via live API calls against `genai.Client` (Google Generative AI Python SDK).

### Model Compatibility for Video Analysis

| Model | Video Passthrough | Content Accepted | Quota (RPD) | Status |
|-------|------------------|-------------------|--------------|--------|
| `gemini-3.1-flash-lite-preview` | ✅ `Part.from_uri()` works | ✅ | ~500+ (AI Studio) | **Use for video** |
| `gemini-2.5-flash` | ✅ works | ✅ | 20 free tier | Counter stale, still works |
| `gemini-2.5-flash-lite` | ✅ accepted | ❌ policy block | 20 free tier | Not usable |
| `gemini-3-flash` | — | ❌ 404 NOT_FOUND | — | Not available |
| `gemini-3.1-flash-lite` | — | ❌ 404 NOT_FOUND | 500 AI Studio | Wrong API name |

### Key Findings

1. **Separate quota buckets confirmed**: `gemini-2.5-flash` at "43/20" while `gemini-2.5-flash-lite` at "3/20" and `gemini-3-flash` at "1/20" — all diverged from same starting point, confirming independent per-model tracking.

2. **Daily RPD counters are stale/unreliable**: `gemini-2.5-flash` showed "43/20" (over limit) but accepted 7+ rapid requests. Daily limits are soft-enforced; RPM limits are the real gate.

3. **`gemini-3.1-flash-lite-preview` is the optimal model**: Supports `Part.from_uri(file_uri=youtube_url, mime_type="video/mp4")` video passthrough, generous quota (no visible ceiling in testing), and 10+ requests succeeded without hitting limits.

4. **`gemini-2.5-flash-lite` refuses video content**: Model accepts the API call but returns a policy block when video content is provided — not usable as primary analyzer.

5. **API name matters**: `gemini-3.1-flash-lite` (GA) returns 404 NOT_FOUND; `gemini-3.1-flash-lite-preview` (preview) works. Always use the preview suffix for new models.

### Implementation in `bin/csf-analyze`

```python
# Per-process key rotation — tracks keys that returned 429 this session
_exhausted_keys: set[str] = set()

_API_KEYS: list[tuple[str, str | None]] = [
    ("GEMINI_API_KEY_2", None),   # Working key first
    ("GEMINI_API_KEY_1", None),   # Backup
    ("GEMINI_PAID_API_KEY", None),
    ("GEMINI_API_KEY", None),
]

def _is_quota_error(exc: Exception) -> bool:
    from google.api_core.exceptions import ResourceExhausted
    return isinstance(exc, ResourceExhausted) or "429" in str(exc)

def _working_key() -> tuple[str, str] | None:
    for name, key in _API_KEYS:
        if key and name not in _exhausted_keys:
            return name, key
    return None

# In gemini_video_analyze: on quota error, skip key and retry
except Exception as e:
    if _is_quota_error(e):
        _exhausted_keys.add(key_name)
        continue  # Try next key
```

### Transcript Caching as Cost Optimization

First run fetches and caches transcript via SQLite (free). Subsequent runs use cached transcript, bypassing API cost entirely. See `csf/cache.py` — `has_cached_transcript()` pre-check routes to `mode="transcript"` (free) vs `mode="sdk"` (API call).

### Quota Budget Estimate for 2,483 Videos

| Phase | Method | Cost |
|-------|--------|------|
| Enumeration | YouTube Data API | ~19 quota units (playlistItems.list, maxResults=50) |
| Transcript fetch | `youtube.com/api/timedtext` | Free |
| Translation | Gemini API | Free tier ~1,000 req/day |
| Analysis (cached) | `mode="transcript"` | Free |
| Analysis (uncached) | `gemini-3.1-flash-lite-preview` | ~$0.25/1M in, $1.50/1M out |
