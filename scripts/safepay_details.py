#!/usr/bin/env python3
"""Fill in SafePay post dates by fetching each victim's detail page.

Published victims lose their countdown bar, and with it the only date on the
listing page, so the date is read from the detail page instead.

Usage:
    python3 safepay_details.py IN.csv OUT.csv --base http://<mirror>.onion

Detail pages are cached under ~/dls/raw/SafePay/details/ so the script can be
re-run cheaply and the raw evidence is preserved.
"""
import argparse
import csv
import random
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup

DATETIME = re.compile(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})")
CLICKS = re.compile(r"(\d[\d\s,]*)\s*clicks", re.I)
CACHE = Path.home() / "dls" / "raw" / "SafePay" / "details"


def slug(detail_path):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", detail_path.strip("/")) or "index"


def parse_detail(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text("\n", strip=True)

    date, dt = "", ""
    m = DATETIME.search(text)
    if m:
        date, dt = m.group(1), f"{m.group(1)} {m.group(2)}"

    clicks = ""
    m = CLICKS.search(text)
    if m:
        clicks = re.sub(r"[^\d]", "", m.group(1))

    body = ""
    holder = soup.select_one(".post-body") or soup.select_one(".container")
    if holder:
        body = re.sub(r"\s+", " ", holder.get_text(" ", strip=True)).strip()

    return date, dt, clicks, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--base", help="site base URL; omit to parse cached pages only")
    ap.add_argument("--offline", action="store_true", help="never fetch, cache only")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(args.infile, encoding="utf-8")))
    if not rows:
        sys.exit("input CSV is empty")

    session = None
    if args.base and not args.offline:
        import requests
        session = requests.Session()
        session.proxies.update({"http": "socks5h://127.0.0.1:9050",
                                "https": "socks5h://127.0.0.1:9050"})

    filled = fetched = cached = failed = 0
    for i, row in enumerate(rows, 1):
        path = (row.get("detail_path") or "").strip()
        if not path:
            continue

        f = CACHE / f"{slug(path)}.html"
        if not f.exists() and session:
            url = args.base.rstrip("/") + path
            for attempt in (1, 2, 3):
                try:
                    r = session.get(url, timeout=120)
                    r.raise_for_status()
                    f.write_text(r.text, encoding="utf-8")
                    fetched += 1
                    break
                except Exception as e:
                    if attempt == 3:
                        print(f"[{i}/{len(rows)}] failed {path}: {e}")
                        failed += 1
                    else:
                        time.sleep(8)
            time.sleep(2 + random.random() * 3)
        elif f.exists():
            cached += 1

        if not f.exists():
            continue

        date, dt, clicks, body = parse_detail(f.read_text(encoding="utf-8", errors="replace"))
        if date and not row.get("post_date"):
            row["post_date"] = date
            filled += 1
        row["post_datetime"] = dt
        row["clicks"] = clicks
        if body and len(body) > len(row.get("description", "")):
            row["description_full"] = body

        if i % 25 == 0:
            print(f"[{i}/{len(rows)}] fetched {fetched}, cached {cached}, dates filled {filled}")

    fields = list(rows[0].keys())
    for extra in ("post_datetime", "clicks", "description_full"):
        if extra not in fields:
            fields.append(extra)

    with open(args.outfile, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

    dated = [r["post_date"] for r in rows if r.get("post_date")]
    print()
    print(f"rows:            {len(rows)}")
    print(f"pages fetched:   {fetched} (cached {cached}, failed {failed})")
    print(f"dates filled in: {filled}")
    print(f"rows with date:  {len(dated)} of {len(rows)}")
    if dated:
        print(f"date range:      {min(dated)} .. {max(dated)}")
    print(f"output:          {args.outfile}")


if __name__ == "__main__":
    main()
