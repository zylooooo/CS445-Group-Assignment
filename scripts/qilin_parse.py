#!/usr/bin/env python3
"""Parse saved Qilin DLS listing pages into a CSV of victim posts.

Usage:
    python3 qilin_parse.py ~/dls/raw/Qilin/*.html -o ~/dls/raw/Qilin/qilin.csv

Reads one or more saved HTML files, extracts every victim card, and writes
one row per unique victim (deduplicated by the post's uuid across files).
"""
import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

DATE_RE = re.compile(r"([A-Z][a-z]{2})[a-z]* (\d{1,2}), (\d{4})")
PHOTOS_RE = re.compile(r"(\d+)\s*photos", re.I)


def uuid_from_href(href):
    if not href:
        return ""
    qs = parse_qs(urlparse(href).query)
    return qs.get("uuid", [""])[0]


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def parse_file(path):
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8", errors="replace"), "html.parser")

    # Map uuid -> countdown seconds, via each "Learn More" anchor's own column.
    countdowns = {}
    for more in soup.find_all("a", class_="learn_more"):
        uid = uuid_from_href(more.get("href"))
        col = more.find_parent("div", class_="col-md-6")
        timer = col.select_one(".countdown-timer") if col else None
        if uid and timer and timer.get("data-remaining"):
            try:
                countdowns[uid] = int(float(timer["data-remaining"]))
            except ValueError:
                pass

    rows = []
    for title in soup.find_all("a", class_="item_box-title"):
        uid = uuid_from_href(title.get("href"))
        card = title.find_parent("div")  # the col-md-10 block holding the card's fields

        industry = ""
        info = card.find("p", class_="item_box-info") if card else None
        if info:
            industry = clean(info.get_text())
            if industry == "0":   # the site prints "0" when no industry is set
                industry = ""

        company_url = ""
        link = card.find("a", class_="item_box-info__link") if card else None
        if link:
            company_url = clean(link.get("href", ""))

        post_date = ""
        for icon in card.find_all("img", src=re.compile(r"clock\.png$")) if card else []:
            m = DATE_RE.search(icon.parent.get_text())
            if m:
                post_date = datetime.strptime(" ".join(m.groups()), "%b %d %Y").strftime("%Y-%m-%d")
                break

        photos = ""
        m = PHOTOS_RE.search(card.get_text()) if card else None
        if m:
            photos = m.group(1)

        remaining = countdowns.get(uid)
        rows.append({
            "group": "qilin",
            "victim": clean(title.get_text()),
            "industry": industry,
            "company_url": company_url,
            "post_date": post_date,
            "photos": photos,
            "status": "pending" if remaining is not None else "published",
            "countdown_hours_left": remaining // 3600 if remaining is not None else "",
            "uuid": uid,
            "source_file": Path(path).name,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="saved listing-page HTML files")
    ap.add_argument("-o", "--output", default="qilin.csv")
    args = ap.parse_args()

    seen, rows, dupes = set(), [], 0
    # Newest capture first (filenames start with the capture date), so current
    # status wins over older captures.
    for f in sorted(args.files, reverse=True):
        for row in parse_file(f):
            if row["uuid"] in seen:
                dupes += 1
                continue
            seen.add(row["uuid"])
            rows.append(row)

    if not rows:
        sys.exit("No victim cards found - is this a saved Qilin listing page?")

    rows.sort(key=lambda r: r["post_date"], reverse=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dates = [r["post_date"] for r in rows if r["post_date"]]
    pending = sum(1 for r in rows if r["status"] == "pending")
    print(f"files parsed:      {len(args.files)}")
    print(f"victims written:   {len(rows)}  ({dupes} duplicates skipped)")
    print(f"pending/published: {pending}/{len(rows) - pending}")
    if dates:
        print(f"date range:        {min(dates)} .. {max(dates)}")
    print(f"output:            {args.output}")


if __name__ == "__main__":
    main()
