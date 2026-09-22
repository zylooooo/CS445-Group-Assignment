#!/usr/bin/env python3
"""Parse saved INC Ransom announcements JSON pages into a CSV of victim posts.

Usage:
    python3 inc_parse.py ~/dls/raw/inc_ransom/*.json -o ~/dls/raw/Inc_Ransom/inc_ransom.csv

The site's API returns URL-encoded strings and millisecond timestamps, so both
are normalised here. Rows are deduplicated by the announcement _id.
"""
import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

MD_LINK = re.compile(r"^\[([^\]]+)\]\(.*\)$")


def dec(value):
    """URL-decode and tidy whitespace."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unquote(str(value))).strip()


def clean_name(raw):
    """Company names are sometimes markdown links; keep the visible label."""
    name = dec(raw)
    m = MD_LINK.match(name)
    return m.group(1).strip() if m else name


def ts_to_date(ms):
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def parse_file(path):
    data = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    items = data.get("payload", {}).get("announcements", [])
    rows = []
    for a in items:
        company = a.get("company") or {}
        leak_ms, created_ms = a.get("leakAt"), a.get("createdAt")

        # Negative = leak date predates the post being created, which can flag
        # recycled or backdated material (Q5).
        offset_days = ""
        if leak_ms and created_ms:
            offset_days = round((leak_ms - created_ms) / 86_400_000, 1)

        rows.append({
            "group": "inc_ransom",
            "victim": clean_name(company.get("company_name")),
            "country": dec(company.get("country")),
            "revenue_usd": company.get("revenue") if company.get("revenue") else "",
            "categories": "; ".join(dec(c) for c in (a.get("categories") or [])),
            "n_categories": len(a.get("categories") or []),
            "description": " ".join(dec(d) for d in (a.get("description") or [])),
            "visits": a.get("visits", ""),
            "leak_date": ts_to_date(leak_ms),
            "created_date": ts_to_date(created_ms),
            "updated_date": ts_to_date(a.get("updatedAt")),
            "leak_minus_created_days": offset_days,
            "id": a.get("_id", ""),
            "source_file": Path(path).name,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="saved announcements JSON pages")
    ap.add_argument("-o", "--output", default="inc_ransom.csv")
    args = ap.parse_args()

    seen, rows, dupes = set(), [], 0
    for f in sorted(args.files):
        for row in parse_file(f):
            if row["id"] in seen:
                dupes += 1
                continue
            seen.add(row["id"])
            rows.append(row)

    if not rows:
        sys.exit("No announcements found - are these saved API pages?")

    rows.sort(key=lambda r: r["created_date"], reverse=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dates = [r["created_date"] for r in rows if r["created_date"]]
    countries = {r["country"] for r in rows if r["country"]}
    with_rev = sum(1 for r in rows if r["revenue_usd"] != "")
    backdated = sum(1 for r in rows
                    if isinstance(r["leak_minus_created_days"], float)
                    and r["leak_minus_created_days"] < -30)
    print(f"files parsed:      {len(args.files)}")
    print(f"victims written:   {len(rows)}  ({dupes} duplicates skipped)")
    print(f"with country:      {sum(1 for r in rows if r['country'])}  "
          f"({len(countries)} distinct)")
    print(f"with revenue:      {with_rev}")
    print(f"leak >30d before created (possible recycled): {backdated}")
    if dates:
        print(f"created range:     {min(dates)} .. {max(dates)}")
    print(f"output:            {args.output}")


if __name__ == "__main__":
    main()
