---
title: "web-ingestion"
node_type: capability
created: 2026-07-28
domain: discovery
---

# web-ingestion

**Inputs:** `url` or `urls`, `max_pages`, `collection`
**Outputs:** wiki/sources/<domain>/ files, dedup report

## Procedure

/crawl4ai <url> --max-pages 5 --collection wiki. Dedup by SHA256+etag.
