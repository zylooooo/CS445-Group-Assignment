# data_v3

Victim listings collected directly from five ransomware data leak sites over Tor on
**28–29 September 2026**, filtered to posts dated **1 January – 30 September 2026**.
Collection ran before the window closed, so the effective coverage is
**1 January – 28 September 2026**.

Sites: **Qilin, INC Ransom, DragonForce, SafePay, Global Secret Group**.

| Group               | Posts in window | Country      | Industry | Revenue | Data size |
| ------------------- | --------------- | ------------ | -------- | ------- | --------- |
| Qilin               | 675             | 31%          | 96%      | –       | –         |
| INC Ransom          | 326             | 100%         | 72%      | 100%    | –         |
| DragonForce         | 302             | 78%          | 81%      | –       | 100%      |
| SafePay             | 152             | 98%          | 58%      | –       | –         |
| Global Secret Group | 42              | 100%         | 100%     | 97%     | 100%      |
| **Total**           | **1,497**       | 74 countries |          |         |           |

`data_v2/` is left untouched. Nothing here was copied from it except earlier captures
of the same five sites, which were unioned with the new capture (see `still_listed`).

## Files

| File                         | Contents                                                                                                                                                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `merged.csv` / `merged.xlsx` | One row per victim post, all five sites. Use this in Tableau.                                                                                                                                                            |
| `<group>.csv`                | The same rows split per site.                                                                                                                                                                                            |
| `cross_site_victims.csv`     | Victims listed by more than one of the five groups inside the window (none found).                                                                                                                                       |
| `cross_reference/`           | Web research on a sample of rows (company facts from official sources) and `data_quality_flags.csv`. **Not part of the dataset**: kept only as a quality check on leak-site values. See `cross_reference/ENRICHMENT.md`. |

CSV files are UTF-8 with a BOM, so Excel opens them without garbling accented text.
Don't re-save them from Excel as CSV: that is what corrupted `data_v2/merged.csv`.

## Columns at a glance

Fill rates are across all 1,497 rows of `merged.csv`. How each column answers Q1–Q10 is in
[`report/g1t6_group_assignment_guide.md`](../report/g1t6_group_assignment_guide.md).

