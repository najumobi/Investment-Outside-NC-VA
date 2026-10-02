# Crime at block level: what it can and cannot tell a first-time 2–4-unit buyer about the first two years (2026-09-30)

Scope: block level throughout (a CrimeGrade block group is about 1,450 residents). Overall, Violent and Property crime are retired and not used. Evidence: the Philadelphia/Cleveland validation in `validation/` (colours vs. 4,000 recorded robberies, 918 block groups), NIBRS 2019 location tables, FBI 2023/2024 summaries, Cleveland's per-type block-group statistics, and the ordinance checks in section 4.

## 1. Are the two questions enough?

No. "Will this building cost me money?" and "Will tenants (or I) walk here?" cover the operating account. Five other things move a first-two-year result at least as much, and crime enters each differently.

| # | Question | What decides it in years 1–2 | Where block-level crime enters |
|---|---|---|---|
| Q0 | Did I pay the right price for what this is? | Entry price against stabilised value and resale comps; usually the largest swing in a two-year result (equity, not cash flow) | Only through Q5 |
| Q1 | Will this building cost me money? | Capex surprises (roof, sewer lateral, HVAC, lead, wiring), compliance costs, insurance, taxes after reassessment, utilities in the owner's name, turnover repairs | Burglary (break-ins during vacancy, copper/HVAC), Vandalism (glass, doors, graffiti); Arson only through vacant neighbours |
| Q2 | Will tenants (or I) walk here? | Days to lease, rent discount, applicant quality, whether a property manager will take the address, whether the owner will visit | Robbery (street), Murder/shootings (salience), Drug crimes (open-air markets), Vandalism (visible disorder), Vehicle theft (parking) |
| Q3 | Will I collect the rent I underwrote? | Tenant pool income, inherited tenants without leases or deposits, voucher payment standards, eviction timeline and cost | Weak and indirect; the load-bearing inputs are not crime |
| Q4 | Will the city or state be my adversary? | Registration, inspection, lead and point-of-sale regimes; nuisance and disruptive-property ordinances; Good Cause; water liens | The address's own police calls and tenant conduct, which no block colour measures |
| Q5 | Can I get out, or refinance, at my number in year 2–3? | Buyer-pool depth, appraisal comps, lender and insurer appetite | Robbery and Murder colours and recent shootings shape buyer perception |
| Q6 | Is the block getting better or worse? | Vacancy, demolitions, investment, ownership churn, the 3–5-year incident trend | A trend in incident data, never a single colour |

Crime's direct channel into cash flow is second-order: longer vacancies, more turnover damage, and losses that fall inside an insurance vacancy exclusion. Its first-order channel is Q5. The studies that hold up find violent crime (robbery, aggravated assault, homicide) moves prices and household turnover and property crime mostly does not (Semenza et al. 2022 for robbery, burglary and homicide; Xie & McDowall 2010 for turnover; Ellen, Horn & Reed 2019 for in-migration after violent-crime declines). Kallberg & Shimizu's results are mixed and should not be cited for a low-price effect.

## 2. What a block colour can carry

From `validation/README.md` (Robbery, 2024–25):

| | Philadelphia (341 block groups) | Cleveland (577) |
|---|---|---|
| Spearman, colour vs. recorded robbery rate | 0.47 | 0.66 |
| Year-to-year Spearman of the recorded counts themselves (the noise floor) | 0.67 | 0.71 |
| Colour vs. one recorded year | 0.39–0.46 | 0.60–0.62 |
| Share of block groups coloured F | 33% | 49% |
| F block groups with a rate below the city median | 32% | 23% |
| F block groups with no robbery in two years | 17% | 13% |
| Top-fifth block groups by recorded rate coloured D- or F | 93% | 97% |
| Spearman inside the F band | 0.22 | 0.36 |

Four consequences:

1. A colour is worth about one year of police data. It cannot beat the noise in a two-year count of a few robberies per block group, and in Cleveland it nearly reaches that ceiling.
2. Letters saturate. Half of Cleveland's block groups are F; the letter separates little there. The continuous position (0 = A+, 1 = F) still orders blocks inside F, weakly.
3. About one F block in four is below its city's median rate. F is a band with a wide interior, not a verdict.
4. Robbery, assault, burglary, theft, vehicle theft and vandalism rank block groups almost identically (Spearman 0.75–0.89 in Cleveland). At this scale they are one signal. Six screenshots of them are one screenshot six times.

