# User Guide - CKS-Enhanced Worktree Management

**Version**: 1.0.0
**Last Updated**: 2025-12-22

---

## Introduction

The CKS-Enhanced Worktree Management system provides intelligent guidance to prevent git worktree confusion and maximize effective use of the `/explore` command. This guide explains how to use the system and interpret its recommendations.

---

## What This System Does

### Worktree Confusion Prevention

The system detects when you might be about to perform operations in the wrong git worktree, helping prevent incidents like the "yt-fts-alt-platforms" confusion where similar worktree names caused issues.

### Explore Opportunity Detection

The system suggests when using the `/explore` command would be more effective than manual discovery, based on successful patterns from similar queries.

---

## How It Works

### Non-Intrusive Integration

The system works silently in the background:

1. **Analyzes** your prompts and file operations
2. **Detects** potential worktree risks or explore opportunities
3. **Provides** contextual suggestions when appropriate
4. **Learns** from successful patterns over time

### What You'll See

When the system detects a potential issue or opportunity, you'll see helpful guidance:

#### Worktree Safety Alert Example

```
## 🚨 Worktree Safety Alert

Based on patterns similar to your request, we've detected potential worktree confusion risks:

**Previous Incident**: yt-fts-alt-platforms confusion (similar naming)
**Risk Level**: HIGH (85% probability)
**Prevention**: Always verify current worktree before operations

Current worktree: P:\yt-fts-alt-platforms
Target worktree: P:\yt-fts-main
```

#### Explore Opportunity Suggestion Example

```
## 💡 Suggestion: Consider /explore

For "understand the codebase architecture" requests, users with similar patterns found /explore highly effective:

**Success Rate**: 95% for similar queries
**Time Saved**: Average 12 minutes vs manual discovery
**Confidence**: 65% probability of benefit

Would you like to run: /explore --focus "codebase structure"
```

---

## Interpreting Recommendations

### Worktree Safety Alerts

**When you see this**: You're about to perform operations that could affect the wrong worktree.

**What to do**:
1. **Verify** your current worktree: Check your prompt or run `git worktree list`
2. **Confirm** you're in the right place before proceeding
3. **Navigate** to the correct worktree if needed

**Risk Levels**:
- **HIGH (>70%)**: Strong recommendation to verify worktree
- **MEDIUM (40-70%)**: Suggestion to double-check
- **LOW (<40%)**: Informational, no action required

### Explore Opportunity Suggestions

**When you see this**: Your query pattern suggests `/explore` would be more effective.

**What to do**:
1. **Consider** the suggestion - it's based on successful patterns
2. **Run** the suggested `/explore` command if it fits your goal
3. **Ignore** the suggestion if you have a different approach in mind

**Confidence Levels**:
- **HIGH (>70%)**: Strong recommendation, likely significant benefit
- **MEDIUM (50-70%)**: Good suggestion, moderate benefit expected
- **LOW (<50%)**: Optional suggestion, minor benefit possible

---

## System Behavior

### Always Non-Blocking

The system **never** prevents you from taking action. It provides guidance, but you maintain full control.

### Graceful Degradation

If the system's cache or CKS integration is unavailable:
- The system continues working normally
- You may not see suggestions temporarily
- No errors or disruptions to your workflow

### Performance

The system is designed for speed:
- **Typical response**: <3ms for cached queries
- **No noticeable delay**: System works faster than you can type
- **Minimal overhead**: Uses intelligent multi-level caching

---

## Examples

### Example 1: Worktree Confusion Prevention

**Scenario**: You're working in `yt-fts-alt-platforms` and want to modify the main project.

**System detects**: Similar patterns to the yt-fts confusion incident.

**You see**:
```
## 🚨 Worktree Safety Alert
**Risk Level**: HIGH (85% probability)
Current worktree: P:\yt-fts-alt-platforms
```

**You verify**: Check `git worktree list` and realize you're in the alt-platforms worktree.

**You navigate**: Change to the correct worktree before making changes.

**Result**: Confusion prevented, work done in correct location.

### Example 2: Explore Opportunity

**Scenario**: You want to understand how the codebase is structured.

**System detects**: This query pattern strongly benefits from `/explore`.

