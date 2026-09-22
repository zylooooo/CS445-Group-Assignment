#!/usr/bin/env python3
"""Merge the five per-site victim CSVs into one Tableau-ready dataset.

Usage:
    python3 merge_all.py -o ~/dls/merged.csv

Each leak site exposes different fields, so this script normalises them onto a
common schema and records HOW each derived value was obtained, so stated facts
and inferred values stay distinguishable in the report.

Outputs:
    merged.csv              one row per victim post
    cross_site_victims.csv  victims claimed by more than one group (Q5)
"""
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DLS = Path.home() / "dls"
WINDOW = ("2026-01-01", "2026-09-30")

# --------------------------------------------------------------------------
# Country reference. Only the entries needed to normalise codes, names and
# country-code top level domains onto one representation.
# --------------------------------------------------------------------------
COUNTRIES = {
    "AE": "United Arab Emirates", "AR": "Argentina", "AT": "Austria",
    "AU": "Australia", "BE": "Belgium", "BD": "Bangladesh", "BG": "Bulgaria",
    "BH": "Bahrain", "BR": "Brazil", "BS": "Bahamas", "CA": "Canada",
    "CH": "Switzerland", "CL": "Chile", "CN": "China", "CO": "Colombia",
    "CR": "Costa Rica", "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany",
    "DK": "Denmark", "DO": "Dominican Republic", "EC": "Ecuador",
    "EE": "Estonia", "EG": "Egypt", "ES": "Spain", "FI": "Finland",
    "FR": "France", "GB": "United Kingdom", "GR": "Greece", "GT": "Guatemala",
    "HK": "Hong Kong", "HR": "Croatia", "HU": "Hungary", "ID": "Indonesia",
    "IE": "Ireland", "IL": "Israel", "IN": "India", "IS": "Iceland",
    "IT": "Italy", "JO": "Jordan", "JP": "Japan", "KE": "Kenya",
    "KR": "South Korea", "KW": "Kuwait", "LB": "Lebanon", "LT": "Lithuania",
    "LU": "Luxembourg", "LV": "Latvia", "MA": "Morocco", "MT": "Malta",
    "MX": "Mexico", "MY": "Malaysia", "NG": "Nigeria", "NL": "Netherlands",
    "NO": "Norway", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama",
    "PE": "Peru", "PH": "Philippines", "PK": "Pakistan", "PL": "Poland",
    "PR": "Puerto Rico", "PT": "Portugal", "QA": "Qatar", "RO": "Romania",
    "RS": "Serbia", "RU": "Russia", "SA": "Saudi Arabia", "SE": "Sweden",
    "SG": "Singapore", "SI": "Slovenia", "SK": "Slovakia", "TH": "Thailand",
    "TN": "Tunisia", "TR": "Turkey", "TW": "Taiwan", "UA": "Ukraine",
    "US": "United States", "UY": "Uruguay", "VE": "Venezuela",
    "VN": "Vietnam", "ZA": "South Africa",
}
NAME_TO_CODE = {v.lower(): k for k, v in COUNTRIES.items()}
NAME_TO_CODE.update({
    "the bahamas": "BS", "usa": "US", "u.s.": "US", "u.s.a.": "US",
    "united states of america": "US", "uk": "GB", "great britain": "GB",
    "england": "GB", "scotland": "GB", "wales": "GB", "south korea": "KR",
    "republic of korea": "KR", "czech republic": "CZ", "holland": "NL",
    "uae": "AE", "russian federation": "RU", "viet nam": "VN",
})
# Country-code TLDs that differ from the ISO code, plus generic TLDs to ignore.
TLD_OVERRIDE = {"uk": "GB", "eu": "", "su": "RU"}
GENERIC_TLD = {
    "com", "net", "org", "info", "biz", "io", "co", "app", "dev", "ai",
    "edu", "gov", "mil", "int", "xyz", "online", "site", "shop", "cloud",
}

