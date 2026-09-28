#!/usr/bin/env python3
"""Parse saved SafePay listing pages into a CSV of victim posts.

Usage:
    python3 safepay_parse.py ~/dls/raw/SafePay/*.html -o ~/dls/raw/SafePay/safepay_listing.csv

The countdown bar carries both the start and end of the extortion deadline, so
the deadline length in hours is derived here. Rows are deduplicated by the
site's own post id, falling back to the detail-page slug.
"""
import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def parse_ts(value):
    if not value:
        return None
    try:
        # Python < 3.11 rejects a trailing "Z"; normalise to naive UTC so
        # created/end can always be subtracted.
        ts = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return ts.astimezone(timezone.utc).replace(tzinfo=None) if ts.tzinfo else ts
    except ValueError:
        return None


def parse_file(path):
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8", errors="replace"), "html.parser")
    rows = []
    for card in soup.select(".card"):
        title = card.select_one(".card-title")
        if not title:
            continue

        flag = card.select_one("img.country-flag")
        country = clean(flag.get("alt")) if flag else ""

        body = card.select_one(".card-text")
        bar = card.select_one(".countdown-bar")
        created = parse_ts(bar.get("data-created")) if bar else None
        end = parse_ts(bar.get("data-end")) if bar else None

        deadline_hours = ""
        if created and end:
            deadline_hours = round((end - created).total_seconds() / 3600, 1)

        views = ""
        badge = card.select_one(".card-footer .badge")
        if badge:
            digits = re.sub(r"[^\d]", "", badge.get_text())
            views = digits or ""

        link = card.select_one(".card-footer a")
        detail = clean(link.get("href")) if link else ""

        published = card.select_one(".published-text")
        published_text = clean(published.get_text()) if published else ""

        # The countdown bar disappears once a victim is published, so its post id is
        # not stable across captures. The detail path is, so dedup on that.
        post_id = detail or (bar.get("data-post-id") if bar else "")

        rows.append({
            "group": "safepay",
            "victim": clean(title.get_text()),
            "country_code": country,
            "description": clean(body.get_text()) if body else "",
            "post_date": created.strftime("%Y-%m-%d") if created else "",
            "deadline_date": end.strftime("%Y-%m-%d") if end else "",
            "deadline_hours": deadline_hours,
            "status": "published" if published_text else "pending",
            "views": views,
            "detail_path": detail,
            "post_id": clean(str(post_id)),
            "source_file": Path(path).name,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="saved listing-page HTML files")
    ap.add_argument("-o", "--output", default="safepay.csv")
    args = ap.parse_args()

    seen, rows, dupes = set(), [], 0
    # Newest capture first (filenames start with the capture date), so the
    # current status and view count win over older captures.
    for f in sorted(args.files, reverse=True):
        for row in parse_file(f):
            key = row["post_id"] or row["victim"].lower()
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            rows.append(row)

    if not rows:
        sys.exit("No victim cards found - is this a saved SafePay listing page?")

    rows.sort(key=lambda r: r["post_date"], reverse=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dates = [r["post_date"] for r in rows if r["post_date"]]
    countries = {r["country_code"] for r in rows if r["country_code"]}
    hours = [r["deadline_hours"] for r in rows if isinstance(r["deadline_hours"], float)]
    pending = sum(1 for r in rows if r["status"] == "pending")
    print(f"files parsed:      {len(args.files)}")
    print(f"victims written:   {len(rows)}  ({dupes} duplicates skipped)")
    print(f"with country:      {sum(1 for r in rows if r['country_code'])}  "
          f"({len(countries)} distinct)")
    print(f"pending/published: {pending}/{len(rows) - pending}")
    if hours:
        print(f"deadline hours:    min {min(hours)}, median "
              f"{sorted(hours)[len(hours) // 2]}, max {max(hours)}")
    if dates:
        print(f"date range:        {min(dates)} .. {max(dates)}")
    print(f"output:            {args.output}")


if __name__ == "__main__":
    main()
