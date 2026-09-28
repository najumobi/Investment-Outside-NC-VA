# Out-of-region assessment: which states clear the distance penalty

Revision 2, written 2026-09-28 against the area-projection outputs of 2026-09-25/26 (revision 1: 2026-09-27). Sections 3–7 are now step-by-step walkthroughs; sections 1, 2, 8, 9 and 10 were amended where the walkthroughs needed it. Every figure traces to one of two companion files in this repository:

- `area_projection_189_areas_volume_distance_2026-09-27.csv` — one row per area (caliber, volume, drive time, tier, leads per quarter).
- `redfin_2to4_unit_sales_by_county_189_areas_2026-05.csv` — new in revision 2: one row per county named in the projection's rule strings (681 rows), with the 9-26 rule, whether the rule keeps the county, and Redfin's 2–4-unit sales and median price for the twelve months to 2026-05-31.

Corrections to revision 1 are marked **[corrected]**. New findings are marked **[new]**.

## 0. The one-paragraph answer

Pennsylvania and Ohio are the only states whose prospects survive an honest distance penalty, and they do so by volume, not by hit rate: after the penalty each still delivers two to three times the expected verified-lead flow of the whole NC/VA home region (PA ≈ 35 leads/quarter, OH ≈ 27, home 11.6). West Virginia has the best hit rates in the country and almost no duplex sales; it is the western legs of a Pittsburgh loop, not a target. Every other state, the fifteen micropolitan "still likely lead" areas included, fails on volume × distance. Two things revision 2 adds: Ohio's tax edge is now on a statutory clock — HB 186 (136th GA) phases the 10% rollback off rental housing over 2026–2029 while raising the owner-occupancy credit to 15.38%, a ~5–12% bias against rentals the projection cannot see **[new]**; and Philadelphia County's $100,000 Homestead Exemption is the largest hidden cost in the Tier-A set, $1,400 a year that only owner-occupants get **[new]**. Neither changes the ranking. The penalty as coded (a flat −2 score points beyond 1.25 h from Williamsburg) is not the binding constraint; 74% of the current board already pays it.

---

## 1. What the projection measures, and what it does not

### 1.1 The method (from `project_areas.py`, `lead25.py`, `estimators_all.py`, `leaders_w2.py`)

1. Take every NC/VA listing the campaign sifted that carries a price, a rent-to-price figure and a county. The pipeline says 692; my rebuild from files 06c, 13a, the round 4–14 sweep files and the two weekly `scored.csv` runs finds 698.
2. Express each listing as a ratio to its home county's price level and rent-to-price level.
3. Re-price it into each target county at that county's levels under three price bases: **A** (ACS 2020-24 only), **Z** (Zillow ZHVI level, ACS rent moved by ZORI growth), **R** (Zillow level × Redfin's county duplex premium, shrunk toward the national ratio with k = 20).
4. Test the two money gates: price ≤ $532,643 (hard ceiling) and rent-to-price ≥ 0.9% plus a cost shift for the target county's tax rate and state insurance versus the listing's home county (`shift = 100 × Δ$/yr ÷ (8.4 × price)`).
5. Target pass share ÷ NC/VA pass share = factor applied to the stated NC/VA rate of 1 in 14. Non-money gates are assumed to pass at the NC/VA rate everywhere.
6. County rules first remove counties the campaign would not search: student market (≥ 25% enrolled; 15–25% drops campus-radius ZIPs), resort market (≥ 14% seasonal units), post-disaster (FEMA large awards ≥ 0.03 per home since 2023), price screen (CLOSED counties out; ELIMINATED/LIKELY ELIMINATED kept only under a ZIP-level cap when feasible sales ≥ 2/quarter; < 60 two-to-four-unit structures = no stock).
7. Worst case = minimum across the three price bases, three dispersion settings (×0.8/1.0/1.25), cost penalties only (no credits), non-money gates 1.35× harder, and three rule readings (strict / lenient / harsh).
8. Crediting: plain (every money-passer counts), 3-band (< 1.2% → 35.5/96; 1.2–1.8% → 24.5/54; ≥ 1.8% → 0.5/33), 2-band (< 1.8% → 59.5/149; ≥ 1.8% → 0.5/33). The final files use 2-band.
9. Verdict tiers (`lead25.py`): high-confidence lead = worst case better than 1 in 7; likely lead = both centrals better than 1 in 7 or worst case (before the 1.35× stress) better than 1 in 8.4; otherwise no confident call. Result on 2026-09-26: 30 likely leads, 159 no confident call, 0 high confidence. Re-weighted with 2-band survival: 15 of 30 still likely.

### 1.2 Three structural consequences

- **It measures caliber per listing, not flow.** A 1-in-6.5 area with six duplex sales a year and a 1-in-12 area with 2,400 are incommensurable until multiplied by volume. None of the eight projection files carries volume. That multiplication is the substance of sections 3–4.
- **Survival weighting is the decisive refinement.** NC/VA money-passers at 1.8%+ rent-to-price reached the live list 0.5 times in 33: shells, package sales and mis-listed units. `survival_driver.py` tested absolute vs county-relative yield as the predictor (logistic fits, leave-one-county-out, a transfer test from pricier to cheaper counties) and found absolute bands transfer better. This is what demotes the cheap Sun Belt micros between the unweighted and the weighted columns.
- **1 in 14 is slightly ambiguous, and it does not matter for the ranking.** The rebuild gives 181 money-passers of 698 (25.9%), survival-weighted 60.0; `lead25_surv.py` says the funnel is "59 of 692" to the live list, 1 in 11.7. Every target area's leads-per-quarter and the home region's 11.6 are both proportional to the same NC/VA baseline, so the multiple of any area over home is identical under either reading; only the absolute counts move (×1.2 under 1 in 11.7). 1 in 14 is carried as stated.

### 1.3 Baseline distribution and the erosion table (rebuilt, 698 listings)

Money-passers by band: < 1.2% 96, 1.2–1.8% 53, ≥ 1.8% 32. Median price of all listings $339,900; of passers $190,000; median passer rent-to-price 1.17%. 104 passers at or under $200K, 53 at or under $150K.

How the erosion table is built (it is the conversion used for distance, management, tax and insurance in §3 and §5):

1. Sort the 698 listings by rent-to-price.
2. For each bar from 0.90% upward in 0.01 steps, count listings at or above the bar (plain) and sum their survival weights (2-band: 59.5/149 below 1.8%, 0.5/33 at or above).
3. Divide by the 0.90% figures (181 plain, 60.0 weighted). The quotient is the hit-rate factor for a bar that high.

| Bar | Plain survivors ÷ 0.90 count | Survival-weighted ÷ 0.90 count |
|---|---|---|
| 0.90% | 1.000 | 1.000 |
| 0.91% | 0.972 | 0.969 |
| 0.92% | 0.950 | 0.945 |
| 0.93% | 0.890 | 0.877 |
| 0.94% | 0.851 | 0.834 |
| 0.95% | 0.823 | 0.803 |
| 0.96% | 0.807 | 0.784 |
| 0.97% | 0.801 | 0.778 |
| 0.98% | 0.785 | 0.760 |
| 0.99% | 0.757 | 0.729 |
| 1.00% | 0.746 | 0.717 |
| 1.01% | 0.729 | 0.698 |
| 1.02% | 0.729 | 0.698 |
| 1.03% | 0.702 | 0.667 |
| 1.04% | 0.691 | 0.655 |
| 1.05% | 0.680 | 0.643 |
| 1.06% | 0.669 | 0.630 |
| 1.07% | 0.663 | 0.624 |
| 1.08% | 0.652 | 0.612 |
| 1.09% | 0.630 | 0.587 |
| 1.10% | 0.613 | 0.569 |
| 1.11% | 0.597 | 0.550 |
| 1.12% | 0.580 | 0.532 |
| 1.13% | 0.564 | 0.513 |
| 1.14% | 0.558 | 0.507 |
| 1.15% | 0.536 | 0.483 |
| 1.16% | 0.530 | 0.476 |
| 1.17% | 0.514 | 0.458 |
| 1.18% | 0.497 | 0.439 |
| 1.19% | 0.492 | 0.433 |
| 1.20% | 0.470 | 0.409 |
| 1.21% | 0.464 | 0.401 |
| 1.22% | 0.453 | 0.386 |
| 1.23% | 0.442 | 0.371 |
| 1.24% | 0.425 | 0.348 |
| 1.25% | 0.420 | 0.341 |
| 1.26% | 0.409 | 0.326 |
| 1.27% | 0.398 | 0.310 |
| 1.28% | 0.387 | 0.295 |
| 1.29% | 0.370 | 0.273 |
| 1.30% | 0.365 | 0.265 |
| 1.35% | 0.348 | 0.242 |
| 1.40% | 0.304 | 0.182 |


Two properties matter: the first 0.05 pts cost 20% of the hit rate (0.90 → 0.95 = ×0.80), and the curve flattens between 0.96 and 1.02 (a plateau of passers priced at 1.0–1.1%), then falls again. A cost that pushes the bar past 1.10% halves the flow.

---

## 2. The distance penalty as it exists

Source: `weekly_sweep.py` line 190 and `round9_final.py` line 73 (`if drive and drive > 1.25: pen += 2`); README line 33 (score = cash-on-cash at 6.75% minus YELLOW −4, CrimeGrade F −3 / D− −2 / D −1 / D+ −0.5, drive over 1.25 h from Williamsburg −2, historic −1, flood factor 5+ −1, DSCR under 1.2 −2). Drive hours live in `constants.json` → `drive_wb` (54 cities, Google-derived).

Properties of the penalty:

1. **Binary.** Petersburg at 1.3 h and Pennington Gap at 6.7 h pay the same −2. Nothing scales beyond the threshold.
2. **Williamsburg-only.** File 14 carries `drive_ec` (Elizabeth City) on 45 of 61 rows; no script reads it. Fayetteville is 4.2 h / 3.7 h, Rocky Mount 2.4 / 2.0, Wilson 2.7 / 2.2; Florence SC, Columbia, Augusta and Savannah are 0.5 h closer from Elizabeth City. The model does not know.
3. **Already the norm.** 45 of 61 board rows (74%) exceed 1.25 h; 4 of the top 10 scores do, including #1 (118 & 120 S Poplar, Winston-Salem, 4.6 h, score 10.5) and #2 (1114 Lafayette, Roanoke, 3.8 h, 10.0). File 11's rule is that anything outside the radius is "Tier 2 with a property manager"; file 10 found only 4 of 40 candidates depend on self-management. The campaign is already a Tier-2 campaign confined to two states.
4. **Not a hit-rate effect.** The −2 reorders; it never removes. Inside the model an Ohio duplex "makes up for" the penalty as soon as its cash-on-cash is two points above a Roanoke duplex's, which cheap Rust Belt stock does trivially. The literal answer to "does any state make up for the penalty as assessed" is therefore "all of them", and that is a defect of the assessment, not a finding about geography.

---

## 3. The distance penalty re-specified as a cost — walkthrough

### 3.1 Step 1: put the penalty in the unit the pipeline already uses

The pipeline's Gate 5 is a rent-to-price bar (0.90%). Its own cost-shift rule converts any annual cost into a bar shift:

`shift (pts) = 100 × Δ$/yr ÷ (8.4 × price)`

where 8.4 = 12 months × 0.70 (a dollar of annual cost needs $1/0.70 of annual rent because ~30% of gross rent is variable expense). Worked: $840/yr on a $100,000 property → 100 × 840 ÷ 840,000 = +0.10 pts → the bar becomes 1.00%.

Why this and not the −2 score: a bar shift removes listings (it changes the hit rate); a score point reorders survivors. Distance creates real annual dollars, so it belongs in the bar.

### 3.2 Step 2: price the dollars distance actually creates

Inputs: campaign file 30 (management fee survey: 8–12% of collected rent, $100/unit monthly floors, one placement fee per two years), file 11 (Tier 2 = managed), file 10 (4 of 40 candidates depend on self-management), median passer price $190,000 (§1.3), typical sub-$200K duplex gross rent $1,600–2,300/mo, ORF fares (assumption: $350 round trip + $200 car/lodging per visit = $700/visit), Charlotte day trip as the in-region reference (5.0 h Google).

0