# --------------------------------------------------------------------------
# Industry reference. Qilin states an industry outright; the other sites do
# not, so it is inferred from description text. Every row records which.
# --------------------------------------------------------------------------
INDUSTRY_KEYWORDS = [
    ("Agriculture & Food", r"agricultur|agro|farming|\bfarm\b|egg production|poultry|livestock|fertiliz|dairy|bakery|brewery|winery|fisher|food process|beverage|crop"),
    ("Healthcare", r"hospital|clinic(?:al)?\b|medical|dental|patient|pharmac|nursing|care home|physician|surgery|veterinar|dermatolog|therapy|healthcare"),
    ("Education", r"school|universit|college|academy|education|student|campus|k-12|kindergarten"),
    ("Government", r"municipal|government|ministry|city of|county of|federal agency|public sector|state agency|public institution"),
    ("Financial Services", r"\bbank(?:ing|s)?\b|credit union|financial services|investment firm|asset management|mortgage|lending|fintech|accounting firm|audit firm|brokerage"),
    ("Insurance", r"insurance|insurer|underwrit|reinsur"),
    ("Legal", r"law firm|attorney|legal services|solicitor|barrister|litigation"),
    ("Construction", r"construction|contractor|builder|roofing|plumbing|civil engineer|scaffold|excavat|heavy equipment|landscap"),
    ("Manufacturing", r"manufactur|factory|machining|fabricat|foundry|plastics|steel|assembly line|gear system|flowmeter|flow measurement|printers?\b|industrial equipment"),
    ("Retail", r"retail|supermarket|grocery|e-commerce|ecommerce|merchandise|boutique|store chain|dealership"),
    ("Technology", r"software|information technology|\bit\b services|saas|networking solutions|computing|data cent(?:er|re)|cybersecurity"),
    ("Telecommunications", r"telecommunication|telecom|internet service provider|mobile network|broadband"),
    ("Transportation & Logistics", r"logistics|freight|shipping|trucking|transport|courier|haulage|fleet|warehous"),
    ("Energy & Utilities", r"energy|utilit(?:y|ies)|electric power|power plant|petroleum|solar|wind farm|water treatment|wastewater|propane|bulk fuel|lubricant"),
    ("Real Estate", r"real estate|property management|realty|leasing|landlord|condominium"),
    ("Hospitality & Travel", r"hotel|resort|restaurant|hospitality|tourism|travel agency|catering|casino|franchise partner|fast food"),
    ("Professional Services", r"consult(?:ing|ancy)|advisory|staffing|recruitment|marketing agency|advertising|public relations|architect"),
    ("Media & Entertainment", r"media|publishing|broadcast|newspaper|entertainment|film|gaming studio"),
    ("Non-profit", r"non-profit|nonprofit|charit|\bngo\b|charitable"),
    ("Automotive", r"automotive|car dealer|auto parts|tire distribution|vehicle service"),
    ("Pharmaceuticals & Biotech", r"pharmaceutical|biotech|life sciences"),
    ("Aerospace & Defense", r"aerospace|defen[cs]e contractor|aviation|airline|aircraft"),
    ("Mining & Materials", r"mining|quarry|minerals|cement|chemical manufactur"),
]
# Markers that introduce the stolen-data inventory rather than the business
# itself. Leaving them in makes phrases like "Loan applications" classify a
# fast-food franchise as Financial Services.
CUT = re.compile(
    r"\b(total leak|leaked data|data\s*:|files?\s*,\s*[\d,]+\s*folders?"
    r"|\d[\d.,]*\s*(gb|tb|mb)\s*,)", re.I)
LEAD_SIZE = re.compile(r"^\s*(full\s+data|total)\s*[\d.,]*\s*(gb|tb|mb)\s*\+?\s*", re.I)
# Qilin's own labels mapped onto the same canonical set.
QILIN_INDUSTRY_MAP = [
    ("Healthcare", r"health|medical|hospital|pharma|dental|biotech"),
    ("Education", r"education|school|university|college"),
    ("Government", r"government|public admin|military|defense"),
    ("Financial Services", r"financ|bank|invest|accounting|capital market"),
    ("Insurance", r"insurance"),
    ("Legal", r"legal|law"),
    ("Manufacturing", r"manufactur|industrial|machinery|electronics|semiconductor|foundr"),
    ("Construction", r"construction|engineering|architect"),
    ("Retail", r"retail|grocery|consumer goods|wholesale|apparel"),
    ("Technology", r"software|technology|\bit\b|computer|internet|telecom equipment"),
    ("Telecommunications", r"telecommunication|telecom"),
    ("Transportation & Logistics", r"transport|logistics|shipping|freight|airline"),
    ("Energy & Utilities", r"energy|utilit|oil|gas|power|mining"),
    ("Real Estate", r"real estate|property"),
    ("Hospitality & Travel", r"hospitality|hotel|restaurant|travel|leisure|tourism"),
    ("Professional Services", r"business services|consulting|staffing|advertising|marketing|professional|human resource"),
    ("Media & Entertainment", r"media|entertainment|publishing|broadcast"),
    ("Non-profit", r"non-profit|nonprofit|charitable|association"),
    ("Agriculture & Food", r"agricultur|food|beverage|farming"),
    ("Automotive", r"automotive|vehicle"),
    ("Aerospace & Defense", r"aerospace|aviation"),
]
# Phrases some sites use to state the industry outright inside free text.
STATED_INDUSTRY = re.compile(r"operates in the ([A-Za-z &/,'-]{3,40}?) industry", re.I)

