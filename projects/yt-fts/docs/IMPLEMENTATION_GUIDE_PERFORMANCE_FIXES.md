# Implementation Guide: yt-fts Performance Optimization

## Quick Start: Immediate Performance Fixes

This guide provides concrete implementation steps for the highest-impact performance optimizations.

## Phase 1: Critical Performance Fixes

### 1. Optimize Channel Resolution

**Expected Improvement**: 80% reduction in resolution time (9s → <2s)

#### A. Reduce delays in batch_downloader.py

```python
# Change this line:
delay_between_channels: float = 60.0  # 60 seconds between channels

# To this:
delay_between_channels: float = 1.0  # 1 second between channels
```

#### B. Optimize fast_channel_resolver.py

```python
# Update yt-dlp options:
self.ydl_opts = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "socket_timeout": 5,  # Reduced from 10
    "retries": 2,  # Reduced from 3
    "fragment_retries": 1,  # Reduced from 3
}
```

### 2. Add Invidious Integration

Create new file: src/yt_fts/invidious_resolver.py

```python
"""
Invidious-based channel resolver to bypass YouTube rate limits.
"""

import aiohttp
import asyncio
from typing import Optional

class InvidiousResolver:
    def __init__(self):
        self.instances = [
            "https://yewtu.be",
            "https://vid.puffyan.us",
            "https://invidious.snopyta.org",
        ]
    
    async def resolve_channel(self, channel_input: str) -> Optional[str]:
        """Resolve channel using Invidious API."""
        
        for instance in self.instances:
            try:
                async with aiohttp.ClientSession() as session:
                    api_url = f"{instance}/api/v1/resolveurl"
                    params = {"url": channel_input}
                    
                    async with session.get(api_url, params=params, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("ucid")
            except:
                continue
        
        return None

# Usage example
async def test_invidious():
    resolver = InvidiousResolver()
    result = await resolver.resolve_channel("@testchannel")
    print(f"Resolved channel: {result}")
```

### 3. Database Optimization

Add indexes to improve query performance:

```sql
-- Create indexes for better performance
CREATE INDEX idx_videos_channel_id ON videos(channel_id);
CREATE INDEX idx_videos_video_date ON videos(video_date);
CREATE INDEX idx_subtitles_video_id ON subtitles(video_id);
```

## Expected Performance Improvements

### Before Optimization
- Channel resolution: 9+ seconds per channel
- Batch delay: 60 seconds between channels
- 50 channels: 56+ minutes overhead

### After Optimization  
- Channel resolution: < 2 seconds per channel
- Batch delay: 1 second between channels
- 50 channels: ~2 minutes total

**Overall improvement: 95% faster processing**

## Implementation Priority

1. **Immediate (1 hour)**: Reduce batch delays to 1 second
2. **Short-term (1 day)**: Add Invidious integration
3. **Medium-term (1 week)**: Database optimization and parallel processing

These simple changes can provide immediate dramatic performance improvements while you implement more advanced optimizations.
