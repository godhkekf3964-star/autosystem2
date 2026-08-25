# -*- coding: utf-8 -*-
import io, json

TEMPLATE = "dashboard_template.html"
OUT = "shorts-dashboard.html"

with io.open(TEMPLATE, "r", encoding="utf-8") as f:
    html = f.read()

with io.open("yt_achieved_block.js", "r", encoding="utf-8") as f:
    data_block = f.read()

with io.open("dashboard_meta.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

generated_at_display = meta["generated_at"].replace("T", " ").replace("Z", "")
prefix_block = '  var YT_GENERATED_AT = "%s";\n' % generated_at_display

placeholder = "  /*__YT_DATA_BLOCK__*/\n"
assert placeholder in html, "template placeholder missing"

html = html.replace(placeholder, prefix_block + data_block)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("assembled:", OUT, "size:", len(html))