LEGAL_SUFFIX = re.compile(
    r"\b(inc|llc|ltd|limited|corp|corporation|co|company|gmbh|bv|nv|sa|sas|srl|"
    r"spa|ag|as|ab|oy|aps|plc|pty|pte|kk|kg|ug|sl|sarl|lda|group|holdings?)\b\.?",
    re.I,
)


def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def domain_of(*candidates):
    """First usable registrable-looking domain from any of the candidates."""
    for raw in candidates:
        v = clean(raw).lower()
        if not v:
            continue
        v = re.sub(r"^https?://", "", v)
        v = v.split("/")[0].split("?")[0].strip()
        v = re.sub(r"^www\.", "", v)
        if "." in v and " " not in v:
            return v
    return ""


def country_from_domain(domain):
    if not domain:
        return ""
    tld = domain.rsplit(".", 1)[-1]
    if tld in TLD_OVERRIDE:
        return TLD_OVERRIDE[tld]
    if tld in GENERIC_TLD:
        return ""
    code = tld.upper()
    return code if code in COUNTRIES else ""


def normalise_country(raw, domain):
    """Return (code, name, source). Stated values win over inferred ones."""
    v = clean(raw)
    if v:
        if len(v) == 2 and v.upper() in COUNTRIES:
            return v.upper(), COUNTRIES[v.upper()], "stated"
        code = NAME_TO_CODE.get(v.lower())
        if code:
            return code, COUNTRIES.get(code, v), "stated"
        return "", v, "stated"          # keep unrecognised names as given
    code = country_from_domain(domain)
    if code:
        return code, COUNTRIES[code], "inferred from domain"
    return "", "", ""


def company_text(text):
    """Drop the stolen-data inventory so only the business description remains."""
    t = clean(text)
    t = LEAD_SIZE.sub("", t)
    m = CUT.search(t)
    if m:
        t = t[:m.start()]
    return t.strip()


def normalise_industry(stated_label, text, victim=""):
    """Return (industry, source, confidence).

    A label stated by the site wins outright. Otherwise every industry is
    scored by how many distinct keywords it matches, with the victim name and
    first sentence weighted double, and the highest score wins. Scoring rather
    than first-match-wins prevents one incidental word deep in a long
    description from deciding the category.
    """
    label = clean(stated_label)
    if label:
        for name, pattern in QILIN_INDUSTRY_MAP:
            if re.search(pattern, label, re.I):
                return name, "stated by site", "high"
        return "Other", "stated by site", "high"

    body = company_text(text)
    if not body and not victim:
        return "", "", ""

    m = STATED_INDUSTRY.search(body)
    if m:
        phrase = m.group(1)
        for table in (QILIN_INDUSTRY_MAP, INDUSTRY_KEYWORDS):
            for name, pattern in table:
                if re.search(pattern, phrase, re.I):
                    return name, "stated in description", "high"

    first = body.split(".")[0]
    head = f"{victim}. {first}"
    scores = {}
    for name, pattern in INDUSTRY_KEYWORDS:
        strong = len({m.group(0).lower() for m in re.finditer(pattern, head, re.I)})
        rest = len({m.group(0).lower() for m in re.finditer(pattern, body, re.I)})
        total = strong * 2 + rest
        if total:
            scores[name] = total
    if not scores:
        return "", "", ""

    order = {n: i for i, (n, _) in enumerate(INDUSTRY_KEYWORDS)}
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], order[kv[0]]))
    top, score = ranked[0]
    runner = ranked[1][1] if len(ranked) > 1 else 0
    confidence = "high" if score >= 3 and score > runner else "low"
    return top, "inferred from description", confidence


