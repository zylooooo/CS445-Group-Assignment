# Ransomware Data Leak Site Study

Collection and analysis pipeline for a study of five ransomware data leak sites over the
period **1 January to 30 September 2026**. Victim listings were scraped directly from each
group's own site over Tor, normalised onto a common schema, and merged into a single dataset
for analysis in Tableau.

Sites studied: **Qilin**, **INC Ransom**, **DragonForce**, **Play**, **SafePay**.
Result: 3,432 collected posts, of which **1,558 fall inside the study window**.

Full collection and normalisation detail is in [METHODOLOGY.md](METHODOLOGY.md).

## Scope and conduct

This repository contains tooling and data for academic research. The following boundaries
were set before collection began and held throughout.

- **Only victim listing metadata was collected.** No leaked files were downloaded at any
  point. `safepay_details.py` fetches each victim's description page and nothing else, and
  INC Ransom's `download`, `get/file` and `get/folder` endpoints, which serve the stolen
  files, were deliberately left untouched.
- **No access control was circumvented.** Two candidate sites were dropped rather than
  defeated: The Gentlemen, which runs a proof-of-work and browser-fingerprinting bot
  challenge, and LockBit, which fronts its listings with an access queue. Accepting a session
  cookie or waiting out an advertised queue is ordinary client behaviour; solving a challenge
  designed to detect automation is not, and was not attempted.
- **No live .onion addresses appear in this repository.** See "Finding a working mirror".
- Requests were rate limited throughout, with randomised pauses between pages and a retry
  ceiling.

## About the data in `data/`

These files contain records of real organisations named as victims by ransomware groups,
including company names, domains, countries, revenue figures where the group published them,
and descriptions of what the group claimed to have stolen.

Please note:

- The data is a **point-in-time snapshot** taken in September 2026. It is not a live or
  authoritative record.
- **Some listings have since been removed from the source sites.** The retention analysis in
  METHODOLOGY.md shows that between 3 and 35 percent of listings per group are no longer
  present on the live sites, which in many cases is consistent with the victim having paid or
  negotiated. This dataset preserves records that the groups themselves have withdrawn.
- All victim information originates from the attackers' own claims and has not been
  independently verified. Revenue figures in particular are published by the attacker and
  should be treated as claims, not facts.
- The data is published for academic assessment. It must not be used to contact, target,
  solicit, or otherwise act against any organisation named in it.

## Requirements

- **Tor**, running as a daemon with a SOCKS5 proxy on `127.0.0.1:9050`. All fetchers route
  through it; nothing here works without it.
- **Python 3.9 or later.**
- A Linux environment is assumed. The scripts were written and run on Kali Linux in a virtual
  machine.

## Setup

Install and start Tor:

```bash
sudo apt install -y tor
sudo systemctl enable --now tor
```

Confirm the proxy is working before going further. This should report `"IsTor":true`:

```bash
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

Create the environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requests[socks]` pulls in `PySocks`, which is required for the `socks5h://` proxy scheme the
fetchers use. The `h` in `socks5h` matters: it makes Tor resolve hostnames remotely, without
which `.onion` addresses cannot resolve at all.

## Finding a working mirror

**No site addresses are shipped with this repository, deliberately.** Leak sites run several
mirrors and rotate them constantly as they are taken down or blocked, so any hardcoded address
would stop working quickly, and publishing one would amount to republishing live criminal
infrastructure. Every fetcher therefore takes the site address as its first argument, and you
supply it.

To find a current address:

1. Open a leak site aggregator, for example `ransomlook.io`, and go to the group's page.
2. Find the section listing the group's known URLs. Each is shown with an online or offline
   status and an uptime percentage.
3. Pick one marked active with a reasonable uptime, and pass it to the script as the base URL.

This is how all five sites in this study were reached.

**Expect failures mid-run.** Mirrors go down partway through a collection. Each fetcher retries
a page three times before moving on, but a mirror that dies entirely means restarting against
a different one. This costs nothing: already-fetched pages are kept on disk, and every parser
deduplicates on the site's own post identifier, so re-running over a mixed set of captures
produces the same result.

Some sites place an interstitial in front of their listings. `fetch_pages.sh` carries a curl
cookie jar, which is enough for a site that only sets a session cookie on first visit.

## Directory layout

The scripts read and write under `~/dls/`, which is not configurable. Create it before you
start:

```bash
mkdir -p ~/dls/raw/{Qilin,Inc_Ransom,DragonForce,Play,SafePay}
```

