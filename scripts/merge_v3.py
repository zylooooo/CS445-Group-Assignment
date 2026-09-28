#!/usr/bin/env python3
"""Merge the five per-site victim CSVs into data_v3/, Tableau-ready.

Usage:
    python3 scripts/merge_v3.py [--out data_v3]

Sites: Qilin, INC Ransom, DragonForce, SafePay, Global Secret Group.

Inputs are the per-site CSVs written by the parsers under ~/dls/raw/ (the
current capture) plus the earlier capture kept in data/ and data_v2/. The two
are unioned on each site's own post id, so a victim the group has since removed
from its site is kept, with still_listed = "no".

Only posts dated 1 Jan 2026 to 30 Sep 2026 are written. Rows with no date are
dropped and counted in the printed report.

Outputs (all UTF-8 with BOM so Excel opens them without mangling the text):
    merged.csv, merged.xlsx      one row per victim post
    <group>.csv                  the same rows split per site
    cross_site_victims.csv       victims listed by more than one group
"""
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW = Path.home() / "dls" / "raw"
WINDOW = ("2026-01-01", "2026-09-30")

# --------------------------------------------------------------------------
# Countries: full ISO 3166-1 alpha-2 table, so no stated code is ever dropped.
# --------------------------------------------------------------------------
_ISO = """AD Andorra|AE United Arab Emirates|AF Afghanistan|AG Antigua and Barbuda|AI Anguilla|AL Albania|AM Armenia|AO Angola|AR Argentina|AS American Samoa|AT Austria|AU Australia|AW Aruba|AZ Azerbaijan|BA Bosnia and Herzegovina|BB Barbados|BD Bangladesh|BE Belgium|BF Burkina Faso|BG Bulgaria|BH Bahrain|BI Burundi|BJ Benin|BM Bermuda|BN Brunei|BO Bolivia|BR Brazil|BS Bahamas|BT Bhutan|BW Botswana|BY Belarus|BZ Belize|CA Canada|CD DR Congo|CF Central African Republic|CG Congo|CH Switzerland|CI Cote d'Ivoire|CL Chile|CM Cameroon|CN China|CO Colombia|CR Costa Rica|CU Cuba|CV Cabo Verde|CW Curacao|CY Cyprus|CZ Czechia|DE Germany|DJ Djibouti|DK Denmark|DM Dominica|DO Dominican Republic|DZ Algeria|EC Ecuador|EE Estonia|EG Egypt|ER Eritrea|ES Spain|ET Ethiopia|FI Finland|FJ Fiji|FO Faroe Islands|FR France|GA Gabon|GB United Kingdom|GD Grenada|GE Georgia|GF French Guiana|GG Guernsey|GH Ghana|GI Gibraltar|GL Greenland|GM Gambia|GN Guinea|GP Guadeloupe|GQ Equatorial Guinea|GR Greece|GT Guatemala|GU Guam|GY Guyana|HK Hong Kong|HN Honduras|HR Croatia|HT Haiti|HU Hungary|ID Indonesia|IE Ireland|IL Israel|IM Isle of Man|IN India|IQ Iraq|IR Iran|IS Iceland|IT Italy|JE Jersey|JM Jamaica|JO Jordan|JP Japan|KE Kenya|KG Kyrgyzstan|KH Cambodia|KN Saint Kitts and Nevis|KR South Korea|KW Kuwait|KY Cayman Islands|KZ Kazakhstan|LA Laos|LB Lebanon|LC Saint Lucia|LI Liechtenstein|LK Sri Lanka|LR Liberia|LS Lesotho|LT Lithuania|LU Luxembourg|LV Latvia|LY Libya|MA Morocco|MC Monaco|MD Moldova|ME Montenegro|MG Madagascar|MK North Macedonia|ML Mali|MM Myanmar|MN Mongolia|MO Macao|MQ Martinique|MR Mauritania|MT Malta|MU Mauritius|MV Maldives|MW Malawi|MX Mexico|MY Malaysia|MZ Mozambique|NA Namibia|NC New Caledonia|NE Niger|NG Nigeria|NI Nicaragua|NL Netherlands|NO Norway|NP Nepal|NZ New Zealand|OM Oman|PA Panama|PE Peru|PF French Polynesia|PG Papua New Guinea|PH Philippines|PK Pakistan|PL Poland|PR Puerto Rico|PS Palestine|PT Portugal|PY Paraguay|QA Qatar|RE Reunion|RO Romania|RS Serbia|RU Russia|RW Rwanda|SA Saudi Arabia|SC Seychelles|SD Sudan|SE Sweden|SG Singapore|SI Slovenia|SK Slovakia|SL Sierra Leone|SM San Marino|SN Senegal|SO Somalia|SR Suriname|SV El Salvador|SX Sint Maarten|SY Syria|SZ Eswatini|TC Turks and Caicos Islands|TD Chad|TG Togo|TH Thailand|TJ Tajikistan|TL Timor-Leste|TM Turkmenistan|TN Tunisia|TO Tonga|TR Turkey|TT Trinidad and Tobago|TW Taiwan|TZ Tanzania|UA Ukraine|UG Uganda|US United States|UY Uruguay|UZ Uzbekistan|VC Saint Vincent and the Grenadines|VE Venezuela|VG British Virgin Islands|VI U.S. Virgin Islands|VN Vietnam|VU Vanuatu|WS Samoa|YE Yemen|ZA South Africa|ZM Zambia|ZW Zimbabwe"""
COUNTRIES = dict(e.split(" ", 1) for e in _ISO.split("|"))
NAME_TO_CODE = {v.lower(): k for k, v in COUNTRIES.items()}
NAME_TO_CODE.update({
    "usa": "US", "u.s.": "US", "u.s.a.": "US", "united states of america": "US",
    "uk": "GB", "great britain": "GB", "england": "GB", "scotland": "GB",
    "wales": "GB", "northern ireland": "GB", "republic of korea": "KR",
    "korea": "KR", "czech republic": "CZ", "holland": "NL", "uae": "AE",
    "russian federation": "RU", "viet nam": "VN", "r.o.c": "TW",
    "turkiye": "TR", "türkiye": "TR", "the netherlands": "NL", "the bahamas": "BS",
    "deutschland": "DE", "españa": "ES", "brasil": "BR", "méxico": "MX",
})
CODE_ALIAS = {"UK": "GB", "EL": "GR"}
US_STATES = ("alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|"
             "florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|"
             "maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|"
             "nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|"
             "north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|"
             "south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|"
             "wisconsin|wyoming")