def name_key(victim, domain):
    """Matching key: prefer the domain, else a normalised company name."""
    if domain:
        return domain
    v = clean(victim).lower()
    v = re.sub(r"https?://", "", v)
    v = LEGAL_SUFFIX.sub(" ", v)
    v = re.sub(r"[^a-z0-9]+", "", v)
    return v


def read_csv(path):
    p = Path(path)
    if not p.exists():
        print(f"  WARNING: {p} not found, skipping", file=sys.stderr)
        return []
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_rows():
    rows = []

    for r in read_csv(DLS / "raw/Qilin/qilin.csv"):
        dom = domain_of(r.get("company_url"))
        code, cname, csrc = normalise_country("", dom)
        ind, isrc, iconf = normalise_industry(r.get("industry"), "", clean(r.get("victim")))
        rows.append(dict(
            group="Qilin", victim=clean(r.get("victim")), domain=dom,
            post_date=clean(r.get("post_date")),
            country_code=code, country_name=cname, country_source=csrc,
            industry=ind, industry_source=isrc, industry_confidence=iconf,
            industry_raw=clean(r.get("industry")),
            revenue_usd="", data_size_gb="", data_categories="",
            description="", views="", status=clean(r.get("status")),
            deadline_hours="", source_id=clean(r.get("uuid")),
        ))

    for r in read_csv(DLS / "raw/Inc_Ransom/inc_ransom.csv"):
        dom = domain_of(r.get("victim"))
        code, cname, csrc = normalise_country(r.get("country"), dom)
        ind, isrc, iconf = normalise_industry("", r.get("description"), clean(r.get("victim")))
        rows.append(dict(
            group="INC Ransom", victim=clean(r.get("victim")), domain=dom,
            post_date=clean(r.get("created_date")),
            country_code=code, country_name=cname, country_source=csrc,
            industry=ind, industry_source=isrc, industry_confidence=iconf,
            industry_raw="",
            revenue_usd=clean(r.get("revenue_usd")), data_size_gb="",
            data_categories=clean(r.get("categories")),
            description=clean(r.get("description")),
            views=clean(r.get("visits")), status="",
            deadline_hours="", source_id=clean(r.get("id")),
        ))

    for r in read_csv(DLS / "raw/DragonForce/dragonforce.csv"):
        dom = domain_of(r.get("website"), r.get("address"))
        code, cname, csrc = normalise_country("", dom)
        ind, isrc, iconf = normalise_industry("", r.get("description"), clean(r.get("victim")))
        cats = "; ".join(x for x in [clean(r.get("tags")), clean(r.get("headline"))] if x)
        rows.append(dict(
            group="DragonForce", victim=clean(r.get("victim")), domain=dom,
            post_date=clean(r.get("post_date")),
            country_code=code, country_name=cname, country_source=csrc,
            industry=ind, industry_source=isrc, industry_confidence=iconf,
            industry_raw="",
            revenue_usd="", data_size_gb=clean(r.get("data_size_gb")),
            data_categories=cats, description=clean(r.get("description")),
            views="", status="", deadline_hours="",
            source_id=clean(r.get("uuid")),
        ))

    for r in read_csv(DLS / "raw/Play/play.csv"):
        dom = domain_of(r.get("website"))
        code, cname, csrc = normalise_country(r.get("country"), dom)
        rows.append(dict(
            group="Play", victim=clean(r.get("victim")), domain=dom,
            post_date=clean(r.get("added_date")),
            country_code=code, country_name=cname, country_source=csrc,
            industry="", industry_source="", industry_confidence="", industry_raw="",
            revenue_usd="", data_size_gb="", data_categories="",
            description="", views=clean(r.get("views")),
            status=clean(r.get("status")), deadline_hours="",
            source_id=clean(r.get("post_id")),
        ))

    for r in read_csv(DLS / "raw/SafePay/safepay.csv"):
        dom = domain_of(r.get("victim"))
        code, cname, csrc = normalise_country(r.get("country_code"), dom)
        text = r.get("description_full") or r.get("description")
        ind, isrc, iconf = normalise_industry("", text, clean(r.get("victim")))
        rows.append(dict(
            group="SafePay", victim=clean(r.get("victim")), domain=dom,
            post_date=clean(r.get("post_date")),
            country_code=code, country_name=cname, country_source=csrc,
            industry=ind, industry_source=isrc, industry_confidence=iconf,
            industry_raw="",
            revenue_usd="", data_size_gb="", data_categories="",
            description=clean(text), views=clean(r.get("views")),
            status=clean(r.get("status")),
            deadline_hours=clean(r.get("deadline_hours")),
            source_id=clean(r.get("post_id")),
        ))

    for row in rows:
        row["match_key"] = name_key(row["victim"], row["domain"])
        row["in_window"] = "yes" if WINDOW[0] <= row["post_date"] <= WINDOW[1] else "no"
        row["post_month"] = row["post_date"][:7] if row["post_date"] else ""
    return rows


