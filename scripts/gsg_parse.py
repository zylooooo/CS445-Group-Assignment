#!/usr/bin/env python3
"""Parse saved Global Secret Group home pages into a CSV.

Usage:
    python3 gsg_parse.py ~/dls/raw/GlobalSecretGroup/*_home.html -o globalSecretGroup.csv
        [--first-seen ~/dls/aggregator/rl_gsg.json]

Each victim is an <a class="project-card" href="/project/<id>/"> holding the name,
country, revenue, a "Key: value |" profile block and two stat counters.

The site publishes no post date anywhere on its public pages. With --first-seen,
the post date is taken from ransomlook.io's "discovered" timestamp for the same
/project/<id>/ link, and date_source records that it is an aggregator date.
"""
import argparse, csv, json, re
from pathlib import Path
from bs4 import BeautifulSoup

FIELDS = ["group", "source_id", "detail_href", "pinned", "status", "victim", "country",
          "revenue", "desc_location", "desc_website", "desc_revenue", "desc_industry",
          "desc_employees", "desc_properties", "files_checked", "data_analyzed",
          "description", "post_date", "date_source", "source_file"]

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("-o", "--out", default="globalSecretGroup.csv")
ap.add_argument("--first-seen")
args = ap.parse_args()

def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


# The site moved from numeric /project/<n>/ links to random ids, so older aggregator
# records only match by name. Link match first, normalised-name match as fallback.
first_seen, first_seen_by_name = {}, {}
if args.first_seen:
    data = json.loads(Path(args.first_seen).read_text(encoding="utf-8"))
    posts = data[1] if isinstance(data, list) else data.get("posts", [])
    for p in posts:
        day = p["discovered"][:10]
        if p.get("link"):
            first_seen[p["link"]] = min(day, first_seen.get(p["link"], day))
        key = norm(p.get("post_title", ""))
        if key:
            first_seen_by_name[key] = min(day, first_seen_by_name.get(key, day))


def text(el):
    return el.get_text(" ", strip=True) if el else ""


def profile(desc):
    """Split 'Country: X |\\nWebsite: Y | ...' into a dict."""
    out = {}
    for part in re.split(r"\s*\|\s*|\n", desc):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


rows = {}
# Newest capture last, so a later capture overwrites status and counters.
for f in sorted(args.files):
    soup = BeautifulSoup(Path(f).read_text(encoding="utf-8", errors="replace"), "html.parser")
    for card in soup.select("a.project-card"):
        href = card.get("href", "")
        pid = href.strip("/").split("/")[-1]
        desc = card.select_one(".card-description")
        desc = desc.get_text("\n", strip=True) if desc else ""
        prof = profile(desc)
        stats = {text(s.select_one(".stat-label")): text(s.select_one(".stat-value"))
                 for s in card.select(".stat")}
        country = card.select_one(".card-country")
        if country and country.select_one(".card-flag"):
            country.select_one(".card-flag").extract()
        row = {
            "group": "Global Secret Group",
            "source_id": pid,
            "detail_href": href,
            "pinned": bool(card.select_one(".pinned-badge")),
            "status": text(card.select_one(".card-status")),
            "victim": text(card.select_one(".card-title")),
            "country": text(country),
            "revenue": text(card.select_one(".card-revenue")),
            "desc_location": prof.get("country", ""),
            "desc_website": prof.get("website", ""),
            "desc_revenue": prof.get("revenue", ""),
            "desc_industry": prof.get("industry", ""),
            "desc_employees": prof.get("employees", ""),
            "desc_properties": prof.get("properties", ""),
            "files_checked": stats.get("Files Checked", "").replace(",", ""),
            "data_analyzed": stats.get("Data Analyzed", ""),
            "description": desc,
            "post_date": "",
            "date_source": "",
            "source_file": Path(f).name,
        }
        day = first_seen.get(href) or first_seen_by_name.get(norm(row["victim"]))
        if day:
            row["post_date"] = day
            row["date_source"] = "aggregator first-seen (ransomlook.io)"
        rows[pid] = row

with open(args.out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows.values())

dated = sum(1 for r in rows.values() if r["post_date"])
print(f"{len(rows)} victims written to {args.out}; {dated} dated from aggregator first-seen")