US_ABBR = ("AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|"
           "MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC")
US_ZIP = re.compile(rf"\b({US_ABBR})\.?,?\s+\d{{5}}(?:-\d{{4}})?\b")
US_STATE_NAME = re.compile(rf",\s*({US_STATES})\s*(?:,|\d{{5}}|$)", re.I)
CA_POSTCODE = re.compile(r"\b[ABCEGHJ-NPRSTVXY]\d[A-Z]\s?\d[A-Z]\d\b")
TLD_OVERRIDE = {"uk": "GB", "eu": "", "su": "RU"}
GENERIC_TLD = {"com", "net", "org", "info", "biz", "io", "co", "app", "dev", "ai", "edu",
               "gov", "mil", "int", "xyz", "online", "site", "shop", "cloud", "tv", "me",
               "us"}   # .us is used by US firms but too rarely to trust as a signal

# --------------------------------------------------------------------------
# Industry. Stated labels (Qilin, GSG) are mapped with an ordered table whose
# order matters: "Hospitality" must be tested before "hospital", "Law" must be
# a whole word, and so on. Descriptions (INC, DragonForce, SafePay) are scored.
# --------------------------------------------------------------------------
LABEL_MAP = [
    ("Hospitality & Travel", r"hospitality|hotel|restaurant|travel|leisure|tourism|fitness|gambling|gaming|casino"),
    ("Healthcare", r"health|medical|hospital|physician|clinic|dental|mental|veterinar|ambulance|alcoholism"),
    ("Pharmaceuticals & Biotech", r"pharma|biotech|drug stores"),
    ("Education", r"education|school|universit|college"),
    ("Government", r"government|public admin|military"),
    ("Legal", r"\blaw\b|legal"),
    ("Insurance", r"insurance"),
    ("Financial Services", r"accounting|financ|bank|invest|credit card|transaction processing|capital market|asset management"),
    ("Real Estate", r"real estate|property"),
    ("Construction", r"construction|civil engineering|building materials"),
    ("Engineering & Architecture", r"architecture|engineering"),
    ("Telecommunications", r"telecommunication|telecom|broadband"),
    ("Technology", r"software|technology|\bit\b|hosting|internet|data cent"),
    ("Media & Entertainment", r"media|entertainment|publishing|broadcast|advertising networks"),
    ("Professional Services", r"business services|consulting|staffing|advertising|marketing|professional|human resource|project management"),
    ("Transportation & Logistics", r"transport|logistics|shipping|freight|airline"),
    ("Energy & Utilities", r"energy|utilit|electricity|\boil\b|\bgas\b|power (?:generation|plant)|electric power|waste|mining"),
    ("Automotive", r"automotive|automobile|vehicle|tires"),
    ("Agriculture & Food", r"agricultur|food|beverage|farming"),
    ("Retail & Wholesale", r"retail|grocery|wholesale|convenience stores|consumer goods|apparel|home decor|drug stores|office products"),
    ("Manufacturing", r"manufactur|industrial|machinery|electronics|semiconductor|chemicals|plastics|rubber|furniture|appliances|tools|building"),
    ("Non-profit", r"non-profit|nonprofit|charitable|membership organi[sz]ations|association"),
    ("Consumer Services", r"consumer services|repair services"),
    ("Holding Companies", r"holding compan|conglomerate"),
]
INDUSTRY_KEYWORDS = [
    ("Agriculture & Food", r"agricultur|agro|farming|\bfarm\b|poultry|livestock|fertiliz|dairy|bakery|brewery|winery|fisher|food process|beverage|crop"),
    ("Healthcare", r"hospital\b|hospitals|clinic(?:al|s)?\b|medical|dental|patient|nursing|care home|physician|surgery|surgical|veterinar|dermatolog|therapy|healthcare|optometr"),
    ("Pharmaceuticals & Biotech", r"pharmaceutical|biotech|life sciences|pharmacy|pharmacies"),
    ("Education", r"school|universit|college|academy|education|student|campus|k-12|kindergarten"),
    ("Government", r"municipal|government|ministry|city of|county of|federal agency|public sector|state agency|public institution|township"),
    ("Financial Services", r"\bbank(?:ing|s)?\b|credit union|financial services|investment firm|asset management|mortgage|lending|fintech|accounting firm|accountants|audit firm|brokerage|\bcpa\b|tax (?:services|preparation)"),
    ("Insurance", r"insurance|insurer|underwrit|reinsur"),
    ("Legal", r"law firm|attorney|legal services|solicitor|barrister|litigation|lawyers"),
    ("Construction", r"construction|contractor|builder|roofing|plumbing|scaffold|excavat|landscap|hvac"),
    ("Engineering & Architecture", r"engineering (?:firm|services|consult)|civil engineer|architect"),
    ("Manufacturing", r"manufactur|factory|machining|fabricat|foundry|plastics|steel|assembly line|industrial equipment|producer of"),
    ("Retail & Wholesale", r"retail|supermarket|grocery|e-commerce|ecommerce|merchandise|boutique|store chain|wholesale|distributor|distribution of"),
    ("Technology", r"software|information technology|\bit\b services|saas|networking solutions|computing|data cent(?:er|re)|cybersecurity|\bic design"),
    ("Telecommunications", r"telecommunication|telecom|internet service provider|mobile network|broadband"),
    ("Transportation & Logistics", r"logistics|freight|shipping|trucking|transportation|courier|haulage|fleet|warehous"),
    ("Energy & Utilities", r"energy|utilit(?:y|ies)|electric power|power plant|petroleum|solar|wind farm|water treatment|wastewater|propane|bulk fuel|lubricant|oil and gas"),
    ("Real Estate", r"real estate|property management|realty|leasing|landlord|condominium"),
    ("Hospitality & Travel", r"hotel|resort|restaurant|hospitality|tourism|travel agency|catering|casino|franchise partner|fast food"),
    ("Professional Services", r"consult(?:ing|ancy)|advisory|staffing|recruitment|marketing agency|advertising|public relations|hr & staffing"),
    ("Media & Entertainment", r"\bmedia\b|publishing|broadcast|newspaper|entertainment|\bfilm\b|gaming studio"),
    ("Non-profit", r"non-profit|nonprofit|charit|\bngo\b|faith based|foundation\b"),
    ("Automotive", r"automotive|car dealer|auto parts|dealership|tire distribution|vehicle service"),
    ("Aerospace & Defense", r"aerospace|defen[cs]e contractor|aviation|airline|aircraft"),
    ("Mining & Materials", r"mining|quarry|minerals|cement|chemical"),
]
CUT = re.compile(r"\b(total leak|leaked data|data\s*:|files?\s*,\s*[\d,]+\s*folders?"
                 r"|\d[\d.,]*\s*(gb|tb|mb)\s*,)", re.I)
