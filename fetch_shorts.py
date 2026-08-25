# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse
import datetime
import time
import sys

import os
API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not API_KEY:
    raise SystemExit("YOUTUBE_API_KEY env var not set")
VIEW_MIN = 1000000
DAYS_BACK = 3
MAX_PER_CATEGORY = 30

# maps to my existing 15-category taxonomy, using YouTube's official videoCategoryId
CATEGORIES = [
    ("영화/애니", 1),
    ("자동차", 2),
    ("음악", 10),
    ("동물", 15),
    ("스포츠", 17),
    ("여행", 19),
    ("게임", 20),
    ("일상/로그", 22),
    ("코미디", 23),
    ("엔터", 24),
    ("뉴스", 25),
    ("스타일", 26),
    ("교육", 27),
    ("IT/기술", 28),
    ("사회", 29),
]

def api_get(path, params):
    params["key"] = API_KEY
    url = "https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def search_category(cat_id, published_after):
    data = api_get("search", {
        "part": "snippet",
        "type": "video",
        "videoDuration": "short",
        "videoCategoryId": str(cat_id),
        "order": "viewCount",
        "maxResults": "50",
        "publishedAfter": published_after,
        "q": "shorts",
    })
    return data.get("items", [])

def get_stats(video_ids):
    out = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        data = api_get("videos", {
            "part": "statistics,snippet",
            "id": ",".join(chunk),
        })
        for item in data.get("items", []):
            out[item["id"]] = item
    return out

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    published_after = (now - datetime.timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = {}
    total_quota_search = 0
    total_quota_videos = 0

    for cat_name, cat_id in CATEGORIES:
        try:
            items = search_category(cat_id, published_after)
            total_quota_search += 100
        except Exception as e:
            print("SEARCH ERROR", cat_name, e, file=sys.stderr)
            result[cat_name] = []
            continue

        video_ids = [it["id"]["videoId"] for it in items if "videoId" in it.get("id", {})]
        if not video_ids:
            result[cat_name] = []
            continue

        try:
            stats = get_stats(video_ids)
            total_quota_videos += 1
        except Exception as e:
            print("STATS ERROR", cat_name, e, file=sys.stderr)
            result[cat_name] = []
            continue

        rows = []
        for vid in video_ids:
            st = stats.get(vid)
            if not st:
                continue
            views = int(st["statistics"].get("viewCount", 0))
            if views < VIEW_MIN:
                continue
            sn = st["snippet"]
            rows.append({
                "id": vid,
                "title": sn.get("title", ""),
                "channel": sn.get("channelTitle", ""),
                "channelId": sn.get("channelId", ""),
                "views": views,
                "likes": int(st["statistics"].get("likeCount", 0)) if "likeCount" in st["statistics"] else None,
                "comments": int(st["statistics"].get("commentCount", 0)) if "commentCount" in st["statistics"] else None,
                "publishedAt": sn.get("publishedAt", ""),
                "thumb": sn.get("thumbnails", {}).get("high", sn.get("thumbnails", {}).get("medium", {})).get("url", ""),
                "url": "https://youtube.com/shorts/" + vid,
            })

        rows.sort(key=lambda r: r["publishedAt"], reverse=True)
        result[cat_name] = rows[:MAX_PER_CATEGORY]

        time.sleep(0.2)

    meta = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "published_after": published_after,
        "quota_used_estimate": total_quota_search + total_quota_videos,
    }

    with open("shorts_data.json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "categories": result}, f, ensure_ascii=False, indent=2)

    total_items = sum(len(v) for v in result.values())
    print("DONE. total items:", total_items, "quota est:", meta["quota_used_estimate"])
    for k, v in result.items():
        print(" -", k, len(v))

if __name__ == "__main__":
    main()