Expected layout:

```
~/dls/
├── raw/
│   ├── Qilin/           captured HTML, then qilin.csv
│   ├── inc_ransom/      captured JSON          (note the lowercase; see Limitations)
│   ├── Inc_Ransom/      inc_ransom.csv
│   ├── DragonForce/     captured JSON, then dragonforce.csv
│   ├── Play/            captured HTML, then play.csv
│   └── SafePay/         captured HTML, details/, then safepay.csv
├── merged.csv
└── cross_site_victims.csv
```

Raw captures are not included in this repository. They contain verbatim leak site content,
including mirror addresses embedded in the pages themselves.

## Pipeline

Each site is collected in two steps, fetch then parse, except SafePay which needs a third.
`merge_all.py` runs last, once all five per-site CSVs exist.

In every command below, `<mirror>` is an address you sourced yourself as described above.

### 1. Qilin

```bash
./scripts/qilin_fetch.sh "http://<mirror>.onion" 60
python3 scripts/qilin_parse.py ~/dls/raw/Qilin/*.html -o ~/dls/raw/Qilin/qilin.csv
```

### 2. INC Ransom

The address here is the API backend host, which differs from the site you browse.

```bash
python3 scripts/inc_fetch.py "http://<api-mirror>.onion" 50
python3 scripts/inc_parse.py ~/dls/raw/inc_ransom/*.json -o ~/dls/raw/Inc_Ransom/inc_ransom.csv
```

### 3. DragonForce

```bash
python3 scripts/dragonforce_fetch.py "http://<mirror>.onion"
python3 scripts/dragonforce_parse.py ~/dls/raw/DragonForce/*.json -o ~/dls/raw/DragonForce/dragonforce.csv
```

### 4. Play

```bash
./scripts/fetch_pages.sh "http://<mirror>.onion/index.php?page={page}" ~/dls/raw/Play 40 "viewtopic("
python3 scripts/play_parse.py ~/dls/raw/Play/*.html -o ~/dls/raw/Play/play.csv
```

### 5. SafePay

Three steps. Published victims lose their countdown bar, and with it the only date shown on
the listing page, so dates are recovered from each victim's detail page.

```bash
./scripts/fetch_pages.sh "http://<mirror>.onion/?page={page}" ~/dls/raw/SafePay 120 "card-title"
python3 scripts/safepay_parse.py ~/dls/raw/SafePay/*.html -o ~/dls/raw/SafePay/safepay_listing.csv
python3 scripts/safepay_details.py ~/dls/raw/SafePay/safepay_listing.csv ~/dls/raw/SafePay/safepay.csv --base "http://<mirror>.onion"
```

The third step fetches roughly 550 pages and takes about an hour. Every page is cached under
`~/dls/raw/SafePay/details/`, so it can be interrupted and resumed at no cost, and re-run
offline with `--offline`.

### 6. Merge

```bash
python3 scripts/merge_all.py
```

Writes `~/dls/merged.csv` and `~/dls/cross_site_victims.csv`, and prints a coverage report.

## Scripts

| Script | Type | Input | Output | Purpose |
|---|---|---|---|---|
| `qilin_fetch.sh` | fetch | mirror URL, max pages | `raw/Qilin/*.html` | Pages Qilin's listing at `/?page=N` over Tor, with retries and pauses. Stops when a page holds no victim cards. |
| `fetch_pages.sh` | fetch | URL template with `{page}`, output dir, max pages, marker | `<dir>/*.html` | Generic paged fetcher used for Play and SafePay. Adds a cookie jar and stops when a site recycles content past its last page. |
| `inc_fetch.py` | fetch | API base URL, page size | `raw/inc_ransom/*.json` | Pages INC Ransom's JSON API, deduplicating by announcement id and stopping at the total the API reports. |
| `dragonforce_fetch.py` | fetch | site base URL | `raw/DragonForce/*.json` | Pages DragonForce's backend API after a warm-up request for its session cookie. Stops at the declared count. |
| `qilin_parse.py` | parse | saved HTML | `qilin.csv` | Extracts victim name, industry label, company URL, post date, photo count and countdown status. |
| `inc_parse.py` | parse | saved JSON | `inc_ransom.csv` | Decodes URL-encoded fields and millisecond timestamps. Derives `leak_minus_created_days`, which flags possible backdated posts. |
| `dragonforce_parse.py` | parse | saved JSON | `dragonforce.csv` | Converts the API's `weight` field from bytes to GB, giving an exact data volume per victim. |
| `play_parse.py` | parse | saved HTML | `play.csv` | Regex based, because the site emits minified HTML with unclosed tags. Isolates each victim by its `viewtopic` identifier. |
| `safepay_parse.py` | parse | saved HTML | `safepay_listing.csv` | Reads country from a flag image's `alt` attribute and derives deadline length from the countdown bar. |
| `safepay_details.py` | enrich | listing CSV, mirror URL | `safepay.csv` | Fetches each victim's detail page to recover the missing post date, plus a click count and fuller description. Caches every page. |
| `merge_all.py` | merge | the five per-site CSVs | `merged.csv`, `cross_site_victims.csv` | Normalises all five onto one schema, unifies country representations, classifies industry from description text, and records the provenance of every derived value. |

