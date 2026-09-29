# G1T6 Group Assignment Guide: Answering Q1–Q10 with `data_v3/merged.csv`

This guide maps every column in `data_v3/merged.csv` to the assignment questions, and gives
the recommended chart, filters and caveats for each question.

**Dataset:** 1,497 victim posts collected directly from five ransomware data leak sites
(Qilin, INC Ransom, DragonForce, SafePay, Global Secret Group), posted 2 Jan – 28 Sep 2026.
Collection ran on 28–29 Sep 2026, so September is partial.

**Use `data_v3/merged.csv` for every chart and figure.** Two other sources exist but are not
part of the dataset:

- `data_v2/` fails the Jan–Sep window rule (it has no date column) and has no scripts for
  three of its five sites.
- `data_v3/cross_reference/` holds web research, kept only as a quality check on leak-site
  values.

---

## 1. Column reference

| #   | Column            | Filled | Example                                               | What it is                                                                | Used for                                 |
| --- | ----------------- | ------ | ----------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------- |
| 1   | `group`           | 100%   | `INC Ransom`                                          | Leak site that published the post                                         | All                                      |
| 2   | `victim`          | 100%   | `cambrialawfirm.com`                                  | Victim name as published                                                  | Q5, Q9                                   |
| 3   | `website`         | 88%    | `cambrialawfirm.com`                                  | Victim's domain                                                           | Cross-group matching for Q5 (none found) |
| 4   | `country`         | 64%    | `CA`                                                  | ISO two-letter country code                                               | Q1, Q2                                   |
| 5   | `country_name`    | 64%    | `Canada`                                              | Full country name; **use for Tableau maps**                               | Q1, Q2                                   |
| 6   | `country_source`  | 64%    | `stated`                                              | `stated`, `stated in address/location`, or `inferred from domain`         | Q1 filter                                |
| 7   | `industry`        | 84%    | `Education`                                           | One of ~25 canonical categories                                           | Q7, Q8                                   |
| 8   | `industry_raw`    | 46%    | `Freight & Logistics Services`                        | The site's own label (Qilin, GSG)                                         | Q7 caveat, Q9                            |
| 9   | `industry_source` | 84%    | `inferred from description`                           | `stated by site`, `stated in description`, or `inferred from description` | Q7 filter                                |
| 10  | `revenue_usd`     | 24%    | `15000000`                                            | Revenue claimed by the group (INC, GSG only)                              | Q6                                       |
| 11  | `data_volume`     | 22%    | `783 GB (501,662 Files, 42,890 Folders)`              | Size label as published                                                   | Q8 notes                                 |
| 12  | `data_size_gb`    | 22%    | `783.0`                                               | Numeric size in GB (DragonForce, GSG only)                                | Q8                                       |
| 13  | `data_categories` | 21%    | `Encrypted; Proof`                                    | The site's own leak labels (mostly INC)                                   | Q8                                       |
| 14  | `data_types`      | 3%     | `Personal data (PII); Employee / HR`                  | Kinds of data stolen, keyword-derived                                     | Q8 (small sample)                        |
| 15  | `employee_count`  | 6%     | `1000-4999`                                           | Headcount as published                                                    | Too sparse; not used                     |
| 16  | `description`     | 54%    | `Re-uploaded; the old download link was unavailable.` | The site's text about the victim                                          | Q5, Q9 quotes                            |
| 17  | `post_date`       | 100%   | `2026-09-28`                                          | Date the victim appeared on the site                                      | Q3, Q7, Q9                               |
| 18  | `post_month`      | 100%   | `2026-09`                                             | `post_date` as `YYYY-MM`                                                  | Q3, Q9 trend charts                      |
| 19  | `date_source`     | 100%   | `stated by site`                                      | GSG = aggregator first-seen date                                          | Exclude GSG from trend charts            |
| 20  | `still_listed`    | 100%   | `yes`                                                 | `no` = removed from the site since the 17–18 Sep capture                  | Q9 (only 2 rows)                         |
| 21  | `recycled_flag`   | 21%    | `yes`                                                 | INC only: re-posted older leak                                            | Q5                                       |
| 22  | `source_id`       | 100%   | `6ab9da399cd108bf260627e8`                            | The site's own post id                                                    | Traceability; count with `COUNTD`        |

### Columns the dataset does not have

None of the five leak sites publishes these, so they cannot be used:

- **Ransom amount and currency.** No site publishes a ransom demand, so currency
  normalisation cannot be done.