## 3. Type by type at block level

Definitions are CrimeGrade's (Assault is aggravated assault; Theft excludes vehicle theft; Arson includes vehicles; Drug crimes are possession, distribution, manufacture and trafficking; Murder excludes attempts). Location shares are NIBRS 2019 (FBI, offences by location). Block-group statistics are Cleveland, 505 city block groups with 150+ residents, 2024 to Nov 2025 annualised; "y2y" is the Spearman between 2023 and 2024 block-group counts.

| Type | Where it happens (NIBRS 2019) | Block-group behaviour (Cleveland) | Question served | Verdict at block level |
|---|---|---|---|---|
| Robbery | 27% street, 20% residence, 12% parking lot, 28% commercial premises (FBI 2023: one third on streets) | 2.8 per block group per year; 24% of block groups had none in 1.9 yrs; y2y 0.71; colour validated 0.47–0.66 | Q2, Q5 | Keep. The best single street-danger colour. Read the position, not the letter. |
| Assault (aggravated) | 60% of all NIBRS assault offences at a residence, 12% street; 79.6% of domestic-relationship violent incidents at a residence vs 41.1% non-domestic (FBI 2020–24) | Felonious assault 4.7/yr; 18% zero; y2y 0.78; 0.81 with robbery | Q4 (police calls at the building), Q3 (turnover) | Redundant with Robbery for ranking; as a colour it is partly a map of household violence, not street risk. Drop the map; use the address's own call history instead. |
| Burglary | 68% residence | 6.3/yr; 20% zero; y2y 0.79; 0.77 with robbery | Q1 | Keep as the vacancy-window risk colour. Building facts (rear access, alley, boarded neighbours, time to re-let) dominate it. |
| Vandalism | 47% residence, 13% street, 13% parking | 16.6/yr; 16% zero; y2y 0.86; 0.87 with theft | Q1, Q2 | Keep as the visible-disorder colour. The most stable block signal after simple assault. |
| Theft | 33% residence, 13% department store, 12% parking, 7% street, 6% grocery, 4% convenience store; about a third at retail premises | 17.5/yr; 15% zero; y2y 0.87 | Q1 (weak) | Drop. Block colours follow shops (shoplifting) and parking lots; the residential theft that costs a landlord (packages, yard items, catalytic converters) is address-specific and not on the map. |
| Vehicle theft | 39% residence, 22% parking, 20% street | 7.6/yr; 18% zero; y2y 0.78 | Q2 (parking amenity) | Optional, only where tenants park on the street. Distorted by the 2022–24 Kia/Hyundai wave (Cleveland thefts doubled 2022→23, 55% Kia/Hyundai; Q1 2024 474 vs Q1 2023 1,058; US MVT −18.6% in 2024), which the 6–12-month data lag can still carry. |
| Drug crimes | 53% street, 16% residence, 9% parking; counts are arrests, not victim reports | 1.5/yr; 27% zero; top 10% of block groups hold 41%; y2y 0.42 | Q4, Q2 | Flag only. A D-/F says "police made drug arrests here in the data window"; it tracks enforcement priority and drug law as much as dealing (arrests fall ~85% after cannabis legalisation: OH Dec 2023, VA and NY 2021, MD 2023; PA and WV medical only; NC not legal). Verify an open-air market with incident points and visits at different hours. |
| Arson | 51% residence, 12% street, 6% parking, 5% field/woods | 0.37/yr; 60% zero; top 10% hold 45%; y2y 0.18 | Q1 | Useless as a gradient; it does not repeat year to year. Replace with a count of vacant or condemned structures within ~30 m and the address's fire history. |
| Murder | 50% residence, 26% street, 8% parking | 0.21/yr; 71% zero; top 10% hold 51%; y2y 0.43 | Q2, Q5 | Flag only. Replace with shootings within 250 m over 3 years (Gun Violence Archive is address-level and national; about 5% of street segments carry ~74% of shootings, Braga et al.). One shooting on the block dominates tenant and buyer perception for years. |
| Rape, Kidnapping, Identity theft, Animal cruelty | Rape and animal cruelty mostly at residences (animal cruelty 69%); identity theft has no location; kidnapping is mostly custodial or domestic | Rape 0.9/yr, 39% zero, y2y 0.32 | none | Not applicable to any of the seven questions. |

