# Web enrichment of blank fields (cross-reference only)

> **Status: not used as analysis data.** The assignment requires victim data to be collected
> directly from the leak sites, so all charts and figures use `data_v3/merged.csv`. This
> folder is kept as a documented quality check: `data_quality_flags.csv` records leak-site
> values that official sources contradict. Research stopped after wave 1 and will not be
> resumed.

`merged.csv` holds only what the five leak sites published. `merged_enriched.csv` is the
same 1,497 rows with some blank fields filled from public clearnet research. Every filled
cell is traceable to a cited source in `enrichment_log.csv`. `merged.csv` is never
modified, so the leak-site-only dataset is always available for the "collect directly
from the DLS" requirement.

## Status

Research was run on **550 of 1,497 rows** (batches 01–11 of 30, 29 September 2026). It was
cut short by two limits of the research environment, described under Limitations.
Rows 551–1,497 have not been researched.

| Field | Blank before | Filled from web | Filled after (of 1,497) |
|---|---|---|---|
| website | 167 | 39 | 1,369 |
| country | 530 | 137 | 1,104 |
| industry | 234 | 66 | 1,329 |
| revenue_usd | 1,130 | 41 | 408 |
| employee_count | 1,403 | 108 | 202 |
| data_size_gb | 1,153 | 0 | 344 |
| data_types | 1,445 | 4 | 56 |

395 cells in total, cited to 240 distinct source domains.

- **Source type:** official 235, reference 85, data-broker estimate 68, news 7.
- **Confidence:** high 195, medium 133, low 67.

## Method

1. **Worklist.** Every row with at least one blank in the seven fields above went into a
   worklist with: victim name, domain, group, post date, known country and industry, and
   the first 250 characters of the leak-site description (to confirm identity). It was
   split into 30 batches of about 50 rows.
2. **Research.** Each batch was researched by a separate AI research agent using web
   search and page fetches, all under the same written rules:
   - **Identity check first.** The company found must match the row's domain and the
     leak-site context. If in doubt, every field is left blank and the reason noted.
     Several rows were left blank for this reason, e.g. a domain belonging to a different
     company than the one the group described.
   - **Clearnet only.** No leak sites, .onion addresses or stolen data were accessed.
     No captchas, logins or paywalls were bypassed. No one was contacted.
   - **Date rule.** Facts about the breach itself (`data_size_gb`, `data_types`) needed a
     source published 1 Jan – 30 Sep 2026 that reports this incident and names this
     group. Company facts (HQ country, industry, revenue, headcount) use the most recent
     available source, and its date is recorded (`undated` if the page shows none).
   - **Accepted sources:**
     - Official: the company's own site, annual reports, SEC/FDIC filings, company registries
     - News: established outlets and security press
     - Reference: Wikipedia, LinkedIn company pages
     - Estimate: data brokers such as ZoomInfo and RocketReach, for revenue and headcount
       only, always marked `estimate` / low confidence
     - Not accepted: AI-generated text and auto-generated threat-intel posts (DeXpose,
       HookPhish and similar). Aggregators were used only to find an article, and the
       article is what gets cited.
3. **Validation** (`scripts/enrich_merge.py`). Each researched value is rejected unless:
   - the field was blank in `merged.csv` (leak-site values always win);
   - it matches the column format (ISO country code, one of the canonical industries,
     numeric revenue, and so on);
   - it has a source URL;
   - for a breach fact, the source date falls inside the window. One breach fact was
     rejected on this rule.
4. **Output.**
   - `merged_enriched.csv` adds a `<field>_origin` column for each enriched field:
     `leak site`, `web`, `web estimate` or blank.
   - Filter `*_origin != "web estimate"` for the conservative subset, or
     `*_origin = "leak site"` for leak-site data only.

Reproduce with `python3 scripts/enrich_merge.py`, which reads the batch results from
`~/dls/enrich/results/`.

## Finding: leak-site industry labels are often wrong

Researchers flagged known values that official sources contradict. They were reported in
`data_quality_flags.csv` rather than changed: **47 flags, 44 of them industry.**

| Industry origin | Rows checked | Flagged wrong | Rate (lower bound) |
|---|---|---|---|
| Stated by the site (Qilin, GSG labels) | 252 | 29 | 12% |
| Inferred by keyword from description | 189 | 15 | 8% |
| Stated in the description text (INC) | 17 | 0 | 0% |

**Qilin's "Business Services" label is the weak spot.** 15 of the 42 checked (36%) are
really manufacturers, logistics firms, retailers and so on: a cosmetics factory, a car
dealer, an Apple reseller, a container terminal. It is Qilin's most common label (131
in-window posts, mapped to Professional Services). So Professional Services is
over-counted in any industry ranking built on Qilin's labels. Recommended treatment for
Q7: report it as a caveat, or exclude `industry_raw = "Business Services"`. Also a small
Q9 insight: the group labels victims carelessly.

Some flags are taxonomy judgements rather than errors: accounting firms were placed under
Financial Services by the merge but Professional Services by some researchers. Three
flags are country errors made by the group itself. INC Ransom lists a law firm in
Augusta, Georgia, USA as `GE` (the country Georgia), and a Swiss company as `US`.

## Limitations

- **Two limits stopped the research partway through:**
  1. **Web-search limit.** The session allows 200 web searches in total, shared by all
     research agents. It ran out early in wave 1, so most batches researched only their
     first 6–20 rows fully and used direct page fetches for the rest.
  2. **Automated safety check.** The research environment's permission check blocked a
     number of lookups, flagging searches that pair a named company with a ransomware
     group or ask for its revenue as a possible "third-party attack". Those lookups were
     not retried or worked around, and the affected fields were left blank.
- **Breach facts are almost never publicly reported.** Only 4 `data_types` values were
  found, from Comparitech, Cyber Daily/BeyondMachines, teiss and one low-confidence
  blog. Company-issued breach notices (e.g. Loyalist College, Ikegami, Belimed)
  generally don't name the group, so under the attribution rule they were not used.
  Q8 cannot rely on this column.
- **Revenue and employee counts for private firms are mostly broker estimates**, and
  several conflicted or were blocked by the broker (403/429). Conflicting figures were
  left blank or marked low confidence.
- Company facts describe the company as currently documented, not necessarily at the
  moment of the attack.
