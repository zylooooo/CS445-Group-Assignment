---
title: "CS445 G1T6 Group Assignment"
author: "Loo Zhi Yi, Sean Elisha Koh Tze Li, Tan Li Quan, Keegan Ravindran, Darren Ong Zhi Zhan, Ingid Størdal Prestegard"
date: "2 October, 2026"
geometry: "top=2cm, bottom=2cm, left=2.5cm, right=2.5cm"
fontsize: 11pt
highlight: tango
titlepage: false
listings-no-page-break: true
code-block-font-size: \scriptsize
output: pdf_document
---

## Q1. What countries are most Targeted By Ransomware Actors?

The country most targeted by ransomware actors is the United States. 356/716 (~50%) of posts with the victim's country stated on the CLS websites are from the US. It is visible as the darkest region on the choropleth map and the top row of the group-by-country heat map. Germany (56), Canada (33), the United Kingdom (30) and Italy (20) are the next most frequently attacked countries, showing that the top five targeted countries are all high-income Western economies.

![Choropleth of victim distribution by country (log victim count).](<assets/Map Showing distribution of victims.png>)

![Heat map of the top 10 countries targeted per group (log victim count).](<assets/Heat map of top 10 countries targeted per group.png>)

---

## Q2. Why are some countries more targeted than others?

Organisations from higher income countries could be targeted because they have more revenue and more comprehensive cyberthreat insurance coverage to pay higher ransoms. Additionally, these countries tend to be more developed, with stricter data breach notification laws, which make ransomewares more damaging, giving threat actors stronger extortion leverage. The heat map also shows that each group has a country it is more focused on. For example, INC Ransom focuses more on the US (57% of its stated-country victims), while SafePay's top target is Germany. (as shown by the Heat Map above)

---

## Q3. Which ransomware group is the most prolific or successful?

**Qilin** is the most prolific group in our dataset. It published 675 victim posts between January and September 2026, more than double INC Ransom (326) and DragonForce (302), with SafePay (152) and Global Secret Group (42) trailing behind.
Qilin is also the most consistent and fastest-growing group: the monthly line chart shows it never dropped below 37 posts in a month and surged from 46 in June to 109 in July and a peak of 142 in August, while DragonForce faded from 60 posts in April to about 10 per month by September.
While leak sites rarely reveal whether a ransom was paid. We can infer that removal of posts mean that the victim paid the ransom. Out of the ~1,020 Qilin posts in 2026 recorded by aggregator sites, only 675 remain listed, meaning about a third were taken down. This could mean that about a third of the ransomware attacks on companies that Qilin targeted were successful. Meanwhile, other groups we tracked removed only about 3-19% of their listings, suggesting a lower success rate.
Lastly, Qilin has targeted multiple industries, being the top group in targeting all industries, especially professional services and manufacturing. This shows that it is not dependent on a single victim niche.

![Total data leak posts per group (distinct victims, Jan-Sep 2026).](<assets/Total data leak posts per group.png>)

![Data leak posts per group per month, Jan-Sep 2026 (September partial).](<assets/Data leak posts per group per month.png>)

---

## Q4. What is so unique about these ransomware actors' TTP that makes them so "successful"?

Qilin operates using a Ransomware-as-a-Service model. ... ...
---

## Q5. Is it common for threat actors to "re-brand" or "repurpose" older data leaks or public breaches to inflate their reputation?

Yes, it is a common practice for threat actors to "re-brand" or "repurpose" because it is a structural incentive for the leak-site or Ransom as a Service (RaaS) economy. Leak-site volume vouches for a Ransomware group's credibility and provides a strong recruiting signal for RaaS affiliates. Posts on data leak sites are usually unverified calims, not confirmed breaches. For the Ransomware groups, this means that posts have a low cost to fabricate while providing high rewards in visibility and potential profits. On top of profitability, rebranding also resets sanctions lists and law enforcement tracking, allowing Ransomware groups to escape scrutiny.

TODO: add in analysis and evidence from own research from the dataset / visualizations generated.

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
