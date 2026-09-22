# Methodology

Collection and normalisation record for a study of five ransomware data leak sites.

## 1. Scope and data window

**Window:** 1 January 2026 to 30 September 2026. Any listing outside this range is retained in
the dataset but marked `in_window = no` and excluded from analysis.

**Sites collected:** Qilin, INC Ransom, DragonForce, Play, SafePay.
**Sites attempted and not collected:** The Gentlemen, LockBit.

**Totals:** 3,432 posts collected in all, of which **1,558 fall inside the window**:

| Group | In window | Total collected | Archive span |
|---|---|---|---|
| Qilin | 646 | 1,200 | 4 Apr 2025 to 17 Sep 2026 |
| INC Ransom | 311 | 825 | 9 Apr 2024 to 17 Sep 2026 |
| DragonForce | 296 | 621 | 6 Dec 2023 to 16 Sep 2026 |
| Play | 162 | 234 | 16 Jul 2025 to 10 Sep 2026 |
| SafePay | 143 | 552 | 2 Aug 2025 to 15 Sep 2026 |

Every site's archive reaches back beyond 1 January 2026, so the window is fully covered on all
five.

**Note on file timestamps.** The collection machine's clock ran approximately one day behind
during the first sessions, so some capture filenames are stamped 2026-09-17 although the
capture was made on 2026-09-18. Post dates in the datasets are read from the sites themselves
and are unaffected.

## 2. Site selection

Candidates were shortlisted by posting volume during the window, using an aggregator's records
for an initial view. The final five were chosen to balance scale against field richness, since
no single site publishes everything the study needed:

- **Qilin** for volume, being the highest-posting group in the period.
- **INC Ransom** because it publishes country and revenue for every victim, plus explicit
  category labels for the stolen data. It closes the gaps the other sites leave.
- **DragonForce** because it publishes an exact data volume per victim.
- **Play** as a second independent source of country, and for its contrasting targeting
  profile.
- **SafePay** for its extortion deadline data and per-victim company profiles.

Two further candidates were attempted and dropped, both documented in section 5.

## 3. Collection approach

Common to all five sites:

- All traffic routed through Tor using a local SOCKS5 proxy, with remote hostname resolution
  so `.onion` addresses resolve correctly.
- A fetch script and a parse script per site, kept separate so that captures can be re-parsed
  without re-fetching.
- Raw captures written to disk and retained, so any figure in this document can be traced back
  to the page it came from. This satisfies the requirement that conclusions be defensible,
  repeatable and understandable.
- Randomised pauses between requests, and a limit of three retries per page.
- Deduplication on each site's own post identifier rather than on victim name, since names
  repeat and are sometimes edited while identifiers are stable. This makes captures from
  different dates safe to merge.
- **Mirror addresses were never committed to version control.** They rotate constantly and are
  sourced per run from an aggregator's group pages. Every fetcher takes the address as an
  argument.

Aggregator data was used only for cross-referencing and for locating current mirrors, never as
a source of victim records. All victim data in this study was collected directly from the
groups' own sites.

## 4. Per-site collection

### Qilin

Server-rendered HTML with server-side pagination at `/?page=N`, 20 victims per page across 62
pages.

**Result:** 1,200 unique posts, 12 pending and 1,188 published. 646 rows fall in the window,
covering 645 unique victim names, the single difference being a repeated name kept apart by
its post identifier.

**Fields:** victim name, an industry-style label, company website URL, post date, photo count,
a countdown timer on unpublished posts from which pending or published status is derived, and
a post identifier.

**Not available:** country, revenue, employee count, or any text describing the stolen data.
Victim detail pages contain images only, which were not downloaded. Country therefore has to
be inferred from the company URL where the domain suffix allows it.

### INC Ransom

A single-page application: the HTML shell is 448 bytes and the victim data is served by a
separate backend host over an open JSON API, which was identified by reading the site's public
application bundle. The endpoint reports a total count alongside each page, so completeness
can be checked rather than assumed. No authentication and no challenge was involved.
Collected over 17 pages at 50 records per page.

