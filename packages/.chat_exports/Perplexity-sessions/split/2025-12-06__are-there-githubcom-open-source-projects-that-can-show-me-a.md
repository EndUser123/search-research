---
title: "are there github.com open source projects, that can show me a dashboard of the last day, 3 days, 2 weeks, etc, of the yo"
date: "2025-12-06"
mode: "COPILOT"
uuid: "eb3520bb-5b31-40c3-bcf6-c33b7e8239d3"
entry_count: 2
---

## Human

are there github.com open source projects, that can show me a dashboard of the last day, 3 days, 2 weeks, etc, of the youtube channels with thumbnails that I'm interested in, plus maybe reddit, x/twitter, etc?

## Assistant

Perfect! Now I have comprehensive information. Let me provide you with a detailed response about the open-source projects that match your use case.

## Open-Source Dashboard Projects for Multi-Platform Content

Yes, there are several excellent GitHub projects that provide dashboards for YouTube channels and other platforms. Here's what I found:

### **Top Recommendation: Glance** ⭐
**Repository:** [glanceapp/glance](https://github.com/glanceapp/glance) (28.9k stars)

This is the most feature-complete and actively maintained option:
- **Self-hosted dashboard** written in Go
- **Multi-platform support:** YouTube, Reddit, RSS feeds, Twitter/X via RSS
- **Time-based filtering:** View content from last day, 3 days, weeks, etc.
- **Video widget** with thumbnails for YouTube subscriptions
- **Highly customizable** YAML configuration
- **Mobile-responsive** design
- **Docker support** for easy deployment
- **Multiple widgets:** RSS readers, video feeds, custom HTML, iframe embeds

This is probably your best fit since it's actively maintained, has excellent configuration options, and supports the exact mix of platforms you want.

***

### **Platform Aggregator: Platform** 
**Repository:** [2310-social-media-aggregator](https://github.com/2310-social-media-aggregator/frontend)

- Aggregates YouTube and Twitch content from creators
- Creator details page showing most recent videos
- "Saved creators" list functionality
- Built with React frontend + Ruby on Rails backend
- Designed specifically for browsing multiple creators' content

**Limitation:** Focused mainly on YouTube + Twitch, not as comprehensive for Reddit/Twitter.

***

### **RSS-Focused: Obsidian RSS Dashboard**
**Repository:** [amatya-aditya/obsidian-rss-dashboard](https://github.com/amatya-aditya/obsidian-rss-dashboard) (200 stars)

- **YouTube integration** with embedded video player
- **RSS/Atom/JSON feed support**
- Podcast support
- Smart tagging system
- Reader view with article fetching
- Save articles as markdown
- **YouTube transcripts** (in progress)
- Mobile-responsive

**Limitation:** Obsidian vault integration (though still usable as standalone dashboard).

***

### **Analytics-Focused: YouTube Channel Dashboard**
**Repository:** [RunnyEgg/Youtube-Dashboard](https://github.com/RunnyEgg/Youtube-Dashboard)

- Uses YouTube Data API v3 to fetch channel data
- Power BI dashboard for visualization
- Shows: lifetime stats, view metrics, top performing videos
- Engagement tracking over time

**Limitation:** More for analytics than discovery/browsing multiple channels.

***

## My Recommendation for Your Use Case

Given your interest in viewing **recent uploads from multiple YouTube channels with thumbnails + Reddit/Twitter content with time filtering**:

1. **Start with Glance** – It's the most flexible and actively maintained. You can configure:
   - YouTube video widget for subscriptions
   - Reddit widget for subreddits
   - RSS feeds for Twitter (via Twitter RSS alternatives like `nitter`)
   - Time-based filtering is built into the UI

2. **Alternative:** If you want something simpler focused specifically on video subscriptions, the **2310 Social Media Aggregator** is more purpose-built but less feature-complete.

Would you like me to help you set up a Glance configuration for your specific YouTube channels, subreddits, and Twitter accounts? Or would you prefer exploring one of the other projects in more detail?

## Human

Can you see files on my computer?

## Assistant

No, there is no access to files on your computer. All interactions are limited to this conversation interface, available tools for web/email/calendar searches, and any files explicitly uploaded or attached to messages. Local file systems remain private and inaccessible.
