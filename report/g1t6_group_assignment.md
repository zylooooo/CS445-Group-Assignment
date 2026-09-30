---
title: "CS445 G1T6 Group Assignment"
author: "Loo Zhi Yi, Sean Elisha Koh Tze Li, Tan Li Quan, Keegan Ravindran, Darren Ong Zhi Zhan, Ingid Størdal Prestegard"
date: "2 October, 2026"
geometry: "top=2cm, bottom=2cm, left=2.5cm, right=2.5cm"
fontsize: 8pt
highlight: tango
titlepage: false
colorlinks: true
listings-no-page-break: true
code-block-font-size: \scriptsize
output: pdf_document
---

## Q1. What countries are most Targeted By Ransomware Actors?

The United States is by the most targeted by ransomware actors, with 356 claimed ransomware victims. This can be seen from \autoref{fig:q1} on the choropleth where United States is the darkest region and in the bar chart where United States leads the other countries. Across the 1, 497 leak-site posts scraped across five ransomware groups, 967 of these posts can be tied to a country. United states accounts for 36.8% of all identifiable claimed victims. This is more than four times Germany in second place (8.4%). From \autoref{fig:q1}, we can also see that nine of the top ten targeted countries are high-income economies in North America, Western Europe and Asia-Pacific, with the exception of Argentina.

One limitation when analyzing this question is that Qilin does not state victim countries, so we inferred them from website domains. This left 463 of it's 675 victims unidentified, most of them on `.com` domains. These figures also only account for victims that ransomware attackers choose to publish and are unverifiable, not all attacks that actually happen.