On the less-discussed types, in one line each: Theft is a map of where shops are; Arson is a map of last year's accidents; Murder is a map of one or two events; Drug crimes is a map of where police chose to make arrests. Only Robbery, Burglary and Vandalism behave like gradients at block scale, and they largely agree with each other.

## 4. Unknown unknowns that are load-bearing

1. The colour ends before you buy. CrimeGrade's data lags 6–12 months, and a two-year hold starts after that. Incident portals (below) are current to the week.

2. Boundary effects. Block-group lines often run down the middle of a street. 40 Robinson St, Binghamton reads A+ (0.06) with D- across the street. For any address within ~100 m of a boundary, read the neighbouring block groups too; the pipeline already reads every polygon in view.

3. Commercial-parcel inflation. A block group holding a gas station or a shopping strip inherits store robberies (28% of robberies are at commercial premises), shoplifting (about a third of thefts) and street drug arrests. The residential street behind it is not that colour.

4. Incident location is not tenant exposure. Six in ten assaults and one in five robberies happen inside residences; eight in ten domestic-relationship violent incidents do. The assault colour of a block is largely what happens inside its households. Street exposure is better indexed by robbery position plus shootings.

5. Modelled colours where nobody reported. CrimeGrade fills reporting gaps with "AI-assisted modelling" from demographics, socioeconomics, geography and neighbours. Pennsylvania's NIBRS transition left most of its agencies out of the 2022 national file and about one in nine still missing in 2024. For Johnstown, McKees Rocks, McKeesport, Charleroi, New Castle and Scranton, check the agency's participation on the FBI Crime Data Explorer before trusting a colour; where the agency did not report, the colour is a demographic estimate.

6. Enforcement artifacts. Drug colours move with drug law (item on Drug crimes above). Vehicle-theft colours still carry the Kia/Hyundai wave. Catalytic-converter thefts fell 68% in 2024. A D on either can describe a wave that has passed.

