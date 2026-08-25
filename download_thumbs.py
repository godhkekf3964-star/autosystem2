# -*- coding: utf-8 -*-
import json
import urllib.request
import base64
import os

with open("shorts_data.json", encoding="utf-8") as f:
    data = json.load(f)

os.makedirs("thumbs", exist_ok=True)

count = 0
failed = 0
for cat, items in data["categories"].items():
    for item in items:
        vid = item["id"]
        path = os.path.join("thumbs", vid + ".jpg")
        if not os.path.exists(path):
            url = "https://i.ytimg.com/vi/%s/mqdefault.jpg" % vid
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    content = resp.read()
                with open(path, "wb") as out:
                    out.write(content)
                count += 1
            except Exception as e:
                print("FAIL", vid, e)
                failed += 1
                continue
        item["thumb_file"] = path

with open("shorts_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("downloaded:", count, "failed:", failed)