- **Initial access vector.** Comes from threat-intel reports, not leak sites.
- **Double-extortion flag.** Every leak-site post is double extortion by definition, so the
  column would be "yes" on every row.

---

## 2. Question by question

### Q1. What countries are most targeted? (1 point)

- **Columns:** `country_name`, `country_source`, `group`
- **Chart:** bar chart of the top 10 countries by post count.
  - Filter `country_source` to `stated` or `stated in address/location` (n = 716) and put
    the n in the chart title.
  - Result: US 356, Germany 56, Canada 33, UK 30, Italy 20.
- **Optional:** a small choropleth map alongside. Don't use a map on its own: the US
  (356 posts) against Germany (56) leaves every other country visually blank.
- **Caveat:** Qilin publishes no country, and domain-ending inference misses US firms on
  `.com`. That is why the filter above excludes `inferred from domain`.

### Q2. Why are some countries more targeted? (1 point)

- **Columns:** `country_name` by `group` (optional chart)
- **Chart (optional):** 100% stacked bar of each group's top countries. It shows targeting
  differs by group: INC is 57% US, while SafePay's top country is Germany.
- **Answer from research** for the top countries in Q1:
  - GDP and ability to pay
  - cyber-insurance uptake
  - US breach-disclosure laws, which raise visibility
  - English-language targeting by operators and affiliates
  - groups avoiding CIS countries

### Q3. Which group is the most prolific or successful? (3 points)

There is no ransom data, so "prolific" is measured by post volume.

| Chart                                                             | Columns                                                   | What it shows                                                                                                           |
| ----------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **3a. Posts per group** (bar)                                     | `group`, COUNTD(`source_id`)                              | Qilin 675 (45%), INC 326, DragonForce 302, SafePay 152, GSG 42. **Main answer.**                                        |
| **3b. Posts per month per group** (line chart or small multiples) | `post_month`, `group`, COUNTD(`source_id`); exclude GSG   | Consistency of activity: Qilin surges Jul–Aug (109 → 142); DragonForce falls from 60 to 10 a month; INC steady at 27–47 |
| **3c. Targeting breadth** (table or bar)                          | COUNTD(`country_name`) and COUNTD(`industry`) per `group` | Broad versus narrow targeting                                                                                           |

- **On "successful":** state that payment outcomes can't be seen on leak sites. As a possible
  signal only, cite that aggregators recorded ~1,020 Qilin posts in the window while 675
  remain listed. About a third were removed, which may reflect payment.
- **Don't** compare groups on `data_size_gb`: only DragonForce and GSG publish it.
- **Avoid dual-axis charts.** Use small multiples.

### Q4. What makes these actors' TTPs so "successful"? (3 points)

- **Columns:** none; build on the Q3 result.
- **Research:** MITRE ATT&CK group pages and CISA advisories for the leading group(s).
  - Qilin, INC Ransom and DragonForce are ransomware-as-a-service, so **initial access
    varies by affiliate**. What is consistent is the group's tooling and extortion model.
- **Add first-hand site observations** (original evidence):
  - Qilin's posting volume and post removal
  - INC Ransom's separate backend API
  - SafePay's standardised deadlines
  - Global Secret Group's press page

### Q5. Is re-branding or recycling of older leaks common? (2 points)

- **Columns:** `recycled_flag`, `description`, `post_date`
- **Evidence:**
  - 39 of 326 INC posts (12%) are flagged as recycled. Quote the "Re-uploaded; the old
    download link was unavailable" descriptions.
  - GSG claims 202,000 victims but lists 42.
  - LockBit relaunched as "5.0" on an older address lineage (see `METHODOLOGY.md`).
- **Chart (optional):** a single bar or callout.
- **Caveat:** one group's flag is evidence that recycling happens, not an ecosystem-wide rate.

### Q6. Does company size or revenue raise or lower risk? (2 points)

- **Columns:** `revenue_usd`, `group` (INC and GSG only, n = 367)
- **Chart:** histogram of revenue bands on a log scale. **Not a scatter plot:** every row is a
  victim, so there are no non-victims to compare against.

  | Revenue band | Posts |
  | ------------ | ----- |
  | Under $10M   | 179   |
  | $10–50M      | 113   |
  | $50–250M     | 48    |
  | $250M–1B     | 16    |
  | $1B+         | 11    |

- **To discuss risk:** compare against a cited baseline of business sizes (e.g. US Census data
  on firm sizes). Without a baseline, say "victims cluster in the $5–30M mid-market", not
  "small firms are at higher risk".