7. Zero-population block groups. Industrial, park and campus block groups get extreme colours from tiny denominators (CrimeGrade's own "zero population effect"). The validation dropped block groups under 150 residents; the address pipeline should flag any address whose block group has under ~300.

8. The crime that costs the landlord is at the address, not on the block. Nuisance and disruptive-property ordinances count police calls or citations at the building and bill or prosecute the owner. In this campaign's cities:

   | City | Rule | Threshold | Consequence |
   |---|---|---|---|
   | Cleveland | Criminal-activity nuisance ordinance, strengthened April 2025 | 3 calls with probable cause in 12 months → warning letter, 14 days to submit a plan; 4th → nuisance declaration; 7 → higher tier. Expanded to drug offences, vehicle noise, street racing | $100/day, then $250, then $1,000; city bills enforcement costs; unpaid fines become a county lien. 14 declarations in the first seven months |
   | Johnstown | Ch. 692 Disruptive Properties | 3 arrests, citations or summonses for listed offences (public order, weapons, drugs, property, animals, rubbish) on the property within any 60 days; each rental unit counts separately | Cost of police response charged to the owner; misdemeanour if unabated; 12 clean months to declassify; tenants already being evicted do not count |
   | Scranton | Ch. 373-4H (2023) | Tenant "routinely engages" = 3 violations in 60 days or 9 in 12 months (disorderly conduct, noise, drug distribution) | Landlord must use all legal means to evict; rental licence can be revoked for 3 chapter violations in 12 months; licence $45/unit, inspection $50/unit every 3 years; victim-call exemption |
   | Pittsburgh | Ch. 670 Disruptive Property Abatement | Repeated violations at the property | Police, EMS and fire costs charged to the owner; green sign on the door; appeals board |
   | Binghamton | Ch. 315 Property and Building Nuisance Reform | 12 points in 6 months or 18 in 12 months (e.g., loitering 2 points) | Warning, then closure proceedings; no points for calls by victims of domestic violence or crime |
   | Huntington | Art. 1110 Chronic Nuisance Property | 3 nuisance activities in 30 days; 2 felonies in a year | 30 days to evict; $100–500/day; landlord can be charged |
   | Toledo | 541.18 (nuisance parties) | 3 party violations within 12 months of first notice | $150 civil fine; notice filed in the rental file |
   | Virginia cities | Va. Code 15.2-907 criminal blight | Drug or prostitution activity at the property | Owner deemed compliant if in good faith evicting the tenant; otherwise corrective action and a lien |
   | Statewide | OH 3767 (drug nuisance, closure up to a year), PA Act 1990-92 (250.505-A, 10-day drug notice), NY RPAPL 715, NC G.S. 19; victim protections PA Act 200 of 2014 and NY's 2019 law; Ohio has none | | |

   Nothing on a CrimeGrade map measures this. The question to add is: how many police calls did this address generate in the last 24 months, and were any tenant citations or arrests among them? That is a public-records request to the police department, and for Cleveland partly readable from the incident dataset by address.

9. Insurance is rated by territory, not block. A landlord policy's premium moves with ZIP-level territory and the property's claims, not the block colour. Two things do bite: the property's own CLUE report (LexisNexis, 7 years of claims; the seller can order it) shows past theft, vandalism and fire claims at the address; and the vacancy clause (30–60 days) excludes vandalism, theft and glass breakage — exactly the perils a burglary/vandalism colour predicts during a turnover longer than the clause.

10. Fire comes from the neighbour. Arson at block level is noise, but fire risk to the building is real where vacant structures adjoin it: about 43% of vacant-building fires are intentional, vacant buildings account for a quarter of intentional structure fires, and roughly one in ten vacant residential fires extends to an adjacent property (USFA). Count vacant or condemned structures within 30 m from the city's condemned list and Street View.

11. Voucher rent ceilings follow the ZIP in some metros. Small Area FMRs (payment standards by ZIP) are mandatory in Cleveland-Elyria, Akron, Dayton-Kettering, Pittsburgh, Philadelphia, Virginia Beach–Norfolk–Newport News, Raleigh, Charlotte, Winston-Salem and Greensboro–High Point. They are not mandatory in Toledo, Canton, Steubenville, Scranton, Johnstown, New Castle, Binghamton, Elmira, Corning, Roanoke, Lynchburg, Richmond–Petersburg, Danville, Durham, Fayetteville, Rocky Mount, Wilson, Huntington, Parkersburg or Cumberland. In the first group a cheap ZIP (where F blocks cluster) gets a low payment standard, capping voucher rent; in the second, the metro-wide FMR applies, so voucher rent in a cheap block can exceed market rent, which is why voucher demand there is insensitive to crime. Check the PHA's payment standard for the ZIP against the pro forma rent.

12. Unauthorised occupants after a break-in. Pennsylvania Act 88 of 2024 (squatter is not a tenant; ejectment, expedited in Philadelphia); North Carolina S.L. 2025-88 (expedited removal, effective 1 Dec 2025); West Virginia HB 4940 (criminal trespass); New York's 2024 budget (squatters excluded from "tenant", court process still required); Ohio's HB 478/480 and SB 241 were introduced in 2024 and I could not confirm enactment; Virginia and Maryland unchanged as far as I found. A burglary-prone block plus a long vacancy makes this regime matter.

13. Address-level incident data exists for most of the campaign, and it beats the colour. Cleveland (Division of Police feature service, 2016–present, block-group ID and public address), Philadelphia (OpenDataPhilly incidents, 2006–present, block address), Fayetteville NC (data.fayettevillenc.gov), Toledo (Police Transparency Hub and public crime map), Akron (APD Crime Search and report lookup by location), Dayton (Transparency Portal), Newport News (crime data CSV), Danville (LexisNexis Community Crime Map, synced to the records system), Roanoke City (Crime Mapping page; partial incident types, police caution against reading it as area safety; county portal 30 days only), Wilson (Crime Analysis page), Rocky Mount (statistics page; CrimeMapping.com), Pittsburgh (WPRDC blotter, city police only). Binghamton, Elmira, Johnson City, Corning, Johnstown, Scranton, New Castle, Charleroi, McKees Rocks, McKeesport, Huntington, Parkersburg, Cumberland, Portsmouth, Petersburg, Suffolk, Lynchburg and Franklin: SpotCrime or CrimeMapping.com for recent months, records request for the 24-month history.

14. Who will service the address. Property managers, insurers and DSCR lenders each keep unpublished no-go lists by street. Three phone calls ("will you manage 3446 E 125th?") answer Q2 and Q5 faster than any map.

15. Non-crime items that dominate a two-year result and are easy to miss: reassessment to the sale price (Ohio school boards can contest value where the sale exceeds it by both 10% and $500,000 under HB 126; Philadelphia's periodic reassessments); water and sewer in the owner's name with lien rights (Cleveland, Philadelphia); Cleveland Residents First (registration, local agent for out-of-area owners, lead-safe certificate for pre-1978, rental certificate of occupancy); Philadelphia's rental licence, certificate of rental suitability, lead certificate, BIRT/NPT, mandatory 30-day Eviction Diversion and roughly six-month evictions; Binghamton's Good Cause opt-in (owner-occupied under 11 units exempt) and Broome lead registry; Virginia rental-inspection districts (Roanoke, Newport News from 1 Jan 2026, Portsmouth, Danville); NC's bar on registration and periodic inspections (G.S. 160D-1207); WV municipal B&O tax on gross rents; eviction all-in cost around $3,500 legal and $7,700 with lost rent and damage; turnover $1,000–2,500 per unit for a small landlord.

## 5. Protocol for the campaign

Maps to collect per address, read as positions (0–1), not letters:
- Robbery (keep; primary street-danger signal).
- Burglary (vacancy-window risk).
- Vandalism (visible disorder; most stable).
- Drug crimes and Murder as binary flags (D- or F → verify with incident points; never as a gradient).
- Skip Assault (redundant with Robbery, residence-dominated), Theft (retail-driven), Vehicle theft (unless street parking; wave-distorted), Arson (noise), Rape, Kidnapping, Identity theft, Animal cruelty.

Address-level checks that the maps cannot do:
1. Incident points within 150 m for 24 months by type (portal or records request), and any incident at the address itself.
2. Police calls for service at the address, 24 months (records request) → nuisance-ordinance exposure.
3. Shootings within 250 m over 3 years (Gun Violence Archive; local shooting datasets where they exist).
4. Vacant or condemned structures within 30 m (city list, Street View, drive-by).
5. CLUE report for the address (via the seller).
6. Insurance quote naming the address, with the vacancy clause and theft sublimit in writing.
7. PHA payment standard for the ZIP vs. pro forma rent (SAFMR metros).
8. Local ordinance check: registration/inspection, nuisance thresholds, lead, Good Cause, utility liens.
9. Three property managers asked whether they will take the address.
10. Block-group population (flag under ~300) and distance to the nearest block-group boundary (flag under ~100 m; read neighbours).

For file 14 (when that bridge is crossed): the single `crime` letter would be replaced by robbery, burglary and vandalism positions, a murder flag, a drug flag, and the 24-month call count at the address; the first three carry the block, the last three carry the building.

## Sources

Validation and data: `validation/README.md`; Cleveland Division of Police Crime_Incidents (ArcGIS FeatureServer); OpenDataPhilly `incidents_part1_part2` (Carto SQL); TIGERweb Census 2020 block groups. NIBRS 2019 offences by location (FBI CDE downloads: crimes against persons, property, society). FBI, "UCR Summary of Crime in the Nation, 2023" (robbery locations). FBI, domestic-relationship violent crime 2020–2024 (79.6% vs 41.1% at residences). CrimeGrade About/methodology page. Cleveland nuisance ordinance: Ideastream 21 Apr 2025 and 28 Jan 2026; Signal Cleveland. Johnstown Codified Ordinances 692.02 (American Legal). Scranton Ch. 373 (ecode360). Toledo 541.18 (American Legal). Pittsburgh Ch. 670 (ecode360; pittsburghpa.gov). Binghamton Ch. 315 (binghamton-ny.gov). Huntington Art. 1110 (elaws) and WSAZ reports. Va. Code 15.2-907. NHLP/PRRAC "What are Small Area FMRs?" (mandatory areas 2018 and 2024); Affordable Housing Finance, 25 Oct 2023. PA Act 88 of 2024 (pa.gov; Dornish & Morrison). NC S.L. 2025-88 (Skyline). WV HB 4940 and the 11-state tally (Cloudastructure). Ohio HB 478/480, SB 241 (Ohio Capital Journal; Community Legal Aid). Fayetteville open data (data.fayettevillenc.gov; Esri ArcNews 2016). Toledo Police Transparency Hub; Akron APD Crime Search; Dayton Transparency Portal; Newport News Crime Data; Danville news release (Community Crime Map); Roanoke Crime Mapping; Wilson Crime Analysis; SpotCrime city pages. Semenza et al. 2022; Xie & McDowall 2010; Ellen, Horn & Reed 2019; Braga et al. (shootings on 5% of segments); USFA vacant-building fire reports; FBI 2024 crime summary (MVT −18.6%).