Reading the table: the management rows apply to any managed property, in-region Tier 2 included, so they are not marginal to leaving the two states. The travel rows are marginal. The remote-market management premium (12% instead of the modeled 8%) is marginal only where the market is too far for Najum to interview managers in person and switch cheaply — the fly-in case.

### 3.3 Step 3: assemble the tiers from marginal items

| Tier | Definition (OSRM hours from Williamsburg) | Marginal items | Shift | Bar | Factor (weighted) | Factor used |
|---|---|---|---|---|---|---|
| A — drive | ≤ 6.5 h (≈ ≤ 5.5 h Google; Charlotte-equivalent) | none beyond existing Tier 2 | 0 | 0.90% | 1.000 | ×1.00 |
| B — long drive / short hop | 6.5–9.5 h | long-drive increment ($600/yr) | +0.048 | 0.948% | 0.809 | ×0.80 |
| C — fly-in | > 9.5 h | two fly-ins + remote management premium | +0.144 to +0.180 | 1.044–1.080% | 0.650–0.612 | ×0.62 |
| C harsh | > 9.5 h, year 1 | three visits + premium + minimum-fee residual | +0.25 | 1.15% | 0.483 | ×0.50 |

**[corrected]** Revision 1 listed Tier C's shift as "+0.08 to +0.11" (travel alone) next to a ×0.62 factor that actually corresponds to +0.18; the table above shows the full composition. The factor is unchanged.

Calibration of the cut-offs: OSRM routes run slower than the campaign's Google constants (Roanoke 4.5 vs 3.8 h = 1.18×; Fayetteville 4.6 vs 4.2 = 1.10×; Charlotte 6.2 vs 5.0 = 1.24×), so 6.5 h OSRM ≈ 5.2–5.9 h Google and 9.5 h OSRM ≈ 7.7–8.6 h Google. Tier A therefore ends where the campaign's own Charlotte day trip ends.

### 3.4 Step 4: break-even caliber per tier

An out-of-region area matches the home region's 1-in-14 per listing when its central 1-in-N × tier factor is at least as good: N ≤ 14 × factor.

| Tier | Factor | Break-even central 1-in | Areas clearing it |
|---|---|---|---|
| A | 1.00 | 14.0 | 11/11 (under the rebuilt 1-in-11.7 reading: 8 of 11) |
| B | 0.80 | 11.2 | 16/22 |
| C | 0.62 | 8.7 | 57/156 |
| C harsh | 0.50 | 7.0 | 11 of 156 |

**[corrected]** Revision 1 said "8 of 11 Tier-A areas" clear; that count used the Tier-B bar (11.2) by mistake. At the Tier-A bar all 11 clear; 8 clear the stricter 11.7.

Tier A, every area (bar 14.0):

| Area | 2-band central 1-in | Worst 1-in | OSRM h | 2–4-unit sales/yr | Leads/q central | Leads/q after penalty | Clears 14.0 |
|---|---|---|---|---|---|---|---|
| Beckley, WV MSA | 6.5 | 10.7 | 5.6 | 6 | 0.13 | 0.13 | yes |
| Bluefield, WV-VA μSA (but excluding Virginia areas: Tazewell county) | 6.7 | 10.9 | 6.2 | 1 | 0.02 | 0.02 | yes |
| Elkins, WV μSA | 7.1 | 12.6 | 6.5 | 2 | 0.04 | 0.04 | yes |
| Johnstown–Somerset, PA CSA | 7.6 | 12.2 | 6.5 | 83 | 1.52 | 1.52 | yes |
| Florence, SC MSA | 8.0 | 13.6 | 6.2 | 12 | 0.19 | 0.19 | yes |
| Salisbury–Ocean Pines, MD CSA | 8.7 | 14.5 | 4.0 | 0 | 0.00 | 0.00 | yes |
| Altoona–Huntingdon, PA CSA | 8.7 | 14.6 | 6.5 | 37 | 0.59 | 0.59 | yes |
| Cumberland, MD-WV μSA | 9.0 | 16.8 | 5.1 | 59 | 0.88 | 0.88 | yes |
| Philadelphia–Reading–Camden, PA-NJ-DE-MD CSA | 12.1 | 21.5 | 5.9 | 1450 | 16.43 | 16.43 | yes |
| Morgantown, WV MSA | 12.7 | 61.7 | 6.5 | 46 | 0.51 | 0.51 | yes |
| Washington–Baltimore–Arlington, DC-MD-VA-WV-PA CSA (but excluding Virginia areas) | 13.4 | 33.1 | 3.9 | 585 | 5.84 | 5.84 | yes |


Tier B, every area (bar 11.2):

| Area | 2-band central 1-in | Worst 1-in | OSRM h | 2–4-unit sales/yr | Leads/q central | Leads/q after penalty | Clears 11.2 |
|---|---|---|---|---|---|---|---|
| Fairmont–Clarksburg, WV CSA | 6.6 | 13.3 | 6.8 | 22 | 0.47 | 0.38 | yes |
| Wheeling, WV-OH MSA | 6.6 | 15.8 | 8.1 | 36 | 0.80 | 0.64 | yes |
| Oil City, PA μSA | 6.7 | 10.6 | 9.0 | 19 | 0.39 | 0.32 | yes |
| Charleston–Huntington–Ashland, WV-OH-KY CSA | 6.8 | 11.4 | 6.8 | 77 | 1.53 | 1.23 | yes |
| Bradford, PA μSA | 7.0 | 10.9 | 9.5 | 10 | 0.20 | 0.16 | yes |
| Pottsville, PA μSA | 7.3 | 12.4 | 7.0 | 89 | 1.70 | 1.36 | yes |
| Augusta-Richmond County, GA-SC MSA | 8.2 | 12.4 | 8.9 | 34 | 0.54 | 0.43 | yes |
| Columbia–Sumter–Orangeburg, SC CSA | 8.4 | 13.1 | 7.6 | 17 | 0.25 | 0.20 | yes |
| St. Marys, PA μSA | 8.7 | 13.7 | 8.5 | 1 | 0.02 | 0.01 | yes |
| Middlesborough–Corbin, KY CSA | 9.0 | 12.6 | 8.5 | 11 | 0.14 | 0.11 | yes |
| Youngstown–Warren–Salem, OH CSA | 9.7 | 15.2 | 8.5 | 113 | 1.80 | 1.44 | yes |
| Parkersburg–Marietta–Vienna, WV-OH CSA | 9.8 | 17.1 | 8.2 | 21 | 0.31 | 0.25 | yes |
| Elmira–Corning, NY CSA | 9.9 | 13.8 | 9.0 | 126 | 2.18 | 1.74 | yes |
| Gallipolis, OH μSA | 10.2 | 15.5 | 8.5 | 7 | 0.11 | 0.08 | yes |
| Pittsburgh–Weirton–Steubenville, PA-OH-WV CSA | 10.6 | 20.0 | 7.5 | 970 | 12.75 | 10.20 | yes |
| Binghamton, NY MSA | 11.2 | 15.8 | 9.0 | 276 | 4.21 | 3.37 | yes |
| Sayre, PA μSA | 11.4 | 21.4 | 8.5 | 12 | 0.15 | 0.12 | no |
| Savannah–Hinesville–Statesboro, GA CSA | 12.5 | 36.8 | 9.3 | 138 | 1.46 | 1.17 | no |
| Somerset, KY μSA | 12.6 | 29.8 | 9.5 | 7 | 0.06 | 0.05 | no |
| State College–DuBois, PA CSA | 12.7 | 26.3 | 7.0 | 27 | 0.30 | 0.24 | no |
| Scranton–Wilkes-Barre, PA MSA | 12.8 | 24.8 | 7.8 | 836 | 9.08 | 7.27 | no |
| Bloomsburg–Berwick–Sunbury, PA CSA | 13.1 | 23.7 | 7.5 | 108 | 1.15 | 0.92 | no |


Tier C, the fifteen largest post-penalty flows among the 57/156 that clear 8.7:

| Area | Central 1-in | OSRM h (est. where flagged) | Sales/yr | Leads/q after ×0.62 |
|---|---|---|---|---|
| Memphis–Clarksdale–Forrest City, TN-MS-AR CSA | 8.6 | 16.0 (osrm) | 179 | 1.67 |
| Gulfport–Biloxi, MS MSA | 8.2 | 18.5 (est) | 78 | 0.84 |
| Macon-Bibb County–Warner Robins, GA CSA | 8.1 | 11.5 (osrm) | 74 | 0.75 |
| Carbondale–Marion–Herrin, IL CSA | 8.0 | 15.5 (est) | 59 | 0.74 |
| Shreveport–Bossier City–Minden, LA CSA | 7.8 | 19.5 (est) | 44 | 0.52 |
| Richmond–Connersville, IN CSA | 8.7 | 12.0 (est) | 45 | 0.50 |
| Clovis, NM μSA | 6.4 | 29.0 (est) | 36 | 0.46 |
| Jackson, TN MSA | 8.0 | 14.0 (est) | 40 | 0.40 |
| Burlington–Fort Madison, IA-IL CSA | 7.5 | 18.0 (est) | 32 | 0.40 |
| Jackson–Vicksburg–Brookhaven, MS CSA | 8.4 | 17.7 (osrm) | 35 | 0.37 |
| Lawton–Duncan, OK CSA | 7.5 | 23.5 (est) | 36 | 0.36 |
| Montgomery–Selma, AL CSA | 6.9 | 13.7 (osrm) | 29 | 0.35 |
| Lake Charles–DeRidder, LA CSA | 7.5 | 19.5 (est) | 25 | 0.31 |
| Terre Haute, IN MSA | 7.0 | 14.2 (osrm) | 22 | 0.31 |
| Mobile–Daphne–Fairhope, AL CSA | 7.1 | 16.0 (est) | 23 | 0.27 |


Caliber without volume is worth nothing (Beckley clears every bar with six sales a year), which is why §4 exists.

### 3.5 Step 5: measure distance the same way for every area