**Result:** 825 announcements, 311 in window. Country present for 825 of 825 across 68
distinct countries; revenue present for 825 of 825.

**Fields:** victim name, country, revenue in USD, category labels for the stolen data
(examples: Encrypted, Proof, Stocks, AD Dump), a free-text description that frequently states
industry, employee band and headquarters city, a visit counter, and leak, created and updated
timestamps.

**Endpoints deliberately not used:** `create/report` and its captcha, and the `download`,
`get/file` and `get/folder` endpoints, which serve the stolen files themselves.

### DragonForce

A Nuxt application whose visible listing paginates client-side, so the page URL never changes
and a plain fetch returns only the first page. The underlying endpoint
`/api/guest/blog/posts` with a page parameter was identified by reading the public application
bundle. The API declares a total count, which allowed completeness to be proven rather than
assumed: it reported 621 publications and 621 were collected, over 26 pages.

**Result:** 621 publications, 296 in window.

**Fields:** victim name, website, address, exact data volume in bytes, tags, description, post
date, publication deadline, and whether the countdown has been stopped. Every publication
carries a data volume, totalling approximately 142 TB. Structured tags are sparse, present on
only 23 of 621, so the first line of the description, which states a volume band such as
"Full DATA 400 GB+", is the more usable categorical field. No country or revenue.

### Play

A minified, table-based site with server-side pagination at `index.php?page=N`, discovered
from an inline `goto_page` function. The markup is malformed, with unclosed elements, so the
parser isolates each victim block by its `viewtopic` identifier and reads fields with targeted
patterns rather than by walking the document tree.

The site recycles content past its last page: pages 1 to 20 are distinct, and pages 21 onward
repeat earlier ones. The archive is therefore 20 pages, and redundant captures were discarded.
The generic fetcher was subsequently given hash-based repeat detection so this halts
automatically.

**Result:** 234 victims, 162 in window. Country present for all 234.

**Fields:** victim name, country as a full name, website, view count, added date, publication
date, and a status badge.

### SafePay

A Bootstrap card layout with server-side pagination at `?page=N`, 9 to 11 victims per page
over roughly 62 pages. Country is encoded only in the `alt` attribute of a flag image, and the
countdown bar carries both the start and the end of the extortion deadline, so the deadline
length can be derived exactly.

**Complication:** published victims lose their countdown bar, and with it the only date shown
on the listing page. After the first parse, 528 of 552 rows had no date. Dates were recovered
from each victim's detail page, fetched and cached individually, which also yielded a click
count and a fuller company profile. All 552 detail pages were fetched with no failures.

**Result:** 552 victims, 143 in window. Country present for 526 of 552 across 32 countries.
Every observed deadline is exactly 72 hours.

## 5. Sites attempted and not collected

### The Gentlemen

The mirror was reachable, but the site root returns an anti-bot interstitial titled
"Gentlecloud Protection" instead of victim listings. A direct fetch returned 8,150 bytes of
challenge page and zero victim entries.

Mechanics observed in the challenge page source:

- Canvas fingerprinting, with the rendered image used as an identifier.
- Mouse movement and click tracking collected in the background.
- Screen resolution check, rejecting 800x600, 1x1 and 0x0 as headless or virtualised.
- A timing floor of roughly 3 to 8 seconds before verification may proceed.
- A SHA-256 proof of work against a server-supplied challenge and difficulty.
- An explicit `navigator.webdriver` check, which exists to detect browser automation.
- A human checkbox, after which a proof object is posted to a verification endpoint.

**Decision.** No attempt was made to defeat the challenge. Solving the proof of work, spoofing
the fingerprint, masking the automation flag, or reusing a human-solved session token inside
an automated scraper would each constitute circumventing a bot-detection control. Another site
was substituted instead. Access was never gained and no victim data was collected here.

**Relevance.** The group operates its own branded anti-bot service with proof of work and
browser fingerprinting, which is evidence of professionalised infrastructure and of capability
that sits at the behavioural rather than the indicator level. It is also a limitation on this
study and on public ransomware statistics generally: sites that resist automated collection
are systematically under-represented in datasets built this way.