LEAD_SIZE = re.compile(r"^\s*(full\s+data|total|data)?\s*[\d.,]*\s*(gb|tb|mb)\s*\+?\s*", re.I)
STATED_INDUSTRY = re.compile(r"operates in the ([A-Za-z &/,'-]{3,40}?) industry"
                             r"|\bIndustry:\s*([A-Za-z &/,'-]{3,60}?)(?=\s+[A-Z][a-z]+(?: [A-Z][a-z]+)?:|\s*\||$)", re.I)

# Kinds of data the groups say they took, for Q8. Derived from each site's own
# category labels and description text by keyword, so it is recorded separately
# from data_categories, which holds only what the site itself published.
DATA_TYPES = [
    ("Personal data (PII)", r"\bpii\b|personal (?:data|information)|social security|\bssn\b|passport|driver'?s licen|date of birth|\bid (?:cards?|documents?|scans?)"),
    ("Employee / HR", r"\bhr\b|human resources|employee|staff (?:data|files|records)|personnel|payroll|salar"),
    ("Customer data", r"customer|client (?:data|info|files|records|list)|clients'"),
    ("Financial / accounting", r"financ|accounting|invoice|bank (?:statements?|details|accounts?)|budget|tax|audit|balance sheet|payment"),
    ("Medical / health (PHI)", r"medical|patient|\bphi\b|health record|diagnos|prescription|hipaa"),
    ("Legal / contracts", r"legal|contract|agreement|\bnda\b|litigation|court"),
    ("Corporate / confidential", r"confidential|corporate|internal (?:docs|documents)|board|management|strateg"),
    ("Email / correspondence", r"e-?mail|correspondence|mailbox|outlook|\.pst\b"),
    ("Databases / backups", r"database|\bsql\b|\bdb\b|backup|\bad dump\b|active directory"),
    ("Engineering / R&D / IP", r"engineering|drawings?|\bcad\b|blueprint|r&d|research|project(?:s| files)|source code|intellectual property|design files"),
    ("Student / education records", r"student|pupil|transcript|enrol"),
]