| #   | Column            | Filled | Example                                               | What it is                                                                                                                                      |
| --- | ----------------- | ------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `group`           | 100%   | `INC Ransom`                                          | Leak site that published the post                                                                                                               |
| 2   | `victim`          | 100%   | `cambrialawfirm.com`                                  | Victim name as published                                                                                                                        |
| 3   | `website`         | 88%    | `cambrialawfirm.com`                                  | Victim's own domain, normalised                                                                                                                 |
| 4   | `country`         | 64%    | `CA`                                                  | ISO 3166-1 alpha-2 country code                                                                                                                 |
| 5   | `country_name`    | 64%    | `Canada`                                              | Full country name; use for Tableau's Country/Region role                                                                                        |
| 6   | `country_source`  | 64%    | `stated`                                              | `stated` (site published it), `stated in address/location` (DragonForce address, GSG location), or `inferred from domain` (ccTLD such as `.de`) |
| 7   | `industry`        | 84%    | `Education`                                           | One of ~25 canonical categories                                                                                                                 |
| 8   | `industry_raw`    | 46%    | `Freight & Logistics Services`                        | The site's own industry label (Qilin, GSG)                                                                                                      |
| 9   | `industry_source` | 84%    | `inferred from description`                           | `stated by site`, `stated in description` (e.g. INC's "Industry: Education"), or `inferred from description` (keyword scoring)                  |
| 10  | `revenue_usd`     | 24%    | `15000000`                                            | Annual revenue claimed by the group, integer USD (INC, GSG only)                                                                                |
| 11  | `data_volume`     | 22%    | `783 GB (501,662 Files, 42,890 Folders)`              | Stolen-data size label as published                                                                                                             |
| 12  | `data_size_gb`    | 22%    | `783.0`                                               | Numeric size in decimal GB (DragonForce exact bytes; GSG parsed from its label)                                                                 |
| 13  | `data_categories` | 21%    | `Encrypted; Proof`                                    | The site's own leak labels (INC `Encrypted / Proof / AD Dump / Stocks`, DragonForce tags)                                                       |
| 14  | `data_types`      | 3%     | `Personal data (PII); Employee / HR`                  | Kinds of data stolen, keyword-derived from the site's labels and stolen-data text. Sparse                                                       |
| 15  | `employee_count`  | 6%     | `1000-4999`                                           | Headcount as published (GSG band, INC "Employees: N")                                                                                           |
| 16  | `description`     | 54%    | `Re-uploaded; the old download link was unavailable.` | Victim description as published (Qilin publishes none)                                                                                          |
| 17  | `post_date`       | 100%   | `2026-09-28`                                          | Date the victim appeared on the site (ISO)                                                                                                      |
| 18  | `post_month`      | 100%   | `2026-09`                                             | `post_date` as `YYYY-MM`, for monthly charts                                                                                                    |
| 19  | `date_source`     | 100%   | `stated by site`                                      | `stated by site`, or `aggregator first-seen (ransomlook.io)` for GSG, whose site shows no post date                                             |
| 20  | `still_listed`    | 100%   | `yes`                                                 | `no` if the post was in the 17–18 Sep capture but has since been removed                                                                        |
| 21  | `recycled_flag`   | 21%    | `yes`                                                 | INC only: `yes` if the leak date precedes the post by 30+ days or the post says it was re-uploaded                                              |
| 22  | `source_id`       | 100%   | `6ab9da399cd108bf260627e8`                            | The site's own post id; unique per group. Count posts with `COUNTD(source_id)`                                                                  |

**Not available from any of the five sites:** ransom amount and currency, initial-access
vector, and a double-extortion flag (every leak-site post is double extortion).

## How it was produced

```bash
source ~/dls/mirrors.env      # mirror addresses, never committed
./scripts/qilin_fetch.sh "$QILIN" 120
python3 scripts/inc_fetch.py "$INC_API" 50
python3 scripts/dragonforce_fetch.py "$DRAGONFORCE"
./scripts/fetch_pages.sh "$SAFEPAY/?page={page}" ~/dls/raw/SafePay 120 "card-title"
python3 scripts/gsg_fetch.py "$GSG"
curl -s -o ~/dls/aggregator/rl_gsg.json "https://www.ransomlook.io/api/group/global%20secret%20group"

python3 scripts/qilin_parse.py ~/dls/raw/Qilin/*.html -o ~/dls/raw/Qilin/qilin.csv
python3 scripts/inc_parse.py ~/dls/raw/inc_ransom/*.json -o ~/dls/raw/Inc_Ransom/inc_ransom.csv
python3 scripts/dragonforce_parse.py ~/dls/raw/DragonForce/*.json -o ~/dls/raw/DragonForce/dragonforce.csv
python3 scripts/safepay_parse.py ~/dls/raw/SafePay/*_page*.html -o ~/dls/raw/SafePay/safepay_listing.csv
python3 scripts/safepay_details.py ~/dls/raw/SafePay/safepay_listing.csv ~/dls/raw/SafePay/safepay.csv \
    --base "$SAFEPAY" --seed data/safepay.csv
python3 scripts/gsg_parse.py ~/dls/raw/GlobalSecretGroup/*_home.html \
    -o ~/dls/raw/GlobalSecretGroup/globalSecretGroup.csv --first-seen ~/dls/aggregator/rl_gsg.json

python3 scripts/merge_v3.py   # writes data_v3/
```

Completeness checks: INC Ransom's API reported 839 announcements and 839 were collected;
DragonForce's reported 627 and 627 were collected. Qilin's archive is 62 pages and
SafePay's is 63; past the last page Qilin re-serves the final page and SafePay returns 404.

## Conduct

Listing metadata only. No leaked files or file indexes were requested: GSG's
`/project/<id>/data/api/` (its stolen-file index), INC's download endpoints and all file
servers were left untouched. No captcha, proof-of-work or queue was solved or bypassed.
PayoutsKing (captcha page) and The Gentlemen (anti-bot challenge) were excluded for that
reason, and Akira because its only mirror was offline throughout collection.

## Limitations

- **Qilin country is known for only 31%.** Qilin publishes only a company URL, and most
  are `.com`. Country rankings lean on INC, SafePay and GSG, which state it.
- **Qilin removes posts.** 675 in-window posts are still listed, against roughly 1,020
  recorded by aggregators over the same period, so about a third have been taken down.
- **Stolen-data types are sparse.** None of these five sites publishes a data inventory
  on its listing. INC's labels describe the extortion stage (`Encrypted`, `Proof`) more
  than the content, except `AD Dump`. `data_types` is filled for only ~3.5% of rows (52).
- **GSG dates are aggregator first-seen dates.** 24 of 42 read 26–27 Jul 2026, which is
  when ransomlook began tracking the group. The site's own news page is dated from
  20 Jun 2026, so every GSG post falls inside the window either way.
- **Industry for INC, DragonForce and SafePay is partly keyword-inferred.**
  `industry_source` separates stated values from inferred ones.
- All victim details are the attackers' claims and have not been verified.
