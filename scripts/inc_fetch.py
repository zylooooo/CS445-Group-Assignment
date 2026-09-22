#!/usr/bin/env python3
"""Fetch INC Ransom announcement pages through Tor into ~/dls/raw/inc_ransom/.

Usage:
    python3 inc_fetch.py "http://<api-mirror>.onion" [per_page]

Argument one is the base URL of a CURRENT mirror, which you must source
yourself: leak sites rotate mirrors constantly, so none is shipped with this
repository. See the "Finding a working mirror" section of the README.

Note the output directory is lowercase "inc_ransom", while merge_all.py reads the
parsed CSV from "raw/Inc_Ransom/inc_ransom.csv". Point inc_parse.py at this
directory for input and at the capitalised one for output.
"""
import json, random, sys, time
from datetime import date
from pathlib import Path
import requests

API = sys.argv[1].rstrip("/")
PER_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 50
OUT = Path.home() / "dls" / "raw" / "inc_ransom"
OUT.mkdir(parents=True, exist_ok=True)
PROXIES = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}

seen, page, total = set(), 1, None
while True:
    url = f"{API}/api/v1/blog/get/announcements?page={page}&perPage={PER_PAGE}"
    body = None
    for attempt in (1, 2, 3):
        try:
            r = requests.get(url, proxies=PROXIES, timeout=120)
            r.raise_for_status()
            body = r.json()
            break
        except Exception as e:
            print(f"page {page} attempt {attempt} failed: {e}")
            time.sleep(10)
    if body is None:
        print(f"page {page} failed 3 times, stopping")
        break

    payload = body.get("payload", {})
    items = payload.get("announcements", [])
    total = payload.get("length", total)
    if not items:
        print(f"page {page} empty, reached the end")
        break

    ids = {a.get("_id") for a in items}
    if ids <= seen:
        print(f"page {page} repeated earlier items, stopping")
        break
    seen |= ids

    f = OUT / f"{date.today()}_page{page:03d}.json"
    f.write_text(json.dumps(body), encoding="utf-8")
    print(f"page {page}: {len(items)} items, {len(seen)}/{total} collected")

    if total and len(seen) >= total:
        print("collected everything the API reports")
        break
    page += 1
    time.sleep(3 + random.random() * 4)

print(f"done. {len(seen)} unique announcements in {OUT}")
