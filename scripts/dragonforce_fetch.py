#!/usr/bin/env python3
"""Fetch DragonForce blog/posts pages through Tor into ~/dls/raw/DragonForce/.

Usage:
    python3 dragonforce_fetch.py "http://<mirror>.onion"

Argument one is the base URL of a CURRENT mirror, which you must source
yourself: leak sites rotate mirrors constantly, so none is shipped with this
repository. See the "Finding a working mirror" section of the README.
"""
import json, random, sys, time
from datetime import date
from pathlib import Path
import requests

BASE = sys.argv[1].rstrip("/")
OUT = Path.home() / "dls" / "raw" / "DragonForce"
OUT.mkdir(parents=True, exist_ok=True)

s = requests.Session()
s.proxies.update({"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"})
try:
    s.get(BASE + "/blog", timeout=120)   # pick up any session cookie first
except Exception as e:
    print(f"warm-up request failed, continuing anyway: {e}")

seen, page, total = set(), 1, None
while True:
    url = f"{BASE}/api/guest/blog/posts?page={page}"
    body = None
    for attempt in (1, 2, 3):
        try:
            r = s.get(url, timeout=120)
            r.raise_for_status()
            body = r.json()
            break
        except Exception as e:
            print(f"page {page} attempt {attempt} failed: {e}")
            time.sleep(10)
    if body is None:
        print(f"page {page} failed 3 times, stopping")
        break

    data = body.get("data") or {}
    items = data.get("publications") or []
    total = data.get("count", total)
    if not items:
        print(f"page {page} empty, reached the end")
        break

    ids = {p.get("uuid") for p in items}
    if ids <= seen:
        print(f"page {page} repeated earlier items, stopping")
        break
    seen |= ids

    (OUT / f"{date.today()}_page{page:03d}.json").write_text(json.dumps(body), encoding="utf-8")
    print(f"page {page}: {len(items)} items, {len(seen)}/{total} collected")

    if total and len(seen) >= total:
        print("collected everything the API reports")
        break
    page += 1
    time.sleep(3 + random.random() * 4)

print(f"done. {len(seen)} unique publications in {OUT}")
if total and len(seen) < total:
    print(f"INCOMPLETE: {total - len(seen)} of {total} missing, re-run against another mirror")
    sys.exit(1)