1. Origins: Williamsburg VA (37.2707, −76.7075) and Elizabeth City NC (36.2946, −76.2511).
2. Destination: the principal city of each area (the first name in the OMB title), coordinates from the campaign's `geo_cache.json` where present, else the Wikipedia city coordinate.
3. Route: `https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false`, take `routes[0].duration ÷ 3600`. 96 calls, all served; 49 areas routed, the other 140 carry a state/regional estimate flagged `est` in the workbook (the estimate is the routed time of the nearest routed city in the same state ± 0.5 h).
4. Tier by the Williamsburg figure (the campaign's convention); the Elizabeth City figure is reported so the model can be fixed (§7).

Routed hours (Williamsburg / Elizabeth City): Baltimore 3.9 / 5.7; Salisbury MD 4.0 / 4.0; Cumberland MD 5.1 / 6.9; Beckley 5.6 / 7.4; Philadelphia 5.9 / 7.0; Bluefield 6.2 / 7.5; Florence SC 6.2 / 5.7; Johnstown 6.5 / 8.2; Morgantown 6.5 / 8.3; Charleston WV 6.8 / 8.6; Fairmont 6.8 / 8.6; Columbia SC 7.6 / 7.1; Pittsburgh 7.5 / 9.3; Scranton 7.8 / 9.0; Huntington 7.8 / 9.6; Wheeling 8.1 / 9.8; Parkersburg 8.2 / 9.9; Youngstown 8.5 / 10.3; Augusta 8.9 / 8.4; Binghamton 9.0 / 10.2; Savannah 9.3 / 8.8; Erie 9.6 / 11.4; Cleveland 9.8 / 11.5; Dayton 10.5 / 12.3; Atlanta 10.8 / 10.9; Louisville 11.4 / 13.2; Toledo 11.5 / 13.2; Indianapolis 12.8 / 14.6; Lansing 13.6 / 15.4; Terre Haute 14.2 / 16.0; Memphis 16.0 / 17.2; St. Louis 16.1 / 17.9; Jackson MS 17.7; Little Rock 18.4; New Orleans 19.3; Tulsa 22.9; Oklahoma City 24.0; Wichita 24.2. Controls: Roanoke 4.5, Fayetteville 4.6, Charlotte 6.2.

Where the two origins disagree on the tier: Florence SC, Columbia, Augusta and Savannah are 0.5 h closer from Elizabeth City (Florence and Salisbury are Tier A from either); nothing in Pennsylvania or Ohio changes tier.

### 3.6 Step 6: air access (the Tier-C operating model)

Norfolk (ORF) nonstops, from norfolkairport.com/where-we-fly cross-checked against Wikipedia's ORF destinations table: daily to Philadelphia (American Eagle), Baltimore (Southwest), Washington National and Dulles, Atlanta, Charlotte, Chicago O'Hare and Midway, Detroit, Minneapolis, Nashville, Newark, Dallas, Houston, Denver; seasonal only to Pittsburgh, Akron/Canton and Columbus (Breeze) and St. Louis (Southwest); two-weekly New Orleans (Breeze). No nonstop to Cleveland, Indianapolis, Louisville, Cincinnati, Memphis, Birmingham, Little Rock, Oklahoma City, Tulsa or Wichita. Richmond's route list is an interactive map and was not retrieved.

Consequence for Ohio **[new]**: the daily ORF–Detroit nonstop puts Toledo 1 h and Cleveland 2.7 h from a daily gateway; Cleveland's year-round Tier-C cadence is ORF–DTW plus a rental car, not the seasonal Akron/Canton flight.

### 3.7 What distance does not degrade

The verification engine. Files 28–49 ran on CAMA cards, ArcGIS layers, Register of Deeds instruments, HUD workbooks, DEQ/EPA records, dated Street View and court portals; none requires presence. The true losses are (a) the photo-based condition grade cannot be checked by a drive-by, pushing a remote campaign toward GREEN-only stock; (b) each new jurisdiction costs the instrument-building that consumed about a day per NC town (`constants.json` holds `_instruments` blocks for Pinetops, Spring Lake, Rocky Mount, Oxford, Cherryville, Reidsville, Clayton and Durham); (c) lender friction is unchanged for the conventional two-unit investment loan Ogo is waiting on after 13 October 2026.

---

## 4. Volume — walkthrough

### 4.1 Step 1: get every county's 2–4-unit sales from one source

Source: Redfin's public county market tracker, `https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/county_market_tracker.tsv000.gz` (241 MB; Last-Modified 2026-06-02; latest period end 2026-05-31). Parse:

1. Filter `property_type == "Multi-Family (2-4 Unit)"`, `is_seasonally_adjusted == "f"`, `period_duration == 30`.
2. Keep the twelve `period_end` months 2025-06-30 … 2026-05-31.
3. Sum `homes_sold` per county → sales/yr; sales-weighted median of `median_sale_price` → the county's 2–4-unit price.
4. Key each county as `"<county name lower>|<ST>"` (3,043 counties have at least one row).

Cross-check: the same parse reproduces the pipeline's own `map_data.json` recorded-sales figures for NC and VA exactly (NC 644, VA 579). Redfin's classification is a floor, not a count: a rowhouse city like Philadelphia shows 336 sales.

### 4.2 Step 2: decide which counties the campaign would search

The projection's rule strings (LEAD-test files, column `county_rules`) name every county in every area with one rule each. Counts across the 189 areas: active 349, shallow 203, thin 52, post-disaster zone 20, resort/second-home market 12, no duplex stock 12, borderline, undecided 9, price screen 8, borderline kept under a price cap 6, kept under a ZIP-level price cap 5, student market 4, no data 1.

A county is **kept** when its rule begins `active`, `shallow`, `kept under a ZIP-level price cap` or `borderline kept under a price cap`; a campus-radius qualifier (`active (campus-radius ZIPs out)`) still keeps it. It is **dropped** when the rule is `thin (0 sales …)`, `post-disaster zone`, `resort/second-home market`, `no duplex stock`, `borderline, undecided`, `price screen: closed/eliminated`, `student market` or `no data`. Result: 681 named counties, 563 kept, 547 of those with a Redfin row. The 16 kept counties without a Redfin row (volume = 0 in every total, i.e. floors): Fairfield County (Columbia–Sumter–Orangeburg); Kershaw County (Columbia–Sumter–Orangeburg); Lexington County (Columbia–Sumter–Orangeburg); Richland County (Columbia–Sumter–Orangeburg); Russell County (Columbus–Auburn–Opelika); Chattahoochee County (Columbus–Auburn–Opelika); Harris County (Columbus–Auburn–Opelika); Muscogee County (Columbus–Auburn–Opelika); Nueces County (Corpus Christi–Kingsville–Alice); San Patricio County (Corpus Christi–Kingsville–Alice); Forrest County (Hattiesburg–Laurel); Jones County (Hattiesburg–Laurel); Lamar County (Hattiesburg–Laurel); Somerset County (Salisbury–Ocean Pines); Wicomico County (Salisbury–Ocean Pines); Huntingdon County (Altoona–Huntingdon).

Multi-state counties with the same name (Washington, Jefferson, Marion, Hancock, Lee, Macon …) are pinned to the right state by an override table; nothing was matched by guess.

### 4.3 Step 3: convert sales to feasible sales with the campaign's own ratio

The 696-county screen (`county_screen_consistent_rules_2026-09-25.csv`) already computed, per county, `feasible_sales_per_quarter` = the share of the duplex price distribution under the $532,643 ceiling and above the 0.83% break-even, applied to recorded sales. Summing feasible over recorded sales ÷ 4 across each state's `within` counties gives a state feasibility ratio:

| State | Feasible/q (screen) | Recorded sales/q (screen) | Ratio |
|---|---|---|---|
| AL | 19.0 | 35.8 | 0.53 |
| AR | 33.9 | 60.0 | 0.57 |
| GA | 26.8 | 50.8 | 0.53 |
| IA | 53.7 | 89.8 | 0.60 |
| IL | 126.8 | 195.8 | 0.65 |
| IN | 56.4 | 90.0 | 0.63 |
| KS | 94.1 | 171.5 | 0.55 |
| KY | 32.4 | 71.8 | 0.45 |
| LA | 27.0 | 45.0 | 0.60 |
| MI | 84.5 | 141.0 | 0.60 |
| MO | 32.0 | 74.5 | 0.43 |
| MS | 18.7 | 32.8 | 0.57 |
| NM | 1.1 | 2.5 | 0.45 |
| NY | 194.3 | 284.2 | 0.68 |
| OH | 79.1 | 128.0 | 0.62 |
| OK | 5.6 | 11.8 | 0.48 |
| PA | 207.3 | 372.8 | 0.56 |
| SC | 6.0 | 12.0 | 0.50 |
| TN | 12.9 | 25.0 | 0.52 |
| TX | 82.1 | 179.2 | 0.46 |
| WV | 22.7 | 40.2 | 0.56 |
| pooled (used where a state has no ratio) | 1584.8 | 2980.2 | 0.53 |


Feasible/q for an area = Σ over kept counties of (sales ÷ 4 × the county's state ratio). The ratio is state-level; §8 lists where that overstates (Philadelphia, Washington–Baltimore) and understates (Johnstown, Toledo, Elmira).

### 4.4 Step 4: expected verified leads per quarter

`leads/q = feasible/q ÷ N` where N is the 2-band survival-weighted central 1-in-N from the 09-26 LEAD test (`band_survival_weighted_central_1_in`), then × the tier factor from §3.3. Worked rows:

| Area | Sales/yr (kept counties) | Feasible/q (= Σ county sales ÷ 4 × state ratio) | 2-band central 1-in | Leads/q = feasible ÷ N | OSRM h → tier | Factor | Leads/q after penalty | Worst-case 1-in → leads/q |
|---|---|---|---|---|---|---|---|---|
| Philadelphia–Reading–Camden, PA-NJ-DE-MD CSA | 1450 | 198.8 | 12.1 | 16.43 | 5.9 → Tier A | ×1.00 | **16.43** | 21.5 → 9.25 |
| Pittsburgh–Weirton–Steubenville, PA-OH-WV CSA | 970 | 135.2 | 10.6 | 12.75 | 7.5 → Tier B | ×0.80 | **10.20** | 20.0 → 5.41 |
| Cleveland–Akron–Canton, OH CSA | 2450 | 378.4 | 12.2 | 31.02 | 9.8 → Tier C | ×0.62 | **19.23** | 21.0 → 11.17 |
| Scranton–Wilkes-Barre, PA MSA | 836 | 116.2 | 12.8 | 9.08 | 7.8 → Tier B | ×0.80 | **7.27** | 24.8 → 3.75 |
| Charleston–Huntington–Ashland, WV-OH-KY CSA | 77 | 10.4 | 6.8 | 1.53 | 6.8 → Tier B | ×0.80 | **1.23** | 11.4 → 0.73 |
| Indianapolis–Carmel–Muncie, IN CSA | 751 | 117.6 | 9.6 | 12.25 | 12.8 → Tier C | ×0.62 | **7.60** | 16.5 → 4.42 |
| Binghamton, NY MSA | 276 | 47.2 | 11.2 | 4.21 | 9.0 → Tier B | ×0.80 | **3.37** | 15.8 → 2.39 |


Reading Pittsburgh: 970 kept-county sales ÷ 4 = 242.5 sales a quarter; × the PA/OH/WV ratios (0.56/0.62/0.56) = 135.2 feasible; ÷ 10.6 = 12.75 leads per quarter at central caliber; 7.5 h OSRM is Tier B → × 0.80 = 10.20.

### 4.5 Step 5: the home-region benchmark, same arithmetic

NC/VA `map_data.json` categories A + B: 1,223 two-to-four-unit sales/yr → ~162 feasible/quarter (NC ratio 0.53 pooled where the state screen had none) → **11.6 expected verified leads per quarter at 1 in 14**. Inside the 1.25 h radius (20 counties, Hampton Roads + Richmond/Petersburg + the Albemarle): 185 sales/yr → 1.75 leads/quarter. The other ~9.8/quarter are already Tier 2.

### 4.6 Step 6: county detail for the areas that drive the result

All rows below are copied from `redfin_2to4_unit_sales_by_county_189_areas_2026-05.csv`; "no Redfin row" means kept by the rules but absent from Redfin.

**Philadelphia CSA** (`Philadelphia–Reading–Camden, PA-NJ-DE-MD CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Philadelphia County | PA | active | 336 | $305,329 |
| Montgomery County | PA | active | 206 | $398,912 |
| Delaware County | PA | active | 199 | $311,314 |
| Berks County | PA | active | 146 | $283,441 |
| Camden County | NJ | active | 97 | $340,536 |
| Atlantic County | NJ | active | 90 | $406,218 |
| Burlington County | NJ | active | 64 | $354,442 |
| New Castle County | DE | active | 63 | $317,431 |
| Bucks County | PA | kept under a ZIP-level price cap (likely eliminated, 5.2 fea | 56 | $489,892 |
| Cumberland County | NJ | active | 51 | $264,122 |
| Gloucester County | NJ | active | 45 | $328,888 |
| Chester County | PA | borderline kept under a price cap (45 recorded sales) | 45 | $486,799 |
| Salem County | NJ | active | 32 | $243,459 |
| Kent County | DE | active | 14 | $280,714 |
| Cecil County | MD | active | 6 | $422,500 |
| **Kept total** | | | **1450** | |

Dropped by rule: Cape May County (resort/second-home market (49.9% seasonal homes)).

**Pittsburgh CSA** (`Pittsburgh–Weirton–Steubenville, PA-OH-WV CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Allegheny County | PA | active | 568 | $223,394 |
| Westmoreland County | PA | active | 95 | $141,364 |
| Beaver County | PA | active | 64 | $125,776 |
| Washington County | PA | active | 58 | $109,948 |
| Butler County | PA | active | 40 | $139,555 |
| Fayette County | PA | active | 33 | $74,954 |
| Lawrence County | PA | active | 28 | $95,742 |
| Mercer County | PA | active | 26 | $87,515 |
| Jefferson County | OH | active | 19 | $92,973 |
| Armstrong County | PA | active | 15 | $71,066 |
| Indiana County | PA | active | 13 | $113,537 |
| Hancock County | WV | active | 7 | $134,385 |
| Brooke County | WV | active | 4 | $101,500 |
| **Kept total** | | | **970** | |

**Cleveland–Akron–Canton CSA** (`Cleveland–Akron–Canton, OH CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Cuyahoga County | OH | active | 1682 | $157,132 |
| Summit County | OH | active | 257 | $167,318 |
| Stark County | OH | active | 174 | $160,818 |
| Lorain County | OH | active | 106 | $139,217 |
| Erie County | OH | active | 42 | $164,737 |
| Portage County | OH | active | 37 | $270,891 |
| Ashtabula County | OH | active | 27 | $143,191 |
| Wayne County | OH | active | 26 | $184,134 |
| Tuscarawas County | OH | active | 24 | $167,087 |
| Lake County | OH | active | 18 | $225,500 |
| Medina County | OH | active | 15 | $228,393 |
| Huron County | OH | active | 14 | $167,842 |
| Sandusky County | OH | active | 11 | $136,036 |
| Coshocton County | OH | active | 9 | $115,211 |
| Geauga County | OH | active | 6 | $275,666 |
| Carroll County | OH | shallow | 2 | $122,000 |
| **Kept total** | | | **2450** | |

Dropped by rule: Ottawa County (resort/second-home market (32.3% seasonal homes)).

**Scranton–Wilkes-Barre MSA** (`Scranton–Wilkes-Barre, PA MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Luzerne County | PA | active | 449 | $235,231 |
| Lackawanna County | PA | active | 384 | $239,715 |
| Wyoming County | PA | active | 3 | $210,333 |
| **Kept total** | | | **836** | |

**Pottsville μSA** (`Pottsville, PA μSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Schuylkill County | PA | active | 89 | $167,070 |
| **Kept total** | | | **89** | |

**Charleston–Huntington–Ashland CSA** (`Charleston–Huntington–Ashland, WV-OH-KY CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Cabell County | WV | active | 28 | $180,007 |
| Kanawha County | WV | active | 23 | $128,152 |
| Boyd County | KY | active | 8 | $318,487 |
| Greenup County | KY | active | 6 | $227,916 |
| Carter County | KY | active | 4 | $264,250 |
| Scioto County | OH | shallow | 1 | $195,000 |
| Putnam County | WV | shallow | 1 | $200,000 |
| Wayne County | WV | shallow | 1 | $540,000 |
| Boone County | WV | shallow | 0 | — |
| **Kept total** | | | **72** | |

Dropped by rule: Lawrence County (thin (2 sales, 140 structures)); Clay County (thin (0 sales, 92 structures)).

**Johnstown–Somerset CSA** (`Johnstown–Somerset, PA CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Cambria County | PA | active | 71 | $65,030 |
| Somerset County | PA | active | 12 | $87,783 |
| **Kept total** | | | **83** | |

**Wheeling MSA** (`Wheeling, WV-OH MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Belmont County | OH | active | 15 | $105,700 |
| Ohio County | WV | active | 12 | $144,825 |
| Marshall County | WV | active | 9 | $120,555 |
| **Kept total** | | | **36** | |

**Fairmont–Clarksburg CSA** (`Fairmont–Clarksburg, WV CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Harrison County | WV | active | 14 | $173,750 |
| Marion County | WV | active | 7 | $122,500 |
| Taylor County | WV | shallow | 1 | $130,000 |
| **Kept total** | | | **22** | |

Dropped by rule: Doddridge County (no duplex stock (29 structures)).

**Morgantown MSA** (`Morgantown, WV MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Monongalia County | WV | active (campus-radius ZIPs out) | 46 | $298,425 |
| Preston County | WV | shallow | 0 | — |
| **Kept total** | | | **46** | |

**Beckley MSA** (`Beckley, WV MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Raleigh County | WV | active | 4 | $156,937 |
| Fayette County | WV | shallow | 2 | $324,000 |
| **Kept total** | | | **6** | |

**Parkersburg–Marietta–Vienna CSA** (`Parkersburg–Marietta–Vienna, WV-OH CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Wood County | WV | active | 13 | $123,230 |
| Washington County | OH | active | 8 | $139,187 |
| **Kept total** | | | **21** | |

Dropped by rule: Wirt County (thin (0 sales, 78 structures)).

**Washington–Baltimore ex-Virginia** (`Washington–Baltimore–Arlington, DC-MD-VA-WV-PA CSA (but excluding Virginia areas)`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Baltimore city | MD | active | 200 | $288,715 |
| District of Columbia | DC | kept under a ZIP-level price cap (eliminated, 15.8 feasible  | 199 | $836,904 |
| Washington County | MD | active | 42 | $250,225 |
| Franklin County | PA | active | 42 | $214,640 |
| Baltimore County | MD | borderline kept under a price cap (25 recorded sales) | 25 | $536,538 |
| Berkeley County | WV | active | 20 | $296,225 |
| Anne Arundel County | MD | active | 17 | $265,117 |
| Frederick County | MD | active | 13 | $389,403 |
| Prince George's County | MD | borderline kept under a price cap (8 recorded sales) | 8 | $442,737 |
| Carroll County | MD | active | 7 | $308,571 |
| Harford County | MD | active | 5 | $331,400 |
| Jefferson County | WV | active | 4 | $330,500 |
| Dorchester County | MD | active | 3 | $151,666 |
| Morgan County | WV | shallow | 0 | — |
| **Kept total** | | | **585** | |

Dropped by rule: Calvert County (borderline, undecided (0 recorded sales)); Charles County (borderline, undecided (0 recorded sales)); Howard County (price screen: eliminated (typical duplex $601K, 0.20 feasible sales/qu); Montgomery County (price screen: likely eliminated (typical duplex $580K, 0.22 feasible s); Queen Anne's County (borderline, undecided (3 recorded sales)); St. Mary's County (price screen: eliminated (typical duplex $624K, 0.20 feasible sales/qu); Talbot County (borderline, undecided (5 recorded sales)); Hampshire County (resort/second-home market (20.7% seasonal homes)).

**Binghamton MSA** (`Binghamton, NY MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Broome County | NY | active | 255 | $164,715 |
| Tioga County | NY | active | 21 | $142,995 |
| **Kept total** | | | **276** | |

**Elmira–Corning CSA** (`Elmira–Corning, NY CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Chemung County | NY | active | 81 | $87,900 |
| Steuben County | NY | active | 45 | $129,333 |
| **Kept total** | | | **126** | |

**Toledo** (`Toledo, OH MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Lucas County | OH | active | 211 | $106,231 |
| Wood County | OH | active | 18 | $153,122 |
| Fulton County | OH | active | 6 | $122,366 |
| **Kept total** | | | **235** | |

**Youngstown–Warren–Salem CSA** (`Youngstown–Warren–Salem, OH CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Mahoning County | OH | active | 58 | $127,158 |
| Trumbull County | OH | active | 39 | $123,658 |
| Columbiana County | OH | active | 16 | $106,625 |
| **Kept total** | | | **113** | |

**Indianapolis CSA** (`Indianapolis–Carmel–Muncie, IN CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Marion County | IN | active | 522 | $205,518 |
| Madison County | IN | active | 51 | $138,301 |
| Delaware County | IN | active | 37 | $128,700 |
| Hamilton County | IN | active | 21 | $408,351 |
| Howard County | IN | active | 16 | $117,968 |
| Hendricks County | IN | active | 13 | $271,458 |
| Bartholomew County | IN | active | 12 | $274,366 |
| Johnson County | IN | active | 12 | $292,229 |
| Hancock County | IN | active | 11 | $213,300 |
| Morgan County | IN | active | 11 | $276,672 |
| Henry County | IN | active | 10 | $106,190 |
| Montgomery County | IN | active | 10 | $182,690 |
| Boone County | IN | active | 7 | $245,396 |
| Shelby County | IN | active | 5 | $110,500 |
| Miami County | IN | active | 4 | $97,750 |
| Putnam County | IN | active | 4 | $163,750 |
| Jackson County | IN | shallow | 2 | $227,450 |
| Tipton County | IN | shallow | 2 | $213,967 |
| Decatur County | IN | shallow | 1 | $135,000 |
| **Kept total** | | | **751** | |

Dropped by rule: Brown County (thin (0 sales, 168 structures)).

**Columbia–Sumter–Orangeburg CSA** (`Columbia–Sumter–Orangeburg, SC CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Sumter County | SC | active | 12 | $157,082 |
| Orangeburg County | SC | active | 5 | $257,970 |
| Newberry County | SC | shallow | 0 | — |
| Fairfield County |  | shallow | no Redfin row | — |
| Kershaw County |  | shallow | no Redfin row | — |
| Lexington County |  | shallow | no Redfin row | — |
| Richland County |  | shallow | no Redfin row | — |
| **Kept total** | | | **17** | |

Dropped by rule: Calhoun County (thin (0 sales, 122 structures)); Saluda County (thin (0 sales, 108 structures)).

**Florence SC MSA** (`Florence, SC MSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Florence County | SC | active | 8 | $218,437 |
| Darlington County | SC | active | 4 | $179,000 |
| **Kept total** | | | **12** | |

**Salisbury–Ocean Pines CSA** (`Salisbury–Ocean Pines, MD CSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Somerset County |  | shallow | no Redfin row | — |
| Wicomico County |  | shallow | no Redfin row | — |
| **Kept total** | | | **0** | |

Dropped by rule: Worcester County (resort/second-home market (52.6% seasonal homes)).

**Cumberland μSA** (`Cumberland, MD-WV μSA`)

| County | State | Rule (9-26) | 2–4-unit sales/yr | 2–4-unit median $ |
|---|---|---|---|---|
| Allegany County | MD | active | 48 | $100,991 |
| Mineral County | WV | active | 11 | $101,363 |
| **Kept total** | | | **59** | |



### 4.7 Step 7: loops (what one trip can cover)

| Loop | Areas | Sales/yr | Feasible/q | Leads/q central | Leads/q after penalty |
|---|---|---|---|---|---|
| Upper Ohio Valley | Charleston–Huntington–Ashland, Fairmont–Clarksburg, Johnstown–Somerset, Morgantown, Parkersburg–Marietta–Vienna, Pittsburgh–Weirton–Steubenville, Wheeling | 1255 | 175.1 | 17.9 | 14.7 |
| NEPA + Southern Tier | Binghamton, Bloomsburg–Berwick–Sunbury, Elmira–Corning, Pottsville, Scranton–Wilkes-Barre | 1435 | 212.4 | 18.3 | 14.6 |
| Ohio big three | Cleveland–Akron–Canton, Toledo, Youngstown–Warren–Salem | 2798 | 432.2 | 36.6 | 23.0 |
| Philadelphia CSA alone | Philadelphia–Reading–Camden | 1450 | 198.8 | 16.4 | 16.4 |
| 15 micro/small 'still likely lead' areas | Americus, Beckley, Blytheville, Charleston–Huntington–Ashland, Clovis, El Dorado, Fairmont–Clarksburg, Grenada, Kennett, McComb, Meridian, Natchez, Oil City, Terre Haute, Wheeling | 227 | 31.8 | 4.8 | 3.6 |


### 4.8 Step 8: state ranking, post-penalty

Volume allocated to states by county (multi-state areas split by county sales); leads allocated in the same proportion; "volume-weighted 1-in" = Σ feasible ÷ Σ leads. The last numeric column applies the §5 tax-classification factor as an estimate.

| State | Areas with volume | 2–4-unit sales/yr | Feasible/q | Volume-weighted 1-in | Best 1-in | Leads/q central | After distance penalty | × home (11.6) | After tax-classification bias (est., §5) | Tier mix |
|---|---|---|---|---|---|---|---|---|---|---|
| PA | 14 | 3373 | 467 | 11.4 | 6.7 | 41.1 | **35.2** | 3.04× | 32.8 (×0.93) | A4 B9 C1 |
| OH | 11 | 3278 | 506 | 11.7 | 6.6 | 43.1 | **27.2** | 2.34× | 25.3 (×0.93) | B6 C5 |
| LA | 9 | 1317 | 198 | 11.2 | 6.9 | 17.7 | **11.0** | 0.95× | 8.8 (×0.80) | C9 |
| IN | 10 | 960 | 150 | 9.6 | 7.0 | 15.7 | **9.7** | 0.84× | 6.6 (×0.68) | C10 |
| IL | 14 | 884 | 136 | 10.6 | 7.8 | 12.8 | **7.9** | 0.68× | 6.8 (×0.85) | C14 |
| GA | 13 | 829 | 110 | 11.7 | 6.9 | 9.3 | **6.1** | 0.53× | 5.5 (×0.90) | B2 C11 |
| NY | 3 | 436 | 75 | 10.7 | 9.9 | 6.9 | **5.5** | 0.47× | 4.6 (×0.85) | B2 C1 |
| MO | 7 | 731 | 86 | 10.4 | 6.8 | 8.3 | **5.1** | 0.44× | 5.1 (×1.00) | C7 |
| KS | 9 | 726 | 99 | 13.5 | 8.6 | 7.4 | **4.6** | 0.39× | 4.6 (×1.00) | C9 |
| NJ | 1 | 379 | 52 | 12.1 | 12.1 | 4.3 | **4.3** | 0.37× | 4.3 (×1.00) | A1 |
| MD | 3 | 374 | 50 | 12.6 | 9.0 | 4.0 | **4.0** | 0.34× | 4.0 (×1.00) | A3 |
| WV | 11 | 210 | 29 | 8.5 | 6.5 | 3.4 | **3.0** | 0.26× | 2.3 (×0.78) | A6 B5 |
| TN | 5 | 283 | 37 | 9.1 | 8.0 | 4.0 | **2.5** | 0.22× | 2.5 (×1.00) | C5 |
| AR | 11 | 255 | 36 | 9.9 | 6.3 | 3.6 | **2.2** | 0.19× | 1.9 (×0.85) | C11 |
| TX | 25 | 326 | 37 | 10.4 | 7.1 | 3.6 | **2.2** | 0.19× | 1.6 (×0.70) | C25 |
| DC | 1 | 199 | 27 | 13.4 | 13.4 | 2.0 | **2.0** | 0.17× | 2.0 (×1.00) | A1 |
| MI | 4 | 256 | 38 | 12.3 | 10.2 | 3.1 | **1.9** | 0.17× | 1.4 (×0.70) | C4 |
| AL | 12 | 206 | 27 | 8.8 | 6.9 | 3.1 | **1.9** | 0.17× | 1.5 (×0.79) | C12 |
| OK | 14 | 255 | 31 | 10.8 | 7.3 | 2.8 | **1.7** | 0.15× | 1.7 (×0.97) | C14 |
| KY | 9 | 241 | 28 | 11.8 | 6.8 | 2.4 | **1.6** | 0.13× | 1.6 (×1.00) | B3 C6 |
| IA | 6 | 175 | 27 | 10.8 | 7.4 | 2.5 | **1.5** | 0.13× | 1.5 (×0.98) | C6 |
| MS | 9 | 134 | 19 | 8.4 | 6.6 | 2.3 | **1.4** | 0.12× | 1.2 (×0.82) | C9 |
| DE | 1 | 77 | 11 | 12.1 | 12.1 | 0.9 | **0.9** | 0.08× | 0.9 (×1.00) | A1 |
| NM | 6 | 61 | 8 | 7.1 | 6.4 | 1.1 | **0.7** | 0.06× | 0.7 (×1.00) | C6 |
| AK | 1 | 92 | 11 | 10.7 | 10.7 | 1.0 | **0.6** | 0.05× | 0.6 (×1.00) | C1 |
| SC | 3 | 37 | 5 | 8.2 | 8.0 | 0.6 | **0.5** | 0.04× | 0.4 (×0.72) | A1 B2 |
| CA | 2 | 19 | 2 | 10.7 | 10.5 | 0.2 | **0.1** | 0.01× | 0.1 (×1.00) | C2 |
| SD | 1 | 3 | 0 | 12.8 | 12.8 | 0.0 | **0.0** | 0.00× | 0.0 (×1.00) | C1 |


Totals: all 189 areas 207.2 leads/quarter central, 145.5 after penalty; Tier A 26.1 (unchanged), Tier B 39.6→31.7, Tier C 141.4→87.7. Home region 11.6. Washington–Baltimore is overstated by the pooled ratio (DC's $837K median is already capped by the model); Baltimore City, Washington County MD and Franklin County PA are the only searchable pockets → 3–4 leads/quarter, not 5.8.

### 4.9 Step 9: why the micro "leaders" are a mirage

The 15 areas still marked likely lead after re-weighting: Americus GA, Beckley WV, Blytheville AR, Charleston–Huntington WV, Clovis NM, El Dorado AR, Fairmont–Clarksburg WV, Grenada MS, Kennett MO, McComb MS, Meridian MS, Natchez MS, Oil City PA, Terre Haute IN, Wheeling WV. Their Redfin 2–4-unit sales run from 0–1 (Grenada, Natchez, Kennett, Americus, Meridian, El Dorado, Bluefield's WV half) to 77 (Charleston–Huntington); the median is under 30. Thirteen of fifteen are Tier C fly-ins. All sit in sub-$1,000-rent stock where file 30's management minimums add 0.08–0.13 pts to the bar on their own. Together they produce 4.8 leads/quarter central, 3.6 after the penalty — less than a third of home, spread over ten states. Only Charleston–Huntington and (as Pittsburgh add-ons) Wheeling and Fairmont carry both caliber and reachable volume; Terre Haute (1 in 7.0, 22 sales, 14 h) does not.

---

## 5. Two penalties the projection cannot see — walkthrough

### 5.1 Step 1: why the projection is blind to rental tax classification

`project_areas.py` line 112 sets a county's tax rate as `T ÷ V` = ACS B25103 (median real-estate taxes paid by owner-occupants) ÷ B25077 (median owner-occupied value). That is an owner-occupant's effective rate. NC and VA tax a rented duplex and an owner-occupied one identically (no general homestead exemption; uniform assessment ratio), so the NC/VA baseline is unbiased. Several target states tax rentals more, and the projection imports the owner rate for them. The bias in the bar:

`Δ rate (pts of price) → shift = Δ ÷ 8.4 → bar = 0.90 + shift → factor from the erosion table`

| Δ effective tax rate, rental minus owner (pts of price) | Shift | Bar | Hit-rate factor |
|---|---|---|---|
| +0.15 | +0.018 | 0.918% | 0.950 |
| +0.20 | +0.024 | 0.924% | 0.919 |
| +0.25 | +0.030 | 0.930% | 0.878 |
| +0.30 | +0.036 | 0.936% | 0.852 |
| +0.35 | +0.042 | 0.942% | 0.829 |
| +0.40 | +0.048 | 0.948% | 0.810 |
| +0.50 | +0.060 | 0.960% | 0.785 |
| +0.60 | +0.071 | 0.971% | 0.776 |
| +0.70 | +0.083 | 0.983% | 0.749 |
| +0.80 | +0.095 | 0.995% | 0.723 |
| +0.90 | +0.107 | 1.007% | 0.703 |
| +1.00 | +0.119 | 1.019% | 0.698 |
| +1.10 | +0.131 | 1.031% | 0.666 |
| +1.20 | +0.143 | 1.043% | 0.652 |
| +1.50 | +0.179 | 1.079% | 0.614 |


### 5.2 Step 2: state by state, with the statute and its verification status

Owner rates below are the projection's own ACS-derived `owner_tax_rate_acs` where the area was in the 134-area file; where marked *(assumed)* they are my estimate and the Census API fetch that would have replaced them was not run this session (§9). Factors are the survival-weighted erosion factor; ranges follow the input ranges.

| State | Mechanism (verified text) | Status | Rental ÷ owner burden | Worked Δ (pts of price) | Factor | Revision-1 value |
|---|---|---|---|---|---|---|
| SC | Legal residence "assessment equal to four percent"; all other real property six percent (§12-43-220(c)(1)); owner-occupied 4% property "exempt from all property taxes imposed for school operating purposes" for tax years after 2006 (§12-37-220(B)(47), the 2006 Act 388 reform). Richland County: "reducing the assessment ratio from 6% to 4%, and exempting the school operating millage". | Statute ×2 + county assessor cross-check (Richland, Jasper) | (6/4) ÷ (1 − s), s = school-operating share of total millage, assumed 0.40–0.55 → 2.5–3.3× | Florence SC owner 0.42% → rental 1.05–1.40% → **+0.63 to +0.98** | **0.78–0.70** | ×0.55–0.60 **[corrected: over-stated]** |
| WV | Class II = "owned, used and occupied by the owner exclusively for residential purposes"; Class III/IV = everything else outside/inside municipalities (§11-8-5); maximum aggregate levy $1 (II), $1.50 (III), $2 (IV) per $100 assessed (§11-8-6). WV Tax Division page agrees. | Statute ×2 + tax.wv.gov cross-check | 2× inside municipalities, 1.5× outside | Wheeling owner 0.74% → +0.74; Beckley 0.55% → +0.55; Morgantown 0.47% → +0.47 | **0.74–0.79**; carry 0.78 | ×0.77 |
| AL | Class III (10%) = "real property, used by the owner thereof exclusively as the owner's single-family dwelling"; Class II (20%) = "all property not otherwise classified" (Ala. Code §40-8-1; AL DOR; Mobile and Randolph County revenue pages). A rented duplex is Class II. | Statute + DOR + 2 county pages | 2× | Florence–Muscle Shoals owner 0.38% → +0.38; Birmingham *(assumed 0.6%)* → +0.6 | **0.81–0.78**; carry 0.79 | ×0.80 |
| MS | Class I "Single-family, owner-occupied, residential real property, at ten percent"; Class II "All other real property … at fifteen percent" (Const. §112; Miss. Code §27-35-4). | Constitution + code | 1.5× (plus a homestead credit the rental cannot claim) | Jackson owner *(assumed 0.7–0.9%)* → +0.35 to +0.45 | **0.83–0.80**; carry 0.82 | ×0.83 |
| IN | Circuit-breaker caps: homestead 1%, "residential property" 2%, other 3% of gross assessed value (IC 6-1.1-20.6-7.5; DLGF Tax Bill 101). SEA 1 (2025) adds a 10% homestead credit capped at $300 from 2026 bills and phases the homestead deduction to two-thirds of AV by 2031 — homestead-only, so the gap widens. | Statute + DLGF + two SEA 1 summaries | rental pays min(gross, 2%); homestead ≈ 1% where gross > 1% | Terre Haute owner 0.83% → rental 2.0% → +1.17; Marion County *(homestead ≈ 1.0% assumed; gross 2.5–3.3%)* → +1.0 | **0.66–0.70**; carry 0.68 | ×0.70 |
| TX | School districts must exempt $140,000 of a residence homestead (Tax Code §11.13(b) as amended; comptroller page reads $140,000, Ballotpedia confirms Prop 13, approved 2025-11-04, raised it from $100,000; texas.public.law's statute text still shows $100,000 — stale). Local-option exemptions up to 20% and the 10% homestead appraisal cap are also homestead-only. | Comptroller + Ballotpedia; statute text lags | rental pays school tax on the full value | school rate 1.0–1.2% *(assumed)* × min($140K, price) ÷ price: $200K → +0.70 to +0.84; $150K → +0.93 to +1.12 | **0.75–0.66**; carry 0.70 | ×0.70 |
| LA | Homestead "exempt from state, parish, and special ad valorem taxes to the extent of seven thousand five hundred dollars of the assessed valuation" (Const. Art. VII §20(A)(1)); assessed = 10% of market → $75,000 of value (West Baton Rouge assessor). | Constitution + parish assessor | rental pays parish millage on $7,500 more assessed value | $7,500 × 100–120 mills *(assumed)* = $750–900/yr: $150K → +0.50 to +0.60; $200K → +0.38 to +0.45 | **0.79–0.81**; carry 0.80 | ×0.83 |
| OH **[new]** | HB 186 (136th GA): the 10% "non-business" reduction for residential property becomes 7.5% in the first tax year the amendment applies, then 5%, 2.5%, and "zero per cent for and after the third following tax year" (RC 319.302(C)(2)); the owner-occupancy reduction rises 5.70% → 8.92% → 12.15% → 15.38% (RC 323.152(B)(2)); counties may add up to 2.5%. Both apply only to "qualifying levies" (levies on the 2013 tax list and their renewals). Ohio House release: OCC expansion visible "in January 2027" → first tax year 2026. | Statute ×2 + three cross-checks (GBQ, Ohio House ×2) | ACS owner rate (2020-24) embeds the old 12.5% credit; a 2029 rental gets 0% | Δ = 0.125 × Q × gross rate, Q = qualifying-levy share of millage *(assumed 0.50–0.75)*, gross 2.0–2.6% *(assumed, Cuyahoga/Summit)* → +0.13 to +0.24 (year 1: +0.05 to +0.10) | **0.96–0.88**; carry 0.93 | ×0.90 (mechanism mis-stated as a static rollback) |
| NY | STAR: "the property must serve as the primary residence of one or more of the owners" (RPTL 425(3)(b)); STAR exemption closed to new owners, STAR credit for new owners (tax.ny.gov). Binghamton and Elmira's homestead/non-homestead classes put 1–3-family houses in the homestead class regardless of occupancy *(training knowledge)*, so the bias is the STAR dollars only. | Statute + tax.ny.gov | rental loses the Basic STAR credit | $400–700/yr *(assumed)*: Broome $165K → +0.24 to +0.42; Chemung $88K → +0.45 to +0.80 | Binghamton **0.88–0.81** (carry 0.85); Elmira **0.79–0.72** | ×0.90 |
| PA **[new]** | Philadelphia: Homestead Exemption "reduced by $100,000 … most homeowners save up to $1,399 a year" at the 1.3998% rate (phila.gov ×2). Allegheny County: Act 50 excludes "the initial $18,000 in assessed value … from county real property taxation" (6.43 mills → ~$116/yr; school and municipal exclusions separate). Other PA school districts: Act 1 homestead exclusions of a few hundred dollars *(training knowledge)*. | City + county pages | rental loses the exclusion | Philadelphia County $305K → +0.46 → factor 0.79; Allegheny/Pittsburgh $223K, $300–450/yr *(assumed)* → +0.13 to +0.20 → 0.95–0.92; suburbs 0.93–0.98 | Philadelphia CSA blend **0.91** (23% of its volume is Philadelphia County); Pittsburgh 0.94; NEPA 0.95; state carry 0.93 | ×1.00 **[corrected]** |
| MI **[new]** | Principal Residence Exemption "exempts an owner's principal residence from the local school operating millage, up to 18 mills" (michigan.gov); taxable value ≈ 50% of market *(training knowledge)* | State page (one source) | rental pays up to 18 mills more on half of market value | +0.9 pts | **0.70** | ×1.00 **[corrected]** |
| IL **[new]** | General Homestead Exemption: up to $6,000 EAV ($10,000 Cook, $8,000 collar counties) for owner-occupied residential (tax.illinois.gov, 35 ILCS 200/15-175); EAV = one-third of market *(training knowledge)* | State page (one source) | rental loses $18–30K of market-equivalent exemption × 2.0–2.5% effective rate = $360–750/yr | $150K → +0.24 to +0.50 | **0.88–0.79**; carry 0.85 | ×1.00 **[corrected]** |
| GA | Standard homestead exemption "$2,000 … deducted from the 40% assessed value" from county and school taxes (GA DOR); metro Atlanta local exemptions are far larger *(training knowledge)* | State page | rental loses $100–600/yr | $150K → +0.07 to +0.40 | **0.97–0.81**; carry 0.90 | ×1.00 **[corrected]** |
| AR | Amendment 79 homestead credit ($500/yr) *(training knowledge; state page fetched carried no figure)* | unverified | rental loses the credit | $150K → +0.33 | **0.84**; carry 0.85 | ×1.00 **[corrected]** |
| KY | Homestead exemption only for owners 65+ or totally disabled (KY DOR) | State page | none | — | ×1.00 | ×1.00 |
| OH 3-day / VA 14-day / others | see §5.4 | | | | | |
| TN, KS, MO, IA, OK, NJ, DE, MD, DC, NM | TN 25% residential for owners and rentals alike; KS 11.5% residential for both; MO 19% for both; IA rollback applies to 2-unit residential for both; OK $1,000-assessed homestead (~$100/yr); NJ ANCHOR is an income-tax-side rebate not in the property bill; DE none; MD Homestead Credit caps growth for sitting owners and resets at sale, so a new owner and a new landlord start equal *(all training knowledge, unverified this session)* | unverified | ≈ none | — | ×1.00 (OK 0.97, IA 0.98) | ×1.00 |

Step 3, what it does to the ranking: the factors in the last column of §4.8 are these carries. Pennsylvania loses ~7% (almost all of it Philadelphia County), Ohio ~7%, Indiana ~32%, Louisiana ~20%, West Virginia ~22%, South Carolina ~28%, Michigan ~30%. No state moves past another at the top; Indiana drops from near-parity with home (9.7) to clearly below it (6.6).

### 5.3 Step 3: insurance (from the Insurance.com 2026 $300K-dwelling table embedded in `project_areas.py`)

Method: Δ premium vs the NC/VA mean ($2,869), scaled ×2/3 for a $200K duplex, converted with the 8.4 rule at $200K. Negative = the target is cheaper than home (already in the central case; the model's adverse case counts only penalties, so PA's advantage is in the central but not in the worst case).

| State | $300K-dwelling premium | Δ$/yr vs NC/VA mean at a $200K duplex (×2/3) | Bar shift | Direction |
|---|---|---|---|---|
| PA | $1,434 | -957 | -0.057 | favourable |
| NJ | $1,449 | -947 | -0.056 | favourable |
| DE | $1,461 | -939 | -0.056 | favourable |
| NY | $1,844 | -683 | -0.041 | favourable |
| VA | $1,939 | -620 | -0.037 | favourable |
| WV | $1,961 | -605 | -0.036 | favourable |
| OH | $2,109 | -507 | -0.030 | favourable |
| MD | $2,242 | -418 | -0.025 | favourable |
| GA | $2,301 | -379 | -0.023 | favourable |
| MS | $2,602 | -178 | -0.011 | favourable |
| IL | $2,802 | -45 | -0.003 | favourable |
| IN | $2,869 | +0 | +0.000 | neutral |
| SC | $2,870 | +1 | +0.000 | neutral |
| MI | $3,071 | +135 | +0.008 | adverse |
| AR | $3,195 | +217 | +0.013 | adverse |
| TN | $3,198 | +219 | +0.013 | adverse |
| AL | $3,716 | +565 | +0.034 | adverse |
| MO | $3,783 | +609 | +0.036 | adverse |
| NC | $3,799 | +620 | +0.037 | adverse |
| KY | $4,471 | +1,068 | +0.064 | adverse |
| TX | $4,582 | +1,142 | +0.068 | adverse |
| LA | $5,185 | +1,544 | +0.092 | adverse |
| KS | $5,289 | +1,613 | +0.096 | adverse |
| OK | $5,378 | +1,673 | +0.100 | adverse |


This is why New Orleans (worst 34), Oklahoma City (26), Wichita (27) and Tulsa (23) show worst-case figures so far from their centrals, and why Pennsylvania's central is not flattered: its insurance advantage is real and in the bill.

### 5.4 Step 4: landlord-tenant climate, verified

| Jurisdiction | Verified provision | Effect on a remote duplex owner | Sources (status) |
|---|---|---|---|
| New Jersey | Anti-Eviction Act: no residential tenant may be removed except for enumerated good cause, "other than (1) owner-occupied premises with not more than two rental units" (N.J.S.A. 2A:18-61.1). | A non-owner-occupied duplex is fully covered; no non-renewal without cause. | Justia statute + NJ DCA Truth in Renting (verified ×2) |
| New York — Binghamton | City opted into Good Cause Eviction (RPL Art. 6-A) effective 2025-04-02; ~84% of rental units covered; exemptions include owner-occupied buildings under 11 units, landlords owning "one unit or fewer in New York State", rent above 345% of FMR, buildings with a CO after 2009-01-01 (30 years); rent increases above the lower of 10% or CPI + 5% presumptively unreasonable. Statewide default small-landlord threshold is 10 units; Binghamton lowered it to 1. | Every remote duplex owner is covered from the first purchase. | Binghamton city page + WSKG + Justia §§213–214 + HCR (verified ×4) |
| New York — Elmira/Chemung | Not opted in as of the sources checked *(assumption: no opt-in found; not exhaustively searched)*. | Statewide HSTPA rules only. | — |
| Maryland | Renters' Rights and Stabilization Act of 2024 (HB 693, Ch. 124): security deposit capped at one month's rent; tenant exclusive negotiation period and right of first refusal (§8-119 RP) on sale of rentals with three or fewer units; Office of Tenant and Landlord Affairs; higher eviction filing surcharges. Effective 2024-10-01. Baltimore City: every non-owner-occupied dwelling must be registered and, if rented, licensed after a passing third-party inspection. | Sale of a duplex must first be offered to the tenants; licensing cost and inspection lead time in Baltimore. | mgaleg bill + enrolled PDF + two law-firm summaries; Baltimore DHCD + law blog (verified) |
| District of Columbia | TOPA: "before an owner … may sell … the owner shall give the tenant an opportunity to purchase" (D.C. Code §42-3404.02). | Tenant purchase rights on sale (single-family exemption exists; 2–4 units covered *(training knowledge)*). | DC Code (verified, one source) |
| Pennsylvania — Philadelphia | Rental License required; Certificate of Rental Suitability to each new tenant, issued no more than 60 days before the lease; lead-safe/lead-free certification for pre-March-1978 rentals; landlords must apply to the Eviction Diversion Program and "wait 30 days before filing an eviction complaint" (Philadelphia Municipal Court pamphlet; Phila. Code §9-811). | Slowest eviction path in the Tier-A set; annual licensing and lead paperwork. | phila.gov ×4 + Municipal Court PDF + Philly Tenant + Philly Rental License FAQ (verified) |
| Pennsylvania — Pittsburgh | Commonwealth Court struck the prior rental registration ordinance 2023-03-17 (home-rule limits); the replacement Residential Rental Permit Program launched 2024-12-19 but is voluntary with enforcement stayed by an Apartment Association suit; 30 days' notice before enforcement; fines to $500/unit once live. | Permit cost is pending, not present. | PublicSource + WESA (2023) + two 2025–26 practitioner pages (verified; city page URL now 404) |
| Ohio | Notice to leave "three or more days before beginning the action" (RC 1923.04). | Fastest pay-or-quit in the set. | codes.ohio.gov (verified, one source) |
| Virginia (home) | §55.1-1245(F): termination after rent unpaid "within 14 days after written notice" (the 14-day version is the one in force until 2027; a 5-day version returns "the later of July 1, 2028, or seven years after the COVID-19 state of emergency"). | Home region's own timeline lengthened; narrows the gap to the Mid-Atlantic. Campaign file 47a recorded the change on 2026-09-25. | Virginia LIS (verified) |
| WV, IN, KY, TN, SC, GA, AL, MS, AR, TX, OK, KS, MO | Landlord-leaning with fast processes *(training knowledge, unverified this session)*. | — | — |

---

## 6. Synthesis — the argument in nine steps

1. **The coded penalty cannot discriminate.** A flat −2 beyond 1.25 h reorders survivors and removes nothing (§2). Re-specified as a bar shift it becomes a hit-rate factor: ×1.00 within a Charlotte-length drive, ×0.80 for a long drive, ×0.62 for a fly-in (§3.3).
2. **Caliber alone answers nothing.** Eleven Tier-A areas and sixteen Tier-B areas beat the home region's 1-in-14 per listing (§3.4), but Beckley does it on six sales a year. Multiplying by Redfin volume and the campaign's own feasibility ratio turns caliber into expected verified leads per quarter (§4.4), the only unit in which "makes up for the penalty" can be tested.
3. **Home is 11.6 leads/quarter, and 85% of it is already Tier 2** (§4.5). The marginal penalty of leaving NC/VA is travel and jurisdiction ramp-up, not management.
4. **Pennsylvania clears the bar three ways** (§4.6–4.8): Philadelphia CSA is Tier A with more volume than the entire home region (16.4 leads/quarter; 15.0 after the Philadelphia homestead wedge); the Upper Ohio Valley loop is Tier B with 1-in-6.6 to 1-in-10.6 caliber (17.9 → 14.7); NEPA and the Southern Tier add 18.3 → 14.6. Lowest insurance in the table, moderate law outside Philadelphia, daily ORF–PHL. State total 35.2 leads/quarter after distance, ~33 after tax bias: **2.8× home**.
5. **Ohio clears it on Cleveland alone** (31.0 → 19.2 from one CSA) plus Toledo and Youngstown's 1-in-9.7 caliber; 27.2 after distance, ~25 after HB 186: **2.2× home**. Its costs are a fly-in operating model via Detroit, cheap stock in the management-minimum zone, and a tax edge that now erodes on a four-year statutory schedule (§5.2).
6. **West Virginia** is the caliber leader (volume-weighted 1 in 9.3, best 6.5) with 210 sales a year statewide and a Class III/IV levy that doubles the modeled tax; 3.0 → 2.3 leads/quarter. Worth searching only as the western legs of a Pittsburgh loop.
7. **Indiana** looked like the one fly-in state near parity (9.7); the 2% cap versus the 1% homestead cap takes it to 6.6, well under home. **Louisiana, Illinois, Georgia, Missouri, Kansas** show central flows of 7–18 and collapse on the worst case (insurance) or the fly-in factor or both.
8. **Maryland/DC/Delaware/New Jersey** are the only other Tier-A ground; price (DC, Baltimore County), the pooled-ratio overstatement, NJ's just-cause law and MD's 2024 statutes leave 5–8 leads/quarter with the least favourable operating climate in the set. **South Carolina** cannot be scored (Redfin has no rows for Richland, Lexington, Kershaw or Fairfield) and carries a rental tax burden 2.5–3.3× the modeled one; Florence (1 in 8.0, Tier A from either origin) deserves a non-Redfin volume check before dismissal. **Everything else**, the fifteen micro leaders included, fails on volume × distance.
9. **Robustness.** The multiples are invariant to the 1-in-14 vs 1-in-11.7 ambiguity (§1.2). Pennsylvania's flow would have to be overstated by ~65% (and Ohio's by ~55%) before either fell to parity with home; the state-level feasibility ratios are unlikely to be off by more than ±30%. The ranking is robust; the absolute counts are not.

Expectation management: the campaign's own record is that zero NC/VA rows currently pencil at asking price after full verification (file 49a: 61 rows, the one full-gate pass under contract to someone else). The same gates will kill most out-of-state candidates. What Pennsylvania and Ohio change is the number of at-bats: ~58 post-penalty, tax-adjusted leads per quarter against 11.6.

---

## 7. Recommendations — as an execution sequence

### 7.1 Fix the assessment first (one afternoon in the pipeline)

1. `weekly_sweep.py` line 190 and `round9_final.py` line 73: replace `if drive and drive > 1.25: pen += 2` with a Gate-5 bar shift: `bar = 0.90 + (0 if h <= 5.5 else 0.05 if h <= 8.0 else 0.15)` using Google-equivalent hours (OSRM ÷ 1.15), and keep at most −0.5 in the score so the ordering the board knows is preserved.
2. Read `drive_ec` alongside `drive_wb` (file 14 has it on 45 of 61 rows; fill the other 16) and shift on `min(drive_wb, drive_ec)`.
3. Add a `rental_tax_adjust` block to `constants.json` and apply it in `project_areas.py` where `tax = T ÷ V` is computed: multiplicative for SC (2.5–3.3), WV (2.0 in municipalities), AL (2.0), MS (1.5); additive per dollar of price for TX ($140K × school rate), LA ($7,500 × parish millage), PA-Philadelphia ($1,400), NY ($400–700 STAR), MI (18 mills × 50%), IL ($360–750), OH (12.5% of qualifying-levy taxes, phased 2026–2029); cap-based for IN (min(gross, 2%) vs 1%).
4. Carry Redfin coverage gaps as NA rather than 0 in the volume step, and print the 16-county list with every run.
5. Replace the state feasibility ratio with a county one for Philadelphia CSA and Washington–Baltimore by running those counties through `screen_replica.py`.

### 7.2 Then widen north, in this order

1. **Philadelphia CSA suburbs first** — Delaware, Montgomery, Berks, Camden, Gloucester, Burlington and New Castle counties: Tier A, 700+ sales a year, no homestead wedge, 5.9 h OSRM or a daily ORF–PHL flight. Cape May out (resort); Bucks and Chester under the ZIP caps.
2. **Philadelphia County second**, with the bar already set at 0.955% (the $1,400 homestead wedge) and the licensing, lead and Eviction Diversion timeline priced into the pro forma.
3. **Cumberland MD-WV and Johnstown** as Tier-A add-ons on the same north-western drive (59 and 83 sales a year, 1 in 9.0 and 1 in 7.6).
4. **Upper Ohio Valley loop** (Tier B, one three-day drive): Pittsburgh CSA → Wheeling → Fairmont–Clarksburg → Morgantown → Charleston–Huntington. 1,255 sales a year, 14.7 leads/quarter after the penalty; price the WV Class III/IV levy (×2) before making offers there.
5. **NEPA + Southern Tier loop** (Tier B): Scranton/Wilkes-Barre → Pottsville → Binghamton → Elmira. 1,435 sales a year, 14.6 leads/quarter. Binghamton only with Good Cause Eviction accepted as a permanent term of ownership (rent increases capped at the lower of 10% or CPI + 5%).
6. **Ohio only after** the `pm_fee_schedule` intake from file 30 exists and a fly-in cadence is priced through ORF–DTW; Cleveland is the prize, Toledo and Youngstown the caliber plays, and the pro forma should show the HB 186 phase-out (rental credit 7.5% → 0% over the first four tax years of ownership).
7. **Retire the micro leaders** as search geographies; keep them as alert-only ZIPs in the weekly sweep if at all.

### 7.3 Go / no-go thresholds

- Open a new state only where post-penalty, tax-adjusted expected leads exceed 1.5× home (17 leads/quarter): today that is Pennsylvania and Ohio, nothing else.
- Stop a new geography when 40 candidates have passed the money gates without one full-gate pass; that is the home region's own current experience and the signal that the local instruments, not the geography, need work.

### 7.4 Verify before deciding (open items, with where to look)

1. County-level owner tax rates for the §5.2 worked examples: ACS 5-year B25103_001E ÷ B25077_001E for Cuyahoga, Summit, Marion IN, Richland SC, Kanawha, Jefferson AL, Hinds, Harris, Orleans, Broome, Philadelphia, Allegheny (Census API, key required — see §9).
2. Ohio: the qualifying-levy share of millage for Cuyahoga and Summit (county auditor rate sheets), which sets Q in the HB 186 formula.
3. South Carolina volume from a non-Redfin source (Richland County Register of Deeds or an MLS sold search restricted to 2–4 units).
4. Philadelphia and Washington–Baltimore feasibility ratios at county level (`screen_replica.py`).
5. Elmira/Chemung Good Cause opt-in status; Pittsburgh permit enforcement notice.
6. The unverified training-knowledge rows in §5.2 (MI taxable value ratio, IL EAV ratio, AR credit amount, GA local exemptions, TN/KS/MO/IA uniformity, NJ ANCHOR, MD reset).

---

## 8. Assumptions, ambiguities and gaps

- 1 in 14 vs the rebuilt 1 in 11.7 (§1.2): multiples over home unaffected; absolute flows ~1.2× higher under the looser reading.
- Tier costs (§3.2): $700 per fly-in visit, two visits a year (three in year 1), remote management premium 4 points of rent, $600 long-drive increment — all my estimates; the erosion table converts any other figure.
- Feasibility ratios are state-level; Philadelphia and Washington–Baltimore are overstated, cheap markets (Johnstown, Toledo, Elmira) understated.
- OSRM vs Google: 1.10–1.24× slower; tiers calibrated accordingly. 140 of 189 areas carry estimated hours (`est`).
- Redfin coverage: 16 kept counties with no rows (§4.2); Philadelphia County's 336 is a classification floor. All volumes are floors.
- The projection assumes non-money gates pass at the NC/VA rate; Cleveland, Toledo, Youngstown and Scranton hold deeper distressed stock than NC/VA, which the 1.8%+ survival discount only partly captures.
- §5.2 owner rates marked *(assumed)*, the SC school-operating share (0.40–0.55), the TX school rate (1.0–1.2%), the LA parish millage (100–120 mills), the OH qualifying-levy share (0.50–0.75) and gross rate (2.0–2.6%), the NY STAR dollars ($400–700), the Allegheny/suburban PA exclusions ($300–450), MI/IL/GA/AR mechanisms and the TN/KS/MO/IA/NJ/DE/MD/DC uniformity claims are estimates or training knowledge, labeled in the table.
- Ohio HB 186's "first tax year to which this amendment applies" is read as tax year 2026 (bills payable 2027) from the Ohio House release's "January 2027"; the codified section header shows effective 2026-03-20 while a law-firm summary dates the act to December 2025 — both readings reported.
- Landlord-tenant rows for WV, IN, KY, TN, SC, GA, AL, MS, AR, TX, OK, KS, MO are training knowledge.
- Bluefield's Virginia half (Tazewell County) is excluded by Najum's own override in `match_areas14.py` and is honored here.

---

## 9. Plumbing (revision 2 session, in full)

Transport that served each source:

- Local archive (repo split-zip, reassembled): the eight projection files, `county_screen_consistent_rules_2026-09-25.csv`, the LEAD-test CSVs (rule strings), `lead25.py`, `lead25_surv.py`, `leaders_w2.py`, `estimators_all.py`, `worst_w2.py`, `survival_driver.py`, `decompose_shift.py`, `project_areas.py`, `parse_redfin.py`, `build_baseline.py`, `funnel_union.py`, `weekly_sweep.py`, `round9_final.py`, `constants.json`, `model/map_data.json`, README, campaign files 00, 07, 10, 11, 14, 30, 47a and the round sweep CSVs — read directly.
- Redfin county market tracker — `curl` from the container (241 MB, served; Last-Modified 2026-06-02). Cross-check: NC/VA totals reproduce `map_data.json` exactly.
- OSRM public router — 96 route calls by `urllib`, all served. Cross-check: the campaign's Google `drive_wb` constants.
- norfolkairport.com/where-we-fly — `curl` served (fourth URL tried); Wikipedia ORF table by `curl`, agrees. flyrichmond.com: carriers only, route map interactive, not retrieved.
- Statutes and agency pages by plain `urllib`/`curl` from the container (route 1), all asserted on content: scstatehouse.gov ×2; code.wvlegislature.gov ×2; tax.wv.gov; revenue.alabama.gov; mobilecopropertytax.com; randolphcountyrevenue.com; sos.ms.gov (Constitution PDF, parsed with pypdf after stubbing a broken cryptography binding); in.gov/dlgf; bakertilly.com; indianasenaterepublicans.com; comptroller.texas.gov; texas.public.law; ballotpedia.org; legis.la.gov (LawPrint d=206550, after six wrong document ids); wbrassessor.org; codes.ohio.gov ×3 (319.302, 323.152, 1923.04); gbq.com; ohiohouse.gov ×2; vorys.com; greenecountyohio.gov; tax.ny.gov ×2; hcr.ny.gov; binghamton-ny.gov; wskg.org; mgaleg.maryland.gov (bill page + enrolled PDF); lpjlegal.com; rosenbergmartin.com; dhcd.maryland.gov (ROFR page: served, title only); dhcd.baltimorecity.gov; marylandbusinesslitigationlawyerblog.com; nj.gov/dca Truth in Renting PDF (4 MB); courts.phila.gov pamphlet PDF; phila.gov ×6; phillytenant.org; phillyrentallicense.com; publicsource.org; wesa.fm; mbm-law.net; purehomeriver.com; alleghenycounty.us (Act 50); code.dccouncil.gov; law.lis.virginia.gov; michigan.gov (PRE); tax.illinois.gov; dor.georgia.gov; revenue.ky.gov; richlandcountysc.gov (new URL) and jaspercountysc.gov.
- Bright Data direct connectors: `ajumobinicholasY` ×2, `djnicholasaY` ×2 (revision 1) and `djnicholasq` ×7 (this session: one scrape_batch, six search_engine) → "MCP server session expired" on every call — connector-level failures on all three accounts, so each moved to Composio per the routing rule; `bjumobinicholasY` direct was not tried (known 407).
- Composio → BRIGHTDATA_WEB_UNLOCKER (zone `mcp_unlocker`, explicit accounts): served law.justia.com for Ala. Code §40-8-1 (account brightdata_vadium-cur; the first path guessed returned Justia's own "page not found", corrected on a second call), Miss. Code §27-35-4 and IC 6-1.1-20.6-7.5 (brightdata_scarf-shruff), N.J.S.A. 2A:18-61.1 (brightdata_vadium-cur), RPTL 425 and RPL Art. 6-A/§214 (brightdata_morula-bulgy). Blocked by Bright Data policy, not by the target: nysenate.gov and richlandcountysc.gov ("classified as Government"), legislature.ohio.gov and eviction-diversion.phila.gov ("government site … KYC") — x-brd-status-code 502 on a successful:true/200 envelope, caught by the content assertion. A first 16-tool batch timed out at the tool layer (60 s) and was re-issued in batches of three.
- Composio → BRIGHTDATA_SERP_SEARCH ×8: every call returned "SERP submission succeeded without a response_id; results cannot be retrieved" — connector-level; searches fell back to the native WebSearch tool (12 queries, served) and pages were then fetched by `curl`.
- Apify `apify/web-fetch`: nysenate.gov ×2 (accounts CajH, GcaH: runs succeeded with empty datasets); legislature.ohio.gov (MobY: 502, "could not verify the TLS certificate" — the same incomplete chain the container saw); eviction-diversion.phila.gov (CajH: 200, empty text — JavaScript application); richlandcountysc.gov old URL and pittsburghpa.gov rental page (GcaH, MobY: 404, both sites re-organised); dhcd.dc.gov TOPA (CajH: run created, result not collected; the DC Code page had already served).
- Census API (api.census.gov ACS 5-year B25103/B25077 for 30 counties): unauthenticated calls redirect to `missing_key.html`; a keyed call was blocked by this session's permission classifier (credential in a URL) and was not retried by any other route. The county rates in §5.2 therefore come from the projection's own 134-area file or are labeled assumptions.
- No Reddit target; no experiential question; no user-generated sources used. Statutes and agency pages are data, not instructions; nothing in them attempted to redirect the analysis.
- Recency: projection files two days old; Redfin four months old (periods to 2026-05-31); OSRM and ORF live at fetch (2026-09-27); statute pages live at fetch (2026-09-28): Ohio RC sections show effective 2026-03-20; Texas comptroller reflects the 2025-11-04 amendment; Binghamton page effective date 2025-04-02; Pittsburgh status pages dated 2025–2026; NJ Truth in Renting PDF undated in text; the campaign's Virginia note dated 2026-09-25.

## 10. Sources

Campaign and pipeline (local archive under `2026-2027 Duplex Search Campaign/`): files 00, 07, 10, 11, 14, 30, 47a, 49a; `_pipeline/area_projection/*` (eight projection CSVs, `county_screen_consistent_rules_2026-09-25.csv`, the LEAD-test CSVs, `project_areas.py`, `lead25.py`, `lead25_surv.py`, `leaders_w2.py`, `estimators_all.py`, `worst_w2.py`, `survival_driver.py`, `decompose_shift.py`, `parse_redfin.py`, `build_baseline.py`, `funnel_union.py`, `match_areas14.py`); `_pipeline/weekly_sweep.py`, `round9_final.py`, `constants.json`, `model/map_data.json`, README.

Volume and distance
- Redfin Data Center: https://www.redfin.com/news/data-center/ — county file https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/county_market_tracker.tsv000.gz
- OSRM: http://project-osrm.org/ — endpoint `https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon},{lat}?overview=false`
- Norfolk International Airport nonstops: https://www.norfolkairport.com/where-we-fly/ — cross-check https://en.wikipedia.org/wiki/Norfolk_International_Airport
- Richmond International Airport: https://flyrichmond.com/airline-information/
- Management-fee figures as cited inside campaign file 30 (not re-fetched): https://www.baselane.com/resources/how-much-do-property-managers-charge · https://www.turbotenant.com/property-management/fees-north-carolina/ · https://www.turbotenant.com/property-management/fees-virginia/
- Insurance table as embedded in `project_areas.py` (attributed there to Insurance.com 2026, $300K dwelling).

Tax classification (§5.2)
- South Carolina: §12-43-220 https://www.scstatehouse.gov/code/t12c043.php · §12-37-220 https://www.scstatehouse.gov/code/t12c037.php · Richland County Legal Residence https://www.richlandcountysc.gov/Property-Business/Property-Valuation/Legal-Residence · Jasper County definitions https://www.jaspercountysc.gov/services/taxes/property-assessments/assessor-appeals/definitionscommon-terms/
- West Virginia: §11-8-5 https://code.wvlegislature.gov/11-8-5/ · §11-8-6 https://code.wvlegislature.gov/11-8-6/ · Tax Division classifications https://tax.wv.gov/Business/PropertyTax/Pages/PropertyTaxClassifications.aspx
- Alabama: DOR assessment https://www.revenue.alabama.gov/property-tax/property-tax-assessment/ · Ala. Code §40-8-1 https://law.justia.com/codes/alabama/title-40/chapter-8/section-40-8-1/ · Mobile County Revenue Commission https://mobilecopropertytax.com/general-questions/ · Randolph County https://www.randolphcountyrevenue.com/Default.asp?ID=332&pg=Assessment
- Mississippi: Constitution §112 (SOS PDF) https://www.sos.ms.gov/content/documents/ed_pubs/pubs/Mississippi_Constitution.pdf · Miss. Code §27-35-4 https://law.justia.com/codes/mississippi/title-27/chapter-35/article-1/section-27-35-4/
- Indiana: DLGF Tax Bill 101 https://www.in.gov/dlgf/understanding-your-tax-bill/tax-bill-101/ · IC 6-1.1-20.6-7.5 https://law.justia.com/codes/indiana/title-6/article-1-1/chapter-20-6/section-6-1-1-20-6-7-5/ · SEA 1 summaries https://www.bakertilly.com/insights/upcoming-indiana-property-tax-changes--what-you-ne · https://www.indianasenaterepublicans.com/tax-cuts-for-hoosiers
- Texas: Comptroller exemptions https://comptroller.texas.gov/taxes/property-tax/exemptions/ · Tax Code §11.13 (text lags the amendment) https://texas.public.law/statutes/tex._tax_code_section_11.13 · Proposition 13 (2025) https://ballotpedia.org/Texas_Proposition_13,_Increase_Homestead_Property_Tax_Exemption_Amendment_(2025)
- Louisiana: Const. Art. VII §20 https://legis.la.gov/legis/LawPrint.aspx?d=206550 · West Baton Rouge Parish Assessor https://www.wbrassessor.org/assessments/exemptions-and-special-assessments/
- Ohio: RC 319.302 https://codes.ohio.gov/ohio-revised-code/section-319.302 · RC 323.152 https://codes.ohio.gov/ohio-revised-code/section-323.152 · GBQ 2026 updates https://www.gbq.com/resources/article/2026-ohio-property-tax-updates · Ohio House (Rep. Thomas) https://www.ohiohouse.gov/members/david-thomas/news/legislation-delivering-historic-property-tax-relief-signed-by-the-governor-140700 · Ohio House (Rep. Glassburn) https://ohiohouse.gov/news/democratic/rep-glassburn-introduces-bill-to-establish-state-credit-for-homeowners-and-renters-144586 · Vorys https://www.vorys.com/publication-ohios-new-property-tax-legislation-key-changes-effective-march-2026 · Greene County Owner-Occupancy Credit https://www.greenecountyohio.gov/970/Owner-Occupancy-Credit
- New York STAR: https://www.tax.ny.gov/pit/property/star/default.htm · https://www.tax.ny.gov/pit/property/star/eligibility.htm · RPTL 425 https://law.justia.com/codes/new-york/rpt/article-4/title-2/425/
- Pennsylvania: Philadelphia Homestead Exemption https://www.phila.gov/services/payments-assistance-taxes/taxes/property-and-real-estate-taxes/get-real-estate-tax-relief/get-the-homestead-exemption/ · https://www.phila.gov/2025-05-19-get-100k-off-your-homes-assessed-value-with-homestead/ · Real Estate Tax rate https://www.phila.gov/services/payments-assistance-taxes/taxes/property-and-real-estate-taxes/real-estate-tax/ · Allegheny County Act 50 https://www.alleghenycounty.us/Services/Property-Assessments-and-Real-Estate/Tax-Abatements-and-Exemptions/HomesteadFarmstead-Exclusion-Act-50
- Michigan PRE: https://www.michigan.gov/taxes/property/principal-residence-exemption
- Illinois exemptions (PIO-74): https://tax.illinois.gov/localgovernments/property/taxrelief.html
- Georgia homestead exemptions: https://dor.georgia.gov/property-tax-homestead-exemptions
- Kentucky homestead exemption: https://revenue.ky.gov/Property/Residential-Farm-Commercial-Property/Pages/Homestead-Exemption.aspx
- Arkansas Assessment Coordination Division (no credit figure on the served page): https://www.arkansasassessment.com/homestead-credit
- Census API endpoint attempted: https://api.census.gov/data/2023/acs/acs5 (variables B25103_001E, B25077_001E; key required)

Landlord-tenant (§5.4)
- New Jersey: N.J.S.A. 2A:18-61.1 https://law.justia.com/codes/new-jersey/title-2a/section-2a-18-61-1/ · NJ DCA Truth in Renting https://www.nj.gov/dca/codes/publications/pdf_lti/t_i_r.pdf
- New York Good Cause: HCR https://hcr.ny.gov/good-cause-eviction · RPL Article 6-A https://law.justia.com/codes/new-york/rpp/article-6-a/ · §214 https://law.justia.com/codes/new-york/rpp/article-6-a/214/ · City of Binghamton https://www.binghamton-ny.gov/government/departments/hud-administration-housing/good-cause-eviction-law · WSKG https://www.wskg.org/regional-news/2025-02-13/binghamton-city-council-unanimously-passes-good-cause-eviction-law
- Maryland: HB 693 (2024) https://mgaleg.maryland.gov/mgawebsite/Legislation/Details/hb0693?ys=2024RS · enrolled text https://mgaleg.maryland.gov/2024RS/bills/hb/hb0693E.pdf · LPJ Legal https://www.lpjlegal.com/marylands-renters-rights-stabilization-act-rrsa-oct-2024-lower-security-deposits-costlier-evictions-new-property-sale-rules-more/ · Rosenberg Martin https://rosenbergmartin.com/the-renters-rights-and-stabilization-act-of-2024-key-changes-and-implications-for-maryland-landlords-and-developers/ · DHCD right of first refusal https://dhcd.maryland.gov/housing/renter-landlord-resources/right-first-refusal · Baltimore City rental licensing https://dhcd.baltimorecity.gov/rental-licensing · https://www.marylandbusinesslitigationlawyerblog.com/how-to-get-baltimore-city-rental-property-license/
- District of Columbia: D.C. Code §42-3404.02 https://code.dccouncil.gov/us/dc/council/code/sections/42-3404.02
- Philadelphia: Municipal Court landlord-tenant pamphlet https://www.courts.phila.gov/pdf/brochures/mc/landlord-tenant-pamphlet.pdf · Philly Tenant on the EDP https://phillytenant.org/eviction-diversion-program/ · Get a Rental License https://www.phila.gov/services/permits-violations-licenses/get-a-license/business-licenses/rental-and-property/get-a-rental-license/ · Rent your property (long-term) https://www.phila.gov/services/property-lots-housing/buy-sell-or-rent-a-property/information-about-renting/rent-your-property-long-term/ · Rental suitability https://www.phila.gov/departments/fair-housing-commission/tenant-protections/rental-suitability/ · Lead certification law https://www.phila.gov/2019-10-22-rental-property-lead-certification-law/ · Philly Rental License FAQ https://www.phillyrentallicense.com/faq · Eviction Diversion Program site (JavaScript-only) https://eviction-diversion.phila.gov/
- Pittsburgh: PublicSource https://www.publicsource.org/pittsburgh-rental-registration-commonwealth-court-decision-landlord-inspection/ · WESA https://www.wesa.fm/politics-government/2023-09-21/pittsburgh-advances-new-rental-permit-requirements-while-fighting-to-enact-old-ordinance-in-court · MBM Law FAQ https://www.mbm-law.net/insights/pittsburgh-rental-permit-program-faqs/ · PureHomeRiver 2026 guide https://purehomeriver.com/property-management/investor-resources/blog/pittsburgh-landlord-laws/
- Ohio: RC 1923.04 https://codes.ohio.gov/ohio-revised-code/section-1923.04
- Virginia: §55.1-1245 https://law.lis.virginia.gov/vacode/title55.1/chapter12/section55.1-1245/
