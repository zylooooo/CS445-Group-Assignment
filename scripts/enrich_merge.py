#!/usr/bin/env python3
"""Fill blanks in data_v3/merged.csv from web-research results, with provenance.

Usage:
    python3 scripts/enrich_merge.py [--results ~/dls/enrich/results] [--out data_v3]

Reads the per-batch JSON results produced by the research step (see
data_v3/cross_reference/ENRICHMENT.md) and writes, into data_v3/cross_reference/:

    merged_enriched.csv   merged.csv with blanks filled, plus one <field>_origin column per
                          enriched field: "leak site", "web", "web estimate" or blank
    enrichment_log.csv    one row per filled cell: value, source URL, name, type, date,
                          confidence. The audit trail behind every web-sourced value.
    data_quality_flags.csv  leak-site values that research suggests are wrong (e.g. a
                          US firm listed as GE). Reported only; merged values unchanged.

merged.csv itself is never modified. Every result is validated first, and anything that
fails is rejected and counted, never silently written:
  - the field must be blank in merged.csv (leak-site values always win)
  - the value must match the column's format (ISO code, canonical industry, number)
  - a source URL is required
  - breach facts (data_size_gb, data_types) need a source dated 2026-01-01..2026-09-30
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_v3 import COUNTRIES, FIELDS as BASE_FIELDS, write_csv  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WINDOW = ("2026-01-01", "2026-09-30")
ENRICHED = ["website", "country", "industry", "revenue_usd", "employee_count",
            "data_size_gb", "data_types"]
BREACH = {"data_size_gb", "data_types"}
INDUSTRIES = {
    "Manufacturing", "Professional Services", "Construction", "Healthcare",
    "Financial Services", "Legal", "Retail & Wholesale", "Engineering & Architecture",
    "Hospitality & Travel", "Education", "Agriculture & Food", "Technology",
    "Transportation & Logistics", "Energy & Utilities", "Government", "Real Estate",
    "Insurance", "Automotive", "Non-profit", "Consumer Services", "Media & Entertainment",
    "Pharmaceuticals & Biotech", "Mining & Materials", "Aerospace & Defense",
    "Telecommunications", "Holding Companies"}
DATA_TYPES = {
    "Personal data (PII)", "Employee / HR", "Customer data", "Financial / accounting",
    "Medical / health (PHI)", "Legal / contracts", "Corporate / confidential",
    "Email / correspondence", "Databases / backups", "Engineering / R&D / IP",
    "Student / education records"}
SOURCE_TYPES = {"official", "news", "reference", "estimate"}


def validate(field, value):
    """Return the normalised value, or None if it doesn't fit the column."""
    if value in (None, ""):
        return None
    v = str(value).strip()
    if field == "website":
        v = re.sub(r"^https?://", "", v.lower()).split("/")[0]
        v = re.sub(r"^www\.", "", v)
        return v if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", v) else None
    if field == "country":
        v = {"UK": "GB"}.get(v.upper(), v.upper())
        return v if v in COUNTRIES else None
    if field == "industry":
        return v if v in INDUSTRIES else None
    if field == "revenue_usd":
        try:
            n = int(float(v.replace(",", "").replace("$", "")))
        except ValueError:
            return None
        return n if n > 0 else None
    if field == "employee_count":
        v = v.replace(",", "").replace(" ", "")
        return v if re.fullmatch(r"\d+(-\d+)?\+?", v) else None
    if field == "data_size_gb":
        try:
            n = round(float(v), 2)
        except ValueError:
            return None
        return n if n > 0 else None
    if field == "data_types":
        parts = [p.strip() for p in v.split(";") if p.strip()]
        return "; ".join(p for p in parts if p in DATA_TYPES) or None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(Path.home() / "dls/enrich/results"))
    ap.add_argument("--out", default=str(REPO / "data_v3"))
    args = ap.parse_args()
    src = Path(args.out)
    out = src / "cross_reference"   # kept apart from the leak-site-only dataset
    out.mkdir(parents=True, exist_ok=True)

    with open(src / "merged.csv", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    by_id = {f"{r['group']}|{r['source_id']}": r for r in rows}
    for r in rows:
        for f in ENRICHED:
            r[f"{f}_origin"] = "leak site" if r[f] else ""

    log, flags, rejected = [], [], Counter()
    files = sorted(Path(args.results).glob("batch_*.json"))
    for fpath in files:
        try:
            results = json.loads(fpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  WARNING: {fpath.name} is not valid JSON ({e}), skipped")
            continue
        for res in results:
            row = by_id.get(res.get("row_id"))
            if row is None:
                rejected["unknown row_id"] += 1
                continue
            # Suspected errors in leak-site values are reported, never applied.
            for field, info in (res.get("suspected_errors") or {}).items():
                field = field.removeprefix("known_")
                if isinstance(info, dict) and str(info.get("source_url", "")).startswith("http"):
                    flags.append({"row_id": res["row_id"], "group": row["group"],
                                  "victim": row["victim"], "field": field,
                                  "leak_site_value": row.get(field, ""),
                                  "suggested_value": info.get("value", ""),
                                  "source_url": info["source_url"],
                                  "source_name": info.get("source_name", ""),
                                  "notes": str(res.get("notes") or "")[:500]})
            for field, info in (res.get("fields") or {}).items():
                if field not in ENRICHED or not isinstance(info, dict):
                    rejected["unknown field"] += 1
                    continue
                if row[field]:
                    rejected["field already known from leak site"] += 1
                    continue
                value = validate(field, info.get("value"))
                if value is None:
                    rejected[f"bad {field} format"] += 1
                    continue
                url = str(info.get("source_url") or "").strip()
                if not url.startswith("http") or ".onion" in url:
                    rejected["missing or invalid source_url"] += 1
                    continue
                sdate = str(info.get("source_date") or "undated").strip()[:10]
                if field in BREACH and not (WINDOW[0] <= sdate <= WINDOW[1]):
                    rejected["breach fact sourced outside Jan-Sep 2026"] += 1
                    continue
                stype = info.get("source_type") if info.get("source_type") in SOURCE_TYPES else "reference"
                row[field] = value
                row[f"{field}_origin"] = "web estimate" if stype == "estimate" else "web"
                if field == "country":
                    row["country_name"] = COUNTRIES[value]
                    row["country_source"] = "web research"
                if field == "industry":
                    row["industry_source"] = "web research"
                log.append({
                    "row_id": res["row_id"], "group": row["group"], "victim": row["victim"],
                    "field": field, "value": value, "source_url": url,
                    "source_name": str(info.get("source_name") or "").strip(),
                    "source_type": stype, "source_date": sdate,
                    "confidence": info.get("confidence") if info.get("confidence") in
                    ("high", "medium", "low") else "low",
                    "notes": str(res.get("notes") or "").strip()[:500],
                })

    fields = BASE_FIELDS + [f"{f}_origin" for f in ENRICHED]
    write_csv(out / "merged_enriched.csv", rows, fields)
    write_csv(out / "enrichment_log.csv", log,
              ["row_id", "group", "victim", "field", "value", "source_url", "source_name",
               "source_type", "source_date", "confidence", "notes"])

    write_csv(out / "data_quality_flags.csv", flags,
              ["row_id", "group", "victim", "field", "leak_site_value", "suggested_value",
               "source_url", "source_name", "notes"])

    print(f"result files: {len(files)}   cells filled: {len(log)}   "
          f"suspected leak-site errors flagged: {len(flags)}")
    print(f"{'field':<16}{'before':>8}{'filled':>8}{'after':>8}  of {len(rows)}")
    filled = Counter(e["field"] for e in log)
    for f in ENRICHED:
        after = sum(1 for r in rows if r[f])
        print(f"{f:<16}{after - filled[f]:>8}{filled[f]:>8}{after:>8}")
    print("by source type:", dict(Counter(e["source_type"] for e in log)))
    print("by confidence: ", dict(Counter(e["confidence"] for e in log)))
    if rejected:
        print("rejected:", dict(rejected))


if __name__ == "__main__":
    main()
