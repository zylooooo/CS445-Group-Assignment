#!/usr/bin/env python3
"""Fetch Global Secret Group's listing page through Tor into ~/dls/raw/GlobalSecretGroup/.

Usage:
    python3 gsg_fetch.py "http://<mirror>.onion"

Argument one is the base URL of a CURRENT mirror, which you must source
yourself: leak sites rotate mirrors constantly, so none is shipped with this
repository. See the "Finding a working mirror" section of the README.

The site lists every victim as a card on its home page (no pagination). Only the
home page and /news/ are fetched. Project pages load their company data and file
index from /project/<id>/data/api/, which serves the stolen-file listing, so they
are deliberately not fetched.
"""
import sys, time
from datetime import date
from pathlib import Path
import requests

BASE = sys.argv[1].rstrip("/")
OUT = Path.home() / "dls" / "raw" / "GlobalSecretGroup"
OUT.mkdir(parents=True, exist_ok=True)
PROXIES = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}

for path, name in (("/", "home"), ("/news/", "news")):
    body = None
    for attempt in (1, 2, 3):
        try:
            r = requests.get(BASE + path, proxies=PROXIES, timeout=120)
            r.raise_for_status()
            body = r.text
            break
        except Exception as e:
            print(f"{path} attempt {attempt} failed: {e}")
            time.sleep(10)
    if body is None:
        print(f"{path} failed 3 times")
        sys.exit(1)
    f = OUT / f"{date.today()}_{name}.html"
    f.write_text(body, encoding="utf-8")
    print(f"{path}: {len(body)} bytes, {body.count('class=\"project-card')} project cards -> {f}")
    time.sleep(3)
