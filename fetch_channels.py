# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse

import os
API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not API_KEY:
    raise SystemExit("YOUTUBE_API_KEY env var not set")

with open("shorts_data.json", encoding="utf-8") as f:
    data = json.load(f)

channel_ids = set()
for cat, items in data["categories"].items():
    for item in items:
        if item.get("channelId"):
            channel_ids.add(item["channelId"])

channel_ids = list(channel_ids)
print("unique channels:", len(channel_ids))

def api_get(path, params):
    params["key"] = API_KEY
    url = "https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

sub_counts = {}
for i in range(0, len(channel_ids), 50):
    chunk = channel_ids[i:i+50]
    d = api_get("channels", {"part": "statistics", "id": ",".join(chunk)})
    for item in d.get("items", []):
        stats = item.get("statistics", {})
        if not stats.get("hiddenSubscriberCount", False):
            sub_counts[item["id"]] = int(stats.get("subscriberCount", 0))
        else:
            sub_counts[item["id"]] = None

for cat, items in data["categories"].items():
    for item in items:
        cid = item.get("channelId")
        item["subscribers"] = sub_counts.get(cid) if cid else None

with open("shorts_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("done")
