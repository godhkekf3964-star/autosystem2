# -*- coding: utf-8 -*-
"""
Runs the full pipeline: fetch shorts -> download thumbnails -> fetch channel
subscriber counts -> assemble the final shorts-dashboard.html.

Requires env var YOUTUBE_API_KEY to be set before running.
Run from this directory: python run_all.py
Produces: shorts-dashboard.html (ready to publish as an Artifact)
"""
import subprocess
import sys
import os

if not os.environ.get("YOUTUBE_API_KEY"):
    print("ERROR: set YOUTUBE_API_KEY env var first", file=sys.stderr)
    sys.exit(1)

steps = ["fetch_shorts.py", "download_thumbs.py", "fetch_channels.py", "assemble.py"]

for step in steps:
    print("=== running", step, "===")
    r = subprocess.run([sys.executable, step])
    if r.returncode != 0:
        print("FAILED at", step, file=sys.stderr)
        sys.exit(1)

print("=== all done: shorts-dashboard.html is ready ===")
