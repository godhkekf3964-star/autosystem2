# Shorts Tracker — auto-refresh pipeline

Collects YouTube Shorts that crossed 1,000,000 views within the last 3 days,
across 15 official YouTube categories, and produces a self-contained
`shorts-dashboard.html` ready to publish as a Claude Artifact.

## Files

- `fetch_shorts.py` — calls YouTube Data API v3 `search.list` + `videos.list`
  per category (15 categories, official `videoCategoryId`), filters for
  views >= 1,000,000 within the last 3 days, writes `shorts_data.json`.
- `download_thumbs.py` — downloads each video's `mqdefault.jpg` thumbnail
  into `thumbs/`.
- `fetch_channels.py` — calls `channels.list` to get subscriber counts for
  every channel in the dataset, merges into `shorts_data.json`.
- `assemble.py` — reads `dashboard_template.html` (the static shell) +
  `shorts_data.json` + downloaded thumbnails, and writes the final,
  self-contained `shorts-dashboard.html` (images inlined as base64).
- `dashboard_template.html` — the dashboard shell with a
  `/*__YT_DATA_BLOCK__*/` placeholder where the data gets injected.
- `run_all.py` — runs all four steps in order.

## Usage (manual or in a scheduled cloud agent)

```bash
export YOUTUBE_API_KEY="..."   # YouTube Data API v3 key, restricted to that API
python run_all.py
```

This produces `shorts-dashboard.html` in the working directory. The calling
agent should then publish/update the Claude Artifact with that file
(pass the existing artifact's `url` so it updates in place rather than
creating a new one).

## Quota

Each full run costs about ~1,500-1,900 YouTube Data API units
(15 categories x 100 units for search + a handful of cheap `videos.list` /
`channels.list` calls). Default daily quota is 10,000 units, so this
comfortably supports refreshing every few hours.
