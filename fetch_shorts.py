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
MAX_PER_COUNTRY = 50

# country_label, flag, regionCode, search query term (language-appropriate)
COUNTRIES = [
    ("한국", "🇰🇷", "KR", "쇼츠"),
    ("미국", "🇺🇸", "US", "shorts"),
    ("일본", "🇯🇵", "JP", "ショート"),
    ("프랑스", "🇫🇷", "FR", "shorts"),
    ("독일", "🇩🇪", "DE", "shorts"),
    ("영국", "🇬🇧", "GB", "shorts"),
    ("브라질", "🇧🇷", "BR", "shorts"),
    ("인도", "🇮🇳", "IN", "shorts"),
]

# YouTube's official videoCategoryId -> my Korean taxonomy label
CATEGORY_MAP = {
    "1": "영화/애니", "2": "자동차", "10": "음악", "15": "동물",
    "17": "스포츠", "19": "여행", "20": "게임", "22": "일상/로그",
    "23": "코미디", "24": "엔터", "25": "뉴스", "26": "스타일",
    "27": "교육", "28": "IT/기술", "29": "사회",
}

def api_get(path, params):
    params["key"] = API_KEY
    url = "https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def search_country(region_code, query, published_after):
    data = api_get("search", {
        "part": "snippet",
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",
        "maxResults": "50",
        "publishedAfter": published_after,
        "regionCode": region_code,
        "q": query,
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
    quota = 0

    for country_label, flag, region_code, query in COUNTRIES:
        try:
            items = search_country(region_code, query, published_after)
            quota += 100
        except Exception as e:
            print("SEARCH ERROR", country_label, e, file=sys.stderr)
            result[country_label] = []
            continue

        video_ids = [it["id"]["videoId"] for it in items if "videoId" in it.get("id", {})]
        if not video_ids:
            result[country_label] = []
            continue

        try:
            stats = get_stats(video_ids)
            quota += 1
        except Exception as e:
            print("STATS ERROR", country_label, e, file=sys.stderr)
            result[country_label] = []
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
            cat_id = sn.get("categoryId", "")
            category = CATEGORY_MAP.get(cat_id, "기타")
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
                "category": category,
                "country": country_label,
                "flag": flag,
            })

        rows.sort(key=lambda r: r["publishedAt"], reverse=True)
        result[country_label] = rows[:MAX_PER_COUNTRY]

        time.sleep(0.2)

    meta = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "published_after": published_after,
        "quota_used_estimate": quota,
    }

    with open("shorts_data.json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "countries": result}, f, ensure_ascii=False, indent=2)

    total_items = sum(len(v) for v in result.values())
    print("DONE. total items:", total_items, "quota est:", meta["quota_used_estimate"])
    for k, v in result.items():
        print(" -", k, len(v))

if __name__ == "__main__":
    main()