LEGAL_SUFFIX = re.compile(r"\b(inc|llc|ltd|limited|corp|corporation|co|company|gmbh|bv|nv|sa|sas|srl|"
                          r"spa|ag|as|ab|oy|aps|plc|pty|pte|kk|kg|ug|sl|sarl|lda|group|holdings?)\b\.?", re.I)


def clean(text):
    t = str(text or "")
    # Repair text that was UTF-8 decoded as cp1252 somewhere upstream (â€™ etc.).
    if re.search(r"[âÃÂ][\x80-\xbf€™œ‘-„]", t):
        try:
            t = t.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    t = t.replace("​", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def domain_of(*candidates):
    for raw in candidates:
        v = clean(raw).lower()
        if not v:
            continue
        v = re.sub(r"^https?://", "", v).split("/")[0].split("?")[0].strip()
        v = re.sub(r"^www\.", "", v)
        if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", v):
            return v
    return ""


def country_from_code_or_name(raw):
    v = clean(raw)
    if not v:
        return ""
    if len(v) == 2:
        c = CODE_ALIAS.get(v.upper(), v.upper())
        return c if c in COUNTRIES else ""
    return NAME_TO_CODE.get(v.lower().strip(" ."), "")


def country_from_text(text):
    """Country named in a free-text address or location. Last mention wins."""
    t = clean(text)
    if not t:
        return ""
    best, pos = "", -1
    for name, code in NAME_TO_CODE.items():
        if len(name) < 4 and name not in ("usa", "uk", "uae"):
            continue
        for m in re.finditer(rf"(?<![a-z]){re.escape(name)}(?![a-z])", t.lower()):
            if m.start() > pos:
                best, pos = code, m.start()
    if best:
        return best
    if US_ZIP.search(t) or US_STATE_NAME.search(t):
        return "US"
    if CA_POSTCODE.search(t):
        return "CA"
    return ""


def country_from_domain(domain):
    if not domain:
        return ""
    tld = domain.rsplit(".", 1)[-1]
    if tld in TLD_OVERRIDE:
        return TLD_OVERRIDE[tld]
    if tld in GENERIC_TLD:
        return ""
    return tld.upper() if tld.upper() in COUNTRIES else ""


def resolve_country(stated="", location_text="", domain=""):
    """(code, source). Stated beats address text beats domain suffix."""
    c = country_from_code_or_name(stated)
    if c:
        return c, "stated"
    c = country_from_text(location_text)
    if c:
        return c, "stated in address/location"
    c = country_from_domain(domain)
    if c:
        return c, "inferred from domain"
    return "", ""


def company_text(text):
    t = LEAD_SIZE.sub("", clean(text))
    m = CUT.search(t)
    return (t[:m.start()] if m else t).strip()


def map_label(label):
    """Map a site's own industry label. Multi-label values use the first that maps."""
    for part in re.split(r"\s*[,/;]\s*|\s+·\s+", clean(label)):
        for name, pattern in LABEL_MAP:
            if re.search(pattern, part, re.I):
                return name
    return ""


def resolve_industry(stated_label, text, victim=""):
    """(industry, source, confidence)."""
    label = clean(stated_label)
    if label:
        mapped = map_label(label)
        return (mapped or "Other"), "stated by site", "high"

    body = company_text(text)
    if not body:
        return "", "", ""
    m = STATED_INDUSTRY.search(body)
    if m:
        mapped = map_label(m.group(1) or m.group(2))
        if mapped:
            return mapped, "stated in description", "high"

    head = f"{victim}. {body.split('.')[0]}"
    scores = {}
    for name, pattern in INDUSTRY_KEYWORDS:
        strong = len({x.group(0).lower() for x in re.finditer(pattern, head, re.I)})
        rest = len({x.group(0).lower() for x in re.finditer(pattern, body, re.I)})
        if strong + rest:
            scores[name] = strong + rest     # head terms count twice: once here, once in body
    if not scores:
        return "", "", ""
    order = {n: i for i, (n, _) in enumerate(INDUSTRY_KEYWORDS)}
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], order[kv[0]]))
    top, score = ranked[0]
    runner = ranked[1][1] if len(ranked) > 1 else 0
    return top, "inferred from description", ("high" if score >= 3 and score > runner else "low")