- **Caveats:**
  - Revenue is the attacker's claim, and 72% of values are round numbers.
  - It comes from 2 of 5 groups.
  - Don't use `employee_count` (6% filled).

### Q7. Which industries are most prone, and why? (3 points)

- **Columns:** `industry`, `industry_raw`, `industry_source`, `group`, `post_month`
- **Charts:**
  - **7a.** Bar chart of industries. Show `industry_raw` = "Business Services" (Qilin, 131
    posts) as a separately labelled bar, or exclude it. Official sources contradicted at
    least 36% of those checked (`data_v3/cross_reference/data_quality_flags.csv`).
  - **7b.** Heat map of group × industry.
  - **Optional:** a filter on `industry_source` to show the ranking holds using only labels
    the sites stated. A bump chart by quarter is possible, but monthly is too noisy.
- **"Why":** research on downtime cost, legacy IT, sensitive data holdings, and thin
  security budgets.
- **Caveat:** the same base-rate issue as Q6. Manufacturing is also a large share of all
  firms.

### Q8. What kinds of data are targeted, by industry? (5 points)

The weakest area in the data. Build it from three honest pieces plus cited research:

| Chart                                    | Columns                                       | Rows                    |
| ---------------------------------------- | --------------------------------------------- | ----------------------- |
| **8a. Heat map of industry × INC label** | `industry`, `data_categories` split on `"; "` | 326 (INC)               |
| **8b. Median data volume by industry**   | `industry`, `data_size_gb` (median, not sum)  | 344 (DragonForce + GSG) |
| **8c. Heat map of industry × data type** | `industry`, `data_types` split on `"; "`      | 52 (show n clearly)     |

- **What INC's labels mean:** *Proof* = sample files, *Encrypted* = systems encrypted,
  *AD Dump* = Active Directory export, *Stocks* = unclear. They describe the extortion stage
  more than the content.
- **Supplement** with cited industry reports on what is stolen by sector: PHI in healthcare,
  student records in education, engineering and design files in manufacturing.
- **State plainly** that these five sites don't publish detailed stolen-data inventories.
- Use heat maps. Tree maps and packed bubbles are poor for comparing across industries.

### Q9. Three interesting insights (9 points)

Spend the most effort here. One chart each:

1. **Qilin's posts disappear and its labels are unreliable.**
   - About a third of Qilin posts recorded by aggregators are no longer listed.
   - At least 36% of its "Business Services" labels were contradicted by official sources.
   - Point: leak-site data needs checking before anyone relies on it.
   - Columns: `group`, `industry_raw`, plus `cross_reference/data_quality_flags.csv`.
2. **Each group changes pace differently.** Reuse chart 3b with annotations: Qilin's Jul–Aug
   surge against DragonForce's decline from April.
3. **Groups run the leak site as a business front.**
   - SafePay's standardised deadlines, now ~84 hours rather than 72
   - GSG's press page linking to its own news coverage
   - INC's 39 re-posts and backend API
   - A table or annotated screenshots work well here.

### Q10. Lessons learnt and struggles (1 point)

No chart. Material:

- Sites dropped for captcha or anti-bot controls: The Gentlemen, LockBit, PayoutsKing.
- Akira's only mirror offline throughout collection.
- Collection bugs found and fixed:
  - silent early stops on HTTP errors
  - pages repeating past the end of the archive
  - industry mis-mapping ("Hospitality" read as healthcare)
- Switching from the `data_v2` group set to a scripted, date-filtered `data_v3`.
- Deciding against web-enriching blank fields, because it would break the "collect
  directly from the DLS" rule.

---

## 3. Page budget

10 pages maximum. Prioritise by points: Q9 (9), Q8 (5), then Q3, Q4 and Q7 (3 each).
Aim for 8–10 charts in total.

## 4. Tableau set-up

- Count posts with **COUNTD(`source_id`)**.
- Set `country_name` to the **Country/Region** geographic role.
- Make `revenue_usd` and `data_size_gb` numeric measures, and `post_date` a **Date**.
- Split `data_categories` and `data_types` on `"; "` for the Q8 heat maps.
- Mark September as partial (data ends on 28 Sep) on any monthly chart.
- Exclude `group = "Global Secret Group"` from monthly charts: its dates are aggregator
  first-seen dates.
- Put the n (number of posts) in every chart title where a filter or a partial column is
  used.