![Choropleth showing logarthmic color scale of victim count across countries (left) and top 10 countries with claimed victims](assets/Q1.png){#fig:q1 width=100%}

---

## Q2. Why are some countries more targeted than others?

Organisations from higher income countries could be targeted because they have more revenue and more comprehensive cyberthreat insurance coverage to pay higher ransoms. Additionally, ransomware groups also favour high GDP markets with stricter data protection laws, giving ransomware organizations stronger extortion leverage as victims are pressured to pay. The United States, Canada, United Kingdom and Australia make up 51% of our identifiable victims, and the European Union countries in the top ten are covered by the General Data Protection Regulation (GDPR). Lastly, the precense of "safe habours" prevents some countries from being attacked. Russia-linked groups such as Qilin avoid Commonwealth of Independent States (CIS) members to reduce domestic legal exposure [^dexpose]. Our dataset has no victims in Russia, Belarus or Kazakhstan even though we have data from Qilin (grey in \autoref{fig:q1}).

[^dexpose]: DeXpose, ["Qilin Ransomware: Group Profile, TTPs, IOCs & Defense"](https://www.dexpose.io/qilin-ransomware/), 11 May 2026.

---

## Q3. Which ransomware group is the most prolific or successful?

**Qilin** is the most prolific group in our dataset. It published 675 of the 1,497 victim posts (45%) between January and September 2026, more than INC Ransom (326) and DragonForce (302) combined, with SafePay (152) and Global Secret Group (42) well behind (\autoref{fig:q3}).

Qilin's lead is sustained, not a single spike. It posted the most victims in seven of the nine months, never fell below 37 posts a month, and surged from 46 in June to 109 in July and a peak of 142 in August. By contrast, DragonForce faded from 60 posts in April to 10 in September, and INC Ransom stayed flat at 27–47 a month.

Leak sites do not reveal whether a ransom was paid, so "success" can only be inferred. One indirect signal is post removal, which can follow a payment or negotiation. Aggregators recorded about 1,020 Qilin posts in this period but only 675 remain listed, so roughly a third were taken down, against 3–9% for SafePay, DragonForce and INC Ransom. This is an upper bound, because some missing posts are retitled entries or aggregator errors. It also means 675 understates Qilin's true volume.

Finally, Qilin is the leading poster in 18 of our 26 industry categories, so it does not depend on a single victim niche.

![Leak-site posts per group (left) and per month (right), Jan–Sep 2026. September covers 1–28 Sep. Global Secret Group is omitted from the monthly chart because its site shows no post dates.](assets/Q3.png){#fig:q3 width=100%}

---

## Q4. What is so unique about these ransomware actors' TTP that makes them so "successful"?

Most of these groups' techniques are not unique: all of them steal data before encrypting and publish victims who refuse to pay (double extortion). What sets Qilin, the most prolific group in Q3, apart is scale. Dragos attributes its lead to "the scale of its affiliate network and its ability to leverage multiple access vectors rather than any single technical innovation"[^dragos].

**Affiliate economics.** Qilin runs Ransomware-as-a-Service (RaaS) with a reported affiliate share of up to 85% of each ransom[^dexpose]. Access brokers, lateral-movement operators and encryption crews work as separate tiers, which lets it run dozens of intrusions at once[^cyble]. That explains its 675 posts.

**Fast exploitation of edge devices.** Affiliates mainly enter through internet-facing appliances and compromised credentials (MITRE ATT&CK T1190, T1078)[^dragos]. In June 2026, Arctic Wolf investigated several intrusions that began with CVE-2026-0257, an authentication bypass in Palo Alto GlobalProtect[^arcticwolf]. The attackers dumped LSASS and NTDS credentials (T1003), moved laterally with PsExec and RDP (T1021), cleared event logs (T1070) and, in some cases, disabled Microsoft Defender (T1562) before encrypting (T1486). Some affiliates also exfiltrated data to MEGA with Rclone (T1567); others encrypted without stealing anything.

**Layered pressure.** Qilin affiliates have threatened to notify victims' regulators[^dexpose], and its site runs countdown timers on unpublished victims. About a third of its posts later disappear (Q3), which is consistent with delisting after negotiation.

The other groups succeed with different playbooks:

| **Group**           | **Reported by researchers**                                                                                                                                                                | **Our scraped data**                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| INC Ransom          | Specialises by sector, preferring law firms and other holders of sensitive data[^cyble]                                                                                                    | Leads our legal and healthcare categories; publishes revenue for every victim; only 50% of posts are labelled "Encrypted"                           |
| DragonForce         | "Cartel" branding; a data audit service that mines stolen datasets over 300 GB for leverage[^checkpoint]; one affiliate hid command-and-control traffic in Microsoft Teams relays[^dragos] | States the stolen data volume for every victim (median 123 GB)                                                                                      |
| SafePay             | Centralised, non-RaaS operation[^checkpoint]                                                                                                                                               | Identical 72-hour deadline for every victim                                                                                                         |
| Global Secret Group | No verified TTP reporting; its access methods, malware and affiliate model remain unknown[^cyberedition]                                                                                   | Most detailed listings in our set: country, industry, headcount and data size for all 42 victims (median 211 GB), revenue for 41, but no post dates |

[^cyberedition]: The Cyber Edition, ["Global Secret Group Ransomware Claims Over 202,000 Victims on New Leak Site"](https://thecyberedition.com/global-secret-group-ransomware-claims-over-202000-victims-on-new-leak-site/), 27 Jul 2026.
[^dragos]: Dragos, ["Industrial Ransomware Analysis for Q2 2026"](https://www.dragos.com/blog/dragos-industrial-ransomware-analysis-q2-2026), 10 Aug 2026.
[^checkpoint]: Check Point Research, ["The State of Ransomware – Q1 2026"](https://research.checkpoint.com/2026/the-state-of-ransomware-q1-2026/), 11 May 2026.
[^arcticwolf]: Arctic Wolf Labs, ["Exploitation of CVE-2026-0257 Leads to Qilin Ransomware"](https://arcticwolf.com/resources/blog/exploitation-of-cve-2026-0257-leads-to-qilin-ransomware/), 20 Jul 2026.
[^cyble]: Cyble, ["Ransomware Threats in the Americas H1 2026"](https://cyble.com/blog/ransomware-threats-in-america-h1-2026/), 14 Aug 2026.

---

## Q5. Is it common for threat actors to "re-brand" or "repurpose" older data leaks or public breaches to inflate their reputation?

It happens, but in our data it is a minority tactic, and inflated claims are more visible than recycled data. The incentive is structural: in the leak-site economy, posting volume signals credibility to victims and to potential affiliates, and because posts are unverified claims they cost little to fake.

**Inflated claims.** Global Secret Group (GSG) launched its leak site in July 2026 claiming about 202,020 victims, while researchers counted roughly 20 disclosed victims on 26 July[^cyberedition]. By late September we could scrape only 42. The headline figure advertises a reach the site itself does not show.

**Recycled leaks.** INC Ransom's site records both when a post was created and when the data was leaked. Six of its 326 posts in 2026 carry leak dates one to twelve months before the post. Silicon Integrated Systems, for example, was posted on 17 September 2026 with a leak date of 9 December 2025. One more victim, `cambrialawfirm.com`, was listed twice (13 August and 28 September), the second time marked "Re-uploaded; the old download link was unavailable".

**Re-branding.** Brands are also fluid. DragonForce markets itself as a "cartel" of sub-brands, but Check Point found the model "smaller than advertised", and one supposed sub-brand, Coinbase Cartel, was linked to a different operation, ShinyHunters[^checkpoint]. Analysts also could not yet tell whether GSG is a genuinely new group or a rebrand of an existing one[^cyberedition].

We therefore see evidence of inflation or recycling in two of our five groups. However, one group's post dates cannot establish how common the practice is across the whole ecosystem.

---

## Q6. Does victim company size or revenue puts them at higher / lower risk of attacks by ransomware actors?

---

## Q7. Which Industries Are More Prone To Ransomware Threats? Why?

---

## Q8. We know actors target sensitive data, but what kind of data do actors usually target? What are the kinds of data targeted in each industry? Show a breakdown comparing types of data stolen

---

## Q9. Share 3 interesting insights you observed

---

## Q10. Share lessons learnt, what were your struggles in executing the project and how did you overcome them?
