#!/usr/bin/env python3
"""Parse saved DragonForce blog/posts JSON pages into a CSV of victim posts.

Usage:
    python3 dragonforce_parse.py ~/dls/raw/DragonForce/*.json -o ~/dls/raw/DragonForce/dragonforce.csv

The API reports data volume in bytes (the "weight" field), which is converted
to GB here. Rows are deduplicated by publication uuid.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

GB = 1000 ** 3   # decimal GB, matching the site's own "400 GB+" labels


def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def iso_date(value):
    return str(value)[:10] if value else ""


def parse_file(path):
    data = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    items = (data.get("data") or {}).get("publications") or []
    rows = []
    for p in items:
        desc_full = str(p.get("description") or "")
        # The first line is the group's own summary label, e.g. "Full DATA 400 GB+".
        headline = clean(desc_full.split("\n")[0]) if desc_full.strip() else ""
        try:
            weight = int(p.get("weight") or 0)   # the API sends this as a string
        except (TypeError, ValueError):
            weight = 0

        rows.append({
            "group": "dragonforce",
            "victim": clean(p.get("name")),
            "website": clean(p.get("website")),
            "address": clean(p.get("address")),
            "data_size_bytes": weight or "",
            "data_size_gb": round(weight / GB, 2) if weight else "",
            "tags": "; ".join(clean(t.get("tag") if isinstance(t, dict) else t)
                              for t in (p.get("tags") or [])),
            "headline": headline,
            "description": clean(desc_full),
            "post_date": iso_date(p.get("created_at")),
            "publish_deadline": iso_date(p.get("timer_publication")),
            "timer_stopped": p.get("is_timer_publication_stopped"),
            "uuid": clean(p.get("uuid")),
            "source_file": Path(path).name,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="saved blog/posts JSON pages")
    ap.add_argument("-o", "--output", default="dragonforce.csv")
    args = ap.parse_args()

    seen, rows, dupes = set(), [], 0
    # Newest capture first so current timer/status fields win.
    for f in sorted(args.files, reverse=True):
        for row in parse_file(f):
            if row["uuid"] in seen:
                dupes += 1
                continue
            seen.add(row["uuid"])
            rows.append(row)

    if not rows:
        sys.exit("No publications found - are these saved API pages?")

    rows.sort(key=lambda r: r["post_date"], reverse=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dates = [r["post_date"] for r in rows if r["post_date"]]
    sizes = [r["data_size_gb"] for r in rows if isinstance(r["data_size_gb"], float)]
    print(f"files parsed:      {len(args.files)}")
    print(f"victims written:   {len(rows)}  ({dupes} duplicates skipped)")
    print(f"with data size:    {len(sizes)}"
          + (f"  (total {round(sum(sizes) / 1024, 1)} TB)" if sizes else ""))
    print(f"with tags:         {sum(1 for r in rows if r['tags'])}")
    if dates:
        print(f"date range:        {min(dates)} .. {max(dates)}")
    print(f"output:            {args.output}")


if __name__ == "__main__":
    main()