def inventory_text(text):
    """The stolen-data inventory part of a description (after the CUT marker), if any."""
    t = clean(text)
    m = CUT.search(t)
    return t[m.start():] if m else ""


def data_types(*texts):
    blob = " ".join(clean(t) for t in texts if t)
    return "; ".join(name for name, pat in DATA_TYPES if re.search(pat, blob, re.I))


UNITS = {"kb": 1e-6, "mb": 1e-3, "gb": 1, "tb": 1e3, "pb": 1e6}


def size_gb(text):
    """First '<number> <unit>' in the text, in decimal GB."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*([kmgtp]b)\b", clean(text), re.I)
    if not m:
        return ""
    return round(float(m.group(1).replace(",", ".")) * UNITS[m.group(2).lower()], 2)


def revenue_usd(text):
    """'$966 Million', '$6,5 Million', '$28.2 M', '1700000000' -> integer USD."""
    t = clean(text).lower().replace("$", "").replace("usd", "").strip()
    if not t:
        return ""
    if re.fullmatch(r"\d+(\.0+)?", t):
        return int(float(t))
    m = re.match(r"<?\s*(\d+(?:[.,]\d+)?)\s*(billion|bn|b|million|mil|mm|m|thousand|k)?\b", t)
    if not m:
        return ""
    mult = {"billion": 1e9, "bn": 1e9, "b": 1e9, "million": 1e6, "mil": 1e6, "mm": 1e6,
            "m": 1e6, "thousand": 1e3, "k": 1e3}.get(m.group(2) or "", 1)
    return int(float(m.group(1).replace(",", ".")) * mult)


EMPLOYS = re.compile(r"\bEmployees:\s*(\d[\d,]*(?:\s*-\s*\d[\d,]*)?\+?)"
                     r"|employs (\d[\d,]*\s*(?:to|-)\s*\d[\d,]*|\d[\d,]*\+?) (?:people|employees)", re.I)


def employees_from_text(text):
    m = EMPLOYS.search(clean(text))
    if not m:
        return ""
    return re.sub(r"\s*(?:to|-)\s*", "-", m.group(1) or m.group(2)).replace(",", "")


def name_key(victim, domain):
    if domain:
        return domain
    v = LEGAL_SUFFIX.sub(" ", clean(victim).lower())
    return re.sub(r"[^a-z0-9]+", "", v)


def read_csv(path):
    p = Path(path)
    if not p.exists():
        print(f"  WARNING: {p} not found, skipping", file=sys.stderr)
        return []
    with open(p, encoding="utf-8-sig", errors="replace") as fh:
        return list(csv.DictReader(fh))


def union(current, earlier, key):
    """Current capture wins; earlier rows the site has since removed are kept."""
    out, seen = [], set()
    for r in current:
        k = key(r)
        if k and k not in seen:
            seen.add(k)
            out.append(dict(r, _still_listed="yes"))
    for r in earlier:
        k = key(r)
        if k and k not in seen:
            seen.add(k)
            out.append(dict(r, _still_listed="no"))
    return out


def row(group, victim, website="", country="", country_source="", industry=("", "", ""),
        industry_raw="", revenue="", data_volume="", data_gb="", data_categories="",
        dtypes="", employees="", description="", post_date="", date_source="stated by site",
        still_listed="", recycled="", source_id=""):
    ind, isrc, _ = industry
    return {
        "group": group, "victim": clean(victim), "website": website,
        "country": country, "country_name": COUNTRIES.get(country, ""),
        "country_source": country_source,
        "industry": ind, "industry_raw": clean(industry_raw), "industry_source": isrc,
        "revenue_usd": revenue, "data_volume": clean(data_volume), "data_size_gb": data_gb,
        "data_categories": clean(data_categories), "data_types": dtypes,
        "employee_count": clean(employees), "description": clean(description),
        "post_date": clean(post_date)[:10], "post_month": clean(post_date)[:7],
        "date_source": date_source, "still_listed": still_listed,
        "recycled_flag": recycled, "source_id": clean(source_id),
    }


def build_rows():
    rows = []

    # Qilin: industry label stated; country only from the company URL's domain.
    for r in union(read_csv(RAW / "Qilin/qilin.csv"), read_csv(REPO / "data/qilin.csv"),
                   lambda r: r.get("uuid")):
        dom = domain_of(r.get("company_url"), r.get("victim"))
        label = "" if clean(r.get("industry")) == "0" else r.get("industry")
        loc = label.split("·", 1)[1] if "·" in (label or "") else ""
        code, csrc = resolve_country("", loc, dom)
        rows.append(row("Qilin", r.get("victim"), dom, code, csrc,
                        resolve_industry(label.split("·")[0] if label else "", "", r.get("victim")),
                        industry_raw=label, post_date=r.get("post_date"),
                        still_listed=r["_still_listed"], source_id=r.get("uuid")))

    # INC Ransom: country, revenue and stolen-data labels stated for every victim.
    for r in union(read_csv(RAW / "Inc_Ransom/inc_ransom.csv"),
                   read_csv(REPO / "data/inc_ransom.csv"), lambda r: r.get("id")):
        dom = domain_of(r.get("victim"))
        code, csrc = resolve_country(r.get("country"), "", dom)
        desc = r.get("description")
        try:
            gap = float(r.get("leak_minus_created_days") or 0)
        except ValueError:
            gap = 0
        recycled = "yes" if gap < -30 or re.search(r"re-?upload", desc or "", re.I) else "no"
        rows.append(row("INC Ransom", r.get("victim"), dom, code, csrc,
                        resolve_industry("", desc, r.get("victim")),
                        revenue=revenue_usd(r.get("revenue_usd")),
                        data_categories=r.get("categories"),
                        dtypes=data_types(r.get("categories"), inventory_text(desc)),
                        employees=employees_from_text(desc), description=desc,
                        post_date=r.get("created_date"), still_listed=r["_still_listed"],
                        recycled=recycled, source_id=r.get("id")))

    # DragonForce: exact data volume; country from the published address.
    for r in union(read_csv(RAW / "DragonForce/dragonforce.csv"),
                   read_csv(REPO / "data/dragonforce.csv"), lambda r: r.get("uuid")):
        dom = domain_of(r.get("website"), r.get("address"))
        code, csrc = resolve_country("", r.get("address"), dom)
        tags = re.findall(r"'tag':\s*'([^']*)'", r.get("tags") or "") or [
            t for t in (r.get("tags") or "").split("; ") if t]
        try:
            gb = round(int(float(r.get("data_size_bytes") or 0)) / 1e9, 2) or ""
        except ValueError:
            gb = ""
        desc = r.get("description")
        rows.append(row("DragonForce", r.get("victim"), dom, code, csrc,
                        resolve_industry("", desc, r.get("victim")),
                        data_volume=(r.get("headline") if size_gb(r.get("headline"))
                                     else (f"{gb} GB" if gb else "")), data_gb=gb,
                        data_categories="; ".join(tags),
                        dtypes=data_types("; ".join(tags), inventory_text(desc)),
                        description=desc, post_date=r.get("post_date"),
                        still_listed=r["_still_listed"], source_id=r.get("uuid")))

    # SafePay: country from the flag; industry from the company description.
    for r in union(read_csv(RAW / "SafePay/safepay.csv"), read_csv(REPO / "data/safepay.csv"),
                   lambda r: r.get("detail_path")):
        dom = domain_of(r.get("victim"))
        code, csrc = resolve_country(r.get("country_code"), "", dom)
        desc = r.get("description_full") or r.get("description")
        rows.append(row("SafePay", r.get("victim"), dom, code, csrc,
                        resolve_industry("", desc, r.get("victim")),
                        description=desc, post_date=r.get("post_date"),
                        still_listed=r["_still_listed"], source_id=r.get("detail_path")))

    # Global Secret Group: full profile stated; date from aggregator first-seen.
    gsg_dates = {r["detail_href"]: r for r in read_csv(RAW / "GlobalSecretGroup/globalSecretGroup.csv")}
    earlier = read_csv(REPO / "data_v2/globalSecretGroup.csv")
    for r in union(list(gsg_dates.values()), earlier, lambda r: r.get("detail_href")):
        dated = gsg_dates.get(r.get("detail_href"), r)
        dom = domain_of(r.get("desc_website"))
        code, csrc = resolve_country(r.get("country"), r.get("desc_location"), dom)
        props = (r.get("desc_properties") or r.get("data_analyzed") or "").lstrip(": ")
        rows.append(row("Global Secret Group", r.get("victim"), dom, code, csrc,
                        resolve_industry(r.get("desc_industry"), "", r.get("victim")),
                        industry_raw=r.get("desc_industry"),
                        revenue=revenue_usd(r.get("desc_revenue") or r.get("revenue")),
                        data_volume=props, data_gb=size_gb(props),
                        employees=r.get("desc_employees"), description=r.get("description"),
                        post_date=dated.get("post_date", ""),
                        date_source=dated.get("date_source") or "",
                        still_listed=r["_still_listed"],
                        source_id=r.get("detail_href", "").strip("/").split("/")[-1]))
    return rows


FIELDS = ["group", "victim", "website", "country", "country_name", "country_source",
          "industry", "industry_raw", "industry_source", "revenue_usd", "data_volume",
          "data_size_gb", "data_categories", "data_types", "employee_count", "description",
          "post_date", "post_month", "date_source", "still_listed", "recycled_flag",
          "source_id"]


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "data_v3"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = build_rows()
    undated = [r for r in rows if not r["post_date"]]
    win = [r for r in rows if WINDOW[0] <= r["post_date"] <= WINDOW[1]]
    win.sort(key=lambda r: (r["group"], r["post_date"]), reverse=True)

    write_csv(out / "merged.csv", win, FIELDS)
    for g in sorted({r["group"] for r in win}):
        slug = re.sub(r"[^a-z0-9]+", "_", g.lower()).strip("_")
        write_csv(out / f"{slug}.csv", [r for r in win if r["group"] == g], FIELDS)

    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "merged"
        ws.append(FIELDS)
        for r in win:
            ws.append([r[f] for f in FIELDS])
        wb.save(out / "merged.xlsx")
    except ImportError:
        print("  openpyxl not installed, merged.xlsx not written")

    by_key = defaultdict(list)
    for r in win:
        k = name_key(r["victim"], r["website"])
        if k:
            by_key[k].append(r)
    cross = [dict(match_key=k, groups=", ".join(sorted({h["group"] for h in hs})),
                  group=h["group"], victim=h["victim"], post_date=h["post_date"],
                  country=h["country"], website=h["website"])
             for k, hs in by_key.items() if len({h["group"] for h in hs}) > 1
             for h in sorted(hs, key=lambda x: x["post_date"])]
    write_csv(out / "cross_site_victims.csv", cross,
              ["match_key", "groups", "group", "victim", "post_date", "country", "website"])

    print(f"rows collected (all dates): {len(rows)}   undated, dropped: {len(undated)}")
    print(f"in window {WINDOW[0]}..{WINDOW[1]}: {len(win)}  -> {out / 'merged.csv'}")
    print(f"{'group':<22}{'rows':>6}{'removed':>9}{'country':>9}{'industry':>9}"
          f"{'revenue':>9}{'size':>7}{'dtypes':>8}  date range")
    for g, n in Counter(r["group"] for r in win).most_common():
        gr = [r for r in win if r["group"] == g]
        pct = lambda f: f"{100 * sum(1 for r in gr if r[f]) // n}%"
        print(f"{g:<22}{n:>6}{sum(r['still_listed'] == 'no' for r in gr):>9}{pct('country'):>9}"
              f"{pct('industry'):>9}{pct('revenue_usd'):>9}{pct('data_size_gb'):>7}"
              f"{pct('data_types'):>8}  {min(r['post_date'] for r in gr)}..{max(r['post_date'] for r in gr)}")
    print(f"victims listed by more than one group: {len({c['match_key'] for c in cross})}")


if __name__ == "__main__":
    main()