### LockBit

The reachable site titles itself "LockBit 5.0" while being hosted on an address from the
`lockbitapt` family associated with LockBit 3.0, much of which was seized during Operation
Cronos in February 2024. The version number advanced across seizure and relaunch while the
address lineage persisted. This is a direct observation of how an established brand is
renumbered and revived rather than replaced, and it stands independently of whether the site
was collected.

**Collection outcome.** The site places an access queue in front of its listings, advertising
a wait of under three minutes and an automatic redirect. A client that waited out the
advertised time and returned with the same session cookie received a byte-identical queue
page, so the listings were never reached. How the queue decides to admit clients was not
investigated, since that would mean working around a load control rather than using the site.
DragonForce was substituted for the remaining slot.

### The distinction applied

Accepting a session cookie, or waiting out an advertised queue, is ordinary client behaviour
and was done where a site required it. Defeating a challenge designed to detect automation is
not, and was not attempted. Both non-collections follow from that line.

## 6. Methodology decisions

**Which timestamp counts as the post date.** Sites expose more than one. INC Ransom carries
both a creation date and a leak date, and filtering the window on each gives 311 and 281
victims respectively, a difference driven by 42 entries whose leak date precedes their
creation date. This study uses the publication or creation date on every site, because it
corresponds to when the victim appeared on the leak site and matches what an aggregator
observes, keeping cross-source comparisons consistent. The leak date is retained in the
dataset and used only in the analysis of possibly recycled material.

**What was never fetched.** No leaked files were downloaded from any site. Detail pages were
fetched only where they carried metadata the listing page omitted, which was SafePay alone.

## 7. Merge and normalisation

The five per-site datasets are combined onto one 22-column schema, producing 3,432 rows of
which 1,558 fall inside the window, plus a separate record of victims claimed by more than one
group.

**Country.** INC Ransom and SafePay publish ISO two-letter codes, Play publishes full names,
and Qilin and DragonForce publish neither. Codes and names are mapped onto a single
representation. Where a site states nothing, the country-code suffix of the victim's own
domain is used. Generic suffixes such as `.com` carry no location information and are left
blank rather than guessed.

**Industry.** Only Qilin states an industry. For the other four it is classified from
description text by scoring how many distinct keywords each candidate industry matches, with
the victim name and first sentence weighted double.

An earlier first-match-wins version was discarded after spot-checking revealed systematic
error: the stolen-data inventory embedded in descriptions was driving the classification. A
fast-food franchise partner was classified as Financial Services because its leak listing
mentioned loan applications and banking records, and an agricultural producer was classified
as Manufacturing on the word "agro-industrial". The inventory text is now cut before
classification, and scoring replaced first-match-wins. The correction moved Financial Services
from 132 victims to 55 and Healthcare from 159 to 107, so the original figures would have
produced a materially wrong industry ranking.

**Provenance.** Every derived value records how it was obtained. `country_source` is either
stated or inferred from domain. `industry_source` is stated by site, stated in description, or
inferred from description. `industry_confidence` is high or low. This keeps values stated by
the source separable from values this pipeline derived, inside the data itself rather than
only in prose.

## 8. Coverage and limitations

Coverage inside the window, out of 1,558 victims:

| Attribute | Coverage | Notes |
|---|---|---|
| Country | 888 (57 percent) | 62 distinct countries |
| Industry | 1,191 (76 percent) | of which 978 high confidence |
| Revenue | 311 | INC Ransom only |
| Data volume | 296 | DragonForce only |
| View counts | 616 | INC Ransom, Play and SafePay |

Country coverage by site is highly uneven: 100 percent for INC Ransom and Play, 99 percent for
SafePay, but 31 percent for Qilin and 24 percent for DragonForce, because those two publish
only a company URL and most are generic domains.

**Principal limitations.**

1. Any country ranking rests on the 888 victims whose country is known, not on all 1,558, and
   the two sites with the weakest country coverage are also two of the largest. The ranking is
   therefore weighted toward the three sites that publish country outright.
