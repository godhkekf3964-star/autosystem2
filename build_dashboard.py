# -*- coding: utf-8 -*-
import json
import base64
import datetime
import os

with open("shorts_data.json", encoding="utf-8") as f:
    data = json.load(f)

generated_at = datetime.datetime.strptime(data["meta"]["generated_at"], "%Y-%m-%dT%H:%M:%SZ")
generated_at = generated_at.replace(tzinfo=datetime.timezone.utc)

def days_label(published_at_str):
    dt = datetime.datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    delta = generated_at - dt
    hours = delta.total_seconds() / 3600.0
    if hours < 24:
        return "오늘 업로드"
    days = int(hours // 24)
    return str(days) + "일 전 업로드"

def fmt_followers(n):
    if n is None:
        return None
    if n >= 100000000:
        return "%.2f억" % (n / 100000000.0)
    if n >= 10000:
        return "%.1f만" % (n / 10000.0)
    return str(n)

def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")

lines = []
lines.append("  var YT_ACHIEVED = [")

all_items = []
for country, items in data["countries"].items():
    for it in items:
        all_items.append(it)

# de-dupe by video id (a video could in theory surface under >1 country query)
seen = set()
deduped = []
for it in all_items:
    if it["id"] in seen:
        continue
    seen.add(it["id"])
    deduped.append(it)
all_items = deduped

for i, it in enumerate(all_items):
    thumb_path = it.get("thumb_file")
    b64 = ""
    if thumb_path and os.path.exists(thumb_path):
        with open(thumb_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")

    followers = it.get("subscribers")
    followers_label = fmt_followers(followers)

    parts = []
    parts.append('category:"%s"' % esc(it.get("category", "기타")))
    parts.append('subtopic:""')
    parts.append('country:"%s"' % esc(it["country"]))
    parts.append('flag:"%s"' % it["flag"])
    parts.append('channel:"%s"' % esc(it["channel"]))
    parts.append('title:"%s"' % esc(it["title"]))
    parts.append('url:"%s"' % it["url"])
    parts.append('views:%d' % it["views"])
    parts.append('uploaded:"%s"' % days_label(it["publishedAt"]))
    parts.append('publishedAt:"%s"' % it["publishedAt"])
    if it.get("likes") is not None:
        parts.append('likes:%d' % it["likes"])
    if it.get("comments") is not None:
        parts.append('comments:%d' % it["comments"])
    if followers is not None:
        parts.append('followers:%d, followersLabel:"%s"' % (followers, followers_label))
    if b64:
        parts.append('img:"data:image/jpeg;base64,%s"' % b64)

    obj = "    {\n      " + ",\n      ".join(parts) + "\n    }"
    lines.append(obj + ("," if i < len(all_items) - 1 else ""))

lines.append("  ];")

js_block = "\n".join(lines) + "\n"

with open("yt_achieved_block.js", "w", encoding="utf-8") as f:
    f.write(js_block)

country_counts = {c: len(items) for c, items in data["countries"].items()}
cat_counts = {}
for it in all_items:
    c = it.get("category", "기타")
    cat_counts[c] = cat_counts.get(c, 0) + 1

meta_out = {
    "generated_at": data["meta"]["generated_at"],
    "published_after": data["meta"]["published_after"],
    "total": len(all_items),
    "country_counts": country_counts,
    "cat_counts": cat_counts,
}
with open("dashboard_meta.json", "w", encoding="utf-8") as f:
    json.dump(meta_out, f, ensure_ascii=False, indent=2)

print("wrote yt_achieved_block.js, items:", len(all_items))