**You see**:
```
## 💡 Suggestion: Consider /explore
**Success Rate**: 95% for similar queries
**Time Saved**: Average 12 minutes
```

**You run**: `/explore --focus "codebase structure"`

**Result**: Get comprehensive codebase overview in 2 minutes instead of 15 minutes of manual searching.

### Example 3: Ignoring Suggestions

**Scenario**: System suggests using `/explore`, but you want to manually search.

**You ignore**: The suggestion and proceed with your approach.

**System respects**: Your choice - no blocking, no repeated prompts.

**Result**: You maintain full control over your workflow.

---

## Tips for Best Results

### 1. Read the Recommendations

The system provides context-specific guidance based on learned patterns. Taking a moment to read suggestions can save time and prevent errors.

### 2. Verify Worktree When Alerted

When you see worktree safety alerts, especially HIGH risk, it's worth taking 10 seconds to verify you're in the right place.

### 3. Consider Explore Suggestions

The `/explore` command is powerful. When the system suggests it, there's a good reason based on successful patterns.

### 4. Provide Feedback (Future)

The system will learn from patterns. In future versions, accepting or rejecting suggestions will help improve recommendations.

### 5. Don't Worry About Performance

The system is optimized for speed. You won't notice any delay - it processes your prompts in milliseconds.

---

## Troubleshooting

### Issue: I'm not seeing any suggestions

**Possible causes**:
1. Your queries don't match known patterns (this is normal)
2. Cache is still warming up (first few sessions)
3. CKS integration temporarily unavailable

**Solution**: This is expected behavior. The system only suggests when it has high confidence.

### Issue: I'm seeing too many suggestions

**Possible causes**:
1. Your queries closely match many patterns
2. Cache hit rate is very high (good performance!)

**Solution**: Suggestions are non-intrusive. You can ignore them if they're not helpful.

### Issue: A suggestion seems wrong

**Possible causes**:
1. Pattern matching isn't perfect (system is learning)
2. Context differs from the pattern match

**Solution**: You maintain full control - ignore suggestions that don't fit your context.

### Issue: System feels slow

**Expected**: System adds <3ms overhead, imperceptible to humans.

**If noticeable delay occurs**:
- Check if CKS is responsive
- Try clearing cache: See Maintenance section below
- Report the issue if delay persists

---

## Maintenance

### Viewing System Status

You can check how the system is performing:

```bash
# Check cache metrics (for developers)
cd P:\.claude\hooks
python -c "from guidance_cache import get_guidance_cache; import json; print(json.dumps(get_guidance_cache().get_metrics(), indent=2))"
```

### Clearing Cache (If Needed)

Rarely needed, but available if issues occur:

```bash
# Clear memory cache only (keeps disk cache)
python -c "from guidance_cache import get_guidance_cache; get_guidance_cache().clear_l1()"

# Clear all cache (memory + disk)
python -c "from guidance_cache import get_guidance_cache; get_guidance_cache().clear_all()"
```

---

## FAQ

**Q: Will this system slow down my work?**

A: No. The system adds less than 3ms overhead, which is imperceptible. It's optimized for speed using multi-level caching.

**Q: Can I turn off the suggestions?**

A: The system is designed to be non-intrusive. Suggestions appear only when the system has high confidence, and you can always ignore them.

**Q: Does this system store my data?**

A: The system stores query patterns and success rates in CKS for learning. It doesn't store sensitive content.

**Q: What if the system is wrong?**

A: The system provides suggestions, not commands. You maintain full control and can always proceed with your own approach.

**Q: How does the system learn?**

A: It analyzes successful patterns from your workflows and similar queries, storing these patterns in CKS for future reference.

**Q: Can I add my own patterns?**

A: Currently, patterns are managed by developers. Future versions may support user-defined patterns.

---

## Getting Help

### Documentation

- **Technical Documentation**: See `PROJECT_DOCUMENTATION.md`
- **Deployment Guide**: See `DEPLOYMENT_CHECKLIST.md`
- **Progress Summary**: See `progress-summary.md`

### Support

For issues or questions:
1. Check this user guide
2. Review troubleshooting section
3. Consult project documentation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-22 | Initial release |

---

**User Guide Version**: 1.0.0
**Last Updated**: 2025-12-22
**Maintained By**: CSF NIP Architecture