def cross_site(rows):
    """Victims claimed by more than one group.

    Matches across the FULL dataset, not only the window, because a victim
    listed by group A before the window and re-listed by group B inside it is
    itself a Q5 signal. Each posting keeps its own in_window flag, and at least
    one posting must fall in the window for the match to be reported.
    """
    by_key = defaultdict(list)
    for r in rows:
        if r["match_key"]:
            by_key[r["match_key"]].append(r)
    out = []
    for key, hits in by_key.items():
        groups = sorted({h["group"] for h in hits})
        if len(groups) < 2:
            continue
        if not any(h["in_window"] == "yes" for h in hits):
            continue
        for h in sorted(hits, key=lambda x: x["post_date"]):
            out.append({
                "match_key": key, "groups": ", ".join(groups),
                "n_groups": len(groups), "group": h["group"],
                "victim": h["victim"], "post_date": h["post_date"],
                "in_window": h["in_window"],
                "country_name": h["country_name"], "domain": h["domain"],
            })
    return sorted(out, key=lambda r: (r["match_key"], r["post_date"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=str(DLS / "merged.csv"))
    ap.add_argument("--cross", default=str(DLS / "cross_site_victims.csv"))
    args = ap.parse_args()

    rows = build_rows()
    if not rows:
        sys.exit("No input rows found - check the per-site CSV paths.")

    fields = ["group", "victim", "domain", "match_key", "post_date", "post_month",
              "in_window", "country_code", "country_name", "country_source",
              "industry", "industry_source", "industry_confidence",
              "industry_raw", "revenue_usd",
              "data_size_gb", "data_categories", "views", "status",
              "deadline_hours", "description", "source_id"]
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["group"], x["post_date"]), reverse=True):
            w.writerow(r)

    matches = cross_site(rows)
    if matches:
        with open(args.cross, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(matches[0].keys()))
            w.writeheader()
            w.writerows(matches)

    win = [r for r in rows if r["in_window"] == "yes"]
    print(f"total rows:            {len(rows)}")
    print(f"in window {WINDOW[0]} to {WINDOW[1]}: {len(win)}")
    print()
    print("per group (in window):")
    for g, n in Counter(r["group"] for r in win).most_common():
        print(f"  {g:<14} {n}")
    print()
    cs = Counter(r["country_source"] for r in win if r["country_source"])
    print(f"country known:         {sum(cs.values())} of {len(win)}"
          f"  (stated {cs.get('stated', 0)}, inferred {cs.get('inferred from domain', 0)})")
    print(f"distinct countries:    {len({r['country_name'] for r in win if r['country_name']})}")
    isrc = Counter(r["industry_source"] for r in win if r["industry_source"])
    print(f"industry known:        {sum(isrc.values())} of {len(win)}")
    for k, v in isrc.most_common():
        print(f"    {k:<26} {v}")
    iconf = Counter(r["industry_confidence"] for r in win if r["industry_confidence"])
    print("    confidence: " + ", ".join(f"{k} {v}" for k, v in iconf.most_common()))
    print(f"with revenue:          {sum(1 for r in win if r['revenue_usd'])}")
    print(f"with data size:        {sum(1 for r in win if r['data_size_gb'])}")
    print(f"with views:            {sum(1 for r in win if r['views'])}")
    print()
    keys = {r["match_key"] for r in matches}
    print(f"victims claimed by more than one group: {len(keys)}"
          f"  ({len(matches)} rows) -> {args.cross}")
    print(f"output:                {args.output}")


if __name__ == "__main__":
    main()
