# Input formats — worked examples

`normalize.py` accepts six input formats. Auto-detection tries each in priority
order; pass `--format <name>` to force one.

All formats produce the same canonical JSONL shape:

```json
{"id": "abc123", "title": "...", "url": "https://...", "source": "...", "raw": {...}}
```

## 1. `youtube-wl` — YouTube watch-later JSON export

Default export from browser extensions like "Save to Watch Later." Each entry
has `videoId`, `title`, `channel`, `url`.

```bash
python normalize.py watch-later.json --drop-dead -o canonical.jsonl
```

**`--drop-dead` removes:**
- `[Deleted video]` and `[Private video]` entries (NotebookLM can't ingest)
- Items with channel `[unknown]`

## 2. `csv` — any CSV with a URL column

Auto-detects URL column (any column containing "url" or "link" in name), title
column ("title" or "name"), source column ("channel", "author", or "source").

```bash
# Auto-detect
python normalize.py bookmarks.csv -o canonical.jsonl

# Explicit columns
python normalize.py bookmarks.csv \
    --url-field link --title-field name --source-field author \
    -o canonical.jsonl
```

## 3. `jsonl` — one JSON object per line

Specify fields if they don't match the defaults (`id`, `title`, `url`, `source`):

```bash
python normalize.py items.jsonl \
    --url-field link --source-field channel_name \
    -o canonical.jsonl
```

## 4. `json-array` — JSON array of objects

Same field-detection rules as `jsonl`:

```bash
python normalize.py items.json -o canonical.jsonl
```

## 5. `url-list` — one URL per line, no metadata

Title is derived from the URL path; source from the domain. `id` is a hash.

```bash
python normalize.py urls.txt -o canonical.jsonl
```

Input example:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://arxiv.org/abs/2401.00001
# Comments and blank lines are skipped
https://example.com/article
```

**Caveat:** URLs without titles cluster worse — title text is the primary
signal. If you have titles, use `csv` or `jsonl` instead.

## 6. `rss` — RSS or Atom feed

Parses `<item>` (RSS) or `<entry>` (Atom). Extracts `title`, `link`, `guid`.

```bash
python normalize.py feed.xml -o canonical.jsonl
# or from a URL — pipe through curl first
curl -sL https://example.com/feed.xml > feed.xml
python normalize.py feed.xml -o canonical.jsonl
```

## Post-normalize: dedup is automatic

`normalize.py` deduplicates by stable ID (explicit `id` field, or hash of
normalized `(title, url)` if absent). Re-running on the same input is safe.

## Verifying the output

```bash
# Count
wc -l canonical.jsonl

# Spot-check first/last
head -1 canonical.jsonl | python -m json.tool
tail -1 canonical.jsonl | python -m json.tool
```

Then proceed to `cluster.py`.
