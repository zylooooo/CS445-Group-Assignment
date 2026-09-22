#!/usr/bin/env python3
"""Parse saved Play listing pages into a CSV of victim posts.

Usage:
    python3 play_parse.py ~/dls/raw/Play/*.html -o ~/dls/raw/Play/play.csv

The site emits minified, unclosed HTML, so each victim block is isolated by its
viewtopic() id and fields are read with targeted patterns rather than a DOM
walk. Rows are deduplicated by that id.
"""
import argparse
import csv
import html
import re
import sys
from pathlib import Path

BLOCK = re.compile(r"onclick=\"viewtopic\('([^']+)'\)\"[^>]*>(.*?)(?=onclick=\"viewtopic\(|</tr>|</table>)", re.S)
NAME = re.compile(r"^(.*?)(?:<div|<i|$)", re.S)
COUNTRY = re.compile(r"class='location'></i>(.*?)(?:<div|<i|$)", re.S)
LINK = re.compile(r"class='link'></i>(.*?)(?:<div|<i|$)", re.S)
VIEWS = re.compile(r"views:\s*([\d,]+)", re.I)
ADDED = re.compile(r"added:\s*(\d{4}-\d{2}-\d{2})", re.I)
PUBDATE = re.compile(r"publication date:\s*(\d{4}-\d{2}-\d{2})", re.I)
STATUS = re.compile(r"<h\s+style=[^>]*>([^<]*)", re.I)
MD_LINK = re.compile(r"^\[([^\]]+)\]\(.*\)$")
TAGS = re.compile(r"<[^>]+>")


def clean(text):
    text = html.unescape(text or "")
    text = TAGS.sub(" ", text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def strip_md(text):
    m = MD_LINK.match(text)
    return m.group(1).strip() if m else text


def first(pattern, blob):
    m = pattern.search(blob)
    return clean(m.group(1)) if m else ""


def parse_file(path):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    rows = []
    for post_id, blob in BLOCK.findall(raw):
        status = first(STATUS, blob).upper()
        rows.append({
            "group": "play",
            "victim": first(NAME, blob),
            "country": first(COUNTRY, blob),
            "website": strip_md(first(LINK, blob)),
            "views": (first(VIEWS, blob) or "").replace(",", ""),
            "added_date": first(ADDED, blob),
            "publication_date": first(PUBDATE, blob),
            "status": status.lower().replace(" ", "_") if status else "",
            "post_id": post_id,
            "source_file": Path(path).name,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="saved listing-page HTML files")
    ap.add_argument("-o", "--output", default="play.csv")
    args = ap.parse_args()

    seen, rows, dupes = set(), [], 0
    for f in sorted(args.files):
        for row in parse_file(f):
            if row["post_id"] in seen:
                dupes += 1
                continue
            seen.add(row["post_id"])
            rows.append(row)

    if not rows:
        sys.exit("No victim blocks found - is this a saved Play listing page?")

    rows.sort(key=lambda r: r["added_date"], reverse=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dates = [r["added_date"] for r in rows if r["added_date"]]
    countries = {r["country"] for r in rows if r["country"]}
    pub = sum(1 for r in rows if r["status"] == "published")
    print(f"files parsed:      {len(args.files)}")
    print(f"victims written:   {len(rows)}  ({dupes} duplicates skipped)")
    print(f"with country:      {sum(1 for r in rows if r['country'])}  "
          f"({len(countries)} distinct)")
    print(f"published/other:   {pub}/{len(rows) - pub}")
    if dates:
        print(f"added range:       {min(dates)} .. {max(dates)}")
    print(f"output:            {args.output}")


if __name__ == "__main__":
    main()