2. Industry for four of the five sites is inferred from free text by keyword scoring, which is
   approximate. The `industry_confidence` column identifies the weaker classifications.
3. Revenue and data volume each come from a single site and do not generalise.
4. The five sites are not a random sample. Two candidates were excluded because they resist
   automated collection, which biases this dataset in the same direction as the public
   statistics it might be compared against.
5. All victim information originates from attacker claims and is not independently verified.

## 9. Findings

### Listing retention differs sharply by group

Victims collected directly from each site inside the window, against the count an aggregator
observed over the same period:

| Group | Collected | Aggregator | Absent from live site |
|---|---|---|---|
| Qilin | 646 | 989 | approximately 35 percent |
| Play | 162 | 199 | approximately 19 percent |
| INC Ransom | 311 | 343 | approximately 9 percent |
| DragonForce | 296 | 318 | approximately 7 percent |
| SafePay | 143 | 148 | approximately 3 percent |

Four groups cluster between 3 and 19 percent, while Qilin removes roughly a third of its
listings. Post removal therefore appears to be a group-level policy rather than a general
property of leak sites. Candidate explanations include differing payment or negotiation rates
and differing attitudes to curating the public record.

A closer title-by-title comparison for Qilin found 407 of 989 observed titles absent from the
live site, about 41 percent, and 63 posts present on the site that the aggregator never
recorded. The 407 figure is an upper bound on true removals, because the absent set visibly
mixes genuinely removed posts, retitled posts, and aggregator noise such as truncated titles
and single posts bundling several companies. Neither source is complete on its own, which is
what justifies using both.

**Methodological consequence:** a single snapshot of one leak site measures that group's
housekeeping as much as its activity.

### The same victims are listed again by other groups

Three victims appear on two different leak sites, and in every case the pattern is
re-victimisation rather than a simultaneous claim:

| Victim | First listing | Second listing | Gap |
|---|---|---|---|
| allmaxnutrition.com | INC Ransom, 27 Aug 2025 | Play, 26 Jan 2026 | 5 months |
| gdz.com | Play, 10 Sep 2025 | Qilin, 8 Jan 2026 | 4 months |
| jubileejobs.org | INC Ransom, 7 Jul 2025 | Qilin, 25 Jul 2026 | 12 months |

Being listed once does not end the exposure, and settling with one group evidently offers no
protection from another. Three overlaps out of 1,558 in-window victims also shows that these
groups rarely compete for the same target.

### Targeting breadth is a group characteristic, not an ecosystem one

Play's victims are 84 percent United States, 196 of 234, followed by Canada with 19 and the
United Kingdom with 7, across only 10 distinct countries in total. INC Ransom spans 68
countries over 825 victims.

An aggregate country ranking therefore conceals which groups drive it, and the ranking itself
depends on which sites were selected for study.

### Extortion workflows differ in kind, not only in scale

- **SafePay** applies a uniform 72-hour deadline to every victim, with no variation by country
  or size, which suggests a standardised and largely automated process rather than per-victim
  negotiation.
- **Play** publishes only completed leaks, 207 marked full and 27 partial, with no pending
  victims or live countdowns anywhere on the site. Qilin and DragonForce both maintain
  countdown timers against unpublished victims.

### Several groups run professionalised infrastructure

Three of the sites examined operate systems that would not look out of place in a commercial
software team. The Gentlemen runs a branded bot-detection service with proof of work and
fingerprinting. INC Ransom runs a single-page frontend against a separate backend API with a
content delivery network for file distribution. LockBit fronts its blog with an access queue.

Two of the five also invest visible effort in presenting victims credibly: INC Ransom publishes
a revenue figure for every victim, in banded formats characteristic of commercial
business-intelligence data, and SafePay publishes a written company profile naming the
headquarters, founding year and service lines. Both function as pressure and reputation
mechanisms rather than as necessary parts of an extortion.

One contrasting observation: SafePay loads favicons from Google and country flags from a
public content delivery network, so visitors' browsers contact ordinary internet services
while viewing the leak site.