## Data dictionary: `merged.csv`

| Column | Description |
|---|---|
| `group` | Which leak site published the listing |
| `victim` | Victim name as published by the group |
| `domain` | Victim's own website domain, normalised, where the site provided one |
| `match_key` | Domain if available, otherwise a normalised company name. Used for cross-site matching |
| `post_date` | Date the victim appeared on the leak site, ISO format |
| `post_month` | `post_date` truncated to `YYYY-MM`, for monthly charts |
| `in_window` | `yes` if `post_date` falls between 2026-01-01 and 2026-09-30 |
| `country_code` | ISO two-letter country code |
| `country_name` | Country name |
| `country_source` | `stated` if the site published it, `inferred from domain` if derived from a country-code domain suffix, blank if unknown |
| `industry` | Canonical industry category |
| `industry_source` | `stated by site`, `stated in description`, or `inferred from description` |
| `industry_confidence` | `high` or `low`, for inferred values. Low means the keyword evidence was weak or a close second category existed |
| `industry_raw` | The site's own industry label, where it published one (Qilin only) |
| `revenue_usd` | Annual revenue as claimed by the group (INC Ransom only) |
| `data_size_gb` | Exact volume of claimed stolen data (DragonForce only) |
| `data_categories` | The group's own labels for the stolen data, for example `Encrypted`, `AD Dump`, `Stocks` |
| `views` | View or visit counter shown on the listing |
| `status` | Publication status, where the site exposes one |
| `deadline_hours` | Length of the extortion countdown in hours (SafePay only) |
| `description` | Victim description text as published by the group |
| `source_id` | The site's own identifier for the post, used for deduplication |

**On the provenance columns.** `country_source`, `industry_source` and `industry_confidence`
exist so that values stated by the source can be separated from values this pipeline derived.
Any analysis that treats an inferred value as a stated one should say so. Filtering to
`country_source = stated` or `industry_confidence = high` gives the conservative subset.

## Limitations

- **Country is known for 888 of the 1,558 in-window victims (57 percent),** across 62
  countries. Coverage is uneven: 100 percent for INC Ransom and Play and 99 percent for
  SafePay, but only 31 percent for Qilin and 24 percent for DragonForce, because those two
  publish only a company URL and most are generic domains carrying no location information.
  The two weakest sites are also two of the largest, so any country ranking is weighted toward
  the three sites that publish country outright.
- **Industry is known for 1,191 of 1,558 (76 percent),** of which 978 are high confidence.
  Only Qilin states an industry; for the others it is classified from description text by
  keyword scoring, which is approximate by nature.
- **Revenue comes only from INC Ransom** (311 in-window victims) and **data volume only from
  DragonForce** (296). Neither generalises to the full dataset.
- **The dataset undercounts.** Comparing against an aggregator's record of the same period
  shows between 3 and 35 percent of listings per group are no longer present on the live
  sites. What remains reflects each group's own housekeeping as much as its activity.
- **Two sites were excluded** for the reasons given under Scope and conduct, so the five
  studied here are not a random sample of the ecosystem. Sites that resist automated
  collection are systematically under-represented in datasets built this way, including this
  one.
- **Paths are not configurable.** The scripts read and write under `~/dls/` throughout. They
  are committed exactly as they were run to produce this dataset rather than refactored after
  the fact.
- **One naming inconsistency.** `inc_fetch.py` writes its JSON to `raw/inc_ransom/` in
  lowercase, while `merge_all.py` reads the parsed CSV from `raw/Inc_Ransom/`. On a
  case-sensitive filesystem these are different directories. The pipeline commands above
  account for this; it is documented rather than silently corrected so the scripts match what
  produced the data.
